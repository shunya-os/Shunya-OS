"""Tests for Phase F — Reasoning Engine (Canonical Architecture).

Covers:
  - Unit tests for all canonical models (Finding, Contradiction, etc.)
  - Deprecated alias compatibility (Observation, Conflict, Gap, Risk)
  - Rule tests for all standard rules (19 total)
  - Contradiction detection tests (including stale context)
  - Confidence scoring tests
  - Determinism tests (identical inputs -> identical outputs)
  - Concurrency tests
  - Failure-path tests
  - Integration tests with Event Bus, Metrics, Health
"""

import threading
import pytest
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta

from app.shunya.reasoning.models import (
    ReasoningResult, Finding, Contradiction, Assumption, Constraint,
    ConfidenceScore, EvidenceReference, ReasoningMetadata,
    FindingType, FindingSeverity, ContradictionType,
    ContradictionSeverity, ConfidenceLevel,
    # Deprecated aliases
    Observation, Conflict, Gap, Risk,
    ConfidenceAssessment, ConflictSeverity, GapSeverity, RiskSeverity,
)
from app.shunya.reasoning.engine import ReasoningEngine, get_reasoning_engine, reset_reasoning_engine
from app.shunya.reasoning.registry import RuleRegistry, RuleDefinition, RuleResult
from app.shunya.reasoning.confidence import ConfidenceEngine
from app.shunya.reasoning.evidence_graph import EvidenceGraph, EvidenceNode
from app.shunya.reasoning.rules import (
    register_standard_rules, ALL_STANDARD_RULES,
    OBSERVATION_RULES, GAP_RULES, CONTRADICTION_RULES, RISK_RULES, ATTENTION_RULES,
    rule_identity_present, rule_knowledge_present, rule_request_context_present,
    rule_missing_identity, rule_missing_knowledge, rule_missing_tenant,
    rule_missing_actor, rule_missing_purpose, rule_missing_fingerprint,
    rule_identity_degraded_contradiction, rule_knowledge_degraded_contradiction,
    rule_budget_truncation_contradiction, rule_stale_context_contradiction,
    rule_degraded_context_risk, rule_missing_identity_risk,
    rule_budget_truncation_risk, rule_no_evidence_risk,
    rule_attention_items, rule_context_fingerprint,
    make_rule,
)


# ---------------------------------------------------------------------------
# Helper: create a mock context
# ---------------------------------------------------------------------------


class MockSection:
    def __init__(self, provider: str = "", items: List[Dict[str, Any]] = None,
                 is_degraded: bool = False):
        self.provider = provider
        self.items = items or []
        self.is_degraded = is_degraded
        self.item_count = len(self.items)


class MockBudget:
    def __init__(self, total_items: int = 0, max_items: int = 100,
                 truncated: bool = False):
        self.total_items = total_items
        self.max_items = max_items
        self.truncated = truncated


class MockContext:
    def __init__(self, context_id: str = "ctx-1", tenant_id: int = 1,
                 actor_id: str = "actor-1", purpose_code: str = "test",
                 fingerprint: str = "fp-abc123", is_degraded: bool = False,
                 sections: Dict[str, Any] = None,
                 budget: Any = None, created_at: Optional[datetime] = None):
        self.context_id = context_id
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.purpose_code = purpose_code
        self.fingerprint = fingerprint
        self.is_degraded = is_degraded
        self.sections = sections or {}
        self.budget = budget
        self.created_at = created_at


def make_full_context() -> MockContext:
    return MockContext(
        context_id="ctx-full", tenant_id=1, actor_id="user-1",
        purpose_code="inquiry", fingerprint="fp-abc123def456",
        sections={
            "identity": MockSection("identity", [{"id": 1, "email": "user@test.com"}], False),
            "knowledge": MockSection("knowledge", [{"id": 10, "fact": "dest_maldives"}], False),
            "request": MockSection("request", [{"tenant_id": 1, "actor_id": "user-1"}], False),
        },
        budget=MockBudget(total_items=3, max_items=100, truncated=False),
    )


# ===========================================================================
# Test: Canonical Models
# ===========================================================================


