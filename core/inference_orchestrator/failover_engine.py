"""Failover Engine — 3-level transparent retry for inference requests.

Levels
------
1. **Model**          — swap to a different model on the same provider.
2. **Provider**       — swap to a different provider for the same model.
3. **Infrastructure** — swap to a fundamentally different infrastructure
                        (e.g. local → remote, primary → DR region).

Each level catches exceptions, checks retryability, and escalates only
when the current level is exhausted.
"""

from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ── Public types ────────────────────────────────────────────────────────────


class FailoverLevel(str, enum.Enum):
    MODEL = "model"
    PROVIDER = "provider"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class FailoverResult:
    """Result of a failover execution attempt."""

    success: bool
    output: Any = None
    error: str | None = None
    attempts: int = 0
    level_used: FailoverLevel | None = None
    chain: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "error": self.error,
            "attempts": self.attempts,
            "level_used": self.level_used.value if self.level_used else None,
            "chain": self.chain,
        }


@dataclass
class FailoverCandidate:
    """A single candidate in the failover chain."""

    model: str
    provider: str
    infrastructure: str = "primary"
    weight: int = 1  # higher = tried first within the same level

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "infrastructure": self.infrastructure,
        }


# Predicate: (exception, attempt_number) -> bool
RetryPredicate = Callable[[Exception, int], bool]


# ── Failover Engine ────────────────────────────────────────────────────────


