"""
Identity Engine — Data Models

Defines the core data structures for the SHUNYA Identity Engine:
identity lifecycle, authentication methods, merge/split records,
and provenance tracking.

All models are fully immutable after creation (frozen dataclasses).
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Identity Status
# ---------------------------------------------------------------------------

class IdentityStatus(Enum):
    """Canonical lifecycle states for an Identity.

    Follows the Business Canon lifecycle: Created → Active → Merged/Split → Retired.
    - ``ACTIVE``: Identity is in full use.
    - ``MERGED``: This identity was merged into another primary identity.
    - ``SPLIT``: This identity was split; a new identity was created.
    - ``RETIRED``: Permanently decommissioned.  The ID is **never** reused.
    - ``PENDING``: Awaiting verification or activation.
    """

    ACTIVE = "active"
    MERGED = "merged"
    SPLIT = "split"
    RETIRED = "retired"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# Entity Type
# ---------------------------------------------------------------------------

class EntityType(Enum):
    """Canonical entity types from the Universal Ontology (§3.4)."""

    HUMAN = "human"
    ORGANIZATION = "organization"
    SYSTEM = "system"
    SERVICE = "service"


# ---------------------------------------------------------------------------
# Auth Method
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuthMethod:
    """An authentication method bound to an identity.

    Attributes:
        method_type: The kind of authenticator (``email``, ``phone``,
            ``oauth``, ``passkey``, ``ssh_key``, ``api_token``, etc.).
        identifier: The actual identifier value (e.g. ``user@example.com``,
            ``+1-555-0100``, ``oauth|google|12345``).
        is_primary: Whether this is the preferred method for the identity.
        verified_at: ISO-8601 timestamp of last verification, or ``None``.
        confidence: Confidence in this method's binding [0, 1].
    """

    method_type: str
    identifier: str
    is_primary: bool = False
    verified_at: datetime | None = None
    confidence: float = 1.0

    def __post_init__(self) -> None:
        """Validate invariants after construction."""
        if not self.method_type or not self.method_type.strip():
            raise ValueError("method_type must be a non-empty string")
        if not self.identifier or not self.identifier.strip():
            raise ValueError("identifier must be a non-empty string")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")

    @property
    def is_verified(self) -> bool:
        """True when this method has been verified."""
        return self.verified_at is not None


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Provenance:
    """Record of how and why an identity was created.

    Attributes:
        source: The system or process that created the identity
            (``identity_engine``, ``import``, ``oauth``, ``admin``, etc.).
        source_detail: Free-form context about the creation.
        performed_by: Identifier of the actor (human or system) that
            performed the creation.
        timestamp: When the creation occurred.
        evidence_id: Optional reference to supporting evidence.
    """

    source: str = "identity_engine"
    source_detail: str = ""
    performed_by: str = "system"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_id: str | None = None


# ---------------------------------------------------------------------------
# Identity ID Generation
# ---------------------------------------------------------------------------

_IDENTITY_ID_PATTERN = re.compile(r"^sid_[0-9a-f]{24,32}$")


def _generate_identity_id() -> str:
    """Generate a permanent, unique identity ID (``sid_`` + 128-bit hex)."""
    return "sid_" + secrets.token_hex(16)


def is_valid_identity_id(candidate: str) -> bool:
    """Return ``True`` if *candidate* is a valid identity ID format."""
    return bool(_IDENTITY_ID_PATTERN.match(candidate))


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Identity:
    """A permanent, unique identity for an entity in SHUNYA.

    Identity is the ontological ``thisness`` of an entity — the property
    that makes it *this* entity and not any other (§4 of Universal Ontology).

    **Rules** (from Universal Ontology §4.2):
    - Uniqueness: No two distinct entities share the same identity.
    - Permanence: Identity is assigned at inception and never changes.
    - Non-reusability: Retired IDs are never reassigned.
    - Essentiality: Identity is essential, not accidental.

    Attributes:
        identity_id: Permanent unique identifier (``sid_`` + 32 hex chars).
        display_name: Human-readable name for this identity.
        entity_type: The kind of entity (human, organization, system, service).
        auth_methods: Authentication methods bound to this identity.
        status: Current lifecycle status.
        created_at: ISO-8601 timestamp of creation.
        updated_at: ISO-8601 timestamp of last change.
        metadata: Extensible key-value metadata.
        provenance: Record of how this identity was created.
    """

    identity_id: str = field(default_factory=_generate_identity_id)
    display_name: str = ""
    entity_type: EntityType = EntityType.HUMAN
    auth_methods: tuple[AuthMethod, ...] = ()
    status: IdentityStatus = IdentityStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: Provenance = field(default_factory=Provenance)

    def __post_init__(self) -> None:
        """Validate invariants after construction."""
        if not is_valid_identity_id(self.identity_id):
            raise ValueError(
                f"Invalid identity_id format: {self.identity_id!r} "
                f"(expected 'sid_' + 32 hex chars)"
            )
        if not isinstance(self.entity_type, EntityType):
            raise ValueError(
                f"entity_type must be an EntityType enum, got {self.entity_type!r}"
            )
        if not isinstance(self.status, IdentityStatus):
            raise ValueError(
                f"status must be an IdentityStatus enum, got {self.status!r}"
            )
        # Ensure at most one primary auth method
        primary_count = sum(1 for m in self.auth_methods if m.is_primary)
        if primary_count > 1:
            raise ValueError(
                f"At most one auth method may be primary; found {primary_count}"
            )

    # -- Convenience accessors -----------------------------------------------

    @property
    def primary_auth_method(self) -> AuthMethod | None:
        """Return the primary auth method, or ``None``."""
        for m in self.auth_methods:
            if m.is_primary:
                return m
        return None

    @property
    def is_active(self) -> bool:
        """``True`` when the identity is in ``ACTIVE`` or ``PENDING`` status."""
        return self.status in (IdentityStatus.ACTIVE, IdentityStatus.PENDING)

    def with_status(self, new_status: IdentityStatus) -> Identity:
        """Return a new Identity with an updated status (immutable pattern).

        This is the only way to change an identity's status since the
        dataclass is frozen.
        """
        return Identity(
            identity_id=self.identity_id,
            display_name=self.display_name,
            entity_type=self.entity_type,
            auth_methods=self.auth_methods,
            status=new_status,
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            metadata=self.metadata,
            provenance=self.provenance,
        )

    def with_auth_methods(self, methods: tuple[AuthMethod, ...]) -> Identity:
        """Return a new Identity with replaced auth methods."""
        return Identity(
            identity_id=self.identity_id,
            display_name=self.display_name,
            entity_type=self.entity_type,
            auth_methods=methods,
            status=self.status,
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            metadata=self.metadata,
            provenance=self.provenance,
        )

    def with_metadata(self, updates: dict[str, Any]) -> Identity:
        """Return a new Identity with merged metadata."""
        merged = dict(self.metadata)
        merged.update(updates)
        return Identity(
            identity_id=self.identity_id,
            display_name=self.display_name,
            entity_type=self.entity_type,
            auth_methods=self.auth_methods,
            status=self.status,
            created_at=self.created_at,
            updated_at=datetime.now(timezone.utc),
            metadata=merged,
            provenance=self.provenance,
        )


# ---------------------------------------------------------------------------
# Merge / Split Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MergeRecord:
    """An immutable record of an identity merge operation.

    Attributes:
        primary_identity_id: The identity that survived the merge.
        secondary_identity_id: The identity that was absorbed.
        timestamp: When the merge occurred.
        reason: Why the merge was performed.
        evidence_id: Optional reference to supporting evidence.
        performed_by: Who or what performed the merge.
    """

    primary_identity_id: str
    secondary_identity_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""
    evidence_id: str | None = None
    performed_by: str = "system"


@dataclass(frozen=True)
class SplitRecord:
    """An immutable record of an identity split operation.

    Attributes:
        original_identity_id: The identity that was split.
        new_identity_id: The newly created identity.
        timestamp: When the split occurred.
        reason: Why the split was performed.
        transferred_methods: Identifiers of auth methods moved to the new identity.
        performed_by: Who or what performed the split.
    """

    original_identity_id: str
    new_identity_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = ""
    transferred_methods: tuple[str, ...] = ()
    performed_by: str = "system"