class TestCanonicalModels:
    def test_finding_observation(self):
        f = Finding(finding_type="observation", fact_key="k", fact_value=True,
                    label="Test", source="test", confidence=0.95)
        assert f.finding_id and f.finding_type == "observation" and f.created_at
        d = f.to_dict()
        assert d["finding_type"] == "observation"
        assert d["fact_key"] == "k"

    def test_finding_gap(self):
        f = Finding(finding_type="gap", severity="blocking", fact_key="m",
                    label="Missing", source="test")
        assert f.finding_type == "gap" and f.severity == "blocking"

    def test_finding_risk(self):
        f = Finding(finding_type="risk", severity="high", fact_key="r",
                    label="Risk", source="test")
        assert f.finding_type == "risk" and f.severity == "high"

    def test_contradiction(self):
        c = Contradiction(contradiction_type="fact_conflict", severity="high",
                          label="Conflict", fact_keys=["a", "b"], sources=["s1", "s2"])
        assert c.contradiction_id and c.contradiction_type == "fact_conflict"
        d = c.to_dict()
        assert d["contradiction_type"] == "fact_conflict"

    def test_contradiction_types(self):
        for ct in ["fact_conflict", "assumption_conflict", "stale_context",
                    "incomplete_evidence", "duplicate_finding"]:
            c = Contradiction(contradiction_type=ct, severity="medium")
            assert c.contradiction_type == ct
        assert hasattr(ContradictionType, "STALE_CONTEXT")

    def test_assumption(self):
        a = Assumption(fact_key="ak", label="Test assumption", assumed_value=True)
        assert a.assumption_id and a.fact_key == "ak"

    def test_constraint(self):
        ct = Constraint(fact_key="ck", constraint_type="boundary", label="Max", value=100)
        assert ct.constraint_id and ct.constraint_type == "boundary"

    def test_confidence_score(self):
        cs = ConfidenceScore(overall_score=0.85, total_findings=10)
        assert cs.compute_level(0.95) == "very_high"
        assert cs.compute_level(0.75) == "high"
        assert cs.compute_level(0.60) == "medium"
        assert cs.compute_level(0.40) == "low"
        assert cs.compute_level(0.15) == "very_low"
        assert cs.compute_level(-1.0) == "insufficient"

    def test_reasoning_result_with_new_types(self):
        obs = Finding(finding_type="observation", fact_key="o", source="t")
        gap = Finding(finding_type="gap", severity="blocking", fact_key="g", source="t")
        risk = Finding(finding_type="risk", severity="high", fact_key="r", source="t")
        c = Contradiction(contradiction_type="fact_conflict", severity="high",
                          label="X", fact_keys=["a"], sources=["s"])
        a = Assumption(fact_key="ak", label="Test assumption")
        ct = Constraint(fact_key="ck", constraint_type="boundary")
        cs = ConfidenceScore(overall_score=0.85)
        result = ReasoningResult(
            findings=[obs, gap, risk], contradictions=[c],
            assumptions=[a], constraints=[ct], confidence=cs)
        assert len(result.findings) == 3
        assert len(result.observations) == 1
        assert len(result.gaps) == 1
        assert len(result.risks) == 1
        assert result.has_contradictions and result.has_gaps and result.has_risks
        assert result.requires_attention

    def test_reasoning_result_properties(self):
        c = Contradiction(contradiction_type="fact_conflict", severity="critical",
                          label="Critical", fact_keys=["a"], sources=["s"])
        g = Finding(finding_type="gap", severity="blocking", fact_key="m", source="t")
        cs = ConfidenceScore(overall_score=0.85)
        result = ReasoningResult(contradictions=[c], findings=[g], confidence=cs)
        assert result.is_healthy is False  # critical contradiction + blocking gap

    def test_evidence_reference_helpers(self):
        assert EvidenceReference.from_knowledge_object("o1", "k1").reference_type == "knowledge"
        assert EvidenceReference.from_identity("id1").reference_type == "identity"
        assert EvidenceReference.from_context("c1").reference_type == "context"
        assert EvidenceReference.from_external("ext", "http://ex.com").reference_type == "external"


