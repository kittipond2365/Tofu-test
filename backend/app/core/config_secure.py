"""
Enhanced configuration with security validation and production hardening.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
import secrets
import re


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Badminton Club Management"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/badminton_db"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/badminton_db"
    
    # Database Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CONNECTION_TIMEOUT: int = 5
    
    # Security - MUST be set in production
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # JWT Settings
    JWT_ISSUER: str = "badminton-app"
    JWT_AUDIENCE: str = "badminton-api"
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    AUTH_RATE_LIMIT_REQUESTS: int = 5
    AUTH_RATE_LIMIT_WINDOW: int = 300  # 5 minutes
    
    # CORS - comma-separated string, parsed manually
    CORS_ORIGINS_STR: str = "http://localhost:3000,http://localhost:3001"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        origins = [origin.strip() for origin in self.CORS_ORIGINS_STR.split(",") if origin.strip()]
        # Security: Validate no wildcard when credentials enabled
        if self.CORS_ALLOW_CREDENTIALS and "*" in origins:
            raise ValueError("CORS cannot use wildcard '*' when allow_credentials is True")
        return origins
    
    @property
    def CORS_ORIGINS_REGEX(self) -> Optional[str]:
        """Allow regex patterns for subdomains in production"""
        if self.ENVIRONMENT == "production":
            # Allow Vercel preview deployments
            return r"https://.*\.vercel\.app"
        return None
    
    # Security Headers
    SECURE_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = True
    CONTENT_SECURITY_POLICY: Optional[str] = None
    
    # File Upload Limits
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    # LINE OAuth (Login)
    LINE_CHANNEL_ID: Optional[str] = None
    LINE_CHANNEL_SECRET: Optional[str] = None
    LINE_REDIRECT_URI: str = "http://localhost:3000/auth/line/callback"
    LINE_STATE_EXPIRY: int = 600  # 10 minutes
    
    # Notifications
    # Note: We use Web Push VAPID (not Firebase!)
    WEB_PUSH_ENABLED: bool = False
    WEB_PUSH_VAPID_PUBLIC_KEY: Optional[str] = None
    WEB_PUSH_VAPID_PRIVATE_KEY: Optional[str] = None
    WEB_PUSH_VAPID_CLAIMS_EMAIL: Optional[str] = None
    
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_TIMEOUT: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    AUDIT_LOG_ENABLED: bool = True
    
    # Request Limits
    MAX_REQUEST_BODY_SIZE: int = 10 * 1024 * 1024  # 10MB
    REQUEST_TIMEOUT: int = 30  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_production_settings(self):
        """Validate critical settings for production"""
        if self.ENVIRONMENT == "production":
            errors = []
            
            # Check SECRET_KEY strength
            if len(self.SECRET_KEY) < 32:
                errors.append("SECRET_KEY must be at least 32 characters in production")
            
            if self.SECRET_KEY == "your-secret-key-change-in-production":
                errors.append("SECRET_KEY must be changed from default value")
            
            # Check HTTPS for production
            if not self.LINE_REDIRECT_URI.startswith("https://"):
                errors.append("LINE_REDIRECT_URI must use HTTPS in production")
            
            # Check database URL is not localhost in production
            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                errors.append("DATABASE_URL should not point to localhost in production")
            
            # Check Redis is not localhost in production
            if "localhost" in self.REDIS_URL or "127.0.0.1" in self.REDIS_URL:
                errors.append("REDIS_URL should not point to localhost in production")
            
            # Check LINE OAuth credentials
            if not self.LINE_CHANNEL_ID or not self.LINE_CHANNEL_SECRET:
                errors.append("LINE_CHANNEL_ID and LINE_CHANNEL_SECRET must be set in production")
            
            if errors:
                raise ValueError(f"Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    def generate_secure_secret(self) -> str:
        """Generate a cryptographically secure secret key"""
        return secrets.token_urlsafe(64)


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production_settings()
    return settings


def validate_password_strength(password: str, settings: Settings = None) -> tuple[bool, Optional[str]]:
    """
    Validate password strength according to settings.
    Returns (is_valid, error_message)
    """
    if settings is None:
        settings = get_settings()
    
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"รหัสผ่านต้องมีความยาวอย่างน้อย {settings.PASSWORD_MIN_LENGTH} ตัวอักษร"
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "รหัสผ่านต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว"
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "รหัสผ่านต้องมีตัวพิมพ์เล็กอย่างน้อย 1 ตัว"
    
    if settings.PASSWORD_REQUIRE_DIGITS and not re.search(r'\d', password):
        return False, "รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว"
    
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\\/\-_=+]', password):
        return False, "รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (!@#$%^&* etc.)"
    
    return True, None
