"""
Tests for the SHUNYA Reasoning Engine.

Covers all 7 reasoning types, the IntelligenceEngine interface, rule/pattern
management, and edge cases.
"""

from __future__ import annotations

import pytest

from core.intelligence.reasoning import (
    Analogy,
    CausalChain,
    CausalLink,
    Conclusion,
    DeductiveRule,
    DeductiveRuleSet,
    EngineInput,
    EngineOutput,
    EscalationResult,
    InductivePattern,
    ReasoningEngine,
    ReasoningType,
    get_reasoning_engine,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def engine() -> ReasoningEngine:
    return ReasoningEngine()


@pytest.fixture
def seeded_engine() -> ReasoningEngine:
    """Engine pre-loaded with rules, patterns, and chains."""
    eng = ReasoningEngine()

    # Deductive rules
    eng.add_rule(
        DeductiveRule(
            premises=("all_humans_are_mortal", "socrates_is_human"),
            conclusion="socrates_is_mortal",
            label="Socrates mortality",
            confidence=1.0,
        )
    )
    eng.add_rule(
        DeductiveRule(
            premises=("all_birds_fly", "tweety_is_a_bird"),
            conclusion="tweety_can_fly",
            label="Tweety flight",
            confidence=0.95,
        )
    )
    eng.add_rule_set(
        DeductiveRuleSet(
            name="weather",
            rules=(
                DeductiveRule(
                    premises=("cloudy", "low_pressure"),
                    conclusion="rain_expected",
                    label="Rain rule",
                    confidence=0.85,
                ),
                DeductiveRule(
                    premises=("high_pressure", "clear_sky"),
                    conclusion="sunny_weather",
                    label="Sunny rule",
                    confidence=0.90,
                ),
            ),
        )
    )

    # Inductive patterns
    eng.add_pattern(
        InductivePattern(
            name="high_engagement",
            observations=("click", "share", "comment"),
            conclusion="user_highly_engaged",
            support_count=45,
            total_count=50,
        )
    )
    eng.add_pattern(
        InductivePattern(
            name="low_engagement",
            observations=("bounce", "no_action"),
            conclusion="user_not_engaged",
            support_count=10,
            total_count=50,
        )
    )

    # Causal chains
    eng.add_causal_chain(
        CausalChain(
            links=(
                CausalLink(
                    cause="server_overload",
                    effect="slow_response",
                    evidence_id="ev-001",
                    strength=0.9,
                ),
                CausalLink(
                    cause="slow_response",
                    effect="user_timeout",
                    evidence_id="ev-002",
                    strength=0.85,
                ),
                CausalLink(
                    cause="user_timeout",
                    effect="abandoned_session",
                    evidence_id="ev-003",
                    strength=0.95,
                ),
            ),
        )
    )

    return eng


# ══════════════════════════════════════════════════════════════════════════════
# Deductive Reasoning Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestDeductiveReasoning:
    def test_basic_deduction(self, seeded_engine: ReasoningEngine) -> None:
        """Deduction fires when all premises are satisfied."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "deductive",
                    "facts": ["all_humans_are_mortal", "socrates_is_human"],
                },
                trace_id="trace-ded-01",
            )
        )
        assert output.output_type == "conclusion.deductive"
        assert output.deterministic is True
        assert output.escalation_used is False
        assert "socrates_is_mortal" in output.payload["conclusion"]
        assert output.confidence > 0.7

    def test_partial_facts_no_deduction(
        self, seeded_engine: ReasoningEngine
    ) -> None:
        """Deduction with only some facts yields no conclusion."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "deductive",
                    "facts": ["all_humans_are_mortal"],
                },
                trace_id="trace-ded-02",
            )
        )
        assert output.confidence == 0.0
        assert "No deductive rules matched" in output.payload["conclusion"]

    def test_no_rules_no_deduction(self, engine: ReasoningEngine) -> None:
        """Engine with no rules returns no conclusion."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "deductive",
                    "facts": ["anything"],
                },
            )
        )
        assert output.confidence == 0.0

    def test_rule_set_registration(self, seeded_engine: ReasoningEngine) -> None:
        """Rule sets are registered and fire correctly."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "deductive",
                    "facts": ["cloudy", "low_pressure"],
                },
                trace_id="trace-ded-03",
            )
        )
        assert "rain_expected" in output.payload["conclusion"]

    def test_multiple_rules_fire(self, seeded_engine: ReasoningEngine) -> None:
        """Multiple rules can fire simultaneously with different facts."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "deductive",
                    "facts": [
                        "all_humans_are_mortal",
                        "socrates_is_human",
                        "high_pressure",
                        "clear_sky",
                    ],
                },
            )
        )
        assert "socrates_is_mortal" in output.payload["conclusion"]
        assert "sunny_weather" in output.payload["conclusion"]

    def test_rule_retrieval(self, seeded_engine: ReasoningEngine) -> None:
        """Registered rules are retrievable by ID."""
        rules = seeded_engine.get_rules()
        assert len(rules) == 4  # 2 direct + 2 from rule set
        rule = seeded_engine.get_rule(rules[0].rule_id)
        assert rule is not None
        assert rule.label is not None


# ══════════════════════════════════════════════════════════════════════════════
# Inductive Reasoning Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestInductiveReasoning:
    def test_best_pattern_match(self, seeded_engine: ReasoningEngine) -> None:
        """Induction finds the best-matching pattern."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "inductive",
                    "facts": ["click", "share", "comment", "like"],
                },
                trace_id="trace-ind-01",
            )
        )
        assert output.output_type == "conclusion.inductive"
        assert output.deterministic is True
        assert "highly_engaged" in output.payload["conclusion"]
        assert output.confidence > 0.0

    def test_no_match_low_confidence(
        self, seeded_engine: ReasoningEngine
    ) -> None:
        """Induction with no pattern match returns zero confidence."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "inductive",
                    "facts": ["unknown_observation_xyz"],
                },
            )
        )
        assert output.confidence == 0.0
        assert "No matching inductive patterns" in output.payload["conclusion"]

    def test_empty_patterns(self, engine: ReasoningEngine) -> None:
        """Engine with no patterns returns no match."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "inductive",
                    "facts": ["anything"],
                },
            )
        )
        assert output.confidence == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Abductive Reasoning Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestAbductiveReasoning:
    def test_abductive_fallback(self, seeded_engine: ReasoningEngine) -> None:
        """Abduction uses deterministic fallback first."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "abductive",
                    "facts": ["socrates_is_mortal", "all_humans_are_mortal"],
                },
                trace_id="trace-abd-01",
                # Low threshold so deterministic fallback (confidence ~0.5)
                # is accepted without escalation
                confidence_threshold=0.30,
            )
        )
        # Should find the reverse rule explanation
        assert output.output_type == "conclusion.abductive"
        assert "Best explanation" in output.payload["conclusion"]

    def test_abductive_escalation(self, engine: ReasoningEngine) -> None:
        """Abduction escalates when no deterministic explanation found."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "abductive",
                    "facts": ["unusual_symptom_observed"],
                },
                trace_id="trace-abd-02",
                confidence_threshold=0.30,
            )
        )
        # With no rules, fallback yields 0.0 confidence, which is below 0.30
        # So escalation is triggered
        # Actually wait: 0.0 < 0.30 means escalation should trigger
        assert output.escalation_used is True
        assert output.deterministic is False

    def test_abductive_high_confidence_no_escalation(
        self, seeded_engine: ReasoningEngine
    ) -> None:
        """Abduction with strong deterministic match avoids escalation."""
        # Add a rule where conclusion matches evidence
        seeded_engine.add_rule(
            DeductiveRule(
                premises=("observed_effect", "known_pattern"),
                conclusion="observed_effect",
                label="Self-match rule",
                confidence=1.0,
            )
        )
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "abductive",
                    "facts": ["observed_effect", "known_pattern"],
                },
                confidence_threshold=0.10,
            )
        )
        assert output.escalation_used is False


