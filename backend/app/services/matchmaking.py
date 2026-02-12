from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class CandidatePlayer:
    user_id: str
    rating: float = 1000.0
    matches_played: int = 0
    last_played_at: Optional[datetime] = None


class MatchmakingError(Exception):
    pass


def _minutes_since(dt: Optional[datetime], now: datetime) -> float:
    if not dt:
        return 10_000.0
    return max((now - dt).total_seconds() / 60.0, 0.0)


def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    return (value - low) / (high - low)


def _pair_key(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted((a, b)))


def select_fair_players(
    players: Iterable[CandidatePlayer],
    target_count: int = 4,
    now: Optional[datetime] = None,
) -> List[CandidatePlayer]:
    """Pick players with fair priority:
    - fewer matches played first
    - longer rest first
    - lower rating slight priority (to avoid starvation)
    """
    now = now or datetime.utcnow()
    pool = list(players)
    if len(pool) < target_count:
        raise MatchmakingError(f"Not enough players for matchmaking. Need {target_count}, got {len(pool)}")

    match_counts = [p.matches_played for p in pool]
    rests = [_minutes_since(p.last_played_at, now) for p in pool]
    ratings = [p.rating for p in pool]

    min_m, max_m = min(match_counts), max(match_counts)
    min_r, max_r = min(rests), max(rests)
    min_rt, max_rt = min(ratings), max(ratings)

    def priority(p: CandidatePlayer) -> float:
        match_score = 1.0 - _normalize(float(p.matches_played), float(min_m), float(max_m))
        rest_score = _normalize(_minutes_since(p.last_played_at, now), min_r, max_r)
        rating_score = 1.0 - _normalize(float(p.rating), float(min_rt), float(max_rt))
        return (0.6 * match_score) + (0.3 * rest_score) + (0.1 * rating_score)

    ranked = sorted(pool, key=priority, reverse=True)
    return ranked[:target_count]


def create_balanced_teams(
    selected_players: List[CandidatePlayer],
    partner_history: Optional[Dict[Tuple[str, str], int]] = None,
) -> Dict[str, object]:
    """Create two balanced teams while minimizing repeated partners.

    selected_players should normally be 4 players.
    Returns:
      {
        "team_a": (user_id_1, user_id_2),
        "team_b": (user_id_3, user_id_4),
        "balance_gap": float,
      }
    """
    if len(selected_players) != 4:
        raise MatchmakingError("Balanced doubles requires exactly 4 players")

    partner_history = partner_history or {}

    best = None
    ids = [p.user_id for p in selected_players]
    player_by_id = {p.user_id: p for p in selected_players}

    for pair in combinations(ids, 2):
        remaining = [x for x in ids if x not in pair]
        team_a = tuple(pair)
        team_b = tuple(remaining)

        # canonical ordering for determinism
        team_a = tuple(sorted(team_a))
        team_b = tuple(sorted(team_b))

        rating_a = sum(player_by_id[x].rating for x in team_a)
        rating_b = sum(player_by_id[x].rating for x in team_b)
        balance_gap = abs(rating_a - rating_b)

        repeated_partners_penalty = (
            partner_history.get(_pair_key(team_a[0], team_a[1]), 0)
            + partner_history.get(_pair_key(team_b[0], team_b[1]), 0)
        )

        # main objective: avoid repeating partners, secondary: rating balance
        score = (repeated_partners_penalty * 200.0) + balance_gap

        candidate = {
            "team_a": team_a,
            "team_b": team_b,
            "balance_gap": balance_gap,
            "score": score,
        }
        if best is None or candidate["score"] < best["score"]:
            best = candidate

    if best is None:
        raise MatchmakingError("Unable to build teams")

    return {
        "team_a": best["team_a"],
        "team_b": best["team_b"],
        "balance_gap": best["balance_gap"],
    }


def generate_fair_doubles_match(
    players: Iterable[CandidatePlayer],
    partner_history: Optional[Dict[Tuple[str, str], int]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, object]:
    selected = select_fair_players(players, target_count=4, now=now)
    return create_balanced_teams(selected, partner_history=partner_history)
