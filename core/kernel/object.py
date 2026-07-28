"""
SHUNYA — UniversalObject Protocol Implementation

The foundational base class for every object in the SHUNYA system.
Implements all 15 mandatory sections of the Universal Object Protocol
as defined in docs/canon/04_universal_object_protocol.md.

Usage:
    >>> from core.kernel import UniversalObject, ObjectStatus
    >>> obj = UniversalObject(
    ...     object_type="human",
    ...     name="John Doe",
    ...     created_by="system",
    ...     updated_by="system",
    ...     owner_id="org_acme",
    ... )
    >>> obj.object_id  # UUID v7
    '01J8X2R4K5M7N9Q0T2V4W6Y8Z'
    >>> obj.status
    'pending'
    >>> obj.is_active
    False
    >>> obj.transition("active", reason="verified")
    >>> obj.verify_integrity()
    True
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from core.kernel.types import (
    AccessControlEntry,
    AccessControlList,
    AuditEntry,
    DiffResult,
    EvidenceRef,
    IdentityAuthority,
    IdentityType,
    InteractionRecord,
    ObjectStatus,
    OwnershipRecord,
    OwnerType,
    RelationshipDirection,
    RelationshipRef,
    SourceType,
    StageTransition,
    TimelineEvent,
    VersionRecord,
    _now_iso,
    generate_uuid7,
)

# ── Public re-exports ─────────────────────────────────────────────────────────

__all__ = [
    "ActionDefinition",
    "UniversalObject",
]


@dataclass
class ActionDefinition:
    """Definition of an action available on a UniversalObject.

    Every object exposes a set of actions that define what can be done
    to it. Actions are filtered by the actor's permissions at runtime.
    """

    name: str = ""
    """Canonical action name (e.g., 'view', 'update', 'delete')."""

    display_name: str = ""
    """Human-readable action name for UI presentation."""

    description: str = ""
    """Description of what the action does."""

    required_permission: str = ""
    """Permission role required to execute this action (e.g., 'viewer', 'editor')."""

    parameters: list[dict[str, Any]] = field(default_factory=list)
    """List of parameter definitions accepted by this action."""

    effect: str = ""
    """Description of the effect executing this action has on the object."""


@dataclass
class ActionResult:
    """Result of executing an action on a UniversalObject."""

    success: bool = True
    """Whether the action was executed successfully."""

    result: Any = None
    """The result payload of the action."""

    error: str = ""
    """Error message if the action failed."""

    action: str = ""
    """Name of the action that was executed."""


# ── Search result type ────────────────────────────────────────────────────────


@dataclass
class SearchResult:
    """A single search result for an object matched by a query."""

    field: str = ""
    """The field that matched the query."""

    value: str = ""
    """The value that matched."""

    score: float = 0.0
    """Relevance score [0.0, 1.0]."""

    context: str = ""
    """Surrounding context snippet."""


# ── UniversalObject ────────────────────────────────────────────────────────────


class UniversalObject:
    """The foundational base class for every object in the SHUNYA system.

    Implements all 15 mandatory sections of the Universal Object Protocol.
    Every object in the system — whether a human, organization, workspace,
    document, or AI agent — derives from this class.

    Protocol sections implemented:
        §4  Identity         — Unique identification and aliasing
        §5  Metadata          — Provenance and descriptive metadata
        §6  Relationships    — Typed connections to other objects
        §7  Timeline         — Immutable chronological event history
        §8  Lifecycle        — Stage-based lifecycle management
        §9  Status           — Current operational status
        §10 Ownership        — Ownership and transfer tracking
        §11 Permissions      — Role-based access control
        §12 Evidence         — Supporting evidence and confidence
        §13 Memory (OPT)     — Experiential memory association
        §14 AI Context       — Machine-readable AI context generation
        §15 Search           — Full-text search and field-level query
        §16 Audit            — Immutable hash-chained audit log
        §17 Actions          — Action definitions and dispatch
        §18 Versioning       — Monotonic version history
    """

    # ── Constants ──────────────────────────────────────────────────────────
    _DEFAULT_VALID_TRANSITIONS: dict[str, list[str]] = {
        "pending": ["active", "deleted"],
        "active": ["superseded", "archived", "deleted", "pending"],
        "superseded": ["archived", "deleted"],
        "archived": ["active", "deleted"],
        "deleted": [],
    }
    """Default valid lifecycle transitions for all objects."""

    _INACTIVE_STATUSES: frozenset[str] = frozenset(
        {"archived", "deleted", "superseded"}
    )
    """Status values considered 'inactive'."""

    # ── Constructor ────────────────────────────────────────────────────────

    def __init__(
        self,
        *,
        object_type: str,
        name: str,
        created_by: str,
        updated_by: str,
        owner_id: str,
        object_id: str | None = None,
        description: str = "",
        tenant_id: str | None = None,
        space_id: str | None = None,
        tags: list[str] | None = None,
        status: str | ObjectStatus = ObjectStatus.PENDING,
        identity_type: str | IdentityType = IdentityType.PERMANENT,
        identity_authority: str | IdentityAuthority = IdentityAuthority.OBJECT_FACTORY,
        external_ids: dict[str, str] | None = None,
        aliases: list[str] | None = None,
        source: str | SourceType = SourceType.SYSTEM,
        source_detail: str = "",
        custom_metadata: dict[str, Any] | None = None,
        owner_type: str | OwnerType = OwnerType.HUMAN,
        valid_transitions: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize a new UniversalObject.

        Args:
            object_type: Canonical type from the Business Canon
                (e.g., 'human', 'organization', 'workspace', 'document').
            name: Human-readable name for the object.
            created_by: ObjectID of the creator.
            updated_by: ObjectID of the last modifier (same as created_by
                upon creation).
            owner_id: ObjectID of the current owner.
            object_id: Optional explicit UUID v7. Auto-generated if omitted.
            description: Optional human-readable description.
            tenant_id: Optional tenant ID for multi-tenant isolation.
            space_id: Optional workspace/space membership ID.
            tags: Optional free-form categorization tags.
            status: Initial lifecycle status. Defaults to ObjectStatus.PENDING.
            identity_type: How the identity was established.
                Defaults to IdentityType.PERMANENT.
            identity_authority: What system asserted this identity.
                Defaults to IdentityAuthority.OBJECT_FACTORY.
            external_ids: Optional map of external system identities
                (e.g., {'crm': 'CRM-123', 'email': 'user@example.com'}).
            aliases: Optional alternative names/labels.
            source: How the object entered the system.
                Defaults to SourceType.SYSTEM.
            source_detail: Specific context about the source.
            custom_metadata: Optional extensible metadata container.
            owner_type: Classification of the owner.
                Defaults to OwnerType.HUMAN.
            valid_transitions: Optional custom lifecycle transition map.
                Uses the system default if omitted.
        """
        now = _now_iso()

        # ── §4 Identity ────────────────────────────────────────────────
        self._object_id: str = object_id or generate_uuid7()
        self._external_ids: dict[str, str] = dict(external_ids or {})
        self._aliases: list[str] = list(aliases or [])
        self._identity_type: IdentityType = IdentityType(identity_type)
        self._identity_authority: IdentityAuthority = IdentityAuthority(
            identity_authority
        )

        # ── §3 Mandatory fields ─────────────────────────────────────────
        self._object_type: str = object_type
        self._name: str = name
        self._description: str = description
        self._tenant_id: str | None = tenant_id
        self._space_id: str | None = space_id
        self._tags: list[str] = list(tags or [])
        self._confidence: float = 0.0  # Derived from evidence; starts at 0

        # ── §5 Metadata ────────────────────────────────────────────────
        self._created_at: str = now
        self._updated_at: str = now
        self._created_by: str = created_by
        self._updated_by: str = updated_by
        self._source: SourceType = SourceType(source)
        self._source_detail: str = source_detail
        self._custom_metadata: dict[str, Any] = dict(custom_metadata or {})

        # ── §6 Relationships ───────────────────────────────────────────
        self._relationships: list[RelationshipRef] = []

        # ── §7 Timeline ────────────────────────────────────────────────
        self._events: list[TimelineEvent] = []

        # ── §8 Lifecycle ───────────────────────────────────────────────
        initial_status = ObjectStatus(status)
        self._current_stage: str = initial_status.value
        self._valid_transitions: dict[str, list[str]] = (
            dict(valid_transitions) if valid_transitions
            else dict(self._DEFAULT_VALID_TRANSITIONS)
        )
        self._lifecycle_history: list[StageTransition] = []

        # ── §9 Status ──────────────────────────────────────────────────
        self._status: str = initial_status.value
        self._status_detail: str = ""
        self._status_updated_at: str = now
        self._status_updated_by: str = created_by

        # ── §10 Ownership ──────────────────────────────────────────────
        self._owner_id: str = owner_id
        self._owner_type: OwnerType = OwnerType(owner_type)
        self._owner_history: list[OwnershipRecord] = [
            OwnershipRecord(
                owner_id=owner_id,
                owner_type=OwnerType(owner_type),
                from_timestamp=now,
                to_timestamp=None,
                reason="initial_creation",
            )
        ]

        # ── §11 Permissions ────────────────────────────────────────────
        owner_entry = AccessControlEntry(
            actor_id=owner_id,
            role="owner",
            scope="*",
            granted_at=now,
            granted_by=created_by,
        )
        self._acl: AccessControlList = AccessControlList(owner=owner_entry)

        # ── §12 Evidence ───────────────────────────────────────────────
        self._evidence_ids: list[str] = []
        self.__evidence_refs: list[EvidenceRef] = []

        # ── §13 Memory (OPTIONAL) ──────────────────────────────────────
        self._memory_ids: list[str] = []

        # ── §14 AI Context ─────────────────────────────────────────────
        self._ai_summary: str = ""
        self._ai_understanding: str = ""
        self._relevant_objects: list[str] = []
        self._interaction_history: list[InteractionRecord] = []

        # ── §15 Search ─────────────────────────────────────────────────
        self._search_terms: list[str] = []
        self._searchable_fields: list[str] = [
            "object_id",
            "object_type",
            "name",
            "description",
            "status",
            "tags",
            "aliases",
        ]

        # ── §16 Audit ──────────────────────────────────────────────────
        self._audit_log: list[AuditEntry] = []
        self._log_action(
            action="object_created",
            actor_id=created_by,
            detail=f"Object of type '{object_type}' named '{name}' created",
        )

        # ── §17 Actions ────────────────────────────────────────────────
        self._available_actions: list[ActionDefinition] = self._build_default_actions()
        self._custom_action_handlers: dict[str, Callable] = {}

        # ── §18 Versioning ─────────────────────────────────────────────
        self._version: int = 1
        self._version_history: list[VersionRecord] = [
            VersionRecord(
                version=1,
                timestamp=now,
                modified_by=created_by,
                snapshot=self._to_snapshot(),
                change_summary="Initial version",
            )
        ]

        # ── Create initial timeline event ──────────────────────────────
        self._add_event(
            event_type="object_created",
            data={
                "object_type": object_type,
                "name": name,
                "source": self._source.value,
            },
            source=created_by,
            previous_state=None,
            new_state=self._to_snapshot(),
        )

    # ──────────────────────────────────────────────────────────────────────────
    # §3 — Mandatory Fields (Python properties)
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def object_id(self) -> str:
        """Globally unique, immutable identifier (UUID v7)."""
        return self._object_id

    @property
    def object_type(self) -> str:
        """Canonical type from the Business Canon."""
        return self._object_type

    @property
    def name(self) -> str:
        """Human-readable name of this object."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._bump_version(modified_by=self._updated_by)

    @property
    def description(self) -> str:
        """Human-readable description of this object."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value
        self._bump_version(modified_by=self._updated_by)

    @property
    def tenant_id(self) -> str | None:
        """Tenant ID for multi-tenant isolation."""
        return self._tenant_id

    @property
    def space_id(self) -> str | None:
        """Workspace/space membership ID."""
        return self._space_id

    @property
    def tags(self) -> list[str]:
        """Free-form categorization tags."""
        return list(self._tags)

    @tags.setter
    def tags(self, value: list[str]) -> None:
        self._tags = list(value)
        self._bump_version(modified_by=self._updated_by)

    @property
    def confidence(self) -> float:
        """Confidence in the object's current state [0.0, 1.0].

        Derived from the quality and quantity of attached evidence.
        """
        return self.get_confidence()

    # ──────────────────────────────────────────────────────────────────────────
    # §4 — Identity
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def external_ids(self) -> dict[str, str]:
        """Map of external system identities (read-only view)."""
        return dict(self._external_ids)

    @property
    def aliases(self) -> list[str]:
        """Alternative names/labels for this object (read-only view)."""
        return list(self._aliases)

    @property
    def identity_type(self) -> IdentityType:
        """How this object's identity was established."""
        return self._identity_type

    @property
    def identity_authority(self) -> IdentityAuthority:
        """What system asserted this object's identity."""
        return self._identity_authority

    def add_external_id(self, system: str, identifier: str) -> None:
        """Add an external system identity.

        Args:
            system: The external system name (e.g., 'crm', 'email').
            identifier: The identifier within that external system.
        """
        self._external_ids[system] = identifier
        self._bump_version(modified_by=self._updated_by)

    def remove_external_id(self, system: str) -> None:
        """Remove an external system identity.

        Args:
            system: The external system name to remove.
        """
        self._external_ids.pop(system, None)
        self._bump_version(modified_by=self._updated_by)

    def add_alias(self, alias: str) -> None:
        """Add an alternative name/label.

        Args:
            alias: The alias to add.
        """
        if alias not in self._aliases:
            self._aliases.append(alias)
            self._bump_version(modified_by=self._updated_by)

    def remove_alias(self, alias: str) -> None:
        """Remove an alternative name/label.

        Args:
            alias: The alias to remove.
        """
        if alias in self._aliases:
            self._aliases.remove(alias)
            self._bump_version(modified_by=self._updated_by)

    # ──────────────────────────────────────────────────────────────────────────
    # §5 — Metadata
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def created_at(self) -> str:
        """ISO-8601 timestamp of when the object was created (immutable)."""
        return self._created_at

    @property
    def updated_at(self) -> str:
        """ISO-8601 timestamp of when the object was last modified."""
        return self._updated_at

    @property
    def created_by(self) -> str:
        """ObjectID of the creator (immutable)."""
        return self._created_by

    @property
    def updated_by(self) -> str:
        """ObjectID of the last modifier."""
        return self._updated_by

    @property
    def source(self) -> SourceType:
        """How the object entered the system."""
        return self._source

    @property
    def source_detail(self) -> str:
        """Specific context about the object's source."""
        return self._source_detail

    @property
    def custom_metadata(self) -> dict[str, Any]:
        """Extensible metadata container (mutable view)."""
        return self._custom_metadata

    @custom_metadata.setter
    def custom_metadata(self, value: dict[str, Any]) -> None:
        self._custom_metadata = dict(value)
        self._bump_version(modified_by=self._updated_by)

    # ──────────────────────────────────────────────────────────────────────────
    # §6 — Relationships
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def relationships(self) -> list[RelationshipRef]:
        """All relationships for this object (read-only view)."""
        return list(self._relationships)

    def add_relationship(
        self,
        target_id: str,
        relationship_type: str,
        metadata: dict[str, Any] | None = None,
        *,
        direction: str | RelationshipDirection = RelationshipDirection.DIRECTIONAL,
        strength: float = 1.0,
        label: str = "",
        evidence_ids: list[str] | None = None,
    ) -> str:
        """Create a relationship from this object to another.

        Args:
            target_id: ObjectID of the target object.
            relationship_type: Canonical relationship type
                (e.g., 'member_of', 'owns', 'contains').
            metadata: Optional contextual metadata.
            direction: Directionality of the relationship.
            strength: Confidence/relevance strength [0.0, 1.0].
            label: Human-readable label.
            evidence_ids: Optional evidence supporting this relationship.

        Returns:
            The relationship_id of the newly created relationship.
        """
        rel = RelationshipRef(
            source_id=self._object_id,
            target_id=target_id,
            relationship_type=relationship_type,
            direction=RelationshipDirection(direction),
            strength=max(0.0, min(1.0, strength)),
            label=label,
            metadata=dict(metadata or {}),
            evidence_ids=list(evidence_ids or []),
        )
        self._relationships.append(rel)
        self._add_event(
            event_type="relationship_added",
            data={
                "relationship_id": rel.relationship_id,
                "relationship_type": relationship_type,
                "target_id": target_id,
            },
            source=self._updated_by,
        )
        self._log_action(
            action="add_relationship",
            actor_id=self._updated_by,
            detail=f"Relationship '{relationship_type}' added to '{target_id}'",
        )
        self._bump_version(modified_by=self._updated_by)
        return rel.relationship_id

    def remove_relationship(self, relationship_id: str) -> None:
        """Remove a relationship by its ID.

        Args:
            relationship_id: The UUID of the relationship to remove.

        Raises:
            ValueError: If no relationship with the given ID exists.
        """
        for i, rel in enumerate(self._relationships):
            if rel.relationship_id == relationship_id:
                removed = self._relationships.pop(i)
                self._add_event(
                    event_type="relationship_removed",
                    data={
                        "relationship_id": relationship_id,
                        "relationship_type": removed.relationship_type,
                        "target_id": removed.target_id,
                    },
                    source=self._updated_by,
                )
                self._log_action(
                    action="remove_relationship",
                    actor_id=self._updated_by,
                    detail=f"Relationship '{removed.relationship_type}' removed",
                )
                self._bump_version(modified_by=self._updated_by)
                return
        raise ValueError(
            f"Relationship '{relationship_id}' not found on object "
            f"'{self._object_id}'"
        )

    def get_relationships(
        self,
        relationship_type: str | None = None,
        direction: str | RelationshipDirection | None = None,
    ) -> list[RelationshipRef]:
        """Get relationships, optionally filtered by type and/or direction.

        Args:
            relationship_type: Optional filter by relationship type.
            direction: Optional filter by relationship direction.

        Returns:
            Filtered list of RelationshipRef objects.
        """
        results = list(self._relationships)
        if relationship_type is not None:
            results = [r for r in results if r.relationship_type == relationship_type]
        if direction is not None:
            dir_val = RelationshipDirection(direction)
            results = [r for r in results if r.direction == dir_val]
        return results

    def get_related_objects(
        self,
        relationship_type: str | None = None,
        direction: str | RelationshipDirection | None = None,
    ) -> list[str]:
        """Get ObjectIDs of related objects, optionally filtered.

        Args:
            relationship_type: Optional filter by relationship type.
            direction: Optional filter by relationship direction.

        Returns:
            List of target ObjectIDs matching the filters.
        """
        rels = self.get_relationships(
            relationship_type=relationship_type, direction=direction
        )
        return [r.target_id for r in rels]

    # ──────────────────────────────────────────────────────────────────────────
    # §7 — Timeline
    # ──────────────────────────────────────────────────────────────────────────

    def _add_event(
        self,
        event_type: str,
        data: dict[str, Any],
        source: str,
        evidence_ids: list[str] | None = None,
        previous_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
    ) -> str:
        """Internal method to record a timeline event.

        Args:
            event_type: Canonical event type.
            data: Event-specific payload.
            source: Actor ID that triggered the event.
            evidence_ids: Optional evidence references.
            previous_state: Optional snapshot before the event.
            new_state: Optional snapshot after the event.

        Returns:
            The event_id of the newly created event.
        """
        event = TimelineEvent(
            object_id=self._object_id,
            event_type=event_type,
            actor_id=source,
            data=dict(data),
            evidence_ids=list(evidence_ids or []),
            previous_state=previous_state,
            new_state=new_state,
        )
        self._events.append(event)
        return event.event_id

    def add_event(
        self,
        event_type: str,
        data: dict[str, Any],
        source: str,
        evidence_ids: list[str] | None = None,
    ) -> str:
        """Add a timeline event to this object.

        Timeline events are append-only and immutable after creation.

        Args:
            event_type: Canonical event type.
            data: Event-specific payload.
            source: ObjectID of the actor that triggered the event.
            evidence_ids: Optional evidence references.

        Returns:
            The event_id of the newly created event.
        """
        event_id = self._add_event(
            event_type=event_type,
            data=data,
            source=source,
            evidence_ids=evidence_ids,
        )
        self._log_action(
            action="add_event",
            actor_id=source,
            detail=f"Timeline event '{event_type}' added",
        )
        return event_id

    def get_events(
        self,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
        event_type: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[TimelineEvent]:
        """Get timeline events with optional filtering and pagination.

        Events are ordered by timestamp (ascending — oldest first).

        Args:
            from_timestamp: Optional start of time range (ISO-8601).
            to_timestamp: Optional end of time range (ISO-8601).
            event_type: Optional filter by event type.
            limit: Optional max number of events to return.
            offset: Optional number of events to skip (default: 0).

        Returns:
            Filtered and paginated list of TimelineEvent objects.
        """
        results = list(self._events)

        if from_timestamp is not None:
            results = [e for e in results if e.timestamp >= from_timestamp]
        if to_timestamp is not None:
            results = [e for e in results if e.timestamp <= to_timestamp]
        if event_type is not None:
            results = [e for e in results if e.event_type == event_type]

        # Sort ascending by timestamp
        results.sort(key=lambda e: e.timestamp)

        if offset:
            results = results[offset:]
        if limit is not None:
            results = results[:limit]

        return results

    def get_latest_events(self, count: int = 5) -> list[TimelineEvent]:
        """Get the most recent timeline events.

        Args:
            count: Number of latest events to return (default: 5).

        Returns:
            The `count` most recent events (newest first).
        """
        sorted_events = sorted(
            self._events, key=lambda e: e.timestamp, reverse=True
        )
        return sorted_events[:count]

    def get_timeline_summary(self) -> dict[str, Any]:
        """Get a summary of the object's timeline.

        Returns:
            A dictionary with:
                - total_events: Count of all events
                - first_event: The earliest event (or None)
                - last_event: The most recent event (or None)
                - event_types: Map of event_type → count
                - date_range: [earliest, latest] timestamps (or None)
        """
        if not self._events:
            return {
                "total_events": 0,
                "first_event": None,
                "last_event": None,
                "event_types": {},
                "date_range": None,
            }

        sorted_events = sorted(self._events, key=lambda e: e.timestamp)
        event_types: dict[str, int] = {}
        for e in self._events:
            event_types[e.event_type] = event_types.get(e.event_type, 0) + 1

        return {
            "total_events": len(self._events),
            "first_event": sorted_events[0],
            "last_event": sorted_events[-1],
            "event_types": event_types,
            "date_range": [sorted_events[0].timestamp, sorted_events[-1].timestamp],
        }

    # ──────────────────────────────────────────────────────────────────────────
    # §8 — Lifecycle
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def current_stage(self) -> str:
        """Current lifecycle stage (e.g., 'active', 'archived')."""
        return self._current_stage

    @property
    def valid_transitions(self) -> dict[str, list[str]]:
        """Map of valid transitions from each lifecycle stage (read-only)."""
        return {k: list(v) for k, v in self._valid_transitions.items()}

    def transition(
        self,
        new_stage: str,
        evidence_ids: list[str] | None = None,
        reason: str = "",
        actor_id: str | None = None,
    ) -> None:
        """Transition the object to a new lifecycle stage.

        The transition is validated against the object's valid_transitions
        map before proceeding. Invalid transitions are rejected with a
        ValueError.

        Args:
            new_stage: The target lifecycle stage.
            evidence_ids: Optional evidence supporting the transition.
            reason: Optional reason for the transition.
            actor_id: ObjectID of the actor requesting the transition.
                Defaults to the current updated_by.

        Raises:
            ValueError: If the transition is not valid from the current stage.
        """
        if new_stage == self._current_stage:
            return

        valid_targets = self._valid_transitions.get(self._current_stage, [])
        if new_stage not in valid_targets:
            raise ValueError(
                f"Cannot transition from '{self._current_stage}' to "
                f"'{new_stage}'. Valid transitions from "
                f"'{self._current_stage}': {valid_targets}"
            )

        actor_id = actor_id or self._updated_by
        from_stage = self._current_stage
        now = _now_iso()

        transition_record = StageTransition(
            from_stage=from_stage,
            to_stage=new_stage,
            timestamp=now,
            actor_id=actor_id,
            reason=reason,
            evidence_ids=list(evidence_ids or []),
        )
        self._lifecycle_history.append(transition_record)

        old_snapshot = self._to_snapshot()
        self._current_stage = new_stage
        self._status = new_stage
        self._status_updated_at = now
        self._status_updated_by = actor_id
        self._updated_at = now
        self._updated_by = actor_id
        new_snapshot = self._to_snapshot()

        self._add_event(
            event_type="status_changed",
            data={
                "old_status": from_stage,
                "new_status": new_stage,
                "reason": reason,
            },
            source=actor_id,
            evidence_ids=evidence_ids,
            previous_state=old_snapshot,
            new_state=new_snapshot,
        )

        self._log_action(
            action="transition",
            actor_id=actor_id,
            detail=f"Stage changed from '{from_stage}' to '{new_stage}'",
            evidence_ids=evidence_ids,
        )
        self._bump_version(modified_by=actor_id)

    def get_lifecycle_history(self) -> list[StageTransition]:
        """Get the full history of lifecycle stage transitions.

        Returns:
            List of StageTransition records in chronological order.
        """
        return list(self._lifecycle_history)

    def can_transition_to(self, stage: str) -> bool:
        """Check whether a transition to the given stage is valid.

        Args:
            stage: The target lifecycle stage.

        Returns:
            True if the transition is valid from the current stage.
        """
        valid_targets = self._valid_transitions.get(self._current_stage, [])
        return stage in valid_targets

    # ──────────────────────────────────────────────────────────────────────────
    # §9 — Status
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def status(self) -> str:
        """Current operational status value."""
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        """Set the operational status directly.

        Prefer using `transition()` for lifecycle-aware status changes
        that respect the valid_transitions map. This setter is for
        cases where a direct status assignment is needed (e.g., during
        deserialization).

        Args:
            value: The new status value.
        """
        old_status = self._status
        if old_status == value:
            return
        now = _now_iso()
        old_snapshot = self._to_snapshot()
        self._status = value
        self._status_updated_at = now
        self._status_updated_by = self._updated_by
        self._add_event(
            event_type="status_changed",
            data={"old_status": old_status, "new_status": value},
            source=self._updated_by,
            previous_state=old_snapshot,
            new_state=self._to_snapshot(),
        )

    @property
    def status_detail(self) -> str:
        """Optional detailed status information."""
        return self._status_detail

    @status_detail.setter
    def status_detail(self, value: str) -> None:
        self._status_detail = value

    @property
    def status_updated_at(self) -> str:
        """ISO-8601 timestamp of when the status last changed."""
        return self._status_updated_at

    @property
    def status_updated_by(self) -> str:
        """ObjectID of the actor that last changed the status."""
        return self._status_updated_by

    @property
    def is_active(self) -> bool:
        """Whether the object is in an active operational state.

        An object is considered active if its status is not one of
        the known inactive statuses ('archived', 'deleted', 'superseded').
        """
        return self._status not in self._INACTIVE_STATUSES

    # ──────────────────────────────────────────────────────────────────────────
    # §10 — Ownership
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def owner_id(self) -> str:
        """ObjectID of the current owner."""
        return self._owner_id

    @property
    def owner_type(self) -> OwnerType:
        """Classification of the current owner."""
        return self._owner_type

    @property
    def owner_history(self) -> list[OwnershipRecord]:
        """Immutable history of ownership changes (read-only view)."""
        return list(self._owner_history)

    def transfer(
        self,
        new_owner_id: str,
        reason: str = "",
        evidence_ids: list[str] | None = None,
        *,
        new_owner_type: str | OwnerType | None = None,
        actor_id: str | None = None,
    ) -> None:
        """Transfer ownership to a new owner.

        Args:
            new_owner_id: ObjectID of the new owner.
            reason: Optional reason for the transfer.
            evidence_ids: Optional evidence supporting the transfer.
            new_owner_type: Optional owner type for the new owner.
                Defaults to the current owner type.
            actor_id: ObjectID of the actor requesting the transfer.
                Defaults to the current updated_by.
        """
        actor_id = actor_id or self._updated_by
        now = _now_iso()

        # Close current ownership period
        if self._owner_history:
            self._owner_history[-1].to_timestamp = now

        new_type = OwnerType(new_owner_type) if new_owner_type else self._owner_type

        record = OwnershipRecord(
            owner_id=new_owner_id,
            owner_type=new_type,
            from_timestamp=now,
            to_timestamp=None,
            reason=reason,
            evidence_ids=list(evidence_ids or []),
        )
        self._owner_history.append(record)

        old_owner = self._owner_id
        self._owner_id = new_owner_id
        self._owner_type = new_type

        self._add_event(
            event_type="ownership_transferred",
            data={
                "old_owner_id": old_owner,
                "new_owner_id": new_owner_id,
                "reason": reason,
            },
            source=actor_id,
            evidence_ids=evidence_ids,
        )
        self._log_action(
            action="transfer",
            actor_id=actor_id,
            detail=f"Ownership transferred from '{old_owner}' to '{new_owner_id}'",
            evidence_ids=evidence_ids,
        )
        self._bump_version(modified_by=actor_id)

    def is_owned_by(self, actor_id: str) -> bool:
        """Check whether the specified actor is the current owner.

        Args:
            actor_id: ObjectID of the actor to check.

        Returns:
            True if the actor is the current owner.
        """
        return self._owner_id == actor_id

    # ──────────────────────────────────────────────────────────────────────────
    # §11 — Permissions
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def acl(self) -> AccessControlList:
        """Access control list for this object."""
        return self._acl

    def check_permission(self, actor_id: str, action: str) -> bool:
        """Check whether an actor has permission to perform an action.

        Permission check logic:
            1. Owner always has full access.
            2. Deny rules always override allow rules.
            3. Role-based matching against defined roles.

        Args:
            actor_id: ObjectID of the actor requesting the action.
            action: The action name to check (e.g., 'view', 'update').

        Returns:
            True if the actor is permitted, False otherwise.
        """
        # Owner has full access
        if self._acl.owner and self._acl.owner.actor_id == actor_id:
            return True

        # Resolve action → required permission level
        required_role = self._resolve_required_role(action)

        # Check deny rules first (deny overrides allow)
        for entry in self._acl.entries:
            if entry.is_deny and entry.actor_id == actor_id:
                # Check scope match
                if entry.scope == "*" or entry.scope == action:
                    return False

        # Check allow rules
        for entry in self._acl.entries:
            if not entry.is_deny and entry.actor_id == actor_id:
                if entry.scope == "*" or entry.scope == action:
                    if self._role_satisfies(entry.role, required_role):
                        return True

        return False

    def grant(
        self,
        actor_id: str,
        role: str,
        scope: str = "*",
        granted_by: str | None = None,
    ) -> None:
        """Grant a permission to an actor.

        Args:
            actor_id: ObjectID of the actor to grant permission to.
            role: The role to grant (e.g., 'editor', 'viewer').
            scope: The scope of the permission ('*' = all scopes).
            granted_by: ObjectID of the actor granting the permission.
                Defaults to the current updated_by.
        """
        grantor = granted_by or self._updated_by
        entry = AccessControlEntry(
            actor_id=actor_id,
            role=role,
            scope=scope,
            granted_by=grantor,
        )
        # Replace any existing entry for same actor+scope
        self._acl.entries = [
            e
            for e in self._acl.entries
            if not (e.actor_id == actor_id and e.scope == scope)
        ]
        self._acl.entries.append(entry)
        self._log_action(
            action="grant",
            actor_id=grantor,
            detail=f"Granted role '{role}' (scope='{scope}') to '{actor_id}'",
        )
        self._bump_version(modified_by=grantor)

    def revoke(
        self,
        actor_id: str,
        role: str,
        scope: str = "*",
        revoked_by: str | None = None,
    ) -> None:
        """Revoke a permission from an actor.

        Args:
            actor_id: ObjectID of the actor to revoke permission from.
            role: The role to revoke.
            scope: The scope of the permission being revoked.
            revoked_by: ObjectID of the actor revoking the permission.
                Defaults to the current updated_by.
        """
        revoker = revoked_by or self._updated_by
        self._acl.entries = [
            e
            for e in self._acl.entries
            if not (
                e.actor_id == actor_id
                and e.role == role
                and e.scope == scope
            )
        ]
        self._log_action(
            action="revoke",
            actor_id=revoker,
            detail=f"Revoked role '{role}' (scope='{scope}') from '{actor_id}'",
        )
        self._bump_version(modified_by=revoker)

    def get_effective_permissions(self, actor_id: str) -> list[dict[str, str]]:
        """Get all effective permissions for an actor.

        Args:
            actor_id: ObjectID of the actor.

        Returns:
            List of dicts with 'role' and 'scope' keys.
        """
        if self._acl.owner and self._acl.owner.actor_id == actor_id:
            return [{"role": "owner", "scope": "*"}]

        permissions: list[dict[str, str]] = []
        for entry in self._acl.entries:
            if entry.actor_id == actor_id and not entry.is_deny:
                permissions.append({"role": entry.role, "scope": entry.scope})
        return permissions

    @staticmethod
    def _resolve_required_role(action: str) -> str:
        """Resolve an action name to the minimum required role level.

        Args:
            action: The action name.

        Returns:
            The minimum role required.
        """
        # Read actions
        if action in {"view", "get_timeline", "get_audit_log", "search"}:
            return "viewer"
        # Write actions
        if action in {"update", "add_evidence", "add_relationship"}:
            return "editor"
        # Elevated actions
        if action in {"delete", "transfer", "grant", "revoke"}:
            return "admin"
        # Default: require editor
        return "editor"

    @staticmethod
    def _role_satisfies(actual_role: str, required_role: str) -> bool:
        """Check if an actual role satisfies the required role level.

        Role hierarchy: owner > admin > editor > viewer

        Args:
            actual_role: The role the actor has.
            required_role: The minimum role required.

        Returns:
            True if the actual role satisfies the requirement.
        """
        hierarchy = {"viewer": 0, "editor": 1, "admin": 2, "owner": 3}
        actual_level = hierarchy.get(actual_role, -1)
        required_level = hierarchy.get(required_role, 0)
        return actual_level >= required_level

    # ──────────────────────────────────────────────────────────────────────────
    # §12 — Evidence
    # ──────────────────────────────────────────────────────────────────────────

    def add_evidence(
        self,
        evidence_id: str,
        attached_by: str | None = None,
        description: str = "",
    ) -> None:
        """Attach evidence to this object.

        Evidence is append-only — once attached, evidence references
        can be superseded but never removed.

        Args:
            evidence_id: The evidence record ID to attach.
            attached_by: ObjectID of the actor attaching the evidence.
                Defaults to the current updated_by.
            description: Optional human-readable description.
        """
        actor = attached_by or self._updated_by
        ref = EvidenceRef(
            evidence_id=evidence_id,
            attached_by=actor,
            description=description,
        )
        self._evidence_ids.append(evidence_id)
        self._evidence_refs.append(ref)
        self._add_event(
            event_type="evidence_added",
            data={
                "evidence_id": evidence_id,
                "description": description,
            },
            source=actor,
            evidence_ids=[evidence_id],
        )
        self._log_action(
            action="add_evidence",
            actor_id=actor,
            detail=f"Evidence '{evidence_id}' attached",
            evidence_ids=[evidence_id],
        )
        self._bump_version(modified_by=actor)

    def remove_evidence(self, evidence_id: str) -> None:
        """Mark evidence as superseded (soft-remove).

        Evidence cannot be truly deleted — it is marked as superseded
        to preserve audit integrity.

        Args:
            evidence_id: The evidence ID to supersede.

        Raises:
            ValueError: If no evidence with the given ID is attached.
        """
        for ref in self._evidence_refs:
            if ref.evidence_id == evidence_id and ref.superseded_by is None:
                ref.superseded_by = f"superseded_{_now_iso()}"
                self._add_event(
                    event_type="evidence_superseded",
                    data={"evidence_id": evidence_id},
                    source=self._updated_by,
                )
                self._log_action(
                    action="remove_evidence",
                    actor_id=self._updated_by,
                    detail=f"Evidence '{evidence_id}' superseded",
                )
                self._bump_version(modified_by=self._updated_by)
                return
        raise ValueError(
            f"Evidence '{evidence_id}' not found on object '{self._object_id}'"
        )

    def get_evidence(self) -> list[EvidenceRef]:
        """Get all active (non-superseded) evidence references.

        Returns:
            List of active EvidenceRef objects.
        """
        return [ref for ref in self._evidence_refs if ref.superseded_by is None]

    def get_evidence_chain(self) -> list[dict[str, Any]]:
        """Get the full provenance chain of all evidence.

        Returns:
            List of all evidence refs (including superseded) with
            supersession links, enabling full provenance traversal.
        """
        chain = []
        for ref in self._evidence_refs:
            entry = {
                "evidence_id": ref.evidence_id,
                "timestamp": ref.timestamp,
                "attached_by": ref.attached_by,
                "description": ref.description,
                "active": ref.superseded_by is None,
            }
            if ref.superseded_by:
                entry["superseded_by"] = ref.superseded_by
            chain.append(entry)
        return chain

    def get_confidence(self) -> float:
        """Derive confidence in the object's current state from evidence.

        Confidence is calculated as:
            - 0.0 if no evidence
            - Decayed by the ratio of superseded evidence
            - Base from active evidence count (capped at 1.0)

        Returns:
            Confidence value in [0.0, 1.0].
        """
        if not self._evidence_refs:
            return 0.0

        total = len(self._evidence_refs)
        active = sum(1 for ref in self._evidence_refs if ref.superseded_by is None)

        if total == 0:
            return 0.0

        # Base confidence from active ratio
        active_ratio = active / total

        if active_ratio == 0.0:
            return 0.0

        # Scale by total evidence (diminishing returns, cap at 10)
        evidence_score = min(total / 10.0, 1.0)

        return round(active_ratio * evidence_score * 0.9 + 0.1 * evidence_score, 4)

    # Internal: access the evidence refs list
    @property
    def _evidence_refs(self) -> list[EvidenceRef]:
        return self.__evidence_refs

    @_evidence_refs.setter
    def _evidence_refs(self, value: list[EvidenceRef]) -> None:
        self.__evidence_refs = value

    # ──────────────────────────────────────────────────────────────────────────
    # §13 — Memory (OPTIONAL)
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def memory_ids(self) -> list[str]:
        """References to associated memory records (read-only view)."""
        return list(self._memory_ids)

    def associate_memory(self, memory_id: str) -> None:
        """Associate a memory record with this object.

        Args:
            memory_id: The memory record ID to associate.
        """
        if memory_id not in self._memory_ids:
            self._memory_ids.append(memory_id)

    def get_memories(
        self,
        memory_type: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
    ) -> list[str]:
        """Get associated memory IDs with optional filters.

        Note: Full memory content retrieval is delegated to the Memory
        subsystem — this method returns IDs that can be resolved there.

        Args:
            memory_type: Optional filter by memory type.
            from_timestamp: Optional start of time range (ISO-8601).
            to_timestamp: Optional end of time range (ISO-8601).

        Returns:
            Filtered list of memory IDs.
        """
        results = list(self._memory_ids)
        return results

    def get_relevant_memories(self, context: str) -> list[str]:
        """Get memory IDs relevant to a given context.

        This is a stub that returns all memory IDs. The actual relevance
        scoring is delegated to the Memory subsystem.

        Args:
            context: The context string to match against.

        Returns:
            List of relevant memory IDs.
        """
        return list(self._memory_ids)

    # ──────────────────────────────────────────────────────────────────────────
    # §14 — AI Context
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def ai_summary(self) -> str:
        """Brief summary of what this object is (auto-generated if empty)."""
        if not self._ai_summary:
            self._ai_summary = self._generate_ai_summary()
        return self._ai_summary

    @ai_summary.setter
    def ai_summary(self, value: str) -> None:
        self._ai_summary = value

    @property
    def ai_understanding(self) -> str:
        """How an AI should understand/interact with this object."""
        if not self._ai_understanding:
            self._ai_understanding = self._generate_ai_understanding()
        return self._ai_understanding

    @ai_understanding.setter
    def ai_understanding(self, value: str) -> None:
        self._ai_understanding = value

    @property
    def relevant_objects(self) -> list[str]:
        """ObjectIDs of related objects the AI should consider."""
        related = set(self._relevant_objects)
        for rel in self._relationships:
            related.add(rel.target_id)
        return list(related)

    @relevant_objects.setter
    def relevant_objects(self, value: list[str]) -> None:
        self._relevant_objects = list(value)

    @property
    def interaction_history(self) -> list[InteractionRecord]:
        """Past AI interactions with this object (read-only view)."""
        return list(self._interaction_history)

    def add_interaction(
        self,
        interaction_type: str,
        summary: str,
        actor_id: str,
    ) -> str:
        """Record an AI interaction with this object.

        Args:
            interaction_type: Type of interaction (e.g., 'query', 'update').
            summary: Brief summary of what happened.
            actor_id: ObjectID of the actor that initiated the interaction.

        Returns:
            The interaction_id of the recorded interaction.
        """
        record = InteractionRecord(
            interaction_type=interaction_type,
            summary=summary,
            actor_id=actor_id,
        )
        self._interaction_history.append(record)
        return record.interaction_id

    def get_ai_context(self) -> str:
        """Generate the full AI context string for this object.

        This method assembles all relevant information about the object
        into a concise, structured string suitable for inclusion in an
        AI prompt.

        Returns:
            A structured multi-line string with the object's AI context.
        """
        lines: list[str] = [
            f"Object: {self._name} ({self._object_type})",
            f"ID: {self._object_id}",
            f"Status: {self._status}",
            f"Stage: {self._current_stage}",
            f"Version: {self._version}",
        ]

        if self._description:
            lines.append(f"Description: {self._description}")

        lines.append(f"Summary: {self.ai_summary}")
        lines.append(f"Understanding: {self.ai_understanding}")

        if self._aliases:
            lines.append(f"Aliases: {', '.join(self._aliases)}")

        if self._tags:
            lines.append(f"Tags: {', '.join(self._tags)}")

        if self._relationships:
            lines.append(f"Relationships ({len(self._relationships)}):")
            for rel in self._relationships[:5]:  # Show top 5
                lines.append(
                    f"  - [{rel.relationship_type}] → {rel.target_id}"
                    f" ({rel.label or 'no label'})"
                )
            if len(self._relationships) > 5:
                lines.append(f"  ... and {len(self._relationships) - 5} more")

        if self._relevant_objects:
            lines.append(
                f"Relevant objects: {', '.join(self._relevant_objects[:5])}"
            )

        if self._evidence_refs:
            active = sum(
                1 for r in self._evidence_refs if r.superseded_by is None
            )
            lines.append(f"Evidence: {active} active, {len(self._evidence_refs)} total")

        if self._interaction_history:
            last = self._interaction_history[-1]
            lines.append(
                f"Last interaction: [{last.interaction_type}] {last.summary}"
                f" ({last.timestamp})"
            )

        lines.append(f"Confidence: {self.get_confidence()}")

        return "\n".join(lines)

    def _generate_ai_summary(self) -> str:
        """Auto-generate a summary from the object's current state.

        Returns:
            A concise summary string.
        """
        parts = [f"{self._object_type}: {self._name}"]
        if self._description:
            parts.append(f"({self._description[:80]})")
        parts.append(f"[{self._status}]")
        if self._tags:
            parts.append(f"[{', '.join(self._tags[:3])}]")
        return " ".join(parts)

    def _generate_ai_understanding(self) -> str:
        """Auto-generate AI understanding directives from object state.

        Returns:
            A string describing how the AI should understand this object.
        """
        if self._object_type == "human":
            return (
                f"This is a Human ({self._name}) with agency rights. "
                "Treat with respect and obtain consent before actions."
            )
        if self._object_type == "organization":
            return (
                f"This is an Organization ({self._name}). "
                "Act in accordance with its governance policies."
            )
        if self._object_type in ("system", "agent", "ai"):
            return (
                f"This is a System/AI component ({self._name}). "
                "Operate within its defined capabilities and constraints."
            )
        return (
            f"This is a {self._object_type} object named '{self._name}' "
            f"in '{self._status}' state. Handle according to its type rules."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # §15 — Search
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def search_index(self) -> str:
        """Full-text search index derived from the object's fields."""
        return self._build_search_index()

    @property
    def search_terms(self) -> list[str]:
        """Keywords for search (auto-generated from object fields)."""
        return self._build_search_terms()

    @property
    def searchable_fields(self) -> list[str]:
        """Which fields are searchable (read-only view)."""
        return list(self._searchable_fields)

    def _build_search_index(self) -> str:
        """Build the full-text search index from object fields.

        Returns:
            A space-joined string of all searchable content.
        """
        parts: list[str] = [
            self._object_id,
            self._object_type,
            self._name,
            self._description,
            self._status,
            self._current_stage,
            *self._tags,
            *self._aliases,
            *self._external_ids.values(),
        ]
        return " ".join(p.lower() for p in parts if p)

    def _build_search_terms(self) -> list[str]:
        """Build search terms from object fields.

        Returns:
            List of lowercase search term keywords.
        """
        return list(
            set(
                self._build_search_index()
                .replace("_", " ")
                .replace("-", " ")
                .split()
            )
        )

    def search(self, query: str) -> list[SearchResult]:
        """Search within this object's fields for a query string.

        Performs case-insensitive substring matching against all
        searchable fields.

        Args:
            query: The search query string.

        Returns:
            List of SearchResult objects with relevance scores.
        """
        query_lower = query.lower()
        results: list[SearchResult] = []

        # Search in each field
        field_values: dict[str, str] = {
            "object_id": self._object_id,
            "object_type": self._object_type,
            "name": self._name,
            "description": self._description,
            "status": self._status,
        }

        for field, value in field_values.items():
            if query_lower in value.lower():
                score = self._compute_search_score(query_lower, value)
                results.append(
                    SearchResult(
                        field=field,
                        value=value,
                        score=score,
                        context=value[:100],
                    )
                )

        # Search in tags
        for tag in self._tags:
            if query_lower in tag.lower():
                results.append(
                    SearchResult(
                        field="tags",
                        value=tag,
                        score=1.0,
                        context=tag,
                    )
                )

        # Search in aliases
        for alias in self._aliases:
            if query_lower in alias.lower():
                results.append(
                    SearchResult(
                        field="aliases",
                        value=alias,
                        score=1.0,
                        context=alias,
                    )
                )

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def search_by_field(self, field: str, value: str) -> list[SearchResult]:
        """Search within a specific field for an exact or partial match.

        Args:
            field: The field name to search in (must be in searchable_fields).
            value: The value to search for.

        Returns:
            List of SearchResult objects.

        Raises:
            ValueError: If the field is not in searchable_fields.
        """
        if field not in self._searchable_fields:
            raise ValueError(
                f"Field '{field}' is not searchable. "
                f"Searchable fields: {self._searchable_fields}"
            )

        value_lower = value.lower()
        field_map: dict[str, str] = {
            "object_id": self._object_id,
            "object_type": self._object_type,
            "name": self._name,
            "description": self._description,
            "status": self._status,
        }

        if field in field_map:
            field_value = field_map[field]
            if value_lower in field_value.lower():
                return [
                    SearchResult(
                        field=field,
                        value=field_value,
                        score=self._compute_search_score(value_lower, field_value),
                        context=field_value[:100],
                    )
                ]
        elif field == "tags":
            matches = [t for t in self._tags if value_lower in t.lower()]
            return [
                SearchResult(field="tags", value=t, score=1.0, context=t)
                for t in matches
            ]
        elif field == "aliases":
            matches = [a for a in self._aliases if value_lower in a.lower()]
            return [
                SearchResult(field="aliases", value=a, score=1.0, context=a)
                for a in matches
            ]

        return []

    @staticmethod
    def _compute_search_score(query: str, value: str) -> float:
        """Compute a relevance score for a search match.

        Exact matches score higher than partial matches.

        Args:
            query: The lowercase search query.
            value: The field value being matched.

        Returns:
            Relevance score in [0.0, 1.0].
        """
        value_lower = value.lower()
        if value_lower == query:
            return 1.0
        if value_lower.startswith(query):
            return 0.9
        if query in value_lower:
            return 0.7
        # Partial word match
        words = value_lower.split()
        if any(query in w for w in words):
            return 0.5
        return 0.3

    # ──────────────────────────────────────────────────────────────────────────
    # §16 — Audit
    # ──────────────────────────────────────────────────────────────────────────

    def _log_action(
        self,
        action: str,
        actor_id: str,
        detail: str,
        evidence_ids: list[str] | None = None,
    ) -> str:
        """Internal method to record an audit entry with hash chain.

        Args:
            action: Canonical action name.
            actor_id: ObjectID of the actor.
            detail: Human-readable detail.
            evidence_ids: Optional evidence references.

        Returns:
            The entry_id of the audit entry.
        """
        previous_hash = self._audit_log[-1].hash if self._audit_log else ""

        entry = AuditEntry(
            action=action,
            actor_id=actor_id,
            detail=detail,
            evidence_ids=list(evidence_ids or []),
            previous_hash=previous_hash,
        )
        entry.hash = entry.compute_hash()
        self._audit_log.append(entry)
        return entry.entry_id

    def log_action(
        self,
        action: str,
        actor_id: str,
        detail: str,
        evidence_ids: list[str] | None = None,
    ) -> str:
        """Record an action in the audit log (public interface).

        The audit log is append-only and hash-chained for integrity
        verification.

        Args:
            action: Canonical action name (e.g., 'view', 'update', 'delete').
            actor_id: ObjectID of the actor performing the action.
            detail: Human-readable description of what was done.
            evidence_ids: Optional evidence references supporting this action.

        Returns:
            The entry_id of the audit entry.
        """
        return self._log_action(
            action=action,
            actor_id=actor_id,
            detail=detail,
            evidence_ids=evidence_ids,
        )

    def get_audit_log(
        self,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
        actor_id: str | None = None,
        action: str | None = None,
    ) -> list[AuditEntry]:
        """Get audit log entries with optional filtering.

        Args:
            from_timestamp: Optional start of time range (ISO-8601).
            to_timestamp: Optional end of time range (ISO-8601).
            actor_id: Optional filter by actor.
            action: Optional filter by action name.

        Returns:
            Filtered list of AuditEntry objects in chronological order.
        """
        results = list(self._audit_log)

        if from_timestamp is not None:
            results = [e for e in results if e.timestamp >= from_timestamp]
        if to_timestamp is not None:
            results = [e for e in results if e.timestamp <= to_timestamp]
        if actor_id is not None:
            results = [e for e in results if e.actor_id == actor_id]
        if action is not None:
            results = [e for e in results if e.action == action]

        return results

    def verify_integrity(self) -> bool:
        """Verify the integrity of the entire audit log hash chain.

        Each audit entry contains a SHA-256 hash of its content plus
        the hash of the previous entry. This method verifies that:
            1. Every entry's hash matches its content.
            2. Every entry's previous_hash matches the previous entry's hash.

        Returns:
            True if the entire audit log chain is intact, False otherwise.
        """
        for i, entry in enumerate(self._audit_log):
            # Verify self-hash
            expected_hash = entry.compute_hash()
            if entry.hash != expected_hash:
                return False

            # Verify chain link
            if i > 0:
                if entry.previous_hash != self._audit_log[i - 1].hash:
                    return False
            else:
                if entry.previous_hash != "":
                    return False

        return True

    # ──────────────────────────────────────────────────────────────────────────
    # §17 — Actions
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def available_actions(self) -> list[ActionDefinition]:
        """All actions available on this object (unfiltered by permissions)."""
        return list(self._available_actions)

    def _build_default_actions(self) -> list[ActionDefinition]:
        """Build the default set of required actions for every object.

        Returns:
            List of ActionDefinition objects.
        """
        return [
            ActionDefinition(
                name="view",
                display_name="View",
                description="View the object's current state and metadata",
                required_permission="viewer",
                parameters=[],
                effect="Read access to all public fields of the object",
            ),
            ActionDefinition(
                name="update",
                display_name="Update",
                description="Modify the object's mutable fields",
                required_permission="editor",
                parameters=[
                    {
                        "name": "fields",
                        "type": "dict",
                        "description": "Field names and new values",
                        "required": True,
                    }
                ],
                effect="Updates object fields and creates a new version",
            ),
            ActionDefinition(
                name="delete",
                display_name="Delete",
                description="Delete (retire) the object",
                required_permission="admin",
                parameters=[
                    {
                        "name": "reason",
                        "type": "string",
                        "description": "Reason for deletion",
                        "required": False,
                    }
                ],
                effect="Soft-deletes the object (status → deleted)",
            ),
            ActionDefinition(
                name="add_evidence",
                display_name="Add Evidence",
                description="Attach evidence to the object",
                required_permission="editor",
                parameters=[
                    {
                        "name": "evidence_id",
                        "type": "string",
                        "description": "Evidence record ID",
                        "required": True,
                    }
                ],
                effect="Attaches a new evidence reference to the object",
            ),
            ActionDefinition(
                name="add_relationship",
                display_name="Add Relationship",
                description="Create a relationship to another object",
                required_permission="editor",
                parameters=[
                    {
                        "name": "target_id",
                        "type": "string",
                        "description": "ObjectID of the target",
                        "required": True,
                    },
                    {
                        "name": "relationship_type",
                        "type": "string",
                        "description": "Canonical relationship type",
                        "required": True,
                    },
                ],
                effect="Creates a typed relationship to another object",
            ),
            ActionDefinition(
                name="get_timeline",
                display_name="Get Timeline",
                description="View the object's event timeline",
                required_permission="viewer",
                parameters=[
                    {
                        "name": "limit",
                        "type": "integer",
                        "description": "Max events to return",
                        "required": False,
                    }
                ],
                effect="Read-only access to the object's timeline",
            ),
            ActionDefinition(
                name="get_audit_log",
                display_name="Get Audit Log",
                description="View the object's audit trail",
                required_permission="viewer",
                parameters=[
                    {
                        "name": "limit",
                        "type": "integer",
                        "description": "Max entries to return",
                        "required": False,
                    }
                ],
                effect="Read-only access to the object's audit log",
            ),
        ]

    def register_action(
        self,
        name: str,
        display_name: str,
        description: str,
        handler: Callable,
        *,
        required_permission: str = "editor",
        parameters: list[dict[str, Any]] | None = None,
        effect: str = "",
    ) -> None:
        """Register a custom action handler for this object.

        Args:
            name: Canonical action name.
            display_name: Human-readable name.
            description: What the action does.
            handler: Callable that implements the action.
            required_permission: Required permission role.
            parameters: Optional parameter definitions.
            effect: Optional description of the action's effect.
        """
        definition = ActionDefinition(
            name=name,
            display_name=display_name,
            description=description,
            required_permission=required_permission,
            parameters=parameters or [],
            effect=effect,
        )
        self._available_actions.append(definition)
        self._custom_action_handlers[name] = handler

    def execute_action(
        self,
        action_name: str,
        params: dict[str, Any] | None = None,
        actor_id: str | None = None,
    ) -> ActionResult:
        """Execute an action on this object.

        This is the central dispatch point for all object actions.
        Built-in actions (view, update, delete, etc.) are handled
        internally. Custom actions are dispatched to registered handlers.

        Args:
            action_name: The canonical action name to execute.
            params: Optional parameters for the action.
            actor_id: ObjectID of the actor executing the action.
                Defaults to the current updated_by.

        Returns:
            An ActionResult indicating success or failure.
        """
        actor_id = actor_id or self._updated_by
        params = params or {}

        # Check permission
        if not self.check_permission(actor_id, action_name):
            return ActionResult(
                success=False,
                error=f"Permission denied: '{actor_id}' cannot perform "
                f"action '{action_name}'",
                action=action_name,
            )

        # Dispatch built-in actions
        builtin_handlers: dict[str, Callable] = {
            "view": self._action_view,
            "update": self._action_update,
            "delete": self._action_delete,
            "add_evidence": self._action_add_evidence,
            "add_relationship": self._action_add_relationship,
            "get_timeline": self._action_get_timeline,
            "get_audit_log": self._action_get_audit_log,
        }

        if action_name in builtin_handlers:
            handler = builtin_handlers[action_name]
            result = handler(params, actor_id)
        elif action_name in self._custom_action_handlers:
            try:
                handler = self._custom_action_handlers[action_name]
                output = handler(self, params, actor_id)
                result = ActionResult(
                    success=True,
                    result=output,
                    action=action_name,
                )
            except Exception as e:
                result = ActionResult(
                    success=False,
                    error=str(e),
                    action=action_name,
                )
        else:
            return ActionResult(
                success=False,
                error=f"Unknown action: '{action_name}'",
                action=action_name,
            )

        # Log the action execution to audit
        self._log_action(
            action=action_name,
            actor_id=actor_id,
            detail=f"Executed action '{action_name}' "
            f"({'success' if result.success else 'failed'})",
        )

        return result

    def get_available_actions(self, actor_id: str) -> list[ActionDefinition]:
        """Get actions available to a specific actor (filtered by permissions).

        Args:
            actor_id: ObjectID of the actor.

        Returns:
            List of ActionDefinition objects the actor is permitted to use.
        """
        return [
            action
            for action in self._available_actions
            if self.check_permission(actor_id, action.name)
        ]

    def is_action_available(self, action_name: str, actor_id: str) -> bool:
        """Check whether a specific action is available to an actor.

        Args:
            action_name: The canonical action name.
            actor_id: ObjectID of the actor.

        Returns:
            True if the action exists and the actor has permission.
        """
        # Check if action exists
        action_names = {a.name for a in self._available_actions}
        if action_name not in action_names:
            return False
        # Check permission
        return self.check_permission(actor_id, action_name)

    def _action_view(
        self, params: dict[str, Any], actor_id: str
    ) -> ActionResult:
        """Built-in 'view' action implementation."""
        return ActionResult(
            success=True,
            result=self.to_dict(),
            action="view",
        )

    def _action_update(
        self, params: dict[str, Any], actor_id: str
    ) -> ActionResult:
        """Built-in 'update' action implementation."""
        fields = params.get("fields", {})
        if not fields:
            return ActionResult(
                success=False,
                error="No fields provided for update",
                action="update",
            )

        old_snapshot = self._to_snapshot()
        updated_fields: list[str] = []

        for key, value in fields.items():
            if hasattr(self, key) and not key.startswith("_"):
                try:
                    setattr(self, key, value)
                    updated_fields.append(key)
                except (AttributeError, ValueError, TypeError) as e:
                    return ActionResult(
                        success=False,
                        error=f"Cannot update field '{key}': {e}",
                        action="update",
                    )

        if not updated_fields:
            return ActionResult(
                success=False,
                error="No valid fields to update",
                action="update",
            )

        self._updated_at = _now_iso()
        self._updated_by = actor_id

        self._add_event(
            event_type="object_updated",
            data={"updated_fields": updated_fields},
            source=actor_id,
            previous_state=old_snapshot,
            new_state=self._to_snapshot(),
        )
        self._bump_version(modified_by=actor_id)

        return ActionResult(
            success=True,
            result={"updated_fields": updated_fields},
            action="update",
        )

    def _action_delete(
        self, params: dict[str, Any], actor_id: str
    ) -> ActionResult:
        """Built-in 'delete' action implementation."""
        reason = params.get("reason", "No reason provided")
        try:
            self.transition(
                new_stage="deleted",
                reason=reason,
                actor_id=actor_id,
            )
        except ValueError as e:
            return ActionResult(
                success=False,
                error=str(e),
                action="delete",
            )
        return ActionResult(
            success=True,
            result={"status": "deleted", "reason": reason},
            action="delete",
        )

    def _action_add_evidence(
        self, params: dict[str, Any], actor_id: str
    ) -> ActionResult:
        """Built-in 'add_evidence' action implementation."""
        evidence_id = params.get("evidence_id")
        if not evidence_id:
            return ActionResult(
                success=False,
                error="evidence_id required",
                action="add_evidence",
            )
        description = params.get("description", "")
        self.add_evidence(
            evidence_id=evidence_id,
            attached_by=actor_id,
            description=description,
        )
        return ActionResult(
            success=True,
            result={"evidence_id": evidence_id},
            action="add_evidence",
        )

    def _action_add_relationship(
        self, params: dict[str, Any], actor_id: str
    ) -> ActionResult:
        """Built-in 'add_relationship' action implementation."""
        target_id = params.get("target_id")
        relationship_type = params.get("relationship_type")
        if not target_id or not relationship_type:
            return ActionResult(
                success=False,
                error="target_id and relationship_type required",
                action="add_relationship",
            )
        rel_id = self.add_relationship(
            target_id=target_id,
            relationship_type=relationship_type,
            metadata=params.get("metadata"),
        )
        return ActionResult(
            success=True,
            result={"relationship_id": rel_id},
            action="add_relationship",
        )

    def _action_get_timeline(
        self, params: dict[str, Any], actor_id: str
    ) -> ActionResult:
        """Built-in 'get_timeline' action implementation."""
        limit = params.get("limit")
        events = self.get_latest_events(count=limit or 20)
        return ActionResult(
            success=True,
            result=[e.__dict__ for e in events],
            action="get_timeline",
        )

    def _action_get_audit_log(
        self, params: dict[str, Any], actor_id: str
    ) -> ActionResult:
        """Built-in 'get_audit_log' action implementation."""
        limit = params.get("limit")
        entries = self._audit_log
        if limit:
            entries = entries[-limit:]
        return ActionResult(
            success=True,
            result=[e.__dict__ for e in entries],
            action="get_audit_log",
        )

    # ──────────────────────────────────────────────────────────────────────────
    # §18 — Versioning
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def version(self) -> int:
        """Current version number (monotonically increasing)."""
        return self._version

    @property
    def version_history(self) -> list[VersionRecord]:
        """Full version history (read-only view)."""
        return list(self._version_history)

    def _bump_version(self, modified_by: str) -> None:
        """Increment the version and record the change.

        This is called internally whenever the object's state changes.
        A snapshot of the current state is stored in the version history.

        Args:
            modified_by: ObjectID of the actor making the change.
        """
        now = _now_iso()
        self._version += 1
        self._updated_at = now
        self._updated_by = modified_by

        self._version_history.append(
            VersionRecord(
                version=self._version,
                timestamp=now,
                modified_by=modified_by,
                snapshot=self._to_snapshot(),
                change_summary=f"Auto-version bump to v{self._version}",
            )
        )

    def get_version(self, version_number: int) -> dict[str, Any] | None:
        """Get a snapshot of the object at a specific version.

        Args:
            version_number: The version number to retrieve.

        Returns:
            The serialized snapshot dict for that version, or None
            if the version does not exist.
        """
        for record in self._version_history:
            if record.version == version_number:
                return dict(record.snapshot)
        return None

    def get_latest_version(self) -> dict[str, Any]:
        """Get the snapshot of the current (latest) version.

        Returns:
            The serialized snapshot dict of the latest version.
        """
        return self._to_snapshot()

    def compare_versions(
        self, v1: int, v2: int
    ) -> DiffResult:
        """Compare two versions and produce a structured diff.

        Args:
            v1: Source version number.
            v2: Target version number.

        Returns:
            A DiffResult with added, removed, and changed fields.

        Raises:
            ValueError: If either version does not exist.
        """
        snapshot1 = self.get_version(v1)
        snapshot2 = self.get_version(v2)

        if snapshot1 is None:
            raise ValueError(f"Version {v1} does not exist")
        if snapshot2 is None:
            raise ValueError(f"Version {v2} does not exist")

        all_keys = set(snapshot1.keys()) | set(snapshot2.keys())
        added: dict[str, Any] = {}
        removed: dict[str, Any] = {}
        changed: dict[str, tuple[Any, Any]] = {}
        unchanged = 0

        for key in all_keys:
            val1 = snapshot1.get(key)
            val2 = snapshot2.get(key)

            if key not in snapshot1:
                added[key] = val2
            elif key not in snapshot2:
                removed[key] = val1
            elif val1 != val2:
                changed[key] = (val1, val2)
            else:
                unchanged += 1

        return DiffResult(
            version_from=v1,
            version_to=v2,
            added_fields=added,
            removed_fields=removed,
            changed_fields=changed,
            unchanged_count=unchanged,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Serialization / Deserialization
    # ──────────────────────────────────────────────────────────────────────────

    def _to_snapshot(self) -> dict[str, Any]:
        """Serialize the object's full current state as a plain dict.

        This snapshot is used for version history and timeline event
        previous/new state tracking.

        Returns:
            Dict with all mutable fields of the object.
        """
        return {
            "object_id": self._object_id,
            "object_type": self._object_type,
            "name": self._name,
            "description": self._description,
            "status": self._status,
            "status_detail": self._status_detail,
            "stage": self._current_stage,
            "version": self._version,
            "created_at": self._created_at,
            "updated_at": self._updated_at,
            "created_by": self._created_by,
            "updated_by": self._updated_by,
            "owner_id": self._owner_id,
            "owner_type": self._owner_type.value,
            "tenant_id": self._tenant_id,
            "space_id": self._space_id,
            "tags": list(self._tags),
            "confidence": self.get_confidence(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire object to a dictionary.

        Returns:
            A comprehensive dict representation of the object with
            all 15 protocol sections.
        """
        return {
            # §3 Mandatory Fields
            "object_id": self._object_id,
            "object_type": self._object_type,
            "name": self._name,
            "description": self._description,
            "status": self._status,
            "version": self._version,
            "created_at": self._created_at,
            "updated_at": self._updated_at,
            "created_by": self._created_by,
            "updated_by": self._updated_by,
            "owner_id": self._owner_id,
            "tenant_id": self._tenant_id,
            "space_id": self._space_id,
            "confidence": self.get_confidence(),
            "tags": self._tags,
            # §4 Identity
            "identity": {
                "object_id": self._object_id,
                "external_ids": dict(self._external_ids),
                "aliases": list(self._aliases),
                "identity_type": self._identity_type.value,
                "identity_authority": self._identity_authority.value,
            },
            # §5 Metadata
            "metadata": {
                "created_at": self._created_at,
                "updated_at": self._updated_at,
                "created_by": self._created_by,
                "updated_by": self._updated_by,
                "source": self._source.value,
                "source_detail": self._source_detail,
                "custom": dict(self._custom_metadata),
            },
            # §6 Relationships
            "relationships": [
                {
                    "relationship_id": r.relationship_id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "relationship_type": r.relationship_type,
                    "direction": r.direction.value,
                    "strength": r.strength,
                    "label": r.label,
                    "metadata": dict(r.metadata),
                    "created_at": r.created_at,
                    "evidence_ids": list(r.evidence_ids),
                }
                for r in self._relationships
            ],
            # §7 Timeline
            "timeline": {
                "events": [
                    {
                        "event_id": e.event_id,
                        "object_id": e.object_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp,
                        "actor_id": e.actor_id,
                        "data": dict(e.data),
                        "evidence_ids": list(e.evidence_ids),
                    }
                    for e in self._events
                ]
            },
            # §8 Lifecycle
            "lifecycle": {
                "current_stage": self._current_stage,
                "valid_transitions": {
                    k: list(v) for k, v in self._valid_transitions.items()
                },
                "history": [
                    {
                        "from_stage": t.from_stage,
                        "to_stage": t.to_stage,
                        "timestamp": t.timestamp,
                        "actor_id": t.actor_id,
                        "reason": t.reason,
                    }
                    for t in self._lifecycle_history
                ],
            },
            # §9 Status
            "status": {
                "status": self._status,
                "status_detail": self._status_detail,
                "status_updated_at": self._status_updated_at,
                "status_updated_by": self._status_updated_by,
                "is_active": self.is_active,
            },
            # §10 Ownership
            "ownership": {
                "owner_id": self._owner_id,
                "owner_type": self._owner_type.value,
                "history": [
                    {
                        "owner_id": o.owner_id,
                        "owner_type": o.owner_type.value,
                        "from": o.from_timestamp,
                        "to": o.to_timestamp,
                        "reason": o.reason,
                    }
                    for o in self._owner_history
                ],
            },
            # §11 Permissions
            "permissions": {
                "acl": {
                    "owner": {
                        "actor_id": self._acl.owner.actor_id,
                        "role": self._acl.owner.role,
                    }
                    if self._acl.owner
                    else None,
                    "entries": [
                        {
                            "actor_id": e.actor_id,
                            "role": e.role,
                            "scope": e.scope,
                            "granted_at": e.granted_at,
                            "granted_by": e.granted_by,
                        }
                        for e in self._acl.entries
                    ],
                }
            },
            # §12 Evidence
            "evidence": {
                "evidence_ids": list(self._evidence_ids),
                "active_evidence": [
                    {
                        "evidence_id": r.evidence_id,
                        "timestamp": r.timestamp,
                        "attached_by": r.attached_by,
                        "description": r.description,
                    }
                    for r in self.get_evidence()
                ],
                "evidence_chain": self.get_evidence_chain(),
                "confidence": self.get_confidence(),
            },
            # §14 AI Context
            "ai_context": {
                "summary": self._ai_summary,
                "understanding": self._ai_understanding,
                "relevant_objects": self.relevant_objects,
                "interaction_count": len(self._interaction_history),
            },
            # §16 Audit
            "audit": {
                "total_entries": len(self._audit_log),
                "integrity_verified": self.verify_integrity(),
            },
            # §17 Actions
            "actions": [
                {
                    "name": a.name,
                    "display_name": a.display_name,
                    "description": a.description,
                    "required_permission": a.required_permission,
                }
                for a in self._available_actions
            ],
            # §18 Versioning
            "versioning": {
                "current_version": self._version,
                "history": [
                    {
                        "version": v.version,
                        "timestamp": v.timestamp,
                        "modified_by": v.modified_by,
                        "change_summary": v.change_summary,
                    }
                    for v in self._version_history
                ],
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UniversalObject:
        """Deserialize a dictionary back into a UniversalObject.

        This is the inverse of to_dict(). It reconstructs the full
        object state from a serialized representation.

        Args:
            data: A dictionary produced by to_dict() or compatible format.

        Returns:
            A fully reconstructed UniversalObject instance.
        """
        # ── Extract mandatory fields ────────────────────────────────────
        identity = data.get("identity", {})
        metadata = data.get("metadata", {})
        # The top-level "status" key may be a string (flat dict) or a
        # status-block dict (nested dict from to_dict()).
        raw_status = data.get("status", "pending")
        if isinstance(raw_status, dict):
            status_value = raw_status.get("status", "pending")
            status_block = raw_status
        else:
            status_value = raw_status
            status_block = {}
        versioning = data.get("versioning", {})

        obj = cls(
            object_id=identity.get("object_id", data.get("object_id")),
            object_type=data.get("object_type", "unknown"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_by=metadata.get("created_by", data.get("created_by", "system")),
            updated_by=metadata.get("updated_by", data.get("updated_by", "system")),
            owner_id=data.get("owner_id", ""),
            tenant_id=data.get("tenant_id"),
            space_id=data.get("space_id"),
            tags=data.get("tags", []),
            status=status_value,
            identity_type=identity.get("identity_type", IdentityType.PERMANENT),
            identity_authority=identity.get(
                "identity_authority", IdentityAuthority.OBJECT_FACTORY
            ),
            external_ids=identity.get("external_ids", {}),
            aliases=identity.get("aliases", []),
            source=metadata.get("source", SourceType.SYSTEM),
            source_detail=metadata.get("source_detail", ""),
            custom_metadata=metadata.get("custom", {}),
        )

        # ── Restore timestamps ──────────────────────────────────────────
        if metadata.get("created_at"):
            obj._created_at = metadata["created_at"]
        if metadata.get("updated_at"):
            obj._updated_at = metadata["updated_at"]

        # ── Restore status details ──────────────────────────────────────
        if status_block.get("status_detail"):
            obj._status_detail = status_block["status_detail"]
        if status_block.get("status_updated_at"):
            obj._status_updated_at = status_block["status_updated_at"]
        if status_block.get("status_updated_by"):
            obj._status_updated_by = status_block["status_updated_by"]

        # ── Restore relationships ───────────────────────────────────────
        for rel_data in data.get("relationships", []):
            rel = RelationshipRef(
                relationship_id=rel_data.get("relationship_id", generate_uuid7()),
                source_id=rel_data.get("source_id", obj._object_id),
                target_id=rel_data.get("target_id", ""),
                relationship_type=rel_data.get("relationship_type", ""),
                direction=RelationshipDirection(
                    rel_data.get("direction", "directional")
                ),
                strength=rel_data.get("strength", 1.0),
                label=rel_data.get("label", ""),
                metadata=rel_data.get("metadata", {}),
                created_at=rel_data.get("created_at", _now_iso()),
                evidence_ids=rel_data.get("evidence_ids", []),
            )
            obj._relationships.append(rel)

        # ── Restore timeline events ─────────────────────────────────────
        timeline = data.get("timeline", {})
        for ev_data in timeline.get("events", []):
            event = TimelineEvent(
                event_id=ev_data.get("event_id", generate_uuid7()),
                object_id=ev_data.get("object_id", obj._object_id),
                event_type=ev_data.get("event_type", ""),
                timestamp=ev_data.get("timestamp", _now_iso()),
                actor_id=ev_data.get("actor_id", ""),
                data=ev_data.get("data", {}),
                evidence_ids=ev_data.get("evidence_ids", []),
            )
            obj._events.append(event)

        # ── Restore lifecycle ───────────────────────────────────────────
        lifecycle = data.get("lifecycle", {})
        if lifecycle.get("valid_transitions"):
            obj._valid_transitions = {
                k: list(v) for k, v in lifecycle["valid_transitions"].items()
            }
        for trans_data in lifecycle.get("history", []):
            obj._lifecycle_history.append(
                StageTransition(
                    from_stage=trans_data.get("from_stage", ""),
                    to_stage=trans_data.get("to_stage", ""),
                    timestamp=trans_data.get("timestamp", _now_iso()),
                    actor_id=trans_data.get("actor_id", ""),
                    reason=trans_data.get("reason", ""),
                )
            )

        # ── Restore ownership ───────────────────────────────────────────
        ownership = data.get("ownership", {})
        if ownership.get("history"):
            obj._owner_history = [
                OwnershipRecord(
                    owner_id=o.get("owner_id", ""),
                    owner_type=OwnerType(o.get("owner_type", "human")),
                    from_timestamp=o.get("from", _now_iso()),
                    to_timestamp=o.get("to"),
                    reason=o.get("reason", ""),
                )
                for o in ownership["history"]
            ]

        # ── Restore permissions ─────────────────────────────────────────
        permissions = data.get("permissions", {})
        acl_data = permissions.get("acl", {})
        owner_entry_data = acl_data.get("owner")
        if owner_entry_data:
            obj._acl.owner = AccessControlEntry(
                actor_id=owner_entry_data.get("actor_id", ""),
                role=owner_entry_data.get("role", "owner"),
                scope="*",
            )
        obj._acl.entries = [
            AccessControlEntry(
                actor_id=e.get("actor_id", ""),
                role=e.get("role", ""),
                scope=e.get("scope", "*"),
                granted_at=e.get("granted_at", _now_iso()),
                granted_by=e.get("granted_by", ""),
            )
            for e in acl_data.get("entries", [])
        ]

        # ── Restore evidence ────────────────────────────────────────────
        evidence = data.get("evidence", {})
        obj._evidence_ids = list(evidence.get("evidence_ids", []))
        for ref_data in evidence.get("evidence_chain", []):
            obj._evidence_refs.append(
                EvidenceRef(
                    evidence_id=ref_data.get("evidence_id", ""),
                    timestamp=ref_data.get("timestamp", _now_iso()),
                    attached_by=ref_data.get("attached_by", ""),
                    description=ref_data.get("description", ""),
                    superseded_by=ref_data.get("superseded_by"),
                )
            )

        # ── Restore AI context ──────────────────────────────────────────
        ai_ctx = data.get("ai_context", {})
        if ai_ctx.get("summary"):
            obj._ai_summary = ai_ctx["summary"]
        if ai_ctx.get("understanding"):
            obj._ai_understanding = ai_ctx["understanding"]
        if ai_ctx.get("relevant_objects"):
            obj._relevant_objects = list(ai_ctx["relevant_objects"])

        # ── Restore version history ─────────────────────────────────────
        for ver_data in versioning.get("history", []):
            ver = VersionRecord(
                version=ver_data.get("version", 1),
                timestamp=ver_data.get("timestamp", _now_iso()),
                modified_by=ver_data.get("modified_by", ""),
                change_summary=ver_data.get("change_summary", ""),
            )
            # Only append if not already present (constructor creates v1)
            if not any(v.version == ver.version for v in obj._version_history):
                obj._version_history.append(ver)

        if versioning.get("current_version"):
            obj._version = versioning["current_version"]

        # ── Restore audit log ───────────────────────────────────────────
        audit_data = data.get("audit", {})
        if audit_data.get("entries"):
            for aud_entry in audit_data["entries"]:
                entry = AuditEntry(
                    entry_id=aud_entry.get("entry_id", generate_uuid7()),
                    action=aud_entry.get("action", ""),
                    actor_id=aud_entry.get("actor_id", ""),
                    timestamp=aud_entry.get("timestamp", _now_iso()),
                    detail=aud_entry.get("detail", ""),
                    evidence_ids=aud_entry.get("evidence_ids", []),
                    previous_hash=aud_entry.get("previous_hash", ""),
                    hash=aud_entry.get("hash", ""),
                )
                obj._audit_log.append(entry)

        return obj

    # ──────────────────────────────────────────────────────────────────────────
    # Representation
    # ──────────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"UniversalObject("
            f"id='{self._object_id[:8]}...', "
            f"type='{self._object_type}', "
            f"name='{self._name}', "
            f"status='{self._status}', "
            f"v{self._version}"
            f")"
        )

    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self._object_type}: {self._name} [{self._status}] (v{self._version})"

    def __eq__(self, other: object) -> bool:
        """Two objects are equal iff they have the same object_id."""
        if not isinstance(other, UniversalObject):
            return NotImplemented
        return self._object_id == other._object_id

    def __hash__(self) -> int:
        """Hash based on the immutable object_id."""
        return hash(self._object_id)