# ══════════════════════════════════════════════════════════════════════════════
# Analogical Reasoning Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestAnalogicalReasoning:
    def test_no_analogies_no_match(self, engine: ReasoningEngine) -> None:
        """Analogy with no registered analogies returns no match."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "analogical",
                    "facts": ["feature_a", "feature_b"],
                },
            )
        )
        assert output.confidence == 0.0
        assert "No matching analogies" in output.payload["conclusion"]

    def test_analogy_with_analogies(
        self, engine: ReasoningEngine
    ) -> None:
        """Analogy matches when features overlap with stored analogies."""
        # Add analogies directly to the internal store
        analogy = Analogy(
            source_id="src-1",
            target_id="tgt-1",
            source_description="Previous project Alpha",
            target_description="Current project Beta",
            shared_features=("agile", "python", "microservices"),
            similarity_score=0.85,
        )
        engine._analogies[analogy.analogy_id] = analogy

        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "analogical",
                    "facts": ["agile", "python", "microservices", "docker"],
                },
                trace_id="trace-ana-01",
            )
        )
        assert output.output_type == "conclusion.analogical"
        assert output.confidence > 0.0
        assert "Previous project Alpha" in output.payload["conclusion"]

    def test_partial_overlap_still_matches(
        self, engine: ReasoningEngine
    ) -> None:
        """Analogy with partial feature overlap still produces a match."""
        analogy = Analogy(
            source_id="src-2",
            target_id="tgt-2",
            source_description="Past migration",
            target_description="Current migration",
            shared_features=("database", "migration", "etl"),
            similarity_score=0.90,
        )
        engine._analogies[analogy.analogy_id] = analogy

        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "analogical",
                    "facts": ["database", "etl"],
                },
            )
        )
        assert output.confidence > 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Causal Reasoning Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCausalReasoning:
    def test_causal_chain_match(
        self, seeded_engine: ReasoningEngine
    ) -> None:
        """Causal reasoning finds chain matching evidence IDs."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "causal",
                    "facts": ["ev-002"],
                },
                trace_id="trace-cau-01",
            )
        )
        assert output.output_type == "conclusion.causal"
        assert output.deterministic is True
        assert output.confidence > 0.0
        assert "Causal chain found" in output.payload["conclusion"]

    def test_causal_no_match(self, seeded_engine: ReasoningEngine) -> None:
        """Causal reasoning with unmatched evidence IDs returns no match."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "causal",
                    "facts": ["nonexistent_evidence"],
                },
            )
        )
        assert output.confidence == 0.0

    def test_causal_chain_matches_any_link(
        self, seeded_engine: ReasoningEngine
    ) -> None:
        """Causal reasoning matches when any link in the chain matches."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "causal",
                    "facts": ["ev-003"],
                },
            )
        )
        assert output.confidence > 0.0
        assert "server_overload" in output.payload["conclusion"]


