"""Tests for the Canonical Runtime Pipeline and OS Kernel (Phase L)."""

import pytest

from core.os import MockRuntime, ShunyaOS, get_os, reset_os
from core.runtime_pipeline import (
    CANONICAL_STAGES,
    PipelineContext,
    PipelineStage,
    RuntimePipeline,
    StepRecord,
)

# ======================================================================
# Pipeline Stage Enum
# ======================================================================


class TestPipelineStage:
    def test_enum_values(self) -> None:
        assert PipelineStage.INTENT_RESOLUTION.value == "intent_resolution"
        assert PipelineStage.WORKSPACE_UPDATE.value == "workspace_update"

    def test_canonical_order(self) -> None:
        assert len(CANONICAL_STAGES) == 11
        assert CANONICAL_STAGES[0] == PipelineStage.INTENT_RESOLUTION
        assert CANONICAL_STAGES[-1] == PipelineStage.WORKSPACE_UPDATE


# ======================================================================
# Pipeline Context
# ======================================================================


class TestPipelineContext:
    def test_auto_id_and_timestamp(self) -> None:
        ctx = PipelineContext(intent="test_intent")
        assert ctx.intent_id != ""
        assert ctx.started_at != ""
        assert ctx.state == "pending"
        assert ctx.trace == []

    def test_explicit_values(self) -> None:
        ctx = PipelineContext(
            intent_id="custom-id",
            intent="talk_to_customer",
            identity_id="id-1",
            object_id="obj-42",
        )
        assert ctx.intent_id == "custom-id"
        assert ctx.identity_id == "id-1"

    def test_status_summary(self) -> None:
        ctx = PipelineContext(intent="test")
        ctx.trace.append(StepRecord(stage="s1", runtime="r1", status="completed",
                                     started_at="now", completed_at="then"))
        ctx.trace.append(StepRecord(stage="s2", runtime="r2", status="noop",
                                     started_at="now", completed_at="then"))
        summary = ctx.status_summary
        assert summary["s1"] == "completed"
        assert summary["s2"] == "noop"

    def test_total_duration(self) -> None:
        ctx = PipelineContext(intent="test")
        ctx.trace.append(StepRecord(stage="s1", runtime="r1", status="completed",
                                     started_at="now", completed_at="then", duration_ms=10.0))
        ctx.trace.append(StepRecord(stage="s2", runtime="r2", status="completed",
                                     started_at="now", completed_at="then", duration_ms=20.0))
        assert ctx.total_duration_ms == 30.0


# ======================================================================
# Runtime Pipeline
# ======================================================================


class TestRuntimePipeline:
    def test_initial_state(self) -> None:
        pipeline = RuntimePipeline()
        h = pipeline.health_check()
        assert h["status"] == "healthy"
        assert h["runtime_count"] == 0

    def test_register_runtime(self) -> None:
        pipeline = RuntimePipeline()
        runtime = MockRuntime(name="test", stages=[PipelineStage.INTENT_RESOLUTION])
        pipeline.register(runtime)
        assert "test" in pipeline.list_runtimes()["intent_resolution"]

    def test_unregister_runtime(self) -> None:
        pipeline = RuntimePipeline()
        runtime = MockRuntime(name="test", stages=[PipelineStage.INTENT_RESOLUTION])
        pipeline.register(runtime)
        pipeline.unregister("test")
        assert pipeline.list_runtimes() == {}

    def test_execute_empty_pipeline(self) -> None:
        pipeline = RuntimePipeline()
        ctx = pipeline.execute("test_intent")
        assert ctx.state == "completed"
        assert len(ctx.trace) == 11  # all 11 stages recorded
        # All should be noop since no runtimes registered
        for record in ctx.trace:
            assert record.status == "noop"

    def test_execute_with_mock_runtime(self) -> None:
        pipeline = RuntimePipeline()
        runtime = MockRuntime(
            name="test_runtime",
            stages=[PipelineStage.INTENT_RESOLUTION, PipelineStage.IDENTITY_RESOLUTION],
        )
        pipeline.register(runtime)
        ctx = pipeline.execute("test_intent", parameters={"key": "val"})
        assert ctx.state == "completed"
        assert ctx.intent == "test_intent"
        assert ctx.parameters == {"key": "val"}
        # Should have 11 stages, 2 handled, 9 noop
        handled = [s for s in ctx.trace if s.status == "completed"]
        noop = [s for s in ctx.trace if s.status == "noop"]
        assert len(handled) == 2
        assert len(noop) == 9

    def test_execute_identity_and_object(self) -> None:
        pipeline = RuntimePipeline()
        ctx = pipeline.execute("test", identity_id="id-1", object_id="obj-1")
        assert ctx.identity_id == "id-1"
        assert ctx.object_id == "obj-1"

    def test_health_with_runtimes(self) -> None:
        pipeline = RuntimePipeline()
        runtime = MockRuntime(name="healthy", stages=[PipelineStage.INTENT_RESOLUTION])
        pipeline.register(runtime)
        h = pipeline.health_check()
        assert h["status"] == "healthy"
        assert h["runtime_count"] == 1

    def test_mock_runtime_process(self) -> None:
        runtime = MockRuntime(name="test", stages=[PipelineStage.INTENT_RESOLUTION])
        ctx = PipelineContext(intent="test")
        result = runtime.process(ctx, PipelineStage.INTENT_RESOLUTION)
        assert result["status"] == "noop"
        assert result["runtime"] == "test"

    def test_mock_runtime_health(self) -> None:
        runtime = MockRuntime(name="test")
        h = runtime.health_check()
        assert h["status"] == "healthy"
        assert h["runtime"] == "test"


