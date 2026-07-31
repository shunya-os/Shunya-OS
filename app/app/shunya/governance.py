"""
Shunya — Governance Layer (Phase 2)

Policy engine that validates every decision before execution.
Sits between Planner and Workflow. Ensures AI proposes, humans dispose.

Responsibilities:
- Policy checking: does this plan comply with business rules?
- Permission checking: does the request have authority?
- Workflow validation: does the plan sequence make sense?
- Evidence verification: does the reasoning support the decision?
- Can STOP execution even if Reasoning made a bad recommendation
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Policy Types
# ---------------------------------------------------------------------------


class PolicySeverity(Enum):
    BLOCK = "block"        # Cannot proceed under any circumstances
    WARN = "warn"          # Logged, human notified, can proceed
    REVIEW = "review"      # Requires human approval before proceeding
    PASS = "pass"          # Automatically approved


class PolicyScope(Enum):
    GLOBAL = "global"          # Applies to all domains
    DOMAIN = "domain"          # Applies to specific domain (travel, healthcare...)
    ACTION = "action"          # Applies to specific action type
    ENVIRONMENT = "environment"  # Applies to specific env (production, staging)


@dataclass
class Policy:
    """A single governance policy rule."""
    name: str
    description: str
    scope: PolicyScope
    severity: PolicySeverity
    condition: str            # Python expression evaluated against context
    error_message: str
    domain: str = ""
    action: str = ""
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def evaluate(self, context: dict) -> tuple[bool, str]:
        """
        Evaluate this policy against a decision context.
        Returns (passed: bool, message: str)
        """
        if not self.enabled:
            return True, ""

        try:
            # Build evaluation environment with safe access to context
            env = {
                "ctx": SafeDict(context),
                "has": lambda k: k in context and context[k] is not None,
                "get": lambda k, d=None: context.get(k, d),
                "len": len,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "re": re,
                "re_match": lambda p, s: bool(re.match(p, str(s))) if s else False,
                "in_range": lambda v, lo, hi: lo <= v <= hi,
            }
            result = eval(self.condition, {"__builtins__": {}}, env)
            if result:
                return True, ""
            return False, self.error_message
        except Exception as e:
            return False, f"Policy evaluation error: {e}"


class SafeDict(dict):
    """A dict wrapper that returns None for missing keys instead of raising KeyError.
    Supports both dict['key'] and dict.key access patterns."""
    def __missing__(self, key):
        return None

    def __getattr__(self, key):
        # Allows ctx.pax_count access in policy conditions
        if key.startswith('_'):
            raise AttributeError(key)
        return self.get(key, None)


# ---------------------------------------------------------------------------
# Governance Result
# ---------------------------------------------------------------------------


@dataclass
class GovernanceVerdict:
    """Result of governance validation on a decision/plan."""
    approved: bool
    confidence: float = 0.0       # 0.0 to 1.0
    blocking_policies: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reviews_required: list[str] = field(default_factory=list)
    evidence_checked: bool = False
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "approved": self.approved,
            "confidence": self.confidence,
            "blocking_policies": self.blocking_policies,
            "warnings": self.warnings,
            "reviews_required": self.reviews_required,
            "evidence_checked": self.evidence_checked,
        }


# ---------------------------------------------------------------------------
# Policy Registry
# ---------------------------------------------------------------------------


class PolicyRegistry:
    """Central registry of all governance policies."""

    def __init__(self):
        self._policies: dict[str, Policy] = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load built-in default policies."""
        defaults = [
            # Budget sanity
            Policy(
                "budget_sanity",
                "Total estimated cost must not exceed 10x the stated budget",
                PolicyScope.GLOBAL, PolicySeverity.WARN,
                condition="not ctx.budget or not ctx.estimated_cost or ctx.estimated_cost <= float(ctx.budget) * 10",
                error_message="Estimated cost far exceeds stated budget",
            ),
            # Destination known
            Policy(
                "destination_known",
                "Destination must be recognized in knowledge base",
                PolicyScope.GLOBAL, PolicySeverity.REVIEW,
                condition="ctx.destination and ctx.destination_confidence and ctx.destination_confidence > 0.3",
                error_message="Destination not recognized with sufficient confidence",
            ),
            # Pax sanity
            Policy(
                "pax_sanity",
                "Number of travelers must be reasonable (1-100)",
                PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                condition="not ctx.pax_count or in_range(ctx.pax_count, 1, 100)",
                error_message="Number of travelers is outside reasonable range (1-100)",
            ),
            # Date sanity
            Policy(
                "date_sanity",
                "Trip must be in the future",
                PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                condition="not ctx.trip_start_date or ctx.trip_start_date > 'today'",
                error_message="Trip dates must be in the future",
            ),
            # Lead time
            Policy(
                "lead_time",
                "Insufficient lead time for international travel",
                PolicyScope.DOMAIN, PolicySeverity.WARN,
                condition="not ctx.is_international or (ctx.lead_time_days or 999) >= 14",
                error_message="International travel requires at least 14 days lead time",
                domain="travel",
            ),
            # Visa check
            Policy(
                "visa_required",
                "Visa requirements must be communicated for international travel",
                PolicyScope.DOMAIN, PolicySeverity.REVIEW,
                condition="not ctx.is_international or ctx.visa_communicated",
                error_message="Visa requirements not communicated for international trip",
                domain="travel",
            ),
            # Wedding specific
            Policy(
                "wedding_lead_time",
                "Destination weddings require minimum 60 days planning",
                PolicyScope.DOMAIN, PolicySeverity.BLOCK,
                condition="not ctx.is_wedding or (ctx.lead_time_days or 0) >= 60",
                error_message="Destination weddings require at least 60 days planning time",
                domain="travel",
            ),
            # Payment integrity
            Policy(
                "payment_no_exceeds_total",
                "Total payments must not exceed invoice total",
                PolicyScope.GLOBAL, PolicySeverity.WARN,
                condition="not ctx.total_paid or not ctx.invoice_total or ctx.total_paid <= ctx.invoice_total * 1.05",
                error_message="Total payments exceed invoice total by more than 5%",
            ),
        ]
        for p in defaults:
            self.register(p)

    def register(self, policy: Policy):
        """Register a new policy."""
        key = f"{policy.scope.value}:{policy.name}"
        self._policies[key] = policy

    def get(self, name: str) -> Optional[Policy]:
        return self._policies.get(name)

    def get_by_scope(self, scope: PolicyScope) -> list[Policy]:
        return [p for p in self._policies.values() if p.scope == scope]

    def get_applicable(self, context: dict) -> list[Policy]:
        """Get all policies that apply to a given decision context."""
        domain = context.get("domain", "")
        action = context.get("action", "")
        applicable = []
        for policy in self._policies.values():
            if not policy.enabled:
                continue
            if policy.scope == PolicyScope.GLOBAL:
                applicable.append(policy)
            elif policy.scope == PolicyScope.DOMAIN and domain == policy.domain:
                applicable.append(policy)
            elif policy.scope == PolicyScope.ACTION and action == policy.action:
                applicable.append(policy)
            elif policy.scope == PolicyScope.ENVIRONMENT:
                applicable.append(policy)
        return applicable


