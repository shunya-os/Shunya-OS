"""Supplier REST API — canonical CRUD with tenant isolation.

GATE 5: Real Supplier capability.
Routes at /api/v1/suppliers/
"""
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request, session
from sqlalchemy import desc

from app import db
from app.authz.decorators import _resolve_org_id, require_permission
from app.models import Supplier

supplier_bp = Blueprint("suppliers", __name__, url_prefix="/api/v1/suppliers")


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
@supplier_bp.route("/", methods=["GET"])
@require_permission("rel.view")
def list_suppliers():
    """List suppliers scoped to the current organization."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    category = request.args.get("category")
    status = request.args.get("status")
    q = Supplier.query.filter(
        (Supplier.tenant_id == org_id) | (Supplier.tenant_id.is_(None))
    )
    if category:
        q = q.filter(Supplier.category == category)
    if status:
        q = q.filter(Supplier.status == status)
    q = q.order_by(desc(Supplier.created_at))

    items, total, page, per_page = _paginate(q)
    return jsonify({
        "success": True,
        "data": [s.to_dict() for s in items],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@supplier_bp.route("/", methods=["POST"])
@require_permission("rel.create")
def create_supplier():
    """Create a new supplier."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "Supplier name is required"}), 400

    existing = Supplier.query.filter_by(name=name).first()
    if existing:
        return jsonify({"success": False, "error": "Supplier with this name already exists"}), 409

    now = datetime.now(timezone.utc)
    supplier = Supplier(
        name=name,
        category=(body.get("category") or "").strip(),
        contact=(body.get("contact") or "").strip(),
        email=(body.get("email") or "").strip(),
        phone=(body.get("phone") or "").strip(),
        city=(body.get("city") or "").strip(),
        gstin=(body.get("gstin") or "").strip(),
        payment_terms=(body.get("payment_terms") or "").strip(),
        notes=(body.get("notes") or "").strip(),
        rating=body.get("rating", 0),
        status=body.get("status", "active"),
        tenant_id=org_id,
        workspace_id=_workspace_id(),
        created_by=_identity_id(),
        created_at=now,
        updated_at=now,
    )
    db.session.add(supplier)
    db.session.commit()

    return jsonify({"success": True, "data": supplier.to_dict()}), 201


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------
@supplier_bp.route("/<int:supplier_id>", methods=["GET"])
@require_permission("rel.view")
def get_supplier(supplier_id: int):
    """Get a single supplier by ID."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({"success": False, "error": "Supplier not found"}), 404

    if supplier.tenant_id and supplier.tenant_id != org_id:
        return jsonify({"success": False, "error": "Supplier not found"}), 404

    return jsonify({"success": True, "data": supplier.to_dict()})


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@supplier_bp.route("/<int:supplier_id>", methods=["PUT", "PATCH"])
@require_permission("rel.update")
def update_supplier(supplier_id: int):
    """Update a supplier."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({"success": False, "error": "Supplier not found"}), 404

    if supplier.tenant_id and supplier.tenant_id != org_id:
        return jsonify({"success": False, "error": "Supplier not found"}), 404

    body = request.get_json(silent=True) or {}
    updatable = {
        "name", "category", "contact", "email", "phone", "city",
        "gstin", "payment_terms", "notes", "rating", "status",
    }
    for key in updatable:
        if key in body:
            setattr(supplier, key, body[key])

    if "name" in body and not (body.get("name") or "").strip():
        return jsonify({"success": False, "error": "Supplier name cannot be empty"}), 400

    supplier.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"success": True, "data": supplier.to_dict()})


# ---------------------------------------------------------------------------
# ARCHIVE (soft delete)
# ---------------------------------------------------------------------------
@supplier_bp.route("/<int:supplier_id>", methods=["DELETE"])
@require_permission("rel.delete")
def archive_supplier(supplier_id: int):
    """Archive (soft-delete) a supplier."""
    org_id = _resolve_org_id()
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400

    supplier = db.session.get(Supplier, supplier_id)
    if not supplier:
        return jsonify({"success": False, "error": "Supplier not found"}), 404

    if supplier.tenant_id and supplier.tenant_id != org_id:
        return jsonify({"success": False, "error": "Supplier not found"}), 404

    supplier.status = "archived"
    supplier.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"success": True, "data": {"id": supplier.id, "status": "archived"}})