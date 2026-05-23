"""Tool 1: Generate budget-allocated shopping plan."""

from __future__ import annotations

import json

from app.core.cache import cache_get, cache_set
from app.models.schemas import ParsedIntent, ShoppingCategory, ShoppingPlan
from app.services.llm import get_llm


async def plan_shopping(intent: ParsedIntent) -> ShoppingPlan:
    cache_key = f"plan:{intent.model_dump_json()}"
    cached = await cache_get("search", cache_key)
    if cached:
        return ShoppingPlan.model_validate(cached)

    budget = intent.budget or 500.0
    llm = get_llm()

    prompt = f"""Given this shopping intent, output a JSON shopping plan:
{intent.model_dump_json()}

Include categories with name, budget_min, budget_max, priority (1=highest),
and 2-3 specific search queries per category.
Also include total_estimated, must_haves, nice_to_haves.

Budget total: ${budget}
Query type: {intent.query_type}
"""

    if intent.query_type == "bundle" and "gaming" in (intent.item + intent.context).lower():
        plan = ShoppingPlan(
            categories=[
                ShoppingCategory(
                    name="Gaming PC",
                    budget_min=400,
                    budget_max=500,
                    priority=1,
                    queries=[
                        "gaming PC under $500 Ryzen 5 GTX 1660",
                        "budget gaming desktop iBUYPOWER CyberPowerPC",
                    ],
                ),
                ShoppingCategory(
                    name="Monitor",
                    budget_min=150,
                    budget_max=200,
                    priority=2,
                    queries=[
                        "24 inch 144Hz gaming monitor under $200",
                        "best budget gaming monitor 1080p",
                    ],
                ),
                ShoppingCategory(
                    name="Headset",
                    budget_min=50,
                    budget_max=80,
                    priority=3,
                    queries=["gaming headset under $80 wireless"],
                ),
            ],
            total_estimated="$780-820",
            must_haves=["Gaming PC", "Monitor"],
            nice_to_haves=["Gaming Chair"],
        )
    elif intent.query_type == "grocery_bundle":
        plan = ShoppingPlan(
            categories=[
                ShoppingCategory(name="Staples", budget_min=600, budget_max=800, priority=1, queries=["bulk rice lentils oil prices"]),
                ShoppingCategory(name="Proteins", budget_min=400, budget_max=500, priority=2, queries=["chicken eggs bulk grocery"]),
                ShoppingCategory(name="Vegetables", budget_min=300, budget_max=400, priority=3, queries=["fresh vegetables bulk"]),
                ShoppingCategory(name="Essentials", budget_min=200, budget_max=300, priority=4, queries=["household essentials bulk"]),
            ],
            total_estimated=f"${budget * 0.95:.0f}-${budget:.0f}",
            must_haves=["Staples", "Proteins"],
            nice_to_haves=["Essentials"],
        )
    else:
        try:
            text = await llm.acomplete(prompt, system="Output valid JSON for a shopping plan.")
            data = json.loads(text) if text.startswith("{") else {}
            plan = ShoppingPlan.model_validate(data) if data.get("categories") else None
        except Exception:
            plan = None

        if not plan or not plan.categories:
            share = budget / 2
            plan = ShoppingPlan(
                categories=[
                    ShoppingCategory(
                        name="Primary",
                        budget_min=share * 0.8,
                        budget_max=share,
                        priority=1,
                        queries=[f"{intent.item} best value under ${share:.0f}"],
                    ),
                    ShoppingCategory(
                        name="Secondary",
                        budget_min=share * 0.5,
                        budget_max=share * 0.8,
                        priority=2,
                        queries=[f"{intent.item} accessories under ${share * 0.5:.0f}"],
                    ),
                ],
                total_estimated=f"${budget * 0.9:.0f}-${budget:.0f}",
                must_haves=["Primary"],
                nice_to_haves=["Secondary"],
            )

    await cache_set("search", cache_key, plan.model_dump())
    return plan
