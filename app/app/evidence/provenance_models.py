"""SHUNYA Evidence Engine — Provenance Models.

Immutable provenance models for Evidence Chain tracking.
Append-only. No mutations. No reasoning.

References:
    SMS-VOLUME-II-WORLD-MODEL.md §8 — Evidence Contract
    UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md §4.3 — Evidence chain
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.evidence.provenance_enums import DerivationType, ProvenanceRelationType, VerificationStatus


# ---------------------------------------------------------------------------
# SourceIdentity — canonical identity for any evidence source
# ---------------------------------------------------------------------------

def _generate_source_id() -> str:
    """Generate a time-ordered source identity.

    Format: src_<48-bit-ms-timestamp-hex><32-bit-random-hex>
    Permanent, unique, never reused.
    """
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    rand = uuid.uuid4().hex[:8]
    return f"src_{timestamp:012x}{rand}"


@dataclass(frozen=True)
class SourceIdentity:
    """Canonical identity for every evidence source.

    Universal source types only — no business assumptions:

    - HUMAN: Direct human input or testimony
    - SYSTEM: Automated system output
    - SENSOR: Physical or logical sensor reading
    - DOCUMENT: Document or record source
    - EXTERNAL: External service or API
    - DERIVED: Process that derived evidence from other sources

    Attributes:
        source_id: Permanent, unique, never reused
        source_type: Universal category (human, system, sensor, document, external, derived)
        identifier: Unique identifier within the source type
        timestamp: When this source was first recorded
    """
    source_id: str = ""
    source_type: str = ""
    identifier: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        """Auto-generate ID and timestamp if not provided."""
        if not self.source_id:
            object.__setattr__(self, "source_id", _generate_source_id())
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# SourceMetadata — immutable descriptive metadata for sources
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceMetadata:
    """Immutable descriptive metadata for evidence sources.

    Descriptive only. No business logic.
    """
    identifier: str
    description: str = ""
    origin: str = ""
    capture_method: str = ""
    producer: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# DerivationRecord — represents deterministic transformations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DerivationRecord:
    """Represents a deterministic transformation.

    NOT reasoning. NOT inference. These are pure data transformations:

    - The original evidence is preserved
    - The derivation is recorded as an immutable fact
    - No truth claims are made

    Attributes:
        derivation_type: How the transformation occurred (parsed, normalized, etc.)
        source_evidence_id: The evidence that was transformed
        target_evidence_id: The evidence created by transformation
        process: Which process performed the transformation
        parameters: Any parameters used in the transformation
        timestamp: When the derivation occurred
    """
    derivation_type: str
    source_evidence_id: str
    target_evidence_id: str
    process: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# VerificationRecord — records verification activity
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerificationRecord:
    """Records verification activity on evidence.

    NOT truth calculation. Only records verification events:

    - verified: Confirmed by verification process
    - unverified: No verification yet
    - challenged: Challenged by another party
    - confirmed: Independently confirmed

    Attributes:
        evidence_id: The evidence being verified
        status: Verification outcome
        verified_by: Who or what performed verification
        method: How the verification was performed
        details: Additional details about the verification
        timestamp: When the verification occurred
    """
    evidence_id: str
    status: str = VerificationStatus.UNVERIFIED.value
    verified_by: str = ""
    method: str = ""
    details: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Citation — canonical reference from evidence to supporting evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Citation:
    """Canonical reference from evidence to supporting evidence.

    Supports many-to-many relationships:
    - One evidence can cite multiple supporting evidence
    - One evidence can be cited by multiple other evidence

    Attributes:
        citing_evidence_id: The evidence making the citation
        cited_evidence_id: The evidence being cited
        contribution: How much this citation contributes (0.0-1.0)
        rationale: Why this citation is relevant
        timestamp: When the citation was created
    """
    citing_evidence_id: str
    cited_evidence_id: str
    contribution: float = 1.0
    rationale: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# EvidenceChainLink — single link in an evidence chain
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceChainLink:
    """Single link in an evidence chain.

    Links evidence to other evidence via provenance relationships:

    - parent: The evidence this one was derived from
    - derived: Evidence derived from this one
    - superseded: Evidence this one replaced
    - withdrawn: Evidence this one nullified

    Attributes:
        link_type: Type of provenance relationship
        target_evidence_id: The related evidence
        contribution: Degree of relationship (0.0-1.0)
        timestamp: When this link was established
    """
    link_type: str
    target_evidence_id: str
    contribution: float = 1.0
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# EvidenceChain — immutable chain linking evidence generations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceChain:
    """Immutable chain linking evidence generations.

    Append-only chain. All links are preserved:

    - parent_evidence: Evidence this one was derived from
    - derived_evidence: Evidence derived from this one
    - superseded_evidence: Evidence this one replaced
    - withdrawn_evidence: Evidence this one nullified

    Attributes:
        evidence_id: The evidence this chain belongs to
        links: List of EvidenceChainLink records (append-only)
        root_evidence_id: The original source evidence in the chain
    """
    evidence_id: str
    links: tuple[EvidenceChainLink, ...] = field(default_factory=tuple)
    root_evidence_id: str = ""


# ---------------------------------------------------------------------------
# ProvenanceGraph — canonical provenance relationships tracker
# ---------------------------------------------------------------------------

class ProvenanceGraph:
    """Canonical provenance relationships tracker.

    Tracks:
    - origin: Where evidence originated
    - derivation: How evidence was derived from other evidence
    - transformation: What transformations were applied
    - aggregation: What evidence was combined
    - citation: What evidence cites what other evidence
    - verification: Verification events on evidence

    Thread-safe for concurrent access.
    """

    def __init__(self) -> None:
        import threading
        self._lock = threading.RLock()
        self._origin: Dict[str, str] = {}  # evidence_id -> source_id
        self._derivation: Dict[str, str] = {}  # evidence_id -> derived_from_evidence_id
        self._transformation: Dict[str, DerivationRecord] = {}
        self._aggregation: Dict[str, List[str]] = {}  # evidence_id -> list of source evidence_ids
        self._citation: Dict[str, List[Citation]] = {}  # evidence_id -> citations it makes
        self._verification: Dict[str, List[VerificationRecord]] = {}  # evidence_id -> verifications

    # ---- Origin ----

    def set_origin(self, evidence_id: str, source_id: str) -> None:
        with self._lock:
            self._origin[evidence_id] = source_id

    def get_origin(self, evidence_id: str) -> Optional[str]:
        with self._lock:
            return self._origin.get(evidence_id)

    # ---- Derivation ----

    def add_derivation(self, evidence_id: str, derived_from: str) -> None:
        with self._lock:
            self._derivation[evidence_id] = derived_from

    def get_derivation(self, evidence_id: str) -> Optional[str]:
        with self._lock:
            return self._derivation.get(evidence_id)

    def get_derivation_chain(self, evidence_id: str) -> List[str]:
        with self._lock:
            chain: List[str] = []
            current = evidence_id
            while current in self._derivation:
                current = self._derivation[current]
                chain.append(current)
            return chain

    # ---- Transformation ----

    def add_transformation(self, record: DerivationRecord) -> None:
        with self._lock:
            key = f"{record.source_evidence_id}->{record.target_evidence_id}"
            self._transformation[key] = record

    def get_transformation(self, source_evidence_id: str, target_evidence_id: str) -> Optional[DerivationRecord]:
        with self._lock:
            key = f"{source_evidence_id}->{target_evidence_id}"
            return self._transformation.get(key)

    def get_transformations_for_source(self, source_evidence_id: str) -> List[DerivationRecord]:
        with self._lock:
            return [r for r in self._transformation.values() if r.source_evidence_id == source_evidence_id]

    # ---- Aggregation ----

    def add_aggregation(self, target_evidence_id: str, source_evidence_ids: List[str]) -> None:
        with self._lock:
            if target_evidence_id not in self._aggregation:
                self._aggregation[target_evidence_id] = []
            self._aggregation[target_evidence_id].extend(source_evidence_ids)

    def get_aggregation_sources(self, evidence_id: str) -> List[str]:
        with self._lock:
            return list(self._aggregation.get(evidence_id, []))

    # ---- Citation ----

    def add_citation(self, citation: Citation) -> None:
        with self._lock:
            if citation.citing_evidence_id not in self._citation:
                self._citation[citation.citing_evidence_id] = []
            self._citation[citation.citing_evidence_id].append(citation)

    def get_citations(self, evidence_id: str) -> List[Citation]:
        with self._lock:
            return list(self._citation.get(evidence_id, []))

    def get_cited_by(self, evidence_id: str) -> List[Citation]:
        with self._lock:
            cited: List[Citation] = []
            for eid, citations in self._citation.items():
                for c in citations:
                    if c.cited_evidence_id == evidence_id:
                        cited.append(c)
            return cited

    # ---- Verification ----

    def add_verification(self, record: VerificationRecord) -> None:
        with self._lock:
            if record.evidence_id not in self._verification:
                self._verification[record.evidence_id] = []
            self._verification[record.evidence_id].append(record)

    def get_verifications(self, evidence_id: str) -> List[VerificationRecord]:
        with self._lock:
            return list(self._verification.get(evidence_id, []))

    # ---- Query ----

    def get_full_provenance(self, evidence_id: str) -> Dict[str, Any]:
        with self._lock:
            return {
                "origin": self._origin.get(evidence_id),
                "derivation": self._derivation.get(evidence_id),
                "derivation_chain": self.get_derivation_chain(evidence_id),
                "transformations": self.get_transformations_for_source(evidence_id),
                "aggregation_sources": self._aggregation.get(evidence_id, []),
                "citations_made": self._citation.get(evidence_id, []),
                "verifications": self._verification.get(evidence_id, []),
                "cited_by_count": len(self.get_cited_by(evidence_id)),
            }