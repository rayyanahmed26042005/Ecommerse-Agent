"""Per-dependency circuit breaker with open/half-open/closed states."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    _registry: dict[str, "CircuitBreaker"] = field(default_factory=dict, repr=False, init=False)

    def __post_init__(self) -> None:
        _BREAKERS[self.name] = self

    def _should_attempt(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("circuit_half_open", breaker=self.name)
                return True
            return False
        return True  # half-open

    def record_success(self) -> None:
        self.failure_count = 0
        if self.state != CircuitState.CLOSED:
            logger.info("circuit_closed", breaker=self.name)
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "circuit_open",
                breaker=self.name,
                failures=self.failure_count,
            )

    def call(
        self,
        func: Callable[..., T],
        *args: Any,
        fallback: Callable[..., T] | None = None,
        **kwargs: Any,
    ) -> T:
        if not self._should_attempt():
            logger.warning("circuit_rejected", breaker=self.name)
            if fallback:
                return fallback(*args, **kwargs)
            raise CircuitOpenError(self.name)
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            if fallback:
                return fallback(*args, **kwargs)
            raise


class CircuitOpenError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Circuit breaker '{name}' is open")
        self.breaker_name = name


_BREAKERS: dict[str, CircuitBreaker] = {}


def get_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    if name not in _BREAKERS:
        _BREAKERS[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _BREAKERS[name]


def breaker_status() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "state": b.state.value,
            "failures": b.failure_count,
        }
        for name, b in _BREAKERS.items()
    }
