"""
SHUNYA Temporal Intelligence — Organizational Timeline

A universal timeline where every runtime event becomes part of one temporal sequence.
Business agnostic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TimelineEvent:
    """A single event in the organizational timeline."""

    event_id: str
    event_type: str
    source: str  # 'cortex', 'decision', 'execution', 'observation', 'learning', 'temporal'
    label: str
    description: str
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "label": self.label,
            "description": self.description,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class Timeline:
    """A universal, append-only timeline of organizational events."""

    def __init__(self):
        self._events: list[TimelineEvent] = []
        self._counter: int = 0

    def record(self, event_type: str, source: str, label: str, description: str = "",
               metadata: dict = None) -> TimelineEvent:
        """Record a new event in the timeline."""
        self._counter += 1
        now = datetime.now(timezone.utc).isoformat()
        event = TimelineEvent(
            event_id=f"evt_{self._counter}",
            event_type=event_type,
            source=source,
            label=label,
            description=description,
            timestamp=now,
            metadata=metadata or {},
        )
        self._events.append(event)
        return event

    def get_events(self, source: str = "", event_type: str = "", limit: int = 50) -> list[TimelineEvent]:
        """Get events, optionally filtered by source or type."""
        events = self._events
        if source:
            events = [e for e in events if e.source == source]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_by_source(self, source: str, limit: int = 20) -> list[TimelineEvent]:
        return self.get_events(source=source, limit=limit)

    @property
    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
        self._counter = 0


_timeline: Optional[Timeline] = None


def get_timeline() -> Timeline:
    global _timeline
    if _timeline is None:
        _timeline = Timeline()
    return _timeline


def reset_timeline() -> None:
    global _timeline
    _timeline = None