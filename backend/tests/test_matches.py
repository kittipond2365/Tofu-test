import pytest


@pytest.mark.asyncio
async def test_create_match_and_update_score(client, auth_headers, second_user_headers, third_user_headers, fourth_user_headers):
    club = await client.post(
        "/api/v1/clubs",
        json={"name": "Match Club", "slug": "match-club", "description": "desc", "is_public": True},
        headers=auth_headers,
    )
    club_id = club.json()["id"]

    await client.post(f"/api/v1/clubs/{club_id}/join", headers=second_user_headers)
    await client.post(f"/api/v1/clubs/{club_id}/join", headers=third_user_headers)
    await client.post(f"/api/v1/clubs/{club_id}/join", headers=fourth_user_headers)

    session = await client.post(
        f"/api/v1/clubs/{club_id}/sessions",
        json={"title": "Match Session", "start_time": "2026-02-20T20:00:00", "max_participants": 8},
        headers=auth_headers,
    )
    session_id = session.json()["id"]
    await client.post(f"/api/v1/sessions/{session_id}/open", headers=auth_headers)

    # Register all players
    for headers in [auth_headers, second_user_headers, third_user_headers, fourth_user_headers]:
        response = await client.post(f"/api/v1/sessions/{session_id}/register", headers=headers)
        assert response.status_code == 200

    # Fetch user IDs
    me = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()["id"]
    u2 = (await client.get("/api/v1/auth/me", headers=second_user_headers)).json()["id"]
    u3 = (await client.get("/api/v1/auth/me", headers=third_user_headers)).json()["id"]
    u4 = (await client.get("/api/v1/auth/me", headers=fourth_user_headers)).json()["id"]

    match = await client.post(
        f"/api/v1/sessions/{session_id}/matches",
        json={
            "court_number": 1,
            "team_a_player_1_id": me,
            "team_a_player_2_id": u2,
            "team_b_player_1_id": u3,
            "team_b_player_2_id": u4,
        },
        headers=auth_headers,
    )
    assert match.status_code == 201
    match_id = match.json()["id"]

    score = await client.patch(
        f"/api/v1/matches/{match_id}/score",
        json={"score": "21-15", "winner_team": "A"},
        headers=auth_headers,
    )
    assert score.status_code == 200
    assert score.json()["winner_team"] == "A"
