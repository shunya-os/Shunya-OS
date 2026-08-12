"""SHUNYA Customer Experience — FDA13 Routes."""
from flask import Blueprint, jsonify, request
from datetime import datetime
from app import db
from app.customer_experience import service as cx

cust_bp = Blueprint("customer_experience", __name__, url_prefix="/api/v1/customer")


@cust_bp.route("/profile/<int:customer_id>", methods=["GET"])
def profile(customer_id):
    result = cx.get_customer_profile(customer_id)
    if result is None:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(result)


@cust_bp.route("/history/<int:customer_id>", methods=["GET"])
def history(customer_id):
    result = cx.get_customer_history(customer_id)
    return jsonify({"history": result})


@cust_bp.route("/commitments", methods=["POST"])
def create_commitment():
    data = request.get_json() or {}
    due_at = None
    if data.get("due_at"):
        due_at = datetime.fromisoformat(data["due_at"])
    cm = cx.create_commitment(
        title=data.get("title", "Commitment"),
        relationship_id=data.get("relationship_id"),
        owner=data.get("owner"),
        due_at=due_at,
        issue_type=data.get("issue_type", "service"),
        campaign_id=data.get("campaign_id"),
    )
    return jsonify({"id": cm.id, "title": cm.title, "status": cm.status,
                     "issue_type": cm.issue_type}), 201


@cust_bp.route("/commitments/<int:cid>", methods=["GET", "PATCH"])
def commitment(cid):
    from app.commitments.models import Commitment
    cm = Commitment.query.get(cid)
    if not cm:
        return jsonify({"error": "Commitment not found"}), 404
    if request.method == "GET":
        return jsonify({"id": cm.id, "title": cm.title, "owner": cm.owner,
                         "due_at": cm.due_at.isoformat() if cm.due_at else None,
                         "status": cm.status, "issue_type": cm.issue_type,
                         "relationship_id": cm.relationship_id})
    data = request.get_json() or {}
    for k in ("status", "owner", "title", "issue_type"):
        if k in data:
            setattr(cm, k, data[k])
    db.session.commit()
    return jsonify({"id": cm.id, "status": cm.status})


@cust_bp.route("/escalations", methods=["POST"])
def create_escalation():
    data = request.get_json() or {}
    due_at = None
    if data.get("due_at"):
        due_at = datetime.fromisoformat(data["due_at"])
    cm = cx.create_escalation(
        relationship_id=data.get("relationship_id", 0),
        summary=data.get("summary", "Escalation"),
        owner=data.get("owner"),
        due_at=due_at,
    )
    return jsonify({"id": cm.id, "title": cm.title, "status": cm.status,
                     "issue_type": cm.issue_type}), 201


@cust_bp.route("/issues", methods=["POST"])
def create_issue():
    data = request.get_json() or {}
    cm = cx.create_issue(
        relationship_id=data.get("relationship_id", 0),
        title=data.get("title", "Issue"),
        severity=data.get("severity", "medium"),
        owner=data.get("owner"),
    )
    return jsonify({"id": cm.id, "title": cm.title, "status": cm.status}), 201


@cust_bp.route("/retention/<int:customer_id>", methods=["GET"])
def retention(customer_id):
    result = cx.get_retention_signals(customer_id)
    return jsonify(result)


@cust_bp.route("/commitments/<int:cid>/resolve", methods=["POST"])
def resolve_commitment(cid):
    data = request.get_json() or {}
    result = cx.resolve_commitment(cid, data.get("resolution_note", ""))
    if result is None:
        return jsonify({"error": "Commitment not found"}), 404
    return jsonify(result)