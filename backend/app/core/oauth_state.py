"""
Simple in-memory state storage for LINE OAuth (fallback when Redis unavailable)
"""
import time
from typing import Optional, Dict
import threading

# Thread-safe storage
_state_store: Dict[str, tuple] = {}
_lock = threading.Lock()


async def store_oauth_state(state: str, client_ip: str, expire: int = 300) -> bool:
    """Store OAuth state in memory with expiry"""
    try:
        with _lock:
            expiry_time = time.time() + expire
            _state_store[state] = (client_ip, expiry_time)
        return True
    except Exception:
        return False


async def get_oauth_state(state: str) -> Optional[str]:
    """Get and delete OAuth state if valid"""
    try:
        with _lock:
            if state not in _state_store:
                return None
            
            client_ip, expiry_time = _state_store[state]
            
            # Check if expired
            if time.time() > expiry_time:
                del _state_store[state]
                return None
            
            # Delete after use (one-time)
            del _state_store[state]
            return client_ip
    except Exception:
        return None


async def delete_oauth_state(state: str) -> None:
    """Delete OAuth state"""
    try:
        with _lock:
            _state_store.pop(state, None)
    except Exception:
        pass
