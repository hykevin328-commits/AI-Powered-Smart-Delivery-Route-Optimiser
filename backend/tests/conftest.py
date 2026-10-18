"""
Pytest configuration and shared fixtures.

Uses an in-memory SQLite engine for tests (no real DB required).
Override DATABASE_URL in the environment to run against a real PostgreSQL instance.
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# ── Override settings before app import ──────────────────────────────────────
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum!")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SYNC_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("APP_ENV", "testing")

from app.config.database import Base, get_db
from app.main import create_app

# ── Test database engine ──────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test DB session that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client with the test database wired in."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── Helper fixtures ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    """Register an admin user and return the access token."""
    resp = await client.post("/api/v1/auth/register", json={
        "full_name": "Test Admin",
        "email": "admin@test.com",
        "password": "Admin1234",
        "role": "admin",
    })
    assert resp.status_code == 201
    login = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin1234",
    })
    return login.json()["data"]["tokens"]["access_token"]


@pytest_asyncio.fixture
async def partner_token(client: AsyncClient) -> str:
    """Register a delivery partner and return the access token."""
    resp = await client.post("/api/v1/auth/register", json={
        "full_name": "Test Partner",
        "email": "partner@test.com",
        "password": "Partner1234",
        "role": "delivery_partner",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "partner@test.com",
        "password": "Partner1234",
    })
    return login.json()["data"]["tokens"]["access_token"]
