from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.models import (
    Club,
    ClubMember,
    Session,
    SessionRegistration,
    SessionStatus,
    UserRole,
    RegistrationStatus,
)
from app.schemas.schemas import SessionCreate, SessionResponse, SessionUpdate

router = APIRouter()


def _can_manage(role: UserRole) -> bool:
    return role in [UserRole.ADMIN, UserRole.ORGANIZER]


@router.post("/clubs/{club_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    club_id: str,
    payload: SessionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = (
        await db.execute(
            select(ClubMember).where(ClubMember.club_id == club_id, ClubMember.user_id == user_id)
        )
    ).scalar_one_or_none()

    if not membership or not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can create session")

    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    club = (await db.execute(select(Club).where(Club.id == club_id))).scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    session = Session(
        club_id=club_id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        start_time=payload.start_time,
        end_time=payload.end_time,
        max_participants=payload.max_participants,
        status=SessionStatus.DRAFT,
        created_by=user_id,
    )
    db.add(session)
    await db.flush()
    return session


@router.get("/clubs/{club_id}/sessions", response_model=List[SessionResponse])
async def list_sessions(
    club_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    membership = (
        await db.execute(
            select(ClubMember).where(ClubMember.club_id == club_id, ClubMember.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this club")

    sessions = (
        await db.execute(
            select(Session).where(Session.club_id == club_id).order_by(Session.start_time.desc())
        )
    ).scalars().all()

    output: List[SessionResponse] = []
    for s in sessions:
        confirmed = (
            await db.execute(
                select(func.count()).where(
                    SessionRegistration.session_id == s.id,
                    SessionRegistration.status == RegistrationStatus.CONFIRMED,
                )
            )
        ).scalar() or 0
        waitlist = (
            await db.execute(
                select(func.count()).where(
                    SessionRegistration.session_id == s.id,
                    SessionRegistration.status == RegistrationStatus.WAITLISTED,
                )
            )
        ).scalar() or 0

        data = SessionResponse.model_validate(s)
        data.confirmed_count = confirmed
        data.waitlist_count = waitlist
        output.append(data)

    return output


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    membership = (
        await db.execute(
            select(ClubMember).where(ClubMember.club_id == session.club_id, ClubMember.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this club")

    confirmed = (
        await db.execute(
            select(func.count()).where(
                SessionRegistration.session_id == session.id,
                SessionRegistration.status == RegistrationStatus.CONFIRMED,
            )
        )
    ).scalar() or 0
    waitlist = (
        await db.execute(
            select(func.count()).where(
                SessionRegistration.session_id == session.id,
                SessionRegistration.status == RegistrationStatus.WAITLISTED,
            )
        )
    ).scalar() or 0

    data = SessionResponse.model_validate(session)
    data.confirmed_count = confirmed
    data.waitlist_count = waitlist
    return data


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    membership = (
        await db.execute(
            select(ClubMember).where(ClubMember.club_id == session.club_id, ClubMember.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not membership or not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can update session")

    updates = payload.model_dump(exclude_unset=True)
    if "start_time" in updates or "end_time" in updates:
        start = updates.get("start_time", session.start_time)
        end = updates.get("end_time", session.end_time)
        if end <= start:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")

    for k, v in updates.items():
        setattr(session, k, v)

    await db.flush()

    data = SessionResponse.model_validate(session)
    return data


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    membership = (
        await db.execute(
            select(ClubMember).where(ClubMember.club_id == session.club_id, ClubMember.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not membership or not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can delete session")

    await db.delete(session)
    return {"message": "Session deleted"}


@router.post("/sessions/{session_id}/open")
async def open_registration(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    membership = (
        await db.execute(
            select(ClubMember).where(ClubMember.club_id == session.club_id, ClubMember.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not membership or not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can open registration")

    if session.status in [SessionStatus.CANCELLED, SessionStatus.COMPLETED]:
        raise HTTPException(status_code=400, detail="Cannot open registration for this session status")

    session.status = SessionStatus.OPEN
    await db.flush()

    return {"message": "Registration opened", "session_id": session_id}
