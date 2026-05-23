"""LangGraph ReAct shopping workflow."""

from __future__ import annotations

import asyncio
from typing import Any

from langgraph.graph import END, StateGraph

from app.agent.direct_search import run_direct_search
from app.agent.feedback_handler import handle_feedback
from app.agent.intent_parser import parse_intent
from app.agent.orchestrator import decide_next_action
from app.core.logging import get_logger
from app.core.agent_logger import log_event
from app.models.schemas import ParsedIntent, ShoppingState
from app.tools.fetch_details import fetch_product_details
from app.tools.fetch_reviews import fetch_reviews
from app.tools.plan_shopping import plan_shopping
from app.tools.search_products import search_products
from app.tools.synthesize import synthesize_and_rank

logger = get_logger(__name__)
MAX_ITERATIONS = 25


async def init_state_node(state: ShoppingState) -> dict[str, Any]:
    raw = state.get("raw_query", "")
    intent = await parse_intent(raw)
    budget = intent.budget or 500.0
    
    log_event("AGENT_INTENT_PARSED", {
        "query": raw,
        "query_type": intent.query_type,
        "budget": budget,
        "constraints": intent.constraints,
        "implicit_needs": intent.implicit_needs,
        "context": intent.context
    })

    return {
        "intent": intent.model_dump(),
        "budget_total": budget,
        "budget_remaining": budget,
        "iteration": 0,
        "max_iterations": MAX_ITERATIONS,
        "messages_trace": [f"Parsed intent: {intent.query_type}"],
        "search_results": state.get("search_results", {}),
        "product_details": state.get("product_details", {}),
        "review_summaries": state.get("review_summaries", {}),
        "done": False,
    }


async def react_node(state: ShoppingState) -> dict[str, Any]:
    iteration = state.get("iteration", 0) + 1
    if iteration > state.get("max_iterations", MAX_ITERATIONS):
        log_event("AGENT_REACT_MAX_ITERATIONS", {
            "iteration": iteration,
            "max_iterations": state.get("max_iterations", MAX_ITERATIONS)
        })
        return {"done": True, "error": "Max iterations reached", "iteration": iteration}

    decision = await decide_next_action(state)
    trace = state.get("messages_trace", []) + [f"[{iteration}] {decision.action}: {decision.reason}"]
    updates: dict[str, Any] = {"iteration": iteration, "messages_trace": trace}

    log_event(f"AGENT_REACT_STEP_{iteration}_DECISION", {
        "iteration": iteration,
        "action": decision.action,
        "reason": decision.reason,
        "params": decision.params
    })

    intent = ParsedIntent.model_validate(state.get("intent", {}))
    plan = state.get("shopping_plan", [])
    queue = list(state.get("items_queue", []))
    search_results = dict(state.get("search_results", {}))
    product_details = dict(state.get("product_details", {}))
    review_summaries = dict(state.get("review_summaries", {}))

    if decision.action == "plan":
        shopping_plan = await plan_shopping(intent)
        categories = [c.model_dump() for c in shopping_plan.categories]
        queue = [c["name"] for c in sorted(categories, key=lambda x: x.get("priority", 99))]
        
        log_event("AGENT_ACTION_PLAN_CREATED", {
            "categories": categories,
            "queue": queue,
            "must_haves": shopping_plan.must_haves,
            "nice_to_haves": shopping_plan.nice_to_haves
        })
        
        updates.update({
            "shopping_plan": categories,
            "items_queue": queue,
            "budget_remaining": state.get("budget_total", 500),
        })

    elif decision.action == "search":
        params = decision.params
        if params.get("advance_queue"):
            queue = params.get("new_queue", queue[1:])
        if not queue and plan:
            queue = [c.get("name") for c in plan]
        if queue:
            category = params.get("category") or queue[0]
            cat_plan = next((c for c in plan if c.get("name") == category), {})
            queries = cat_plan.get("queries", [f"{category} best value"])
            budget_max = cat_plan.get("budget_max", state.get("budget_remaining", 500))
            query = queries[0] if queries else category
            results = await search_products(query, float(budget_max))
            search_results[category] = [r.model_dump() for r in results]
            
            log_event("AGENT_ACTION_SEARCH_COMPLETED", {
                "category": category,
                "query": query,
                "budget_max": budget_max,
                "results_count": len(results),
                "top_results": [{"name": r.name, "price": r.price_hint, "url": r.url} for r in results[:3]]
            })
            
            if category == queue[0]:
                queue = queue[1:]
            updates["search_results"] = search_results
            updates["items_queue"] = queue

    elif decision.action == "details":
        url = decision.params.get("url", "")
        name = decision.params.get("name", "")
        if url:
            details = await fetch_product_details(url, name)
            product_details[url] = details.model_dump()
            
            log_event("AGENT_ACTION_DETAILS_COMPLETED", {
                "product_name": name,
                "url": url,
                "price": details.price,
                "in_stock": details.in_stock,
                "rating": details.rating
            })
            
            if details.price:
                remaining = state.get("budget_remaining", 500) - details.price
                updates["budget_remaining"] = max(0, remaining)
            updates["product_details"] = product_details

    elif decision.action == "reviews":
        name = decision.params.get("name", "")
        if name:
            summary = await fetch_reviews(name, intent.context)
            review_summaries[name] = summary.model_dump()
            
            log_event("AGENT_ACTION_REVIEWS_COMPLETED", {
                "product_name": name,
                "sentiment_score": summary.sentiment_score,
                "pros_count": len(summary.pros),
                "cons_count": len(summary.cons)
            })
            
            updates["review_summaries"] = review_summaries

    elif decision.action == "synthesize":
        suggestions, reasoning, insights = await synthesize_and_rank(
            search_results,
            product_details,
            review_summaries,
            state.get("budget_total", 500),
            plan,
        )
        
        log_event("AGENT_ACTION_SYNTHESIZE_COMPLETED", {
            "suggestions_count": len(suggestions),
            "suggestions": [{"title": s.title, "price": s.price, "category": s.category} for s in suggestions],
            "reasoning": reasoning,
            "insights": insights
        })
        
        updates.update({
            "final_recommendations": [s.model_dump() for s in suggestions],
            "reasoning": reasoning,
            "insights": insights,
            "done": True,
        })

    elif decision.action == "done":
        log_event("AGENT_ACTION_DONE", {"reason": "Orchestrator decided flow is completed"})
        updates["done"] = True

    return updates


