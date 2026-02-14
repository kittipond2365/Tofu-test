import redis.asyncio as aioredis
from datetime import datetime, timedelta
from app.core.config import get_settings

settings = get_settings()
redis_client = None

async def get_redis_client():
    global redis_client
    if redis_client is None and settings.REDIS_URL:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

async def store_oauth_state(state: str, ip_address: str, expires_in: int = 600):
    """Store OAuth state in Redis with expiration"""
    r = await get_redis_client()
    if r:
        key = f"oauth_state:{state}"
        await r.setex(key, expires_in, ip_address)
    else:
        # Fallback: don't store (will fail validation, but safe)
        pass

async def validate_oauth_state(state: str, ip_address: str) -> bool:
    """Validate OAuth state from Redis"""
    r = await get_redis_client()
    if not r:
        return False
    
    key = f"oauth_state:{state}"
    stored_ip = await r.get(key)
    
    if stored_ip and stored_ip == ip_address:
        # Delete after successful validation (one-time use)
        await r.delete(key)
        return True
    return False

async def close_oauth_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
