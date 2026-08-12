"""SHUNYA Marketing OS — FDA14 Service.

Campaign CRUD, audience definitions, content planning, lead capture, approvals.
"""
from datetime import datetime, timezone
from typing import Optional
from app import db
from app.marketing.models import Campaign, AudienceDefinition, CampaignContent
from app.commitments.models import Commitment
from app.crm.service import create_lead_with_identity


def create_campaign(name: str, tenant_id: int, **kwargs) -> Campaign:
    camp = Campaign(
        name=name,
        tenant_id=tenant_id,
        description=kwargs.get("description", ""),
        objective=kwargs.get("objective", "awareness"),
        owner=kwargs.get("owner"),
        status=kwargs.get("status", "draft"),
        budget=kwargs.get("budget", 0),
        budget_type=kwargs.get("budget_type", "total"),
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
        utm_source=kwargs.get("utm_source", ""),
        utm_campaign=kwargs.get("utm_campaign", ""),
        utm_medium=kwargs.get("utm_medium", ""),
        created_by=kwargs.get("created_by"),
    )
    db.session.add(camp)
    db.session.commit()
    return camp


def get_campaign(campaign_id: int, tenant_id: int) -> Optional[dict]:
    camp = Campaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    if not camp:
        return None
    return camp.to_dict()


def list_campaigns(tenant_id: int) -> list:
    camps = Campaign.query.filter_by(tenant_id=tenant_id).order_by(Campaign.created_at.desc()).all()
    return [c.to_dict() for c in camps]


def update_campaign(campaign_id: int, tenant_id: int, **kwargs) -> Optional[dict]:
    camp = Campaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    if not camp:
        return None
    for k in ("name", "description", "objective", "owner", "status", "budget",
              "budget_type", "start_date", "end_date", "utm_source", "utm_campaign", "utm_medium"):
        if k in kwargs:
            setattr(camp, k, kwargs[k])
    db.session.commit()
    return camp.to_dict()


def create_audience(campaign_id: int, name: str, tenant_id: int, **kwargs) -> AudienceDefinition:
    aud = AudienceDefinition(
        campaign_id=campaign_id,
        name=name,
        description=kwargs.get("description", ""),
        criteria_json=kwargs.get("criteria_json", "{}"),
        source=kwargs.get("source", "manual"),
        tenant_id=tenant_id,
    )
    db.session.add(aud)
    db.session.commit()
    return aud


def list_audiences(tenant_id: int, campaign_id: Optional[int] = None) -> list:
    q = AudienceDefinition.query.filter_by(tenant_id=tenant_id)
    if campaign_id:
        q = q.filter_by(campaign_id=campaign_id)
    auds = q.all()
    return [{"id": a.id, "campaign_id": a.campaign_id, "name": a.name,
             "description": a.description, "source": a.source} for a in auds]


def create_content(campaign_id: int, title: str, tenant_id: int, **kwargs) -> CampaignContent:
    content = CampaignContent(
        campaign_id=campaign_id,
        title=title,
        content_type=kwargs.get("content_type", "post"),
        body=kwargs.get("body", ""),
        status="draft",
        asset_url=kwargs.get("asset_url", ""),
        owner=kwargs.get("owner"),
        tenant_id=tenant_id,
    )
    db.session.add(content)
    db.session.commit()
    return content


def approve_content(content_id: int, tenant_id: int,
                    approver: str = "") -> Optional[dict]:
    """Approve content by creating a governed Commitment."""
    content = CampaignContent.query.filter_by(id=content_id, tenant_id=tenant_id).first()
    if not content:
        return None

    cm = Commitment(
        title=f"Approve: {content.title}",
        owner=approver or "",
        status="pending",
        issue_type="approval",
        campaign_id=content.campaign_id,
        meta={"content_id": content_id},
    )
    db.session.add(cm)
    content.status = "pending_review"
    content.approval_commitment_id = cm.id
    db.session.commit()

    return {"content_id": content_id, "approval_commitment_id": cm.id,
            "content_status": content.status, "commitment_status": cm.status}


def capture_lead(tenant_id: int, **kwargs) -> dict:
    """Capture a lead from a campaign source. Uses canonical CRM service."""
    campaign_id = kwargs.get("campaign_id")
    lead = create_lead_with_identity(
        tenant_id=tenant_id,
        name=kwargs.get("name", ""),
        phone=kwargs.get("phone", ""),
        email=kwargs.get("email", ""),
        source=kwargs.get("source", "campaign"),
        destination=kwargs.get("destination", ""),
        pax=kwargs.get("pax", ""),
        budget=kwargs.get("budget", 0),
    )
    # Attach campaign attribution
    if campaign_id and lead:
        lead.campaign_id = campaign_id
        lead.utm_source = kwargs.get("utm_source", "")
        lead.utm_campaign = kwargs.get("utm_campaign", "")
        lead.utm_medium = kwargs.get("utm_medium", "")
        lead.utm_term = kwargs.get("utm_term", "")
        lead.utm_content = kwargs.get("utm_content", "")
        db.session.commit()

    return {"lead_id": lead.id, "code": lead.code, "success": True}