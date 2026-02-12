"""
Enhanced authentication with LINE OAuth state validation and security improvements.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database_secure import get_db
from app.core.security_secure import (
    create_access_token, create_refresh_token, get_password_hash, verify_password,
    decode_token, get_current_user_id, audit_log, check_rate_limit, validate_password_strength
)
from app.core.config_secure import get_settings, Settings, validate_password_strength as validate_password
from app.schemas.schemas import TokenResponse, UserResponse
from app.models.models import User
from app.services.line_oauth_secure import line_oauth_service
from app.core.redis import cache_set, cache_get
from app.core.oauth_state import store_oauth_state, get_oauth_state, delete_oauth_state

router = APIRouter()
security = HTTPBearer()


# ============= Request Schemas =============

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        is_valid, error_msg = validate_password(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace('-', '').replace('+', '').isdigit():
            raise ValueError("เบอร์โทรศัพท์ไม่ถูกต้อง")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.replace('-', '').replace('+', '').isdigit():
            raise ValueError("เบอร์โทรศัพท์ไม่ถูกต้อง")
        return v


# ============= Authentication Endpoints =============

@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Register a new user with email and password"""
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        audit_log(
            action="register_failed",
            resource_type="user",
            details={"reason": "email_exists", "email": user_data.email},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="อีเมลนี้ถูกใช้งานแล้ว"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        display_name=user_data.display_name,
        phone=user_data.phone,
        avatar_url=user_data.avatar_url
    )
    
    db.add(new_user)
    await db.flush()
    
    # Audit log
    audit_log(
        action="register_success",
        user_id=new_user.id,
        resource_type="user",
        resource_id=new_user.id,
        ip_address=client_ip
    )
    
    return new_user


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Login with email and password"""
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        audit_log(
            action="login_failed",
            details={"reason": "invalid_credentials", "email": credentials.email},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        audit_log(
            action="login_failed",
            user_id=user.id,
            details={"reason": "account_inactive"},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="บัญชีผู้ใช้ถูกระงับ"
        )
    
    # Create tokens
    access_token, _ = create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    refresh_token, _ = create_refresh_token(
        data={"sub": user.id}
    )
    
    # Audit log
    audit_log(
        action="login_success",
        user_id=user.id,
        ip_address=client_ip
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )


# ============= LINE OAuth Endpoints =============

@router.get("/auth/line/login")
async def line_login(
    request: Request,
    settings: Settings = Depends(get_settings)
):
    """Get LINE Login URL with state parameter for CSRF protection"""
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    state = str(uuid.uuid4())
    
    # Try Redis first, fallback to memory storage
    cache_key = f"line_oauth_state:{state}"
    redis_success = await cache_set(cache_key, client_ip, expire=settings.LINE_STATE_EXPIRY)
    
    if not redis_success:
        # Fallback to memory storage
        await store_oauth_state(state, client_ip, expire=settings.LINE_STATE_EXPIRY)
    
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
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """
    LINE OAuth callback with state validation.
    Handles LINE login/signup securely.
    """
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    # Validate state parameter (CSRF protection)
    # Try Redis first, fallback to memory storage
    cache_key = f"line_oauth_state:{state}"
    stored_ip = await cache_get(cache_key)
    
    if stored_ip:
        # Delete from Redis
        from app.core.redis import get_redis
        r = await get_redis()
        await r.delete(cache_key)
    else:
        # Fallback to memory storage
        stored_ip = await get_oauth_state(state)
        if stored_ip:
            await delete_oauth_state(state)
    
    if not stored_ip:
        audit_log(
            action="line_oauth_failed",
            details={"reason": "invalid_state", "state": state},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="รหัสสถานะไม่ถูกต้องหรือหมดอายุ กรุณาลองใหม่"
        )
    
    # Optional: Validate IP matches (additional security)
    # if stored_ip != client_ip:
    #     logger.warning("LINE OAuth IP mismatch", stored=stored_ip, current=client_ip)
    
    # Exchange code for token
    token_data = await line_oauth_service.exchange_code_for_token(code)
    if not token_data:
        audit_log(
            action="line_oauth_failed",
            details={"reason": "token_exchange_failed"},
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถแลกเปลี่ยนโทเค็นได้"
        )
    
    access_token = token_data.get("access_token")
    
    # Get user profile from LINE
    profile = await line_oauth_service.get_user_profile(access_token)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถดึงข้อมูลผู้ใช้จาก LINE ได้"
        )
    
    line_user_id = profile.get("userId")
    display_name = profile.get("displayName")
    picture_url = profile.get("pictureUrl")
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.line_user_id == line_user_id))
    user = result.scalar_one_or_none()
    
    if user:
        # Update avatar if changed
        if picture_url and user.avatar_url != picture_url:
            user.avatar_url = picture_url
            await db.flush()
        
        # Existing user - generate tokens
        access_token, _ = create_access_token(data={"sub": user.id, "email": user.email or ""})
        refresh_token, _ = create_refresh_token(data={"sub": user.id})
        
        audit_log(
            action="line_login_success",
            user_id=user.id,
            details={"line_user_id": line_user_id},
            ip_address=client_ip
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    # New user - create account
    new_user = User(
        email=None,  # No email initially
        hashed_password=None,  # No password for LINE users
        full_name=display_name,
        display_name=display_name,
        line_user_id=line_user_id,
        avatar_url=picture_url,
        is_verified=True
    )
    
    db.add(new_user)
    await db.flush()
    
    # Generate tokens
    access_token, _ = create_access_token(data={"sub": new_user.id, "email": ""})
    refresh_token, _ = create_refresh_token(data={"sub": new_user.id})
    
    audit_log(
        action="line_register_success",
        user_id=new_user.id,
        details={"line_user_id": line_user_id},
        ip_address=client_ip
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# ============= Token Refresh =============

@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    """Refresh access token using refresh token"""
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    payload = decode_token(refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="โทเค็นรีเฟรชไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ไม่พบผู้ใช้หรือบัญชีถูกระงับ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    new_access_token, _ = create_access_token(data={"sub": user.id, "email": user.email or ""})
    new_refresh_token, _ = create_refresh_token(data={"sub": user.id})
    
    audit_log(
        action="token_refresh",
        user_id=user.id,
        ip_address=client_ip
    )
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# ============= User Profile Endpoints =============

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
            detail="ไม่พบผู้ใช้"
        )
    
    return user


@router.patch("/auth/me", response_model=UserResponse)
async def update_profile(
    update_data: ProfileUpdateRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    client_ip = getattr(request.state, 'client_ip', 'unknown')
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบผู้ใช้"
        )
    
    # Update fields if provided
    updates = {}
    if update_data.display_name is not None:
        updates["display_name"] = update_data.display_name
        user.display_name = update_data.display_name
    if update_data.full_name is not None:
        updates["full_name"] = update_data.full_name
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
                    detail="อีเมลนี้ถูกใช้งานแล้ว"
                )
        updates["email"] = update_data.email
        user.email = update_data.email
    if update_data.phone is not None:
        updates["phone"] = update_data.phone
        user.phone = update_data.phone
    
    await db.flush()
    
    # Audit log
    audit_log(
        action="profile_update",
        user_id=user_id,
        details=updates,
        ip_address=client_ip
    )
    
    return user
