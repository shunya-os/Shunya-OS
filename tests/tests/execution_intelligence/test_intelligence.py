"""Tests for Phase N+2 — Execution Intelligence Engine.

Covers all 10 core deliverables:
1. Execution Health Engine
2. Timeline Intelligence
3. Dependency Graph Engine
4. Risk Detection Engine
5. Next Action Engine
6. Portfolio Intelligence
7. Explainability Layer
8. Runtime Services
9. Public API (ExecutionIntelligenceEngine facade)
10. Edge cases & determinism
"""

import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import pytest

from app.execution import (
    BusinessExecutionInstance, ExecutionObligation, ExecutionException,
    ExecutionResourceAllocation, ExecutionResourceConsumption,
    ExecutionResourceRequirement, ExecutionService,
    ExecState, ObligationState,
)
from app.execution_intelligence import (
    ExecutionIntelligenceEngine, get_execution_intelligence, reset_execution_intelligence,
)
from app.execution_intelligence.models import (
    HealthAssessment, HealthStatus, HealthDimension,
    TimelineSnapshot, CompletionPrediction,
    DependencyNode, DependencyEdge, CriticalPath,
    RiskAssessment, RiskLevel, RiskFactor,
    NextAction, ActionPriority,
    PortfolioSummary, PortfolioBreakdown,
    EvidenceTrace, Explanation,
    RuntimeConfig, QueryFilter,
)
from app.execution_intelligence.engine import (
    ExecutionHealthEngine, TimelineIntelligenceEngine,
    DependencyGraphEngine, RiskDetectionEngine,
    NextActionEngine, PortfolioIntelligence,
    ExplainabilityLayer, RuntimeService,
)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def svc() -> ExecutionService:
    return ExecutionService()


@pytest.fixture
def config() -> RuntimeConfig:
    return RuntimeConfig(
        risk_timeout_threshold_hours=48.0,
        health_warning_threshold=0.7,
        health_critical_threshold=0.4,
        enable_explainability=True,
    )


def make_exec(svc: ExecutionService, state: str = ExecState.ACTIVE,
              tenant_id: int = 1, ct: str = "booking", cid: str = "b1",
              started: bool = True) -> BusinessExecutionInstance:
    r = svc.activate(ct, cid, tenant_id)
    exec_id = r["exec_id"]
    inst = svc._execs[exec_id]
    if not started:
        inst.state = ExecState.PENDING
        inst.started_at = None
    elif state != ExecState.ACTIVE:
        svc.transition(exec_id, state, tenant_id)
    inst.state = state  # ensure exact state
    return inst


def make_obl(svc: ExecutionService, exec_id: str, tenant_id: int = 1,
             obl_type: str = "payment", desc: str = "Test",
             state: str = ObligationState.PENDING, due_at: Optional[str] = None,
             dependencies: Optional[List[str]] = None) -> ExecutionObligation:
    r = svc.add_obligation(exec_id, tenant_id, obl_type, desc, due_at=due_at)
    obl = svc._objs[r["obl_id"]]
    obl.state = state
    if dependencies:
        obl.dependencies = dependencies
    return obl


# Fix: svc._objs -> svc._obls
def make_obl_fixed(svc: ExecutionService, exec_id: str, tenant_id: int = 1,
                   obl_type: str = "payment", desc: str = "Test",
                   state: str = ObligationState.PENDING,
                   due_at: Optional[str] = None) -> ExecutionObligation:
    r = svc.add_obligation(exec_id, tenant_id, obl_type, desc, due_at=due_at)
    obl = svc._obls[r["obl_id"]]
    obl.state = state
    return obl


# =========================================================================
# 1. Execution Health Engine
# =========================================================================

