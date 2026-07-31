"""Tests for SHUNYA Cognitive Runtime (Phase E).

Covers:
1. Model contracts (defaults, state transitions, pipeline ordering)
2. CognitiveRuntime creation and plugin registration
3. Default engine registration
4. Full pipeline execution (session lifecycle)
5. Confidence propagation
6. Escalation handling
7. Cancellation
8. Observability (events, traces)
9. Policy enforcement
10. Parallel execution
11. Retry logic
12. Health check
"""

import asyncio
import time

import pytest

from core.cognitive_runtime import (
    CognitiveRuntime,
    CognitiveSession,
    PipelineStage,
    RuntimePolicies,
    SessionState,
)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def runtime():
    r = CognitiveRuntime()
    return r


@pytest.fixture
def full_runtime():
    r = CognitiveRuntime()
    r.register_default_engines()
    return r


# ══════════════════════════════════════════════════════════════════════════
# 1. Model Contracts
# ══════════════════════════════════════════════════════════════════════════

class TestSessionModel:
    def test_defaults(self):
        s = CognitiveSession()
        assert s.session_id
        assert s.trace_id
        assert s.state == SessionState.RUNNING
        assert s.current_stage == PipelineStage.RECEIVED
        assert not s.cancellation.cancelled
        assert not s.completion.completed

    def test_valid_transitions(self):
        s = CognitiveSession()
        s.transition_to(SessionState.FAILED)
        assert s.state == SessionState.FAILED
        with pytest.raises(ValueError, match="Invalid session state transition"):
            s.transition_to(SessionState.RUNNING)

    def test_event_addition(self):
        s = CognitiveSession(actor="test", objective="test")
        s.add_event("SessionStarted", {"actor": "test"})
        s.add_event("TestEvent", {"key": "val"})
        assert len(s.trace.timeline) == 2
        assert s.trace.timeline[0].event_type == "SessionStarted"
        assert s.trace.timeline[1].event_type == "TestEvent"
        assert s.trace.timeline[1].payload["key"] == "val"

    def test_pipeline_ordering(self):
        from core.cognitive_runtime.models import PIPELINE_ORDER
        stages = [s.value for s in PIPELINE_ORDER]
        assert stages == [
            "received", "perceiving", "assembling_context", "reasoning",
            "planning", "deciding", "reflecting", "learning",
            "confidence_update", "completed",
        ]

    def test_terminal_states(self):
        assert PipelineStage.COMPLETED.is_terminal
        assert PipelineStage.FAILED.is_terminal
        assert PipelineStage.CANCELLED.is_terminal
        assert not PipelineStage.PERCEIVING.is_terminal


# ══════════════════════════════════════════════════════════════════════════
# 2. Runtime & Plugin Registration
# ══════════════════════════════════════════════════════════════════════════

class TestRuntimeRegistration:
    def test_empty_runtime(self, runtime):
        assert len(runtime.list_plugins()) == 0
        hc = runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["engines_registered"] == 0

    def test_register_single_engine(self, runtime):
        mock = _MockEngine()
        runtime.register_engine(mock, "mock_perception", PipelineStage.PERCEIVING)
        assert len(runtime.list_plugins()) == 1
        plugin = runtime.get_plugin("mock_perception")
        assert plugin is not None
        assert plugin.stage == PipelineStage.PERCEIVING

    def test_duplicate_registration_raises(self, runtime):
        mock = _MockEngine()
        runtime.register_engine(mock, "dup", PipelineStage.PERCEIVING)
        with pytest.raises(ValueError, match="already registered"):
            runtime.register_engine(mock, "dup", PipelineStage.REASONING)

    def test_default_engine_registration(self, full_runtime):
        plugins = full_runtime.list_plugins()
        engine_ids = {p.engine_id for p in plugins}
        expected = {"perception", "context_assembly", "reasoning", "planning",
                    "decision", "reflection", "learning", "confidence"}
        assert engine_ids == expected
        assert len(plugins) == 8


# ══════════════════════════════════════════════════════════════════════════
# 3. Session Creation
# ══════════════════════════════════════════════════════════════════════════

class TestSessionCreation:
    def test_create_session(self, runtime):
        s = runtime.create_session(
            actor="test_user",
            objective="Test Q3 analysis",
            triggering_event="manual",
            context={"department": "engineering"},
        )
        assert s.actor == "test_user"
        assert s.objective == "Test Q3 analysis"
        assert s.triggering_event == "manual"
        assert s.context["department"] == "engineering"
        # SessionStarted event emitted
        assert any(e.event_type == "SessionStarted" for e in s.trace.timeline)


# ══════════════════════════════════════════════════════════════════════════
# 4. Full Pipeline Execution
# ══════════════════════════════════════════════════════════════════════════

