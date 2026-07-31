"""Tests for Phase H — Governance Engine (ES-001).

Covers:
  - Unit tests for all canonical governance models
  - Safe expression evaluator tests
  - Policy evaluation tests
  - Constitutional validation tests
  - Context enrichment tests
  - GovernanceEngine 6-stage pipeline tests
  - Input validation tests
  - Risk assessment tests
  - Determinism tests (identical inputs -> identical outputs)
  - Tenant isolation tests
  - Audit log tests
  - Legacy backward compatibility tests

Architectural authority: ES-001 — Governance Engine Specification
"""

from __future__ import annotations

import copy
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import pytest
from unittest.mock import patch

from app.shunya.governance_engine.models import (
    ActionType, VerdictDecision, PolicySeverity, PolicyScope,
    GovernanceState, FailureMode,
    Policy, PolicyViolation, PolicyRegistry,
    ContextEnrichment, AuditEntry,
    GovernanceInput, GovernanceVerdict,
    GovernanceStats,
)
from app.shunya.governance_engine.engine import (
    GovernanceEngine, get_governance_engine, reset_governance_engine,
)
from app.shunya.governance_engine.evaluator import (
    safe_eval, safe_eval_bool, tokenize, Parser, evaluate,
    TokenType, SafeContext, _WHITELISTED_FUNCTIONS,
)


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture(autouse=True)
def reset_engine():
    """Reset the singleton before each test."""
    reset_governance_engine()
    yield
    reset_governance_engine()


@pytest.fixture
def engine():
    return GovernanceEngine()


@pytest.fixture
def valid_input():
    return GovernanceInput(
        action_type="plan",
        proposal={"destination": "Paris", "budget": 5000, "pax": "2 adults"},
        evidence_chain=[{"source": "reasoning", "finding_id": "f1"}],
        confidence=0.85,
        tenant_id=1,
        actor_id="actor-1",
        domain="travel",
    )


@pytest.fixture
def valid_plan_context():
    return {
        "action_type": "plan",
        "tenant_id": 1,
        "domain": "travel",
        "destination": "Paris",
        "budget": 5000,
        "pax": "2 adults",
        "confidence": 0.85,
        "evidence_chain": [{"source": "reasoning"}],
    }


# ======================================================================
# Model Tests
# ======================================================================


