"""FOR-2C.1: Cross-domain integration — wire events from Proposal, Task, Document into Relationship timeline.

This module provides integration hooks that other domains call to emit timeline events
and update AI memory when business events occur.
"""

from datetime import datetime, timezone
from app import db
from app.relationship.models import (
    TimelineEntry, RelationshipMemory,
)


def record_event(relationship_id: int, organization_id: int,
                  event_type: str, title: str = "", description: str = "",
                  reference_type: str = "", reference_id: int = None,
                  metadata: dict = None, created_by: str = "") -> TimelineEntry:
    """Record a business event on a Relationship timeline.

    Call this from Proposal, Task, Document, Communication, and Finance flows.
    """
    entry = TimelineEntry(
        organization_id=organization_id,
        relationship_id=relationship_id,
        event_type=event_type,
        title=title or event_type,
        description=(description or "")[:1000],
        reference_type=reference_type,
        reference_id=reference_id,
        metadata_json=__import__("json").dumps(metadata or {}),
        created_by=created_by,
    )
    db.session.add(entry)
    return entry


def update_ai_memory_from_event(relationship_id: int, organization_id: int,
                                  event_type: str, summary_fragment: str = "") -> None:
    """Update AI memory with a summary fragment from a business event.

    The AI memory accumulates context over time.
    """
    memory = RelationshipMemory.query.filter_by(
        relationship_id=relationship_id,
        organization_id=organization_id,
    ).first()
    if not memory:
        return

    import json
    data = json.loads(memory.memory_json or "{}")

    # Add event to memory context
    if "recent_events" not in data:
        data["recent_events"] = []
    data["recent_events"].append({
        "type": event_type,
        "summary": summary_fragment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    # Keep last 20 events
    data["recent_events"] = data["recent_events"][-20:]

    memory.memory_json = json.dumps(data)
    memory.last_ai_update = datetime.now(timezone.utc)
    db.session.add(memory)