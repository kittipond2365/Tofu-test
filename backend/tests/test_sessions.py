import pytest
from conftest import track_club, track_session


@pytest.mark.asyncio
async def test_create_session_and_open_registration(client, auth_headers):
    club = await client.post(
        "/api/v1/clubs",
        json={"name": "Session Club", "slug": "session-club", "description": "desc", "is_public": True},
        headers=auth_headers,
    )
    assert club.status_code == 201
    club_id = club.json()["id"]
    track_club(club_id)

    session = await client.post(
        f"/api/v1/clubs/{club_id}/sessions",
        json={"title": "Friday Session", "start_time": "2026-02-20T18:00:00", "max_participants": 4},
        headers=auth_headers,
    )
    assert session.status_code == 201
    session_id = session.json()["id"]
    track_session(session_id)

    opened = await client.post(f"/api/v1/sessions/{session_id}/open", headers=auth_headers)
    assert opened.status_code == 200
    assert opened.json()["message"] == "Registration opened"


@pytest.mark.asyncio
async def test_register_for_open_session(client, auth_headers, second_user_headers):
    club = await client.post(
        "/api/v1/clubs",
        json={"name": "Register Club", "slug": "register-club", "description": "desc", "is_public": True},
        headers=auth_headers,
    )
    assert club.status_code == 201
    club_id = club.json()["id"]
    track_club(club_id)

    await client.post(f"/api/v1/clubs/{club_id}/join", headers=second_user_headers)

    session = await client.post(
        f"/api/v1/clubs/{club_id}/sessions",
        json={"title": "Open Session", "start_time": "2026-02-20T19:00:00", "max_participants": 4},
        headers=auth_headers,
    )
    assert session.status_code == 201
    session_id = session.json()["id"]
    track_session(session_id)

    await client.post(f"/api/v1/sessions/{session_id}/open", headers=auth_headers)

    reg = await client.post(f"/api/v1/sessions/{session_id}/register", headers=second_user_headers)
    assert reg.status_code == 200
    assert reg.json()["status"] in ["confirmed", "waitlisted"]
