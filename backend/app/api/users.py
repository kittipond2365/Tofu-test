from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.models import User, Club, ClubMember, ClubModerator, UserRole

router = APIRouter()


@router.get("/users/me")
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/me")
async def update_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    return {"message": "Update current user - to be implemented"}


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/me/clubs/{club_id}/role")
async def get_user_club_role(
    club_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get current user's role in a specific club"""
    # Check if user is the owner
    club_result = await db.execute(select(Club).where(Club.id == club_id))
    club = club_result.scalar_one_or_none()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check ownership
    if club.owner_id == user_id:
        return {
            "club_id": club_id,
            "user_id": user_id,
            "role": "owner",
            "is_owner": True,
            "is_moderator": False,
            "is_member": True
        }
    
    # Check if moderator
    mod_result = await db.execute(
        select(ClubModerator).where(
            ClubModerator.club_id == club_id,
            ClubModerator.user_id == user_id
        )
    )
    is_moderator = mod_result.scalar_one_or_none() is not None
    
    # Check membership
    member_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == user_id
        )
    )
    membership = member_result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this club"
        )
    
    role = membership.role.value if membership.role else "member"
    
    return {
        "club_id": club_id,
        "user_id": user_id,
        "role": role,
        "is_owner": False,
        "is_moderator": is_moderator,
        "is_member": True
    }


@router.get("/users/me/is-super-admin")
async def check_super_admin(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Check if current user is a super admin"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user_id,
        "is_super_admin": user.is_super_admin
    }