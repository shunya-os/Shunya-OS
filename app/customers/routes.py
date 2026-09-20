"""Customer REST API — canonical CRUD with tenant isolation.

GATE 3/4: Real Customer capability.
Routes at /api/v1/customers/
"""
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request, session
from sqlalchemy import desc

from app import db
from app.authz.decorators import _resolve_org_id, require_permission
from app.customers.models import Customer

customer_bp = Blueprint("customers", __name__, url_prefix="/api/v1/customers")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _workspace_id() -> str | None:
    return request.headers.get("X-Workspace-Id") or g.get("workspace_id")


def _paginate(query, page_arg="page", per_page_arg="per_page"):
    page = max(request.args.get(page_arg, 1, type=int), 1)
    per_page = min(max(request.args.get(per_page_arg, 50, type=int), 1), 200)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total, page, per_page


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------
@customer_bp.route("/", methods=["GET"])
@require_permission("rel.view")
def list_customers():
    """List customers scoped to the current organization."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    status = request.args.get("status")
    q = Customer.query.filter(
        (Customer.tenant_id == org_id) | (Customer.tenant_id.is_(None))
    )
    if status:
        q = q.filter(Customer.status == status)
    q = q.order_by(desc(Customer.created_at))

    items, total, page, per_page = _paginate(q)
    return jsonify({
        "success": True,
        "data": [c.to_dict() for c in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@customer_bp.route("/", methods=["POST"])
@require_permission("rel.create")
def create_customer():
    """Create a new customer."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "Customer name is required"}), 400

    now = datetime.now(timezone.utc)
    customer = Customer(
        name=name,
        phone=(body.get("phone") or "").strip(),
        email=(body.get("email") or "").strip(),
        status=body.get("status", "active"),
        tenant_id=org_id,
        created_at=now,
        updated_at=now,
    )
    db.session.add(customer)
    db.session.commit()

    return jsonify({"success": True, "data": customer.to_dict()}), 201


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------
@customer_bp.route("/<int:customer_id>", methods=["GET"])
@require_permission("rel.view")
def get_customer(customer_id: int):
    """Get a single customer by ID."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    if customer.tenant_id and customer.tenant_id != org_id:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    return jsonify({"success": True, "data": customer.to_dict()})


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@customer_bp.route("/<int:customer_id>", methods=["PUT", "PATCH"])
@require_permission("rel.update")
def update_customer(customer_id: int):
    """Update a customer."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    if customer.tenant_id and customer.tenant_id != org_id:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    body = request.get_json(silent=True) or {}
    updatable = {"name", "phone", "email", "status"}
    for key in updatable:
        if key in body:
            setattr(customer, key, body[key])

    if "name" in body and not (body.get("name",) or "").strip():
        return jsonify({"success": False, "error": "Customer name cannot be empty"}), 400

    customer.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"success": True, "data": customer.to_dict()})


# ---------------------------------------------------------------------------
# ARCHIVE (soft delete)
# ---------------------------------------------------------------------------
@customer_bp.route("/<int:customer_id>", methods=["DELETE"])
@require_permission("rel.delete")
def archive_customer(customer_id: int):
    """Archive (soft-delete) a customer."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    if customer.tenant_id and customer.tenant_id != org_id:
        return jsonify({"success": False, "error": "Customer not found"}), 404

    customer.status = "archived"
    customer.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"success": True, "data": {"id": customer.id, "status": "archived"}})