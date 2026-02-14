import pytest


@pytest.mark.asyncio
async def test_create_and_list_clubs(client, auth_headers):
    create = await client.post(
        "/api/v1/clubs",
        json={"name": "Test Club", "slug": "test-club", "description": "desc", "is_public": True},
        headers=auth_headers,
    )
    assert create.status_code == 201

    listed = await client.get("/api/v1/clubs", headers=auth_headers)
    assert listed.status_code == 200
    clubs = listed.json()
    assert len(clubs) == 1
    assert clubs[0]["slug"] == "test-club"


@pytest.mark.asyncio
async def test_join_public_club(client, auth_headers, second_user_headers):
    club = await client.post(
        "/api/v1/clubs",
        json={"name": "Joinable Club", "slug": "joinable-club", "description": "desc", "is_public": True},
        headers=auth_headers,
    )
    club_id = club.json()["id"]

    join = await client.post(f"/api/v1/clubs/{club_id}/join", headers=second_user_headers)
    assert join.status_code == 200
    assert join.json()["message"] == "Successfully joined club"

    details = await client.get(f"/api/v1/clubs/{club_id}", headers=second_user_headers)
    assert details.status_code == 200
    assert details.json()["member_count"] == 2
