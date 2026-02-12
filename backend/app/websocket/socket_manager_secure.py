"""
Enhanced WebSocket manager with authentication and security.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Callable
import socketio
from fastapi import HTTPException

from app.core.config_secure import get_settings
from app.core.security_secure import decode_token

settings = get_settings()


class SocketManager:
    def __init__(self, other_app=None, cors_origins=None) -> None:
        # Configure CORS - use specific origins in production
        if cors_origins is None:
            cors_origins = settings.CORS_ORIGINS if settings.ENVIRONMENT == "development" else []
        
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=cors_origins if settings.ENVIRONMENT == "development" else settings.CORS_ORIGINS,
            # Enable authentication
            auth=True,
            # Ping settings for connection health
            ping_timeout=60,
            ping_interval=25,
            # Maximum payload size (5MB)
            max_http_buffer_size=5 * 1024 * 1024,
        )
        self.app = socketio.ASGIApp(self.sio, other_asgi_app=other_app)
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle connection with optional authentication"""
            # Get token from auth or query string
            token = None
            if auth and isinstance(auth, dict):
                token = auth.get("token")
            
            # Also check query string
            if not token:
                query_string = environ.get("QUERY_STRING", "")
                params = dict(p.split("=") for p in query_string.split("&") if "=" in p)
                token = params.get("token")
            
            # Validate token if provided
            if token:
                payload = decode_token(token)
                if payload:
                    # Store user info in session
                    await self.sio.save_session(sid, {
                        "user_id": payload.get("sub"),
                        "authenticated": True
                    })
                    return True
            
            # Allow connection but mark as unauthenticated
            await self.sio.save_session(sid, {
                "user_id": None,
                "authenticated": False
            })
            return True
        
        @self.sio.event
        async def disconnect(sid):
            """Handle disconnection"""
            pass
        
        @self.sio.event
        async def authenticate(sid, data):
            """Authenticate existing connection"""
            token = data.get("token") if isinstance(data, dict) else None
            if not token:
                return {"success": False, "error": "No token provided"}
            
            payload = decode_token(token)
            if payload:
                await self.sio.save_session(sid, {
                    "user_id": payload.get("sub"),
                    "authenticated": True
                })
                return {"success": True}
            
            return {"success": False, "error": "Invalid token"}
        
        @self.sio.event
        async def join_session(sid, data):
            """Join a session room (requires authentication)"""
            session = await self.sio.get_session(sid)
            if not session or not session.get("authenticated"):
                return {"error": "Not authenticated"}
            
            session_id = (data or {}).get("session_id")
            if session_id:
                await self.sio.enter_room(sid, f"session:{session_id}")
                return {"success": True, "session_id": session_id}
            return {"error": "No session_id provided"}
        
        @self.sio.event
        async def leave_session(sid, data):
            """Leave a session room"""
            session_id = (data or {}).get("session_id")
            if session_id:
                await self.sio.leave_room(sid, f"session:{session_id}")
                return {"success": True}
            return {"error": "No session_id provided"}
        
        @self.sio.event
        async def join_club(sid, data):
            """Join a club room (requires authentication)"""
            session = await self.sio.get_session(sid)
            if not session or not session.get("authenticated"):
                return {"error": "Not authenticated"}
            
            club_id = (data or {}).get("club_id")
            if club_id:
                await self.sio.enter_room(sid, f"club:{club_id}")
                return {"success": True, "club_id": club_id}
            return {"error": "No club_id provided"}
        
        @self.sio.event
        async def leave_club(sid, data):
            """Leave a club room"""
            club_id = (data or {}).get("club_id")
            if club_id:
                await self.sio.leave_room(sid, f"club:{club_id}")
                return {"success": True}
            return {"error": "No club_id provided"}
    
    async def _check_authenticated(self, sid: str) -> bool:
        """Check if socket session is authenticated"""
        session = await self.sio.get_session(sid)
        return session is not None and session.get("authenticated", False)
    
    async def broadcast_registration_update(
        self, 
        session_id: str, 
        payload: Dict[str, Any]
    ) -> None:
        """Broadcast registration update to session room"""
        await self.sio.emit(
            "registration_updated", 
            payload, 
            room=f"session:{session_id}"
        )
    
    async def broadcast_match_started(
        self, 
        session_id: str, 
        payload: Dict[str, Any]
    ) -> None:
        """Broadcast match start to session room"""
        await self.sio.emit(
            "match_started", 
            payload, 
            room=f"session:{session_id}"
        )
    
    async def broadcast_score_update(
        self, 
        session_id: str, 
        payload: Dict[str, Any]
    ) -> None:
        """Broadcast score update to session room"""
        await self.sio.emit(
            "score_updated", 
            payload, 
            room=f"session:{session_id}"
        )
    
    async def broadcast_to_club(
        self,
        club_id: str,
        event: str,
        payload: Dict[str, Any]
    ) -> None:
        """Broadcast message to all club members"""
        await self.sio.emit(
            event,
            payload,
            room=f"club:{club_id}"
        )
    
    async def send_to_user(
        self,
        user_id: str,
        event: str,
        payload: Dict[str, Any]
    ) -> None:
        """Send message to specific user (requires user tracking)"""
        # This would require maintaining a mapping of user_id -> socket_ids
        # For now, broadcast to all and let client filter
        await self.sio.emit(event, payload)


# Global instance - will be initialized with proper CORS in main
socket_manager: Optional[SocketManager] = None
sio: Optional[socketio.AsyncServer] = None
socket_app = None


def initialize_socket_manager(other_app=None):
    """Initialize the socket manager with proper configuration"""
    global socket_manager, sio, socket_app
    socket_manager = SocketManager(other_app=other_app)
    sio = socket_manager.sio
    socket_app = socket_manager.app
    return socket_manager
