"""
SHUNYA — Persistent Plans & Governed Action (Phase 14, computation-only)
"""
from datetime import datetime, timezone
from typing import Optional

# Plan lifecycle states
class PlanState:
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    REVIEW_REQUIRED = "review_required"

# Action types
class ActionType:
    NOTIFY = "notify"
    SURFACE = "surface"
    ESCALATE = "escalate"
    SCHEDULE = "schedule"
    REVIEW = "review"


class PlanningService:
    """Persistent Plans & Governed Action.

    Consumes Phase 13 Relevance/Attention signals.
    Creates persistent plans, tracks lifecycle, governs action execution.
    Does NOT deliver notifications, execute Phase 14C, or implement Phase 17.
    """

    def __init__(self, phase4_service=None, phase13_service=None):
        self._p4 = phase4_service
        self._p13 = phase13_service
        self._version = "14.1"

    # ------------------------------------------------------------------
    # Plan creation from attention signals
    # ------------------------------------------------------------------
    def create_plan(self, attention_result: dict, context: dict,
                    tenant_id: int = 1, principal_id: Optional[str] = None) -> dict:
        """Create a persistent plan from an attention signal."""
        # Phase 4 current-use revalidation
        if self._p4:
            p4 = self._p4.check_eligibility(attention_result.get("purpose_code", "planning"))
            if not p4.get("eligible", True):
                return self._error("blocked_by_current_use", tenant_id, principal_id)

        # Tenant isolation
        sig_tenant = attention_result.get("tenant_id")
        if sig_tenant is not None and sig_tenant != tenant_id:
            return self._error("tenant_mismatch", tenant_id, principal_id)

        category = attention_result.get("attention_category", "not_relevant")
        reasons = attention_result.get("reasons", [])
        precedence = attention_result.get("precedence_score", 0)

        # Determine plan state from attention category
        if category == "immediate_attention":
            plan_state = PlanState.PROPOSED
            priority = "critical"
        elif category == "attention_worthy":
            plan_state = PlanState.PROPOSED
            priority = "high"
        elif category == "relevant":
            plan_state = PlanState.PROPOSED
            priority = "normal"
        else:
            return self._error("not_relevant_no_plan", tenant_id, principal_id)

        # Determine action type
        action_type = self._determine_action(attention_result)

        plan = {
            "plan_id": hashlib.sha256(f"{tenant_id}:{datetime.now(timezone.utc).isoformat()}:{str(reasons)}".encode()).hexdigest()[:16],
            "tenant_id": tenant_id,
            "state": plan_state,
            "priority": priority,
            "attention_category": category,
            "reasons": reasons,
            "precedence_score": precedence,
            "action_type": action_type,
            "proposed_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": None,
            "completed_at": None,
            "principal_id": principal_id,
            "version": self._version,
        }
        return plan

    def _determine_action(self, attention_result: dict) -> str:
        """Determine the appropriate action type from attention context."""
        category = attention_result.get("attention_category", "")
        reasons = attention_result.get("reasons", [])
        evidence = attention_result.get("evidence", [])

        if category == "immediate_attention":
            return ActionType.ESCALATE
        elif category == "attention_worthy":
            # Check if any reason involves a conflict
            if any("conflict" in r.lower() for r in reasons):
                return ActionType.REVIEW
            return ActionType.SURFACE
        elif category == "relevant":
            return ActionType.SURFACE
        return ActionType.NOTIFY

    # ------------------------------------------------------------------
    # Plan lifecycle
    # ------------------------------------------------------------------
    def approve_plan(self, plan: dict, principal_id: Optional[str] = None) -> dict:
        if plan.get("state") != PlanState.PROPOSED:
            return self._error("cannot_approve_non_proposed", plan.get("tenant_id"), principal_id)
        plan["state"] = PlanState.APPROVED
        plan["approved_at"] = datetime.now(timezone.utc).isoformat()
        return plan

    def reject_plan(self, plan: dict, reason: str = "", principal_id: Optional[str] = None) -> dict:
        if plan.get("state") not in (PlanState.PROPOSED, PlanState.REVIEW_REQUIRED):
            return self._error("cannot_reject_in_current_state", plan.get("tenant_id"), principal_id)
        plan["state"] = PlanState.REJECTED
        plan["rejection_reason"] = reason
        return plan

    def activate_plan(self, plan: dict, principal_id: Optional[str] = None) -> dict:
        if plan.get("state") != PlanState.APPROVED:
            return self._error("cannot_activate_unapproved", plan.get("tenant_id"), principal_id)
        plan["state"] = PlanState.ACTIVE
        return plan

    def complete_plan(self, plan: dict, principal_id: Optional[str] = None) -> dict:
        if plan.get("state") != PlanState.ACTIVE:
            return self._error("cannot_complete_inactive", plan.get("tenant_id"), principal_id)
        plan["state"] = PlanState.COMPLETED
        plan["completed_at"] = datetime.now(timezone.utc).isoformat()
        return plan

    def supersede_plan(self, plan: dict, new_plan_id: str, principal_id: Optional[str] = None) -> dict:
        if plan.get("state") in (PlanState.COMPLETED, PlanState.REJECTED):
            return self._error("cannot_supersede_terminal", plan.get("tenant_id"), principal_id)
        plan["state"] = PlanState.SUPERSEDED
        plan["superseded_by"] = new_plan_id
        return plan

    def request_review(self, plan: dict, principal_id: Optional[str] = None) -> dict:
        if plan.get("state") not in (PlanState.PROPOSED, PlanState.APPROVED):
            return self._error("cannot_request_review", plan.get("tenant_id"), principal_id)
        plan["state"] = PlanState.REVIEW_REQUIRED
        return plan

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------
    def inspect_plan(self, plan: dict) -> dict:
        return {
            "plan_id": plan.get("plan_id"),
            "tenant_id": plan.get("tenant_id"),
            "state": plan.get("state"),
            "priority": plan.get("priority"),
            "attention_category": plan.get("attention_category"),
            "action_type": plan.get("action_type"),
            "proposed_at": plan.get("proposed_at"),
            "approved_at": plan.get("approved_at"),
            "completed_at": plan.get("completed_at"),
        }

    def explain_plan(self, plan: dict) -> dict:
        return {
            "plan_id": plan.get("plan_id"),
            "state": plan.get("state"),
            "reasons": plan.get("reasons", []),
            "precedence_score": plan.get("precedence_score"),
            "why": self._generate_explanation(plan),
        }

    def _generate_explanation(self, plan: dict) -> str:
        reasons = plan.get("reasons", [])
        category = plan.get("attention_category", "unknown")
        if reasons:
            return f"Plan created from {category} because: {'; '.join(reasons[:3])}"
        return f"Plan created from {category} attention signal"

    # ------------------------------------------------------------------
    # Error
    # ------------------------------------------------------------------
    def _error(self, reason: str, tenant_id: int = 1, principal_id: Optional[str] = None) -> dict:
        return {
            "error": reason,
            "tenant_id": tenant_id,
            "principal_id": principal_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


import hashlib