"""Three-layer cache: L1 in-process, L2 Redis, cache-aside pattern."""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from typing import Any

from app.config import get_settings
from app.core.logging import get_logger
from app.core.redis_client import get_redis

logger = get_logger(__name__)


class L1Cache:
    """Simple LRU in-process cache."""

    def __init__(self, maxsize: int = 256) -> None:
        self._store: OrderedDict[str, tuple[Any, float, int]] = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, created, ttl = self._store[key]
        if time.time() - created > ttl:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        if key in self._store:
            del self._store[key]
        elif len(self._store) >= self._maxsize:
            self._store.popitem(last=False)
        self._store[key] = (value, time.time(), ttl)

    @property
    def size(self) -> int:
        return len(self._store)


_l1 = L1Cache()


def _cache_key(prefix: str, raw: str) -> str:
    digest = hashlib.sha256(raw.encode()).hexdigest()[:32]
    return f"cache:{prefix}:{digest}"


async def cache_get(prefix: str, raw_key: str) -> Any | None:
    key = _cache_key(prefix, raw_key)
    hit = _l1.get(key)
    if hit is not None:
        logger.debug("cache_l1_hit", prefix=prefix)
        return hit
    try:
        redis = await get_redis()
        data = await redis.get(key)
        if data:
            value = json.loads(data)
            settings = get_settings()
            ttl = getattr(settings, f"cache_ttl_{prefix}", 3600)
            _l1.set(key, value, ttl)
            logger.debug("cache_l2_hit", prefix=prefix)
            return value
    except Exception as e:
        logger.warning("cache_redis_miss", error=str(e))
    return None


async def cache_set(prefix: str, raw_key: str, value: Any) -> None:
    key = _cache_key(prefix, raw_key)
    settings = get_settings()
    ttl = getattr(settings, f"cache_ttl_{prefix}", 3600)
    _l1.set(key, value, ttl)
    try:
        redis = await get_redis()
        await redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning("cache_redis_set_failed", error=str(e))


async def cache_delete_prefix(prefix: str) -> None:
    try:
        redis = await get_redis()
        pattern = f"cache:{prefix}:*"
        async for key in redis.scan_iter(match=pattern, count=100):
            await redis.delete(key)
    except Exception:
        pass


def l1_stats() -> dict[str, int]:
    return {"size": _l1.size}
