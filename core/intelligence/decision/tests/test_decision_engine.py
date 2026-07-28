"""
SHUNYA — Decision Engine Tests

Tests for the Decision Engine covering:
- Decision lifecycle transitions
- Policy rule evaluation
- Evidence sufficiency validation
- Option management
- Engine interface compliance
"""
import pytest

from core.intelligence.decision import (
    DECISION_VALID_TRANSITIONS,
    DecisionEngine,
    DecisionOption,
    DecisionStatus,
    PolicyRule,
)
from core.intelligence.models import EngineInput

# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def engine() -> DecisionEngine:
    """Create a fresh DecisionEngine for each test."""
    return DecisionEngine()


@pytest.fixture
def sample_decision_payload() -> dict:
    """Sample decision creation payload."""
    return {
        "label": "Approve vendor payment",
        "description": "Should we pay vendor ACME Corp $50,000?",
        "owner": "user_123",
        "created_by": "user_123",
        "decision_type": "standard",
    }


# ── Decision Lifecycle ─────────────────────────────────────────────────────────


class TestDecisionLifecycle:
    """Test the decision lifecycle state machine."""

    @pytest.mark.asyncio
    async def test_create_decision(self, engine: DecisionEngine, sample_decision_payload: dict):
        """Test creating a decision via process()."""
        result = await engine.process(EngineInput(
            input_type="create_decision",
            payload=sample_decision_payload,
        ))
        assert result.payload["status"] == "candidate"
        assert result.payload["decision_id"]
        assert result.confidence >= 0.0
        assert result.deterministic

    @pytest.mark.asyncio
    async def test_create_decision_missing_label(self, engine: DecisionEngine):
        """Test that creating a decision without a label returns an error."""
        result = await engine.process(EngineInput(
            input_type="create_decision",
            payload={"owner": "user_123"},
        ))
        assert "error" in result.payload
        assert "label" in result.payload["error"]

    @pytest.mark.asyncio
    async def test_create_decision_missing_owner(self, engine: DecisionEngine):
        """Test that creating a decision without an owner returns an error."""
        result = await engine.process(EngineInput(
            input_type="create_decision",
            payload={"label": "Test"},
        ))
        assert "error" in result.payload
        assert "owner" in result.payload["error"]

    def test_valid_transition(self, engine: DecisionEngine):
        """Test a valid lifecycle transition."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        # Transition CANDIDATE -> POLICY_EVALUATION
        updated = engine.transition(
            decision_id=did,
            target_status=DecisionStatus.POLICY_EVALUATION,
            actor_id="user_123",
            reason="Starting evaluation",
        )
        assert updated.status == DecisionStatus.POLICY_EVALUATION
        assert len(updated.status_history) == 1

    def test_invalid_transition(self, engine: DecisionEngine):
        """Test that invalid transitions raise ValueError."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        # Cannot go directly from CANDIDATE to APPROVED
        with pytest.raises(ValueError, match="Cannot transition"):
            engine.transition(
                decision_id=did,
                target_status=DecisionStatus.APPROVED,
                actor_id="user_123",
                reason="Skip steps",
            )

    def test_full_lifecycle(self, engine: DecisionEngine):
        """Test a complete decision lifecycle."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        path = [
            DecisionStatus.POLICY_EVALUATION,
            DecisionStatus.UNDER_REVIEW,
            DecisionStatus.APPROVED,
            DecisionStatus.EXECUTING,
            DecisionStatus.COMPLETED,
        ]

        for target in path:
            updated = engine.transition(
                decision_id=did,
                target_status=target,
                actor_id="user_123",
                reason=f"Moving to {target.value}",
            )
            assert updated.status == target

        # Verify completed_at is set
        final = engine.get_decision(did)
        assert final is not None
        assert final.completed_at is not None

    def test_failed_execution(self, engine: DecisionEngine):
        """Test that a decision can fail during execution."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        engine.transition(did, DecisionStatus.POLICY_EVALUATION, "user_123")
        engine.transition(did, DecisionStatus.UNDER_REVIEW, "user_123")
        engine.transition(did, DecisionStatus.APPROVED, "user_123")
        engine.transition(did, DecisionStatus.EXECUTING, "user_123")
        updated = engine.transition(did, DecisionStatus.FAILED, "user_123", "Execution error")

        assert updated.status == DecisionStatus.FAILED
        assert updated.completed_at is not None

    def test_rejected_decision(self, engine: DecisionEngine):
        """Test that a decision can be rejected."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        updated = engine.transition(
            did, DecisionStatus.REJECTED, "user_123", "Not needed"
        )
        assert updated.status == DecisionStatus.REJECTED

    def test_sent_back_to_candidate(self, engine: DecisionEngine):
        """Test that a decision can be sent back for revision."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        engine.transition(did, DecisionStatus.POLICY_EVALUATION, "user_123")
        engine.transition(did, DecisionStatus.UNDER_REVIEW, "user_123")
        engine.transition(did, DecisionStatus.SENT_BACK, "user_123", "Need more info")

        # SENT_BACK can go back to CANDIDATE
        updated = engine.transition(
            did, DecisionStatus.CANDIDATE, "user_123", "Revised"
        )
        assert updated.status == DecisionStatus.CANDIDATE

    def test_same_status_transition(self, engine: DecisionEngine):
        """Test that transitioning to the same status is a no-op."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        # Should not raise
        updated = engine.transition(
            did, DecisionStatus.CANDIDATE, "user_123", "No change"
        )
        assert updated.status == DecisionStatus.CANDIDATE


# ── Policy Rules ────────────────────────────────────────────────────────────────


class TestPolicyRules:
    """Test policy rule evaluation."""

    def test_add_policy_rule(self, engine: DecisionEngine):
        """Test adding a policy rule."""
        rule_id = engine.add_policy_rule(PolicyRule(
            name="amount_threshold",
            rule_type="block",
            condition={"field": "amount", "operator": ">", "value": 100000},
            priority=1,
            reason="Block payments over $100K",
        ))
        assert rule_id
        assert len(engine.get_policy_rules()) == 1

    def test_add_invalid_rule_type(self, engine: DecisionEngine):
        """Test that invalid rule types are rejected."""
        with pytest.raises(ValueError, match="Invalid rule_type"):
            engine.add_policy_rule(PolicyRule(
                name="bad",
                rule_type="invalid_type",
                condition={},
            ))

    def test_remove_policy_rule(self, engine: DecisionEngine):
        """Test removing a policy rule."""
        rule_id = engine.add_policy_rule(PolicyRule(
            name="test", rule_type="allow", condition={}, priority=1
        ))
        assert engine.remove_policy_rule(rule_id)
        assert not engine.remove_policy_rule("nonexistent")

    @pytest.mark.asyncio
    async def test_block_rule_blocks_decision(self, engine: DecisionEngine):
        """Test that a block rule blocks a decision."""
        engine.add_policy_rule(PolicyRule(
            name="high_value",
            rule_type="block",
            condition={"field": "payload.amount", "operator": ">", "value": 100000},
            priority=1,
            reason="High value payments need extra review",
        ))

        decision = engine._handle_create_decision(
            {"label": "Large payment", "owner": "user_123", "payload": {"amount": 150000}},
            "trace_1",
        )
        did = decision["decision_id"]

        # Create a decision with amount > 100K
        result = await engine.process(EngineInput(
            input_type="evaluate_policy",
            payload={"decision_id": did},
        ))

        assert result.payload["blocked"] is True
        assert not result.payload["all_passed"]

    @pytest.mark.asyncio
    async def test_allow_rule_passes(self, engine: DecisionEngine):
        """Test that an allow rule passes."""
        engine.add_policy_rule(PolicyRule(
            name="low_value",
            rule_type="allow",
            condition={"field": "payload.amount", "operator": "<", "value": 1000},
            priority=1,
            reason="Low value payments are auto-approved",
        ))

        decision = engine._handle_create_decision(
            {"label": "Small payment", "owner": "user_123", "payload": {"amount": 500}},
            "trace_1",
        )
        did = decision["decision_id"]

        result = await engine.process(EngineInput(
            input_type="evaluate_policy",
            payload={"decision_id": did},
        ))

        # Allow rule passes — decision is not blocked
        assert not result.payload["blocked"]

    def test_rule_priority_order(self, engine: DecisionEngine):
        """Test that rules are evaluated in priority order."""
        engine.add_policy_rule(PolicyRule(
            name="high_priority", rule_type="block",
            condition={"field": "label", "operator": "==", "value": "Test"},
            priority=0,  # Highest priority
        ))
        engine.add_policy_rule(PolicyRule(
            name="low_priority", rule_type="allow",
            condition={},  # Always passes
            priority=10,
        ))

        rules = engine.get_policy_rules()
        assert rules[0].priority == 0
        assert rules[1].priority == 10


# ── Evidence Sufficiency ────────────────────────────────────────────────────────


class TestEvidenceSufficiency:
    """Test evidence sufficiency validation."""

    def test_no_evidence_not_sufficient(self, engine: DecisionEngine):
        """Test that a decision with no evidence fails sufficiency."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        sufficiency = engine.check_evidence_sufficiency(
            decision_id=did, minimum_count=1
        )
        assert not sufficiency.satisfied
        assert "Need 1 evidence records, have 0" in sufficiency.reason

    def test_sufficient_with_evidence_ids(self, engine: DecisionEngine):
        """Test sufficiency with evidence attached."""
        decision = engine._handle_create_decision(
            {
                "label": "Test",
                "owner": "user_123",
                "evidence_ids": ["ev_1", "ev_2", "ev_3"],
            },
            "trace_1",
        )
        did = decision["decision_id"]

        sufficiency = engine.check_evidence_sufficiency(
            decision_id=did, minimum_count=2
        )
        assert sufficiency.satisfied

    def test_minimum_confidence_not_met(self, engine: DecisionEngine):
        """Test that minimum confidence requirement without evidence engine fails."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        sufficiency = engine.check_evidence_sufficiency(
            decision_id=did,
            minimum_count=0,
            minimum_confidence=0.5,
        )
        # Without evidence engine, confidence is 0.0
        assert not sufficiency.satisfied


# ── Option Management ────────────────────────────────────────────────────────────


class TestOptionManagement:
    """Test decision option management."""

    def test_add_option(self, engine: DecisionEngine):
        """Test adding an option to a decision."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        option = DecisionOption(label="Approve", description="Go ahead", confidence=0.8)
        updated = engine.add_option(did, option)
        assert len(updated.options) == 1
        assert updated.options[0].label == "Approve"

    @pytest.mark.asyncio
    async def test_select_option_by_id(self, engine: DecisionEngine):
        """Test selecting an option by option_id."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        option = DecisionOption(label="Approve", confidence=0.9)
        engine.add_option(did, option)

        result = await engine.process(EngineInput(
            input_type="select_option",
            payload={"decision_id": did, "option_id": option.option_id},
        ))
        assert result.payload["selected_option"].option_id == option.option_id

    @pytest.mark.asyncio
    async def test_select_option_by_index(self, engine: DecisionEngine):
        """Test selecting an option by index."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        engine.add_option(did, DecisionOption(label="Option A", confidence=0.7))
        engine.add_option(did, DecisionOption(label="Option B", confidence=0.9))

        result = await engine.process(EngineInput(
            input_type="select_option",
            payload={"decision_id": did, "option_index": 1},
        ))
        assert result.payload["selected_option"].label == "Option B"

    @pytest.mark.asyncio
    async def test_select_option_invalid_index(self, engine: DecisionEngine):
        """Test that selecting an invalid index raises."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        result = await engine.process(EngineInput(
            input_type="select_option",
            payload={"decision_id": did, "option_index": 99},
        ))
        assert "error" in result.payload

    @pytest.mark.asyncio
    async def test_generate_options(self, engine: DecisionEngine):
        """Test generating deterministic options."""
        result = await engine.process(EngineInput(
            input_type="generate_options",
            payload={
                "label": "Test decision",
                "description": "Should we proceed?",
            },
            confidence_threshold=0.5,  # Low threshold to avoid escalation
        ))
        assert len(result.payload["options"]) == 3
        assert result.payload["options"][0]["label"] == "Approve"


# ── Engine Interface ────────────────────────────────────────────────────────────


class TestEngineInterface:
    """Test the DecisionEngine's IntelligenceEngine interface compliance."""

    def test_get_capabilities(self, engine: DecisionEngine):
        """Test that capabilities are returned."""
        caps = engine.get_capabilities()
        assert isinstance(caps, list)
        assert len(caps) > 0
        assert "create_decision" in caps
        assert "evaluate_policy" in caps
        assert "transition_decision" in caps

    def test_health_check(self, engine: DecisionEngine):
        """Test health check returns valid status."""
        health = engine.health_check()
        assert health["engine_id"] == "decision_engine"
        assert health["engine_type"] == "decision"
        assert health["status"] in ("active", "degraded", "offline")
        assert "total_decisions" in health
        assert "total_policy_rules" in health

    def test_escalate(self, engine: DecisionEngine):
        """Test that escalation produces a valid result."""
        result = engine.escalate(EngineInput(
            input_type="generate_options",
            payload={"label": "Test", "description": "Test desc"},
        ))
        assert result.input_type == "generate_options"
        assert result.prompt
        assert "Test" in result.prompt

    @pytest.mark.asyncio
    async def test_unknown_input_type(self, engine: DecisionEngine):
        """Test that unknown input types return an error."""
        result = await engine.process(EngineInput(
            input_type="nonexistent",
            payload={},
        ))
        assert "error" in result.payload

    @pytest.mark.asyncio
    async def test_importable(self):
        """Test that the engine is importable from the expected path."""
        from core.intelligence.decision import DecisionEngine
        assert DecisionEngine is not None


