"""Tool 2: DuckDuckGo + optional Tavily/Brave product search."""

from __future__ import annotations

import re
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from app.config import get_settings
from app.core.cache import cache_get, cache_set
from app.core.circuit_breaker import get_breaker
from app.core.logging import get_logger
from app.models.schemas import SearchResultItem

logger = get_logger(__name__)


def extract_price_from_snippet(text: str) -> float | None:
    patterns = [
        r"\$\s*([\d,]+(?:\.\d{2})?)",
        r"([\d,]+)\s*USD",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def extract_domain(url: str) -> str:
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else "web"


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=10))
def _ddg_search(query: str, max_results: int) -> list[dict[str, Any]]:
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def _mock_catalog() -> list[SearchResultItem]:
    return [
        SearchResultItem(
            name="Aurora Pro Wireless Earbuds",
            url="https://www.amazon.com/dp/example-earbuds",
            price_hint=129.0,
            snippet="ANC Bluetooth 5.3 IPX4 28h battery earbuds",
            source="amazon.com",
        ),
        SearchResultItem(
            name="SoundWave Lite Earbuds",
            url="https://www.bestbuy.com/site/example",
            price_hint=99.0,
            snippet="Comfort fit wireless earbuds 24h battery USB-C",
            source="bestbuy.com",
        ),
        SearchResultItem(
            name="Nimbus Lite Vacuum",
            url="https://www.target.com/p/example-vacuum",
            price_hint=179.0,
            snippet="Quiet HEPA cordless vacuum cleaner 40min",
            source="target.com",
        ),
        SearchResultItem(
            name="Luma Desk Lamp",
            url="https://www.ikea.com/example-lamp",
            price_hint=89.0,
            snippet="Dimmable LED desk lamp USB-C CRI 95 adjustable",
            source="ikea.com",
        ),
        SearchResultItem(
            name="Voyage Travel Kit",
            url="https://www.amazon.com/dp/example-travel",
            price_hint=49.0,
            snippet="TSA-ready compact travel organizer kit",
            source="amazon.com",
        ),
        SearchResultItem(
            name="Ergo Chair Lite",
            url="https://www.amazon.com/dp/example-chair",
            price_hint=199.0,
            snippet="Ergonomic office chair lumbar support mesh",
            source="amazon.com",
        ),
        SearchResultItem(
            name="iBUYPOWER Gaming PC SlateMesh",
            url="https://www.amazon.com/dp/example-gaming-pc",
            price_hint=449.0,
            snippet="Ryzen 5 GTX 1660 Super 16GB RAM gaming desktop",
            source="amazon.com",
        ),
        SearchResultItem(
            name='ASUS 24" 144Hz Gaming Monitor',
            url="https://www.amazon.com/dp/example-monitor",
            price_hint=179.0,
            snippet="1080p 1ms IPS gaming monitor 144Hz",
            source="amazon.com",
        ),
        SearchResultItem(
            name="CeraVe Hydrating Cleanser",
            url="https://www.amazon.com/dp/example-skincare",
            price_hint=14.0,
            snippet="Gentle fragrance-free cleanser sensitive skin",
            source="amazon.com",
        ),
    ]


def _mock_search(query: str, budget_max: float) -> list[SearchResultItem]:
    q = query.lower()
    stop = {"best", "under", "the", "for", "a", "an", "find", "buy", "online", "recommend", "looking"}
    words = [w for w in re.findall(r"[a-z0-9]+", q) if w not in stop and len(w) > 2]

    filtered = [i for i in _mock_catalog() if i.price_hint and i.price_hint <= budget_max * 1.1]
    if not filtered:
        filtered = _mock_catalog()

    rules: list[tuple[list[str], Any]] = [
        (["gaming", "pc", "desktop", "gpu"], lambda i: "gaming" in i.name.lower() or "ibuypower" in i.name.lower()),
        (["monitor", "display", "144hz"], lambda i: "monitor" in i.name.lower()),
        (["vacuum", "quiet", "hepa", "clean"], lambda i: "vacuum" in i.name.lower()),
        (["earbud", "headphone", "audio", "anc"], lambda i: "earbud" in i.name.lower()),
        (["lamp", "desk", "light"], lambda i: "lamp" in i.name.lower()),
        (["travel", "kit", "tsa"], lambda i: "travel" in i.name.lower()),
        (["chair", "ergonomic", "office"], lambda i: "chair" in i.name.lower()),
        (["skincare", "cleanser", "moisturizer", "skin"], lambda i: "cerave" in i.name.lower()),
    ]
    for keys, pred in rules:
        if any(k in q for k in keys):
            hits = [i for i in filtered if pred(i)]
            if hits:
                return hits[:5]

    def score(item: SearchResultItem) -> int:
        text = f"{item.name} {item.snippet}".lower()
        return sum(2 if w in item.name.lower() else 1 for w in words if w in text)

    ranked = sorted(filtered, key=lambda i: (-score(i), i.price_hint or 9999))
    if ranked and score(ranked[0]) > 0:
        return ranked[:5]
    return filtered[:5]


async def _tavily_search(query: str, budget_max: float) -> list[SearchResultItem]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    search_query = f"{query} buy online under ${budget_max}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": search_query,
                "max_results": 8,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    items: list[SearchResultItem] = []
    for r in data.get("results", []):
        price = extract_price_from_snippet(r.get("content", ""))
        items.append(
            SearchResultItem(
                name=r.get("title", "Product"),
                url=r.get("url", ""),
                price_hint=price,
                snippet=(r.get("content") or "")[:200],
                source=extract_domain(r.get("url", "")),
            )
        )
    return items


async def search_products(query: str, budget_max: float, num_results: int = 8) -> list[SearchResultItem]:
    cache_key = f"search:{query.strip().lower()}:{budget_max}"
    cached = await cache_get("search", cache_key)
    if cached:
        return [SearchResultItem.model_validate(i) for i in cached]

    settings = get_settings()
    breaker = get_breaker("duckduckgo", settings.cb_failure_threshold, settings.cb_recovery_timeout)
    search_query = f"{query} buy online under ${budget_max}"
    products: list[SearchResultItem] = []

    try:
        raw = breaker.call(
            lambda: _ddg_search(search_query, num_results),
            fallback=lambda: [],
        )
        for r in raw:
            price = extract_price_from_snippet(r.get("body", ""))
            if price is None or price <= budget_max * 1.1:
                products.append(
                    SearchResultItem(
                        name=r.get("title", "Product"),
                        url=r.get("href", ""),
                        price_hint=price,
                        snippet=(r.get("body") or "")[:200],
                        source=extract_domain(r.get("href", "")),
                    )
                )
    except Exception as e:
        logger.warning("ddg_search_failed", error=str(e))

    if len(products) < 3 and settings.tavily_api_key:
        try:
            tavily_items = await _tavily_search(query, budget_max)
            products.extend(tavily_items)
        except Exception as e:
            logger.warning("tavily_search_failed", error=str(e))

    if not products:
        products = _mock_search(query, budget_max)

    products = sorted(products, key=lambda x: x.price_hint or 9999)[:5]
    await cache_set("search", cache_key, [p.model_dump() for p in products])
    return products
