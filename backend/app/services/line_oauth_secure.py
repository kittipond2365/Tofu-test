"""
Enhanced LINE OAuth service with better error handling and logging.
"""
import httpx
from typing import Optional, Dict
import structlog

from app.core.config_secure import get_settings

logger = structlog.get_logger()


class LineOAuthService:
    """LINE Login OAuth2 service with enhanced security"""
    
    AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
    TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL = "https://api.line.me/v2/profile"
    VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"
    
    def __init__(self):
        self._settings = None
    
    @property
    def settings(self):
        if self._settings is None:
            self._settings = get_settings()
        return self._settings
    
    def get_login_url(self, state: str) -> str:
        """Generate LINE Login URL with CSRF protection state"""
        if not self.settings.LINE_CHANNEL_ID:
            raise ValueError("LINE_CHANNEL_ID not configured")
        
        params = {
            "response_type": "code",
            "client_id": self.settings.LINE_CHANNEL_ID,
            "redirect_uri": self.settings.LINE_REDIRECT_URI,
            "state": state,
            "scope": "profile openid",
            "nonce": "badminton_app"
        }
        
        # Build query string manually to ensure proper encoding
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        if not self.settings.LINE_CHANNEL_ID or not self.settings.LINE_CHANNEL_SECRET:
            logger.error("LINE OAuth not configured - missing channel ID or secret")
            return None
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.LINE_REDIRECT_URI,
            "client_id": self.settings.LINE_CHANNEL_ID,
            "client_secret": self.settings.LINE_CHANNEL_SECRET
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.TOKEN_URL, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("LINE token exchange successful")
                    return result
                elif response.status_code == 400:
                    error_data = response.json()
                    logger.error(
                        "LINE token exchange failed - bad request",
                        error=error_data.get("error"),
                        description=error_data.get("error_description")
                    )
                    return None
                else:
                    logger.error(
                        "LINE token exchange failed",
                        status=response.status_code,
                        body=response.text
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.error("LINE token exchange timeout")
            return None
        except httpx.RequestError as e:
            logger.error("LINE token exchange request error", error=str(e))
            return None
        except Exception as e:
            logger.error("LINE token exchange unexpected error", error=str(e))
            return None
    
    async def get_user_profile(self, access_token: str) -> Optional[Dict]:
        """Get user profile from LINE API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.PROFILE_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("LINE profile fetch failed - invalid access token")
                    return None
                else:
                    logger.error(
                        "LINE profile fetch failed",
                        status=response.status_code,
                        body=response.text
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.error("LINE profile fetch timeout")
            return None
        except httpx.RequestError as e:
            logger.error("LINE profile fetch request error", error=str(e))
            return None
        except Exception as e:
            logger.error("LINE profile fetch unexpected error", error=str(e))
            return None
    
    async def verify_access_token(self, access_token: str) -> Optional[Dict]:
        """Verify access token validity"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.VERIFY_URL,
                    params={"access_token": access_token}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        "LINE token verification failed",
                        status=response.status_code
                    )
                    return None
                    
        except Exception as e:
            logger.error("LINE token verification error", error=str(e))
            return None


# Global instance with lazy initialization
_line_oauth_service: Optional[LineOAuthService] = None


def get_line_oauth_service() -> LineOAuthService:
    """Get or create LINE OAuth service instance"""
    global _line_oauth_service
    if _line_oauth_service is None:
        _line_oauth_service = LineOAuthService()
    return _line_oauth_service


# Backwards compatibility
line_oauth_service = get_line_oauth_service()