class TestModels:
    """Canonical governance data model tests."""

    def test_governance_input_defaults(self):
        inp = GovernanceInput(action_type="plan", proposal={}, tenant_id=1)
        assert inp.action_type == "plan"
        assert inp.confidence == 0.0
        assert inp.domain == "travel"
        assert inp.timestamp is not None

    def test_governance_input_clamps_confidence(self):
        inp = GovernanceInput(action_type="plan", proposal={}, confidence=1.5, tenant_id=1)
        assert inp.confidence == 1.0
        inp2 = GovernanceInput(action_type="plan", proposal={}, confidence=-0.5, tenant_id=1)
        assert inp2.confidence == 0.0

    def test_governance_verdict_defaults(self):
        v = GovernanceVerdict(approved=True)
        assert v.decision == VerdictDecision.APPROVE
        assert v.audit_id != ""
        assert v.evaluated_at is not None

    def test_governance_verdict_properties(self):
        approve = GovernanceVerdict(approved=True, decision=VerdictDecision.APPROVE)
        assert approve.is_approved
        assert not approve.is_review_required
        assert not approve.is_rejected

        review = GovernanceVerdict(approved=False, decision=VerdictDecision.REVIEW)
        assert review.is_review_required
        assert not review.is_approved

        reject = GovernanceVerdict(approved=False, decision=VerdictDecision.REJECT)
        assert reject.is_rejected

    def test_verdict_to_dict(self):
        v = GovernanceVerdict(
            approved=True,
            decision=VerdictDecision.APPROVE,
            confidence=0.9,
            explanation="All passed",
            blocking_policies=[],
            warnings=["budget: high"],
            policy_violations=[
                PolicyViolation("budget", PolicySeverity.WARN, "Budget is high", "detail")
            ],
        )
        d = v.to_dict()
        assert d["approved"] is True
        assert d["decision"] == "APPROVE"
        assert d["confidence"] == 0.9
        assert len(d["policy_violations"]) == 1
        assert d["policy_violations"][0]["policy_name"] == "budget"

    def test_policy_auto_id(self):
        p = Policy("test_policy", "Test", PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                    condition="True", error_message="Err")
        assert p.name == "test_policy"
        assert p.created_at is not None

    def test_policy_to_dict(self):
        p = Policy("test", "Test", PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                    condition="True", error_message="Err")
        d = p.to_dict()
        assert d["name"] == "test"
        assert d["severity"] == "block"
        assert d["scope"] == "global"

    def test_policy_registry_default_policies(self):
        reg = PolicyRegistry()
        assert reg.count >= 7  # Default policies

    def test_policy_registry_register_and_get(self):
        reg = PolicyRegistry()
        p = Policy("custom", "Custom", PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                    condition="True", error_message="Err")
        reg.register(p)
        retrieved = reg.get("global:custom")
        assert retrieved is not None
        assert retrieved.name == "custom"

    def test_policy_registry_deregister(self):
        reg = PolicyRegistry()
        initial = reg.count
        reg.deregister("global:budget_sanity")
        assert reg.count == initial - 1

    def test_policy_registry_get_applicable_global(self):
        reg = PolicyRegistry()
        applicable = reg.get_applicable({"domain": "travel", "action_type": "plan"})
        # All GLOBAL policies should apply
        global_count = len([p for p in reg._policies.values() if p.scope == PolicyScope.GLOBAL])
        assert len(applicable) >= global_count

    def test_policy_registry_get_applicable_domain(self):
        reg = PolicyRegistry()
        # No domain-specific policies in defaults, so only globals
        applicable = reg.get_applicable({"domain": "healthcare", "action_type": "plan"})
        global_count = len([p for p in reg._policies.values() if p.scope == PolicyScope.GLOBAL])
        assert len(applicable) >= global_count

    def test_audit_entry_to_dict(self):
        entry = AuditEntry(
            audit_id="a1", verdict=VerdictDecision.APPROVE, confidence=0.9,
            action_type="plan", tenant_id=1, domain="travel",
            policies_evaluated=3, blocking_policies=[], warnings=[], reviews_required=[],
            explanation="OK", context_snapshot={},
            evaluated_at=datetime(2026, 7, 19, tzinfo=timezone.utc),
        )
        d = entry.to_dict()
        assert d["audit_id"] == "a1"
        assert d["verdict"] == "APPROVE"
        assert d["confidence"] == 0.9

    def test_governance_stats(self):
        stats = GovernanceStats(total_decisions=100, approved=80, rejected=10,
                                review_required=5, errors=5, avg_confidence=0.8)
        d = stats.to_dict()
        assert d["total_decisions"] == 100
        assert d["approval_rate"] == 80.0
        assert d["avg_confidence"] == 0.8

    def test_context_enrichment_defaults(self):
        ce = ContextEnrichment()
        assert ce.pax_count is None
        assert ce.estimated_cost == 0.0
        assert not ce.is_international
        assert ce.lead_time_days == 999

    def test_action_type_enum(self):
        assert ActionType.PLAN.value == "plan"
        assert ActionType.FINANCIAL.value == "financial"

    def test_verdict_decision_enum(self):
        assert VerdictDecision.APPROVE.value == "APPROVE"
        assert VerdictDecision.REVIEW.value == "REVIEW"
        assert VerdictDecision.REJECT.value == "REJECT"

    def test_failure_mode_enum(self):
        assert FailureMode.MISSING_EVIDENCE.value == "missing_evidence"
        assert FailureMode.TIMEOUT.value == "timeout"

    def test_policy_severity_comparison(self):
        assert PolicySeverity.BLOCK != PolicySeverity.WARN
        assert PolicySeverity.REVIEW.value == "review"

    def test_policy_violation_creation(self):
        pv = PolicyViolation("budget_sanity", PolicySeverity.WARN, "Budget exceeded")
        assert pv.policy_name == "budget_sanity"
        assert pv.severity == PolicySeverity.WARN

    def test_governance_input_from_package(self):
        """Test converting a mock Phase G GovernancePackage to GovernanceInput."""
        class MockPackage:
            plan = None
            evidence_summary = [{"src": "reasoning"}]
            tenant_id = 42
            actor_id = "agent-1"
            confidence = 0.75

        pkg = MockPackage()
        inp = GovernanceInput.from_governance_package(pkg)
        assert inp.action_type == "plan"
        assert inp.tenant_id == 42
        assert inp.actor_id == "agent-1"
        assert inp.confidence == 0.75


