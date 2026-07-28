"""
SHUNYA — Timeline Engine Models

Immutable timeline event model with integrity hash chain support and
canonical event type enumeration.

Implements the Timeline contracts defined in:
    - docs/canon/04_universal_object_protocol.md §7 (Timeline)
    - docs/canon/05_runtime_canon.md §6 (Timeline Engine)
    - docs/canon/00_universal_ontology.md §8 (Event)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.kernel.types import generate_uuid7

# ── Timestamp helper ───────────────────────────────────────────────────────────


def _now_iso() -> str:
    """Return the current UTC timestamp as ISO-8601 with 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── TimelineEventType ──────────────────────────────────────────────────────────


class TimelineEventType(str, Enum):
    """Canonical types for timeline events.

    Every state change, lifecycle transition, relationship modification,
    or evidence change on an object is recorded as a typed timeline event.
    """

    OBJECT_CREATED = "object_created"
    """A new object was created."""

    OBJECT_MODIFIED = "object_modified"
    """An object's fields were modified."""

    STATUS_CHANGED = "status_changed"
    """An object's lifecycle status changed."""

    RELATIONSHIP_ADDED = "relationship_added"
    """A relationship was added to an object."""

    RELATIONSHIP_REMOVED = "relationship_removed"
    """A relationship was removed from an object."""

    EVIDENCE_ATTACHED = "evidence_attached"
    """Evidence was attached to an object."""

    EVIDENCE_SUPERSEDED = "evidence_superseded"
    """Evidence was superseded by newer evidence."""

    OWNERSHIP_CHANGED = "ownership_changed"
    """Ownership of the object was transferred."""

    OBJECT_DELETED = "object_deleted"
    """An object was deleted or retired."""

    OBJECT_RETIRED = "object_retired"
    """An object was retired (soft-delete with retention)."""

    VERSION_CREATED = "version_created"
    """A new version of the object was created."""

    CUSTOM = "custom"
    """A custom event type defined by the domain adapter."""

    @classmethod
    def from_string(cls, value: str) -> TimelineEventType:
        """Convert a string to a TimelineEventType, falling back to CUSTOM.

        Args:
            value: The string representation of the event type.

        Returns:
            The matching TimelineEventType, or CUSTOM if no match.
        """
        try:
            return cls(value)
        except ValueError:
            return cls.CUSTOM


# ── Integrity Chain Helpers ────────────────────────────────────────────────────


GENESIS_HASH = "0" * 64
"""The hash of the first event in an integrity chain (64 zeros)."""


def compute_event_hash(
    data: dict[str, Any],
    previous_hash: str,
) -> str:
    """Compute the SHA-256 integrity hash for a timeline event.

    The hash is computed over the event's data dict (serialized as a
    stable string) concatenated with the previous event's hash. This
    creates an immutable chain where any modification to any event in
    the chain will invalidate all subsequent hashes.

    Args:
        data: The event-specific payload dict.
        previous_hash: The hash of the previous event in the chain.

    Returns:
        A 64-character hex SHA-256 digest.
    """
    hasher = hashlib.sha256()
    # Stable serialization: sort the JSON-serialised representation
    serialized = str(sorted(data.items()))
    hasher.update(serialized.encode("utf-8"))
    hasher.update(previous_hash.encode("utf-8"))
    return hasher.hexdigest()


# ── TimelineEvent ──────────────────────────────────────────────────────────────


@dataclass
class TimelineEvent:
    """An immutable, chronologically-ordered event on an object's timeline.

    Every state change, status transition, evidence attachment, or
    relationship modification produces a timeline event. The timeline
    is append-only — events can never be deleted or modified after
    creation.

    Integrity is guaranteed by a SHA-256 hash chain: each event stores
    the hash of the previous event, forming an immutable chain that
    can be verified at any time.

    References:
        - 04_universal_object_protocol.md §7.2 (TimelineEvent structure)
        - 05_runtime_canon.md §6 (Timeline Engine rules)
    """

    event_id: str = field(default_factory=generate_uuid7)
    """Globally unique identifier for this event (UUID v7)."""

    object_id: str = ""
    """ObjectID of the object this event belongs to."""

    event_type: TimelineEventType = TimelineEventType.CUSTOM
    """Canonical type of this timeline event."""

    timestamp: str = field(default_factory=_now_iso)
    """When the event occurred (ISO-8601 with 'Z' suffix)."""

    actor_id: str = ""
    """ObjectID of the actor that triggered this event."""

    data: dict[str, Any] = field(default_factory=dict)
    """Event-specific payload describing what changed."""

    evidence_ids: list[str] = field(default_factory=list)
    """Evidence references supporting this event."""

    previous_state: dict[str, Any] | None = None
    """Snapshot of the object state *before* this event (if captured)."""

    new_state: dict[str, Any] | None = None
    """Snapshot of the object state *after* this event (if captured)."""

    previous_hash: str = GENESIS_HASH
    """SHA-256 hash of the previous event in the integrity chain.

    The first event for an object has previous_hash = '0' * 64.
    Every subsequent event chains to its predecessor, forming a
    linked integrity chain.
    """

    integrity_hash: str = ""
    """SHA-256 hash of *this* event's content (data + previous_hash).

    This is the hash that the next event stores as its ``previous_hash``.
    When non-empty, ``verify_integrity()`` can check that this event's
    content has not been tampered with by recomputing the hash and
    comparing against this stored value.
    """

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible metadata container for domain-specific data."""

    def verify_hash(self) -> bool:
        """Verify this event's own integrity hash.

        Recomputes the SHA-256 hash from this event's ``data`` and
        ``previous_hash``, and compares it against the stored
        ``integrity_hash``. If ``integrity_hash`` is empty (not yet
        computed), the method returns False.

        This only validates a single event. For full chain verification,
        use ``TimelineEngine.verify_integrity()``.

        Returns:
            True if ``integrity_hash`` is non-empty and matches the
            recomputed hash of this event's data.
        """
        if not self.integrity_hash:
            return False
        expected = compute_event_hash(self.data, self.previous_hash)
        return self.integrity_hash == expected
