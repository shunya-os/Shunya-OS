"""
SHUNYA — Decision Engine Models

Defines the decision lifecycle states, policy rule types, decision option
structures, and evidence sufficiency contracts for the Decision Engine.

Implements the Decision lifecycle defined in:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §9 (Decision Engine)
    - docs/canon/07_ai_canon.md §10 (Executive Engine)

Lifecycle:
    CANDIDATE ──► POLICY_EVALUATION ──► UNDER_REVIEW ──► APPROVED
        │               │                    │               │
        ▼               ▼                    ▼               ▼
    REJECTED       BLOCKED              SENT_BACK       EXECUTING
                                                            │
                                                            ▼
                                                       COMPLETED
                                                            │
                                                            ▼
                                                       FAILED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ── Timestamp helper ───────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── DecisionStatus ─────────────────────────────────────────────────────────────


class DecisionStatus(str, Enum):
    """Lifecycle states for a decision in the SHUNYA system.

    Every decision progresses through a defined lifecycle from proposal
    through evaluation, approval, execution, and completion. Transitions
    are validated at each step.
    """

    CANDIDATE = "candidate"
    """Decision has been proposed but not yet processed."""

    POLICY_EVALUATION = "policy_evaluation"
    """Decision is being evaluated against policy rules."""

    UNDER_REVIEW = "under_review"
    """Decision is under human review."""

    APPROVED = "approved"
    """Decision has been approved and is ready for execution."""

    EXECUTING = "executing"
    """Decision is currently being executed."""

    COMPLETED = "completed"
    """Decision was executed successfully."""

    FAILED = "failed"
    """Decision execution failed."""

    REJECTED = "rejected"
    """Decision was rejected during evaluation/review."""

    BLOCKED = "blocked"
    """Decision was blocked by a policy rule."""

    SENT_BACK = "sent_back"
    """Decision was returned for revision during review."""

    @classmethod
    def from_string(cls, value: str) -> DecisionStatus:
        """Convert a string to a DecisionStatus.

        Args:
            value: The string representation.

        Returns:
            The matching DecisionStatus.

        Raises:
            ValueError: If the string does not match any known status.
        """
        return cls(value)


# ── Valid transitions map ──────────────────────────────────────────────────────


DECISION_VALID_TRANSITIONS: dict[DecisionStatus, list[DecisionStatus]] = {
    DecisionStatus.CANDIDATE: [
        DecisionStatus.POLICY_EVALUATION,
        DecisionStatus.REJECTED,
    ],
    DecisionStatus.POLICY_EVALUATION: [
        DecisionStatus.UNDER_REVIEW,
        DecisionStatus.BLOCKED,
        DecisionStatus.REJECTED,
    ],
    DecisionStatus.UNDER_REVIEW: [
        DecisionStatus.APPROVED,
        DecisionStatus.SENT_BACK,
        DecisionStatus.REJECTED,
    ],
    DecisionStatus.APPROVED: [
        DecisionStatus.EXECUTING,
        DecisionStatus.REJECTED,
    ],
    DecisionStatus.EXECUTING: [
        DecisionStatus.COMPLETED,
        DecisionStatus.FAILED,
    ],
    DecisionStatus.COMPLETED: [],
    DecisionStatus.FAILED: [],
    DecisionStatus.REJECTED: [],
    DecisionStatus.BLOCKED: [],
    DecisionStatus.SENT_BACK: [
        DecisionStatus.CANDIDATE,
        DecisionStatus.REJECTED,
    ],
}
"""Map of valid lifecycle transitions for decisions.

Key: current DecisionStatus
Value: list of allowed target DecisionStatus values.
"""


# ── PolicyRule ─────────────────────────────────────────────────────────────────


@dataclass
class PolicyRule:
    """A deterministic policy rule for evaluating decisions.

    Rules are evaluated in order. The first matching rule determines
    the result. Rules have the following semantics:
        - ALLOW rules: decision proceeds if condition is met.
        - BLOCK rules: decision is blocked if condition is met.
        - REQUIRE_EVIDENCE rules: decision requires minimum evidence.
        - REQUIRE_APPROVAL rules: decision requires human approval.
    """

    rule_id: str = ""
    """Unique identifier for this rule."""

    name: str = ""
    """Human-readable name of the rule."""

    rule_type: str = "allow"
    """Type of rule: 'allow', 'block', 'require_evidence', 'require_approval'."""

    condition: dict[str, Any] = field(default_factory=dict)
    """Condition expression dict evaluated against the decision payload.

    Example: {'field': 'amount', 'operator': '>', 'value': 10000}
    """

    priority: int = 0
    """Evaluation priority (lower = evaluated first)."""

    reason: str = ""
    """Human-readable explanation of why this rule exists."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible metadata for this rule."""


PolicyRuleResult = tuple[bool, str]
"""Result of a policy rule evaluation.

Returns (passed, reason) where:
    - passed: True if the rule allows the decision, False if blocked.
    - reason: Human-readable explanation of the result.
"""


# ── DecisionOption ─────────────────────────────────────────────────────────────


@dataclass
class DecisionOption:
    """A single decision option with trade-off analysis.

    Options represent alternative courses of action for a decision.
    Each option includes expected outcomes, risks, and a confidence score.
    """

    option_id: str = ""
    """Unique identifier for this option."""

    label: str = ""
    """Short label describing this option."""

    description: str = ""
    """Detailed description of what this option entails."""

    expected_outcome: dict[str, Any] = field(default_factory=dict)
    """Predicted outcome if this option is selected."""

    risks: list[dict[str, Any]] = field(default_factory=list)
    """List of identified risks for this option.

    Each risk: {'description': str, 'severity': 'low'|'medium'|'high',
                'probability': float [0,1]}
    """

    confidence: float = 0.0
    """Confidence in this option's expected outcome [0.0, 1.0]."""

    trade_offs: dict[str, str] = field(default_factory=dict)
    """Key trade-offs associated with this option.

    Example: {'speed': 'fast execution, higher cost',
              'quality': 'high quality, longer timeline'}
    """

    ai_generated: bool = False
    """Whether this option was generated by AI (True) or deterministic (False)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible metadata for this option."""