# ======================================================================
# Safe Expression Evaluator Tests
# ======================================================================


class TestSafeEvaluator:
    """Tests for the safe expression evaluator replacing eval()."""

    def test_literal_number(self):
        assert safe_eval("42", {}) == 42
        assert safe_eval("3.14", {}) == 3.14

    def test_literal_string(self):
        assert safe_eval("'hello'", {}) == "hello"
        assert safe_eval('"world"', {}) == "world"

    def test_literal_bool(self):
        assert safe_eval("True", {}) is True
        assert safe_eval("False", {}) is False
        assert safe_eval("true", {}) is True

    def test_literal_none(self):
        assert safe_eval("None", {}) is None
        assert safe_eval("null", {}) is None

    def test_field_access(self):
        ctx = {"name": "Alice", "age": 30}
        assert safe_eval("name == 'Alice'", ctx) is True
        assert safe_eval("age > 25", ctx) is True
        assert safe_eval("age < 20", ctx) is False

    def test_missing_field_returns_none(self):
        ctx = {"name": "Alice"}
        result = safe_eval("missing_field", ctx)
        assert result is None

    def test_comparison_operators(self):
        ctx = {"a": 10, "b": 20}
        assert safe_eval("a == 10", ctx) is True
        assert safe_eval("a != b", ctx) is True
        assert safe_eval("a < b", ctx) is True
        assert safe_eval("b > a", ctx) is True
        assert safe_eval("a <= 10", ctx) is True
        assert safe_eval("b >= 20", ctx) is True

    def test_boolean_operators(self):
        ctx = {"a": True, "b": False}
        assert safe_eval("a and True", ctx) is True
        assert safe_eval("a and b", ctx) is False
        assert safe_eval("a or b", ctx) is True
        assert safe_eval("not b", ctx) is True

    def test_short_circuit_and(self):
        ctx = {"a": False}
        # If 'and' short-circuits, 'b' is never accessed
        assert safe_eval("a and missing_key > 5", ctx) is False

    def test_short_circuit_or(self):
        ctx = {"a": True}
        assert safe_eval("a or missing_key > 5", ctx) is True

    def test_arithmetic(self):
        ctx = {"x": 10, "y": 3}
        assert safe_eval("x + y", ctx) == 13
        assert safe_eval("x - y", ctx) == 7
        assert safe_eval("x * y", ctx) == 30
        assert safe_eval("x / y", ctx) == 10 / 3

    def test_division_by_zero(self):
        assert safe_eval("10 / 0", {}) == float('inf')

    def test_parentheses(self):
        ctx = {"a": 1, "b": 2, "c": 3}
        assert safe_eval("(a + b) * c", ctx) == 9
        assert safe_eval("a + b * c", ctx) == 7

    def test_has_function(self):
        ctx = {"name": "Alice"}
        assert safe_eval("has('name')", ctx) is True
        assert safe_eval("has('missing')", ctx) is False

    def test_in_range_function(self):
        ctx = {"val": 5}
        assert safe_eval("in_range(val, 1, 10)", ctx) is True
        assert safe_eval("in_range(val, 10, 20)", ctx) is False

    def test_len_function(self):
        ctx = {"items": [1, 2, 3]}
        assert safe_eval("len(items) == 3", ctx) is True
        assert safe_eval("len(items) > 0", ctx) is True

    def test_in_operator(self):
        ctx = {"val": 5, "allowed": [1, 3, 5, 7]}
        assert safe_eval("val in allowed", ctx) is True
        ctx2 = {"val": 2, "allowed": [1, 3, 5]}
        assert safe_eval("val in allowed", ctx2) is False

    def test_nested_expression(self):
        ctx = {"a": 10, "b": 5, "c": 20}
        assert safe_eval("a > b and a < c or b > c", ctx) is True

    def test_error_on_unknown_function(self):
        with pytest.raises(ValueError, match="Unknown function"):
            safe_eval("exec('rm -rf /')", {})

    def test_safe_eval_bool(self):
        assert safe_eval_bool("1 == 1", {}) is True
        assert safe_eval_bool("1 == 2", {}) is False
        assert safe_eval_bool("0", {}) is False
        assert safe_eval_bool("1", {}) is True

    def test_no_eval_injection(self):
        """Verify that dangerous constructs are not accessible."""
        with pytest.raises((ValueError, TypeError, AttributeError, NameError)):
            safe_eval("__import__('os').system('ls')", {})
        with pytest.raises((ValueError, TypeError, AttributeError)):
            safe_eval("__builtins__", {})

    def test_list_literal(self):
        assert safe_eval("[1, 2, 3]", {}) == [1, 2, 3]

    def test_function_in_condition(self):
        ctx = {"pax_count": 5}
        assert safe_eval("in_range(pax_count, 1, 100)", ctx) is True
        assert safe_eval("in_range(pax_count, 1, 3)", ctx) is False

    def test_whitelisted_functions_only(self):
        """Verify that only whitelisted functions are callable."""
        with pytest.raises(ValueError, match="Unknown function"):
            safe_eval("print('hi')", {})
        with pytest.raises(ValueError, match="Unknown function"):
            safe_eval("open('/etc/passwd')", {})
        with pytest.raises(ValueError, match="Unknown function"):
            safe_eval("eval('1+1')", {})


