"""
SHUNYA Reasoning Engine — In-Memory Implementation

The Reasoning Engine is the inference core of the Intelligence Runtime.
It derives conclusions from evidence, observations, and context using 7
canonical reasoning types:

  Type             | Deterministic | Method
  ---------------- | ------------- | ------
  Deductive        | ✓ Always      | Rule-based inference engine
  Inductive        | ✓ Pattern     | Statistical pattern matching
  Abductive        | ✗ AI-assisted | Best explanation from LLM
  Analogical       | ✓ Rule-based  | Similarity scoring
  Causal           | ✓ Rule-based  | Evidence chain traversal
  Counterfactual   | ✗ AI-assisted | LLM simulation
  Probabilistic    | ✓ Formula     | Confidence-weighted aggregation

Architecture rules:
  - Determinstic computations run locally and return immediately.
  - AI-assisted types (abductive, counterfactual) trigger escalate() when
    the confidence threshold is not met.
  - The engine never imports from app/ (strangler-fig isolation).
  - Every reasoning chain is traceable via trace_id.

References:
  - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §7 (Reasoning Engine)
  - docs/canon/07_ai_canon.md §8 (Reasoner Engine)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.intelligence.reasoning.models import (
    Analogy,
    CausalChain,
    Conclusion,
    CounterfactualScenario,
    DeductiveRule,
    DeductiveRuleSet,
    EngineInput,
    EngineOutput,
    EscalationResult,
    InductivePattern,
    ReasoningType,
)

logger = logging.getLogger(__name__)


# ── Confidence constants ──────────────────────────────────────────────────────


_DEDUCTIVE_BASE_CONFIDENCE: float = 0.95
"""Base confidence for deductive reasoning when rules are satisfied."""

_INDUCTIVE_BASE_CONFIDENCE: float = 0.80
"""Base confidence for inductive reasoning before adjustment."""

_ANALOGICAL_BASE_CONFIDENCE: float = 0.75
"""Base confidence for analogical reasoning."""

_CAUSAL_BASE_CONFIDENCE: float = 0.80
"""Base confidence for causal reasoning."""

_PROBABILISTIC_BASE_CONFIDENCE: float = 0.70
"""Base confidence for probabilistic aggregation."""

_ESCLATION_CONFIDENCE_FLOOR: float = 0.30
"""Minimum confidence returned by escalate() if the AI provider cannot be reached."""


# ── ReasoningEngine ───────────────────────────────────────────────────────────


class ReasoningEngine:
    """In-memory Reasoning Engine supporting 7 reasoning types.

    The engine implements the ``IntelligenceEngine`` interface (``process``,
    ``escalate``, ``get_capabilities``, ``health_check``) as specified in
    the Intelligence Runtime Canon §3.

    **Deterministic reasoning types** (Deductive, Inductive, Analogical,
    Causal, Probabilistic) are computed entirely in-memory with no external
    dependencies.

    **AI-assisted types** (Abductive, Counterfactual) rely on ``escalate()``
    which serves as a bridge to an external inference provider.  In this
    implementation, ``escalate()`` returns a structured placeholder result
    — a production system would route to an LLM provider.

    Usage::

        engine = ReasoningEngine()

        # Register rules for deductive reasoning
        engine.add_rule(DeductiveRule(
            premises=("all_humans_are_mortal", "socrates_is_human"),
            conclusion="socrates_is_mortal",
            label="Socrates mortality",
        ))

        # Run deductive reasoning
        output = engine.process(EngineInput(
            input_type="query",
            payload={"reasoning_type": "deductive", "facts": ["socrates_is_human"]},
            trace_id="trace-001",
        ))
    """

    # ── Engine identity ───────────────────────────────────────────────────────

    engine_id: str = "reasoning_engine"
    """Unique identifier for this engine instance."""

    engine_type: str = "reasoning"
    """Engine type per Intelligence Runtime classification."""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def __init__(self) -> None:
        # Deductive rule store: rule_id -> DeductiveRule
        self._rules: dict[str, DeductiveRule] = {}

        # Rule indexes: predicate -> set of rule_ids
        self._rule_premise_index: dict[str, set[str]] = {}

        # Inductive patterns: pattern_id -> InductivePattern
        self._patterns: dict[str, InductivePattern] = {}

        # Known analogies for similarity scoring
        self._analogies: dict[str, Analogy] = {}

        # Causal chains
        self._causal_chains: dict[str, CausalChain] = {}

        # Counterfactual scenarios
        self._counterfactuals: dict[str, CounterfactualScenario] = {}

        # Stream of conclusions
        self._conclusions: dict[str, Conclusion] = {}

    # ══════════════════════════════════════════════════════════════════════════
    # IntelligenceEngine Interface
    # ══════════════════════════════════════════════════════════════════════════

    def process(self, inp: EngineInput) -> EngineOutput:
        """Process an input through the reasoning pipeline.

        The processing flow follows the Intelligence Runtime Canon (§7.3):

            1. Determine the requested reasoning type from the payload.
            2. Compute deterministically (type-specific logic).
            3. If confidence >= threshold, return the result.
            4. If confidence < threshold, call ``escalate()``.
            5. Combine results and return.

        Args:
            inp: The ``EngineInput`` containing the query, context, and
                reasoning parameters.

        Returns:
            An ``EngineOutput`` with the conclusion or escalation result.

        Raises:
            ValueError: If the requested reasoning type is unknown.
        """
        start = time.perf_counter()
        reasoning_type_str = inp.payload.get("reasoning_type", "")
        facts: list[str] = inp.payload.get("facts", [])
        trace_id = inp.trace_id or ""

        try:
            reasoning_type = ReasoningType(reasoning_type_str)
        except ValueError:
            raise ValueError(
                f"Unknown reasoning type {reasoning_type_str!r}. "
                f"Valid types: {[t.value for t in ReasoningType]}"
            )

        escalation_used = False
        deterministic = True

        # ── Route to type-specific handler ────────────────────────────────

        if reasoning_type == ReasoningType.DEDUCTIVE:
            conclusion = self._deductive_reason(facts, trace_id)
            confidence = conclusion.confidence

        elif reasoning_type == ReasoningType.INDUCTIVE:
            conclusion = self._inductive_reason(facts, trace_id)
            confidence = conclusion.confidence

        elif reasoning_type == ReasoningType.ABDUCTIVE:
            # Deterministic fallback first, then escalate
            conclusion = self._abductive_fallback(facts, trace_id)
            confidence = conclusion.confidence
            if confidence < inp.confidence_threshold:
                escalation = self._escalate_abductive(inp)
                escalation_used = True
                deterministic = False
                conclusion = Conclusion(
                    reasoning_type=ReasoningType.ABDUCTIVE,
                    statement=escalation.result.get(
                        "explanation", conclusion.statement
                    ),
                    confidence=escalation.confidence,
                    confidence_factors={"provider": 1.0},
                    trace_id=trace_id,
                    metadata={"escalation_provider": escalation.provider},
                )
                confidence = escalation.confidence

        elif reasoning_type == ReasoningType.ANALOGICAL:
            conclusion = self._analogical_reason(facts, trace_id)
            confidence = conclusion.confidence

        elif reasoning_type == ReasoningType.CAUSAL:
            conclusion = self._causal_reason(facts, trace_id)
            confidence = conclusion.confidence

        elif reasoning_type == ReasoningType.COUNTERFACTUAL:
            # Always escalate for counterfactual reasoning
            escalation = self._escalate_counterfactual(inp)
            escalation_used = True
            deterministic = False
            conclusion = Conclusion(
                reasoning_type=ReasoningType.COUNTERFACTUAL,
                statement=escalation.result.get("scenario", ""),
                confidence=escalation.confidence,
                confidence_factors={"provider": 1.0},
                trace_id=trace_id,
                metadata={"escalation_provider": escalation.provider},
            )
            confidence = escalation.confidence

        elif reasoning_type == ReasoningType.PROBABILISTIC:
            conclusion = self._probabilistic_reason(facts, trace_id)
            confidence = conclusion.confidence

        else:
            raise ValueError(
                f"Unhandled reasoning type: {reasoning_type}"
            )

        # Store conclusion
        self._conclusions[conclusion.conclusion_id] = conclusion

        elapsed = (time.perf_counter() - start) * 1000.0

        return EngineOutput(
            output_type=f"conclusion.{reasoning_type.value}",
            payload={
                "conclusion": conclusion.statement,
                "conclusion_id": conclusion.conclusion_id,
                "evidence_chain": list(conclusion.evidence_chain),
                "alternatives": list(conclusion.alternatives),
                "reasoning_type": reasoning_type.value,
            },
            confidence=confidence,
            confidence_factors=conclusion.confidence_factors,
            deterministic=deterministic,
            trace_id=trace_id,
            escalation_used=escalation_used,
            processing_time_ms=round(elapsed, 2),
        )

    def escalate(self, inp: EngineInput) -> EscalationResult:
        """Bridge to external AI inference.

        Called when deterministic computation yields confidence below the
        engine's threshold (0.70 by default) for AI-assisted reasoning types.

        In this implementation, ``escalate()`` returns a structured
        placeholder.  Production deployments should replace this with an
        actual LLM inference call.

        Args:
            inp: The original ``EngineInput`` that triggered escalation.

        Returns:
            An ``EscalationResult`` with the AI-provided result.
        """
        reasoning_type = inp.payload.get("reasoning_type", "")
        if reasoning_type == ReasoningType.ABDUCTIVE.value:
            return self._escalate_abductive(inp)
        elif reasoning_type == ReasoningType.COUNTERFACTUAL.value:
            return self._escalate_counterfactual(inp)
        else:
            # Generic escalation fallback
            return EscalationResult(
                result={"note": "AI-assisted reasoning requested"},
                confidence=_ESCLATION_CONFIDENCE_FLOOR,
                provider="placeholder",
                processing_time_ms=0.0,
            )

    def get_capabilities(self) -> list[str]:
        """Return list of capability strings for this engine.

        Returns:
            List of canonical capability identifiers.
        """
        return [
            "reasoning.deductive",
            "reasoning.inductive",
            "reasoning.abductive",
            "reasoning.analogical",
            "reasoning.causal",
            "reasoning.counterfactual",
            "reasoning.probabilistic",
        ]

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            A dictionary with engine identity, rule/pattern counts, and
            overall status.
        """
        return {
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "status": "healthy",
            "rules_count": len(self._rules),
            "patterns_count": len(self._patterns),
            "analogies_count": len(self._analogies),
            "causal_chains_count": len(self._causal_chains),
            "counterfactuals_count": len(self._counterfactuals),
            "conclusions_count": len(self._conclusions),
        }

    # ══════════════════════════════════════════════════════════════════════════
    # Rule / Pattern Management
    # ══════════════════════════════════════════════════════════════════════════

    def add_rule(self, rule: DeductiveRule) -> str:
        """Register a deductive rule.

        Args:
            rule: The ``DeductiveRule`` to register.

        Returns:
            The rule's ID.
        """
        self._rules[rule.rule_id] = rule
        for premise in rule.premises:
            self._rule_premise_index.setdefault(premise, set()).add(rule.rule_id)
        logger.debug("Registered deductive rule %s: %s", rule.rule_id, rule.label)
        return rule.rule_id

    def add_rule_set(self, rule_set: DeductiveRuleSet) -> list[str]:
        """Register a named set of deductive rules.

        Args:
            rule_set: The ``DeductiveRuleSet`` to register.

        Returns:
            List of registered rule IDs.
        """
        return [self.add_rule(rule) for rule in rule_set.rules]

    def get_rule(self, rule_id: str) -> DeductiveRule | None:
        """Retrieve a deductive rule by ID.

        Args:
            rule_id: The rule's unique identifier.

        Returns:
            The ``DeductiveRule``, or ``None`` if not found.
        """
        return self._rules.get(rule_id)

    def add_pattern(self, pattern: InductivePattern) -> str:
        """Register an inductive pattern.

        Args:
            pattern: The ``InductivePattern`` to register.

        Returns:
            The pattern's ID.
        """
        self._patterns[pattern.pattern_id] = pattern
        logger.debug("Registered inductive pattern %s: %s", pattern.pattern_id, pattern.name)
        return pattern.pattern_id

    def get_pattern(self, pattern_id: str) -> InductivePattern | None:
        """Retrieve an inductive pattern by ID.

        Args:
            pattern_id: The pattern's unique identifier.

        Returns:
            The ``InductivePattern``, or ``None`` if not found.
        """
        return self._patterns.get(pattern_id)

    def add_causal_chain(self, chain: CausalChain) -> str:
        """Register a causal chain.

        Args:
            chain: The ``CausalChain`` to register.

        Returns:
            The chain's ID.
        """
        self._causal_chains[chain.chain_id] = chain
        logger.debug(
            "Registered causal chain %s with %d links",
            chain.chain_id,
            len(chain.links),
        )
        return chain.chain_id

    def get_causal_chain(self, chain_id: str) -> CausalChain | None:
        """Retrieve a causal chain by ID.

        Args:
            chain_id: The chain's unique identifier.

        Returns:
            The ``CausalChain``, or ``None`` if not found.
        """
        return self._causal_chains.get(chain_id)

    # ══════════════════════════════════════════════════════════════════════════
    # Reasoning Type Implementations
    # ══════════════════════════════════════════════════════════════════════════

    # ── 1. Deductive (§7.2) ────────────────────────────────────────────────

    def _deductive_reason(
        self, facts: list[str], trace_id: str
    ) -> Conclusion:
        """Apply deductive rules to a set of known facts.

        Iterates over all registered rules.  If every premise of a rule is
        present in the ``facts`` list, the rule fires and its conclusion is
        emitted.

        Args:
            facts: List of known fact strings.
            trace_id: Correlation ID for traceability.

        Returns:
            A ``Conclusion`` with the deductive result.
        """
        fact_set = set(facts)
        matched_conclusions: list[str] = []
        matched_rule_ids: list[str] = []
        total_rules = len(self._rules)
        matched_weight = 0.0

        for rule_id, rule in self._rules.items():
            if all(p in fact_set for p in rule.premises):
                matched_conclusions.append(rule.conclusion)
                matched_rule_ids.append(rule_id)
                matched_weight += rule.confidence

        if matched_conclusions:
            avg_confidence = matched_weight / len(matched_conclusions)
            # Scale from base confidence
            confidence = (
                _DEDUCTIVE_BASE_CONFIDENCE * 0.5
                + avg_confidence * 0.5
            )
            confidence = min(1.0, confidence)
            conclusion_text = "; ".join(matched_conclusions)
        else:
            confidence = 0.0
            conclusion_text = "No deductive rules matched the given facts."

        return Conclusion(
            reasoning_type=ReasoningType.DEDUCTIVE,
            statement=conclusion_text,
            confidence=round(confidence, 6),
            confidence_factors={
                "matched_rules": len(matched_rule_ids),
                "total_rules": total_rules,
                "avg_rule_confidence": round(matched_weight / max(len(matched_conclusions), 1), 6),
                "base_confidence": _DEDUCTIVE_BASE_CONFIDENCE,
            },
            evidence_chain=tuple(matched_rule_ids),
            trace_id=trace_id,
        )

    # ── 2. Inductive (§7.2) ───────────────────────────────────────────────

    def _inductive_reason(
        self, observations: list[str], trace_id: str
    ) -> Conclusion:
        """Match observations against registered inductive patterns.

        For each pattern, computes an overlap score between the pattern's
        observed values and the provided observations.  Returns the best-
        matching pattern's conclusion.

        Args:
            observations: List of observed values.
            trace_id: Correlation ID for traceability.

        Returns:
            A ``Conclusion`` with the best inductive match.
        """
        obs_set = set(observations)
        best_pattern: InductivePattern | None = None
        best_score = 0.0

        for pattern in self._patterns.values():
            pattern_obs = set(pattern.observations)
            if not pattern_obs:
                continue
            overlap = len(obs_set & pattern_obs)
            score = overlap / len(pattern_obs) if pattern_obs else 0.0
            # Weight by pattern confidence
            weighted = score * pattern.confidence
            if weighted > best_score:
                best_score = weighted
                best_pattern = pattern

        if best_pattern is not None and best_score > 0.0:
            confidence = (
                _INDUCTIVE_BASE_CONFIDENCE * 0.3
                + best_score * 0.7
            )
            confidence = min(1.0, confidence)
            return Conclusion(
                reasoning_type=ReasoningType.INDUCTIVE,
                statement=(
                    f"Inductive match: {best_pattern.conclusion} "
                    f"(pattern: {best_pattern.name}, "
                    f"support: {best_pattern.support_count}/{best_pattern.total_count})"
                ),
                confidence=round(confidence, 6),
                confidence_factors={
                    "matched_pattern_id": best_pattern.pattern_id,
                    "pattern_confidence": best_pattern.confidence,
                    "overlap_score": round(best_score, 6),
                    "support_ratio": round(best_pattern.support_count / best_pattern.total_count, 6),
                },
                trace_id=trace_id,
            )
        else:
            return Conclusion(
                reasoning_type=ReasoningType.INDUCTIVE,
                statement="No matching inductive patterns found for the given observations.",
                confidence=0.0,
                confidence_factors={"patterns_checked": len(self._patterns)},
                trace_id=trace_id,
            )

    # ── 3. Abductive ─────────────────────────────────────────────────────

    def _abductive_fallback(
        self, evidence: list[str], trace_id: str
    ) -> Conclusion:
        """Deterministic fallback for abductive reasoning.

        Attempts to find the best explanation by cross-referencing evidence
        against known rules (reversed: conclusion → premises).  If no
        deterministic explanation is found, confidence will be low and
        escalation will be triggered.

        Args:
            evidence: List of observed evidence strings.
            trace_id: Correlation ID.

        Returns:
            A ``Conclusion`` — low confidence if no rule conclusively explains.
        """
        ev_set = set(evidence)
        candidates: list[tuple[str, float]] = []

        for rule in self._rules.values():
            if rule.conclusion in ev_set:
                # Reverse direction: if the conclusion is observed, the
                # premises are candidate explanations
                overlap = sum(1 for p in rule.premises if p in ev_set)
                if overlap > 0:
                    score = (overlap / len(rule.premises)) * rule.confidence
                    candidates.append((rule.conclusion, score))

        if candidates:
            best = max(candidates, key=lambda x: x[1])
            return Conclusion(
                reasoning_type=ReasoningType.ABDUCTIVE,
                statement=(
                    f"Best explanation: {best[0]} "
                    f"(confidence: {best[1]:.2f})"
                ),
                confidence=round(best[1], 6),
                confidence_factors={
                    "candidates": len(candidates),
                    "deterministic_fallback": 1.0,
                },
                trace_id=trace_id,
            )
        else:
            return Conclusion(
                reasoning_type=ReasoningType.ABDUCTIVE,
                statement="No deterministic explanation found. Escalating to AI.",
                confidence=0.0,
                confidence_factors={"deterministic_fallback": 0.0},
                trace_id=trace_id,
            )

    def _escalate_abductive(self, inp: EngineInput) -> EscalationResult:
        """Escalate abductive reasoning to an AI inference provider.

        In a production deployment, this would call an LLM API to generate
        the best explanation for the given evidence.  This placeholder
        implementation returns a structured mock result.

        Args:
            inp: The original engine input.

        Returns:
            An ``EscalationResult`` with AI-provided explanation.
        """
        evidence = inp.payload.get("facts", [])
        result = {
            "explanation": (
                f"AI-assisted abductive reasoning for evidence: {evidence}. "
                "Explanation: the most plausible cause given observed effects."
            ),
            "alternative_explanations": [],
            "confidence_note": "AI-generated, verify independently",
        }
        return EscalationResult(
            result=result,
            confidence=0.65,
            provider="placeholder_llm",
            processing_time_ms=0.0,
        )

    # ── 4. Analogical (§7.2) ─────────────────────────────────────────────

    def _analogical_reason(
        self, features: list[str], trace_id: str
    ) -> Conclusion:
        """Score similarity between target features and known analogies.

        Computes Jaccard similarity between the provided feature set and
        each registered analogy's shared features.

        Args:
            features: List of feature strings describing the target situation.
            trace_id: Correlation ID.

        Returns:
            A ``Conclusion`` with the best analogy match.
        """
        feat_set = set(features)
        best_analogy: Analogy | None = None
        best_score = 0.0

        for analogy in self._analogies.values():
            shared_set = set(analogy.shared_features)
            if not shared_set and not feat_set:
                continue
            union = feat_set | shared_set
            if not union:
                continue
            jaccard = len(feat_set & shared_set) / len(union)
            weighted = jaccard * analogy.similarity_score * _ANALOGICAL_BASE_CONFIDENCE
            if weighted > best_score:
                best_score = weighted
                best_analogy = analogy

        if best_analogy is not None and best_score > 0.0:
            confidence = min(1.0, best_score * 1.2)  # Slight boost for clarity
            return Conclusion(
                reasoning_type=ReasoningType.ANALOGICAL,
                statement=(
                    f"Analogical match: {best_analogy.source_description} "
                    f"→ {best_analogy.target_description} "
                    f"(similarity: {best_analogy.similarity_score:.2f})"
                ),
                confidence=round(confidence, 6),
                confidence_factors={
                    "matched_analogy_id": best_analogy.analogy_id,
                    "jaccard_similarity": round(
                        len(feat_set & set(best_analogy.shared_features))
                        / max(len(feat_set | set(best_analogy.shared_features)), 1),
                        6,
                    ),
                    "base_similarity": best_analogy.similarity_score,
                },
                trace_id=trace_id,
            )
        else:
            return Conclusion(
                reasoning_type=ReasoningType.ANALOGICAL,
                statement="No matching analogies found.",
                confidence=0.0,
                confidence_factors={"analogies_checked": len(self._analogies)},
                trace_id=trace_id,
            )

    # ── 5. Causal (§7.2) ─────────────────────────────────────────────────

    def _causal_reason(
        self, evidence_ids: list[str], trace_id: str
    ) -> Conclusion:
        """Traverse evidence chains to determine causal relationships.

        Uses the registered causal chains to determine cause-effect
        relationships for the given evidence IDs.

        Args:
            evidence_ids: List of evidence IDs to reason about.
            trace_id: Correlation ID.

        Returns:
            A ``Conclusion`` with causal chain results.
        """
        matched_chains: list[CausalChain] = []
        for chain in self._causal_chains.values():
            for link in chain.links:
                if link.evidence_id in evidence_ids:
                    matched_chains.append(chain)
                    break

        if matched_chains:
            best_chain = max(matched_chains, key=lambda c: c.overall_strength)
            cause_parts = []
            for link in best_chain.links:
                cause_parts.append(f"{link.cause} → {link.effect}")
            chain_text = "; ".join(cause_parts)
            confidence = _CAUSAL_BASE_CONFIDENCE * best_chain.overall_strength
            confidence = min(1.0, confidence)
            return Conclusion(
                reasoning_type=ReasoningType.CAUSAL,
                statement=(
                    f"Causal chain found: {chain_text} "
                    f"(strength: {best_chain.overall_strength:.3f})"
                ),
                confidence=round(confidence, 6),
                confidence_factors={
                    "matched_chains": len(matched_chains),
                    "overall_strength": best_chain.overall_strength,
                    "chain_length": len(best_chain.links),
                },
                evidence_chain=tuple(
                    link.evidence_id for link in best_chain.links
                ),
                trace_id=trace_id,
            )
        else:
            return Conclusion(
                reasoning_type=ReasoningType.CAUSAL,
                statement="No causal chains matched the given evidence IDs.",
                confidence=0.0,
                confidence_factors={"chains_checked": len(self._causal_chains)},
                trace_id=trace_id,
            )

    # ── 6. Counterfactual ─────────────────────────────────────────────────

    def _escalate_counterfactual(self, inp: EngineInput) -> EscalationResult:
        """Escalate counterfactual reasoning to an AI inference provider.

        Counterfactual reasoning is always AI-assisted per the canon.
        This placeholder returns a structured mock.

        Args:
            inp: The original engine input.

        Returns:
            An ``EscalationResult`` with the counterfactual scenario.
        """
        facts = inp.payload.get("facts", [])
        scenario_text = (
            f"AI-assisted counterfactual analysis for: {facts}. "
            "If the alternative had occurred, the predicted outcome "
            "would differ significantly based on the key factors identified."
        )
        result = {
            "scenario": scenario_text,
            "actual_event": " ".join(facts) if facts else "unknown",
            "alternative_event": "alternative course of action",
            "key_factors": ["timing", "resources", "context"],
            "confidence_note": "AI-generated simulation, verify independently",
        }
        return EscalationResult(
            result=result,
            confidence=0.60,
            provider="placeholder_llm",
            processing_time_ms=0.0,
        )

    # ── 7. Probabilistic (§7.2) ──────────────────────────────────────────

    def _probabilistic_reason(
        self, inputs: list[str], trace_id: str
    ) -> Conclusion:
        """Aggregate multiple lines of reasoning with confidence weighting.

        Expects *inputs* to be a list of strings formatted as
        ``"label:confidence"`` where confidence is a float in [0, 1].
        Computes a weighted aggregate confidence score.

        Args:
            inputs: List of ``"label:confidence"`` strings.
            trace_id: Correlation ID.

        Returns:
            A ``Conclusion`` with the aggregated probabilistic result.
        """
        if not inputs:
            return Conclusion(
                reasoning_type=ReasoningType.PROBABILISTIC,
                statement="No inputs provided for probabilistic aggregation.",
                confidence=0.0,
                confidence_factors={"inputs_count": 0},
                trace_id=trace_id,
            )

        parsed: list[tuple[str, float]] = []
        for item in inputs:
            if ":" in item:
                label, val_str = item.rsplit(":", 1)
                try:
                    val = float(val_str)
                    if 0.0 <= val <= 1.0:
                        parsed.append((label.strip(), val))
                except ValueError:
                    continue

        if not parsed:
            return Conclusion(
                reasoning_type=ReasoningType.PROBABILISTIC,
                statement="Could not parse any valid confidence inputs.",
                confidence=0.0,
                confidence_factors={"parsed_count": 0},
                trace_id=trace_id,
            )

        confidences = [c for _, c in parsed]
        n = len(confidences)
        mean_conf = sum(confidences) / n
        # Weight by 1 - variance (higher variance reduces confidence)
        variance = sum((c - mean_conf) ** 2 for c in confidences) / n
        consistency_weight = 1.0 - variance  # range [0, 1]
        aggregated = mean_conf * consistency_weight
        aggregated = max(0.0, min(1.0, aggregated))

        return Conclusion(
            reasoning_type=ReasoningType.PROBABILISTIC,
            statement=(
                f"Probabilistic aggregation of {n} inputs: "
                f"mean={mean_conf:.3f}, "
                f"variance={variance:.4f}, "
                f"aggregated={aggregated:.3f}"
            ),
            confidence=round(aggregated, 6),
            confidence_factors={
                "inputs_count": n,
                "mean_confidence": round(mean_conf, 6),
                "variance": round(variance, 6),
                "consistency_weight": round(consistency_weight, 6),
            },
            trace_id=trace_id,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Query Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def get_conclusion(self, conclusion_id: str) -> Conclusion | None:
        """Retrieve a stored conclusion by its ID.

        Args:
            conclusion_id: The conclusion's unique identifier.

        Returns:
            The ``Conclusion``, or ``None`` if not found.
        """
        return self._conclusions.get(conclusion_id)

    def get_conclusions_by_trace(self, trace_id: str) -> list[Conclusion]:
        """Retrieve all conclusions for a given trace.

        Args:
            trace_id: The correlation ID.

        Returns:
            List of matching ``Conclusion`` records.
        """
        return [
            c for c in self._conclusions.values() if c.trace_id == trace_id
        ]

    def get_rules(self) -> list[DeductiveRule]:
        """Return all registered deductive rules.

        Returns:
            List of all ``DeductiveRule`` instances.
        """
        return list(self._rules.values())

    def get_patterns(self) -> list[InductivePattern]:
        """Return all registered inductive patterns.

        Returns:
            List of all ``InductivePattern`` instances.
        """
        return list(self._patterns.values())


# ── Singleton accessor ────────────────────────────────────────────────────────


_reasoning_engine_instance: ReasoningEngine | None = None


def get_reasoning_engine() -> ReasoningEngine:
    """Return the singleton ReasoningEngine instance.

    Creates the instance on first call.  Use this for production scenarios
    where a single shared engine instance is desired.

    Returns:
        The shared ``ReasoningEngine`` instance.
    """
    global _reasoning_engine_instance
    if _reasoning_engine_instance is None:
        _reasoning_engine_instance = ReasoningEngine()
    return _reasoning_engine_instance