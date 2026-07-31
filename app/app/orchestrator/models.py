"""SHUNYA — Integration & Orchestration canonical models (Milestone IV).

Pipeline context, cross-module contracts, explanation graphs,
profiling snapshots, and supporting types for system coordination.
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

class PipelineStage(str, Enum):
    BUSINESS_EVENT = "business_event"
    ENTITY_RESOLUTION = "entity_resolution"
    EXECUTION = "execution"
    EVIDENCE = "evidence"
    AWARENESS = "awareness"
    ORGANIZATION = "organization"
    LEARNING = "learning"
    PREDICTION = "prediction"
    PLANNER = "planner"
    GOVERNANCE = "governance"
    RESPONSE = "response"


class ContractSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ExplanationDepth(str, Enum):
    SUMMARY = "summary"
    STANDARD = "standard"
    DETAILED = "detailed"
    FULL = "full"


# =========================================================================
# 1. Pipeline Context
# =========================================================================

@dataclass
class ContextEntry:
    """A single entry in the pipeline context."""
    stage: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    module_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "timestamp": self.timestamp,
            "module_version": self.module_version,
        }


@dataclass
class ContextProvenance:
    """Provenance chain for context propagation."""
    entries: List[ContextEntry] = field(default_factory=list)
    current_stage: str = PipelineStage.BUSINESS_EVENT.value

    def record(self, stage: str, data: Dict[str, Any], version: str = ""):
        self.entries.append(ContextEntry(
            stage=stage, data=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            module_version=version,
        ))
        self.current_stage = stage

    def get_stage(self, stage: str) -> Optional[ContextEntry]:
        for e in reversed(self.entries):
            if e.stage == stage:
                return e
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stages": [e.to_dict() for e in self.entries],
            "current_stage": self.current_stage,
            "total_stages": len(self.entries),
        }


@dataclass
class PipelineContext:
    """Shared execution context that flows through the pipeline.

    Every subsystem enriches context without replacing prior information.
    """
    pipeline_id: str = ""
    tenant_id: int = 0

    # Identity
    execution_id: Optional[str] = None
    business_event: Dict[str, Any] = field(default_factory=dict)

    # Subsystem snapshots
    execution_state: Dict[str, Any] = field(default_factory=dict)
    evidence_state: Dict[str, Any] = field(default_factory=dict)
    awareness_state: Dict[str, Any] = field(default_factory=dict)
    organization_state: Dict[str, Any] = field(default_factory=dict)
    learning_snapshot: Dict[str, Any] = field(default_factory=dict)
    prediction_snapshot: Dict[str, Any] = field(default_factory=dict)
    planner_snapshot: Dict[str, Any] = field(default_factory=dict)
    governance_snapshot: Dict[str, Any] = field(default_factory=dict)

    # Provenance chain
    provenance: Optional[ContextProvenance] = None

    # Final output
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    unified_response: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.pipeline_id:
            raw = f"pipe:{self.tenant_id}:{datetime.now(timezone.utc).isoformat()}"
            self.pipeline_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.provenance:
            self.provenance = ContextProvenance()

    def record_stage(self, stage: str, data: Dict[str, Any],
                     version: str = ""):
        if self.provenance:
            self.provenance.record(stage, data, version)

    def add_recommendation(self, rec: Dict[str, Any]):
        self.recommendations.append(rec)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id, "tenant_id": self.tenant_id,
            "execution_id": self.execution_id,
            "recommendation_count": len(self.recommendations),
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "error_count": len(self.errors),
        }


@dataclass
class PipelineResult:
    """Final result of a pipeline execution."""
    pipeline_id: str = ""
    success: bool = True
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    governance_verdict: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    latency_seconds: float = 0.0
    stages_completed: int = 0
    explanation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id, "success": self.success,
            "recommendation_count": len(self.recommendations),
            "governance_verdict": self.governance_verdict,
            "errors": self.errors,
            "latency_seconds": round(self.latency_seconds, 4),
            "stages_completed": self.stages_completed,
        }


# =========================================================================
# 2. Cross-Module Contracts
# =========================================================================

@dataclass
class ContractSpec:
    """A single cross-module contract specification."""
    contract_id: str = ""
    source_module: str = ""
    target_module: str = ""
    rule: str = ""
    severity: str = ContractSeverity.ERROR.value
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id, "source_module": self.source_module,
            "target_module": self.target_module, "rule": self.rule,
            "severity": self.severity, "description": self.description,
        }


@dataclass
class ContractViolation:
    """A detected contract violation during validation."""
    contract_id: str = ""
    source_module: str = ""
    target_module: str = ""
    rule: str = ""
    detail: str = ""
    severity: str = ContractSeverity.ERROR.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "source_module": self.source_module,
            "target_module": self.target_module,
            "rule": self.rule, "detail": self.detail,
            "severity": self.severity,
        }


@dataclass
class ContractCatalogue:
    """Machine-readable catalogue of all cross-module contracts."""
    contracts: List[ContractSpec] = field(default_factory=list)

    def add(self, source: str, target: str, rule: str,
            severity: str = ContractSeverity.ERROR.value,
            description: str = "") -> ContractSpec:
        raw = f"{source}:{target}:{rule}"
        cid = hashlib.sha256(raw.encode()).hexdigest()[:16]
        spec = ContractSpec(
            contract_id=cid, source_module=source, target_module=target,
            rule=rule, severity=severity, description=description,
        )
        self.contracts.append(spec)
        return spec

    def to_dict(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.contracts]


# =========================================================================
# 3. Unified Explainability
# =========================================================================

@dataclass
class ExplanationNode:
    """A single node in the end-to-end explanation graph."""
    node_id: str = ""
    stage: str = ""
    label: str = ""
    claims: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id[:12], "stage": self.stage,
            "label": self.label[:60],
            "claims": self.claims[:3],
            "evidence": self.evidence[:3],
            "confidence": round(self.confidence, 4),
        }


@dataclass
class ExplanationGraph:
    """End-to-end explanation graph tracing a recommendation through
    every pipeline stage."""
    graph_id: str = ""
    pipeline_id: str = ""
    nodes: List[ExplanationNode] = field(default_factory=list)
    root_node_id: Optional[str] = None

    def add_node(self, stage: str, label: str,
                 claims: List[str], evidence: List[str],
                 confidence: float = 1.0,
                 parent_id: Optional[str] = None) -> ExplanationNode:
        raw = f"{self.pipeline_id}:{stage}:{label}:{len(self.nodes)}"
        nid = hashlib.sha256(raw.encode()).hexdigest()[:16]
        node = ExplanationNode(
            node_id=nid, stage=stage, label=label,
            claims=claims, evidence=evidence,
            confidence=confidence, parent_id=parent_id,
        )
        self.nodes.append(node)
        if parent_id is None and self.root_node_id is None:
            self.root_node_id = nid
        return node

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id[:16],
            "pipeline_id": self.pipeline_id,
            "node_count": len(self.nodes),
            "nodes": [n.to_dict() for n in self.nodes],
        }


# =========================================================================
# 4. Profiling
# =========================================================================

@dataclass
class ProfilerSnapshot:
    """A single stage timing measurement."""
    snapshot_id: str = ""
    stage: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    context_size_bytes: int = 0
    memory_estimate_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "duration_seconds": round(self.duration_seconds, 6),
            "context_size_bytes": self.context_size_bytes,
            "memory_estimate_bytes": self.memory_estimate_bytes,
        }


@dataclass
class OrchestratorConfig:
    """Configuration for the Orchestrator Engine."""
    enable_governance: bool = True
    enable_planner: bool = True
    enable_predictions: bool = True
    enable_learning: bool = True
    enable_profiling: bool = False
    max_context_bytes: int = 262144  # 256KB
    version: str = "mi4.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_governance": self.enable_governance,
            "enable_planner": self.enable_planner,
            "enable_predictions": self.enable_predictions,
            "enable_learning": self.enable_learning,
            "enable_profiling": self.enable_profiling,
            "max_context_bytes": self.max_context_bytes,
            "version": self.version,
        }