class FailoverEngine:
    """3-level transparent retry for inference requests.

    Usage::

        engine = FailoverEngine()
        result = engine.execute(
            candidates=[...],
            invoke=my_llm_call,
            context={"messages": [...]},
        )
        if result.success:
            use(result.output)
    """

    def __init__(
        self,
        max_retries_per_level: int = 2,
        base_delay: float = 0.5,
        max_delay: float = 10.0,
        jitter: bool = True,
    ) -> None:
        self._max_attempts = max_retries_per_level
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._jitter = jitter
        self._retry_predicate: RetryPredicate = _default_retry_predicate

    def set_retry_predicate(self, predicate: RetryPredicate) -> None:
        """Override the default retry predicate.

        The predicate receives ``(exception, attempt_number)`` and returns
        ``True`` if the attempt should be retried.
        """
        self._retry_predicate = predicate

    # ── Execution ───────────────────────────────────────────────────────

    def execute(
        self,
        candidates: list[FailoverCandidate],
        invoke: Callable[..., Any],
        context: dict[str, Any] | None = None,
    ) -> FailoverResult:
        """Execute *invoke* with 3-level failover across *candidates*.

        Parameters
        ----------
        candidates : list[FailoverCandidate]
            Ordered list of candidates.  Sorted by level then weight.
        invoke : Callable
            The LLM invocation function.  Receives ``(model, provider,
            infrastructure, context)``.
        context : dict | None
            Arbitrary context passed to *invoke*.

        Returns
        -------
        FailoverResult
            Structured result with the outcome and chain.
        """
        ctx = context or {}
        chain: list[dict] = []
        total_attempts = 0

        # Sort candidates: model-first, then provider, then infrastructure
        sorted_candidates = self._sort_candidates(candidates)

        for level, level_candidates in self._group_by_level(sorted_candidates):
            for candidate in level_candidates:
                max_attempts = 1 if level == FailoverLevel.INFRASTRUCTURE else self._max_attempts
                for attempt in range(1, max_attempts + 1):
                    total_attempts += 1
                    attempt_info = {
                        "attempt": total_attempts,
                        "level": level.value,
                        "model": candidate.model,
                        "provider": candidate.provider,
                        "infrastructure": candidate.infrastructure,
                    }

                    try:
                        logger.info(
                            "Failover attempt %d/%d [%s]: %s on %s (%s)",
                            attempt, max_attempts, level.value,
                            candidate.model, candidate.provider,
                            candidate.infrastructure,
                        )
                        output = invoke(
                            model=candidate.model,
                            provider=candidate.provider,
                            infrastructure=candidate.infrastructure,
                            context=ctx,
                        )
                        attempt_info["status"] = "success"
                        chain.append(attempt_info)
                        return FailoverResult(
                            success=True,
                            output=output,
                            attempts=total_attempts,
                            level_used=level,
                            chain=chain,
                        )
                    except Exception as exc:
                        attempt_info["status"] = "failed"
                        attempt_info["error"] = str(exc)
                        chain.append(attempt_info)
                        logger.warning(
                            "Failover attempt %d failed [%s]: %s on %s — %s",
                            attempt, level.value,
                            candidate.model, candidate.provider, exc,
                        )

                        # Check if we should retry
                        if not self._retry_predicate(exc, attempt):
                            logger.info(
                                "Non-retryable error on %s/%s, "
                                "escalating to next level",
                                candidate.model, candidate.provider,
                            )
                            break  # escalate to next candidate

                        if attempt < max_attempts:
                            self._backoff(attempt)

        # All candidates exhausted
        return FailoverResult(
            success=False,
            error=(
                f"All candidates exhausted after {total_attempts} attempts "
                f"across all failover levels"
            ),
            attempts=total_attempts,
            chain=chain,
        )

    # ── Internals ───────────────────────────────────────────────────────

    def _sort_candidates(
        self,
        candidates: list[FailoverCandidate],
    ) -> list[FailoverCandidate]:
        """Sort by level priority (model→provider→infra), then weight desc."""
        level_order = {
            FailoverLevel.MODEL: 0,
            FailoverLevel.PROVIDER: 1,
            FailoverLevel.INFRASTRUCTURE: 2,
        }

        def _level_key(c: FailoverCandidate) -> int:
            # Infer level from candidate attributes
            # We don't have an explicit level field, so we infer it from the chain
            return 0  # Will be overridden by grouping

        return sorted(
            candidates,
            key=lambda c: (-c.weight, c.model, c.provider),
        )

    def _group_by_level(
        self,
        candidates: list[FailoverCandidate],
    ) -> list[tuple[FailoverLevel, list[FailoverCandidate]]]:
        """Group candidates by inferred failover level.

        Heuristic (can be overridden by setting explicit level on candidates):
        - Same model, different provider → PROVIDER level
        - Different model → MODEL level
        - Different infrastructure → INFRASTRUCTURE level
        """
        groups: list[tuple[FailoverLevel, list[FailoverCandidate]]] = []

        # Simple grouping: first candidate is MODEL level, subsequent
        # candidates with same model but different provider are PROVIDER,
        # and anything with infrastructure != 'primary' is INFRASTRUCTURE.
        if not candidates:
            return groups

        # All candidates with same model → MODEL level
        # All candidates with same model but different provider → PROVIDER level
        # All candidates with different infrastructure → INFRASTRUCTURE level

        seen_models: set[str] = set()
        seen_providers: set[str] = set()
        infra_candidates: list[FailoverCandidate] = []

        model_group: list[FailoverCandidate] = []
        provider_group: list[FailoverCandidate] = []

        for c in candidates:
            if c.infrastructure != "primary":
                infra_candidates.append(c)
            elif c.model not in seen_models:
                model_group.append(c)
                seen_models.add(c.model)
                seen_providers.add(c.provider)
            elif c.provider not in seen_providers:
                provider_group.append(c)
                seen_providers.add(c.provider)
            else:
                # Additional model variants
                model_group.append(c)

        if model_group:
            groups.append((FailoverLevel.MODEL, model_group))
        if provider_group:
            groups.append((FailoverLevel.PROVIDER, provider_group))
        if infra_candidates:
            groups.append((FailoverLevel.INFRASTRUCTURE, infra_candidates))

        # If we only have one group, everything is MODEL level
        if len(groups) == 1 and groups[0][0] == FailoverLevel.MODEL:
            # Try to split into model/provider
            if len(candidates) > 1:
                models = {c.model for c in candidates}
                if len(models) == 1:
                    # All same model — this is a provider-level failover
                    groups = [(FailoverLevel.PROVIDER, candidates)]
                else:
                    groups = [(FailoverLevel.MODEL, candidates)]

        return groups

    def _backoff(self, attempt: int) -> None:
        """Sleep with exponential backoff (+ optional jitter)."""
        import random

        delay = min(self._base_delay * (2 ** (attempt - 1)), self._max_delay)
        if self._jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        time.sleep(delay)


# ── Default retry predicate ────────────────────────────────────────────────


def _default_retry_predicate(exc: Exception, attempt: int) -> bool:
    """Retry on transient errors, give up on permanent ones.

    Transient:   timeout, rate-limit (429/503), connection errors
    Permanent:   auth failure, invalid request, model-not-found
    """
    msg = str(exc).lower()
    # Transient indicators
    transient = (
        "timeout" in msg
        or "rate limit" in msg
        or "429" in msg
        or "503" in msg
        or "service unavailable" in msg
        or "connection" in msg
        or "retry" in msg
        or "temporarily" in msg
        or "overloaded" in msg
        or "too many requests" in msg
    )
    # Permanent indicators
    permanent = (
        "auth" in msg and "fail" in msg
        or "unauthorized" in msg
        or "forbidden" in msg
        or "invalid api key" in msg
        or "model not found" in msg
        or "not found" in msg
        or "bad request" in msg
        or "permission" in msg
    )
    return transient and not permanent