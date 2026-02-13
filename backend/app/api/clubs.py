from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.cache import cache_response, invalidate_cache
from app.core.redis import cache_delete_pattern
from app.schemas.schemas import (
    ClubCreate, ClubUpdate, ClubResponse, ClubDetailResponse, ClubMemberResponse
)
from app.models.models import Club, ClubMember, User, UserRole

router = APIRouter()


@router.post("/clubs", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club(
    club_data: ClubCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new club"""
    # Check if slug already exists
    result = await db.execute(select(Club).where(Club.slug == club_data.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Club slug already exists"
        )
    
    # Create club with owner_id
    new_club = Club(
        name=club_data.name,
        slug=club_data.slug,
        description=club_data.description,
        location=club_data.location,
        max_members=club_data.max_members,
        is_public=club_data.is_public,
        owner_id=user_id
    )
    db.add(new_club)
    await db.flush()
    
    # Add creator as admin
    creator_membership = ClubMember(
        club_id=new_club.id,
        user_id=user_id,
        role=UserRole.ADMIN
    )
    db.add(creator_membership)
    
    # Commit transaction before returning
    await db.commit()
    
    # Invalidate clubs cache AFTER commit
    await cache_delete_pattern("clubs:*")
    
    return new_club


@router.get("/clubs", response_model=List[ClubResponse])
async def list_clubs(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List clubs where user is a member"""
    result = await db.execute(
        select(Club)
        .join(ClubMember)
        .where(ClubMember.user_id == user_id)
        .where(ClubMember.role != None)  # Active memberships only
    )
    clubs = result.scalars().all()
    
    # Add member count
    club_responses = []
    for club in clubs:
        count_result = await db.execute(
            select(func.count(ClubMember.id)).where(ClubMember.club_id == club.id)
        )
        member_count = count_result.scalar()
        
        club_data = ClubResponse.model_validate(club)
        club_data.member_count = member_count
        club_responses.append(club_data)
    
    return club_responses


@router.get("/clubs/{club_id}", response_model=ClubDetailResponse)
async def get_club(
    club_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get club details with members"""
    # Check if user is member
    membership_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == user_id
        )
    )
    if not membership_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this club"
        )
    
    # Get club
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    # Get members with user info
    members_result = await db.execute(
        select(ClubMember, User)
        .join(User)
        .where(ClubMember.club_id == club_id)
    )
    members = members_result.all()
    
    member_responses = []
    for member, user in members:
        member_responses.append(ClubMemberResponse(
            id=member.id,
            user_id=user.id,
            role=member.role,
            full_name=user.full_name,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            matches_in_club=member.matches_in_club,
            rating_in_club=member.rating_in_club,
            joined_at=member.joined_at
        ))
    
    club_detail = ClubDetailResponse.model_validate(club)
    club_detail.members = member_responses
    club_detail.member_count = len(member_responses)
    
    return club_detail


@router.patch("/clubs/{club_id}", response_model=ClubResponse)
async def update_club(
    club_id: str,
    club_data: ClubUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update club (admin/organizer only)"""
    # Check permissions
    membership_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == user_id,
            ClubMember.role.in_([UserRole.ADMIN, UserRole.ORGANIZER])
        )
    )
    if not membership_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or organizer can update club"
        )
    
    # Get club
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    # Update fields
    update_data = club_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(club, field, value)
    
    return club


@router.post("/clubs/{club_id}/join")
async def join_club(
    club_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Join a club"""
    # Check if already member
    existing = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == user_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this club"
        )
    
    # Check club exists and is public
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found"
        )
    
    if not club.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This club is invite-only"
        )
    
    # Check member limit
    count_result = await db.execute(
        select(func.count(ClubMember.id)).where(ClubMember.club_id == club_id)
    )
    if count_result.scalar() >= club.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Club has reached maximum members"
        )
    
    # Add member
    new_member = ClubMember(
        club_id=club_id,
        user_id=user_id,
        role=UserRole.MEMBER
    )
    db.add(new_member)
    
    return {"message": "Successfully joined club"}


@router.post("/clubs/{club_id}/invite")
async def invite_member(
    club_id: str,
    invitee_email: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Invite user to club by email (admin/organizer only)"""
    # Check permissions
    membership_result = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == user_id,
            ClubMember.role.in_([UserRole.ADMIN, UserRole.ORGANIZER])
        )
    )
    if not membership_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or organizer can invite members"
        )
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == invitee_email))
    invitee = result.scalar_one_or_none()
    
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with this email"
        )
    
    # Check if already member
    existing = await db.execute(
        select(ClubMember).where(
            ClubMember.club_id == club_id,
            ClubMember.user_id == invitee.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member"
        )
    
    # Add member
    new_member = ClubMember(
        club_id=club_id,
        user_id=invitee.id,
        role=UserRole.MEMBER
    )
    db.add(new_member)
    
    return {"message": f"Successfully invited {invitee.full_name}"}
