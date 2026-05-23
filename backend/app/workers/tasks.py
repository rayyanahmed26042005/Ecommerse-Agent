"""Celery background tasks for AI workloads."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.agent.graph import run_shopping_agent
from app.core.logging import get_logger
from app.services.chat_service import agent_result_to_chat_response
from app.workers.celery_app import celery_app
from app.core.agent_logger import log_event

logger = get_logger(__name__)


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


async def _update_task_redis(task_id: str, data: dict[str, Any]) -> None:
    try:
        import json

        from app.core.redis_client import get_redis

        redis = await get_redis()
        await redis.setex(f"task:{task_id}", 86400, json.dumps(data, default=str))
    except Exception as e:
        logger.warning("task_redis_update_failed", task_id=task_id, error=str(e))


@celery_app.task(bind=True, name="app.workers.tasks.run_shopping_task", max_retries=2)
def run_shopping_task(
    self,
    task_id: str,
    query: str,
    user_id: str,
    feedback: str | None = None,
    prior_state: dict | None = None,
) -> dict[str, Any]:
    logger.info("shopping_task_started", task_id=task_id, user_id=user_id)
    
    log_event("CELERY_TASK_STARTED", {
        "task_id": task_id,
        "user_id": user_id,
        "query": query,
        "feedback": feedback,
        "has_prior_state": prior_state is not None
    }, task_id=task_id)

    async def _execute() -> dict[str, Any]:
        log_event("CELERY_TASK_STATUS_UPDATE", {
            "status": "processing",
            "progress": 0.1
        }, task_id=task_id)
        
        await _update_task_redis(
            task_id,
            {"status": "processing", "progress": 0.1, "user_id": user_id},
        )
        
        result = await run_shopping_agent(query, feedback=feedback, prior_state=prior_state)
        
        log_event("CELERY_TASK_STATUS_UPDATE", {
            "status": "processing",
            "progress": 0.8
        }, task_id=task_id)
        
        await _update_task_redis(
            task_id,
            {"status": "processing", "progress": 0.8},
        )
        
        response = agent_result_to_chat_response(result)
        payload = {
            "status": "completed",
            "progress": 1.0,
            "result": response.model_dump(),
        }
        
        log_event("CELERY_TASK_SUCCESS", {
            "status": "completed",
            "progress": 1.0,
            "suggestions_count": len(response.suggestions),
            "summary": response.summary
        }, task_id=task_id)
        
        await _update_task_redis(task_id, payload)
        return payload

    try:
        return _run_async(_execute())
    except Exception as exc:
        logger.error("shopping_task_failed", task_id=task_id, error=str(exc))
        
        log_event("CELERY_TASK_FAILED", {
            "status": "failed",
            "error": str(exc)
        }, task_id=task_id)
        
        _run_async(
            _update_task_redis(
                task_id,
                {"status": "failed", "error": str(exc), "progress": 0},
            )
        )
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="app.workers.tasks.health_ping")
def health_ping() -> str:
    return "ok"
