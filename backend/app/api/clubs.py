from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.cache import cache_response, invalidate_cache
from app.core.redis import cache_delete_pattern
from app.schemas.schemas import (
    ClubCreate, ClubUpdate, ClubResponse, ClubDetailResponse, ClubMemberResponse
)
from app.models.models import Club, ClubMember, Session, User, UserRole, SessionStatus

router = APIRouter()


@router.post("/clubs", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club(
    club_data: ClubCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new club"""
    import re
    
    # Validate slug format (server-side)
    if not re.match(r'^[a-z0-9-]+$', club_data.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug must contain only lowercase letters, numbers, and hyphens"
        )
    if len(club_data.slug) < 3 or len(club_data.slug) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug must be between 3 and 50 characters"
        )
    
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
    
    # Invalidate clubs cache (commit handled by DB dependency)
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

    if not clubs:
        return []

    club_ids = [club.id for club in clubs]

    owner_rows = (
        await db.execute(
            select(Club.id, User.full_name)
            .join(User, User.id == Club.owner_id)
            .where(Club.id.in_(club_ids))
        )
    ).all()
    owner_map = {club_id: full_name for club_id, full_name in owner_rows}

    member_rows = (
        await db.execute(
            select(ClubMember.club_id, func.count(ClubMember.user_id))
            .where(ClubMember.club_id.in_(club_ids))
            .group_by(ClubMember.club_id)
        )
    ).all()
    member_count_map = {club_id: count for club_id, count in member_rows}

    upcoming_rows = (
        await db.execute(
            select(Session.club_id, func.count(Session.id))
            .where(
                and_(
                    Session.club_id.in_(club_ids),
                    Session.start_time >= func.now(),
                    Session.status != SessionStatus.CANCELLED,
                )
            )
            .group_by(Session.club_id)
        )
    ).all()
    upcoming_map = {club_id: count for club_id, count in upcoming_rows}

    activity_rows = (
        await db.execute(
            select(Session.club_id, func.max(Session.updated_at))
            .where(Session.club_id.in_(club_ids))
            .group_by(Session.club_id)
        )
    ).all()
    activity_map = {club_id: ts for club_id, ts in activity_rows}

    club_responses = []
    for club in clubs:
        club_data = ClubResponse.model_validate(club)
        club_data.member_count = member_count_map.get(club.id, 0)
        club_data.owner_name = owner_map.get(club.id)
        club_data.upcoming_sessions_count = upcoming_map.get(club.id, 0)
        club_data.last_activity_at = activity_map.get(club.id)
        club_responses.append(club_data)

    return club_responses


@router.get("/clubs/public", response_model=List[ClubResponse])
async def list_public_clubs(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all public clubs that user is not a member of"""
    # Get user's current club memberships
    membership_result = await db.execute(
        select(ClubMember.club_id).where(ClubMember.user_id == user_id)
    )
    member_club_ids = {row[0] for row in membership_result.all()}
    
    # Get public clubs that user is not a member of
    result = await db.execute(
        select(Club)
        .where(Club.is_public == True)
        .where(~Club.id.in_(member_club_ids) if member_club_ids else True)
        .order_by(Club.created_at.desc())
    )
    clubs = result.scalars().all()

    if not clubs:
        return []

    club_ids = [club.id for club in clubs]

    owner_rows = (
        await db.execute(
            select(Club.id, User.full_name)
            .join(User, User.id == Club.owner_id)
            .where(Club.id.in_(club_ids))
        )
    ).all()
    owner_map = {club_id: full_name for club_id, full_name in owner_rows}

    member_rows = (
        await db.execute(
            select(ClubMember.club_id, func.count(ClubMember.user_id))
            .where(ClubMember.club_id.in_(club_ids))
            .group_by(ClubMember.club_id)
        )
    ).all()
    member_count_map = {club_id: count for club_id, count in member_rows}

    upcoming_rows = (
        await db.execute(
            select(Session.club_id, func.count(Session.id))
            .where(
                and_(
                    Session.club_id.in_(club_ids),
                    Session.start_time >= func.now(),
                    Session.status != SessionStatus.CANCELLED,
                )
            )
            .group_by(Session.club_id)
        )
    ).all()
    upcoming_map = {club_id: count for club_id, count in upcoming_rows}

    activity_rows = (
        await db.execute(
            select(Session.club_id, func.max(Session.updated_at))
            .where(Session.club_id.in_(club_ids))
            .group_by(Session.club_id)
        )
    ).all()
    activity_map = {club_id: ts for club_id, ts in activity_rows}

    club_responses = []
    for club in clubs:
        club_data = ClubResponse.model_validate(club)
        club_data.member_count = member_count_map.get(club.id, 0)
        club_data.owner_name = owner_map.get(club.id)
        club_data.upcoming_sessions_count = upcoming_map.get(club.id, 0)
        club_data.last_activity_at = activity_map.get(club.id)
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
            avatar_url=user.picture_url,
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
        select(func.count(ClubMember.user_id)).where(ClubMember.club_id == club_id)
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
