"""
G5 — Universal Growth Service Layer.

Reuses:
- Campaign model (app/marketing/models.py) — canonical campaign root
- G4 commercial models (app/commercial/models.py) — for the revenue/outcome bridge
- TouchpointInteraction — multi-touch persistence
- AttributeTouch — canonical attribution with evidence
- CampaignEvent — event-driven lifecycle
- GrowthLearning — grounded insights

Do NOT duplicate existing lead/opportunity CRUD from G4.
Do NOT create a parallel campaign CRUD system — existing marketing_os handles that.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from decimal import Decimal
import json

from app import db
from app.marketing.models import Campaign
from app.commercial.models import CommercialOpportunity, CommercialProposal
from app.g5.models import (
    CampaignEvent,
    TouchpointInteraction,
    AttributeTouch,
    GrowthLearning,
    ATTRIBUTION_STATES,
    CAMPAIGN_EVENT_TYPES,
    INTERACTION_TYPES,
    LEARNING_CATEGORIES,
)


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGN EVENTS
# ══════════════════════════════════════════════════════════════════════


def record_campaign_event(
    campaign_id: int,
    tenant_id: int,
    event_type: str,
    description: str = "",
    previous_state: str = "",
    new_state: str = "",
    trigger_source: str = "system",
    evidence_ref: str = "",
    payload: Optional[dict] = None,
    created_by: str = "",
) -> dict:
    """Record a campaign lifecycle event. Append-only, no overwrites."""
    if event_type not in CAMPAIGN_EVENT_TYPES:
        event_type = "campaign_assessment"

    event = CampaignEvent(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        event_type=event_type,
        previous_state=previous_state,
        new_state=new_state,
        description=description or "",
        trigger_source=trigger_source,
        evidence_ref=evidence_ref or "",
        payload_json=json.dumps(payload or {}),
        created_by=created_by or "",
    )
    db.session.add(event)
    db.session.commit()
    return event.to_dict()


def get_campaign_events(
    campaign_id: int,
    tenant_id: int,
    event_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    q = CampaignEvent.query.filter_by(
        campaign_id=campaign_id, tenant_id=tenant_id
    )
    if event_type:
        q = q.filter_by(event_type=event_type)
    events = (
        q.order_by(CampaignEvent.occurred_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [e.to_dict() for e in events]


# ══════════════════════════════════════════════════════════════════════
# TOUCHPOINT INTERACTIONS (multi-touch)
# ══════════════════════════════════════════════════════════════════════


def record_interaction(
    tenant_id: int,
    interaction_type: str = "first_discovery",
    campaign_id: Optional[int] = None,
    identity_ref: str = "",
    person_name: str = "",
    person_email: str = "",
    relationship_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    source: str = "",
    channel: str = "",
    referrer: str = "",
    utm_source: str = "",
    utm_medium: str = "",
    utm_campaign: str = "",
    utm_term: str = "",
    utm_content: str = "",
    session_ref: str = "",
    tracking_id: str = "",
    description: str = "",
    engagement_duration_seconds: Optional[int] = None,
    engagement_depth: int = 0,
    content_ref: str = "",
    evidence: Optional[dict] = None,
    source_confidence: int = 50,
    occurred_at: Optional[str] = None,
    recorded_by: str = "",
) -> dict:
    """Record a single interaction/touchpoint. Multiple per identity expected."""
    if interaction_type not in INTERACTION_TYPES:
        interaction_type = "other"

    occ = None
    if occurred_at:
        try:
            occ = datetime.fromisoformat(occurred_at)
        except (ValueError, TypeError):
            occ = datetime.now(timezone.utc)

    interaction = TouchpointInteraction(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        identity_ref=identity_ref or "",
        person_name=person_name or "",
        person_email=person_email or "",
        relationship_id=relationship_id,
        organization_id=organization_id,
        interaction_type=interaction_type,
        description=description or "",
        source=source or "",
        channel=channel or "",
        referrer=referrer or "",
        utm_source=utm_source or "",
        utm_medium=utm_medium or "",
        utm_campaign=utm_campaign or "",
        utm_term=utm_term or "",
        utm_content=utm_content or "",
        session_ref=session_ref or "",
        tracking_id=tracking_id or "",
        engagement_duration_seconds=engagement_duration_seconds,
        engagement_depth=engagement_depth or 0,
        content_ref=content_ref or "",
        evidence_json=json.dumps(evidence or {}),
        source_confidence=source_confidence or 50,
        occurred_at=occ or datetime.now(timezone.utc),
        recorded_by=recorded_by or "",
    )
    db.session.add(interaction)
    db.session.commit()
    return interaction.to_dict()


def get_interactions(
    tenant_id: int,
    campaign_id: Optional[int] = None,
    identity_ref: Optional[str] = None,
    relationship_id: Optional[int] = None,
    interaction_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    """Retrieve interactions with optional filters. Always tenant-safe."""
    q = TouchpointInteraction.query.filter_by(tenant_id=tenant_id)
    if campaign_id:
        q = q.filter_by(campaign_id=campaign_id)
    if identity_ref:
        q = q.filter_by(identity_ref=identity_ref)
    if relationship_id:
        q = q.filter_by(relationship_id=relationship_id)
    if interaction_type:
        q = q.filter_by(interaction_type=interaction_type)
    interactions = (
        q.order_by(TouchpointInteraction.occurred_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [i.to_dict() for i in interactions]


def get_interactions_by_identity(
    tenant_id: int, identity_ref: str, limit: int = 50
) -> list:
    """Get all interactions for a given identity (person)."""
    return get_interactions(
        tenant_id=tenant_id, identity_ref=identity_ref, limit=limit
    )


# ══════════════════════════════════════════════════════════════════════
# CANONICAL ATTRIBUTION
# ══════════════════════════════════════════════════════════════════════


def create_attribution(
    tenant_id: int,
    target_type: str,
    target_id: int,
    campaign_id: Optional[int] = None,
    source: str = "",
    source_ref: str = "",
    channel: str = "",
    content_ref: str = "",
    utm_source: str = "",
    utm_medium: str = "",
    utm_campaign: str = "",
    utm_term: str = "",
    utm_content: str = "",
    attribution_state: str = "unknown",
    confidence: int = 50,
    evidence_summary: str = "",
    identity_ref: str = "",
    relationship_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    proposal_id: Optional[int] = None,
    outcome_id: Optional[int] = None,
    revenue_amount: Optional[float] = None,
    is_revenue_outcome: bool = False,
    evidence: Optional[dict] = None,
    interaction_id: Optional[int] = None,
    is_first_known: bool = False,
    target_description: str = "",
    created_by: str = "",
) -> dict:
    """Create a single attribution record.

    Does NOT overwrite existing attribution. New evidence creates a
    new record. Historical attributions remain intact.
    """
    if attribution_state not in ATTRIBUTION_STATES:
        attribution_state = "unknown"

    attr = AttributeTouch(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        target_type=target_type,
        target_id=target_id,
        target_description=target_description or "",
        source=source or "",
        source_ref=source_ref or "",
        channel=channel or "",
        content_ref=content_ref or "",
        utm_source=utm_source or "",
        utm_medium=utm_medium or "",
        utm_campaign=utm_campaign or "",
        utm_term=utm_term or "",
        utm_content=utm_content or "",
        attribution_state=attribution_state,
        confidence=confidence or 50,
        evidence_summary=evidence_summary or "",
        identity_ref=identity_ref or "",
        relationship_id=relationship_id,
        organization_id=organization_id,
        opportunity_id=opportunity_id,
        proposal_id=proposal_id,
        outcome_id=outcome_id,
        revenue_amount=Decimal(str(revenue_amount)) if revenue_amount is not None else None,
        is_revenue_outcome=is_revenue_outcome or False,
        evidence_json=json.dumps(evidence or {}),
        interaction_id=interaction_id,
        is_first_known=is_first_known or False,
        attribution_policy="evidenced",
        created_by=created_by or "",
    )
    db.session.add(attr)
    db.session.commit()

    # Fire campaign event for attribution change
    if campaign_id:
        record_campaign_event(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            event_type="attribution_changed",
            description=f"Attribution {attribution_state} for {target_type} #{target_id}",
            trigger_source="system",
            evidence_ref=f"attribution_{attr.id}",
        )

    return attr.to_dict()


def get_attributions(
    tenant_id: int,
    campaign_id: Optional[int] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    identity_ref: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    """Get attribution records. Never silently overwritten — returns all."""
    q = AttributeTouch.query.filter_by(tenant_id=tenant_id)
    if campaign_id:
        q = q.filter_by(campaign_id=campaign_id)
    if target_type:
        q = q.filter_by(target_type=target_type)
    if target_id:
        q = q.filter_by(target_id=target_id)
    if identity_ref:
        q = q.filter_by(identity_ref=identity_ref)
    attributions = (
        q.order_by(AttributeTouch.attributed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [a.to_dict() for a in attributions]


def get_attribution_chain(
    campaign_id: int, tenant_id: int
) -> dict:
    """Get the full attribution chain for a campaign.

    Returns:
    - First known source
    - All interactions
    - Attributions to relationships
    - Attributions to opportunities (G4 bridge)
    - Revenue/proposal outcomes
    - Learning
    """
    campaign = Campaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    if not campaign:
        return {"error": "Campaign not found", "campaign_id": campaign_id}

    attributions = get_attributions(tenant_id=tenant_id, campaign_id=campaign_id)
    interactions = get_interactions(tenant_id=tenant_id, campaign_id=campaign_id)

    # Find first known source
    first_known = [
        a for a in attributions if a.get("is_first_known")
    ]

    # Revenue outcomes
    revenue_attrs = [
        a for a in attributions if a.get("is_revenue_outcome")
    ]

    # G4 opportunities linked to this campaign
    opportunities = CommercialOpportunity.query.filter_by(
        campaign_id=campaign_id
    ).all()

    # Proposals from those opportunities
    opp_ids = [o.id for o in opportunities]
    proposals = []
    if opp_ids:
        proposals = CommercialProposal.query.filter(
            CommercialProposal.opportunity_id.in_(opp_ids)
        ).all()

    # Learning
    learnings = GrowthLearning.query.filter_by(
        campaign_id=campaign_id, tenant_id=tenant_id
    ).order_by(GrowthLearning.observed_at.desc()).limit(20).all()

    return {
        "campaign": {
            "id": campaign.id,
            "name": campaign.name,
            "objective": campaign.objective,
            "status": campaign.status,
        },
        "first_known_source": first_known,
        "total_attributions": len(attributions),
        "attributions": attributions[:50],
        "total_interactions": len(interactions),
        "interactions": interactions[:50],
        "first_known_source": first_known[:5] if first_known else [],
        "g4_opportunities": [o.to_dict() for o in opportunities],
        "g4_proposals": [p.to_dict() for p in proposals],
        "revenue_attributions": revenue_attrs,
        "total_revenue": sum(
            float(a.get("revenue_amount", 0) or 0)
            for a in revenue_attrs
        ),
        "learnings": [l.to_dict() for l in learnings],
    }


# ══════════════════════════════════════════════════════════════════════
# GROWTH LEARNING
# ══════════════════════════════════════════════════════════════════════


def create_learning(
    tenant_id: int,
    category: str = "campaign_performance",
    title: str = "",
    observation: str = "",
    significance: str = "normal",
    evidence_summary: str = "",
    evidence_refs: Optional[list] = None,
    confidence: int = 50,
    data_source: str = "shunya_internal",
    campaign_id: Optional[int] = None,
    attribution_id: Optional[int] = None,
    interaction_id: Optional[int] = None,
    outcome_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    recommendation: str = "",
    recommendation_confidence: int = 50,
    recommendation_action: str = "",
    is_actionable: bool = False,
    external_source: str = "",
    external_retrieved_at: Optional[str] = None,
    external_context: str = "",
    created_by: str = "",
) -> dict:
    """Create a learning record grounded in actual data.

    If evidence is insufficient, set confidence low (or 0) and
    set category to 'insufficient_evidence'.
    """
    import json

    if category not in LEARNING_CATEGORIES:
        category = "insufficient_evidence"

    ext_retrieved = None
    if external_retrieved_at:
        try:
            ext_retrieved = datetime.fromisoformat(external_retrieved_at)
        except (ValueError, TypeError):
            pass

    learning = GrowthLearning(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        category=category,
        title=title or "",
        observation=observation or "",
        significance=significance or "normal",
        evidence_summary=evidence_summary or "",
        evidence_refs=json.dumps(evidence_refs or []),
        confidence=confidence or 50,
        data_source=data_source or "shunya_internal",
        attribution_id=attribution_id,
        interaction_id=interaction_id,
        outcome_id=outcome_id,
        opportunity_id=opportunity_id,
        recommendation=recommendation or "",
        recommendation_confidence=recommendation_confidence or 50,
        recommendation_action=recommendation_action or "",
        is_actionable=is_actionable or False,
        external_source=external_source or "",
        external_retrieved_at=ext_retrieved,
        external_context=external_context or "",
        created_by=created_by or "",
    )
    db.session.add(learning)
    db.session.commit()

    # Fire campaign event for learning
    if campaign_id:
        record_campaign_event(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            event_type="learning_available",
            description=f"Learning: {title}",
            trigger_source="intelligence",
            evidence_ref=f"learning_{learning.id}",
        )

    return learning.to_dict()


def get_learnings(
    tenant_id: int,
    campaign_id: Optional[int] = None,
    category: Optional[str] = None,
    significance: Optional[str] = None,
    is_actionable: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    q = GrowthLearning.query.filter_by(tenant_id=tenant_id)
    if campaign_id:
        q = q.filter_by(campaign_id=campaign_id)
    if category:
        q = q.filter_by(category=category)
    if significance:
        q = q.filter_by(significance=significance)
    if is_actionable is not None:
        q = q.filter_by(is_actionable=is_actionable)
    learnings = (
        q.order_by(GrowthLearning.observed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [l.to_dict() for l in learnings]


# ══════════════════════════════════════════════════════════════════════
# G4 → G5 INTEGRATION: bridge campaign to commercial outcome
# ══════════════════════════════════════════════════════════════════════


def attribute_opportunity_to_campaign(
    opportunity_id: int,
    campaign_id: int,
    tenant_id: int,
    confidence: int = 50,
    attribution_state: str = "plausibly_attributable",
    evidence_summary: str = "",
    created_by: str = "",
) -> Optional[dict]:
    """Link a G4 CommercialOpportunity to a G5 campaign via attribution."""
    opp = CommercialOpportunity.query.get(opportunity_id)
    if not opp:
        return None
    campaign = Campaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    if not campaign:
        return None

    # Update the opportunity's campaign_id (G4 already supports this)
    opp.campaign_id = campaign_id
    db.session.commit()

    # Create attribution record
    attr = create_attribution(
        tenant_id=tenant_id,
        target_type="opportunity",
        target_id=opportunity_id,
        campaign_id=campaign_id,
        source=campaign.utm_source or "campaign",
        utm_source=campaign.utm_source or "",
        utm_medium=campaign.utm_medium or "",
        utm_campaign=campaign.utm_campaign or "",
        attribution_state=attribution_state,
        confidence=confidence,
        evidence_summary=evidence_summary or f"Campaign \"{campaign.name}\" → Opportunity \"{opp.title}\"",
        opportunity_id=opportunity_id,
        created_by=created_by,
    )

    return attr


def attribute_outcome_to_campaign(
    opportunity_id: int,
    proposal_id: int,
    campaign_id: int,
    tenant_id: int,
    revenue_amount: Optional[float] = None,
    confidence: int = 50,
    attribution_state: str = "strongly_attributable",
    created_by: str = "",
) -> Optional[dict]:
    """Link a commercial outcome/proposal to a campaign via attribution."""
    proposal = CommercialProposal.query.get(proposal_id)
    if not proposal:
        return None

    attr = create_attribution(
        tenant_id=tenant_id,
        target_type="proposal",
        target_id=proposal_id,
        campaign_id=campaign_id,
        target_description=f"Proposal: {proposal.title}",
        source="campaign_conversion",
        attribution_state=attribution_state,
        confidence=confidence,
        opportunity_id=opportunity_id,
        proposal_id=proposal_id,
        revenue_amount=revenue_amount,
        is_revenue_outcome=revenue_amount is not None,
        created_by=created_by,
    )

    # Fire conversion event
    if revenue_amount:
        record_campaign_event(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            event_type="conversion_occurred",
            description=f"Revenue outcome: {revenue_amount} from proposal #{proposal_id}",
            trigger_source="system",
            evidence_ref=f"proposal_{proposal_id}",
            payload={"revenue_amount": revenue_amount, "proposal_id": proposal_id},
        )

    return attr


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGN INTELLIGENCE — grounded questions
# ══════════════════════════════════════════════════════════════════════


def campaign_intelligence(
    campaign_id: int, tenant_id: int
) -> dict:
    """Answer the key questions for a campaign.

    What is working?
    What is not working?
    Where are responses increasing?
    Where are conversions weak?
    Which campaign produces meaningful downstream value?
    Where is money/time being spent without outcome?

    All answers are grounded in actual SHUNYA data.
    If insufficient evidence, says so.
    """
    campaign = Campaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    if not campaign:
        return {"error": "Campaign not found"}

    interactions = get_interactions(tenant_id=tenant_id, campaign_id=campaign_id)
    learnings = get_learnings(tenant_id=tenant_id, campaign_id=campaign_id)
    attributions = get_attributions(tenant_id=tenant_id, campaign_id=campaign_id)
    events = get_campaign_events(campaign_id=campaign_id, tenant_id=tenant_id)

    # Count interactions by type
    from collections import Counter
    type_counts = Counter(i.get("interaction_type") for i in interactions)
    source_counts = Counter(i.get("source") for i in interactions)

    # Count outcomes
    revenue_attrs = [a for a in attributions if a.get("is_revenue_outcome")]
    total_revenue = sum(float(a.get("revenue_amount", 0) or 0) for a in revenue_attrs)
    budget = float(campaign.budget or 0)

    # Actionable recommendations
    actionable_learnings = [l for l in learnings if l.get("is_actionable")]

    # Assess
    has_response = len(interactions) > 0
    has_conversion = len(revenue_attrs) > 0
    has_learning = len(learnings) > 0
    roi_known = budget > 0 and total_revenue > 0

    return {
        "campaign": {
            "id": campaign.id,
            "name": campaign.name,
            "objective": campaign.objective,
            "status": campaign.status,
            "budget": str(budget),
        },
        "assessment": {
            "has_response": has_response,
            "has_conversion": has_conversion,
            "has_learning": has_learning,
            "roi_known": roi_known,
            "total_interactions": len(interactions),
            "total_attributions": len(attributions),
            "total_revenue": str(total_revenue),
            "roi": str(round(total_revenue / budget, 2)) if budget > 0 else "N/A",
        },
        "interaction_summary": {
            "by_type": dict(type_counts.most_common(10)),
            "by_source": dict(source_counts.most_common(10)),
        },
        "what_is_working": [
            l for l in learnings
            if l.get("significance") in ("significant", "critical")
            and l.get("confidence", 0) >= 60
        ][:5],
        "what_needs_attention": [
            l for l in learnings
            if l.get("category") in ("waste_detection", "insufficient_evidence")
            or (l.get("significance") == "critical" and l.get("confidence", 0) < 50)
        ][:5],
        "actionable_recommendations": actionable_learnings[:5],
        "recent_events": events[:10],
        "insufficient_evidence": not has_response and not has_conversion,
        "confidence_summary": (
            "sufficient" if has_response or has_conversion
            else "insufficient"
        ),
    }


# ══════════════════════════════════════════════════════════════════════
# MULTI-TOUCH ATTRIBUTION (orchestrated)
# ══════════════════════════════════════════════════════════════════════


def multi_touch_attribution_for_identity(
    identity_ref: str, tenant_id: int
) -> dict:
    """Build the multi-touch story for a single identity.

    Returns all known touchpoints, campaign associations, and outcomes.
    Does NOT fabricate a single-source attribution where evidence is weak.
    """
    interactions = get_interactions_by_identity(tenant_id, identity_ref)

    # Group interactions by campaign
    from collections import defaultdict
    by_campaign: dict = defaultdict(list)
    for i in interactions:
        cid = i.get("campaign_id")
        if cid:
            by_campaign[str(cid)].append(i)

    # Get attributions for this identity
    attributions = get_attributions(
        tenant_id=tenant_id, identity_ref=identity_ref
    )

    # Get relationship if known
    relationship = None
    relationship_id = None
    for i in interactions:
        if i.get("relationship_id"):
            relationship_id = i["relationship_id"]
            break

    return {
        "identity_ref": identity_ref,
        "total_touchpoints": len(interactions),
        "touchpoints": interactions[:50],
        "campaigns_touched": list(by_campaign.keys()),
        "attributions": attributions[:50],
        "first_touch": interactions[-1] if interactions else None,
        "last_touch": interactions[0] if interactions else None,
        "relationship_id": relationship_id,
    }