# ===========================================================================
# Test: Deprecated Alias Compatibility
# ===========================================================================


class TestDeprecatedAliases:
    def test_observation_is_finding(self):
        obs = Observation(fact_key="k", source="t")
        assert isinstance(obs, Finding)
        assert obs.finding_type == "observation"

    def test_gap_is_finding(self):
        g = Gap(finding_type="gap", severity="blocking", fact_key="m", source="t")
        assert isinstance(g, Finding)
        assert g.finding_type == "gap" and g.severity == "blocking"

    def test_risk_is_finding(self):
        r = Risk(finding_type="risk", severity="high", fact_key="r", source="t")
        assert isinstance(r, Finding)
        assert r.finding_type == "risk" and r.severity == "high"

    def test_conflict_is_contradiction(self):
        c = Conflict(fact_keys=["a"], sources=["s"])
        assert isinstance(c, Contradiction)
        assert c.contradiction_type == "fact_conflict"

    def test_confidence_assessment_is_confidence_score(self):
        ca = ConfidenceAssessment(overall_score=0.5)
        assert isinstance(ca, ConfidenceScore)
        assert ca.overall_score == 0.5

    def test_severity_aliases(self):
        assert ConflictSeverity.CRITICAL.value == "critical"
        assert GapSeverity.BLOCKING.value == "blocking"
        assert RiskSeverity.HIGH.value == "high"

    def test_old_imports_in_reasoning_result(self):
        result = ReasoningResult(
            findings=[Observation(fact_key="o", source="t")],
            contradictions=[Conflict(fact_keys=["a"], sources=["s"])],
        )
        assert len(result.observations) == 1
        assert result.has_contradictions


# ===========================================================================
# Test: Individual Rules
# ===========================================================================


class TestObservationRules:
    def test_identity_present(self):
        result = rule_identity_present(make_full_context())
        assert len(result.findings) == 1
        assert result.findings[0].fact_key == "identity.present"

    def test_identity_present_empty(self):
        assert len(rule_identity_present(MockContext()).findings) == 0

    def test_identity_present_degraded(self):
        ctx = MockContext(sections={"identity": MockSection("identity", [], is_degraded=True)})
        assert len(rule_identity_present(ctx).findings) == 1

    def test_knowledge_present(self):
        result = rule_knowledge_present(make_full_context())
        assert len(result.findings) == 1
        assert result.findings[0].fact_key == "knowledge.present"

    def test_request_context_present(self):
        result = rule_request_context_present(make_full_context())
        assert len(result.findings) == 1
        assert result.findings[0].fact_key == "request.context.present"

    def test_context_fingerprint(self):
        result = rule_context_fingerprint(make_full_context())
        assert len(result.findings) == 1
        assert result.findings[0].fact_key == "context.fingerprint"

    def test_context_fingerprint_missing(self):
        assert len(rule_context_fingerprint(MockContext(fingerprint="")).findings) == 0


class TestGapRules:
    def test_missing_identity_section(self):
        result = rule_missing_identity(MockContext(actor_id=""))
        assert len(result.findings) == 1
        assert result.findings[0].finding_type == "gap"
        assert result.findings[0].severity == "blocking"

    def test_missing_tenant(self):
        result = rule_missing_tenant(MockContext(tenant_id=0))
        assert len(result.findings) == 1
        assert result.findings[0].severity == "blocking"

    def test_missing_actor(self):
        result = rule_missing_actor(MockContext(actor_id=""))
        assert len(result.findings) == 1

    def test_missing_purpose(self):
        result = rule_missing_purpose(MockContext(purpose_code=""))
        assert len(result.findings) == 1

    def test_missing_fingerprint(self):
        result = rule_missing_fingerprint(MockContext(fingerprint=""))
        assert len(result.findings) == 1

    def test_no_gaps_on_full_context(self):
        ctx = make_full_context()
        for fn in [rule_missing_identity, rule_missing_knowledge, rule_missing_tenant,
                    rule_missing_actor, rule_missing_purpose, rule_missing_fingerprint]:
            assert len(fn(ctx).findings) == 0


