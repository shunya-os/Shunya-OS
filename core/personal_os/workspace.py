"""Universal Workspace — adaptive, no fixed applications.

The Workspace continuously changes according to current reality,
attention, objective, evidence, conversation, and execution state.
"""

from __future__ import annotations
from typing import Any
from core.personal_os.models import AttentionSignal, LivingContextSnapshot


class WorkspaceEngine:
    """Adaptive workspace — no fixed applications, no fixed menus."""

    def __init__(self) -> None:
        self._owner_id: str = ""
        self._current_view: dict[str, Any] = {}

    def set_owner(self, oid: str) -> None:
        self._owner_id = oid

    def render(self, context: LivingContextSnapshot,
               signals: list[AttentionSignal]) -> dict[str, Any]:
        """Render the workspace based on current context and attention."""
        sections = []

        # Priority items from attention signals
        if signals:
            top = signals[:3]
            sections.append({
                "section": "attention",
                "title": "What Matters Now",
                "items": [{"type": s.signal_type, "description": s.description,
                           "priority": s.priority, "recommendation": s.recommendation}
                          for s in top],
            })

        # Active initiatives
        if context.active_initiatives:
            sections.append({
                "section": "initiatives",
                "title": "Active Initiatives",
                "count": len(context.active_initiatives),
                "items": [{"id": iid} for iid in context.active_initiatives],
            })

        # Active agreements
        if context.active_agreements:
            sections.append({
                "section": "agreements",
                "title": "Agreements Requiring Attention",
                "count": len(context.active_agreements),
                "items": [{"id": aid} for aid in context.active_agreements],
            })

        # Financial snapshot
        if context.financial_commitments:
            sections.append({
                "section": "financial",
                "title": "Financial Overview",
                "count": len(context.financial_commitments),
            })

        # Health concerns
        if context.health_concerns:
            sections.append({
                "section": "health",
                "title": "Health Alerts",
                "count": len(context.health_concerns),
                "items": [{"concern": hc} for hc in context.health_concerns],
            })

        # Learning paths
        if context.learning_paths:
            sections.append({
                "section": "learning",
                "title": "Learning in Progress",
                "count": len(context.learning_paths),
                "items": [{"path": lp} for lp in context.learning_paths],
            })

        self._current_view = {
            "owner_id": self._owner_id,
            "sections": sections,
            "total_sections": len(sections),
            "attention_signals": len(signals),
        }
        return self._current_view

    def get_state(self) -> dict[str, Any]:
        return self._current_view