# ── Decision Retrieval ──────────────────────────────────────────────────────────


class TestDecisionRetrieval:
    """Test decision retrieval and listing."""

    def test_get_decision(self, engine: DecisionEngine):
        """Test retrieving a decision by ID."""
        decision = engine._handle_create_decision(
            {"label": "Test", "owner": "user_123"}, "trace_1"
        )
        did = decision["decision_id"]

        retrieved = engine.get_decision(did)
        assert retrieved is not None
        assert retrieved.label == "Test"

    def test_get_nonexistent_decision(self, engine: DecisionEngine):
        """Test that getting a nonexistent decision returns None."""
        assert engine.get_decision("nonexistent") is None

    def test_list_decisions_by_status(self, engine: DecisionEngine):
        """Test listing decisions filtered by status."""
        engine._handle_create_decision({"label": "A", "owner": "u1"}, "t1")
        engine._handle_create_decision({"label": "B", "owner": "u1"}, "t2")
        engine._handle_create_decision({"label": "C", "owner": "u2"}, "t3")

        decisions = engine.list_decisions(status=DecisionStatus.CANDIDATE)
        assert len(decisions) == 3

        decisions = engine.list_decisions(owner="u1")
        assert len(decisions) == 2

        decisions = engine.list_decisions(owner="u2")
        assert len(decisions) == 1

    def test_decision_count(self, engine: DecisionEngine):
        """Test total decision count."""
        assert engine.get_decision_count() == 0
        engine._handle_create_decision({"label": "A", "owner": "u1"}, "t1")
        assert engine.get_decision_count() == 1


