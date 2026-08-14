"""SHUNYA — Execution Intelligence Engine canonical models (Phase N+2).

All data models: domain-agnostic, immutable-style dataclasses for health
assessments, timeline snapshots, dependency graphs, risk assessments,
next actions, portfolio summaries, evidence traces, and API types.

Architectural authority: ES-010 — Execution Intelligence Specification
"""

from __future__ import annotations

import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# =========================================================================
# Shared Enums
# =========================================================================

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    AT_RISK = "at_risk"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthDimension(str, Enum):
    STATE = "state"
    PROGRESS = "progress"
    TIMELINESS = "timeliness"
    RESOURCE_POSITION = "resource_position"
    EXCEPTION_BURDEN = "exception_burden"
    OBLIGATION_HEALTH = "obligation_health"
    DEPENDENCY_HEALTH = "dependency_health"


class RiskLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionPriority(Enum):
    IMMEDIATE = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFORMATIONAL = 4


# =========================================================================
# 1. Execution Health Engine
# =========================================================================

@dataclass
class HealthAssessment:
    """Complete health evaluation of a single execution instance."""
    exec_id: str
    tenant_id: int
    overall: str = HealthStatus.UNKNOWN.value
    dimensions: Dict[str, str] = field(default_factory=dict)
    scores: Dict[str, float] = field(default_factory=dict)
    evidence: Dict[str, List[str]] = field(default_factory=dict)
    assessed_at: str = ""

    def __post_init__(self) -> None:
        if not self.assessed_at:
            self.assessed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exec_id": self.exec_id,
            "tenant_id": self.tenant_id,
            "overall": self.overall,
            "dimensions": self.dimensions,
            "scores": self.scores,
            "evidence": self.evidence,
            "assessed_at": self.assessed_at,
        }


# =========================================================================
# 2. Timeline Intelligence
# =========================================================================

@dataclass
class TimelineSnapshot:
    """Snapshot of execution timeline state."""
    exec_id: str
    tenant_id: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    elapsed_seconds: float = 0.0
    remaining_seconds_estimate: Optional[float] = None
    completion_ratio: float = 0.0
    milestones_passed: List[str] = field(default_factory=list)
    milestones_remaining: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exec_id": self.exec_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "elapsed_seconds": self.elapsed_seconds,
            "remaining_seconds_estimate": self.remaining_seconds_estimate,
            "completion_ratio": self.completion_ratio,
            "milestones_passed": self.milestones_passed,
            "milestones_remaining": self.milestones_remaining,
        }


@dataclass
class CompletionPrediction:
    """Predicted completion time and confidence."""
    exec_id: str
    predicted_at: str
    confidence: float = 0.0
    optimistic_at: Optional[str] = None
    pessimistic_at: Optional[str] = None
    basis: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exec_id": self.exec_id,
            "predicted_at": self.predicted_at,
            "confidence": self.confidence,
            "optimistic_at": self.optimistic_at,
            "pessimistic_at": self.pessimistic_at,
            "basis": self.basis,
        }


# =========================================================================
# 3. Dependency Graph Engine
# =========================================================================

@dataclass
class DependencyNode:
    """A node in the execution dependency graph."""
    node_id: str
    exec_id: str
    obl_id: str
    obl_type: str
    description: str
    state: str
    in_degree: int = 0
    out_degree: int = 0
    level: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "exec_id": self.exec_id,
            "obl_id": self.obl_id,
            "obl_type": self.obl_type,
            "description": self.description,
            "state": self.state,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "level": self.level,
        }


@dataclass
class DependencyEdge:
    """A directed dependency edge between two obligation nodes."""
    from_obl_id: str
    to_obl_id: str
    exec_id: str
    is_critical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_obl_id,
            "to": self.to_obl_id,
            "exec_id": self.exec_id,
            "is_critical": self.is_critical,
        }


@dataclass
class CriticalPath:
    """The critical path through a dependency graph."""
    exec_id: str
    path: List[str] = field(default_factory=list)
    total_length: int = 0
    bottlenecks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exec_id": self.exec_id,
            "path": self.path,
            "total_length": self.total_length,
            "bottlenecks": self.bottlenecks,
        }


# =========================================================================
# 4. Risk Detection Engine
# =========================================================================

