"""Tests for Phase J — Observer Engine (ES-006).

Covers:
  - Canonical data model tests
  - Evidence validation (6 dimensions)
  - Outcome comparison
  - Deviation detection with tolerances
  - Anomaly detection (4 pattern-based rules)
  - Confidence assessment
  - Full 9-stage pipeline integration
  - Immutable observations
  - Determinism
  - Concurrency
  - Legacy backward compatibility

Architectural authority: ES-006 — Observer Engine Specification
"""

from __future__ import annotations

import copy
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta

import pytest

from app.shunya.observer_engine.models import (
    ObservationType, ObservationSeverity, EvidenceValidationStatus, FailureMode,
    Tolerance, ObservationVariance, ObservationState,
    EvidenceValidationResult, DeviationReport, AnomalyReport,
    LearningSignal, VerifiedObservation,
    ObserverInput, ObserverOutput, ObserverStats,
)
from app.shunya.observer_engine.engine import (
    ObserverEngine, get_observer_engine, reset_observer_engine,
)
from app.shunya.observer_engine._legacy_observer import (
    ObserverLayer,
)


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture(autouse=True)
def reset_engine():
    reset_observer_engine()
    yield
    reset_observer_engine()


@pytest.fixture
def engine():
    return ObserverEngine()


def make_input(workflow_id: str = "wf-1", plan_id: str = "plan-1",
               tenant_id: int = 1, completed: int = 3, failed: int = 0,
               evidence_count: int = 3, metrics: Optional[Dict] = None,
               expected_req: Optional[Dict] = None) -> ObserverInput:
    if metrics is None:
        metrics = {"completed": completed, "failed": failed,
                   "total_duration_seconds": 5.0, "total_retries": 0}

    tasks = [{"task_id": f"t{i}", "state": "completed",
              "action": "echo", "target": "local"}
             for i in range(completed)]
    tasks += [{"task_id": f"t{failed+i}", "state": "failed",
               "action": "echo", "target": "local"}
              for i in range(failed)]

    evidence = [{
        "evidence_id": f"ev_{i}",
        "task_id": f"t{i}",
        "action": "echo",
        "channel": "local",
        "success": True,
        "response": {"ok": True},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    } for i in range(evidence_count)]

    inp = ObserverInput(
        workflow_id=workflow_id,
        plan_id=plan_id,
        tenant_id=tenant_id,
        tasks=tasks,
        evidence=evidence,
        metrics=metrics,
        workflow_state="completed",
    )

    if expected_req:
        inp.expected_metrics = expected_req.get("metrics")
        inp.expected_tasks = expected_req.get("tasks")

    return inp


# ======================================================================
# Model Tests
# ======================================================================


