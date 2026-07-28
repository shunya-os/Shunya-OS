"""
Relationship Engine — Data Models

Defines the core data structures for the SHUNYA Relationship Engine:
relationship types, directions, the Relationship dataclass, and
type identifiers.

Relationships are typed, directed connections between two UniversalObjects.
They describe how things relate to each other (Universal Ontology §6).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Relationship Direction
# ---------------------------------------------------------------------------

class RelationshipDirection(Enum):
    """The directionality of a relationship (Universal Ontology §6.2).

    Values:
        DIRECTIONAL: Source → target (asymmetric).
        BIDIRECTIONAL: Source ↔ target (symmetric in effect).
        HIERARCHICAL: Parent → child (transitive hierarchy).
        TEMPORAL: Time-bound (valid for a specific duration).
        CONTEXTUAL: Context-dependent (valid within a specific context).
        INHERITED: Transitive (inherited through other relationships).
    """

    DIRECTIONAL = "directional"
    BIDIRECTIONAL = "bidirectional"
    HIERARCHICAL = "hierarchical"
    TEMPORAL = "temporal"
    CONTEXTUAL = "contextual"
    INHERITED = "inherited"


# ---------------------------------------------------------------------------
# Relationship Type
# ---------------------------------------------------------------------------

class RelationshipType(Enum):
    """Canonical relationship types (Business Canon §3.5).

    These types cover the fundamental kinds of connections between
    UniversalObjects in SHUNYA.
    """

    OWNS = "owns"
    MEMBER_OF = "member_of"
    WORKS_AT = "works_at"
    REPORTS_TO = "reports_to"
    CREATED = "created"
    MODIFIED = "modified"
    REFERENCES = "references"
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTAINS = "contains"
    PART_OF = "part_of"
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    RELATED_TO = "related_to"


# ---------------------------------------------------------------------------
# Relationship Status
# ---------------------------------------------------------------------------

class RelationshipStatus(Enum):
    """Lifecycle status for a relationship (Business Canon §3.5).

    Follows the lifecycle: Proposed → Active → Superseded → Ended.
    """

    PROPOSED = "proposed"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ENDED = "ended"


# ---------------------------------------------------------------------------
# Relationship ID Generation
# ---------------------------------------------------------------------------

def _generate_relationship_id() -> str:
    """Generate a UUID v7 relationship ID.

    UUID v7 is time-ordered, prefix-sortable, and collision-resistant.
    """
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Relationship
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Relationship:
    """A typed, directed connection between two UniversalObjects.

    Relationships are the structural fabric of SHUNYA — they describe
    how entities, objects, and concepts relate to each other.

    **Ontological properties** (Universal Ontology §6.2):
    - Directionality: Source → target (or bidirectional, hierarchical, etc.)
    - Typedness: Every relationship has a canonical type.
    - Time-boundedness: Relationships exist for a duration.
    - Strength: A confidence/weight [0, 1].

    Attributes:
        relationship_id: Globally unique identifier (UUID v7).
        source_id: The object from which the relationship originates.
        target_id: The object to which the relationship points.
        relationship_type: The canonical type of the relationship.
        direction: The directionality semantics.
        strength: How well-established the relationship is [0, 1].
        label: Human-readable label for the relationship.
        metadata: Extensible key-value metadata.
        created_at: When the relationship was created.
        updated_at: When the relationship was last modified.
        created_by: ID of the entity that created this relationship.
        valid_from: Optional start of the relationship's validity window.
        valid_until: Optional end of the relationship's validity window.
        status: Current lifecycle status.
        evidence_ids: References to supporting evidence.
    """

    relationship_id: str = field(default_factory=_generate_relationship_id)
    source_id: str = ""
    target_id: str = ""
    relationship_type: RelationshipType = RelationshipType.RELATED_TO
    direction: RelationshipDirection = RelationshipDirection.DIRECTIONAL
    strength: float = 1.0
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "system"
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate invariants after construction."""
        if not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if not self.target_id:
            raise ValueError("target_id must be a non-empty string")
        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id must be different")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"strength must be in [0, 1], got {self.strength}")
        if not isinstance(self.relationship_type, RelationshipType):
            raise ValueError(
                f"relationship_type must be a RelationshipType enum, "
                f"got {self.relationship_type!r}"
            )
        if not isinstance(self.direction, RelationshipDirection):
            raise ValueError(
                f"direction must be a RelationshipDirection enum, "
                f"got {self.direction!r}"
            )
        if not isinstance(self.status, RelationshipStatus):
            raise ValueError(
                f"status must be a RelationshipStatus enum, "
                f"got {self.status!r}"
            )
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValueError("valid_from must precede valid_until")

        # Temporal relationships must have a validity window
        if self.direction == RelationshipDirection.TEMPORAL and self.valid_until is None:
            raise ValueError(
                "TEMPORAL relationships must specify valid_until"
            )

    # -- Convenience accessors -----------------------------------------------

    @property
    def is_active_now(self) -> bool:
        """``True`` if the relationship is active at the current moment.

        Checks both the lifecycle status and the temporal validity window.
        """
        if self.status != RelationshipStatus.ACTIVE:
            return False
        now = datetime.now(timezone.utc)
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True

    def is_valid_at(self, when: datetime) -> bool:
        """``True`` if the relationship was valid at the given time."""
        if self.status != RelationshipStatus.ACTIVE:
            return False
        if self.valid_from and when < self.valid_from:
            return False
        if self.valid_until and when > self.valid_until:
            return False
        return True

    def reversed(self) -> Relationship:
        """Return a new Relationship with source and target swapped.

        The new relationship retains the same type and strength but
        the direction is set to ``DIRECTIONAL`` (mirror semantics).
        """
        return Relationship(
            relationship_id=_generate_relationship_id(),
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type=self.relationship_type,
            direction=RelationshipDirection.DIRECTIONAL,
            strength=self.strength,
            label=f"(reverse) {self.label}" if self.label else "",
            metadata=self.metadata,
            created_by=self.created_by,
            evidence_ids=self.evidence_ids,
            status=self.status,
        )


# ---------------------------------------------------------------------------
# Relationship filter helpers
# ---------------------------------------------------------------------------

def matches_type(
    rel: Relationship,
    type_filter: RelationshipType | str | None,
) -> bool:
    """Return ``True`` if a relationship matches the given type filter.

    If *type_filter* is ``None``, all types match.
    """
    if type_filter is None:
        return True
    if isinstance(type_filter, str):
        return rel.relationship_type.value == type_filter
    return rel.relationship_type == type_filter


def matches_strength(rel: Relationship, min_strength: float | None) -> bool:
    """Return ``True`` if a relationship meets the minimum strength.

    If *min_strength* is ``None``, all strengths match.
    """
    if min_strength is None:
        return True
    return rel.strength >= min_strength