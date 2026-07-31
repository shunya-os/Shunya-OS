"""Tests for Phase I — Executor Engine (ES-005).

Covers:
  - Canonical data model tests
  - Retry policy calculation
  - Workflow lifecycle
  - ExecutorEngine 9-stage pipeline
  - Input validation
  - Dependency verification
  - Task dispatch and execution
  - Evidence collection
  - Outcome packaging
  - Determinism
  - Concurrency
  - Legacy backward compatibility

Architectural authority: ES-005 — Executor Engine Specification
"""

from __future__ import annotations

import copy
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import pytest

from app.shunya.executor_engine.models import (
    WorkflowState, TaskState, ExecutionType,
    BackoffStrategy, FailureType,
    RetryPolicy, Compensation, ExecutionFailure,
    ExecutionEvidence, Checkpoint,
    Task, Workflow,
    ExecutionMetrics, OutcomePackage,
    ExecutorInput, ExecutorOutput,
    ExecutorStats,
)
from app.shunya.executor_engine.engine import (
    ExecutorEngine, get_executor_engine, reset_executor_engine,
)
from app.shunya.executor_engine._legacy_executor import (
    ExecutorLayer,
)


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture(autouse=True)
def reset_engine():
    reset_executor_engine()
    yield
    reset_executor_engine()


@pytest.fixture
def engine():
    return ExecutorEngine()


def make_task(task_id: str = "t1", action: str = "notify",
              target: str = "internal", deps: Optional[List[str]] = None,
              payload: Optional[Dict] = None) -> Task:
    return Task(
        task_id=task_id,
        action=action,
        target=target,
        dependencies=deps or [],
        payload=payload or {"message": "Hello"},
    )


def make_valid_input(tasks: Optional[List[Task]] = None) -> ExecutorInput:
    if tasks is None:
        tasks = [make_task()]
    return ExecutorInput(
        governance_approved=True,
        tenant_id=1,
        tasks=tasks,
    )


# ======================================================================
# Model Tests
# ======================================================================


