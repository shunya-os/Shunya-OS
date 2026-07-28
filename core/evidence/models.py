"""
SHUNYA Evidence Engine — Data Models

Defines the core data structures for evidence lifecycle management:
evidence types, direction, status, the Evidence record itself, and
evidence chains for provenance tracking.

All models are fully immutable after creation (frozen dataclasses).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.kernel.types import generate_uuid7

# ---------------------------------------------------------------------------
# Evidence Type
# ---------------------------------------------------------------------------


class EvidenceType(Enum):
    """Canonical types of evidence in SHUNYA.

    Each type categorises the provenance and nature of the evidence record.
    """

    DOCUMENT = "document"
    RECORD = "record"
    OBSERVATION = "observation"
    STATEMENT = "statement"
    CONFIRMATION = "confirmation"
    RECEIPT = "receipt"
    LOG = "log"
    CERTIFICATE = "certificate"
    CONTRACT = "contract"
    COMMUNICATION = "communication"
    SYSTEM_LOG = "system_log"
    HUMAN_TESTIMONY = "human_testimony"
    FORECAST = "forecast"
    MEASUREMENT = "measurement"
    DERIVED = "derived"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Evidence Direction
# ---------------------------------------------------------------------------


class EvidenceDirection(Enum):
    """Whether the evidence supports or contradicts its subject."""

    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"


# ---------------------------------------------------------------------------
# Evidence Status
# ---------------------------------------------------------------------------


class EvidenceStatus(Enum):
    """Lifecycle states for an evidence record.

    Evidence is immutable after creation and can only transition through
    supersession — it is never deleted.  The status progression is:

        COLLECTED → VERIFIED → SUPERSEDED
                                    ↑
        CONTESTED ──────────────────┘
        REJECTED  ──────────────────┘

    * ``COLLECTED``: Freshly recorded, not yet verified.
    * ``VERIFIED``: Independently confirmed by a verifier.
    * ``SUPERSEDED``: Replaced by newer evidence; preserved for provenance.
    * ``CONTESTED``: Its validity is in question.
    * ``REJECTED``: Determined to be invalid or inadmissible.
    """

    COLLECTED = "collected"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"
    CONTESTED = "contested"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _compute_hash(
    evidence_id: str,
    object_id: str,
    evidence_type: str,
    statement: str,
    source: str,
    source_reliability: float,
    direction: str,
    timestamp: str,
    captured_at: str,
    parent_evidence_id: str | None,
    metadata: dict[str, Any],
) -> str:
    """Compute a deterministic SHA-256 integrity hash for an evidence record.

    The hash covers all content-bearing fields so that any tampering is
    detectable via :meth:`EvidenceEngine.verify_integrity`.
    """
    payload = {
        "evidence_id": evidence_id,
        "object_id": object_id,
        "evidence_type": evidence_type,
        "statement": statement,
        "source": source,
        "source_reliability": source_reliability,
        "direction": direction,
        "timestamp": timestamp,
        "captured_at": captured_at,
        "parent_evidence_id": parent_evidence_id,
        "metadata": dict(sorted(metadata.items())),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Evidence:
    """A single piece of evidence in the SHUNYA evidence system.

    Evidence is **immutable** after creation.  It can be superseded
    (marked as ``SUPERSEDED``) but never deleted or modified.  Integrity
    is guaranteed by a content-addressed SHA-256 hash.

    Attributes:
        evidence_id: Globally unique UUID v7 string.
        object_id: ObjectID of the subject this evidence is about.
        evidence_type: Categorical type of the evidence.
        statement: What the evidence asserts (free-form text).
        source: Who or what produced the evidence.
        source_reliability: Reliability of the source [0, 1].
        confidence: Derived confidence score [0, 1].
        direction: Whether this evidence supports or contradicts.
        timestamp: ISO-8601 string of when the evidence was collected.
        captured_at: ISO-8601 string of when underlying data was captured.
        verified_at: ISO-8601 string of when evidence was verified, or None.
        verified_by: Identifier of the verifier, or None.
        parent_evidence_id: UUID v7 of parent evidence (for chaining), or None.
        status: Current lifecycle status.
        metadata: Extensible metadata dictionary.
        hash: SHA-256 integrity hash of the evidence content.
    """

    evidence_id: str = field(default_factory=generate_uuid7)
    """Globally unique identifier for this evidence (UUID v7)."""

    object_id: str = ""
    """ObjectID of the subject this evidence is about."""

    evidence_type: str = EvidenceType.OTHER.value
    """Categorical type (string matching an ``EvidenceType`` value)."""

    statement: str = ""
    """What the evidence asserts (free-form text)."""

    source: str = ""
    """Who or what produced this evidence."""

    source_reliability: float = 0.5
    """Reliability of the source on [0, 1]."""

    confidence: float = 0.0
    """Derived confidence score [0, 1].  Computed, never asserted."""

    direction: str = EvidenceDirection.SUPPORTING.value
    """"supporting" or "contradicting"."""

    timestamp: str = field(default_factory=_now_iso)
    """ISO-8601 string of when the evidence was collected."""

    captured_at: str = field(default_factory=_now_iso)
    """ISO-8601 string of when underlying data was captured."""

    verified_at: str | None = None
    """ISO-8601 string of when evidence was verified, or ``None``."""

    verified_by: str | None = None
    """Identifier of the entity that verified this evidence, or ``None``."""

    parent_evidence_id: str | None = None
    """UUID v7 of the parent evidence in the chain, or ``None`` for root."""

    status: str = EvidenceStatus.COLLECTED.value
    """Current lifecycle status."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible metadata dictionary."""

    hash: str = field(init=False)
    """SHA-256 integrity hash of the evidence content."""

    def __post_init__(self) -> None:
        """Validate constraints after initialisation."""
        # Validate source_reliability range
        if not (0.0 <= self.source_reliability <= 1.0):
            raise ValueError(
                f"source_reliability must be in [0, 1], got {self.source_reliability}"
            )

        # Validate direction
        valid_directions = {e.value for e in EvidenceDirection}
        if self.direction not in valid_directions:
            raise ValueError(
                f"direction must be one of {valid_directions}, got {self.direction!r}"
            )

        # Validate evidence_type
        valid_types = {e.value for e in EvidenceType}
        if self.evidence_type not in valid_types:
            raise ValueError(
                f"evidence_type must be one of {valid_types}, got {self.evidence_type!r}"
            )

        # Validate status
        valid_statuses = {e.value for e in EvidenceStatus}
        if self.status not in valid_statuses:
            raise ValueError(
                f"status must be one of {valid_statuses}, got {self.status!r}"
            )

        # Compute the integrity hash using object.__setattr__ because the
        # dataclass is frozen.  The hash covers all content-bearing fields.
        h = _compute_hash(
            evidence_id=self.evidence_id,
            object_id=self.object_id,
            evidence_type=self.evidence_type,
            statement=self.statement,
            source=self.source,
            source_reliability=self.source_reliability,
            direction=self.direction,
            timestamp=self.timestamp,
            captured_at=self.captured_at,
            parent_evidence_id=self.parent_evidence_id,
            metadata=self.metadata,
        )
        object.__setattr__(self, "hash", h)


