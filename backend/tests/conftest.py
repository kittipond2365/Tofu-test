import os
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel

# Must be set before importing app modules
TEST_DB_PATH = Path(__file__).parent / "test.db"
os.environ.setdefault("ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-and-local-123456")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.core.database import async_engine
from app.main import base_app
from app.models import models  # noqa: F401
import app.api.clubs as clubs_api

app = base_app  # Use base_app directly for testing (without socketio wrapper)


@pytest_asyncio.fixture(autouse=True)
async def reset_db(monkeypatch):
    async def _noop_cache_delete_pattern(_: str):
        return None

    monkeypatch.setattr(clubs_api, "cache_delete_pattern", _noop_cache_delete_pattern)

    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    response = await client.post("/api/v1/auth/test-login", json={"name": "Test Admin"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_user_headers(client: AsyncClient):
    response = await client.post("/api/v1/auth/test-login", json={"name": "Second User"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def third_user_headers(client: AsyncClient):
    response = await client.post("/api/v1/auth/test-login", json={"name": "Third User"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def fourth_user_headers(client: AsyncClient):
    response = await client.post("/api/v1/auth/test-login", json={"name": "Fourth User"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
