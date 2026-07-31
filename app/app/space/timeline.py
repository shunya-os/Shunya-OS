"""SHUNYA Phase A1 — Space Timeline Integration.

Every meaningful event appears in one timeline.
Nothing should maintain independent histories.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.space.models import SpaceTimelineEvent
from app.space.store import get_store, SpaceStore


# =========================================================================
# Timeline Categories
# =========================================================================

TIMELINE_CATEGORIES = {
    "communication": "Communication",
    "decision": "Decision",
    "execution": "Execution",
    "document": "Document",
    "evidence": "Evidence",
    "payment": "Payment",
    "approval": "Approval",
    "meeting": "Meeting",
    "observation": "Observation",
    "ai_insight": "AI Insight",
}


class SpaceTimelineManager:
    """Manages the unified timeline for a Space.

    Every meaningful event appears in one timeline.
    Integrates with the existing Kernel Timeline (app.kernel.timeline).
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    # ------------------------------------------------------------------
    # Event management
    # ------------------------------------------------------------------

    def add_event(self, space_id: str, event_type: str,
                  title: str = "",
                  description: str = "",
                  actor: str = "",
                  importance: float = 0.5,
                  category: str = "",
                  payload: Optional[Dict[str, Any]] = None
                  ) -> Optional[SpaceTimelineEvent]:
        """Add a timeline event to a Space."""
        now = datetime.now(timezone.utc).isoformat()
        event = SpaceTimelineEvent(
            event_id=f"tev_{__import__('uuid').uuid4().hex[:16]}",
            event_type=event_type,
            timestamp=now,
            title=title,
            description=description,
            actor=actor,
            importance=importance,
            category=category or self._infer_category(event_type),
            payload=payload or {},
        )
        success = self._store.add_timeline_event(space_id, event)
        return event if success else None

    def get_timeline(self, space_id: str,
                     limit: int = 50,
                     category: str = "",
                     event_type: str = "") -> List[SpaceTimelineEvent]:
        """Get timeline events for a Space."""
        space = self._store.get(space_id)
        if not space:
            return []
        events = space.timeline
        if category:
            events = [e for e in events if e.category == category]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_timeline_by_category(self, space_id: str
                                 ) -> Dict[str, List[SpaceTimelineEvent]]:
        """Get timeline events grouped by category."""
        space = self._store.get(space_id)
        if not space:
            return {}
        grouped = {}
        for event in space.timeline:
            cat = event.category or "other"
            grouped.setdefault(cat, []).append(event)
        # Sort each group by timestamp descending
        for cat in grouped:
            grouped[cat].sort(key=lambda e: e.timestamp, reverse=True)
        return grouped

    # ------------------------------------------------------------------
    # Integration helpers
    # ------------------------------------------------------------------

    def record_communication(self, space_id: str, title: str,
                             actor: str = "",
                             payload: Optional[Dict[str, Any]] = None
                             ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "communication", title=title, actor=actor,
            category="communication", importance=0.6, payload=payload,
        )

    def record_decision(self, space_id: str, title: str,
                        actor: str = "",
                        payload: Optional[Dict[str, Any]] = None
                        ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "decision", title=title, actor=actor,
            category="decision", importance=0.8, payload=payload,
        )

    def record_execution(self, space_id: str, title: str,
                         actor: str = "",
                         payload: Optional[Dict[str, Any]] = None
                         ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "execution", title=title, actor=actor,
            category="execution", importance=0.7, payload=payload,
        )

    def record_document(self, space_id: str, title: str,
                        actor: str = "",
                        payload: Optional[Dict[str, Any]] = None
                        ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "document", title=title, actor=actor,
            category="document", importance=0.5, payload=payload,
        )

    def record_evidence(self, space_id: str, title: str,
                        actor: str = "",
                        payload: Optional[Dict[str, Any]] = None
                        ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "evidence", title=title, actor=actor,
            category="evidence", importance=0.7, payload=payload,
        )

    def record_approval(self, space_id: str, title: str,
                        actor: str = "",
                        payload: Optional[Dict[str, Any]] = None
                        ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "approval", title=title, actor=actor,
            category="approval", importance=0.9, payload=payload,
        )

    def record_ai_insight(self, space_id: str, title: str,
                          actor: str = "SHUNYA",
                          payload: Optional[Dict[str, Any]] = None
                          ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "ai_insight", title=title, actor=actor,
            category="ai_insight", importance=0.6, payload=payload,
        )

    def record_observation(self, space_id: str, title: str,
                           actor: str = "",
                           payload: Optional[Dict[str, Any]] = None
                           ) -> Optional[SpaceTimelineEvent]:
        return self.add_event(
            space_id, "observation", title=title, actor=actor,
            category="observation", importance=0.5, payload=payload,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_category(event_type: str) -> str:
        """Infer a timeline category from an event type."""
        event_type_lower = event_type.lower()
        for cat_key, cat_label in TIMELINE_CATEGORIES.items():
            if cat_key in event_type_lower:
                return cat_key
        # Default mapping
        if event_type_lower in ("created", "updated", "deleted", "archived"):
            return "observation"
        return "observation"


# =========================================================================
# Singleton
# =========================================================================

_timeline: Optional[SpaceTimelineManager] = None


def get_timeline_manager() -> SpaceTimelineManager:
    global _timeline
    if _timeline is None:
        _timeline = SpaceTimelineManager()
    return _timeline


def reset_timeline_manager() -> None:
    global _timeline
    _timeline = None