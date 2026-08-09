"""Tests for Phase N+3 — Autonomous Operational Awareness.

Covers all 10 core deliverables:
1. Canonical Observation Model
2. Observation Pipeline
3. Awareness Engine
4. Change Impact Analyzer
5. Continuous Risk Monitoring
6. Organizational Awareness
7. Event Prioritization
8. Awareness Memory
9. Runtime Integration
10. Edge cases & determinism
"""
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import pytest

from app.execution import (
    BusinessExecutionInstance, ExecutionService, ExecState, ObligationState,
    ExecutionObligation, ExecutionException,
)
from app.execution_intelligence import (
    ExecutionIntelligenceEngine, get_execution_intelligence, reset_execution_intelligence,
)
from app.awareness import (
    AwarenessEngine, get_awareness_engine, reset_awareness_engine,
    ObservationPipeline, ChangeImpactAnalyzer, ContinuousRiskMonitor,
    OrganizationalAwareness, EventPrioritization, AwarenessMemory,
    RuntimeService,
)
from app.awareness.models import (
    ObservationCategory, ObservationPriority, AwarenessLevel,
    PropagationTarget, ImpactType,
    CanonicalObservation, ObservationEnrichment, ImpactAssessment,
    AwarenessSnapshot, OrganizationalAwarenessState,
    PrioritizedObservation, AwarenessMemoryEntry,
    RuntimeConfig, AwarenessFilter, AwarenessStats,
)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture(autouse=True)
def _app_context(app):
    """Provide Flask app context for awareness tests that access DB."""
    pass


@pytest.fixture
def svc() -> ExecutionService:
    s = ExecutionService()
    s._execs = {}
    s._obls = {}
    s._excs = {}
    s._allocs = {}
    s._cons = {}
    return s


@pytest.fixture
def config() -> RuntimeConfig:
    return RuntimeConfig()


def make_exec(svc: ExecutionService, state: str = ExecState.ACTIVE,
              tenant_id: int = 1, ct: str = "booking", cid: str = "b1") -> BusinessExecutionInstance:
    r = svc.activate(ct, cid, tenant_id)
    exec_id = r["exec_id"]
    if not hasattr(svc, '_execs'):
        svc._execs = {}
    inst = svc._execs.get(exec_id)
    if inst is None:
        inst = BusinessExecutionInstance()
        inst.exec_id = exec_id
        inst.state = state
        inst.tenant_id = tenant_id
        inst.created_at = datetime.now(timezone.utc).isoformat()
        inst.started_at = datetime.now(timezone.utc).isoformat()
        svc._execs[exec_id] = inst
    elif state != ExecState.ACTIVE:
        inst.state = state
    return inst


def make_obl(svc: ExecutionService, exec_id: str, tenant_id: int = 1,
             desc: str = "Test", state: str = ObligationState.PENDING) -> ExecutionObligation:
    if not hasattr(svc, '_obls'):
        svc._obls = {}
    obl_id = f"obl_{exec_id}_{len(svc._obls)}"
    obl = ExecutionObligation()
    obl.obl_id = obl_id
    obl.exec_id = exec_id
    obl.tenant_id = tenant_id
    obl.description = desc
    obl.state = state
    obl.due_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    svc._obls[obl_id] = obl
    return obl


def make_obs(category: str = ObservationCategory.SYSTEM_EVENT.value,
             tenant_id: int = 1, source: str = "test", source_id: str = "e1",
             prev: Optional[str] = None, curr: Optional[str] = None) -> CanonicalObservation:
    return CanonicalObservation(
        category=category, tenant_id=tenant_id, source=source,
        source_id=source_id, previous_state=prev, current_state=curr,
        payload={"test": True},
    )


# =========================================================================
# 1. Canonical Observation Model
# =========================================================================

