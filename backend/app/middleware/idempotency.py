"""X-Idempotency-Key middleware."""

from __future__ import annotations

import hashlib
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.core.logging import get_logger
from app.core.redis_client import get_redis

logger = get_logger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        key = request.headers.get("X-Idempotency-Key")
        if not key:
            return await call_next(request)

        settings = get_settings()
        body = await request.body()
        fingerprint = hashlib.sha256(
            f"{request.method}:{request.url.path}:{body.decode(errors='ignore')}".encode()
        ).hexdigest()
        redis_key = f"idempotency:{key}:{fingerprint}"

        try:
            redis = await get_redis()
            cached = await redis.get(redis_key)
            if cached:
                data = json.loads(cached)
                return JSONResponse(
                    content=data["body"],
                    status_code=data["status"],
                    headers={"X-Idempotent-Replayed": "true"},
                )
        except Exception as e:
            logger.warning("idempotency_check_failed", error=str(e))
            return await call_next(request)

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive)
        response = await call_next(request)

        if response.status_code < 500:
            try:
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk
                try:
                    parsed = json.loads(body_bytes)
                except json.JSONDecodeError:
                    parsed = {"raw": body_bytes.decode(errors="ignore")}
                await redis.setex(
                    redis_key,
                    settings.idempotency_ttl_seconds,
                    json.dumps({"status": response.status_code, "body": parsed}),
                )
                return JSONResponse(
                    content=parsed,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            except Exception as e:
                logger.warning("idempotency_store_failed", error=str(e))

        return response