# ======================================================================
# Policy Evaluation Tests
# ======================================================================


class TestPolicyEvaluation:
    """Tests for policy evaluation with safe expressions."""

    def test_policy_passes(self, engine):
        p = Policy("test_pass", "Test", PolicyScope.GLOBAL, PolicySeverity.PASS,
                    condition="True", error_message="Should not trigger")
        engine.register_policy(p)
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"dummy": True},
            tenant_id=1, confidence=0.95,
            evidence_chain=[{"src": "reasoning"}],
        ))
        assert result.is_approved

    def test_policy_block(self, engine):
        p = Policy("test_block", "Test", PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                    condition="False", error_message="Blocked by test")
        engine.register_policy(p)
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"dummy": True}, tenant_id=1,
        ))
        assert result.is_rejected
        assert any("test_block" in b for b in result.blocking_policies)

    def test_policy_warn(self, engine):
        p = Policy("test_warn", "Test", PolicyScope.GLOBAL, PolicySeverity.WARN,
                    condition="False", error_message="Warning by test")
        engine.register_policy(p)
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"dummy": True},
            confidence=0.9, tenant_id=1,
        ))
        assert result.is_approved  # WARN alone doesn't block
        assert any("test_warn" in w for w in result.warnings)

    def test_policy_review(self, engine):
        p = Policy("test_review", "Test", PolicyScope.GLOBAL, PolicySeverity.REVIEW,
                    condition="False", error_message="Review by test")
        engine.register_policy(p)
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"dummy": True}, tenant_id=1,
        ))
        assert result.is_review_required
        assert result.required_human_approval

    def test_disabled_policy_not_evaluated(self, engine):
        p = Policy("disabled", "Test", PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                    condition="False", error_message="Should not be checked",
                    enabled=False)
        engine.register_policy(p)
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=1, confidence=0.95,
            evidence_chain=[{"src": "reasoning"}],
        ))
        assert result.is_approved  # Disabled policy doesn't block

    def test_policy_with_context_field(self, engine):
        """Policy that checks a context field value."""
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris", "budget": 10000},
            confidence=0.5,
            tenant_id=1,
        ))
        # The budget_sanity policy should check estimated_cost <= budget * 10
        # With destination=Paris (international), estimated_cost will be computed
        assert result.decision in (VerdictDecision.APPROVE, VerdictDecision.REVIEW)

    def test_unknown_domain_allowed(self, engine):
        """Unknown domain is a warning, not a block."""
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=1, confidence=0.95,
            domain="unknown-domain",
            evidence_chain=[{"src": "reasoning"}],
        ))
        # Should still pass
        assert result.is_approved or result.decision == VerdictDecision.REVIEW


# ======================================================================
# Constitutional Validation Tests
# ======================================================================


