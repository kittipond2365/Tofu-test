from __future__ import annotations

from typing import Any, Dict

import socketio


class SocketManager:
    def __init__(self, other_app=None) -> None:
        self.sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
        self.app = socketio.ASGIApp(self.sio, other_asgi_app=other_app)
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.sio.event
        async def connect(sid, environ, auth):
            return True

        @self.sio.event
        async def disconnect(sid):
            return None

        @self.sio.event
        async def join_session(sid, data):
            session_id = (data or {}).get("session_id")
            if session_id:
                await self.sio.enter_room(sid, f"session:{session_id}")

        @self.sio.event
        async def leave_session(sid, data):
            session_id = (data or {}).get("session_id")
            if session_id:
                await self.sio.leave_room(sid, f"session:{session_id}")

        @self.sio.event
        async def join_club(sid, data):
            club_id = (data or {}).get("club_id")
            if club_id:
                await self.sio.enter_room(sid, f"club:{club_id}")

        @self.sio.event
        async def leave_club(sid, data):
            club_id = (data or {}).get("club_id")
            if club_id:
                await self.sio.leave_room(sid, f"club:{club_id}")

    async def broadcast_registration_update(self, session_id: str, payload: Dict[str, Any]) -> None:
        await self.sio.emit("registration_updated", payload, room=f"session:{session_id}")

    async def broadcast_match_started(self, session_id: str, payload: Dict[str, Any]) -> None:
        await self.sio.emit("match_started", payload, room=f"session:{session_id}")

    async def broadcast_score_update(self, session_id: str, payload: Dict[str, Any]) -> None:
        await self.sio.emit("score_updated", payload, room=f"session:{session_id}")


socket_manager = SocketManager()
sio = socket_manager.sio
socket_app = socket_manager.app
