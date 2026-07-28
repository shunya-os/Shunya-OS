"""
SHUNYA — Reflection Engine

Evaluates outcomes of decisions and actions: compares actual vs expected,
detects anomalies, computes success scores, generates improvement signals,
and routes signals to the Learning Engine.

The Reflection Engine is the Evaluator layer of the Cognitive OS. It answers
"how well did we do?" and "what can we improve?" entirely through deterministic
computation. AI-assisted escalation is available for open-ended textual analysis
when confidence is below threshold.

Deterministic work:
    - Outcome vs expected comparison
    - Success score computation (weighted dimensions)
    - Anomaly detection (threshold-based)
    - Improvement signal categorization

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §10 (Reflection Engine)
    - docs/canon/07_ai_canon.md §11 (Evaluator Engine)
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from core.intelligence.models import (
    EngineInput,
    EngineOutput,
    EscalationResult,
)
from core.intelligence.reflection.models import (
    DEFAULT_ANOMALY_THRESHOLDS,
    DEFAULT_REFLECTION_WEIGHTS,
    Anomaly,
    AnomalySeverity,
    ImprovementSignal,
    ImprovementSignalCategory,
    OutcomeComparison,
    ReflectionRecord,
    SuccessScoreComponents,
)

logger = logging.getLogger(__name__)


# ── IntelligenceEngine ABC ──────────────────────────────────────────────────────


class IntelligenceEngine(ABC):
    """Abstract base class for all Intelligence Engines in SHUNYA.

    Every engine in the Intelligence Runtime implements this interface,
    providing deterministic processing with optional AI-assisted escalation
    when confidence falls below the configured threshold.
    """

    engine_id: str
    engine_type: str

    @abstractmethod
    async def process(self, input: EngineInput) -> EngineOutput:
        """Process an input and return output.

        Always deterministic unless escalation is triggered, in which
        case process() calls escalate() to bridge to an external AI.
        """

    @abstractmethod
    def escalate(self, input: EngineInput) -> EscalationResult:
        """Bridge to external AI inference.

        Called when deterministic computation yields confidence below
        the engine's configured threshold. Returns the data structure
        that would be sent to an AI provider.
        """

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return list of capability strings describing this engine."""

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Return engine health status."""


# ── ReflectionEngine ────────────────────────────────────────────────────────────


class ReflectionEngine(IntelligenceEngine):
    """Evaluates outcomes of decisions and actions through reflection.

    The Reflection Engine compares actual outcomes against expected
    outcomes, detects anomalies via threshold-based detection, computes
    success scores from weighted dimension evaluations, generates
    categorized improvement signals, and routes them to the Learning Engine.

    Integration points:
        - core/timeline/ for historical outcome data
        - core/evidence/ for outcome evidence
        - core/intelligence/learning/ for improvement signals

    Example::

        engine = ReflectionEngine()

        # Reflect on a decision outcome
        result = await engine.process(EngineInput(
            input_type="reflect",
            payload={
                "subject_id": "decision_abc_123",
                "subject_type": "decision",
                "subject_label": "Approve vendor payment",
                "expected_outcome": {
                    "cost": 50000,
                    "timing": "on_time",
                    "quality": "high",
                },
                "actual_outcome": {
                    "cost": 52000,
                    "timing": "on_time",
                    "quality": "medium",
                },
            },
        ))
        # result.payload contains comparisons, anomalies, success_score, signals
    """

    # ── Engine identity ──────────────────────────────────────────────────────

    engine_id: str = "reflection_engine"
    engine_type: str = "reflection"
    _DEFAULT_CONFIDENCE_THRESHOLD: float = 0.60

    # ── Constructor ──────────────────────────────────────────────────────────

    def __init__(self) -> None:
        """Initialize an empty Reflection Engine."""
        self._reflections: dict[str, ReflectionRecord] = {}
        self._timeline_engine: Any = None  # Optional TimelineEngine reference
        self._evidence_engine: Any = None  # Optional EvidenceEngine reference
        self._anomaly_thresholds: dict[str, float] = dict(DEFAULT_ANOMALY_THRESHOLDS)
        self._dimension_weights: dict[str, float] = dict(DEFAULT_REFLECTION_WEIGHTS)

    # ── Configuration ─────────────────────────────────────────────────────────

    def set_timeline_engine(self, timeline_engine: Any) -> None:
        """Set the Timeline Engine for historical data retrieval.

        Args:
            timeline_engine: A TimelineEngine instance from core.timeline.
        """
        self._timeline_engine = timeline_engine

    def set_evidence_engine(self, evidence_engine: Any) -> None:
        """Set the Evidence Engine for outcome evidence retrieval.

        Args:
            evidence_engine: An EvidenceEngine instance from core.evidence.
        """
        self._evidence_engine = evidence_engine

    def set_dimension_weights(self, weights: dict[str, float]) -> None:
        """Override the default dimension weights for success scoring.

        Args:
            weights: Dict mapping dimension name to weight. Must sum to ~1.0.

        Raises:
            ValueError: If weights is empty or contains invalid values.
        """
        if not weights:
            raise ValueError("Dimension weights cannot be empty")

        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(
                "Dimension weights sum to %.4f (expected ~1.0)", total
            )

        for dim, weight in weights.items():
            if weight < 0.0 or weight > 1.0:
                raise ValueError(
                    f"Weight for {dim!r} must be in [0, 1], got {weight}"
                )

        self._dimension_weights = dict(weights)
        logger.info(
            "Dimension weights updated: %s (total=%.4f)", weights, sum(weights.values())
        )

    def set_anomaly_thresholds(self, thresholds: dict[str, float]) -> None:
        """Override the default anomaly detection thresholds.

        Args:
            thresholds: Dict mapping severity level to deviation threshold.
                Must include all four levels: 'info', 'warning', 'error', 'critical'.
        """
        required = {"info", "warning", "error", "critical"}
        if not required.issubset(thresholds.keys()):
            raise ValueError(
                f"Thresholds must include all severity levels: {required}. "
                f"Got: {set(thresholds.keys())}"
            )
        self._anomaly_thresholds = dict(thresholds)
        logger.info("Anomaly thresholds updated: %s", thresholds)

    # ── IntelligenceEngine interface ──────────────────────────────────────────

    async def process(self, input: EngineInput) -> EngineOutput:
        """Process a reflection-related input.

        Supported input types:
            - 'reflect': Perform full reflection on an outcome.
            - 'compare_outcomes': Compare expected vs actual outcomes.
            - 'detect_anomalies': Detect anomalies in comparison results.
            - 'compute_success_score': Compute success score from comparisons.
            - 'generate_signals': Generate improvement signals from reflection.
            - 'get_reflection': Retrieve a reflection record.
            - 'list_reflections': List reflections filtered by criteria.

        Args:
            input: Structured input with type and payload.

        Returns:
            EngineOutput containing the result of processing.

        Raises:
            ValueError: If input_type is unknown or payload is invalid.
        """
        start_time = time.time()
        input_type = input.input_type
        payload = input.payload
        trace_id = input.trace_id

        try:
            if input_type == "reflect":
                result = self._handle_full_reflection(payload, trace_id)
            elif input_type == "compare_outcomes":
                result = self._handle_compare_outcomes(payload, trace_id)
            elif input_type == "detect_anomalies":
                result = self._handle_detect_anomalies(payload, trace_id)
            elif input_type == "compute_success_score":
                result = self._handle_compute_success_score(payload, trace_id)
            elif input_type == "generate_signals":
                result = self._handle_generate_signals(payload, trace_id)
            elif input_type == "get_reflection":
                result = self._handle_get_reflection(payload, trace_id)
            elif input_type == "list_reflections":
                result = self._handle_list_reflections(payload, trace_id)
            else:
                raise ValueError(f"Unknown reflection input_type: {input_type!r}")

            confidence = result.get("confidence", 1.0)
            processing_ms = (time.time() - start_time) * 1000

            return EngineOutput(
                output_type=f"reflection_{input_type}",
                payload=result,
                confidence=confidence,
                confidence_factors={"deterministic": 1.0},
                deterministic=True,
                trace_id=trace_id,
                escalation_used=False,
                processing_time_ms=round(processing_ms, 2),
            )

        except Exception as e:
            logger.exception("ReflectionEngine.process(%s) failed", input_type)
            processing_ms = (time.time() - start_time) * 1000
            return EngineOutput(
                output_type=f"reflection_{input_type}_error",
                payload={"error": str(e), "input_type": input_type},
                confidence=0.0,
                confidence_factors={"error": 1.0},
                deterministic=True,
                trace_id=trace_id,
                processing_time_ms=round(processing_ms, 2),
            )

    def escalate(self, input: EngineInput) -> EscalationResult:
        """Prepare escalation data for AI-assisted reflection analysis.

        Builds the prompt and context for an AI provider when deterministic
        reflection analysis is insufficient or confidence is below threshold.

        Args:
            input: The original engine input that triggered escalation.

        Returns:
            EscalationResult with prompt and context for the AI provider.
        """
        payload = input.payload
        subject_id = payload.get("subject_id", "unknown")
        subject_label = payload.get("subject_label", "")

        prompt = (
            f"Analyze the following reflection subject for improvement insights.\n\n"
            f"Subject: {subject_label} (ID: {subject_id})\n"
            f"Expected outcome: {payload.get('expected_outcome', {})}\n"
            f"Actual outcome: {payload.get('actual_outcome', {})}\n"
            f"Success score: {payload.get('success_score', 'N/A')}\n\n"
            f"Context: {input.context or {}}\n"
            f"Provide: 1) Root cause analysis of deviations "
            f"2) Specific improvement recommendations "
            f"3) Categorization of improvement signals."
        )

        return EscalationResult(
            input_type=input.input_type,
            prompt=prompt,
            context=input.context,
            trace_id=input.trace_id,
        )

    def get_capabilities(self) -> list[str]:
        """Return list of capability strings.

        Returns:
            List of capabilities this engine provides.
        """
        return [
            "reflect",
            "compare_outcomes",
            "detect_anomalies",
            "compute_success_score",
            "generate_signals",
            "list_reflections",
        ]

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            Dict with engine status information.
        """
        from core.intelligence.models import EngineStatus

        status = EngineStatus.ACTIVE
        issues: list[str] = []

        return {
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "status": status.value,
            "total_reflections": len(self._reflections),
            "dimension_weights": dict(self._dimension_weights),
            "anomaly_thresholds": dict(self._anomaly_thresholds),
            "timeline_engine_connected": self._timeline_engine is not None,
            "evidence_engine_connected": self._evidence_engine is not None,
            "issues": issues,
        }

    # ── Public API: Reflection Queries ───────────────────────────────────────

    def get_reflection(self, reflection_id: str) -> ReflectionRecord | None:
        """Retrieve a reflection record by ID.

        Args:
            reflection_id: The reflection's UUID.

        Returns:
            The ReflectionRecord, or None if not found.
        """
        return self._reflections.get(reflection_id)

    def list_reflections(
        self,
        subject_id: str | None = None,
        subject_type: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        has_anomalies: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReflectionRecord]:
        """List reflections with optional filtering.

        Args:
            subject_id: Optional filter by subject ID.
            subject_type: Optional filter by subject type.
            min_score: Optional minimum success score filter.
            max_score: Optional maximum success score filter.
            has_anomalies: Optional filter for reflections with anomalies.
            limit: Maximum results to return (default 50).
            offset: Pagination offset.

        Returns:
            List of matching ReflectionRecord objects, ordered by timestamp
            descending (newest first).
        """
        result = list(self._reflections.values())

        if subject_id is not None:
            result = [r for r in result if r.subject_id == subject_id]
        if subject_type is not None:
            result = [r for r in result if r.subject_type == subject_type]
        if min_score is not None:
            result = [r for r in result if r.success_score >= min_score]
        if max_score is not None:
            result = [r for r in result if r.success_score <= max_score]
        if has_anomalies is True:
            result = [r for r in result if r.has_anomalies]
        elif has_anomalies is False:
            result = [r for r in result if not r.has_anomalies]

        result.sort(key=lambda r: r.timestamp, reverse=True)
        return result[offset : offset + limit]

    def get_reflection_count(self) -> int:
        """Get the total number of reflections tracked.

        Returns:
            Total reflection count.
        """
        return len(self._reflections)

    # ── Public API: Core reflection operations ───────────────────────────────

    def compare_outcomes(
        self,
        expected: dict[str, Any],
        actual: dict[str, Any],
        tolerances: dict[str, float] | None = None,
    ) -> list[OutcomeComparison]:
        """Compare expected vs actual outcomes across all dimensions.

        Performs per-key comparison of expected vs actual outcome dicts.
        For numeric values, computes absolute and percentage deviation.
        For non-numeric values, performs exact match comparison.

        Args:
            expected: Dict of expected outcome dimensions.
            actual: Dict of actual observed outcome dimensions.
            tolerances: Optional per-dimension tolerance thresholds.
                Defaults to 0.0 (exact match required).

        Returns:
            List of OutcomeComparison objects, one per dimension.
        """
        all_keys = set(expected.keys()) | set(actual.keys())
        comparisons: list[OutcomeComparison] = []

        for key in sorted(all_keys):
            exp_val = expected.get(key)
            act_val = actual.get(key)
            tolerance = (tolerances or {}).get(key, 0.0)

            deviation = 0.0
            deviation_pct = 0.0
            detail = ""

            if exp_val is None and act_val is None:
                within_tolerance = True
                detail = f"'{key}': both missing, treated as match"
            elif exp_val is None:
                within_tolerance = False
                deviation = 1.0
                deviation_pct = 1.0
                detail = f"'{key}': unexpected key in actual outcome"
            elif act_val is None:
                within_tolerance = False
                deviation = 1.0
                deviation_pct = 1.0
                detail = f"'{key}': expected key missing from actual outcome"
            elif isinstance(exp_val, (int, float)) and isinstance(act_val, (int, float)):
                deviation = abs(float(act_val) - float(exp_val))
                if float(exp_val) != 0:
                    deviation_pct = deviation / abs(float(exp_val))
                else:
                    deviation_pct = deviation if deviation > 0 else 0.0
                within_tolerance = deviation <= tolerance
                detail = (
                    f"'{key}': expected={exp_val}, actual={act_val}, "
                    f"deviation={deviation:.4f} ({deviation_pct*100:.1f}%)"
                )
            else:
                # Non-numeric: exact match
                deviation = 0.0 if exp_val == act_val else 1.0
                deviation_pct = 0.0 if exp_val == act_val else 1.0
                within_tolerance = exp_val == act_val
                detail = (
                    f"'{key}': expected={exp_val!r}, actual={act_val!r} "
                    f"{'match' if within_tolerance else 'MISMATCH'}"
                )

            comparisons.append(
                OutcomeComparison(
                    dimension=key,
                    expected=exp_val,
                    actual=act_val,
                    deviation=deviation,
                    deviation_pct=round(deviation_pct, 6),
                    within_tolerance=within_tolerance,
                    tolerance=tolerance,
                    detail=detail,
                )
            )

        return comparisons

    def detect_anomalies(
        self,
        comparisons: list[OutcomeComparison],
    ) -> list[Anomaly]:
        """Detect anomalies from outcome comparisons using threshold-based detection.

        Each comparison is evaluated against the configured severity thresholds.
        A comparison that exceeds the lowest threshold generates an anomaly at
        the highest exceeded severity level.

        Args:
            comparisons: List of OutcomeComparison objects to evaluate.

        Returns:
            List of detected Anomaly objects, empty if none found.
        """
        anomalies: list[Anomaly] = []

        for comp in comparisons:
            if comp.within_tolerance:
                continue

            deviation_pct = comp.deviation_pct

            # Determine severity based on deviation magnitude
            severity = AnomalySeverity.INFO
            threshold_value = 0.0

            if deviation_pct >= self._anomaly_thresholds["critical"]:
                severity = AnomalySeverity.CRITICAL
                threshold_value = self._anomaly_thresholds["critical"]
            elif deviation_pct >= self._anomaly_thresholds["error"]:
                severity = AnomalySeverity.ERROR
                threshold_value = self._anomaly_thresholds["error"]
            elif deviation_pct >= self._anomaly_thresholds["warning"]:
                severity = AnomalySeverity.WARNING
                threshold_value = self._anomaly_thresholds["warning"]
            elif deviation_pct >= self._anomaly_thresholds["info"]:
                severity = AnomalySeverity.INFO
                threshold_value = self._anomaly_thresholds["info"]

            from core.kernel.types import generate_uuid7

            anomaly = Anomaly(
                anomaly_id=generate_uuid7(),
                field=comp.dimension,
                expected_value=comp.expected,
                actual_value=comp.actual,
                deviation=deviation_pct,
                severity=severity,
                description=(
                    f"{severity.value.upper()}: {comp.detail} "
                    f"(exceeded {severity.value} threshold of {threshold_value})"
                ),
                threshold=threshold_value,
            )
            anomalies.append(anomaly)

        # Sort anomalies by severity (most severe first)
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.ERROR: 1,
            AnomalySeverity.WARNING: 2,
            AnomalySeverity.INFO: 3,
        }
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 99))

        return anomalies

    def compute_success_score(
        self,
        comparisons: list[OutcomeComparison],
        weights: dict[str, float] | None = None,
    ) -> SuccessScoreComponents:
        """Compute a weighted success score from outcome comparisons.

        Each dimension's score is computed as:
            score = 1.0 - deviation_pct  (clamped to [0, 1])

        The overall score is the weighted average across all dimensions
        that appear in both comparisons and weights.

        Args:
            comparisons: List of OutcomeComparison objects.
            weights: Optional per-dimension weights. Uses engine defaults if
                omitted. Only dimensions present in both comparisons and
                weights are included.

        Returns:
            A SuccessScoreComponents with per-dimension scores and overall.
        """
        effective_weights = weights or self._dimension_weights

        dimension_scores: dict[str, float] = {}
        active_weights: dict[str, float] = {}

        total_weight_used = 0.0

        for comp in comparisons:
            dim = comp.dimension
            weight = effective_weights.get(dim)

            if weight is None or weight <= 0.0:
                continue

            score = max(0.0, 1.0 - comp.deviation_pct)
            dimension_scores[dim] = round(score, 6)
            active_weights[dim] = weight
            total_weight_used += weight

        if not dimension_scores or total_weight_used <= 0.0:
            return SuccessScoreComponents(
                dimension_scores={},
                weights={},
                overall_score=0.0,
            )

        # Normalize weights to sum to 1.0
        if abs(total_weight_used - 1.0) > 0.001:
            normalized_weights = {
                dim: w / total_weight_used
                for dim, w in active_weights.items()
            }
        else:
            normalized_weights = dict(active_weights)

        overall = sum(
            dimension_scores[dim] * normalized_weights[dim]
            for dim in dimension_scores
        )
        overall = round(overall, 6)

        return SuccessScoreComponents(
            dimension_scores=dimension_scores,
            weights=normalized_weights,
            overall_score=overall,
        )

    def generate_improvement_signals(
        self,
        reflection: ReflectionRecord,
    ) -> list[ImprovementSignal]:
        """Generate improvement signals from a reflection's anomalies.

        Each anomaly with severity WARNING or higher generates an
        improvement signal. The signal category is inferred from the
        anomaly field name.

        Args:
            reflection: The completed reflection record.

        Returns:
            List of generated ImprovementSignal objects.
        """
        signals: list[ImprovementSignal] = []

        for anomaly in reflection.anomalies:
            if anomaly.severity in (AnomalySeverity.INFO,):
                continue  # Don't generate signals for info-level anomalies

            from core.kernel.types import generate_uuid7

            category = self._infer_signal_category(anomaly.field)
            priority = self._severity_to_priority(anomaly.severity)

            signal = ImprovementSignal(
                signal_id=generate_uuid7(),
                category=category,
                description=f"Improvement needed: {anomaly.field} deviation",
                detail=anomaly.description,
                priority=priority,
                source_reflection_id=reflection.reflection_id,
                context={
                    "field": anomaly.field,
                    "expected": str(anomaly.expected_value),
                    "actual": str(anomaly.actual_value),
                    "deviation": anomaly.deviation,
                    "severity": anomaly.severity.value,
                },
            )
            signals.append(signal)

        return signals

    # ── Private: Input Handlers ──────────────────────────────────────────────

    def _handle_full_reflection(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Perform a complete reflection cycle.

        Combines compare_outcomes, detect_anomalies, compute_success_score,
        and generate_signals into a single operation.

        Args:
            payload: Reflection data including expected/actual outcomes.
            trace_id: Correlation ID.

        Returns:
            Dict with complete reflection results.

        Raises:
            ValueError: If required fields are missing.
        """
        subject_id = payload.get("subject_id", "")
        subject_type = payload.get("subject_type", "")
        subject_label = payload.get("subject_label", "")
        expected = payload.get("expected_outcome", {})
        actual = payload.get("actual_outcome", {})
        tolerances = payload.get("tolerances")
        weights = payload.get("weights")

        if not subject_id:
            raise ValueError("'subject_id' is required for reflection")
        if not expected:
            raise ValueError("'expected_outcome' is required for reflection")

        # Step 1: Compare outcomes
        comparisons = self.compare_outcomes(expected, actual, tolerances)

        # Step 2: Detect anomalies
        anomalies = self.detect_anomalies(comparisons)

        # Step 3: Compute success score
        score_components = self.compute_success_score(comparisons, weights)

        # Step 4: Build reflection record
        reflection = ReflectionRecord(
            subject_id=subject_id,
            subject_type=subject_type or "unknown",
            subject_label=subject_label,
            trace_id=trace_id,
            expected_outcome=expected,
            actual_outcome=actual,
            comparisons=comparisons,
            success_score=score_components.overall_score,
            success_score_components=score_components,
            anomalies=anomalies,
            confidence=score_components.overall_score,
        )

        # Step 5: Generate improvement signals
        signals = self.generate_improvement_signals(reflection)
        reflection.improvement_signals = signals

        # Store the reflection
        self._reflections[reflection.reflection_id] = reflection

        logger.info(
            "Created reflection %s for %s (subject=%s, score=%.4f, anomalies=%d, signals=%d)",
            reflection.reflection_id,
            subject_type,
            subject_id,
            reflection.success_score,
            len(anomalies),
            len(signals),
        )

        return {
            "reflection_id": reflection.reflection_id,
            "subject_id": subject_id,
            "subject_type": subject_type,
            "success_score": reflection.success_score,
            "comparisons": [vars(c) for c in comparisons],
            "anomalies": [vars(a) for a in anomalies],
            "signals": [vars(s) for s in signals],
            "confidence": reflection.confidence,
            "timestamp": reflection.timestamp,
        }

    def _handle_compare_outcomes(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a compare_outcomes request.

        Args:
            payload: Must include 'expected_outcome' and 'actual_outcome'.
            trace_id: Correlation ID.

        Returns:
            Dict with comparison results.
        """
        expected = payload.get("expected_outcome", {})
        actual = payload.get("actual_outcome", {})
        tolerances = payload.get("tolerances")

        if not expected:
            raise ValueError("'expected_outcome' is required")

        comparisons = self.compare_outcomes(expected, actual, tolerances)
        all_within = all(c.within_tolerance for c in comparisons)

        return {
            "comparisons": [vars(c) for c in comparisons],
            "all_within_tolerance": all_within,
            "total_dimensions": len(comparisons),
            "within_tolerance_count": sum(1 for c in comparisons if c.within_tolerance),
        }

    def _handle_detect_anomalies(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a detect_anomalies request.

        Args:
            payload: Must include 'comparisons' (list of dicts).
            trace_id: Correlation ID.

        Returns:
            Dict with detected anomalies.
        """
        raw_comparisons = payload.get("comparisons", [])
        if not raw_comparisons:
            raise ValueError("'comparisons' is required for anomaly detection")

        comparisons = [
            OutcomeComparison(**c) if not isinstance(c, OutcomeComparison) else c
            for c in raw_comparisons
        ]

        anomalies = self.detect_anomalies(comparisons)

        return {
            "anomalies": [vars(a) for a in anomalies],
            "total_anomalies": len(anomalies),
            "has_critical": any(
                a.severity == AnomalySeverity.CRITICAL for a in anomalies
            ),
            "has_errors": any(
                a.severity == AnomalySeverity.ERROR for a in anomalies
            ),
        }

    def _handle_compute_success_score(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a compute_success_score request.

        Args:
            payload: Must include 'comparisons'. Optional: 'weights'.
            trace_id: Correlation ID.

        Returns:
            Dict with success score components.
        """
        raw_comparisons = payload.get("comparisons", [])
        weights = payload.get("weights")

        if not raw_comparisons:
            raise ValueError("'comparisons' is required for success score computation")

        comparisons = [
            OutcomeComparison(**c) if not isinstance(c, OutcomeComparison) else c
            for c in raw_comparisons
        ]

        components = self.compute_success_score(comparisons, weights)

        return {
            "overall_score": components.overall_score,
            "dimension_scores": components.dimension_scores,
            "weights": components.weights,
        }

    def _handle_generate_signals(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a generate_signals request.

        Args:
            payload: Must include 'reflection_id' or full reflection data.
            trace_id: Correlation ID.

        Returns:
            Dict with generated improvement signals.
        """
        reflection_id = payload.get("reflection_id")
        if reflection_id:
            reflection = self._get_reflection(reflection_id)
        else:
            # Create from payload data
            reflection = ReflectionRecord(
                subject_id=payload.get("subject_id", ""),
                subject_type=payload.get("subject_type", "unknown"),
                subject_label=payload.get("subject_label", ""),
                expected_outcome=payload.get("expected_outcome", {}),
                actual_outcome=payload.get("actual_outcome", {}),
            )
            # Build anomalies from raw anomaly data if provided
            raw_anomalies = payload.get("anomalies", [])
            if raw_anomalies:
                comparison = OutcomeComparison(
                    dimension=raw_anomalies[0].get("field", "unknown"),
                    expected=raw_anomalies[0].get("expected_value"),
                    actual=raw_anomalies[0].get("actual_value"),
                    deviation=raw_anomalies[0].get("deviation", 0.0),
                    deviation_pct=raw_anomalies[0].get("deviation", 0.0),
                    within_tolerance=False,
                )
                anomalies = self.detect_anomalies([comparison])
                reflection.anomalies = anomalies

        signals = self.generate_improvement_signals(reflection)

        return {
            "signals": [vars(s) for s in signals],
            "total_signals": len(signals),
            "reflection_id": reflection.reflection_id,
        }

    def _handle_get_reflection(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a get_reflection request.

        Args:
            payload: Must include 'reflection_id'.
            trace_id: Correlation ID.

        Returns:
            Dict with the reflection record.
        """
        reflection_id = payload.get("reflection_id", "")
        if not reflection_id:
            raise ValueError("'reflection_id' is required")
        reflection = self._get_reflection(reflection_id)
        return {
            "reflection_id": reflection_id,
            "reflection": reflection,
        }

    def _handle_list_reflections(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a list_reflections request.

        Args:
            payload: Optional filters.
            trace_id: Correlation ID.

        Returns:
            Dict with 'reflections' list and 'total' count.
        """
        reflections = self.list_reflections(
            subject_id=payload.get("subject_id"),
            subject_type=payload.get("subject_type"),
            min_score=payload.get("min_score"),
            max_score=payload.get("max_score"),
            has_anomalies=payload.get("has_anomalies"),
            limit=payload.get("limit", 50),
            offset=payload.get("offset", 0),
        )

        return {
            "reflections": reflections,
            "total": len(reflections),
        }

    # ── Private: Helpers ──────────────────────────────────────────────────────

    def _get_reflection(self, reflection_id: str) -> ReflectionRecord:
        """Get a reflection by ID, raising if not found.

        Args:
            reflection_id: The reflection UUID.

        Returns:
            The ReflectionRecord.

        Raises:
            ValueError: If the reflection is not found.
        """
        reflection = self._reflections.get(reflection_id)
        if reflection is None:
            raise ValueError(f"Reflection not found: {reflection_id!r}")
        return reflection

    def _infer_signal_category(self, field: str) -> ImprovementSignalCategory:
        """Infer the improvement signal category from a field name.

        Maps common field names to improvement categories.

        Args:
            field: The anomaly field name.

        Returns:
            The inferred ImprovementSignalCategory.
        """
        field_lower = field.lower()

        if any(term in field_lower for term in ("process", "workflow", "step")):
            return ImprovementSignalCategory.PROCESS
        if any(term in field_lower for term in ("knowledge", "fact", "info")):
            return ImprovementSignalCategory.KNOWLEDGE
        if any(term in field_lower for term in ("reason", "logic", "conclusion")):
            return ImprovementSignalCategory.REASONING
        if any(term in field_lower for term in ("time", "timing", "schedule")):
            return ImprovementSignalCategory.TIMING
        if any(term in field_lower for term in ("comm", "message", "report")):
            return ImprovementSignalCategory.COMMUNICATION
        if any(term in field_lower for term in ("evidence", "proof", "data")):
            return ImprovementSignalCategory.EVIDENCE
        if any(term in field_lower for term in ("policy", "rule", "govern")):
            return ImprovementSignalCategory.GOVERNANCE
        if any(term in field_lower for term in ("tool", "integration", "api")):
            return ImprovementSignalCategory.TOOL

        return ImprovementSignalCategory.OTHER

    def _severity_to_priority(self, severity: AnomalySeverity) -> int:
        """Convert anomaly severity to a numeric priority for signals.

        Args:
            severity: The anomaly severity level.

        Returns:
            Priority value (1-10, higher = more urgent).
        """
        mapping = {
            AnomalySeverity.CRITICAL: 10,
            AnomalySeverity.ERROR: 7,
            AnomalySeverity.WARNING: 4,
            AnomalySeverity.INFO: 1,
        }
        return mapping.get(severity, 1)