class TestCanonicalObservationModel:

    def test_default_fields(self):
        obs = CanonicalObservation()
        assert obs.observation_id
        assert obs.category == ObservationCategory.SYSTEM_EVENT.value
        assert obs.timestamp
        assert obs.idempotency_key == obs.observation_id
        assert obs.correlation_id == obs.observation_id

    def test_custom_fields(self):
        obs = CanonicalObservation(
            category=ObservationCategory.EXECUTION_STATE_CHANGE.value,
            tenant_id=1, source="execution", source_id="e1",
            previous_state="active", current_state="fulfilled",
        )
        assert obs.category == "execution_state_change"
        assert obs.previous_state == "active"
        assert obs.current_state == "fulfilled"

    def test_idempotency_key_explicit(self):
        obs = CanonicalObservation(idempotency_key="my-key")
        assert obs.idempotency_key == "my-key"

    def test_to_dict(self):
        obs = make_obs()
        d = obs.to_dict()
        assert d["observation_id"] == obs.observation_id
        assert d["category"] == obs.category
        assert d["tenant_id"] == obs.tenant_id

    def test_categories_distinct(self):
        cats = [c.value for c in ObservationCategory]
        assert len(cats) == len(set(cats))
        assert "execution_state_change" in cats
        assert "exception_occurred" in cats
        assert "system_event" in cats


# =========================================================================
# 2. Observation Pipeline
# =========================================================================

class TestObservationPipeline:

    def test_process_valid_observation(self, config):
        pipeline = ObservationPipeline(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value)
        result = pipeline.process(obs)
        assert result.observation_id == obs.observation_id
        assert result.enrichment is not None
        assert result.priority == ObservationPriority.MEDIUM.value

    def test_idempotency(self, config):
        pipeline = ObservationPipeline(config)
        obs = make_obs()
        r1 = pipeline.process(obs)
        r2 = pipeline.process(obs)
        assert r2.payload.get("_duplicate") is True

    def test_validation_missing_tenant(self, config):
        pipeline = ObservationPipeline(config)
        obs = CanonicalObservation(category="test", source="test")
        result = pipeline.process(obs)
        assert "_validation_errors" in result.payload

    def test_validation_unknown_category(self, config):
        pipeline = ObservationPipeline(config)
        obs = CanonicalObservation(tenant_id=1, source="test", category="fake_category")
        result = pipeline.process(obs)
        assert "_validation_errors" in result.payload

    def test_propagation_targets_execution_change(self, config):
        pipeline = ObservationPipeline(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value)
        result = pipeline.process(obs)
        assert PropagationTarget.EXECUTION_INTELLIGENCE.value in result.enrichment.propagation_targets

    def test_propagation_targets_exception(self, config):
        pipeline = ObservationPipeline(config)
        obs = make_obs(ObservationCategory.EXCEPTION_OCCURRED.value)
        result = pipeline.process(obs)
        assert PropagationTarget.MEMORY.value in result.enrichment.propagation_targets

    def test_priority_mapping(self, config):
        pipeline = ObservationPipeline(config)
        by_category = {
            ObservationCategory.EXCEPTION_OCCURRED.value: ObservationPriority.CRITICAL.value,
            ObservationCategory.RISK_LEVEL_CHANGE.value: ObservationPriority.HIGH.value,
            ObservationCategory.SYSTEM_EVENT.value: ObservationPriority.INFO.value,
        }
        for cat, expected in by_category.items():
            obs = make_obs(cat)
            result = pipeline.process(obs)
            assert result.priority == expected, f"{cat}: expected {expected} got {result.priority}"

    def test_determinism(self, config):
        pipeline = ObservationPipeline(config)
        obs = make_obs(ObservationCategory.OBLIGATION_CHANGE.value)
        r1 = pipeline.process(obs)
        # Can't process same obs twice (idempotency), so create a structurally identical one
        obs2 = CanonicalObservation(
            category=ObservationCategory.OBLIGATION_CHANGE.value,
            tenant_id=1, source="test", source_id="e1",
        )
        r2 = ObservationPipeline(config).process(obs2)
        assert r1.priority == r2.priority
        assert len(r1.enrichment.propagation_targets) == len(r2.enrichment.propagation_targets)


