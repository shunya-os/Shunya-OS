"""SHUNYA Evidence Engine — Canonical Evidence Models.

Constitutional data models only. No reasoning. No truth calculation.
No business logic. No persistence.

Architecture references:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    SMS-VOLUME-I_5-CORE-SEMANTICS.md §8 — The Meaning of Evidence
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §4 — Evidence Chain
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.evidence.enums import EvidenceStatus, EvidenceType, SourceCategory
from app.evidence.values import Confidence, Freshness


# ---------------------------------------------------------------------------
# Evidence identity — UUID v7-like, time-ordered, permanent
# ---------------------------------------------------------------------------

def _generate_evidence_id() -> str:
    """Generate a time-ordered evidence identity.

    Format: ev_<48-bit-ms-timestamp-hex><32-bit-random-hex>
    Permanent, unique, never reused.
    """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    rand = uuid.uuid4().hex[:8]
    return f"ev_{timestamp:012x}{rand}"


# ---------------------------------------------------------------------------
# EvidenceSource — canonical representation of origin (§8.2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceSource:
    """Canonical representation of evidence origin.

    Captures where the evidence came from, how it was produced,
    and what actor or process is responsible.

    No business assumptions. Universal.

    Attributes:
        category:   The source category (human, system, sensor, document,
                    derived, external)
        identifier: Unique identifier of the source within its category
                    (e.g., a human identity_id, a system name, a sensor id)
        description: Human-readable description of the source
        metadata:   Additional source-specific metadata
    """
    category: SourceCategory
    identifier: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Provenance — canonical chain of custody
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Provenance:
    """Canonical chain of custody for an evidence record.

    Append-only. Never rewritten. Each Provenance record is immutable
    once created.

    Tracks:
        - Who created the evidence
        - What process or engine produced it
        - What source it came from
        - What prior evidence it supersedes
        - What prior evidence it was derived from

    Attributes:
        created_by:   The actor, engine, or process that created this evidence
        created_at:   ISO 8601 timestamp of creation
        source:       The EvidenceSource describing origin
        process:      The engine or pipeline stage that produced this evidence
                      (e.g., "observer_engine", "reasoning_engine")
        supersedes:   Evidence ID that this record supersedes, or empty string
        derived_from: Evidence ID that this record was derived from, or empty
        rationale:    Free-text rationale for why this evidence was created
    """
    created_by: str
    created_at: str
    source: EvidenceSource
    process: str = ""
    supersedes: str = ""
    derived_from: str = ""
    rationale: str = ""


# ---------------------------------------------------------------------------
# Observation — "I observed X"
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Observation:
    """An observation record.

    An Observation records only: "I observed X."
    It does NOT answer "X is true."

    NOT truth.
    NOT reasoning.
    NOT conclusion.

    An Observation is the atomic unit of acquired information.
    It is the input from which all higher-order knowledge is derived.

    Attributes:
        observation_id:  Permanent, unique identity
        observer:        Who or what made the observation
        observed_at:     ISO 8601 timestamp of when the observation occurred
        content:         What was observed (free-text for flexibility)
        context:         The circumstances under which the observation was made
        confidence:      Raw confidence in the observation itself
        source:          Where the observation came from
        metadata:        Additional observation-specific metadata
    """
    observation_id: str = ""
    observer: str = ""
    observed_at: str = ""
    content: str = ""
    context: str = ""
    confidence: Confidence | None = None
    source: EvidenceSource | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.observation_id:
            object.__setattr__(self, "observation_id", _generate_evidence_id())
        if not self.observed_at:
            object.__setattr__(
                self, "observed_at",
                datetime.now(timezone.utc).isoformat(),
            )


# ---------------------------------------------------------------------------
# Evidence — canonical immutable evidence record (§8.2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    """Canonical immutable evidence record.

    Evidence is the foundation of explainability. Every computed
    conclusion carries traceable evidence. No output exists without
    provenance.

    Constitutional invariants enforced:
        - Evidence records are NEVER deleted
        - Evidence identity is permanent, unique, never reused
        - Evidence versions are append-only (never rewritten)
        - Every evidence record has at least one target
        - Confidence is always 0.0–1.0

    Attributes:
        evidence_id:   Permanent, unique, never reused
        target_id:     The object, node, or conclusion this evidence supports
        target_type:   The type of the target (e.g., "Node", "Conclusion")
        observation_id: The observation this evidence is based on, or empty
        provenance:    Canonical chain of custody (immutable)
        source:        Where this evidence came from
        evidence_type: How the evidence was produced (observed, reported, etc.)
        confidence:    Canonical confidence score
        status:        Lifecycle status (active, superseded, withdrawn, expired)
        version:       Monotonic version number (starts at 1)
        created_at:    ISO 8601 timestamp of creation
        supersedes:    Evidence ID that this record supersedes, or empty string
        freshness:     Temporal validity information
        metadata:      Additional context
    """
    evidence_id: str = ""
    target_id: str = ""
    target_type: str = ""
    observation_id: str = ""
    provenance: Provenance | None = None
    source: EvidenceSource | None = None
    evidence_type: str = EvidenceType.OBSERVED.value
    confidence: Confidence | None = None
    status: str = EvidenceStatus.ACTIVE.value
    version: int = 1
    created_at: str = ""
    supersedes: str = ""
    freshness: Freshness | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_id:
            object.__setattr__(self, "evidence_id", _generate_evidence_id())
        if not self.created_at:
            object.__setattr__(
                self, "created_at",
                datetime.now(timezone.utc).isoformat(),
            )

    # ---- Property helpers ---------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self.status == EvidenceStatus.ACTIVE.value

    @property
    def is_superseded(self) -> bool:
        return self.status == EvidenceStatus.SUPERSEDED.value

    @property
    def is_withdrawn(self) -> bool:
        return self.status == EvidenceStatus.WITHDRAWN.value

    @property
    def is_expired(self) -> bool:
        return self.status == EvidenceStatus.EXPIRED.value

    @property
    def short_id(self) -> str:
        return self.evidence_id[:16] if self.evidence_id else ""

    # ---- Version helpers ----------------------------------------------------

    def next_version(
        self,
        status: str = "",
        confidence: Confidence | None = None,
        provenance: Provenance | None = None,
        freshness: Freshness | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Evidence:
        """Create the next version of this evidence record.

        The original record is NOT modified (it is frozen).
        A new Evidence record is returned with incremented version.

        Version history is append-only. The original record is preserved
        in the store alongside the new version.

        Args:
            status:      New status, or current if empty
            confidence:  New confidence, or current if None
            provenance:  New provenance, or current if None
            freshness:   New freshness, or current if None
            metadata:    Metadata to merge with current

        Returns:
            A new Evidence record with version + 1
        """
        merged_metadata = dict(self.metadata)
        if metadata:
            merged_metadata.update(metadata)

        return Evidence(
            evidence_id=self.evidence_id,
            target_id=self.target_id,
            target_type=self.target_type,
            observation_id=self.observation_id,
            provenance=provenance or self.provenance,
            source=self.source,
            evidence_type=self.evidence_type,
            confidence=confidence or self.confidence,
            status=status or self.status,
            version=self.version + 1,
            created_at=datetime.now(timezone.utc).isoformat(),
            supersedes=(
                self.supersedes if self.supersedes
                else self.evidence_id
            ),
            freshness=freshness or self.freshness,
            metadata=merged_metadata,
        )

    # ---- Serialization ------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a canonical dictionary."""
        d: Dict[str, Any] = {
            "evidence_id": self.evidence_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "observation_id": self.observation_id,
            "evidence_type": self.evidence_type,
            "status": self.status,
            "version": self.version,
            "created_at": self.created_at,
            "supersedes": self.supersedes,
        }
        if self.provenance is not None:
            d["provenance"] = {
                "created_by": self.provenance.created_by,
                "created_at": self.provenance.created_at,
                "source": {
                    "category": self.provenance.source.category.value,
                    "identifier": self.provenance.source.identifier,
                    "description": self.provenance.source.description,
                },
                "process": self.provenance.process,
                "supersedes": self.provenance.supersedes,
                "derived_from": self.provenance.derived_from,
                "rationale": self.provenance.rationale,
            }
        if self.source is not None:
            d["source"] = {
                "category": self.source.category.value,
                "identifier": self.source.identifier,
                "description": self.source.description,
            }
        if self.confidence is not None:
            d["confidence"] = {
                "score": self.confidence.score,
                "label": self.confidence.label,
                "reason": self.confidence.reason,
            }
        if self.freshness is not None:
            d["freshness"] = {
                "captured_at": self.freshness.captured_at,
                "valid_until": self.freshness.valid_until,
            }
        if self.metadata:
            d["metadata"] = dict(self.metadata)
        return d