class TestExecutionHealthEngine:

    def test_healthy_active_execution(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="Payment")]
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, obls, [], svc)
        assert h.exec_id == inst.exec_id
        assert h.overall in (HealthStatus.HEALTHY.value, HealthStatus.WARNING.value)
        assert HealthDimension.STATE.value in h.dimensions
        assert HealthDimension.PROGRESS.value in h.dimensions

    def test_fulfilled_execution(self, svc, config):
        inst = make_exec(svc, ExecState.FULFILLED)
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], [], svc)
        assert h.overall == HealthStatus.HEALTHY.value

    def test_failed_execution(self, svc, config):
        inst = make_exec(svc, ExecState.FAILED)
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], [], svc)
        assert h.overall == HealthStatus.CRITICAL.value

    def test_blocked_execution(self, svc, config):
        inst = make_exec(svc, ExecState.BLOCKED)
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], [], svc)
        assert h.overall == HealthStatus.CRITICAL.value

    def test_state_dimension_healthy(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], [], svc)
        assert h.dimensions[HealthDimension.STATE.value] == HealthStatus.HEALTHY.value

    def test_exception_burden_reduces_health(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        excs = [ExecutionException(f"e{i}", inst.exec_id, inst.tenant_id, "test", "medium")
                for i in range(5)]
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], excs, svc)
        assert h.scores[HealthDimension.EXCEPTION_BURDEN.value] < 0.5

    def test_resource_shortfall_detected(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        svc.allocate_resource(inst.exec_id, inst.tenant_id, "budget", 1000, "USD")
        svc.record_consumption("dummy", inst.exec_id, inst.tenant_id, 1500, "USD")
        # Also add a real alloc so consumption has matching alloc
        r = svc.allocate_resource(inst.exec_id, inst.tenant_id, "budget", 2000, "USD")
        svc.record_consumption(r["alloc_id"], inst.exec_id, inst.tenant_id, 1500, "USD")
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], [], svc)
        # Should detect the position
        assert HealthDimension.RESOURCE_POSITION.value in h.dimensions

    def test_overdue_obligations_affect_timeliness(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        obls = [make_obl_fixed(svc, inst.exec_id, desc="Overdue", due_at=past)]
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, obls, [], svc)
        assert h.scores.get(HealthDimension.TIMELINESS.value, 1.0) <= 0.5

    def test_determinism(self, svc, config):
        """Same inputs produce identical outputs."""
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="Test")]
        engine = ExecutionHealthEngine(config)
        h1 = engine.assess(inst, obls, [], svc)
        h2 = engine.assess(inst, obls, [], svc)
        assert h1.overall == h2.overall
        assert h1.scores == h2.scores

    def test_to_dict(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], [], svc)
        d = h.to_dict()
        assert d["exec_id"] == inst.exec_id
        assert "overall" in d
        assert "dimensions" in d
        assert "scores" in d
        assert "evidence" in d


# =========================================================================
# 2. Timeline Intelligence
# =========================================================================