# ── EvidenceRequirement ────────────────────────────────────────────────────────


@dataclass
class EvidenceSufficiency:
    """Defines the evidence requirements for a decision.

    Determines whether enough evidence exists to proceed with a decision
    through its lifecycle.
    """

    minimum_evidence_count: int = 1
    """Minimum number of evidence records required."""

    minimum_confidence: float = 0.0
    """Minimum aggregate confidence required from evidence [0.0, 1.0]."""

    required_types: list[str] = field(default_factory=list)
    """Specific evidence types that must be present.

    Example: ['measurement', 'confirmation']
    """

    satisfied: bool = False
    """Whether the evidence sufficiency requirements are met."""

    reason: str = ""
    """Human-readable explanation of sufficiency or deficiency."""


# ── DecisionRecord ─────────────────────────────────────────────────────────────


@dataclass
class DecisionRecord:
    """A complete record of a decision through its lifecycle.

    This is the primary data structure for the Decision Engine. Every
    decision that enters the system creates a DecisionRecord that is
    updated as it progresses through the lifecycle.
    """

    decision_id: str = ""
    """Globally unique identifier for this decision (UUID v7)."""

    label: str = ""
    """Short human-readable label for this decision."""

    description: str = ""
    """Detailed description of what this decision is about."""

    status: DecisionStatus = DecisionStatus.CANDIDATE
    """Current lifecycle status."""

    options: list[DecisionOption] = field(default_factory=list)
    """Available decision options."""

    selected_option: DecisionOption | None = None
    """The option that was selected for execution."""

    owner: str = ""
    """ObjectID of the actor that owns this decision."""

    created_by: str = ""
    """ObjectID of the actor that created this decision."""

    actor_id: str = ""
    """ObjectID of the actor currently responsible for this decision."""

    policy_rule_results: list[dict[str, Any]] = field(default_factory=list)
    """Results of policy rule evaluations.

    Each entry: {'rule_id': str, 'rule_name': str, 'passed': bool,
                 'reason': str}
    """

    evidence_ids: list[str] = field(default_factory=list)
    """Evidence references supporting this decision."""

    evidence_sufficiency: EvidenceSufficiency | None = None
    """Evidence sufficiency assessment (None = not yet assessed)."""

    confidence: float = 0.0
    """Overall confidence in this decision [0.0, 1.0]."""

    confidence_factors: dict[str, float] = field(default_factory=dict)
    """Breakdown of confidence computation components."""

    context: dict[str, Any] = field(default_factory=dict)
    """Assembled context that informed this decision."""

    payload: dict[str, Any] = field(default_factory=dict)
    """Arbitrary payload data attached to this decision."""

    trace_id: str = ""
    """Correlation ID for tracing across the intelligence runtime."""

    escalation_used: bool = False
    """Whether AI-assisted escalation was used during decision-making."""

    status_history: list[dict[str, Any]] = field(default_factory=list)
    """Chronological history of status transitions.

    Each entry: {'from_status': str, 'to_status': str, 'timestamp': str,
                 'actor_id': str, 'reason': str}
    """

    created_at: str = field(default_factory=_now_iso)
    """ISO-8601 timestamp of when the decision was created."""

    updated_at: str = field(default_factory=_now_iso)
    """ISO-8601 timestamp of the last update."""

    completed_at: str | None = None
    """ISO-8601 timestamp of when the decision was completed/failed."""

    decision_type: str = "standard"
    """Type of decision (e.g., 'standard', 'emergency', 'auto')."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extensible metadata container."""

    def __post_init__(self) -> None:
        """Auto-generate ID and timestamps if missing."""
        if not self.decision_id:
            from core.kernel.types import generate_uuid7
            object.__setattr__(self, "decision_id", generate_uuid7())

    def add_status_history(
        self,
        from_status: str,
        to_status: str,
        actor_id: str,
        reason: str,
    ) -> None:
        """Append a status transition to the history.

        Args:
            from_status: Previous status string.
            to_status: New status string.
            actor_id: Actor that triggered the transition.
            reason: Reason for the transition.
        """
        entry: dict[str, Any] = {
            "from_status": from_status,
            "to_status": to_status,
            "timestamp": _now_iso(),
            "actor_id": actor_id,
            "reason": reason,
        }
        self.status_history.append(entry)
        object.__setattr__(self, "updated_at", _now_iso())


# ── Escalation Request ──────────────────────────────────────────────────────────


@dataclass
class DecisionEscalationRequest:
    """Data for escalating a decision to an external AI inference provider.

    When deterministic evaluation yields confidence below threshold,
    this structure captures the context needed for AI-assisted
    processing (e.g., option generation, trade-off analysis).
    """

    decision_id: str = ""
    """The decision that triggered escalation."""

    input_type: str = "decision_escalation"
    """Type of escalation request."""

    prompt: str = ""
    """The prompt to send to the AI provider."""

    context: dict[str, Any] = field(default_factory=dict)
    """Assembled context for the AI provider."""

    trace_id: str = ""
    """Correlation ID for tracing."""

    request_type: str = "option_generation"
    """Type of AI assistance requested:

    - 'option_generation': Generate decision options.
    - 'trade_off_analysis': Analyze trade-offs between options.
    - 'risk_assessment': Assess risks of an option."""