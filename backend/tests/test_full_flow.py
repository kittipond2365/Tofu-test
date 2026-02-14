import pytest
from conftest import track_club, track_session, TEST_SECRET


@pytest.mark.asyncio
async def test_complete_user_journey(client):
    # 1) Login user A
    login_a = await client.post(
        "/api/v1/auth/test-login",
        json={"name": "User A"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    assert login_a.status_code == 200
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2) Create club
    club = await client.post(
        "/api/v1/clubs",
        json={"name": "Journey Club", "slug": "journey-club", "description": "E2E API flow", "is_public": True},
        headers=headers_a,
    )
    assert club.status_code == 201
    club_id = club.json()["id"]
    track_club(club_id)

    # 3) Create session
    session = await client.post(
        f"/api/v1/clubs/{club_id}/sessions",
        json={"title": "Friday Session", "start_time": "2026-02-20T18:00:00", "max_participants": 20},
        headers=headers_a,
    )
    assert session.status_code == 201
    session_id = session.json()["id"]
    track_session(session_id)

    # 4) Open registration
    opened = await client.post(f"/api/v1/sessions/{session_id}/open", headers=headers_a)
    assert opened.status_code == 200

    # 5) Login user B, join club, register session
    login_b = await client.post(
        "/api/v1/auth/test-login",
        json={"name": "User B"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    joined = await client.post(f"/api/v1/clubs/{club_id}/join", headers=headers_b)
    assert joined.status_code == 200

    registered = await client.post(f"/api/v1/sessions/{session_id}/register", headers=headers_b)
    assert registered.status_code == 200
    assert registered.json()["status"] in ["confirmed", "waitlisted"]

    # 6) Verify registrations list
    registrations = await client.get(f"/api/v1/sessions/{session_id}/registrations", headers=headers_a)
    assert registrations.status_code == 200
    assert len(registrations.json()) >= 1
