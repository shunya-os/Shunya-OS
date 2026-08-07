"""Attention Intelligence — determines what matters right now.

Scans every composed UCP for signals and prioritizes them.
Attention is dynamic, never static.
"""

from __future__ import annotations
from typing import Any
from core.personal_os.models import AttentionSignal, LivingContextSnapshot


class AttentionEngine:
    """Determines priority across all UCPs."""

    def scan(self, context: LivingContextSnapshot,
             runtimes: dict[str, Any]) -> list[AttentionSignal]:
        signals: list[AttentionSignal] = []

        # Check initiatives for delayed/blocked milestones
        for iid in context.active_initiatives:
            signals.append(AttentionSignal(
                owner_id=context.owner_id, priority=0.8,
                signal_type="initiative_attention",
                description=f"Initiative {iid} requires attention",
                source_ucp="initiative", source_id=iid,
                recommendation="Check milestone status and unblock progress",
                requires_action=True, can_automate=False, can_delegate=True))

        # Check agreements for breaches
        for aid in context.active_agreements:
            signals.append(AttentionSignal(
                owner_id=context.owner_id, priority=0.9,
                signal_type="agreement_breach",
                description=f"Agreement {aid} has detected issues",
                source_ucp="agreement", source_id=aid,
                recommendation="Review and address agreement issues",
                requires_action=True, can_automate=False, can_delegate=False))

        # Check financial concerns
        for fc in context.financial_commitments:
            signals.append(AttentionSignal(
                owner_id=context.owner_id, priority=0.7,
                signal_type="financial_attention",
                description=f"Financial commitment requires review",
                source_ucp="financial",
                recommendation="Review financial position",
                requires_action=True, can_automate=False, can_delegate=True))

        # Check health concerns
        for hc in context.health_concerns:
            signals.append(AttentionSignal(
                owner_id=context.owner_id, priority=0.85,
                signal_type="health_concern",
                description=f"Health concern: {hc}",
                source_ucp="health",
                recommendation="Schedule health review",
                requires_action=True, can_automate=False, can_delegate=False))

        # Check operations issues
        for oi in context.operations_issues:
            signals.append(AttentionSignal(
                owner_id=context.owner_id, priority=0.75,
                signal_type="operations_issue",
                description=f"Operations issue: {oi}",
                source_ucp="operations",
                recommendation="Review and resolve operations issue",
                requires_action=True, can_automate=False, can_delegate=True))

        # Sort by priority descending
        signals.sort(key=lambda s: s.priority, reverse=True)
        return signals