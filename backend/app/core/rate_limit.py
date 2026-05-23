"""Redis token-bucket rate limiting."""

from __future__ import annotations

import time
from typing import Literal

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.core.logging import get_logger
from app.core.redis_client import get_redis

logger = get_logger(__name__)
LimitType = Literal["user", "ip", "tool"]


async def _token_bucket(
    key: str,
    limit: int,
    window_seconds: int = 60,
) -> tuple[bool, int]:
    """Returns (allowed, remaining)."""
    try:
        redis = await get_redis()
        now = int(time.time())
        bucket_key = f"rl:{key}:{now // window_seconds}"
        current = await redis.incr(bucket_key)
        if current == 1:
            await redis.expire(bucket_key, window_seconds + 1)
        remaining = max(0, limit - current)
        return current <= limit, remaining
    except Exception as e:
        logger.warning("rate_limit_degraded", error=str(e))
        return True, limit


async def check_rate_limit(
    request: Request,
    limit_type: LimitType = "ip",
    user_id: str | None = None,
    tool_name: str | None = None,
) -> None:
    settings = get_settings()
    if limit_type == "user" and user_id:
        key = f"user:{user_id}"
        limit = settings.rate_limit_user_per_minute
    elif limit_type == "tool" and tool_name:
        key = f"tool:{tool_name}"
        limit = settings.rate_limit_tool_per_minute
    else:
        client = request.client.host if request.client else "unknown"
        key = f"ip:{client}"
        limit = settings.rate_limit_ip_per_minute

    allowed, remaining = await _token_bucket(key, limit)
    request.state.rate_limit_remaining = remaining
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )
