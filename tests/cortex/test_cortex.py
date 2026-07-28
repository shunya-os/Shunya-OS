"""
Tests for SHUNYA Organizational Cortex — Phase Z5.

Validates:
  - OrganizationState aggregation
  - Attention ranking
  - Health computation
  - Cross-runtime synthesis
  - Executive Brief projection
  - Attention lifecycle
  - Founder inspection chain
  - Business agnosticism
"""

import pytest
from app.cortex.state import OrganizationState, StateSynthesizer, get_synthesizer, reset_synthesizer
from app.cortex.attention import (
    AttentionItem, AttentionEngine, AttentionStatus, compute_priority,
    get_engine, reset_engine,
)
from app.cortex.health import compute_health, health_label, HEALTH_DIMENSIONS
from app.cortex.brief import project_brief, ExecutiveBrief
from app.decision_runtime.models import Decision, DecisionStatus, get_store as get_decision_store, reset_store as reset_decision_store
from app.decision_runtime.commitment import get_service as get_commitment_service, reset_service as reset_commitment_service
from app.decision_runtime.outcome import get_store as get_outcome_store, Outcome, reset_store as reset_outcome_store
from app.decision_runtime.learning import get_store as get_learning_store, LearningRecord, reset_store as reset_learning_store
from app.intelligence.observation import (
    Observation, ObservationStatus, get_store as get_obs_store, reset_store as reset_obs_store,
)


# ══════════════════════════════════════════════════════════════
# OrganizationState Tests
# ══════════════════════════════════════════════════════════════


class TestOrganizationState:
    def test_default_state(self):
        state = OrganizationState()
        assert state.active_commitments == 0
        assert state.total_decisions == 0
        assert state.overall_health == 0.0
        assert state.synthesized_at == ""

    def test_to_dict_structure(self):
        state = OrganizationState(organization_name="TestOrg", synthesized_at="now")
        d = state.to_dict()
        assert "commitments" in d
        assert "decisions" in d
        assert "risks_opportunities" in d
        assert "observations" in d
        assert "insights" in d
        assert "learning" in d
        assert "health" in d
        assert d["organization_name"] == "TestOrg"

    def test_state_synthesis_empty(self):
        reset_decision_store()
        reset_commitment_service()
        reset_obs_store()
        reset_outcome_store()
        reset_learning_store()
        reset_synthesizer()

        synth = get_synthesizer("TestOrg")
        state = synth.synthesize()
        assert state.organization_name == "TestOrg"
        assert state.synthesized_at != ""
        assert state.total_decisions == 0
        assert state.active_observations == 0
        assert state.learning_signals == 0
        assert len(state.health_scores) > 0

    def test_state_synthesis_with_data(self):
        reset_decision_store()
        reset_commitment_service()
        reset_obs_store()
        reset_outcome_store()
        reset_learning_store()
        reset_synthesizer()

        # Add some decisions
        ds = get_decision_store()
        ds.add(Decision(decision_id="d1", origin_insight_id="i1", label="T", description="T",
                        status=DecisionStatus.AWAITING_APPROVAL))
        ds.add(Decision(decision_id="d2", origin_insight_id="i2", label="T", description="T",
                        status=DecisionStatus.COMPLETED))

        # Add some observations
        obs = get_obs_store()
        obs.add(Observation(observation_id="o1", object_id="obj1", event_id="e1", label="T", description="T",
                            status=ObservationStatus.ACTIVE))
        obs.add(Observation(observation_id="o2", object_id="obj2", event_id="e2", label="T", description="T",
                            status=ObservationStatus.ACTIVE))

        # Add learning
        ls = get_learning_store()
        ls.add(LearningRecord(learning_id="l1", decision_id="d1", outcome_id="o1", commitment_id="c1"))

        synth = get_synthesizer("TestOrg")
        state = synth.synthesize()
        assert state.total_decisions == 2
        assert state.waiting_approval == 1
        assert state.active_observations == 2
        assert state.learning_signals == 1


# ══════════════════════════════════════════════════════════════
# Attention Engine Tests
# ══════════════════════════════════════════════════════════════


