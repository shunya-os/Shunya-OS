"""
SHUNYA — Kernel Type Definitions

Foundational enums, dataclasses, and type aliases used by the
UniversalObject protocol implementation. Every object in the system
derives from or references these types.

Implements the type contracts defined in
docs/canon/04_universal_object_protocol.md.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ── UUID v7 generation ────────────────────────────────────────────────────────


def generate_uuid7() -> str:
    """Generate a UUID v7 string.

    UUID v7 is time-ordered (ms-precision timestamp prefix) which enables
    chronological sorting without a separate timestamp column.

    Returns:
        A 36-character UUID v7 string (hexadecimal with dashes).
    """
    # UUID v7 layout (RFC 9562):
    #   bits  0-47: Unix ms timestamp
    #   bits 48-51: version (0111 = 7)
    #   bits 52-59: rand_a (high 8 bits of random)
    #   bits 60-63: variant (10xx)
    #   bits 64-127: rand_b (64 bits of random)
    timestamp_ms = int(time.time() * 1000)

    # 48-bit timestamp
    time_bytes = timestamp_ms.to_bytes(6, byteorder="big")

    # Random bytes for the remaining 10 bytes
    rand_bytes = uuid.uuid4().bytes[0:10]

    # Assemble: 6 bytes timestamp + 10 bytes random
    raw_bytes = time_bytes + rand_bytes

    # Set version (7) in the 7th byte (bits 48-51)
    raw_arr = bytearray(raw_bytes)
    raw_arr[6] = (raw_arr[6] & 0x0F) | 0x70  # version 7

    # Set variant (10xx) in byte 8 (bits 62-63)
    raw_arr[8] = (raw_arr[8] & 0x3F) | 0x80

    # Convert to standard UUID hex string
    hex_str = raw_arr.hex()
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


def _now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Root enums ────────────────────────────────────────────────────────────────


class ObjectStatus(str, Enum):
    """Lifecycle status values for any UniversalObject.

    These represent the canonical operational state of an object.
    Every object must have exactly one status at all times.
    """

    ACTIVE = "active"
    """Object is fully operational and visible."""

    SUPERSEDED = "superseded"
    """Object has been replaced by a newer version but remains for audit."""

    ARCHIVED = "archived"
    """Object is retained for historical reference but not actively used."""

    PENDING = "pending"
    """Object is awaiting approval, verification, or activation."""

    DELETED = "deleted"
    """Object has been soft-deleted and is no longer accessible via normal queries."""


class IdentityType(str, Enum):
    """Classification of how an object's identity was established."""

    PERMANENT = "permanent"
    """Permanent identity assigned at creation — never changes."""
    EXTERNAL = "external"
    """Identity derived from an external system (e.g., CRM, email)."""
    DERIVED = "derived"
    """Identity inferred or computed from other objects/evidence."""
    TEMPORARY = "temporary"
    """Identity is transient — will be resolved or merged later."""
    MERGED = "merged"
    """Identity was merged from two or more previous identities."""
    SPLIT = "split"
    """Identity resulted from splitting a previous identity."""
    DELETED = "deleted"
    """Identity has been retired/deleted."""


class IdentityAuthority(str, Enum):
    """System or entity that asserted the object's identity."""

    IDENTITY_ENGINE = "identity_engine"
    """Automated identity resolution engine."""
    OBJECT_FACTORY = "object_factory"
    """Object creation pipeline."""
    FOUNDER = "founder"
    """Human founder or bootstrapping process."""
    GOVERNANCE = "governance"
    """Governance/administrative action."""
    EXTERNAL = "external"
    """Trusted external authority."""


class SourceType(str, Enum):
    """How an object entered the SHUNYA system."""

    API = "api"
    """Created or imported via an API call."""
    HUMAN = "human"
    """Created manually by a human user."""
    IMPORT = "import"
    """Bulk-imported from an external system."""
    SYSTEM = "system"
    """Created internally by the SHUNYA system."""
    EXTERNAL = "external"
    """Sourced from an external system via integration."""
    DERIVED = "derived"
    """Computed or inferred from other objects."""


class RelationshipDirection(str, Enum):
    """Directionality of a relationship between two objects."""

    DIRECTIONAL = "directional"
    """Source → Target (one-way)."""
    BIDIRECTIONAL = "bidirectional"
    """Mutual relationship (two-way)."""
    HIERARCHICAL = "hierarchical"
    """Parent/child or containment relationship."""
    TEMPORAL = "temporal"
    """Time-bound relationship with validity window."""
    CONTEXTUAL = "contextual"
    """Meaningful only in a specific context."""
    INHERITED = "inherited"
    """Acquired from a parent or container object."""


class OwnerType(str, Enum):
    """Classification of an object's owner."""

    HUMAN = "human"
    """A human user owns the object."""
    ORGANIZATION = "organization"
    """An organization/team owns the object."""
    SYSTEM = "system"
    """The SHUNYA system owns the object."""
    SHARED = "shared"
    """Ownership is shared among multiple actors."""


