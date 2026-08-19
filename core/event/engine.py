"""
SHUNYA — Event Engine (Event Bus)

GATE 2.1 CONSOLIDATION: QUARANTINED — This in-memory EventEngine is NOT
the canonical event bus. It is used only by tests.

The canonical event bus is app/shunya/infrastructure/event_bus.py
(CanonicalEvent, EventBus with Redis relay, idempotency, DLQ).

Kept as a test-only utility. Do not use in production code.
New production event code must use the canonical EventBus.

Capabilities:
    - Emit typed SystemEvent objects with full event envelope
    - Subscribe to specific event types with callable handlers
    - Unsubscribe by subscription ID
    - Query events by type, object, source, and time range
    - Replay historical events to current subscribers
    - At-least-once delivery with failure isolation
    - Event statistics by type and priority

References:
    - docs/canon/00_universal_ontology.md §8 (Event)
    - docs/canon/05_runtime_canon.md §4 (Event System)
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from core.event.models import (
    EventPriority,
    EventType,
    SystemEvent,
)

logger = logging.getLogger(__name__)


# ── Type aliases ───────────────────────────────────────────────────────────────

EventHandler = Callable[[SystemEvent], None]
"""Type alias for event handler callables.

A handler receives a single SystemEvent argument and returns None.
Handlers should be idempotent — they may be called multiple times
for the same event during replay operations.
"""


# ── EventEngine ────────────────────────────────────────────────────────────────


class EventEngine:
    """In-memory event bus with typed subscriptions and replay.

    The engine stores every emitted event in chronological order and
    delivers them to registered subscribers. Subscribers are invoked
    asynchronously (in separate threads) so that a slow or failing
    handler never blocks the event bus.

    Delivery semantics:
        - **At-least-once**: Events are durably stored before dispatch.
          Subscribers may receive the same event more than once during
          replay, so handlers should be idempotent.
        - **Ordered**: Within a single event_type, delivery order follows
          timestamp order.
        - **Isolated**: Exceptions in subscriber handlers are caught and
          logged. A failing subscriber never crashes the bus or prevents
          delivery to other subscribers.

    Example::

        engine = EventEngine()

        # Subscribe to an event type
        def on_object_created(event: SystemEvent) -> None:
            print(f"Object created: {event.object_id}")

        sub_id = engine.subscribe(EventType.OBJECT_CREATED, on_object_created)

        # Emit an event
        event = engine.emit(
            event_type=EventType.OBJECT_CREATED,
            source="object_factory",
            actor_id="system",
            object_id="obj_abc_123",
            payload={"name": "Widget Alpha"},
        )

        # Replay events
        count = engine.replay(event_type=EventType.OBJECT_CREATED)

        # Clean up
        engine.unsubscribe(sub_id)
    """

    def __init__(self) -> None:
        """Initialize an empty event bus."""
        # All events, in emission order
        self._events: list[SystemEvent] = []
        # Index by event_id for fast lookup
        self._events_by_id: dict[str, SystemEvent] = {}
        # Index by object_id for object-scoped queries
        self._events_by_object: dict[str, list[SystemEvent]] = {}
        # Index by source for source-scoped queries
        self._events_by_source: dict[str, list[SystemEvent]] = {}

        # Subscriptions: event_type -> [(subscription_id, handler)]
        self._subscriptions: dict[str, list[tuple[str, EventHandler]]] = {}
        # Reverse map: subscription_id -> event_type (for unsubscription)
        self._sub_id_to_type: dict[str, str] = {}

        # Counter for subscription IDs
        self._sub_counter: int = 0
        # Lock for subscription mutations
        self._sub_lock = threading.Lock()

    # ── Emission ──────────────────────────────────────────────────────────────

    def emit(
        self,
        event_type: EventType | str,
        source: str,
        actor_id: str,
        object_id: str,
        payload: dict[str, Any] | None = None,
        related_object_ids: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        priority: EventPriority | str | None = None,
        ttl_seconds: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SystemEvent:
        """Emit a new event to the event bus.

        The event is created, stored, and dispatched to all subscribers
        of its event type. Dispatch is asynchronous — the method returns
        immediately after storage and dispatch is triggered in background
        threads.

        Args:
            event_type: Canonical event type (EventType member or string).
            source: Component/engine that generated the event
                (e.g., 'object_factory', 'observer_engine').
            actor_id: ObjectID of the actor that caused the event.
            object_id: ObjectID of the primary object this event is about.
            payload: Event-specific data payload. Defaults to empty dict.
            related_object_ids: Other objects involved. Defaults to empty list.
            evidence_ids: Evidence references. Defaults to empty list.
            priority: Delivery priority. Defaults to EventPriority.NORMAL.
            ttl_seconds: Time-to-live in seconds. None means no expiry.
            metadata: Extensible metadata. Defaults to empty dict.

        Returns:
            The newly created SystemEvent, which is now immutable.

        Raises:
            ValueError: If event_type is not a valid EventType.
        """
        # Normalise event_type
        if isinstance(event_type, str):
            event_type = EventType.from_string(event_type)
        elif not isinstance(event_type, EventType):
            raise ValueError(f"Invalid event_type: {event_type!r}")

        # Normalise priority
        if isinstance(priority, str):
            priority = EventPriority(priority)
        elif priority is None:
            priority = EventPriority.NORMAL
        elif not isinstance(priority, EventPriority):
            raise ValueError(f"Invalid priority: {priority!r}")

        event = SystemEvent(
            event_type=event_type,
            source=source,
            actor_id=actor_id,
            object_id=object_id,
            payload=payload or {},
            related_object_ids=related_object_ids or [],
            evidence_ids=evidence_ids or [],
            priority=priority,
            ttl_seconds=ttl_seconds,
            metadata=metadata or {},
        )

        # Store the event
        self._events.append(event)
        self._events_by_id[event.event_id] = event

        # Index by object
        if object_id not in self._events_by_object:
            self._events_by_object[object_id] = []
        self._events_by_object[object_id].append(event)

        # Index by source
        if source not in self._events_by_source:
            self._events_by_source[source] = []
        self._events_by_source[source].append(event)

        # Dispatch to subscribers asynchronously
        self._dispatch(event)

        return event

    # ── Subscription Management ───────────────────────────────────────────────

    def subscribe(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> str:
        """Subscribe to an event type.

        The handler will be called for every event of the specified type,
        including events emitted *after* subscription and events replayed
        via ``replay()``.

        Handlers are called asynchronously. Exceptions in handlers are
        caught and logged — they do not crash the bus or affect other
        subscribers.

        Args:
            event_type: The event type to subscribe to. Use a string like
                ``"*"`` or ``"all"`` to subscribe to ALL event types.
            handler: A callable that accepts a single SystemEvent argument.
                The handler should be idempotent (may be called multiple
                times for the same event during replay).

        Returns:
            A subscription_id string that can be used with ``unsubscribe()``.
        """
        # Normalise
        if isinstance(event_type, EventType):
            type_key = event_type.value
        else:
            type_key = event_type

        with self._sub_lock:
            self._sub_counter += 1
            sub_id = f"sub_{self._sub_counter}"

            if type_key not in self._subscriptions:
                self._subscriptions[type_key] = []
            self._subscriptions[type_key].append((sub_id, handler))
            self._sub_id_to_type[sub_id] = type_key

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe a handler from the event bus.

        Args:
            subscription_id: The ID returned by ``subscribe()``.

        Returns:
            True if the subscription was found and removed, False if the
            subscription_id does not exist.
        """
        with self._sub_lock:
            event_type = self._sub_id_to_type.pop(subscription_id, None)
            if event_type is None:
                return False

            handlers = self._subscriptions.get(event_type, [])
            self._subscriptions[event_type] = [
                (sid, h) for sid, h in handlers if sid != subscription_id
            ]

            # Clean up empty lists
            if not self._subscriptions[event_type]:
                del self._subscriptions[event_type]

        return True

    def get_subscriptions(self) -> dict[str, list[str]]:
        """Get all active subscriptions.

        Returns:
            A dict mapping ``event_type`` (string) to a list of
            ``subscription_id`` strings. Subscriptions are live and
            will receive future events.
        """
        with self._sub_lock:
            return {
                event_type: [sid for sid, _ in handlers]
                for event_type, handlers in self._subscriptions.items()
            }

    # ── Event Retrieval ───────────────────────────────────────────────────────

    def get_event(self, event_id: str) -> SystemEvent | None:
        """Get a single event by its ID.

        Args:
            event_id: The UUID v7 string of the event.

        Returns:
            The SystemEvent if found, or None if the event_id is unknown.
        """
        return self._events_by_id.get(event_id)

    def get_events(
        self,
        event_type: EventType | str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[SystemEvent]:
        """Get events matching the given filters.

        Events are returned in chronological order (by emission timestamp).

        Args:
            event_type: Optional filter by event type.
            from_time: Optional ISO-8601 start bound (inclusive).
            to_time: Optional ISO-8601 end bound (inclusive).
            limit: Maximum events to return.
            offset: Number of events to skip (for pagination).

        Returns:
            A list of matching SystemEvent objects.
        """
        if isinstance(event_type, str):
            event_type_filter = EventType.from_string(event_type)
        else:
            event_type_filter = event_type

        result: list[SystemEvent] = []
        for ev in self._events:
            if event_type_filter and ev.event_type != event_type_filter:
                continue
            if from_time and ev.timestamp < from_time:
                continue
            if to_time and ev.timestamp > to_time:
                continue
            result.append(ev)

        if offset > 0:
            result = result[offset:]
        if limit is not None:
            result = result[:limit]
        return result

    def get_events_by_object(
        self,
        object_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[SystemEvent]:
        """Get all events related to a specific object.

        Args:
            object_id: The ObjectID to query.
            limit: Maximum events to return.
            offset: Pagination offset.

        Returns:
            Events for the object, ordered by timestamp ascending.
        """
        events = self._events_by_object.get(object_id, [])
        if offset > 0:
            events = events[offset:]
        if limit is not None:
            events = events[:limit]
        return events

    def get_events_by_source(
        self,
        source: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[SystemEvent]:
        """Get all events from a specific source component.

        Args:
            source: The source component name (e.g., 'object_factory').
            limit: Maximum events to return.
            offset: Pagination offset.

        Returns:
            Events from the source, ordered by timestamp ascending.
        """
        events = self._events_by_source.get(source, [])
        if offset > 0:
            events = events[offset:]
        if limit is not None:
            events = events[:limit]
        return events

    # ── Replay ────────────────────────────────────────────────────────────────

    def replay(
        self,
        event_type: EventType | str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
    ) -> int:
        """Re-emit historical events to current subscribers.

        This replays matching events through the subscription system.
        Events are dispatched to currently registered subscribers only —
        subscribers that existed when the event was first emitted but
        have since been unsubscribed will not receive replayed events.

        This is useful for:
            - Recovering state after a subscriber crash
            - Bootstrapping new subscribers with historical context
            - Testing subscription logic against known event sequences

        Args:
            event_type: Optional filter to replay only a specific type.
            from_time: Optional ISO-8601 start bound (inclusive).
            to_time: Optional ISO-8601 end bound (inclusive).

        Returns:
            The number of events that were dispatched.
        """
        if isinstance(event_type, str):
            event_type_filter = EventType.from_string(event_type)
        else:
            event_type_filter = event_type

        count = 0
        for ev in self._events:
            if event_type_filter and ev.event_type != event_type_filter:
                continue
            if from_time and ev.timestamp < from_time:
                continue
            if to_time and ev.timestamp > to_time:
                continue
            self._dispatch(ev)
            count += 1

        return count

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics.

        Returns:
            A dict with:
                - ``total_events``: Total number of events emitted
                - ``events_by_type``: Dict mapping event_type -> count
                - ``events_by_priority``: Dict mapping priority -> count
                - ``active_subscriptions``: Number of active subscriptions
                - ``unique_objects``: Number of unique objects with events
                - ``unique_sources``: Number of unique sources
        """
        by_type: dict[str, int] = {}
        by_priority: dict[str, int] = {}

        for ev in self._events:
            # Use .value so the dict keys are plain strings
            et = ev.event_type.value
            by_type[et] = by_type.get(et, 0) + 1

            ep = ev.priority.value
            by_priority[ep] = by_priority.get(ep, 0) + 1

        return {
            "total_events": len(self._events),
            "events_by_type": dict(sorted(by_type.items())),
            "events_by_priority": dict(sorted(by_priority.items())),
            "active_subscriptions": len(self._sub_id_to_type),
            "unique_objects": len(self._events_by_object),
            "unique_sources": len(self._events_by_source),
        }

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Reset the event bus to its initial empty state.

        This discards all stored events, but preserves subscriptions.
        Subscriptions survive clear() so that components don't need to
        re-register after a reset. This is primarily useful for testing.

        To also clear subscriptions, call ``clear()`` then iterate over
        ``get_subscriptions()`` and ``unsubscribe()`` each.
        """
        self._events.clear()
        self._events_by_id.clear()
        self._events_by_object.clear()
        self._events_by_source.clear()

    # ── Internal Dispatch ─────────────────────────────────────────────────────

    def _dispatch(self, event: SystemEvent) -> None:
        """Dispatch an event to all matching subscribers.

        Subscribers are invoked in separate daemon threads so that
        handler execution never blocks the event bus. Exceptions in
        handlers are caught and logged.

        The dispatch first checks for type-specific subscriptions, then
        checks for wildcard/all subscriptions.

        Args:
            event: The event to dispatch.
        """
        type_key = event.event_type.value
        handlers: list[EventHandler] = []

        with self._sub_lock:
            # Type-specific handlers
            for sid, handler in self._subscriptions.get(type_key, []):
                handlers.append(handler)

            # Wildcard handlers (subscribe to "*" or "all")
            for wildcard in ("*", "all"):
                for sid, handler in self._subscriptions.get(wildcard, []):
                    handlers.append(handler)

        # Dispatch each handler in its own thread
        for handler in handlers:
            t = threading.Thread(
                target=self._run_handler,
                args=(handler, event),
                daemon=True,
            )
            t.start()

    def _run_handler(self, handler: EventHandler, event: SystemEvent) -> None:
        """Execute a single event handler, catching and logging exceptions.

        Args:
            handler: The handler callable.
            event: The event to pass to the handler.
        """
        try:
            handler(event)
        except Exception:
            logger.exception(
                "Event handler %s failed for event %s (%s)",
                getattr(handler, "__name__", str(handler)),
                event.event_id,
                event.event_type.value,
            )