"""
G5 — Universal Marketing, Growth, Attribution & Learning API Routes.

Uses existing workspace architecture. No parallel frontend.
Integrates with G4 commercial routes for the full end-to-end path.
"""

from datetime import datetime
from flask import Blueprint, jsonify, request

from app import db
from app.marketing.models import Campaign
from app.g5.service import (
    record_campaign_event,
    get_campaign_events,
    record_interaction,
    get_interactions,
    create_attribution,
    get_attributions,
    get_attribution_chain,
    create_learning,
    get_learnings,
    attribute_opportunity_to_campaign,
    attribute_outcome_to_campaign,
    campaign_intelligence,
    multi_touch_attribution_for_identity,
)

g5_bp = Blueprint("g5", __name__, url_prefix="/api/v1/growth")


def _resolve_tenant():
    """Resolve tenant from session or request."""
    from flask import session
    # Check session's current_org_id first (set by signin route)
    org_id = session.get("current_org_id")
    if org_id:
        return org_id
    return request.args.get("tenant_id", 1, type=int)


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGN EVENTS
# ══════════════════════════════════════════════════════════════════════


@g5_bp.route("/campaigns/<int:cid>/events", methods=["GET"])
def list_campaign_events(cid):
    """Get campaign event stream."""
    tenant_id = _resolve_tenant()
    event_type = request.args.get("event_type")
    limit = min(request.args.get("limit", 50, type=int), 100)
    offset = request.args.get("offset", 0, type=int)
    events = get_campaign_events(
        campaign_id=cid,
        tenant_id=tenant_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    return jsonify({"success": True, "events": events})


@g5_bp.route("/campaigns/<int:cid>/events", methods=["POST"])
def create_campaign_event(cid):
    """Record a campaign lifecycle event."""
    tenant_id = _resolve_tenant()
    data = request.get_json() or {}
    event = record_campaign_event(
        campaign_id=cid,
        tenant_id=tenant_id,
        event_type=data.get("event_type", "campaign_assessment"),
        description=data.get("description", ""),
        previous_state=data.get("previous_state", ""),
        new_state=data.get("new_state", ""),
        trigger_source=data.get("trigger_source", "system"),
        evidence_ref=data.get("evidence_ref", ""),
        payload=data.get("payload"),
        created_by=data.get("created_by", ""),
    )
    return jsonify({"success": True, "event": event}), 201


# ══════════════════════════════════════════════════════════════════════
# MULTI-TOUCH INTERACTIONS
# ══════════════════════════════════════════════════════════════════════


@g5_bp.route("/interactions", methods=["GET"])
def list_interactions():
    """List touchpoint interactions with optional filters."""
    tenant_id = _resolve_tenant()
    campaign_id = request.args.get("campaign_id", type=int)
    identity_ref = request.args.get("identity_ref")
    relationship_id = request.args.get("relationship_id", type=int)
    interaction_type = request.args.get("interaction_type")
    limit = min(request.args.get("limit", 50, type=int), 100)
    offset = request.args.get("offset", 0, type=int)
    interactions = get_interactions(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        identity_ref=identity_ref,
        relationship_id=relationship_id,
        interaction_type=interaction_type,
        limit=limit,
        offset=offset,
    )
    return jsonify({"success": True, "interactions": interactions})


@g5_bp.route("/interactions", methods=["POST"])
def record_new_interaction():
    """Record a new touchpoint interaction."""
    tenant_id = _resolve_tenant()
    data = request.get_json() or {}
    interaction = record_interaction(
        tenant_id=tenant_id,
        interaction_type=data.get("interaction_type", "first_discovery"),
        campaign_id=data.get("campaign_id"),
        identity_ref=data.get("identity_ref", ""),
        person_name=data.get("person_name", ""),
        person_email=data.get("person_email", ""),
        relationship_id=data.get("relationship_id"),
        organization_id=data.get("organization_id"),
        source=data.get("source", ""),
        channel=data.get("channel", ""),
        referrer=data.get("referrer", ""),
        utm_source=data.get("utm_source", ""),
        utm_medium=data.get("utm_medium", ""),
        utm_campaign=data.get("utm_campaign", ""),
        utm_term=data.get("utm_term", ""),
        utm_content=data.get("utm_content", ""),
        session_ref=data.get("session_ref", ""),
        tracking_id=data.get("tracking_id", ""),
        description=data.get("description", ""),
        engagement_duration_seconds=data.get("engagement_duration_seconds"),
        engagement_depth=data.get("engagement_depth", 0),
        content_ref=data.get("content_ref", ""),
        evidence=data.get("evidence"),
        source_confidence=data.get("source_confidence", 50),
        occurred_at=data.get("occurred_at"),
        recorded_by=data.get("recorded_by", ""),
    )
    return jsonify({"success": True, "interaction": interaction}), 201


@g5_bp.route("/interactions/by-identity/<path:identity_ref>", methods=["GET"])
def interactions_by_identity(identity_ref):
    """Get all interactions for a given identity (person)."""
    tenant_id = _resolve_tenant()
    limit = min(request.args.get("limit", 50, type=int), 100)
    from app.g5.service import get_interactions_by_identity
    interactions = get_interactions_by_identity(
        tenant_id=tenant_id, identity_ref=identity_ref, limit=limit
    )
    return jsonify({"success": True, "identity_ref": identity_ref, "interactions": interactions})


# ══════════════════════════════════════════════════════════════════════
# CANONICAL ATTRIBUTION
# ══════════════════════════════════════════════════════════════════════


@g5_bp.route("/attributions", methods=["GET"])
def list_attributions():
    """List attribution records."""
    tenant_id = _resolve_tenant()
    campaign_id = request.args.get("campaign_id", type=int)
    target_type = request.args.get("target_type")
    target_id = request.args.get("target_id", type=int)
    identity_ref = request.args.get("identity_ref")
    limit = min(request.args.get("limit", 50, type=int), 100)
    offset = request.args.get("offset", 0, type=int)
    attributions = get_attributions(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        target_type=target_type,
        target_id=target_id,
        identity_ref=identity_ref,
        limit=limit,
        offset=offset,
    )
    return jsonify({"success": True, "attributions": attributions})


@g5_bp.route("/attributions", methods=["POST"])
def create_new_attribution():
    """Create an attribution record."""
    tenant_id = _resolve_tenant()
    data = request.get_json() or {}
    attr = create_attribution(
        tenant_id=tenant_id,
        target_type=data.get("target_type", "interaction"),
        target_id=data.get("target_id"),
        campaign_id=data.get("campaign_id"),
        source=data.get("source", ""),
        source_ref=data.get("source_ref", ""),
        channel=data.get("channel", ""),
        content_ref=data.get("content_ref", ""),
        utm_source=data.get("utm_source", ""),
        utm_medium=data.get("utm_medium", ""),
        utm_campaign=data.get("utm_campaign", ""),
        utm_term=data.get("utm_term", ""),
        utm_content=data.get("utm_content", ""),
        attribution_state=data.get("attribution_state", "unknown"),
        confidence=data.get("confidence", 50),
        evidence_summary=data.get("evidence_summary", ""),
        identity_ref=data.get("identity_ref", ""),
        relationship_id=data.get("relationship_id"),
        organization_id=data.get("organization_id"),
        opportunity_id=data.get("opportunity_id"),
        proposal_id=data.get("proposal_id"),
        outcome_id=data.get("outcome_id"),
        revenue_amount=data.get("revenue_amount"),
        is_revenue_outcome=data.get("is_revenue_outcome", False),
        evidence=data.get("evidence"),
        interaction_id=data.get("interaction_id"),
        is_first_known=data.get("is_first_known", False),
        target_description=data.get("target_description", ""),
        created_by=data.get("created_by", ""),
    )
    return jsonify({"success": True, "attribution": attr}), 201


@g5_bp.route("/attributions/chain/<int:campaign_id>", methods=["GET"])
def attribution_chain(campaign_id):
    """Get the full attribution chain for a campaign."""
    tenant_id = _resolve_tenant()
    chain = get_attribution_chain(campaign_id, tenant_id)
    return jsonify({"success": True, "chain": chain})


@g5_bp.route("/attributions/multi-touch", methods=["GET"])
def multi_touch_attribution():
    """Get multi-touch attribution for an identity."""
    tenant_id = _resolve_tenant()
    identity_ref = request.args.get("identity_ref")
    if not identity_ref:
        return jsonify({"error": "identity_ref is required"}), 400
    result = multi_touch_attribution_for_identity(identity_ref, tenant_id)
    return jsonify({"success": True, "multi_touch": result})


# ══════════════════════════════════════════════════════════════════════
# G4 → G5 INTEGRATION
# ══════════════════════════════════════════════════════════════════════


@g5_bp.route("/integrate/opportunity", methods=["POST"])
def integrate_opportunity():
    """Link a G4 CommercialOpportunity to a campaign."""
    tenant_id = _resolve_tenant()
    data = request.get_json() or {}
    result = attribute_opportunity_to_campaign(
        opportunity_id=data.get("opportunity_id"),
        campaign_id=data.get("campaign_id"),
        tenant_id=tenant_id,
        confidence=data.get("confidence", 50),
        attribution_state=data.get("attribution_state", "plausibly_attributable"),
        evidence_summary=data.get("evidence_summary", ""),
        created_by=data.get("created_by", ""),
    )
    if not result:
        return jsonify({"error": "Opportunity or Campaign not found"}), 404
    return jsonify({"success": True, "attribution": result}), 201


@g5_bp.route("/integrate/outcome", methods=["POST"])
def integrate_outcome():
    """Link a commercial outcome/proposal to a campaign."""
    tenant_id = _resolve_tenant()
    data = request.get_json() or {}
    result = attribute_outcome_to_campaign(
        opportunity_id=data.get("opportunity_id"),
        proposal_id=data.get("proposal_id"),
        campaign_id=data.get("campaign_id"),
        tenant_id=tenant_id,
        revenue_amount=data.get("revenue_amount"),
        confidence=data.get("confidence", 50),
        attribution_state=data.get("attribution_state", "strongly_attributable"),
        created_by=data.get("created_by", ""),
    )
    if not result:
        return jsonify({"error": "Proposal not found"}), 404
    return jsonify({"success": True, "attribution": result}), 201


# ══════════════════════════════════════════════════════════════════════
# GROWTH LEARNING
# ══════════════════════════════════════════════════════════════════════


@g5_bp.route("/learnings", methods=["GET"])
def list_learnings():
    """List growth learnings/insights."""
    tenant_id = _resolve_tenant()
    campaign_id = request.args.get("campaign_id", type=int)
    category = request.args.get("category")
    significance = request.args.get("significance")
    is_actionable = request.args.get("is_actionable", type=bool)
    limit = min(request.args.get("limit", 50, type=int), 100)
    offset = request.args.get("offset", 0, type=int)
    learnings = get_learnings(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        category=category,
        significance=significance,
        is_actionable=is_actionable,
        limit=limit,
        offset=offset,
    )
    return jsonify({"success": True, "learnings": learnings})


@g5_bp.route("/learnings", methods=["POST"])
def create_learning_record():
    """Create a learning/insight record."""
    tenant_id = _resolve_tenant()
    data = request.get_json() or {}
    learning = create_learning(
        tenant_id=tenant_id,
        category=data.get("category", "campaign_performance"),
        title=data.get("title", ""),
        observation=data.get("observation", ""),
        significance=data.get("significance", "normal"),
        evidence_summary=data.get("evidence_summary", ""),
        evidence_refs=data.get("evidence_refs"),
        confidence=data.get("confidence", 50),
        data_source=data.get("data_source", "shunya_internal"),
        campaign_id=data.get("campaign_id"),
        attribution_id=data.get("attribution_id"),
        interaction_id=data.get("interaction_id"),
        outcome_id=data.get("outcome_id"),
        opportunity_id=data.get("opportunity_id"),
        recommendation=data.get("recommendation", ""),
        recommendation_confidence=data.get("recommendation_confidence", 50),
        recommendation_action=data.get("recommendation_action", ""),
        is_actionable=data.get("is_actionable", False),
        external_source=data.get("external_source", ""),
        external_retrieved_at=data.get("external_retrieved_at"),
        external_context=data.get("external_context", ""),
        created_by=data.get("created_by", ""),
    )
    return jsonify({"success": True, "learning": learning}), 201


# ══════════════════════════════════════════════════════════════════════
# CAMPAIGN INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════


@g5_bp.route("/intelligence/<int:campaign_id>", methods=["GET"])
def campaign_intel(campaign_id):
    """Get grounded campaign intelligence assessment."""
    tenant_id = _resolve_tenant()
    intel = campaign_intelligence(campaign_id, tenant_id)
    return jsonify({"success": True, "intelligence": intel})


@g5_bp.route("/intelligence/overview", methods=["GET"])
def growth_overview():
    """Overview of growth intelligence across all campaigns."""
    tenant_id = _resolve_tenant()
    campaigns = Campaign.query.filter_by(tenant_id=tenant_id).all()

    total_budget = 0.0
    total_revenue = 0.0
    total_interactions = 0
    total_learnings = 0
    active_campaigns = 0
    campaigns_with_data = 0

    for c in campaigns:
        budget = float(c.budget or 0)
        total_budget += budget
        if c.status == "active":
            active_campaigns += 1

        chain = get_attribution_chain(c.id, tenant_id)
        if "error" not in chain:
            if chain.get("total_interactions", 0) > 0 or chain.get("total_attributions", 0) > 0:
                campaigns_with_data += 1
            total_interactions += chain.get("total_interactions", 0)
            total_revenue += chain.get("total_revenue", 0)

    learnings = get_learnings(tenant_id=tenant_id)
    total_learnings = len(learnings)
    actionable = [l for l in learnings if l.get("is_actionable")]

    return jsonify({
        "success": True,
        "overview": {
            "total_campaigns": len(campaigns),
            "active_campaigns": active_campaigns,
            "campaigns_with_data": campaigns_with_data,
            "total_budget": str(total_budget),
            "total_attributed_revenue": str(total_revenue),
            "total_interactions": total_interactions,
            "total_learnings": total_learnings,
            "actionable_learnings": len(actionable),
            "roi": str(round(total_revenue / total_budget, 2)) if total_budget > 0 else "N/A",
        }
    })