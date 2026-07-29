"""
Tests for SHUNYA Decision Runtime — Phase Z4.

Validates:
  - Decision lifecycle (transitions, validation, store)
  - Policy evaluation (all actions, priority, default)
  - Commitment integration (BusinessExecutionInstance bridge)
  - Outcome recording
  - Learning generation
  - Decision explainability (chain inspection)
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.decision_runtime.models import (
    Decision, DecisionStatus, DecisionStore, get_store, reset_store,
    VALID_DECISION_TRANSITIONS,
)
from app.decision_runtime.policy import (
    PolicyAction, Policy, PolicyResult, PolicyEngine, get_engine, reset_engine,
    _policy_high_confidence, _policy_low_confidence, _policy_high_impact,
    _policy_critical_urgency, _policy_medium_confidence,
    _policy_high_confidence_low_urgency,
)
from app.decision_runtime.commitment import CommitmentService, get_service, reset_service
from app.decision_runtime.outcome import Outcome, OutcomeStore, get_store as get_outcome_store, reset_store as reset_outcome_store
from app.decision_runtime.learning import LearningRecord, LearningStore, get_store as get_learning_store, reset_store as reset_learning_store


# ══════════════════════════════════════════════════════════════
# Decision Lifecycle Tests
# ══════════════════════════════════════════════════════════════


class TestDecision:
    def test_initial_status(self):
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="Test", description="Test")
        assert d.status == DecisionStatus.CANDIDATE

    def test_valid_transition(self):
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T")
        d.transition_to(DecisionStatus.POLICY_EVALUATING)
        assert d.status == DecisionStatus.POLICY_EVALUATING
        assert d.evaluated_at is not None

    def test_invalid_transition(self):
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T",
                     status=DecisionStatus.COMPLETED)
        with pytest.raises(ValueError, match="Cannot transition"):
            d.transition_to(DecisionStatus.CANDIDATE)

    def test_all_terminal_states_have_no_outgoing(self):
        for terminal in [DecisionStatus.COMPLETED, DecisionStatus.CANCELLED, DecisionStatus.SUPERSEDED]:
            assert VALID_DECISION_TRANSITIONS[terminal] == set()

    def test_full_lifecycle(self):
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T")
        d.transition_to(DecisionStatus.POLICY_EVALUATING)
        d.transition_to(DecisionStatus.APPROVED)
        d.transition_to(DecisionStatus.COMMITTED)
        d.transition_to(DecisionStatus.EXECUTING)
        d.transition_to(DecisionStatus.COMPLETED)
        assert d.status == DecisionStatus.COMPLETED
        assert d.completed_at is not None

    def test_rejected_cancelled(self):
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T",
                     status=DecisionStatus.AWAITING_APPROVAL)
        d.transition_to(DecisionStatus.REJECTED)
        d.transition_to(DecisionStatus.CANCELLED)
        assert d.status == DecisionStatus.CANCELLED

    def test_to_dict(self):
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="Test", description="Desc")
        data = d.to_dict()
        assert data["decision_id"] == "d1"
        assert data["status"] == "candidate"

    def test_decision_agnostic(self):
        """Verify decision objects have no industry assumptions."""
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T")
        assert not hasattr(d, "industry")
        assert not hasattr(d, "vertical")


class TestDecisionStore:
    def setup_method(self):
        reset_store()

    def test_add_and_get(self):
        store = get_store()
        d = Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T")
        store.add(d)
        assert store.get("d1") is d
        assert store.count == 1

    def test_get_by_insight(self):
        store = get_store()
        store.add(Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T"))
        store.add(Decision(decision_id="d2", origin_insight_id="ins1", label="T", description="T"))
        store.add(Decision(decision_id="d3", origin_insight_id="ins2", label="T", description="T"))
        assert len(store.get_by_insight("ins1")) == 2
        assert len(store.get_by_insight("ins2")) == 1

    def test_get_active(self):
        store = get_store()
        store.add(Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T",
                           status=DecisionStatus.CANDIDATE))
        store.add(Decision(decision_id="d2", origin_insight_id="ins1", label="T", description="T",
                           status=DecisionStatus.COMPLETED))
        assert len(store.get_active()) == 1

    def test_clear(self):
        store = get_store()
        store.add(Decision(decision_id="d1", origin_insight_id="ins1", label="T", description="T"))
        store.clear()
        assert store.count == 0


# ══════════════════════════════════════════════════════════════
# Policy Engine Tests
# ══════════════════════════════════════════════════════════════


class TestPolicyEngine:
    def setup_method(self):
        reset_engine()

    def test_default_action(self):
        engine = get_engine()
        # A decision with no matching policies
        result = engine.evaluate({
            "confidence": 0.5,
            "business_impact": "unknown",
            "urgency": "normal",
        })
        # Should match at least one built-in policy (medium confidence recommend)
        assert result.action is not None

    def test_high_confidence_auto(self):
        result = _policy_high_confidence({
            "confidence": 0.95,
            "business_impact": "low",
        })
        assert result is not None
        assert result.action == PolicyAction.EXECUTE_AUTOMATICALLY

    def test_high_confidence_high_impact(self):
        # high_confidence_auto should not match because impact is high
        result = _policy_high_confidence({
            "confidence": 0.95,
            "business_impact": "high",
        })
        assert result is None

    def test_low_confidence_approval(self):
        result = _policy_low_confidence({"confidence": 0.3})
        assert result is not None
        assert result.action == PolicyAction.REQUEST_APPROVAL

    def test_high_impact_approval(self):
        result = _policy_high_impact({"business_impact": "high"})
        assert result is not None
        assert result.action == PolicyAction.REQUEST_APPROVAL

    def test_critical_urgency_escalation(self):
        result = _policy_critical_urgency({"urgency": "critical", "owner": "admin"})
        assert result is not None
        assert result.action == PolicyAction.ESCALATE
        assert result.escalation_target == "admin"

    def test_medium_confidence_recommend(self):
        result = _policy_medium_confidence({"confidence": 0.6})
        assert result is not None
        assert result.action == PolicyAction.RECOMMEND

    def test_high_confidence_low_urgency(self):
        result = _policy_high_confidence_low_urgency({"confidence": 0.8, "urgency": "low"})
        assert result is not None
        assert result.action == PolicyAction.INFORM

    def test_policy_registration(self):
        engine = PolicyEngine()
        assert engine.policy_count == 0
        engine.register(Policy(
            policy_id="test-policy",
            name="Test",
            description="A test policy",
            priority=50,
            evaluate_fn=lambda d: PolicyResult(action=PolicyAction.INFORM, reason="test") if d.get("test") else None,
        ))
        assert engine.policy_count == 1

    def test_policy_priority(self):
        engine = PolicyEngine()
        results = []
        engine.register(Policy(
            policy_id="p1", name="P1", description="",
            priority=10,
            evaluate_fn=lambda d: PolicyResult(action=PolicyAction.INFORM, reason="low") if True else None,
        ))
        engine.register(Policy(
            policy_id="p2", name="P2", description="",
            priority=100,
            evaluate_fn=lambda d: PolicyResult(action=PolicyAction.ESCALATE, reason="high") if True else None,
        ))
        # Higher priority should be evaluated first
        result = engine.evaluate({"confidence": 0.5})
        assert result.action == PolicyAction.ESCALATE


# ══════════════════════════════════════════════════════════════
# Commitment Integration Tests
# ══════════════════════════════════════════════════════════════


class TestCommitment:
    def setup_method(self):
        reset_service()

    def test_create_commitment_from_approved_decision(self):
        service = get_service()
        decision = Decision(
            decision_id="d1", origin_insight_id="ins1", label="Test", description="Test",
            status=DecisionStatus.APPROVED, tenant_id=1,
        )
        result = service.create_commitment(decision)
        assert "commitment_id" in result
        assert "exec_id" in result
        assert decision.status == DecisionStatus.COMMITTED

    def test_create_commitment_from_non_approved(self):
        service = get_service()
        decision = Decision(
            decision_id="d1", origin_insight_id="ins1", label="Test", description="Test",
            status=DecisionStatus.CANDIDATE,
        )
        result = service.create_commitment(decision)
        assert "error" in result

    def test_get_commitment(self):
        service = get_service()
        decision = Decision(
            decision_id="d1", origin_insight_id="ins1", label="Test", description="Test",
            status=DecisionStatus.APPROVED, tenant_id=1,
        )
        result = service.create_commitment(decision)
        cmt = service.get_commitment(result["commitment_id"])
        assert cmt is not None
        assert cmt.decision_id == "d1"

    def test_get_execution(self):
        service = get_service()
        decision = Decision(
            decision_id="d1", origin_insight_id="ins1", label="Test", description="Test",
            status=DecisionStatus.APPROVED, tenant_id=1,
        )
        result = service.create_commitment(decision)
        execution = service.get_execution(result["commitment_id"])
        assert execution is not None
        assert "execution" in execution


# ══════════════════════════════════════════════════════════════
# Outcome Recording Tests
# ══════════════════════════════════════════════════════════════


class TestOutcome:
    def setup_method(self):
        reset_outcome_store()

    def test_create_outcome(self):
        store = get_outcome_store()
        outcome = Outcome(
            outcome_id="o1", commitment_id="cmt1", decision_id="d1",
            label="Test", description="Test outcome",
            quality=0.85,
        )
        store.add(outcome)
        assert store.count == 1

    def test_get_by_decision(self):
        store = get_outcome_store()
        store.add(Outcome(outcome_id="o1", commitment_id="cmt1", decision_id="d1", label="T", description="T"))
        store.add(Outcome(outcome_id="o2", commitment_id="cmt2", decision_id="d2", label="T", description="T"))
        assert store.get_by_decision("d1") is not None
        assert store.get_by_decision("d1").outcome_id == "o1"

    def test_get_by_commitment(self):
        store = get_outcome_store()
        store.add(Outcome(outcome_id="o1", commitment_id="cmt1", decision_id="d1", label="T", description="T"))
        assert store.get_by_commitment("cmt1") is not None
        assert store.get_by_commitment("cmt1").outcome_id == "o1"

    def test_unexpected_effects(self):
        outcome = Outcome(
            outcome_id="o1", commitment_id="cmt1", decision_id="d1",
            label="T", description="T",
            unexpected_effects=["Revenue impact was higher than projected", "Customer churn decreased"],
        )
        assert len(outcome.unexpected_effects) == 2


# ══════════════════════════════════════════════════════════════
# Learning Generation Tests
# ══════════════════════════════════════════════════════════════


class TestLearning:
    def setup_method(self):
        reset_learning_store()

    def test_create_learning_record(self):
        store = get_learning_store()
        record = LearningRecord(
            learning_id="l1", decision_id="d1", outcome_id="o1", commitment_id="cmt1",
            expected_outcome="Revenue increase of 15%",
            actual_outcome="Revenue increase of 18%",
            variance="Better than expected by 3%",
            variance_magnitude=0.2,
            reason="Market conditions were more favourable than projected",
            improvement_opportunity="Increase growth projections for similar scenarios",
            learning_confidence=0.85,
        )
        store.add(record)
        assert store.count == 1
        assert store.get("l1") is record

    def test_get_by_decision(self):
        store = get_learning_store()
        store.add(LearningRecord(learning_id="l1", decision_id="d1", outcome_id="o1", commitment_id="cmt1"))
        store.add(LearningRecord(learning_id="l2", decision_id="d2", outcome_id="o2", commitment_id="cmt2"))
        assert store.get_by_decision("d1") is not None
        assert store.get_by_decision("d1").learning_id == "l1"

    def test_get_all(self):
        store = get_learning_store()
        store.add(LearningRecord(learning_id="l1", decision_id="d1", outcome_id="o1", commitment_id="cmt1"))
        store.add(LearningRecord(learning_id="l2", decision_id="d2", outcome_id="o2", commitment_id="cmt2"))
        assert len(store.get_all()) == 2


# ══════════════════════════════════════════════════════════════
# Decision Explainability Tests
# ══════════════════════════════════════════════════════════════


class TestDecisionExplainability:
    def test_decision_to_chain_resolution(self):
        """Verify a decision can be traced through the full chain."""
        from app.decision_runtime.models import Decision, DecisionStatus, get_store as get_decision_store
        from app.decision_runtime.policy import get_engine as get_policy_engine
        from app.decision_runtime.commitment import get_service as get_commitment_service
        from app.decision_runtime.outcome import get_store as get_outcome_store, Outcome
        from app.decision_runtime.learning import get_store as get_learning_store, LearningRecord

        # Reset all stores
        reset_store()
        reset_engine()
        reset_service()
        reset_outcome_store()
        reset_learning_store()

        # Create a decision
        decision_store = get_decision_store()
        decision = Decision(
            decision_id="dec_test_1",
            origin_insight_id="insight_test",
            label="Test decision",
            description="Test for explainability",
            confidence=0.85,
            status=DecisionStatus.APPROVED,
            tenant_id=1,
        )
        decision_store.add(decision)

        # Create a commitment
        commitment_service = get_commitment_service()
        result = commitment_service.create_commitment(decision)

        # Record an outcome
        outcome_store = get_outcome_store()
        outcome = Outcome(
            outcome_id="out_test_1",
            commitment_id=result["commitment_id"],
            decision_id="dec_test_1",
            label="Test outcome",
            description="Test outcome description",
            quality=0.9,
        )
        outcome_store.add(outcome)

        # Record learning
        learning_store = get_learning_store()
        learning = LearningRecord(
            learning_id="lrn_test_1",
            decision_id="dec_test_1",
            outcome_id="out_test_1",
            commitment_id=result["commitment_id"],
            expected_outcome="Expected X",
            actual_outcome="Got Y",
            variance="X vs Y",
            variance_magnitude=0.3,
            reason="Market conditions",
            learning_confidence=0.8,
        )
        learning_store.add(learning)

        # Verify the full chain
        assert decision_store.get("dec_test_1") is not None
        assert commitment_service.get_by_decision("dec_test_1") is not None
        assert outcome_store.get_by_decision("dec_test_1") is not None
        assert learning_store.get_by_decision("dec_test_1") is not None

        # Verify the chain IDs connect
        chain = [
            ("decision", decision_store.get("dec_test_1")),
            ("commitment", commitment_service.get_by_decision("dec_test_1")),
            ("outcome", outcome_store.get_by_decision("dec_test_1")),
            ("learning", learning_store.get_by_decision("dec_test_1")),
        ]
        for name, obj in chain:
            assert obj is not None, f"Missing {name} in chain"

    def test_decision_agnostic_across_chain(self):
        """Verify the entire decision chain has no industry assumptions."""
        from app.decision_runtime.models import Decision
        from app.decision_runtime.outcome import Outcome
        from app.decision_runtime.learning import LearningRecord

        for cls in [Decision, Outcome, LearningRecord]:
            instance = cls.__new__(cls)
            # Check no industry-specific attributes
            for attr in ["industry", "vertical", "sector", "business_type"]:
                assert not hasattr(instance, attr), f"{cls.__name__} has {attr}"

    def test_decision_integration_with_app(self):
        """Verify the app factory loads with decision runtime."""
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            # Verify app is running — use /health (always available regardless of
            # frontend build status) instead of / (which 503s without built SPA).
            r = c.get('/health')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert data.get('status') == 'ok'

            # Verify decision inspection — the before_request middleware
            # intercepts inspect_decision_system=1 on any route path.
            r = c.get('/workspace/?inspect_decision_system=1')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'decisions' in data
            assert 'policies' in data
            assert 'commitments' in data
            assert 'outcomes' in data
            assert 'learning' in data