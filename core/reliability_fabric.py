"""
SHUNYA — Reliability Fabric (FDA5-G6).

Every external integration must have explicit handling for:
- timeout, retry, exponential backoff
- duplicate delivery, rate limiting
- provider outage, malformed response
- partial failure, authentication expiry
- permanent vs transient failure
"""

import logging
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Failure Classification
# ═══════════════════════════════════════════════════════════════════

class FailureType(Enum):
    """Classification of integration failures."""
    TRANSIENT = "transient"          # Safe to retry
    PERMANENT = "permanent"          # Do not retry
    AUTH_EXPIRED = "auth_expired"    # Requires re-authentication
    RATE_LIMITED = "rate_limited"    # Back off and retry
    VALIDATION = "validation"       # Payload/request malformed
    PROVIDER_OUTAGE = "outage"       # Provider unavailable
    TIMEOUT = "timeout"              # Request timed out
    DUPLICATE = "duplicate"          # Already processed
    UNKNOWN = "unknown"              # Unclassified


# ═══════════════════════════════════════════════════════════════════
# Retry Configuration
# ═══════════════════════════════════════════════════════════════════

class RetryPolicy:
    """Configure retry behavior for an integration."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        retryable_failures: set[FailureType] = None,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_failures = retryable_failures or {
            FailureType.TRANSIENT,
            FailureType.RATE_LIMITED,
            FailureType.TIMEOUT,
            FailureType.PROVIDER_OUTAGE,
        }
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number (1-indexed)."""
        delay = min(self.base_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
        if self.jitter:
            delay *= 0.5 + random.random() * 0.5  # 50-100% of calculated delay
        return delay

    def should_retry(self, attempt: int, failure_type: FailureType) -> bool:
        """Determine if a retry should be attempted."""
        if attempt >= self.max_retries:
            return False
        return failure_type in self.retryable_failures


# ═══════════════════════════════════════════════════════════════════
# Retry Decorator
# ═══════════════════════════════════════════════════════════════════

def with_retry(
    policy: Optional[RetryPolicy] = None,
    on_failure: Optional[Callable] = None,
):
    """Decorator: retry a function with exponential backoff.

    Args:
        policy: RetryPolicy configuration (defaults to 3 retries, 2x backoff)
        on_failure: Optional callback for each failure (attempt, failure_type, exception)
    """
    if policy is None:
        policy = RetryPolicy()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, policy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    failure_type = _classify_failure(e)
                    if not policy.should_retry(attempt, failure_type):
                        raise
                    if on_failure:
                        on_failure(attempt, failure_type, e)
                    if attempt < policy.max_retries:
                        delay = policy.get_delay(attempt)
                        logger.warning(
                            f"Retry {attempt}/{policy.max_retries} after {delay:.1f}s "
                            f"({failure_type.value}): {e}"
                        )
                        time.sleep(delay)
            raise last_exception  # Should not reach here
        return wrapper
    return decorator


def _classify_failure(exception: Exception) -> FailureType:
    """Classify an exception into a FailureType."""
    msg = str(exception).lower()
    if "timeout" in msg or "timed out" in msg:
        return FailureType.TIMEOUT
    if "rate" in msg and "limit" in msg:
        return FailureType.RATE_LIMITED
    if "auth" in msg or "unauthorized" in msg or "expired" in msg:
        return FailureType.AUTH_EXPIRED
    if "already exists" in msg or "duplicate" in msg:
        return FailureType.DUPLICATE
    if "validation" in msg or "invalid" in msg:
        return FailureType.VALIDATION
    if "connection" in msg or "unavailable" in msg or "refused" in msg:
        return FailureType.PROVIDER_OUTAGE
    return FailureType.TRANSIENT


# ═══════════════════════════════════════════════════════════════════
# Circuit Breaker
# ═══════════════════════════════════════════════════════════════════

class CircuitState(Enum):
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing — reject requests
    HALF_OPEN = "half_open"   # Testing recovery


class CircuitBreaker:
    """Prevents cascading failures by stopping calls to a failing provider."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute a function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._recovery_timed_out():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker OPEN for {self.name}")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self.failure_count = 0
        self.last_failure_time = None
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.half_open_calls = 0

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _recovery_timed_out(self) -> bool:
        if not self.last_failure_time:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def get_state(self) -> CircuitState:
        if self.state == CircuitState.OPEN and self._recovery_timed_out():
            self.state = CircuitState.HALF_OPEN
            self.half_open_calls = 0
        return self.state


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is open."""
    pass


# ═══════════════════════════════════════════════════════════════════
# Idempotency
# ═══════════════════════════════════════════════════════════════════

class IdempotencyRegistry:
    """Ensures operations with the same idempotency key are only performed once."""

    def __init__(self):
        self._keys: dict[str, dict] = {}

    def check_and_set(self, key: str, ttl_seconds: int = 3600) -> bool:
        """Check if an idempotency key has been used.

        Returns True if this is a new key (operation should proceed).
        Returns False if key was already processed (operation is a duplicate).
        """
        if key in self._keys:
            entry = self._keys[key]
            if (datetime.utcnow() - entry["created"]).total_seconds() < ttl_seconds:
                return False  # Duplicate within TTL
        self._keys[key] = {"created": datetime.utcnow()}
        return True

    def get_result(self, key: str) -> Optional[dict]:
        """Get the stored result for a duplicate key."""
        return self._keys.get(key, {}).get("result")

    def store_result(self, key: str, result: dict) -> None:
        """Store the result for a completed operation."""
        if key in self._keys:
            self._keys[key]["result"] = result

    def cleanup_expired(self, ttl_seconds: int = 3600) -> int:
        """Remove expired keys. Returns count removed."""
        now = datetime.utcnow()
        expired = [
            k for k, v in self._keys.items()
            if (now - v["created"]).total_seconds() >= ttl_seconds
        ]
        for k in expired:
            del self._keys[k]
        return len(expired)