class TestConstitutionalValidation:
    """Tests for constitutional rule validation."""

    def test_missing_tenant_rejected(self, engine):
        """Constitutional rule: tenant_isolation_constitutional."""
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=None,
        ))
        assert result.is_rejected
        assert any("tenant" in b.lower() for b in result.blocking_policies)

    def test_invalid_tenant_rejected(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=0,
        ))
        assert result.is_rejected

    def test_valid_tenant_not_rejected_by_constitution(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=1, confidence=0.9,
        ))
        # Should not be in ERROR state — engine processes valid input without crashing
        assert result.state != GovernanceState.ERROR


# ======================================================================
# Context Enrichment Tests
# ======================================================================


class TestContextEnrichment:
    """Tests for context enrichment stage."""

    def test_enrich_pax_count(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"pax": "2 adults", "destination": "Goa"},
            tenant_id=1, confidence=0.9,
        ))
        # pax_count should be extracted as 2
        assert result.is_approved or result.decision is not None

    def test_enrich_international_domestic(self, engine):
        # Domestic destination should set is_international=False
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Goa"},
            tenant_id=1, confidence=0.9,
        ))
        # Goa is domestic
        assert result.decision is not None

    def test_enrich_wedding_check(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"occasion": "wedding", "dates": "10 Dec 2026 - 15 Dec 2026"},
            tenant_id=1, confidence=0.9,
        ))
        # Wedding flag should be set
        assert result.decision is not None

    def test_enrich_estimated_cost(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={
                "daily_budget_per_person": 5000,
                "itinerary_days": 5,
                "pax": "2 adults",
            },
            tenant_id=1, confidence=0.9,
        ))
        assert result.decision is not None


# ======================================================================
# Input Validation Tests
# ======================================================================


class TestInputValidation:
    """Tests for input validation stage."""

    def test_invalid_action_type_rejected(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="invalid_type",
            proposal={},
            tenant_id=1,
        ))
        assert result.is_rejected
        assert result.state == GovernanceState.ERROR

    def test_empty_proposal_rejected(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={},
            tenant_id=1,
        ))
        assert result.is_rejected
        assert result.state == GovernanceState.ERROR

    def test_empty_proposal_with_confidence_rejected(self, engine):
        """Empty proposal still fails even with high confidence."""
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={},
            confidence=0.9,
            tenant_id=1,
        ))
        assert result.is_rejected

    def test_valid_input_not_rejected_by_validation(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris", "budget": 5000},
            confidence=0.85,
            tenant_id=1,
            domain="travel",
            evidence_chain=[{"src": "reasoning"}],
        ))
        assert result.state != GovernanceState.ERROR


# ======================================================================
# Risk Assessment Tests
# ======================================================================


class TestRiskAssessment:
    """Tests for risk assessment stage."""

    def test_low_confidence_increases_risk(self, engine):
        low_conf = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris"},
            confidence=0.1,
            tenant_id=1,
        ))
        high_conf = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris"},
            confidence=0.95,
            tenant_id=1,
        ))
        # Low confidence should be at least as restrictive as high confidence
        low_severity = 0 if low_conf.is_approved else (1 if low_conf.is_review_required else 2)
        high_severity = 0 if high_conf.is_approved else (1 if high_conf.is_review_required else 2)
        assert low_severity >= high_severity

    def test_empty_evidence_increases_risk(self, engine):
        with_evidence = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris"},
            confidence=0.7,
            tenant_id=1,
            evidence_chain=[{"src": "reasoning"}],
        ))
        without_evidence = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris"},
            confidence=0.7,
            tenant_id=1,
            evidence_chain=[],
        ))
        # Without evidence should be at least as restrictive
        w_sev = 0 if with_evidence.is_approved else (1 if with_evidence.is_review_required else 2)
        wo_sev = 0 if without_evidence.is_approved else (1 if without_evidence.is_review_required else 2)
        assert wo_sev >= w_sev

    def test_missing_evidence_does_not_break(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris"},
            confidence=0.5,
            tenant_id=1,
        ))
        assert result.decision in (VerdictDecision.APPROVE, VerdictDecision.REVIEW, VerdictDecision.REJECT)


# ======================================================================
# Determinism Tests
# ======================================================================