class TestContradictionRules:
    def test_identity_degraded(self):
        ctx = MockContext(sections={"identity": MockSection("identity", [], is_degraded=True)})
        result = rule_identity_degraded_contradiction(ctx)
        assert len(result.contradictions) >= 1
        assert result.contradictions[0].contradiction_type == "fact_conflict"

    def test_budget_truncation(self):
        ctx = MockContext(budget=MockBudget(total_items=150, max_items=100, truncated=True))
        result = rule_budget_truncation_contradiction(ctx)
        assert len(result.contradictions) == 1
        assert result.contradictions[0].contradiction_type == "incomplete_evidence"

    def test_no_contradictions_on_full(self):
        assert len(rule_identity_degraded_contradiction(make_full_context()).contradictions) == 0

    def test_stale_context(self):
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        ctx = MockContext(created_at=old)
        result = rule_stale_context_contradiction(ctx)
        assert len(result.contradictions) == 1
        assert result.contradictions[0].contradiction_type == "stale_context"

    def test_fresh_context(self):
        ctx = MockContext(created_at=datetime.now(timezone.utc))
        assert len(rule_stale_context_contradiction(ctx).contradictions) == 0


class TestRiskRules:
    def test_degraded_context_risk(self):
        result = rule_degraded_context_risk(MockContext(is_degraded=True))
        assert len(result.findings) == 1 and result.findings[0].finding_type == "risk"

    def test_no_evidence_risk(self):
        result = rule_no_evidence_risk(MockContext())
        assert len(result.findings) == 1 and result.findings[0].finding_type == "risk"
        assert result.findings[0].severity == "critical"

    def test_no_risk_on_full_context(self):
        ctx = make_full_context()
        for fn in [rule_degraded_context_risk, rule_missing_identity_risk,
                    rule_budget_truncation_risk, rule_no_evidence_risk]:
            assert len(fn(ctx).findings) == 0


class TestAttentionRules:
    def test_attention_on_degraded(self):
        assert len(rule_attention_items(MockContext(is_degraded=True)).findings) >= 1

    def test_attention_on_empty(self):
        assert len(rule_attention_items(MockContext()).findings) == 0


# ===========================================================================
# Test: Registry
# ===========================================================================


class TestRuleRegistry:
    def test_register(self):
        reg = RuleRegistry()
        reg.register(RuleDefinition(name="d", fn=lambda ctx: RuleResult(rule_name="d")))
        assert reg.count == 1

    def test_execute_all(self):
        reg = RuleRegistry(); register_standard_rules(reg)
        assert len(reg.execute_all(make_full_context())) == len(ALL_STANDARD_RULES)

    def test_enable_disable(self):
        reg = RuleRegistry()
        reg.register(RuleDefinition(name="d", fn=lambda ctx: RuleResult(rule_name="d")))
        assert reg.is_enabled("d") is True
        reg.disable("d"); assert reg.is_enabled("d") is False
        reg.enable("d"); assert reg.is_enabled("d") is True

    def test_execute_by_name(self):
        reg = RuleRegistry()
        reg.register(RuleDefinition(name="d", fn=lambda ctx: RuleResult(
            rule_name="d", findings=[Finding(fact_key="x", source="t")])))
        result = reg.execute_by_name("d")
        assert result is not None and len(result.findings) == 1

    def test_execute_nonexistent(self):
        assert RuleRegistry().execute_by_name("nonexistent") is None

    def test_rule_versioning(self):
        reg = RuleRegistry()
        reg.register(RuleDefinition(name="d", fn=lambda ctx: RuleResult(rule_name="d"), version=1))
        v1 = reg.get("d").version
        reg.register(RuleDefinition(name="d", fn=lambda ctx: RuleResult(rule_name="d"), version=1))
        assert reg.get("d").version == v1 + 1

    def test_execute_category(self):
        reg = RuleRegistry(); register_standard_rules(reg)
        ctx = make_full_context()
        assert len(reg.execute_category("observation", ctx)) == 4
        assert len(reg.execute_category("contradiction", ctx)) == 4
        assert len(reg.execute_category("gap", ctx)) == 6

    def test_execute_all_empty(self):
        assert len(RuleRegistry().execute_all(None)) == 0

    def test_unregister(self):
        reg = RuleRegistry()
        reg.register(RuleDefinition(name="d", fn=lambda ctx: RuleResult(rule_name="d")))
        assert reg.unregister("d") is True and reg.count == 0
        assert reg.unregister("nonexistent") is False

    def test_clear(self):
        reg = RuleRegistry(); register_standard_rules(reg)
        reg.clear(); assert reg.count == 0

    def test_rule_without_fn(self):
        reg = RuleRegistry()
        reg.register(RuleDefinition(name="no_fn", fn=None))
        result = reg.execute_by_name("no_fn")
        assert result is not None and result.passed is False and "no executable" in (result.error or "")

    def test_execute_ordering(self):
        reg = RuleRegistry()
        calls = []
        def mk(name):
            def fn(ctx): calls.append(name); return RuleResult(rule_name=name)
            return fn
        reg.register(RuleDefinition(name="c", fn=mk("c"), priority=30))
        reg.register(RuleDefinition(name="a", fn=mk("a"), priority=10))
        reg.register(RuleDefinition(name="b", fn=mk("b"), priority=20))
        reg.execute_all(None)
        assert calls == ["a", "b", "c"]