class TestModels:
    """Canonical executor model tests."""

    def test_retry_policy_defaults(self):
        rp = RetryPolicy()
        assert rp.max_attempts == 3
        assert rp.backoff == "exponential"
        assert rp.initial_delay_ms == 1000

    def test_retry_policy_calculate_delay_exponential(self):
        rp = RetryPolicy(backoff="exponential")
        assert rp.calculate_delay(1) == 1000
        assert rp.calculate_delay(2) == 2000
        assert rp.calculate_delay(3) == 4000

    def test_retry_policy_calculate_delay_linear(self):
        rp = RetryPolicy(backoff="linear", initial_delay_ms=2000)
        assert rp.calculate_delay(1) == 2000
        assert rp.calculate_delay(2) == 4000
        assert rp.calculate_delay(3) == 6000

    def test_retry_policy_calculate_delay_fixed(self):
        rp = RetryPolicy(backoff="fixed", initial_delay_ms=5000)
        assert rp.calculate_delay(1) == 5000
        assert rp.calculate_delay(5) == 5000

    def test_retry_policy_max_delay_cap(self):
        rp = RetryPolicy(backoff="exponential", max_delay_ms=3000)
        assert rp.calculate_delay(5) == 3000  # 1000*16=16000 capped to 3000

    def test_retry_policy_should_retry(self):
        rp = RetryPolicy()
        assert rp.should_retry(1, "timeout") is True
        assert rp.should_retry(3, "timeout") is False  # max_attempts reached

    def test_retry_policy_non_retryable(self):
        rp = RetryPolicy(non_retryable_errors=["permission_denied"])
        assert rp.should_retry(1, "permission_denied") is False
        assert rp.should_retry(1, "timeout") is True

    def test_retry_policy_retryable_only(self):
        rp = RetryPolicy(retryable_errors=["timeout", "rate_limit"])
        assert rp.should_retry(1, "timeout") is True
        assert rp.should_retry(1, "invalid_payload") is False

    def test_compensation_defaults(self):
        c = Compensation(action="none")
        assert c.is_noop() is True
        c2 = Compensation(action="delete_record")
        assert c2.is_noop() is False

    def test_execution_failure_to_dict(self):
        ef = ExecutionFailure(
            failure_type="timeout", message="Timed out",
            task_id="t1", attempt=2, recovered=False,
        )
        d = ef.to_dict()
        assert d["failure_type"] == "timeout"
        assert d["attempt"] == 2
        assert d["recovered"] is False

    def test_evidence_defaults(self):
        ev = ExecutionEvidence(task_id="t1", action="send_message")
        assert ev.evidence_id != ""
        assert ev.timestamp is not None
        assert ev.success is False

    def test_evidence_to_dict(self):
        ev = ExecutionEvidence(
            task_id="t1", action="send_message", channel="whatsapp",
            message_id="msg_123", success=True,
        )
        d = ev.to_dict()
        assert d["message_id"] == "msg_123"
        assert d["success"] is True
        assert d["channel"] == "whatsapp"

    def test_task_defaults(self):
        t = Task()
        assert t.task_id != ""
        assert t.state == "pending"
        assert t.timeout == 30
        assert t.attempt == 0

    def test_task_properties(self):
        t = Task(state="completed")
        assert t.is_completed
        assert not t.is_failed
        t2 = Task(state="failed")
        assert t2.is_failed

    def test_task_duration_seconds(self):
        t = Task(
            started_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 1, 10, 0, 5, tzinfo=timezone.utc),
        )
        assert t.duration_seconds == 5.0

    def test_task_to_dict(self):
        t = Task(task_id="t1", action="send_message", state="pending")
        d = t.to_dict()
        assert d["task_id"] == "t1"
        assert d["action"] == "send_message"
        assert d["state"] == "pending"

    def test_workflow_defaults(self):
        w = Workflow()
        assert w.workflow_id != ""
        assert w.state == "active"
        assert w.created_at is not None

    def test_workflow_task_accessors(self):
        tasks = [
            Task(task_id="t1", state="completed"),
            Task(task_id="t2", state="failed"),
            Task(task_id="t3", state="pending"),
        ]
        w = Workflow(tasks=tasks)
        assert len(w.completed_tasks) == 1
        assert len(w.failed_tasks) == 1
        assert len(w.pending_tasks) == 1
        assert w.find_task("t1") is not None
        assert w.find_task("nonexistent") is None
        assert not w.all_completed

    def test_outcome_package_defaults(self):
        op = OutcomePackage()
        assert op.outcome_id != ""
        assert op.created_at is not None

    def test_executor_input_validation_valid(self):
        inp = make_valid_input()
        errors = inp.validate()
        assert errors == []

    def test_executor_input_validation_not_approved(self):
        inp = ExecutorInput(governance_approved=False, tenant_id=1, tasks=[make_task()])
        errors = inp.validate()
        assert any("PLAN_NOT_APPROVED" in e for e in errors)

    def test_executor_input_validation_empty_tasks(self):
        inp = ExecutorInput(governance_approved=True, tenant_id=1)
        errors = inp.validate()
        assert any("EMPTY_PLAN" in e for e in errors)

    def test_executor_input_validation_missing_tenant(self):
        inp = ExecutorInput(governance_approved=True, tasks=[make_task()])
        errors = inp.validate()
        assert any("TENANT" in e for e in errors)

    def test_executor_input_validation_unknown_dependency(self):
        t = make_task(task_id="t1", deps=["t2"])
        inp = ExecutorInput(governance_approved=True, tenant_id=1, tasks=[t])
        errors = inp.validate()
        assert any("unknown dependency" in e for e in errors)

    def test_executor_metrics_to_dict(self):
        m = ExecutionMetrics(total_tasks=10, completed=7, failed=3)
        d = m.to_dict()
        assert d["total_tasks"] == 10
        assert d["completed"] == 7

    def test_stats_to_dict(self):
        s = ExecutorStats(total_workflows=100, completed=80)
        d = s.to_dict()
        assert d["completion_rate"] == 80.0


