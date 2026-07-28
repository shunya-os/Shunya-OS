"""SHUNYA — Context budget enforcement (Phase E).

Configurable limits, deterministic prioritisation, overflow handling,
and reporting of omitted context.

Architectural authority: ES-009, SHUNYA_SYSTEM_FLOW.md §2
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.shunya.context.models import BudgetReport


class BudgetEnforcer:
    """Enforces context budget limits.

    Priorities: request metadata (highest), identity, knowledge (lowest).
    Overflow items are removed in reverse priority order.
    """

    PROVIDER_PRIORITY = {
        "request": 0,    # Highest — always included
        "identity": 1,   # Always include
        "knowledge": 2,  # Lowest — may be truncated
    }

    def __init__(self, max_items: int = 100, max_size_bytes: int = 102400) -> None:
        self._max_items = max_items
        self._max_size_bytes = max_size_bytes

    def enforce(
        self,
        items_by_provider: Dict[str, List[Dict[str, Any]]],
        config_max_items: Optional[int] = None,
        config_max_size: Optional[int] = None,
    ) -> BudgetReport:
        """Enforce budget limits across provider sections.

        Returns a BudgetReport documenting what was kept and what was omitted.
        """
        max_items = config_max_items or self._max_items
        max_size = config_max_size or self._max_size_bytes

        report = BudgetReport(max_items=max_items, max_size_bytes=max_size)
        kept: Dict[str, List[Dict[str, Any]]] = {}
        total_items = 0
        total_size = 0

        # Sort providers by priority (lowest number = highest priority)
        sorted_providers = sorted(
            items_by_provider.keys(),
            key=lambda p: self.PROVIDER_PRIORITY.get(p, 99),
        )

        for provider in sorted_providers:
            items = items_by_provider.get(provider, [])
            kept_items: List[Dict[str, Any]] = []
            for item in items:
                if total_items >= max_items:
                    break
                item_size = _estimate_item_size(item)
                if total_size + item_size > max_size:
                    continue
                kept_items.append(item)
                total_items += 1
                total_size += item_size

            kept[provider] = kept_items
            report.sections[provider] = len(kept_items)

        report.total_items = total_items
        report.total_size_bytes = total_size
        report.truncated = total_items < sum(
            len(items) for items in items_by_provider.values()
        )

        return report


def _estimate_item_size(item: Dict[str, Any]) -> int:
    """Estimate the byte size of a context item."""
    try:
        import json
        return len(json.dumps(item, default=str))
    except (TypeError, ValueError):
        return 1024  # Default estimate