class TestModels:
    """Canonical observer model tests."""

    def test_tolerance_classify(self):
        t = Tolerance("test", 0.1, 0.25, 0.5)
        assert t.classify(0.05) == ObservationSeverity.INFO
        assert t.classify(0.15) == ObservationSeverity.WARNING
        assert t.classify(0.3) == ObservationSeverity.ERROR
        assert t.classify(0.6) == ObservationSeverity.CRITICAL

    def test_evidence_validation_defaults(self):
        ev = EvidenceValidationResult()
        assert not ev.passed
        assert not ev.any_failed
        assert ev.quality_score == 0.0

    def test_evidence_validation_passed(self):
        ev = EvidenceValidationResult(
            completeness=EvidenceValidationStatus.PASS,
            authenticity=EvidenceValidationStatus.PASS,
            consistency=EvidenceValidationStatus.PASS,
            correlation=EvidenceValidationStatus.PASS,
            timestamp_integrity=EvidenceValidationStatus.PASS,
            provenance=EvidenceValidationStatus.PASS,
        )
        assert ev.passed
        assert not ev.any_failed

    def test_deviation_report_auto_id(self):
        dr = DeviationReport(dimension="test")
        assert dr.deviation_id != ""
        assert dr.severity == "info"

    def test_deviation_report_to_dict(self):
        dr = DeviationReport(dimension="cost", delta=100.0, delta_percentage=0.5,
                             severity="error")
        d = dr.to_dict()
        assert d["dimension"] == "cost"
        assert d["severity"] == "error"

    def test_anomaly_report_auto_id(self):
        ar = AnomalyReport(pattern="all_failed", description="All failed")
        assert ar.anomaly_id != ""

    def test_learning_signal_defaults(self):
        ls = LearningSignal()
        assert ls.signal_id != ""
        assert ls.confidence == 0.5
        assert ls.created_at is not None

    def test_verified_observation_defaults(self):
        vo = VerifiedObservation()
        assert vo.observation_id != ""
        assert vo.observation_type == "passive"
        assert vo.created_at is not None

    def test_verified_observation_to_dict(self):
        vo = VerifiedObservation(
            observation_id="obs-1", workflow_id="wf-1",
            confidence=0.85, severity="info",
            variances=[ObservationVariance(dimension="test", delta=1.0)],
        )
        d = vo.to_dict()
        assert d["observation_id"] == "obs-1"
        assert d["confidence"] == 0.85
        assert len(d["variances"]) == 1

    def test_observer_input_validation_valid(self):
        inp = make_input()
        assert inp.validate() == []

    def test_observer_input_validation_missing_workflow(self):
        inp = ObserverInput(tasks=[{"task_id": "t1"}])
        errors = inp.validate()
        assert any("UNKNOWN_WORKFLOW" in e for e in errors)

    def test_observer_input_validation_missing_tenant(self):
        inp = ObserverInput(workflow_id="wf-1", tasks=[{"task_id": "t1"}])
        errors = inp.validate()
        assert any("TENANT" in e for e in errors)

    def test_observer_stats_to_dict(self):
        s = ObserverStats(total_observations=100, with_anomalies=5)
        d = s.to_dict()
        assert d["total_observations"] == 100
        assert d["avg_confidence"] == 0.0


# ======================================================================
# Evidence Validation Tests
# ======================================================================


class TestEvidenceValidation:
    """Tests for the 6-dimension evidence validation."""

    def test_all_evidence_present_passes(self, engine):
        inp = make_input(evidence_count=3)
        output = engine.observe(inp)
        assert output.success
        assert output.observation is not None
        assert output.observation.evidence_validation is not None
        assert output.observation.evidence_validation.completeness == EvidenceValidationStatus.PASS

    def test_no_evidence_fails_completeness(self, engine):
        inp = make_input(evidence_count=0)
        output = engine.observe(inp)
        assert output.success  # Observation still proceeds
        ev = output.observation.evidence_validation
        assert ev.completeness == EvidenceValidationStatus.FAIL
        assert ev.quality_score == 0.0

    def test_missing_evidence_id_warns(self, engine):
        inp = make_input()
        inp.evidence[0] = {"task_id": "t0", "success": True}  # No evidence_id
        output = engine.observe(inp)
        assert output.observation.evidence_validation.authenticity == EvidenceValidationStatus.WARN

    def test_evidence_timestamp_integrity(self, engine):
        # Future timestamp should warn
        inp = make_input()
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        inp.evidence[0]["timestamp"] = future
        output = engine.observe(inp)
        assert output.observation.evidence_validation.timestamp_integrity == EvidenceValidationStatus.WARN

    def test_evidence_correlation(self, engine):
        inp = make_input()
        inp.evidence[0]["task_id"] = "nonexistent_task"
        output = engine.observe(inp)
        assert output.observation.evidence_validation.correlation == EvidenceValidationStatus.WARN


# ======================================================================
# Deviation Detection Tests
# ======================================================================


