"""SHUNYA Sales Intelligence — FDA12 Service.

All capabilities are DERIVED from canonical models. No new tables.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from app import db
from app.models import Lead, Task, Proposal
from app.relationship.models import TimelineEntry


def lead_scoring(lead_id: int) -> dict:
    """Score a lead from evidence. Each score is explained."""
    lead = Lead.query.get(lead_id)
    if not lead:
        return {"error": "Lead not found", "score": 0}

    signals = []
    score = 0

    # Budget signal
    budget = float(lead.budget or 0)
    if budget > 10000:
        signals.append({"signal": "high_budget", "weight": 20, "evidence": f"Budget {budget}"})
        score += 20
    elif budget > 2000:
        signals.append({"signal": "medium_budget", "weight": 10, "evidence": f"Budget {budget}"})
        score += 10

    # Destination defined
    if lead.destination:
        signals.append({"signal": "has_destination", "weight": 15, "evidence": lead.destination})
        score += 15

    # Source quality
    if lead.source in ("referral", "direct"):
        signals.append({"signal": "high_quality_source", "weight": 10, "evidence": f"Source: {lead.source}"})
        score += 10

    # Contacted/qualified state
    if lead.status in ("contacted", "qualified", "converted"):
        signals.append({"signal": "engaged", "weight": 15, "evidence": f"Status: {lead.status}"})
        score += 15
    if lead.status == "qualified":
        signals.append({"signal": "qualified", "weight": 20, "evidence": "Lead is qualified"})
        score += 20

    # Follow-up task exists
    tasks = Task.query.filter_by(lead_id=lead.id, status="pending").count()
    if tasks > 0:
        signals.append({"signal": "has_pending_followup", "weight": 5, "evidence": f"{tasks} pending tasks"})
        score += 5

    # Timeline activity
    timeline_count = TimelineEntry.query.filter(
        TimelineEntry.reference_type == "lead",
        TimelineEntry.reference_id == lead.id,
    ).count()
    if timeline_count > 3:
        signals.append({"signal": "high_activity", "weight": 10, "evidence": f"{timeline_count} timeline entries"})
        score += 10

    return {
        "lead_id": lead_id,
        "score": min(score, 100),
        "max_score": 100,
        "signals": signals,
        "classification": "hot" if score >= 70 else "warm" if score >= 40 else "cold",
    }


def next_best_action(lead_id: int) -> list:
    """Recommend next actions based on lead state."""
    lead = Lead.query.get(lead_id)
    if not lead:
        return []

    recommendations = []

    if lead.status == "new":
        recommendations.append({
            "action": "contact_lead",
            "reason": "New lead needs initial contact",
            "urgency": "high",
            "owner": lead.assigned_to or "unassigned",
            "confidence": "deterministic",
        })

    if lead.status == "contacted":
        overdue_tasks = Task.query.filter_by(lead_id=lead.id, status="pending").filter(
            Task.due_date < datetime.now(timezone.utc).date()
        ).count()
        if overdue_tasks:
            recommendations.append({
                "action": "complete_overdue_followup",
                "reason": f"{overdue_tasks} overdue follow-up tasks",
                "urgency": "high",
                "owner": lead.assigned_to or "unassigned",
                "confidence": "deterministic",
            })
        else:
            recommendations.append({
                "action": "follow_up",
                "reason": "Lead contacted but not yet qualified",
                "urgency": "medium",
                "owner": lead.assigned_to or "unassigned",
                "confidence": "deterministic",
            })

    if lead.status == "qualified" or lead.stage == "qualified":
        recommendations.append({
            "action": "send_proposal",
            "reason": "Lead is qualified, ready for proposal",
            "urgency": "medium",
            "owner": lead.assigned_to or "unassigned",
            "confidence": "deterministic",
        })

    if lead.stage == "new" and not lead.assigned_to:
        recommendations.append({
            "action": "assign_owner",
            "reason": "Lead has no assigned owner",
            "urgency": "high",
            "owner": "manager",
            "confidence": "deterministic",
        })

    return recommendations


def pipeline_health(tenant_id: int) -> dict:
    """Pipeline stage distribution and aging."""
    all_leads = Lead.query.filter_by(tenant_id=tenant_id).all()
    total = len(all_leads)

    stages = {}
    for l in all_leads:
        s = l.stage or "new"
        stages[s] = stages.get(s, 0) + 1

    # Aging analysis
    aging = []
    now = datetime.now(timezone.utc)
    for l in all_leads:
        if l.status in ("new", "contacted") and l.created_at:
            days = (datetime.now(timezone.utc) - l.created_at.replace(tzinfo=timezone.utc)).days
            if days > 7:
                aging.append({"id": l.id, "code": l.code, "name": l.customer_name,
                              "stage": l.stage, "days_since_creation": days,
                              "assigned_to": l.assigned_to})

    return {
        "total_leads": total,
        "stage_distribution": stages,
        "stalled_count": len(aging),
        "stalled_leads": sorted(aging, key=lambda x: x["days_since_creation"], reverse=True)[:10],
        "unassigned": sum(1 for l in all_leads if not l.assigned_to),
    }


def forecast(tenant_id: int, months: int = 3) -> dict:
    """Simple forecast from pipeline value and conversion rates."""
    all_leads = Lead.query.filter_by(tenant_id=tenant_id).all()
    qualified = [l for l in all_leads if l.status == "qualified"]
    proposals = Proposal.query.all()
    draft_proposals = [p for p in proposals if p.status == "draft"]
    won_proposals = [p for p in proposals if p.status == "accepted"]

    pipeline_value = sum(float(p.budget or 0) for p in draft_proposals)
    won_value = sum(float(p.budget or 0) for p in won_proposals)
    qualified_count = len(qualified)
    historical_conversion = len(won_proposals) / max(len(all_leads), 1)

    return {
        "forecast_months": months,
        "pipeline_value": str(pipeline_value),
        "qualified_count": qualified_count,
        "expected_value": str(round(pipeline_value * historical_conversion, 2)) if historical_conversion else "0",
        "historical_conversion_rate": round(historical_conversion * 100, 1),
        "won_value": str(won_value),
        "assumptions": [
            "Forecast uses pipeline value × historical conversion rate",
            "Historical rate is total won / total leads",
            "Does not account for seasonality or stage-weighted conversion",
        ],
    }


def salesperson_intel(agent_id: str) -> dict:
    """Workload and performance metrics for a salesperson."""
    leads = Lead.query.filter_by(assigned_to=agent_id).all()
    total = len(leads)
    active = sum(1 for l in leads if l.status in ("new", "contacted", "qualified"))
    won = sum(1 for l in leads if l.status == "converted")
    lost = sum(1 for l in leads if l.status == "lost")

    pending_tasks = Task.query.filter_by(assigned_to=agent_id, status="pending").count()
    overdue_tasks = Task.query.filter_by(assigned_to=agent_id, status="pending").filter(
        Task.due_date < datetime.now(timezone.utc).date()
    ).count() if Task.query.filter_by(assigned_to=agent_id).first() else 0

    return {
        "agent_id": agent_id,
        "total_leads": total,
        "active_leads": active,
        "won": won,
        "lost": lost,
        "conversion_rate": round(won / max(total, 1) * 100, 1),
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "follow_up_debt": overdue_tasks,
    }


def conversion_analysis(tenant_id: int) -> dict:
    """Stage conversion rates and loss reasons."""
    all_leads = Lead.query.filter_by(tenant_id=tenant_id).all()
    total = len(all_leads)

    loss_reasons = {}
    for l in all_leads:
        if l.status == "lost" and l.outcome:
            reason = l.outcome or "unknown"
            loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

    return {
        "total_leads": total,
        "converted": sum(1 for l in all_leads if l.status == "converted"),
        "lost": sum(1 for l in all_leads if l.status == "lost"),
        "conversion_rate": round(sum(1 for l in all_leads if l.status == "converted") / max(total, 1) * 100, 1),
        "loss_reasons": loss_reasons,
        "top_loss_reason": max(loss_reasons, key=loss_reasons.get) if loss_reasons else None,
    }