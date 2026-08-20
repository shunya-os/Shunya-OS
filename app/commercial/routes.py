"""G4 — Commercial API Routes.

Universal commercial operations:
- Opportunity/need CRUD with lifecycle transitions
- Commercial context retrieval
- Proposal/offer lifecycle
- Commercial intelligence
- Follow-up/awareness queries
"""

from datetime import datetime
from flask import Blueprint, jsonify, request, g

from app import db
from app.commercial.models import (
    CommercialOpportunity,
    CommercialContext,
    CommercialProposal,
    CommercialTransition,
    CommercialType,
)
from app.commercial.service import (
    create_opportunity,
    transition_opportunity,
    create_proposal,
    transition_proposal,
    get_commercial_context,
    update_commercial_summary,
    get_opportunities_needing_attention,
    get_upcoming_follow_ups,
    get_commercial_intelligence,
    answer_commercial_question,
    get_opportunities_for_relationship,
    get_proposals_for_opportunity,
)
from app.authz.decorators import require_permission


def _resolve_org_id() -> int:
    """Resolve tenant/organization from session or request."""
    from app.authz.decorators import _resolve_org_id as resolve
    org_id = resolve()
    if org_id:
        return org_id
    return g.get("tenant_id", 1)


commercial_bp = Blueprint(
    "commercial", __name__, url_prefix="/api/v1/commercial"
)


# ══════════════════════════════════════════════════════════════════════
# OPPORTUNITY CRUD
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/opportunities", methods=["GET"])
@require_permission("rel.view")
def list_opportunities():
    """List commercial opportunities for the current organization."""
    org_id = _resolve_org_id()
    state = request.args.get("state", "")
    relationship_id = request.args.get("relationship_id", type=int)
    limit = min(request.args.get("limit", 50, type=int), 100)
    offset = request.args.get("offset", 0, type=int)

    q = CommercialOpportunity.query.filter_by(organization_id=org_id)
    if state:
        q = q.filter(CommercialOpportunity.lifecycle_state == state)
    if relationship_id:
        q = q.filter(CommercialOpportunity.relationship_id == relationship_id)

    total = q.count()
    opps = q.order_by(CommercialOpportunity.updated_at.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "success": True,
        "opportunities": [o.to_dict() for o in opps],
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@commercial_bp.route("/opportunities", methods=["POST"])
@require_permission("rel.create")
def create_opportunity_route():
    """Create a new commercial opportunity."""
    data = request.get_json(silent=True) or {}
    org_id = _resolve_org_id()

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "Title is required"}), 400

    try:
        opp = create_opportunity(
            organization_id=org_id,
            title=title,
            description=data.get("description", ""),
            relationship_id=data.get("relationship_id"),
            opportunity_type=data.get("opportunity_type", "opportunity"),
            estimated_value=data.get("estimated_value"),
            currency=data.get("currency", ""),
            confidence=data.get("confidence", 50),
            urgency=data.get("urgency", 50),
            source=data.get("source", "manual"),
            owner_identity_id=data.get("owner_identity_id", ""),
            campaign_id=data.get("campaign_id"),
            created_by=data.get("created_by", g.get("user", "")),
        )
        return jsonify({"success": True, "opportunity": opp.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@commercial_bp.route("/opportunities/<int:opp_id>", methods=["GET"])
@require_permission("rel.view")
def get_opportunity(opp_id: int):
    """Get a single opportunity by ID."""
    org_id = _resolve_org_id()
    opp = CommercialOpportunity.query.filter_by(
        id=opp_id, organization_id=org_id
    ).first()
    if not opp:
        return jsonify({"success": False, "error": "Opportunity not found"}), 404

    return jsonify({"success": True, "opportunity": opp.to_dict()})


@commercial_bp.route("/opportunities/<int:opp_id>", methods=["PATCH"])
@require_permission("rel.edit")
def update_opportunity(opp_id: int):
    """Update opportunity fields (not lifecycle state)."""
    org_id = _resolve_org_id()
    opp = CommercialOpportunity.query.filter_by(
        id=opp_id, organization_id=org_id
    ).first()
    if not opp:
        return jsonify({"success": False, "error": "Opportunity not found"}), 404

    data = request.get_json(silent=True) or {}
    updatable = [
        "title", "description", "opportunity_type",
        "estimated_value", "currency", "confidence", "urgency", "priority",
        "next_action", "next_action_due_at",
        "owner_identity_id", "risks",
    ]
    for key in updatable:
        if key in data:
            setattr(opp, key, data[key])

    opp.updated_by = data.get("updated_by", g.get("user", ""))
    opp.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"success": True, "opportunity": opp.to_dict()})