# ---------------------------------------------------------------------------
# Governance Layer
# ---------------------------------------------------------------------------


class GovernanceLayer:
    """
    The governance engine. Validates every decision/plan before execution.

    In the Shunya pipeline, this sits between Planner and Workflow:
        Planner → Governance → Workflow → Executor
    """

    def __init__(self):
        self.policies = PolicyRegistry()
        self._audit_log: list[dict] = []

    def validate_plan(self, plan: dict, context: dict | None = None) -> GovernanceVerdict:
        """
        Validate a plan against all applicable policies.

        Args:
            plan: The plan dict from PlannerLayer
            context: Additional context (domain, environment, user role...)

        Returns:
            GovernanceVerdict with approval status, blocking policies, warnings
        """
        ctx = {**(context or {}), **plan}
        ctx.setdefault("domain", "travel")
        ctx.setdefault("action", "itinerary")

        # Enrich context with computed values
        self._enrich_context(ctx)

        applicable = self.policies.get_applicable(ctx)
        verdict = GovernanceVerdict(
            approved=True,
            context=ctx,
        )

        for policy in applicable:
            passed, message = policy.evaluate(ctx)
            if not passed:
                entry = f"[{policy.severity.value}] {policy.name}: {message}"
                if policy.severity == PolicySeverity.BLOCK:
                    verdict.blocking_policies.append(entry)
                    verdict.approved = False
                elif policy.severity == PolicySeverity.WARN:
                    verdict.warnings.append(entry)
                elif policy.severity == PolicySeverity.REVIEW:
                    verdict.reviews_required.append(entry)
                    verdict.approved = False  # Requires human review

        # Calculate confidence score
        total = len(applicable) or 1
        blocked = len(verdict.blocking_policies)
        warned = len(verdict.warnings)
        reviewed = len(verdict.reviews_required)
        passed_count = total - blocked - warned - reviewed
        verdict.confidence = max(0.0, min(1.0, passed_count / total))

        # Check evidence
        verdict.evidence_checked = bool(ctx.get("reasoning_evidence"))

        self._audit(verdict, ctx)
        return verdict

    def validate_action(self, action: str, payload: dict, context: dict | None = None) -> GovernanceVerdict:
        """
        Validate a specific action (not a full plan).

        Used by Executor before performing any action.
        """
        ctx = {
            **(context or {}),
            "action": action,
            **payload,
        }
        return self.validate_plan({}, ctx)

    def _enrich_context(self, ctx: dict):
        """Add computed fields to context for policy evaluation."""
        # Pax count
        pax_str = str(ctx.get("pax", ""))
        nums = [int(s) for s in pax_str.split() if s.isdigit()]
        ctx["pax_count"] = nums[0] if nums else None

        # Estimated cost
        daily = ctx.get("daily_budget_per_person", ctx.get("budget_estimate", 0))
        days = ctx.get("itinerary_days", ctx.get("duration_days", 0))
        pax = ctx.get("pax_count", 1)
        ctx["estimated_cost"] = float(daily or 0) * int(days or 1) * int(pax or 1)

        # International check
        dest = str(ctx.get("destination", "")).lower()
        domestic_places = {"goa", "kerala", "udaipur", "manali", "shimla",
                           "andaman", "jaipur", "delhi", "mumbai", "bengaluru",
                           "chennai", "kolkata", "hyderabad", "pune", "agra"}
        ctx["is_international"] = dest not in domestic_places and bool(dest)

        # Wedding check
        notes = str(ctx.get("notes", "")).lower()
        ctx["is_wedding"] = "wedding" in notes or ctx.get("occasion") == "wedding"

        # Lead time
        dates_str = str(ctx.get("dates", ""))
        ctx["lead_time_days"] = self._estimate_lead_time(dates_str)

        # Trip start date
        ctx["trip_start_date"] = self._extract_start_date(dates_str)

    def _estimate_lead_time(self, dates_str: str) -> int:
        """Estimate lead time in days from date string."""
        if not dates_str:
            return 999
        try:
            from datetime import datetime as dt
            raw = dates_str.replace("to", "-").replace("till", "-").split("-")
            first_date = raw[0].strip() if raw else ""
            for fmt in ("%d %b %Y", "%d %B %Y", "%d %b", "%d %B", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    d = dt.strptime(first_date, fmt)
                    return (d - datetime.utcnow()).days
                except ValueError:
                    continue
        except Exception:
            pass
        return 999

    def _extract_start_date(self, dates_str: str) -> str:
        """Extract start date as string for policy comparison."""
        if not dates_str:
            return ""
        return dates_str.split("-")[0].strip() if "-" in dates_str else dates_str.strip()

    def _audit(self, verdict: GovernanceVerdict, context: dict):
        """Record governance decision for audit trail."""
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "approved": verdict.approved,
            "confidence": verdict.confidence,
            "blocking": len(verdict.blocking_policies),
            "warnings": len(verdict.warnings),
            "reviews": len(verdict.reviews_required),
            "destination": context.get("destination", ""),
            "action": context.get("action", ""),
        })

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        """Return recent governance audit entries."""
        return list(reversed(self._audit_log[-limit:]))

    @property
    def stats(self) -> dict:
        """Return governance statistics."""
        total = len(self._audit_log)
        approved = sum(1 for e in self._audit_log if e["approved"])
        blocked = total - approved
        avg_confidence = sum(e["confidence"] for e in self._audit_log) / total if total else 0
        return {
            "total_decisions": total,
            "approved": approved,
            "blocked": blocked,
            "approval_rate": round(approved / total * 100, 1) if total else 0,
            "avg_confidence": round(avg_confidence, 2),
            "policies_loaded": len(self.policies._policies),
        }