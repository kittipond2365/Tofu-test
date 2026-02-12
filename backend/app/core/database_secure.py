"""
Enhanced database configuration with connection pooling and SSL support.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import re

from app.core.config_secure import get_settings

settings = get_settings()


def convert_to_async_url(url: str) -> str:
    """
    Convert PostgreSQL URL to async format.
    Render and other providers give: postgresql://
    SQLAlchemy async needs: postgresql+asyncpg://
    """
    if not url:
        raise ValueError("DATABASE_URL is empty or not set. Please check your environment variables.")
    
    url = url.strip()
    
    # If already has async driver, return as-is
    if "+asyncpg" in url or "+aiopg" in url:
        return url
    
    # Convert postgresql:// to postgresql+asyncpg://
    # Handle both postgresql:// and postgres://
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    # If URL doesn't start with expected prefix, raise error
    raise ValueError(
        f"DATABASE_URL must start with 'postgresql://' or 'postgres://'. "
        f"Current URL starts with: {url[:20]}..."
    )


def convert_to_sync_url(url: str) -> str:
    """
    Convert PostgreSQL URL to sync format for Alembic.
    Remove async driver if present, ensure sync driver.
    """
    if not url:
        return url
    
    # Remove async driver if present
    url = re.sub(r'postgresql\+asyncpg://', 'postgresql://', url)
    url = re.sub(r'postgresql\+aiopg://', 'postgresql://', url)
    
    # For sync, we can use default postgresql:// or add psycopg2
    # Using default postgresql:// which uses psycopg2 if available
    return url


# Convert URLs to appropriate formats
# Render provides: postgresql://user:pass@host/db
# Async needs: postgresql+asyncpg://user:pass@host/db
ASYNC_DATABASE_URL = convert_to_async_url(settings.DATABASE_URL)
SYNC_DATABASE_URL = convert_to_sync_url(settings.DATABASE_URL_SYNC or settings.DATABASE_URL)

# Debug logging (remove in production)
import os
if os.getenv("DEBUG") == "true":
    print(f"DEBUG: Original DATABASE_URL = {settings.DATABASE_URL[:30]}...")
    print(f"DEBUG: Async URL = {ASYNC_DATABASE_URL[:30]}...")
    print(f"DEBUG: Sync URL = {SYNC_DATABASE_URL[:30]}...")

# Async engine for FastAPI with connection pooling
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # Connection pooling settings
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before using
    # SSL for production
    connect_args={
        "ssl": settings.ENVIRONMENT == "production"
    } if settings.ENVIRONMENT == "production" else {}
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=sync_engine)


async def get_db():
    """
    Dependency for getting async database sessions.
    Handles commit/rollback automatically.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_no_commit():
    """
    Get database session without automatic commit.
    Use for read-only operations or when manual commit is needed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> dict:
    """
    Perform health check on database connection.
    Returns status dictionary.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to verify connection
            result = await session.execute(text("SELECT 1"))
            await result.scalar()
            
            # Get connection info
            result = await session.execute(text(
                "SELECT version(), current_database(), current_user"
            ))
            version, database, user = result.fetchone()
            
            return {
                "status": "connected",
                "database": database,
                "user": user,
                "version": version.split()[0] if version else "unknown"
            }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e)
        }


async def get_database_stats() -> dict:
    """
    Get database statistics for monitoring.
    """
    try:
        async with AsyncSessionLocal() as session:
            stats = {}
            
            # Connection count
            result = await session.execute(text(
                """
                SELECT count(*) as connections 
                FROM pg_stat_activity 
                WHERE datname = current_database()
                """
            ))
            stats["active_connections"] = result.scalar()
            
            # Table statistics
            result = await session.execute(text(
                """
                SELECT 
                    schemaname,
                    tablename,
                    n_live_tup as row_count
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 10
                """
            ))
            stats["tables"] = [
                {"schema": r[0], "table": r[1], "rows": r[2]}
                for r in result.fetchall()
            ]
            
            return stats
    except Exception as e:
        return {"error": str(e)}
