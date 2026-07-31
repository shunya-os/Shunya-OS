"""SHUNYA — Governance Engine (Phase H — ES-001).

The Governance Engine is the independent validation gate between Planning
and Execution. Every proposed action must pass through governance before
reaching the Executor.

The engine implements a deterministic 6-stage pipeline:
  1. Input Validation
  2. Context Enrichment
  3. Constitutional Validation
  4. Policy Evaluation
  5. Risk Assessment
  6. Verdict Production

Architectural authority: ES-001 — Governance Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.shunya.governance_engine.models import (
    ActionType, VerdictDecision, PolicySeverity, PolicyScope,
    GovernanceState, FailureMode,
    Policy, PolicyRegistry, PolicyViolation,
    GovernanceInput, GovernanceVerdict,
    ContextEnrichment, AuditEntry, GovernanceStats,
)
from app.shunya.governance_engine.evaluator import safe_eval_bool


# ---------------------------------------------------------------------------
# Constitutional Rules (hard-coded, cannot be overridden by business policies)
# ---------------------------------------------------------------------------

_CONSTITUTIONAL_RULES: List[Dict[str, Any]] = [
    {
        "name": "governance_before_execution",
        "principle": "No action may execute without governance approval",
        "check": lambda ctx: True,  # Always satisfied (the engine itself enforces this)
        "severity": "critical",
    },
    {
        "name": "ai_proposes_humans_disposes",
        "principle": "Financial and data mutation actions require human approval",
        "check": lambda ctx: ctx.get("action_type", "") not in ("data_mutation", "financial"),
        "severity": "review",  # REVIEW, not SEVERE — these need human approval not outright rejection
    },
    {
        "name": "separation_of_responsibilities",
        "principle": "Governance Engine never executes actions",
        "check": lambda ctx: True,  # Enforced by architectural boundary
        "severity": "critical",
    },
    {
        "name": "tenant_isolation_constitutional",
        "principle": "All actions must be scoped to a valid tenant",
        "check": lambda ctx: ctx.get("tenant_id") is not None and int(ctx.get("tenant_id", 0)) > 0,
        "severity": "critical",
    },
]


# ---------------------------------------------------------------------------
# Governance Engine
# ---------------------------------------------------------------------------


class GovernanceEngine:
    """Governance Engine — validates proposals against policies and constitution.

    Implements a deterministic 6-stage pipeline per ES-001.
    """

    def __init__(self) -> None:
        self.policies = PolicyRegistry()
        self._audit_log: List[AuditEntry] = []
        self._stats = GovernanceStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, gov_input: GovernanceInput) -> GovernanceVerdict:
        """Evaluate a governance input against policies and constitution.

        Implements the full 6-stage deterministic pipeline.
        """
        audit_id = str(uuid.uuid4())
        context = _input_to_context(gov_input)

        # Stage 0: Input Validation
        validation_result = self._validate_input(gov_input, context)
        if validation_result is not None:
            return self._finalize_verdict(validation_result, context, audit_id)

        # Stage 1: Context Enrichment
        enrichment = self._enrich_context(context)
        context["_enrichment"] = enrichment

        # Stage 2: Constitutional Validation
        constitutional_result = self._validate_constitution(context)
        if constitutional_result is not None:
            return self._finalize_verdict(constitutional_result, context, audit_id)

        # Stage 3: Policy Evaluation
        policy_result = self._evaluate_policies(context)
        if isinstance(policy_result, GovernanceVerdict):
            return self._finalize_verdict(policy_result, context, audit_id)

        # Stage 4: Risk Assessment
        risk_result = self._assess_risk(context, policy_result)
        if risk_result is not None:
            # If risk assessment decides to stop (e.g., high risk returns dict with decision)
            # it returns a dict; we proceed to verdict production
            pass

        # Stage 5: Verdict Production
        verdict = self._produce_verdict(context, risk_result, audit_id)
        return self._finalize_verdict(verdict, context, audit_id)

    def evaluate_plan(self, plan: Dict[str, Any],
                      context: Optional[Dict[str, Any]] = None,
                      domain: str = "travel") -> GovernanceVerdict:
        """Convenience method: evaluate a plan dict with optional context."""
        merged = {**(context or {}), **plan}
        merged.setdefault("domain", domain)
        merged.setdefault("action_type", ActionType.PLAN.value)
        gov_input = GovernanceInput(
            action_type=merged.get("action_type", "plan"),
            proposal=plan,
            evidence_chain=merged.get("evidence_chain", []),
            confidence=float(merged.get("confidence", 0.5)),
            tenant_id=merged.get("tenant_id"),
            actor_id=merged.get("actor_id", ""),
            domain=merged.get("domain", domain),
        )
        return self.evaluate(gov_input)

    def evaluate_action(self, action: str, payload: Dict[str, Any],
                        context: Optional[Dict[str, Any]] = None) -> GovernanceVerdict:
        """Convenience method: evaluate a single action."""
        merged = {**(context or {}), **payload, "action_type": action}
        gov_input = GovernanceInput(
            action_type=action,
            proposal=payload,
            tenant_id=merged.get("tenant_id"),
            actor_id=merged.get("actor_id", ""),
            domain=merged.get("domain", "travel"),
        )
        return self.evaluate(gov_input)

    # ------------------------------------------------------------------
    # Pipeline Stages
    # ------------------------------------------------------------------

    def _validate_input(self, gov_input: GovernanceInput,
                        context: Dict[str, Any]) -> Optional[GovernanceVerdict]:
        """Stage 0: Validate input structure and required fields."""
        # Validate action_type
        try:
            ActionType(gov_input.action_type)
        except (ValueError, KeyError):
            return self._make_error_verdict(
                f"Invalid action_type: '{gov_input.action_type}'. "
                f"Must be one of: {[a.value for a in ActionType]}",
                FailureMode.INVALID_CONTEXT.value,
            )

        # Validate proposal
        if not gov_input.proposal:
            return self._make_error_verdict(
                "Empty proposal — proposal must be a non-empty dict",
                FailureMode.INVALID_CONTEXT.value,
            )

        # Validate tenant_id
        if gov_input.tenant_id is None or int(gov_input.tenant_id) <= 0:
            return self._make_error_verdict(
                "Missing or invalid tenant_id",
                FailureMode.INVALID_CONTEXT.value,
            )

        # Validate domain
        known_domains = {"travel", "healthcare", "legal", "finance", "education", "general"}
        if gov_input.domain not in known_domains:
            # Domain warning — not blocking
            context["_domain_warning"] = True

        return None  # Validation passed

    def _enrich_context(self, context: Dict[str, Any]) -> ContextEnrichment:
        """Stage 1: Enrich context with computed fields."""
        enrichment = ContextEnrichment()

        # Pax count
        pax_raw = context.get("pax", context.get("pax_count", ""))
        if isinstance(pax_raw, (int, float)):
            enrichment.pax_count = int(pax_raw)
        elif isinstance(pax_raw, str):
            nums = [int(s) for s in pax_raw.split() if s.isdigit()]
            enrichment.pax_count = nums[0] if nums else None

        # Estimated cost
        daily = context.get("daily_budget_per_person", context.get("budget_estimate", 0))
        days = context.get("itinerary_days", context.get("duration_days", 0))
        pax = enrichment.pax_count or 1
        try:
            enrichment.estimated_cost = float(daily or 0) * int(days or 1) * int(pax or 1)
        except (TypeError, ValueError):
            enrichment.estimated_cost = 0.0

        # International check
        dest = str(context.get("destination", "")).lower()
        domestic_places = {
            "goa", "kerala", "udaipur", "manali", "shimla",
            "andaman", "jaipur", "delhi", "mumbai", "bengaluru",
            "chennai", "kolkata", "hyderabad", "pune", "agra",
        }
        enrichment.is_international = dest not in domestic_places and bool(dest)

        # Wedding check
        notes = str(context.get("notes", "")).lower()
        enrichment.is_wedding = "wedding" in notes or context.get("occasion") == "wedding"

        # Lead time
        dates_str = str(context.get("dates", ""))
        enrichment.lead_time_days = self._estimate_lead_time(dates_str)
        enrichment.trip_start_date = self._extract_start_date(dates_str)

        # Destination confidence
        enrichment.destination_confidence = float(context.get("destination_confidence", 0.0))

        # Write enrichment fields into context for policy evaluation
        context["pax_count"] = enrichment.pax_count
        context["estimated_cost"] = enrichment.estimated_cost
        context["is_international"] = enrichment.is_international
        context["is_wedding"] = enrichment.is_wedding
        context["lead_time_days"] = enrichment.lead_time_days
        context["trip_start_date"] = enrichment.trip_start_date
        context["destination_confidence"] = enrichment.destination_confidence

        return enrichment

    def _validate_constitution(self, context: Dict[str, Any]) -> Optional[GovernanceVerdict]:
        """Stage 2: Validate constitutional compliance.

        Distinguishes between:
        - Critical violations → REJECT (e.g., missing tenant)
        - Review violations → REVIEW (e.g., action types requiring human approval)
        """
        critical_violations: List[str] = []
        review_violations: List[str] = []
        for rule in _CONSTITUTIONAL_RULES:
            try:
                passed = rule["check"](context)
                if not passed:
                    entry = f"[{rule['severity']}] {rule['name']}: {rule['principle']}"
                    if rule["severity"] == "review":
                        review_violations.append(entry)
                    else:
                        critical_violations.append(entry)
            except Exception:
                entry = f"[{rule['severity']}] {rule['name']}: evaluation error"
                if rule["severity"] == "review":
                    review_violations.append(entry)
                else:
                    critical_violations.append(entry)

        # Critical violations → REJECT
        if critical_violations:
            return GovernanceVerdict(
                approved=False,
                decision=VerdictDecision.REJECT,
                confidence=0.0,
                explanation="Constitutional violations: " + "; ".join(critical_violations),
                blocking_policies=critical_violations,
                evidence_checked=bool(context.get("evidence_chain")),
            )

        # Review violations → REVIEW (human approval required)
        if review_violations:
            return GovernanceVerdict(
                approved=False,
                decision=VerdictDecision.REVIEW,
                confidence=0.0,
                explanation="Human review required: " + "; ".join(review_violations),
                reviews_required=review_violations,
                required_human_approval=True,
                evidence_checked=bool(context.get("evidence_chain")),
            )

        return None  # Constitution passed

    def _evaluate_policies(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Stage 3: Evaluate all applicable policies.

        Returns a dict with policy results, or a GovernanceVerdict if a
        blocking policy is found.
        """
        applicable = self.policies.get_applicable(context)
        blocking: List[str] = []
        warnings: List[str] = []
        reviews: List[str] = []
        violations: List[PolicyViolation] = []

        for policy in applicable:
            try:
                passed = safe_eval_bool(policy.condition, context)
                if not passed:
                    entry = f"[{policy.severity.value}] {policy.name}: {policy.error_message}"
                    violations.append(PolicyViolation(
                        policy_name=policy.name,
                        severity=policy.severity,
                        message=policy.error_message,
                        domain=policy.domain,
                    ))
                    if policy.severity == PolicySeverity.BLOCK:
                        blocking.append(entry)
                    elif policy.severity == PolicySeverity.WARN:
                        warnings.append(entry)
                    elif policy.severity == PolicySeverity.REVIEW:
                        reviews.append(entry)
            except Exception as e:
                entry = f"[error] {policy.name}: Policy evaluation error: {e}"
                blocking.append(entry)
                violations.append(PolicyViolation(
                    policy_name=policy.name,
                    severity=PolicySeverity.BLOCK,
                    message=f"Policy evaluation error: {e}",
                    domain=policy.domain,
                ))

        # Check for blocking policies
        if blocking:
            return GovernanceVerdict(
                approved=False,
                decision=VerdictDecision.REJECT,
                confidence=0.0,
                explanation="Blocking policies: " + "; ".join(blocking),
                blocking_policies=blocking,
                warnings=warnings,
                reviews_required=reviews,
                policy_violations=violations,
                evidence_checked=bool(context.get("evidence_chain")),
            )

        # Check for review-required policies
        if reviews:
            return GovernanceVerdict(
                approved=False,
                decision=VerdictDecision.REVIEW,
                confidence=0.0,
                explanation="Human review required: " + "; ".join(reviews),
                blocking_policies=blocking,
                warnings=warnings,
                reviews_required=reviews,
                policy_violations=violations,
                required_human_approval=True,
                evidence_checked=bool(context.get("evidence_chain")),
            )

        # Return results for risk assessment
        return {
            "applicable_count": len(applicable),
            "blocking": blocking,
            "warnings": warnings,
            "reviews": reviews,
            "violations": violations,
        }

    def _assess_risk(self, context: Dict[str, Any],
                     policy_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Stage 4: Assess overall risk from policy results and confidence."""
        if policy_result is None:
            policy_result = {
                "applicable_count": 0,
                "blocking": [], "warnings": [], "reviews": [], "violations": [],
            }

        applicable_count = policy_result.get("applicable_count", 0) or 1
        warn_count = len(policy_result.get("warnings", []))
        review_count = len(policy_result.get("reviews", []))

        # Base risk: ratio of non-passing policies
        non_passing = warn_count + review_count
        policy_risk = non_passing / applicable_count

        # Confidence factor: lower input confidence = higher risk
        input_confidence = float(context.get("confidence", 0.5))
        confidence_risk = 1.0 - input_confidence

        # Evidence factor: missing evidence = higher risk
        evidence = context.get("evidence_chain", [])
        evidence_risk = 0.0 if evidence else 0.2

        # Composite risk score
        risk_score = (policy_risk * 0.5) + (confidence_risk * 0.3) + (evidence_risk * 0.2)
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine verdict from risk
        if risk_score < 0.3:
            return {
                "risk_score": risk_score,
                "decision": VerdictDecision.APPROVE,
                "explanation": f"Risk score {risk_score:.2f} — low risk, approved",
                "warnings": policy_result.get("warnings", []),
                "reviews": policy_result.get("reviews", []),
                "violations": policy_result.get("violations", []),
                "blocking": policy_result.get("blocking", []),
            }
        elif risk_score < 0.7:
            return {
                "risk_score": risk_score,
                "decision": VerdictDecision.REVIEW,
                "explanation": f"Risk score {risk_score:.2f} — medium risk, human review required",
                "warnings": policy_result.get("warnings", []),
                "reviews": policy_result.get("reviews", []),
                "violations": policy_result.get("violations", []),
                "blocking": policy_result.get("blocking", []),
            }
        else:
            return {
                "risk_score": risk_score,
                "decision": VerdictDecision.REJECT,
                "explanation": f"Risk score {risk_score:.2f} — high risk, rejected",
                "warnings": policy_result.get("warnings", []),
                "reviews": policy_result.get("reviews", []),
                "violations": policy_result.get("violations", []),
                "blocking": policy_result.get("blocking", []),
            }

    def _produce_verdict(self, context: Dict[str, Any],
                         risk_result: Dict[str, Any],
                         audit_id: str) -> GovernanceVerdict:
        """Stage 5: Produce the final verdict."""
        decision = risk_result.get("decision", VerdictDecision.APPROVE)
        risk_score = risk_result.get("risk_score", 0.0)

        # Gather policy results from risk_result (forwarded from policy evaluation)
        warnings: List[str] = risk_result.get("warnings", [])
        reviews: List[str] = risk_result.get("reviews", [])
        violations: List[PolicyViolation] = risk_result.get("violations", [])
        blocking: List[str] = risk_result.get("blocking", [])

        # Confidence: 1.0 - risk_score
        confidence = 1.0 - risk_score

        is_approved = decision == VerdictDecision.APPROVE
        required_human = decision == VerdictDecision.REVIEW

        return GovernanceVerdict(
            approved=is_approved,
            decision=decision,
            confidence=confidence,
            explanation=risk_result.get("explanation", ""),
            blocking_policies=blocking,
            warnings=warnings,
            reviews_required=reviews,
            evidence_checked=bool(context.get("evidence_chain")),
            policy_violations=violations,
            required_human_approval=required_human,
            audit_id=audit_id,
            context_snapshot=_sanitize_context(context),
            state=GovernanceState.APPROVED if is_approved
            else GovernanceState.REVIEW_REQUIRED if required_human
            else GovernanceState.REJECTED,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _finalize_verdict(self, verdict: GovernanceVerdict,
                          context: Dict[str, Any],
                          audit_id: str) -> GovernanceVerdict:
        """Record the verdict in the audit log and update stats."""
        # Always use the audit_id from the caller, not the one auto-generated in __post_init__
        verdict.audit_id = audit_id

        entry = AuditEntry(
            audit_id=audit_id,
            verdict=verdict.decision,
            confidence=verdict.confidence,
            action_type=context.get("action_type", "unknown"),
            tenant_id=context.get("tenant_id"),
            domain=context.get("domain", "travel"),
            policies_evaluated=len(verdict.blocking_policies)
            + len(verdict.warnings) + len(verdict.reviews_required),
            blocking_policies=verdict.blocking_policies,
            warnings=verdict.warnings,
            reviews_required=verdict.reviews_required,
            explanation=verdict.explanation,
            context_snapshot=_sanitize_context(context),
            evaluated_at=datetime.now(timezone.utc),
        )
        self._audit_log.append(entry)

        # Update stats
        self._stats.total_decisions += 1
        if verdict.decision == VerdictDecision.APPROVE:
            self._stats.approved += 1
        elif verdict.decision == VerdictDecision.REJECT:
            self._stats.rejected += 1
        elif verdict.decision == VerdictDecision.REVIEW:
            self._stats.review_required += 1
        if verdict.decision == VerdictDecision.REJECT and not verdict.blocking_policies:
            self._stats.errors += 1
        self._stats.policies_registered = self.policies.count
        self._stats.avg_confidence = (
            (self._stats.avg_confidence * (self._stats.total_decisions - 1) + verdict.confidence)
            / self._stats.total_decisions
        )

        return verdict

    def _make_error_verdict(self, explanation: str, error_type: str) -> GovernanceVerdict:
        """Create an error verdict for failed validation."""
        return GovernanceVerdict(
            approved=False,
            decision=VerdictDecision.REJECT,
            confidence=0.0,
            explanation=explanation,
            blocking_policies=[f"[error] {error_type}: {explanation}"],
            state=GovernanceState.ERROR,
        )

    def _estimate_lead_time(self, dates_str: str) -> int:
        """Estimate lead time in days from date string."""
        if not dates_str:
            return 999
        try:
            raw = dates_str.replace("to", "-").replace("till", "-").split("-")
            first_date = raw[0].strip() if raw else ""
            for fmt in ("%d %b %Y", "%d %B %Y", "%d %b", "%d %B",
                        "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    d = datetime.strptime(first_date, fmt)
                    return (d - datetime.now(timezone.utc)).days
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

    # ------------------------------------------------------------------
    # Audit Log
    # ------------------------------------------------------------------

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent governance audit entries."""
        return [e.to_dict() for e in reversed(self._audit_log[-limit:])]

    def get_audit_entry(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific audit entry by ID."""
        for entry in self._audit_log:
            if entry.audit_id == audit_id:
                return entry.to_dict()
        return None

    # ------------------------------------------------------------------
    # Policy Management
    # ------------------------------------------------------------------

    def register_policy(self, policy: Policy) -> None:
        """Register a policy in the registry."""
        self.policies.register(policy)

    def deregister_policy(self, name: str) -> bool:
        """Deregister a policy by its fully-qualified key."""
        return self.policies.deregister(name)

    def list_policies(self) -> List[Dict[str, Any]]:
        """List all registered policies."""
        return self.policies.list_policies()

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @property
    def stats(self) -> Dict[str, Any]:
        """Return governance engine statistics."""
        return self._stats.to_dict()

    @property
    def audit_log_size(self) -> int:
        """Return the number of audit log entries."""
        return len(self._audit_log)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_ENGINE_INSTANCE: Optional[GovernanceEngine] = None


def get_governance_engine() -> GovernanceEngine:
    """Get or create the singleton GovernanceEngine instance."""
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = GovernanceEngine()
    return _ENGINE_INSTANCE


def reset_governance_engine() -> None:
    """Reset the singleton GovernanceEngine (for testing)."""
    global _ENGINE_INSTANCE
    _ENGINE_INSTANCE = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _input_to_context(gov_input: GovernanceInput) -> Dict[str, Any]:
    """Convert a GovernanceInput to the internal context dict."""
    context: Dict[str, Any] = {
        "action_type": gov_input.action_type,
        "proposal": gov_input.proposal,
        "evidence_chain": gov_input.evidence_chain,
        "confidence": gov_input.confidence,
        "risk_flags": gov_input.risk_flags,
        "user_intent": gov_input.user_intent,
        "tenant_id": gov_input.tenant_id,
        "actor_id": gov_input.actor_id,
        "purpose_code": gov_input.purpose_code,
        "subject": gov_input.subject,
        "domain": gov_input.domain,
        "timestamp": gov_input.timestamp,
    }
    # Merge proposal fields into the top-level context for policy evaluation
    if isinstance(gov_input.proposal, dict):
        for k, v in gov_input.proposal.items():
            if k not in context or context[k] is None:
                context[k] = v
    return context


def _sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a sanitized snapshot of context for the audit log."""
    snapshot = dict(context)
    # Remove internal keys
    for key in list(snapshot.keys()):
        if key.startswith("_"):
            del snapshot[key]
    # Remove large objects
    if "proposal" in snapshot and isinstance(snapshot["proposal"], dict):
        snapshot["proposal_keys"] = list(snapshot["proposal"].keys())
        del snapshot["proposal"]
    return snapshot