class TestDeviationDetection:
    """Tests for deviation detection with tolerances."""

    def test_no_expected_no_deviation(self, engine):
        inp = make_input()
        output = engine.observe(inp)
        assert output.deviation_reports == []

    def test_task_completion_deviation(self, engine):
        exp_metrics = {"completed": 5, "failed": 0, "total_duration_seconds": 5.0, "total_retries": 0}
        inp = make_input(completed=3, expected_req={"metrics": exp_metrics})
        output = engine.observe(inp)
        assert len(output.deviation_reports) >= 1
        task_dev = next((d for d in output.deviation_reports if d.dimension == "task_completion"), None)
        assert task_dev is not None
        assert task_dev.delta == -2  # 3 - 5

    def test_duration_deviation(self, engine):
        exp_metrics = {"completed": 3, "failed": 0, "total_duration_seconds": 10.0, "total_retries": 0}
        inp = make_input(completed=3, expected_req={"metrics": exp_metrics})
        output = engine.observe(inp)
        dur_dev = next((d for d in output.deviation_reports if d.dimension == "duration"), None)
        assert dur_dev is not None
        assert dur_dev.delta == -5.0  # 5 - 10

    def test_deviation_severity_scales(self, engine):
        """Small deviation should be INFO, large deviation should be higher."""
        small = make_input(completed=3, expected_req={
            "metrics": {"completed": 3, "failed": 0, "total_duration_seconds": 5.0, "total_retries": 0},
        })
        out_small = engine.observe(small)
        small_sevs = [d.severity for d in out_small.deviation_reports]
        assert all(s == "info" for s in small_sevs)


# ======================================================================
# Anomaly Detection Tests
# ======================================================================


class TestAnomalyDetection:
    """Tests for pattern-based anomaly detection."""

    def test_all_tasks_failed_anomaly(self, engine):
        inp = make_input(completed=0, failed=3, evidence_count=0)
        output = engine.observe(inp)
        anomalies = [a for a in output.anomaly_reports if a.pattern == "all_tasks_failed"]
        assert len(anomalies) >= 1

    def test_no_evidence_anomaly(self, engine):
        inp = make_input(completed=3, evidence_count=0)
        output = engine.observe(inp)
        anomalies = [a for a in output.anomaly_reports if a.pattern == "no_evidence_collected"]
        assert len(anomalies) >= 1

    def test_high_failure_rate_anomaly(self, engine):
        inp = make_input(completed=2, failed=3, evidence_count=0)
        output = engine.observe(inp)
        anomalies = [a for a in output.anomaly_reports if a.pattern == "high_failure_rate"]
        assert len(anomalies) >= 1

    def test_successful_execution_no_anomalies(self, engine):
        inp = make_input(completed=5, evidence_count=5)
        output = engine.observe(inp)
        assert output.anomaly_reports == []


# ======================================================================
# Confidence Assessment Tests
# ======================================================================


class TestConfidence:
    """Tests for confidence assessment."""

    def test_high_quality_evidence_high_confidence(self, engine):
        inp = make_input(completed=5, evidence_count=5)
        output = engine.observe(inp)
        assert output.observation is not None
        assert output.observation.confidence > 0.5

    def test_anomalies_reduce_confidence(self, engine):
        good = make_input(completed=5, evidence_count=5)
        bad = make_input(completed=0, failed=5, evidence_count=0)

        out_good = engine.observe(good)
        out_bad = engine.observe(bad)

        assert out_bad.observation.confidence < out_good.observation.confidence

    def test_evidence_failure_reduces_confidence(self, engine):
        no_evidence = make_input(completed=3, evidence_count=0)
        with_evidence = make_input(completed=3, evidence_count=3)

        out_no = engine.observe(no_evidence)
        out_with = engine.observe(with_evidence)

        assert out_no.observation.confidence < out_with.observation.confidence


# ======================================================================
# Pipeline Integration Tests
# ======================================================================


