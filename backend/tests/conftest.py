import os
import pytest_asyncio
from httpx import AsyncClient

# API Configuration - use env var for CI, fallback to production for local runs
BASE_URL = os.getenv("TEST_TARGET_URL", "https://tofubadminton-backend.onrender.com")
TEST_SECRET = os.getenv("TEST_SECRET", "test-secret-for-ci-only-2024")

# Store created test data for cleanup
test_club_ids = []
test_session_ids = []


@pytest_asyncio.fixture
async def client():
    """HTTP client that calls the production API directly."""
    async with AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/test-login",
        json={"name": "Test Admin"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def second_user_headers(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/test-login",
        json={"name": "Second User"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def third_user_headers(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/test-login",
        json={"name": "Third User"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def fourth_user_headers(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/test-login",
        json={"name": "Fourth User"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(client):
    """Cleanup test data after each test."""
    global test_club_ids, test_session_ids
    
    # Reset tracking lists before test
    test_club_ids = []
    test_session_ids = []
    
    yield
    
    # Cleanup: Delete test sessions and clubs
    # Note: Sessions and clubs are deleted in reverse order of dependencies
    
    # Delete test sessions first (depend on clubs)
    for session_id in test_session_ids:
        try:
            await client.delete(f"/api/v1/sessions/{session_id}")
        except Exception:
            pass  # Ignore cleanup errors
    
    # Delete test clubs
    for club_id in test_club_ids:
        try:
            await client.delete(f"/api/v1/clubs/{club_id}")
        except Exception:
            pass  # Ignore cleanup errors
    
    # Reset tracking lists
    test_club_ids = []
    test_session_ids = []


def track_club(club_id: str):
    """Track a club ID for cleanup."""
    test_club_ids.append(club_id)


def track_session(session_id: str):
    """Track a session ID for cleanup."""
    test_session_ids.append(session_id)
