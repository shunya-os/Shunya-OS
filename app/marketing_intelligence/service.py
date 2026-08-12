"""SHUNYA Marketing Intelligence — FDA15 Service.

Attribution, conversion, channel comparison, revenue trace, experiments.
All attribution is COMPUTED from canonical events — no parallel event store.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from app import db
from app.models import Lead, Proposal
from app.customers.models import Customer as CustomerModel
from app.relationship.models import TimelineEntry, CanonicalRelationship as Relationship
from app.marketing.models import Campaign, Experiment


def get_attribution(campaign_id: int, tenant_id: int) -> dict:
    """Trace campaign → lead → customer → revenue."""
    campaign = Campaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    if not campaign:
        return {"error": "Campaign not found", "campaign_id": campaign_id}

    leads = Lead.query.filter_by(campaign_id=campaign_id).all()
    lead_ids = [l.id for l in leads]
    customers = CustomerModel.query.filter(
        CustomerModel.lead_id.in_(lead_ids)
    ).all() if lead_ids else []
    touchpoints = TimelineEntry.query.filter_by(campaign_id=campaign_id).count()
    proposals = Proposal.query.filter(
        Proposal.opportunity_id.in_(lead_ids)
    ).all() if lead_ids else []
    total_revenue = sum(float(p.budget or 0) for p in proposals if p.status == "accepted")

    return {
        "campaign": campaign.name,
        "campaign_id": campaign_id,
        "leads_count": len(leads),
        "customers_count": len(customers),
        "touchpoints": touchpoints,
        "total_revenue": str(total_revenue),
        "leads": [{"id": l.id, "code": l.code, "name": l.customer_name, "status": l.status}
                  for l in leads[:20]],
        "customers": [{"id": c.id, "name": c.name, "email": c.email}
                      for c in customers[:20]],
    }


def get_conversion(tenant_id: int) -> dict:
    """Stage conversion rates from lead captured → contacted → qualified → won."""
    all_leads = Lead.query.filter_by(tenant_id=tenant_id).all()
    total = len(all_leads)
    contacted = sum(1 for l in all_leads if l.status in ("contacted", "qualified", "converted"))
    qualified = sum(1 for l in all_leads if l.status in ("qualified", "converted"))
    won = sum(1 for l in all_leads if l.status == "converted")

    return {
        "total_leads": total,
        "contacted": contacted,
        "contacted_rate": round(contacted / total * 100, 1) if total else 0,
        "qualified": qualified,
        "qualified_rate": round(qualified / total * 100, 1) if total else 0,
        "won": won,
        "won_rate": round(won / total * 100, 1) if total else 0,
        "lost": sum(1 for l in all_leads if l.status == "lost"),
        "pipeline_value": sum(float(p.budget or 0) for p in Proposal.query.all()
                              if p.status == "draft"),
        "won_value": sum(float(p.budget or 0) for p in Proposal.query.all()
                         if p.status == "accepted"),
    }


def compare_channels(tenant_id: int) -> list:
    """Compare lead sources/channels by volume and conversion."""
    from sqlalchemy import text
    rows = db.session.execute(
        text("""
            SELECT source, COUNT(*) as total,
                   SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as won,
                   SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost
            FROM leads
            WHERE source IS NOT NULL AND source != ''
            GROUP BY source
            ORDER BY total DESC
        """)
    ).fetchall()

    return [{
        "source": r.source,
        "total": r.total,
        "won": r.won,
        "lost": r.lost,
        "conversion_rate": round(r.won / r.total * 100, 1) if r.total else 0,
    } for r in rows]


def revenue_trace(customer_id: int, tenant_id: int) -> Optional[dict]:
    """Drill from Customer → Lead → Campaign → source event."""
    c = CustomerModel.query.filter_by(id=customer_id).first()
    if not c:
        return None

    lead = Lead.query.get(c.lead_id) if c.lead_id else None
    campaign = Campaign.query.get(lead.campaign_id) if lead and lead.campaign_id else None

    timeline = []
    if c.relationship_id:
        timeline = TimelineEntry.query.filter_by(
            relationship_id=c.relationship_id
        ).order_by(TimelineEntry.event_time.desc()).limit(20).all()

    return {
        "customer": {"id": c.id, "name": c.name, "email": c.email,
                      "relationship_id": c.relationship_id, "lead_id": c.lead_id},
        "lead": {"id": lead.id, "code": lead.code, "status": lead.status,
                 "source": lead.source} if lead else None,
        "campaign": {"id": campaign.id, "name": campaign.name,
                     "utm_source": campaign.utm_source} if campaign else None,
        "timeline": [{
            "event_type": t.event_type, "event_time": t.event_time.isoformat() if t.event_time else None,
            "title": t.title, "campaign_id": t.campaign_id, "source_event": t.source_event
        } for t in timeline],
    }


def get_waste(campaign_id: int, tenant_id: int) -> dict:
    """Surface poor-performing campaigns."""
    campaign = Campaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    if not campaign:
        return {"error": "Campaign not found"}

    leads = Lead.query.filter_by(campaign_id=campaign_id).all()
    total = len(leads)
    lost = sum(1 for l in leads if l.status == "lost")
    budget = float(campaign.budget or 0)

    return {
        "campaign": campaign.name,
        "total_leads": total,
        "lost_leads": lost,
        "lost_rate": round(lost / total * 100, 1) if total else 0,
        "budget": str(budget),
        "cost_per_lead": str(round(budget / total, 2)) if total else "N/A",
        "recommendation": "Review campaign targeting" if lost > 0 else "No waste detected",
    }


def get_cac(tenant_id: int) -> dict:
    """Customer Acquisition Cost from campaign data."""
    campaigns = Campaign.query.filter_by(tenant_id=tenant_id).all()
    total_budget = sum(float(c.budget or 0) for c in campaigns)
    total_customers = CustomerModel.query.filter_by(tenant_id=tenant_id).count()

    return {
        "total_budget": str(total_budget),
        "total_customers": total_customers,
        "cac": str(round(total_budget / total_customers, 2)) if total_customers else "N/A",
        "note": "CAC is approximate. Based on campaign budget, not total operational cost.",
    }