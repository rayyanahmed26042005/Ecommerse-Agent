"""ReAct orchestrator: decides next tool based on state."""

from __future__ import annotations

import json

from app.models.schemas import OrchestratorDecision, ShoppingState
from app.services.llm import get_llm


def format_state_for_llm(state: ShoppingState) -> str:
    plan = state.get("shopping_plan", [])
    queue = state.get("items_queue", [])
    search = state.get("search_results", {})
    details_count = len(state.get("product_details", {}))
    reviews_count = len(state.get("review_summaries", {}))
    return f"""
Query: {state.get('raw_query', '')}
Budget total: {state.get('budget_total', 'unknown')}
Budget remaining: {state.get('budget_remaining', 'unknown')}
Plan categories: {len(plan)}
Items queue: {queue}
Search results categories: {list(search.keys())}
Product details fetched: {details_count}
Reviews fetched: {reviews_count}
Done: {state.get('done', False)}
Iteration: {state.get('iteration', 0)}
"""


def rule_based_decision(state: ShoppingState) -> OrchestratorDecision:
    """Deterministic ReAct policy when LLM unavailable."""
    if not state.get("shopping_plan"):
        return OrchestratorDecision(action="plan", reason="No plan yet", params={})

    queue = state.get("items_queue", [])
    search = state.get("search_results", {})
    details = state.get("product_details", {})
    reviews = state.get("review_summaries", {})

    if queue:
        cat = queue[0]
        if cat not in search:
            return OrchestratorDecision(
                action="search",
                reason=f"Search category {cat}",
                params={"category": cat},
            )
        items = search.get(cat, [])
        for item in items[:2]:
            url = item.get("url", "")
            if url and url not in details:
                return OrchestratorDecision(
                    action="details",
                    reason="Fetch product details",
                    params={"url": url, "name": item.get("name", "")},
                )
        for item in items[:1]:
            name = item.get("name", "")
            if name and name not in reviews:
                return OrchestratorDecision(
                    action="reviews",
                    reason="Fetch community reviews",
                    params={"name": name},
                )
        new_queue = queue[1:]
        if new_queue != queue:
            return OrchestratorDecision(
                action="search",
                reason="Advance queue",
                params={"advance_queue": True, "new_queue": new_queue},
            )

    if search and not state.get("final_recommendations"):
        return OrchestratorDecision(action="synthesize", reason="Compile recommendations", params={})

    return OrchestratorDecision(action="done", reason="Complete", params={})


async def decide_next_action(state: ShoppingState) -> OrchestratorDecision:
    if state.get("next_action"):
        action = state["next_action"]
        valid = {"plan", "search", "details", "reviews", "synthesize", "done"}
        if action not in valid:
            return rule_based_decision(state)
        return OrchestratorDecision(
            action=action,
            reason="From feedback",
            params=state.get("action_params", {}),
        )

    llm = get_llm()
    context = format_state_for_llm(state)

    if llm.provider == "mock":
        return rule_based_decision(state)

    prompt = f"""You are a shopping ReAct agent. Current state:
{context}

Decide the next action. Options:
- plan: generate shopping plan (first if no plan)
- search: search for next item in queue
- details: fetch price/specs for a product URL
- reviews: get community reviews for top candidate
- synthesize: compile final recommendations when enough data
- done: output ready

Output JSON: {{"action": "...", "reason": "...", "params": {{}}}}"""

    try:
        text = await llm.acomplete(prompt)
        data = json.loads(text) if "{" in text else {}
        return OrchestratorDecision.model_validate(data)
    except Exception:
        return rule_based_decision(state)
