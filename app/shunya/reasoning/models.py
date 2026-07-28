"""SHUNYA — Reasoning Engine Foundation models (Phase F — Canonical).

Canonical reasoning models: immutable representations of reasoning
findings, contradictions, assumptions, constraints, confidence scores,
and evidence provenance. Every reasoning object retains provenance back
to Context Fusion, Identity Engine, and Knowledge Store.

Architectural authority: G5.7 — Canonical Phase F Architecture Decision

Deprecated aliases (maintained for one phase cycle):
  Observation -> Finding (finding_type="observation")
  Gap -> Finding (finding_type="gap")
  Risk -> Finding (finding_type="risk")
  Conflict -> Contradiction
  ConflictSeverity -> ContradictionSeverity
  ConfidenceAssessment -> ConfidenceScore
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FindingType(Enum):
    """Classification of a single finding."""
    OBSERVATION = "observation"
    GAP = "gap"
    RISK = "risk"


class FindingSeverity(Enum):
    """Unified severity for all finding types."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    BLOCKING = "blocking"
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class ContradictionType(Enum):
    """Type of contradiction detected."""
    FACT_CONFLICT = "fact_conflict"
    ASSUMPTION_CONFLICT = "assumption_conflict"
    STALE_CONTEXT = "stale_context"
    INCOMPLETE_EVIDENCE = "incomplete_evidence"
    DUPLICATE_FINDING = "duplicate_finding"


class ContradictionSeverity(Enum):
    """Severity of a detected contradiction."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ConfidenceLevel(Enum):
    """Confidence classification."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    INSUFFICIENT = "insufficient"


# --- Deprecated severity aliases (one cycle) ---
ObservationType = FindingType  # Observation subsumed into Finding
ConflictSeverity = ContradictionSeverity
GapSeverity = FindingSeverity
RiskSeverity = FindingSeverity


# ---------------------------------------------------------------------------
# Evidence Reference
# ---------------------------------------------------------------------------


