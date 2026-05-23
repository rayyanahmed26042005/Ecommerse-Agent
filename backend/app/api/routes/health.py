"""Health and database test routes."""

from fastapi import APIRouter

from app.core.circuit_breaker import breaker_status
from app.core.database import db_health
from app.core.qdrant_client import qdrant_health
from app.core.redis_client import redis_health

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {
        "message": "EcoAi Smart Shopping API is running",
        "service": "ecoai-backend",
        "version": "1.0.0",
    }


@router.get("/health")
async def health():
    redis = await redis_health()
    qdrant = await qdrant_health()
    return {
        "status": "ok",
        "redis": redis,
        "qdrant": qdrant,
        "circuit_breakers": breaker_status(),
    }


@router.get("/test")
async def test_database():
    return await db_health()