# ══════════════════════════════════════════════════════════════════════════════
# Counterfactual Reasoning Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCounterfactualReasoning:
    def test_counterfactual_always_escalates(
        self, engine: ReasoningEngine
    ) -> None:
        """Counterfactual reasoning always uses AI escalation."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "counterfactual",
                    "facts": ["deployed_buggy_code"],
                },
                trace_id="trace-cft-01",
            )
        )
        assert output.output_type == "conclusion.counterfactual"
        assert output.deterministic is False
        assert output.escalation_used is True
        assert output.payload["conclusion"]


# ══════════════════════════════════════════════════════════════════════════════
# Probabilistic Reasoning Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestProbabilisticReasoning:
    def test_high_consistency_high_confidence(
        self, engine: ReasoningEngine
    ) -> None:
        """Consistent inputs produce high aggregate confidence."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "probabilistic",
                    "facts": [
                        "source_a:0.9",
                        "source_b:0.85",
                        "source_c:0.95",
                    ],
                },
                trace_id="trace-prob-01",
            )
        )
        assert output.output_type == "conclusion.probabilistic"
        assert output.deterministic is True
        assert output.confidence > 0.7

    def test_high_variance_lower_confidence(
        self, engine: ReasoningEngine
    ) -> None:
        """High-variance inputs produce lower aggregate confidence."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "probabilistic",
                    "facts": ["source_a:0.9", "source_b:0.1"],
                },
            )
        )
        assert output.confidence < 0.6  # penalised by variance

    def test_single_input(self, engine: ReasoningEngine) -> None:
        """Single input passes through cleanly."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "probabilistic",
                    "facts": ["only_source:0.75"],
                },
            )
        )
        assert output.confidence == 0.75

    def test_malformed_inputs_skipped(
        self, engine: ReasoningEngine
    ) -> None:
        """Malformed confidence strings are skipped gracefully."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "probabilistic",
                    "facts": [
                        "good:0.8",
                        "no_value_here",
                        "also_bad",
                        "another:0.6",
                    ],
                },
            )
        )
        assert output.confidence > 0.0
        assert "2 inputs" in output.payload["conclusion"] or "aggregated" in output.payload["conclusion"]

    def test_empty_inputs(self, engine: ReasoningEngine) -> None:
        """Empty input list returns zero confidence."""
        output = engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "probabilistic",
                    "facts": [],
                },
            )
        )
        assert output.confidence == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Engine Interface Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEngineInterface:
    def test_get_capabilities(self, engine: ReasoningEngine) -> None:
        """Engine exposes all 7 reasoning capabilities."""
        caps = engine.get_capabilities()
        assert len(caps) == 7
        assert "reasoning.deductive" in caps
        assert "reasoning.inductive" in caps
        assert "reasoning.abductive" in caps
        assert "reasoning.analogical" in caps
        assert "reasoning.causal" in caps
        assert "reasoning.counterfactual" in caps
        assert "reasoning.probabilistic" in caps

    def test_health_check(self, engine: ReasoningEngine) -> None:
        """Health check returns engine identity and status."""
        health = engine.health_check()
        assert health["engine_id"] == "reasoning_engine"
        assert health["engine_type"] == "reasoning"
        assert health["status"] == "healthy"

    def test_health_check_with_data(
        self, seeded_engine: ReasoningEngine
    ) -> None:
        """Health check reflects registered rules and patterns."""
        health = seeded_engine.health_check()
        assert health["rules_count"] == 4
        assert health["patterns_count"] == 2

    def test_escalate_method(self, engine: ReasoningEngine) -> None:
        """Escalate returns structured EscalationResult."""
        result = engine.escalate(
            EngineInput(
                input_type="query",
                payload={"reasoning_type": "abductive", "facts": ["test"]},
            )
        )
        assert isinstance(result, EscalationResult)
        assert result.confidence >= 0.0
        assert result.provider == "placeholder_llm"

    def test_unknown_reasoning_type(self, engine: ReasoningEngine) -> None:
        """Unknown reasoning type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown reasoning type"):
            engine.process(
                EngineInput(
                    input_type="query",
                    payload={"reasoning_type": "nonexistent", "facts": []},
                )
            )

    def test_conclusion_storage_and_retrieval(
        self, seeded_engine: ReasoningEngine
    ) -> None:
        """Conclusions are stored and retrievable by ID and trace."""
        output = seeded_engine.process(
            EngineInput(
                input_type="query",
                payload={
                    "reasoning_type": "deductive",
                    "facts": ["all_humans_are_mortal", "socrates_is_human"],
                },
                trace_id="trace-store-01",
            )
        )
        cid = output.payload["conclusion_id"]
        conclusion = seeded_engine.get_conclusion(cid)
        assert conclusion is not None
        assert conclusion.statement == output.payload["conclusion"]

        trace_results = seeded_engine.get_conclusions_by_trace("trace-store-01")
        assert len(trace_results) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Model Validation Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestModelValidation:
    def test_empty_rule_premises_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least one premise"):
            DeductiveRule(premises=(), conclusion="something")

    def test_empty_rule_conclusion_rejected(self) -> None:
        with pytest.raises(ValueError, match="must have a conclusion"):
            DeductiveRule(premises=("p",), conclusion="")

    def test_invalid_pattern_counts(self) -> None:
        with pytest.raises(ValueError, match="cannot exceed"):
            InductivePattern(
                name="bad",
                observations=("a",),
                conclusion="c",
                support_count=10,
                total_count=5,
            )

    def test_invalid_source_reliability(self) -> None:
        with pytest.raises(ValueError, match="strength must be in"):
            CausalLink(
                cause="c", effect="e", evidence_id="ev-1", strength=1.5
            )

    def test_empty_causal_chain(self) -> None:
        """Empty causal chain has zero strength."""
        chain = CausalChain(links=())
        assert chain.overall_strength == 0.0
        assert chain.confidence == 0.0

    def test_causal_confidence_computation(self) -> None:
        """Causal chain confidence is geo-mean of link strengths."""
        chain = CausalChain(
            links=(
                CausalLink(cause="a", effect="b", evidence_id="e1", strength=0.9),
                CausalLink(cause="b", effect="c", evidence_id="e2", strength=0.8),
            ),
        )
        expected = (0.9 * 0.8) ** 0.5
        assert chain.overall_strength == pytest.approx(expected, rel=1e-5)
        assert chain.confidence == pytest.approx(expected, rel=1e-5)

    def test_analogy_auto_confidence(self) -> None:
        """Analogy confidence auto-derives from similarity_score."""
        a = Analogy(
            source_id="s",
            target_id="t",
            source_description="src",
            target_description="tgt",
            shared_features=("a", "b"),
            similarity_score=0.75,
        )
        assert a.confidence == 0.75

    def test_inductive_pattern_auto_confidence(self) -> None:
        """InductivePattern auto-computes confidence from ratio."""
        p = InductivePattern(
            name="test",
            observations=("a", "b"),
            conclusion="c",
            support_count=40,
            total_count=50,
        )
        assert p.confidence == 0.8  # 40/50


# ══════════════════════════════════════════════════════════════════════════════
# Singleton Accessor
# ══════════════════════════════════════════════════════════════════════════════


class TestSingleton:
    def test_get_reasoning_engine(self) -> None:
        """Singleton accessor returns same instance."""
        e1 = get_reasoning_engine()
        e2 = get_reasoning_engine()
        assert e1 is e2

    def test_import_from_init(self) -> None:
        """Engine is importable from core.intelligence.reasoning."""
        from core.intelligence.reasoning import (
            ReasoningEngine as ImportedEngine,
        )

        assert ImportedEngine is ReasoningEngine