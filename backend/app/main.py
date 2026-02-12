from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import get_settings
from app.api import auth, users, clubs, sessions, matches, registrations, stats, notifications
from sqlmodel import SQLModel
from app.models import models
from app.core.database import async_engine
from app.core.redis import get_redis, close_redis
from app.core.config import get_settings
from app.websocket.socket_manager import SocketManager
from app.services.notifications import notification_service

settings = get_settings()
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Badminton Club Management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug endpoint to verify WebSocket mounting
@app.get("/ws-test")
async def ws_test():
    return {"status": "WebSocket mounted at /ws"}


@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    logger.info("Starting up Badminton API", app_name=settings.APP_NAME)
    # Initialize Redis
    await get_redis()
    logger.info("Redis connected")
    
    # Initialize Notification Services
    if settings.FCM_ENABLED and settings.FCM_SERVER_KEY:
        notification_service.configure_push(settings.FCM_SERVER_KEY)
    
    if settings.EMAIL_ENABLED and settings.SMTP_USER:
        notification_service.configure_email(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL
        )
    
    # Create tables (in production, use Alembic migrations instead)
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Badminton API")
    await close_redis()
    await async_engine.dispose()


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    # Check Redis connection
    try:
        r = await get_redis()
        await r.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "database": "connected"
    }


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])
app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["Users"])
app.include_router(clubs.router, prefix=settings.API_V1_PREFIX, tags=["Clubs"])
app.include_router(sessions.router, prefix=settings.API_V1_PREFIX, tags=["Sessions"])
app.include_router(matches.router, prefix=settings.API_V1_PREFIX, tags=["Matches"])
app.include_router(registrations.router, prefix=settings.API_V1_PREFIX, tags=["Registrations"])
app.include_router(stats.router, prefix=settings.API_V1_PREFIX, tags=["Statistics"])
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX, tags=["Notifications"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Create Socket.IO app with FastAPI as fallback
# This allows socket.io to handle /socket.io/ paths and FastAPI to handle everything else
socket_manager = SocketManager(other_app=app)
app = socket_manager.app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