# ══════════════════════════════════════════════════════════════════════
# LIFECYCLE TRANSITIONS
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/opportunities/<int:opp_id>/transition", methods=["POST"])
@require_permission("rel.edit")
def transition_opportunity_route(opp_id: int):
    """Transition an opportunity to a new lifecycle state."""
    org_id = _resolve_org_id()
    opp = CommercialOpportunity.query.filter_by(
        id=opp_id, organization_id=org_id
    ).first()
    if not opp:
        return jsonify({"success": False, "error": "Opportunity not found"}), 404

    data = request.get_json(silent=True) or {}
    to_state = data.get("to_state", "")
    reason = data.get("reason", "")
    is_correction = data.get("is_correction", False)
    correction_reason = data.get("correction_reason", "")
    triggered_by = data.get("triggered_by", g.get("user", ""))

    if not to_state:
        return jsonify({"success": False, "error": "to_state is required"}), 400

    success, error = transition_opportunity(
        opp=opp,
        to_state=to_state,
        reason=reason,
        triggered_by=triggered_by,
        is_correction=is_correction,
        correction_reason=correction_reason,
    )

    if not success:
        return jsonify({"success": False, "error": error}), 400

    return jsonify({"success": True, "opportunity": opp.to_dict()})


# ══════════════════════════════════════════════════════════════════════
# TRANSITION HISTORY
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/transitions", methods=["GET"])
@require_permission("rel.view")
def list_transitions():
    """Get transition audit log."""
    org_id = _resolve_org_id()
    entity_type = request.args.get("entity_type", "")
    entity_id = request.args.get("entity_id", type=int)
    limit = min(request.args.get("limit", 50, type=int), 200)

    q = CommercialTransition.query.filter_by(organization_id=org_id)
    if entity_type:
        q = q.filter_by(entity_type=entity_type)
    if entity_id:
        q = q.filter_by(entity_id=entity_id)

    transitions = q.order_by(CommercialTransition.transitioned_at.desc()).limit(limit).all()
    return jsonify({
        "success": True,
        "transitions": [t.to_dict() for t in transitions],
        "total": len(transitions),
    })


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL CONTEXT
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/context/<int:relationship_id>", methods=["GET"])
@require_permission("rel.view")
def get_context(relationship_id: int):
    """Get commercial context for a relationship."""
    org_id = _resolve_org_id()
    ctx = get_commercial_context(org_id, relationship_id)
    if not ctx:
        return jsonify({"success": False, "error": "No commercial context found"}), 404

    # Also get all opportunities for this relationship
    opportunities = get_opportunities_for_relationship(org_id, relationship_id)

    return jsonify({
        "success": True,
        "context": ctx,
        "opportunities": opportunities,
    })


@commercial_bp.route("/context/<int:relationship_id>", methods=["PATCH"])
@require_permission("rel.edit")
def update_context(relationship_id: int):
    """Update commercial context summary/suggestions."""
    org_id = _resolve_org_id()
    data = request.get_json(silent=True) or {}

    success = update_commercial_summary(
        organization_id=org_id,
        relationship_id=relationship_id,
        summary=data.get("summary", ""),
        suggested_next_action=data.get("suggested_next_action", ""),
        suggested_action_reason=data.get("suggested_action_reason", ""),
    )

    if not success:
        return jsonify({"success": False, "error": "Failed to update context"}), 500

    ctx = get_commercial_context(org_id, relationship_id)
    return jsonify({"success": True, "context": ctx})


# ══════════════════════════════════════════════════════════════════════
# PROPOSAL / OFFER
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/proposals", methods=["GET"])
@require_permission("rel.view")
def list_proposals():
    """List commercial proposals."""
    org_id = _resolve_org_id()
    opportunity_id = request.args.get("opportunity_id", type=int)
    status = request.args.get("status", "")
    limit = min(request.args.get("limit", 50, type=int), 100)

    q = CommercialProposal.query.filter_by(organization_id=org_id)
    if opportunity_id:
        q = q.filter_by(opportunity_id=opportunity_id)
    if status:
        q = q.filter_by(status=status)

    total = q.count()
    proposals = q.order_by(CommercialProposal.updated_at.desc()).limit(limit).all()

    return jsonify({
        "success": True,
        "proposals": [p.to_dict() for p in proposals],
        "total": total,
    })


