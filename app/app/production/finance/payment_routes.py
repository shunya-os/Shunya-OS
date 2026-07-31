"""SHUNYA — Payment API Routes (Finance).

Endpoints for recording payments.
Uses the Payment model from app.models (legacy schema).
"""

from datetime import datetime

from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import Payment, PaymentType, Lead

finance_payment_bp = Blueprint("finance_payment", __name__)


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
    """Get a required field, raising BadRequest if missing/empty."""
    label = label or field
    value = data.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise BadRequest(f"'{label}' is required")
    return value


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@finance_payment_bp.route("/payment", methods=["POST"])
@login_required
def record_payment():
    """Record a new payment.

    Request body:
        lead_id (int, required) — ID of the lead this payment is for
        type (str, optional) — payment type: guest_payment | supplier_payment | refund | deposit (default: guest_payment)
        amount (float, required) — payment amount
        method (str, optional) — payment method (e.g. bank_transfer, cash, upi, credit_card)
        ref_number (str, optional) — reference / transaction number
        paid_at (str, optional) — ISO datetime string (default: now)
        notes (str, optional) — payment notes

    Returns:
        201 — Payment recorded
    """
    data = _require_json()
    lead_id = _require_field(data, "lead_id", "Lead ID")
    lead_id = int(lead_id)

    # Verify lead exists
    lead = db.session.get(Lead, lead_id)
    if not lead:
        raise NotFound(f"Lead with id {lead_id} not found")

    amount = _require_field(data, "amount", "Amount")
    amount = float(amount)

    # Parse paid_at if provided
    paid_at = None
    if data.get("paid_at"):
        try:
            paid_at = datetime.fromisoformat(data["paid_at"])
        except (ValueError, TypeError):
            raise BadRequest("Invalid 'paid_at' format. Use ISO datetime (e.g. 2024-12-01T10:30:00)")

    payment = Payment(
        lead_id=lead_id,
        type=data.get("type", PaymentType.GUEST.value),
        amount=amount,
        method=data.get("method", ""),
        ref_number=data.get("ref_number", ""),
        paid_at=paid_at or datetime.utcnow(),
        notes=data.get("notes", ""),
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": payment.to_dict(),
    }), 201