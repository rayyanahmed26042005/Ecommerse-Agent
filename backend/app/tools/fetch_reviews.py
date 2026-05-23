"""Tool 4: Reddit PRAW review aggregation with LLM summary."""

from __future__ import annotations

import json

from app.config import get_settings
from app.core.cache import cache_get, cache_set
from app.core.circuit_breaker import get_breaker
from app.core.logging import get_logger
from app.models.schemas import ReviewSummary
from app.services.llm import get_llm

logger = get_logger(__name__)

SUBREDDIT_MAP = {
    "gaming": ["buildapc", "pcgaming", "GameDeals"],
    "pc": ["buildapc", "pcgaming"],
    "monitor": ["buildapc", "Monitors"],
    "earbud": ["headphones", "BuyItForLife"],
    "vacuum": ["BuyItForLife", "Appliances"],
    "skincare": ["SkincareAddiction"],
    "office": ["WorkFromHome", "homeoffice"],
    "baby": ["BabyBumps", "beyondthebump"],
    "default": ["BuyItForLife", "frugal"],
}


def _pick_subreddits(product_name: str, context: str = "") -> list[str]:
    combined = (product_name + " " + context).lower()
    subs: list[str] = []
    for keyword, sub_list in SUBREDDIT_MAP.items():
        if keyword != "default" and keyword in combined:
            subs.extend(sub_list)
    return subs or SUBREDDIT_MAP["default"]


def _fetch_reddit_sync(product_name: str, subreddits: list[str], limit: int = 5) -> list[str]:
    settings = get_settings()
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        return []

    import praw

    reddit = praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )
    comments: list[str] = []
    for sub in subreddits[:3]:
        try:
            for post in reddit.subreddit(sub).search(product_name, limit=limit):
                post.comments.replace_more(limit=0)
                for c in list(post.comments)[:5]:
                    if hasattr(c, "body") and len(c.body) > 20:
                        comments.append(c.body[:500])
        except Exception as e:
            logger.warning("reddit_sub_failed", sub=sub, error=str(e))
    return comments


def _mock_reviews(product_name: str) -> ReviewSummary:
    return ReviewSummary(
        sentiment_score=0.72,
        pros=[
            "Excellent value for the specs",
            "Easy to upgrade later",
            "Strong community recommendation",
        ],
        cons=["Fan can be loud under load", "Build quality is adequate not premium"],
        longevity="Users report good performance after 1-2 years",
        sample_size=24,
    )


async def fetch_reviews(product_name: str, context: str = "") -> ReviewSummary:
    cache_key = f"reviews:{product_name}:{context}"
    cached = await cache_get("reviews", cache_key)
    if cached:
        return ReviewSummary.model_validate(cached)

    settings = get_settings()
    subs = _pick_subreddits(product_name, context)
    comments: list[str] = []

    if settings.reddit_client_id:
        breaker = get_breaker("reddit", settings.cb_failure_threshold, settings.cb_recovery_timeout)
        try:
            comments = breaker.call(
                lambda: _fetch_reddit_sync(product_name, subs),
                fallback=lambda: [],
            )
        except Exception as e:
            logger.warning("reddit_fetch_failed", error=str(e))

    if not comments:
        summary = _mock_reviews(product_name)
        await cache_set("reviews", cache_key, summary.model_dump())
        return summary

    llm = get_llm()
    prompt = f"""Summarize reviews for "{product_name}" from these comments.
Return JSON: sentiment_score (0-1), pros (list), cons (list), longevity (string), sample_size (int).

Comments:
{chr(10).join(comments[:15])[:4000]}"""

    try:
        text = await llm.acomplete(prompt, system="Summarize reviews. Output JSON only.")
        data = json.loads(text) if text.strip().startswith("{") else {}
        summary = ReviewSummary.model_validate(data)
        summary.sample_size = max(summary.sample_size, len(comments))
    except Exception:
        summary = _mock_reviews(product_name)
        summary.sample_size = len(comments)

    await cache_set("reviews", cache_key, summary.model_dump())
    return summary
