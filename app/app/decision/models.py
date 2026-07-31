"""SHUNYA — Decision Intelligence canonical models (Milestone V).

All decision entities are derived intelligence — never canonical state.
No Decision entity is stored in execution, awareness, or organizational modules.
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

class OptionCategory(str, Enum):
    PROCEED = "proceed"
    DELAY = "delay"
    ESCALATE = "escalate"
    DELEGATE = "delegate"
    REQUEST_APPROVAL = "request_approval"
    ACQUIRE_RESOURCES = "acquire_resources"
    SPLIT_EXECUTION = "split_execution"
    REVISE_COMMITMENT = "revise_commitment"
    RE_PLAN = "re_plan"
    MARK_INFEASIBLE = "mark_infeasible"


class ConstraintSeverity(str, Enum):
    FATAL = "fatal"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RecommendationStatus(str, Enum):
    RECOMMENDED = "recommended"
    ALTERNATIVE = "alternative"
    FEASIBLE = "feasible"
    INFEAISBLE = "infeasible"


# =========================================================================
# 1. Decision Context
# =========================================================================

@dataclass
class DecisionContext:
    """Complete context for a decision evaluation."""
    context_id: str = ""
    tenant_id: int = 0
    execution_id: str = ""
    trigger: str = ""                 # blocked, delayed, risk, manual, periodic
    execution_state: Dict[str, Any] = field(default_factory=dict)
    awareness_state: Dict[str, Any] = field(default_factory=dict)
    organization_state: Dict[str, Any] = field(default_factory=dict)
    learning_snapshot: Dict[str, Any] = field(default_factory=dict)
    prediction_snapshot: Dict[str, Any] = field(default_factory=dict)
    governance_state: Dict[str, Any] = field(default_factory=dict)
    planner_state: Dict[str, Any] = field(default_factory=dict)
    evidences: List[str] = field(default_factory=list)
    objectives: List[DecisionObjective] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.context_id:
            raw = f"dc:{self.tenant_id}:{self.execution_id}:{datetime.now(timezone.utc).isoformat()}"
            self.context_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id, "tenant_id": self.tenant_id,
            "execution_id": self.execution_id, "trigger": self.trigger,
            "evidences": len(self.evidences),
            "objectives": [o.to_dict() for o in self.objectives],
        }


# =========================================================================
# 2. Decision Option
# =========================================================================

@dataclass
class DecisionOption:
    """A single feasible course of action."""
    option_id: str = ""
    category: str = OptionCategory.PROCEED.value
    label: str = ""
    description: str = ""
    rationale: str = ""
    constraints: List[DecisionConstraint] = field(default_factory=list)
    tradeoffs: List[DecisionTradeoff] = field(default_factory=list)
    overall_score: float = 0.0
    status: str = RecommendationStatus.FEASIBLE.value

    def __post_init__(self) -> None:
        if not self.option_id and self.label:
            raw = f"opt:{self.category}:{self.label}"
            self.option_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        elif not self.option_id:
            self.option_id = hashlib.sha256(
                f"opt:{self.category}:{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id, "category": self.category,
            "label": self.label[:40], "description": self.description[:60],
            "constraint_count": len(self.constraints),
            "tradeoff_count": len(self.tradeoffs),
            "overall_score": round(self.overall_score, 4),
            "status": self.status,
        }


# =========================================================================
# 3. Decision Constraint
# =========================================================================

@dataclass
class DecisionConstraint:
    """A constraint applied to a decision option."""
    constraint_id: str = ""
    name: str = ""
    description: str = ""
    severity: str = ConstraintSeverity.INFO.value
    violated: bool = False
    detail: str = ""
    source: str = ""                  # governance, policy, resource, deadline, ownership

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id[:12],
            "name": self.name, "severity": self.severity,
            "violated": self.violated, "detail": self.detail,
            "source": self.source,
        }


# =========================================================================
# 4. Decision Objective
# =========================================================================

@dataclass
class DecisionObjective:
    """A weighted objective for decision evaluation."""
    objective_id: str = ""
    name: str = ""
    description: str = ""
    weight: float = 1.0
    direction: str = "maximize"       # or minimize
    current_score: float = 0.0
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_id": self.objective_id[:12], "name": self.name,
            "weight": self.weight, "direction": self.direction,
            "current_score": round(self.current_score, 4),
        }


@dataclass
class ObjectiveWeight:
    """Named weight for a single objective."""
    name: str = ""
    weight: float = 1.0
    direction: str = "maximize"


# =========================================================================
# 5. Decision Trade-off
# =========================================================================

@dataclass
class DecisionTradeoff:
    """A single trade-off dimension for an option."""
    dimension: str = ""               # benefit, cost, risk, impact, timeline, resource, opportunity
    score: float = 0.0                # normalized 0..1
    evidence: List[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": round(self.score, 4),
            "evidence": self.evidence[:3],
            "detail": self.detail[:80],
        }


# =========================================================================
# 6. Decision Evaluation
# =========================================================================

@dataclass
class DecisionEvaluation:
    """Full evaluation of all options against objectives and constraints."""
    evaluation_id: str = ""
    context_id: str = ""
    tenant_id: int = 0
    options: List[DecisionOption] = field(default_factory=list)
    objectives: List[DecisionObjective] = field(default_factory=list)
    constraints_applied: List[str] = field(default_factory=list)
    recommendation: Optional[DecisionRecommendation] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.evaluation_id:
            raw = f"de:{self.tenant_id}:{self.context_id}:{datetime.now(timezone.utc).isoformat()}"
            self.evaluation_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "option_count": len(self.options),
            "objective_count": len(self.objectives),
            "constraints_applied": len(self.constraints_applied),
            "recommendation": self.recommendation.to_dict() if self.recommendation else None,
            "created_at": self.created_at,
        }


# =========================================================================
# 7. Decision Recommendation
# =========================================================================

@dataclass
class DecisionRecommendation:
    """The final recommendation — never a single "correct" answer.

    Presents ranked options with transparent trade-offs.
    """
    recommendation_id: str = ""
    evaluation_id: str = ""
    ranked_options: List[DecisionOption] = field(default_factory=list)
    rejected_options: List[DecisionOption] = field(default_factory=list)
    top_option_id: Optional[str] = None
    rationale: str = ""
    remaining_uncertainty: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.recommendation_id:
            raw = f"rec:{self.evaluation_id}:{datetime.now(timezone.utc).isoformat()}"
            self.recommendation_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "top_option": self.top_option_id[:12] if self.top_option_id else None,
            "options_ranked": len(self.ranked_options),
            "options_rejected": len(self.rejected_options),
            "rationale": self.rationale[:120],
            "remaining_uncertainty": self.remaining_uncertainty[:3],
        }


# =========================================================================
# 8. Decision Explanation
# =========================================================================

@dataclass
class DecisionExplanation:
    """Complete explanation for a decision recommendation."""
    recommendation_id: str = ""
    available_options: List[Dict[str, Any]] = field(default_factory=list)
    rejected_options: List[Dict[str, Any]] = field(default_factory=list)
    ranking_rationale: str = ""
    tradeoffs: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    predictions_used: List[str] = field(default_factory=list)
    learning_artifacts: List[str] = field(default_factory=list)
    governance_considerations: List[str] = field(default_factory=list)
    remaining_uncertainty: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available_options": self.available_options,
            "rejected_options": self.rejected_options,
            "ranking_rationale": self.ranking_rationale[:200],
            "tradeoff_count": len(self.tradeoffs),
            "constraint_count": len(self.constraints),
            "predictions_used": self.predictions_used[:5],
            "remaining_uncertainty": self.remaining_uncertainty[:3],
        }


# =========================================================================
# 9. Decision Snapshot (for provenance)
# =========================================================================

@dataclass
class DecisionSnapshot:
    """Immutable provenance snapshot of a decision evaluation."""
    snapshot_id: str = ""
    evaluation_id: str = ""
    engine_version: str = "mi5.0"
    architecture_version: str = "1.0"
    input_fingerprint: str = ""
    output_fingerprint: str = ""
    objective_set: List[str] = field(default_factory=list)
    constraint_set: List[str] = field(default_factory=list)
    evidence_snapshot: List[str] = field(default_factory=list)
    learning_snapshot: List[str] = field(default_factory=list)
    prediction_snapshot: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            raw = f"snap:{self.evaluation_id}:{datetime.now(timezone.utc).isoformat()}"
            self.snapshot_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "engine_version": self.engine_version,
            "objective_set": self.objective_set,
            "constraint_set": self.constraint_set,
            "created_at": self.created_at,
        }


# =========================================================================
# 10. Scenario Evaluation
# =========================================================================

@dataclass
class ScenarioEvalResult:
    """Result of evaluating a decision option under multiple scenarios."""
    option_id: str = ""
    option_label: str = ""
    current_reality: Dict[str, Any] = field(default_factory=dict)
    best_case: Dict[str, Any] = field(default_factory=dict)
    worst_case: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    consensus_score: float = 0.0
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id[:12],
            "option_label": self.option_label[:40],
            "current_reality_score": self.current_reality.get("score", 0),
            "best_case_score": self.best_case.get("score", 0),
            "worst_case_score": self.worst_case.get("score", 0),
            "consensus_score": round(self.consensus_score, 4),
        }


# =========================================================================
# 11. Option Generation Rule
# =========================================================================

@dataclass
class OptionGenerationRule:
    """A declarative rule for generating decision options."""
    rule_id: str = ""
    trigger_states: List[str] = field(default_factory=list)
    generate: str = OptionCategory.PROCEED.value
    condition: str = ""
    priority: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id[:12], "trigger_states": self.trigger_states,
            "generates": self.generate, "condition": self.condition[:40],
            "priority": self.priority,
        }


# =========================================================================
# 12. Runtime Types
# =========================================================================

@dataclass
class DecisionConfig:
    """Configuration for Decision Intelligence."""
    default_objectives: List[ObjectiveWeight] = field(default_factory=lambda: [
        ObjectiveWeight("completion_probability", 0.25, "maximize"),
        ObjectiveWeight("delay_minimization", 0.20, "minimize"),
        ObjectiveWeight("cost_efficiency", 0.15, "maximize"),
        ObjectiveWeight("risk_reduction", 0.20, "minimize"),
        ObjectiveWeight("resource_efficiency", 0.20, "maximize"),
    ])
    enable_scenario_evaluation: bool = True
    min_options_for_ranking: int = 1
    max_options_generated: int = 10
    version: str = "mi5.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_count": len(self.default_objectives),
            "enable_scenario_evaluation": self.enable_scenario_evaluation,
            "max_options_generated": self.max_options_generated,
            "version": self.version,
        }


@dataclass
class DecisionFilter:
    """Filter for querying decision history."""
    tenant_id: Optional[int] = None
    limit: int = 50


@dataclass
class DecisionStats:
    """Decision Intelligence statistics."""
    total_evaluations: int = 0
    total_options_generated: int = 0
    total_recommendations: int = 0
    avg_options_per_evaluation: float = 0.0
    avg_latency_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evaluations": self.total_evaluations,
            "total_options_generated": self.total_options_generated,
            "total_recommendations": self.total_recommendations,
            "avg_options_per_evaluation": round(self.avg_options_per_evaluation, 2),
            "avg_latency_seconds": round(self.avg_latency_seconds, 4),
        }
