"""
SHUNYA — Decision Engine

Manages the complete decision lifecycle: from candidate decision through
policy evaluation, human review, approval, execution, and outcome capture.
The Decision Engine is deterministic for lifecycle management, policy
evaluation, and evidence validation. AI assistance is only used for
option generation and trade-off analysis via escalation.

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

Deterministic work:
    - Policy rule evaluation
    - Valid transition enforcement
    - Permission checking via UniversalObject ACL
    - Evidence sufficiency validation

AI-assisted work (via escalate):
    - Decision option generation
    - Trade-off analysis
    - Risk assessment text

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §9 (Decision Engine)
    - docs/canon/07_ai_canon.md §10 (Executive Engine)
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from core.intelligence.decision.models import (
    DECISION_VALID_TRANSITIONS,
    DecisionOption,
    DecisionRecord,
    DecisionStatus,
    EvidenceSufficiency,
    PolicyRule,
    _now_iso,
)
from core.intelligence.models import (
    EngineInput,
    EngineOutput,
    EscalationResult,
)

logger = logging.getLogger(__name__)


# ── IntelligenceEngine ABC ──────────────────────────────────────────────────────


class IntelligenceEngine(ABC):
    """Abstract base class for all Intelligence Engines in SHUNYA.

    Every engine in the Intelligence Runtime implements this interface,
    providing deterministic processing with optional AI-assisted escalation
    when confidence falls below the configured threshold.
    """

    engine_id: str
    engine_type: str

    @abstractmethod
    async def process(self, input: EngineInput) -> EngineOutput:
        """Process an input and return output.

        Always deterministic unless escalation is triggered, in which
        case process() calls escalate() to bridge to an external AI.
        """

    @abstractmethod
    def escalate(self, input: EngineInput) -> EscalationResult:
        """Bridge to external AI inference.

        Called when deterministic computation yields confidence below
        the engine's configured threshold. Returns the data structure
        that would be sent to an AI provider.
        """

    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """Return list of capability strings describing this engine."""

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Return engine health status."""


# ── DecisionEngine ──────────────────────────────────────────────────────────────


