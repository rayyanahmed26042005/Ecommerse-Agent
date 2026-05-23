"""Chat API with async Celery execution."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.agent.graph import run_shopping_agent
from app.api.auth import get_current_user_optional
from app.core.rate_limit import check_rate_limit
from app.core.redis_client import get_redis
from app.models.schemas import ChatRequest, ChatResponse, TaskStatusResponse
from app.services.chat_service import agent_result_to_chat_response
from app.workers.tasks import run_shopping_task
from app.core.agent_logger import log_event

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    user: str | None = Depends(get_current_user_optional),
):
    await check_rate_limit(request, "ip")
    await check_rate_limit(request, "user", user_id=body.user_id)

    sync = request.query_params.get("sync", "false").lower() == "true"

    log_event("CHAT_REQUEST_RECEIVED", {
        "user_id": body.user_id,
        "message": body.message,
        "feedback": body.feedback,
        "conversation_id": body.conversation_id,
        "sync": sync
    })

    if sync:
        result = await run_shopping_agent(
            body.message,
            feedback=body.feedback,
        )
        chat_response = agent_result_to_chat_response(result)
        log_event("CHAT_SYNC_RESPONSE_SENT", {
            "user_id": body.user_id,
            "summary": chat_response.summary,
            "suggestions_count": len(chat_response.suggestions),
            "status": chat_response.status
        })
        return chat_response

    task_id = str(uuid.uuid4())
    log_event("CHAT_ASYNC_TASK_GENERATED", {
        "task_id": task_id,
        "user_id": body.user_id,
        "message": body.message
    }, task_id=task_id)

    use_async = True
    try:
        redis = await get_redis()
        await redis.ping()
        await redis.setex(
            f"task:{task_id}",
            86400,
            json.dumps({
                "status": "pending",
                "progress": 0,
                "user_id": body.user_id,
                "query": body.message,
            }),
        )
    except Exception as e:
        log_event("CHAT_REDIS_SETUP_FAILED", {"error": str(e)}, task_id=task_id)
        use_async = False

    if use_async:
        try:
            run_shopping_task.apply_async(
                args=[task_id, body.message, body.user_id, body.feedback, None],
                task_id=task_id,
                queue="high_priority",
            )
            log_event("CHAT_ASYNC_TASK_QUEUED", {
                "task_id": task_id,
                "user_id": body.user_id,
                "status": "processing"
            }, task_id=task_id)
            return ChatResponse(
                summary="Your request is being processed by our shopping agent.",
                suggestions=[],
                insights=["Results will be ready shortly."],
                task_id=task_id,
                status="processing",
            )
        except Exception as e:
            log_event("CHAT_CELERY_QUEUE_FAILED", {"error": str(e)}, task_id=task_id)
            use_async = False

    # Fallback: run agent in-process when Celery/Redis unavailable
    log_event("CHAT_FALLBACK_SYNC_TRIGGERED", {"user_id": body.user_id}, task_id=task_id)
    result = await run_shopping_agent(body.message, feedback=body.feedback)
    chat_response = agent_result_to_chat_response(result)
    log_event("CHAT_FALLBACK_SYNC_RESPONSE_SENT", {
        "user_id": body.user_id,
        "summary": chat_response.summary,
        "suggestions_count": len(chat_response.suggestions),
        "status": chat_response.status
    }, task_id=task_id)
    return chat_response


@router.get("/chat/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, request: Request):
    await check_rate_limit(request, "ip")

    try:
        redis = await get_redis()
        raw = await redis.get(f"task:{task_id}")
        if raw:
            data = json.loads(raw)
            status_val = data.get("status", "pending")
            result = data.get("result")
            
            # Log completion or failure of tasks when polled
            if status_val in ("completed", "failed"):
                log_event(f"CHAT_ASYNC_TASK_POLL_{status_val.upper()}", {
                    "task_id": task_id,
                    "status": status_val,
                    "progress": float(data.get("progress", 0)),
                    "error": data.get("error")
                }, task_id=task_id)
                
            return TaskStatusResponse(
                task_id=task_id,
                status=status_val,
                result=ChatResponse.model_validate(result) if result else None,
                error=data.get("error"),
                progress=float(data.get("progress", 0)),
            )
    except Exception as e:
        log_event("CHAT_TASK_POLL_REDIS_FAILED", {"error": str(e)}, task_id=task_id)
        pass

    from celery.result import AsyncResult
    from app.workers.celery_app import celery_app

    ar = AsyncResult(task_id, app=celery_app)
    if ar.state == "PENDING":
        return TaskStatusResponse(task_id=task_id, status="pending", progress=0)
    if ar.state == "STARTED":
        return TaskStatusResponse(task_id=task_id, status="processing", progress=0.5)
    if ar.state == "SUCCESS":
        data = ar.result or {}
        result = data.get("result")
        return TaskStatusResponse(
            task_id=task_id,
            status="completed",
            result=ChatResponse.model_validate(result) if result else None,
            progress=1.0,
        )
    if ar.state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status="failed",
            error=str(ar.result),
            progress=0,
        )

    raise HTTPException(status_code=404, detail="Task not found")
