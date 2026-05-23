"""Fast path: search directly from user query (no multi-step plan loop)."""

from __future__ import annotations

from app.agent.intent_parser import parse_intent
from app.models.schemas import ParsedIntent
from app.tools.fetch_details import fetch_product_details
from app.tools.fetch_reviews import fetch_reviews
from app.tools.search_products import search_products
from app.tools.synthesize import synthesize_and_rank
from app.core.agent_logger import log_event


async def run_direct_search(query: str) -> dict:
    """Single-pass search using the user's exact words."""
    log_event("AGENT_DIRECT_SEARCH_START", {"query": query})
    
    intent = await parse_intent(query)
    budget = intent.budget or 500.0
    
    log_event("AGENT_DIRECT_SEARCH_INTENT_PARSED", {
        "query": query,
        "intent": intent.model_dump(),
        "budget": budget
    })

    results = await search_products(query, budget, num_results=10)
    if not results:
        results = await search_products(intent.item or query, budget, num_results=10)
        
    log_event("AGENT_DIRECT_SEARCH_PRODUCTS_SEARCHED", {
        "query": query,
        "results_count": len(results),
        "results": [{"name": r.name, "price": r.price_hint, "url": r.url} for r in results]
    })

    category = "Top picks"
    search_results = {category: [r.model_dump() for r in results]}

    product_details: dict = {}
    for item in results[:3]:
        if item.url:
            details = await fetch_product_details(item.url, item.name)
            product_details[item.url] = details.model_dump()
            
            log_event("AGENT_DIRECT_SEARCH_DETAILS_COMPLETED", {
                "product_name": item.name,
                "url": item.url,
                "price": details.price,
                "rating": details.rating,
                "in_stock": details.in_stock
            })

    review_summaries: dict = {}
    if results:
        top = results[0]
        summary = await fetch_reviews(top.name, intent.context)
        review_summaries[top.name] = summary.model_dump()
        
        log_event("AGENT_DIRECT_SEARCH_REVIEWS_COMPLETED", {
            "product_name": top.name,
            "sentiment_score": summary.sentiment_score,
            "pros": summary.pros,
            "cons": summary.cons
        })

    suggestions, reasoning, insights = await synthesize_and_rank(
        search_results,
        product_details,
        review_summaries,
        budget,
        plan_categories=[
            {
                "name": category,
                "budget_min": budget * 0.3,
                "budget_max": budget,
            }
        ],
    )
    
    log_event("AGENT_DIRECT_SEARCH_SYNTHESIZE_COMPLETED", {
        "suggestions_count": len(suggestions),
        "suggestions": [{"title": s.title, "price": s.price, "category": s.category} for s in suggestions],
        "reasoning": reasoning,
        "insights": insights
    })

    return {
        "intent": intent.model_dump(),
        "budget_total": budget,
        "search_results": search_results,
        "product_details": product_details,
        "review_summaries": review_summaries,
        "final_recommendations": [s.model_dump() for s in suggestions],
        "reasoning": reasoning,
        "insights": insights,
        "done": True,
    }
