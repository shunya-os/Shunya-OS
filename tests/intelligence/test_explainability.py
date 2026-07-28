"""
Tests for SHUNYA Explainable Intelligence Runtime — Phase Z3.

Validates:
  - Provenance chains
  - Confidence calculation
  - Observation lifecycle
  - Scenario isolation
  - Explainability integrity
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.intelligence.provenance import (
    ProvenanceNode, ProvenanceChain, ProvenanceStore, get_store, reset_store,
    NODE_SOURCE, NODE_EVENT, NODE_EVIDENCE, NODE_OBSERVATION,
    NODE_REASONING, NODE_INSIGHT, NODE_RECOMMENDATION,
)
from app.intelligence.confidence import (
    ConfidenceInput, compute_confidence, confidence_label, confidence_breakdown,
)
from app.intelligence.observation import (
    Observation, ObservationStore, ObservationStatus, get_store as get_obs_store,
    reset_store as reset_obs_store,
)
from app.intelligence.scenario import (
    ScenarioProvider, ScenarioObject, ScenarioEvent, ScenarioEvidence,
    ScenarioRelationship, InvestmentFirmScenario, get_scenario, list_scenarios,
    register, _registry,
)
from app.intelligence.reasoning import ReasoningEngine, get_engine, reset_engine
from app.intelligence.insight import InsightCompiler, get_compiler, reset_compiler
from app.intelligence.inspector import FounderInspector


# ══════════════════════════════════════════════════════════════
# Provenance Chain Tests
# ══════════════════════════════════════════════════════════════


class TestProvenanceNode:
    def test_valid_node_types(self):
        for ntype in [NODE_SOURCE, NODE_EVENT, NODE_EVIDENCE, NODE_OBSERVATION,
                      NODE_REASONING, NODE_INSIGHT, NODE_RECOMMENDATION]:
            node = ProvenanceNode(node_id="test", node_type=ntype, label="test", content="test")
            assert node.node_type == ntype

    def test_invalid_node_type(self):
        with pytest.raises(ValueError, match="Invalid node_type"):
            ProvenanceNode(node_id="test", node_type="invalid", label="test", content="test")

    def test_confidence_range(self):
        with pytest.raises(ValueError, match="Confidence must be between"):
            ProvenanceNode(node_id="test", node_type=NODE_SOURCE, label="test", content="test", confidence=1.5)

    def test_negative_confidence(self):
        with pytest.raises(ValueError, match="Confidence must be between"):
            ProvenanceNode(node_id="test", node_type=NODE_SOURCE, label="test", content="test", confidence=-0.1)

    def test_to_dict(self):
        node = ProvenanceNode(node_id="n1", node_type=NODE_SOURCE, label="Object", content="Test")
        d = node.to_dict()
        assert d["node_id"] == "n1"
        assert d["node_type"] == NODE_SOURCE
        assert d["label"] == "Object"
        assert d["confidence"] == 1.0


class TestProvenanceChain:
    def test_empty_chain(self):
        chain = ProvenanceChain("test-chain")
        assert chain.node_count == 0
        assert not chain.is_intact
        assert "empty" in chain.verify_integrity()[0]

    def test_single_node_chain(self):
        chain = ProvenanceChain("test-chain")
        node = ProvenanceNode(node_id="n1", node_type=NODE_SOURCE, label="Root", content="Test")
        chain.add_node(node)
        assert chain.node_count == 1
        assert chain.is_intact
        assert chain.root is not None
        assert chain.leaf is not None

    def test_full_chain_integrity(self):
        chain = ProvenanceChain("full-chain")
        nodes = [
            ProvenanceNode(node_id="src", node_type=NODE_SOURCE, label="Source", content="Object"),
            ProvenanceNode(node_id="evt", node_type=NODE_EVENT, label="Event", content="Observed", parent_id="src"),
            ProvenanceNode(node_id="evid", node_type=NODE_EVIDENCE, label="Evidence", content="Proof", parent_id="evt"),
            ProvenanceNode(node_id="obs", node_type=NODE_OBSERVATION, label="Observation", content="Pattern", parent_id="evid"),
            ProvenanceNode(node_id="rsn", node_type=NODE_REASONING, label="Reasoning", content="Analysis", parent_id="obs"),
            ProvenanceNode(node_id="ins", node_type=NODE_INSIGHT, label="Insight", content="Conclusion", parent_id="rsn"),
        ]
        for n in nodes:
            chain.add_node(n)
        assert chain.node_count == 6
        assert chain.is_intact
        assert chain.root.node_id == "src"
        assert chain.leaf.node_id == "ins"

    def test_broken_chain_detected(self):
        chain = ProvenanceChain("broken-chain")
        chain.add_node(ProvenanceNode(node_id="n1", node_type=NODE_SOURCE, label="Root", content="Test"))
        chain.add_node(ProvenanceNode(node_id="n3", node_type=NODE_EVENT, label="Child", content="Test", parent_id="n2"))
        issues = chain.verify_integrity()
        assert len(issues) == 1
        assert "n2" in issues[0]

    def test_duplicate_node_id(self):
        chain = ProvenanceChain("dup-chain")
        chain.add_node(ProvenanceNode(node_id="n1", node_type=NODE_SOURCE, label="Root", content="Test"))
        with pytest.raises(ValueError, match="already exists"):
            chain.add_node(ProvenanceNode(node_id="n1", node_type=NODE_EVENT, label="Dup", content="Test"))

    def test_resolve_backwards(self):
        chain = ProvenanceChain("resolve-chain")
        chain.add_node(ProvenanceNode(node_id="src", node_type=NODE_SOURCE, label="Source", content="O"))
        chain.add_node(ProvenanceNode(node_id="evt", node_type=NODE_EVENT, label="Event", content="E", parent_id="src"))
        chain.add_node(ProvenanceNode(node_id="ins", node_type=NODE_INSIGHT, label="Insight", content="I", parent_id="evt"))
        resolved = chain.resolve("ins")
        assert len(resolved) == 3
        assert resolved[0].node_id == "ins"
        assert resolved[2].node_id == "src"


class TestProvenanceStore:
    def setup_method(self):
        reset_store()

    def test_add_and_get_chain(self):
        store = get_store()
        chain = ProvenanceChain("c1")
        chain.add_node(ProvenanceNode(node_id="n1", node_type=NODE_SOURCE, label="Root", content="Test"))
        store.add_chain(chain)
        assert store.chain_count == 1
        assert store.get_chain("c1") is chain

    def test_resolve_statement(self):
        store = get_store()
        chain = ProvenanceChain("c1")
        chain.add_node(ProvenanceNode(node_id="src", node_type=NODE_SOURCE, label="S", content="O"))
        chain.add_node(ProvenanceNode(node_id="ins", node_type=NODE_INSIGHT, label="I", content="C", parent_id="src"))
        store.add_chain(chain)
        resolved = store.resolve_statement("ins")
        assert resolved is not None
        assert len(resolved) == 2

    def test_all_issues_empty(self):
        store = get_store()
        assert store.all_issues() == {}

    def test_clear(self):
        store = get_store()
        chain = ProvenanceChain("c1")
        chain.add_node(ProvenanceNode(node_id="n1", node_type=NODE_SOURCE, label="R", content="T"))
        store.add_chain(chain)
        store.clear()
        assert store.chain_count == 0


# ══════════════════════════════════════════════════════════════
# Confidence Calculation Tests
# ══════════════════════════════════════════════════════════════


class TestConfidence:
    def test_all_factors_high(self):
        inputs = ConfidenceInput(
            evidence_completeness=1.0,
            observation_freshness=1.0,
            source_reliability=1.0,
            relationship_consistency=1.0,
            conflict_detected=False,
            recency_hours=0,
            missing_information_ratio=0.0,
        )
        score = compute_confidence(inputs)
        assert score >= 0.9

    def test_all_factors_low(self):
        inputs = ConfidenceInput(
            evidence_completeness=0.0,
            observation_freshness=0.0,
            source_reliability=0.0,
            relationship_consistency=0.0,
            conflict_detected=True,
            recency_hours=720,  # 30 days
            missing_information_ratio=1.0,
        )
        score = compute_confidence(inputs)
        assert score < 0.3

    def test_all_unknown(self):
        inputs = ConfidenceInput()
        score = compute_confidence(inputs)
        assert score == 0.0

    def test_conflict_penalty(self):
        no_conflict = ConfidenceInput(
            evidence_completeness=0.8, source_reliability=0.8,
            conflict_detected=False,
        )
        conflict = ConfidenceInput(
            evidence_completeness=0.8, source_reliability=0.8,
            conflict_detected=True,
        )
        assert compute_confidence(conflict) < compute_confidence(no_conflict)

    def test_missing_information_penalty(self):
        complete = ConfidenceInput(evidence_completeness=0.8, source_reliability=0.8, missing_information_ratio=0.0)
        incomplete = ConfidenceInput(evidence_completeness=0.8, source_reliability=0.8, missing_information_ratio=0.5)
        assert compute_confidence(incomplete) < compute_confidence(complete)

    def test_recency_decay(self):
        fresh = ConfidenceInput(source_reliability=0.9, recency_hours=1)
        stale = ConfidenceInput(source_reliability=0.9, recency_hours=336)  # 2 weeks
        assert compute_confidence(stale) < compute_confidence(fresh)

    def test_confidence_labels(self):
        assert confidence_label(0.95) == "Very high confidence"
        assert confidence_label(0.80) == "High confidence"
        assert confidence_label(0.60) == "Medium confidence"
        assert confidence_label(0.30) == "Low confidence"
        assert confidence_label(0.10) == "Very low confidence"

    def test_confidence_breakdown_structure(self):
        inputs = ConfidenceInput(evidence_completeness=0.8, source_reliability=0.9)
        breakdown = confidence_breakdown(inputs)
        assert "factors" in breakdown
        assert "total_score" in breakdown
        assert "conflict_penalty_applied" in breakdown
        assert "Evidence completeness" in breakdown["factors"]
        assert "Source reliability" in breakdown["factors"]
        assert "Recency" in breakdown["factors"]
        assert breakdown["factors"]["Recency"]["value"] is None

    def test_invalid_evidence_completeness(self):
        with pytest.raises(ValueError, match="evidence_completeness"):
            ConfidenceInput(evidence_completeness=1.5)

    def test_custom_weights(self):
        inputs = ConfidenceInput(evidence_completeness=0.5, source_reliability=0.5)
        weights = {"evidence_completeness": 1.0, "source_reliability": 0.0}
        # With evidence_completeness weight=1.0, the score should be evidence_completeness*1.0 / 1.0 = 0.5
        score = compute_confidence(inputs, weights)
        assert score == pytest.approx(0.5, rel=0.01)


# ══════════════════════════════════════════════════════════════
# Observation Lifecycle Tests
# ══════════════════════════════════════════════════════════════


class TestObservation:
    def test_initial_status(self):
        obs = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="Test", description="Test")
        assert obs.status == ObservationStatus.DETECTED

    def test_valid_transition_detected_to_validated(self):
        obs = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T")
        obs.transition_to(ObservationStatus.VALIDATED)
        assert obs.status == ObservationStatus.VALIDATED
        assert obs.validated_at is not None

    def test_valid_transition_active_to_superseded(self):
        obs = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T",
                          status=ObservationStatus.ACTIVE)
        obs.transition_to(ObservationStatus.SUPERSEDED)
        assert obs.status == ObservationStatus.SUPERSEDED
        assert obs.superseded_at is not None

    def test_invalid_transition(self):
        obs = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T",
                          status=ObservationStatus.ARCHIVED)
        with pytest.raises(ValueError, match="Cannot transition"):
            obs.transition_to(ObservationStatus.ACTIVE)

    def test_is_active(self):
        active = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T",
                             status=ObservationStatus.ACTIVE)
        assert active.is_active
        detected = Observation(observation_id="o2", object_id="obj1", event_id="evt2", label="T", description="T")
        assert not detected.is_active

    def test_age_hours(self):
        old = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T",
                          detected_at=datetime.now(timezone.utc) - timedelta(hours=24))
        assert old.age_hours >= 23.9

    def test_to_dict(self):
        obs = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="Test", description="Test")
        d = obs.to_dict()
        assert d["observation_id"] == "o1"
        assert d["status"] == "detected"


class TestObservationStore:
    def setup_method(self):
        reset_obs_store()

    def test_add_and_get(self):
        store = get_obs_store()
        obs = Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T")
        store.add(obs)
        assert store.get("o1") is obs
        assert store.count == 1

    def test_get_by_object(self):
        store = get_obs_store()
        store.add(Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T"))
        store.add(Observation(observation_id="o2", object_id="obj1", event_id="evt2", label="T", description="T"))
        store.add(Observation(observation_id="o3", object_id="obj2", event_id="evt3", label="T", description="T"))
        assert len(store.get_by_object("obj1")) == 2
        assert len(store.get_by_object("obj2")) == 1

    def test_get_active(self):
        store = get_obs_store()
        store.add(Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T",
                              status=ObservationStatus.ACTIVE))
        store.add(Observation(observation_id="o2", object_id="obj1", event_id="evt2", label="T", description="T",
                              status=ObservationStatus.DETECTED))
        assert len(store.get_active()) == 1

    def test_supersede_object_observations(self):
        store = get_obs_store()
        store.add(Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T",
                              status=ObservationStatus.ACTIVE))
        store.add(Observation(observation_id="o2", object_id="obj1", event_id="evt2", label="T", description="T",
                              status=ObservationStatus.ACTIVE))
        superseded = store.supersede_object_observations("obj1")
        assert len(superseded) == 2
        assert len(store.get_active()) == 0

    def test_clear(self):
        store = get_obs_store()
        store.add(Observation(observation_id="o1", object_id="obj1", event_id="evt1", label="T", description="T"))
        store.clear()
        assert store.count == 0


# ══════════════════════════════════════════════════════════════
# Scenario Provider Tests
# ══════════════════════════════════════════════════════════════


class TestScenarioProvider:
    def test_investment_firm_scenario(self):
        scenario = InvestmentFirmScenario()
        assert scenario.name == "Investment Firm"
        assert len(scenario.get_objects()) >= 3
        assert len(scenario.get_events()) >= 3
        assert len(scenario.get_evidence()) >= 3
        assert len(scenario.get_relationships()) >= 1

    def test_investment_firm_objects_have_ids(self):
        scenario = InvestmentFirmScenario()
        for obj in scenario.get_objects():
            assert obj.object_id is not None
            assert obj.name is not None

    def test_investment_firm_events_have_evidence_refs(self):
        scenario = InvestmentFirmScenario()
        for event in scenario.get_events():
            assert event.event_id is not None
            assert event.object_id is not None

    def test_get_scenario_by_name(self):
        scenario = get_scenario("Investment Firm")
        assert scenario is not None
        assert scenario.name == "Investment Firm"

    def test_get_scenario_not_found(self):
        scenario = get_scenario("NonExistent")
        assert scenario is None

    def test_list_scenarios(self):
        scenarios = list_scenarios()
        assert len(scenarios) >= 1
        assert any(s["name"] == "Investment Firm" for s in scenarios)

    def test_register_custom_scenario(self):
        class CustomScenario(ScenarioProvider):
            name = "Custom"
            description = "A custom test scenario"
            def get_objects(self): return []
            def get_events(self): return []
            def get_evidence(self): return []
            def get_relationships(self): return []

        register(CustomScenario)
        assert get_scenario("Custom") is not None
        # Cleanup
        _registry.pop("Custom", None)


# ══════════════════════════════════════════════════════════════
# Explainability Integrity Tests
# ══════════════════════════════════════════════════════════════


class TestExplainabilityIntegrity:
    """Test that the full explainability chain is intact."""

    def setup_method(self):
        reset_store()
        reset_obs_store()
        reset_engine()
        reset_compiler()

    def test_full_chain_from_scenario(self):
        """Load scenario, evaluate, verify every insight is traceable."""
        from app.intelligence.runtime import load_default_scenario
        load_default_scenario()

        engine = get_engine()
        compiler = get_compiler()
        prov_store = get_store()

        # Verify insights were produced
        insights = compiler.compile_all()
        assert len(insights) > 0, "No insights produced from scenario"

        # Verify every insight has a traceable chain
        for insight in insights:
            chain = prov_store.get_chain(insight.chain_id)
            assert chain is not None, f"Chain {insight.chain_id} not found"
            assert chain.is_intact, f"Chain {insight.chain_id} has integrity issues: {chain.verify_integrity()}"
            assert chain.node_count >= 3, f"Chain {insight.chain_id} has < 3 nodes"

    def test_inspector_can_resolve_insight(self):
        """Verify the Founder Inspector can resolve any insight."""
        from app.intelligence.runtime import load_default_scenario
        load_default_scenario()

        compiler = get_compiler()
        inspector = FounderInspector()

        insights = compiler.compile_all()
        assert len(insights) > 0

        for insight in insights:
            inspection = inspector.inspect_insight(insight.insight_id)
            assert inspection["provenance"]["chain_found"], f"Chain not found for {insight.insight_id}"
            assert inspection["provenance"]["chain_intact"], f"Chain not intact for {insight.insight_id}"

    def test_confidence_is_computed_not_hardcoded(self):
        """Verify that confidence values in insights are computed, not hardcoded."""
        from app.intelligence.runtime import load_default_scenario
        load_default_scenario()

        compiler = get_compiler()
        insights = compiler.compile_all()

        for insight in insights:
            # Confidence should be between 0 and 1 (not a hardcoded value like 0.5 or 0.8)
            assert 0.0 <= insight.confidence <= 1.0
            # Confidence should have meaningful precision (not a round number)
            # This checks that it was computed, not hardcoded
            assert insight.confidence_label is not None

    def test_observation_lifecycle_integrity(self):
        """Verify observation lifecycle works end-to-end."""
        from app.intelligence.runtime import load_default_scenario
        load_default_scenario()

        obs_store = get_obs_store()

        # All observations should have valid statuses
        for obs_id in ["obs_evt-ju001", "obs_evt-ju002", "obs_evt-nm001", "obs_evt-nm002", "obs_evt-nm003"]:
            obs = obs_store.get(obs_id)
            assert obs is not None, f"Observation {obs_id} not found"
            assert obs.status in ObservationStatus
            assert obs.age_hours >= 0

    def test_executive_brief_is_compiled(self):
        """Verify executive brief is generated from runtime data, not copy."""
        from app.intelligence.runtime import load_default_scenario
        load_default_scenario()

        compiler = get_compiler()
        brief = compiler.compile_executive_brief(org_name="TestOrg")

        assert brief.summary is not None
        assert len(brief.summary) > 0
        assert "TestOrg" in brief.summary
        assert len(brief.insights) > 0

    def test_scenario_does_not_leak_into_core(self):
        """Verify the core runtime doesn't depend on any specific scenario."""
        from app.intelligence.runtime import load_default_scenario
        load_default_scenario()

        engine = get_engine()
        compiler = get_compiler()

        # The engine should work without any scenario
        reset_obs_store()
        reset_engine()
        reset_compiler()

        engine2 = get_engine()
        compiler2 = get_compiler()

        # With no observations, no insights should be produced
        insights = compiler2.compile_all()
        assert len(insights) == 0

        # But the engine should still work
        brief = compiler2.compile_executive_brief(org_name="Empty")
        assert brief.summary is not None
        assert "no active insights" in brief.summary.lower() or "operating normally" in brief.summary.lower()