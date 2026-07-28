"""
SHUNYA — Event Engine

The Event Engine is the canonical event bus for the SHUNYA runtime. It
provides asynchronous event emission, typed subscriptions, at-least-once
delivery semantics, and event replay capabilities.

Public API:
    - EventEngine       — In-memory event bus with subscriptions and replay
    - SystemEvent       — Immutable dataclass for system events
    - EventType         — Canonical event type enumeration
    - EventPriority     — Priority level enumeration
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