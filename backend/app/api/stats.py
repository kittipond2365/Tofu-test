from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.models import Club, ClubMember, Match, MatchStatus, Session, User
from app.schemas.schemas import ClubStatsResponse, PlayerStatsResponse, SessionResponse

router = APIRouter()


async def _check_member_or_403(db: AsyncSession, club_id: str, user_id: str) -> ClubMember:
    membership = (
        await db.execute(select(ClubMember).where(ClubMember.club_id == club_id, ClubMember.user_id == user_id))
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this club")
    return membership


@router.get("/clubs/{club_id}/stats", response_model=ClubStatsResponse)
async def get_club_stats(
    club_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _check_member_or_403(db, club_id, user_id)

    club = (await db.execute(select(Club).where(Club.id == club_id))).scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    total_members = (await db.execute(select(func.count(ClubMember.user_id)).where(ClubMember.club_id == club_id))).scalar() or 0
    total_sessions = (await db.execute(select(func.count(Session.id)).where(Session.club_id == club_id))).scalar() or 0

    total_matches = (
        await db.execute(
            select(func.count(Match.id))
            .join(Session, Session.id == Match.session_id)
            .where(Session.club_id == club_id)
        )
    ).scalar() or 0

    top_rows = (
        await db.execute(
            select(ClubMember, User)
            .join(User, User.id == ClubMember.user_id)
            .where(ClubMember.club_id == club_id)
            .order_by(ClubMember.rating_in_club.desc(), ClubMember.wins_in_club.desc())
            .limit(5)
        )
    ).all()

    top_players: List[PlayerStatsResponse] = []
    for cm, u in top_rows:
        losses = max(cm.matches_in_club - cm.wins_in_club, 0)
        win_rate = (cm.wins_in_club / cm.matches_in_club * 100.0) if cm.matches_in_club else 0.0
        top_players.append(
            PlayerStatsResponse(
                user_id=u.id,
                full_name=u.full_name,
                display_name=u.display_name,
                avatar_url=u.picture_url,
                total_matches=cm.matches_in_club,
                wins=cm.wins_in_club,
                losses=losses,
                win_rate=round(win_rate, 2),
                rating=cm.rating_in_club,
                matches_this_month=0,
            )
        )

    recent_sessions = (
        await db.execute(select(Session).where(Session.club_id == club_id).order_by(Session.start_time.desc()).limit(5))
    ).scalars().all()

    recent_session_responses = [SessionResponse.model_validate(s) for s in recent_sessions]

    return ClubStatsResponse(
        club_id=club.id,
        club_name=club.name,
        total_members=total_members,
        total_sessions=total_sessions,
        total_matches=total_matches,
        top_players=top_players,
        recent_sessions=recent_session_responses,
    )


@router.get("/clubs/{club_id}/leaderboard", response_model=List[PlayerStatsResponse])
async def get_leaderboard(
    club_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _check_member_or_403(db, club_id, user_id)

    rows = (
        await db.execute(
            select(ClubMember, User)
            .join(User, User.id == ClubMember.user_id)
            .where(ClubMember.club_id == club_id)
            .order_by(ClubMember.rating_in_club.desc(), ClubMember.wins_in_club.desc(), ClubMember.matches_in_club.desc())
        )
    ).all()

    return [
        PlayerStatsResponse(
            user_id=u.id,
            full_name=u.full_name,
            display_name=u.display_name,
            avatar_url=u.picture_url,
            total_matches=cm.matches_in_club,
            wins=cm.wins_in_club,
            losses=max(cm.matches_in_club - cm.wins_in_club, 0),
            win_rate=round((cm.wins_in_club / cm.matches_in_club * 100.0), 2) if cm.matches_in_club else 0.0,
            rating=cm.rating_in_club,
            matches_this_month=0,
        )
        for cm, u in rows
    ]


@router.get("/users/{user_id}/stats", response_model=PlayerStatsResponse)
async def get_user_stats(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # allow self or club peers (must share at least one club)
    if user_id != current_user_id:
        shared = (
            await db.execute(
                select(func.count())
                .where(ClubMember.user_id == current_user_id)
                .where(ClubMember.club_id.in_(select(ClubMember.club_id).where(ClubMember.user_id == user_id)))
            )
        ).scalar() or 0
        if shared == 0:
            raise HTTPException(status_code=403, detail="Not allowed to view this user's stats")

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    start_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    matches_this_month = (
        await db.execute(
            select(func.count(Match.id)).where(
                Match.status == MatchStatus.COMPLETED,
                Match.completed_at >= start_month,
                or_(
                    Match.team_a_player_1_id == user_id,
                    Match.team_a_player_2_id == user_id,
                    Match.team_b_player_1_id == user_id,
                    Match.team_b_player_2_id == user_id,
                ),
            )
        )
    ).scalar() or 0

    win_rate = (user.wins / user.total_matches * 100.0) if user.total_matches else 0.0

    return PlayerStatsResponse(
        user_id=user.id,
        full_name=user.full_name,
        display_name=user.display_name,
        avatar_url=user.picture_url,
        total_matches=user.total_matches,
        wins=user.wins,
        losses=user.losses,
        win_rate=round(win_rate, 2),
        rating=user.rating,
        matches_this_month=matches_this_month,
    )


@router.get("/clubs/{club_id}/players/{user_id}/stats", response_model=PlayerStatsResponse)
async def get_player_club_stats(
    club_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _check_member_or_403(db, club_id, current_user_id)

    row = (
        await db.execute(
            select(ClubMember, User)
            .join(User, User.id == ClubMember.user_id)
            .where(ClubMember.club_id == club_id, ClubMember.user_id == user_id)
        )
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Player not found in this club")

    cm, u = row

    start_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    matches_this_month = (
        await db.execute(
            select(func.count(Match.id))
            .join(Session, Session.id == Match.session_id)
            .where(
                Session.club_id == club_id,
                Match.status == MatchStatus.COMPLETED,
                Match.completed_at >= start_month,
                or_(
                    Match.team_a_player_1_id == user_id,
                    Match.team_a_player_2_id == user_id,
                    Match.team_b_player_1_id == user_id,
                    Match.team_b_player_2_id == user_id,
                ),
            )
        )
    ).scalar() or 0

    losses = max(cm.matches_in_club - cm.wins_in_club, 0)
    win_rate = (cm.wins_in_club / cm.matches_in_club * 100.0) if cm.matches_in_club else 0.0

    return PlayerStatsResponse(
        user_id=u.id,
        full_name=u.full_name,
        display_name=u.display_name,
        avatar_url=u.picture_url,
        total_matches=cm.matches_in_club,
        wins=cm.wins_in_club,
        losses=losses,
        win_rate=round(win_rate, 2),
        rating=cm.rating_in_club,
        matches_this_month=matches_this_month,
    )
