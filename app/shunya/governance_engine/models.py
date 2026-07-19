"""SHUNYA — Governance Engine canonical models (Phase H — ES-001).

Canonical governance data models: immutable representations of governance
inputs, verdicts, policies, audit entries, and supporting types.

Architectural authority: ES-001 — Governance Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ActionType(Enum):
    """Types of actions that can be submitted for governance validation."""
    PLAN = "plan"
    ACTION = "action"
    PROPOSAL_SEND = "proposal_send"
    DATA_MUTATION = "data_mutation"
    FINANCIAL = "financial"


class VerdictDecision(Enum):
    """The three possible governance verdicts."""
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


class PolicySeverity(Enum):
    """Severity of a policy violation."""
    BLOCK = "block"       # Cannot proceed under any circumstances
    WARN = "warn"         # Logged, human notified, can proceed
    REVIEW = "review"     # Requires human approval before proceeding
    PASS = "pass"         # Automatically approved


class PolicyScope(Enum):
    """Scope of a governance policy."""
    GLOBAL = "global"              # Applies to all domains
    DOMAIN = "domain"              # Applies to a specific domain
    ACTION = "action"              # Applies to a specific action type
    ENVIRONMENT = "environment"     # Applies to a specific environment


class GovernanceState(Enum):
    """States of the governance evaluation state machine."""
    IDLE = "idle"
    RECEIVING = "receiving"
    VALIDATING_CONTEXT = "validating_context"
    VALIDATING_CONSTITUTION = "validating_constitution"
    EVALUATING_POLICIES = "evaluating_policies"
    ASSESSING_RISK = "assessing_risk"
    APPROVED = "approved"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"
    ERROR = "error"


class FailureMode(Enum):
    """Failure modes for governance processing."""
    MISSING_EVIDENCE = "missing_evidence"
    UNKNOWN_POLICY_REFERENCE = "unknown_policy_reference"
    INVALID_CONTEXT = "invalid_context"
    POLICY_CONFLICT = "policy_conflict"
    TIMEOUT = "timeout"
    CIRCULAR_POLICY_DEPENDENCY = "circular_policy_dependency"
    CONTEXT_ENRICHMENT_FAILURE = "context_enrichment_failure"
    POLICY_EVALUATION_EXCEPTION = "policy_evaluation_exception"
    CONCURRENT_REGISTRY_MODIFICATION = "concurrent_registry_modification"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


@dataclass
class PolicyViolation:
    """Structured details of a policy violation."""
    policy_name: str
    severity: PolicySeverity
    message: str
    detail: str = ""
    domain: str = ""


@dataclass
class Policy:
    """A single governance policy rule.

    Evaluation is performed by the safe expression evaluator,
    NOT by Python's built-in eval().
    """
    name: str
    description: str
    scope: PolicyScope
    severity: PolicySeverity
    condition: str              # Safe expression evaluated against context
    error_message: str
    domain: str = ""
    action: str = ""
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "scope": self.scope.value,
            "severity": self.severity.value,
            "condition": self.condition,
            "error_message": self.error_message,
            "domain": self.domain,
            "action": self.action,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ContextEnrichment:
    """Computed fields added during context enrichment phase."""
    pax_count: Optional[int] = None
    estimated_cost: float = 0.0
    is_international: bool = False
    is_wedding: bool = False
    lead_time_days: int = 999
    trip_start_date: str = ""
    destination_confidence: float = 0.0


@dataclass
class AuditEntry:
    """An immutable audit record of a governance decision."""
    audit_id: str
    verdict: VerdictDecision
    confidence: float
    action_type: str
    tenant_id: Optional[int]
    domain: str
    policies_evaluated: int
    blocking_policies: List[str]
    warnings: List[str]
    reviews_required: List[str]
    explanation: str
    context_snapshot: Dict[str, Any]
    evaluated_at: datetime
    error_detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "action_type": self.action_type,
            "tenant_id": self.tenant_id,
            "domain": self.domain,
            "policies_evaluated": self.policies_evaluated,
            "blocking_policies": self.blocking_policies,
            "warnings": self.warnings,
            "reviews_required": self.reviews_required,
            "explanation": self.explanation,
            "evaluated_at": self.evaluated_at.isoformat(),
            "error_detail": self.error_detail,
        }


@dataclass
class GovernanceInput:
    """Input contract for governance validation per ES-001 §4."""
    action_type: str               # Must be a valid ActionType
    proposal: Dict[str, Any]       # The plan or action being proposed
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    risk_flags: List[str] = field(default_factory=list)
    user_intent: str = ""
    tenant_id: Optional[int] = None
    actor_id: str = ""
    purpose_code: str = ""
    subject: str = ""
    domain: str = "travel"
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        # Clamp confidence to [0.0, 1.0]
        self.confidence = max(0.0, min(1.0, self.confidence))

    @classmethod
    def from_governance_package(cls, pkg: Any, domain: str = "travel") -> GovernanceInput:
        """Convert a Phase G GovernancePackage to a GovernanceInput."""
        proposal = {}
        if hasattr(pkg, 'plan') and pkg.plan:
            proposal = pkg.plan.to_dict() if hasattr(pkg.plan, 'to_dict') else {}
            if callable(proposal):
                proposal = proposal()

        evidence = []
        if hasattr(pkg, 'evidence_summary') and pkg.evidence_summary:
            evidence_val = pkg.evidence_summary
            evidence = evidence_val if isinstance(evidence_val, list) else [evidence_val]

        return cls(
            action_type=ActionType.PLAN.value,
            proposal=proposal,
            evidence_chain=evidence,
            confidence=getattr(pkg, 'confidence', 0.5) if not isinstance(
                getattr(pkg, 'confidence', 0.5), (int, float)) else getattr(pkg, 'confidence', 0.5),
            tenant_id=getattr(pkg, 'tenant_id', None),
            actor_id=getattr(pkg, 'actor_id', ''),
            domain=domain,
        )


@dataclass
class GovernanceVerdict:
    """Output contract for governance validation per ES-001 §5."""
    approved: bool
    decision: VerdictDecision = VerdictDecision.APPROVE
    confidence: float = 0.0          # 0.0 to 1.0 overall governance confidence
    explanation: str = ""
    blocking_policies: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    reviews_required: List[str] = field(default_factory=list)
    evidence_checked: bool = False
    policy_violations: List[PolicyViolation] = field(default_factory=list)
    required_human_approval: bool = False
    audit_id: str = ""
    evaluated_at: Optional[datetime] = None
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    state: GovernanceState = GovernanceState.IDLE

    def __post_init__(self) -> None:
        if not self.audit_id:
            self.audit_id = str(uuid.uuid4())
        if self.evaluated_at is None:
            self.evaluated_at = datetime.now(timezone.utc)

    @property
    def is_approved(self) -> bool:
        return self.decision == VerdictDecision.APPROVE

    @property
    def is_review_required(self) -> bool:
        return self.decision == VerdictDecision.REVIEW

    @property
    def is_rejected(self) -> bool:
        return self.decision == VerdictDecision.REJECT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "decision": self.decision.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "blocking_policies": self.blocking_policies,
            "warnings": self.warnings,
            "reviews_required": self.reviews_required,
            "evidence_checked": self.evidence_checked,
            "policy_violations": [
                {"policy_name": v.policy_name, "severity": v.severity.value,
                 "message": v.message, "detail": v.detail}
                for v in self.policy_violations
            ],
            "required_human_approval": self.required_human_approval,
            "audit_id": self.audit_id,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }


@dataclass
class PolicyRegistry:
    """Central registry of all governance policies with per-scope lookup."""

    def __init__(self):
        self._policies: Dict[str, Policy] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load built-in default policies (business-agnostic defaults)."""
        defaults = [
            # Budget sanity — global warning
            Policy(
                "budget_sanity",
                "Total estimated cost must not exceed 10x the stated budget",
                PolicyScope.GLOBAL, PolicySeverity.WARN,
                condition=("not has('budget') or not has('estimated_cost') "
                           "or estimated_cost <= float(budget) * 10"),
                error_message="Estimated cost far exceeds stated budget (more than 10x)",
            ),
            # Tenant isolation — block cross-tenant access
            Policy(
                "tenant_isolation",
                "Action must have a valid tenant_id",
                PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                condition="has('tenant_id') and int(tenant_id) > 0",
                error_message="Missing or invalid tenant_id — tenant isolation enforced",
            ),
            # Confidence floor — reject plans below minimum confidence
            Policy(
                "confidence_floor",
                "Governance confidence must meet minimum threshold",
                PolicyScope.GLOBAL, PolicySeverity.REVIEW,
                condition="not has('confidence') or confidence >= 0.3",
                error_message="Governance confidence below minimum threshold (0.3)",
            ),
            # Evidence completeness — warn on missing evidence
            Policy(
                "evidence_completeness",
                "Evidence chain should be present for thorough governance",
                PolicyScope.GLOBAL, PolicySeverity.WARN,
                condition="has('evidence_chain') and len(evidence_chain) > 0",
                error_message="No evidence chain provided — governance confidence reduced",
            ),
            # Action type validation
            Policy(
                "valid_action_type",
                "Action type must be recognized",
                PolicyScope.GLOBAL, PolicySeverity.BLOCK,
                condition=("has('action_type') and action_type in "
                           "['plan', 'action', 'proposal_send', 'data_mutation', 'financial']"),
                error_message="Unrecognized action type",
            ),
            # Constitutional — AI Proposes, Humans Dispose
            Policy(
                "ai_proposes_humans_disposes",
                "Human approval required for high-severity actions involving "
                "data mutation or financial decisions",
                PolicyScope.GLOBAL, PolicySeverity.REVIEW,
                condition=("not has('action_type') or action_type not in "
                           "['data_mutation', 'financial', 'proposal_send']"),
                error_message="This action requires human approval per constitutional principle",
            ),
            # Domain specificity warning
            Policy(
                "domain_known",
                "Action domain must be recognized",
                PolicyScope.GLOBAL, PolicySeverity.WARN,
                condition="has('domain') and domain in ['travel', 'healthcare', 'legal', 'finance', 'education']",
                error_message="Domain not recognized — proceeding with default policies",
            ),
        ]
        for p in defaults:
            self.register(p)

    def register(self, policy: Policy) -> None:
        """Register a new policy."""
        key = f"{policy.scope.value}:{policy.name}"
        self._policies[key] = policy

    def get(self, name: str) -> Optional[Policy]:
        return self._policies.get(name)

    def deregister(self, name: str) -> bool:
        """Remove a policy by its fully-qualified key (scope:name)."""
        if name in self._policies:
            del self._policies[name]
            return True
        return False

    def get_by_scope(self, scope: PolicyScope) -> List[Policy]:
        return [p for p in self._policies.values() if p.scope == scope]

    def get_applicable(self, context: Dict[str, Any]) -> List[Policy]:
        """Get all policies that apply to a given context."""
        domain = context.get("domain", "")
        action = context.get("action_type", "")
        applicable: List[Policy] = []
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

    @property
    def count(self) -> int:
        return len(self._policies)

    def list_policies(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for _, p in sorted(self._policies.items())]


@dataclass
class GovernanceStats:
    """Governance engine statistics."""
    total_decisions: int = 0
    approved: int = 0
    rejected: int = 0
    review_required: int = 0
    errors: int = 0
    avg_confidence: float = 0.0
    policies_registered: int = 0

    def to_dict(self) -> Dict[str, Any]:
        total = self.total_decisions or 1
        return {
            "total_decisions": self.total_decisions,
            "approved": self.approved,
            "rejected": self.rejected,
            "review_required": self.review_required,
            "errors": self.errors,
            "approval_rate": round(self.approved / total * 100, 1),
            "rejection_rate": round(self.rejected / total * 100, 1),
            "avg_confidence": round(self.avg_confidence, 2),
            "policies_registered": self.policies_registered,
        }