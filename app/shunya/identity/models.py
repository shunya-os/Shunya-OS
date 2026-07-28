"""SHUNYA — Identity Engine models (Phase D).

Canonical identity representation per SHUNYA_CORE_MODELS.md §3.

Architectural authority: ES-010, SHUNYA_CORE_MODELS.md §3
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class IdentityType(Enum):
    """Supported identity types per Core Models §3."""
    EMAIL = "email"
    PHONE = "phone"
    CHANNEL_WHATSAPP = "channel:whatsapp"
    CHANNEL_TELEGRAM = "channel:telegram"
    DOCUMENT_ID = "document_id"
    EXTERNAL_ID = "external_id"
    ALIAS = "alias"


class IdentityStatus(Enum):
    """Identity lifecycle states."""
    ACTIVE = "active"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"
    MERGED = "merged"
    ARCHIVED = "archived"


class ResolutionStatus(Enum):
    """Outcome of an identity resolution attempt."""
    MATCHED = "MATCHED"
    NO_MATCH = "NO_MATCH"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass
class IdentityClaim:
    """A raw identity claim to be resolved."""
    identity_type: str
    identity_value: str
    tenant_id: int = 0
    source: str = ""


@dataclass
class Identity:
    """Canonical identity record.

    Every identity has a unique ID, belongs to exactly one canonical person,
    and is scoped to exactly one tenant.
    """

    identity_id: str = ""
    person_id: str = ""
    identity_type: str = IdentityType.EMAIL.value
    identity_value: str = ""
    normalized_value: str = ""
    tenant_id: int = 0
    status: str = IdentityStatus.ACTIVE.value
    verification_state: str = "unverified"
    confidence: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    superseded_at: Optional[datetime] = None
    merged_into_id: Optional[str] = None
    merged_from_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.identity_id:
            self.identity_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at

    @property
    def is_active(self) -> bool:
        return self.status in (IdentityStatus.ACTIVE.value, IdentityStatus.VERIFIED.value)

    @property
    def is_verified(self) -> bool:
        return self.verification_state == "verified"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "person_id": self.person_id,
            "identity_type": self.identity_type,
            "identity_value": self.identity_value,
            "normalized_value": self.normalized_value,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "verification_state": self.verification_state,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else None,
            "merged_into_id": self.merged_into_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Identity":
        return cls(
            identity_id=data.get("identity_id", ""),
            person_id=data.get("person_id", ""),
            identity_type=data.get("identity_type", IdentityType.EMAIL.value),
            identity_value=data.get("identity_value", ""),
            normalized_value=data.get("normalized_value", ""),
            tenant_id=data.get("tenant_id", 0),
            status=data.get("status", IdentityStatus.ACTIVE.value),
            verification_state=data.get("verification_state", "unverified"),
            confidence=data.get("confidence", 0.5),
            provenance=data.get("provenance", {}),
            metadata=data.get("metadata", {}),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
            superseded_at=_parse_dt(data.get("superseded_at")),
            merged_into_id=data.get("merged_into_id"),
        )


@dataclass
class ResolutionResult:
    """Outcome of an identity resolution."""
    status: ResolutionStatus = ResolutionStatus.NO_MATCH
    identity: Optional[Identity] = None
    candidates: List[Identity] = field(default_factory=list)
    confidence: float = 0.0
    reason: str = ""


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
    return None


STRONG_TYPES = {
    IdentityType.EMAIL,
    IdentityType.PHONE,
    IdentityType.CHANNEL_WHATSAPP,
    IdentityType.CHANNEL_TELEGRAM,
    IdentityType.DOCUMENT_ID,
}

MEDIUM_TYPES = {IdentityType.EXTERNAL_ID}
WEAK_TYPES = {IdentityType.ALIAS}