# ======================================================================
# OS Kernel
# ======================================================================


class TestShunyaOS:
    def setup_method(self) -> None:
        reset_os()

    def test_get_os_singleton(self) -> None:
        os1 = get_os()
        os2 = get_os()
        assert os1 is os2

    def test_reset_os(self) -> None:
        os1 = get_os()
        reset_os()
        os2 = get_os()
        assert os1 is not os2

    def test_bootstrap_creates_all_mocks(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        h = os.health_check()
        assert h["bootstrapped"] is True
        assert h["runtime_count"] == 10  # 10 mock runtimes

    def test_process_intent_with_bootstrap(self) -> None:
        os = ShunyaOS()
        ctx = os.process_intent("talk_to_customer", {"name": "Alice"})
        assert ctx.state == "completed"
        assert ctx.intent == "talk_to_customer"
        assert ctx.parameters == {"name": "Alice"}
        assert len(ctx.trace) == 11

    def test_health_before_bootstrap(self) -> None:
        os = ShunyaOS()
        h = os.health_check()
        assert h["status"] == "not_bootstrapped"

    def test_health_after_bootstrap(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        h = os.health_check()
        assert h["status"] == "healthy"
        assert h["pipeline"]["runtime_count"] == 10

    def test_shutdown(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        assert os.health_check()["status"] == "healthy"
        os.shutdown()
        assert os.health_check()["status"] == "not_bootstrapped"

    def test_replace_runtime(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        # Replace a mock with a real runtime implementation
        real = MockRuntime(name="kernel", stages=[PipelineStage.INTENT_RESOLUTION])
        os.replace_runtime("kernel", real)
        assert os.get_runtime("kernel") is real

    def test_replace_runtime_invalid_name(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        with pytest.raises(ValueError, match="not registered"):
            os.replace_runtime("nonexistent", MockRuntime(name="x"))

    def test_process_intent_auto_bootstrap(self) -> None:
        """process_intent should auto-bootstrap if not already bootstrapped."""
        os = ShunyaOS()
        ctx = os.process_intent("test")
        assert ctx.state == "completed"
        assert os.health_check()["bootstrapped"] is True

    def test_initial_health_unbootstrapped(self) -> None:
        os = ShunyaOS()
        h = os.health_check()
        assert h["status"] == "not_bootstrapped"

    def test_get_runtime_returns_none_for_missing(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        assert os.get_runtime("nonexistent") is None

    def test_process_intent_preserves_identity_id(self) -> None:
        os = ShunyaOS()
        ctx = os.process_intent("test", identity_id="identity-abc", object_id="object-xyz")
        assert ctx.identity_id == "identity-abc"
        assert ctx.object_id == "object-xyz"

    def test_runtimes_property(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        rt = os.runtimes
        assert "kernel" in rt
        assert len(rt) == 10