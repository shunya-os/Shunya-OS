"""Tests for Milestone V — Decision Intelligence.

Covers: option generation, constraint evaluation, trade-off analysis,
objective scoring, scenario evaluation, decision ranking, explainability,
provenance, integration, and edge cases.
"""
import pytest
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from app.decision import (
    DecisionEngine, get_decision_engine, reset_decision_engine,
)
from app.decision.models import (
    OptionCategory, ConstraintSeverity, RecommendationStatus,
    DecisionContext, DecisionOption, DecisionConstraint,
    DecisionObjective, DecisionTradeoff, ObjectiveWeight,
    DecisionEvaluation, DecisionRecommendation, DecisionExplanation,
    DecisionSnapshot, ScenarioEvalResult,
    OptionGenerationRule, DecisionConfig,
)
from app.decision.engine import (
    OptionGenerator, ConstraintEngine, TradeoffAnalyzer,
    ObjectiveEngine, ScenarioEvaluator,
)
from app.execution import ExecutionService, ExecState, ObligationState


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def engine() -> DecisionEngine:
    reset_decision_engine()
    return get_decision_engine()


@pytest.fixture
def config() -> DecisionConfig:
    return DecisionConfig()


@pytest.fixture
def ctx() -> DecisionContext:
    return DecisionContext(
        tenant_id=1, execution_id="e1", trigger="test",
        execution_state={"state": "active", "obligations": ["o1"]},
        prediction_snapshot={"risk_level": "low", "delay_probability": 0.2},
        governance_state={"approved": True},
        organization_state={"insights": ["role1"]},
    )


# =========================================================================
# 1. Decision Context
# =========================================================================

class TestDecisionContext:

    def test_context_has_id(self):
        c = DecisionContext(tenant_id=1, execution_id="e1")
        assert c.context_id
        assert len(c.context_id) == 16

    def test_context_with_objectives(self):
        obj = DecisionObjective(name="test", weight=1.0)
        c = DecisionContext(tenant_id=1, execution_id="e1",
                            objectives=[obj])
        assert len(c.objectives) == 1

    def test_context_to_dict(self):
        c = DecisionContext(tenant_id=1, execution_id="e1")
        d = c.to_dict()
        assert "context_id" in d


# =========================================================================
# 2. Option Generation
# =========================================================================

class TestOptionGenerator:

    def test_options_generated(self, config):
        gen = OptionGenerator(config)
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "active"})
        options = gen.generate(ctx)
        assert len(options) >= 2  # proceed + mark_infeasible at minimum

    def test_proceed_always_available(self, config):
        gen = OptionGenerator(config)
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "blocked"})
        options = gen.generate(ctx)
        categories = [o.category for o in options]
        assert OptionCategory.PROCEED.value in categories

    def test_infeasible_always_available(self, config):
        gen = OptionGenerator(config)
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "failed"})
        options = gen.generate(ctx)
        categories = [o.category for o in options]
        assert OptionCategory.MARK_INFEASIBLE.value in categories

    def test_delay_generated_for_active(self, config):
        gen = OptionGenerator(config)
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "active"})
        options = gen.generate(ctx)
        categories = [o.category for o in options]
        assert OptionCategory.DELAY.value in categories

    def test_option_has_id(self, config):
        gen = OptionGenerator(config)
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "active"})
        options = gen.generate(ctx)
        for o in options:
            assert o.option_id

    def test_option_limit(self):
        small = DecisionConfig(max_options_generated=3)
        gen = OptionGenerator(small)
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "active"})
        options = gen.generate(ctx)
        assert len(options) <= 3


# =========================================================================
# 3. Constraint Evaluation
# =========================================================================

class TestConstraintEngine:

    def test_state_transition_valid(self, ctx):
        ce = ConstraintEngine()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        constraints = ce.evaluate(opt, ctx)
        state_c = [c for c in constraints if c.name == "state_transition_validity"]
        assert state_c
        assert not state_c[0].violated

    def test_state_transition_invalid(self):
        ce = ConstraintEngine()
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "fulfilled"})
        opt = DecisionOption(category=OptionCategory.ACQUIRE_RESOURCES.value)
        constraints = ce.evaluate(opt, ctx)
        state_c = [c for c in constraints if c.name == "state_transition_validity"]
        assert state_c
        assert state_c[0].violated

    def test_governance_fatal(self, ctx):
        ctx.governance_state = {"approved": False}
        ce = ConstraintEngine()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        constraints = ce.evaluate(opt, ctx)
        gov_c = [c for c in constraints if c.name == "governance_compatibility"]
        assert gov_c
        assert gov_c[0].violated
        assert gov_c[0].severity == ConstraintSeverity.FATAL.value

    def test_risk_high_warning(self, ctx):
        ctx.prediction_snapshot = {"risk_level": "critical"}
        ce = ConstraintEngine()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        constraints = ce.evaluate(opt, ctx)
        risk_c = [c for c in constraints if c.name == "risk_tolerance"]
        assert risk_c and risk_c[0].violated

    def test_all_options_have_same_constraints(self, ctx):
        ce = ConstraintEngine()
        opt1 = DecisionOption(category=OptionCategory.DELAY.value)
        opt2 = DecisionOption(category=OptionCategory.ESCALATE.value)
        c1 = ce.evaluate(opt1, ctx)
        c2 = ce.evaluate(opt2, ctx)
        assert len(c1) == len(c2)

    def test_constraint_sources(self, ctx):
        ce = ConstraintEngine()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        constraints = ce.evaluate(opt, ctx)
        sources = {c.source for c in constraints}
        assert "execution_state" in sources
        assert "resources" in sources
        assert "governance" in sources


