"""Chat service: maps agent output to frontend API contract."""

from __future__ import annotations

from typing import Any

from app.models.schemas import ChatResponse, ProductSuggestion


def agent_result_to_chat_response(result: dict[str, Any]) -> ChatResponse:
    suggestions_raw = result.get("final_recommendations", [])
    suggestions = [ProductSuggestion.model_validate(s) for s in suggestions_raw]
    insights = result.get("insights", [])
    if isinstance(insights, str):
        insights = [insights]
    return ChatResponse(
        summary=result.get("reasoning") or "Top options based on value, reliability, and reviews.",
        suggestions=suggestions,
        insights=insights or [
            "Compared price fit, community sentiment, and availability.",
            "Best retailer prices are highlighted on each card.",
        ],
        reasoning=result.get("reasoning"),
        status="completed",
    )
