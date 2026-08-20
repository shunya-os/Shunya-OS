"""
G5 — Canonical Models for Universal Marketing, Growth, Attribution & Learning.

NO duplicate of existing primitives (Campaign, AudienceDefinition, CampaignContent, Experiment
already exist in app/marketing/models.py).
NO industry-specific assumptions.
NO parallel campaign system.

Reuses:
- G4 CommercialOpportunity (app/commercial/models.py) — has campaign_id for the revenue bridge
- Campaign (app/marketing/models.py) — canonical campaign root
- CanonicalRelationship (app/relationship/models.py) — for relationship linkage
- TimelineEntry (app/relationship/models.py) — for event history
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app import db
from sqlalchemy import Index, Text


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGN EVENT — every meaningful campaign lifecycle moment
# ══════════════════════════════════════════════════════════════════════

CAMPAIGN_EVENT_TYPES = [
    "campaign_created",
    "campaign_activated",
    "campaign_paused",
    "campaign_completed",
    "campaign_cancelled",
    "campaign_underperforming",
    "campaign_budget_changed",
    "campaign_objective_changed",
    "new_response_arrived",
    "attribution_changed",
    "conversion_occurred",
    "commercial_outcome_emerged",
    "learning_available",
    "no_meaningful_response",
    "campaign_assessment",
]


class CampaignEvent(db.Model):
    """Immutable record of every meaningful campaign lifecycle moment.

    This is NOT a log of every HTTP call. It records only intentional
    state transitions and detected situations that SHUNYA should know about.
    """

    __tablename__ = "g5_campaign_events"
    __table_args__ = (
        Index("ix_g5_ce_campaign", "campaign_id"),
        Index("ix_g5_ce_time", "campaign_id", "occurred_at"),
        Index("ix_g5_ce_type", "campaign_id", "event_type"),
        Index("ix_g5_ce_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, nullable=False, index=True)
    tenant_id = db.Column(db.Integer, nullable=False)

    event_type = db.Column(db.String(40), nullable=False)
    previous_state = db.Column(db.String(30), default="")
    new_state = db.Column(db.String(30), default="")
    description = db.Column(db.Text, default="")

    # Evidence: what detected/triggered this event
    trigger_source = db.Column(db.String(60), default="system")
    # system, user, integration, intelligence, attribution
    evidence_ref = db.Column(db.String(255), default="")

    # Payload: structured data about the event
    payload_json = db.Column(db.Text, default="{}")

    # Lineage
    created_by = db.Column(db.String(64), default="")
    occurred_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "tenant_id": self.tenant_id,
            "event_type": self.event_type,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "description": self.description,
            "trigger_source": self.trigger_source,
            "evidence_ref": self.evidence_ref,
            "payload": json.loads(self.payload_json or "{}"),
            "created_by": self.created_by,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


# ══════════════════════════════════════════════════════════════════════
# MULTI-TOUCH INTERACTION — preserves every known touchpoint over time
# ══════════════════════════════════════════════════════════════════════

INTERACTION_TYPES = [
    "first_discovery",
    "repeated_exposure",
    "referral",
    "email_interaction",
    "website_visit",
    "conversation",
    "advertisement",
    "event",
    "content_engagement",
    "direct_outreach",
    "social_engagement",
    "phone_call",
    "form_submission",
    "download",
    "other",
]


class TouchpointInteraction(db.Model):
    """A single known interaction/touchpoint in the growth path.

    Preserves raw evidence first — any attribution reasoning is derived
    from these records. Multiple interactions per campaign/identity
    are expected (multi-touch reality).

    Does NOT force a single-source model. Does NOT overwrite history.
    """

    __tablename__ = "g5_interactions"
    __table_args__ = (
        Index("ix_g5_int_campaign", "campaign_id"),
        Index("ix_g5_int_identity", "identity_ref"),
        Index("ix_g5_int_relationship", "relationship_id"),
        Index("ix_g5_int_tenant", "tenant_id"),
        Index("ix_g5_int_type", "campaign_id", "interaction_type"),
        Index("ix_g5_int_time", "identity_ref", "occurred_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, nullable=True, index=True)
    tenant_id = db.Column(db.Integer, nullable=False)

    # ── Identity
    identity_ref = db.Column(db.String(255), default="")
    person_name = db.Column(db.String(255), default="")
    person_email = db.Column(db.String(255), default="")

    # ── Relationship linkage (if known)
    relationship_id = db.Column(db.Integer, nullable=True, index=True)
    organization_id = db.Column(db.Integer, nullable=True)

    # ── Interaction type
    interaction_type = db.Column(db.String(40), default="first_discovery")
    description = db.Column(db.Text, default="")

    # ── Source / Channel / Referrer
    source = db.Column(db.String(255), default="")
    channel = db.Column(db.String(255), default="")
    referrer = db.Column(db.String(500), default="")

    # ── Tracking context
    utm_source = db.Column(db.String(255), default="")
    utm_medium = db.Column(db.String(255), default="")
    utm_campaign = db.Column(db.String(255), default="")
    utm_term = db.Column(db.String(255), default="")
    utm_content = db.Column(db.String(255), default="")

    # ── Session / tracking ref
    session_ref = db.Column(db.String(255), default="")
    tracking_id = db.Column(db.String(255), default="")

    # ── Engagement
    engagement_duration_seconds = db.Column(db.Integer, nullable=True)
    engagement_depth = db.Column(db.Integer, default=0)
    content_ref = db.Column(db.String(500), default="")

    # ── Evidence
    evidence_json = db.Column(db.Text, default="{}")
    source_confidence = db.Column(db.Integer, default=50)  # 0-100

    # ── Lineage
    recorded_by = db.Column(db.String(64), default="")
    occurred_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "tenant_id": self.tenant_id,
            "identity_ref": self.identity_ref,
            "person_name": self.person_name,
            "person_email": self.person_email,
            "relationship_id": self.relationship_id,
            "organization_id": self.organization_id,
            "interaction_type": self.interaction_type,
            "description": self.description,
            "source": self.source,
            "channel": self.channel,
            "referrer": self.referrer,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "utm_term": self.utm_term,
            "utm_content": self.utm_content,
            "session_ref": self.session_ref,
            "tracking_id": self.tracking_id,
            "engagement_duration_seconds": self.engagement_duration_seconds,
            "engagement_depth": self.engagement_depth,
            "content_ref": self.content_ref,
            "evidence": json.loads(self.evidence_json or "{}"),
            "source_confidence": self.source_confidence,
            "recorded_by": self.recorded_by,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


# ══════════════════════════════════════════════════════════════════════
# CANONICAL ATTRIBUTION — preserves evidence and uncertainty
# ══════════════════════════════════════════════════════════════════════

ATTRIBUTION_STATES = [
    "directly_linked",       # Direct known causality (e.g. known conversion)
    "strongly_attributable",  # Strong evidence of attribution
    "plausibly_attributable", # Reasonable inference
    "correlated",            # Temporal correlation, no direct evidence
    "disputed",              # Conflicting evidence
    "unknown",               # No attribution determination
    "not_attributable",      # Explicitly determined as not caused by this
]


class AttributeTouch(db.Model):
    """A single attribution link in the causal chain.

    Each record preserves ONE link in the chain:
    SOURCE → CAMPAIGN → INTERACTION → RELATIONSHIP → OPPORTUNITY → REVENUE

    Multiple links form the full path. Historical attributions are NEVER
    silently overwritten — new evidence creates a new record.

    Confidence is always stated — never assumed certainty where none exists.
    """

    __tablename__ = "g5_attributions"
    __table_args__ = (
        Index("ix_g5_attr_campaign", "campaign_id"),
        Index("ix_g5_attr_source", "source", "source_ref"),
        Index("ix_g5_attr_target", "target_type", "target_id"),
        Index("ix_g5_attr_identity", "identity_ref"),
        Index("ix_g5_attr_tenant", "tenant_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, nullable=True, index=True)
    tenant_id = db.Column(db.Integer, nullable=False)

    # ── What is being attributed
    target_type = db.Column(db.String(40), nullable=False)
    # interaction, relationship, opportunity, proposal, revenue, outcome, person
    target_id = db.Column(db.Integer, nullable=False, index=True)
    target_description = db.Column(db.String(500), default="")

    # ── Source of attribution
    source = db.Column(db.String(255), default="")
    source_ref = db.Column(db.String(255), default="")

    # ── Channel / Content / Asset
    channel = db.Column(db.String(255), default="")
    content_ref = db.Column(db.String(500), default="")

    # ── Tracking context
    utm_source = db.Column(db.String(255), default="")
    utm_medium = db.Column(db.String(255), default="")
    utm_campaign = db.Column(db.String(255), default="")
    utm_term = db.Column(db.String(255), default="")
    utm_content = db.Column(db.String(255), default="")

    # ── Attribution state
    attribution_state = db.Column(db.String(30), default="unknown", nullable=False)
    confidence = db.Column(db.Integer, default=50)  # 0-100
    evidence_summary = db.Column(db.Text, default="")

    # ── Identity / Relationship
    identity_ref = db.Column(db.String(255), default="")
    relationship_id = db.Column(db.Integer, nullable=True)
    organization_id = db.Column(db.Integer, nullable=True)

    # ── Commercial linkage (G4 bridge)
    opportunity_id = db.Column(db.Integer, nullable=True, index=True)
    proposal_id = db.Column(db.Integer, nullable=True)
    outcome_id = db.Column(db.Integer, nullable=True)
    revenue_amount = db.Column(db.Numeric(15, 2), nullable=True)
    is_revenue_outcome = db.Column(db.Boolean, default=False)

    # ── Evidence preservation
    evidence_json = db.Column(db.Text, default="{}")
    interaction_id = db.Column(db.Integer, nullable=True)
    is_first_known = db.Column(db.Boolean, default=False)
    attribution_policy = db.Column(db.String(40), default="evidenced")

    # ── Lineage
    created_by = db.Column(db.String(64), default="")
    attributed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "tenant_id": self.tenant_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_description": self.target_description,
            "source": self.source,
            "source_ref": self.source_ref,
            "channel": self.channel,
            "content_ref": self.content_ref,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "utm_term": self.utm_term,
            "utm_content": self.utm_content,
            "attribution_state": self.attribution_state,
            "confidence": self.confidence,
            "evidence_summary": self.evidence_summary,
            "identity_ref": self.identity_ref,
            "relationship_id": self.relationship_id,
            "organization_id": self.organization_id,
            "opportunity_id": self.opportunity_id,
            "proposal_id": self.proposal_id,
            "outcome_id": self.outcome_id,
            "revenue_amount": float(self.revenue_amount) if self.revenue_amount else None,
            "is_revenue_outcome": self.is_revenue_outcome,
            "evidence": json.loads(self.evidence_json or "{}"),
            "interaction_id": self.interaction_id,
            "is_first_known": self.is_first_known,
            "attribution_policy": self.attribution_policy,
            "created_by": self.created_by,
            "attributed_at": self.attributed_at.isoformat() if self.attributed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════════════════
# GROWTH LEARNING — insights grounded in actual outcomes
# ══════════════════════════════════════════════════════════════════════

LEARNING_CATEGORIES = [
    "campaign_performance",
    "channel_effectiveness",
    "audience_response",
    "content_effectiveness",
    "attribution_insight",
    "conversion_pattern",
    "waste_detection",
    "opportunity_insight",
    "outcome_analysis",
    "recommendation",
    "insufficient_evidence",
    "external_information",
]


class GrowthLearning(db.Model):
    """A learning/insight grounded in actual SHUNYA data.

    Every learning record preserves:
    - What was observed
    - What evidence supports it
    - What the confidence is
    - What actual data grounds it
    - What should be done next (if anything)

    If evidence is insufficient, SHUNYA says so — no fabricated intelligence.
    """

    __tablename__ = "g5_learnings"
    __table_args__ = (
        Index("ix_g5_lrn_campaign", "campaign_id"),
        Index("ix_g5_lrn_tenant", "tenant_id"),
        Index("ix_g5_lrn_category", "campaign_id", "category"),
        Index("ix_g5_lrn_time", "tenant_id", "observed_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, nullable=True, index=True)
    tenant_id = db.Column(db.Integer, nullable=False)

    # ── Core learning
    category = db.Column(db.String(40), default="campaign_performance")
    title = db.Column(db.String(500), nullable=False)
    observation = db.Column(db.Text, default="")
    significance = db.Column(db.String(20), default="normal")
    # normal, notable, significant, critical

    # ── Grounding evidence
    evidence_summary = db.Column(db.Text, default="")
    evidence_refs = db.Column(db.Text, default="[]")  # JSON list of ref IDs
    confidence = db.Column(db.Integer, default=50)  # 0-100
    data_source = db.Column(db.String(60), default="shunya_internal")
    # shunya_internal, external_current, historical, inference

    # ── Attribution linkage
    attribution_id = db.Column(db.Integer, nullable=True)
    interaction_id = db.Column(db.Integer, nullable=True)
    outcome_id = db.Column(db.Integer, nullable=True)
    opportunity_id = db.Column(db.Integer, nullable=True)

    # ─── Recommendation
    recommendation = db.Column(db.Text, default="")
    recommendation_confidence = db.Column(db.Integer, default=50)
    recommendation_action = db.Column(db.String(255), default="")
    is_actionable = db.Column(db.Boolean, default=False)

    # ── External info provenance
    external_source = db.Column(db.String(255), default="")
    external_retrieved_at = db.Column(db.DateTime, nullable=True)
    external_context = db.Column(db.Text, default="")

    # ── Lineage
    created_by = db.Column(db.String(64), default="")
    observed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "tenant_id": self.tenant_id,
            "category": self.category,
            "title": self.title,
            "observation": self.observation,
            "significance": self.significance,
            "evidence_summary": self.evidence_summary,
            "evidence_refs": json.loads(self.evidence_refs or "[]"),
            "confidence": self.confidence,
            "data_source": self.data_source,
            "attribution_id": self.attribution_id,
            "interaction_id": self.interaction_id,
            "outcome_id": self.outcome_id,
            "opportunity_id": self.opportunity_id,
            "recommendation": self.recommendation,
            "recommendation_confidence": self.recommendation_confidence,
            "recommendation_action": self.recommendation_action,
            "is_actionable": self.is_actionable,
            "external_source": self.external_source,
            "external_retrieved_at": self.external_retrieved_at.isoformat() if self.external_retrieved_at else None,
            "external_context": self.external_context,
            "created_by": self.created_by,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }