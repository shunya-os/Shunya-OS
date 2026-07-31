"""SHUNYA — Legacy GovernanceLayer (Backward Compatibility).

Wraps the canonical GovernanceEngine to provide backward-compatible
interfaces for existing call sites that import GovernanceLayer,
GovernanceVerdict, Policy, PolicyRegistry, PolicySeverity, PolicyScope.

All new code SHOULD import from app.shunya.governance_engine directly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.shunya.governance_engine.models import (
    GovernanceInput, GovernanceVerdict as CanonicalVerdict,
    Policy as CanonicalPolicy,
    PolicyRegistry as CanonicalPolicyRegistry,
    PolicySeverity, PolicyScope,
)
from app.shunya.governance_engine.engine import GovernanceEngine


class GovernanceLayer:
    """Legacy GovernanceLayer wrapping GovernanceEngine for backward compatibility."""

    def __init__(self):
        self._engine = GovernanceEngine()

    def validate_plan(self, plan: dict, context: dict | None = None) -> 'GovernanceVerdict':
        """Validate a plan against all applicable policies (legacy API)."""
        ctx = {**(context or {}), **plan}
        ctx.setdefault("domain", "travel")
        ctx.setdefault("action_type", "plan")
        gov_input = GovernanceInput(
            action_type=ctx.get("action_type", "plan"),
            proposal=plan,
            evidence_chain=ctx.get("evidence_chain", ctx.get("reasoning_evidence", [])),
            confidence=float(ctx.get("confidence", 0.5)),
            tenant_id=ctx.get("tenant_id"),
            actor_id=ctx.get("actor_id", ""),
            domain=ctx.get("domain", "travel"),
        )
        canonical = self._engine.evaluate(gov_input)
        return GovernanceVerdict.from_canonical(canonical, ctx)

    def validate_action(self, action: str, payload: dict,
                        context: dict | None = None) -> 'GovernanceVerdict':
        """Validate a specific action (legacy API)."""
        ctx = {**(context or {}), "action": action, **payload}
        gov_input = GovernanceInput(
            action_type=action,
            proposal=payload,
            tenant_id=ctx.get("tenant_id"),
            actor_id=ctx.get("actor_id", ""),
            domain=ctx.get("domain", "travel"),
        )
        canonical = self._engine.evaluate(gov_input)
        return GovernanceVerdict.from_canonical(canonical, ctx)

    @property
    def policies(self) -> object:
        return self._engine.policies

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        return self._engine.get_audit_log(limit)

    @property
    def stats(self) -> dict:
        return self._engine.stats


class GovernanceVerdict:
    """Legacy GovernanceVerdict (backward-compatible)."""

    def __init__(self, approved: bool, confidence: float = 0.0,
                 blocking_policies: list[str] | None = None,
                 warnings: list[str] | None = None,
                 reviews_required: list[str] | None = None,
                 evidence_checked: bool = False,
                 context: dict | None = None):
        self.approved = approved
        self.confidence = confidence
        self.blocking_policies = blocking_policies or []
        self.warnings = warnings or []
        self.reviews_required = reviews_required or []
        self.evidence_checked = evidence_checked
        self.context = context or {}

    def to_dict(self) -> dict:
        return {
            "approved": self.approved,
            "confidence": self.confidence,
            "blocking_policies": self.blocking_policies,
            "warnings": self.warnings,
            "reviews_required": self.reviews_required,
            "evidence_checked": self.evidence_checked,
        }

    @classmethod
    def from_canonical(cls, canonical: CanonicalVerdict,
                       context: dict) -> 'GovernanceVerdict':
        """Convert a canonical GovernanceVerdict to a legacy one."""
        return cls(
            approved=canonical.approved,
            confidence=canonical.confidence,
            blocking_policies=canonical.blocking_policies,
            warnings=canonical.warnings,
            reviews_required=canonical.reviews_required,
            evidence_checked=canonical.evidence_checked,
            context=context,
        )


# Re-export legacy types with same names
Policy = CanonicalPolicy
PolicyRegistry = CanonicalPolicyRegistry