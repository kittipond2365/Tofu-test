from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import get_settings
from app.api import auth, users, clubs, sessions, matches, registrations, stats, notifications
from sqlmodel import SQLModel
from app.models import models  # noqa: F401
from app.core.database import async_engine
from app.core.redis import get_redis, close_redis
from app.services.notifications import notification_service
from app.websocket.socket_manager import socket_manager

settings = get_settings()
logger = structlog.get_logger()

base_app = FastAPI(
    title=settings.APP_NAME,
    description="Badminton Club Management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

base_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@base_app.get("/ws-test")
async def ws_test():
    return {"status": "WebSocket mounted at /ws"}


@base_app.on_event("startup")
async def startup_event():
    cfg = get_settings()
    logger.info("Starting up Badminton API", app_name=cfg.APP_NAME)
    await get_redis()
    logger.info("Redis connected")

    if cfg.FCM_ENABLED and cfg.FCM_SERVER_KEY:
        notification_service.configure_push(cfg.FCM_SERVER_KEY)

    if cfg.EMAIL_ENABLED and cfg.SMTP_USER:
        notification_service.configure_email(
            cfg.SMTP_HOST,
            cfg.SMTP_PORT,
            cfg.SMTP_USER,
            cfg.SMTP_PASSWORD,
            cfg.SMTP_FROM_EMAIL,
        )

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@base_app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Badminton API")
    await close_redis()
    await async_engine.dispose()


@base_app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
    }


@base_app.get("/health")
async def health_check():
    try:
        r = await get_redis()
        await r.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return {"status": "healthy", "redis": redis_status, "database": "connected"}


base_app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])
base_app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["Users"])
base_app.include_router(clubs.router, prefix=settings.API_V1_PREFIX, tags=["Clubs"])
base_app.include_router(sessions.router, prefix=settings.API_V1_PREFIX, tags=["Sessions"])
base_app.include_router(matches.router, prefix=settings.API_V1_PREFIX, tags=["Matches"])
base_app.include_router(registrations.router, prefix=settings.API_V1_PREFIX, tags=["Registrations"])
base_app.include_router(stats.router, prefix=settings.API_V1_PREFIX, tags=["Statistics"])
base_app.include_router(notifications.router, prefix=settings.API_V1_PREFIX, tags=["Notifications"])


@base_app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Use shared singleton socket_manager instance from websocket module
socket_manager.app.other_asgi_app = base_app
app = socket_manager.app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
