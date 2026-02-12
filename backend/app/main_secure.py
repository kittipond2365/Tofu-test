"""
Enhanced FastAPI main application with security hardening.
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
import structlog
import time

from app.core.config_secure import get_settings
from app.api import auth, users, clubs, sessions, matches, registrations, stats, notifications
from app.models import models
from app.core.database_secure import async_engine, check_database_connection
from app.core.redis import get_redis, close_redis
from app.websocket.socket_manager import SocketManager
from app.services.notifications import notification_service
from app.core.security_secure import check_rate_limit

settings = get_settings()
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Badminton Club Management API - Secure",
    version="1.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# ==================== Security Middleware ====================

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware with security checks
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,
)

# Trusted host validation (production only)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "*.vercel.app",
            "*.railway.app",
            "*.onrender.com",
            # Add your custom domain here
        ]
    )

# ==================== Request Middleware ====================

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    if settings.SECURE_HEADERS_ENABLED:
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        
        # HSTS (HTTPS Strict Transport Security)
        if settings.ENVIRONMENT == "production":
            hsts_value = f"max-age={settings.HSTS_MAX_AGE}"
            if settings.HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            if settings.HSTS_PRELOAD:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Content Security Policy
        if settings.CONTENT_SECURITY_POLICY:
            response.headers["Content-Security-Policy"] = settings.CONTENT_SECURITY_POLICY
    
    # Rate limit headers
    if hasattr(request.state, 'rate_limit_remaining'):
        response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
    
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Get client IP (handle proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    request.state.client_ip = client_ip
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=round(process_time * 1000, 2),
        client_ip=client_ip,
        user_agent=request.headers.get("user-agent", "unknown"),
    )
    
    return response


# ==================== Event Handlers ====================

@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    logger.info(
        "Starting up Badminton API",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        version="1.1.0"
    )
    
    # Validate production settings
    if settings.ENVIRONMENT == "production":
        try:
            settings.validate_production_settings()
            logger.info("Production settings validated successfully")
        except ValueError as e:
            logger.error("Production settings validation failed", error=str(e))
            raise
    
    # Initialize Redis
    try:
        await get_redis()
        logger.info("Redis connected")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))
        if settings.ENVIRONMENT == "production":
            raise
    
    # Initialize Notification Services
    if settings.WEB_PUSH_ENABLED and settings.WEB_PUSH_VAPID_PRIVATE_KEY:
        notification_service.configure_web_push(
            settings.WEB_PUSH_VAPID_PUBLIC_KEY,
            settings.WEB_PUSH_VAPID_PRIVATE_KEY,
            settings.WEB_PUSH_VAPID_CLAIMS_EMAIL
        )
        logger.info("Web Push (VAPID) notifications configured")
    
    if settings.EMAIL_ENABLED and settings.SMTP_USER:
        notification_service.configure_email(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL
        )
        logger.info("Email notifications configured")
    
    # Create tables (in production, use Alembic migrations instead)
    if settings.ENVIRONMENT != "production":
        async with async_engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        logger.info("Database tables created")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Badminton API")
    await close_redis()
    await async_engine.dispose()


# ==================== Routes ====================

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.1.0",
        "environment": settings.ENVIRONMENT,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    # Check Redis
    try:
        r = await get_redis()
        await r.ping()
        redis_status = "connected"
        redis_info = await r.info("server")
        redis_version = redis_info.get("redis_version", "unknown")
    except Exception as e:
        redis_status = "disconnected"
        redis_version = None
        logger.warning("Health check: Redis disconnected", error=str(e))
    
    # Check Database
    db_status = await check_database_connection()
    
    # Overall status
    is_healthy = redis_status == "connected" and db_status["status"] == "connected"
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": time.time(),
        "version": "1.1.0",
        "services": {
            "redis": {
                "status": redis_status,
                "version": redis_version
            },
            "database": db_status
        }
    }
    
    status_code = 200 if is_healthy else 503
    return JSONResponse(content=response, status_code=status_code)


@app.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    return {"ready": True}


@app.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"alive": True}


# WebSocket test endpoint
@app.get("/ws-test")
async def ws_test():
    return {"status": "WebSocket mounted at /ws"}


# Include routers with rate limiting
app.include_router(
    auth.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Authentication"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    users.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Users"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    clubs.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Clubs"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    sessions.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Sessions"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    matches.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Matches"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    registrations.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Registrations"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    stats.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Statistics"],
    dependencies=[Depends(check_rate_limit)]
)
app.include_router(
    notifications.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Notifications"],
    dependencies=[Depends(check_rate_limit)]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        client_ip=getattr(request.state, 'client_ip', 'unknown')
    )
    
    # Don't expose internal details in production
    if settings.ENVIRONMENT == "production":
        message = "Internal server error"
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": message,
            "error_code": "INTERNAL_ERROR"
        }
    )


# Create Socket.IO app with FastAPI as fallback
socket_manager = SocketManager(
    other_app=app,
    cors_origins=settings.CORS_ORIGINS if settings.ENVIRONMENT != "production" else None
)
app = socket_manager.app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_secure:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    )