@dataclass
class EvidenceReference:
    """A link from a reasoning conclusion back to a source.

    Every conclusion is explainable via its evidence references.
    References may point to:
      - A KnowledgeObject (via object_id and key)
      - An Identity (via identity_id)
      - A WorkspaceContext (via context_id)
      - An external source (via source_uri)
    """

    reference_type: str = "knowledge"
    source_name: str = ""
    source_uri: str = ""
    object_id: str = ""
    object_key: str = ""
    namespace: str = ""
    identity_id: str = ""
    context_id: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_knowledge_object(
        cls, object_id: str, key: str, namespace: str = "",
        confidence: float = 1.0, source_name: str = "knowledge_store",
    ) -> "EvidenceReference":
        return cls(reference_type="knowledge", source_name=source_name,
                    object_id=object_id, object_key=key, namespace=namespace,
                    confidence=confidence)

    @classmethod
    def from_identity(cls, identity_id: str, source_name: str = "identity_engine",
                      confidence: float = 1.0) -> "EvidenceReference":
        return cls(reference_type="identity", source_name=source_name,
                    identity_id=identity_id, confidence=confidence)

    @classmethod
    def from_context(cls, context_id: str, source_name: str = "context_fusion_engine",
                     confidence: float = 1.0) -> "EvidenceReference":
        return cls(reference_type="context", source_name=source_name,
                    context_id=context_id, confidence=confidence)

    @classmethod
    def from_external(cls, source_name: str, source_uri: str,
                      confidence: float = 1.0) -> "EvidenceReference":
        return cls(reference_type="external", source_name=source_name,
                    source_uri=source_uri, confidence=confidence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_type": self.reference_type,
            "source_name": self.source_name,
            "source_uri": self.source_uri,
            "object_id": self.object_id,
            "object_key": self.object_key,
            "namespace": self.namespace,
            "identity_id": self.identity_id,
            "context_id": self.context_id,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """A single finding — what is true, missing, or risky.

    The `finding_type` field discriminates:
      - "observation": what is true
      - "gap": what is missing
      - "risk": what is risky

    Every finding carries provenance back to evidence references.
    """

    finding_id: str = ""
    finding_type: str = FindingType.OBSERVATION.value
    severity: str = FindingSeverity.INFO.value
    fact_key: str = ""
    fact_value: Any = None
    label: str = ""
    description: str = ""
    source: str = ""
    confidence: float = 1.0
    evidence: List[EvidenceReference] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.finding_id:
            self.finding_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_type": self.finding_type,
            "severity": self.severity,
            "fact_key": self.fact_key,
            "fact_value": str(self.fact_value) if self.fact_value is not None else None,
            "label": self.label,
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Contradiction
# ---------------------------------------------------------------------------


@dataclass
class Contradiction:
    """A detected contradiction — conflicting facts, stale context, etc.

    Detection only. No automatic resolution.

    Contradiction types:
      - fact_conflict: two or more facts contradict each other
      - assumption_conflict: mutually exclusive assumptions
      - stale_context: context data is stale
      - incomplete_evidence: evidence set is incomplete
      - duplicate_finding: duplicate or redundant findings
    """

    contradiction_id: str = ""
    contradiction_type: str = ContradictionType.FACT_CONFLICT.value
    severity: str = ContradictionSeverity.MEDIUM.value
    label: str = ""
    description: str = ""
    fact_keys: List[str] = field(default_factory=list)
    fact_values: List[Any] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    finding_ids: List[str] = field(default_factory=list)
    resolution_guidance: str = ""
    rule_name: str = ""
    evidence: List[EvidenceReference] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.contradiction_id:
            self.contradiction_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id,
            "contradiction_type": self.contradiction_type,
            "severity": self.severity,
            "label": self.label,
            "description": self.description,
            "fact_keys": self.fact_keys,
            "fact_values": [str(v) if v is not None else None for v in self.fact_values],
            "sources": self.sources,
            "finding_ids": self.finding_ids,
            "resolution_guidance": self.resolution_guidance,
            "rule_name": self.rule_name,
            "evidence": [e.to_dict() for e in self.evidence],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Assumption
# ---------------------------------------------------------------------------


@dataclass
class Assumption:
    """A documented assumption made during reasoning.

    Assumptions are explicit and traceable facts that were presumed
    true in the absence of direct evidence.
    """

    assumption_id: str = ""
    fact_key: str = ""
    label: str = ""
    description: str = ""
    assumed_value: Any = None
    evidence: List[EvidenceReference] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.assumption_id:
            self.assumption_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assumption_id": self.assumption_id,
            "fact_key": self.fact_key,
            "label": self.label,
            "description": self.description,
            "assumed_value": str(self.assumed_value) if self.assumed_value is not None else None,
            "evidence": [e.to_dict() for e in self.evidence],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Constraint
# ---------------------------------------------------------------------------


@dataclass
class Constraint:
    """A documented constraint identified during reasoning.

    Constraints represent boundaries, limitations, or invariants
    that must be respected by downstream engines.
    """

    constraint_id: str = ""
    fact_key: str = ""
    constraint_type: str = ""
    label: str = ""
    description: str = ""
    value: Any = None
    evidence: List[EvidenceReference] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.constraint_id:
            self.constraint_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "fact_key": self.fact_key,
            "constraint_type": self.constraint_type,
            "label": self.label,
            "description": self.description,
            "value": str(self.value) if self.value is not None else None,
            "evidence": [e.to_dict() for e in self.evidence],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Confidence Score
# ---------------------------------------------------------------------------


@dataclass
class ConfidenceScore:
    """Deterministic confidence scoring.

    Confidence is computed from five dimensions:
      - Completeness: What fraction of required facts are present
      - Consistency: How consistent the facts are (no contradictions)
      - Freshness: How recent the facts are
      - Corroboration: How many independent sources confirm each fact
      - ProvenanceQuality: How reliable the sources are

    No AI-derived confidence. No statistical inference.
    All scores are deterministic given the same inputs.
    """

    overall_score: float = 0.0
    level: str = ConfidenceLevel.INSUFFICIENT.value
    completeness_score: float = 0.0
    consistency_score: float = 1.0
    freshness_score: float = 1.0
    corroboration_score: float = 0.0
    provenance_quality_score: float = 0.0
    total_findings: int = 0
    total_contradictions: int = 0
    total_assumptions: int = 0
    total_constraints: int = 0
    required_facts_present: int = 0
    required_facts_total: int = 0
    evidence: List[EvidenceReference] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def compute_level(cls, score: float) -> str:
        if score >= 0.90:
            return ConfidenceLevel.VERY_HIGH.value
        if score >= 0.70:
            return ConfidenceLevel.HIGH.value
        if score >= 0.50:
            return ConfidenceLevel.MEDIUM.value
        if score >= 0.30:
            return ConfidenceLevel.LOW.value
        if score >= 0.0:
            return ConfidenceLevel.VERY_LOW.value
        return ConfidenceLevel.INSUFFICIENT.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 4),
            "level": self.level,
            "completeness_score": round(self.completeness_score, 4),
            "consistency_score": round(self.consistency_score, 4),
            "freshness_score": round(self.freshness_score, 4),
            "corroboration_score": round(self.corroboration_score, 4),
            "provenance_quality_score": round(self.provenance_quality_score, 4),
            "total_findings": self.total_findings,
            "total_contradictions": self.total_contradictions,
            "total_assumptions": self.total_assumptions,
            "total_constraints": self.total_constraints,
            "required_facts_present": self.required_facts_present,
            "required_facts_total": self.required_facts_total,
        }


