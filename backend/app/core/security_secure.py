"""
Enhanced security module with JWT improvements, rate limiting, and audit logging.
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import uuid
import secrets
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Use the secure config
from app.core.config_secure import get_settings, Settings

ph = PasswordHasher()
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using Argon2"""
    if not hashed_password:
        return False
    try:
        ph.verify(hashed_password, plain_password)
        # Rehash if needed (Argon2 parameters may have changed)
        if ph.check_needs_rehash(hashed_password):
            # In production, you should update the stored hash
            pass
        return True
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    """Hash password using Argon2"""
    return ph.hash(password)


def create_access_token(
    data: dict,
    settings: Settings = None,
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None
) -> tuple[str, str]:
    """
    Create access token with enhanced security claims.
    Returns (token, jti)
    """
    if settings is None:
        settings = get_settings()
    
    to_encode = data.copy()
    
    # Generate unique token ID for revocation support
    if jti is None:
        jti = str(uuid.uuid4())
    
    # Calculate expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": jti
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt, jti


def create_refresh_token(
    data: dict,
    settings: Settings = None,
    jti: Optional[str] = None
) -> tuple[str, str]:
    """
    Create refresh token with enhanced security claims.
    Returns (token, jti)
    """
    if settings is None:
        settings = get_settings()
    
    to_encode = data.copy()
    
    if jti is None:
        jti = str(uuid.uuid4())
    
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": jti
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt, jti


def decode_token(
    token: str, 
    settings: Settings = None,
    token_type: str = "access"
) -> Optional[dict]:
    """
    Decode and validate JWT token with full security checks.
    """
    if settings is None:
        settings = get_settings()
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE
        )
        
        # Validate token type
        if payload.get("type") != token_type:
            return None
        
        return payload
    except JWTError:
        return None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings)
) -> str:
    """
    Extract and validate user ID from JWT token.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ไม่ได้รับการยืนยันตัวตน - กรุณาเข้าสู่ระบบ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(credentials.credentials, settings, token_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="โทเค็นไม่ถูกต้องหรือหมดอายุ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="โทเค็นไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Check if token is revoked (would need Redis lookup)
    # jti = payload.get("jti")
    # if await is_token_revoked(jti):
    #     raise HTTPException(...)
    
    return user_id


async def get_optional_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings)
) -> Optional[str]:
    """Optional authentication - returns user_id or None"""
    if not credentials:
        return None
    
    payload = decode_token(credentials.credentials, settings, token_type="access")
    if payload is None:
        return None
    
    return payload.get("sub")


# ==================== Rate Limiting ====================

class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
    
    def is_allowed(self, key: str, max_requests: int, window: int) -> tuple[bool, int, int]:
        """
        Check if request is allowed.
        Returns (allowed, remaining, retry_after)
        """
        now = datetime.utcnow().timestamp()
        
        if key not in self._storage:
            self._storage[key] = {"count": 1, "reset_at": now + window}
            return True, max_requests - 1, 0
        
        entry = self._storage[key]
        
        # Reset if window expired
        if now > entry["reset_at"]:
            self._storage[key] = {"count": 1, "reset_at": now + window}
            return True, max_requests - 1, 0
        
        # Check limit
        if entry["count"] >= max_requests:
            retry_after = int(entry["reset_at"] - now)
            return False, 0, retry_after
        
        entry["count"] += 1
        return True, max_requests - entry["count"], 0
    
    def cleanup(self):
        """Remove expired entries"""
        now = datetime.utcnow().timestamp()
        expired = [k for k, v in self._storage.items() if now > v["reset_at"]]
        for k in expired:
            del self._storage[k]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _rate_limiter


async def check_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> None:
    """
    Rate limiting dependency for FastAPI.
    Use as: dependencies=[Depends(check_rate_limit)]
    """
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    # Determine rate limit based on endpoint
    path = request.url.path
    
    # Stricter limits for auth endpoints
    if "/auth/" in path and path.endswith(("/login", "/register", "/refresh")):
        max_requests = settings.AUTH_RATE_LIMIT_REQUESTS
        window = settings.AUTH_RATE_LIMIT_WINDOW
    else:
        max_requests = settings.RATE_LIMIT_REQUESTS
        window = settings.RATE_LIMIT_WINDOW
    
    # Use IP + path as key
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{path}"
    
    allowed, remaining, retry_after = _rate_limiter.is_allowed(key, max_requests, window)
    
    # Add rate limit headers
    request.state.rate_limit_remaining = remaining
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"คำขอมากเกินไป กรุณาลองใหม่ในอีก {retry_after} วินาที",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(datetime.utcnow().timestamp() + retry_after))
            }
        )


# ==================== Audit Logging ====================

import structlog

audit_logger = structlog.get_logger("audit")


def audit_log(
    action: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Log audit event for security tracking.
    """
    event = {
        "event_type": "audit",
        "action": action,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp": datetime.utcnow().isoformat()
    }
    audit_logger.info("audit_event", **event)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)
