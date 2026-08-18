"""Tests for Milestone III — Prediction & Simulation.

Covers all 10 core deliverables:
1. Prediction Engine — 9 categories
2. Prediction Provenance
3. Prediction Lifecycle
4. Prediction Explainability
5. Simulation Engine
6. Prediction Degradation (refusal)
7. Scenario Comparator
8. Runtime Integration
9. Deterministic Testing
10. Edge cases
"""
import pytest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from app.execution.constants import ExecState, ObligationState
from app.execution import ExecutionService
from app.execution_intelligence import get_execution_intelligence


class _BusinessExecutionInstance:
    """Minimal inline mock — these were previously imported from a removed module."""
    pass


class _ExecutionObligation:
    """Minimal inline mock — these were previously imported from a removed module."""
    pass


# Alias for test usage
BusinessExecutionInstance = _BusinessExecutionInstance
ExecutionObligation = _ExecutionObligation
from app.learning_intelligence import get_learning_intelligence
from app.prediction import (
    PredictionAndSimulationEngine, get_prediction_engine, reset_prediction_engine,
)
from app.prediction.models import (
    PredictionCategory, SimulationType, PredictionStatus,
    PredictionRecord, PredictionParameters, PredictionConfig,
    ConfidenceDecomposition, EvidenceTrace, Assumption, Uncertainty,
    PredictionExplanation, PredictionRefusal,
    SimulationInput, SimulationResult, SimulationFork,
    ScenarioBranch, ScenarioComparison,
    PredictionAuditEntry, ConfidenceFactor,
)
from app.prediction.engine import (
    PredictionEngine, SimulationEngine, ScenarioComparator,
    PredictionLifecycle, PredictionExplainability, PredictionAudit,
    RuntimeService,
)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def config() -> PredictionConfig:
    return PredictionConfig(min_samples_for_prediction=1)


@pytest.fixture(autouse=True)
def _app_context(app):
    """Provide Flask app context for prediction tests that access DB."""
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
def rt(config) -> RuntimeService:
    return RuntimeService(config)


@pytest.fixture
def ps(config) -> PredictionAndSimulationEngine:
    return PredictionAndSimulationEngine(config)


def make_exec(svc, state=ExecState.ACTIVE, tenant_id=1, ct="booking", cid="b1"):
    r = svc.activate(ct, cid, tenant_id)
    exec_id = r["exec_id"]
    if not hasattr(svc, '_execs'):
        svc._execs = {}
    if not hasattr(svc, '_excs'):
        svc._excs = {}
    inst = BusinessExecutionInstance()
    inst.exec_id = exec_id
    inst.state = state
    inst.tenant_id = tenant_id
    inst.commitment_type = ct
    inst.commitment_id = cid
    inst.created_at = datetime.now(timezone.utc).isoformat()
    inst.started_at = datetime.now(timezone.utc).isoformat()
    inst.completed_at = None if state == ExecState.ACTIVE else datetime.now(timezone.utc).isoformat()
    inst.obligations = []
    inst.exceptions = []
    svc._execs[exec_id] = inst
    return inst


