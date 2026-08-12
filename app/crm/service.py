"""SHUNYA CRM — Lead-to-Customer Foundation Service.

Connects existing canonical owners into one coherent lifecycle:
Lead → Relationship → Opportunity → Proposal → Customer.

No new models. No parallel stores. Uses existing:
- Lead (app.models.Lead) for capture
- CanonicalRelationship (app.relationship.models) for relationship
- TimelineEntry (app.relationship.models) for history
- Proposal (app.models.Proposal) for quoting
- Task (app.models.Task) for follow-ups
- Customer (app.customers.models) for conversion
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from app import db
from app.models import Lead, LeadStatus, LeadSource, Task, Proposal
from app.relationship.models import (
    CanonicalRelationship as Relationship,
    TimelineEntry,
)
from app.relationship.services import create_relationship, _add_timeline_entry
from app.customers.models import Customer

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# SLA Constants
# ══════════════════════════════════════════════════════════════════

DEFAULT_SLA_HOURS = 24  # Default SLA: respond within 24 hours
ESCALATION_SLA_HOURS = 48  # Escalate if not contacted within 48 hours


# ══════════════════════════════════════════════════════════════════
# Qualification
# ══════════════════════════════════════════════════════════════════


class QualificationResult:
    """Result of a lead qualification decision."""

    def __init__(self, qualified: bool, reason: str, detail: str = ""):
        self.qualified = qualified
        self.reason = reason  # qualified, unqualified, needs_info, lost
        self.detail = detail

    def to_dict(self) -> dict:
        return {
            "qualified": self.qualified,
            "reason": self.reason,
            "detail": self.detail,
        }


def qualify_lead(lead: Lead) -> QualificationResult:
    """Determine if a lead is qualified based on available information.

    Uses the canonical qualification logic. Returns an explainable result.
    """
    if not lead.customer_name and not lead.phone and not lead.email:
        return QualificationResult(
            qualified=False, reason="needs_info",
            detail="Missing customer name, phone, or email"
        )
    if lead.pax and lead.destination:
        return QualificationResult(
            qualified=True, reason="qualified",
            detail=f"Lead has destination ({lead.destination}) and pax ({lead.pax})"
        )
    if lead.budget and lead.budget > 0:
        return QualificationResult(
            qualified=True, reason="qualified",
            detail=f"Lead has budget ({lead.budget})"
        )
    return QualificationResult(
        qualified=False, reason="needs_info",
        detail="Lead has basic contact info but insufficient qualification data"
    )


# ══════════════════════════════════════════════════════════════════
# Lead Lifecycle
# ══════════════════════════════════════════════════════════════════


def create_lead_with_identity(
    *,
    tenant_id: int,
    name: str = "",
    phone: str = "",
    email: str = "",
    source: str = "manual",
    destination: str = "",
    pax: str = "",
    budget: float = 0,
    notes: str = "",
    assigned_to: str = "",
    created_by: str = "",
    _retry_count: int = 0,
) -> Lead:
    """Create a lead with identity resolution and relationship binding.

    This is the canonical lead capture path.
    Uses the existing Lead model — no new lead store.
    Creates a Relationship if one doesn't exist for the email/phone.
    Retries on code uniqueness failure (concurrent creation safety).
    """
    from app.relationship.services import create_relationship as _create_rel
    from sqlalchemy.exc import IntegrityError

    try:
        from app.models import next_inquiry_code
        code = next_inquiry_code(db.session)
        lead = Lead(
            code=code,
            source=source,
            customer_name=name,
            phone=phone,
            email=email,
            destination=destination,
            pax=pax,
            budget=budget,
            notes=notes,
            status=LeadStatus.NEW.value,
            stage="new",
            assigned_to=assigned_to,
        )
        db.session.add(lead)
        db.session.flush()

        rel = _resolve_identity(tenant_id, name, phone, email, created_by)
        if rel:
            lead.person_id = rel.id
            _add_timeline_entry(
                organization_id=tenant_id,
                relationship_id=rel.id,
                event_type="lead.created",
                title=f"New lead from {source}: {name or phone or email}",
                description=f"Lead code: {code}, Source: {source}",
                reference_type="lead",
                reference_id=lead.id,
                created_by=created_by,
            )

        db.session.commit()
        return lead
    except IntegrityError:
        db.session.rollback()
        if _retry_count < 5:
            return create_lead_with_identity(
                tenant_id=tenant_id, name=name, phone=phone, email=email,
                source=source, destination=destination, pax=pax, budget=budget,
                notes=notes, assigned_to=assigned_to, created_by=created_by,
                _retry_count=_retry_count + 1,
            )
        raise


def _resolve_identity(
    tenant_id: int, name: str, phone: str, email: str, created_by: str
) -> Optional[Relationship]:
    """Find or create a canonical relationship for this lead.

    Tries email match, then phone match, then creates new.
    This is the canonical identity resolution path.
    """
    if email:
        rel = Relationship.query.filter_by(
            organization_id=tenant_id, email=email
        ).first()
        if rel:
            return rel
    if phone:
        rel = Relationship.query.filter_by(
            organization_id=tenant_id, phone=phone
        ).first()
        if rel:
            return rel
    # Create new relationship
    return create_relationship(
        organization_id=tenant_id,
        data={
            "display_name": name or phone or email or "Unknown Lead",
            "email": email,
            "phone": phone,
            "source": "lead_capture",
            "relationship_type": "lead",
            "internal_owner": created_by or "",
        },
        created_by=created_by,
    )


def assign_lead(lead: Lead, owner: str, tenant_id: int) -> Lead:
    """Assign a lead to an owner. Records on timeline."""
    old_owner = lead.assigned_to
    lead.assigned_to = owner
    lead.updated_at = datetime.utcnow()

    # Record on relationship timeline
    if lead.person_id:
        _add_timeline_entry(
            organization_id=tenant_id,
            relationship_id=lead.person_id,
            event_type="lead.assigned",
            title=f"Lead assigned to {owner}",
            description=f"Previous owner: {old_owner or 'unassigned'}",
            reference_type="lead",
            reference_id=lead.id,
            created_by=owner,
        )
    db.session.commit()
    return lead


def qualify_lead_and_update(lead: Lead, tenant_id: int) -> QualificationResult:
    """Qualify a lead and update its status. Returns the qualification result."""
    result = qualify_lead(lead)
    if result.qualified:
        lead.status = LeadStatus.IN_PROGRESS.value
        lead.stage = "qualified"
        if lead.person_id:
            _add_timeline_entry(
                organization_id=tenant_id,
                relationship_id=lead.person_id,
                event_type="lead.qualified",
                title="Lead qualified",
                description=result.detail,
                reference_type="lead",
                reference_id=lead.id,
            )
    else:
        lead.stage = result.reason
    lead.updated_at = datetime.utcnow()
    db.session.commit()
    return result


# ══════════════════════════════════════════════════════════════════
# SLA Management
# ══════════════════════════════════════════════════════════════════


def check_sla(lead: Lead) -> dict:
    """Check if a lead is within SLA. Returns SLA status."""
    now = datetime.utcnow()
    elapsed = now - lead.created_at
    within_sla = elapsed < timedelta(hours=DEFAULT_SLA_HOURS)
    escalated = elapsed > timedelta(hours=ESCALATION_SLA_HOURS)

    return {
        "lead_id": lead.id,
        "created_at": lead.created_at.isoformat(),
        "elapsed_hours": round(elapsed.total_seconds() / 3600, 1),
        "within_sla": within_sla,
        "escalated": escalated,
        "sla_deadline": (lead.created_at + timedelta(hours=DEFAULT_SLA_HOURS)).isoformat(),
        "escalation_deadline": (lead.created_at + timedelta(hours=ESCALATION_SLA_HOURS)).isoformat(),
    }


def create_follow_up(lead: Lead, title: str, due_date: datetime, assigned_to: str) -> Task:
    """Create a follow-up task for a lead.

    Uses the canonical Task model (app.models.Task) — no new task engine.
    The task is linked to the lead via lead_id FK.
    """
    from app.models import TaskList
    task_list = TaskList.query.filter_by(name="CRM Follow-ups").first()
    if not task_list:
        task_list = TaskList(name="CRM Follow-ups")
        db.session.add(task_list)
        db.session.flush()

    task = Task(
        lead_id=lead.id,
        task_list_id=task_list.id,
        title=title,
        description=f"Follow-up for lead {lead.code} ({lead.customer_name})",
        assigned_to=assigned_to,
        status="pending",
        due_date=due_date.date() if hasattr(due_date, 'date') else due_date,
    )
    db.session.add(task)
    db.session.commit()

    if lead.person_id:
        _add_timeline_entry(
            organization_id=lead.person_id if hasattr(lead, 'person_id') else 0,
            relationship_id=lead.person_id,
            event_type="followup.created",
            title=f"Follow-up created: {title}",
            description=f"Assigned to: {assigned_to}, Due: {due_date.isoformat()}",
            reference_type="task",
            reference_id=task.id,
        )
    return task


# ══════════════════════════════════════════════════════════════════
# Pipeline / Opportunity
# ══════════════════════════════════════════════════════════════════


def create_opportunity(lead: Lead, tenant_id: int, title: str = "") -> Proposal:
    """Create an opportunity/proposal from a qualified lead.

    Uses the existing Proposal model — no new opportunity store.
    Linked to lead via opportunity_id FK.
    """
    proposal = Proposal(
        organization_id=tenant_id,
        relationship_id=lead.person_id,
        opportunity_id=lead.id,
        title=title or f"Proposal for {lead.customer_name or lead.code}",
        status="draft",
        destination=lead.destination,
        pax=lead.pax,
        budget=lead.budget,
        created_by=lead.assigned_to or "",
    )
    db.session.add(proposal)
    lead.stage = "opportunity"
    lead.updated_at = datetime.utcnow()
    db.session.commit()

    if lead.person_id:
        _add_timeline_entry(
            organization_id=tenant_id,
            relationship_id=lead.person_id,
            event_type="opportunity.created",
            title=f"Opportunity created: {proposal.title}",
            description=f"Proposal #{proposal.id}, Status: draft",
            reference_type="proposal",
            reference_id=proposal.id,
        )
    return proposal


def convert_to_customer(lead: Lead, tenant_id: int) -> Optional[Customer]:
    """Convert a won lead to a customer.

    Uses the existing Customer model — no new customer store.
    """
    if lead.status != LeadStatus.CONVERTED.value:
        lead.status = LeadStatus.CONVERTED.value
        lead.stage = "customer"
        lead.updated_at = datetime.utcnow()

    customer = Customer(
        name=lead.customer_name or "",
        phone=lead.phone or "",
        email=lead.email or "",
    )
    db.session.add(customer)
    db.session.flush()

    if lead.person_id:
        _add_timeline_entry(
            organization_id=tenant_id,
            relationship_id=lead.person_id,
            event_type="customer.converted",
            title=f"Lead converted to customer: {lead.customer_name or lead.code}",
            description=f"Customer #{customer.id}, Lead code: {lead.code}",
            reference_type="customer",
            reference_id=customer.id,
        )
    db.session.commit()
    return customer


def mark_lost(lead: Lead, reason: str, tenant_id: int) -> Lead:
    """Mark a lead as lost with a reason."""
    lead.status = LeadStatus.CANCELLED.value
    lead.stage = "lost"
    lead.outcome = reason
    lead.updated_at = datetime.utcnow()

    if lead.person_id:
        _add_timeline_entry(
            organization_id=tenant_id,
            relationship_id=lead.person_id,
            event_type="lead.lost",
            title=f"Lead lost: {reason}",
            description=f"Reason: {reason}",
            reference_type="lead",
            reference_id=lead.id,
        )
    db.session.commit()
    return lead


# ══════════════════════════════════════════════════════════════════
# Reassignment
# ══════════════════════════════════════════════════════════════════


def reassign_unattended_leads(tenant_id: int, new_owner: str) -> list[Lead]:
    """Reassign leads that are past SLA escalation deadline.

    No lead may disappear because an owner fails to act.
    """
    now = datetime.utcnow()
    deadline = now - timedelta(hours=ESCALATION_SLA_HOURS)
    unattended = Lead.query.filter(
        Lead.status.in_([LeadStatus.NEW.value, LeadStatus.IN_PROGRESS.value]),
        Lead.created_at < deadline,
    ).all()

    reassigned = []
    for lead in unattended:
        old_owner = lead.assigned_to
        lead.assigned_to = new_owner
        lead.updated_at = now
        reassigned.append(lead)

        if lead.person_id:
            _add_timeline_entry(
                organization_id=tenant_id,
                relationship_id=lead.person_id,
                event_type="lead.reassigned",
                title=f"Lead reassigned from {old_owner or 'unassigned'} to {new_owner}",
                description=f"SLA escalation: unattended for >{ESCALATION_SLA_HOURS}h",
                reference_type="lead",
                reference_id=lead.id,
            )

    db.session.commit()
    return reassigned