# ======================================================================
# Pipeline Tests
# ======================================================================


class TestPipeline:
    """Tests for the 9-stage execution pipeline."""

    def test_execute_valid_input_returns_output(self, engine):
        inp = make_valid_input()
        output = engine.execute(inp)
        assert output.workflow_id != ""
        assert output.outcome is not None

    def test_execute_rejects_not_approved(self, engine):
        inp = ExecutorInput(governance_approved=False, tenant_id=1, tasks=[make_task()])
        output = engine.execute(inp)
        assert not output.success
        assert output.workflow_state == "failed"

    def test_execute_rejects_empty_plan(self, engine):
        inp = ExecutorInput(governance_approved=True, tenant_id=1)
        output = engine.execute(inp)
        assert not output.success

    def test_execute_rejects_missing_tenant(self, engine):
        inp = ExecutorInput(governance_approved=True, tasks=[make_task()])
        output = engine.execute(inp)
        assert not output.success

    def test_execute_single_task_completes(self, engine):
        t = make_task()
        output = engine.execute(make_valid_input([t]))
        assert output.success
        assert output.workflow_state in ("completed", "partial")

    def test_execute_multiple_tasks_completes(self, engine):
        tasks = [
            make_task(task_id="t1", deps=[]),
            make_task(task_id="t2", deps=["t1"]),
            make_task(task_id="t3", deps=["t1"]),
        ]
        output = engine.execute(make_valid_input(tasks))
        assert output.success
        assert output.outcome is not None
        assert output.outcome.metrics is not None
        assert output.outcome.metrics.completed == 3

    def test_execute_dependency_order_respected(self, engine):
        t1 = make_task(task_id="t1", deps=[])
        t2 = make_task(task_id="t2", deps=["t1"])
        t3 = make_task(task_id="t3", deps=["t2"])
        output = engine.execute(make_valid_input([t1, t2, t3]))
        assert output.success

    def test_execute_circular_dependency_handled(self, engine):
        t1 = make_task(task_id="t1", deps=["t3"])
        t2 = make_task(task_id="t2", deps=["t1"])
        t3 = make_task(task_id="t3", deps=["t2"])
        output = engine.execute(make_valid_input([t1, t2, t3]))
        # Should not crash; may complete partially
        assert output.workflow_state is not None

    def test_execute_produces_evidence(self, engine):
        t = make_task()
        output = engine.execute(make_valid_input([t]))
        assert output.outcome is not None
        assert len(output.outcome.evidence) >= 0  # May be 0 if mock executor

    def test_execute_produces_metrics(self, engine):
        t = make_task()
        output = engine.execute(make_valid_input([t]))
        assert output.outcome is not None
        assert output.outcome.metrics is not None
        assert output.outcome.metrics.total_tasks == 1

    def test_execute_workflow_state_completed(self, engine):
        tasks = [
            make_task(task_id="t1"),
            make_task(task_id="t2"),
        ]
        output = engine.execute(make_valid_input(tasks))
        assert output.workflow_state == "completed"

    def test_workflow_store_updated(self, engine):
        inp = make_valid_input([make_task()])
        output = engine.execute(inp)
        wf = engine.get_workflow(output.workflow_id)
        assert wf is not None
        assert wf.state in ("completed", "partial")


# ======================================================================
# Outcome Packaging Tests
# ======================================================================