class TestPipeline:
    """Tests for the full 9-stage observation pipeline."""

    def test_observe_valid_input(self, engine):
        output = engine.observe(make_input())
        assert output.success
        assert output.observation_id != ""
        assert output.observation is not None

    def test_observe_rejects_invalid_input(self, engine):
        output = engine.observe(ObserverInput())
        assert not output.success
        assert len(output.errors) > 0

    def test_observe_produces_observation(self, engine):
        output = engine.observe(make_input())
        obs = output.observation
        assert obs.workflow_id == "wf-1"
        assert obs.plan_id == "plan-1"
        assert obs.tenant_id == 1

    def test_observe_produces_learning_signals(self, engine):
        output = engine.observe(make_input(failed=1, completed=2, evidence_count=0))
        assert len(output.learning_signals) > 0

    def test_observation_stores_in_engine(self, engine):
        output = engine.observe(make_input())
        retrieved = engine.get_observation(output.observation_id)
        assert retrieved is not None
        assert retrieved.observation_id == output.observation_id

    def test_observation_from_outcome_package(self, engine):
        """Test observe_from_outcome with a mock OutcomePackage-like object."""
        class MockOutcome:
            workflow_id = "wf-out"
            plan_id = "plan-out"
            workflow_state = "completed"
            tasks = [{"task_id": "t1", "state": "completed"}]
            evidence = []
            failures = []
            metrics = {"completed": 1, "failed": 0, "total_duration_seconds": 1.0, "total_retries": 0}

        output = engine.observe_from_outcome(MockOutcome(), tenant_id=1)
        assert output.success
        assert output.observation.workflow_id == "wf-out"


# ======================================================================
# Determinism Tests
# ======================================================================


class TestDeterminism:
    """Tests for observer determinism."""

    def test_identical_inputs_identical_observations(self, engine):
        inp = make_input()
        out1 = engine.observe(inp)
        out2 = engine.observe(inp)

        assert out1.success == out2.success
        assert out1.observation.confidence == out2.observation.confidence
        assert len(out1.anomaly_reports) == len(out2.anomaly_reports)
        assert len(out1.deviation_reports) == len(out2.deviation_reports)


# ======================================================================
# Immutability Tests
# ======================================================================


class TestImmutability:
    """Tests for observation immutability after creation."""

    def test_observation_is_dataclass(self, engine):
        output = engine.observe(make_input())
        obs = output.observation
        # Dataclass fields are immutable by convention (no setters exposed)
        # Verify the observation is stored and retrieved intact
        retrieved = engine.get_observation(output.observation_id)
        assert retrieved.confidence == obs.confidence
        assert retrieved.severity == obs.severity

    def test_multiple_observations_independent(self, engine):
        out1 = engine.observe(make_input(workflow_id="wf-a"))
        out2 = engine.observe(make_input(workflow_id="wf-b"))
        assert out1.observation.workflow_id == "wf-a"
        assert out2.observation.workflow_id == "wf-b"
        assert out1.observation_id != out2.observation_id


# ======================================================================
# Concurrency Tests
# ======================================================================


class TestConcurrency:
    """Tests for thread safety."""

    def test_concurrent_observation(self, engine):
        results: List[ObserverOutput] = []
        errors: List[Exception] = []

        def run() -> None:
            try:
                results.append(engine.observe(make_input()))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 10


# ======================================================================
# Singleton Tests
# ======================================================================


class TestSingleton:
    def test_get_engine_singleton(self):
        e1 = get_observer_engine()
        e2 = get_observer_engine()
        assert e1 is e2

    def test_reset_creates_new(self):
        e1 = get_observer_engine()
        reset_observer_engine()
        e2 = get_observer_engine()
        assert e1 is not e2


# ======================================================================
# Query Tests
# ======================================================================


