"""OpenTelemetry and Prometheus metrics setup."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from fastapi import FastAPI

_metrics_initialized = False
_request_counter = None
_request_latency = None


def setup_observability(app: "FastAPI") -> None:
    global _metrics_initialized, _request_counter, _request_latency
    settings = get_settings()

    try:
        from prometheus_client import Counter, Histogram, make_asgi_app

        _request_counter = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )
        _request_latency = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
        )
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        _metrics_initialized = True
    except ImportError:
        logger.warning("prometheus_client_not_installed")

    if settings.otel_enabled:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create({"service.name": settings.otel_service_name})
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=settings.jaeger_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            FastAPIInstrumentor.instrument_app(app)
            logger.info("otel_enabled", endpoint=settings.jaeger_endpoint)
        except Exception as e:
            logger.warning("otel_setup_failed", error=str(e))


def record_request(method: str, endpoint: str, status: int, duration: float) -> None:
    if _request_counter and _request_latency:
        _request_counter.labels(method=method, endpoint=endpoint, status=status).inc()
        _request_latency.labels(method=method, endpoint=endpoint).observe(duration)