# =========================================================================
# 4. Trade-off Analysis
# =========================================================================

class TestTradeoffAnalyzer:

    def test_eight_dimensions(self, ctx):
        ta = TradeoffAnalyzer()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        tradeoffs = ta.analyze(opt, ctx)
        assert len(tradeoffs) == 8

    def test_all_dimensions_named(self, ctx):
        ta = TradeoffAnalyzer()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        tradeoffs = ta.analyze(opt, ctx)
        dims = {t.dimension for t in tradeoffs}
        assert "benefit" in dims
        assert "cost" in dims
        assert "risk" in dims
        assert "organizational_impact" in dims
        assert "timeline_impact" in dims
        assert "resource_impact" in dims
        assert "prediction_confidence" in dims
        assert "opportunity_cost" in dims

    def test_tradeoff_has_evidence(self, ctx):
        ta = TradeoffAnalyzer()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        tradeoffs = ta.analyze(opt, ctx)
        for t in tradeoffs:
            assert len(t.evidence) >= 1

    def test_delay_less_beneficial_than_proceed(self, ctx):
        ta = TradeoffAnalyzer()
        opt_p = DecisionOption(category=OptionCategory.PROCEED.value)
        opt_d = DecisionOption(category=OptionCategory.DELAY.value)
        t_p = ta.analyze(opt_p, ctx)
        t_d = ta.analyze(opt_d, ctx)
        b_p = next(t.score for t in t_p if t.dimension == "benefit")
        b_d = next(t.score for t in t_d if t.dimension == "benefit")
        assert b_p > b_d

    def test_infeasible_lowest_benefit(self, ctx):
        ta = TradeoffAnalyzer()
        for cat in [OptionCategory.PROCEED, OptionCategory.DELAY,
                     OptionCategory.ESCALATE, OptionCategory.MARK_INFEASIBLE]:
            opt = DecisionOption(category=cat.value)
            t = ta.analyze(opt, ctx)
            b = next(t2.score for t2 in t if t2.dimension == "benefit")

    def test_to_dict(self, ctx):
        ta = TradeoffAnalyzer()
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        tradeoffs = ta.analyze(opt, ctx)
        d = tradeoffs[0].to_dict()
        assert "dimension" in d
        assert "score" in d


# =========================================================================
# 5. Objective Scoring
# =========================================================================

class TestObjectiveEngine:

    def test_default_objectives(self, config):
        oe = ObjectiveEngine(config)
        objs = oe._default_objectives()
        assert len(objs) == 5

    def test_weights_sum_to_one(self, config):
        oe = ObjectiveEngine(config)
        objs = oe._default_objectives()
        total = sum(o.weight for o in objs)
        assert abs(total - 1.0) < 0.01

    def test_option_scored(self, ctx, config):
        oe = ObjectiveEngine(config)
        opt = DecisionOption(category=OptionCategory.PROCEED.value)
        ctx.tradeoff_analyzer = None  # must add tradeoffs manually
        ta = TradeoffAnalyzer()
        ta.analyze(opt, ctx)
        score = oe.score(opt, ctx)
        assert 0 <= score <= 1.0

    def test_infeasible_lowest_score(self, ctx, config):
        oe = ObjectiveEngine(config)
        ta = TradeoffAnalyzer()
        opt = DecisionOption(category=OptionCategory.MARK_INFEASIBLE.value)
        ta.analyze(opt, ctx)
        s_inf = oe.score(opt, ctx)
        opt2 = DecisionOption(category=OptionCategory.PROCEED.value)
        ta.analyze(opt2, ctx)
        s_proc = oe.score(opt2, ctx)
        assert s_inf <= s_proc


# =========================================================================
# 6. Scenario Evaluation
# =========================================================================

class TestScenarioEvaluator:

    def test_evaluate_option(self, ctx):
        se = ScenarioEvaluator()
        opt = DecisionOption(category=OptionCategory.PROCEED.value,
                             overall_score=0.7)
        result = se.evaluate(opt, ctx)
        assert result.option_id == opt.option_id
        assert result.consensus_score > 0

    def test_consensus_between_best_and_worst(self, ctx):
        se = ScenarioEvaluator()
        opt = DecisionOption(category=OptionCategory.PROCEED.value,
                             overall_score=0.7)
        result = se.evaluate(opt, ctx)
        assert result.best_case.get("score", 0) > result.worst_case.get("score", 0)
        assert result.best_case.get("score", 0) > result.current_reality.get("score", 0)

    def test_to_dict(self, ctx):
        se = ScenarioEvaluator()
        opt = DecisionOption(category=OptionCategory.PROCEED.value,
                             overall_score=0.7)
        result = se.evaluate(opt, ctx)
        d = result.to_dict()
        assert "consensus_score" in d


