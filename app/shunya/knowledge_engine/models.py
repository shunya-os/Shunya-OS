"""SHUNYA — Knowledge Engine canonical models (Phase L — ES-002).

Canonical knowledge data models: immutable, versioned fact records with
checksum integrity, state machine lifecycle, evidence chains, and
supporting types.

Architectural authority: ES-002 — Knowledge Engine Specification
"""

from __future__ import annotations

import uuid, hashlib, json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FactState(Enum):
    """Lifecycle states for a knowledge fact (ES-002 §6)."""
    UNKNOWN = "unknown"
    OBSERVED = "observed"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    RETIRED = "retired"
    CONFLICT = "conflict"


class KnowledgeCategory(Enum):
    """Categories of knowledge (ES-002 §14)."""
    FACT = "fact"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    POLICY = "policy"
    USER_KNOWLEDGE = "user_knowledge"
    WORKSPACE_KNOWLEDGE = "workspace_knowledge"
    ORGANIZATIONAL = "organizational"
    HISTORICAL = "historical"
    LEARNED = "learned"
    DERIVED = "derived"
    CONTEXT_SNAPSHOT = "context_snapshot"
    EVIDENCE_RECORD = "evidence_record"


class ValueType(Enum):
    """Types of fact values."""
    TEXT = "text"
    JSON = "json"
    NUMBER = "number"
    MARKDOWN = "markdown"
    BOOLEAN = "boolean"


class SourceType(Enum):
    """Sources of knowledge facts."""
    MANUAL = "manual"
    WEB_SCRAPE = "web_scrape"
    REASONING = "reasoning"
    LEARNING = "learning"
    OBSERVER = "observer"
    IMPORT = "import"


# ---------------------------------------------------------------------------
# Allowed state transitions (ES-002 §6)
# ---------------------------------------------------------------------------

_STATE_TRANSITIONS: Dict[FactState, List[FactState]] = {
    FactState.UNKNOWN: [FactState.OBSERVED],
    FactState.OBSERVED: [FactState.VERIFIED, FactState.RETIRED, FactState.CONFLICT],
    FactState.VERIFIED: [FactState.TRUSTED, FactState.CONFLICT, FactState.SUPERSEDED, FactState.RETIRED],
    FactState.TRUSTED: [FactState.SUPERSEDED, FactState.ARCHIVED, FactState.RETIRED],
    FactState.SUPERSEDED: [FactState.ARCHIVED, FactState.TRUSTED],
    FactState.CONFLICT: [FactState.TRUSTED, FactState.SUPERSEDED],
    FactState.ARCHIVED: [FactState.RETIRED],
    FactState.RETIRED: [],
}


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


@dataclass
class FactVersion:
    """A single immutable version of a knowledge fact (ES-002 §15)."""
    fact_key: str
    version: int = 1
    value: Any = None
    value_type: str = ValueType.TEXT.value
    state: str = FactState.OBSERVED.value
    confidence: float = 1.0
    evidence: str = ""
    source: str = SourceType.MANUAL.value
    created_by: str = ""
    tenant_id: Optional[int] = None
    domain: str = ""
    category: str = KnowledgeCategory.FACT.value
    checksum: str = ""
    created_at: Optional[datetime] = None
    superseded_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.valid_from is None:
            self.valid_from = self.created_at
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """Compute SHA-256 checksum of this version's content (ES-002 §15).

        Only includes immutable content fields. Mutable fields (state, confidence,
        superseded_at) are excluded so checksums remain valid across lifecycle.
        """
        raw = json.dumps({
            "fact_key": self.fact_key,
            "version": self.version,
            "value": self.value,
            "value_type": self.value_type,
            "evidence": self.evidence,
            "source": self.source,
            "created_by": self.created_by,
            "tenant_id": self.tenant_id,
            "domain": self.domain,
            "category": self.category,
            "tags": sorted(self.tags),
        }, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def verify_checksum(self) -> bool:
        """Verify the checksum of this version (ES-002 §15)."""
        return self.checksum == self._compute_checksum()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_key": self.fact_key,
            "version": self.version,
            "value": self.value,
            "value_type": self.value_type,
            "state": self.state,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "source": self.source,
            "checksum": self.checksum,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else None,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "tenant_id": self.tenant_id,
            "domain": self.domain,
            "category": self.category,
            "tags": self.tags,
        }


