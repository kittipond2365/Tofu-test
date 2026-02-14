"""
Simple in-memory OAuth state storage (Redis-free fallback).

- One-time use state tokens
- Optional IP binding
- Automatic expiry cleanup on access
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, TypedDict
import threading


class StoredOAuthState(TypedDict):
    ip: str
    expires: datetime


_oauth_states: Dict[str, StoredOAuthState] = {}
_lock = threading.Lock()


def _utcnow() -> datetime:
    return datetime.utcnow()


def _cleanup_expired(now: Optional[datetime] = None) -> None:
    current = now or _utcnow()
    expired_keys = [k for k, v in _oauth_states.items() if v["expires"] <= current]
    for key in expired_keys:
        _oauth_states.pop(key, None)


async def store_oauth_state(state: str, ip_address: str, expires_in: int = 600) -> bool:
    """Store OAuth state in memory with expiry."""
    try:
        with _lock:
            _cleanup_expired()
            _oauth_states[state] = {
                "ip": ip_address,
                "expires": _utcnow() + timedelta(seconds=expires_in),
            }
        return True
    except Exception:
        return False


async def validate_oauth_state(state: str, ip_address: str) -> bool:
    """Validate and consume one-time OAuth state token."""
    try:
        with _lock:
            _cleanup_expired()
            stored = _oauth_states.pop(state, None)

            if not stored:
                return False

            if stored["expires"] <= _utcnow():
                return False

            # Allow unknown IPs to avoid proxy-related false negatives.
            if stored["ip"] in ("", "unknown") or ip_address in ("", "unknown"):
                return True

            return stored["ip"] == ip_address
    except Exception:
        return False


# Backward-compatible helper for existing imports/usages.
async def get_oauth_state(state: str) -> Optional[str]:
    """Get and consume state, returning stored IP if valid and not expired."""
    try:
        with _lock:
            _cleanup_expired()
            stored = _oauth_states.pop(state, None)
            if not stored:
                return None
            if stored["expires"] <= _utcnow():
                return None
            return stored["ip"]
    except Exception:
        return None


async def delete_oauth_state(state: str) -> None:
    """Delete OAuth state from memory."""
    try:
        with _lock:
            _oauth_states.pop(state, None)
    except Exception:
        pass
