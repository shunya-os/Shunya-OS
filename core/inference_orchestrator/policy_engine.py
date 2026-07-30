"""Policy Engine — selects models by capability, not by name.

Every inference request is resolved through a policy that maps the
intended *task profile* (conversation, coding, reasoning, extraction)
to a concrete model + provider pair.  Capability-based routing means
policies are stable across provider migrations and model deprecations.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ── Public types ────────────────────────────────────────────────────────────


class RoutingPolicy(str, enum.Enum):
    """Named policies baked into the orchestrator."""

    CONVERSATION = "conversation"  # cheapest available, fast, general chat
    CODING = "coding"  # strongest reasoning / code-gen model
    REASONING = "reasoning"  # balanced — good chain-of-thought
    EXTRACTION = "extraction"  # cheap, high-throughput extraction
    DEFAULT = "default"  # fallback when no specific policy matches


@dataclass
class ModelCapability:
    """Describes what a model can do.  Used for capability-based routing."""

    name: str
    provider: str
    max_tokens: int = 8192
    supports_tools: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_per_1k_input: float = 0.0  # USD
    cost_per_1k_output: float = 0.0
    context_window: int = 8192
    throughput_tier: int = 1  # 1=cheapest, 5=most expensive
    reasoning_tier: int = 1  # 1=basic, 5=deep reasoning
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "max_tokens": self.max_tokens,
            "supports_tools": self.supports_tools,
            "supports_vision": self.supports_vision,
            "supports_streaming": self.supports_streaming,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "context_window": self.context_window,
            "throughput_tier": self.throughput_tier,
            "reasoning_tier": self.reasoning_tier,
            "tags": self.tags,
        }


@dataclass
class RoutingDecision:
    """Result of a policy resolution — the model + provider to use."""

    model: str
    provider: str
    policy: str
    reason: str
    fallback_chain: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "policy": self.policy,
            "reason": self.reason,
            "fallback_chain": self.fallback_chain,
            "metadata": self.metadata,
        }


# Predicate: (model_capability, request_context) -> bool
PolicyPredicate = Callable[[ModelCapability, dict[str, Any]], bool]


@dataclass
class PolicyRule:
    """A single policy rule: a name, a predicate, and a rank function."""

    name: str
    description: str
    predicate: PolicyPredicate | None = None
    rank_key: str = "throughput_tier"  # sort models by this capability attr
    rank_ascending: bool = True  # True = cheapest / fastest first


# ── Policy Engine ───────────────────────────────────────────────────────────


class PolicyEngine:
    """Resolves inference requests to a concrete model via capability-routing.

    Usage::

        engine = PolicyEngine()
        engine.register_models([...])
        engine.register_policy("my_policy", PolicyRule(...))
        decision = engine.resolve("conversation", {"tools": True})
    """

    def __init__(self) -> None:
        self._models: list[ModelCapability] = []
        self._policies: dict[str, PolicyRule] = {}
        self._default_policy: str = RoutingPolicy.DEFAULT.value

        self._register_default_policies()

    # ── Registration ────────────────────────────────────────────────────

    def register_policy(self, name: str, rule: PolicyRule) -> None:
        """Register (or overwrite) a named policy rule."""
        self._policies[name] = rule
        logger.info("Registered policy '%s': %s", name, rule.description)

    def register_models(self, models: list[ModelCapability]) -> None:
        """Register the available model catalogue."""
        self._models = list(models)
        logger.info("Registered %d models for policy routing", len(self._models))

    def set_default_policy(self, name: str) -> None:
        """Override the fallback policy name."""
        self._default_policy = name

    def get_policy_names(self) -> list[str]:
        return list(self._policies.keys())

    def get_models(self) -> list[ModelCapability]:
        return list(self._models)

    # ── Resolution ──────────────────────────────────────────────────────

    def resolve(
        self,
        policy_name: str,
        context: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        """Resolve *policy_name* to a concrete model given *context*.

        Returns a ``RoutingDecision`` with the best-match model, provider,
        and a human-readable ``reason``.  Never raises — falls back to the
        default policy if the requested one is unknown.
        """
        ctx = context or {}
        policy = self._policies.get(policy_name)

        # Unknown policy → fall back to default
        if policy is None:
            return self._resolve_fallback(
                policy_name,
                f"Unknown policy '{policy_name}', using default",
            )

        # Filter by predicate (if one exists)
        candidates = self._models
        if policy.predicate is not None:
            candidates = [m for m in candidates if policy.predicate(m, ctx)]

        if not candidates:
            reason = (
                f"Policy '{policy_name}': no model matched predicate "
                f"(context={ctx}), using default"
            )
            return self._resolve_fallback(policy_name, reason)

        # Rank and pick the best match
        best = self._rank(candidates, policy)
        fallback_chain = [
            {"model": m.name, "provider": m.provider}
            for m in candidates[1:4]  # top 3 alternates
        ]

        return RoutingDecision(
            model=best.name,
            provider=best.provider,
            policy=policy_name,
            reason=(
                f"Policy '{policy_name}' resolved to {best.name} "
                f"on {best.provider} (rank: {policy.rank_key}, "
                f"tier={getattr(best, policy.rank_key, '?')})"
            ),
            fallback_chain=fallback_chain,
            metadata={
                "candidates_considered": len(candidates),
                "rank_key": policy.rank_key,
                "rank_value": getattr(best, policy.rank_key, None),
            },
        )

    # ── Internals ───────────────────────────────────────────────────────

    def _register_default_policies(self) -> None:
        self.register_policy(
            RoutingPolicy.CONVERSATION.value,
            PolicyRule(
                name="conversation",
                description="Cheapest available model for general chat",
                predicate=lambda m, ctx: m.throughput_tier <= 2,
                rank_key="throughput_tier",
                rank_ascending=True,
            ),
        )
        self.register_policy(
            RoutingPolicy.CODING.value,
            PolicyRule(
                name="coding",
                description="Strongest reasoning / code-generation model",
                predicate=lambda m, ctx: m.reasoning_tier >= 4,
                rank_key="reasoning_tier",
                rank_ascending=False,
            ),
        )
        self.register_policy(
            RoutingPolicy.REASONING.value,
            PolicyRule(
                name="reasoning",
                description="Balanced model with good chain-of-thought",
                predicate=lambda m, ctx: m.reasoning_tier >= 3,
                rank_key="reasoning_tier",
                rank_ascending=False,
            ),
        )
        self.register_policy(
            RoutingPolicy.EXTRACTION.value,
            PolicyRule(
                name="extraction",
                description="Cheap, high-throughput extraction model",
                predicate=lambda m, ctx: m.throughput_tier <= 2,
                rank_key="throughput_tier",
                rank_ascending=True,
            ),
        )
        self.register_policy(
            RoutingPolicy.DEFAULT.value,
            PolicyRule(
                name="default",
                description="Fallback — cheapest model that satisfies the request",
                rank_key="throughput_tier",
                rank_ascending=True,
            ),
        )

    def _resolve_fallback(
        self,
        requested_policy: str,
        reason: str,
    ) -> RoutingDecision:
        """Fall back to the default policy."""
        default = self._policies.get(self._default_policy)
        if default is None or not self._models:
            return RoutingDecision(
                model="",
                provider="",
                policy=requested_policy,
                reason=f"{reason} — no models registered",
            )

        best = self._rank(self._models, default)
        return RoutingDecision(
            model=best.name,
            provider=best.provider,
            policy=requested_policy,
            reason=reason,
            fallback_chain=[{"model": m.name, "provider": m.provider} for m in self._models[:3]],
        )

    @staticmethod
    def _rank(candidates: list[ModelCapability], policy: PolicyRule) -> ModelCapability:
        """Sort candidates by *rank_key* and return the best."""
        key = policy.rank_key
        ascending = policy.rank_ascending
        sorted_candidates = sorted(
            candidates,
            key=lambda m: getattr(m, key, 0),
            reverse=not ascending,
        )
        return sorted_candidates[0]