"""
SHUNYA — Canonical Identity Resolution Interface (FDA4).

ONE canonical identity governance authority.

Identity is NOT memory:
- Identity = who/what an entity is (authoritative resolution)
- Memory = contextual information about an entity
- Knowledge = business facts about an entity

All identity claims converge on this interface.
No Gmail-specific identity authority.
No duplicate identity resolver.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Identity Types ────────────────────────────────────────────────────

class IdentityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    CONTACT = "contact"
    LEAD = "lead"
    USER = "user"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    SYSTEM = "system"


class ClaimType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    EXTERNAL_ID = "external_id"
    ALIAS = "alias"
    DOMAIN = "domain"
    SOCIAL_PROFILE = "social_profile"
    ADDRESS = "address"
    IDENTIFIER = "identifier"


class ClaimStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CONFLICTED = "conflicted"
    INVALIDATED = "invalidated"


class MergeStatus(str, Enum):
    NOT_MERGED = "not_merged"
    MERGED = "merged"
    SPLIT = "split"
    CONFLICTED = "conflicted"


class DuplicateClassification(str, Enum):
    CONFIRMED = "confirmed"
    POSSIBLE = "possible"
    NOT_DUPLICATE = "not_duplicate"
    CONFLICT = "conflict"


# ── Identity Claim ────────────────────────────────────────────────────

@dataclass
class IdentityClaim:
    """A single identity claim with provenance.

    Examples:
    - email address X belongs to person Y
    - phone X belongs to company Y
    - Gmail sender X resolves to contact Y
    """
    claim_id: str = ""
    identity_id: str = ""          # Resolved canonical identity
    identity_type: IdentityType = IdentityType.PERSON
    claim_type: ClaimType = ClaimType.EMAIL
    claim_value: str = ""          # The actual value (email, phone, name)
    source: str = ""               # "gmail", "contact", "import", "manual"
    source_id: str = ""            # Source-specific identifier
    tenant_id: str = ""
    confidence: float = 1.0
    status: ClaimStatus = ClaimStatus.ACTIVE
    observed_at: str = field(default_factory=_now_iso)
    created_at: str = field(default_factory=_now_iso)
    provenance: str = ""

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "identity_id": self.identity_id,
            "identity_type": self.identity_type.value if isinstance(self.identity_type, Enum) else self.identity_type,
            "claim_type": self.claim_type.value if isinstance(self.claim_type, Enum) else self.claim_type,
            "claim_value": self.claim_value,
            "source": self.source,
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "confidence": self.confidence,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "observed_at": self.observed_at,
            "provenance": self.provenance,
        }


# ── Identity Resolution Result ────────────────────────────────────────

@dataclass
class IdentityResolution:
    """Result of resolving an identity claim to a canonical identity."""
    identity_id: str = ""
    identity_type: IdentityType = IdentityType.PERSON
    claims: list[IdentityClaim] = field(default_factory=list)
    alias_values: list[str] = field(default_factory=list)
    confidence: float = 0.0
    resolution_method: str = ""    # "direct", "alias", "merge", "new"
    duplicate_of: list[str] = field(default_factory=list)
    merge_status: MergeStatus = MergeStatus.NOT_MERGED
    merged_identities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "identity_id": self.identity_id,
            "identity_type": self.identity_type.value if isinstance(self.identity_type, Enum) else self.identity_type,
            "claims": [c.to_dict() for c in self.claims],
            "alias_values": self.alias_values,
            "confidence": self.confidence,
            "resolution_method": self.resolution_method,
            "duplicate_of": self.duplicate_of,
            "merge_status": self.merge_status.value if isinstance(self.merge_status, Enum) else self.merge_status,
            "merged_identities": self.merged_identities,
        }


# ── Canonical Identity Interface ──────────────────────────────────────

class IdentityResolutionInterface(ABC):
    """FDA4 canonical governance interface for identity resolution.

    Every identity source (Gmail, Contacts, Import, API) must converge
    on this interface.

    Consumers must NOT:
    - Bypass this interface to access identity storage directly
    - Create a parallel identity resolver
    - Treat identity claims as memory or knowledge
    """

    @abstractmethod
    def resolve(self, claim_value: str, claim_type: ClaimType = ClaimType.EMAIL,
                tenant_id: str = "") -> IdentityResolution:
        """Resolve a claim value to a canonical identity.

        Returns the canonical identity, its claims, and alias values.
        """
        ...

    @abstractmethod
    def add_claim(self, claim: IdentityClaim) -> IdentityClaim:
        """Add a new identity claim.

        If the claim value matches an existing identity, the claim is
        linked to that identity. Otherwise, a new identity is created.
        """
        ...

    @abstractmethod
    def get_identity(self, identity_id: str,
                     tenant_id: str = "") -> Optional[IdentityResolution]:
        """Get the full identity resolution for a canonical identity ID."""
        ...

    @abstractmethod
    def get_claims(self, identity_id: str,
                   tenant_id: str = "") -> list[IdentityClaim]:
        """Get all claims for a canonical identity."""
        ...

    @abstractmethod
    def get_canonical_interface(self) -> str:
        """Return the canonical interface identifier."""
        return "IdentityResolutionInterface"


# ── Identity Governance Rules ─────────────────────────────────────────

class IdentityGovernance:
    """FDA4 governance rules for identity vs memory vs knowledge boundary.

    Identity claims must NOT be confused with:
    - Memory (contextual information about an entity)
    - Knowledge (authoritative business facts)
    """

    @staticmethod
    def is_valid_identity_type(t: str) -> bool:
        return t in [e.value for e in IdentityType]

    @staticmethod
    def is_valid_claim_type(t: str) -> bool:
        return t in [e.value for e in ClaimType]

    @staticmethod
    def assert_not_identity_leak(storage_type: str) -> None:
        """Identity claims must not be stored in non-identity stores."""
        forbidden = {"memory_records", "knowledge_facts", "evidence_records"}
        if storage_type in forbidden:
            raise ValueError(
                f"Forbidden: identity claims in {storage_type}. "
                "Identity claims must use the canonical IdentityResolutionInterface."
            )