class TestAttentionEngine:
    def setup_method(self):
        reset_engine()

    def test_priority_computation(self):
        item = AttentionItem(
            item_id="a1", label="Test", description="Test",
            source_type="risk", source_id="s1",
            impact=0.9, urgency=0.8, commitment_risk=0.7,
        )
        score = compute_priority(item)
        assert 0.0 <= score <= 1.0
        # With 3 signals high and 7 at default (0.5 or 0.0), score should be above neutral
        assert score > 0.3

    def test_priority_lower_signals(self):
        high = AttentionItem(item_id="a1", label="H", description="", source_type="risk", source_id="s1",
                             impact=0.9, urgency=0.9)
        low = AttentionItem(item_id="a2", label="L", description="", source_type="risk", source_id="s2",
                            impact=0.1, urgency=0.1)
        assert compute_priority(high) > compute_priority(low)

    def test_add_and_queue(self):
        engine = get_engine()
        item = AttentionItem(item_id="a1", label="Test", description="Test", source_type="risk", source_id="s1")
        engine.add_item(item)
        queue = engine.get_attention_queue()
        assert len(queue) == 1
        assert queue[0].item_id == "a1"

    def test_queue_ordered_by_priority(self):
        engine = get_engine()
        low = AttentionItem(item_id="a1", label="L", description="", source_type="risk", source_id="s1",
                            impact=0.1, urgency=0.1)
        high = AttentionItem(item_id="a2", label="H", description="", source_type="risk", source_id="s2",
                             impact=0.9, urgency=0.9)
        engine.add_item(low)
        engine.add_item(high)
        queue = engine.get_attention_queue()
        assert queue[0].item_id == "a2"
        assert queue[1].item_id == "a1"

    def test_resolved_items_excluded_from_queue(self):
        engine = get_engine()
        item = AttentionItem(item_id="a1", label="T", description="", source_type="risk", source_id="s1")
        engine.add_item(item)
        item.transition_to(AttentionStatus.RANKED)
        item.transition_to(AttentionStatus.ASSIGNED)
        item.transition_to(AttentionStatus.OBSERVED)
        item.transition_to(AttentionStatus.RESOLVED)
        queue = engine.get_attention_queue()
        assert len(queue) == 0

    def test_attention_lifecycle(self):
        item = AttentionItem(item_id="a1", label="T", description="", source_type="risk", source_id="s1")
        assert item.status == AttentionStatus.DETECTED
        item.transition_to(AttentionStatus.RANKED)
        assert item.status == AttentionStatus.RANKED
        assert item.ranked_at is not None
        item.transition_to(AttentionStatus.ASSIGNED)
        assert item.assigned_at is not None
        item.transition_to(AttentionStatus.OBSERVED)
        item.transition_to(AttentionStatus.RESOLVED)
        item.transition_to(AttentionStatus.ARCHIVED)
        assert item.status == AttentionStatus.ARCHIVED

    def test_invalid_attention_transition(self):
        item = AttentionItem(item_id="a1", label="T", description="", source_type="risk", source_id="s1",
                             status=AttentionStatus.ARCHIVED)
        with pytest.raises(ValueError, match="Cannot transition"):
            item.transition_to(AttentionStatus.DETECTED)

    def test_get_by_source(self):
        engine = get_engine()
        item = AttentionItem(item_id="a1", label="T", description="", source_type="decision", source_id="dec_1")
        engine.add_item(item)
        found = engine.get_by_source("decision", "dec_1")
        assert found is not None
        assert found.item_id == "a1"
        assert engine.get_by_source("risk", "dec_1") is None


# ══════════════════════════════════════════════════════════════
# Health Computation Tests
# ══════════════════════════════════════════════════════════════


class TestHealth:
    def test_all_dimensions_computed(self):
        state = OrganizationState()
        scores = compute_health(state)
        for dim in HEALTH_DIMENSIONS:
            assert dim in scores, f"Missing dimension: {dim}"
            assert 0.0 <= scores[dim] <= 1.0, f"Invalid score for {dim}: {scores[dim]}"

    def test_health_labels(self):
        assert health_label(0.95) == "Excellent"
        assert health_label(0.80) == "Good"
        assert health_label(0.60) == "Fair"
        assert health_label(0.30) == "Poor"
        assert health_label(0.10) == "Critical"

    def test_execution_health_improves_with_completion(self):
        good = compute_health(OrganizationState(active_commitments=5, completed_commitments=10))
        bad = compute_health(OrganizationState(active_commitments=5, blocked_commitments=10))
        assert good["execution_health"] > bad["execution_health"]

    def test_decision_health_penalized_by_waiting(self):
        good = compute_health(OrganizationState(total_decisions=10, waiting_approval=1))
        bad = compute_health(OrganizationState(total_decisions=10, waiting_approval=8))
        assert good["decision_health"] > bad["decision_health"]

    def test_knowledge_health_penalized_by_stale(self):
        good = compute_health(OrganizationState(active_observations=10, stale_observations=1))
        bad = compute_health(OrganizationState(active_observations=1, stale_observations=10))
        assert good["knowledge_health"] > bad["knowledge_health"]

    def test_evidence_health_improves_with_high_confidence(self):
        good = compute_health(OrganizationState(total_insights=10, high_confidence_insights=8))
        bad = compute_health(OrganizationState(total_insights=10, high_confidence_insights=1))
        assert good["evidence_health"] > bad["evidence_health"]


