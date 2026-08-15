"""
SHUNYA Organizational Cortex — OrganizationState

The canonical runtime aggregate representing the entire organization's state.
The highest-level runtime representation inside SHUNYA.

Continuously represents:
  Active Commitments, Blocked Commitments, Critical Risks,
  Emerging Opportunities, Organizational Health, Cross-functional Dependencies,
  Resource Contention, Waiting Decisions, Policy Violations,
  Stale Observations, Execution Backlog, Learning Signals,
  Executive Attention Queue
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.decision_runtime.models import Decision, DecisionStatus, get_store as get_decision_store
from app.decision_runtime.commitment import get_service as get_commitment_service
from app.decision_runtime.outcome import get_store as get_outcome_store
from app.decision_runtime.learning import get_store as get_learning_store
from app.intelligence.observation import get_store as get_obs_store, ObservationStatus
from app.intelligence.insight import get_compiler
from app.execution.constants import ExecState


@dataclass
class OrganizationState:
    """The canonical aggregate of the entire organization's runtime state.

    This is a snapshot — computed on demand by synthesizing all runtime modules.
    The Cortex never owns the underlying systems; it synthesizes them.
    """

    # ─── Commitments ───
    active_commitments: int = 0
    blocked_commitments: int = 0
    completed_commitments: int = 0
    failed_commitments: int = 0
    execution_backlog: int = 0

    # ─── Decisions ───
    total_decisions: int = 0
    active_decisions: int = 0
    waiting_approval: int = 0
    policy_violations: int = 0

    # ─── Risks & Opportunities ───
    critical_risks: int = 0
    emerging_opportunities: int = 0
    resource_contention: int = 0

    # ─── Observations ───
    active_observations: int = 0
    stale_observations: int = 0
    superseded_observations: int = 0

    # ─── Insights ───
    total_insights: int = 0
    high_confidence_insights: int = 0
    low_confidence_insights: int = 0

    # ─── Learning ───
    learning_signals: int = 0
    high_confidence_learning: int = 0

    # ─── Health ───
    health_scores: dict[str, float] = field(default_factory=dict)
    overall_health: float = 0.0

    # ─── Metadata ───
    synthesized_at: str = ""
    organization_name: str = ""

    def to_dict(self) -> dict:
        return {
            "commitments": {
                "active": self.active_commitments,
                "blocked": self.blocked_commitments,
                "completed": self.completed_commitments,
                "failed": self.failed_commitments,
                "backlog": self.execution_backlog,
            },
            "decisions": {
                "total": self.total_decisions,
                "active": self.active_decisions,
                "waiting_approval": self.waiting_approval,
                "policy_violations": self.policy_violations,
            },
            "risks_opportunities": {
                "critical_risks": self.critical_risks,
                "emerging_opportunities": self.emerging_opportunities,
                "resource_contention": self.resource_contention,
            },
            "observations": {
                "active": self.active_observations,
                "stale": self.stale_observations,
                "superseded": self.superseded_observations,
            },
            "insights": {
                "total": self.total_insights,
                "high_confidence": self.high_confidence_insights,
                "low_confidence": self.low_confidence_insights,
            },
            "learning": {
                "signals": self.learning_signals,
                "high_confidence": self.high_confidence_learning,
            },
            "health": {
                "scores": self.health_scores,
                "overall": self.overall_health,
            },
            "synthesized_at": self.synthesized_at,
            "organization_name": self.organization_name,
        }


class StateSynthesizer:
    """Continuously synthesizes OrganizationState from all runtime modules.

    The Cortex never owns these systems. It reads from them.
    """

    def __init__(self, org_name: str = "Organization"):
        self.org_name = org_name

    def synthesize(self) -> OrganizationState:
        """Read from all runtime modules and produce a canonical state snapshot."""
        state = OrganizationState(
            organization_name=self.org_name,
            synthesized_at=datetime.now(timezone.utc).isoformat(),
        )

        # ─── Decisions ───
        ds = get_decision_store()
        state.total_decisions = ds.count
        state.active_decisions = len(ds.get_active())
        state.waiting_approval = len([
            d for d in ds._decisions.values()
            if d.status.value == DecisionStatus.AWAITING_APPROVAL.value
        ]) if hasattr(ds, '_decisions') else 0

        # ─── Commitments ───
        cs = get_commitment_service()
        state.active_commitments = cs.count

        # ─── Observations ───
        obs = get_obs_store()
        state.active_observations = len(obs.get_active())
        state.superseded_observations = len([
            o for o in obs._observations.values()
            if o.status == ObservationStatus.SUPERSEDED
        ]) if hasattr(obs, '_observations') else 0

        # ─── Insights ───
        compiler = get_compiler()
        insights = compiler.compile_all()
        state.total_insights = len(insights)
        state.high_confidence_insights = sum(1 for i in insights if i.confidence >= 0.75)
        state.low_confidence_insights = sum(1 for i in insights if i.confidence < 0.5)

        # ─── Learning ───
        ls = get_learning_store()
        state.learning_signals = ls.count
        state.high_confidence_learning = sum(
            1 for r in ls.get_all() if r.learning_confidence >= 0.75
        ) if hasattr(ls, 'get_all') else 0

        # ─── Outcomes ───
        os = get_outcome_store()
        # Count outcomes as completed commitments
        state.completed_commitments = os.count

        # ─── Risks (approximated from low-confidence insights + critical-urgency decisions) ───
        state.critical_risks = state.low_confidence_insights
        state.emerging_opportunities = state.high_confidence_insights

        # ─── Health (computed) ───
        from app.cortex.health import compute_health
        state.health_scores = compute_health(state)
        state.overall_health = sum(state.health_scores.values()) / max(len(state.health_scores), 1)

        return state


_synthesizer: Optional[StateSynthesizer] = None


def get_synthesizer(org_name: str = "Organization") -> StateSynthesizer:
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = StateSynthesizer(org_name)
    return _synthesizer


def reset_synthesizer() -> None:
    global _synthesizer
    _synthesizer = None