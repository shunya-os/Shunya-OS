"""
SHUNYA Reasoning Engine — Data Models

Defines the core data structures for the Reasoning Engine: reasoning types,
conclusions, evidence chains, confidence scoring, and the engine input/output
contract as specified in the Intelligence Runtime Canon.

All models are fully immutable after creation (frozen dataclasses) unless
otherwise noted.

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §3, §7
    - docs/canon/07_ai_canon.md §8 (Reasoner Engine)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.kernel.types import generate_uuid7

# ---------------------------------------------------------------------------
# Reasoning Types
# ---------------------------------------------------------------------------


class ReasoningType(Enum):
    """Canonical reasoning types supported by the Reasoning Engine.

    Each type corresponds to a distinct mode of inference, with its own
    determinism boundary as defined in the Intelligence Runtime Canon (§7.2).

    Values:
        DEDUCTIVE: Rule-based inference from general premises to specific
            conclusions. Always deterministic.
        INDUCTIVE: Statistical pattern matching from specific observations
            to general patterns. Always deterministic.
        ABDUCTIVE: Best explanation inference from observed evidence to
            likely causes. AI-assisted (LLM).
        ANALOGICAL: Similarity-based reasoning from known situations to
            novel ones. Always deterministic.
        CAUSAL: Cause-and-effect inference via evidence chain traversal.
            Always deterministic.
        COUNTERFACTUAL: "What if" simulation of alternative scenarios.
            AI-assisted (LLM).
        PROBABILISTIC: Confidence-weighted aggregation of multiple lines
            of reasoning. Always deterministic.
    """

    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CAUSAL = "causal"
    COUNTERFACTUAL = "counterfactual"
    PROBABILISTIC = "probabilistic"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Engine Input / Output Contract (§3.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EngineInput:
    """Standardised input to any Intelligence Engine.

    Attributes:
        input_type: Type of the input (e.g. "observation", "query",
            "action_result").
        payload: Structured input data.
        context: Optional assembled context from Context Assembly Engine.
        trace_id: Correlation ID for the full reasoning chain.
        confidence_threshold: Minimum confidence before escalation to AI
            is triggered (default: 0.70 per Reasoning threshold).
    """

    input_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] | None = None
    trace_id: str = ""
    confidence_threshold: float = 0.70


@dataclass(frozen=True)
class EngineOutput:
    """Standardised output from any Intelligence Engine.

    Attributes:
        output_type: Type of the output (e.g. "conclusion", "plan",
            "decision").
        payload: Structured output data.
        confidence: Computed confidence score [0, 1].
        confidence_factors: Breakdown of the confidence computation.
        deterministic: True if computed locally, False if AI-assisted.
        trace_id: Correlation ID matching the input.
        escalation_used: True if escalate() was called.
        processing_time_ms: Wall-clock time for processing in milliseconds.
    """

    output_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_factors: dict[str, Any] = field(default_factory=dict)
    deterministic: bool = True
    trace_id: str = ""
    escalation_used: bool = False
    processing_time_ms: float = 0.0


# ---------------------------------------------------------------------------
# Deductive Rule
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeductiveRule:
    """A single rule for deductive reasoning.

    Rules follow the form: if *premises* are satisfied, *conclusion* follows
    with the given *confidence*.

    Attributes:
        rule_id: Unique identifier for the rule.
        premises: List of premise strings that must all be satisfied.
        conclusion: The conclusion string that follows when premises hold.
        label: Human-readable label for the rule.
        confidence: Base confidence of the rule's conclusion [0, 1].
        metadata: Optional extensible metadata.
    """

    rule_id: str = field(default_factory=generate_uuid7)
    premises: tuple[str, ...] = ()
    conclusion: str = ""
    label: str = ""
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate invariants after construction."""
        if not self.premises:
            raise ValueError("A deductive rule must have at least one premise")
        if not self.conclusion:
            raise ValueError("A deductive rule must have a conclusion")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be in [0, 1], got {self.confidence}"
            )


