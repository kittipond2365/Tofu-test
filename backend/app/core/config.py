from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
from pydantic import Field


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Badminton Club Management"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database - Store raw URL from env
    DATABASE_URL_RAW: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/badminton_db",
        alias="DATABASE_URL"
    )
    
    @property
    def DATABASE_URL(self) -> str:
        """URL for async operations (asyncpg)"""
        url = self.DATABASE_URL_RAW
        # Convert postgres:// or postgresql:// to postgresql+asyncpg://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """URL for sync operations (alembic, direct SQL)"""
        url = self.DATABASE_URL_RAW
        # Convert to postgresql:// (no +asyncpg)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        elif url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS - comma-separated string, parsed manually
    CORS_ORIGINS_STR: str = "http://localhost:3000,http://localhost:3001,https://tofubadminton-frontend.onrender.com"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]
    
    # LINE OAuth (Login)
    LINE_CHANNEL_ID: Optional[str] = None
    LINE_CHANNEL_SECRET: Optional[str] = None
    LINE_REDIRECT_URI: str = "https://tofubadminton-frontend.onrender.com/auth/line/callback"
    
    # Notifications
    FCM_ENABLED: bool = False
    FCM_SERVER_KEY: Optional[str] = None
    
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