# =========================================================================
# 3. Change Impact Analyzer
# =========================================================================

class TestChangeImpactAnalyzer:

    def test_state_change_impact(self):
        analyzer = ChangeImpactAnalyzer()
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value, source_id="e1",
                       prev="active", curr="fulfilled")
        impact = analyzer.assess(obs)
        assert ImpactType.STATE_CHANGE.value in impact.impact_types
        assert "e1" in impact.affected_executions
        assert "active" in impact.description

    def test_exception_impact(self):
        analyzer = ChangeImpactAnalyzer()
        obs = make_obs(ObservationCategory.EXCEPTION_OCCURRED.value, source_id="e1")
        impact = analyzer.assess(obs)
        assert ImpactType.RISK_CHANGE.value in impact.impact_types
        assert ImpactType.STATE_CHANGE.value in impact.impact_types

    def test_health_change_impact(self):
        analyzer = ChangeImpactAnalyzer()
        obs = make_obs(ObservationCategory.EXECUTION_HEALTH_CHANGE.value, source_id="e1")
        impact = analyzer.assess(obs)
        assert ImpactType.HEALTH_CHANGE.value in impact.impact_types

    def test_risk_change_impact(self):
        analyzer = ChangeImpactAnalyzer()
        obs = make_obs(ObservationCategory.RISK_LEVEL_CHANGE.value, source_id="e1")
        impact = analyzer.assess(obs)
        assert ImpactType.RISK_CHANGE.value in impact.impact_types

    def test_system_event_impact(self):
        analyzer = ChangeImpactAnalyzer()
        obs = make_obs(ObservationCategory.SYSTEM_EVENT.value)
        impact = analyzer.assess(obs)
        assert ImpactType.NO_IMPACT.value in impact.impact_types

    def test_determinism(self):
        analyzer = ChangeImpactAnalyzer()
        obs = make_obs(ObservationCategory.OBLIGATION_CHANGE.value, source_id="e1")
        i1 = analyzer.assess(obs)
        i2 = analyzer.assess(obs)
        assert i1.impact_types == i2.impact_types
        assert i1.description == i2.description


# =========================================================================
# 4. Continuous Risk Monitoring
# =========================================================================

class TestContinuousRiskMonitor:

    def test_no_affected_execs(self, svc, config):
        monitor = ContinuousRiskMonitor(config)
        obs = make_obs(source_id="nonexistent")
        changes = monitor.on_observation(obs, get_execution_intelligence(), svc)
        assert len(changes) == 0

    def test_observes_risk_change(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE, tenant_id=1, ct="b", cid="b1")
        monitor = ContinuousRiskMonitor(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value,
                       source_id=inst.exec_id)
        ei = get_execution_intelligence()
        changes = monitor.on_observation(obs, ei, svc)
        # Risk may be NONE, but it should be cached
        assert monitor.get_risk(inst.exec_id) is not None

    def test_cache_updates(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE, ct="b", cid="b1")
        monitor = ContinuousRiskMonitor(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value,
                       source_id=inst.exec_id)
        ei = get_execution_intelligence()
        monitor.on_observation(obs, ei, svc)
        monitor.on_observation(obs, ei, svc)
        # Should have cached values
        assert monitor.get_health(inst.exec_id) is not None

    def test_risk_monitoring_disabled(self, svc):
        config_disabled = RuntimeConfig(enable_risk_monitoring=False)
        monitor = ContinuousRiskMonitor(config_disabled)
        obs = make_obs(source_id="e1")
        changes = monitor.on_observation(obs, get_execution_intelligence(), svc)
        assert len(changes) == 0

    def test_stats(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE, ct="b", cid="b1")
        monitor = ContinuousRiskMonitor(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value,
                       source_id=inst.exec_id)
        ei = get_execution_intelligence()
        monitor.on_observation(obs, ei, svc)
        s = monitor.stats
        assert s["monitored_executions"] >= 1
        assert "risk_levels" in s


