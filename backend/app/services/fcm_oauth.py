import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

import structlog
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.core.config import get_settings

logger = structlog.get_logger()

_FCM_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
_token_lock = Lock()
_cached_token: Optional[str] = None
_cached_expiry: Optional[datetime] = None


def _load_service_account_info() -> dict:
    """Load service account credentials from env JSON or file path."""
    settings = get_settings()

    if settings.FCM_SERVICE_ACCOUNT_JSON:
        try:
            return json.loads(settings.FCM_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError as exc:
            logger.error("Invalid FCM service account JSON", error=str(exc))
            raise

    path = Path(settings.FCM_SERVICE_ACCOUNT_PATH)
    if not path.is_absolute():
        path = Path.cwd() / path

    if not path.exists():
        raise FileNotFoundError(f"FCM service account file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_fcm_access_token() -> str:
    """Generate a fresh OAuth2 access token for FCM HTTP v1 API."""
    info = _load_service_account_info()
    credentials = service_account.Credentials.from_service_account_info(info, scopes=_FCM_SCOPES)
    credentials.refresh(Request())

    if not credentials.token:
        raise RuntimeError("Failed to obtain FCM OAuth token")

    return credentials.token


def get_cached_fcm_token() -> str:
    """Return cached OAuth2 token, refreshing when expired/near-expiry."""
    global _cached_token, _cached_expiry

    now = datetime.now(timezone.utc)

    with _token_lock:
        # Refresh 5 minutes before expiry to avoid edge expiration during request
        if _cached_token and _cached_expiry and now < (_cached_expiry - timedelta(minutes=5)):
            return _cached_token

        info = _load_service_account_info()
        credentials = service_account.Credentials.from_service_account_info(info, scopes=_FCM_SCOPES)
        credentials.refresh(Request())

        if not credentials.token:
            raise RuntimeError("Failed to refresh cached FCM OAuth token")

        _cached_token = credentials.token
        _cached_expiry = credentials.expiry or (now + timedelta(hours=1))

        logger.info("FCM OAuth token refreshed", expires_at=_cached_expiry.isoformat())
        return _cached_token