@dataclass
class RiskFactor:
    """A single identified risk factor with evidence."""
    risk_type: str
    description: str
    level: str = RiskLevel.MEDIUM.value
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_type": self.risk_type,
            "description": self.description,
            "level": self.level,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class RiskAssessment:
    """Complete risk evaluation for an execution."""
    exec_id: str
    tenant_id: int
    overall_risk: str = RiskLevel.NONE.value
    factors: List[RiskFactor] = field(default_factory=list)
    assessed_at: str = ""

    def __post_init__(self) -> None:
        if not self.assessed_at:
            self.assessed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exec_id": self.exec_id,
            "tenant_id": self.tenant_id,
            "overall_risk": self.overall_risk,
            "factors": [f.to_dict() for f in self.factors],
            "assessed_at": self.assessed_at,
        }


# =========================================================================
# 5. Next Action Engine
# =========================================================================

@dataclass
class NextAction:
    """A recommended next action with priority and evidence."""
    action_id: str = ""
    exec_id: str = ""
    tenant_id: int = 0
    action_type: str = ""
    description: str = ""
    priority: int = ActionPriority.MEDIUM.value
    depends_on: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.action_id:
            raw = f"{self.exec_id}:{self.action_type}:{datetime.now(timezone.utc).isoformat()}"
            self.action_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "exec_id": self.exec_id,
            "tenant_id": self.tenant_id,
            "action_type": self.action_type,
            "description": self.description,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "evidence": self.evidence,
            "generated_at": self.generated_at,
        }


# =========================================================================
# 6. Portfolio Intelligence
# =========================================================================

@dataclass
class PortfolioBreakdown:
    """Breakdown of executions by state across a tenant."""
    total: int = 0
    active: int = 0
    blocked: int = 0
    at_risk: int = 0
    fulfilled: int = 0
    failed: int = 0
    cancelled: int = 0
    pending: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total, "active": self.active,
            "blocked": self.blocked, "at_risk": self.at_risk,
            "fulfilled": self.fulfilled, "failed": self.failed,
            "cancelled": self.cancelled, "pending": self.pending,
        }


@dataclass
class PortfolioSummary:
    """Aggregated intelligence across all executions for a tenant."""
    tenant_id: int
    breakdown: PortfolioBreakdown = field(default_factory=PortfolioBreakdown)
    health_distribution: Dict[str, int] = field(default_factory=dict)
    overall_health: str = HealthStatus.UNKNOWN.value
    top_risks: List[RiskFactor] = field(default_factory=list)
    top_actions: List[NextAction] = field(default_factory=list)
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "breakdown": self.breakdown.to_dict(),
            "health_distribution": self.health_distribution,
            "overall_health": self.overall_health,
            "top_risks": [r.to_dict() for r in self.top_risks],
            "top_actions": [a.to_dict() for a in self.top_actions],
            "generated_at": self.generated_at,
        }


# =========================================================================
# 7. Explainability Layer
# =========================================================================

@dataclass
class EvidenceTrace:
    """A single traceable piece of evidence leading to a conclusion."""
    trace_id: str = ""
    claim: str = ""
    evidence: str = ""
    source: str = ""
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.trace_id:
            raw = f"{self.claim}:{self.evidence}:{self.source}"
            self.trace_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "claim": self.claim,
            "evidence": self.evidence,
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass
class Explanation:
    """Full explanation of an intelligence output with evidence chain."""
    topic: str
    conclusion: str = ""
    traces: List[EvidenceTrace] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "conclusion": self.conclusion,
            "traces": [t.to_dict() for t in self.traces],
            "alternatives": self.alternatives,
            "confidence": self.confidence,
        }


# =========================================================================
# 8. Runtime Types
# =========================================================================

@dataclass
class RuntimeConfig:
    """Configuration for the Execution Intelligence Engine."""
    max_critical_path_depth: int = 50
    risk_timeout_threshold_hours: float = 48.0
    health_warning_threshold: float = 0.7
    health_critical_threshold: float = 0.4
    portfolio_top_k: int = 5
    enable_explainability: bool = True
    version: str = "n+2.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_critical_path_depth": self.max_critical_path_depth,
            "risk_timeout_threshold_hours": self.risk_timeout_threshold_hours,
            "health_warning_threshold": self.health_warning_threshold,
            "health_critical_threshold": self.health_critical_threshold,
            "portfolio_top_k": self.portfolio_top_k,
            "enable_explainability": self.enable_explainability,
            "version": self.version,
        }


@dataclass
class QueryFilter:
    """Filter for querying execution intelligence."""
    tenant_id: Optional[int] = None
    exec_ids: Optional[List[str]] = None
    states: Optional[List[str]] = None
    health_statuses: Optional[List[str]] = None
    risk_levels: Optional[List[str]] = None
    limit: int = 50
    offset: int = 0
