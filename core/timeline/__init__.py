"""
SHUNYA — Timeline Engine

The Timeline Engine provides the universal timeline service used by every
object. It records immutable, chronologically-ordered events with integrity
hash chaining for tamper-evident audit trails.

Public API:
    - TimelineEngine      — In-memory timeline engine with integrity chains
    - TimelineEvent       — Immutable dataclass for timeline events
    - TimelineEventType   — Canonical event type enumeration
    - compute_event_hash  — SHA-256 integrity hash computation
    - GENESIS_HASH        — The hash of the first event in a chain
"""

from __future__ import annotations

from core.timeline.engine import TimelineEngine
from core.timeline.models import (
    GENESIS_HASH,
    TimelineEvent,
    TimelineEventType,
    compute_event_hash,
)

__all__ = [
    "GENESIS_HASH",
    "TimelineEngine",
    "TimelineEvent",
    "TimelineEventType",
    "compute_event_hash",
]