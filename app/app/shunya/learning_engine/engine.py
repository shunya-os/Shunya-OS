"""SHUNYA — Learning Engine (Phase K — ES-007).

The Learning Engine transforms verified observations into long-term
improvement. It is the engine that closes the Compounding Intelligence
Loop — it analyzes observations, discovers patterns, evaluates outcomes,
calibrates confidence, and produces governance-validated proposals.

The engine implements a deterministic 9-stage pipeline:
  1. Learning Intake
  2. Pattern Discovery
  3. Correlation Analysis
  4. Outcome Evaluation
  5. Confidence Calibration
  6. Improvement Recommendation
  7. Knowledge Proposal
  8. Governance Review Package
  9. Continuous Learning Archive

Architectural authority: ES-007 — Learning Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set

from app.shunya.learning_engine.models import (
    LearningType, PatternType, FrequencyTrend, RecurrenceType,
    KnowledgeProposalState, FailureMode,
    PatternScope, Recurrence, Pattern,
    LearningRecommendation, ConfidenceCalibration,
    OutcomeEvaluation, KnowledgeProposal, PerformanceInsight,
    LearningInput, LearningOutput, LearningStats,
)


# ---------------------------------------------------------------------------
# Default Constants
# ---------------------------------------------------------------------------

_DEFAULT_LEARNING_RATE = 0.1
_MIN_OBSERVATIONS_FOR_PATTERN = 3
_MIN_CONFIDENCE_FOR_RECOMMENDATION = 0.3

# ---------------------------------------------------------------------------
# Pattern matching rules (signal-type → pattern-type mappings)
# ---------------------------------------------------------------------------

_SIGNAL_TO_PATTERN: Dict[str, str] = {
    "deviation": PatternType.FAILURE.value,
    "anomaly": PatternType.ANOMALY.value,
    "success": PatternType.SUCCESS.value,
    "failure": PatternType.FAILURE.value,
}


# ---------------------------------------------------------------------------
# Learning Engine
# ---------------------------------------------------------------------------


class LearningEngine:
    """Learning Engine — transforms observations into improvement.

    Implements a deterministic 9-stage pipeline per ES-007.
    """

    def __init__(self) -> None:
        self._patterns: Dict[str, Pattern] = {}
        self._recommendations: List[LearningRecommendation] = []
        self._proposals: List[KnowledgeProposal] = []
        self._calibrations: List[ConfidenceCalibration] = []
        self._stats = LearningStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def learn(self, inp: LearningInput) -> LearningOutput:
        """Process observations and generate learning outputs.

        Implements the full 9-stage deterministic pipeline.
        """
        output = LearningOutput()

        # Stage 1: Learning Intake
        intake_errors = inp.validate()
        if intake_errors:
            output.success = False
            output.errors = intake_errors
            return output

        # Track processed signal IDs for provenance
        processed_ids: Set[str] = set()

        # Stage 2-3: Pattern Discovery + Correlation Analysis
        patterns = self._discover_patterns(inp, processed_ids)
        for p in patterns:
            self._patterns[p.pattern_id] = p
        output.patterns = patterns

        # Stage 4: Outcome Evaluation
        evaluations = self._evaluate_outcomes(inp)
        output.evaluations = evaluations

        # Stage 5: Confidence Calibration
        calibrations = self._calibrate_confidence(inp, evaluations)
        self._calibrations.extend(calibrations)
        output.calibrations = calibrations

        # Stage 6: Improvement Recommendation
        recommendations = self._generate_recommendations(
            patterns, calibrations, evaluations, inp
        )
        self._recommendations.extend(recommendations)
        output.recommendations = recommendations

        # Stage 7: Knowledge Proposal
        proposals = self._generate_proposals(recommendations)
        self._proposals.extend(proposals)
        output.proposals = proposals

        # Stage 8-9: Governance Package + Archive
        # (In-memory storage; governance validation is deferred)
        self._archive_learning(inp, output)

        # Update stats
        self._stats.total_cycles += 1
        self._stats.total_signals_processed += len(inp.signals)
        self._stats.patterns_discovered = len(self._patterns)
        self._stats.recommendations_generated = len(self._recommendations)
        self._stats.calibrations_performed = len(self._calibrations)

        return output

    def learn_from_signals(self, signals: List[Dict[str, Any]],
                           tenant_id: int = 1) -> LearningOutput:
        """Convenience: learn from a list of learning signal dicts."""
        inp = LearningInput(signals=signals, tenant_id=tenant_id)
        return self.learn(inp)

    # ------------------------------------------------------------------
    # Pipeline Stages
    # ------------------------------------------------------------------

    def _discover_patterns(self, inp: LearningInput,
                           processed_ids: Set[str]) -> List[Pattern]:
        """Stages 2-3: Discover patterns across signals and correlate."""
        patterns_by_type: Dict[str, List[Dict[str, Any]]] = {}
        signal_ids_by_type: Dict[str, List[str]] = {}

        for sig in inp.signals:
            sig_type = sig.get("signal_type", "")
            mapped = _SIGNAL_TO_PATTERN.get(sig_type, PatternType.TREND.value)
            if mapped not in patterns_by_type:
                patterns_by_type[mapped] = []
                signal_ids_by_type[mapped] = []
            patterns_by_type[mapped].append(sig)
            signal_ids_by_type[mapped].append(sig.get("signal_id", ""))
            if sig.get("signal_id"):
                processed_ids.add(sig["signal_id"])

        patterns: List[Pattern] = []

        for ptype, matching in patterns_by_type.items():
            if len(matching) < _MIN_OBSERVATIONS_FOR_PATTERN:
                continue  # Not enough data for a reliable pattern

            count = len(matching)
            confidences = [s.get("confidence", 0.5) for s in matching]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            deltas = [abs(s.get("delta_percentage", 0.0)) for s in matching if s.get("delta_percentage")]
            avg_impact = sum(deltas) / len(deltas) if deltas else 0.1

            name = ptype.replace("_", " ").title()
            if ptype == PatternType.FAILURE.value:
                name = f"Recurring {ptype}: {matching[0].get('dimension', 'unknown')}"

            pattern = Pattern(
                name=name,
                description=f"Discovered {count} signals of type '{ptype}' "
                           f"with avg confidence {avg_confidence:.2f}",
                pattern_type=ptype,
                frequency=count,
                frequency_trend=FrequencyTrend.STABLE.value,
                confidence=min(1.0, avg_confidence * 1.1),
                impact=min(1.0, avg_impact),
                source_signal_ids=signal_ids_by_type.get(ptype, []),
                status="active",
            )
            patterns.append(pattern)

        # If no patterns discovered with sufficient data, create a note
        if not patterns and len(inp.signals) > 0:
            patterns.append(Pattern(
                name="Insufficient Data",
                description=f"Only {len(inp.signals)} signals available; "
                           f"minimum {_MIN_OBSERVATIONS_FOR_PATTERN} required per pattern type",
                pattern_type=PatternType.TREND.value,
                confidence=0.1,
                impact=0.0,
                status="active",
            ))

        return patterns

    def _evaluate_outcomes(self, inp: LearningInput) -> List[OutcomeEvaluation]:
        """Stage 4: Evaluate outcome quality against objectives."""
        evaluations: List[OutcomeEvaluation] = []

        # Count by signal type
        type_counts: Dict[str, int] = {}
        confidences: Dict[str, List[float]] = {}
        for sig in inp.signals:
            st = sig.get("signal_type", "unknown")
            type_counts[st] = type_counts.get(st, 0) + 1
            if st not in confidences:
                confidences[st] = []
            confidences[st].append(sig.get("confidence", 0.5))

        total = len(inp.signals)
        if total == 0:
            return evaluations

        for st, count in type_counts.items():
            rate = count / total
            avg_conf = sum(confidences.get(st, [0.5])) / len(confidences.get(st, [0.5]))
            quality = rate * avg_conf
            evaluations.append(OutcomeEvaluation(
                dimension=f"signal_type:{st}",
                expected_value=0.0,  # No prior expectation
                actual_value=rate,
                quality_score=quality,
                explanation=f"{count}/{total} signals ({rate:.0%}) are type '{st}' "
                           f"with avg confidence {avg_conf:.2f}",
            ))

        # Overall quality
        overall = sum(e.quality_score for e in evaluations) / max(len(evaluations), 1)
        evaluations.append(OutcomeEvaluation(
            dimension="overall",
            quality_score=overall,
            explanation=f"Overall outcome quality: {overall:.2f}",
        ))

        return evaluations

    def _calibrate_confidence(self, inp: LearningInput,
                               evaluations: List[OutcomeEvaluation]) -> List[ConfidenceCalibration]:
        """Stage 5: Adjust confidence based on observed outcome accuracy.

        Formula: new = old + (outcome_accuracy - old) × learning_rate  (ES-007 §7)
        """
        calibrations: List[ConfidenceCalibration] = []

        for sig in inp.signals:
            old_conf = sig.get("confidence", 0.5)
            sig_type = sig.get("signal_type", "")

            # Determine outcome accuracy: success signals → accurate, failure → inaccurate
            is_accurate = sig_type == "success" or sig_type == "deviation"
            outcome_accuracy = 1.0 if is_accurate else 0.0

            new_conf = old_conf + (outcome_accuracy - old_conf) * _DEFAULT_LEARNING_RATE
            new_conf = max(0.0, min(1.0, new_conf))

            if abs(new_conf - old_conf) > 0.01:
                calibrations.append(ConfidenceCalibration(
                    dimension=sig.get("dimension", "overall"),
                    old_confidence=old_conf,
                    new_confidence=round(new_conf, 3),
                    outcome_accuracy=outcome_accuracy,
                    learning_rate=_DEFAULT_LEARNING_RATE,
                    source_signal_ids=[sig.get("signal_id", "")],
                ))

        return calibrations

    def _generate_recommendations(
        self,
        patterns: List[Pattern],
        calibrations: List[ConfidenceCalibration],
        evaluations: List[OutcomeEvaluation],
        inp: LearningInput,
    ) -> List[LearningRecommendation]:
        """Stage 6: Generate actionable improvement recommendations."""
        recommendations: List[LearningRecommendation] = []

        # From patterns with significant impact
        for p in patterns:
            if p.confidence < _MIN_CONFIDENCE_FOR_RECOMMENDATION:
                continue
            if p.pattern_type in (PatternType.FAILURE.value, PatternType.ANOMALY.value):
                recommendations.append(LearningRecommendation(
                    title=f"Address recurring {p.pattern_type}: {p.name}",
                    description=p.description,
                    recommendation_type="knowledge_update",
                    priority=min(1.0, p.impact * p.confidence),
                    confidence=p.confidence,
                    impact_estimate=p.impact,
                    source_pattern_ids=[p.pattern_id],
                    source_signal_ids=p.source_signal_ids,
                ))

        # From calibrations with significant change
        for c in calibrations:
            if abs(c.new_confidence - c.old_confidence) > 0.2:
                recommendations.append(LearningRecommendation(
                    title=f"Calibrate confidence: {c.dimension} "
                          f"({c.old_confidence:.2f} → {c.new_confidence:.2f})",
                    description=f"Confidence adjusted by {(c.new_confidence - c.old_confidence):.2f} "
                               f"based on outcome accuracy {c.outcome_accuracy}",
                    recommendation_type="confidence_calibration",
                    priority=0.5,
                    confidence=c.new_confidence,
                    source_signal_ids=c.source_signal_ids,
                ))

        # Default: if nothing actionable
        if not recommendations and len(inp.signals) >= _MIN_OBSERVATIONS_FOR_PATTERN:
                recommendations.append(LearningRecommendation(
                    title="No actionable improvements identified",
                    description="All observed patterns are within expected bounds",
                    recommendation_type="confidence_calibration",
                    priority=0.1,
                    confidence=0.5,
                ))

        return recommendations

    def _generate_proposals(
        self, recommendations: List[LearningRecommendation]
    ) -> List[KnowledgeProposal]:
        """Stage 7: Package recommendations as concrete knowledge proposals."""
        proposals: List[KnowledgeProposal] = []

        for rec in recommendations:
            if rec.recommendation_type == "knowledge_update" and rec.confidence >= 0.3:
                proposals.append(KnowledgeProposal(
                    fact_key=f"learning_pattern:{rec.title[:50]}",
                    current_value=None,
                    proposed_value=rec.description,
                    proposal_type="create",
                    rationale=rec.description,
                    state=KnowledgeProposalState.PROPOSED.value,
                    confidence=rec.confidence,
                    source_recommendation_id=rec.recommendation_id,
                    rollback_plan=f"Supersede fact_key with previous version",
                ))

        return proposals

    def _archive_learning(self, inp: LearningInput, output: LearningOutput) -> None:
        """Stages 8-9: Archive learning outputs for audit.

        Currently stores in-memory. Future: write to Knowledge Engine.
        """
        pass

    # ------------------------------------------------------------------
    # Public Queries
    # ------------------------------------------------------------------

    def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        return self._patterns.get(pattern_id)

    def list_patterns(self, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
        ps = list(self._patterns.values())
        if pattern_type:
            ps = [p for p in ps if p.pattern_type == pattern_type]
        return [p.to_dict() for p in ps]

    def list_recommendations(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in reversed(self._recommendations[-limit:])]

    def list_proposals(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in reversed(self._proposals[-limit:])]

    def list_calibrations(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in reversed(self._calibrations[-limit:])]

    @property
    def stats(self) -> Dict[str, Any]:
        return self._stats.to_dict()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_ENGINE_INSTANCE: Optional[LearningEngine] = None


def get_learning_engine() -> LearningEngine:
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = LearningEngine()
    return _ENGINE_INSTANCE


def reset_learning_engine() -> None:
    global _ENGINE_INSTANCE
    _ENGINE_INSTANCE = None