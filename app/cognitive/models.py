"""SHUNYA — Cognitive Validation canonical models (Milestone VA).

All entities are derived intelligence — never canonical state.
No entity is stored in execution, awareness, or organizational modules.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================================================
# Enums
# =========================================================================

class ReasoningStage(str, Enum):
    BUSINESS_EVENT = "business_event"
    EXECUTION = "execution"
    EVIDENCE = "evidence"
    AWARENESS = "awareness"
    ORGANIZATION = "organization"
    LEARNING = "learning"
    PREDICTION = "prediction"
    DECISION = "decision"
    GOVERNANCE = "governance"
    RECOMMENDATION = "recommendation"


class ContradictionSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ConsistencyStatus(str, Enum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    UNVERIFIABLE = "unverifiable"


# =========================================================================
# 1. Reasoning Graph
# =========================================================================

@dataclass
class ReasoningNode:
    """A single node in the reasoning trace chain."""
    node_id: str = ""
    stage: str = ""
    label: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    parent_id: Optional[str] = None
    module_version: str = ""
    input_fingerprint: str = ""
    output_fingerprint: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.node_id:
            raw = f"rn:{self.stage}:{self.label}:{datetime.now(timezone.utc).isoformat()}"
            self.node_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id[:12], "stage": self.stage,
            "label": self.label[:60], "confidence": round(self.confidence, 4),
            "parent_id": self.parent_id[:12] if self.parent_id else None,
            "evidence": self.evidence[:3],
            "module_version": self.module_version,
            "timestamp": self.timestamp,
        }


@dataclass
class ReasoningGraph:
    """Complete reasoning trace from business event to final recommendation."""
    graph_id: str = ""
    pipeline_id: str = ""
    tenant_id: int = 0
    nodes: List[ReasoningNode] = field(default_factory=list)
    root_node_id: Optional[str] = None
    leaf_node_id: Optional[str] = None
    confidence_chain: Optional[ConfidenceChain] = None
    provenance: Optional[ReasoningProvenance] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.graph_id:
            raw = f"cg:{self.pipeline_id}:{datetime.now(timezone.utc).isoformat()}"
            self.graph_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def add_node(self, stage: str, label: str, data: Dict[str, Any] = None,
                 evidence: List[str] = None, confidence: float = 1.0,
                 module_version: str = "", parent_id: Optional[str] = None
                 ) -> ReasoningNode:
        raw = f"{self.graph_id}:{stage}:{label}:{len(self.nodes)}"
        nid = hashlib.sha256(raw.encode()).hexdigest()[:16]
        inp_fp = hashlib.sha256(str(data).encode()).hexdigest()
        out_fp = hashlib.sha256(str(data).encode()).hexdigest()
        node = ReasoningNode(
            node_id=nid, stage=stage, label=label,
            data=data or {}, evidence=evidence or [],
            confidence=confidence, parent_id=parent_id or self.root_node_id,
            module_version=module_version,
            input_fingerprint=inp_fp, output_fingerprint=out_fp,
        )
        self.nodes.append(node)
        if self.root_node_id is None:
            self.root_node_id = node.node_id
        self.leaf_node_id = node.node_id
        return node

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "pipeline_id": self.pipeline_id,
            "node_count": len(self.nodes),
            "nodes": [n.to_dict() for n in self.nodes],
            "confidence_chain": self.confidence_chain.to_dict() if self.confidence_chain else None,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "created_at": self.created_at,
        }


# =========================================================================
# 2. Confidence Propagation
# =========================================================================

@dataclass
class ConfidenceStage:
    """Confidence at a single stage of the reasoning pipeline."""
    stage: str = ""
    input_confidence: float = 0.0
    output_confidence: float = 0.0
    degradation_reason: str = ""
    transformation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "input_confidence": round(self.input_confidence, 4),
            "output_confidence": round(self.output_confidence, 4),
            "degradation": round(self.output_confidence - self.input_confidence, 4),
            "degradation_reason": self.degradation_reason,
        }


@dataclass
class ConfidenceChain:
    """Confidence propagation through the complete reasoning pipeline."""
    chain_id: str = ""
    stages: List[ConfidenceStage] = field(default_factory=list)
    initial_confidence: float = 1.0
    final_confidence: float = 0.0

    def add_stage(self, stage: str, input_conf: float, output_conf: float,
                  reason: str = "", transformation: str = "") -> ConfidenceStage:
        cs = ConfidenceStage(stage=stage, input_confidence=input_conf,
                             output_confidence=output_conf,
                             degradation_reason=reason,
                             transformation=transformation)
        self.stages.append(cs)
        self.final_confidence = output_conf
        return cs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_confidence": round(self.initial_confidence, 4),
            "final_confidence": round(self.final_confidence, 4),
            "total_degradation": round(self.final_confidence - self.initial_confidence, 4),
            "stages": [s.to_dict() for s in self.stages],
        }


# =========================================================================
# 3. Reasoning Replay
# =========================================================================

@dataclass
class ReplayInput:
    """Input snapshot for deterministic reasoning replay."""
    execution_snapshot: Dict[str, Any] = field(default_factory=dict)
    evidence_snapshot: Dict[str, Any] = field(default_factory=dict)
    learning_snapshot: Dict[str, Any] = field(default_factory=dict)
    prediction_snapshot: Dict[str, Any] = field(default_factory=dict)
    decision_snapshot: Dict[str, Any] = field(default_factory=dict)
    governance_snapshot: Dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        raw = str(self.execution_snapshot) + str(self.evidence_snapshot) + \
              str(self.learning_snapshot) + str(self.prediction_snapshot) + \
              str(self.decision_snapshot) + str(self.governance_snapshot)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class ReplayDiagnostic:
    """Structured diagnostic for replay verification."""
    check: str = ""
    passed: bool = True
    expected: str = ""
    actual: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check": self.check, "passed": self.passed,
            "expected": self.expected[:80], "actual": self.actual[:80],
            "detail": self.detail[:120],
        }


@dataclass
class ReplayResult:
    """Result of a deterministic replay."""
    replay_id: str = ""
    original_graph_id: str = ""
    input_fingerprint: str = ""
    output_fingerprint: str = ""
    identical: bool = True
    diagnostics: List[ReplayDiagnostic] = field(default_factory=list)
    stages_replayed: int = 0
    original_output: Dict[str, Any] = field(default_factory=dict)
    replayed_output: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.replay_id:
            raw = f"rp:{self.input_fingerprint}:{datetime.now(timezone.utc).isoformat()}"
            self.replay_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replay_id": self.replay_id, "identical": self.identical,
            "stages_replayed": self.stages_replayed,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "created_at": self.created_at,
        }


# =========================================================================
# 4. Consistency Validation
# =========================================================================

@dataclass
class ConsistencyCheck:
    """A single consistency check result."""
    check_id: str = ""
    check_name: str = ""
    source: str = ""
    target: str = ""
    status: str = ConsistencyStatus.CONSISTENT.value
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id[:12], "check_name": self.check_name,
            "source": self.source, "target": self.target,
            "status": self.status, "detail": self.detail[:80],
        }


@dataclass
class ConsistencyResult:
    """Result of running all consistency checks on a reasoning graph."""
    result_id: str = ""
    graph_id: str = ""
    checks: List[ConsistencyCheck] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    unverifiable: int = 0
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.result_id:
            raw = f"cr:{self.graph_id}:{datetime.now(timezone.utc).isoformat()}"
            self.result_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id[:12], "graph_id": self.graph_id[:12],
            "checks": len(self.checks),
            "passed": self.passed, "failed": self.failed,
            "unverifiable": self.unverifiable,
        }


# =========================================================================
# 5. Contradiction Detection
# =========================================================================

@dataclass
class Contradiction:
    """A detected contradiction between reasoning stages."""
    contradiction_id: str = ""
    source_stage: str = ""
    target_stage: str = ""
    severity: str = ContradictionSeverity.WARNING.value
    description: str = ""
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id[:12],
            "source_stage": self.source_stage,
            "target_stage": self.target_stage,
            "severity": self.severity,
            "description": self.description[:80],
            "evidence": self.evidence[:3],
        }


@dataclass
class ContradictionReport:
    """Complete report of all contradictions in a reasoning graph."""
    report_id: str = ""
    graph_id: str = ""
    contradictions: List[Contradiction] = field(default_factory=list)
    total: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.report_id:
            raw = f"con:{self.graph_id}:{datetime.now(timezone.utc).isoformat()}"
            self.report_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id[:12], "graph_id": self.graph_id[:12],
            "contradictions": len(self.contradictions),
            "errors": self.errors, "warnings": self.warnings, "infos": self.infos,
        }


# =========================================================================
# 6. Reasoning Provenance
# =========================================================================

@dataclass
class ReasoningProvenance:
    """Immutable provenance for a reasoning graph."""
    architecture_version: str = "1.0"
    engine_versions: Dict[str, str] = field(default_factory=dict)
    input_fingerprints: Dict[str, str] = field(default_factory=dict)
    output_fingerprints: Dict[str, str] = field(default_factory=dict)
    module_versions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture_version": self.architecture_version,
            "engine_versions": self.engine_versions,
            "module_versions": self.module_versions,
        }


@dataclass
class ProvenanceSnapshot:
    """A single immutable provenance snapshot."""
    snapshot_id: str = ""
    graph_id: str = ""
    provenance: Optional[ReasoningProvenance] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            raw = f"ps:{self.graph_id}:{datetime.now(timezone.utc).isoformat()}"
            self.snapshot_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id[:12],
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }


# =========================================================================
# 7. Audit API Types
# =========================================================================

@dataclass
class AuditQuery:
    """Query for the audit API."""
    graph_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    tenant_id: Optional[int] = None
    stage: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class AuditResult:
    """Result of an audit API query."""
    graphs: List[ReasoningGraph] = field(default_factory=list)
    total: int = 0
    query: Optional[AuditQuery] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "returned": len(self.graphs),
            "graphs": [g.to_dict() for g in self.graphs[:5]],
        }


# =========================================================================
# 8. Runtime Types
# =========================================================================

@dataclass
class TraceConfig:
    """Configuration for cognitive validation."""
    max_trace_nodes: int = 100
    enable_contradiction_detection: bool = True
    enable_consistency_validation: bool = True
    enable_replay_verification: bool = True
    version: str = "miva.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_trace_nodes": self.max_trace_nodes,
            "enable_contradiction_detection": self.enable_contradiction_detection,
            "enable_consistency_validation": self.enable_consistency_validation,
            "enable_replay_verification": self.enable_replay_verification,
            "version": self.version,
        }


@dataclass
class CognitiveStats:
    """Cognitive Validation statistics."""
    total_graphs: int = 0
    total_replays: int = 0
    total_contradictions: int = 0
    total_consistency_checks: int = 0
    consistent_pct: float = 0.0
    replay_identical_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_graphs": self.total_graphs,
            "total_replays": self.total_replays,
            "total_contradictions": self.total_contradictions,
            "total_consistency_checks": self.total_consistency_checks,
            "consistent_pct": round(self.consistent_pct, 1),
            "replay_identical_pct": round(self.replay_identical_pct, 1),
        }