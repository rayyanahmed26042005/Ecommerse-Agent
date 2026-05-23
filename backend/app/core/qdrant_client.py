"""Qdrant vector store for semantic memory (embeddings / RAG)."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_client = None


def get_qdrant():
    global _client
    if _client is None:
        try:
            from qdrant_client import QdrantClient

            settings = get_settings()
            _client = QdrantClient(url=settings.qdrant_url)
        except Exception as e:
            logger.warning("qdrant_unavailable", error=str(e))
            return None
    return _client


async def qdrant_health() -> dict[str, Any]:
    client = get_qdrant()
    if not client:
        return {"status": "unavailable"}
    try:
        collections = client.get_collections()
        return {
            "status": "connected",
            "collections": [c.name for c in collections.collections],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
