"""
Async SQLAlchemy engine, session factory, and dependency injection helper.
Uses asyncpg driver for full async support with Supabase PostgreSQL.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config.settings import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# NullPool is recommended for serverless / short-lived processes (Supabase).
# For dedicated servers, swap to AsyncAdaptedQueuePool with pool_size tuning.
_is_testing = settings.APP_ENV == "testing"
_db_url = settings.DATABASE_URL or "sqlite+aiosqlite:///./dev.db"

_engine_kwargs: dict = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
}
if _is_testing:
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_size"]    = 10
    _engine_kwargs["max_overflow"] = 20

engine = create_async_engine(_db_url, **_engine_kwargs)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Base model ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a SQLAlchemy async session and guarantees cleanup.
    Use as a FastAPI dependency: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Context-manager version (for non-route code) ──────────────────────────────
@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
