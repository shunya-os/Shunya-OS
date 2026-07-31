"""SHUNYA — Proposal REST API routes.

CRUD + lifecycle routes for the Proposal model, mounted at /api/v1/objects/proposal.
"""
import json
import re
from datetime import datetime

from flask import request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import Proposal, ProposalVersion, Organization, Lead
from app.production.objects import objects_bp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-")


def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _require_field(data: dict, field: str, label: str = "") -> str:
    label = label or field
    value = data.get(field)
    if value is None or not str(value).strip():
        raise BadRequest(f"'{label}' is required")
    return str(value).strip()


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _proposal_to_dict(proposal: Proposal, include_html: bool = False) -> dict:
    """Serialize a proposal to the standard envelope."""
    d = proposal.to_dict(include_html=include_html)
    d["slug"] = _slugify(proposal.title) if proposal.title else ""
    return d


def _proposal_version_to_dict(version: ProposalVersion) -> dict:
    """Serialize a ProposalVersion to the standard envelope."""
    return {
        "id": version.id,
        "proposal_id": version.proposal_id,
        "version_number": version.version_number,
        "snapshot_json": json.loads(version.snapshot_json) if version.snapshot_json else {},
        "change_summary": version.change_summary or "",
        "created_by": version.created_by or "",
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


def _pagination_envelope(query, page: int, per_page: int) -> dict:
    """Build a pagination envelope from a SQLAlchemy query."""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": pagination.items,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@objects_bp.route("/proposal", methods=["POST"])
@login_required
def create_proposal():
    """Create a new Proposal.

    Required fields: title, budget
    Optional fields: organization_id, relationship_id, opportunity_id,
                     destination, duration_days, pax, currency (default INR),
                     inclusions, exclusions, terms, itinerary_json, pricing_json
    """
    data = _require_json()
    title = _require_field(data, "title", "Proposal title")
    budget = _require_field(data, "budget", "Budget")

    # Parse budget to numeric
    try:
        budget_val = float(budget)
    except (ValueError, TypeError):
        raise BadRequest("'Budget' must be a valid number")

    # Validate optional FK references exist when provided
    org_id = data.get("organization_id")
    if org_id is not None:
        org = Organization.query.get(int(org_id))
        if not org:
            raise BadRequest(f"Organization with id={org_id} not found")

    rel_id = data.get("relationship_id")
    if rel_id is not None:
        from app.models import Relationship
        rel = Relationship.query.get(int(rel_id))
        if not rel:
            raise BadRequest(f"Relationship with id={rel_id} not found")

    opp_id = data.get("opportunity_id")
    if opp_id is not None:
        lead = Lead.query.get(int(opp_id))
        if not lead:
            raise BadRequest(f"Opportunity (Lead) with id={opp_id} not found")

    proposal = Proposal(
        title=title,
        budget=budget_val,
        organization_id=data.get("organization_id"),
        relationship_id=data.get("relationship_id"),
        opportunity_id=data.get("opportunity_id"),
        destination=data.get("destination", ""),
        duration_days=data.get("duration_days", 0),
        pax=data.get("pax", ""),
        currency=data.get("currency", "INR"),
        inclusions=data.get("inclusions", ""),
        exclusions=data.get("exclusions", ""),
        terms=data.get("terms", ""),
        itinerary_json=data.get("itinerary_json", "[]"),
        pricing_json=data.get("pricing_json", "{}"),
        status="draft",
        created_by=getattr(g, "user", ""),
    )
    db.session.add(proposal)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _proposal_to_dict(proposal),
    }), 201


