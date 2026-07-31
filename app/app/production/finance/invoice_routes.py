"""SHUNYA — Invoice API Routes (Finance).

Endpoints for creating and listing invoices.
Uses the Invoice model from app.models (legacy schema).
"""

from datetime import date, datetime

from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import Invoice, InvoiceStatus, Lead

finance_invoice_bp = Blueprint("finance_invoice", __name__)


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


@finance_invoice_bp.route("/invoice", methods=["POST"])
@login_required
def create_invoice():
    """Create a new invoice.

    Request body:
        lead_id (int, required) — ID of the lead being invoiced
        total_amount (float, optional) — pre-tax total
        tax (float, optional) — tax amount
        tax_rate (float, optional) — tax rate percentage (e.g. 18.00)
        discount (float, optional) — discount amount
        grand_total (float, required) — final amount after tax/discount
        currency (str, optional) — currency code (default: INR)
        due_date (str, optional) — ISO date string (YYYY-MM-DD)
        status (str, optional) — invoice status (default: draft)

    Returns:
        201 — Invoice created
    """
    data = _require_json()
    lead_id = _require_field(data, "lead_id", "Lead ID")
    lead_id = int(lead_id)

    # Verify lead exists
    lead = db.session.get(Lead, lead_id)
    if not lead:
        raise NotFound(f"Lead with id {lead_id} not found")

    grand_total = _require_field(data, "grand_total", "Grand total")
    grand_total = float(grand_total)

    # Generate invoice number: INV-{YYYYMMDD}-{random 4 digits}
    import random
    today = date.today().strftime("%Y%m%d")
    invoice_number = f"INV-{today}-{random.randint(1000, 9999)}"

    invoice = Invoice(
        lead_id=lead_id,
        invoice_number=invoice_number,
        total_amount=float(data.get("total_amount", 0) or 0),
        tax=float(data.get("tax", 0) or 0),
        tax_rate=float(data.get("tax_rate", 0) or 0),
        discount=float(data.get("discount", 0) or 0),
        grand_total=grand_total,
        currency=data.get("currency", "INR"),
        status=data.get("status", InvoiceStatus.DRAFT.value),
        due_date=(
            datetime.strptime(data["due_date"], "%Y-%m-%d").date()
            if data.get("due_date")
            else None
        ),
        raised_at=datetime.utcnow(),
    )

    db.session.add(invoice)
    db.session.commit()

    return jsonify({
        "success": True,
        "data": invoice.to_dict(),
    }), 201


@finance_invoice_bp.route("/invoice", methods=["GET"])
@login_required
def list_invoices():
    """List invoices for the current user's organization.

    Query parameters:
        lead_id (int, optional) — filter by lead
        status (str, optional) — filter by status (draft, sent, paid, void, overdue)
        page (int, optional) — page number (default: 1)
        per_page (int, optional) — items per page (default: 20, max: 100)

    Returns:
        200 — Paginated list of invoices
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Invoice.query

    # Filter by lead_id if provided
    lead_id = request.args.get("lead_id", type=int)
    if lead_id is not None:
        query = query.filter(Invoice.lead_id == lead_id)

    # Filter by status if provided
    status = request.args.get("status")
    if status:
        query = query.filter(Invoice.status == status)

    # Order by most recent first
    query = query.order_by(Invoice.raised_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "data": [inv.to_dict() for inv in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })