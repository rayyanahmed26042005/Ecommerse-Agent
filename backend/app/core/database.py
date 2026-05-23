"""PostgreSQL async session and health checks."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    from app.models import db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def db_health() -> dict[str, Any]:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.scalar()
            tables = await session.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
            )
            table_names = [r[0] for r in tables.fetchall()]
        return {
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "database_url": settings.database_url.split("@")[-1],
            "database_name": settings.database_url.rsplit("/", 1)[-1],
            "connection_status": "connected" if row == 1 else "error",
            "collections": table_names,
        }
    except Exception as e:
        logger.error("db_health_failed", error=str(e))
        return {
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "database_url": "unavailable",
            "database_name": "ecoai",
            "connection_status": f"error: {e}",
            "collections": [],
        }