# ---------------------------------------------------------------------------
# EvidenceChain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceChain:
    """A provenance chain of evidence from root to leaf.

    The chain is ordered from the root (origin) evidence to the most
    recent descendant, forming a single path through the evidence DAG.

    Attributes:
        root_evidence_id: UUID v7 of the chain's root evidence.
        chain: Ordered list of ``Evidence``, root first, leaf last.
        depth: Number of links in the chain.
        overall_confidence: Aggregate confidence across the chain [0, 1].
        verified: Whether every link in the chain has been verified.
    """

    root_evidence_id: str
    """UUID v7 of the root (origin) evidence in this chain."""

    chain: list[Evidence]
    """Ordered list of ``Evidence`` records, root first, then descendants."""

    depth: int = 0
    """Number of hops from root to leaf."""

    overall_confidence: float = 0.0
    """Aggregate confidence across the chain [0, 1]."""

    verified: bool = False
    """Whether every link in the chain has been verified."""

    def __post_init__(self) -> None:
        """Auto-compute depth and verified flag."""
        object.__setattr__(self, "depth", len(self.chain) - 1 if self.chain else 0)
        if not self.chain:
            object.__setattr__(self, "verified", False)
        else:
            object.__setattr__(
                self,
                "verified",
                all(ev.status == EvidenceStatus.VERIFIED.value for ev in self.chain),
            )