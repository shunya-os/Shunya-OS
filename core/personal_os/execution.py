"""Universal Execution — every recommendation is executable.

Orchestrates execution across UCPs and providers.
Does not duplicate provider capabilities.
"""

from __future__ import annotations
from typing import Any
from core.personal_os.models import AttentionSignal, ExecutableRecommendation, LivingContextSnapshot


class ExecutionOrchestrator:
    """Orchestrates execution — communication, generation, scheduling, etc."""

    def formulate(self, context: LivingContextSnapshot,
                  signals: list[AttentionSignal]) -> list[ExecutableRecommendation]:
        recs: list[ExecutableRecommendation] = []

        for s in signals:
            rec = ExecutableRecommendation(
                title=s.recommendation,
                description=s.description,
                reasoning=f"Attention signal from {s.source_ucp}: {s.signal_type}",
                evidence=[{"type": "attention_signal", "signal_type": s.signal_type,
                           "priority": s.priority}],
                confidence=0.7,
                assumptions=["All UCPs are operational"],
                uncertainty=["Execution may require human approval"],
                alternatives=[{"title": "Defer", "impact": "No action taken now"}],
                expected_impact=f"Resolved {s.signal_type} issue",
                execution_type="approve" if not s.can_automate else "automate",
                can_execute=s.can_automate,
            )
            recs.append(rec)

        return recs

    def execute(self, rec: ExecutableRecommendation,
                runtimes: dict[str, Any]) -> dict[str, Any]:
        if not rec.can_execute:
            return {"executed": False, "reason": "Requires human approval"}
        rec.executed = True
        return {"executed": True, "recommendation": rec.title}