@commercial_bp.route("/proposals", methods=["POST"])
@require_permission("proposal.create")
def create_proposal_route():
    """Create a commercial proposal."""
    data = request.get_json(silent=True) or {}
    org_id = _resolve_org_id()

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"success": False, "error": "Title is required"}), 400

    try:
        proposal = create_proposal(
            organization_id=org_id,
            relationship_id=data.get("relationship_id"),
            opportunity_id=data.get("opportunity_id"),
            title=title,
            proposal_type=data.get("proposal_type", "proposal"),
            scope_description=data.get("scope_description", ""),
            assumptions=data.get("assumptions", ""),
            exclusions=data.get("exclusions", ""),
            currency=data.get("currency", "INR"),
            total_value=data.get("total_value", 0),
            terms=data.get("terms", ""),
            conditions=data.get("conditions", ""),
            pricing_structure=data.get("pricing_structure"),
            created_by=data.get("created_by", g.get("user", "")),
        )
        return jsonify({"success": True, "proposal": proposal.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@commercial_bp.route("/proposals/<int:proposal_id>", methods=["GET"])
@require_permission("rel.view")
def get_proposal(proposal_id: int):
    """Get a single proposal."""
    org_id = _resolve_org_id()
    proposal = CommercialProposal.query.filter_by(
        id=proposal_id, organization_id=org_id
    ).first()
    if not proposal:
        return jsonify({"success": False, "error": "Proposal not found"}), 404
    return jsonify({"success": True, "proposal": proposal.to_dict()})


@commercial_bp.route("/proposals/<int:proposal_id>/transition", methods=["POST"])
@require_permission("proposal.update")
def transition_proposal_route(proposal_id: int):
    """Transition a proposal's lifecycle state.

    Accepting a proposal triggers the canonical:
    Decision → Commitment → Execution path.
    """
    org_id = _resolve_org_id()
    proposal = CommercialProposal.query.filter_by(
        id=proposal_id, organization_id=org_id
    ).first()
    if not proposal:
        return jsonify({"success": False, "error": "Proposal not found"}), 404

    data = request.get_json(silent=True) or {}
    to_state = data.get("to_state", "")
    reason = data.get("reason", "")
    triggered_by = data.get("triggered_by", g.get("user", ""))

    if not to_state:
        return jsonify({"success": False, "error": "to_state is required"}), 400

    success, error, decision = transition_proposal(
        proposal=proposal,
        to_state=to_state,
        reason=reason,
        triggered_by=triggered_by,
    )

    if not success:
        return jsonify({"success": False, "error": error}), 400

    result = {"success": True, "proposal": proposal.to_dict()}
    if decision:
        result["decision"] = decision

    return jsonify(result)


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/intelligence", methods=["GET"])
@require_permission("rel.view")
def commercial_intelligence():
    """Get commercial intelligence snapshot."""
    org_id = _resolve_org_id()
    intelligence = get_commercial_intelligence(org_id)
    return jsonify({"success": True, "intelligence": intelligence})


@commercial_bp.route("/intelligence/ask", methods=["POST"])
@require_permission("rel.view")
def ask_commercial():
    """Ask a commercial intelligence question."""
    org_id = _resolve_org_id()
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")

    if not question:
        return jsonify({"success": False, "error": "Question is required"}), 400

    result = answer_commercial_question(org_id, question)
    return jsonify({"success": True, **result})


# ══════════════════════════════════════════════════════════════════════
# FOLLOW-UP / AWARENESS
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/attention", methods=["GET"])
@require_permission("rel.view")
def needs_attention():
    """Get opportunities needing human attention."""
    org_id = _resolve_org_id()
    opportunities = get_opportunities_needing_attention(org_id)
    upcoming = get_upcoming_follow_ups(org_id)
    return jsonify({
        "success": True,
        "needs_attention": opportunities,
        "upcoming_follow_ups": upcoming,
    })


# ══════════════════════════════════════════════════════════════════════
# RELATIONSHIP OPPORTUNITIES
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/relationships/<int:rel_id>/opportunities", methods=["GET"])
@require_permission("rel.view")
def relationship_opportunities(rel_id: int):
    """Get all opportunities for a relationship."""
    org_id = _resolve_org_id()
    opps = get_opportunities_for_relationship(org_id, rel_id)
    return jsonify({
        "success": True,
        "opportunities": opps,
        "total": len(opps),
    })


# ══════════════════════════════════════════════════════════════════════
# COMMERCIAL TYPES (config-driven vocabulary)
# ══════════════════════════════════════════════════════════════════════


@commercial_bp.route("/types", methods=["GET"])
@require_permission("rel.view")
def list_types():
    """List configurable commercial types for the organization."""
    org_id = _resolve_org_id()
    domain = request.args.get("domain", "")
    q = CommercialType.query.filter(
        (CommercialType.organization_id == org_id) |
        (CommercialType.organization_id.is_(None))
    )
    if domain:
        q = q.filter_by(domain=domain)

    types = q.order_by(CommercialType.sort_order).all()
    return jsonify({
        "success": True,
        "types": [{
            "id": t.id,
            "domain": t.domain,
            "type_key": t.type_key,
            "display_label": t.display_label,
            "icon": t.icon,
            "color": t.color,
            "is_default": t.is_default,
            "is_system": t.is_system,
        } for t in types],
    })