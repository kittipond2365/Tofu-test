import pytest_asyncio


@pytest_asyncio.fixture
async def test_user(client):
    response = await client.post("/api/v1/auth/test-login", json={"name": "Fixture User", "line_user_id": "test_001"})
    assert response.status_code == 200
    return response.json()["user"]


@pytest_asyncio.fixture
async def test_club(client, auth_headers):
    response = await client.post(
        "/api/v1/clubs",
        json={
            "name": "Fixture Club",
            "slug": "fixture-club",
            "description": "Fixture club for tests",
            "is_public": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_session(client, auth_headers, test_club):
    response = await client.post(
        f"/api/v1/clubs/{test_club['id']}/sessions",
        json={
            "title": "Fixture Session",
            "start_time": "2026-02-20T18:00:00",
            "max_participants": 20,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()
