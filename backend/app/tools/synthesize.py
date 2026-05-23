"""Tool 5: Rank products and generate final recommendations."""

from __future__ import annotations

from app.models.schemas import (
    ProductDetails,
    ProductSuggestion,
    Retailer,
    ReviewSummary,
    SearchResultItem,
)
from app.services.llm import get_llm

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=1200&auto=format&fit=crop"


def price_fit_score(price: float | None, budget_min: float, budget_max: float) -> float:
    if price is None:
        return 0.5
    if budget_min <= price <= budget_max:
        return 1.0
    if price < budget_min:
        return 0.85
    if price <= budget_max * 1.1:
        return 0.6
    return 0.2


def review_score(summary: ReviewSummary | None) -> float:
    if not summary:
        return 0.5
    return min(1.0, max(0.0, summary.sentiment_score))


def availability_score(details: ProductDetails | None) -> float:
    if not details:
        return 0.5
    if details.in_stock is True:
        return 1.0
    if details.in_stock is False:
        return 0.0
    return 0.5


def compute_score(
    price: float | None,
    budget_min: float,
    budget_max: float,
    review: ReviewSummary | None,
    details: ProductDetails | None,
) -> float:
    return (
        price_fit_score(price, budget_min, budget_max) * 0.4
        + review_score(review) * 0.35
        + availability_score(details) * 0.25
    )


def _specs_list(details: ProductDetails | None, item: SearchResultItem) -> list[str]:
    specs: list[str] = []
    if details and details.specs:
        specs.extend([f"{k}: {v}" for k, v in list(details.specs.items())[:4]])
    if item.snippet:
        parts = [p.strip() for p in item.snippet.replace("|", " ").split() if len(p.strip()) > 2]
        specs.extend(parts[:4 - len(specs)])
    return specs[:4] or ["Popular pick", "Good value"]


async def synthesize_and_rank(
    search_results: dict[str, list[dict]],
    product_details: dict[str, dict],
    review_summaries: dict[str, dict],
    budget_total: float,
    plan_categories: list[dict] | None = None,
) -> tuple[list[ProductSuggestion], str, list[str]]:
    """Returns (suggestions, reasoning, insights)."""
    candidates: list[tuple[float, ProductSuggestion, str]] = []
    category_budgets: dict[str, tuple[float, float]] = {}
    if plan_categories:
        for cat in plan_categories:
            category_budgets[cat.get("name", "")] = (
                cat.get("budget_min", 0),
                cat.get("budget_max", budget_total),
            )

    total_cost = 0.0
    insights: list[str] = []

    for category, items_raw in search_results.items():
        bmin, bmax = category_budgets.get(category, (0, budget_total))
        items = [SearchResultItem.model_validate(i) for i in items_raw[:3]]

        for item in items:
            details_raw = product_details.get(item.url) or product_details.get(item.name)
            details = ProductDetails.model_validate(details_raw) if details_raw else None
            review_raw = review_summaries.get(item.name)
            review = ReviewSummary.model_validate(review_raw) if review_raw else None

            price = (details.price if details and details.price else None) or item.price_hint
            score = compute_score(price, bmin, bmax, review, details)

            pros = review.pros[:2] if review else []
            cons = review.cons[:1] if review else []
            reasoning_parts = []
            if price:
                reasoning_parts.append(f"At ${price:.0f}, fits {category} budget range.")
            if pros:
                reasoning_parts.append(pros[0])
            if cons:
                reasoning_parts.append(f"Note: {cons[0]}")

            rating = (details.rating if details and details.rating else 4.5) or 4.5
            retailers = [
                Retailer(name=item.source or "Online", price=price or item.price_hint or 0, best=True)
            ]
            if item.price_hint and price and item.price_hint != price:
                retailers.append(
                    Retailer(name="Listed", price=item.price_hint, best=False)
                )

            suggestion = ProductSuggestion(
                title=item.name,
                category=category,
                price=price or item.price_hint or 99.0,
                rating=rating,
                image=DEFAULT_IMAGE,
                specs=_specs_list(details, item),
                retailers=retailers,
                reasoning=" ".join(reasoning_parts) or "Balanced value and availability.",
                url=item.url,
            )
            candidates.append((score, suggestion, category))
            if price:
                total_cost += price

    candidates.sort(key=lambda x: x[0], reverse=True)
    suggestions = [c[1] for c in candidates[:8]]

    if total_cost > budget_total and suggestions:
        insights.append(
            f"Total ${total_cost:.0f} exceeds budget ${budget_total:.0f}; consider dropping nice-to-haves."
        )
        # Trim lowest priority / highest price items
        while total_cost > budget_total and len(suggestions) > 2:
            removed = suggestions.pop()
            total_cost -= removed.price
            insights.append(f"Removed {removed.title} to stay within budget.")

    if not suggestions:
        suggestions = [
            ProductSuggestion(
                title="Curated Value Pick",
                category="General",
                price=min(99.0, budget_total * 0.3),
                rating=4.5,
                image=DEFAULT_IMAGE,
                specs=["Best value", "Highly rated"],
                retailers=[Retailer(name="Amazon", price=99, best=True)],
                reasoning="Fallback recommendation when search returned limited results.",
            )
        ]

    llm = get_llm()
    names = ", ".join(s.title for s in suggestions[:5])
    reasoning = (
        f"Recommended {len(suggestions)} items totaling ~${sum(s.price for s in suggestions):.0f} "
        f"against your ${budget_total:.0f} budget. Top picks: {names}."
    )

    try:
        text = await llm.acomplete(
            f"Write 2-3 sentences explaining why these products were chosen: {names}. "
            f"Budget: ${budget_total}. Insights so far: {insights}"
        )
        if text and len(text) > 20 and not text.startswith("{"):
            reasoning = text.strip()[:500]
    except Exception:
        pass

    if not insights:
        insights = [
            "Compared price fit, community sentiment, and stock availability.",
            "Best price retailers are highlighted on each card.",
            "Use compare to line up specs side by side.",
        ]

    return suggestions, reasoning, insights
