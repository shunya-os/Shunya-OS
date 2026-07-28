"""Tests for the Kernel Runtime Adapter (Directive L-01)."""

import pytest

from core.kernel_runtime import KernelRuntime
from core.os import ShunyaOS, reset_os
from core.runtime_pipeline import (
    PipelineContext,
    PipelineStage,
    RuntimePipeline,
)

# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def kernel() -> KernelRuntime:
    return KernelRuntime()


@pytest.fixture
def pipeline() -> RuntimePipeline:
    p = RuntimePipeline()
    p.register(KernelRuntime())
    return p


# ======================================================================
# KernelRuntime — contract
# ======================================================================


class TestKernelRuntimeContract:
    def test_runtime_interface(self, kernel: KernelRuntime) -> None:
        assert kernel.name == "kernel"
        assert len(kernel.stages) == 2
        assert PipelineStage.INTENT_RESOLUTION in kernel.stages
        assert PipelineStage.OBJECT_RESOLUTION in kernel.stages

    def test_health_check(self, kernel: KernelRuntime) -> None:
        h = kernel.health_check()
        assert h["status"] == "healthy"
        assert h["runtime"] == "kernel"
        assert h["object_count"] == 0
        assert len(h["supported_intents"]) >= 5

    def test_health_check_after_object_creation(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(
            intent="create_object",
            parameters={"name": "Test", "object_type": "doc"},
            identity_id="user-1",
        )
        kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        kernel.process(ctx, PipelineStage.OBJECT_RESOLUTION)
        h = kernel.health_check()
        assert h["object_count"] == 1


# ======================================================================
# INTENT_RESOLUTION stage
# ======================================================================


class TestIntentResolution:
    def test_known_intent(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(
            intent="create_object",
            parameters={"name": "Alice", "object_type": "person"},
        )
        result = kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["valid"] is True
        assert result["intent_type"] == "object"

    def test_unknown_intent(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(intent="fly_to_moon")
        result = kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["valid"] is False
        assert "suggested_intents" in result

    def test_missing_required_params(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(
            intent="create_object",
            parameters={},  # missing name and object_type
        )
        result = kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["valid"] is False
        assert "missing" in result["message"].lower()

    def test_sign_in_intent(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "user@co.com"},
        )
        result = kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["intent_type"] == "auth"

    def test_talk_to_customer_intent(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(intent="talk_to_customer")
        result = kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["intent_type"] == "conversation"

    def test_noop_for_unknown_stage(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(intent="test")
        result = kernel.process(ctx, PipelineStage.MEMORY_UPDATE)
        assert result["status"] == "noop"


# ======================================================================
# OBJECT_RESOLUTION stage
# ======================================================================


class TestObjectResolution:
    def test_create_object(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(
            intent="create_object",
            parameters={"name": "Alice", "object_type": "person"},
            identity_id="user-1",
        )
        # Must resolve intent first
        kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        result = kernel.process(ctx, PipelineStage.OBJECT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is True
        assert result["created"] is True
        assert result["object_id"] is not None
        assert ctx.object_id == result["object_id"]  # pipeline context updated

    def test_create_object_sets_correct_fields(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(
            intent="create_object",
            parameters={
                "name": "Project Alpha",
                "object_type": "project",
                "description": "A test project",
                "tags": ["test", "demo"],
            },
            identity_id="user-42",
        )
        kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        kernel.process(ctx, PipelineStage.OBJECT_RESOLUTION)
        obj = kernel.get_object(ctx.object_id)
        assert obj is not None
        assert obj.name == "Project Alpha"
        assert obj.object_type == "project"
        assert obj.description == "A test project"
        assert "test" in (obj.tags or [])

    def test_resolve_existing_object(self, kernel: KernelRuntime) -> None:
        # Create object
        create_ctx = PipelineContext(
            intent="create_object",
            parameters={"name": "Bob", "object_type": "person"},
            identity_id="user-1",
        )
        kernel.process(create_ctx, PipelineStage.INTENT_RESOLUTION)
        kernel.process(create_ctx, PipelineStage.OBJECT_RESOLUTION)
        created_id = create_ctx.object_id

        # View it
        view_ctx = PipelineContext(
            intent="view_object",
            object_id=created_id,
        )
        kernel.process(view_ctx, PipelineStage.INTENT_RESOLUTION)
        result = kernel.process(view_ctx, PipelineStage.OBJECT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is True
        assert result["object_id"] == created_id

    def test_resolve_nonexistent_object(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(
            intent="view_object",
            object_id="nonexistent",
        )
        kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        result = kernel.process(ctx, PipelineStage.OBJECT_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is False

    def test_noop_for_non_object_intent(self, kernel: KernelRuntime) -> None:
        ctx = PipelineContext(intent="sign_in", parameters={"email": "a@b.com"})
        kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
        result = kernel.process(ctx, PipelineStage.OBJECT_RESOLUTION)
        assert result["status"] == "noop"

    def test_multiple_objects_independent(self, kernel: KernelRuntime) -> None:
        ids = []
        for i in range(3):
            ctx = PipelineContext(
                intent="create_object",
                parameters={"name": f"Obj-{i}", "object_type": "item"},
                identity_id="user-1",
            )
            kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
            kernel.process(ctx, PipelineStage.OBJECT_RESOLUTION)
            ids.append(ctx.object_id)
        assert len(set(ids)) == 3  # all unique

    def test_list_objects(self, kernel: KernelRuntime) -> None:
        for i in range(5):
            ctx = PipelineContext(
                intent="create_object",
                parameters={"name": f"Obj-{i}", "object_type": "item"},
                identity_id="u1",
            )
            kernel.process(ctx, PipelineStage.INTENT_RESOLUTION)
            kernel.process(ctx, PipelineStage.OBJECT_RESOLUTION)
        objects = kernel.list_objects()
        assert len(objects) == 5
        assert all(o["object_id"] for o in objects)


# ======================================================================
# Pipeline integration
# ======================================================================


class TestPipelineIntegration:
    def test_pipeline_with_kernel_runtime(self) -> None:
        pipeline = RuntimePipeline()
        pipeline.register(KernelRuntime())

        ctx = pipeline.execute(
            intent="create_object",
            parameters={"name": "Test", "object_type": "doc"},
            identity_id="user-1",
        )
        assert ctx.state == "completed"
        # intent_resolution and object_resolution should be completed
        intent_step = next(s for s in ctx.trace if s.stage == "intent_resolution")
        object_step = next(s for s in ctx.trace if s.stage == "object_resolution")
        assert intent_step.status == "completed"
        assert object_step.status == "completed"
        assert ctx.object_id is not None


# ======================================================================
# OS Kernel integration
# ======================================================================


class TestOSKernelIntegration:
    def setup_method(self) -> None:
        reset_os()

    def test_os_bootstrap_has_real_kernel(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        kernel = os.get_runtime("kernel")
        assert kernel is not None
        assert kernel.name == "kernel"
        h = kernel.health_check()
        assert h["status"] == "healthy"

    def test_process_intent_creates_object(self) -> None:
        os = ShunyaOS()
        ctx = os.process_intent(
            intent="create_object",
            parameters={"name": "Project X", "object_type": "project"},
            identity_id="user-42",
        )
        assert ctx.state == "completed"
        assert ctx.object_id is not None

        # Verify through kernel runtime
        kernel = os.get_runtime("kernel")
        assert kernel is not None
        obj = kernel.get_object(ctx.object_id)
        assert obj is not None
        assert obj.name == "Project X"

    def test_pipeline_trace_includes_kernel_stages(self) -> None:
        os = ShunyaOS()
        ctx = os.process_intent(
            intent="create_object",
            parameters={"name": "Doc", "object_type": "doc"},
        )
        stages = ctx.status_summary
        assert stages.get("intent_resolution") == "completed"
        assert stages.get("object_resolution") == "completed"

    def test_view_object_after_creation(self) -> None:
        os = ShunyaOS()
        # Create
        create_ctx = os.process_intent(
            intent="create_object",
            parameters={"name": "Report", "object_type": "doc"},
            identity_id="user-1",
        )
        obj_id = create_ctx.object_id

        # View
        view_ctx = os.process_intent(
            intent="view_object",
            parameters={"name": "Report", "object_type": "doc"},
            identity_id="user-1",
            object_id=obj_id,
        )
        assert view_ctx.state == "completed"
        kernel = os.get_runtime("kernel")
        assert kernel is not None
        obj = kernel.get_object(obj_id)
        assert obj is not None
        assert obj.name == "Report"

    def test_cannot_replace_kernel_runtime(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        from core.kernel_runtime import KernelRuntime
        # Should raise — kernel is already registered
        with pytest.raises(ValueError, match="not registered"):
            os.replace_runtime("nonexistent", KernelRuntime())

    def test_kernel_runtime_count_included(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        h = os.health_check()
        # 1 real kernel + 9 mocks = 10
        assert h["runtime_count"] == 10
        assert h["pipeline"]["runtime_count"] == 10