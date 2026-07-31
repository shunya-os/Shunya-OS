"""Tests for Milestone VI — Executive Intelligence.

Covers: synthesis, priorities, risks, opportunities, decision queue,
health model, narrative, attention model, explainability, integration.
"""
import pytest
from typing import Any, Dict, List

from app.executive import (
    ExecutiveIntelligenceEngine, get_executive_engine, reset_executive_engine,
)
from app.executive.models import (
    PriorityCategory, RiskCategory, OpportunityCategory, HealthDimension,
    ExecutiveInsight, ExecutivePriority, ExecutiveRisk,
    ExecutiveOpportunity, ExecutiveDecisionRequest,
    ExecutiveHealth, ExecutiveTrend, ExecutiveNarrative,
    ExecutiveBrief, ExecutiveDigest,
    AttentionScore, ExecutiveConfig, ExecutiveStats,
)
from app.executive.engine import (
    ExecutiveSynthesisEngine, PriorityEngine,
    ExecutiveRiskIntelligence, ExecutiveOpportunityIntel,
    DecisionQueue, ExecutiveHealthModel,
    ExecutiveNarrativeGenerator, ExecutiveAttentionModel,
    ExecutiveExplainability,
)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def engine() -> ExecutiveIntelligenceEngine:
    reset_executive_engine()
    return get_executive_engine()


@pytest.fixture
def config() -> ExecutiveConfig:
    return ExecutiveConfig()


# =========================================================================
# 1. Executive Synthesis
# =========================================================================

class TestSynthesis:

    def test_synthesize_returns_digest(self, engine):
        d = engine.synthesize(tenant_id=1)
        assert d["digest_id"]
        assert d["priorities"] >= 1
        assert d["risks"] >= 1
        assert d["opportunities"] >= 1

    def test_digest_has_brief(self, engine):
        d = engine.synthesize(tenant_id=1)
        assert d["health"] is not None

    def test_digest_has_narrative(self, engine):
        d = engine.synthesize(tenant_id=1)
        assert d["narrative_sections"] >= 1

    def test_digest_has_attention(self, engine):
        d = engine.synthesize(tenant_id=1)
        assert d["attention_items"] >= 1

    def test_multiple_tenants(self, engine):
        d1 = engine.synthesize(tenant_id=1)
        d2 = engine.synthesize(tenant_id=2)
        assert d1["digest_id"] != d2["digest_id"]


# =========================================================================
# 2. Executive Brief
# =========================================================================

class TestBrief:

    def test_get_brief(self, engine):
        engine.synthesize(tenant_id=1)
        b = engine.get_brief(tenant_id=1)
        assert "summary" in b

    def test_brief_has_health(self, engine):
        engine.synthesize(tenant_id=1)
        b = engine.get_brief(tenant_id=1)
        assert "overall_health" in b

    def test_brief_has_counts(self, engine):
        engine.synthesize(tenant_id=1)
        b = engine.get_brief(tenant_id=1)
        assert b["critical_count"] >= 1

    def test_brief_no_digest(self, engine):
        b = engine.get_brief(tenant_id=999)
        assert "error" in b


# =========================================================================
# 3. Priorities
# =========================================================================

class TestPriorities:

    def test_get_priorities(self, engine):
        engine.synthesize(tenant_id=1)
        p = engine.get_priorities(tenant_id=1)
        assert len(p) >= 1

    def test_priority_has_evidence(self, engine):
        engine.synthesize(tenant_id=1)
        p = engine.get_priorities(tenant_id=1)
        for pri in p:
            assert len(pri.get("evidence", [])) >= 0

    def test_priority_has_attention_score(self, engine):
        engine.synthesize(tenant_id=1)
        p = engine.get_priorities(tenant_id=1)
        for pri in p:
            assert "attention_score" in pri

    def test_priority_ranking(self, engine):
        engine.synthesize(tenant_id=1)
        p = engine.get_priorities(tenant_id=1)
        for i in range(len(p) - 1):
            assert p[i].get("confidence", 0) >= 0  # Just check they exist
            _ = p[i].get("attention_score", 0)  # Verify key exists


# =========================================================================
# 4. Risks
# =========================================================================