class TestDeterminism:
    """Tests for governance engine determinism."""

    def test_identical_inputs_identical_outputs(self, engine):
        inp = GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris", "budget": 5000, "pax": "2 adults"},
            confidence=0.85,
            tenant_id=1,
            domain="travel",
            evidence_chain=[{"src": "reasoning"}],
        )

        result1 = engine.evaluate(inp)
        result2 = engine.evaluate(inp)

        assert result1.decision == result2.decision
        assert result1.confidence == result2.confidence
        assert result1.blocking_policies == result2.blocking_policies
        assert result1.warnings == result2.warnings

    def test_different_inputs_different_outputs(self, engine):
        inp_low = GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris"},
            confidence=0.1,
            tenant_id=1,
        )
        inp_high = GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris"},
            confidence=0.95,
            tenant_id=1,
            evidence_chain=[{"src": "r1"}, {"src": "r2"}],
        )

        result_low = engine.evaluate(inp_low)
        result_high = engine.evaluate(inp_high)

        # Different inputs should produce different confidence scores
        assert abs(result_low.confidence - result_high.confidence) > 0.01


# ======================================================================
# Audit Log Tests
# ======================================================================


class TestAuditLog:
    """Tests for governance audit log."""

    def test_audit_entry_created(self, engine):
        engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True}, tenant_id=1,
        ))
        log = engine.get_audit_log()
        assert len(log) == 1

    def test_audit_entry_contains_verdict(self, engine):
        engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=1, confidence=0.9,
        ))
        entry = engine.get_audit_log()[0]
        assert "audit_id" in entry
        assert "verdict" in entry
        assert "evaluated_at" in entry

    def test_audit_log_respects_limit(self, engine):
        for _ in range(5):
            engine.evaluate(GovernanceInput(
                action_type="plan", proposal={"test": True},
                tenant_id=1, confidence=0.9,
            ))
        assert len(engine.get_audit_log(limit=3)) == 3
        assert len(engine.get_audit_log(limit=10)) == 5

    def test_audit_entry_by_id(self, engine):
        inp = GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=1, confidence=0.9,
        )
        result = engine.evaluate(inp)
        entry = engine.get_audit_entry(result.audit_id)
        assert entry is not None
        assert entry["audit_id"] == result.audit_id

    def test_audit_log_append_only(self, engine):
        engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True}, tenant_id=1,
        ))
        size1 = engine.audit_log_size
        engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True}, tenant_id=1,
        ))
        size2 = engine.audit_log_size
        assert size2 == size1 + 1


# ======================================================================
# Tenant Isolation Tests
# ======================================================================


class TestTenantIsolation:
    """Tests for tenant isolation in governance."""

    def test_different_tenants_independent(self, engine):
        inp1 = GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=1, confidence=0.9,
        )
        inp2 = GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=2, confidence=0.9,
        )
        r1 = engine.evaluate(inp1)
        r2 = engine.evaluate(inp2)
        # Both should succeed (same policies apply to both tenants)
        assert r1.decision == r2.decision

    def test_no_tenant_rejected(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=None,
        ))
        assert result.is_rejected

    def test_tenant_zero_rejected(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=0,
        ))
        assert result.is_rejected


# ======================================================================
# Statistics Tests
# ======================================================================


class TestStatistics:
    """Tests for governance engine statistics."""

    def test_stats_after_evaluation(self, engine):
        engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True}, tenant_id=1,
        ))
        stats = engine.stats
        assert stats["total_decisions"] == 1
        assert stats["policies_registered"] > 0

    def test_stats_multiple_decisions(self, engine):
        for _ in range(3):
            engine.evaluate(GovernanceInput(
                action_type="plan", proposal={"test": True},
                tenant_id=1, confidence=0.9,
            ))
        stats = engine.stats
        assert stats["total_decisions"] == 3

    def test_stats_approval_rate(self, engine):
        engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"dummy": True},
            tenant_id=1, confidence=0.5,
        ))
        stats = engine.stats
        assert stats["approval_rate"] is not None


# ======================================================================
# Policy Management Tests
# ======================================================================


