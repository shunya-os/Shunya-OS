"""SHUNYA Customer Experience — FDA13 Service.

Customer profile, history, commitments, escalations, retention signals.
All composed from canonical owners: Customer, Commitment, TimelineEntry, Lead.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from app import db
from app.customers.models import Customer
from app.commitments.models import Commitment
from app.relationship.models import TimelineEntry, CanonicalRelationship as Relationship
from app.models import Lead, Task


def get_customer_profile(customer_id: int) -> Optional[dict]:
    """One canonical customer context: identity, preferences, history, relationship."""
    c = Customer.query.get(customer_id)
    if not c:
        return None

    history = get_customer_history(customer_id)
    commitments = Commitment.query.filter_by(relationship_id=c.relationship_id).all() \
        if c.relationship_id else []
    retention = get_retention_signals(customer_id)

    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "status": c.status,
        "relationship_id": c.relationship_id,
        "lead_id": c.lead_id,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "history_count": len(history),
        "history": history[:10],
        "open_commitments": [{
            "id": cm.id, "title": cm.title, "owner": cm.owner,
            "due_at": cm.due_at.isoformat() if cm.due_at else None,
            "status": cm.status, "issue_type": cm.issue_type,
        } for cm in commitments if cm.status != "completed"],
        "retention": retention,
    }


def get_customer_history(customer_id: int) -> list:
    """Customer history from the canonical relationship timeline."""
    c = Customer.query.get(customer_id)
    if not c or not c.relationship_id:
        return []

    entries = TimelineEntry.query.filter_by(
        relationship_id=c.relationship_id
    ).order_by(TimelineEntry.event_time.desc()).limit(50).all()

    return [{
        "event_type": e.event_type,
        "event_time": e.event_time.isoformat() if e.event_time else None,
        "title": e.title,
        "description": e.description,
        "reference_type": e.reference_type,
        "reference_id": e.reference_id,
    } for e in entries]


def create_commitment(title: str, relationship_id: Optional[int],
                      owner: Optional[str] = None, due_at: Optional[datetime] = None,
                      issue_type: str = "service", campaign_id: Optional[int] = None,
                      meta: Optional[dict] = None) -> Commitment:
    """Create a governed customer commitment using the canonical Commitment model."""
    cm = Commitment(
        title=title,
        owner=owner or "",
        due_at=due_at,
        status="pending",
        relationship_id=relationship_id,
        campaign_id=campaign_id,
        issue_type=issue_type,
        meta=meta or {},
    )
    db.session.add(cm)
    db.session.commit()
    return cm


def create_escalation(relationship_id: int, summary: str,
                      owner: Optional[str] = None, due_at: Optional[datetime] = None) -> Commitment:
    """Escalation becomes a governed commitment with issue_type='escalation'."""
    return create_commitment(
        title=f"ESCALATION: {summary}",
        relationship_id=relationship_id,
        owner=owner,
        due_at=due_at or datetime.now(timezone.utc) + timedelta(hours=24),
        issue_type="escalation",
        meta={"escalation": True, "summary": summary},
    )


def create_issue(relationship_id: int, title: str, severity: str = "medium",
                 owner: Optional[str] = None) -> Commitment:
    """Issue = governed commitment with issue_type='issue' and severity in meta."""
    return create_commitment(
        title=f"[{severity.upper()}] {title}",
        relationship_id=relationship_id,
        owner=owner,
        issue_type="issue",
        meta={"severity": severity},
    )


def get_retention_signals(customer_id: int) -> dict:
    """Evidence-backed retention risk. Never fabricates certainty."""
    c = Customer.query.get(customer_id)
    if not c:
        return {"risk": "unknown", "signals": []}

    signals = []
    risk_score = 0

    # Customer status
    if c.status == "at_risk":
        signals.append({"signal": "customer_status", "weight": 20,
                        "evidence": "Customer flagged at_risk"})
        risk_score += 20

    # Recent interactions
    if c.relationship_id:
        last_entry = TimelineEntry.query.filter_by(
            relationship_id=c.relationship_id
        ).order_by(TimelineEntry.event_time.desc()).first()
        if last_entry and last_entry.event_time:
            event_time = last_entry.event_time
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            days_since = (datetime.now(timezone.utc) - event_time).days
            if days_since > 30:
                signals.append({"signal": "no_recent_interaction", "weight": 25,
                                "evidence": f"Last interaction {days_since} days ago"})
                risk_score += 25

    # Open issues
    if c.relationship_id:
        open_issues = Commitment.query.filter_by(
            relationship_id=c.relationship_id, issue_type="issue"
        ).filter(Commitment.status != "completed").count()
        if open_issues:
            signals.append({"signal": "open_issues", "weight": 15,
                            "evidence": f"{open_issues} open issues"})
            risk_score += 15

    # Missed commitments
    if c.relationship_id:
        missed = Commitment.query.filter_by(
            relationship_id=c.relationship_id
        ).filter(Commitment.status.in_(["failed"])).count()
        if missed:
            signals.append({"signal": "missed_commitments", "weight": 20,
                            "evidence": f"{missed} failed commitments"})
            risk_score += 20

    return {
        "risk": "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low",
        "risk_score": min(risk_score, 100),
        "signals": signals,
        "note": "Risk is derived from objective signals. No predictive certainty implied.",
    }


def resolve_commitment(commitment_id: int, resolution_note: str = "") -> Optional[dict]:
    """Resolve a commitment to completed."""
    cm = Commitment.query.get(commitment_id)
    if not cm:
        return None
    cm.status = "completed"
    db.session.commit()
    return {"id": cm.id, "status": cm.status, "resolution_note": resolution_note}