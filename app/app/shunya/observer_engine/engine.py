"""SHUNYA — Observer Engine (Phase J — ES-006).

The Observer Engine transforms execution outcomes into verified observations.
It is the bridge between *what actually happened* (Executor) and *what should
change as a result* (Learning, Knowledge).

The engine implements a deterministic 9-stage pipeline:
  1. Observation Intake
  2. Evidence Validation
  3. Outcome Comparison
  4. Deviation Detection
  5. Anomaly Detection
  6. Confidence Assessment
  7. Observation Packaging
  8. Learning Handoff
  9. Knowledge Notification

Architectural authority: ES-006 — Observer Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.shunya.observer_engine.models import (
    ObservationType, ObservationSeverity, EvidenceValidationStatus, FailureMode,
    Tolerance, ObservationVariance, ObservationState,
    EvidenceValidationResult, DeviationReport, AnomalyReport,
    LearningSignal, VerifiedObservation,
    ObserverInput, ObserverOutput, ObserverStats,
)


# ---------------------------------------------------------------------------
# Default tolerance thresholds per dimension
# ---------------------------------------------------------------------------

_DEFAULT_TOLERANCES: Dict[str, Tolerance] = {
    "task_completion": Tolerance("task_completion", 0.0, 0.0, 0.01),  # Any failed task is error+
    "evidence_quality": Tolerance("evidence_quality", 0.1, 0.3, 0.5),
    "confidence": Tolerance("confidence", 0.1, 0.25, 0.4),
    "duration": Tolerance("duration", 0.2, 0.5, 1.0),
    "cost": Tolerance("cost", 0.1, 0.25, 0.5),
}

# ---------------------------------------------------------------------------
# Anomaly patterns (simple rule-based)
# ---------------------------------------------------------------------------

_ANOMALY_PATTERNS: List[Dict[str, Any]] = [
    {
        "name": "all_tasks_failed",
        "description": "All tasks in the workflow failed",
        "check": lambda o: o.get("total", 0) > 0 and o.get("failed", 0) == o.get("total", 0),
        "severity": ObservationSeverity.CRITICAL.value,
    },
    {
        "name": "no_evidence_collected",
        "description": "No execution evidence was collected despite completed tasks",
        "check": lambda o: o.get("completed", 0) > 0 and o.get("evidence_count", 0) == 0,
        "severity": ObservationSeverity.WARNING.value,
    },
    {
        "name": "high_failure_rate",
        "description": "More than half of tasks failed",
        "check": lambda o: o.get("total", 0) > 2 and (
            o.get("failed", 0) / max(o.get("total", 1), 1) > 0.5),
        "severity": ObservationSeverity.ERROR.value,
    },
    {
        "name": "zero_duration",
        "description": "Workflow completed in zero measurable time",
        "check": lambda o: o.get("total_duration_seconds", 1.0) < 0.001 and o.get("total", 0) > 0,
        "severity": ObservationSeverity.WARNING.value,
    },
]


# ---------------------------------------------------------------------------
# Observer Engine
# ---------------------------------------------------------------------------


class ObserverEngine:
    """Observer Engine — transforms execution outcomes into verified observations.

    Implements a deterministic 9-stage pipeline per ES-006.
    """

    def __init__(self) -> None:
        self._tolerances: Dict[str, Tolerance] = dict(_DEFAULT_TOLERANCES)
        self._observations: List[VerifiedObservation] = []
        self._stats = ObserverStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe(self, inp: ObserverInput) -> ObserverOutput:
        """Observe an execution outcome.

        Implements the full 9-stage deterministic pipeline.
        """
        # Stage 1: Observation Intake
        intake_errors, actual_state = self._intake(inp)
        if intake_errors:
            return ObserverOutput(success=False, errors=intake_errors)

        # Stage 2: Evidence Validation
        evidence_result = self._validate_evidence(inp, actual_state)

        # Stage 3: Outcome Comparison
        expected_state = self._build_expected_state(inp)
        variances = self._compare_outcomes(expected_state, actual_state)

        # Stage 4: Deviation Detection
        deviations = self._detect_deviations(variances)

        # Stage 5: Anomaly Detection
        anomalies = self._detect_anomalies(inp, actual_state)

        # Stage 6: Confidence Assessment
        confidence = self._assess_confidence(evidence_result, deviations, anomalies)

        # Stage 7: Observation Packaging
        severity = self._classify_severity(deviations, anomalies, evidence_result)
        observation = self._package_observation(
            inp, actual_state, evidence_result, variances,
            deviations, anomalies, confidence, severity,
        )

        # Stage 8: Learning Handoff
        learning_signals = self._extract_learning_signals(observation)

        # Stage 9: Knowledge Notification
        self._notify_knowledge(observation)

        # Store and update stats
        observation.learning_signals = learning_signals
        self._observations.append(observation)
        self._update_stats(observation, deviations, anomalies, evidence_result)

        return ObserverOutput(
            observation_id=observation.observation_id,
            observation=observation,
            anomaly_reports=anomalies,
            deviation_reports=deviations,
            learning_signals=learning_signals,
            success=True,
        )

    def observe_from_outcome(self, outcome_pkg: Any,
                             tenant_id: int = 1) -> ObserverOutput:
        """Convenience: observe from a Phase I OutcomePackage."""
        tasks: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []

        if hasattr(outcome_pkg, 'tasks') and outcome_pkg.tasks:
            tasks = outcome_pkg.tasks
        if hasattr(outcome_pkg, 'evidence') and outcome_pkg.evidence:
            evidence = [e.to_dict() if hasattr(e, 'to_dict') else e
                        for e in outcome_pkg.evidence]
        if hasattr(outcome_pkg, 'failures') and outcome_pkg.failures:
            failures = [f.to_dict() if hasattr(f, 'to_dict') else f
                        for f in outcome_pkg.failures]

        inp = ObserverInput(
            workflow_id=getattr(outcome_pkg, 'workflow_id', ''),
            plan_id=getattr(outcome_pkg, 'plan_id', ''),
            tenant_id=tenant_id,
            tasks=tasks,
            evidence=evidence,
            failures=failures,
            workflow_state=getattr(outcome_pkg, 'workflow_state', ''),
            metrics=getattr(outcome_pkg, 'metrics', None),
        )
        return self.observe(inp)

    # ------------------------------------------------------------------
    # Pipeline Stages
    # ------------------------------------------------------------------

    def _intake(self, inp: ObserverInput) -> Tuple[List[str], Dict[str, Any]]:
        """Stage 1: Receive and validate the execution outcome."""
        errors = inp.validate()
        if errors:
            return errors, {}

        actual_state: Dict[str, Any] = {
            "workflow_id": inp.workflow_id,
            "plan_id": inp.plan_id,
            "tenant_id": inp.tenant_id,
            "workflow_state": inp.workflow_state,
            "tasks": inp.tasks,
            "evidence": inp.evidence,
            "failures": inp.failures,
            "total_tasks": len(inp.tasks),
        }

        # Extract metrics
        if inp.metrics:
            actual_state["completed"] = inp.metrics.get("completed", 0)
            actual_state["failed"] = inp.metrics.get("failed", 0)
            actual_state["total_duration_seconds"] = inp.metrics.get("total_duration_seconds", 0.0)
            actual_state["total_retries"] = inp.metrics.get("total_retries", 0)
        else:
            actual_state["completed"] = sum(
                1 for t in inp.tasks if t.get("state") == "completed"
            )
            actual_state["failed"] = len(inp.failures)
            actual_state["total_duration_seconds"] = 0.0
            actual_state["total_retries"] = 0

        actual_state["evidence_count"] = len(inp.evidence)
        actual_state["failure_count"] = len(inp.failures)

        return [], actual_state

    def _validate_evidence(self, inp: ObserverInput,
                           actual_state: Dict[str, Any]) -> EvidenceValidationResult:
        """Stage 2: Validate execution evidence across 6 dimensions."""
        result = EvidenceValidationResult()

        if not inp.evidence:
            result.completeness = EvidenceValidationStatus.FAIL
            result.quality_score = 0.0
            return result

        # Completeness: all evidence has required fields
        required = {"evidence_id", "task_id", "success"}
        all_complete = all(
            all(k in e for k in required)
            for e in inp.evidence if isinstance(e, dict)
        )
        result.completeness = EvidenceValidationStatus.PASS if all_complete else EvidenceValidationStatus.WARN

        # Authenticity: evidence IDs are non-empty and unique
        ids = [e.get("evidence_id", "") for e in inp.evidence if isinstance(e, dict)]
        if all(ids) and len(ids) == len(set(ids)):
            result.authenticity = EvidenceValidationStatus.PASS
        else:
            result.authenticity = EvidenceValidationStatus.WARN

        # Consistency: evidence success/failure matches task states
        task_states = {t.get("task_id"): t.get("state") for t in inp.tasks if isinstance(t, dict)}
        all_consistent = all(
            e.get("success", False) == (task_states.get(e.get("task_id", "")) == "completed")
            for e in inp.evidence if isinstance(e, dict) and e.get("task_id") in task_states
        )
        result.consistency = EvidenceValidationStatus.PASS if all_consistent else EvidenceValidationStatus.WARN

        # Correlation: evidence references known task IDs
        task_ids = {t.get("task_id") for t in inp.tasks if isinstance(t, dict)}
        all_correlated = all(
            e.get("task_id", "") in task_ids
            for e in inp.evidence if isinstance(e, dict)
        )
        result.correlation = EvidenceValidationStatus.PASS if all_correlated else EvidenceValidationStatus.WARN

        # Timestamp integrity: evidence timestamps are present and not in the future
        now = datetime.now(timezone.utc)
        all_timely = True
        for e in inp.evidence:
            if isinstance(e, dict) and e.get("timestamp"):
                ts_str = e["timestamp"]
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts > now:
                        all_timely = False
                except (ValueError, TypeError):
                    all_timely = False
        result.timestamp_integrity = EvidenceValidationStatus.PASS if all_timely else EvidenceValidationStatus.WARN

        # Provenance: evidence has a known source (channel)
        all_provenance = all(
            e.get("channel", "") or e.get("action", "")
            for e in inp.evidence if isinstance(e, dict)
        )
        result.provenance = EvidenceValidationStatus.PASS if all_provenance else EvidenceValidationStatus.WARN

        # Compute quality score (multiplicative per spec)
        scores = []
        for status in (result.completeness, result.authenticity, result.consistency,
                       result.correlation, result.timestamp_integrity, result.provenance):
            if status == EvidenceValidationStatus.PASS:
                scores.append(1.0)
            elif status == EvidenceValidationStatus.FAIL:
                scores.append(0.0)
            else:
                scores.append(0.5)  # WARN → partial score

        # Product of all dimensions
        product = 1.0
        for s in scores:
            product *= s
        result.quality_score = product

        return result

    def _build_expected_state(self, inp: ObserverInput) -> Dict[str, Any]:
        """Build the expected state from the plan (if available)."""
        expected: Dict[str, Any] = {}

        if inp.expected_metrics:
            expected["completed"] = inp.expected_metrics.get("completed", 0)
            expected["failed"] = inp.expected_metrics.get("failed", 0)
            expected["total_duration_seconds"] = inp.expected_metrics.get("total_duration_seconds", 0.0)
            expected["total_retries"] = inp.expected_metrics.get("total_retries", 0)

        if inp.expected_tasks:
            expected["total_tasks"] = len(inp.expected_tasks)

        return expected

    def _compare_outcomes(self, expected: Dict[str, Any],
                          actual: Dict[str, Any]) -> List[ObservationVariance]:
        """Stage 3: Compare actual outcomes to expected outcomes."""
        variances: List[ObservationVariance] = []

        if not expected:
            return variances  # No expected data → no comparison

        # Task completion comparison
        e_completed = expected.get("completed", 0)
        a_completed = actual.get("completed", 0)
        if e_completed != a_completed:
            delta = a_completed - e_completed
            pct = _safe_pct(delta, e_completed or 1)
            variances.append(ObservationVariance(
                dimension="task_completion",
                expected=e_completed,
                actual=a_completed,
                delta=delta,
                delta_percentage=pct,
                severity=_tolerance_severity("task_completion", pct),
                explanation=f"Completed {a_completed} tasks vs expected {e_completed}",
            ))

        # Duration comparison
        e_dur = expected.get("total_duration_seconds", 0.0)
        a_dur = actual.get("total_duration_seconds", 0.0)
        if e_dur > 0 and abs(e_dur - a_dur) > 0.001:
            delta = a_dur - e_dur
            pct = _safe_pct(delta, e_dur)
            variances.append(ObservationVariance(
                dimension="duration",
                expected=e_dur,
                actual=a_dur,
                delta=delta,
                delta_percentage=pct,
                severity=_tolerance_severity("duration", pct),
                explanation=f"Duration {a_dur:.1f}s vs expected {e_dur:.1f}s",
            ))

        # Retry comparison
        e_retries = expected.get("total_retries", 0)
        a_retries = actual.get("total_retries", 0)
        if e_retries != a_retries:
            delta = a_retries - e_retries
            pct = _safe_pct(delta, e_retries or 1)
            variances.append(ObservationVariance(
                dimension="retries",
                expected=e_retries,
                actual=a_retries,
                delta=delta,
                delta_percentage=pct,
                severity=_tolerance_severity("confidence", pct),
                explanation=f"Retries {a_retries} vs expected {e_retries}",
            ))

        return variances

    def _detect_deviations(self, variances: List[ObservationVariance]) -> List[DeviationReport]:
        """Stage 4: Quantify differences and produce deviation reports."""
        reports: List[DeviationReport] = []

        for v in variances:
            severity = ObservationSeverity.INFO
            tolerance = self._tolerances.get(v.dimension)
            if tolerance:
                severity = tolerance.classify(v.delta_percentage)

            reports.append(DeviationReport(
                dimension=v.dimension,
                expected_value=v.expected,
                actual_value=v.actual,
                delta=v.delta,
                delta_percentage=v.delta_percentage,
                severity=severity.value,
                tolerance_used=tolerance,
            ))

        return reports

    def _detect_anomalies(self, inp: ObserverInput,
                          actual_state: Dict[str, Any]) -> List[AnomalyReport]:
        """Stage 5: Detect unexpected patterns and outliers."""
        reports: List[AnomalyReport] = []
        context = {
            "total": actual_state.get("total_tasks", 0),
            "completed": actual_state.get("completed", 0),
            "failed": actual_state.get("failed", 0),
            "evidence_count": actual_state.get("evidence_count", 0),
            "total_duration_seconds": actual_state.get("total_duration_seconds", 0.0),
        }

        for pattern in _ANOMALY_PATTERNS:
            try:
                if pattern["check"](context):
                    reports.append(AnomalyReport(
                        pattern=pattern["name"],
                        description=pattern["description"],
                        severity=pattern["severity"],
                    ))
            except Exception:
                continue

        return reports

    def _assess_confidence(self, evidence_result: EvidenceValidationResult,
                           deviations: List[DeviationReport],
                           anomalies: List[AnomalyReport]) -> float:
        """Stage 6: Compute confidence in the observation.

        Factors: evidence quality (0-1), deviation severity, anomaly presence.
        """
        evidence_score = evidence_result.quality_score

        # Deviation penalty: CRITICAL→0.3, ERROR→0.5, WARNING→0.8, INFO→1.0
        dev_penalties = {
            ObservationSeverity.CRITICAL.value: 0.3,
            ObservationSeverity.ERROR.value: 0.5,
            ObservationSeverity.WARNING.value: 0.8,
            ObservationSeverity.INFO.value: 1.0,
        }
        dev_score = min(
            (dev_penalties.get(d.severity, 1.0) for d in deviations),
            default=1.0,
        )

        # Anomaly penalty: any anomaly halves the score
        anomaly_penalty = 0.5 if anomalies else 1.0

        confidence = evidence_score * dev_score * anomaly_penalty
        return max(0.0, min(1.0, confidence))

    def _classify_severity(self, deviations: List[DeviationReport],
                           anomalies: List[AnomalyReport],
                           evidence: EvidenceValidationResult) -> str:
        """Determine overall observation severity."""
        if any(a.severity == ObservationSeverity.CRITICAL.value for a in anomalies):
            return ObservationSeverity.CRITICAL.value
        if any(d.severity == ObservationSeverity.CRITICAL.value for d in deviations):
            return ObservationSeverity.CRITICAL.value
        if evidence.any_failed:
            return ObservationSeverity.ERROR.value
        if anomalies:
            return ObservationSeverity.ERROR.value
        if any(d.severity == ObservationSeverity.ERROR.value for d in deviations):
            return ObservationSeverity.ERROR.value
        if any(d.severity == ObservationSeverity.WARNING.value for d in deviations):
            return ObservationSeverity.WARNING.value
        return ObservationSeverity.INFO.value

    def _package_observation(self, inp: ObserverInput,
                             actual_state: Dict[str, Any],
                             evidence_result: EvidenceValidationResult,
                             variances: List[ObservationVariance],
                             deviations: List[DeviationReport],
                             anomalies: List[AnomalyReport],
                             confidence: float,
                             severity: str) -> VerifiedObservation:
        """Stage 7: Package all findings into a structured observation."""
        act_state = ObservationState(
            status=actual_state.get("workflow_state", "unknown"),
            dimensions=[
                {"name": "tasks", "value": actual_state.get("total_tasks", 0)},
                {"name": "completed", "value": actual_state.get("completed", 0)},
                {"name": "failed", "value": actual_state.get("failed", 0)},
                {"name": "evidence_count", "value": actual_state.get("evidence_count", 0)},
            ],
        )

        return VerifiedObservation(
            workflow_id=inp.workflow_id,
            plan_id=inp.plan_id,
            tenant_id=inp.tenant_id,
            observation_type=inp.observation_type,
            actual_state=act_state,
            variances=variances,
            evidence_quality=evidence_result.quality_score,
            confidence=confidence,
            severity=severity,
            evidence_validation=evidence_result,
            anomalies=anomalies,
            deviations=deviations,
        )

    def _extract_learning_signals(self, obs: VerifiedObservation) -> List[LearningSignal]:
        """Stage 8: Extract learning signals from deviations and anomalies."""
        signals: List[LearningSignal] = []

        for dev in obs.deviations:
            if dev.severity in (ObservationSeverity.ERROR.value,
                                ObservationSeverity.CRITICAL.value):
                signals.append(LearningSignal(
                    observation_id=obs.observation_id,
                    workflow_id=obs.workflow_id,
                    signal_type="deviation",
                    description=f"Deviated on '{dev.dimension}': "
                                f"expected {dev.expected_value}, got {dev.actual_value}",
                    dimension=dev.dimension,
                    delta=dev.delta,
                    delta_percentage=dev.delta_percentage,
                    confidence=obs.confidence,
                    tenant_id=obs.tenant_id,
                ))

        for anomaly in obs.anomalies:
            signals.append(LearningSignal(
                observation_id=obs.observation_id,
                workflow_id=obs.workflow_id,
                signal_type="anomaly",
                description=anomaly.description,
                dimension=anomaly.dimension or "general",
                confidence=obs.confidence * 0.8,  # Slightly lower for anomalies
                tenant_id=obs.tenant_id,
            ))

        if not signals:
            signals.append(LearningSignal(
                observation_id=obs.observation_id,
                workflow_id=obs.workflow_id,
                signal_type="success",
                description="Execution completed as expected",
                confidence=obs.confidence,
                tenant_id=obs.tenant_id,
            ))

        return signals

    def _notify_knowledge(self, obs: VerifiedObservation) -> None:
        """Stage 9: Notify Knowledge Engine of new verified observation.

        Currently stores in-memory. Future: write to Knowledge Engine API.
        """
        pass  # Knowledge Engine integration deferred

    # ------------------------------------------------------------------
    # Public Queries
    # ------------------------------------------------------------------

    def get_observation(self, observation_id: str) -> Optional[VerifiedObservation]:
        for obs in reversed(self._observations):
            if obs.observation_id == observation_id:
                return obs
        return None

    def list_observations(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in reversed(self._observations[-limit:])]

    def list_anomalies(self, limit: int = 20) -> List[Dict[str, Any]]:
        anomalies: List[Dict[str, Any]] = []
        for obs in reversed(self._observations):
            if obs.anomalies:
                for a in obs.anomalies:
                    anomalies.append(a.to_dict())
                    if len(anomalies) >= limit:
                        break
            if len(anomalies) >= limit:
                break
        return anomalies

    def list_deviations(self, limit: int = 20) -> List[Dict[str, Any]]:
        deviations: List[Dict[str, Any]] = []
        for obs in reversed(self._observations):
            if obs.deviations:
                for d in obs.deviations:
                    deviations.append(d.to_dict())
                    if len(deviations) >= limit:
                        break
            if len(deviations) >= limit:
                break
        return deviations

    def set_tolerance(self, tolerance: Tolerance) -> None:
        """Set or update a tolerance threshold for a dimension."""
        self._tolerances[tolerance.dimension] = tolerance

    @property
    def stats(self) -> Dict[str, Any]:
        return self._stats.to_dict()

    def _update_stats(self, obs: VerifiedObservation,
                      deviations: List[DeviationReport],
                      anomalies: List[AnomalyReport],
                      evidence: EvidenceValidationResult) -> None:
        self._stats.total_observations += 1
        if anomalies:
            self._stats.with_anomalies += 1
        if deviations:
            self._stats.with_deviations += 1
        if evidence.any_failed:
            self._stats.with_evidence_failures += 1
        n = self._stats.total_observations
        self._stats.avg_confidence = (
            (self._stats.avg_confidence * (n - 1) + obs.confidence) / n
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_ENGINE_INSTANCE: Optional[ObserverEngine] = None


def get_observer_engine() -> ObserverEngine:
    """Get or create the singleton ObserverEngine instance."""
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = ObserverEngine()
    return _ENGINE_INSTANCE


def reset_observer_engine() -> None:
    """Reset the singleton ObserverEngine (for testing)."""
    global _ENGINE_INSTANCE
    _ENGINE_INSTANCE = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_pct(delta: float, reference: float) -> float:
    """Compute delta_percentage, avoiding division by zero."""
    if reference == 0.0:
        return float('inf') if delta != 0 else 0.0
    return delta / reference


def _tolerance_severity(dimension: str, pct: float) -> str:
    """Classify a delta percentage against default tolerances."""
    tol = _DEFAULT_TOLERANCES.get(dimension)
    if tol is None:
        return ObservationSeverity.INFO.value
    return tol.classify(pct).value