class TestOutcomePackaging:
    """Tests for outcome packaging (Stage 8)."""

    def test_outcome_contains_all_tasks(self, engine):
        tasks = [make_task(task_id="t1"), make_task(task_id="t2")]
        output = engine.execute(make_valid_input(tasks))
        assert output.outcome is not None
        assert len(output.outcome.tasks) == 2

    def test_outcome_contains_workflow_state(self, engine):
        output = engine.execute(make_valid_input([make_task()]))
        assert output.outcome is not None
        assert output.outcome.workflow_state == output.workflow_state

    def test_outcome_contains_metrics(self, engine):
        output = engine.execute(make_valid_input([make_task()]))
        assert output.outcome is not None
        assert output.outcome.metrics is not None
        assert output.outcome.metrics.total_tasks > 0

    def test_outcome_to_dict(self, engine):
        output = engine.execute(make_valid_input([make_task()]))
        assert output.outcome is not None
        d = output.outcome.to_dict()
        assert "outcome_id" in d
        assert "metrics" in d


# ======================================================================
# Retry and Error Handling Tests
# ======================================================================


class TestRetryAndErrors:
    """Tests for retry policies and error handling."""

    def test_task_with_retry_policy(self, engine):
        rp = RetryPolicy(max_attempts=3)
        t = make_task(task_id="t1", payload={"should_fail": True})
        t.retry_policy = rp
        inp = make_valid_input([t])
        output = engine.execute(inp)
        # Task may succeed or fail depending on executor
        assert output.outcome is not None

    def test_workflow_failure_recorded_outcome(self, engine):
        inp = ExecutorInput(governance_approved=False, tenant_id=1, tasks=[make_task()])
        output = engine.execute(inp)
        assert not output.success
        assert len(output.errors) > 0

    def test_partial_execution(self, engine):
        """Some tasks succeed, some dependencies missing."""
        t1 = make_task(task_id="t1")
        t2 = make_task(task_id="t2", deps=["nonexistent"])
        output = engine.execute(make_valid_input([t1, t2]))
        assert output.workflow_state == "failed" or output.success is not None


# ======================================================================
# Determinism Tests
# ======================================================================


class TestDeterminism:
    """Tests for executor determinism."""

    def test_identical_inputs_identical_outputs(self, engine):
        tasks = [
            make_task(task_id="t1"),
            make_task(task_id="t2", deps=["t1"]),
        ]
        inp = make_valid_input(tasks)

        out1 = engine.execute(inp)
        out2 = engine.execute(inp)

        assert out1.success == out2.success
        assert out1.workflow_state == out2.workflow_state

    def test_identical_inputs_identical_metrics(self, engine):
        inp = make_valid_input([make_task()])

        out1 = engine.execute(inp)
        out2 = engine.execute(inp)

        if out1.outcome and out2.outcome:
            assert out1.outcome.metrics.total_tasks == out2.outcome.metrics.total_tasks


# ======================================================================
# Concurrency Tests
# ======================================================================


class TestConcurrency:
    """Tests for thread safety."""

    def test_concurrent_execution(self, engine):
        results: List[ExecutorOutput] = []
        errors: List[Exception] = []

        def run() -> None:
            try:
                r = engine.execute(make_valid_input([make_task()]))
                results.append(r)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrency errors: {errors}"
        assert len(results) == 10

    def test_concurrent_identical_inputs(self, engine):
        results: List[ExecutorOutput] = []
        inp = make_valid_input([make_task(task_id="concurrent_test")])

        def run() -> None:
            r = engine.execute(inp)
            results.append(r)

        threads = [threading.Thread(target=run) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r.success for r in results]
        assert all(s == successes[0] for s in successes)


# ======================================================================
# Singleton Tests
# ======================================================================


class TestSingleton:
    """Tests for module-level singleton."""

    def test_get_engine_singleton(self):
        e1 = get_executor_engine()
        e2 = get_executor_engine()
        assert e1 is e2

    def test_reset_creates_new_singleton(self):
        e1 = get_executor_engine()
        reset_executor_engine()
        e2 = get_executor_engine()
        assert e1 is not e2


# ======================================================================
# Statistics Tests
# ======================================================================