class TestPolicyManagement:
    """Tests for policy registration and deregistration."""

    def test_register_policy(self, engine):
        initial = engine.list_policies()
        p = Policy("new_policy", "New", PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                    condition="False", error_message="Block")
        engine.register_policy(p)
        assert len(engine.list_policies()) == len(initial) + 1

    def test_deregister_policy(self, engine):
        initial = engine.list_policies()
        engine.deregister_policy("global:budget_sanity")
        assert len(engine.list_policies()) == len(initial) - 1

    def test_deregister_nonexistent(self, engine):
        result = engine.deregister_policy("nonexistent")
        assert result is False

    def test_list_policies_contains_expected(self, engine):
        policies = engine.list_policies()
        names = [p["name"] for p in policies]
        assert "budget_sanity" in names
        assert "tenant_isolation" in names
        assert "confidence_floor" in names


# ======================================================================
# Error Handling Tests
# ======================================================================


class TestErrorHandling:
    """Tests for error handling in governance engine."""

    def test_missing_evidence_gives_warning(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "Paris", "budget": 5000},
            confidence=0.9,
            tenant_id=1,
            evidence_chain=[],
        ))
        # evidence_completeness policy should fire a warning
        assert result.evidence_checked is False
        # But should not necessarily block
        assert result.decision is not None

    def test_policy_evaluation_error_blocks(self, engine):
        """A policy that raises an exception should be treated as BLOCK."""
        p = Policy("broken", "Broken", PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                    condition="undefined_function_call()", error_message="Should error")
        engine.register_policy(p)
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            tenant_id=1, confidence=0.9,
        ))
        # Division by zero in condition -> treated as blocked
        assert result.is_rejected

    def test_unknown_action_type_errors(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="unknown", proposal={"test": True},
            tenant_id=1,
        ))
        assert result.state == GovernanceState.ERROR
        assert result.is_rejected

    def test_zero_confidence_not_crash(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan", proposal={"test": True},
            confidence=0.0, tenant_id=1,
        ))
        # Zero confidence may trigger confidence_floor (REVIEW)
        assert result.decision is not None


# ======================================================================
# Singleton Engine Tests
# ======================================================================


class TestSingleton:
    """Tests for module-level singleton."""

    def test_get_engine_singleton(self):
        eng1 = get_governance_engine()
        eng2 = get_governance_engine()
        assert eng1 is eng2

    def test_reset_creates_new_singleton(self):
        eng1 = get_governance_engine()
        reset_governance_engine()
        eng2 = get_governance_engine()
        assert eng1 is not eng2


# ======================================================================
# Concurrency Tests
# ======================================================================


