"""
SHUNYA — Event Engine

GATE 2.1 CONSOLIDATION: QUARANTINED — This in-memory EventEngine is NOT
the canonical event bus. It is used only by tests.

The canonical event bus is app/shunya/infrastructure/event_bus.py
(CanonicalEvent, EventBus with Redis relay, idempotency, DLQ).

Kept as a test-only utility. Do not use in production code.
"""

from __future__ import annotations

from core.event.engine import EventEngine
from core.event.models import (
    EventPriority,
    EventType,
    SystemEvent,
)

__all__ = [
    "EventEngine",
    "EventPriority",
    "EventType",
    "SystemEvent",
]