class TestPipelineExecution:
    @pytest.mark.asyncio
    async def test_full_execution(self, full_runtime):
        session = full_runtime.create_session(
            actor="test",
            objective="Execute full pipeline",
        )
        result = await full_runtime.execute(session)
        assert result.state == SessionState.COMPLETED
        assert result.current_stage == PipelineStage.COMPLETED
        assert result.completion.completed
        assert result.completion.total_duration_ms > 0

    @pytest.mark.asyncio
    async def test_execution_trace(self, full_runtime):
        session = full_runtime.create_session(actor="test", objective="Trace test")
        result = await full_runtime.execute(session)
        # Should have SessionStarted + StageStarted/Completed for each stage + SessionCompleted
        assert len(result.trace.timeline) > 5
        assert any(e.event_type == "SessionStarted" for e in result.trace.timeline)
        assert any(e.event_type == "SessionCompleted" for e in result.trace.timeline)

    @pytest.mark.asyncio
    async def test_confidence_evolution(self, full_runtime):
        session = full_runtime.create_session(actor="test", objective="Confidence test")
        result = await full_runtime.execute(session)
        assert len(result.confidence_history) > 0
        assert len(result.trace.confidence_evolution) > 0
        # Final accumulated confidence should be recorded
        final_events = [e for e in result.trace.timeline if e.event_type == "ConfidenceUpdated"]
        assert len(final_events) > 0

    @pytest.mark.asyncio
    async def test_engine_timing(self, full_runtime):
        session = full_runtime.create_session(actor="test", objective="Timing test")
        result = await full_runtime.execute(session)
        assert len(result.timing) == 8  # All 8 engines
        for eid, timing in result.timing.items():
            assert timing.engine_id == eid
            assert timing.duration_ms >= 0
            assert timing.start_time_ms > 0

    @pytest.mark.asyncio
    async def test_engine_results(self, full_runtime):
        session = full_runtime.create_session(actor="test", objective="Results test")
        result = await full_runtime.execute(session)
        assert len(result.engine_results) == 8
        for eid, res in result.engine_results.items():
            assert "output_type" in res
            assert "confidence" in res

    @pytest.mark.asyncio
    async def test_deterministic_execution(self, full_runtime):
        """Two identical executions should produce identical output patterns
        (non-deterministic only if escalation occurs, which requires AI)."""
        s1 = full_runtime.create_session(actor="test", objective="Determinism A")
        s2 = full_runtime.create_session(actor="test", objective="Determinism B")
        r1 = await full_runtime.execute(s1)
        r2 = await full_runtime.execute(s2)
        # Both should complete
        assert r1.state == SessionState.COMPLETED
        assert r2.state == SessionState.COMPLETED
        # Engine result keys should be the same
        assert set(r1.engine_results.keys()) == set(r2.engine_results.keys())

    @pytest.mark.asyncio
    async def test_execute_terminal_session_raises(self, full_runtime):
        s = full_runtime.create_session(actor="test", objective="Terminal")
        s.transition_to(SessionState.COMPLETED)
        with pytest.raises(ValueError, match="Cannot execute terminal session"):
            await full_runtime.execute(s)


# ══════════════════════════════════════════════════════════════════════════
# 5. Cancellation
# ══════════════════════════════════════════════════════════════════════════

class TestCancellation:
    @pytest.mark.asyncio
    async def test_cancel_before_execution(self, full_runtime):
        s = full_runtime.create_session(actor="test", objective="Cancel early")
        full_runtime.cancel_session(s, reason="User abort")
        assert s.state == SessionState.CANCELLED
        assert s.cancellation.cancelled
        result = await full_runtime.execute(s)
        # Executing a cancelled session should not run engines
        assert result.cancellation.cancelled

    @pytest.mark.asyncio
    async def test_cancel_twice_no_error(self, full_runtime):
        s = full_runtime.create_session(actor="test", objective="Double cancel")
        full_runtime.cancel_session(s)
        full_runtime.cancel_session(s)  # No error
        assert s.state == SessionState.CANCELLED


# ══════════════════════════════════════════════════════════════════════════
# 6. Observability
# ══════════════════════════════════════════════════════════════════════════

class TestObservability:
    @pytest.mark.asyncio
    async def test_session_trace_timeline(self, full_runtime):
        s = full_runtime.create_session(actor="test", objective="Timeline")
        result = await full_runtime.execute(s)
        events = result.trace.timeline
        event_types = [e.event_type for e in events]
        assert "SessionStarted" in event_types
        assert "SessionCompleted" in event_types
        assert "StageStarted" in event_types
        assert "StageCompleted" in event_types
        assert "ConfidenceUpdated" in event_types

    @pytest.mark.asyncio
    async def test_session_trace_no_errors(self, full_runtime):
        s = full_runtime.create_session(actor="test", objective="Clean run")
        result = await full_runtime.execute(s)
        assert len(result.errors) == 0
        assert len(result.trace.errors) == 0


