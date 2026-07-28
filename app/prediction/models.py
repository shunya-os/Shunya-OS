"""SHUNYA — Prediction & Simulation canonical models (Milestone III).

All prediction artifacts: prediction records, simulation results, 
confidence decomposition, scenario comparisons, audit trail entries,
and supporting types.

Architectural authority: Prediction Philosophy v1.0
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


# =========================================================================
# Enums
# =========================================================================

class PredictionCategory(str, Enum):
    COMPLETION = "completion"
    DELAY = "delay"
    WORKLOAD = "workload"
    CAPACITY = "capacity"
    BOTTLENECK = "bottleneck"
    DEPENDENCY = "dependency"
    ORG_IMPACT = "organizational_impact"
    OPPORTUNITY = "opportunity"
    RECOMMENDATION_OUTCOME = "recommendation_outcome"


class SimulationType(str, Enum):
    WHAT_IF = "what_if"
    COUNTERFACTUAL = "counterfactual"
    SCENARIO_BRANCH = "scenario_branch"
    COMPARISON = "comparison"


class PredictionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class ConfidenceFactorName(str, Enum):
    SAMPLE_SIZE = "sample_size"
    CONSISTENCY = "consistency"
    FRESHNESS = "freshness"
    EVIDENCE_QUALITY = "evidence_quality"
    TEMPORAL_PROXIMITY = "temporal_proximity"


# =========================================================================
# 1. Prediction Core
# =========================================================================

@dataclass
class ConfidenceFactor:
    """A single factor in the confidence decomposition."""
    name: str = ""
    value: float = 0.0
    weight: float = 0.0
    contribution: float = 0.0
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.name, "value": round(self.value, 4),
            "weight": self.weight, "contribution": round(self.contribution, 4),
            "detail": self.detail,
        }


@dataclass
class ConfidenceDecomposition:
    """Full 5-factor confidence decomposition."""
    overall: float = 0.0
    factors: List[ConfidenceFactor] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": round(self.overall, 4),
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass
class EvidenceTrace:
    """A single evidence trace for a prediction."""
    source: str = ""
    claim: str = ""
    evidence: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source, "claim": self.claim,
            "evidence": self.evidence, "confidence": round(self.confidence, 4),
        }


@dataclass
class Assumption:
    """An explicit assumption made by a prediction."""
    description: str = ""
    impact: str = ""
    probability: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"description": self.description, "impact": self.impact,
                "probability": round(self.probability, 4)}


@dataclass
class Uncertainty:
    """A known uncertainty affecting the prediction."""
    factor: str = ""
    impact: str = ""
    direction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor, "impact": self.impact,
            "direction": self.direction,
        }


@dataclass
class PredictionParameters:
    """Parameters that define the prediction."""
    category: str = ""
    entity_type: str = ""            # execution, portfolio, organization
    entity_id: str = ""
    tenant_id: int = 0
    horizon_hours: float = 72.0
    max_horizon_hours: float = 720.0
    min_confidence_threshold: float = 0.20
    impact_level: str = "informational"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category, "entity_type": self.entity_type,
            "entity_id": self.entity_id, "tenant_id": self.tenant_id,
            "horizon_hours": self.horizon_hours,
            "max_horizon_hours": self.max_horizon_hours,
            "min_confidence_threshold": self.min_confidence_threshold,
            "impact_level": self.impact_level,
        }


@dataclass
class PredictionRecord:
    """Complete prediction record with full provenance."""
    prediction_id: str = ""
    params: Optional[PredictionParameters] = None
    status: str = PredictionStatus.ACTIVE.value

    # Prediction output
    output: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[ConfidenceDecomposition] = None

    # Provenance
    engine_version: str = "mi3.0"
    architecture_version: str = "1.0"
    input_fingerprint: str = ""
    output_fingerprint: str = ""

    # Evidence
    evidence_traces: List[EvidenceTrace] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    uncertainties: List[Uncertainty] = field(default_factory=list)

    # Lifecycle
    created_at: str = ""
    valid_until: str = ""
    superseded_by: Optional[str] = None
    withdrawn_reason: Optional[str] = None
    version: int = 1

    def __post_init__(self) -> None:
        now = datetime.now(timezone.utc)
        if not self.prediction_id and self.params:
            raw = f"{self.params.tenant_id}:{self.params.category}:{self.params.entity_id}:{now.isoformat()}"
            self.prediction_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = now.isoformat()
        if not self.valid_until and self.params:
            horizon = now + timedelta(hours=self.params.horizon_hours)
            self.valid_until = horizon.isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "params": self.params.to_dict() if self.params else {},
            "status": self.status,
            "output": self.output,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "engine_version": self.engine_version,
            "input_fingerprint": self.input_fingerprint[:16],
            "output_fingerprint": self.output_fingerprint[:16],
            "evidence_traces": [t.to_dict() for t in self.evidence_traces],
            "assumptions": [a.to_dict() for a in self.assumptions],
            "uncertainties": [u.to_dict() for u in self.uncertainties],
            "created_at": self.created_at,
            "valid_until": self.valid_until,
            "superseded_by": self.superseded_by,
            "version": self.version,
        }


# =========================================================================
# 2. Prediction Explainability
# =========================================================================

@dataclass
class PredictionExplanation:
    """Structured explanation for a prediction."""
    prediction_id: str = ""
    type: str = ""
    conclusion: str = ""
    why: str = ""
    evidence_traces: List[EvidenceTrace] = field(default_factory=list)
    historical_patterns: List[str] = field(default_factory=list)
    learning_artifacts: List[str] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    uncertainties: List[Uncertainty] = field(default_factory=list)
    confidence_decomposition: Optional[ConfidenceDecomposition] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id, "type": self.type,
            "conclusion": self.conclusion, "why": self.why,
            "evidence_traces": [t.to_dict() for t in self.evidence_traces],
            "historical_patterns": self.historical_patterns,
            "learning_artifacts": self.learning_artifacts,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "uncertainties": [u.to_dict() for u in self.uncertainties],
            "confidence_decomposition": self.confidence_decomposition.to_dict()
            if self.confidence_decomposition else None,
        }


@dataclass
class PredictionRefusal:
    """Structured refusal when a prediction cannot be made."""
    refused: bool = True
    reason: str = ""
    detail: str = ""
    available_samples: int = 0
    minimum_required: int = 3
    confidence_if_computed: Optional[float] = None
    threshold: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "refused": True, "reason": self.reason,
            "detail": self.detail,
            "available_samples": self.available_samples,
            "minimum_required": self.minimum_required,
            "confidence_if_computed": round(self.confidence_if_computed, 4)
            if self.confidence_if_computed is not None else None,
            "threshold": self.threshold,
        }


# =========================================================================
# 3. Simulation
# =========================================================================

@dataclass
class SimulationFork:
    """A forked copy of execution state for simulation."""
    fork_id: str = ""
    tenant_id: int = 0
    label: str = ""
    modified_exec_ids: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.fork_id:
            raw = f"fork:{self.tenant_id}:{self.label}:{datetime.now(timezone.utc).isoformat()}"
            self.fork_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fork_id": self.fork_id, "tenant_id": self.tenant_id,
            "label": self.label,
            "modified_exec_ids": self.modified_exec_ids,
            "created_at": self.created_at,
        }


@dataclass
class SimulationInput:
    """Input to a simulation."""
    simulation_type: str = SimulationType.WHAT_IF.value
    tenant_id: int = 0
    label: str = ""
    modifications: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # modifications = {exec_id: {field: value, ...}, ...}
    query_exec_ids: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class ScenarioBranch:
    """A single branch in a scenario comparison."""
    branch_id: str = ""
    label: str = ""
    modifications: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    predictions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_id": self.branch_id, "label": self.label,
            "predictions": self.predictions,
            "created_at": self.created_at,
        }


@dataclass
class SimulationResult:
    """Result of a simulation run."""
    simulation_id: str = ""
    simulation_type: str = SimulationType.WHAT_IF.value
    tenant_id: int = 0
    label: str = ""
    forks: List[SimulationFork] = field(default_factory=list)
    predictions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    execution_count: int = 0
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.simulation_id:
            raw = f"sim:{self.tenant_id}:{self.label}:{datetime.now(timezone.utc).isoformat()}"
            self.simulation_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "simulation_type": self.simulation_type,
            "tenant_id": self.tenant_id, "label": self.label,
            "fork_count": len(self.forks),
            "predictions": {k: v for k, v in list(self.predictions.items())[:10]},
            "execution_count": self.execution_count,
            "created_at": self.created_at,
        }


@dataclass
class ScenarioComparison:
    """Comparison of multiple scenario branches."""
    comparison_id: str = ""
    tenant_id: int = 0
    branches: List[ScenarioBranch] = field(default_factory=list)
    rankings: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.comparison_id:
            raw = f"comp:{self.tenant_id}:{datetime.now(timezone.utc).isoformat()}"
            self.comparison_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "tenant_id": self.tenant_id,
            "branch_count": len(self.branches),
            "rankings": self.rankings,
            "created_at": self.created_at,
        }


# =========================================================================
# 4. Audit
# =========================================================================

@dataclass
class PredictionAuditEntry:
    """Immutable audit entry for a prediction lifecycle event."""
    entry_id: str = ""
    prediction_id: str = ""
    event: str = ""                  # created, revised, expired, superseded, withdrawn
    timestamp: str = ""
    snapshot: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.entry_id:
            raw = f"{self.prediction_id}:{self.event}:{self.timestamp or datetime.now(timezone.utc).isoformat()}"
            self.entry_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id, "prediction_id": self.prediction_id,
            "event": self.event, "timestamp": self.timestamp,
            "snapshot": self.snapshot, "reason": self.reason,
        }


# =========================================================================
# 5. Runtime Types
# =========================================================================

@dataclass
class PredictionConfig:
    """Configuration for the Prediction & Simulation Engine."""
    freshness_hours: float = 24.0
    max_horizon_hours: float = 720.0
    min_samples_for_prediction: int = 3
    calibration_threshold: float = 0.20
    learning_rate: float = 0.10
    max_simulation_runtime_ms: int = 5000
    prediction_memory_size: int = 500
    version: str = "mi3.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "freshness_hours": self.freshness_hours,
            "max_horizon_hours": self.max_horizon_hours,
            "min_samples_for_prediction": self.min_samples_for_prediction,
            "calibration_threshold": self.calibration_threshold,
            "learning_rate": self.learning_rate,
            "max_simulation_runtime_ms": self.max_simulation_runtime_ms,
            "prediction_memory_size": self.prediction_memory_size,
            "version": self.version,
        }


@dataclass
class PredictionFilter:
    """Filter for querying prediction history."""
    tenant_id: Optional[int] = None
    categories: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    entity_ids: Optional[List[str]] = None
    limit: int = 50
    offset: int = 0


@dataclass
class PredictionStats:
    """Prediction engine statistics."""
    total_predictions: int = 0
    active_predictions: int = 0
    expired_predictions: int = 0
    superseded_predictions: int = 0
    withdrawn_predictions: int = 0
    total_simulations: int = 0
    audit_log_size: int = 0
    predictions_by_category: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_predictions": self.total_predictions,
            "active_predictions": self.active_predictions,
            "expired_predictions": self.expired_predictions,
            "superseded_predictions": self.superseded_predictions,
            "withdrawn_predictions": self.withdrawn_predictions,
            "total_simulations": self.total_simulations,
            "audit_log_size": self.audit_log_size,
            "predictions_by_category": self.predictions_by_category,
        }