class ActionEffect(str, Enum):
    """Describes what effect an action has on the object."""

    READ = "read"
    """Read-only — no state change."""
    WRITE = "write"
    """Modifies object state."""
    DELETE = "delete"
    """Retires or deletes the object."""
    ADMIN = "admin"
    """Administrative operation."""
    RELATIONSHIP = "relationship"
    """Creates or modifies relationships."""
    EVIDENCE = "evidence"
    """Attaches evidence."""
    SYSTEM = "system"
    """System-level operation."""


# ── Support dataclasses ────────────────────────────────────────────────────────


@dataclass
class EvidenceRef:
    """Reference to an evidence record attached to an object.

    Evidence provides the factual basis for assertions about an object's
    state, relationships, and lifecycle transitions.
    """

    evidence_id: str
    """Unique identifier for the evidence record (UUID)."""

    timestamp: str = field(default_factory=_now_iso)
    """When the evidence was attached (ISO-8601)."""

    attached_by: str = ""
    """ObjectID of the actor that attached this evidence."""

    description: str = ""
    """Human-readable description of what this evidence supports."""

    superseded_by: str | None = None
    """If superseded, the evidence_id that replaces this one."""


@dataclass
class RelationshipRef:
    """A typed connection from this object to another UniversalObject.

    Relationships are the core of the SHUNYA ontology — they define how
    objects relate to each other within the knowledge graph.
    """

    relationship_id: str = field(default_factory=generate_uuid7)
    """Unique identifier for this relationship instance."""

    source_id: str = ""
    """ObjectID of the source (origin) of the relationship."""

    target_id: str = ""
    """ObjectID of the target of the relationship."""

    relationship_type: str = ""
    """Canonical type from the Relationship Canon (e.g., 'member_of', 'owns')."""

    direction: RelationshipDirection = RelationshipDirection.DIRECTIONAL
    """Directionality of the relationship."""

    strength: float = 1.0
    """Confidence/relevance strength of the relationship [0.0, 1.0]."""

    label: str = ""
    """Human-readable label for the relationship."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible metadata contextual to this relationship."""

    created_at: str = field(default_factory=_now_iso)
    """When the relationship was created (ISO-8601)."""

    evidence_ids: list[str] = field(default_factory=list)
    """Evidence references supporting this relationship."""


@dataclass
class TimelineEvent:
    """An immutable, chronologically-ordered event on an object's timeline.

    Every state change, status transition, evidence attachment, or
    relationship modification produces a timeline event. The timeline
    is append-only and events can never be deleted or modified.
    """

    event_id: str = field(default_factory=generate_uuid7)
    """Unique identifier for this event (UUID)."""

    object_id: str = ""
    """ObjectID of the object this event belongs to."""

    event_type: str = ""
    """Canonical event type (e.g., 'object_created', 'status_changed')."""

    timestamp: str = field(default_factory=_now_iso)
    """When the event occurred (ISO-8601)."""

    actor_id: str = ""
    """ObjectID of the actor that triggered the event."""

    data: dict[str, Any] = field(default_factory=dict)
    """Event-specific payload with details about what changed."""

    evidence_ids: list[str] = field(default_factory=list)
    """Evidence references supporting this event."""

    previous_state: dict[str, Any] | None = None
    """Snapshot of the object state before the event."""

    new_state: dict[str, Any] | None = None
    """Snapshot of the object state after the event."""


@dataclass
class AuditEntry:
    """An immutable entry in the object's audit log.

    Unlike timeline events which track the object's story, audit entries
    track every action taken *on* the object for compliance and
    accountability purposes. The audit log is hash-chained for integrity
    verification.
    """

    entry_id: str = field(default_factory=generate_uuid7)
    """Unique identifier for this audit entry (UUID)."""

    action: str = ""
    """Canonical action name (e.g., 'view', 'update', 'delete')."""

    actor_id: str = ""
    """ObjectID of the actor that performed the action."""

    timestamp: str = field(default_factory=_now_iso)
    """When the action occurred (ISO-8601)."""

    detail: str = ""
    """Human-readable description of what was done."""

    evidence_ids: list[str] = field(default_factory=list)
    """Optional evidence references supporting this audit entry."""

    previous_hash: str = ""
    """Hash of the previous audit entry (chain integrity)."""

    hash: str = ""
    """SHA-256 hash of this entry (self-hash for chain integrity)."""

    def compute_hash(self) -> str:
        """Compute the SHA-256 hash of this entry's content.

        The hash covers all fields except the `hash` field itself,
        enabling chain-of-custody verification.

        Returns:
            Hex digest of the entry's content hash.
        """
        hasher = hashlib.sha256()
        hasher.update(self.entry_id.encode("utf-8"))
        hasher.update(self.action.encode("utf-8"))
        hasher.update(self.actor_id.encode("utf-8"))
        hasher.update(self.timestamp.encode("utf-8"))
        hasher.update(self.detail.encode("utf-8"))
        hasher.update(str(self.evidence_ids).encode("utf-8"))
        hasher.update(self.previous_hash.encode("utf-8"))
        return hasher.hexdigest()


