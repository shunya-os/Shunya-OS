"""SHUNYA Kernel — Universal Timeline.

Implements the chronological record defined in:
    UNIVERSAL_ONTOLOGY.md §12 — Timeline
    UNIVERSAL_ONTOLOGY.md §12.2 — Timeline structure (past/present/future)
    UNIVERSAL_ONTOLOGY.md §19 (O-19) — Timelines are append-only

Every Object has exactly one timeline. The timeline is an append-only
record of all events involving the object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Timeline event
# ---------------------------------------------------------------------------

@dataclass
class TimelineEvent:
    """A single event on an object's timeline.

    Attributes:
        event_id: Unique event identifier
        event_type: Canonical event type (from Ontology §8.3)
        timestamp: When the event occurred
        title: Short human-readable title
        description: Longer description
        actor: Who or what caused the event
        importance: 0.0 (trivial) to 1.0 (critical)
        payload: Additional event-specific data
    """
    event_id: str
    event_type: str
    timestamp: datetime
    title: str = ""
    description: str = ""
    actor: str = ""
    importance: float = 0.5
    payload: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Timeline (append-only)
# ---------------------------------------------------------------------------

class Timeline:
    """Append-only chronological record for an Object.

    Constitutional invariants enforced:
        O-02: History is immutable (events cannot be removed)
        O-19: Timelines are append-only (events can be added but never removed)
        O-09: Context is never destroyed (timeline events preserved)

    Every Object has exactly one Timeline (Ontology §12.1).
    """

    def __init__(self, object_id: str):
        self._object_id = object_id
        self._past: List[TimelineEvent] = []
        self._expected_future: List[TimelineEvent] = []
        self._alternative_futures: Dict[str, List[TimelineEvent]] = {}

    @property
    def object_id(self) -> str:
        return self._object_id

    @property
    def past(self) -> List[TimelineEvent]:
        """All events that have occurred (immutable, O-02)."""
        return list(self._past)

    @property
    def expected_future(self) -> List[TimelineEvent]:
        """Projected future events (mutable, updated with new knowledge)."""
        return list(self._expected_future)

    @property
    def all_events(self) -> List[TimelineEvent]:
        """All past events and expected future events, chronologically."""
        return sorted(
            self._past + self._expected_future,
            key=lambda e: e.timestamp,
        )

    @property
    def event_count(self) -> int:
        return len(self._past)

    def append(self, event: TimelineEvent) -> None:
        """Add an event to the past timeline (append-only, O-19).

        Args:
            event: The event to append
        """
        self._past.append(event)

    def add_expected(self, event: TimelineEvent) -> None:
        """Add a projected future event.

        Future events are mutable and can be replaced when knowledge changes.
        """
        # Replace existing future event with same event_id
        for i, existing in enumerate(self._expected_future):
            if existing.event_id == event.event_id:
                self._expected_future[i] = event
                return
        self._expected_future.append(event)

    def remove_expected(self, event_id: str) -> bool:
        """Remove a projected future event.

        Returns True if the event was found and removed.
        """
        for i, existing in enumerate(self._expected_future):
            if existing.event_id == event_id:
                self._expected_future.pop(i)
                return True
        return False

    def promote_to_past(self, event_id: str) -> bool:
        """Promote a future event to the past timeline.

        Called when a projected event actually occurs.
        Returns True if the event was promoted.
        """
        for i, event in enumerate(self._expected_future):
            if event.event_id == event_id:
                self._expected_future.pop(i)
                self._past.append(event)
                return True
        return False

    def add_alternative_future(
        self, scenario: str, events: List[TimelineEvent]
    ) -> None:
        """Add an alternative timeline for what-if scenarios.

        Args:
            scenario: Name of the scenario (e.g., "best_case", "worst_case")
            events: Projected events for this scenario
        """
        self._alternative_futures[scenario] = list(events)

    def get_alternative_future(self, scenario: str) -> List[TimelineEvent]:
        """Get events for an alternative timeline scenario."""
        return list(self._alternative_futures.get(scenario, []))

    def get_events_in_range(
        self, start: datetime, end: datetime
    ) -> List[TimelineEvent]:
        """Get all past events within a time range."""
        return [
            e for e in self._past
            if start <= e.timestamp <= end
        ]

    def get_events_by_type(self, event_type: str) -> List[TimelineEvent]:
        """Get all past events of a specific type."""
        return [e for e in self._past if e.event_type == event_type]

    def query(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        min_importance: float = 0.0,
        max_events: int = 100,
    ) -> List[TimelineEvent]:
        """Query past events with filters."""
        results = self._past
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if actor:
            results = [e for e in results if e.actor == actor]
        if min_importance > 0.0:
            results = [e for e in results if e.importance >= min_importance]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:max_events]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the timeline for projection."""
        return {
            "object_id": self._object_id,
            "past_count": len(self._past),
            "future_count": len(self._expected_future),
            "past": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "timestamp": e.timestamp.isoformat(),
                    "title": e.title,
                    "importance": e.importance,
                }
                for e in self._past[-20:]  # Last 20 for projection
            ],
            "expected_future": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "timestamp": e.timestamp.isoformat(),
                    "title": e.title,
                }
                for e in self._expected_future[:10]
            ],
        }