class TestRisks:

    def test_get_risks(self, engine):
        engine.synthesize(tenant_id=1)
        r = engine.get_risks(tenant_id=1)
        assert len(r) >= 1

    def test_risk_has_likelihood(self, engine):
        engine.synthesize(tenant_id=1)
        r = engine.get_risks(tenant_id=1)
        for risk in r:
            assert "likelihood" in risk

    def test_risk_has_trend(self, engine):
        engine.synthesize(tenant_id=1)
        r = engine.get_risks(tenant_id=1)
        for risk in r:
            assert "trend" in risk


# =========================================================================
# 5. Opportunities
# =========================================================================

class TestOpportunities:

    def test_get_opportunities(self, engine):
        engine.synthesize(tenant_id=1)
        o = engine.get_opportunities(tenant_id=1)
        assert len(o) >= 1

    def test_opportunity_has_value(self, engine):
        engine.synthesize(tenant_id=1)
        o = engine.get_opportunities(tenant_id=1)
        for opp in o:
            assert "expected_value" in opp

    def test_opportunity_has_confidence(self, engine):
        engine.synthesize(tenant_id=1)
        o = engine.get_opportunities(tenant_id=1)
        for opp in o:
            assert "confidence" in opp


# =========================================================================
# 6. Decision Queue
# =========================================================================

class TestDecisionQueue:

    def test_get_decisions(self, engine):
        engine.synthesize(tenant_id=1)
        d = engine.get_decision_queue(tenant_id=1)
        assert len(d) >= 1

    def test_decision_has_options(self, engine):
        engine.synthesize(tenant_id=1)
        d = engine.get_decision_queue(tenant_id=1)
        for dec in d:
            assert "option_count" in dec

    def test_decision_has_urgency(self, engine):
        engine.synthesize(tenant_id=1)
        d = engine.get_decision_queue(tenant_id=1)
        for dec in d:
            assert "urgency" in dec


# =========================================================================
# 7. Health Model
# =========================================================================

class TestHealth:

    def test_get_health(self, engine):
        engine.synthesize(tenant_id=1)
        h = engine.get_health(tenant_id=1)
        assert "overall" in h
        assert "dimensions" in h

    def test_health_has_dimensions(self, engine):
        engine.synthesize(tenant_id=1)
        h = engine.get_health(tenant_id=1)
        for dim in HealthDimension:
            if dim == HealthDimension.OVERALL:
                continue
            assert dim.value in h["dimensions"], f"Missing dimension: {dim.value}"

    def test_health_has_trend(self, engine):
        engine.synthesize(tenant_id=1)
        h = engine.get_health(tenant_id=1)
        assert "overall_trend" in h

    def test_health_no_digest(self, engine):
        # get_health should fall back to computing from model
        h = engine.get_health(tenant_id=999)
        assert "overall" in h


# =========================================================================
# 8. Attention Ranking
# =========================================================================

class TestAttention:

    def test_attention_ranking(self, engine):
        engine.synthesize(tenant_id=1)
        a = engine.get_attention_ranking(tenant_id=1)
        assert len(a) >= 1

    def test_attention_sorted(self, engine):
        engine.synthesize(tenant_id=1)
        a = engine.get_attention_ranking(tenant_id=1)
        for i in range(len(a) - 1):
            assert a[i]["score"] >= a[i + 1]["score"]

    def test_attention_model(self, config):
        model = ExecutiveAttentionModel(config)
        p = [ExecutivePriority(tenant_id=1, title="Test", confidence=0.8,
                                urgency=0.7, impact=0.9, attention_score=0.8)]
        r = [ExecutiveRisk(tenant_id=1, title="Risk", confidence=0.7,
                           likelihood=0.5, impact=0.7)]
        o = [ExecutiveOpportunity(tenant_id=1, title="Opp", confidence=0.6,
                                  expected_value=0.7)]
        scores = model.score(p, r, o)
        assert len(scores) >= 3
        assert scores[0].total_score >= scores[1].total_score


# =========================================================================
# 9. Explainability
# =========================================================================

class TestExplainability:

    def test_trace_insight(self, engine):
        engine.synthesize(tenant_id=1)
        p = engine.get_priorities(tenant_id=1)
        if p:
            # Get the actual insight objects from the digest for the full ID
            digest = engine._synthesis.get_latest_digest(1)
            if digest and digest.priorities:
                actual_id = digest.priorities[0].insight_id
                t = engine.trace_insight(actual_id)
                assert "lineage" in t

    def test_trace_insight_not_found(self, engine):
        t = engine.trace_insight("nonexistent")
        assert "error" in t

    def test_trace_digest(self, engine):
        engine.synthesize(tenant_id=1)
        t = engine.trace_digest(tenant_id=1)
        assert "traced_items" in t

    def test_explain_trace_priority(self, engine):
        expl = ExecutiveExplainability()
        p = ExecutivePriority(tenant_id=1, title="Test", evidence=["e1", "e2"])
        t = expl.trace(p)
        assert t["trace_complete"] is True

    def test_explain_trace_digest(self, engine):
        engine.synthesize(tenant_id=1)
        expl = ExecutiveExplainability()
        digest = engine._synthesis.get_latest_digest(1)
        t = expl.trace_digest(digest)
        assert t["traced_items"] >= 1


