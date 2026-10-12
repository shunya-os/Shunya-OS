"""SHUNYA Customer Experience — FDA13 Routes."""
from flask import Blueprint, jsonify, request, g
from datetime import datetime
from app import db
from app.authz.decorators import _resolve_org_id, require_permission
from app.customer_experience import service as cx

cust_bp = Blueprint("customer_experience", __name__, url_prefix="/api/v1/customer")


def _org_context() -> int | None:
    """Server-resolved organization context (B17).

    The customer-experience family previously exposed any customer's profile,
    history and commitments by guessed id with no authentication or tenant
    boundary. Organization is now resolved from the verified session only.
    """
    return _resolve_org_id()


def _scoped_customer(customer_id: int):
    """Return the customer ONLY if it belongs to the caller's organization.

    Fails closed: an id that exists in another tenant is indistinguishable
    from a missing id (404) — no cross-tenant existence oracle.
    """
    from app.customers.models import Customer
    org_id = _org_context()
    if not org_id:
        return None, None
    customer = Customer.query.filter_by(
        id=customer_id, tenant_id=org_id
    ).first()
    return customer, org_id


def _scoped_commitment(cid: int, org_id: int):
    """Return a commitment only when its customer relationship is in-org."""
    from app.commitments.models import Commitment
    from app.customers.models import Customer
    cm = Commitment.query.get(cid)
    if not cm:
        return None
    if not cm.relationship_id:
        return None
    owned = Customer.query.filter_by(
        relationship_id=cm.relationship_id, tenant_id=org_id
    ).first()
    return cm if owned else None


@cust_bp.route("/profile/<int:customer_id>", methods=["GET"])
@require_permission("rel.view")
def profile(customer_id):
    customer, org_id = _scoped_customer(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    result = cx.get_customer_profile(customer.id)
    if result is None:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(result)


@cust_bp.route("/history/<int:customer_id>", methods=["GET"])
@require_permission("rel.view")
def history(customer_id):
    customer, org_id = _scoped_customer(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    result = cx.get_customer_history(customer.id)
    return jsonify({"history": result})


@cust_bp.route("/commitments", methods=["POST"])
@require_permission("rel.create")
def create_commitment():
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
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
@require_permission("rel.view")
def commitment(cid):
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    from app.commitments.models import Commitment
    cm = _scoped_commitment(cid, org_id)
    if not cm:
        return jsonify({"error": "Commitment not found"}), 404
    if request.method == "GET":
        return jsonify({"id": cm.id, "title": cm.title, "owner": cm.owner,
                         "due_at": cm.due_at.isoformat() if cm.due_at else None,
                         "status": cm.status, "issue_type": cm.issue_type,
                         "relationship_id": cm.relationship_id})
    if not _has_perm("rel.edit"):
        return jsonify({"success": False, "error": "Forbidden: missing permission"}), 403
    data = request.get_json() or {}
    for k in ("status", "owner", "title", "issue_type"):
        if k in data:
            setattr(cm, k, data[k])
    db.session.commit()
    return jsonify({"id": cm.id, "status": cm.status})


@cust_bp.route("/escalations", methods=["POST"])
@require_permission("rel.create")
def create_escalation():
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
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
@require_permission("rel.create")
def create_issue():
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    data = request.get_json() or {}
    cm = cx.create_issue(
        relationship_id=data.get("relationship_id", 0),
        title=data.get("title", "Issue"),
        severity=data.get("severity", "medium"),
        owner=data.get("owner"),
    )
    return jsonify({"id": cm.id, "title": cm.title, "status": cm.status}), 201


@cust_bp.route("/retention/<int:customer_id>", methods=["GET"])
@require_permission("rel.view")
def retention(customer_id):
    customer, org_id = _scoped_customer(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    result = cx.get_retention_signals(customer.id)
    return jsonify(result)


@cust_bp.route("/commitments/<int:cid>/resolve", methods=["POST"])
@require_permission("rel.edit")
def resolve_commitment(cid):
    org_id = _org_context()
    if not org_id:
        return jsonify({"error": "No organization context"}), 400
    cm = _scoped_commitment(cid, org_id)
    if not cm:
        return jsonify({"error": "Commitment not found"}), 404
    data = request.get_json() or {}
    result = cx.resolve_commitment(cm.id, data.get("resolution_note", ""))
    if result is None:
        return jsonify({"error": "Commitment not found"}), 404
    return jsonify(result)


def _has_perm(permission: str) -> bool:
    from app.authz.services import check_permission
    from app.authz.decorators import _resolve_identity
    identity = _resolve_identity()
    org_id = _org_context()
    if not identity or not org_id:
        return False
    return check_permission(org_id, identity, permission)