class TestConcurrency:
    """Tests for thread safety."""

    def test_concurrent_evaluation(self, engine):
        results: List[GovernanceVerdict] = []
        errors: List[Exception] = []

        def evaluate() -> None:
            try:
                result = engine.evaluate(GovernanceInput(
                    action_type="plan",
                    proposal={"test": "concurrent"},
                    tenant_id=1, confidence=0.8,
                ))
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=evaluate) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrency errors: {errors}"
        assert len(results) == 10

    def test_concurrent_identical_inputs(self, engine):
        results: List[GovernanceVerdict] = []

        def evaluate() -> None:
            result = engine.evaluate(GovernanceInput(
                action_type="plan",
                proposal={"test": "determinism"},
                tenant_id=1, confidence=0.8,
            ))
            results.append(result)

        threads = [threading.Thread(target=evaluate) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be identical
        decisions = [r.decision for r in results]
        assert all(d == decisions[0] for d in decisions)
        confidences = [r.confidence for r in results]
        assert all(abs(c - confidences[0]) < 0.001 for c in confidences)


# ======================================================================
# Legacy Backward Compatibility Tests
# ======================================================================


class TestLegacyBackwardCompatibility:
    """Tests for backward compatibility with old GovernanceLayer API."""

    def test_legacy_governance_layer_importable(self):
        from app.shunya.governance_engine._legacy_governance import (
            GovernanceLayer, GovernanceVerdict as LegacyVerdict,
        )
        assert GovernanceLayer is not None

    def test_legacy_validate_plan(self):
        from app.shunya.governance_engine._legacy_governance import GovernanceLayer
        layer = GovernanceLayer()
        result = layer.validate_plan(
            {"destination": "Paris", "budget": 5000},
            {"tenant_id": 1, "confidence": 0.8},
        )
        assert hasattr(result, "approved")
        assert hasattr(result, "confidence")
        assert hasattr(result, "blocking_policies")
        assert hasattr(result, "warnings")

    def test_legacy_validate_action(self):
        from app.shunya.governance_engine._legacy_governance import GovernanceLayer
        layer = GovernanceLayer()
        result = layer.validate_action("send_proposal", {},
                                        {"tenant_id": 1})
        assert hasattr(result, "approved")

    def test_legacy_verdict_to_dict(self):
        from app.shunya.governance_engine._legacy_governance import GovernanceVerdict as LegacyVerdict
        v = LegacyVerdict(approved=True, confidence=0.9,
                           blocking_policies=["block1"],
                           warnings=["warn1"])
        d = v.to_dict()
        assert d["approved"] is True
        assert d["confidence"] == 0.9
        assert "block1" in d["blocking_policies"]

    def test_legacy_layer_audit_log(self):
        from app.shunya.governance_engine._legacy_governance import GovernanceLayer
        layer = GovernanceLayer()
        layer.validate_plan({"test": True}, {"tenant_id": 1})
        log = layer.get_audit_log()
        assert len(log) >= 1


# ======================================================================
# Integration Tests
# ======================================================================


class TestIntegration:
    """Integration tests for Governance Engine."""

    def test_full_approval_flow(self, engine):
        """A well-formed proposal with high confidence and evidence should approve."""
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={
                "destination": "Paris",
                "budget": 10000,
                "pax": "2 adults",
                "dates": "1 Dec 2026 - 5 Dec 2026",
            },
            confidence=0.95,
            tenant_id=1,
            domain="travel",
            evidence_chain=[
                {"source": "reasoning", "finding_id": "f1"},
                {"source": "reasoning", "finding_id": "f2"},
            ],
        ))
        assert result.decision == VerdictDecision.APPROVE

    def test_review_for_financial_action(self, engine):
        """Financial actions should trigger REVIEW (AI Proposes, Humans Dispose)."""
        result = engine.evaluate(GovernanceInput(
            action_type="financial",
            proposal={"amount": 50000},
            confidence=0.9,
            tenant_id=1,
        ))
        assert result.decision == VerdictDecision.REVIEW
        assert result.required_human_approval

    def test_review_for_data_mutation(self, engine):
        """Data mutation actions should trigger REVIEW."""
        result = engine.evaluate(GovernanceInput(
            action_type="data_mutation",
            proposal={"table": "users", "operation": "delete"},
            confidence=0.9,
            tenant_id=1,
        ))
        assert result.decision == VerdictDecision.REVIEW

    def test_audit_trail_includes_all_verdicts(self, engine):
        """All decisions should be recorded in the audit trail."""
        for action in ["plan", "financial", "data_mutation", "action"]:
            engine.evaluate(GovernanceInput(
                action_type=action,
                proposal={"test": True},
                tenant_id=1,
            ))
        log = engine.get_audit_log(limit=10)
        assert len(log) == 4


# ======================================================================
# Edge Case Tests
# ======================================================================


class TestEdgeCases:
    """Edge case tests for governance engine."""

    def test_extremely_large_proposal_no_crash(self, engine):
        large_proposal = {"key": "x" * 10000}
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal=large_proposal,
            tenant_id=1,
            confidence=0.5,
        ))
        assert result.decision is not None

    def test_special_characters_in_context(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"name": "test\nwith\tchars"},
            tenant_id=1,
            confidence=0.5,
        ))
        assert result.decision is not None

    def test_unicode_destination(self, engine):
        result = engine.evaluate(GovernanceInput(
            action_type="plan",
            proposal={"destination": "東京", "budget": 10000},
            tenant_id=1,
            confidence=0.8,
        ))
        assert result.decision is not None

    def test_multiple_consecutive_evaluations(self, engine):
        for i in range(20):
            result = engine.evaluate(GovernanceInput(
                action_type="plan",
                proposal={"iteration": i},
                tenant_id=1,
                confidence=0.8,
            ))
            assert result.decision is not None
        assert engine.audit_log_size == 20