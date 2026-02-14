import os

import pytest


# Test secret for protection layer 2
TEST_SECRET = "test-secret-for-ci-only-2024"


@pytest.mark.asyncio
async def test_test_login_enabled_in_testing(client):
    response = await client.post(
        "/api/v1/auth/test-login", 
        json={"name": "Auth Tester"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert "refresh_token" in payload
    assert payload["user"]["display_name"] == "Auth Tester"


@pytest.mark.asyncio
async def test_refresh_token_flow(client):
    login = await client.post(
        "/api/v1/auth/test-login", 
        json={"name": "Refresh Tester"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]


@pytest.mark.asyncio
async def test_test_login_disabled_without_secret(client):
    response = await client.post("/api/v1/auth/test-login", json={"name": "Blocked"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_test_login_disabled_outside_testing(client, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    response = await client.post(
        "/api/v1/auth/test-login", 
        json={"name": "Blocked"},
        headers={"X-Test-Secret": TEST_SECRET}
    )
    assert response.status_code == 403
    assert "Test login disabled" in response.json()["detail"]
    monkeypatch.setenv("ENV", "testing")