class DecisionEngine(IntelligenceEngine):
    """Manages the complete decision lifecycle in the SHUNYA system.

    The Decision Engine is the only engine that can create, transition,
    and track decisions through their full lifecycle. It integrates with:
        - core/event/ for decision lifecycle events
        - core/evidence/ for evidence validation
        - UniversalObject for permission checking

    The engine is deterministic for lifecycle management and policy
    evaluation. AI-assisted escalation is used only for option generation
    and trade-off analysis when confidence is below the threshold.

    Example::

        engine = DecisionEngine()

        # Create a decision
        result = await engine.process(EngineInput(
            input_type="create_decision",
            payload={
                "label": "Approve vendor payment",
                "description": "Should we pay vendor ACME Corp $50,000?",
                "owner": "user_123",
                "created_by": "user_123",
            },
        ))

        # Evaluate against policy
        engine.add_policy_rule(PolicyRule(
            name="amount_threshold",
            rule_type="block",
            condition={"field": "amount", "operator": ">", "value": 100000},
            reason="Block payments over $100K",
        ))
        result = await engine.process(EngineInput(
            input_type="evaluate_policy",
            payload={"decision_id": result.payload["decision_id"]},
        ))

        # Transition through lifecycle
        result = engine.transition(
            decision_id=result.payload["decision_id"],
            target_status=DecisionStatus.APPROVED,
            actor_id="user_123",
            reason="Approved by finance lead",
        )
    """

    # ── Engine identity ──────────────────────────────────────────────────────

    engine_id: str = "decision_engine"
    engine_type: str = "decision"
    _DEFAULT_CONFIDENCE_THRESHOLD: float = 0.80

    # ── Constructor ──────────────────────────────────────────────────────────

    def __init__(self) -> None:
        """Initialize an empty Decision Engine."""
        self._decisions: dict[str, DecisionRecord] = {}
        self._policy_rules: list[PolicyRule] = []
        self._event_engine: Any = None  # Optional EventEngine reference
        self._evidence_engine: Any = None  # Optional EvidenceEngine reference

    # ── Configuration ─────────────────────────────────────────────────────────

    def set_event_engine(self, event_engine: Any) -> None:
        """Set the Event Engine for emitting lifecycle events.

        Args:
            event_engine: An EventEngine instance from core.event.
        """
        self._event_engine = event_engine

    def set_evidence_engine(self, evidence_engine: Any) -> None:
        """Set the Evidence Engine for evidence validation.

        Args:
            evidence_engine: An EvidenceEngine instance from core.evidence.
        """
        self._evidence_engine = evidence_engine

    # ── IntelligenceEngine interface ──────────────────────────────────────────

    async def process(self, input: EngineInput) -> EngineOutput:
        """Process a decision-related input.

        Supported input types:
            - 'create_decision': Create a new decision record.
            - 'evaluate_policy': Evaluate a decision against policy rules.
            - 'assess_evidence': Assess evidence sufficiency for a decision.
            - 'select_option': Select an option for a decision.
            - 'get_decision': Retrieve a decision record.
            - 'list_decisions': List decisions filtered by status.

        Args:
            input: Structured input with type and payload.

        Returns:
            EngineOutput containing the result of processing.

        Raises:
            ValueError: If input_type is unknown or payload is invalid.
        """
        start_time = time.time()
        input_type = input.input_type
        payload = input.payload
        trace_id = input.trace_id
        threshold = input.confidence_threshold or self._DEFAULT_CONFIDENCE_THRESHOLD

        try:
            if input_type == "create_decision":
                result = self._handle_create_decision(payload, trace_id)
            elif input_type == "evaluate_policy":
                result = self._handle_evaluate_policy(payload, trace_id)
            elif input_type == "assess_evidence":
                result = self._handle_assess_evidence(payload, trace_id)
            elif input_type == "select_option":
                result = self._handle_select_option(payload, trace_id)
            elif input_type == "get_decision":
                result = self._handle_get_decision(payload, trace_id)
            elif input_type == "list_decisions":
                result = self._handle_list_decisions(payload, trace_id)
            elif input_type == "generate_options":
                return await self._handle_generate_options(
                    input, start_time, threshold
                )
            else:
                raise ValueError(f"Unknown decision input_type: {input_type!r}")

            confidence = result.get("confidence", 1.0)
            processing_ms = (time.time() - start_time) * 1000

            return EngineOutput(
                output_type=f"decision_{input_type}",
                payload=result,
                confidence=confidence,
                confidence_factors={"policy_consistency": 1.0, "deterministic": 1.0},
                deterministic=True,
                trace_id=trace_id,
                escalation_used=False,
                processing_time_ms=round(processing_ms, 2),
            )

        except Exception as e:
            logger.exception("DecisionEngine.process(%s) failed", input_type)
            processing_ms = (time.time() - start_time) * 1000
            return EngineOutput(
                output_type=f"decision_{input_type}_error",
                payload={"error": str(e), "input_type": input_type},
                confidence=0.0,
                confidence_factors={"error": 1.0},
                deterministic=True,
                trace_id=trace_id,
                processing_time_ms=round(processing_ms, 2),
            )

    def escalate(self, input: EngineInput) -> EscalationResult:
        """Prepare escalation data for AI-assisted decision processing.

        Builds the prompt and context for an AI provider when deterministic
        option generation is insufficient or confidence is below threshold.

        Args:
            input: The original engine input that triggered escalation.

        Returns:
            EscalationResult with prompt and context for the AI provider.
        """
        payload = input.payload
        label = payload.get("label", "Unknown decision")
        description = payload.get("description", "")

        prompt = (
            f"Generate decision options for: {label}\n"
            f"Description: {description}\n\n"
            f"Context: {input.context or {}}\n"
            f"For each option, provide: label, description, "
            f"expected outcome, risks, and confidence."
        )

        return EscalationResult(
            input_type=input.input_type,
            prompt=prompt,
            context=input.context,
            trace_id=input.trace_id,
        )

    def get_capabilities(self) -> list[str]:
        """Return list of capability strings.

        Returns:
            List of capabilities this engine provides.
        """
        return [
            "create_decision",
            "evaluate_policy",
            "assess_evidence",
            "select_option",
            "transition_decision",
            "generate_options",
            "list_decisions",
            "lifecycle_management",
        ]

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            Dict with engine status information.
        """
        from core.intelligence.models import EngineStatus

        status = EngineStatus.ACTIVE
        issues: list[str] = []

        return {
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "status": status.value,
            "total_decisions": len(self._decisions),
            "total_policy_rules": len(self._policy_rules),
            "event_engine_connected": self._event_engine is not None,
            "evidence_engine_connected": self._evidence_engine is not None,
            "issues": issues,
        }

    # ── Public API: Policy Rules ─────────────────────────────────────────────

    def add_policy_rule(self, rule: PolicyRule) -> str:
        """Register a policy rule for decision evaluation.

        Rules are stored in priority order (lowest first).

        Args:
            rule: The PolicyRule to add.

        Returns:
            The rule_id of the added rule.

        Raises:
            ValueError: If rule.rule_type is invalid.
        """
        valid_types = {"allow", "block", "require_evidence", "require_approval"}
        if rule.rule_type not in valid_types:
            raise ValueError(
                f"Invalid rule_type: {rule.rule_type!r}. "
                f"Must be one of {valid_types}"
            )

        if not rule.rule_id:
            from core.kernel.types import generate_uuid7
            object.__setattr__(rule, "rule_id", generate_uuid7())

        self._policy_rules.append(rule)
        self._policy_rules.sort(key=lambda r: r.priority)
        logger.info("Added policy rule %s (%s)", rule.rule_id, rule.name)
        return rule.rule_id

    def remove_policy_rule(self, rule_id: str) -> bool:
        """Remove a policy rule by ID.

        Args:
            rule_id: The rule_id of the rule to remove.

        Returns:
            True if the rule was removed, False if not found.
        """
        before = len(self._policy_rules)
        self._policy_rules = [r for r in self._policy_rules if r.rule_id != rule_id]
        removed = len(self._policy_rules) < before
        if removed:
            logger.info("Removed policy rule %s", rule_id)
        return removed

    def get_policy_rules(self) -> list[PolicyRule]:
        """Get all registered policy rules.

        Returns:
            List of PolicyRule objects ordered by priority.
        """
        return list(self._policy_rules)

    # ── Public API: Transitions ──────────────────────────────────────────────

    def transition(
        self,
        decision_id: str,
        target_status: DecisionStatus,
        actor_id: str,
        reason: str = "",
    ) -> DecisionRecord:
        """Transition a decision to a new lifecycle status.

        Validates that the transition is allowed by the lifecycle state
        machine before applying it.

        Args:
            decision_id: The decision to transition.
            target_status: The target DecisionStatus.
            actor_id: The actor performing the transition.
            reason: Human-readable reason for the transition.

        Returns:
            The updated DecisionRecord.

        Raises:
            ValueError: If decision_id is unknown.
            ValueError: If the transition is not allowed.
        """
        decision = self._get_decision(decision_id)
        current = decision.status

        if current == target_status:
            logger.warning(
                "Decision %s already in status %s", decision_id, current.value
            )
            return decision

        allowed = DECISION_VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise ValueError(
                f"Cannot transition decision {decision_id} from "
                f"{current.value!r} to {target_status.value!r}. "
                f"Allowed transitions from {current.value!r}: "
                f"{[s.value for s in allowed]}"
            )

        # Record the transition
        decision.add_status_history(
            from_status=current.value,
            to_status=target_status.value,
            actor_id=actor_id,
            reason=reason,
        )

        # Update status
        object.__setattr__(decision, "status", target_status)

        # Set completed_at for terminal states
        if target_status in (DecisionStatus.COMPLETED, DecisionStatus.FAILED):
            object.__setattr__(decision, "completed_at", _now_iso())

        # Update the actor responsible
        object.__setattr__(decision, "actor_id", actor_id)

        # Emit event if event engine is configured
        if self._event_engine is not None:
            self._emit_status_event(decision, current, target_status, actor_id)

        logger.info(
            "Decision %s: %s -> %s (by %s)",
            decision_id,
            current.value,
            target_status.value,
            actor_id,
        )

        return decision

    # ── Public API: Evidence Sufficiency ─────────────────────────────────────

    def check_evidence_sufficiency(
        self,
        decision_id: str,
        minimum_count: int = 1,
        minimum_confidence: float = 0.0,
        required_types: list[str] | None = None,
    ) -> EvidenceSufficiency:
        """Check whether a decision has sufficient evidence.

        Args:
            decision_id: The decision to check.
            minimum_count: Minimum number of evidence records required.
            minimum_confidence: Minimum aggregate confidence required.
            required_types: Specific evidence types that must be present.

        Returns:
            An EvidenceSufficiency result.
        """
        decision = self._get_decision(decision_id)
        evidence_ids = decision.evidence_ids

        evidence_count = len(evidence_ids)
        has_enough_count = evidence_count >= minimum_count

        has_required_types = True
        missing_types: list[str] = []

        if required_types and self._evidence_engine is not None:
            for req_type in required_types:
                type_found = False
                for eid in evidence_ids:
                    ev = self._evidence_engine.get_evidence(eid)
                    if ev and ev.evidence_type == req_type:
                        type_found = True
                        break
                if not type_found:
                    has_required_types = False
                    missing_types.append(req_type)

        # Compute aggregate confidence if evidence engine available
        aggregate_confidence = 0.0
        if self._evidence_engine is not None and evidence_ids:
            confidences = []
            for eid in evidence_ids:
                ev = self._evidence_engine.get_evidence(eid)
                if ev:
                    confidences.append(ev.confidence)
            if confidences:
                aggregate_confidence = sum(confidences) / len(confidences)

        has_enough_confidence = aggregate_confidence >= minimum_confidence

        satisfied = has_enough_count and has_required_types and has_enough_confidence

        reasons: list[str] = []
        if not has_enough_count:
            reasons.append(
                f"Need {minimum_count} evidence records, have {evidence_count}"
            )
        if not has_enough_confidence:
            reasons.append(
                f"Need {minimum_confidence} confidence, have {aggregate_confidence:.4f}"
            )
        if not has_required_types:
            reasons.append(f"Missing required types: {missing_types}")

        sufficiency = EvidenceSufficiency(
            minimum_evidence_count=minimum_count,
            minimum_confidence=minimum_confidence,
            required_types=required_types or [],
            satisfied=satisfied,
            reason="; ".join(reasons) if reasons else "Evidence sufficiency met.",
        )

        # Attach to the decision record
        object.__setattr__(decision, "evidence_sufficiency", sufficiency)

        return sufficiency

    # ── Public API: Option Management ────────────────────────────────────────

    def add_option(
        self,
        decision_id: str,
        option: DecisionOption,
    ) -> DecisionRecord:
        """Add a decision option to a decision.

        Args:
            decision_id: The decision to add the option to.
            option: The DecisionOption to add.

        Returns:
            The updated DecisionRecord.

        Raises:
            ValueError: If decision_id is unknown.
        """
        decision = self._get_decision(decision_id)
        if not option.option_id:
            from core.kernel.types import generate_uuid7
            object.__setattr__(option, "option_id", generate_uuid7())
        decision.options.append(option)
        object.__setattr__(decision, "updated_at", _now_iso())
        logger.info("Added option %s to decision %s", option.option_id, decision_id)
        return decision

    # ── Public API: Decision Retrieval ───────────────────────────────────────

    def get_decision(self, decision_id: str) -> DecisionRecord | None:
        """Retrieve a decision record by ID.

        Args:
            decision_id: The decision's UUID.

        Returns:
            The DecisionRecord, or None if not found.
        """
        return self._decisions.get(decision_id)

    def list_decisions(
        self,
        status: DecisionStatus | str | None = None,
        owner: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DecisionRecord]:
        """List decisions with optional filtering.

        Args:
            status: Optional filter by status.
            owner: Optional filter by owner.
            limit: Maximum results to return (default 50).
            offset: Pagination offset.

        Returns:
            List of matching DecisionRecord objects, ordered by created_at
            descending (newest first).
        """
        result = list(self._decisions.values())

        if status is not None:
            if isinstance(status, str):
                status = DecisionStatus.from_string(status)
            result = [d for d in result if d.status == status]

        if owner is not None:
            result = [d for d in result if d.owner == owner]

        # Sort newest first
        result.sort(key=lambda d: d.created_at, reverse=True)

        return result[offset : offset + limit]

    def get_decision_count(self) -> int:
        """Get the total number of decisions tracked.

        Returns:
            Total decision count.
        """
        return len(self._decisions)

    # ── Private: Input Handlers ──────────────────────────────────────────────

    def _handle_create_decision(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a create_decision request.

        Args:
            payload: Decision creation data.
            trace_id: Correlation ID.

        Returns:
            Dict with the created decision_id and decision record.

        Raises:
            ValueError: If required fields are missing.
        """
        label = payload.get("label", "")
        description = payload.get("description", "")
        owner = payload.get("owner", "")
        created_by = payload.get("created_by", owner)
        decision_type = payload.get("decision_type", "standard")
        context = payload.get("context", {})
        metadata = payload.get("metadata", {})
        evidence_ids = payload.get("evidence_ids", [])
        decision_payload = payload.get("payload", {})

        if not label:
            raise ValueError("'label' is required to create a decision")
        if not owner:
            raise ValueError("'owner' is required to create a decision")

        decision = DecisionRecord(
            label=label,
            description=description,
            owner=owner,
            created_by=created_by,
            actor_id=created_by,
            context=context,
            metadata=metadata,
            decision_type=decision_type,
            trace_id=trace_id,
            evidence_ids=evidence_ids,
            payload=decision_payload,
        )

        self._decisions[decision.decision_id] = decision

        # Emit creation event if event engine is configured
        if self._event_engine is not None:
            self._emit_creation_event(decision)

        logger.info(
            "Created decision %s: %s (owner=%s)",
            decision.decision_id,
            label,
            owner,
        )

        return {
            "decision_id": decision.decision_id,
            "decision": decision,
            "status": decision.status.value,
            "confidence": decision.confidence,
        }

    def _handle_evaluate_policy(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Evaluate a decision against all registered policy rules.

        Args:
            payload: Must include 'decision_id'.
            trace_id: Correlation ID.

        Returns:
            Dict with evaluation results.

        Raises:
            ValueError: If decision_id is missing or unknown.
        """
        decision_id = payload.get("decision_id", "")
        if not decision_id:
            raise ValueError("'decision_id' is required for policy evaluation")

        decision = self._get_decision(decision_id)

        results: list[dict[str, Any]] = []
        all_passed = True

        for rule in self._policy_rules:
            passed, reason = self._evaluate_single_rule(rule, decision)
            results.append({
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "rule_type": rule.rule_type,
                "passed": passed,
                "reason": reason,
            })
            if not passed:
                all_passed = False
                if rule.rule_type == "block":
                    # Block rules are terminal for evaluation
                    break

        decision.policy_rule_results = results
        object.__setattr__(decision, "updated_at", _now_iso())

        blocked = any(
            r["rule_type"] == "block" and not r["passed"] for r in results
        )
        needs_approval = any(
            r["rule_type"] == "require_approval" and r["passed"] for r in results
        )

        # Calculate confidence from policy consistency
        if results:
            passed_count = sum(1 for r in results if r["passed"])
            policy_confidence = passed_count / len(results)
        else:
            policy_confidence = 1.0

        object.__setattr__(decision, "confidence", policy_confidence)
        object.__setattr__(
            decision,
            "confidence_factors",
            {**decision.confidence_factors, "policy_consistency": policy_confidence},
        )

        return {
            "decision_id": decision_id,
            "all_passed": all_passed,
            "blocked": blocked,
            "needs_approval": needs_approval,
            "results": results,
            "confidence": policy_confidence,
        }

    def _handle_assess_evidence(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Assess evidence sufficiency for a decision.

        Args:
            payload: Must include 'decision_id'. Optional: 'minimum_count',
                'minimum_confidence', 'required_types'.
            trace_id: Correlation ID.

        Returns:
            Dict with evidence assessment results.
        """
        decision_id = payload.get("decision_id", "")
        if not decision_id:
            raise ValueError("'decision_id' is required for evidence assessment")

        minimum_count = payload.get("minimum_count", 1)
        minimum_confidence = payload.get("minimum_confidence", 0.0)
        required_types = payload.get("required_types")

        sufficiency = self.check_evidence_sufficiency(
            decision_id=decision_id,
            minimum_count=minimum_count,
            minimum_confidence=minimum_confidence,
            required_types=required_types,
        )

        decision = self._get_decision(decision_id)
        evidence_confidence = 1.0 if sufficiency.satisfied else 0.3

        object.__setattr__(
            decision,
            "confidence_factors",
            {**decision.confidence_factors, "evidence_sufficiency": evidence_confidence},
        )

        return {
            "decision_id": decision_id,
            "satisfied": sufficiency.satisfied,
            "reason": sufficiency.reason,
            "minimum_count": sufficiency.minimum_evidence_count,
            "minimum_confidence": sufficiency.minimum_confidence,
            "evidence_count": len(decision.evidence_ids),
            "evidence_confidence": evidence_confidence,
        }

    def _handle_select_option(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Select an option for a decision.

        Args:
            payload: Must include 'decision_id' and either 'option_id'
                or 'option_index'.
            trace_id: Correlation ID.

        Returns:
            Dict with the selected option and updated decision.

        Raises:
            ValueError: If decision_id, option_id/index is missing.
        """
        decision_id = payload.get("decision_id", "")
        option_id = payload.get("option_id")
        option_index = payload.get("option_index")

        if not decision_id:
            raise ValueError("'decision_id' is required to select an option")

        decision = self._get_decision(decision_id)

        selected: DecisionOption | None = None

        if option_id is not None:
            for opt in decision.options:
                if opt.option_id == option_id:
                    selected = opt
                    break
            if selected is None:
                raise ValueError(
                    f"Option {option_id!r} not found in decision {decision_id}"
                )
        elif option_index is not None:
            if 0 <= option_index < len(decision.options):
                selected = decision.options[option_index]
            else:
                raise ValueError(
                    f"Option index {option_index} out of range "
                    f"(decision has {len(decision.options)} options)"
                )
        else:
            raise ValueError(
                "Either 'option_id' or 'option_index' is required to select an option"
            )

        object.__setattr__(decision, "selected_option", selected)
        object.__setattr__(decision, "updated_at", _now_iso())

        # Update confidence based on selected option
        option_confidence = selected.confidence
        object.__setattr__(
            decision,
            "confidence_factors",
            {**decision.confidence_factors, "option_confidence": option_confidence},
        )

        logger.info(
            "Selected option %s for decision %s",
            selected.option_id,
            decision_id,
        )

        return {
            "decision_id": decision_id,
            "selected_option": selected,
            "confidence": option_confidence,
        }

    def _handle_get_decision(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a get_decision request.

        Args:
            payload: Must include 'decision_id'.
            trace_id: Correlation ID.

        Returns:
            Dict with the decision record.

        Raises:
            ValueError: If decision_id is missing or unknown.
        """
        decision_id = payload.get("decision_id", "")
        if not decision_id:
            raise ValueError("'decision_id' is required")
        decision = self._get_decision(decision_id)
        return {"decision_id": decision_id, "decision": decision}

    def _handle_list_decisions(
        self,
        payload: dict[str, Any],
        trace_id: str,
    ) -> dict[str, Any]:
        """Handle a list_decisions request.

        Args:
            payload: Optional filters: 'status', 'owner', 'limit', 'offset'.
            trace_id: Correlation ID.

        Returns:
            Dict with 'decisions' list and 'total' count.
        """
        status_filter = payload.get("status")
        owner_filter = payload.get("owner")
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)

        if status_filter is not None and isinstance(status_filter, str):
            try:
                status_filter = DecisionStatus.from_string(status_filter)
            except ValueError:
                raise ValueError(f"Unknown decision status: {status_filter!r}")

        decisions = self.list_decisions(
            status=status_filter,
            owner=owner_filter,
            limit=limit,
            offset=offset,
        )

        return {
            "decisions": decisions,
            "total": len(decisions),
            "limit": limit,
            "offset": offset,
        }

    async def _handle_generate_options(
        self,
        input: EngineInput,
        start_time: float,
        threshold: float,
    ) -> EngineOutput:
        """Handle option generation with confidence-based escalation.

        Deterministic option generation (simple mirroring) is attempted
        first. If confidence is below threshold, the engine escalates
        to an AI provider.

        Args:
            input: The original engine input.
            start_time: Start time for processing time calculation.
            threshold: Confidence threshold for escalation.

        Returns:
            EngineOutput with generated options.
        """
        payload = input.payload
        decision_id = payload.get("decision_id", "")
        label = payload.get("label", "Unknown decision")
        description = payload.get("description", "")

        escalation_used = False

        # Attempt deterministic generation
        options = self._generate_deterministic_options(label, description)

        if options:
            confidence = 0.6  # Moderate confidence for deterministic generation
        else:
            confidence = 0.0

        if confidence < threshold:
            # Escalate to AI
            escalation = self.escalate(input)
            escalation_used = True
            options = []  # AI would generate these
            confidence = 0.3  # Escalated but not yet processed
            logger.info(
                "Escalated option generation for %s (confidence %.2f < %.2f)",
                decision_id,
                confidence,
                threshold,
            )

        processing_ms = (time.time() - start_time) * 1000

        return EngineOutput(
            output_type="decision_generate_options",
            payload={
                "decision_id": decision_id,
                "options": [vars(o) for o in options],
                "escalation_prompt": escalation.prompt if escalation_used else None,
            },
            confidence=confidence,
            confidence_factors={
                "deterministic": 0.6 if options else 0.0,
            },
            deterministic=not escalation_used,
            trace_id=input.trace_id,
            escalation_used=escalation_used,
            processing_time_ms=round(processing_ms, 2),
        )

    # ── Private: Helpers ──────────────────────────────────────────────────────

    def _get_decision(self, decision_id: str) -> DecisionRecord:
        """Get a decision by ID, raising if not found.

        Args:
            decision_id: The decision UUID.

        Returns:
            The DecisionRecord.

        Raises:
            ValueError: If the decision is not found.
        """
        decision = self._decisions.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision not found: {decision_id!r}")
        return decision

    def _evaluate_single_rule(
        self,
        rule: PolicyRule,
        decision: DecisionRecord,
    ) -> tuple[bool, str]:
        """Evaluate a single policy rule against a decision.

        Args:
            rule: The policy rule to evaluate.
            decision: The decision to evaluate against.

        Returns:
            Tuple of (passed, reason).
        """
        condition = rule.condition
        field = condition.get("field", "")
        operator = condition.get("operator", "")
        rule_value = condition.get("value")

        if not field or not operator:
            return True, f"Rule {rule.name}: no condition defined (always passes)"

        # Get the actual value from decision or payload
        actual_value = self._resolve_field(field, decision)

        if actual_value is None:
            return True, f"Rule {rule.name}: field {field!r} not present (skipped)"

        try:
            actual_num = float(actual_value) if actual_value is not None else None
            rule_num = float(rule_value) if rule_value is not None else None
            if actual_num is None or rule_num is None:
                return False, f"Rule {rule.name}: cannot compare None values"
            if operator == ">":
                passed = actual_num > rule_num
            elif operator == "<":
                passed = actual_num < rule_num
            elif operator == ">=":
                passed = actual_num >= rule_num
            elif operator == "<=":
                passed = actual_num <= rule_num
            elif operator == "==":
                passed = actual_value == rule_value
            elif operator == "!=":
                passed = actual_value != rule_value
            elif operator == "in":
                passed = actual_value in (rule_value or [])
            elif operator == "not_in":
                passed = actual_value not in (rule_value or [])
            else:
                return True, f"Rule {rule.name}: unknown operator {operator!r}"
        except (TypeError, ValueError) as e:
            return False, f"Rule {rule.name}: evaluation error: {e}"

        if rule.rule_type == "block":
            if passed:
                return False, f"BLOCKED by rule '{rule.name}': {rule.reason}"
            return True, f"Rule '{rule.name}' condition not met (not blocked)"

        if rule.rule_type == "require_evidence":
            evidence_count = len(decision.evidence_ids)
            if evidence_count < (rule_value or 1):
                return False, (
                    f"Rule '{rule.name}' requires {rule_value or 1} evidence records, "
                    f"have {evidence_count}"
                )
            return True, f"Rule '{rule.name}' evidence requirement met"

        if rule.rule_type == "require_approval":
            if passed:
                return True, f"Rule '{rule.name}': approval required (condition met)"
            return True, f"Rule '{rule.name}': approval not required (condition not met)"

        # Allow rules
        return passed, (
            f"Rule '{rule.name}': {'passed' if passed else 'failed'}"
        )

    def _resolve_field(self, field: str, decision: DecisionRecord) -> Any:
        """Resolve a field path from a decision record or its payload.

        Supports dot-separated paths (e.g., 'payload.amount').

        Args:
            field: The field path to resolve.
            decision: The decision record.

        Returns:
            The resolved value, or None if not found.
        """
        parts = field.split(".")

        if len(parts) == 1:
            # Try decision attributes first, then payload
            if hasattr(decision, field):
                val = getattr(decision, field)
                return val if not callable(val) else None
            return decision.payload.get(field)

        if parts[0] == "payload":
            obj = decision.payload
        else:
            obj = getattr(decision, parts[0], decision.payload)

        for part in parts[1:]:
            if isinstance(obj, dict):
                val = obj.get(part)
                if val is not None:
                    obj = val
                else:
                    return None
            else:
                obj = getattr(obj, part, None)
            if obj is None:
                return None

        return obj

    def _generate_deterministic_options(
        self,
        label: str,
        description: str,
    ) -> list[DecisionOption]:
        """Generate simple deterministic options for a decision.

        This is a fallback when AI-assisted generation is not available.
        Produces basic approve/reject/defer options.

        Args:
            label: Decision label.
            description: Decision description.

        Returns:
            List of basic DecisionOption objects.
        """
        return [
            DecisionOption(
                label="Approve",
                description=f"Approve: {label}",
                expected_outcome={"action": "approved", "label": label},
                confidence=0.6,
                risks=[{"description": "Standard execution risk", "severity": "low"}],
                ai_generated=False,
            ),
            DecisionOption(
                label="Reject",
                description=f"Reject: {label}",
                expected_outcome={"action": "rejected", "label": label},
                confidence=0.6,
                risks=[{"description": "Opportunity cost", "severity": "medium"}],
                ai_generated=False,
            ),
            DecisionOption(
                label="Defer",
                description=f"Defer decision: {label}",
                expected_outcome={"action": "deferred", "label": label},
                confidence=0.5,
                risks=[{"description": "Delay may increase cost", "severity": "medium"}],
                ai_generated=False,
            ),
        ]

    def _emit_creation_event(self, decision: DecisionRecord) -> None:
        """Emit a decision created event via the event engine.

        Args:
            decision: The newly created decision.
        """
        try:
            self._event_engine.emit(
                event_type="decision.created",
                source=self.engine_id,
                actor_id=decision.created_by,
                object_id=decision.decision_id,
                payload={
                    "label": decision.label,
                    "description": decision.description,
                    "decision_type": decision.decision_type,
                },
                metadata={"trace_id": decision.trace_id},
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("Failed to emit creation event: %s", e)

    def _emit_status_event(
        self,
        decision: DecisionRecord,
        from_status: DecisionStatus,
        to_status: DecisionStatus,
        actor_id: str,
    ) -> None:
        """Emit a decision status change event via the event engine.

        Args:
            decision: The decision that changed.
            from_status: Previous status.
            to_status: New status.
            actor_id: The actor that triggered the change.
        """
        try:
            self._event_engine.emit(
                event_type="decision.status_changed",
                source=self.engine_id,
                actor_id=actor_id,
                object_id=decision.decision_id,
                payload={
                    "from_status": from_status.value,
                    "to_status": to_status.value,
                    "label": decision.label,
                },
                metadata={"trace_id": decision.trace_id},
            )
        except (ValueError, TypeError, KeyError) as e:
            logger.warning("Failed to emit status event: %s", e)