@dataclass
class VersionRecord:
    """A record of a specific version in the object's version history.

    Version numbers are monotonically increasing integers. Every
    modification to an object creates a new version record. Previous
    versions are immutable snapshots retained for audit and rollback.
    """

    version: int = 1
    """Monotonically increasing version number."""

    timestamp: str = field(default_factory=_now_iso)
    """When this version was created (ISO-8601)."""

    modified_by: str = ""
    """ObjectID of the actor that created this version."""

    snapshot: dict[str, Any] = field(default_factory=dict)
    """Serialized snapshot of the object's full state at this version."""

    change_summary: str = ""
    """Human-readable summary of what changed in this version."""


@dataclass
class OwnershipRecord:
    """A record of an ownership period in the object's ownership history.

    Ownership history is immutable — past records are never modified.
    """

    owner_id: str = ""
    """ObjectID of the owner during this period."""

    owner_type: OwnerType = OwnerType.HUMAN
    """Type of the owner during this period."""

    from_timestamp: str = field(default_factory=_now_iso)
    """When this ownership period began (ISO-8601)."""

    to_timestamp: str | None = None
    """When this ownership period ended, or None if current (ISO-8601)."""

    reason: str = ""
    """Reason for the ownership change (e.g., 'initial_creation', 'org_transfer')."""

    evidence_ids: list[str] = field(default_factory=list)
    """Evidence supporting this ownership transfer."""


@dataclass
class AccessControlEntry:
    """A single entry in the access control list.

    Each entry grants or denies a role to an actor within a specific scope.
    Deny always overrides allow.
    """

    actor_id: str = ""
    """ObjectID of the actor this entry applies to."""

    role: str = ""
    """Role identifier (e.g., 'owner', 'editor', 'viewer')."""

    scope: str = "*"
    """Scope within which the role applies ('*' = all scopes)."""

    granted_at: str = field(default_factory=_now_iso)
    """When this entry was created (ISO-8601)."""

    granted_by: str = ""
    """ObjectID of the actor that granted this permission."""

    is_deny: bool = False
    """If True, this is a deny rule (overrides all allow rules)."""


@dataclass
class AccessControlList:
    """Access control list for a UniversalObject.

    Supports role-based access control with optional fine-grained
    scope limitations. Deny rules always override allow rules.
    """

    owner: AccessControlEntry | None = None
    """The owner entry — has implicit full access."""

    entries: list[AccessControlEntry] = field(default_factory=list)
    """List of access control entries."""


@dataclass
class InteractionRecord:
    """A record of a past AI interaction with this object.

    Interaction history helps the AI understand how it has previously
    engaged with the object, enabling contextual continuity.
    """

    interaction_id: str = field(default_factory=generate_uuid7)
    """Unique identifier for this interaction (UUID)."""

    timestamp: str = field(default_factory=_now_iso)
    """When the interaction occurred (ISO-8601)."""

    interaction_type: str = ""
    """Type of interaction (e.g., 'query', 'update', 'analysis')."""

    summary: str = ""
    """Brief summary of the interaction."""

    actor_id: str = ""
    """ObjectID of the actor that initiated the interaction."""


@dataclass
class StageTransition:
    """A record of a lifecycle stage transition.

    Stage transitions are immutable — they are recorded chronologically
    and can be replayed to reconstruct the object's full lifecycle path.
    """

    from_stage: str = ""
    """Previous lifecycle stage."""

    to_stage: str = ""
    """New lifecycle stage."""

    timestamp: str = field(default_factory=_now_iso)
    """When the transition occurred (ISO-8601)."""

    actor_id: str = ""
    """ObjectID of the actor that triggered the transition."""

    reason: str = ""
    """Reason for the transition."""

    evidence_ids: list[str] = field(default_factory=list)
    """Evidence supporting this transition."""


@dataclass
class DiffResult:
    """Represents the difference between two object versions.

    Returned by compare_versions() to show what changed between
    two snapshots of the same object at different version numbers.
    """

    version_from: int = 0
    """Source version number."""

    version_to: int = 0
    """Target version number."""

    added_fields: dict[str, Any] = field(default_factory=dict)
    """Fields present in the target but not in the source."""

    removed_fields: dict[str, Any] = field(default_factory=dict)
    """Fields present in the source but not in the target."""

    changed_fields: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    """Fields with different values (old_value, new_value)."""

    unchanged_count: int = 0
    """Number of fields that remained the same."""