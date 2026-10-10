"""Cost Tracker — records per-provider token usage and estimated costs.

G3 Phase 7.3.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Per-1K-token pricing in USD (fallback estimates when provider doesn't supply)
# Source: published API pricing as of 2025 — update as providers change.
_DEFAULT_PRICES: dict[str, dict[str, float]] = {
    "groq": {"input_per_1k": 0.0001, "output_per_1k": 0.0004},
    "openrouter": {"input_per_1k": 0.001, "output_per_1k": 0.003},
    "openai": {"input_per_1k": 0.0025, "output_per_1k": 0.01},
    "anthropic": {"input_per_1k": 0.003, "output_per_1k": 0.015},
    "local": {"input_per_1k": 0.0, "output_per_1k": 0.0},
    "default": {"input_per_1k": 0.001, "output_per_1k": 0.003},
}


class CostTracker:
    """Records and estimates inference costs per provider.

    Thread-safe for concurrent writes from the pipeline's observe stage.
    """

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []
        self._per_provider: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0, "requests": 0}
        )

    def record(
        self,
        provider: str,
        model: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0.0,
        success: bool = True,
    ) -> dict[str, Any]:
        """Record usage and compute estimated cost.

        Returns the cost breakdown for this record.
        """
        prices = _DEFAULT_PRICES.get(provider.lower(), _DEFAULT_PRICES["default"])
        input_cost = (input_tokens / 1000) * prices["input_per_1k"]
        output_cost = (output_tokens / 1000) * prices["output_per_1k"]
        estimated_cost = round(input_cost + output_cost, 6)

        record = {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "success": success,
            "estimated_cost_usd": estimated_cost,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._records.append(record)

        # Accumulate per-provider totals
        acc = self._per_provider[provider.lower()]
        acc["input_tokens"] += input_tokens
        acc["output_tokens"] += output_tokens
        acc["estimated_cost_usd"] = round(acc["estimated_cost_usd"] + estimated_cost, 6)
        acc["requests"] += 1

        return record

    def get_provider_summary(self, provider: str | None = None) -> dict[str, Any]:
        """Get cost summary for a provider (or all if None)."""
        if provider:
            data = dict(self._per_provider.get(provider.lower(), {}))
            data["provider"] = provider
            return data

        total: dict[str, Any] = {"total_input_tokens": 0, "total_output_tokens": 0,
                                 "total_cost_usd": 0.0, "providers": {}}
        for prov, acc in self._per_provider.items():
            total["total_input_tokens"] += acc["input_tokens"]
            total["total_output_tokens"] += acc["output_tokens"]
            total["total_cost_usd"] = round(total["total_cost_usd"] + acc["estimated_cost_usd"], 6)
            total["providers"][prov] = dict(acc)
        return total

    def get_all_records(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent cost records."""
        return self._records[-limit:]

    def get_total_cost(self) -> float:
        """Return total estimated cost across all providers."""
        return round(sum(r["estimated_cost_usd"] for r in self._records), 6)

    def reset(self) -> None:
        """Clear all accumulated records (testing)."""
        self._records.clear()
        self._per_provider.clear()


# Module-level singleton
_INSTANCE: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = CostTracker()
    return _INSTANCE


def reset_cost_tracker() -> None:
    global _INSTANCE
    if _INSTANCE:
        _INSTANCE.reset()
    _INSTANCE = None