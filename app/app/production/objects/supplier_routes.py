"""SHUNYA — Supplier creation route.

POST /api/v1/objects/supplier
Creates a new Supplier record.
"""
from datetime import datetime

from flask import request, jsonify, g
from werkzeug.exceptions import BadRequest

from app import db
from app.auth_routes import login_required
from app.models import Supplier
from app.production.objects import objects_bp


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _require_json() -> dict:
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON")
    return data


def _require_field(data: dict, field: str, label: str = "") -> str:
    label = label or field
    value = data.get(field)
    if not value or not str(value).strip():
        raise BadRequest(f"'{label}' is required")
    return str(value).strip()


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _supplier_to_dict(supplier: Supplier) -> dict:
    """Serialize a supplier to the standard envelope."""
    return {
        "id": supplier.id,
        "name": supplier.name,
        "category": supplier.category or "",
        "contact": supplier.contact or "",
        "email": supplier.email or "",
        "phone": supplier.phone or "",
        "city": supplier.city or "",
        "gstin": supplier.gstin or "",
        "payment_terms": supplier.payment_terms or "",
        "notes": supplier.notes or "",
        "rating": supplier.rating or 0,
        "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@objects_bp.route("/supplier", methods=["POST"])
@login_required
def create_supplier():
    """Create a new supplier.

    Request body:
    {
        "name": "Grand Hyatt",        # required
        "category": "hotel",           # optional: hotel / flight / transport / activity / venue
        "contact": "Reservations",     # optional
        "email": "reservations@hyatt.com",  # optional
        "phone": "+1-555-0199",        # optional
        "city": "Mumbai",              # optional
        "gstin": "GSTIN5678",          # optional
        "payment_terms": "Net 30",     # optional
        "notes": "Preferred hotel partner",  # optional
        "rating": 4                    # optional (0-5)
    }
    """
    data = _require_json()
    name = _require_field(data, "name", "Supplier name")

    # Parse rating (int, can be string from JSON)
    raw_rating = data.get("rating")
    if raw_rating is not None:
        try:
            rating = int(raw_rating)
        except (ValueError, TypeError):
            rating = 0
    else:
        rating = 0

    supplier = Supplier(
        name=name,
        category=data.get("category", "").strip(),
        contact=data.get("contact", "").strip(),
        email=data.get("email", "").strip(),
        phone=data.get("phone", "").strip(),
        city=data.get("city", "").strip(),
        gstin=data.get("gstin", "").strip(),
        payment_terms=data.get("payment_terms", "").strip(),
        notes=data.get("notes", "").strip(),
        rating=rating,
    )
    db.session.add(supplier)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": _supplier_to_dict(supplier),
    }), 201