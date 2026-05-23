"""LLM provider abstraction: Groq, Gemini, or mock."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.config import get_settings
from app.core.circuit_breaker import get_breaker
from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.breaker = get_breaker(
            "llm",
            failure_threshold=self.settings.cb_failure_threshold,
            recovery_timeout=self.settings.cb_recovery_timeout,
        )

    @property
    def provider(self) -> str:
        if self.settings.groq_api_key:
            return "groq"
        if self.settings.gemini_api_key:
            return "gemini"
        return self.settings.llm_provider

    async def complete(self, prompt: str, system: str = "") -> str:
        def _sync_call() -> str:
            import asyncio

            return asyncio.get_event_loop().run_until_complete(
                self._acomplete(prompt, system)
            )

        return self.breaker.call(
            lambda: __import__("asyncio").run(self._acomplete(prompt, system)),
            fallback=lambda: self._mock_complete(prompt),
        )

    async def acomplete(self, prompt: str, system: str = "") -> str:
        try:
            return await self._acomplete(prompt, system)
        except Exception as e:
            logger.warning("llm_fallback_mock", error=str(e))
            return self._mock_complete(prompt)

    async def _acomplete(self, prompt: str, system: str = "") -> str:
        provider = self.provider
        if provider == "groq":
            return await self._groq(prompt, system)
        if provider == "gemini":
            return await self._gemini(prompt, system)
        return self._mock_complete(prompt)

    async def _groq(self, prompt: str, system: str) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.groq_model,
                    "messages": [
                        {"role": "system", "content": system or "You are a helpful shopping assistant. Respond concisely."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _gemini(self, prompt: str, system: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={self.settings.gemini_api_key}"
        )
        full = f"{system}\n\n{prompt}" if system else prompt
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url,
                json={"contents": [{"parts": [{"text": full}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _mock_complete(self, prompt: str) -> str:
        if "shopping plan" in prompt.lower() or "categories" in prompt.lower():
            return json.dumps({
                "categories": [
                    {
                        "name": "Primary Item",
                        "budget_min": 50,
                        "budget_max": 150,
                        "priority": 1,
                        "queries": ["best value product under budget"],
                    }
                ],
                "total_estimated": "$100-150",
                "must_haves": ["Primary Item"],
                "nice_to_haves": [],
            })
        if "extract product" in prompt.lower() or "page content" in prompt.lower():
            return json.dumps({
                "price": 99.0,
                "currency": "USD",
                "in_stock": True,
                "rating": 4.5,
                "rating_count": 100,
                "specs": {"brand": "Generic"},
            })
        if "summarize reviews" in prompt.lower():
            return json.dumps({
                "sentiment_score": 0.75,
                "pros": ["Good value", "Reliable"],
                "cons": ["Limited color options"],
                "longevity": "Users report satisfaction over 1+ years",
                "sample_size": 12,
            })
        if '"action"' in prompt or "decide the next action" in prompt.lower():
            return json.dumps({"action": "synthesize", "reason": "Enough data gathered", "params": {}})
        return json.dumps({"summary": "Curated picks based on your query.", "insights": ["Compared value and ratings"]})

    async def structured(
        self,
        prompt: str,
        model: type[BaseModel],
        system: str = "",
    ) -> BaseModel:
        text = await self.acomplete(
            f"{prompt}\n\nRespond with valid JSON only matching the schema.",
            system=system,
        )
        data = _extract_json(text)
        return model.model_validate(data)


_llm: LLMService | None = None


def get_llm() -> LLMService:
    global _llm
    if _llm is None:
        _llm = LLMService()
    return _llm