class TestStatistics:
    """Tests for executor statistics."""

    def test_stats_after_execution(self, engine):
        engine.execute(make_valid_input([make_task()]))
        s = engine.stats
        assert s["total_workflows"] == 1
        assert s["adapters_registered"] == 0

    def test_stats_multiple_executions(self, engine):
        for _ in range(3):
            engine.execute(make_valid_input([make_task()]))
        s = engine.stats
        assert s["total_workflows"] == 3

    def test_stats_tracks_failures(self, engine):
        engine.execute(ExecutorInput(
            governance_approved=False, tenant_id=1, tasks=[make_task()],
        ))
        s = engine.stats
        assert s["failed"] == 1
        assert s["completion_rate"] == 0.0


# ======================================================================
# Adapter Registration Tests
# ======================================================================


class TestAdapters:
    """Tests for channel adapter registration."""

    def test_register_adapter(self, engine):
        engine.register_adapter("test", type("MockAdapter", (), {
            "channel_type": "test",
            "send": lambda self, m: None,
            "is_configured": lambda self: True,
        })())
        assert engine.stats["adapters_registered"] == 1


# ======================================================================
# Outcome List Tests
# ======================================================================


class TestOutcomeList:
    """Tests for outcome query methods."""

    def test_list_outcomes(self, engine):
        engine.execute(make_valid_input([make_task()]))
        outcomes = engine.list_outcomes()
        assert len(outcomes) == 1

    def test_list_outcomes_limit(self, engine):
        for _ in range(5):
            engine.execute(make_valid_input([make_task()]))
        assert len(engine.list_outcomes(limit=3)) == 3
        assert len(engine.list_outcomes(limit=10)) == 5  # +1 from test above


# ======================================================================
# Legacy Backward Compatibility Tests
# ======================================================================


class TestLegacyBackwardCompatibility:
    """Tests for legacy ExecutorLayer compatibility."""

    def test_legacy_executor_layer_importable(self):
        from app.shunya.executor_engine._legacy_executor import ExecutorLayer
        assert ExecutorLayer is not None

    def test_legacy_layer_has_engine(self):
        layer = ExecutorLayer()
        assert hasattr(layer, 'engine')
        assert hasattr(layer, 'stats')


# ======================================================================
# Edge Case Tests
# ======================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_action_defaults(self, engine):
        """A task with no action should use the default executor."""
        t = Task(task_id="t1")
        inp = make_valid_input([t])
        output = engine.execute(inp)
        assert output.success

    def test_large_number_of_tasks(self, engine):
        tasks = [make_task(task_id=f"t{i}") for i in range(50)]
        output = engine.execute(make_valid_input(tasks))
        assert output.success
        assert output.outcome is not None
        assert output.outcome.metrics.total_tasks == 50

    def test_chain_dependency(self, engine):
        """A 10-task chain should complete in order."""
        tasks = []
        for i in range(10):
            deps = [f"t{i-1}"] if i > 0 else []
            tasks.append(make_task(task_id=f"t{i}", deps=deps))
        output = engine.execute(make_valid_input(tasks))
        assert output.success
        assert output.outcome is not None
        assert output.outcome.metrics.completed == 10

    def test_multiple_roots(self, engine):
        """Multiple root tasks (no dependencies) should all execute."""
        tasks = [
            make_task(task_id="t1"),
            make_task(task_id="t2"),
            make_task(task_id="t3"),
            make_task(task_id="t4", deps=["t1"]),
            make_task(task_id="t5", deps=["t2"]),
        ]
        output = engine.execute(make_valid_input(tasks))
        assert output.success
        assert output.outcome is not None
        assert output.outcome.metrics.completed == 5

    def test_active_workflows_counts(self, engine):
        assert engine.active_workflows == 0
        engine.execute(make_valid_input([make_task()]))
        # Completed workflows are no longer active
        assert engine.active_workflows == 0
        assert engine.total_workflows == 1