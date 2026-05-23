"""Parse user query into structured shopping intent."""

from __future__ import annotations

import re

from app.models.schemas import ParsedIntent
from app.services.llm import get_llm


def _extract_budget(text: str) -> float | None:
    patterns = [
        r"\$\s*([\d,]+(?:\.\d{2})?)",
        r"under\s*\$?\s*([\d,]+)",
        r"budget\s*(?:of\s*)?\$?\s*([\d,]+)",
        r"([\d,]+)\s*dollars?",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return float(m.group(1).replace(",", ""))
    return None


def _infer_query_type(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["grocery", "ration", "food", "month supply", "staples"]):
        return "grocery_bundle"
    if any(w in lower for w in ["routine", "skincare", "cleanser", "moisturizer"]):
        return "routine"
    if any(
        w in lower
        for w in ["setup", "bundle", "office", "gaming", "baby", "essentials kit"]
    ):
        return "bundle"
    return "single"


async def parse_intent(raw_query: str) -> ParsedIntent:
    budget = _extract_budget(raw_query)
    query_type = _infer_query_type(raw_query)
    implicit: list[str] = []
    constraints: list[str] = []
    lower = raw_query.lower()

    if "sensitive" in lower:
        constraints.extend(["fragrance-free", "non-comedogenic"])
    if "teen" in lower or "teenager" in lower:
        implicit.append("value over luxury")
        implicit.append("upgradeable preferred")
    if "baby" in lower or "newborn" in lower:
        implicit.append("safety-first")
        constraints.append("certified products for safety items")
    if "remote" in lower or "home office" in lower:
        implicit.append("ergonomics priority")

    people_match = re.search(r"(\d+)\s*people", lower)
    people = int(people_match.group(1)) if people_match else None

    duration = None
    if "month" in lower:
        duration = "1 month"
    elif "60 day" in lower or "60-day" in lower:
        duration = "60 days"
    elif "6 month" in lower:
        duration = "6 months"

    llm = get_llm()
    if llm.provider != "mock":
        try:
            parsed = await llm.structured(
                f"""Parse this shopping query into structured intent JSON:
Query: {raw_query}

Fields: query_type, item (main product/theme), budget (number or null),
constraints (list), implicit_needs (list), context, people, duration""",
                ParsedIntent,
                system="You extract shopping intent. Output JSON only.",
            )
            if parsed.budget is None and budget:
                parsed.budget = budget
            return parsed
        except Exception:
            pass

    return ParsedIntent(
        query_type=query_type,
        item=raw_query.strip()[:200],
        budget=budget,
        constraints=constraints,
        implicit_needs=implicit,
        context=query_type,
        people=people,
        duration=duration,
    )