# ---------------------------------------------------------------------------
# EvidenceStore — abstract interface (in-memory for now)
# ---------------------------------------------------------------------------

class EvidenceStore:
    """Abstract interface for Evidence storage.

    Implementations:
        - InMemoryEvidenceStore (current — development / testing)
        - SqlEvidenceStore (future — production)

    No business logic. No reasoning. No search ranking.
    """

    def create(self, evidence: Evidence) -> Evidence:
        """Persist a new Evidence record.

        Raises ValueError if evidence_id already exists.
        """
        raise NotImplementedError

    def get(self, evidence_id: str) -> Evidence | None:
        """Get an Evidence record by identity. Returns None if not found."""
        raise NotImplementedError

    def get_version(self, evidence_id: str, version: int) -> Evidence | None:
        """Get a specific version of an Evidence record.

        Returns None if the evidence or version does not exist.
        """
        raise NotImplementedError

    def get_history(self, evidence_id: str) -> list[Evidence]:
        """Get the full version history for an Evidence record.

        Returns versions in ascending order (oldest first).
        The version history is append-only and never rewritten.

        Returns an empty list if the evidence does not exist.
        """
        raise NotImplementedError

    def count(self) -> int:
        """Total number of evidence records (counting base identities, not versions)."""
        raise NotImplementedError

    def all(self) -> list[Evidence]:
        """Get all evidence records (latest version of each)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# InMemoryEvidenceStore — development / testing implementation
# ---------------------------------------------------------------------------

class InMemoryEvidenceStore(EvidenceStore):
    """In-memory evidence store for development and testing.

    Thread-safe via RLock.
    Supports version history (append-only, never rewritten).
    """

    def __init__(self) -> None:
        import threading
        self._lock = threading.RLock()
        # evidence_id -> { version -> Evidence }
        self._store: dict[str, dict[int, Evidence]] = {}
        # Track latest version per evidence_id
        self._latest: dict[str, int] = {}

    def create(self, evidence: Evidence) -> Evidence:
        with self._lock:
            eid = evidence.evidence_id
            if eid in self._store:
                raise ValueError(
                    f"Evidence '{eid}' already exists in the store"
                )
            self._store[eid] = {evidence.version: evidence}
            self._latest[eid] = evidence.version
            return evidence

    def create_version(self, evidence: Evidence) -> Evidence:
        """Store a new version of an existing evidence record.

        Raises ValueError if the base evidence does not exist
        or if the version already exists (append-only invariant).
        """
        with self._lock:
            eid = evidence.evidence_id
            if eid not in self._store:
                raise ValueError(
                    f"Evidence '{eid}' not found in the store. "
                    "Cannot create a new version for a non-existent record."
                )
            if evidence.version in self._store[eid]:
                raise ValueError(
                    f"Version {evidence.version} of evidence '{eid}' "
                    "already exists. Version history is append-only."
                )
            self._store[eid][evidence.version] = evidence
            if evidence.version > self._latest[eid]:
                self._latest[eid] = evidence.version
            return evidence

    def get(self, evidence_id: str) -> Evidence | None:
        with self._lock:
            versions = self._store.get(evidence_id)
            if versions is None:
                return None
            latest_ver = self._latest.get(evidence_id)
            if latest_ver is None:
                return None
            return versions.get(latest_ver)

    def get_version(self, evidence_id: str, version: int) -> Evidence | None:
        with self._lock:
            versions = self._store.get(evidence_id)
            if versions is None:
                return None
            return versions.get(version)

    def get_history(self, evidence_id: str) -> list[Evidence]:
        with self._lock:
            versions = self._store.get(evidence_id)
            if versions is None:
                return []
            return [
                versions[v] for v in sorted(versions.keys())
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._store)

    def all(self) -> list[Evidence]:
        with self._lock:
            results: list[Evidence] = []
            for eid, latest_ver in self._latest.items():
                versions = self._store.get(eid, {})
                ev = versions.get(latest_ver)
                if ev is not None:
                    results.append(ev)
            return results


# ---------------------------------------------------------------------------
# Legacy compatibility stubs — Phase 7 evidence models
# Preserve the import contract for app/__init__.py and test files.
# ---------------------------------------------------------------------------

class SourceReference:
    """Legacy SQLAlchemy model stub. Compatibility only."""
    __tablename__ = "source_references"


class EvidenceLink:
    """Legacy SQLAlchemy model stub. Compatibility only."""
    __tablename__ = "evidence_links"


class AssertionRecord:
    """Legacy SQLAlchemy model stub. Compatibility only."""
    __tablename__ = "assertion_records"


class SourceAssessment:
    """Legacy SQLAlchemy model stub. Compatibility only."""
    __tablename__ = "source_assessments"