# ===========================================================================
# Test: Confidence Engine
# ===========================================================================


class TestConfidenceEngine:
    def test_assess_full(self):
        engine = ConfidenceEngine()
        findings = [
            Finding(finding_type="observation", fact_key="identity.present",
                    fact_value=True, source="identity_engine"),
            Finding(finding_type="observation", fact_key="knowledge.present",
                    fact_value=True, source="knowledge_store"),
            Finding(finding_type="observation", fact_key="request.context.present",
                    fact_value=True, source="context_fusion_engine"),
            Finding(finding_type="observation", fact_key="context.fingerprint",
                    fact_value="fp-abc", source="context_fusion_engine"),
        ]
        cs = engine.assess(findings, [])
        assert cs.overall_score > 0.5
        assert cs.total_findings == 4
        assert cs.required_facts_present == 4

    def test_consistency_penalty(self):
        engine = ConfidenceEngine()
        findings = [Finding(finding_type="observation", fact_key="k", source="t")]
        cs = engine.assess(findings, [
            Contradiction(contradiction_type="fact_conflict", severity="critical"),
            Contradiction(contradiction_type="fact_conflict", severity="medium"),
        ])
        assert cs.consistency_score < 0.5

    def test_gap_penalty(self):
        engine = ConfidenceEngine()
        findings = [
            Finding(finding_type="observation", fact_key="k", source="t"),
            Finding(finding_type="gap", severity="blocking", fact_key="m", source="t"),
        ]
        cs = engine.assess(findings, [])
        assert cs.completeness_score < 0.5

    def test_empty(self):
        cs = ConfidenceEngine().assess([], [])
        assert cs.overall_score == 0.25  # consistency (1.0) * weight (0.25)
        assert cs.level == "very_low"

    def test_determinism(self):
        engine = ConfidenceEngine()
        findings = [Finding(finding_type="observation", fact_key="k", source="t")]
        cs1 = engine.assess(findings, [])
        cs2 = engine.assess(findings, [])
        assert cs1.overall_score == cs2.overall_score
        for dim in ["completeness_score", "consistency_score",
                     "freshness_score", "corroboration_score",
                     "provenance_quality_score"]:
            assert getattr(cs1, dim) == getattr(cs2, dim)


# ===========================================================================
# Test: Evidence Graph
# ===========================================================================


