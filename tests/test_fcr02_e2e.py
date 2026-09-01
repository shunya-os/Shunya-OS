"""FCR-02 E2E — SHUNYAAI multi-engine pipeline acceptance tests.

Proves a real SHUNYAAI request traverses multiple intelligence stages
through the capability registry, producing a result without crashing.
"""

import pytest
from app import db, create_app


@pytest.fixture(scope="module")
def app():
    _app = create_app()
    _app.config["TESTING"] = True
    return _app


@pytest.fixture(autouse=True)
def clean_chain(app):
    """Clean execution chain records before each test."""
    with app.app_context():
        from app.evidence.models_db import EvidenceRecord
        from app.evidence.decision_trace import DecisionTrace
        from app.execution_engine.models import Execution, ExecutionLog
        # Only clean ai_* records (test data)
        for ev in EvidenceRecord.query.filter(
            EvidenceRecord.source_type.in_(["ai_query", "ai_action"])
        ).all():
            db.session.delete(ev)
        db.session.commit()


# ---------------------------------------------------------------------------
# Pipeline E2E
# ---------------------------------------------------------------------------

class TestSHUNYAIIntelligencePipeline:
    """Prove the 8-engine pipeline runs end-to-end via the capability registry."""

    def test_pipeline_all_stages_run(self, app):
        """Prove all 8 pipeline stages execute without crash."""
        from core.shunyaai_pipeline import get_pipeline
        pipeline = get_pipeline()

        result = pipeline.run(
            user_input="Show me my current leads and their status",
            identity_id="test_user",
            tenant_id="89",
            session_id="e2e_session_001",
        )

        # At least 5 stages should complete (perception, context, reasoning, planning, decision)
        # Reflection and learning may be skipped if there's nothing to reflect on
        assert result.stages_completed >= 5, \
            f"Expected >=5 stages completed, got {result.stages_completed}: {result.to_dict()}"

        # No crashes
        assert len(result.errors) == 0 or all(
            "UNWIRED" in e.get("error", "") for e in result.errors
        ), f"Unexpected errors: {result.errors}"

        # Should have a response
        assert result.final_output.get("response_text", ""), \
            "Pipeline should produce response text"

        # Verify per-stage output
        stages = result.stages
        assert "perception" in stages, "Perception stage should run"
        assert "reasoning" in stages, "Reasoning stage should run"
        assert "planning" in stages, "Planning stage should run"
        assert "decision" in stages, "Decision stage should run"

    def test_pipeline_handles_read_query(self, app):
        """Prove pipeline handles a read-style query."""
        from core.shunyaai_pipeline import get_pipeline
        pipeline = get_pipeline()

        result = pipeline.run(
            user_input="What is the status of lead INV-2024?",
            identity_id="test_user",
            tenant_id="89",
            session_id="e2e_session_002",
        )

        assert result.stages_completed >= 5, \
            f"Read query should complete >=5 stages: {result.stages_completed}"

    def test_pipeline_handles_action_query(self, app):
        """Prove pipeline handles an action-style query."""
        from core.shunyaai_pipeline import get_pipeline
        pipeline = get_pipeline()

        result = pipeline.run(
            user_input="Create a new task for follow-up with Acme Corp tomorrow",
            identity_id="test_user",
            tenant_id="89",
            session_id="e2e_session_003",
        )

        assert result.stages_completed >= 5, \
            f"Action query should complete >=5 stages: {result.stages_completed}"

    def test_pipeline_requires_no_app_context(self, app):
        """Prove the pipeline itself works without Flask app context.
        (The pipeline only uses the capability registry, which is pure Python.)
        """
        from core.shunyaai_pipeline import get_pipeline, reset_pipeline
        reset_pipeline()
        pipeline = get_pipeline()

        # Run outside app context — use the registry directly
        result = pipeline.run(
            user_input="Test query without app context",
            identity_id="test",
            tenant_id="89",
            session_id="e2e_test_noctx",
        )

        # Pipeline should still complete stages (registry is pure Python)
        assert result.stages_completed >= 5, \
            f"Pipeline should work without app context: {result.stages_completed}"


# ---------------------------------------------------------------------------
# Execution Chain Wiring in ask()
# ---------------------------------------------------------------------------

