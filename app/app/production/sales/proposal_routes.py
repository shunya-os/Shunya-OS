"""SHUNYA — Proposal API Routes (Sales).

Endpoints for managing business proposals/quotes.
Uses the Proposal model from app.models.
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import Proposal

sales_proposal_bp = Blueprint("sales_proposal", __name__)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _require_json() -> dict:
    """Get and validate JSON body."""
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _require_field(data: dict, field: str, label: str = "") -> str:
    """Get a required string field, raising BadRequest if missing/empty."""
    label = label or field
    value = data.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise BadRequest(f"'{label}' is required")
    return value


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@sales_proposal_bp.route("/proposal", methods=["POST"])
@login_required
def create_proposal():
    """Create a new proposal.

    Request body:
        title (str, required) — proposal title
        organization_id (int, optional) — owning org
        relationship_id (int, optional) — linked relationship
        destination (str, optional) — destination name
        duration_days (int, optional) — tour/event duration
        pax (str, optional) — passenger count description
        budget (float, optional) — budget amount
        currency (str, optional) — currency code (default: INR)

    Returns:
        201 — Proposal created
    """
    data = _require_json()
    title = _require_field(data, "title")

    org_id = data.get("organization_id")
    rel_id = data.get("relationship_id")

    proposal = Proposal(
        title=title,
        organization_id=int(org_id) if org_id is not None else None,
        relationship_id=int(rel_id) if rel_id is not None else None,
        destination=data.get("destination", ""),
        duration_days=int(data.get("duration_days", 0)),
        pax=data.get("pax", ""),
        budget=float(data.get("budget", 0) or 0),
        currency=data.get("currency", "INR"),
        status="draft",
        version_number=1,
        created_by=getattr(g, "user_email", ""),
    )

    db.session.add(proposal)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": proposal.to_dict(),
    }), 201


@sales_proposal_bp.route("/proposal", methods=["GET"])
@login_required
def list_proposals():
    """List proposals.

    Query parameters:
        status (str, optional) — filter by status
        organization_id (int, optional) — filter by org
        page (int, optional) — page number (default: 1)
        per_page (int, optional) — items per page (default: 20, max: 100)

    Returns:
        200 — Paginated list of proposals
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Proposal.query

    org_id = request.args.get("organization_id", type=int)
    if org_id is not None:
        query = query.filter(Proposal.organization_id == org_id)

    status = request.args.get("status")
    if status:
        query = query.filter(Proposal.status == status)

    query = query.order_by(Proposal.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


@sales_proposal_bp.route("/proposal/<int:proposal_id>", methods=["PUT"])
@login_required
def update_proposal(proposal_id):
    """Update an existing proposal.

    Request body (all fields optional):
        title, status, destination, duration_days, pax, budget, currency,
        itinerary_json, pricing_json, inclusions, exclusions, terms,
        brand_color, brand_logo_url, cover_image_url

    Returns:
        200 — Proposal updated
    """
    proposal = db.session.get(Proposal, proposal_id)
    if not proposal:
        raise NotFound(f"Proposal with id {proposal_id} not found")

    data = _require_json()

    updatable_fields = [
        "title", "status", "destination", "duration_days", "pax",
        "budget", "currency", "itinerary_json", "pricing_json",
        "inclusions", "exclusions", "terms", "brand_color",
        "brand_logo_url", "cover_image_url",
    ]

    for field in updatable_fields:
        if field in data:
            setattr(proposal, field, data[field])

    proposal.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "data": proposal.to_dict(),
    })


@sales_proposal_bp.route("/proposal/<int:proposal_id>/share", methods=["POST"])
@login_required
def share_proposal(proposal_id):
    """Mark a proposal as sent (shared with client).

    Request body:
        sent_via (str, optional) — channel used (email, whatsapp, link, etc.)

    Returns:
        200 — Proposal marked as sent
    """
    proposal = db.session.get(Proposal, proposal_id)
    if not proposal:
        raise NotFound(f"Proposal with id {proposal_id} not found")

    data = _require_json()
    proposal.status = "sent"
    proposal.sent_at = datetime.utcnow()
    proposal.sent_via = data.get("sent_via", "link")
    proposal.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "data": proposal.to_dict(),
    })


@sales_proposal_bp.route("/proposal/<int:proposal_id>/track", methods=["POST"])
@login_required
def track_proposal(proposal_id):
    """Record a tracking event on a proposal (viewed, accepted, etc.).

    Request body:
        event (str, required) — one of: viewed, accepted, cancelled

    Returns:
        200 — Tracking event recorded
    """
    proposal = db.session.get(Proposal, proposal_id)
    if not proposal:
        raise NotFound(f"Proposal with id {proposal_id} not found")

    data = _require_json()
    event = _require_field(data, "event").lower()

    if event == "viewed":
        proposal.viewed_at = datetime.utcnow()
    elif event == "accepted":
        proposal.status = "accepted"
        proposal.accepted_at = datetime.utcnow()
    elif event == "cancelled":
        proposal.status = "cancelled"
    else:
        raise BadRequest(f"Unknown event '{event}'. Supported: viewed, accepted, cancelled")

    proposal.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "success": True,
        "data": proposal.to_dict(),
    })