class TestEvidenceGraph:
    def test_add_reasoning_result(self):
        graph = EvidenceGraph()
        result = ReasoningResult(
            findings=[Finding(fact_key="o", source="t")],
            contradictions=[Contradiction(contradiction_type="fact_conflict", severity="high",
                                          label="X", fact_keys=["a"], sources=["s"])],
            assumptions=[Assumption(fact_key="ak", label="A")],
            constraints=[Constraint(fact_key="ck", constraint_type="b")],
        )
        graph.add_reasoning_result(result)
        assert graph.node_count == 5  # root + 1 finding + 1 contradiction + 1 assumption + 1 constraint
        assert graph.edge_count == 4

    def test_get_path_to_source(self):
        graph = EvidenceGraph()
        f = Finding(fact_key="o", source="t")
        result = ReasoningResult(findings=[f])
        graph.add_reasoning_result(result)
        path = graph.get_path_to_source(f.finding_id)
        assert len(path) == 2
        assert path[-1].node_type == "reasoning_result"

    def test_explain(self):
        graph = EvidenceGraph()
        f = Finding(fact_key="o", label="Test finding", source="t")
        graph.add_reasoning_result(ReasoningResult(findings=[f]))
        assert "Test finding" in graph.explain(f.finding_id)

    def test_explain_nonexistent(self):
        assert "No evidence path" in EvidenceGraph().explain("nonexistent")

    def test_to_dict(self):
        graph = EvidenceGraph()
        graph.add_reasoning_result(ReasoningResult(
            findings=[Finding(fact_key="o", source="t")]))
        d = graph.to_dict()
        assert d["node_count"] == 2


# ===========================================================================
# Test: Reasoning Engine
# ===========================================================================


class TestReasoningEngine:
    def test_engine_creation(self):
        engine = ReasoningEngine()
        assert engine.registry.count == 19  # 4 obs + 6 gap + 4 contradiction + 4 risk + 1 composite

    def test_evaluate_full_context(self):
        engine = ReasoningEngine()
        ctx = make_full_context()
        result = engine.evaluate(ctx)
        assert len(result.findings) > 0
        assert len(result.observations) == 4
        assert len(result.gaps) == 0
        assert len(result.risks) == 0
        assert result.confidence is not None
        assert result.metadata is not None
        assert result.metadata.rules_executed == 19

    def test_evaluate_empty_context(self):
        result = ReasoningEngine().evaluate(None)
        assert result is not None and result.confidence is not None

    def test_evaluate_degraded_context(self):
        engine = ReasoningEngine()
        ctx = MockContext(is_degraded=True, sections={
            "identity": MockSection("identity", [], is_degraded=True),
            "knowledge": MockSection("knowledge", [], is_degraded=True),
        })
        result = engine.evaluate(ctx)
        assert result.has_contradictions or result.has_risks or result.has_gaps
        assert result.requires_attention

    def test_determinism(self):
        engine = ReasoningEngine()
        ctx = make_full_context()
        r1, r2 = engine.evaluate(ctx), engine.evaluate(ctx)
        assert len(r1.findings) == len(r2.findings)
        assert r1.confidence.overall_score == r2.confidence.overall_score

    def test_execute_rule_by_name(self):
        result = ReasoningEngine().execute_rule("identity_present", make_full_context())
        assert result is not None and len(result.findings) == 1

    def test_execute_rule_nonexistent(self):
        assert ReasoningEngine().execute_rule("nonexistent", None) is None

    def test_build_evidence_graph(self):
        engine = ReasoningEngine()
        result = engine.evaluate(make_full_context())
        graph = engine.build_evidence_graph(result)
        assert graph.node_count >= 2


# ===========================================================================
# Test: Determinism
# ===========================================================================


class TestDeterminism:
    def test_identical_inputs_identical_outputs(self):
        engine = ReasoningEngine()
        ctx = make_full_context()
        results = [engine.evaluate(ctx) for _ in range(3)]
        assert all(r.metadata.rules_executed == results[0].metadata.rules_executed for r in results)
        assert all(r.confidence.overall_score == results[0].confidence.overall_score for r in results)
        assert all(len(r.findings) == len(results[0].findings) for r in results)

    def test_different_inputs_different_outputs(self):
        engine = ReasoningEngine()
        r1 = engine.evaluate(make_full_context())
        r2 = engine.evaluate(MockContext())
        assert len(r1.findings) != len(r2.findings)
        assert r1.confidence.overall_score != r2.confidence.overall_score


# ===========================================================================
# Test: Concurrency
# ===========================================================================


