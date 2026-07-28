"""SHUNYA Confidence Engine — compute, combine, and track confidence scores.

The Confidence Engine is the single source of truth for confidence
in the Intelligence Runtime. All confidence computation is deterministic
and formula-based. No AI escalation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from core.intelligence.models import EngineInput, EngineOutput

# Default weights for confidence computation
DEFAULT_WEIGHTS = {
    "source_reliability": 0.25,
    "evidence_strength": 0.30,
    "consistency": 0.20,
    "recency": 0.10,
    "certainty": 0.15,
}


@dataclass
class ConfidenceFactor:
    """A single factor in a confidence computation."""

    name: str
    value: float
    weight: float
    source: str = ""


@dataclass
class ConfidenceScore:
    """A complete confidence score with breakdown."""

    score_id: str = ""
    overall: float = 0.0
    factors: list[ConfidenceFactor] = field(default_factory=list)
    subject_id: str = ""
    subject_type: str = ""
    computation_method: str = "weighted_average"

    def __post_init__(self):
        if not self.score_id:
            from core.kernel.types import generate_uuid7
            self.score_id = generate_uuid7()


class ConfidenceEngine:
    """Compute, combine, and track confidence scores.

    All confidence computation is deterministic and formula-based.
    Never escalates to AI.
    """

    def __init__(self, weights: dict[str, float] | None = None):
        self.engine_id = "confidence_engine"
        self.engine_type = "confidence"
        self._weights = weights or DEFAULT_WEIGHTS.copy()
        self._history: list[ConfidenceScore] = []

    # ── Public Interface ─────────────────────────────────────────────

    def process(self, input_data: EngineInput) -> EngineOutput:
        """Compute confidence from input factors.

        Args:
            input_data: payload should contain:
                - factors: list of {name, value, weight?, source?}
                - subject_id: optional
                - subject_type: optional

        Returns:
            EngineOutput with computed confidence score.
        """
        t0 = time.time()
        payload = input_data.payload
        raw_factors = payload.get("factors", [])
        subject_id = payload.get("subject_id", "")
        subject_type = payload.get("subject_type", "")

        factors = []
        for f in raw_factors:
            name = f.get("name", "unknown")
            value = float(f.get("value", 0.5))
            weight = float(f.get("weight", self._weights.get(name, 0.2)))
            source = f.get("source", "")
            factors.append(ConfidenceFactor(
                name=name, value=value, weight=weight, source=source,
            ))

        score = self.compute(factors, subject_id, subject_type)
        self._history.append(score)

        return EngineOutput(
            output_type="confidence_score",
            payload={
                "score_id": score.score_id,
                "overall": score.overall,
                "factors": [
                    {"name": f.name, "value": f.value, "weight": f.weight}
                    for f in score.factors
                ],
                "subject_id": score.subject_id,
                "computation_method": score.computation_method,
            },
            confidence=score.overall,
            confidence_factors={f.name: f.value for f in score.factors},
            deterministic=True,
            trace_id=input_data.trace_id,
            processing_time_ms=(time.time() - t0) * 1000,
        )

    def escalate(self, input_data: EngineInput) -> Any:
        """Confidence Engine never escalates. All computation is deterministic."""
        return self.process(input_data)

    def get_capabilities(self) -> list[str]:
        return [
            "weighted_average", "min_confidence", "max_confidence",
            "bayesian_combination", "confidence_tracking",
        ]

    def health_check(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "status": "active",
            "total_scores": len(self._history),
            "weights": self._weights,
        }

    # ── Confidence Computation ───────────────────────────────────────

    def compute(
        self,
        factors: list[ConfidenceFactor],
        subject_id: str = "",
        subject_type: str = "",
        method: str = "weighted_average",
    ) -> ConfidenceScore:
        """Compute a confidence score from factors.

        Args:
            factors: List of confidence factors with values and weights.
            subject_id: Optional subject identifier.
            subject_type: Optional subject type.
            method: Computation method (weighted_average, min, max, bayesian).

        Returns:
            ConfidenceScore with overall score and breakdown.
        """
        if not factors:
            return ConfidenceScore(
                overall=0.5, subject_id=subject_id, subject_type=subject_type,
            )

        if method == "min":
            overall = min(f.value for f in factors)
        elif method == "max":
            overall = max(f.value for f in factors)
        elif method == "bayesian":
            overall = self._bayesian_combination(factors)
        else:  # weighted_average
            overall = self._weighted_average(factors)

        return ConfidenceScore(
            overall=round(overall, 4),
            factors=factors,
            subject_id=subject_id,
            subject_type=subject_type,
            computation_method=method,
        )

    def _weighted_average(self, factors: list[ConfidenceFactor]) -> float:
        """Compute weighted average of confidence factors."""
        total_weight = sum(f.weight for f in factors)
        if total_weight == 0:
            return 0.5
        weighted = sum(f.value * f.weight for f in factors)
        return weighted / total_weight

    def _bayesian_combination(self, factors: list[ConfidenceFactor]) -> float:
        """Combine multiple confidence estimates using Bayesian-like averaging.

        Treats each factor as an independent estimate and combines them.
        """
        if not factors:
            return 0.5
        # Prior: 0.5 with weight of 1
        prior = 0.5
        prior_weight = 1.0
        numerator = prior * prior_weight
        denominator = prior_weight
        for f in factors:
            numerator += f.value * f.weight
            denominator += f.weight
        return numerator / denominator

    def combine(
        self,
        scores: list[ConfidenceScore],
        method: str = "weighted_average",
    ) -> ConfidenceScore:
        """Combine multiple confidence scores into one."""
        if not scores:
            return ConfidenceScore()
        factors = []
        for s in scores:
            factors.append(ConfidenceFactor(
                name=s.subject_type or "combined",
                value=s.overall,
                weight=1.0 / len(scores),
                source=s.subject_id,
            ))
        return self.compute(factors, method=method)

    # ── Utility ──────────────────────────────────────────────────────

    def label(self, confidence: float) -> str:
        """Convert a confidence score to a human-readable label."""
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "moderate"
        elif confidence >= 0.3:
            return "low"
        return "very_low"

    def get_history(self, limit: int = 10) -> list[ConfidenceScore]:
        return self._history[-limit:]

    def clear(self) -> None:
        self._history.clear()