# ---------------------------------------------------------------------------
# Inductive Pattern
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InductivePattern:
    """A statistical pattern used for inductive reasoning.

    Attributes:
        pattern_id: Unique identifier for the pattern.
        name: Human-readable name.
        observations: Set of observed values or conditions.
        conclusion: The generalisation drawn from the observations.
        support_count: Number of observations supporting this pattern.
        total_count: Total observations considered.
        confidence: Derived confidence (support_count / total_count).
        metadata: Optional extensible metadata.
    """

    pattern_id: str = field(default_factory=generate_uuid7)
    name: str = ""
    observations: tuple[str, ...] = ()
    conclusion: str = ""
    support_count: int = 0
    total_count: int = 1
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Auto-compute confidence and validate invariants."""
        if self.total_count <= 0:
            raise ValueError("total_count must be positive")
        if self.support_count > self.total_count:
            raise ValueError(
                f"support_count ({self.support_count}) cannot exceed "
                f"total_count ({self.total_count})"
            )
        computed = self.support_count / self.total_count
        object.__setattr__(self, "confidence", round(computed, 6))


# ---------------------------------------------------------------------------
# Analogy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Analogy:
    """A scored analogy between a source situation and a target situation.

    Attributes:
        analogy_id: Unique identifier.
        source_id: Identifier of the known/source situation.
        target_id: Identifier of the novel/target situation.
        source_description: Description of the source situation.
        target_description: Description of the target situation.
        shared_features: Features common to both situations.
        similarity_score: Computed similarity [0, 1].
        confidence: Transformed similarity score for confidence tracking.
        metadata: Optional extensible metadata.
    """

    analogy_id: str = field(default_factory=generate_uuid7)
    source_id: str = ""
    target_id: str = ""
    source_description: str = ""
    target_description: str = ""
    shared_features: tuple[str, ...] = ()
    similarity_score: float = 0.0
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not 0.0 <= self.similarity_score <= 1.0:
            raise ValueError(
                f"similarity_score must be in [0, 1], got {self.similarity_score}"
            )
        object.__setattr__(self, "confidence", round(self.similarity_score, 6))


# ---------------------------------------------------------------------------
# Causal Link / Evidence Chain
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CausalLink:
    """A single link in a causal evidence chain.

    Attributes:
        cause: Description of the cause.
        effect: Description of the effect.
        evidence_id: ID of the evidence supporting this causal link.
        strength: How strongly the cause leads to the effect [0, 1].
        direction: "forward" (cause→effect) or "reverse" (effect→cause).
    """

    cause: str = ""
    effect: str = ""
    evidence_id: str = ""
    strength: float = 1.0
    direction: str = "forward"

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.cause:
            raise ValueError("cause must be non-empty")
        if not self.effect:
            raise ValueError("effect must be non-empty")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(
                f"strength must be in [0, 1], got {self.strength}"
            )
        if self.direction not in ("forward", "reverse"):
            raise ValueError(
                f"direction must be 'forward' or 'reverse', got {self.direction!r}"
            )


@dataclass(frozen=True)
class CausalChain:
    """An ordered chain of causal links from root cause to final effect.

    Attributes:
        chain_id: Unique identifier.
        links: Ordered list of CausalLink, root cause first.
        overall_strength: Aggregate strength across the chain [0, 1].
        confidence: Derived confidence from the chain traversal.
    """

    chain_id: str = field(default_factory=generate_uuid7)
    links: tuple[CausalLink, ...] = ()
    overall_strength: float = 0.0
    confidence: float = 0.0

    def __post_init__(self) -> None:
        """Auto-compute aggregate strength and confidence."""
        if not self.links:
            object.__setattr__(self, "overall_strength", 0.0)
            object.__setattr__(self, "confidence", 0.0)
        else:
            product = 1.0
            for link in self.links:
                product *= link.strength
            geo_mean = product ** (1.0 / len(self.links))
            object.__setattr__(self, "overall_strength", round(geo_mean, 6))
            object.__setattr__(self, "confidence", round(geo_mean, 6))


# ---------------------------------------------------------------------------
# Counterfactual Scenario
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CounterfactualScenario:
    """A "what if" scenario for counterfactual reasoning.

    Attributes:
        scenario_id: Unique identifier.
        actual_event: What actually happened.
        alternative_event: What could have happened instead.
        predicted_outcome: The predicted outcome of the alternative.
        factors: Key factors that would differ.
        confidence: Confidence in the prediction [0, 1].
        metadata: Optional extensible metadata.
    """

    scenario_id: str = field(default_factory=generate_uuid7)
    actual_event: str = ""
    alternative_event: str = ""
    predicted_outcome: str = ""
    factors: tuple[str, ...] = ()
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Conclusion
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Conclusion:
    """A single reasoning conclusion produced by the Reasoning Engine.

    Every conclusion includes its reasoning type, the evidence chain
    supporting it, the computed confidence, and alternative conclusions
    that were considered but not selected.

    Attributes:
        conclusion_id: Unique identifier.
        reasoning_type: The type of reasoning that produced this conclusion.
        statement: The conclusion statement.
        confidence: Computed confidence score [0, 1].
        confidence_factors: Breakdown of confidence computation.
        evidence_chain: Ordered list of evidence IDs supporting the conclusion.
        alternatives: Other conclusions that were considered.
        trace_id: Correlation ID for the reasoning chain.
        timestamp: ISO-8601 timestamp of when the conclusion was reached.
        metadata: Optional extensible metadata.
    """

    conclusion_id: str = field(default_factory=generate_uuid7)
    reasoning_type: ReasoningType = ReasoningType.DEDUCTIVE
    statement: str = ""
    confidence: float = 0.0
    confidence_factors: dict[str, Any] = field(default_factory=dict)
    evidence_chain: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    trace_id: str = ""
    timestamp: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate reasoning_type."""
        if not isinstance(self.reasoning_type, ReasoningType):
            raise TypeError(
                f"reasoning_type must be a ReasoningType enum, "
                f"got {self.reasoning_type!r}"
            )


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EscalationResult:
    """Result of escalating to an external AI inference provider.

    The escalation bridge is called when deterministic computation yields
    confidence below the engine's threshold.

    Attributes:
        result: The AI-provided result payload.
        confidence: Re-computed confidence after AI processing [0, 1].
        provider: Identifier of the AI provider used.
        raw_response: The raw response from the provider, if available.
        processing_time_ms: Time spent in AI inference.
    """

    result: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    provider: str = ""
    raw_response: str = ""
    processing_time_ms: float = 0.0


# ---------------------------------------------------------------------------
# Deductive Rule Set
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeductiveRuleSet:
    """A named collection of deductive rules.

    Attributes:
        name: Name for this rule set.
        rules: Tuple of DeductiveRule instances.
        description: Optional description of what this rule set covers.
    """

    name: str = ""
    rules: tuple[DeductiveRule, ...] = ()
    description: str = ""


__all__ = [
    "Analogy",
    "CausalChain",
    "CausalLink",
    "Conclusion",
    "CounterfactualScenario",
    "DeductiveRule",
    "DeductiveRuleSet",
    "EngineInput",
    "EngineOutput",
    "EscalationResult",
    "InductivePattern",
    "ReasoningType",
]