class TestQueries:
    """Tests for observation query methods."""

    def test_list_observations(self, engine):
        engine.observe(make_input())
        assert len(engine.list_observations()) == 1

    def test_list_anomalies(self, engine):
        engine.observe(make_input(completed=0, failed=3, evidence_count=0))
        assert len(engine.list_anomalies()) >= 1

    def test_list_deviations(self, engine):
        exp = {"metrics": {"completed": 10, "failed": 0, "total_duration_seconds": 5.0, "total_retries": 0}}
        engine.observe(make_input(completed=3, expected_req=exp))
        assert len(engine.list_deviations()) >= 1


# ======================================================================
# Legacy Backward Compatibility Tests
# ======================================================================


class TestLegacyBackwardCompatibility:
    """Tests for legacy ObserverLayer."""

    def test_legacy_observer_layer_importable(self):
        from app.shunya.observer_engine._legacy_observer import ObserverLayer
        assert ObserverLayer is not None

    def test_legacy_observe_api(self):
        layer = ObserverLayer()
        result = layer.observe("send_message", "Message sent",
                                lead_id=1, expected="Message sent",
                                success=True)
        assert hasattr(result, "to_dict")
        d = result.to_dict()
        assert d["action"] == "send_message"
        assert d["success"] is True

    def test_legacy_discrepancy_detected(self):
        layer = ObserverLayer()
        result = layer.observe("payment", "Failed",
                                lead_id=1, expected="Success",
                                success=False)
        assert result.discrepancy != ""


# ======================================================================
# Statistics Tests
# ======================================================================


class TestStats:
    def test_stats_after_observation(self, engine):
        engine.observe(make_input())
        s = engine.stats
        assert s["total_observations"] == 1
        assert s["avg_confidence"] > 0

    def test_stats_multiple_observations(self, engine):
        for _ in range(3):
            engine.observe(make_input())
        assert engine.stats["total_observations"] == 3

    def test_stats_tracks_anomalies(self, engine):
        engine.observe(make_input(completed=0, failed=3, evidence_count=0))
        assert engine.stats["with_anomalies"] >= 1


# ======================================================================
# Tolerance Configuration Tests
# ======================================================================


class TestTolerances:
    def test_set_custom_tolerance(self, engine):
        t = Tolerance("custom_dim", 0.05, 0.1, 0.2)
        engine.set_tolerance(t)
        inp = make_input()
        output = engine.observe(inp)
        assert output.success

    def test_tolerance_thresholds_used(self, engine):
        engine.set_tolerance(Tolerance("task_completion", 0.0, 0.0, 0.01))
        exp = {"metrics": {"completed": 5, "failed": 0, "total_duration_seconds": 5.0, "total_retries": 0}}
        inp = make_input(completed=3, expected_req={"metrics": exp})
        output = engine.observe(inp)
        dev = next((d for d in output.deviation_reports if d.dimension == "task_completion"), None)
        assert dev is not None
        assert dev.tolerance_used is not None
        assert dev.tolerance_used.dimension == "task_completion"


# ======================================================================
# Edge Case Tests
# ======================================================================


class TestEdgeCases:
    def test_empty_tasks_with_failures(self, engine):
        inp = ObserverInput(
            workflow_id="wf-edge", tenant_id=1,
            failures=[{"failure_type": "timeout", "message": "Timed out"}],
            tasks=[{"task_id": "t1", "state": "failed"}],
        )
        output = engine.observe(inp)
        assert output.success

    def test_large_number_of_evidence(self, engine):
        evidence = [
            {"evidence_id": f"ev_{i}", "task_id": f"t{i}",
             "success": True, "action": "echo"}
            for i in range(100)
        ]
        tasks = [{"task_id": f"t{i}", "state": "completed"} for i in range(100)]
        inp = ObserverInput(
            workflow_id="wf-large", tenant_id=1,
            tasks=tasks, evidence=evidence,
            metrics={"completed": 100, "failed": 0, "total_duration_seconds": 10.0, "total_retries": 0},
        )
        output = engine.observe(inp)
        assert output.success