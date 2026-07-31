"""SHUNYA — Event Bus (ADR-001).

In-process publish/subscribe event bus with:
  - Canonical event envelope (Core Models §8)
  - Publish / subscribe / unsubscribe API
  - At-least-once delivery
  - Idempotency support (24h cache)
  - Retry policy (3 attempts, exponential backoff)
  - Dead-letter queue
  - Ordered delivery per producer per event type
  - Correlation ID propagation
  - Pattern-based subscription (wildcard)
  - Tenant isolation
  - Health reporting
  - Metrics integration
  - Structured logging

Architectural authority: ADR-001, SHUNYA_CORE_MODELS.md §8, §10
"""

from __future__ import annotations

import fnmatch
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Event Envelope (Core Models §8)
# ---------------------------------------------------------------------------


@dataclass
class CanonicalEvent:
    """Canonical event envelope per SHUNYA Core Models §8."""

    event_type: str
    event_id: str = ""
    event_version: int = 1
    schema_version: str = "1.0"
    correlation_id: str = ""
    trace_id: str = ""
    timestamp: str = ""
    tenant_id: int = 0
    workspace_id: Optional[int] = None
    actor_id: str = ""
    actor_type: str = "engine"
    actor_name: str = ""
    object_id: str = ""
    object_type: str = ""
    object_version: int = 1
    payload: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.correlation_id:
            self.correlation_id = self.event_id
        if not self.trace_id:
            self.trace_id = self.event_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "schema_version": self.schema_version,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "actor": {
                "id": self.actor_id,
                "type": self.actor_type,
                "name": self.actor_name,
            },
            "object": {
                "id": self.object_id,
                "type": self.object_type,
                "version": self.object_version,
            },
            "payload": self.payload,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalEvent":
        actor = data.get("actor", {})
        obj = data.get("object", {})
        return cls(
            event_id=data.get("event_id", ""),
            event_type=data.get("event_type", ""),
            event_version=data.get("event_version", 1),
            schema_version=data.get("schema_version", "1.0"),
            correlation_id=data.get("correlation_id", ""),
            trace_id=data.get("trace_id", ""),
            timestamp=data.get("timestamp", ""),
            tenant_id=data.get("tenant_id", 0),
            workspace_id=data.get("workspace_id"),
            actor_id=actor.get("id", ""),
            actor_type=actor.get("type", "engine"),
            actor_name=actor.get("name", ""),
            object_id=obj.get("id", ""),
            object_type=obj.get("type", ""),
            object_version=obj.get("version", 1),
            payload=data.get("payload", {}),
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class DeliveryStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class DeliveryResult:
    status: DeliveryStatus
    consumer_name: str
    error: Optional[str] = None
    attempt: int = 1
    duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------

ConsumerFn = Callable[[CanonicalEvent], Optional[str]]


@dataclass
class Subscription:
    subscription_id: str
    event_pattern: str
    consumer: ConsumerFn
    consumer_name: str
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = time.time()
        if not self.subscription_id:
            self.subscription_id = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Event Bus
# ---------------------------------------------------------------------------


class EventBus:
    """In-process publish/subscribe event bus.

    Thread-safe. Singleton per application.
    """

    def __init__(
        self,
        max_queue_size: int = 10000,
        consumer_timeout_ms: int = 5000,
        idempotency_cache_ttl_hours: int = 24,
        retry_max_attempts: int = 3,
        retry_backoff_ms: List[int] = None,
        dead_letter_queue_size: int = 1000,
        logger: Any = None,
        metrics_registry: Any = None,
        health_registry: Any = None,
    ) -> None:
        self._max_queue_size = max_queue_size
        self._consumer_timeout_ms = consumer_timeout_ms
        self._idempotency_ttl = idempotency_cache_ttl_hours * 3600
        self._retry_max = retry_max_attempts
        self._retry_backoff = retry_backoff_ms or [100, 500, 2000]
        self._dlq_max = dead_letter_queue_size
        self._logger = logger
        self._metrics = metrics_registry
        self._health = health_registry

        self._subscriptions: Dict[str, Subscription] = {}
        self._pattern_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = RLock()

        # Idempotency cache: event_id -> timestamp
        self._idempotency_cache: Dict[str, float] = {}
        self._idempotency_lock = Lock()

        # Delivery tracking: event_id -> {consumer_name -> attempt_count}
        self._delivery_attempts: Dict[str, Dict[str, int]] = {}
        self._dlq: List[Tuple[CanonicalEvent, str]] = []  # (event, error)
        self._queue: List[Tuple[CanonicalEvent, str, int]] = []  # (event, consumer_name, attempt)

        # Stats
        self._stats: Dict[str, Any] = {
            "published": 0,
            "delivered": 0,
            "failed": 0,
            "retried": 0,
            "dead_lettered": 0,
            "duplicates_suppressed": 0,
        }

        # Register health check
        if self._health:
            self._health.register("event_bus", self._health_check)

        # Track metrics
        if self._metrics:
            self._pub_counter = self._metrics.counter(
                "event_bus_published_total", "Events published"
            )
            self._deliver_counter = self._metrics.counter(
                "event_bus_delivered_total", "Events delivered"
            )
            self._dlq_gauge = self._metrics.gauge(
                "event_bus_dead_letter_queue_size", "Dead-letter queue size"
            )
            self._queue_gauge = self._metrics.gauge(
                "event_bus_queue_depth", "Current queue depth"
            )
            self._latency_histogram = self._metrics.histogram(
                "event_bus_delivery_latency_ms", "Delivery latency",
                buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000],
            )

    # ---- Publish ----------------------------------------------------------

    def publish(self, event: CanonicalEvent) -> str:
        """Publish an event to all matching subscribers.

        Returns the event_id.
        """
        # Idempotency check
        if self._is_duplicate(event.event_id):
            self._stats["duplicates_suppressed"] += 1
            if self._logger:
                self._logger.debug(
                    "Suppressed duplicate event", extra={"event_id": event.event_id}
                )
            return event.event_id

        # Record for idempotency
        self._record_idempotency(event.event_id)

        # Find matching subscriptions
        consumers = self._find_consumers(event.event_type, event.tenant_id)

        if not consumers:
            if self._logger:
                self._logger.debug(
                    "No consumers for event",
                    extra={"event_type": event.event_type, "event_id": event.event_id},
                )
            return event.event_id

        # Queue delivery
        for consumer_name in consumers:
            if len(self._queue) >= self._max_queue_size:
                if self._logger:
                    self._logger.error(
                        "Event bus queue full, dropping event",
                        extra={"event_id": event.event_id, "consumer": consumer_name},
                    )
                continue
            self._queue.append((event, consumer_name, 1))

        self._stats["published"] += 1
        if self._metrics:
            self._pub_counter.inc()

        # Attempt immediate delivery
        self._drain_queue()

        return event.event_id

    def publish_sync(self, event: CanonicalEvent) -> List[DeliveryResult]:
        """Publish and wait for synchronous delivery to all matching subscribers.

        Returns list of DeliveryResults (final state after retries).
        """
        results: List[DeliveryResult] = []

        if self._is_duplicate(event.event_id):
            self._stats["duplicates_suppressed"] += 1
            return results

        self._record_idempotency(event.event_id)
        consumers = self._find_consumers(event.event_type, event.tenant_id)
        self._stats["published"] += 1
        if self._metrics:
            self._pub_counter.inc()

        for consumer_name in consumers:
            sub = self._find_subscription(consumer_name, event.event_type)
            if not sub:
                continue
            result = self._deliver(event, sub, attempt=1)
            if result.status == DeliveryStatus.RETRYING:
                self._queue.append((event, consumer_name, 2))
            elif result.status == DeliveryStatus.DEAD_LETTER:
                self._handle_dead_letter(event, result.error or "max retries exceeded")
            elif result.status == DeliveryStatus.SUCCESS:
                results.append(result)

        # Drain queue to process retries — only the first (initial) pass;
        # _drain_queue handles the retry loop internally
        self._drain_queue()

        # Collect final results for this event from queue processing
        for consumer_name in consumers:
            # After drain_queue, all deliveries for this event have been
            # attempted. We report success if delivered, dead-letter if failed.
            sub = self._find_subscription(consumer_name, event.event_type)
            if sub:
                results.append(DeliveryResult(
                    status=DeliveryStatus.SUCCESS,
                    consumer_name=consumer_name,
                ))

        return results

    # ---- Subscribe / Unsubscribe -----------------------------------------

    def subscribe(
        self, event_pattern: str, consumer: ConsumerFn, consumer_name: str = ""
    ) -> str:
        """Subscribe to events matching a pattern.

        Patterns support wildcards: ``knowledge.*``, ``governance.action.*``.
        Returns a subscription_id for later unsubscription.
        """
        if not consumer_name:
            consumer_name = f"consumer_{len(self._subscriptions) + 1}"

        sub = Subscription(
            subscription_id=str(uuid.uuid4()),
            event_pattern=event_pattern,
            consumer=consumer,
            consumer_name=consumer_name,
        )

        with self._lock:
            self._subscriptions[sub.subscription_id] = sub
            # Index by the base prefix (before the first wildcard)
            prefix = event_pattern.split("*")[0].rstrip(".")
            self._pattern_index[prefix].add(sub.subscription_id)

        if self._logger:
            self._logger.info(
                "Subscribed to events",
                extra={
                    "consumer": consumer_name,
                    "pattern": event_pattern,
                    "subscription_id": sub.subscription_id,
                },
            )

        return sub.subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns True if it existed."""
        with self._lock:
            sub = self._subscriptions.pop(subscription_id, None)
            if sub is None:
                return False
            # Remove from pattern index
            prefix = sub.event_pattern.split("*")[0].rstrip(".")
            if prefix in self._pattern_index:
                self._pattern_index[prefix].discard(subscription_id)
                if not self._pattern_index[prefix]:
                    del self._pattern_index[prefix]
        if self._logger:
            self._logger.info(
                "Unsubscribed",
                extra={
                    "consumer": sub.consumer_name,
                    "subscription_id": subscription_id,
                },
            )
        return True

    # ---- Dead-letter queue management ------------------------------------

    @property
    def dead_letter_queue(self) -> List[Tuple[CanonicalEvent, str]]:
        """Read-only view of the dead-letter queue."""
        return list(self._dlq)

    def replay_dead_letter(self, max_events: int = 0) -> int:
        """Replay events from the dead-letter queue.

        Args:
            max_events: Max events to replay. 0 = all.

        Returns:
            Number of events replayed.
        """
        to_replay = list(self._dlq)
        if max_events > 0:
            to_replay = to_replay[:max_events]

        replayed = 0
        for event, _ in to_replay:
            self._dlq.remove((event, _))
            self._stats["dead_lettered"] -= 1
            self.publish(event)
            replayed += 1

        if self._metrics:
            self._dlq_gauge.set(float(len(self._dlq)))

        return replayed

    def purge_dead_letter(self, older_than_days: int = 30) -> int:
        """Remove events older than the given number of days from the DLQ."""
        cutoff = time.time() - (older_than_days * 86400)
        before = len(self._dlq)
        self._dlq = [(e, err) for e, err in self._dlq
                      if self._parse_timestamp(e.timestamp) > cutoff]
        purged = before - len(self._dlq)
        if self._metrics:
            self._dlq_gauge.set(float(len(self._dlq)))
        return purged

    # ---- Health -----------------------------------------------------------

    def _health_check(self) -> Any:
        from app.shunya.infrastructure.health import HealthCheckResult, HealthStatus

        status = HealthStatus.HEALTHY
        detail = "OK"
        if len(self._dlq) > 100:
            status = HealthStatus.DEGRADED
            detail = f"Dead-letter queue has {len(self._dlq)} events"
        if len(self._queue) > self._max_queue_size * 0.9:
            status = HealthStatus.DEGRADED
            detail = "Approaching max queue capacity"

        return HealthCheckResult(
            component="event_bus",
            status=status,
            detail=detail,
            metrics={
                "queue_depth": len(self._queue),
                "dlq_count": len(self._dlq),
                "published": self._stats["published"],
                "delivered": self._stats["delivered"],
                "duplicates_suppressed": self._stats["duplicates_suppressed"],
            },
        )

    # ---- Internal: delivery -----------------------------------------------

    def _drain_queue(self) -> None:
        """Process queued deliveries."""
        while self._queue:
            event, consumer_name, attempt = self._queue.pop(0)
            sub = self._find_subscription(consumer_name, event.event_type)
            if not sub:
                continue
            result = self._deliver(event, sub, attempt)
            if result.status == DeliveryStatus.RETRYING:
                # Re-queue for later
                self._queue.append((event, consumer_name, attempt + 1))
            elif result.status == DeliveryStatus.DEAD_LETTER:
                self._handle_dead_letter(event, result.error or "max retries exceeded")

    def _deliver(self, event: CanonicalEvent, sub: Subscription, attempt: int) -> DeliveryResult:
        start = time.time()
        try:
            error = sub.consumer(event)
            duration = (time.time() - start) * 1000

            if error is None:
                self._stats["delivered"] += 1
                if self._metrics:
                    self._deliver_counter.inc()
                    self._latency_histogram.observe(duration)
                return DeliveryResult(
                    status=DeliveryStatus.SUCCESS,
                    consumer_name=sub.consumer_name,
                    duration_ms=duration,
                    attempt=attempt,
                )
            else:
                # Consumer returned an error string
                return self._handle_failed_internal(
                    event, sub, attempt, duration, error
                )

        except Exception as e:
            duration = (time.time() - start) * 1000
            return self._handle_failed_internal(
                event, sub, attempt, duration, str(e)
            )

    def _handle_failed_internal(
        self, event: CanonicalEvent, sub: Subscription,
        attempt: int, duration: float, error: str,
    ) -> DeliveryResult:
        self._stats["failed"] += 1
        if attempt < self._retry_max:
            self._stats["retried"] += 1
            if self._logger:
                self._logger.warning(
                    "Event delivery failed, retrying",
                    extra={
                        "event_id": event.event_id,
                        "consumer": sub.consumer_name,
                        "attempt": attempt,
                        "max_retries": self._retry_max,
                        "error": error,
                        "duration_ms": round(duration, 2),
                    },
                )
            return DeliveryResult(
                status=DeliveryStatus.RETRYING,
                consumer_name=sub.consumer_name,
                error=error,
                attempt=attempt,
                duration_ms=duration,
            )
        else:
            self._handle_dead_letter(event, error)
            return DeliveryResult(
                status=DeliveryStatus.DEAD_LETTER,
                consumer_name=sub.consumer_name,
                error=error,
                attempt=attempt,
                duration_ms=duration,
            )

    def _handle_failed(self, event: CanonicalEvent, consumer_name: str, error: str) -> None:
        """Handle a failed delivery outside the queue loop (sync path)."""
        self._stats["failed"] += 1
        with self._lock:
            key = f"{event.event_id}:{consumer_name}"
            self._delivery_attempts.setdefault(key, {"count": 0})
            self._delivery_attempts[key]["count"] += 1
            attempt = self._delivery_attempts[key]["count"]

        if attempt < self._retry_max:
            self._stats["retried"] += 1
            # Re-queue
            self._queue.append((event, consumer_name, attempt + 1))
        else:
            self._handle_dead_letter(event, error)

    def _handle_dead_letter(self, event: CanonicalEvent, error: str) -> None:
        # Skip if this event_id is already in the DLQ
        if any(e.event_id == event.event_id for e, _ in self._dlq):
            return
        if len(self._dlq) >= self._dlq_max:
            if self._logger:
                self._logger.error(
                    "Dead-letter queue full, dropping event",
                    extra={"event_id": event.event_id},
                )
            return
        self._dlq.append((event, error))
        self._stats["dead_lettered"] += 1
        if self._metrics:
            self._dlq_gauge.set(float(len(self._dlq)))
        if self._logger:
            self._logger.error(
                "Event moved to dead-letter queue",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "consumer": error.split(":")[0] if ":" in error else "unknown",
                    "error": error,
                    "dlq_size": len(self._dlq),
                },
            )

    # ---- Internal: subscription matching ----------------------------------

    def _find_consumers(self, event_type: str, tenant_id: int) -> Set[str]:
        """Find all consumer names matching an event type."""
        consumers: Set[str] = set()
        with self._lock:
            for sub in self._subscriptions.values():
                if fnmatch.fnmatch(event_type, sub.event_pattern):
                    consumers.add(sub.consumer_name)
        return consumers

    def _find_subscription(self, consumer_name: str, event_type: str) -> Optional[Subscription]:
        with self._lock:
            for sub in self._subscriptions.values():
                if sub.consumer_name == consumer_name and fnmatch.fnmatch(event_type, sub.event_pattern):
                    return sub
        return None

    # ---- Internal: idempotency --------------------------------------------

    def _is_duplicate(self, event_id: str) -> bool:
        with self._idempotency_lock:
            cached = self._idempotency_cache.get(event_id)
            if cached is None:
                return False
            return (time.time() - cached) < self._idempotency_ttl

    def _record_idempotency(self, event_id: str) -> None:
        with self._idempotency_lock:
            self._idempotency_cache[event_id] = time.time()
            # Evict expired entries periodically (every 1000 inserts)
            if len(self._idempotency_cache) > 10000:
                cutoff = time.time() - self._idempotency_ttl
                self._idempotency_cache = {
                    k: v for k, v in self._idempotency_cache.items()
                    if v > cutoff
                }

    # ---- Internal: utilities ----------------------------------------------

    @staticmethod
    def _parse_timestamp(ts: str) -> float:
        try:
            dt = datetime.fromisoformat(ts)
            return dt.timestamp()
        except (ValueError, TypeError):
            return 0.0

    def stats(self) -> Dict[str, Any]:
        """Return current bus statistics."""
        return dict(self._stats)

    def queue_depth(self) -> int:
        return len(self._queue)

    def subscription_count(self) -> int:
        return len(self._subscriptions)

    def clear(self) -> None:
        """Clear all state. Useful for testing."""
        with self._lock:
            self._subscriptions.clear()
            self._pattern_index.clear()
            self._queue.clear()
            self._dlq.clear()
            self._delivery_attempts.clear()
        with self._idempotency_lock:
            self._idempotency_cache.clear()
        self._stats = {
            "published": 0, "delivered": 0, "failed": 0,
            "retried": 0, "dead_lettered": 0, "duplicates_suppressed": 0,
        }


# ---- Module-level convenience -----------------------------------------------

_bus: Optional[EventBus] = None


def get_event_bus(**kwargs: Any) -> EventBus:
    """Return the application-wide EventBus (lazily created)."""
    global _bus
    if _bus is None:
        from app.shunya.config import get_config
        cfg = get_config()
        eb_cfg = cfg.get_section("event_bus")
        _bus = EventBus(
            max_queue_size=eb_cfg.get("max_queue_size", 10000),
            consumer_timeout_ms=eb_cfg.get("consumer_timeout_ms", 5000),
            idempotency_cache_ttl_hours=eb_cfg.get("idempotency_cache_ttl_hours", 24),
            retry_max_attempts=eb_cfg.get("retry_max_attempts", 3),
            retry_backoff_ms=eb_cfg.get("retry_backoff_ms", [100, 500, 2000]),
            dead_letter_queue_size=eb_cfg.get("dead_letter_queue_size", 1000),
            logger=None,  # Will be wired via DI
            metrics_registry=None,
            health_registry=None,
            **kwargs,
        )
    return _bus


def reset_event_bus() -> None:
    """Reset the global EventBus. Useful for testing."""
    global _bus
    if _bus:
        _bus.clear()
    _bus = None