# =========================================================================
# 5. Organizational Awareness
# =========================================================================

class TestOrganizationalAwareness:

    def test_initial_state(self, config):
        org = OrganizationalAwareness(config)
        state = org.get_tenant_state(1)
        assert state.total_executions == 0
        assert state.overall_awareness == AwarenessLevel.BLIND.value

    def test_update_single_observation(self, config):
        org = OrganizationalAwareness(config)
        obs = make_obs(source_id="e1")
        org.update(obs)
        snap = org.get_snapshot("e1", 1)
        assert snap is not None
        assert snap.observation_count == 1
        assert snap.exec_id == "e1"

    def test_awareness_level_computation(self, config):
        org = OrganizationalAwareness(config)
        # 10 observations → FULL
        for i in range(10):
            obs = make_obs(source_id=f"e1", tenant_id=1)
            org.update(obs)
        snap = org.get_snapshot("e1", 1)
        assert snap.level == AwarenessLevel.FULL.value

    def test_tenant_aggregation(self, config):
        org = OrganizationalAwareness(config)
        for i in range(3):
            obs = make_obs(source_id=f"e{i}", tenant_id=1)
            org.update(obs)
        state = org.get_tenant_state(1)
        assert state.total_executions == 3
        assert state.monitored_executions == 3

    def test_tenant_isolation(self, config):
        org = OrganizationalAwareness(config)
        org.update(make_obs(source_id="e1", tenant_id=1))
        org.update(make_obs(source_id="e2", tenant_id=2))
        s1 = org.get_tenant_state(1)
        s2 = org.get_tenant_state(2)
        assert s1.total_executions == 1
        assert s2.total_executions == 1

    def test_to_dict(self, config):
        org = OrganizationalAwareness(config)
        org.update(make_obs(source_id="e1"))
        snap = org.get_snapshot("e1", 1)
        d = snap.to_dict()
        assert d["exec_id"] == "e1"
        assert "level" in d


# =========================================================================
# 6. Event Prioritization
# =========================================================================

class TestEventPrioritization:

    def test_exception_priority(self):
        prio = EventPrioritization()
        obs = make_obs(ObservationCategory.EXCEPTION_OCCURRED.value)
        result = prio.prioritize(obs)
        assert result.priority_score == ObservationPriority.CRITICAL.value

    def test_risk_change_priority(self):
        prio = EventPrioritization()
        obs = make_obs(ObservationCategory.RISK_LEVEL_CHANGE.value)
        result = prio.prioritize(obs)
        assert result.priority_score == ObservationPriority.HIGH.value

    def test_routine_priority(self):
        prio = EventPrioritization()
        obs = make_obs(ObservationCategory.SYSTEM_EVENT.value)
        result = prio.prioritize(obs)
        assert result.priority_score == ObservationPriority.INFO.value

    def test_blocked_progression_priority(self):
        prio = EventPrioritization()
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value,
                       prev=ExecState.BLOCKED, curr=ExecState.ACTIVE)
        result = prio.prioritize(obs)
        assert result.priority_score <= ObservationPriority.HIGH.value

    def test_reason_included(self):
        prio = EventPrioritization()
        obs = make_obs(ObservationCategory.EXCEPTION_OCCURRED.value)
        result = prio.prioritize(obs)
        assert len(result.reason) > 0
        assert "exception" in result.reason


# =========================================================================
# 7. Awareness Memory
# =========================================================================