@objects_bp.route("/proposal", methods=["GET"])
@login_required
def list_proposals():
    """List proposals with pagination and optional filters.

    Query params:
        page (int, default 1)
        per_page (int, default 20)
        status (str, optional) — filter by status
        organization_id (int, optional) — filter by organization
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # cap

    query = Proposal.query.order_by(Proposal.updated_at.desc())

    status = request.args.get("status")
    if status:
        query = query.filter(Proposal.status == status)

    org_id = request.args.get("organization_id")
    if org_id:
        try:
            query = query.filter(Proposal.organization_id == int(org_id))
        except (ValueError, TypeError):
            raise BadRequest("'organization_id' must be a valid integer")

    envelope = _pagination_envelope(query, page, per_page)

    return jsonify({
        "success": True,
        "data": {
            "items": [_proposal_to_dict(p) for p in envelope["items"]],
            "page": envelope["page"],
            "per_page": envelope["per_page"],
            "total": envelope["total"],
            "pages": envelope["pages"],
            "has_next": envelope["has_next"],
            "has_prev": envelope["has_prev"],
        },
    })


@objects_bp.route("/proposal/<int:proposal_id>", methods=["GET"])
@login_required
def get_proposal(proposal_id: int):
    """Get a single proposal by id."""
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        raise NotFound("Proposal not found")

    return jsonify({
        "success": True,
        "data": _proposal_to_dict(proposal),
    })


@objects_bp.route("/proposal/<int:proposal_id>", methods=["PUT"])
@login_required
def update_proposal(proposal_id: int):
    """Update a proposal. Rejects if status is 'accepted' or 'cancelled'.

    Saves a snapshot as ProposalVersion before applying changes.
    Only updates the fields provided in the request body.
    """
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        raise NotFound("Proposal not found")

    if proposal.status in ("accepted", "cancelled"):
        raise BadRequest(
            f"Cannot update proposal with status '{proposal.status}'"
        )

    data = _require_json()
    if not data:
        raise BadRequest("Request body must not be empty")

    # -- Save previous state as ProposalVersion -- #
    prev_snapshot = proposal.to_dict()
    version = ProposalVersion(
        proposal_id=proposal.id,
        version_number=proposal.version_number,
        snapshot_json=json.dumps(prev_snapshot, default=str),
        change_summary=data.get("_change_summary", ""),
        created_by=getattr(g, "user", ""),
    )
    db.session.add(version)

    # -- Apply updates to mutable fields -- #
    mutable_fields = [
        "title", "destination", "duration_days", "pax", "budget",
        "currency", "inclusions", "exclusions", "terms",
        "itinerary_json", "pricing_json", "organization_id",
        "relationship_id", "opportunity_id",
    ]

    for field in mutable_fields:
        if field in data:
            # Parse budget to numeric if provided
            if field == "budget":
                try:
                    setattr(proposal, field, float(data[field]))
                except (ValueError, TypeError):
                    raise BadRequest("'Budget' must be a valid number")
            elif field in ("duration_days",):
                try:
                    setattr(proposal, field, int(data[field]))
                except (ValueError, TypeError):
                    raise BadRequest(f"'{field}' must be a valid integer")
            elif field in ("organization_id", "relationship_id", "opportunity_id"):
                val = data[field]
                if val is not None:
                    setattr(proposal, field, int(val))
                else:
                    setattr(proposal, field, None)
            else:
                setattr(proposal, field, data[field])

    # Bump version number
    proposal.version_number = (proposal.version_number or 1) + 1

    db.session.commit()

    return jsonify({
        "success": True,
        "data": _proposal_to_dict(proposal),
    })


@objects_bp.route("/proposal/<int:proposal_id>", methods=["DELETE"])
@login_required
def cancel_proposal(proposal_id: int):
    """Soft-delete a proposal by setting status to 'cancelled'.

    Rejects if already 'accepted'.
    """
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        raise NotFound("Proposal not found")

    if proposal.status == "accepted":
        raise BadRequest("Cannot cancel an accepted proposal")

    proposal.status = "cancelled"
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _proposal_to_dict(proposal),
    })


@objects_bp.route("/proposal/<int:proposal_id>/versions", methods=["GET"])
@login_required
def list_proposal_versions(proposal_id: int):
    """List all versions for a proposal, ordered by version_number desc."""
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        raise NotFound("Proposal not found")

    versions = (
        ProposalVersion.query
        .filter_by(proposal_id=proposal.id)
        .order_by(ProposalVersion.version_number.desc())
        .all()
    )

    return jsonify({
        "success": True,
        "data": [_proposal_version_to_dict(v) for v in versions],
    })


@objects_bp.route("/proposal/<int:proposal_id>/submit", methods=["POST"])
@login_required
def submit_proposal(proposal_id: int):
    """Submit a draft proposal — changes status from 'draft' to 'sent'.

    Sets sent_at to the current UTC timestamp.
    """
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        raise NotFound("Proposal not found")

    if proposal.status != "draft":
        raise BadRequest(
            f"Cannot submit proposal with status '{proposal.status}'; "
            "only 'draft' proposals can be submitted"
        )

    proposal.status = "sent"
    proposal.sent_at = datetime.utcnow()

    # Bump version on submit
    prev_snapshot = proposal.to_dict()
    version = ProposalVersion(
        proposal_id=proposal.id,
        version_number=proposal.version_number,
        snapshot_json=json.dumps(prev_snapshot, default=str),
        change_summary="Submitted proposal",
        created_by=getattr(g, "user", ""),
    )
    db.session.add(version)
    proposal.version_number = (proposal.version_number or 1) + 1

    db.session.commit()

    return jsonify({
        "success": True,
        "data": _proposal_to_dict(proposal),
    })