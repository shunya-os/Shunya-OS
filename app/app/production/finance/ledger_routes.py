"""SHUNYA — Ledger API Routes (Finance).

Customer ledger, supplier ledger, outstanding tracking, and payment reminders.
"""
from datetime import datetime, date

from flask import Blueprint, request, jsonify, g
from sqlalchemy import func, case
from werkzeug.exceptions import BadRequest, NotFound

from app import db
from app.auth_routes import login_required
from app.models import Invoice, InvoiceStatus, Payment, PaymentType, Lead, Supplier

finance_ledger_bp = Blueprint("finance_ledger", __name__)


# ---------------------------------------------------------------------------
# Helpers
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
# GET /ledger/customer — Customer-wise ledger
# ---------------------------------------------------------------------------

@finance_ledger_bp.route("/ledger/customer", methods=["GET"])
@login_required
def customer_ledger():
    """Customer ledger showing invoices raised and payments received per customer.

    Query parameters:
        lead_id (int, optional) — filter to a single lead
        page (int, optional) — page number (default: 1)
        per_page (int, optional) — items per page (default: 20, max: 100)

    Returns:
        200 — Array of customer ledger entries
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Lead.query.order_by(Lead.created_at.desc())

    lead_id = request.args.get("lead_id", type=int)
    if lead_id is not None:
        query = query.filter(Lead.id == lead_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Build ledger entries per customer
    entries = []
    for lead in pagination.items:
        invoices = lead.invoices.all()
        payments = lead.payments.filter(Payment.type == PaymentType.GUEST.value).all()

        total_invoiced = sum(float(i.grand_total or 0) for i in invoices)
        total_paid = sum(float(p.amount or 0) for p in payments)
        outstanding = round(total_invoiced - total_paid, 2)

        entries.append({
            "lead_id": lead.id,
            "customer_name": lead.customer_name,
            "code": lead.code,
            "phone": lead.phone,
            "email": lead.email,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "outstanding": outstanding,
            "invoice_count": len(invoices),
            "payment_count": len(payments),
            "invoices": [
                {
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "grand_total": float(inv.grand_total or 0),
                    "status": inv.status,
                    "due_date": inv.due_date.isoformat() if inv.due_date else None,
                    "raised_at": inv.raised_at.isoformat() if inv.raised_at else None,
                }
                for inv in invoices
            ],
            "payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount or 0),
                    "method": p.method,
                    "ref_number": p.ref_number,
                    "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                }
                for p in payments
            ],
        })

    return jsonify({
        "success": True,
        "data": entries,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


# ---------------------------------------------------------------------------
# GET /ledger/supplier — Supplier-wise ledger
# ---------------------------------------------------------------------------

@finance_ledger_bp.route("/ledger/supplier", methods=["GET"])
@login_required
def supplier_ledger():
    """Supplier ledger showing payments made to suppliers, grouped by supplier.

    Query parameters:
        supplier_id (int, optional) — filter to a single supplier
        lead_id (int, optional) — filter by lead
        page (int, optional) — page number (default: 1)
        per_page (int, optional) — items per page (default: 20, max: 100)

    Returns:
        200 — Array of supplier ledger entries
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    query = Supplier.query.order_by(Supplier.name.asc())

    supplier_id = request.args.get("supplier_id", type=int)
    if supplier_id is not None:
        query = query.filter(Supplier.id == supplier_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    entries = []
    for supplier in pagination.items:
        # Get leads with supplier_payment for this supplier
        # Supplier payments reference a lead; we look up by supplier name/ref
        supplier_payments = (
            Payment.query
            .filter(
                Payment.type == PaymentType.SUPPLIER.value,
                Payment.ref_number.like(f"%{supplier.name}%") if supplier.name else False,
            )
            .order_by(Payment.paid_at.desc())
            .all()
        )

        total_paid = sum(float(p.amount or 0) for p in supplier_payments)

        entries.append({
            "supplier_id": supplier.id,
            "name": supplier.name,
            "category": supplier.category,
            "city": supplier.city,
            "contact": supplier.contact,
            "email": supplier.email,
            "phone": supplier.phone,
            "payment_terms": supplier.payment_terms,
            "total_paid": total_paid,
            "payment_count": len(supplier_payments),
            "payments": [
                {
                    "id": p.id,
                    "lead_id": p.lead_id,
                    "amount": float(p.amount or 0),
                    "method": p.method,
                    "ref_number": p.ref_number,
                    "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                    "notes": p.notes,
                }
                for p in supplier_payments
            ],
        })

    return jsonify({
        "success": True,
        "data": entries,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


# ---------------------------------------------------------------------------
# GET /outstanding — Outstanding / unpaid invoices
# ---------------------------------------------------------------------------

@finance_ledger_bp.route("/outstanding", methods=["GET"])
@login_required
def outstanding():
    """List outstanding (unpaid / overdue) invoices.

    Query parameters:
        status (str, optional) — filter: sent | overdue | all (default: all)
        lead_id (int, optional) — filter by lead
        page (int, optional) — page number (default: 1)
        per_page (int, optional) — items per page (default: 20, max: 100)

    Returns:
        200 — Array of outstanding invoice entries
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)

    # Outstanding = invoices that are sent or overdue (not paid, void, or draft)
    query = Invoice.query.filter(
        Invoice.status.in_([InvoiceStatus.SENT.value, InvoiceStatus.OVERDUE.value])
    ).order_by(Invoice.due_date.asc().nullslast())

    status_filter = request.args.get("status")
    if status_filter and status_filter in ("sent", "overdue"):
        query = query.filter(Invoice.status == status_filter)

    lead_id = request.args.get("lead_id", type=int)
    if lead_id is not None:
        query = query.filter(Invoice.lead_id == lead_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    entries = []
    for inv in pagination.items:
        lead = db.session.get(Lead, inv.lead_id) if inv.lead_id else None
        days_overdue = None
        if inv.due_date and inv.status == InvoiceStatus.OVERDUE.value:
            delta = date.today() - inv.due_date
            days_overdue = delta.days if delta.days >= 0 else 0

        entries.append({
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "lead_id": inv.lead_id,
            "customer_name": lead.customer_name if lead else None,
            "grand_total": float(inv.grand_total or 0),
            "currency": inv.currency,
            "status": inv.status,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "days_overdue": days_overdue,
            "raised_at": inv.raised_at.isoformat() if inv.raised_at else None,
        })

    return jsonify({
        "success": True,
        "data": entries,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        },
    })


# ---------------------------------------------------------------------------
# POST /reminder — Send/log a payment reminder
# ---------------------------------------------------------------------------

@finance_ledger_bp.route("/reminder", methods=["POST"])
@login_required
def send_reminder():
    """Log or send a payment reminder for an unpaid invoice.

    Request body:
        lead_id (int, required) — ID of the lead to remind
        invoice_id (int, optional) — specific invoice to remind about
        message (str, optional) — custom reminder message
        method (str, optional) — how the reminder is being sent (email | sms | manual) (default: manual)

    Returns:
        201 — Reminder logged
    """
    data = _require_json()

    # Accept either invoice_id (look up lead from invoice) or explicit lead_id
    invoice_id_raw = data.get("invoice_id")
    lead_id_raw = data.get("lead_id")

    if invoice_id_raw is not None:
        invoice_id = int(invoice_id_raw)
        invoice = db.session.get(Invoice, invoice_id)
        if not invoice:
            raise NotFound(f"Invoice with id {invoice_id} not found")
        lead = db.session.get(Lead, invoice.lead_id)
        lead_id = invoice.lead_id
    elif lead_id_raw is not None:
        lead_id = int(lead_id_raw)
        lead = db.session.get(Lead, lead_id)
        if not lead:
            raise NotFound(f"Lead with id {lead_id} not found")
        invoice_id = data.get("invoice_id")
    else:
        raise BadRequest("Either 'invoice_id' or 'lead_id' is required")

    if invoice_id is not None:
        invoice_id = int(invoice_id)
    target_invoice = None

    if invoice_id is not None:
        invoice_id = int(invoice_id)
        target_invoice = db.session.get(Invoice, invoice_id)
        if not target_invoice:
            raise NotFound(f"Invoice with id {invoice_id} not found")
        if target_invoice.lead_id != lead_id:
            raise BadRequest("Invoice does not belong to the specified lead")

    message = data.get("message", "").strip()
    method = data.get("method", "manual")

    # Log the reminder as an activity on the lead
    invoice_ref = f" #{target_invoice.invoice_number}" if target_invoice else ""
    reminder_note = (
        message
        or f"Payment reminder sent via {method} for lead {lead.code}{invoice_ref}"
    )

    lead.log_activity(
        action="payment_reminder",
        detail=f"[{method}] {reminder_note}",
        user=getattr(g, "current_user", ""),
    )

    return jsonify({
        "success": True,
        "data": {
            "lead_id": lead_id,
            "lead_code": lead.code,
            "customer_name": lead.customer_name,
            "invoice_id": target_invoice.id if target_invoice else None,
            "invoice_number": target_invoice.invoice_number if target_invoice else None,
            "method": method,
            "message": reminder_note,
        },
    }), 201
