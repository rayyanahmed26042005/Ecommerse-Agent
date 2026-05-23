"""Pydantic models and LangGraph state definitions."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# --- API models (frontend contract) ---


class Retailer(BaseModel):
    name: str
    price: float
    best: bool = False


class ProductSuggestion(BaseModel):
    title: str
    category: str
    price: float
    rating: float = 4.5
    image: str = ""
    specs: list[str] = Field(default_factory=list)
    retailers: list[Retailer] = Field(default_factory=list)
    reasoning: str | None = None
    url: str | None = None


class ChatRequest(BaseModel):
    user_id: str = "demo-user-1"
    message: str
    feedback: str | None = None
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    summary: str | None = None
    suggestions: list[ProductSuggestion] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    reasoning: str | None = None
    task_id: str | None = None
    status: Literal["completed", "processing", "failed"] = "completed"


class TaskStatusResponse(BaseModel):
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    result: ChatResponse | None = None
    error: str | None = None
    progress: float = 0.0


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Agent / tool models ---


class ShoppingCategory(BaseModel):
    name: str
    budget_min: float
    budget_max: float
    priority: int = 1
    queries: list[str] = Field(default_factory=list)


class ShoppingPlan(BaseModel):
    categories: list[ShoppingCategory] = Field(default_factory=list)
    total_estimated: str = ""
    must_haves: list[str] = Field(default_factory=list)
    nice_to_haves: list[str] = Field(default_factory=list)


class SearchResultItem(BaseModel):
    name: str
    url: str
    price_hint: float | None = None
    snippet: str = ""
    source: str = ""


class ProductDetails(BaseModel):
    price: float | None = None
    was_price: float | None = None
    currency: str = "USD"
    in_stock: bool | None = None
    rating: float | None = None
    rating_count: int | None = None
    specs: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


class ReviewSummary(BaseModel):
    sentiment_score: float = 0.5
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    longevity: str = ""
    sample_size: int = 0


class ParsedIntent(BaseModel):
    query_type: str = "single"  # single | bundle | grocery_bundle | routine
    item: str = ""
    budget: float | None = None
    constraints: list[str] = Field(default_factory=list)
    implicit_needs: list[str] = Field(default_factory=list)
    context: str = ""
    people: int | None = None
    duration: str | None = None


class OrchestratorDecision(BaseModel):
    action: Literal["plan", "search", "details", "reviews", "synthesize", "done"]
    reason: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


def merge_dicts(left: dict, right: dict) -> dict:
    merged = {**left, **right}
    return merged


class ShoppingState(TypedDict, total=False):
    raw_query: str
    intent: dict
    shopping_plan: list[dict]
    items_queue: list[str]
    current_category: str
    search_results: dict
    product_details: dict
    review_summaries: dict
    budget_total: float
    budget_remaining: float
    final_recommendations: list[dict]
    reasoning: str
    done: bool
    error: str | None
    messages_trace: Annotated[list[str], lambda a, b: a + b]
    iteration: int
    max_iterations: int
    next_action: str
    action_params: dict
