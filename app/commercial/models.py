"""G4 — Universal Commercial Models.

No industry-specific types are hardcoded (no lead, customer, deal, quote).
The canonical model uses universal terms: Opportunity, Context, Proposal.
Business vocabulary is config-driven via CommercialType.

Reuses existing canonical:
- CanonicalRelationship (app.relationship.models)
- TimelineEntry (app.relationship.models)
- RelationshipMemory (app.relationship.models)
- Commitment (app.commitments.models)
- DecisionContext / DecisionEvaluation (app.decision.models)
- BusinessExecutionInstance (app.execution)
- Outcome (app.execution.models)
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from app import db
from sqlalchemy import Index, Numeric, Text


# ══════════════════════════════════════════════════════════════════════
# OPPORTUNITY / NEED LIFECYCLE
# ══════════════════════════════════════════════════════════════════════

OPPORTUNITY_STATES = [
    "discovered",        # A need/opportunity has been identified
    "being_understood",  # Actively learning about the need
    "active",            # Engaged relationship, exploring fit
    "waiting",           # Awaiting information, decision, or external input
    "proposal_pending",  # Proposal/offer has been extended
    "accepted",          # Decision made — accepted in principle
    "declined",          # Decision made — declined
    "committed",         # Converted into a formal commitment
    "executing",         # Commitment is being executed
    "completed",         # Delivered, outcome observed
    "lost",              # Lost, withdrawn, or no longer viable
]

VALID_TRANSITIONS: dict[str, list[str]] = {
    "discovered": ["being_understood", "active", "waiting", "lost"],
    "being_understood": ["active", "waiting", "lost", "discovered"],
    "active": ["waiting", "proposal_pending", "lost", "being_understood"],
    "waiting": ["active", "proposal_pending", "lost", "being_understood"],
    "proposal_pending": ["accepted", "declined", "lost", "waiting", "active"],
    "accepted": ["committed", "declined", "lost", "proposal_pending"],
    "declined": ["discovered", "lost"],
    "committed": ["executing", "lost"],
    "executing": ["completed", "lost"],
    "completed": [],
    "lost": ["discovered"],
}


def is_valid_lifecycle_transition(from_state: str, to_state: str) -> bool:
    """Check if a lifecycle transition is valid per the canonical state machine."""
    allowed = VALID_TRANSITIONS.get(from_state, [])
    return to_state in allowed


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL OPPORTUNITY
# ══════════════════════════════════════════════════════════════════════


class CommercialOpportunity(db.Model):
    """A universal commercial opportunity or need.

    NOT a CRM lead. This represents any commercial context where a
    relationship has an identifiable need, opportunity, or intention
    that could lead to a commercial outcome.

    Business-agnostic: no destination, pax, industry-specific fields.
    Custom attributes via JSON for vertical-specific data.
    """

    __tablename__ = "g4_opportunities"
    __table_args__ = (
        Index("ix_g4_opp_org", "organization_id"),
        Index("ix_g4_opp_rel", "relationship_id"),
        Index("ix_g4_opp_state", "organization_id", "lifecycle_state"),
        Index("ix_g4_opp_owner", "owner_identity_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False, index=True
    )
    relationship_id = db.Column(
        db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True, index=True
    )

    # ── Core identity ──
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, default="")
    opportunity_type = db.Column(db.String(60), default="opportunity")
    # Config-driven: "opportunity", "need", "lead", "enquiry", etc.

    # ── Lifecycle ──
    lifecycle_state = db.Column(db.String(40), default="discovered", nullable=False)
    previous_state = db.Column(db.String(40), default="")
    state_changed_at = db.Column(db.DateTime, nullable=True)
    state_change_reason = db.Column(db.Text, default="")

    # ── Commercial attributes ──
    estimated_value = db.Column(Numeric(15, 2), nullable=True)
    currency = db.Column(db.String(10), default="")
    confidence = db.Column(db.Integer, default=50)  # 0-100
    urgency = db.Column(db.Integer, default=50)  # 0-100
    priority = db.Column(db.Integer, default=0)  # 0-100

    # ── Context ──
    source = db.Column(db.String(255), default="")
    source_reference = db.Column(db.String(255), default="")
    # e.g. "manual", "email", "connector", "import", "referral"

    owner_identity_id = db.Column(db.String(64), default="")
    next_action = db.Column(db.Text, default="")
    next_action_due_at = db.Column(db.DateTime, nullable=True)

    risks = db.Column(db.Text, default="[]")  # JSON array of risk items
    evidence = db.Column(db.Text, default="[]")  # JSON array of evidence refs
    custom_attributes = db.Column(db.Text, default="{}")

    # ── Linking ──
    campaign_id = db.Column(db.Integer, nullable=True, index=True)
    conversation_ref = db.Column(db.String(255), default="")

    # ── Audit ──
    created_by = db.Column(db.String(64), default="")
    updated_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Lifecycle history (JSON — full audit trail in TimelineEntry) ──
    lifecycle_history = db.Column(db.Text, default="[]")

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "relationship_id": self.relationship_id,
            "title": self.title,
            "description": (self.description or "")[:500],
            "opportunity_type": self.opportunity_type,
            "lifecycle_state": self.lifecycle_state,
            "previous_state": self.previous_state,
            "state_changed_at": self.state_changed_at.isoformat() if self.state_changed_at else None,
            "state_change_reason": self.state_change_reason,
            "estimated_value": float(self.estimated_value) if self.estimated_value else None,
            "currency": self.currency,
            "confidence": self.confidence,
            "urgency": self.urgency,
            "priority": self.priority,
            "source": self.source,
            "source_reference": self.source_reference,
            "owner_identity_id": self.owner_identity_id,
            "next_action": self.next_action,
            "next_action_due_at": self.next_action_due_at.isoformat() if self.next_action_due_at else None,
            "risks": json.loads(self.risks or "[]"),
            "evidence": json.loads(self.evidence or "[]"),
            "custom_attributes": json.loads(self.custom_attributes or "{}"),
            "campaign_id": self.campaign_id,
            "conversation_ref": self.conversation_ref,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL CONTEXT (the full picture)
# ══════════════════════════════════════════════════════════════════════


class CommercialContext(db.Model):
    """The full commercial context for a relationship.

    Not a pipeline stage. Represents the complete commercial understanding
    SHUNYA has about a relationship at any point in time.

    One per relationship. Updated as SHUNYA learns.
    """

    __tablename__ = "g4_contexts"
    __table_args__ = (
        Index("ix_g4_ctx_rel", "relationship_id", unique=True),
        Index("ix_g4_ctx_org", "organization_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    relationship_id = db.Column(
        db.Integer, db.ForeignKey("rel_relationships.id"), nullable=False, unique=True
    )

    # ── Commercial summary (AI enriched) ──
    summary = db.Column(db.Text, default="")
    active_opportunity_id = db.Column(
        db.Integer, db.ForeignKey("g4_opportunities.id"), nullable=True
    )

    # ── Commercial signals ──
    engagement_level = db.Column(db.Integer, default=50)  # 0-100
    relationship_health = db.Column(db.Integer, default=50)  # 0-100
    lifetime_value_estimate = db.Column(Numeric(15, 2), default=0)
    retention_risk = db.Column(db.Integer, default=50)  # 0-100

    # ── Next best action (AI-informed) ──
    suggested_next_action = db.Column(db.Text, default="")
    suggested_action_reason = db.Column(db.Text, default="")
    suggested_at = db.Column(db.DateTime, nullable=True)

    # ── Metadata ──
    tags = db.Column(db.Text, default="[]")
    signals_json = db.Column(db.Text, default="{}")

    # ── Timestamps ──
    last_interaction_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        import json
        opp = None
        if self.active_opportunity_id:
            opp_obj = db.session.get(CommercialOpportunity, self.active_opportunity_id)
            if opp_obj:
                opp = opp_obj.to_dict()
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "relationship_id": self.relationship_id,
            "summary": self.summary,
            "active_opportunity": opp,
            "engagement_level": self.engagement_level,
            "relationship_health": self.relationship_health,
            "lifetime_value_estimate": float(self.lifetime_value_estimate or 0),
            "retention_risk": self.retention_risk,
            "suggested_next_action": self.suggested_next_action,
            "suggested_action_reason": (self.suggested_action_reason or "")[:200],
            "suggested_at": self.suggested_at.isoformat() if self.suggested_at else None,
            "tags": json.loads(self.tags or "[]"),
            "signals": json.loads(self.signals_json or "{}"),
            "last_interaction_at": self.last_interaction_at.isoformat() if self.last_interaction_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ══════════════════════════════════════════════════════════════════════
# CANONICAL PROPOSAL / OFFER
# ══════════════════════════════════════════════════════════════════════

PROPOSAL_LIFECYCLE = [
    "draft",
    "ai_generating",
    "review",
    "sent",
    "viewed",
    "negotiating",
    "accepted",
    "declined",
    "withdrawn",
    "expired",
]


class CommercialProposal(db.Model):
    """A canonical commercial proposal or offer.

    One representation that renderers can consume:
    - PDF
    - smart document
    - email
    - web presentation
    - message

    Preserves: source context, assumptions, scope, value/price, validity,
    exclusions, decisions required, evidence/provenance.
    """

    __tablename__ = "g4_proposals"
    __table_args__ = (
        Index("ix_g4_prop_org", "organization_id"),
        Index("ix_g4_prop_opp", "opportunity_id"),
        Index("ix_g4_prop_status", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False, index=True
    )
    relationship_id = db.Column(
        db.Integer, db.ForeignKey("rel_relationships.id"), nullable=True
    )
    opportunity_id = db.Column(
        db.Integer, db.ForeignKey("g4_opportunities.id"), nullable=True, index=True
    )
    version_number = db.Column(db.Integer, default=1, nullable=False)

    # ── Core ──
    title = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(30), default="draft", nullable=False)
    proposal_type = db.Column(db.String(60), default="proposal")

    # ── Scope & Context ──
    scope_description = db.Column(db.Text, default="")
    assumptions = db.Column(db.Text, default="")
    exclusions = db.Column(db.Text, default="")

    # ── Value & Pricing ──
    currency = db.Column(db.String(10), default="INR")
    subtotal = db.Column(Numeric(15, 2), default=0)
    tax_amount = db.Column(Numeric(15, 2), default=0)
    discount_amount = db.Column(Numeric(15, 2), default=0)
    total_value = db.Column(Numeric(15, 2), default=0)
    pricing_structure = db.Column(db.Text, default="[]")  # JSON: line items

    # ── Validity ──
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    delivery_timeline = db.Column(db.Text, default="")

    # ── Terms ──
    terms = db.Column(db.Text, default="")
    conditions = db.Column(db.Text, default="")
    decisions_required = db.Column(db.Text, default="[]")

    # ── Provenance ──
    source_context = db.Column(db.Text, default="")  # What informed this proposal
    ai_generated = db.Column(db.Boolean, default=False)
    ai_model = db.Column(db.String(100), default="")
    ai_prompt = db.Column(db.Text, default="")
    evidence_refs = db.Column(db.Text, default="[]")  # JSON: evidence UUIDs

    # ── Rendering artifacts ──
    rendered_html = db.Column(db.Text, default="")
    rendered_pdf_path = db.Column(db.String(500), default="")

    # ── Communication ──
    sent_at = db.Column(db.DateTime, nullable=True)
    sent_via = db.Column(db.String(30), default="")
    viewed_at = db.Column(db.DateTime, nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    decision_id = db.Column(db.String(64), nullable=True)
    commitment_id = db.Column(db.String(64), nullable=True)  # ref to Commitment

    # ── History ──
    rejection_reason = db.Column(db.Text, default="")

    # ── Audit ──
    created_by = db.Column(db.String(64), default="")
    updated_by = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "relationship_id": self.relationship_id,
            "opportunity_id": self.opportunity_id,
            "version_number": self.version_number,
            "title": self.title,
            "status": self.status,
            "proposal_type": self.proposal_type,
            "scope_description": (self.scope_description or "")[:500],
            "assumptions": (self.assumptions or "")[:500],
            "exclusions": (self.exclusions or "")[:500],
            "currency": self.currency,
            "subtotal": float(self.subtotal or 0),
            "tax_amount": float(self.tax_amount or 0),
            "discount_amount": float(self.discount_amount or 0),
            "total_value": float(self.total_value or 0),
            "pricing_structure": json.loads(self.pricing_structure or "[]"),
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "delivery_timeline": self.delivery_timeline,
            "terms": (self.terms or "")[:500],
            "conditions": (self.conditions or "")[:500],
            "decisions_required": json.loads(self.decisions_required or "[]"),
            "source_context": (self.source_context or "")[:500],
            "ai_generated": self.ai_generated,
            "evidence_refs": json.loads(self.evidence_refs or "[]"),
            "rendered_pdf_path": self.rendered_pdf_path,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent_via": self.sent_via,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "decision_id": self.decision_id,
            "commitment_id": self.commitment_id,
            "rejection_reason": self.rejection_reason,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "can_accept": self.status == "sent",
            "can_decline": self.status in ("sent", "negotiating"),
        }

    @property
    def can_accept(self) -> bool:
        return self.status == "sent"

    @property
    def can_decline(self) -> bool:
        return self.status in ("sent", "negotiating")


# ══════════════════════════════════════════════════════════════════════
# LIFECYCLE TRANSITION (audit log)
# ══════════════════════════════════════════════════════════════════════


class CommercialTransition(db.Model):
    """Immutable audit log of every commercial lifecycle transition.

    Every state change in the commercial path is recorded here.
    Nothing is deleted — only appended. Governed correction is allowed
    through an explicit correction event with reason.
    """

    __tablename__ = "g4_transitions"
    __table_args__ = (
        Index("ix_g4_tr_entity", "organization_id", "entity_type", "entity_id"),
        Index("ix_g4_tr_time", "organization_id", "transitioned_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=False
    )
    entity_type = db.Column(db.String(30), nullable=False)  # "opportunity" or "proposal"
    entity_id = db.Column(db.Integer, nullable=False, index=True)

    from_state = db.Column(db.String(40), nullable=False)
    to_state = db.Column(db.String(40), nullable=False)
    reason = db.Column(db.Text, default="")
    is_correction = db.Column(db.Boolean, default=False)
    correction_reason = db.Column(db.Text, default="")

    triggered_by = db.Column(db.String(64), default="")
    transitioned_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "reason": self.reason,
            "is_correction": self.is_correction,
            "correction_reason": self.correction_reason,
            "triggered_by": self.triggered_by,
            "transitioned_at": self.transitioned_at.isoformat() if self.transitioned_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL TYPE (config-driven vocabulary)
# ══════════════════════════════════════════════════════════════════════


class CommercialType(db.Model):
    """Config-driven commercial vocabulary.

    Organizations define their own business vocabulary here.
    One business calls it "Lead", another calls it "Enquiry", a third
    calls it "Opportunity". The canonical model remains universal.
    """

    __tablename__ = "g4_types"
    __table_args__ = (
        Index("ix_g4_type_org", "organization_id"),
        Index("ix_g4_type_org_key", "organization_id", "type_key", unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=True
    )
    domain = db.Column(db.String(30), nullable=False)  # "opportunity" or "proposal"
    type_key = db.Column(db.String(60), nullable=False)
    display_label = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(60), default="trending-up")
    color = db.Column(db.String(20), default="#6366f1")
    is_default = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))