# ---------------------------------------------------------------------------
# Reasoning Metadata
# ---------------------------------------------------------------------------


@dataclass
class ReasoningMetadata:
    """Provenance and metadata for a reasoning result."""

    reasoning_id: str = ""
    reasoning_engine_version: str = "1.0.0"
    context_id: str = ""
    correlation_id: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_ms: float = 0.0
    rules_executed: int = 0
    rules_passed: int = 0
    rules_failed: int = 0
    engine_name: str = "reasoning_engine"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.reasoning_id:
            self.reasoning_id = str(uuid.uuid4())
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        if self.completed_at is None:
            self.completed_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning_id": self.reasoning_id,
            "reasoning_engine_version": self.reasoning_engine_version,
            "context_id": self.context_id,
            "correlation_id": self.correlation_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "rules_executed": self.rules_executed,
            "rules_passed": self.rules_passed,
            "rules_failed": self.rules_failed,
            "engine_name": self.engine_name,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Reasoning Result
# ---------------------------------------------------------------------------


@dataclass
class ReasoningResult:
    """The canonical output of the Reasoning Engine.

    Immutable once constructed. Composed of:
      - findings: What is true, missing, and risky
      - contradictions: What is conflicting
      - assumptions: Explicit assumptions
      - constraints: Identified boundaries
      - attention_items: What requires attention
      - confidence: Deterministic confidence score
      - metadata: Provenance back to Context Fusion and Knowledge Store

    Backward-compatible computed properties:
      - .observations -> findings with finding_type="observation"
      - .gaps -> findings with finding_type="gap"
      - .risks -> findings with finding_type="risk"
      - .has_conflicts -> bool(len(contradictions) > 0)
    """

    result_id: str = ""
    findings: List[Finding] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    attention_items: List[str] = field(default_factory=list)
    confidence: Optional[ConfidenceScore] = None
    metadata: Optional[ReasoningMetadata] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.result_id:
            self.result_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    @property
    def observations(self) -> List[Finding]:
        return [f for f in self.findings if f.finding_type == FindingType.OBSERVATION.value]

    @property
    def gaps(self) -> List[Finding]:
        return [f for f in self.findings if f.finding_type == FindingType.GAP.value]

    @property
    def risks(self) -> List[Finding]:
        return [f for f in self.findings if f.finding_type == FindingType.RISK.value]

    @property
    def has_conflicts(self) -> bool:
        return len(self.contradictions) > 0

    @property
    def has_contradictions(self) -> bool:
        return len(self.contradictions) > 0

    @property
    def has_gaps(self) -> bool:
        return any(f.finding_type == FindingType.GAP.value for f in self.findings)

    @property
    def has_risks(self) -> bool:
        return any(f.finding_type == FindingType.RISK.value for f in self.findings)

    @property
    def is_healthy(self) -> bool:
        if self.confidence is None:
            return False
        if any(c.severity == ContradictionSeverity.CRITICAL.value for c in self.contradictions):
            return False
        if any(f.severity == FindingSeverity.BLOCKING.value for f in self.findings
               if f.finding_type == FindingType.GAP.value):
            return False
        if self.confidence.level in (ConfidenceLevel.LOW.value,
                                     ConfidenceLevel.VERY_LOW.value,
                                     ConfidenceLevel.INSUFFICIENT.value):
            return False
        return True

    @property
    def requires_attention(self) -> bool:
        return len(self.attention_items) > 0 or self.has_contradictions or self.has_risks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "findings": [f.to_dict() for f in self.findings],
            "contradictions": [c.to_dict() for c in self.contradictions],
            "assumptions": [a.to_dict() for a in self.assumptions],
            "constraints": [c.to_dict() for c in self.constraints],
            "attention_items": self.attention_items,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_contradictions": self.has_contradictions,
            "has_gaps": self.has_gaps,
            "has_risks": self.has_risks,
            "is_healthy": self.is_healthy,
            "requires_attention": self.requires_attention,
        }


# ---------------------------------------------------------------------------
# Deprecated aliases (one phase cycle)
# ---------------------------------------------------------------------------

# Backward-compatible aliases so existing imports continue to work.
# New code MUST use Finding, Contradiction, ConfidenceScore directly.

Observation = Finding
Gap = Finding
Risk = Finding
Conflict = Contradiction
ConfidenceAssessment = ConfidenceScore