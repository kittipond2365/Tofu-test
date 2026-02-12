from typing import Dict, Set
from app.core.redis import get_redis

class RedisSessionManager:
    """Manage WebSocket sessions using Redis"""
    
    async def add_user_to_room(self, user_id: str, room: str):
        """Add user to a room"""
        r = await get_redis()
        await r.sadd(f"room:{room}", user_id)
        await r.sadd(f"user_rooms:{user_id}", room)
    
    async def remove_user_from_room(self, user_id: str, room: str):
        """Remove user from a room"""
        r = await get_redis()
        await r.srem(f"room:{room}", user_id)
        await r.srem(f"user_rooms:{user_id}", room)
    
    async def get_room_users(self, room: str) -> Set[str]:
        """Get all users in a room"""
        r = await get_redis()
        users = await r.smembers(f"room:{room}")
        return users
    
    async def get_user_rooms(self, user_id: str) -> Set[str]:
        """Get all rooms a user is in"""
        r = await get_redis()
        rooms = await r.smembers(f"user_rooms:{user_id}")
        return rooms
    
    async def set_user_online(self, user_id: str, socket_id: str):
        """Mark user as online"""
        r = await get_redis()
        await r.setex(f"online:{user_id}", 3600, socket_id)  # 1 hour expiry
    
    async def set_user_offline(self, user_id: str):
        """Mark user as offline"""
        r = await get_redis()
        await r.delete(f"online:{user_id}")
        # Also remove from all rooms
        rooms = await self.get_user_rooms(user_id)
        for room in rooms:
            await self.remove_user_from_room(user_id, room)
        await r.delete(f"user_rooms:{user_id}")
    
    async def is_user_online(self, user_id: str) -> bool:
        """Check if user is online"""
        r = await get_redis()
        exists = await r.exists(f"online:{user_id}")
        return bool(exists)
    
    async def get_online_users(self) -> Set[str]:
        """Get all online users"""
        r = await get_redis()
        keys = await r.keys("online:*")
        users = {key.replace("online:", "") for key in keys}
        return users

# Global instance
session_manager = RedisSessionManager()
