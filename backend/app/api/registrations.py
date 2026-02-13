from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.models import (
    ClubMember,
    RegistrationStatus,
    Session,
    SessionRegistration,
    SessionStatus,
    User,
    UserRole,
)
from app.websocket.socket_manager import socket_manager

router = APIRouter()


def _can_manage(role: UserRole) -> bool:
    return role in [UserRole.ADMIN, UserRole.ORGANIZER]


@router.post("/sessions/{session_id}/register")
async def register_for_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status not in [SessionStatus.OPEN, SessionStatus.FULL]:
        raise HTTPException(status_code=400, detail="Session is not open for registration")

    membership = (
        await db.execute(
            select(ClubMember).where(ClubMember.club_id == session.club_id, ClubMember.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this club")

    existing = (
        await db.execute(
            select(SessionRegistration).where(
                SessionRegistration.session_id == session_id,
                SessionRegistration.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if existing and existing.status in [RegistrationStatus.CONFIRMED, RegistrationStatus.WAITLISTED]:
        raise HTTPException(status_code=400, detail="Already registered")

    confirmed_count = (
        await db.execute(
            select(func.count()).where(
                SessionRegistration.session_id == session_id,
                SessionRegistration.status == RegistrationStatus.CONFIRMED,
            )
        )
    ).scalar() or 0

    if confirmed_count < session.max_participants:
        status = RegistrationStatus.CONFIRMED
        waitlist_position = None
    else:
        status = RegistrationStatus.WAITLISTED
        max_pos = (
            await db.execute(
                select(func.max(SessionRegistration.waitlist_position)).where(
                    SessionRegistration.session_id == session_id,
                    SessionRegistration.status == RegistrationStatus.WAITLISTED,
                )
            )
        ).scalar() or 0
        waitlist_position = max_pos + 1
        session.status = SessionStatus.FULL

    if existing:
        existing.status = status
        existing.waitlist_position = waitlist_position
        existing.registered_at = datetime.now(timezone.utc)
        reg = existing
    else:
        reg = SessionRegistration(
            session_id=session_id,
            user_id=user_id,
            status=status,
            waitlist_position=waitlist_position,
        )
        db.add(reg)

    await db.flush()

    await socket_manager.broadcast_registration_update(
        session_id=session_id,
        payload={
            "session_id": session_id,
            "user_id": user_id,
            "action": "registered",
            "status": status,
            "waitlist_position": waitlist_position,
        },
    )

    return {
        "message": "Registered",
        "status": status,
        "waitlist_position": waitlist_position,
    }


@router.post("/sessions/{session_id}/cancel")
async def cancel_registration(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    reg = (
        await db.execute(
            select(SessionRegistration).where(
                SessionRegistration.session_id == session_id,
                SessionRegistration.user_id == user_id,
                SessionRegistration.status.in_([RegistrationStatus.CONFIRMED, RegistrationStatus.WAITLISTED]),
            )
        )
    ).scalar_one_or_none()

    if not reg:
        raise HTTPException(status_code=404, detail="Active registration not found")

    was_confirmed = reg.status == RegistrationStatus.CONFIRMED
    reg.status = RegistrationStatus.CANCELLED
    reg.waitlist_position = None

    promoted_user_id = None
    if was_confirmed:
        # promote first waitlisted
        candidate = (
            await db.execute(
                select(SessionRegistration)
                .where(
                    SessionRegistration.session_id == session_id,
                    SessionRegistration.status == RegistrationStatus.WAITLISTED,
                )
                .order_by(SessionRegistration.waitlist_position.asc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if candidate:
            candidate.status = RegistrationStatus.CONFIRMED
            candidate.waitlist_position = None
            promoted_user_id = candidate.user_id

            # re-number remaining queue
            remaining = (
                await db.execute(
                    select(SessionRegistration)
                    .where(
                        SessionRegistration.session_id == session_id,
                        SessionRegistration.status == RegistrationStatus.WAITLISTED,
                    )
                    .order_by(SessionRegistration.waitlist_position.asc())
                )
            ).scalars().all()
            for idx, item in enumerate(remaining, start=1):
                item.waitlist_position = idx

    await db.flush()

    await socket_manager.broadcast_registration_update(
        session_id=session_id,
        payload={
            "session_id": session_id,
            "user_id": user_id,
            "action": "cancelled",
            "promoted_user_id": promoted_user_id,
        },
    )

    return {"message": "Registration cancelled", "promoted_user_id": promoted_user_id}


@router.post("/sessions/{session_id}/checkin")
async def check_in(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    reg = (
        await db.execute(
            select(SessionRegistration).where(
                SessionRegistration.session_id == session_id,
                SessionRegistration.user_id == user_id,
                SessionRegistration.status == RegistrationStatus.CONFIRMED,
            )
        )
    ).scalar_one_or_none()

    if not reg:
        raise HTTPException(status_code=404, detail="Confirmed registration not found")

    reg.checked_in_at = datetime.now(timezone.utc)
    reg.status = RegistrationStatus.ATTENDED
    await db.flush()

    return {"message": "Checked in", "checked_in_at": reg.checked_in_at.isoformat()}


@router.post("/sessions/{session_id}/checkout")
async def check_out(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    reg = (
        await db.execute(
            select(SessionRegistration).where(
                SessionRegistration.session_id == session_id,
                SessionRegistration.user_id == user_id,
                SessionRegistration.status == RegistrationStatus.ATTENDED,
            )
        )
    ).scalar_one_or_none()

    if not reg:
        raise HTTPException(status_code=404, detail="Checked-in registration not found")

    reg.checked_out_at = datetime.now(timezone.utc)
    await db.flush()

    return {"message": "Checked out", "checked_out_at": reg.checked_out_at.isoformat()}


@router.get("/sessions/{session_id}/registrations")
async def list_registrations(
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

    regs = (
        await db.execute(
            select(SessionRegistration, User)
            .join(User, User.id == SessionRegistration.user_id)
            .where(SessionRegistration.session_id == session_id)
            .order_by(
                SessionRegistration.status.asc(),
                SessionRegistration.waitlist_position.asc().nullsfirst(),
                SessionRegistration.registered_at.asc(),
            )
        )
    ).all()

    return [
        {
            "id": r.id,
            "user_id": u.id,
            "full_name": u.full_name,
            "display_name": u.display_name,
            "status": r.status,
            "waitlist_position": r.waitlist_position,
            "checked_in_at": r.checked_in_at,
            "checked_out_at": r.checked_out_at,
            "registered_at": r.registered_at,
        }
        for r, u in regs
    ]
