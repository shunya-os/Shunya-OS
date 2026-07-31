"""Tests for the Identity Runtime Adapter (Directive L-02)."""

import pytest

from core.identity_runtime import IdentityRuntime
from core.os import ShunyaOS, reset_os
from core.runtime_pipeline import PipelineContext, PipelineStage, RuntimePipeline

# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def identity() -> IdentityRuntime:
    return IdentityRuntime()


@pytest.fixture
def pipeline() -> RuntimePipeline:
    p = RuntimePipeline()
    p.register(IdentityRuntime())
    return p


# ======================================================================
# IdentityRuntime — contract
# ======================================================================


class TestIdentityRuntimeContract:
    def test_runtime_interface(self, identity: IdentityRuntime) -> None:
        assert identity.name == "identity"
        assert len(identity.stages) == 1
        assert PipelineStage.IDENTITY_RESOLUTION in identity.stages

    def test_health_check(self, identity: IdentityRuntime) -> None:
        h = identity.health_check()
        assert h["status"] == "healthy"
        assert h["runtime"] == "identity"
        assert h["identity_count"] == 0

    def test_health_check_after_creation(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "alice@co.com", "name": "Alice"},
        )
        identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        h = identity.health_check()
        assert h["identity_count"] == 1
        assert h["active_count"] == 1

    def test_noop_for_unknown_stage(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(intent="test")
        result = identity.process(ctx, PipelineStage.OBJECT_RESOLUTION)
        assert result["status"] == "noop"


# ======================================================================
# IDENTITY_RESOLUTION — resolve by identity_id
# ======================================================================


class TestResolveById:
    def test_resolve_existing_id(self, identity: IdentityRuntime) -> None:
        # Create first
        create_ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "bob@co.com", "name": "Bob"},
        )
        identity.process(create_ctx, PipelineStage.IDENTITY_RESOLUTION)
        created_id = create_ctx.identity_id

        # Resolve by ID
        ctx = PipelineContext(intent="view_object", identity_id=created_id)
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is True
        assert result["identity_id"] == created_id
        assert result["source"] == "resolved_by_id"

    def test_resolve_nonexistent_id(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(intent="view_object", identity_id="nonexistent-id")
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is False


# ======================================================================
# IDENTITY_RESOLUTION — resolve by email
# ======================================================================


class TestResolveByEmail:
    def test_resolve_existing_email(self, identity: IdentityRuntime) -> None:
        # Create
        create_ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "carol@co.com", "name": "Carol"},
        )
        identity.process(create_ctx, PipelineStage.IDENTITY_RESOLUTION)

        # Resolve by email
        ctx = PipelineContext(
            intent="view_object",
            parameters={"email": "carol@co.com"},
        )
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is True
        assert result["source"] == "resolved_by_email"
        # Context should be updated with identity_id
        assert ctx.identity_id == result["identity_id"]

    def test_resolve_nonexistent_email(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "ghost@co.com"},
        )
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is True
        assert result.get("created") is True


# ======================================================================
# IDENTITY_RESOLUTION — create on sign-up
# ======================================================================


class TestSignUp:
    def test_sign_in_creates_identity(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "dave@co.com", "name": "Dave"},
        )
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is True
        assert result.get("created") is True
        assert ctx.identity_id is not None

    def test_sign_in_same_email_returns_existing(self, identity: IdentityRuntime) -> None:
        # First sign-in creates
        ctx1 = PipelineContext(
            intent="sign_in",
            parameters={"email": "eve@co.com", "name": "Eve"},
        )
        identity.process(ctx1, PipelineStage.IDENTITY_RESOLUTION)
        id1 = ctx1.identity_id

        # Second sign-in resolves
        ctx2 = PipelineContext(
            intent="sign_in",
            parameters={"email": "eve@co.com"},
        )
        result2 = identity.process(ctx2, PipelineStage.IDENTITY_RESOLUTION)
        assert result2["found"] is True
        assert result2.get("created") is None or result2.get("created") is False
        # Should return same identity
        assert result2["identity_id"] == id1

    def test_sign_in_default_name(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "frank@co.com"},
        )
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "completed"
        identity_obj = identity.get_identity(ctx.identity_id)
        assert identity_obj is not None
        assert identity_obj.display_name == "frank"  # derived from email


# ======================================================================
# IDENTITY_RESOLUTION — noop cases
# ======================================================================


