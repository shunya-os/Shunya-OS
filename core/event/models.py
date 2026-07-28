"""
SHUNYA — Event Engine Models

Canonical event envelope, event type enumeration, and priority levels
for the SHUNYA event bus. Every event in the system follows this schema,
regardless of source component.

Implements the Event contracts defined in:
    - docs/canon/00_universal_ontology.md §8 (Event)
    - docs/canon/05_runtime_canon.md §4 (Event System)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.kernel.types import generate_uuid7

# ── Timestamp helper ───────────────────────────────────────────────────────────


def _now_iso() -> str:
    """Return the current UTC timestamp as ISO-8601 with 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── EventPriority ──────────────────────────────────────────────────────────────


class EventPriority(str, Enum):
    """Priority level for system events.

    Priority determines the order of event processing and delivery.
    Higher-priority events are delivered before lower-priority ones
    within the same timestamp.
    """

    CRITICAL = "critical"
    """Events that require immediate attention (e.g., system failures)."""

    HIGH = "high"
    """Important events that should be processed promptly."""

    NORMAL = "normal"
    """Default priority for most events."""

    LOW = "low"
    """Background events with no urgency."""


# ── EventType ──────────────────────────────────────────────────────────────────


class EventType(str, Enum):
    """Canonical system event types.

    Every event in the SHUNYA system has a typed event_type that describes
    what happened. These correspond to the canonical event types defined
    in the Runtime Canon §4.2.

    Reference: docs/canon/05_runtime_canon.md §4.2
    """

    # ── Object Lifecycle ──────────────────────────────────────────────────
    OBJECT_CREATED = "object.created"
    """A new object was created."""

    OBJECT_MODIFIED = "object.modified"
    """An object's fields were modified."""

    OBJECT_DELETED = "object.deleted"
    """An object was deleted or retired."""

    OBJECT_STATUS_CHANGED = "object.status_changed"
    """An object's lifecycle status changed."""

    # ── Relationships ─────────────────────────────────────────────────────
    RELATIONSHIP_ADDED = "relationship.added"
    """A relationship was created between two objects."""

    RELATIONSHIP_REMOVED = "relationship.removed"
    """A relationship was removed."""

    # ── Evidence ───────────────────────────────────────────────────────────
    EVIDENCE_ATTACHED = "evidence.attached"
    """Evidence was attached to an object."""

    EVIDENCE_SUPERSEDED = "evidence.superseded"
    """Evidence was superseded by newer evidence."""

    # ── Observations ───────────────────────────────────────────────────────
    OBSERVATION_CREATED = "observation.created"
    """A new observation was recorded."""

    OBSERVATION_STATUS_CHANGED = "observation.status_changed"
    """An observation's lifecycle status changed."""

    # ── Decisions ──────────────────────────────────────────────────────────
    DECISION_CREATED = "decision.created"
    """A decision was initiated."""

    DECISION_STATUS_CHANGED = "decision.status_changed"
    """A decision's status changed."""

    # ── Commitments ────────────────────────────────────────────────────────
    COMMITMENT_CREATED = "commitment.created"
    """A commitment was made."""

    COMMITMENT_STATUS_CHANGED = "commitment.status_changed"
    """A commitment's status changed."""

    # ── Execution ──────────────────────────────────────────────────────────
    TASK_COMPLETED = "task.completed"
    """A task was completed."""

    WORKFLOW_COMPLETED = "workflow.completed"
    """A workflow completed."""

    OUTCOME_RECORDED = "outcome.recorded"
    """An outcome was measured and recorded."""

    # ── Knowledge & Memory ─────────────────────────────────────────────────
    KNOWLEDGE_UPDATED = "knowledge.updated"
    """Knowledge was added or modified."""

    MEMORY_FORMED = "memory.formed"
    """A new memory was created."""

    # ── Human ───────────────────────────────────────────────────────────────
    HUMAN_ACTION = "human.action"
    """A human performed an action in the system."""

    # ── System ─────────────────────────────────────────────────────────────
    SYSTEM_EVENT = "system.event"
    """A generic system-level event."""

    ERROR = "error"
    """An error occurred in the system."""

    WARNING = "warning"
    """A warning condition was detected."""

    @classmethod
    def from_string(cls, value: str) -> EventType:
        """Convert a string to an EventType.

        Args:
            value: The string representation of the event type.

        Returns:
            The matching EventType.

        Raises:
            ValueError: If the string does not match any known EventType.
        """
        return cls(value)


# ── SystemEvent ────────────────────────────────────────────────────────────────


@dataclass
class SystemEvent:
    """A canonical event in the SHUNYA event bus.

    Every event in the system — whether generated by an engine, a human,
    an external system, or the runtime itself — follows this envelope.
    Events are immutable after emission and are delivered to subscribers
    via the EventEngine.

    The event envelope carries:
        - **Identity**: event_id (UUID v7), event_type, event_version
        - **Temporal**: timestamp (ISO-8601, set on creation)
        - **Source**: source component, actor_id, object_id, related objects
        - **Payload**: type-specific data
        - **Evidence**: supporting evidence references
        - **Quality of Service**: priority, ttl_seconds
        - **Extensibility**: metadata dict

    References:
        - docs/canon/00_universal_ontology.md §8 (Event)
        - docs/canon/05_runtime_canon.md §4 (Event System)
    """

    event_id: str = field(default_factory=generate_uuid7)
    """Globally unique identifier for this event (UUID v7)."""

    event_type: EventType = EventType.SYSTEM_EVENT
    """Canonical event type (see EventType enum)."""

    event_version: int = 1
    """Schema version of the event payload."""

    timestamp: str = field(default_factory=_now_iso)
    """When the event occurred (ISO-8601 with 'Z' suffix)."""

    source: str = ""
    """Which engine or component generated this event (e.g., 'object_factory')."""

    actor_id: str = ""
    """ObjectID of the actor that caused this event."""

    object_id: str = ""
    """ObjectID of the primary object this event is about."""

    related_object_ids: list[str] = field(default_factory=list)
    """ObjectIDs of other objects involved in this event."""

    payload: dict[str, Any] = field(default_factory=dict)
    """Event-specific data payload."""

    evidence_ids: list[str] = field(default_factory=list)
    """Evidence references supporting this event."""

    priority: EventPriority = EventPriority.NORMAL
    """Delivery priority for this event."""

    ttl_seconds: int | None = None
    """Time-to-live in seconds. None means no expiry."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible metadata container for domain-specific data."""