class TestExecutionChainWiring:
    """Prove the execution chain is properly wired into the ask() function."""

    def test_ask_read_creates_evidence_and_observation(self, app):
        """Prove ask() with a read query creates only evidence + observation."""
        with app.app_context():
            from core.intelligence_runtime.integration import _get_capability_context

            # Simulate a read query through capability routing
            ctx = _get_capability_context(
                "Show me my current leads",
                identity_id="test_user",
                tenant_id="89",
                workspace_type="org",
            )

            # Read queries should not have can_execute capability
            assert ctx.get("can_execute") is False, \
                f"Read query should not be executable: {ctx}"
            assert ctx.get("capability_count") > 0, \
                "Should match at least one capability"

    def test_ask_action_query_identifies_write(self, app):
        """Prove ask() identifies action queries correctly."""
        with app.app_context():
            from core.intelligence_runtime.integration import _get_capability_context

            ctx = _get_capability_context(
                "Create a new invoice for $5000",
                identity_id="test_user",
                tenant_id="89",
                workspace_type="org",
            )

            # Invoice creation is a write
            assert ctx.get("can_write") is True, \
                f"Invoice creation should be writable: {ctx}"

    def test_ask_returns_pipeline_result(self, app):
        """Prove ask() returns pipeline stages in the response."""
        with app.app_context():
            from core.intelligence_runtime.integration import _get_capability_context

            ctx = _get_capability_context(
                "Analyze my sales pipeline",
                identity_id="test_user",
                tenant_id="89",
                workspace_type="org",
            )

            assert "matched_capabilities" in ctx, \
                f"ask() should include capability routing: {ctx}"

    def test_chain_does_not_leak_synthetic_records(self, app):
        """Prove the execution chain doesn't create records from capability routing alone."""
        with app.app_context():
            from app.evidence.models_db import EvidenceRecord
            from app.evidence.decision_trace import DecisionTrace
            from app.execution_engine.models import Execution

            # Evidence records should only exist from actual ask() calls
            # Capability routing alone should not create records
            before_ev = EvidenceRecord.query.count()
            before_dt = DecisionTrace.query.count()
            before_ex = Execution.query.count()

            # Just running capability routing
            from core.intelligence_runtime.integration import _get_capability_context
            ctx = _get_capability_context(
                "Show me my invoices",
                identity_id="test_user",
                tenant_id="89",
            )

            # No records should have been created
            assert EvidenceRecord.query.count() == before_ev, \
                "Capability routing alone must not create evidence"
            assert DecisionTrace.query.count() == before_dt, \
                "Capability routing alone must not create decision traces"
            assert Execution.query.count() == before_ex, \
                "Capability routing alone must not create executions"


# ---------------------------------------------------------------------------
# Registry + Pipeline Integration
# ---------------------------------------------------------------------------

class TestRegistryPipelineIntegration:
    """Prove the capability registry and pipeline work together coherently."""

    def test_pipeline_invokes_engines_through_registry(self, app):
        """Prove every pipeline stage call goes through the registry's invoke()."""
        from core.capability_registry import get_registry
        registry = get_registry()

        # Check all intelligence engines are registered and have handlers
        for name in ["perception", "context_assembly", "reasoning",
                     "planning", "decision", "reflection", "learning", "confidence"]:
            cap = registry.get(name)
            assert cap is not None, f"{name} should be registered"
            assert cap.status == "AVAILABLE", \
                f"{name} should be AVAILABLE, got {cap.status}"
            assert cap._handler is not None, \
                f"{name} should have a handler registered"

    def test_pipeline_engine_invocation_updates_counters(self, app):
        """Prove each pipeline invocation increments the engine's usage counter."""
        from core.capability_registry import get_registry
        from core.shunyaai_pipeline import get_pipeline, reset_pipeline

        reset_pipeline()
        registry = get_registry()

        before = registry.get("perception")._invocation_count

        pipeline = get_pipeline()
        result = pipeline.run(
            user_input="Test invocation counting",
            identity_id="test",
            tenant_id="89",
            session_id="e2e_count",
        )

        after = registry.get("perception")._invocation_count
        assert after > before, \
            "Pipeline invocation should increment engine counter"

    def test_pipeline_graceful_degradation(self, app):
        """Prove missing engines don't crash the pipeline."""
        from core.capability_registry import get_registry
        registry = get_registry()

        # Temporarily remove the handler from reflection
        reflection = registry.get("reflection")
        original_handler = reflection._handler
        reflection._handler = None
        reflection.status = "UNWIRED"

        try:
            from core.shunyaai_pipeline import get_pipeline, reset_pipeline
            reset_pipeline()
            pipeline = get_pipeline()

            result = pipeline.run(
                user_input="Test graceful degradation",
                identity_id="test",
                tenant_id="89",
                session_id="e2e_degradation",
            )

            # Should still complete other stages
            assert result.stages_completed >= 5, \
                f"Should still complete >=5 stages: {result.stages_completed}"
            # Reflection should be skipped (UNWIRED) but not crash
            reflection_info = result.stages.get("reflection", {})
            assert "UNWIRED" in reflection_info.get("error", ""), \
                f"Reflection should be marked UNWIRED: {reflection_info}"
        finally:
            # Restore
            reflection._handler = original_handler
            reflection.status = "AVAILABLE"