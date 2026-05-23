"""Async Redis connection pool."""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def redis_health() -> dict[str, Any]:
    try:
        r = await get_redis()
        pong = await r.ping()
        return {"status": "connected" if pong else "error", "ping": pong}
    except Exception as e:
        return {"status": "error", "error": str(e)}
