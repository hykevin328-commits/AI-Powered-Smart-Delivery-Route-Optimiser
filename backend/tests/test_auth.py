"""
Authentication endpoint tests.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "Alice1234",
        "role": "delivery_partner",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["email"] == "alice@example.com"
    assert data["data"]["role"] == "delivery_partner"
    assert "hashed_password" not in data["data"]


async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "full_name": "Bob Dup",
        "email": "bob@example.com",
        "password": "Bob12345",
        "role": "delivery_partner",
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "ALREADY_EXISTS"


async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "full_name": "Weak User",
        "email": "weak@example.com",
        "password": "password",   # no uppercase, no digit
    })
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Carol Login",
        "email": "carol@example.com",
        "password": "Carol1234",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "carol@example.com",
        "password": "Carol1234",
    })
    assert resp.status_code == 200
    tokens = resp.json()["data"]["tokens"]
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Dave Wrong",
        "email": "dave@example.com",
        "password": "Dave1234",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "dave@example.com",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "INVALID_CREDENTIALS"


async def test_get_profile(client: AsyncClient, partner_token: str):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "delivery_partner"


async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Eve Refresh",
        "email": "eve@example.com",
        "password": "Eve12345",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "eve@example.com",
        "password": "Eve12345",
    })
    refresh_token = login.json()["data"]["tokens"]["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()["data"]


async def test_logout(client: AsyncClient, partner_token: str):
    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert resp.status_code == 200
    assert "logged out" in resp.json()["message"].lower()


async def test_protected_route_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_admin_only_route_as_partner(client: AsyncClient, partner_token: str):
    resp = await client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert resp.status_code == 403
