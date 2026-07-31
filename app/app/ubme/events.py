"""UBME Event Bus — Simple in-process publish/subscribe event system.

Every metadata change (create, update, delete, transition) emits events.
Automation, AI, Timeline, and Notifications can subscribe.
"""

from __future__ import annotations

import enum
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable


class EventType(str, enum.Enum):
    OBJECT_CREATED = "object.created"
    OBJECT_UPDATED = "object.updated"
    OBJECT_DELETED = "object.deleted"
    OBJECT_TRANSITIONED = "object.transitioned"
    MODULE_CREATED = "module.created"
    MODULE_DELETED = "module.deleted"


EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    """Simple in-process publish/subscribe event bus.

    Subscribers are called synchronously in registration order.
    For async/out-of-process subscribers, use the Notification Runtime.
    """

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._wildcard_subscribers: list[EventHandler] = []

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Register a handler for ALL events (wildcard)."""
        self._wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a handler. No-op if not found."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
            except ValueError:
                pass

    def emit(self, event_type: EventType, **data: Any) -> None:
        """Emit an event with the given data.

        Each event includes:
        - type: EventType value
        - timestamp: ISO-8601 UTC
        - data: caller-provided keyword arguments
        """
        event: dict[str, Any] = {
            "type": event_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        # Notify type-specific subscribers
        for handler in self._subscribers.get(event_type, []):
            try:
                handler(event)
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    "EventBus handler failed for %s", event_type.value
                )
        # Notify wildcard subscribers
        for handler in self._wildcard_subscribers:
            try:
                handler(event)
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    "EventBus wildcard handler failed for %s", event_type.value
                )

    def clear(self) -> None:
        """Remove all subscribers. Used for testing."""
        self._subscribers.clear()
        self._wildcard_subscribers.clear()


# ── Singleton ──

_BUS: EventBus | None = None


def get_bus() -> EventBus:
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS


def reset_bus() -> None:
    """Reset bus (testing)."""
    global _BUS
    if _BUS:
        _BUS.clear()
    _BUS = None