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
        issue_type=data.get("issue_type", ""),
        meta=data.get("meta", {}),
    )

    return jsonify({
        "id": c.id,
        "title": c.title,
        "status": c.status,
        "owner": c.owner,
        "due_at": c.due_at.isoformat() if c.due_at else None,
        "issue_type": c.issue_type or "",
        "meta": c.meta or {},
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }), 201


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

    results = []
    for c in q.all():
        overdue = False
        if c.due_at and c.status not in ("completed", "failed"):
            now = datetime.utcnow()
            due = c.due_at
            if due.tzinfo:
                due = due.replace(tzinfo=None)
            overdue = now > due

        results.append({
            "id": c.id,
            "title": c.title,
            "owner": c.owner or "",
            "status": c.status,
            "due_at": c.due_at.isoformat() if c.due_at else None,
            "issue_type": c.issue_type or "",
            "meta": c.meta or {},
            "overdue": overdue,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return jsonify({"commitments": results, "total": len(results)})


@commitments_bp.route("/<int:commitment_id>", methods=["GET"])
def get_commitment(commitment_id):
    c = Commitment.query.get_or_404(commitment_id)
    overdue = False
    if c.due_at and c.status not in ("completed", "failed"):
        now = datetime.utcnow()
        due = c.due_at
        if due.tzinfo:
            due = due.replace(tzinfo=None)
        overdue = now > due

    return jsonify({
        "id": c.id,
        "title": c.title,
        "owner": c.owner or "",
        "status": c.status,
        "due_at": c.due_at.isoformat() if c.due_at else None,
        "issue_type": c.issue_type or "",
        "meta": c.meta or {},
        "overdue": overdue,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    })


@commitments_bp.route("/<int:commitment_id>", methods=["PATCH"])
def update(commitment_id):
    c = Commitment.query.get_or_404(commitment_id)
    data = request.json or {}
    if "status" in data:
        c = update_status(c, data["status"])
    if "title" in data:
        c.title = data["title"]
    if "owner" in data:
        c.owner = data["owner"]
    if "issue_type" in data:
        c.issue_type = data["issue_type"]
    if "meta" in data:
        current_meta = dict(c.meta or {})
        current_meta.update(data["meta"])
        c.meta = current_meta
    if "due_at" in data:
        c.due_at = datetime.fromisoformat(data["due_at"]) if data["due_at"] else None
    from app import db
    db.session.commit()

    return jsonify({
        "id": c.id,
        "title": c.title,
        "owner": c.owner or "",
        "status": c.status,
        "due_at": c.due_at.isoformat() if c.due_at else None,
        "issue_type": c.issue_type or "",
        "meta": c.meta or {},
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    })