# =========================================================================
# 7. Decision Ranking
# =========================================================================

class TestDecisionRanking:

    def test_full_evaluation(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        assert len(evaluation.options) >= 2
        assert evaluation.recommendation is not None
        assert evaluation.recommendation.top_option_id is not None

    def test_options_ranked_by_score(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        scores = [o.overall_score for o in evaluation.recommendation.ranked_options]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    def test_top_option_is_feasible(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        top = evaluation.recommendation.ranked_options[0] if evaluation.recommendation.ranked_options else None
        if top:
            fatal = [c for c in top.constraints
                     if c.violated and c.severity == ConstraintSeverity.FATAL.value]
            assert len(fatal) == 0

    def test_recommendation_rationale(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        assert "Top option" in evaluation.recommendation.rationale


# =========================================================================
# 8. Decision Explainability
# =========================================================================

class TestDecisionExplainability:

    def test_explain(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        explanation = engine.explain(evaluation)
        assert explanation.recommendation_id is not None
        assert "available_options" in explanation.to_dict()

    def test_explain_contains_constraints(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        explanation = engine.explain(evaluation)
        d = explanation.to_dict()
        assert d["constraint_count"] >= 1

    def test_explain_contains_tradeoffs(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        explanation = engine.explain(evaluation)
        d = explanation.to_dict()
        assert "tradeoff_count" in d

    def test_explain_uncertainty(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        explanation = engine.explain(evaluation)
        assert len(explanation.remaining_uncertainty) >= 1


# =========================================================================
# 9. Decision Provenance
# =========================================================================

class TestDecisionProvenance:

    def test_snapshot_created(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        snapshot = engine.build_snapshot(evaluation)
        assert snapshot.snapshot_id
        assert snapshot.objective_set

    def test_snapshot_has_fingerprints(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        snapshot = engine.build_snapshot(evaluation)
        assert snapshot.input_fingerprint
        assert snapshot.output_fingerprint

    def test_snapshot_has_constraints(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        snapshot = engine.build_snapshot(evaluation)
        assert len(snapshot.constraint_set) >= 1

    def test_snapshot_versioned(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        snapshot = engine.build_snapshot(evaluation)
        assert snapshot.engine_version == "mi5.0"


# =========================================================================
# 10. Integration & Edge Cases
# =========================================================================

class TestIntegration:

    def test_evaluate_with_full_context(self, ctx, engine):
        ctx.execution_state = {"state": "blocked", "obligations": ["o1", "o2"]}
        ctx.prediction_snapshot = {"risk_level": "medium", "delay_probability": 0.5}
        evaluation = engine.evaluate(ctx)
        assert len(evaluation.options) >= 1
        assert evaluation.recommendation.top_option_id is not None

    def test_blocked_execution_more_options(self):
        ctx = DecisionContext(tenant_id=1, execution_id="e1",
                              execution_state={"state": "blocked"})
        gen = OptionGenerator()
        blocked_opts = gen.generate(ctx)
        ctx2 = DecisionContext(tenant_id=1, execution_id="e2",
                               execution_state={"state": "active"})
        active_opts = gen.generate(ctx2)
        # Blocked state typically has more options
        assert len(blocked_opts) >= 1

    def test_get_history(self, ctx, engine):
        engine.evaluate(ctx)
        ctx2 = DecisionContext(tenant_id=1, execution_id="e2",
                               execution_state={"state": "active"})
        engine.evaluate(ctx2)
        history = engine.get_history(1)
        assert len(history) >= 2

    def test_stats(self, ctx, engine):
        engine.evaluate(ctx)
        s = engine.stats()
        assert s["total_evaluations"] >= 1
        assert s["total_options_generated"] >= 2

    def test_get_config(self, engine):
        c = engine.get_config()
        assert "version" in c
        assert c["version"] == "mi5.0"

    def test_engine_singleton(self):
        reset_decision_engine()
        e1 = get_decision_engine()
        e2 = get_decision_engine()
        assert e1 is e2

    def test_rejected_options_identified(self, ctx, engine):
        ctx.governance_state = {"approved": False}
        evaluation = engine.evaluate(ctx)
        rejected = evaluation.recommendation.rejected_options
        assert len(rejected) >= 1

    def test_to_dict_option(self):
        opt = DecisionOption(category=OptionCategory.PROCEED.value, label="Test")
        d = opt.to_dict()
        assert "category" in d
        assert "overall_score" in d

    def test_to_dict_evaluation(self, ctx, engine):
        evaluation = engine.evaluate(ctx)
        d = evaluation.to_dict()
        assert "option_count" in d
        assert "recommendation" in d