@dataclass
class KnowledgeInput:
    """Input contract for storing a knowledge fact (ES-002 §4)."""
    fact_key: str
    value: Any
    domain: str = ""
    category: str = KnowledgeCategory.FACT.value
    value_type: str = ValueType.TEXT.value
    confidence: float = 1.0
    evidence: str = ""
    source: str = SourceType.MANUAL.value
    created_by: str = ""
    tenant_id: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    initial_state: str = FactState.OBSERVED.value

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, self.confidence))
        if self.source == SourceType.MANUAL.value:
            self.initial_state = FactState.VERIFIED.value

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.fact_key or len(self.fact_key) > 255:
            errors.append("INVALID_FACT_KEY: must be 1-255 chars")
        if self.value is None or (isinstance(self.value, str) and not self.value.strip()):
            errors.append("EMPTY_VALUE: value cannot be empty")
        if not self.domain:
            errors.append("MISSING_DOMAIN: domain is required")
        if self.tenant_id is None or self.tenant_id <= 0:
            errors.append("MISSING_TENANT: tenant_id required")
        if self.confidence < 0.0 or self.confidence > 1.0:
            errors.append("INVALID_CONFIDENCE: must be 0.0-1.0")
        if self.valid_until and self.valid_from and self.valid_until <= self.valid_from:
            errors.append("INVALID_DATE_RANGE: valid_until must be after valid_from")
        return errors


@dataclass
class KnowledgeRetrievalResult:
    """Output contract for fact retrieval (ES-002 §5)."""
    fact_key: str
    version: int
    value: Any
    value_type: str
    confidence: float
    evidence: str
    source: str
    checksum: str
    created_by: str
    created_at: Optional[datetime] = None
    superseded_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    tenant_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_key": self.fact_key,
            "version": self.version,
            "value": self.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "source": self.source,
            "checksum": self.checksum,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "superseded_at": self.superseded_at.isoformat() if self.superseded_at else None,
            "tenant_id": self.tenant_id,
        }


@dataclass
class KnowledgeSearchResult:
    """Output contract for fact search (ES-002 §5)."""
    results: List[KnowledgeRetrievalResult] = field(default_factory=list)
    total_count: int = 0
    confidence_range: List[float] = field(default_factory=lambda: [0.0, 0.0])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "total_count": self.total_count,
            "confidence_range": self.confidence_range,
        }


@dataclass
class SourceRef:
    """A source reference in an evidence chain."""
    fact_key: str
    version: int
    evidence: str
    source: str
    confidence: float


@dataclass
class EvidenceChain:
    """Complete evidence chain for a fact (ES-002 §5)."""
    fact: KnowledgeRetrievalResult
    source_references: List[SourceRef] = field(default_factory=list)
    supporting_facts: List[KnowledgeRetrievalResult] = field(default_factory=list)
    contradicting_facts: List[KnowledgeRetrievalResult] = field(default_factory=list)
    resolution_state: str = "supported"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact": self.fact.to_dict(),
            "source_references": [
                {"fact_key": s.fact_key, "version": s.version, "evidence": s.evidence,
                 "source": s.source, "confidence": s.confidence}
                for s in self.source_references
            ],
            "supporting_facts": [f.to_dict() for f in self.supporting_facts],
            "contradicting_facts": [f.to_dict() for f in self.contradicting_facts],
            "resolution_state": self.resolution_state,
        }


@dataclass
class KnowledgeStats:
    """Knowledge engine statistics."""
    total_versions: int = 0
    facts_current: int = 0
    conflicts: int = 0
    facts_by_domain: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_versions": self.total_versions,
            "facts_current": self.facts_current,
            "conflicts": self.conflicts,
            "facts_by_domain": dict(self.facts_by_domain),
        }