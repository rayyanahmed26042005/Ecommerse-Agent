"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.routes import catalog, chat, health
from app.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.observability import setup_observability
from app.core.redis_client import close_redis
from app.middleware.idempotency import IdempotencyMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    try:
        await init_db()
    except Exception:
        pass  # DB optional for local dev without postgres
    yield
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
    )

    app.add_middleware(GZipMiddleware, minimum_size=500)
    cors_origins = (
        ["*"]
        if settings.debug or settings.environment == "development"
        else settings.cors_origin_list
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "ETag", "X-Idempotent-Replayed"],
    )
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(health.router)
    app.include_router(catalog.router)
    app.include_router(chat.router)

    setup_observability(app)
    return app


app = create_app()
