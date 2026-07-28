"""SHUNYA — Context assembly (Phase E).

Deterministic orchestration of context providers.
Produces identical results for identical inputs.

Architectural authority: ES-009
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.shunya.context.models import (
    ContextRequest, ContextSection, WorkspaceContext,
    BudgetReport, ContextProvenance,
)
from app.shunya.context.providers import ContextProvider
from app.shunya.context.budget import BudgetEnforcer
from app.shunya.context.fingerprint import Fingerprinter


class ContextAssembler:
    """Orchestrates context providers into a canonical WorkspaceContext.

    Deterministic — identical inputs always produce identical outputs
    (same sections, same fingerprints).
    """

    def __init__(
        self,
        providers: List[ContextProvider],
        budget_enforcer: Optional[BudgetEnforcer] = None,
        fingerprinter: Optional[Fingerprinter] = None,
    ) -> None:
        self._providers = providers
        self._budget = budget_enforcer or BudgetEnforcer()
        self._fingerprinter = fingerprinter or Fingerprinter()

    def assemble(self, request: ContextRequest) -> WorkspaceContext:
        """Assemble a workspace context from all providers.

        Args:
            request: The context assembly request.

        Returns:
            A fully assembled WorkspaceContext.
        """
        start = time.time()

        # Phase 1: Fetch from all providers
        sections: Dict[str, ContextSection] = {}
        raw_items: Dict[str, List[Dict[str, Any]]] = {}

        for provider in self._providers:
            section = provider.fetch(request)
            sections[provider.name()] = section
            if not section.is_degraded:
                raw_items[provider.name()] = section.items

        # Phase 2: Enforce budget
        budget = self._budget.enforce(
            raw_items,
            config_max_items=request.max_items,
            config_max_size=request.max_size_bytes,
        )

        # Phase 3: Filter items by budget
        for provider_name, kept_count in budget.sections.items():
            if provider_name in sections:
                section = sections[provider_name]
                section.items = section.items[:kept_count]
                section.item_count = len(section.items)

        # Phase 4: Compute fingerprint
        fingerprint = self._fingerprinter.fingerprint(
            sections={k: v.items for k, v in sections.items()},
            tenant_id=request.tenant_id,
            actor_id=request.actor_id,
            purpose_code=request.purpose_code,
        )

        # Phase 5: Build context
        is_degraded = any(s.is_degraded for s in sections.values()) or budget.truncated

        context = WorkspaceContext(
            tenant_id=request.tenant_id,
            actor_id=request.actor_id,
            purpose_code=request.purpose_code,
            fingerprint=fingerprint,
            sections=sections,
            budget=budget,
            provenance=ContextProvenance(
                request_id=request.request_id,
                correlation_id=request.correlation_id,
            ),
            is_degraded=is_degraded,
            metadata=request.metadata,
        )

        return context