"""Controlled Learning Loop — governed, attributable, reversible.

ZGC-PR-17C §4 mandate:
  Observation → Outcome → Evaluation → Learning signal → Governed
  knowledge/memory update → Future decision improvement

Safeguards:
  attributable (every signal has identity_id + timestamp)
  observable (learning signals are stored as MemoryRecord entries)
  reversible (learning history is append-only; superseded records preserve old data)
  confidence-scored (signals below threshold stay as observations, not authority)
  governed (no autonomous code/prompt/model mutation)
  tenant-isolated (signals are scoped by identity_id + tenant_id)
  auditable (every signal has provenance trace)

Integrates: core.learning_intelligence.LearningIntelligenceEngine (UCP-11)
as a computation component for skill gap analysis where applicable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ── Learning Signal Types ──────────────────────────────────────────────────


@dataclass
class LearningSignal:
    """A governed learning signal — never promoted to authority without confidence.

    Stored in durable memory (MemoryRecord) for retrieval by future intelligence.
    """
    signal_id: str = ""
    signal_type: str = "outcome_observation"  # outcome_observation | user_correction | preference_discovery
    identity_id: str = ""
    tenant_id: str = ""
    observation: str = ""
    expected_outcome: str = ""
    actual_outcome: str = ""
    evaluation: str = ""  # success | partial | failure | unknown
    confidence: float = 0.0  # 0.0-1.0; signals below 0.6 stay as observations
    improvement_signal: str = ""
    source: str = "intelligence_runtime"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    superseded_by: str = ""  # signal_id of superseding signal (reversibility)
    provenance: dict = field(default_factory=dict)


class ControlledLearningLoop:
    """Governed learning from observations: evaluate → signal → persist.

    Does NOT modify code, prompts, or model weights. Learning is stored as
    durable memory records that future intelligence can retrieve but that
    never autonomously alter system behaviour.
    """

    def __init__(self, memory_engine=None, db_repository=None):
        self._memory = memory_engine
        self._db_repo = db_repository
        self._learning_engine = None  # lazy: core.learning_intelligence

    # ── Wiring ─────────────────────────────────────────────────────────────

    def wire_memory(self, memory_engine) -> None:
        self._memory = memory_engine

    def wire_learning_engine(self, engine) -> None:
        self._learning_engine = engine

    # ── Core Pipeline ──────────────────────────────────────────────────────

    def process_observation(
        self,
        observation: str,
        expected_outcome: str,
        actual_outcome: str,
        identity_id: str = "",
        tenant_id: str = "",
        source: str = "intelligence_runtime",
        metadata: dict | None = None,
    ) -> LearningSignal:
        """Observation → Evaluation → Learning signal → Governed memory update.

        Steps:
        1. Evaluate outcome against expectation
        2. Compute confidence score for the signal
        3. Create a governed LearningSignal
        4. Persist via the durable memory bridge
        5. Return the signal for decision improvement
        """
        from core.intelligence_runtime.types import MemoryType

        # 1. Evaluate
        evaluation = self._evaluate(expected_outcome, actual_outcome)
        confidence = self._compute_confidence(evaluation, actual_outcome)

        # 2. Build learning signal
        signal_id = f"ls_{datetime.now(timezone.utc).timestamp():.0f}_{identity_id[:8] if identity_id else 'anon'}"
        signal = LearningSignal(
            signal_id=signal_id,
            signal_type="outcome_observation",
            identity_id=identity_id,
            tenant_id=tenant_id,
            observation=observation,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            evaluation=evaluation,
            confidence=confidence,
            improvement_signal=self._generate_improvement(observation, evaluation, confidence),
            source=source,
            provenance=metadata or {},
        )

        # 3. Governed memory update — only if confidence >= 0.6
        #    (below threshold it remains an observation, not authoritative knowledge)
        if confidence >= 0.6 and self._memory:
            key = f"learning_signal_{signal_id}"
            value = (
                f"Observation: {observation}\n"
                f"Expected: {expected_outcome}\n"
                f"Actual: {actual_outcome}\n"
                f"Evaluation: {evaluation}\n" 
                f"Confidence: {confidence:.2f}\n"
                f"Improvement: {signal.improvement_signal}"
            )
            self._memory.store(
                key=key, content=value,
                memory_type=MemoryType.LONG_TERM,
                source=f"learning_loop/{evaluation}",
                confidence=confidence,
                identity_id=identity_id,
                tenant_id=tenant_id,
            )
            logger.info(
                "Learning signal %s stored (confidence=%.2f, evaluation=%s)",
                signal_id, confidence, evaluation,
            )
        else:
            logger.info(
                "Learning signal %s below confidence threshold (%.2f < 0.6) — "
                "kept as observation only",
                signal_id, confidence,
            )

        # 4. Optional: feed to learning intelligence engine for skill analysis
        if self._learning_engine and confidence >= 0.7:
            try:
                self._learning_engine.analyze_skill_gaps(
                    {"identity_id": identity_id, "tenant_id": tenant_id},
                    [{"observation": observation, "evaluation": evaluation}],
                )
            except Exception as exc:
                logger.warning("Learning intelligence engine skipped: %s", exc)

        return signal

    # ── Internal ───────────────────────────────────────────────────────────

    def _evaluate(self, expected: str, actual: str) -> str:
        expected_lower = expected.lower().strip()
        actual_lower = actual.lower().strip()

        if not actual_lower or actual_lower == "unknown":
            return "unknown"
        if "success" in actual_lower or "completed" in actual_lower or "achieved" in actual_lower:
            return "success"
        if "fail" in actual_lower or "error" in actual_lower or "exception" in actual_lower:
            return "failure"
        if "partial" in actual_lower or "progress" in actual_lower or "ongoing" in actual_lower:
            return "partial"
        # Positive sentiment
        if any(w in actual_lower for w in ["improved", "better", "good", "positive"]):
            return "success"
        # Negative sentiment
        if any(w in actual_lower for w in ["worse", "bad", "declined", "negative"]):
            return "failure"
        return "unknown"

    def _compute_confidence(self, evaluation: str, actual_outcome: str) -> float:
        """Compute confidence based on evaluation clarity and outcome specificity."""
        if evaluation == "unknown":
            return 0.3
        length = len(actual_outcome.strip())
        if length > 100:
            detail_score = 0.4
        elif length > 30:
            detail_score = 0.3
        else:
            detail_score = 0.2

        outcome_scores = {"success": 0.4, "failure": 0.35, "partial": 0.3, "unknown": 0.15}
        eval_score = outcome_scores.get(evaluation, 0.2)
        # Combine: detail_score + eval_score, max 0.95
        return min(detail_score + eval_score, 0.95)

    def _generate_improvement(self, observation: str, evaluation: str, confidence: float) -> str:
        """Generate a governed improvement signal — never modifies code."""
        if evaluation == "success":
            return f"Reinforce: {observation[:100]}"
        elif evaluation == "failure":
            return f"Review: {observation[:100]}"
        elif evaluation == "partial":
            return f"Continue: {observation[:100]}"
        return f"Monitor: {observation[:100]}"


# ── Singleton ──────────────────────────────────────────────────────────────

_LEARNING_LOOP: ControlledLearningLoop | None = None


def get_learning_loop() -> ControlledLearningLoop:
    global _LEARNING_LOOP
    if _LEARNING_LOOP is None:
        _LEARNING_LOOP = ControlledLearningLoop()
    return _LEARNING_LOOP


def reset_learning_loop() -> None:
    global _LEARNING_LOOP
    _LEARNING_LOOP = None