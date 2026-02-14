from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.security import (
    create_access_token, create_refresh_token, get_password_hash, verify_password,
    decode_token, get_current_user_id
)
from app.schemas.schemas import TokenResponse, UserResponse
from app.models.models import User
from app.core.oauth_state import store_oauth_state, validate_oauth_state

router = APIRouter()
security = HTTPBearer()


def _get_client_ip(request: Request) -> str:
    """Best-effort client IP extraction (proxy-aware)."""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # Standard format: client, proxy1, proxy2
        return x_forwarded_for.split(",")[0].strip()

    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip.strip()

    return request.client.host if request.client else "unknown"


# Request schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    picture_url: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TestUserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    line_user_id: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None


import os


@router.post("/auth/test-login")
async def test_login(
    test_user: TestUserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create test user and return JWT (TESTING ONLY)"""
    if os.getenv("ENV") != "testing":
        raise HTTPException(status_code=403, detail="Test login disabled in production")

    # Create or get test user
    line_user_id = test_user.line_user_id or f"test:{test_user.name.lower().replace(' ', '-')}"

    result = await db.execute(select(User).where(User.line_user_id == line_user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            line_user_id=line_user_id,
            email=test_user.email,
            hashed_password=None,
            full_name=test_user.name,
            display_name=test_user.name,
            is_verified=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)
        await db.flush()

    access_token = create_access_token(data={"sub": user.id, "email": user.email or ""})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user
    }


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    display_name = user_data.display_name or user_data.full_name

    new_user = User(
        id=user_id,
        line_user_id=f"email:{user_data.email.lower()}",
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        display_name=display_name,
        phone=user_data.phone,
        picture_url=user_data.picture_url,
    )
    
    db.add(new_user)
    await db.flush()
    
    return new_user


@router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token"""
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30
    )


# LINE OAuth service
from app.services.line_oauth import line_oauth_service


@router.get("/auth/line/login")
async def line_login(request: Request):
    """Get LINE Login URL"""
    import uuid
    state = str(uuid.uuid4())
    client_ip = _get_client_ip(request)
    await store_oauth_state(state, client_ip)
    login_url = line_oauth_service.get_login_url(state)
    return {
        "login_url": login_url,
        "state": state
    }


@router.get("/auth/line/callback")
async def line_callback(
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """LINE OAuth callback - handle LINE login/signup"""
    # Validate OAuth state (one-time token)
    client_ip = _get_client_ip(request)
    is_valid_state = await validate_oauth_state(state, client_ip)
    if not is_valid_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state validation failed"
        )

    # Exchange code for token
    token_data = await line_oauth_service.exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
    
    access_token = token_data.get("access_token")
    
    # Get user profile from LINE
    profile = await line_oauth_service.get_user_profile(access_token)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user profile"
        )
    
    line_user_id = profile.get("userId")
    display_name = profile.get("displayName")
    picture_url = profile.get("pictureUrl")
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.line_user_id == line_user_id))
    user = result.scalar_one_or_none()
    
    if user:
        # Update avatar if changed
        if picture_url and user.picture_url != picture_url:
            user.picture_url = picture_url
            await db.flush()
        
        # Existing user - generate tokens
        access_token = create_access_token(data={"sub": user.id, "email": user.email or ""})
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30
        )
    
    # New user - create account
    # Use LINE display_name as default, user can change later
    new_user = User(
        id=str(uuid.uuid4()),
        email=None,
        hashed_password=None,
        full_name=display_name,
        display_name=display_name,
        line_user_id=line_user_id,
        picture_url=picture_url,
        is_verified=True,
        created_at=datetime.utcnow(),
    )
    
    db.add(new_user)
    await db.flush()
    
    # Generate tokens
    access_token = create_access_token(data={"sub": new_user.id, "email": ""})
    refresh_token = create_refresh_token(data={"sub": new_user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    refresh_token = payload.refresh_token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": user.id, "email": user.email or ""})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=30
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user info"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# Profile update schemas
class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


@router.patch("/auth/me", response_model=UserResponse)
async def update_profile(
    update_data: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile (display name, email, etc.)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if update_data.display_name is not None:
        user.display_name = update_data.display_name
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.email is not None:
        # Check if email is already used by another user
        if update_data.email:
            existing = await db.execute(
                select(User).where(
                    User.email == update_data.email,
                    User.id != user_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        user.email = update_data.email
    if update_data.phone is not None:
        user.phone = update_data.phone
    
    await db.flush()
    return user