class TestConcurrency:
    def test_concurrent_evaluation(self):
        engine = ReasoningEngine()
        ctx = make_full_context()
        results, errors = [], []
        def evaluate():
            try: results.append(engine.evaluate(ctx))
            except Exception as e: errors.append(e)
        threads = [threading.Thread(target=evaluate) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0 and len(results) == 10
        scores = [r.confidence.overall_score for r in results]
        assert all(s == scores[0] for s in scores)

    def test_concurrent_registry_operations(self):
        reg = RuleRegistry()
        errors = []
        def register_rules(start: int):
            try:
                for i in range(start, start + 5):
                    reg.register(RuleDefinition(
                        name=f"rule_{i}", fn=lambda ctx: RuleResult(rule_name=f"rule_{i}"),
                        priority=i))
            except Exception as e: errors.append(e)
        threads = [threading.Thread(target=register_rules, args=(i * 5,)) for i in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0

    def test_concurrent_different_contexts(self):
        engine = ReasoningEngine()
        results, errors = {}, []
        def evaluate(cid: str):
            try: results[cid] = engine.evaluate(MockContext(context_id=cid))
            except Exception as e: errors.append(e)
        threads = [threading.Thread(target=evaluate, args=(f"ctx-{i}",)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert len(errors) == 0 and len(results) == 10


# ===========================================================================
# Test: Failure Paths
# ===========================================================================


class TestFailurePaths:
    def test_empty_sections(self):
        assert ReasoningEngine().evaluate(MockContext(sections={})) is not None

    def test_partial_sections(self):
        assert ReasoningEngine().evaluate(MockContext(
            sections={"identity": MockSection("identity", [{"id": 1}], False)})) is not None

    def test_registry_execute_all_empty(self):
        assert RuleRegistry().execute_all(None) == []

    def test_registry_execute_category_empty(self):
        assert RuleRegistry().execute_category("nonexistent", None) == []

    def test_confidence_assess_empty(self):
        assert ConfidenceEngine().assess([], []).overall_score == 0.25

    def test_rule_without_fn(self):
        reg = RuleRegistry()
        reg.register(RuleDefinition(name="no_fn", fn=None))
        result = reg.execute_by_name("no_fn")
        assert result is not None and result.passed is False


# ===========================================================================
# Test: Integration (Mock infrastructure)
# ===========================================================================


class TestIntegration:
    def test_with_event_bus(self):
        events = []
        class MockEventBus:
            def publish(self, event): events.append(event)
        result = ReasoningEngine(event_bus=MockEventBus()).evaluate(make_full_context())
        assert len(events) == 1
        assert events[0].event_type == "reasoning.evaluation.completed"
        assert events[0].object_id == result.result_id

    def test_with_health_registry(self):
        checks = {}
        class MockHealth:
            def register(self, name, fn): checks[name] = fn
        engine = ReasoningEngine(health_registry=MockHealth())
        assert "reasoning_engine" in checks
        assert hasattr(checks["reasoning_engine"](), "status")

    def test_with_metrics_registry(self):
        counters = {}
        class MockMetrics:
            def counter(self, name, desc):
                counters[name] = {"c": 0}
                class C:
                    def inc(s, n=1): counters[name]["c"] += n
                return C()
            def histogram(self, name, desc, buckets=None):
                class H:
                    def observe(s, v): pass
                return H()
        result = ReasoningEngine(metrics_registry=MockMetrics()).evaluate(make_full_context())
        assert counters.get("reasoning_evaluations_total", {}).get("c", 0) >= 1

    def test_di_integration(self):
        result = ReasoningEngine().evaluate(make_full_context())
        assert result is not None and result.confidence is not None

    def test_empty_event_bus(self):
        assert ReasoningEngine().evaluate(make_full_context()) is not None


# ===========================================================================
# Test: Module-level convenience functions
# ===========================================================================


class TestModuleLevel:
    def test_get_singleton(self):
        reset_reasoning_engine()
        engine = get_reasoning_engine()
        assert engine is not None and engine.registry.count == 19

    def test_reset(self):
        reset_reasoning_engine()
        e1 = get_reasoning_engine()
        reset_reasoning_engine()
        e2 = get_reasoning_engine()
        assert e1 is not e2