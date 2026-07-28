"""
SHUNYA Universal Business Graph — Graph Events

Everything changing the graph becomes a GraphEvent.
Integrates with Temporal Intelligence.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class GraphEvent:
    event_id: str
    event_type: str
    entity_id: str
    payload: dict = field(default_factory=dict)
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class GraphEventStore:
    def __init__(self):
        self._events: list[GraphEvent] = []
        self._counter: int = 0

    def record(self, event_type: str, entity_id: str, payload: dict = None) -> GraphEvent:
        self._counter += 1
        evt = GraphEvent(
            event_id=f"ge_{self._counter}",
            event_type=event_type,
            entity_id=entity_id,
            payload=payload or {},
        )
        self._events.append(evt)
        return evt

    def get_events(self, entity_id: str = "", limit: int = 50) -> list[GraphEvent]:
        if entity_id:
            return [e for e in self._events if e.entity_id == entity_id][-limit:]
        return self._events[-limit:]

    @property
    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
        self._counter = 0


_store: Optional[GraphEventStore] = None


def get_store() -> GraphEventStore:
    global _store
    if _store is None:
        _store = GraphEventStore()
    return _store


def reset_store() -> None:
    global _store
    _store = None