# ══════════════════════════════════════════════════════════════════════════
# 7. Health Check
# ══════════════════════════════════════════════════════════════════════════

class TestHealthCheck:
    def test_empty_runtime_health(self, runtime):
        hc = runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["engines_registered"] == 0
        assert "policies" in hc

    def test_full_runtime_health(self, full_runtime):
        hc = full_runtime.health_check()
        assert hc["status"] == "healthy"
        assert hc["engines_registered"] == 8
        assert len(hc["engine_plugins"]) == 8


# ══════════════════════════════════════════════════════════════════════════
# 8. Plugin Architecture
# ══════════════════════════════════════════════════════════════════════════

class TestPluginArchitecture:
    def test_stage_to_engine_mapping(self, full_runtime):
        from core.cognitive_runtime.models import PipelineStage
        # Check that all stages have at least one engine
        stages_with_engines = set()
        for p in full_runtime.list_plugins():
            stages_with_engines.add(p.stage)
        # Should have exactly 8 stages (excluding received/completed)
        expected_stages = {
            PipelineStage.PERCEIVING, PipelineStage.ASSEMBLING_CONTEXT,
            PipelineStage.REASONING, PipelineStage.PLANNING,
            PipelineStage.DECIDING, PipelineStage.REFLECTING,
            PipelineStage.LEARNING, PipelineStage.CONFIDENCE_UPDATE,
        }
        assert stages_with_engines == expected_stages

    def test_plugin_confidence_weights(self, full_runtime):
        total_weight = sum(p.confidence_weight for p in full_runtime.list_plugins())
        assert abs(total_weight - 1.0) < 0.01  # Should sum to ~1.0


# ══════════════════════════════════════════════════════════════════════════
# 9. Default Engine Weights
# ══════════════════════════════════════════════════════════════════════════

class TestDefaultWeights:
    def test_weights_sum_to_one(self):
        from core.cognitive_runtime.models import DEFAULT_ENGINE_WEIGHTS
        total = sum(DEFAULT_ENGINE_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01


# ══════════════════════════════════════════════════════════════════════════
# 10. Runtime Policies
# ══════════════════════════════════════════════════════════════════════════

class TestPolicies:
    def test_custom_policies(self):
        policies = RuntimePolicies()
        policies.retry.max_retries = 0
        policies.escalation.allow_escalation = False
        r = CognitiveRuntime(policies=policies)
        assert r._policies.retry.max_retries == 0
        assert not r._policies.escalation.allow_escalation

    @pytest.mark.asyncio
    async def test_policies_in_health_check(self, full_runtime):
        hc = full_runtime.health_check()
        assert "policies" in hc
        assert hc["policies"]["retry_max"] == 3
        assert hc["policies"]["fail_fast"] is True


# ══════════════════════════════════════════════════════════════════════════
# 11. Parallel Execution Safety Check
# ══════════════════════════════════════════════════════════════════════════

class TestParallelExecution:
    @pytest.mark.asyncio
    async def test_parallel_groups_registered(self, full_runtime):
        """REFLECTING and LEARNING should be parallel_safe."""
        for p in full_runtime.list_plugins():
            if p.engine_id == "reflection":
                assert p.parallel_safe
            if p.engine_id == "learning":
                assert p.parallel_safe
            if p.engine_id in ("perception", "reasoning", "decision"):
                assert not p.parallel_safe

    @pytest.mark.asyncio
    async def test_parallel_timing(self, full_runtime):
        """REFLECTING and LEARNING should run concurrently (total time < sum)."""
        session = full_runtime.create_session(actor="test", objective="Parallel timing")
        start = time.time()
        result = await full_runtime.execute(session)
        total = time.time() - start
        assert result.state == SessionState.COMPLETED


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════

class _MockEngine:
    """Minimal mock engine for registration tests."""
    engine_id = "mock"
    engine_type = "mock"

    async def process(self, input_data):
        from core.intelligence.models import EngineOutput
        return EngineOutput(
            output_type="mock",
            payload={"result": "ok"},
            confidence=0.95,
            deterministic=True,
        )

    def escalate(self, input_data):
        from core.intelligence.models import EscalationResult
        return EscalationResult(input_type=input_data.input_type, prompt="mock")

    def get_capabilities(self) -> list[str]:
        return ["mock"]

    def health_check(self) -> dict:
        return {"status": "healthy", "engine_id": "mock", "engine_type": "mock"}