import functools
import json
from typing import Callable, TypeVar
from app.core.redis import cache_get, cache_set, cache_delete, cache_delete_pattern

T = TypeVar('T')

def cache_response(prefix: str, expire: int = 300):
    """Decorator to cache API response"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = await cache_get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Call original function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_set(cache_key, json.dumps(result, default=str), expire)
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Decorator to invalidate cache after function call"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await cache_delete_pattern(pattern)
            return result
        return wrapper
    return decorator