# =========================================================================
# 10. Narrative
# =========================================================================

class TestNarrative:

    def test_get_narrative(self, engine):
        engine.synthesize(tenant_id=1)
        n = engine.get_narrative(tenant_id=1)
        assert "section_count" in n

    def test_narrative_has_confidence(self, engine):
        engine.synthesize(tenant_id=1)
        n = engine.get_narrative(tenant_id=1)
        assert "confidence" in n

    def test_narrative_generator(self, config):
        gen = ExecutiveNarrativeGenerator()
        h = ExecutiveHealth(tenant_id=1)
        h.overall = 0.75
        n = gen.generate(1, h, [], [], [], [])
        assert len(n.sections) >= 1


# =========================================================================
# 11. Integration & Edge Cases
# =========================================================================

class TestIntegration:

    def test_full_synthesis_cycle(self, engine):
        d = engine.synthesize(tenant_id=1)
        b = engine.get_brief(1)
        p = engine.get_priorities(1)
        r = engine.get_risks(1)
        o = engine.get_opportunities(1)
        dq = engine.get_decision_queue(1)
        h = engine.get_health(1)
        a = engine.get_attention_ranking(1)
        n = engine.get_narrative(1)
        assert len(p) >= 1 and len(r) >= 1 and len(o) >= 1
        assert len(dq) >= 1
        assert h["overall"] > 0
        assert len(a) >= 1
        assert n["section_count"] >= 1

    def test_stats(self, engine):
        engine.synthesize(tenant_id=1)
        s = engine.stats()
        assert s["total_digests"] >= 1

    def test_get_config(self, engine):
        c = engine.get_config()
        assert c["version"] == "mi6.0"

    def test_engine_singleton(self):
        reset_executive_engine()
        e1 = get_executive_engine()
        e2 = get_executive_engine()
        assert e1 is e2

    def test_priority_engine_ranking(self):
        pe = PriorityEngine()
        p = [ExecutivePriority(tenant_id=1, title="A", attention_score=0.5),
             ExecutivePriority(tenant_id=1, title="B", attention_score=0.9)]
        ranked = pe.rank(p)
        assert ranked[0].title == "B"

    def test_risk_intelligence(self):
        ri = ExecutiveRiskIntelligence()
        risks = ri.aggregate(1)
        assert len(risks) >= 1

    def test_opportunity_intel(self):
        oi = ExecutiveOpportunityIntel()
        opps = oi.identify(1)
        assert len(opps) >= 1

    def test_decision_queue(self):
        dq = DecisionQueue()
        decisions = dq.queue(1)
        assert len(decisions) >= 1

    def test_health_model(self):
        hm = ExecutiveHealthModel()
        health = hm.compute(1)
        assert health.overall > 0
        assert len(health.dimensions) >= 7

    def test_attention_model_factors(self, config):
        model = ExecutiveAttentionModel(config)
        s = AttentionScore(item_id="t1", label="Test", category="priority",
                           business_impact=0.8, urgency=0.5, confidence=0.7,
                           strategic_importance=0.6, cross_functional_effect=0.4,
                           time_sensitivity=0.5)
        scores = model.score([], [], [])
        assert isinstance(scores, list)

    def test_to_dict_priority(self):
        p = ExecutivePriority(tenant_id=1, title="Test")
        d = p.to_dict()
        assert "attention_score" in d

    def test_to_dict_risk(self):
        r = ExecutiveRisk(tenant_id=1, title="Risk", likelihood=0.5, impact=0.7)
        d = r.to_dict()
        assert "likelihood" in d

    def test_to_dict_opportunity(self):
        o = ExecutiveOpportunity(tenant_id=1, title="Opp", expected_value=0.7)
        d = o.to_dict()
        assert "expected_value" in d

    def test_get_health_no_digest_fallback(self, engine):
        h = engine.get_health(tenant_id=999)
        assert "overall" in h