# ── Valid Transitions Map ───────────────────────────────────────────────────────


class TestValidTransitions:
    """Test the valid transitions map integrity."""

    def test_all_statuses_covered(self):
        """Test that every DecisionStatus appears in the transitions map."""
        for status in DecisionStatus:
            assert status in DECISION_VALID_TRANSITIONS, (
                f"Missing transitions for {status.value}"
            )

    def test_no_self_loops(self):
        """Test that no status transitions to itself."""
        for status, targets in DECISION_VALID_TRANSITIONS.items():
            assert status not in targets, (
                f"Self-loop detected for {status.value}"
            )

    def test_terminal_states_have_no_outgoing(self):
        """Test that terminal states have no outgoing transitions."""
        for status in (DecisionStatus.COMPLETED, DecisionStatus.FAILED,
                       DecisionStatus.REJECTED, DecisionStatus.BLOCKED):
            assert DECISION_VALID_TRANSITIONS[status] == [], (
                f"Terminal state {status.value} should have no outgoing transitions"
            )

    def test_transitions_targets_are_valid(self):
        """Test that all transition targets are valid DecisionStatus values."""
        all_statuses = set(DecisionStatus)
        for status, targets in DECISION_VALID_TRANSITIONS.items():
            for target in targets:
                assert target in all_statuses, (
                    f"Invalid target {target.value} in transitions from {status.value}"
                )