def should_continue(state: ShoppingState) -> str:
    if state.get("done"):
        return "end"
    if state.get("iteration", 0) >= state.get("max_iterations", MAX_ITERATIONS):
        return "end"
    return "continue"


def build_graph() -> Any:
    graph = StateGraph(ShoppingState)
    graph.add_node("init", init_state_node)
    graph.add_node("react", react_node)
    graph.set_entry_point("init")
    graph.add_edge("init", "react")
    graph.add_conditional_edges("react", should_continue, {"continue": "react", "end": END})
    return graph.compile()


_compiled_graph = None


def get_graph() -> Any:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def run_shopping_agent(
    query: str,
    feedback: str | None = None,
    prior_state: dict | None = None,
) -> dict[str, Any]:
    """Execute the full ReAct shopping workflow."""
    log_event("AGENT_FLOW_START", {
        "query": query,
        "feedback": feedback,
        "has_prior_state": prior_state is not None
    })

    initial: ShoppingState = {
        "raw_query": query,
        "search_results": {},
        "product_details": {},
        "review_summaries": {},
        "messages_trace": [],
        "done": False,
    }
    if prior_state:
        initial.update(prior_state)
        initial["raw_query"] = query

    if feedback and prior_state:
        initial = handle_feedback(feedback, initial)
    else:
        # Fast path: most chat messages are single-product searches
        intent = await parse_intent(query)
        if intent.query_type in ("single", "routine") and not feedback:
            log_event("AGENT_FAST_PATH_TRIGGERED", {
                "query": query,
                "intent": intent.model_dump()
            })
            result = await run_direct_search(query)
            log_event("AGENT_FAST_PATH_COMPLETED", {
                "query": query,
                "recommendations_count": len(result.get("final_recommendations", [])),
                "reasoning": result.get("reasoning")
            })
            return result

    graph = get_graph()
    result = await graph.ainvoke(initial)

    if not result.get("final_recommendations") and result.get("search_results"):
        suggestions, reasoning, insights = await synthesize_and_rank(
            result.get("search_results", {}),
            result.get("product_details", {}),
            result.get("review_summaries", {}),
            result.get("budget_total", 500),
            result.get("shopping_plan"),
        )
        result["final_recommendations"] = [s.model_dump() for s in suggestions]
        result["reasoning"] = reasoning
        result["insights"] = insights

    log_event("AGENT_FLOW_END", {
        "query": query,
        "iterations": result.get("iteration", 0),
        "recommendations_count": len(result.get("final_recommendations", [])),
        "reasoning": result.get("reasoning")
    })

    return result
