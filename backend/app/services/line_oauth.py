import httpx
from typing import Optional, Dict
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class LineOAuthService:
    """LINE Login OAuth2 service"""
    
    AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
    TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL = "https://api.line.me/v2/profile"
    VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"
    
    def __init__(self):
        self.channel_id = settings.LINE_CHANNEL_ID
        self.channel_secret = settings.LINE_CHANNEL_SECRET
        self.redirect_uri = settings.LINE_REDIRECT_URI
    
    def get_login_url(self, state: str) -> str:
        """Generate LINE Login URL"""
        params = {
            "response_type": "code",
            "client_id": self.channel_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": "profile openid",
            "nonce": "badminton_app"
        }
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        if not self.channel_id or not self.channel_secret:
            logger.error("LINE OAuth not configured")
            return None
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.channel_id,
            "client_secret": self.channel_secret
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.TOKEN_URL, data=data)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error("LINE token exchange failed", 
                               status=response.status_code, 
                               body=response.text)
                    return None
                    
        except Exception as e:
            logger.error("LINE token exchange error", error=str(e))
            return None
    
    async def get_user_profile(self, access_token: str) -> Optional[Dict]:
        """Get user profile from LINE"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.PROFILE_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error("LINE profile fetch failed",
                               status=response.status_code,
                               body=response.text)
                    return None
                    
        except Exception as e:
            logger.error("LINE profile fetch error", error=str(e))
            return None

# Global instance
line_oauth_service = LineOAuthService()
