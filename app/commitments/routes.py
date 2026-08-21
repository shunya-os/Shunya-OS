from flask import Blueprint, request, jsonify
from datetime import datetime
from app.commitments.service import create_commitment, update_status
from app.commitments.models import Commitment

commitments_bp = Blueprint("commitments", __name__, url_prefix="/api/v1/commitments")


@commitments_bp.route("/", methods=["POST"])
def create():
    data = request.json or {}

    due_at = None
    if data.get("due_at"):
        due_at = datetime.fromisoformat(data["due_at"])

    c = create_commitment(
        title=data.get("title"),
        owner=data.get("owner"),
        due_at=due_at,
    )

    return jsonify({
        "id": c.id,
        "title": c.title,
        "status": c.status
    })


@commitments_bp.route("/", methods=["GET"])
def list_commitments():
    owner = request.args.get("owner")
    status = request.args.get("status")
    limit = min(request.args.get("limit", 50, type=int), 200)
    q = Commitment.query
    if owner:
        q = q.filter(Commitment.owner == owner)
    if status:
        q = q.filter(Commitment.status == status)
    q = q.order_by(Commitment.created_at.desc()).limit(limit)
    return jsonify({
        "commitments": [{
            "id": c.id,
            "title": c.title,
            "owner": c.owner,
            "status": c.status,
            "due_at": c.due_at.isoformat() if c.due_at else None,
            "issue_type": c.issue_type or "",
            "created_at": c.created_at.isoformat() if c.created_at else None,
        } for c in q.all()]
    })


@commitments_bp.route("/<int:commitment_id>", methods=["PATCH"])
def update(commitment_id):
    c = Commitment.query.get_or_404(commitment_id)

    updated = update_status(c, request.json.get("status"))

    return jsonify({
        "id": updated.id,
        "status": updated.status
    })