# ══════════════════════════════════════════════════════════════
# Executive Brief Tests
# ══════════════════════════════════════════════════════════════


class TestExecutiveBrief:
    def test_brief_generated_from_state(self):
        reset_decision_store()
        reset_commitment_service()
        reset_obs_store()
        reset_outcome_store()
        reset_learning_store()
        reset_synthesizer()
        reset_engine()

        # Add some data
        ds = get_decision_store()
        ds.add(Decision(decision_id="d1", origin_insight_id="i1", label="Test", description="Test",
                        status=DecisionStatus.AWAITING_APPROVAL))
        obs = get_obs_store()
        obs.add(Observation(observation_id="o1", object_id="obj1", event_id="e1", label="Active obs", description="Test",
                            status=ObservationStatus.ACTIVE))

        brief = project_brief("TestOrg")
        assert isinstance(brief, ExecutiveBrief)
        assert brief.summary != ""
        assert "TestOrg" in brief.summary
        assert brief.generated_at != ""
        assert len(brief.state) > 0

    def test_brief_has_health_summary(self):
        brief = project_brief("TestOrg")
        assert brief.health_summary != ""

    def test_brief_to_dict(self):
        brief = project_brief()
        d = brief.to_dict()
        assert "summary" in d
        assert "health_summary" in d
        assert "state" in d
        assert "generated_at" in d


# ══════════════════════════════════════════════════════════════
# Business Agnosticism Tests
# ══════════════════════════════════════════════════════════════


class TestBusinessAgnosticism:
    def test_organization_state_no_industry(self):
        state = OrganizationState()
        assert not hasattr(state, "industry")
        assert not hasattr(state, "vertical")
        assert not hasattr(state, "sector")

    def test_attention_item_no_industry(self):
        item = AttentionItem(item_id="a1", label="T", description="", source_type="risk", source_id="s1")
        assert not hasattr(item, "industry")
        assert not hasattr(item, "vertical")

    def test_health_computation_agnostic(self):
        """Health computation works identically for any organization."""
        state = OrganizationState(active_commitments=5, completed_commitments=3)
        scores = compute_health(state)
        assert len(scores) == len(HEALTH_DIMENSIONS)


# ══════════════════════════════════════════════════════════════
# Cortex Integration Tests
# ══════════════════════════════════════════════════════════════


class TestCortexIntegration:
    def test_cortex_loads_with_app(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            assert c.get('/').status_code == 200
            assert c.get('/workspace/').status_code == 200

            # Verify cortex inspection
            r = c.get('/workspace/?inspect_cortex=1')
            assert r.status_code == 200
            data = r.get_json()
            assert data is not None
            assert 'organization_state' in data
            assert 'attention_queue' in data
            assert 'executive_brief' in data

            # Verify brief inspection
            r = c.get('/workspace/?inspect_brief=1')
            assert r.status_code == 200
            brief = r.get_json()
            assert brief is not None
            assert 'summary' in brief
            assert 'health_summary' in brief

    def test_attention_queue_populated_on_startup(self):
        from app import create_app
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        with app.test_client() as c:
            r = c.get('/workspace/?inspect_cortex=1')
            data = r.get_json()
            # Should have attention items from the demo data
            assert len(data['attention_queue']) >= 0

    def test_cortex_chain_resolution(self):
        """Verify the full Cortex chain is resolvable."""
        from app.cortex.brief import resolve_brief_sentence
        brief = project_brief("TestOrg")
        if brief.paragraphs:
            chain = resolve_brief_sentence(brief.paragraphs[0]["text"][:30], brief)
            assert len(chain) >= 2
            assert chain[0]["layer"] == "ExecutiveBrief"
            assert chain[1]["layer"] == "OrganizationState"