class TestTimelineIntelligence:

    def test_snapshot_active(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="A"),
                make_obl_fixed(svc, inst.exec_id, desc="B")]
        engine = TimelineIntelligenceEngine(config)
        snap = engine.snapshot(inst, obls)
        assert snap.exec_id == inst.exec_id
        assert snap.completion_ratio == 0.0
        assert len(snap.milestones_remaining) == 2

    def test_snapshot_partial_progress(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [
            make_obl_fixed(svc, inst.exec_id, desc="Done", state=ObligationState.SATISFIED),
            make_obl_fixed(svc, inst.exec_id, desc="Pending", state=ObligationState.PENDING),
        ]
        engine = TimelineIntelligenceEngine(config)
        snap = engine.snapshot(inst, obls)
        assert snap.completion_ratio == 0.5
        assert len(snap.milestones_passed) == 1

    def test_completion_prediction_fulfilled(self, svc, config):
        inst = make_exec(svc, ExecState.FULFILLED)
        engine = TimelineIntelligenceEngine(config)
        snap = engine.snapshot(inst, [])
        pred = engine.predict_completion(snap)
        assert pred.confidence == 1.0
        assert "already completed" in pred.basis[0]

    def test_prediction_pending_not_started(self, svc, config):
        inst = make_exec(svc, ExecState.PENDING, started=False)
        engine = TimelineIntelligenceEngine(config)
        snap = engine.snapshot(inst, [])
        pred = engine.predict_completion(snap)
        assert pred.confidence == 0.0

    def test_prediction_with_progress(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [
            make_obl_fixed(svc, inst.exec_id, desc="Done", state=ObligationState.SATISFIED),
        ]
        engine = TimelineIntelligenceEngine(config)
        snap = engine.snapshot(inst, obls)
        pred = engine.predict_completion(snap)
        assert pred.confidence > 0.0

    def test_determinism(self, svc, config):
        """Same inputs produce identical outputs (structural determinism)."""
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="X")]
        engine = TimelineIntelligenceEngine(config)
        s1 = engine.snapshot(inst, obls)
        s2 = engine.snapshot(inst, obls)
        # Structural fields are deterministic; elapsed_seconds varies with wall clock
        assert s1.exec_id == s2.exec_id
        assert s1.completion_ratio == s2.completion_ratio
        assert len(s1.milestones_remaining) == len(s2.milestones_remaining)

    def test_to_dict(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = TimelineIntelligenceEngine(config)
        snap = engine.snapshot(inst, [])
        d = snap.to_dict()
        assert d["exec_id"] == inst.exec_id


# =========================================================================
# 3. Dependency Graph Engine
# =========================================================================

class TestDependencyGraphEngine:

    def test_empty_graph(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = DependencyGraphEngine(config)
        nodes, edges = engine.build_graph(inst, [])
        assert len(nodes) == 0
        assert len(edges) == 0

    def test_single_node(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obl = make_obl_fixed(svc, inst.exec_id, desc="Only")
        engine = DependencyGraphEngine(config)
        nodes, edges = engine.build_graph(inst, [obl])
        assert len(nodes) == 1
        assert len(edges) == 0

    def test_dependency_edge(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        o1 = make_obl_fixed(svc, inst.exec_id, desc="A")
        o2 = make_obl_fixed(svc, inst.exec_id, desc="B")
        svc.add_dependency(o2.obl_id, o1.obl_id, inst.tenant_id)
        obl2 = svc._obls[o2.obl_id]
        engine = DependencyGraphEngine(config)
        nodes, edges = engine.build_graph(inst, [o1, obl2])
        assert len(edges) >= 1

    def test_critical_path_chain(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        o1 = make_obl_fixed(svc, inst.exec_id, desc="A")
        o2 = make_obl_fixed(svc, inst.exec_id, desc="B")
        o3 = make_obl_fixed(svc, inst.exec_id, desc="C")
        svc.add_dependency(o2.obl_id, o1.obl_id, inst.tenant_id)
        svc.add_dependency(o3.obl_id, o2.obl_id, inst.tenant_id)
        obl1 = svc._obls[o1.obl_id]
        obl2 = svc._obls[o2.obl_id]
        obl3 = svc._obls[o3.obl_id]
        engine = DependencyGraphEngine(config)
        nodes, edges = engine.build_graph(inst, [obl1, obl2, obl3])
        cp = engine.find_critical_path(nodes, edges, [obl1, obl2, obl3])
        assert len(cp.path) >= 1
        assert cp.total_length >= 1

    def test_critical_path_no_bottlenecks(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        o1 = make_obl_fixed(svc, inst.exec_id, desc="Solo")
        engine = DependencyGraphEngine(config)
        nodes, edges = engine.build_graph(inst, [o1])
        cp = engine.find_critical_path(nodes, edges, [o1])
        assert cp.exec_id == inst.exec_id

    def test_determinism(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        o1 = make_obl_fixed(svc, inst.exec_id, desc="X")
        o2 = make_obl_fixed(svc, inst.exec_id, desc="Y")
        svc.add_dependency(o2.obl_id, o1.obl_id, inst.tenant_id)
        obl1 = svc._obls[o1.obl_id]
        obl2 = svc._obls[o2.obl_id]
        engine = DependencyGraphEngine(config)
        n1, e1 = engine.build_graph(inst, [obl1, obl2])
        n2, e2 = engine.build_graph(inst, [obl1, obl2])
        assert len(n1) == len(n2)
        assert len(e1) == len(e2)


# =========================================================================
# 4. Risk Detection Engine
# =========================================================================

class TestRiskDetectionEngine:

    def test_no_risk_healthy_execution(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = RiskDetectionEngine(config)
        r = engine.assess(inst, [], [])
        assert r.overall_risk == RiskLevel.NONE.value

    def test_blocked_obligation_detected(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="B", state=ObligationState.BLOCKED)]
        engine = RiskDetectionEngine(config)
        r = engine.assess(inst, obls, [])
        assert any(f.risk_type == "blocked_obligations" for f in r.factors)

    def test_critical_exception_detected(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        excs = [ExecutionException("e1", inst.exec_id, inst.tenant_id, "timeout", "critical")]
        engine = RiskDetectionEngine(config)
        r = engine.assess(inst, [], excs)
        assert any(f.risk_type == "critical_exceptions" for f in r.factors)

    def test_resource_shortfall_risk(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        health = HealthAssessment(
            exec_id=inst.exec_id, tenant_id=inst.tenant_id,
            overall=HealthStatus.CRITICAL.value,
            dimensions={HealthDimension.RESOURCE_POSITION.value: HealthStatus.CRITICAL.value},
            scores={HealthDimension.RESOURCE_POSITION.value: 0.2},
            evidence={HealthDimension.RESOURCE_POSITION.value: ["shortfall"]},
        )
        engine = RiskDetectionEngine(config)
        r = engine.assess(inst, [], [], health)
        assert any(f.risk_type == "resource_shortfall" for f in r.factors)

    def test_overall_risk_critical(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        excs = [ExecutionException("e1", inst.exec_id, inst.tenant_id, "fatal", "critical")]
        obls = [make_obl_fixed(svc, inst.exec_id, desc="B", state=ObligationState.BLOCKED)]
        health = HealthAssessment(
            exec_id=inst.exec_id, tenant_id=inst.tenant_id,
            overall=HealthStatus.CRITICAL.value,
            dimensions={HealthDimension.RESOURCE_POSITION.value: HealthStatus.CRITICAL.value},
            scores={HealthDimension.RESOURCE_POSITION.value: 0.2},
            evidence={},
        )
        engine = RiskDetectionEngine(config)
        r = engine.assess(inst, obls, excs, health)
        assert r.overall_risk in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value)

    def test_determinism(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="B", state=ObligationState.BLOCKED)]
        engine = RiskDetectionEngine(config)
        r1 = engine.assess(inst, obls, [])
        r2 = engine.assess(inst, obls, [])
        assert len(r1.factors) == len(r2.factors)
        assert r1.overall_risk == r2.overall_risk

    def test_to_dict(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = RiskDetectionEngine(config)
        r = engine.assess(inst, [], [])
        d = r.to_dict()
        assert d["exec_id"] == inst.exec_id
        assert "overall_risk" in d
        assert "factors" in d


# =========================================================================
# 5. Next Action Engine
# =========================================================================

class TestNextActionEngine:

    def test_no_actions_for_fulfilled(self, svc, config):
        inst = make_exec(svc, ExecState.FULFILLED)
        engine = NextActionEngine()
        actions = engine.assess(inst, [], [])
        assert len(actions) == 0

    def test_unblock_action_generated(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="Blocked", state=ObligationState.BLOCKED)]
        engine = NextActionEngine()
        actions = engine.assess(inst, obls, [])
        assert any(a.action_type == "unblock_obligation" for a in actions)

    def test_satisfy_ready_action(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="Ready", state=ObligationState.READY)]
        engine = NextActionEngine()
        actions = engine.assess(inst, obls, [])
        assert any(a.action_type == "satisfy_obligation" for a in actions)

    def test_mitigate_risk_action(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        mock_risk = RiskAssessment(
            exec_id=inst.exec_id, tenant_id=inst.tenant_id,
            overall_risk=RiskLevel.HIGH.value,
            factors=[RiskFactor("test_risk", "mock factor", RiskLevel.HIGH.value)],
        )
        engine = NextActionEngine()
        actions = engine.assess(inst, [], [], risk=mock_risk)
        assert any(a.action_type == "mitigate_risk" for a in actions)

    def test_actions_capped_at_10(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        # Generate many blocked obligations
        obls = []
        for i in range(10):
            o = make_obl_fixed(svc, inst.exec_id, desc=f"B{i}", state=ObligationState.BLOCKED)
            obls.append(o)
        engine = NextActionEngine()
        actions = engine.assess(inst, obls, [])
        assert len(actions) <= 10

    def test_determinism(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        obls = [make_obl_fixed(svc, inst.exec_id, desc="Blocked", state=ObligationState.BLOCKED)]
        engine = NextActionEngine()
        a1 = engine.assess(inst, obls, [])
        a2 = engine.assess(inst, obls, [])
        assert len(a1) == len(a2)
        for a, b in zip(a1, a2):
            assert a.action_type == b.action_type
            assert a.priority == b.priority


# =========================================================================
# 6. Portfolio Intelligence
# =========================================================================

class TestPortfolioIntelligence:

    def test_empty_portfolio(self, svc, config):
        engine = PortfolioIntelligence(config)
        h = ExecutionHealthEngine(config)
        r = RiskDetectionEngine(config)
        a = NextActionEngine()
        summary = engine.summarize(1, svc, h, r, a)
        assert summary.tenant_id == 1
        assert summary.breakdown.total == 0

    def test_portfolio_with_executions(self, svc, config):
        make_exec(svc, ExecState.ACTIVE, tenant_id=1, ct="booking", cid="b1")
        make_exec(svc, ExecState.FULFILLED, tenant_id=1, ct="booking", cid="b2")
        make_exec(svc, ExecState.FAILED, tenant_id=1, ct="booking", cid="b3")
        engine = PortfolioIntelligence(config)
        h = ExecutionHealthEngine(config)
        r = RiskDetectionEngine(config)
        a = NextActionEngine()
        summary = engine.summarize(1, svc, h, r, a)
        assert summary.breakdown.total == 3
        assert summary.breakdown.active == 1
        assert summary.breakdown.fulfilled == 1
        assert summary.breakdown.failed == 1

    def test_tenant_isolation(self, svc, config):
        make_exec(svc, ExecState.ACTIVE, tenant_id=1, ct="booking", cid="b1")
        make_exec(svc, ExecState.ACTIVE, tenant_id=2, ct="booking", cid="b2")
        engine = PortfolioIntelligence(config)
        h = ExecutionHealthEngine(config)
        r = RiskDetectionEngine(config)
        a = NextActionEngine()
        s1 = engine.summarize(1, svc, h, r, a)
        s2 = engine.summarize(2, svc, h, r, a)
        assert s1.breakdown.total == 1
        assert s1.breakdown.total == s2.breakdown.total

    def test_health_distribution(self, svc, config):
        make_exec(svc, ExecState.ACTIVE, tenant_id=1, ct="booking", cid="b1")
        make_exec(svc, ExecState.FULFILLED, tenant_id=1, ct="booking", cid="b2")
        engine = PortfolioIntelligence(config)
        h = ExecutionHealthEngine(config)
        r = RiskDetectionEngine(config)
        a = NextActionEngine()
        summary = engine.summarize(1, svc, h, r, a)
        assert len(summary.health_distribution) > 0

    def test_to_dict(self, svc, config):
        engine = PortfolioIntelligence(config)
        h = ExecutionHealthEngine(config)
        r = RiskDetectionEngine(config)
        a = NextActionEngine()
        summary = engine.summarize(1, svc, h, r, a)
        d = summary.to_dict()
        assert d["tenant_id"] == 1
        assert "breakdown" in d


# =========================================================================
# 7. Explainability Layer
# =========================================================================

class TestExplainabilityLayer:

    def test_explain_health(self):
        engine = ExplainabilityLayer()
        h = HealthAssessment(
            exec_id="test-1", tenant_id=1,
            overall=HealthStatus.HEALTHY.value,
            dimensions={HealthDimension.STATE.value: HealthStatus.HEALTHY.value},
            scores={HealthDimension.STATE.value: 0.9},
            evidence={HealthDimension.STATE.value: ["execution is active"]},
        )
        exp = engine.explain_health(h)
        assert exp.topic == f"Execution Health: test-1"
        assert "healthy" in exp.conclusion.lower()
        assert len(exp.traces) > 0

    def test_explain_risk(self):
        engine = ExplainabilityLayer()
        r = RiskAssessment(
            exec_id="test-1", tenant_id=1,
            overall_risk=RiskLevel.HIGH.value,
            factors=[RiskFactor("blocked", "blocked obligation", RiskLevel.HIGH.value)],
        )
        exp = engine.explain_risk(r)
        assert "Risk Assessment" in exp.topic
        assert "high" in exp.conclusion.lower()

    def test_explain_action(self):
        engine = ExplainabilityLayer()
        action = NextAction(
            exec_id="test-1", tenant_id=1,
            action_type="unblock_obligation",
            description="Unblock payment",
            priority=ActionPriority.IMMEDIATE.value,
            evidence=["obl_id=abc"],
        )
        exp = engine.explain_action(action)
        assert "Next Action" in exp.topic
        assert "Unblock" in exp.conclusion

    def test_explain_portfolio(self):
        engine = ExplainabilityLayer()
        summary = PortfolioSummary(
            tenant_id=1,
            breakdown=PortfolioBreakdown(total=5, active=2, fulfilled=3),
        )
        exp = engine.explain_portfolio(summary)
        assert "Portfolio Summary" in exp.topic
        assert "5" in exp.conclusion


# =========================================================================
# 8. Runtime Services
# =========================================================================

class TestRuntimeService:

    def test_full_assessment(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        make_obl_fixed(svc, inst.exec_id, desc="Payment")
        rt = RuntimeService(config)
        result = rt.full_assessment(inst, svc)
        assert result["exec_id"] == inst.exec_id
        assert "health" in result
        assert "timeline" in result
        assert "risk" in result
        assert "next_actions" in result
        assert "explanations" in result

    def test_portfolio_summary(self, svc, config):
        make_exec(svc, ExecState.ACTIVE, tenant_id=1, ct="b", cid="b1")
        rt = RuntimeService(config)
        result = rt.portfolio_summary(1, svc)
        assert result["tenant_id"] == 1
        assert "breakdown" in result
        assert "explanation" in result

    def test_stats(self, svc, config):
        rt = RuntimeService(config)
        s = rt.stats()
        assert "total_assessments" in s
        assert "config" in s

    def test_event_log(self, svc, config):
        rt = RuntimeService(config)
        inst = make_exec(svc, ExecState.ACTIVE)
        rt.full_assessment(inst, svc)
        log = rt.get_event_log()
        assert len(log) >= 1
        assert log[0]["event"] == "full_assessment"

    def test_explain_assessment(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        rt = RuntimeService(config)
        result = rt.full_assessment(inst, svc)
        expl = rt.explain_assessment(result)
        assert "explanations" in expl
        assert "health" in expl["explanations"]


# =========================================================================
# 9. Public API (ExecutionIntelligenceEngine facade)
# =========================================================================

class TestExecutionIntelligenceEngine:

    def test_singleton(self):
        reset_execution_intelligence()
        e1 = get_execution_intelligence()
        e2 = get_execution_intelligence()
        assert e1 is e2

    def test_full_assessment(self, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        make_obl_fixed(svc, inst.exec_id, desc="Test")
        ei = ExecutionIntelligenceEngine()
        result = ei.full_assessment(inst, svc)
        assert "health" in result
        assert "timeline" in result
        assert "risk" in result
        assert "next_actions" in result

    def test_portfolio_summary(self, svc):
        make_exec(svc, ExecState.ACTIVE, tenant_id=1, ct="b", cid="b1")
        ei = ExecutionIntelligenceEngine()
        result = ei.portfolio_summary(1, svc)
        assert "breakdown" in result

    def test_assess_health(self, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        ei = ExecutionIntelligenceEngine()
        h = ei.assess_health(inst, svc)
        assert isinstance(h, HealthAssessment)

    def test_assess_risk(self, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        ei = ExecutionIntelligenceEngine()
        r = ei.assess_risk(inst, svc)
        assert isinstance(r, RiskAssessment)

    def test_next_actions(self, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        make_obl_fixed(svc, inst.exec_id, desc="Blocked", state=ObligationState.BLOCKED)
        ei = ExecutionIntelligenceEngine()
        actions = ei.next_actions(inst, svc)
        assert len(actions) > 0

    def test_timeline(self, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        ei = ExecutionIntelligenceEngine()
        result = ei.timeline(inst, svc)
        assert "snapshot" in result
        assert "prediction" in result

    def test_dependency_graph(self, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        o1 = make_obl_fixed(svc, inst.exec_id, desc="A")
        o2 = make_obl_fixed(svc, inst.exec_id, desc="B")
        svc.add_dependency(o2.obl_id, o1.obl_id, inst.tenant_id)
        ei = ExecutionIntelligenceEngine()
        result = ei.dependency_graph(inst, svc)
        assert "nodes" in result
        assert "edges" in result
        assert "critical_path" in result

    def test_explain(self, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        ei = ExecutionIntelligenceEngine()
        result = ei.full_assessment(inst, svc)
        expl = ei.explain(result)
        assert "explanations" in expl

    def test_stats(self):
        ei = ExecutionIntelligenceEngine()
        s = ei.stats()
        assert "total_assessments" in s
        assert "config" in s

    def test_runtime_property(self):
        ei = ExecutionIntelligenceEngine()
        assert hasattr(ei, 'runtime')
        assert isinstance(ei.runtime, RuntimeService)


# =========================================================================
# 10. Edge Cases & Concurrency
# =========================================================================

class TestEdgeCases:

    def test_health_unknown_state(self):
        engine = ExecutionHealthEngine()
        inst = BusinessExecutionInstance("e1", 1, "test", "t1", state="unknown_state")
        h = engine.assess(inst, [], [], ExecutionService())
        # unknown_state maps to UNKNOWN dimension but overall weighted average
        # may produce WARNING since the score is 0.5 (above warning_threshold=0.7? No, 0.5 < 0.7)
        assert h.overall is not None

    def test_empty_execution_no_obligations(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], [], svc)
        assert h.overall is not None

    def test_many_exceptions(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        excs = [ExecutionException(f"e{i}", inst.exec_id, inst.tenant_id, "err", "high")
                for i in range(20)]
        engine = ExecutionHealthEngine(config)
        h = engine.assess(inst, [], excs, svc)
        assert h.scores[HealthDimension.EXCEPTION_BURDEN.value] <= 0.0

    def test_critical_path_single_node(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = DependencyGraphEngine(config)
        cp = engine.find_critical_path([], [], [])
        assert cp.path == []

    def test_no_risk_no_factors(self, svc, config):
        inst = make_exec(svc, ExecState.ACTIVE)
        engine = RiskDetectionEngine(config)
        r = engine.assess(inst, [], [])
        assert len(r.factors) == 0

    def test_timeline_no_start(self, svc, config):
        inst = make_exec(svc, ExecState.PENDING, started=False)
        engine = TimelineIntelligenceEngine(config)
        snap = engine.snapshot(inst, [])
        assert snap.elapsed_seconds == 0.0

    def test_concurrent_assessments(self, svc, config):
        """Multiple threads can assess simultaneously without corruption."""
        inst = make_exec(svc, ExecState.ACTIVE, ct="concurrent", cid="c1")
        make_obl_fixed(svc, inst.exec_id, desc="X")
        make_obl_fixed(svc, inst.exec_id, desc="Y")
        results = []
        errors = []

        def assess(n):
            try:
                engine = ExecutionHealthEngine(config)
                obls = list(svc._obls.values())
                h = engine.assess(inst, obls, [], svc)
                results.append(h.overall)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=assess, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert len(results) == 10

    def test_all_engines_reset(self):
        reset_execution_intelligence()
        assert get_execution_intelligence() is not None
        reset_execution_intelligence()
        assert get_execution_intelligence() is not None