class TestAwarenessMemory:

    def test_record_and_retrieve(self, config):
        mem = AwarenessMemory(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value, source_id="e1")
        mem.record(obs)
        recent = mem.recent()
        assert len(recent) == 1
        assert recent[0].observation_id == obs.observation_id

    def test_fifo_eviction(self):
        small_config = RuntimeConfig(max_memory_size=3)
        mem = AwarenessMemory(small_config)
        for i in range(5):
            obs = make_obs(source_id=f"e{i}")
            mem.record(obs)
        assert mem.size() == 3

    def test_filter_by_tenant(self, config):
        mem = AwarenessMemory(config)
        mem.record(make_obs(source_id="e1", tenant_id=1))
        mem.record(make_obs(source_id="e2", tenant_id=2))
        t1 = mem.recent(tenant_id=1)
        t2 = mem.recent(tenant_id=2)
        assert len(t1) == 1
        assert len(t2) == 1

    def test_filter_by_priority(self, config):
        mem = AwarenessMemory(config)
        obs_critical = make_obs(ObservationCategory.EXCEPTION_OCCURRED.value, source_id="e1")
        obs_critical.priority = ObservationPriority.CRITICAL.value
        obs_info = make_obs(ObservationCategory.SYSTEM_EVENT.value, source_id="e2")
        obs_info.priority = ObservationPriority.INFO.value
        mem.record(obs_critical)
        mem.record(obs_info)
        high_priority = mem.recent(min_priority=ObservationPriority.HIGH.value)
        assert len(high_priority) >= 1

    def test_find_by_source(self, config):
        mem = AwarenessMemory(config)
        mem.record(make_obs(source_id="e1"))
        mem.record(make_obs(source_id="e2"))
        mem.record(make_obs(source_id="e1"))
        found = mem.find_by_source("e1")
        assert len(found) == 2

    def test_to_dict(self, config):
        mem = AwarenessMemory(config)
        mem.record(make_obs())
        entries = mem.recent()
        d = entries[0].to_dict()
        assert "observation_id" in d
        assert "category" in d


# =========================================================================
# 8. Runtime Integration
# =========================================================================

class TestRuntimeService:

    def test_ingest_observation(self, svc, config):
        rt = RuntimeService(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value, source_id="e1")
        result = rt.ingest(obs)
        assert result["observation_id"] == obs.observation_id
        assert not result["duplicate"]

    def test_ingest_with_execution_intel(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE, ct="b", cid="b1")
        ei = get_execution_intelligence()
        rt = RuntimeService(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value, source_id=inst.exec_id)
        result = rt.ingest(obs, ei, svc)
        assert "risk_changes" in result

    def test_ingest_duplicate(self, config):
        rt = RuntimeService(config)
        obs = make_obs()
        r1 = rt.ingest(obs)
        r2 = rt.ingest(obs)
        assert r2["duplicate"] is True

    def test_get_awareness(self, config):
        rt = RuntimeService(config)
        obs = make_obs(source_id="e1")
        rt.ingest(obs)
        state = rt.get_awareness("e1", 1)
        assert state["level"] is not None

    def test_get_tenant_awareness(self, config):
        rt = RuntimeService(config)
        rt.ingest(make_obs(source_id="e1", tenant_id=1))
        state = rt.get_tenant_awareness(1)
        assert state["total_executions"] >= 1

    def test_get_risk_status(self, config):
        rt = RuntimeService(config)
        status = rt.get_risk_status("e1")
        assert "risk_level" in status
        assert "health_status" in status

    def test_get_recent_observations(self, config):
        rt = RuntimeService(config)
        rt.ingest(make_obs(source_id="e1"))
        rt.ingest(make_obs(source_id="e2"))
        recent = rt.get_recent_observations()
        assert len(recent) >= 2

    def test_stats(self, config):
        rt = RuntimeService(config)
        rt.ingest(make_obs(source_id="e1"))
        s = rt.stats()
        assert s["total_observations"] >= 1
        assert "risk_monitor" in s
        assert "awareness" in s
        assert "pipeline" in s

    def test_event_log(self, config):
        rt = RuntimeService(config)
        rt.ingest(make_obs(source_id="e1"))
        log = rt.get_event_log()
        assert len(log) >= 1
        assert log[0]["event"] == "ingest"


# =========================================================================
# 9. Awareness Engine Facade
# =========================================================================

