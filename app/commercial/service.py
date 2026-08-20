"""G4 — Commercial Service Layer.

Wires the universal commercial model to the existing canonical runtime:
- CanonicalRelationship (identity resolution)
- TimelineEntry (relationship history)
- RelationshipMemory (AI memory)
- Commitment / BusinessExecutionInstance (execution)
- DecisionContext (commercial decisions)
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from app import db
from app.commercial.models import (
    CommercialOpportunity,
    CommercialContext,
    CommercialProposal,
    CommercialTransition,
    is_valid_lifecycle_transition,
)

from app.relationship.models import TimelineEntry
from app.relationship.services import _add_timeline_entry

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# OPPORTUNITY LIFECYCLE
# ══════════════════════════════════════════════════════════════════════


def create_opportunity(
    *,
    organization_id: int,
    title: str,
    description: str = "",
    relationship_id: Optional[int] = None,
    opportunity_type: str = "opportunity",
    estimated_value: Optional[float] = None,
    currency: str = "",
    confidence: int = 50,
    urgency: int = 50,
    source: str = "manual",
    owner_identity_id: str = "",
    campaign_id: Optional[int] = None,
    created_by: str = "",
) -> CommercialOpportunity:
    """Create a new commercial opportunity.

    This is the canonical opportunity creation path.
    A TimelineEntry is created on the relationship if linked.
    """
    opp = CommercialOpportunity(
        organization_id=organization_id,
        relationship_id=relationship_id,
        title=title,
        description=description,
        opportunity_type=opportunity_type,
        lifecycle_state="discovered",
        previous_state="",
        estimated_value=Decimal(str(estimated_value)) if estimated_value is not None else None,
        currency=currency,
        confidence=confidence,
        urgency=urgency,
        source=source,
        owner_identity_id=owner_identity_id,
        campaign_id=campaign_id,
        created_by=created_by,
        updated_by=created_by,
    )
    db.session.add(opp)
    db.session.flush()

    # Record initial lifecycle history
    history = [{"from": "", "to": "discovered", "at": datetime.now(timezone.utc).isoformat(), "by": created_by}]
    opp.lifecycle_history = json.dumps(history)

    # Audit transition
    _record_transition(
        organization_id=organization_id,
        entity_type="opportunity",
        entity_id=opp.id,
        from_state="",
        to_state="discovered",
        reason="Created",
        triggered_by=created_by,
    )

    # Timeline entry on relationship
    if relationship_id:
        _add_timeline_entry(
            organization_id=organization_id,
            relationship_id=relationship_id,
            event_type="opportunity.discovered",
            title=f"Opportunity discovered: {title}",
            description=f"Type: {opportunity_type}, Source: {source}",
            reference_type="g4_opportunity",
            reference_id=opp.id,
            created_by=created_by,
        )

    # Create or update commercial context
    if relationship_id:
        _ensure_context(organization_id, relationship_id, opp.id)

    db.session.commit()
    logger.info("Opportunity %s created for org %s", opp.id, organization_id)
    return opp


def transition_opportunity(
    opp: CommercialOpportunity,
    to_state: str,
    reason: str = "",
    triggered_by: str = "",
    is_correction: bool = False,
    correction_reason: str = "",
) -> tuple[bool, Optional[str]]:
    """Transition an opportunity to a new lifecycle state.

    Returns (success, error_message).
    Only valid transitions are accepted. Corrections require an explicit reason.
    """
    from_state = opp.lifecycle_state

    if from_state == to_state:
        return True, None  # Idempotent

    if not is_valid_lifecycle_transition(from_state, to_state) and not is_correction:
        return False, f"Invalid transition: {from_state} → {to_state}"

    if is_correction and not correction_reason:
        return False, "Correction requires a reason"

    opp.previous_state = from_state
    opp.lifecycle_state = to_state
    opp.state_changed_at = datetime.now(timezone.utc)
    opp.state_change_reason = reason
    opp.updated_at = datetime.now(timezone.utc)

    # Update lifecycle history
    history = json.loads(opp.lifecycle_history or "[]")
    history.append({
        "from": from_state,
        "to": to_state,
        "at": datetime.now(timezone.utc).isoformat(),
        "by": triggered_by,
        "reason": reason,
        "is_correction": is_correction,
    })
    opp.lifecycle_history = json.dumps(history)

    # Audit transition
    _record_transition(
        organization_id=opp.organization_id,
        entity_type="opportunity",
        entity_id=opp.id,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
        triggered_by=triggered_by,
        is_correction=is_correction,
        correction_reason=correction_reason,
    )

    # Timeline entry on relationship
    if opp.relationship_id:
        _add_timeline_entry(
            organization_id=opp.organization_id,
            relationship_id=opp.relationship_id,
            event_type=f"opportunity.{to_state}",
            title=f"Opportunity {to_state}: {opp.title}",
            description=reason or f"Transitioned from {from_state} to {to_state}",
            reference_type="g4_opportunity",
            reference_id=opp.id,
        )

    db.session.commit()
    return True, None


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL CONTEXT
# ══════════════════════════════════════════════════════════════════════


def _ensure_context(
    organization_id: int,
    relationship_id: int,
    active_opp_id: Optional[int] = None,
) -> CommercialContext:
    """Get or create a CommercialContext for a relationship."""
    ctx = CommercialContext.query.filter_by(
        organization_id=organization_id, relationship_id=relationship_id
    ).first()
    if not ctx:
        ctx = CommercialContext(
            organization_id=organization_id,
            relationship_id=relationship_id,
            active_opportunity_id=active_opp_id,
        )
        db.session.add(ctx)
    elif active_opp_id:
        ctx.active_opportunity_id = active_opp_id
    return ctx


def get_commercial_context(organization_id: int, relationship_id: int) -> Optional[dict]:
    """Get full commercial context for a relationship."""
    ctx = CommercialContext.query.filter_by(
        organization_id=organization_id, relationship_id=relationship_id
    ).first()
    if not ctx:
        return None
    return ctx.to_dict()


def update_commercial_summary(
    organization_id: int,
    relationship_id: int,
    summary: str = "",
    suggested_next_action: str = "",
    suggested_action_reason: str = "",
) -> bool:
    """Update AI-enriched commercial summary for a relationship."""
    ctx = _ensure_context(organization_id, relationship_id)
    if summary:
        ctx.summary = summary
    if suggested_next_action:
        ctx.suggested_next_action = suggested_next_action
        ctx.suggested_action_reason = suggested_action_reason
        ctx.suggested_at = datetime.now(timezone.utc)
    ctx.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return True


# ══════════════════════════════════════════════════════════════════════
# PROPOSAL / OFFER
# ══════════════════════════════════════════════════════════════════════


def create_proposal(
    *,
    organization_id: int,
    relationship_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    title: str,
    proposal_type: str = "proposal",
    scope_description: str = "",
    assumptions: str = "",
    exclusions: str = "",
    currency: str = "INR",
    total_value: float = 0,
    terms: str = "",
    conditions: str = "",
    valid_until: Optional[datetime] = None,
    pricing_structure: Optional[list] = None,
    created_by: str = "",
) -> CommercialProposal:
    """Create a canonical commercial proposal.

    One representation that multiple renderers can consume.
    """
    proposal = CommercialProposal(
        organization_id=organization_id,
        relationship_id=relationship_id,
        opportunity_id=opportunity_id,
        title=title,
        proposal_type=proposal_type,
        status="draft",
        currency=currency,
        total_value=Decimal(str(total_value)),
        scope_description=scope_description,
        assumptions=assumptions,
        exclusions=exclusions,
        terms=terms,
        conditions=conditions,
        valid_from=datetime.now(timezone.utc),
        valid_until=valid_until,
        source_context=f"Created via {proposal_type} workflow",
        pricing_structure=json.dumps(pricing_structure or []),
        created_by=created_by,
        updated_by=created_by,
    )
    db.session.add(proposal)
    db.session.flush()

    # Add timeline entry
    if relationship_id:
        _add_timeline_entry(
            organization_id=organization_id,
            relationship_id=relationship_id,
            event_type="proposal.created",
            title=f"Proposal created: {title}",
            description=f"Value: {currency} {total_value}, Type: {proposal_type}",
            reference_type="g4_proposal",
            reference_id=proposal.id,
            created_by=created_by,
        )

    # Record transition
    _record_transition(
        organization_id=organization_id,
        entity_type="proposal",
        entity_id=proposal.id,
        from_state="",
        to_state="draft",
        reason="Created",
        triggered_by=created_by,
    )

    db.session.commit()
    return proposal


def transition_proposal(
    proposal: CommercialProposal,
    to_state: str,
    reason: str = "",
    triggered_by: str = "",
) -> tuple[bool, Optional[str], Optional[dict]]:
    """Transition a proposal to a new state.

    Returns (success, error, decision_context) where decision_context
    is populated when the transition represents a commercial decision
    (accepted → generates a commitment path).
    """
    from_state = proposal.status

    if from_state == to_state:
        return True, None, None

    # Validate lifecycle
    PROPOSAL_TRANSITIONS = {
        "draft": ["ai_generating", "review", "sent", "withdrawn"],
        "ai_generating": ["draft", "review"],
        "review": ["draft", "sent", "withdrawn"],
        "sent": ["viewed", "negotiating", "accepted", "declined", "withdrawn", "expired"],
        "viewed": ["negotiating", "accepted", "declined", "withdrawn"],
        "negotiating": ["sent", "accepted", "declined", "withdrawn"],
        "accepted": [],
        "declined": [],
        "withdrawn": ["draft"],
        "expired": ["draft"],
    }
    allowed = PROPOSAL_TRANSITIONS.get(from_state, [])
    if to_state not in allowed:
        return False, f"Invalid proposal transition: {from_state} → {to_state}", None

    proposal.status = to_state
    proposal.updated_by = triggered_by
    proposal.updated_at = datetime.now(timezone.utc)

    decision_result = None

    if to_state == "accepted":
        proposal.accepted_at = datetime.now(timezone.utc)
        # Generate the decision → commitment → execution path
        decision_result = _handle_proposal_accepted(proposal, triggered_by)

    if to_state == "declined":
        proposal.rejection_reason = reason

    if to_state == "sent":
        proposal.sent_at = datetime.now(timezone.utc)
        proposal.sent_via = triggered_by or "manual"

    if to_state == "viewed":
        proposal.viewed_at = datetime.now(timezone.utc)

    # Record transition
    _record_transition(
        organization_id=proposal.organization_id,
        entity_type="proposal",
        entity_id=proposal.id,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
        triggered_by=triggered_by,
    )

    # Timeline entry
    if proposal.relationship_id:
        _add_timeline_entry(
            organization_id=proposal.organization_id,
            relationship_id=proposal.relationship_id,
            event_type=f"proposal.{to_state}",
            title=f"Proposal {to_state}: {proposal.title}",
            description=reason or f"From {from_state} to {to_state}",
            reference_type="g4_proposal",
            reference_id=proposal.id,
        )

    db.session.commit()
    return True, None, decision_result


def _handle_proposal_accepted(
    proposal: CommercialProposal, triggered_by: str
) -> dict:
    """When a proposal is accepted: create canonical commitment + execution.

    This wires through the existing:
    Commercial Decision → canonical Decision → Commitment → BusinessExecutionInstance
    """
    decision_result = {
        "decision_made": True,
        "commitment_created": False,
        "execution_started": False,
        "commitment_id": None,
        "execution_id": None,
    }

    try:
        # 1. Create a Commitment using the existing Commitment model
        from app.commitments.models import Commitment

        commitment = Commitment(
            title=f"Execute: {proposal.title}",
            owner=triggered_by or "system",
            status="pending",
            relationship_id=proposal.relationship_id,
        )
        db.session.add(commitment)
        db.session.flush()
        proposal.commitment_id = str(commitment.id)
        decision_result["commitment_created"] = True
        decision_result["commitment_id"] = str(commitment.id)

        # 2. Activate BusinessExecutionInstance
        from app.execution import BusinessExecutionInstance

        exec_instance = BusinessExecutionInstance()
        result = exec_instance.activate(
            commitment_type="proposal",
            commitment_id=str(commitment.id),
            tenant_id=proposal.organization_id,
        )
        if result.get("success"):
            decision_result["execution_started"] = True
            decision_result["execution_id"] = result.get("exec_id")

        # 3. Transition the opportunity to "committed"
        if proposal.opportunity_id:
            opp = db.session.get(CommercialOpportunity, proposal.opportunity_id)
            if opp and opp.lifecycle_state in ("accepted", "proposal_pending"):
                transition_opportunity(
                    opp=opp,
                    to_state="committed",
                    reason=f"Proposal #{proposal.id} accepted",
                    triggered_by=triggered_by,
                )

        logger.info(
            "Proposal %s accepted → commitment %s → execution %s",
            proposal.id, commitment.id, result.get("exec_id"),
        )
    except Exception as e:
        logger.error("Failed to wire acceptance path for proposal %s: %s", proposal.id, e)
        decision_result["error"] = str(e)

    return decision_result


# ══════════════════════════════════════════════════════════════════════
# TRANSITION AUDIT
# ══════════════════════════════════════════════════════════════════════


def _record_transition(
    *,
    organization_id: int,
    entity_type: str,
    entity_id: int,
    from_state: str,
    to_state: str,
    reason: str = "",
    triggered_by: str = "",
    is_correction: bool = False,
    correction_reason: str = "",
) -> CommercialTransition:
    """Record an immutable transition event."""
    t = CommercialTransition(
        organization_id=organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        from_state=from_state,
        to_state=to_state,
        reason=reason,
        triggered_by=triggered_by,
        is_correction=is_correction,
        correction_reason=correction_reason,
    )
    db.session.add(t)
    db.session.flush()
    return t


# ══════════════════════════════════════════════════════════════════════
# FOLLOW-UP / NEXT ACTION (awareness integration)
# ══════════════════════════════════════════════════════════════════════


def get_opportunities_needing_attention(organization_id: int) -> list[dict]:
    """Find opportunities that need human attention.

    Returns opportunities where:
    - staging for >48h without state change
    - proposal_pending for >7d without decision
    - next_action_due_at is past due
    """
    now = datetime.now(timezone.utc)
    from sqlalchemy import func

    needs_attention = CommercialOpportunity.query.filter(
        CommercialOpportunity.organization_id == organization_id,
        CommercialOpportunity.lifecycle_state.in_([
            "discovered", "being_understood", "active", "waiting", "proposal_pending"
        ]),
    ).all()

    results = []
    for opp in needs_attention:
        reasons = []

        # Stale in current state
        if opp.state_changed_at:
            state_changed = opp.state_changed_at
            if state_changed.tzinfo is None:
                state_changed = state_changed.replace(tzinfo=timezone.utc)
            days_in_state = (now - state_changed).total_seconds() / 86400
            if days_in_state > 2 and opp.lifecycle_state in ("waiting", "discovered"):
                reasons.append(f"Stale for {days_in_state:.0f} days in '{opp.lifecycle_state}'")
            if days_in_state > 7 and opp.lifecycle_state == "proposal_pending":
                reasons.append(f"Proposal pending for {days_in_state:.0f} days without decision")

        # Overdue next action
        if opp.next_action_due_at:
            due_at = opp.next_action_due_at
            if due_at.tzinfo is None:
                due_at = due_at.replace(tzinfo=timezone.utc)
            if due_at < now:
                overdue_hours = (now - due_at).total_seconds() / 3600
                reasons.append(f"Next action overdue by {overdue_hours:.0f}h: {opp.next_action[:100]}")

        if reasons:
            d = opp.to_dict()
            d["attention_reasons"] = reasons
            results.append(d)

    return results


def get_upcoming_follow_ups(organization_id: int, within_hours: int = 48) -> list[dict]:
    """Get opportunities with upcoming follow-up actions."""
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=within_hours)

    upcoming = CommercialOpportunity.query.filter(
        CommercialOpportunity.organization_id == organization_id,
        CommercialOpportunity.next_action_due_at.isnot(None),
        CommercialOpportunity.next_action_due_at.between(now, deadline),
    ).all()

    return [opp.to_dict() for opp in upcoming]


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════


def get_commercial_intelligence(organization_id: int) -> dict:
    """Aggregate commercial intelligence for an organization.

    Answers: What changed? What needs attention? What is at risk?
    Which relationship matters now? What should I do next? Why?
    """
    now = datetime.now(timezone.utc)
    from sqlalchemy import func

    # Count opportunities by state
    state_counts = {}
    for state in ["discovered", "active", "waiting", "proposal_pending", "accepted", "executing", "lost"]:
        count = CommercialOpportunity.query.filter(
            CommercialOpportunity.organization_id == organization_id,
            CommercialOpportunity.lifecycle_state == state,
        ).count()
        if count > 0:
            state_counts[state] = count

    # Total active value
    active_value = db.session.query(
        func.sum(CommercialOpportunity.estimated_value)
    ).filter(
        CommercialOpportunity.organization_id == organization_id,
        CommercialOpportunity.lifecycle_state.in_([
            "active", "being_understood", "proposal_pending", "accepted", "committed", "executing"
        ]),
    ).scalar() or 0

    # High-urgency opportunities
    urgent = CommercialOpportunity.query.filter(
        CommercialOpportunity.organization_id == organization_id,
        CommercialOpportunity.urgency >= 80,
        CommercialOpportunity.lifecycle_state.notin_(["completed", "lost"]),
    ).count()

    # Needed attention
    attention = get_opportunities_needing_attention(organization_id)

    # Recent changes (last 7 days)
    week_ago = now.replace(day=now.day - 7) if now.day > 7 else now - timedelta(days=7)
    recent_transitions = CommercialTransition.query.filter(
        CommercialTransition.organization_id == organization_id,
        CommercialTransition.transitioned_at >= week_ago,
    ).order_by(CommercialTransition.transitioned_at.desc()).limit(20).all()

    return {
        "state_distribution": state_counts,
        "total_active_value": float(active_value),
        "urgent_opportunities": urgent,
        "needs_attention_count": len(attention),
        "needs_attention": attention[:5],
        "recent_transitions": len(recent_transitions),
        "total_opportunities": sum(state_counts.values()) if state_counts else 0,
        "at_risk_count": sum(1 for a in attention if "Stale" in str(a.get("attention_reasons", []))),
    }


def answer_commercial_question(
    organization_id: int, question: str
) -> dict:
    """Answer a commercial intelligence question using the G3 foundation.

    Uses the existing intelligence system to reason about commercial state.
    """
    intelligence = get_commercial_intelligence(organization_id)

    answers = {
        "what_changed": f"{intelligence['recent_transitions']} commercial transitions in the last 7 days",
        "what_needs_attention": f"{intelligence['needs_attention_count']} opportunities need attention",
        "what_is_at_risk": f"{intelligence['at_risk_count']} opportunities at risk of stalling",
        "which_relationship_matters": "Check commercial contexts with highest urgency/priority",
        "what_should_i_do_next": "Review opportunities needing attention — check suggested next actions",
        "why": "Based on lifecycle state analysis and overdue next actions",
    }

    # Match question to known patterns
    q = question.lower()
    for key, answer in answers.items():
        key_words = key.replace("_", " ")
        if any(word in q for word in key_words.split()):
            return {"question": question, "answer": answer, "evidence": intelligence}

    return {"question": question, "answer": "Analyzing commercial context...", "evidence": intelligence}


def get_opportunities_for_relationship(
    organization_id: int, relationship_id: int
) -> list[dict]:
    """Get all opportunities for a specific relationship."""
    opps = CommercialOpportunity.query.filter_by(
        organization_id=organization_id,
        relationship_id=relationship_id,
    ).order_by(CommercialOpportunity.created_at.desc()).all()
    return [o.to_dict() for o in opps]


def get_proposals_for_opportunity(
    organization_id: int, opportunity_id: int
) -> list[dict]:
    """Get all proposals for a specific opportunity."""
    proposals = CommercialProposal.query.filter_by(
        organization_id=organization_id,
        opportunity_id=opportunity_id,
    ).order_by(CommercialProposal.version_number.desc()).all()
    return [p.to_dict() for p in proposals]