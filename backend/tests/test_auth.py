import os

import pytest


@pytest.mark.asyncio
async def test_test_login_enabled_in_testing(client):
    response = await client.post("/api/v1/auth/test-login", json={"name": "Auth Tester"})
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert "refresh_token" in payload
    assert payload["user"]["display_name"] == "Auth Tester"


@pytest.mark.asyncio
async def test_refresh_token_flow(client):
    login = await client.post("/api/v1/auth/test-login", json={"name": "Refresh Tester"})
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["refresh_token"]


@pytest.mark.asyncio
async def test_test_login_disabled_outside_testing(client, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    response = await client.post("/api/v1/auth/test-login", json={"name": "Blocked"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Test login disabled in production"
    monkeypatch.setenv("ENV", "testing")
