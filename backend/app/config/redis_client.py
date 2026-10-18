"""
Redis client singleton using the redis-py async interface.
Used for caching traffic data, route results, and token blacklisting.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config.settings import settings

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return (and lazily create) the shared async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


# ── Helper utilities ──────────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Serialize value to JSON and store with TTL (seconds)."""
    client = await get_redis()
    await client.setex(key, ttl, json.dumps(value))


async def cache_get(key: str) -> Optional[Any]:
    """Retrieve and deserialize a cached value, or None if missing."""
    client = await get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_delete(key: str) -> None:
    client = await get_redis()
    await client.delete(key)


async def cache_exists(key: str) -> bool:
    client = await get_redis()
    return bool(await client.exists(key))