class TestAwarenessEngineFacade:

    def test_singleton(self):
        reset_awareness_engine()
        e1 = get_awareness_engine()
        e2 = get_awareness_engine()
        assert e1 is e2

    def test_ingest(self, svc):
        ae = AwarenessEngine()
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value, source_id="e1")
        result = ae.ingest(obs)
        assert result["observation_id"] == obs.observation_id

    def test_observe_execution_state(self, svc):
        ae = AwarenessEngine()
        result = ae.observe_execution_state("e1", 1, "active", "fulfilled")
        assert result["observation_id"] is not None

    def test_observe_exception(self, svc):
        ae = AwarenessEngine()
        result = ae.observe_exception("e1", 1, "timeout", "critical")
        assert result["category"] == ObservationCategory.EXCEPTION_OCCURRED.value

    def test_observe_health_change(self, svc):
        ae = AwarenessEngine()
        result = ae.observe_health_change("e1", 1, "healthy", "at_risk")
        assert result["category"] == ObservationCategory.EXECUTION_HEALTH_CHANGE.value

    def test_get_awareness(self):
        ae = AwarenessEngine()
        ae.observe_execution_state("e1", 1, "pending", "active")
        state = ae.get_awareness("e1", 1)
        assert state["level"] is not None

    def test_get_tenant_awareness(self):
        ae = AwarenessEngine()
        ae.observe_execution_state("e1", 1, "pending", "active")
        state = ae.get_tenant_awareness(1)
        assert state["total_executions"] >= 1

    def test_get_risk_status(self):
        ae = AwarenessEngine()
        status = ae.get_risk_status("e1")
        assert "risk_level" in status

    def test_get_recent_observations(self):
        ae = AwarenessEngine()
        ae.observe_execution_state("e1", 1, "pending", "active")
        ae.observe_exception("e2", 1, "timeout", "high")
        recent = ae.get_recent_observations()
        assert len(recent) >= 2

    def test_stats(self):
        ae = AwarenessEngine()
        s = ae.stats()
        assert "total_observations" in s
        assert "config" in s

    def test_runtime_property(self):
        ae = AwarenessEngine()
        assert hasattr(ae, 'runtime')
        assert isinstance(ae.runtime, RuntimeService)


# =========================================================================
# 10. Edge Cases & Concurrency
# =========================================================================

class TestEdgeCases:

    def test_awareness_unknown_execution(self, config):
        rt = RuntimeService(config)
        state = rt.get_awareness("nonexistent", 1)
        assert state["level"] == AwarenessLevel.BLIND.value

    def test_empty_memory(self, config):
        mem = AwarenessMemory(config)
        assert mem.size() == 0
        assert mem.recent() == []

    def test_observation_without_source(self):
        obs = make_obs(source="")
        pipeline = ObservationPipeline()
        result = pipeline.process(obs)
        assert "_validation_errors" in result.payload

    def test_organizational_awareness_no_observations(self, config):
        org = OrganizationalAwareness(config)
        state = org.get_tenant_state(99)
        assert state.overall_awareness == AwarenessLevel.BLIND.value

    def test_concurrent_ingest(self, config):
        """Multiple threads can ingest simultaneously."""
        rt = RuntimeService(config)
        results = []
        errors = []

        def ingest(n: int):
            try:
                obs = make_obs(source_id=f"e{n}", tenant_id=1)
                result = rt.ingest(obs)
                results.append(result["observation_id"])
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=ingest, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        # At least some should succeed (non-duplicate)
        non_dup = [r for r in results if r]
        assert len(non_dup) == 10

    def test_engine_reset(self):
        reset_awareness_engine()
        assert get_awareness_engine() is not None
        reset_awareness_engine()
        assert get_awareness_engine() is not None

    def test_awareness_memory_summary(self, config):
        mem = AwarenessMemory(config)
        obs = make_obs(ObservationCategory.EXECUTION_STATE_CHANGE.value, source_id="e1",
                       prev="active", curr="fulfilled")
        mem.record(obs)
        entries = mem.recent()
        assert "active" in entries[0].payload_summary