"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EcoAi Smart Shopping"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://ecoai:ecoai@localhost:5432/ecoai"
    )
    database_url_sync: str = Field(
        default="postgresql://ecoai:ecoai@localhost:5432/ecoai"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "product_memory"

    # LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str = ""
    llm_provider: Literal["groq", "gemini", "mock"] = "mock"

    # External APIs (optional)
    tavily_api_key: str = ""
    brave_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "EcoAiShoppingAgent/1.0"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    oauth_enabled: bool = False

    # Rate limiting
    rate_limit_user_per_minute: int = 30
    rate_limit_ip_per_minute: int = 60
    rate_limit_tool_per_minute: int = 20

    # Idempotency
    idempotency_ttl_seconds: int = 3600

    # Cache TTLs (seconds)
    cache_ttl_search: int = 6 * 3600
    cache_ttl_details: int = 24 * 3600
    cache_ttl_reviews: int = 48 * 3600
    cache_ttl_l1_maxsize: int = 256

    # Circuit breaker
    cb_failure_threshold: int = 5
    cb_recovery_timeout: int = 60

    # Celery
    celery_task_soft_time_limit: int = 300
    celery_task_time_limit: int = 360

    # Observability
    otel_enabled: bool = False
    otel_service_name: str = "ecoai-backend"
    jaeger_endpoint: str = "http://localhost:4317"
    log_level: str = "INFO"

    # HTTP
    max_request_body_bytes: int = 1_048_576

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
