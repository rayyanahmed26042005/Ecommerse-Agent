"""Handle user feedback with targeted state updates (no full pipeline rerun)."""

from __future__ import annotations

import re

from app.models.schemas import ShoppingState


def extract_new_budget(feedback: str) -> float | None:
    m = re.search(r"\$?\s*([\d,]+)", feedback)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def extract_preference(feedback: str) -> str | None:
    m = re.search(r"prefer\s+(\w+)", feedback, re.I)
    return m.group(1) if m else None


def get_over_budget_items(state: ShoppingState) -> list[str]:
    queue: list[str] = []
    budget = state.get("budget_remaining", state.get("budget_total", 0))
    search_results = state.get("search_results", {})
    product_details = state.get("product_details", {})
    for cat, items in search_results.items():
        for item in items:
            url = item.get("url", "")
            details = product_details.get(url, {})
            price = details.get("price") or item.get("price_hint")
            if price and price > budget:
                queue.append(cat)
                break
    return list(dict.fromkeys(queue))


def handle_feedback(feedback: str, state: ShoppingState) -> ShoppingState:
    """Update state based on feedback without full pipeline rerun when possible."""
    feedback_lower = feedback.lower()
    new_state = dict(state)
    new_state["done"] = False

    if any(w in feedback_lower for w in ["expensive", "cheap", "affordable", "budget", "cheaper"]):
        new_budget = extract_new_budget(feedback) or state.get("budget_total", 500) * 0.8
        new_state["budget_total"] = new_budget
        new_state["budget_remaining"] = new_budget
        new_state["items_queue"] = get_over_budget_items(state) or state.get("items_queue", [])
        new_state["next_action"] = "search"
        new_state["messages_trace"] = state.get("messages_trace", []) + [
            f"Feedback: budget adjusted to ${new_budget:.0f}"
        ]

    elif any(w in feedback_lower for w in ["more options", "alternatives", "different", "other"]):
        depth = state.get("search_depth", 1) + 1
        new_state["search_depth"] = depth
        new_state["items_queue"] = list(state.get("search_results", {}).keys()) or state.get(
            "items_queue", []
        )
        new_state["next_action"] = "search"

    elif "prefer" in feedback_lower or "like" in feedback_lower:
        preference = extract_preference(feedback) or feedback
        filters = state.get("filters", {})
        filters["brand_preference"] = preference
        new_state["filters"] = filters
        new_state["next_action"] = "synthesize"
        new_state["messages_trace"] = state.get("messages_trace", []) + [
            f"Re-ranking with preference: {preference}"
        ]
    else:
        new_state["next_action"] = "plan"
        new_state["items_queue"] = []
        new_state["search_results"] = {}
        new_state["product_details"] = {}
        new_state["review_summaries"] = {}

    return new_state
