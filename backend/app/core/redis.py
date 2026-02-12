import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()

# Redis async client
redis_client: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    """Get Redis async client"""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

# Cache helpers
async def cache_get(key: str) -> str | None:
    """Get value from cache"""
    r = await get_redis()
    return await r.get(key)

async def cache_set(key: str, value: str, expire: int = 300):
    """Set value to cache with expiration (default 5 minutes)"""
    r = await get_redis()
    await r.setex(key, expire, value)

async def cache_delete(key: str):
    """Delete key from cache"""
    r = await get_redis()
    await r.delete(key)

async def cache_delete_pattern(pattern: str):
    """Delete keys matching pattern"""
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)
