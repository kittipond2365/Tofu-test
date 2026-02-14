from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.models import (
    ClubMember,
    Match,
    MatchStatus,
    RegistrationStatus,
    Session,
    SessionRegistration,
    User,
    UserRole,
)
from app.schemas.schemas import MatchCreate, MatchResponse, MatchUpdateScore, MatchUpdateStatus, PlayerSummary
from app.services.matchmaking import CandidatePlayer, MatchmakingError, generate_fair_doubles_match
from app.websocket.socket_manager import socket_manager

router = APIRouter()


def _can_manage(role: UserRole) -> bool:
    return role in [UserRole.ADMIN, UserRole.ORGANIZER]


async def _get_session_or_404(db: AsyncSession, session_id: str) -> Session:
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def _check_member_or_403(db: AsyncSession, club_id: str, user_id: str) -> ClubMember:
    membership = (
        await db.execute(select(ClubMember).where(ClubMember.club_id == club_id, ClubMember.user_id == user_id))
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this club")
    return membership


async def _players_map(db: AsyncSession, user_ids: List[str]) -> Dict[str, User]:
    rows = (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
    return {u.id: u for u in rows}


def _to_player_summary(u: User) -> PlayerSummary:
    return PlayerSummary(
        id=u.id,
        full_name=u.full_name,
        display_name=u.display_name,
        avatar_url=u.avatar_url,
        rating=u.rating,
    )


async def _serialize_match(db: AsyncSession, match: Match) -> MatchResponse:
    user_ids = [
        match.team_a_player_1_id,
        match.team_b_player_1_id,
    ]
    if match.team_a_player_2_id:
        user_ids.append(match.team_a_player_2_id)
    if match.team_b_player_2_id:
        user_ids.append(match.team_b_player_2_id)

    users = await _players_map(db, list(set(user_ids)))

    if match.team_a_player_1_id not in users or match.team_b_player_1_id not in users:
        raise HTTPException(status_code=500, detail="Match has invalid player references")

    return MatchResponse(
        id=match.id,
        session_id=match.session_id,
        court_number=match.court_number,
        team_a_player_1=_to_player_summary(users[match.team_a_player_1_id]),
        team_a_player_2=_to_player_summary(users[match.team_a_player_2_id]) if match.team_a_player_2_id else None,
        team_b_player_1=_to_player_summary(users[match.team_b_player_1_id]),
        team_b_player_2=_to_player_summary(users[match.team_b_player_2_id]) if match.team_b_player_2_id else None,
        score=match.score,
        winner_team=match.winner_team,
        status=match.status,
        started_at=match.started_at,
        completed_at=match.completed_at,
        created_at=match.created_at,
    )


async def _get_partner_history(db: AsyncSession, session_id: str) -> Dict[Tuple[str, str], int]:
    matches = (await db.execute(select(Match).where(Match.session_id == session_id))).scalars().all()
    history: Dict[Tuple[str, str], int] = {}

    for m in matches:
        if m.team_a_player_2_id:
            key = tuple(sorted((m.team_a_player_1_id, m.team_a_player_2_id)))
            history[key] = history.get(key, 0) + 1
        if m.team_b_player_2_id:
            key = tuple(sorted((m.team_b_player_1_id, m.team_b_player_2_id)))
            history[key] = history.get(key, 0) + 1

    return history


async def _build_auto_match(db: AsyncSession, session_id: str) -> MatchCreate:
    regs = (
        await db.execute(
            select(SessionRegistration, User)
            .join(User, User.id == SessionRegistration.user_id)
            .where(
                SessionRegistration.session_id == session_id,
                SessionRegistration.status.in_([RegistrationStatus.CONFIRMED, RegistrationStatus.ATTENDED]),
            )
        )
    ).all()

    if len(regs) < 4:
        raise HTTPException(status_code=400, detail="Need at least 4 registered players for auto matchmaking")

    matches = (await db.execute(select(Match).where(Match.session_id == session_id))).scalars().all()
    player_match_count: Dict[str, int] = {}
    player_last_played_at: Dict[str, datetime] = {}

    for m in matches:
        participants = [m.team_a_player_1_id, m.team_b_player_1_id]
        if m.team_a_player_2_id:
            participants.append(m.team_a_player_2_id)
        if m.team_b_player_2_id:
            participants.append(m.team_b_player_2_id)
        for uid in participants:
            player_match_count[uid] = player_match_count.get(uid, 0) + 1
            last_time = m.completed_at or m.started_at or m.created_at
            if uid not in player_last_played_at or (last_time and last_time > player_last_played_at[uid]):
                player_last_played_at[uid] = last_time

    candidates = [
        CandidatePlayer(
            user_id=user.id,
            rating=user.rating,
            matches_played=player_match_count.get(user.id, 0),
            last_played_at=player_last_played_at.get(user.id),
        )
        for _, user in regs
    ]

    partner_history = await _get_partner_history(db, session_id)

    try:
        result = generate_fair_doubles_match(candidates, partner_history=partner_history)
    except MatchmakingError as e:
        raise HTTPException(status_code=400, detail=str(e))

    team_a = result["team_a"]
    team_b = result["team_b"]

    max_court = (await db.execute(select(func.max(Match.court_number)).where(Match.session_id == session_id))).scalar() or 0

    return MatchCreate(
        court_number=max_court + 1,
        team_a_player_1_id=team_a[0],
        team_a_player_2_id=team_a[1],
        team_b_player_1_id=team_b[0],
        team_b_player_2_id=team_b[1],
    )


@router.post("/sessions/{session_id}/matches", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    session_id: str,
    payload: Optional[MatchCreate] = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_or_404(db, session_id)
    membership = await _check_member_or_403(db, session.club_id, user_id)
    if not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can create matches")

    # Auto-matchmaking when no payload or empty payload (no player_ids specified)
    if payload is None or (payload.team_a_player_1_id is None and payload.team_b_player_1_id is None):
        payload = await _build_auto_match(db, session_id)

    players = [
        payload.team_a_player_1_id,
        payload.team_b_player_1_id,
    ]
    if payload.team_a_player_2_id:
        players.append(payload.team_a_player_2_id)
    if payload.team_b_player_2_id:
        players.append(payload.team_b_player_2_id)

    if len(set(players)) != len(players):
        raise HTTPException(status_code=400, detail="Players in a match must be unique")

    # Ensure all players are registered in this session
    registered_player_ids = (
        await db.execute(
            select(SessionRegistration.user_id).where(
                SessionRegistration.session_id == session_id,
                SessionRegistration.status.in_([RegistrationStatus.CONFIRMED, RegistrationStatus.ATTENDED]),
            )
        )
    ).scalars().all()

    if not set(players).issubset(set(registered_player_ids)):
        raise HTTPException(status_code=400, detail="All players must be registered in this session")

    match = Match(
        session_id=session_id,
        court_number=payload.court_number,
        team_a_player_1_id=payload.team_a_player_1_id,
        team_a_player_2_id=payload.team_a_player_2_id,
        team_b_player_1_id=payload.team_b_player_1_id,
        team_b_player_2_id=payload.team_b_player_2_id,
        status=MatchStatus.SCHEDULED,
    )
    db.add(match)
    await db.flush()

    return await _serialize_match(db, match)


@router.get("/sessions/{session_id}/matches", response_model=List[MatchResponse])
async def list_matches(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_or_404(db, session_id)
    await _check_member_or_403(db, session.club_id, user_id)

    matches = (
        await db.execute(select(Match).where(Match.session_id == session_id).order_by(Match.created_at.desc()))
    ).scalars().all()

    return [await _serialize_match(db, m) for m in matches]


@router.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    session = await _get_session_or_404(db, match.session_id)
    await _check_member_or_403(db, session.club_id, user_id)

    return await _serialize_match(db, match)


@router.patch("/matches/{match_id}/score", response_model=MatchResponse)
async def update_score(
    match_id: str,
    payload: MatchUpdateScore,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    session = await _get_session_or_404(db, match.session_id)
    membership = await _check_member_or_403(db, session.club_id, user_id)
    if not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can update score")

    match.score = payload.score
    match.winner_team = payload.winner_team

    if match.status != MatchStatus.COMPLETED:
        match.status = MatchStatus.ONGOING if not match.started_at else match.status

    await db.flush()

    await socket_manager.broadcast_score_update(
        session_id=match.session_id,
        payload={"match_id": match.id, "score": match.score, "winner_team": match.winner_team},
    )

    return await _serialize_match(db, match)


@router.patch("/matches/{match_id}/status", response_model=MatchResponse)
async def update_status(
    match_id: str,
    payload: MatchUpdateStatus,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    session = await _get_session_or_404(db, match.session_id)
    membership = await _check_member_or_403(db, session.club_id, user_id)
    if not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can update status")

    new_status = payload.status
    match.status = new_status

    if new_status == MatchStatus.ONGOING and not match.started_at:
        match.started_at = datetime.utcnow()
    if new_status == MatchStatus.COMPLETED and not match.completed_at:
        match.completed_at = datetime.utcnow()

    await db.flush()
    return await _serialize_match(db, match)


@router.post("/matches/{match_id}/start", response_model=MatchResponse)
async def start_match(
    match_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    session = await _get_session_or_404(db, match.session_id)
    membership = await _check_member_or_403(db, session.club_id, user_id)
    if not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can start match")

    if match.status == MatchStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Completed match cannot be started")

    match.status = MatchStatus.ONGOING
    if not match.started_at:
        match.started_at = datetime.utcnow()
    await db.flush()

    await socket_manager.broadcast_match_started(
        session_id=match.session_id,
        payload={"match_id": match.id, "started_at": match.started_at.isoformat()},
    )

    return await _serialize_match(db, match)


@router.post("/matches/{match_id}/complete", response_model=MatchResponse)
async def complete_match(
    match_id: str,
    winner_team: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if winner_team not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="winner_team must be 'A' or 'B'")

    match = (await db.execute(select(Match).where(Match.id == match_id))).scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    session = await _get_session_or_404(db, match.session_id)
    membership = await _check_member_or_403(db, session.club_id, user_id)
    if not _can_manage(membership.role):
        raise HTTPException(status_code=403, detail="Only admin/organizer can complete match")

    if match.status == MatchStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Match already completed")

    match.status = MatchStatus.COMPLETED
    match.winner_team = winner_team
    if not match.started_at:
        match.started_at = datetime.utcnow()
    match.completed_at = datetime.utcnow()

    team_a_ids = [match.team_a_player_1_id] + ([match.team_a_player_2_id] if match.team_a_player_2_id else [])
    team_b_ids = [match.team_b_player_1_id] + ([match.team_b_player_2_id] if match.team_b_player_2_id else [])

    winner_ids = team_a_ids if winner_team == "A" else team_b_ids
    loser_ids = team_b_ids if winner_team == "A" else team_a_ids

    all_player_ids = team_a_ids + team_b_ids
    users = (await db.execute(select(User).where(User.id.in_(all_player_ids)))).scalars().all()
    by_id = {u.id: u for u in users}

    for uid in winner_ids:
        if uid in by_id:
            by_id[uid].wins += 1
            by_id[uid].total_matches += 1
            by_id[uid].rating += 5
    for uid in loser_ids:
        if uid in by_id:
            by_id[uid].losses += 1
            by_id[uid].total_matches += 1
            by_id[uid].rating = max(100.0, by_id[uid].rating - 3)

    members = (
        await db.execute(
            select(ClubMember).where(
                ClubMember.club_id == session.club_id,
                ClubMember.user_id.in_(all_player_ids),
            )
        )
    ).scalars().all()

    for cm in members:
        cm.matches_in_club += 1
        if cm.user_id in winner_ids:
            cm.wins_in_club += 1
            cm.rating_in_club += 5
        else:
            cm.rating_in_club = max(100.0, cm.rating_in_club - 3)

    await db.flush()

    return await _serialize_match(db, match)