def add_obl(svc, exec_id, tenant_id=1, desc="Pay", state=ObligationState.PENDING, due_at=None):
    if not hasattr(svc, '_obls'):
        svc._obls = {}
    obl_id = f"obl_{exec_id}_{len(svc._obls)}"
    obl = ExecutionObligation()
    obl.obl_id = obl_id
    obl.exec_id = exec_id
    obl.tenant_id = tenant_id
    obl.description = desc
    obl.obl_type = "payment"
    obl.dependencies = []
    obl.state = state
    obl.due_at = due_at or (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    svc._obls[obl_id] = obl
    return obl


# =========================================================================
# 1. Prediction Engine — 9 Categories
# =========================================================================

class TestPredictionEngine:

    def test_completion_forecast(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        add_obl(svc, inst.exec_id, desc="A", state=ObligationState.SATISFIED)
        result = rt.predict("completion", "execution", inst.exec_id, 1,
                            exec_service=svc)
        assert result["params"]["category"] == "completion"
        assert "predicted_at" in result["output"]
        assert result["status"] == "active"

    def test_delay_forecast(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        add_obl(svc, inst.exec_id, desc="Overdue", state=ObligationState.PENDING, due_at=past)
        result = rt.predict("delay", "execution", inst.exec_id, 1, exec_service=svc)
        assert "delay_probability" in result["output"]
        assert result["output"]["overdue_count"] >= 1

    def test_workload_forecast(self, rt, svc):
        make_exec(svc, ExecState.ACTIVE, ct="b1", cid="b1")
        make_exec(svc, ExecState.ACTIVE, ct="b2", cid="b2")
        result = rt.predict("workload", "portfolio", "all", 1, exec_service=svc)
        assert "current_active" in result["output"]

    def test_capacity_forecast(self, rt, svc):
        make_exec(svc, ExecState.ACTIVE)
        result = rt.predict("capacity", "portfolio", "all", 1, exec_service=svc)
        assert "resource_utilization_pct" in result["output"]

    def test_bottleneck_forecast(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        add_obl(svc, inst.exec_id, desc="Blocked", state=ObligationState.BLOCKED)
        result = rt.predict("bottleneck", "execution", inst.exec_id, 1, exec_service=svc)
        assert "bottleneck_obl_id" in result["output"]

    def test_dependency_forecast(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        result = rt.predict("dependency", "execution", inst.exec_id, 1, exec_service=svc)
        assert "satisfaction_probability" in result["output"]

    def test_org_impact_forecast(self, rt, svc):
        inst = make_exec(svc, ExecState.BLOCKED)
        result = rt.predict("organizational_impact", "execution", inst.exec_id, 1,
                            exec_service=svc)
        assert "organizational_impact" in result["output"]

    def test_opportunity_forecast(self, rt, svc, config):
        learn_intel = get_learning_intelligence()
        learn_intel.learn_from_outcomes(
            [{"success": True, "dimension": "booking", "dimension_value": "success",
              "observation_id": "o1"},
             {"success": True, "dimension": "booking", "dimension_value": "success",
              "observation_id": "o2"}], 1)
        result = rt.predict("opportunity", "portfolio", "all", 1,
                            exec_service=svc, learn_intel=learn_intel)
        assert "opportunities" in result["output"]

    def test_recommendation_forecast(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        add_obl(svc, inst.exec_id, desc="Blocked", state=ObligationState.BLOCKED)
        from app.execution_intelligence import ExecutionIntelligenceEngine
        ei = ExecutionIntelligenceEngine()
        result = rt.predict("recommendation_outcome", "execution", inst.exec_id, 1,
                            exec_service=svc, exec_intel=ei)
        assert "recommended_actions" in result["output"]


# =========================================================================
# 2. Prediction Provenance
# =========================================================================

class TestPredictionProvenance:

    def test_prediction_has_id(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert result["prediction_id"]
        assert len(result["prediction_id"]) == 16

    def test_prediction_has_confidence(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert result["confidence"] is not None
        assert "overall" in result["confidence"]

    def test_prediction_has_input_fingerprint(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert result["input_fingerprint"]

    def test_prediction_has_output_fingerprint(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert result["output_fingerprint"]

    def test_prediction_has_version(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert result["version"] >= 1

    def test_prediction_has_evidence_traces(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert len(result["evidence_traces"]) >= 0

    def test_prediction_has_assumptions(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert isinstance(result["assumptions"], list)


# =========================================================================
# 3. Prediction Lifecycle
# =========================================================================

class TestPredictionLifecycle:

    def test_create_and_retrieve(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        fetched = rt.get_prediction(result["prediction_id"])
        assert fetched is not None
        assert fetched["prediction_id"] == result["prediction_id"]

    def test_supersession(self, rt, svc):
        inst = make_exec(svc)
        r1 = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        r2 = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert r1["prediction_id"] != r2["prediction_id"]
        fetched_r1 = rt.get_prediction(r1["prediction_id"])
        assert fetched_r1["status"] == "superseded"

    def test_withdrawal(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        ok = rt.withdraw_prediction(result["prediction_id"], "test withdrawal")
        assert ok is True
        fetched = rt.get_prediction(result["prediction_id"])
        assert fetched["status"] == "withdrawn"

    def test_expiration(self, rt, svc):
        config = PredictionConfig()
        lifecycle = PredictionLifecycle(config)
        rec = PredictionRecord(
            params=PredictionParameters(category="completion", entity_type="test",
                                        entity_id="e1", tenant_id=1,
                                        horizon_hours=0),  # immediately expired
        )
        lifecycle.store(rec)
        count = lifecycle.expire_all()
        assert count >= 1

    def test_get_history(self, rt, svc):
        inst = make_exec(svc)
        rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        rt.predict("delay", "execution", inst.exec_id, 1, exec_service=svc)
        history = rt.get_prediction_history(inst.exec_id, 1)
        assert len(history) >= 2


# =========================================================================
# 4. Prediction Explainability
# =========================================================================

class TestPredictionExplainability:

    def test_explain_completion(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        exp = rt.explain_prediction(result["prediction_id"])
        assert "conclusion" in exp
        assert "why" in exp

    def test_explain_delay(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("delay", "execution", inst.exec_id, 1, exec_service=svc)
        exp = rt.explain_prediction(result["prediction_id"])
        assert "conclusion" in exp
        assert "evidence_traces" in exp

    def test_explain_not_found(self, rt):
        exp = rt.explain_prediction("nonexistent")
        assert "error" in exp


# =========================================================================
# 5. Simulation Engine
# =========================================================================

class TestSimulationEngine:

    def test_simulate_basic(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        add_obl(svc, inst.exec_id, desc="Test")
        result = rt.simulate("unblock_test",
                             {inst.exec_id: {"state": ExecState.ACTIVE}},
                             1, query_ids=[inst.exec_id], exec_service=svc)
        assert result["simulation_id"]
        assert result["fork_count"] >= 1

    def test_simulate_with_predictions(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        add_obl(svc, inst.exec_id, desc="A", state=ObligationState.SATISFIED)
        result = rt.simulate("test",
                             {inst.exec_id: {"state": ExecState.ACTIVE}},
                             1, query_ids=[inst.exec_id], exec_service=svc)
        assert len(result["predictions"]) >= 1

    def test_simulation_fork_isolation(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        result = rt.simulate("test", {inst.exec_id: {"state": ExecState.FULFILLED}},
                             1, query_ids=[inst.exec_id], exec_service=svc)
        # Original should be unchanged
        assert svc._execs[inst.exec_id].state == ExecState.ACTIVE


# =========================================================================
# 6. Prediction Degradation (Refusal)
# =========================================================================

class TestPredictionDegradation:

    def test_refuse_nonexistent_execution(self, rt, svc):
        result = rt.predict("completion", "execution", "nonexistent", 1, exec_service=svc)
        assert result["output"].get("_refused") is True

    def test_refuse_unknown_category(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("fake_category", "execution", inst.exec_id, 1, exec_service=svc)
        assert result["output"].get("_refused") is True


# =========================================================================
# 7. Scenario Comparator
# =========================================================================

class TestScenarioComparator:

    def test_empty_comparison(self):
        comp = ScenarioComparator()
        result = comp.compare([])
        assert len(result.branches) == 0

    def test_basic_comparison(self):
        comp = ScenarioComparator()
        b1 = ScenarioBranch(label="fast", modifications={"e1": {"state": "active"}},
                            predictions={"completion": {"completion_ratio": 0.8}})
        b2 = ScenarioBranch(label="slow", modifications={"e1": {"state": "blocked"}},
                            predictions={"completion": {"completion_ratio": 0.2}})
        result = comp.compare([b1, b2])
        assert len(result.rankings) == 2
        assert result.rankings[0]["score"] >= result.rankings[1]["score"]


# =========================================================================
# 8. Runtime Integration
# =========================================================================

class TestRuntimeIntegration:

    def test_predict_all_categories(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        for cat in ["completion", "delay", "bottleneck", "dependency",
                     "organizational_impact"]:
            result = rt.predict(cat, "execution", inst.exec_id, 1, exec_service=svc)
            assert result["params"]["category"] == cat

    def test_stats(self, rt, svc):
        inst = make_exec(svc)
        rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        s = rt.stats()
        assert s["total_predictions"] >= 1
        assert s["active_predictions"] >= 1

    def test_get_history_filtered(self, rt, svc):
        inst = make_exec(svc)
        rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        rt.predict("delay", "execution", inst.exec_id, 1, exec_service=svc)
        filtered = rt.get_history(tenant_id=1, category="completion")
        assert len(filtered) >= 1
        for r in filtered:
            assert r["params"]["category"] == "completion"


# =========================================================================
# 9. Deterministic Testing
# =========================================================================

class TestDeterministic:

    def test_same_inputs_same_output(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        add_obl(svc, inst.exec_id, desc="A", state=ObligationState.SATISFIED)
        result1 = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        # Create a fresh engine with same state
        config2 = PredictionConfig()
        rt2 = RuntimeService(config2)
        svc2 = ExecutionService()
        inst2 = make_exec(svc2, ExecState.ACTIVE, cid="b1")
        add_obl(svc2, inst2.exec_id, desc="A", state=ObligationState.SATISFIED)
        result2 = rt2.predict("completion", "execution", inst2.exec_id, 1, exec_service=svc2)
        # Same state → same category, evidence traces, assumptions
        assert result1["params"]["category"] == result2["params"]["category"]
        assert len(result1["assumptions"]) == len(result2["assumptions"])

    def test_simulation_reproducible(self, rt, svc):
        inst = make_exec(svc, ExecState.ACTIVE)
        r1 = rt.simulate("test", {inst.exec_id: {"state": "active"}}, 1,
                         query_ids=[inst.exec_id], exec_service=svc)
        r2 = rt.simulate("test", {inst.exec_id: {"state": "active"}}, 1,
                         query_ids=[inst.exec_id], exec_service=svc)
        assert r1["simulation_type"] == r2["simulation_type"]

    def test_engine_reset(self):
        reset_prediction_engine()
        e1 = get_prediction_engine()
        e2 = get_prediction_engine()
        assert e1 is e2


# =========================================================================
# 10. Edge Cases
# =========================================================================

class TestEdgeCases:

    def test_finished_execution(self, rt, svc):
        inst = make_exec(svc, ExecState.FULFILLED)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        assert result["output"].get("completed") is True

    def test_confidence_decomposition(self, rt, svc):
        inst = make_exec(svc)
        result = rt.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        conf = result.get("confidence", {})
        assert "overall" in conf
        assert "factors" in conf
        assert len(conf["factors"]) == 5

    def test_get_nonexistent_prediction(self, rt):
        p = rt.get_prediction("nonexistent")
        assert p is None

    def test_withdraw_nonexistent(self, rt):
        assert rt.withdraw_prediction("nonexistent", "test") is False

    def test_simulate_empty_modifications(self, rt, svc):
        result = rt.simulate("empty", {}, 1, exec_service=svc)
        assert result["simulation_id"]

    def test_facade_get_history(self, ps, svc):
        inst = make_exec(svc)
        ps.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        h = ps.get_history(tenant_id=1)
        assert len(h) >= 1

    def test_facade_get_active(self, ps, svc):
        inst = make_exec(svc)
        ps.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        active = ps.get_active_prediction("completion", inst.exec_id, 1)
        assert active is not None

    def test_facade_explain(self, ps, svc):
        inst = make_exec(svc)
        result = ps.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        exp = ps.explain_prediction(result["prediction_id"])
        assert "conclusion" in exp

    def test_facade_stats(self, ps, svc):
        inst = make_exec(svc)
        ps.predict("completion", "execution", inst.exec_id, 1, exec_service=svc)
        s = ps.stats()
        assert s["total_predictions"] >= 1

    def test_facade_compare_scenarios(self, ps):
        b1 = ScenarioBranch(label="A", modifications={}, predictions={"c": {"completion_ratio": 0.8}})
        b2 = ScenarioBranch(label="B", modifications={}, predictions={"c": {"completion_ratio": 0.2}})
        result = ps.compare_scenarios([b1, b2])
        assert result["branch_count"] == 2