"""SHUNYA Marketing OS — Canonical Campaign, Audience, Content, Experiment Models.

These are the ONLY new models for FDA14-FDA15. All other capabilities are
derived/retrieval views computed from existing canonical owners.
"""
from datetime import datetime, timezone
from app import db


class Campaign(db.Model):
    """Generic marketing campaign. Platform-specific campaigns (AdCampaign in
    app/integration/models.py) link to this via campaign_id references."""
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    objective = db.Column(db.String(80), default="awareness")
    # awareness, traffic, engagement, leads, sales, conversions, retention

    owner = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(30), default="draft")
    # draft, active, paused, completed, archived

    budget = db.Column(db.Numeric(12, 2), default=0)
    budget_type = db.Column(db.String(20), default="total")
    # total, daily, monthly

    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    utm_source = db.Column(db.String(255), default="")
    utm_campaign = db.Column(db.String(255), default="")
    utm_medium = db.Column(db.String(255), default="")

    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    created_by = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "objective": self.objective, "owner": self.owner, "status": self.status,
            "budget": str(self.budget) if self.budget else "0",
            "budget_type": self.budget_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "utm_source": self.utm_source, "utm_campaign": self.utm_campaign,
            "utm_medium": self.utm_medium,
            "tenant_id": self.tenant_id, "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AudienceDefinition(db.Model):
    """Audience/segment definition for campaign targeting."""
    __tablename__ = "audience_definitions"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    criteria_json = db.Column(db.Text, default="{}")  # JSON: segment criteria
    source = db.Column(db.String(60), default="manual")
    # manual, imported, behavioral, lookalike

    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id, "campaign_id": self.campaign_id, "name": self.name,
            "description": self.description, "criteria_json": self.criteria_json,
            "source": self.source, "tenant_id": self.tenant_id,
        }


class CampaignContent(db.Model):
    """Content items planned/pending/approved for a campaign."""
    __tablename__ = "campaign_contents"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(60), default="post")
    # post, email, landing_page, ad_creative, video, document
    body = db.Column(db.Text, default="")
    status = db.Column(db.String(30), default="draft")
    # draft, pending_review, approved, published, rejected
    asset_url = db.Column(db.String(500), default="")
    owner = db.Column(db.String(120), nullable=True)
    approval_commitment_id = db.Column(db.Integer, nullable=True)  # Link to Commitment

    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))


class Experiment(db.Model):
    """Marketing experiment metadata. Minimal — no authoritative truth duplication."""
    __tablename__ = "experiments"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    hypothesis = db.Column(db.Text, default="")
    variant = db.Column(db.String(60), default="A")
    status = db.Column(db.String(30), default="planned")
    # planned, running, completed, inconclusive
    metric = db.Column(db.String(60), default="conversion")
    confidence = db.Column(db.Float, nullable=True)
    sample_size = db.Column(db.Integer, nullable=True)

    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))