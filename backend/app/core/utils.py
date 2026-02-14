from datetime import datetime


def utc_now() -> datetime:
    """Return naive UTC datetime for PostgreSQL compatibility."""
    return datetime.utcnow()