class TestNoop:
    def test_noop_for_non_identity_intent(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(intent="create_object", parameters={"name": "X", "object_type": "doc"})
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "noop"

    def test_resolve_by_identifier(self, identity: IdentityRuntime) -> None:
        # Create identity
        create_ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "grace@co.com", "name": "Grace"},
        )
        identity.process(create_ctx, PipelineStage.IDENTITY_RESOLUTION)

        # Resolve by generic identifier
        ctx = PipelineContext(
            intent="talk_to_customer",
            parameters={"identifier": "grace@co.com"},
        )
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "completed"
        assert result["found"] is True

    def test_resolve_by_identifier_unknown(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(
            intent="talk_to_customer",
            parameters={"identifier": "unknown@co.com"},
        )
        result = identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert result["status"] == "noop"


# ======================================================================
# Delegated repository access
# ======================================================================


class TestDelegatedAccess:
    def test_get_identity(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "hank@co.com", "name": "Hank"},
        )
        identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        obj = identity.get_identity(ctx.identity_id)
        assert obj is not None
        assert obj.display_name == "Hank"

    def test_find_by_email(self, identity: IdentityRuntime) -> None:
        ctx = PipelineContext(
            intent="sign_in",
            parameters={"email": "iris@co.com", "name": "Iris"},
        )
        identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        obj = identity.find_by_email("iris@co.com")
        assert obj is not None
        assert obj.display_name == "Iris"

    def test_identity_count(self, identity: IdentityRuntime) -> None:
        assert identity.get_identity_count() == 0
        for i in range(3):
            ctx = PipelineContext(
                intent="sign_in",
                parameters={"email": f"user{i}@co.com", "name": f"User{i}"},
            )
            identity.process(ctx, PipelineStage.IDENTITY_RESOLUTION)
        assert identity.get_identity_count() == 3


# ======================================================================
# Pipeline integration
# ======================================================================


class TestPipelineIntegration:
    def test_pipeline_with_identity_runtime(self) -> None:
        pipeline = RuntimePipeline()
        pipeline.register(IdentityRuntime())

        ctx = pipeline.execute(
            intent="sign_in",
            parameters={"email": "alice@co.com", "name": "Alice"},
        )
        assert ctx.state == "completed"
        identity_step = next(s for s in ctx.trace if s.stage == "identity_resolution")
        assert identity_step.status == "completed"
        assert ctx.identity_id is not None

    def test_identity_context_propagation(self) -> None:
        """Identity from sign_in should be available to subsequent stages."""
        pipeline = RuntimePipeline()
        pipeline.register(IdentityRuntime())

        ctx = pipeline.execute(
            intent="sign_in",
            parameters={"email": "bob@co.com", "name": "Bob"},
        )
        assert ctx.identity_id is not None

        # Verify the identity resolution record shows details
        identity_step = next(s for s in ctx.trace if s.stage == "identity_resolution")
        assert identity_step.result.get("display_name") == "Bob"


# ======================================================================
# OS Kernel integration
# ======================================================================


class TestOSKernelIntegration:
    def setup_method(self) -> None:
        reset_os()

    def test_os_bootstrap_has_real_identity(self) -> None:
        os = ShunyaOS()
        os.bootstrap()
        identity_rt = os.get_runtime("identity")
        assert identity_rt is not None
        assert identity_rt.name == "identity"
        h = identity_rt.health_check()
        assert h["status"] == "healthy"

    def test_process_intent_creates_identity(self) -> None:
        os = ShunyaOS()
        ctx = os.process_intent(
            intent="sign_in",
            parameters={"email": "founder@co.com", "name": "Founder"},
        )
        assert ctx.state == "completed"
        assert ctx.identity_id is not None

        identity_rt = os.get_runtime("identity")
        assert identity_rt is not None
        obj = identity_rt.get_identity(ctx.identity_id)
        assert obj is not None
        assert obj.display_name == "Founder"

    def test_shared_engine_not_owned_by_runtime(self) -> None:
        """The runtime should delegate to the engine, not own its own store."""
        os = ShunyaOS()
        os.bootstrap()
        identity_rt = os.get_runtime("identity")
        assert identity_rt is not None
        # The runtime should not have a _identities store of its own
        assert not hasattr(identity_rt, "_identities")
        # It should have an _engine that does
        assert hasattr(identity_rt, "_engine")

    def test_two_real_runtimes_count(self) -> None:
        """Kernel + identity = 2 real, 7 adapters = 9 total."""
        os = ShunyaOS()
        os.bootstrap()
        h = os.health_check()
        assert h["runtime_count"] == 9
        pipeline_h = h["pipeline"]
        assert pipeline_h["runtime_count"] == 9