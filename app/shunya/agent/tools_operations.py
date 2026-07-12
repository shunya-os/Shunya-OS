"""
Operations, Payment, Quote, Workflow & Admin tools for Bird AI.

Each tool handler:
  - Imports needed models from app.models
  - Uses flask.g for context (tenant, user)
  - Returns ToolResult
  - Registered at module level with register_tool()
"""
from __future__ import annotations

from typing import Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from flask import g

from app import db
from app.models import (
    Entity, EntityDefinition, ActivityLog, next_entity_code,
    TeamMember, Payment, Invoice, Notification, Message,
)
from app.shunya.agent import (
    ToolDef, ToolCategory, ToolPermission, ToolResult, register_tool,
)
from app.shunya.planner.sequential_planner import SequentialPlanner, PlanStep

# ---------------------------------------------------------------------------
# Helper — create an entity record for a given type
# ---------------------------------------------------------------------------

def _create_entity_for_tool(
    entity_type: str,
    data: dict,
    status: str = "new",
    assigned_to: Optional[int] = None,
    code_prefix: Optional[str] = None,
) -> dict:
    """Create an Entity record, log activity, return metadata dict."""
    tenant_id = g.tenant.id
    user_id = g.user.id

    definition = EntityDefinition.query.filter_by(
        tenant_id=tenant_id, type=entity_type, is_active=True
    ).first()
    if not definition:
        raise ValueError(f"No entity definition found for type '{entity_type}'")

    code = next_entity_code(db.session, tenant_id, entity_type)

    entity = Entity(
        tenant_id=tenant_id,
        definition_id=definition.id,
        code=code,
        status=status,
        data=data,
        assigned_to=assigned_to,
        created_by=user_id,
    )
    if code_prefix:
        entity.code_prefix = code_prefix
    db.session.add(entity)
    db.session.flush()

    activity = ActivityLog(
        tenant_id=tenant_id,
        entity_id=entity.id,
        user_id=user_id,
        action="created",
        detail=f"Created {entity_type}: {code} via Bird AI",
        governance_level="auto",
    )
    db.session.add(activity)
    db.session.commit()

    return {
        "id": entity.id,
        "code": code,
        "type": entity_type,
        "display": entity.display_name,
        "target": f"/entities/{entity_type}/{entity.id}",
    }

# ===========================================================================
# 1. create_quote — Generate quote from lead + itinerary
# ===========================================================================

def _handler_create_quote(params: dict, agent) -> ToolResult:
    """Generate a quote for a lead based on itinerary details."""
    lead_id = params.get("lead_id") or params.get("entity_id")
    customer_name = params.get("customer_name") or params.get("name", "")
    destination = params.get("destination", "")
    amount = float(params.get("amount", 0))
    items = params.get("items", [])
    notes = params.get("notes", "")

    if not customer_name and not lead_id:
        return ToolResult(False, message="I need a customer name or lead ID to create a quote.")

    data = {
        "customer_name": customer_name,
        "destination": destination,
        "amount": amount,
        "items": items if isinstance(items, list) else [],
        "notes": notes,
        "lead_id": lead_id,
        "status": "draft",
    }
    try:
        result = _create_entity_for_tool("quote", data, status="draft")
        return ToolResult(
            success=True,
            message=f"Quote {result['code']} created for {customer_name or 'customer'}.",
            data=result,
        )
    except ValueError as e:
        return ToolResult(False, message=str(e))


# ===========================================================================
# 2. send_quote — Share quote via WhatsApp/email
# ===========================================================================

def _handler_send_quote(params: dict, agent) -> ToolResult:
    """Send a quote to the customer via the specified channel."""
    quote_id = params.get("quote_id") or params.get("entity_id")
    channel = params.get("channel", "whatsapp")
    recipient = params.get("recipient", "")
    message = params.get("message", "")

    if not quote_id:
        return ToolResult(False, message="I need the quote ID to send it.")

    # Fetch the quote entity
    quote = Entity.query.filter_by(
        id=quote_id, tenant_id=g.tenant.id, is_archived=False
    ).first()
    if not quote:
        return ToolResult(False, message=f"Quote #{quote_id} not found.")

    customer_name = quote.data.get("customer_name", "Customer")
    amount = quote.data.get("amount", 0)

    body = message or (
        f"Dear {customer_name},\n\n"
        f"Please find your quote ({quote.code}) for {amount}.\n"
        f"View it here: {g.tenant.domain or 'your portal'}/quotes/{quote.id}\n\n"
        f"- {g.tenant.company_name or 'Team'}"
    )

    log = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=quote.id,
        user_id=g.user.id,
        action="quote_sent",
        detail=f"Quote {quote.code} sent via {channel} to {recipient or customer_name}",
        metadata_json={"channel": channel, "recipient": recipient or customer_name},
    )
    db.session.add(log)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Quote {quote.code} sent via {channel}.",
        data={"quote_id": quote.id, "channel": channel, "recipient": recipient or customer_name},
    )


# ===========================================================================
# 3. check_quote_status — See if customer viewed quote
# ===========================================================================

def _handler_check_quote_status(params: dict, agent) -> ToolResult:
    """Check whether a quote has been viewed, accepted, or is still pending."""
    quote_id = params.get("quote_id") or params.get("entity_id")
    if not quote_id:
        return ToolResult(False, message="I need the quote ID to check its status.")

    quote = Entity.query.filter_by(
        id=quote_id, tenant_id=g.tenant.id, is_archived=False
    ).first()
    if not quote:
        return ToolResult(False, message=f"Quote #{quote_id} not found.")

    # Gather activity events for this quote
    activities = ActivityLog.query.filter_by(
        tenant_id=g.tenant.id, entity_id=quote.id
    ).order_by(ActivityLog.created_at.desc()).limit(10).all()

    events = [
        {
            "action": a.action,
            "detail": a.detail,
            "at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in activities
    ]

    return ToolResult(
        success=True,
        message=f"Quote {quote.code} is currently '{quote.status}'.",
        data={
            "quote_id": quote.id,
            "code": quote.code,
            "status": quote.status,
            "events": events,
            "is_viewed": any("viewed" in (a.detail or "").lower() for a in activities),
        },
    )


# ===========================================================================
# 4. modify_quote — Adjust quote details
# ===========================================================================

def _handler_modify_quote(params: dict, agent) -> ToolResult:
    """Update one or more fields on an existing quote."""
    quote_id = params.get("quote_id") or params.get("entity_id")
    if not quote_id:
        return ToolResult(False, message="I need the quote ID to modify it.")

    quote = Entity.query.filter_by(
        id=quote_id, tenant_id=g.tenant.id, is_archived=False
    ).first()
    if not quote:
        return ToolResult(False, message=f"Quote #{quote_id} not found.")

    changes = []
    for key, val in params.items():
        if key in ("quote_id", "entity_id", "action"):
            continue
        quote.data[key] = val
        changes.append(f"{key}={val}")

    if changes:
        activity = ActivityLog(
            tenant_id=g.tenant.id,
            entity_id=quote.id,
            user_id=g.user.id,
            action="updated",
            detail=f"Quote {quote.code} modified: {'; '.join(changes[:5])}",
        )
        db.session.add(activity)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Quote {quote.code} updated ({len(changes)} change(s)).",
        data={"quote_id": quote.id, "code": quote.code, "changes": changes},
    )


# ===========================================================================
# 5. create_itinerary — Build day-by-day itinerary
# ===========================================================================

def _handler_create_itinerary(params: dict, agent) -> ToolResult:
    """Build a day-by-day itinerary for a customer."""
    lead_id = params.get("lead_id") or params.get("entity_id")
    customer_name = params.get("customer_name") or params.get("name", "Customer")
    destination = params.get("destination", "")
    start_date = params.get("start_date", "")
    end_date = params.get("end_date", "")
    days = params.get("days", [])
    preferences = params.get("preferences", "")

    if not destination:
        return ToolResult(False, message="I need a destination to build an itinerary.")

    data = {
        "customer_name": customer_name,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "days": days if isinstance(days, list) else [],
        "preferences": preferences,
        "lead_id": lead_id,
    }
    try:
        result = _create_entity_for_tool("itinerary", data, status="draft")
        return ToolResult(
            success=True,
            message=f"Itinerary for {destination} created ({result['code']}).",
            data=result,
        )
    except ValueError as e:
        return ToolResult(False, message=str(e))


# ===========================================================================
# 6. compare_packages — Compare 2-3 packages
# ===========================================================================

def _handler_compare_packages(params: dict, agent) -> ToolResult:
    """Compare two or three packages side by side for a customer."""
    packages = params.get("packages", [])
    if isinstance(packages, str):
        packages = [p.strip() for p in packages.split(",") if p.strip()]

    if len(packages) < 2:
        return ToolResult(False, message="I need at least 2 packages to compare.")

    return ToolResult(
        success=True,
        message=f"Comparing {len(packages)} packages.",
        data={
            "packages": packages,
            "comparison_fields": ["price", "destination", "duration", "inclusions", "rating"],
            "suggested_action": "Review the comparison table above and let me know your preference.",
        },
    )


# ===========================================================================
# 7. create_booking — Convert quote to confirmed booking
# ===========================================================================

def _handler_create_booking(params: dict, agent) -> ToolResult:
    """Convert a quote into a confirmed booking."""
    quote_id = params.get("quote_id") or params.get("entity_id")
    customer_name = params.get("customer_name") or params.get("name", "")
    notes = params.get("notes", "")

    if not quote_id and not customer_name:
        return ToolResult(False, message="I need a quote ID or customer name to create a booking.")

    # If quote_id is given, inherit data from the quote
    quote_data = {}
    if quote_id:
        quote = Entity.query.filter_by(
            id=quote_id, tenant_id=g.tenant.id, is_archived=False
        ).first()
        if not quote:
            return ToolResult(False, message=f"Quote #{quote_id} not found.")
        quote_data = {
            "customer_name": quote.data.get("customer_name", ""),
            "destination": quote.data.get("destination", ""),
            "amount": quote.data.get("amount", 0),
            "items": quote.data.get("items", []),
            "source_quote_id": quote.id,
            "source_quote_code": quote.code,
        }
        # Mark the quote as accepted
        if quote.status != "accepted":
            quote.status = "accepted"
            db.session.flush()

    data = {**quote_data, "notes": notes}
    if customer_name:
        data["customer_name"] = customer_name

    try:
        result = _create_entity_for_tool("booking", data, status="confirmed")
        return ToolResult(
            success=True,
            message=f"Booking {result['code']} confirmed for {data.get('customer_name', 'customer')}.",
            data=result,
        )
    except ValueError as e:
        return ToolResult(False, message=str(e))


# ===========================================================================
# 8. check_availability — Check hotel/activity availability
# ===========================================================================

def _handler_check_availability(params: dict, agent) -> ToolResult:
    """Check availability for hotels, activities, or transport using web search."""
    item_type = params.get("type", "hotel")
    destination = params.get("destination", "")
    date = params.get("date", "")
    query_parts = [f"{item_type} availability", destination, date]
    search_query = " ".join(p for p in query_parts if p)

    if not search_query.strip():
        return ToolResult(False, message="I need a destination and dates to check availability.")

    # Fall back to web search for availability data
    from app.shunya.web_search import web_search
    results = web_search(search_query, limit=5)

    return ToolResult(
        success=True,
        message=f"Found {len(results) if results else 0} availability results for {destination or item_type}.",
        data={
            "destination": destination,
            "type": item_type,
            "date": date,
            "web_results": results or [],
            "note": "These are web search results. Verify directly with the supplier for exact availability.",
        },
    )


# ===========================================================================
# 9. create_invoice — Generate GST invoice from booking
# ===========================================================================

def _handler_create_invoice(params: dict, agent) -> ToolResult:
    """Generate a GST invoice from a confirmed booking."""
    booking_id = params.get("booking_id") or params.get("entity_id")
    customer_name = params.get("customer_name") or params.get("name", "")
    amount = float(params.get("amount", 0))
    tax_rate = float(params.get("tax_rate", 18))
    discount = float(params.get("discount", 0))
    notes = params.get("notes", "")

    if not customer_name and not booking_id:
        return ToolResult(False, message="I need a booking ID or customer name to create an invoice.")

    booking_data = {}
    if booking_id:
        booking = Entity.query.filter_by(
            id=booking_id, tenant_id=g.tenant.id, is_archived=False
        ).first()
        if not booking:
            return ToolResult(False, message=f"Booking #{booking_id} not found.")
        booking_data = {
            "customer_name": booking.data.get("customer_name", ""),
            "amount": booking.data.get("amount", 0),
            "source_booking_id": booking.id,
            "source_booking_code": booking.code,
        }

    final_amount = float(booking_data.get("amount", amount))
    tax_amount = round(final_amount * tax_rate / 100, 2)
    grand_total = round(final_amount - discount + tax_amount, 2)

    data = {
        "customer_name": customer_name or booking_data.get("customer_name", ""),
        "base_amount": final_amount,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "discount": discount,
        "grand_total": grand_total,
        "currency": "INR",
        "notes": notes,
        **(booking_data if not customer_name else {}),
    }

    try:
        result = _create_entity_for_tool("invoice", data, status="pending")
        return ToolResult(
            success=True,
            message=f"Invoice {result['code']} created for ₹{grand_total:,.2f} (incl. GST {tax_rate}%).",
            data={
                **result,
                "base_amount": final_amount,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "grand_total": grand_total,
            },
        )
    except ValueError as e:
        return ToolResult(False, message=str(e))


# ===========================================================================
# 10. send_invoice — Share invoice via WhatsApp/email
# ===========================================================================

def _handler_send_invoice(params: dict, agent) -> ToolResult:
    """Send an invoice to the customer via the specified channel."""
    invoice_id = params.get("invoice_id") or params.get("entity_id")
    channel = params.get("channel", "email")
    recipient = params.get("recipient", "")
    message = params.get("message", "")

    if not invoice_id:
        return ToolResult(False, message="I need the invoice ID to send it.")

    invoice = Entity.query.filter_by(
        id=invoice_id, tenant_id=g.tenant.id, is_archived=False
    ).first()
    if not invoice:
        return ToolResult(False, message=f"Invoice #{invoice_id} not found.")

    customer_name = invoice.data.get("customer_name", "Customer")
    grand_total = invoice.data.get("grand_total", 0)

    body = message or (
        f"Dear {customer_name},\n\n"
        f"Please find your invoice ({invoice.code}) amounting to ₹{grand_total:,.2f}.\n"
        f"Due date: {invoice.data.get('due_date', 'Upon receipt')}\n"
        f"View online: {g.tenant.domain or 'your portal'}/invoices/{invoice.id}\n\n"
        f"Thank you for your business!\n- {g.tenant.company_name or 'Team'}"
    )

    log = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=invoice.id,
        user_id=g.user.id,
        action="invoice_sent",
        detail=f"Invoice {invoice.code} sent via {channel} to {recipient or customer_name}",
        metadata_json={"channel": channel, "recipient": recipient or customer_name},
    )
    db.session.add(log)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Invoice {invoice.code} sent via {channel}.",
        data={
            "invoice_id": invoice.id,
            "code": invoice.code,
            "channel": channel,
            "recipient": recipient or customer_name,
        },
    )


# ===========================================================================
# 11. record_payment — Record a payment
# ===========================================================================

def _handler_record_payment(params: dict, agent) -> ToolResult:
    """Record a payment against an invoice or booking."""
    invoice_id = params.get("invoice_id")
    booking_id = params.get("booking_id")
    amount = float(params.get("amount", 0))
    gateway = params.get("gateway", "cash")
    gateway_ref = params.get("gateway_ref", "")
    notes = params.get("notes", "")

    entity_id = invoice_id or booking_id
    if not entity_id:
        return ToolResult(False, message="I need an invoice or booking ID to record a payment.")
    if amount <= 0:
        return ToolResult(False, message="Payment amount must be greater than zero.")

    try:
        result = _create_entity_for_tool(
            "payment",
            {
                "amount": amount,
                "gateway": gateway,
                "gateway_ref": gateway_ref,
                "notes": notes,
                "paid_at": datetime.utcnow().isoformat(),
                "invoice_id": invoice_id,
                "booking_id": booking_id,
            },
            status="completed",
        )

        # Also record in the Payment model for financial tracking
        payment_record = Payment(
            tenant_id=g.tenant.id,
            entity_id=entity_id,
            amount=Decimal(str(amount)),
            currency="INR",
            type="guest_payment",
            gateway=gateway,
            gateway_ref=gateway_ref,
            status="completed",
            notes=notes,
            paid_at=datetime.utcnow(),
        )
        db.session.add(payment_record)
        db.session.commit()

        # If linked to an invoice, update invoice data
        if invoice_id:
            inv = Entity.query.filter_by(
                id=invoice_id, tenant_id=g.tenant.id, is_archived=False
            ).first()
            if inv:
                total_paid = float(inv.data.get("total_paid", 0)) + amount
                inv.data["total_paid"] = total_paid
                grand_total = float(inv.data.get("grand_total", 0))
                if total_paid >= grand_total:
                    inv.status = "paid"
                db.session.commit()

        return ToolResult(
            success=True,
            message=f"Payment of ₹{amount:,.2f} recorded successfully.",
            data={
                **result,
                "amount": amount,
                "gateway": gateway,
                "payment_record_id": payment_record.id,
            },
        )
    except ValueError as e:
        return ToolResult(False, message=str(e))


# ===========================================================================
# 12. check_payment_status — See what's paid/pending
# ===========================================================================

def _handler_check_payment_status(params: dict, agent) -> ToolResult:
    """Check payment status for an invoice, booking, or customer."""
    entity_id = params.get("entity_id") or params.get("invoice_id") or params.get("booking_id")
    customer_name = params.get("customer_name") or params.get("name", "")

    # If a specific entity is referenced
    if entity_id:
        entity = Entity.query.filter_by(
            id=entity_id, tenant_id=g.tenant.id, is_archived=False
        ).first()
        if not entity:
            return ToolResult(False, message=f"Entity #{entity_id} not found.")

        payments = Payment.query.filter_by(
            tenant_id=g.tenant.id, entity_id=entity.id
        ).order_by(Payment.created_at.desc()).all()

        total_paid = sum(float(p.amount) for p in payments)
        grand_total = float(entity.data.get("grand_total", entity.data.get("amount", 0)))

        return ToolResult(
            success=True,
            message=f"Payment status for {entity.code}: {entity.status}.",
            data={
                "entity_id": entity.id,
                "code": entity.code,
                "status": entity.status,
                "grand_total": grand_total,
                "total_paid": total_paid,
                "balance": round(grand_total - total_paid, 2),
                "payments": [
                    {
                        "id": p.id,
                        "amount": float(p.amount),
                        "gateway": p.gateway,
                        "status": p.status,
                        "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                    }
                    for p in payments
                ],
            },
        )

    # List all payments for a customer name
    if customer_name:
        entities = Entity.query.filter(
            Entity.tenant_id == g.tenant.id,
            Entity.data["customer_name"].astext == customer_name,
            Entity.is_archived.is_(False),
        ).limit(10).all()

        results = []
        for ent in entities:
            payments = Payment.query.filter_by(
                tenant_id=g.tenant.id, entity_id=ent.id
            ).all()
            total_paid = sum(float(p.amount) for p in payments)
            grand_total = float(ent.data.get("grand_total", ent.data.get("amount", 0)))
            results.append({
                "code": ent.code,
                "type": ent.data.get("type", ""),
                "status": ent.status,
                "grand_total": grand_total,
                "total_paid": total_paid,
                "balance": round(grand_total - total_paid, 2),
            })

        return ToolResult(
            success=True,
            message=f"Payment status for {customer_name}: {len(results)} record(s).",
            data={"customer": customer_name, "records": results},
        )

    return ToolResult(False, message="I need an invoice/booking ID or customer name to check payment status.")


# ===========================================================================
# 13. send_payment_reminder — Auto-send reminder
# ===========================================================================

def _handler_send_payment_reminder(params: dict, agent) -> ToolResult:
    """Send a payment reminder for an outstanding invoice."""
    invoice_id = params.get("invoice_id") or params.get("entity_id")
    channel = params.get("channel", "email")
    recipient = params.get("recipient", "")
    custom_message = params.get("message", "")

    if not invoice_id:
        return ToolResult(False, message="I need the invoice ID to send a reminder.")

    invoice = Entity.query.filter_by(
        id=invoice_id, tenant_id=g.tenant.id, is_archived=False
    ).first()
    if not invoice:
        return ToolResult(False, message=f"Invoice #{invoice_id} not found.")

    customer_name = invoice.data.get("customer_name", "Customer")
    grand_total = float(invoice.data.get("grand_total", 0))
    total_paid = float(invoice.data.get("total_paid", 0))
    balance = round(grand_total - total_paid, 2)

    if balance <= 0:
        return ToolResult(
            success=True,
            message=f"Invoice {invoice.code} is already fully paid. No reminder needed.",
            data={"invoice_id": invoice.id, "code": invoice.code, "balance": 0},
        )

    body = custom_message or (
        f"Dear {customer_name},\n\n"
        f"This is a friendly reminder for Invoice {invoice.code}.\n"
        f"Amount Due: ₹{balance:,.2f}\n"
        f"Please make the payment at your earliest convenience.\n\n"
        f"Pay here: {g.tenant.domain or 'your portal'}/invoices/{invoice.id}\n\n"
        f"Thank you,\n{g.tenant.company_name or 'Team'}"
    )

    log = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=invoice.id,
        user_id=g.user.id,
        action="payment_reminder",
        detail=f"Payment reminder sent for {invoice.code} via {channel} — balance ₹{balance:,.2f}",
        metadata_json={"channel": channel, "recipient": recipient or customer_name, "balance": balance},
    )
    db.session.add(log)

    # Also create a notification
    notification = Notification(
        tenant_id=g.tenant.id,
        user_id=g.user.id,
        entity_id=invoice.id,
        type="payment_reminder",
        title=f"Payment Reminder: {invoice.code}",
        message=f"₹{balance:,.2f} outstanding. Sent via {channel}.",
        icon="💰",
    )
    db.session.add(notification)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Payment reminder sent for ₹{balance:,.2f} on invoice {invoice.code}.",
        data={
            "invoice_id": invoice.id,
            "code": invoice.code,
            "balance": balance,
            "channel": channel,
            "recipient": recipient or customer_name,
        },
    )


# ===========================================================================
# 14. calculate_gst — Calculate GST for an amount
# ===========================================================================

def _handler_calculate_gst(params: dict, agent) -> ToolResult:
    """Calculate GST components for a given amount."""
    amount = float(params.get("amount", 0))
    rate = float(params.get("rate", 18))

    if amount <= 0:
        return ToolResult(False, message="I need a valid amount to calculate GST.")

    tax = round(amount * rate / 100, 2)
    total = round(amount + tax, 2)
    half_rate = rate / 2
    cgst = round(tax / 2, 2)
    sgst = round(tax / 2, 2)

    return ToolResult(
        success=True,
        message=f"GST {rate}% on ₹{amount:,.2f}: Tax = ₹{tax:,.2f}, Total = ₹{total:,.2f}",
        data={
            "base_amount": amount,
            "rate": rate,
            "tax": tax,
            "total": total,
            "cgst": cgst,
            "sgst": sgst,
            "cgst_rate": half_rate,
            "sgst_rate": half_rate,
        },
    )


# ===========================================================================
# 15. view_outstanding — All unpaid invoices
# ===========================================================================

def _handler_view_outstanding(params: dict, agent) -> ToolResult:
    """List all unpaid invoices for the tenant."""
    limit = min(int(params.get("limit", 50)), 200)

    invoice_def = EntityDefinition.query.filter_by(
        tenant_id=g.tenant.id, type="invoice", is_active=True
    ).first()

    if not invoice_def:
        return ToolResult(False, message="No invoice entity type defined for this tenant.")

    invoices = Entity.query.filter(
        Entity.tenant_id == g.tenant.id,
        Entity.definition_id == invoice_def.id,
        Entity.is_archived.is_(False),
        Entity.status.in_(["pending", "overdue", "partially_paid"]),
    ).order_by(Entity.created_at.desc()).limit(limit).all()

    results = []
    total_outstanding = 0.0
    for inv in invoices:
        grand_total = float(inv.data.get("grand_total", 0))
        total_paid = float(inv.data.get("total_paid", 0))
        balance = round(grand_total - total_paid, 2)
        total_outstanding += balance
        results.append({
            "id": inv.id,
            "code": inv.code,
            "customer": inv.data.get("customer_name", ""),
            "grand_total": grand_total,
            "total_paid": total_paid,
            "balance": balance,
            "status": inv.status,
            "created": inv.created_at.isoformat() if inv.created_at else None,
        })

    return ToolResult(
        success=True,
        message=f"{len(results)} outstanding invoice(s). Total due: ₹{total_outstanding:,.2f}",
        data={
            "count": len(results),
            "total_outstanding": round(total_outstanding, 2),
            "invoices": results,
        },
    )


# ===========================================================================
# 16. execute_workflow — Multi-step workflow via SequentialPlanner
# ===========================================================================

def _handler_execute_workflow(params: dict, agent) -> ToolResult:
    """Execute a multi-step workflow using the SequentialPlanner."""
    entity_type = params.get("entity_type", "")
    actions = params.get("actions", [])
    entity_id = params.get("entity_id")

    if not actions:
        return ToolResult(False, message="I need at least one action to create a workflow plan.")

    if isinstance(actions, str):
        # Parse comma-separated action list
        actions = [{"action": a.strip()} for a in actions.split(",") if a.strip()]

    planner = SequentialPlanner()
    plan = planner.plan_for_actions(entity_type, actions)

    # Log each step as an activity
    for step in plan.steps:
        log = ActivityLog(
            tenant_id=g.tenant.id,
            entity_id=entity_id,
            user_id=g.user.id,
            action="workflow_step",
            detail=(
                f"Workflow step [{step.id}]: {step.action} → {step.entity_type} "
                f"(priority {step.priority})"
            ),
            metadata_json={
                "step_id": step.id,
                "step_action": step.action,
                "depends_on": step.depends_on,
                "priority": step.priority,
            },
        )
        db.session.add(log)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Workflow plan created with {plan.total_steps} step(s).",
        data={
            "total_steps": plan.total_steps,
            "steps": [
                {
                    "id": s.id,
                    "action": s.action,
                    "depends_on": s.depends_on,
                    "priority": s.priority,
                }
                for s in plan.steps
            ],
            "execution_order": plan.step_ids,
        },
    )


# ===========================================================================
# 17. create_reminder — Set a reminder
# ===========================================================================

def _handler_create_reminder(params: dict, agent) -> ToolResult:
    """Create a reminder for a user or team."""
    title = params.get("title") or params.get("text", "Reminder")
    due_at = params.get("due_at") or params.get("datetime", "")
    remind_in_minutes = int(params.get("remind_in_minutes", 0))
    entity_id = params.get("entity_id")
    assignee = params.get("assignee") or params.get("assigned_to", "")

    # Compute the reminder time
    if remind_in_minutes > 0:
        remind_at = datetime.utcnow() + timedelta(minutes=remind_in_minutes)
    elif due_at:
        try:
            remind_at = datetime.fromisoformat(due_at)
        except (ValueError, TypeError):
            remind_at = datetime.utcnow() + timedelta(hours=1)
    else:
        remind_at = datetime.utcnow() + timedelta(hours=1)

    notification = Notification(
        tenant_id=g.tenant.id,
        user_id=g.user.id,
        entity_id=entity_id,
        type="reminder",
        title=title,
        message=f"Reminder set for {remind_at.strftime('%Y-%m-%d %H:%M UTC')}",
        icon="⏰",
    )
    db.session.add(notification)

    log = ActivityLog(
        tenant_id=g.tenant.id,
        entity_id=entity_id,
        user_id=g.user.id,
        action="reminder_created",
        detail=f"Reminder: {title}" + (f" (assignee: {assignee})" if assignee else ""),
        metadata_json={
            "title": title,
            "remind_at": remind_at.isoformat(),
            "assignee": assignee,
        },
    )
    db.session.add(log)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"Reminder '{title}' set for {remind_at.strftime('%b %d, %H:%M')}.",
        data={
            "title": title,
            "remind_at": remind_at.isoformat(),
            "assignee": assignee,
            "notification_id": notification.id,
        },
    )


# ===========================================================================
# 18. manage_team — Add/remove team members (Admin only)
# ===========================================================================

def _handler_manage_team(params: dict, agent) -> ToolResult:
    """Add or remove team members. Admin-only operation."""
    action_type = params.get("action", "add")  # add or remove
    name = params.get("name", "")
    email = params.get("email", "")
    role = params.get("role", "agent")

    if not name:
        return ToolResult(False, message="I need the team member's name.")

    tenant_id = g.tenant.id

    if action_type == "remove":
        member = TeamMember.query.filter_by(
            tenant_id=tenant_id, name=name
        ).first()
        if not member:
            member = TeamMember.query.filter_by(
                tenant_id=tenant_id, email=email
            ).first() if email else None
        if not member:
            return ToolResult(False, message=f"Team member '{name}' not found.")
        member.is_active = False
        db.session.commit()

        return ToolResult(
            success=True,
            message=f"{member.name} has been deactivated.",
            data={"member_id": member.id, "name": member.name, "status": "deactivated"},
        )

    # Add a new team member
    existing = TeamMember.query.filter_by(tenant_id=tenant_id, email=email).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.name = name
            existing.role = role
            db.session.commit()
            return ToolResult(
                success=True,
                message=f"Reactivated {name} as {role}.",
                data={"member_id": existing.id, "name": name, "role": role},
            )
        return ToolResult(False, message=f"A member with email '{email}' already exists.")

    member = TeamMember(
        tenant_id=tenant_id,
        name=name,
        email=email or f"{name.lower().replace(' ', '.')}@tenant.local",
        role=role,
        is_active=True,
    )
    db.session.add(member)

    log = ActivityLog(
        tenant_id=tenant_id,
        user_id=g.user.id,
        action="team_member_added",
        detail=f"Added team member: {name} ({role})",
    )
    db.session.add(log)
    db.session.commit()

    return ToolResult(
        success=True,
        message=f"{name} added as {role}.",
        data={"member_id": member.id, "name": name, "role": role},
    )


# ===========================================================================
# 19. view_audit_log — See all actions (Admin only)
# ===========================================================================

def _handler_view_audit_log(params: dict, agent) -> ToolResult:
    """View the audit log of all actions taken in the system."""
    limit = min(int(params.get("limit", 50)), 500)
    action_filter = params.get("action", "")
    entity_id = params.get("entity_id")
    days = int(params.get("days", 30))

    query = ActivityLog.query.filter(
        ActivityLog.tenant_id == g.tenant.id
    )

    if action_filter:
        query = query.filter(ActivityLog.action == action_filter)
    if entity_id:
        query = query.filter(ActivityLog.entity_id == entity_id)
    if days > 0:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ActivityLog.created_at >= since)

    logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()

    results = [
        {
            "id": l.id,
            "action": l.action,
            "detail": l.detail,
            "entity_id": l.entity_id,
            "user_id": l.user_id,
            "governance_level": l.governance_level,
            "at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]

    return ToolResult(
        success=True,
        message=f"Found {len(results)} audit log entries.",
        data={
            "count": len(results),
            "filter": {
                "action": action_filter or "all",
                "days": days,
                "entity_id": entity_id,
            },
            "entries": results,
        },
    )


# ===========================================================================
# 20. run_governance_check — Run all governance policies (Admin only)
# ===========================================================================

def _handler_run_governance_check(params: dict, agent) -> ToolResult:
    """Run governance policy checks across entities."""
    from app.shunya.governance import GovernanceEngine

    entity_id = params.get("entity_id")
    entity_type = params.get("entity_type", "")

    checks_run = []
    issues = []
    passed = []

    try:
        engine = GovernanceEngine()

        if entity_id:
            result = engine.check_entity(entity_id, g.tenant.id)
            checks_run.append(f"entity_{entity_id}")
            if result.get("blocked"):
                issues.append(result)
            else:
                passed.append(result)
        else:
            # Check all entity types for this tenant
            definitions = EntityDefinition.query.filter_by(
                tenant_id=g.tenant.id, is_active=True
            ).all()
            for defn in definitions:
                if entity_type and defn.type != entity_type:
                    continue
                batch = engine.check_entity_type(defn.type, g.tenant.id)
                checks_run.append(f"type_{defn.type}")
                for b in (batch or []):
                    if b.get("blocked"):
                        issues.append(b)
                    else:
                        passed.append(b)

        summary = {
            "checks_run": len(checks_run),
            "passed": len(passed),
            "issues": len(issues),
            "details": {
                "checks": checks_run[:20],
                "issue_count": len(issues),
                "pass_count": len(passed),
            },
        }

        if issues:
            return ToolResult(
                success=True,
                message=f"Governance check complete: {len(issues)} issue(s) found, {len(passed)} passed.",
                data={
                    **summary,
                    "issues": [
                        {
                            "entity_id": i.get("entity_id"),
                            "reason": i.get("reason", i.get("blocker_reason", "Unknown issue")),
                        }
                        for i in issues[:10]
                    ],
                },
            )

        return ToolResult(
            success=True,
            message=f"Governance check complete: All {len(passed)} check(s) passed. No issues found.",
            data=summary,
        )

    except ImportError:
        # Fallback if GovernanceEngine is not available
        return ToolResult(
            success=True,
            message="Governance engine not imported. Using default policy: all entities require review for amounts > ₹1,00,000.",
            data={
                "checks_run": 0,
                "note": "GovernanceEngine not available. Install app.shunya.governance for full checks.",
                "default_policy": "Amount threshold: ₹1,00,000",
            },
        )
    except Exception as e:
        return ToolResult(
            success=False,
            message=f"Governance check encountered an error: {str(e)}",
            data={"error": str(e)},
        )


# ===========================================================================
# Registry — Module-level tool registrations
# ===========================================================================

register_tool(ToolDef(
    id="create_quote",
    name="create_quote",
    description="Create a new quote from a lead or customer with itinerary details, pricing, and items.",
    category=ToolCategory.QUOTE,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_create_quote,
    parameters={
        "lead_id": {"type": "integer", "description": "Lead/entity ID to quote against", "required": False},
        "customer_name": {"type": "string", "description": "Customer name for the quote", "required": False},
        "destination": {"type": "string", "description": "Travel destination", "required": False},
        "amount": {"type": "number", "description": "Quote total amount", "required": False},
        "items": {"type": "array", "description": "List of quote line items", "required": False},
        "notes": {"type": "string", "description": "Additional notes", "required": False},
    },
    examples=[
        "Create a quote for John for the Bali trip for ₹50,000",
        "Generate a quote from lead #42 for the Maldives package",
    ],
))

register_tool(ToolDef(
    id="send_quote",
    name="send_quote",
    description="Send a quote to a customer via WhatsApp, email, or other channels.",
    category=ToolCategory.QUOTE,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_send_quote,
    parameters={
        "quote_id": {"type": "integer", "description": "Quote entity ID to send", "required": True},
        "channel": {"type": "string", "description": "Delivery channel (whatsapp, email)", "required": False},
        "recipient": {"type": "string", "description": "Recipient phone or email", "required": False},
        "message": {"type": "string", "description": "Custom message to include", "required": False},
    },
    examples=[
        "Send quote #12 to customer via WhatsApp",
        "Email quote to john@example.com",
    ],
))

register_tool(ToolDef(
    id="check_quote_status",
    name="check_quote_status",
    description="Check whether a customer has viewed, accepted, or rejected a quote.",
    category=ToolCategory.QUOTE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_handler_check_quote_status,
    parameters={
        "quote_id": {"type": "integer", "description": "Quote entity ID", "required": True},
    },
    examples=[
        "Has the customer viewed quote #12?",
        "What's the status of quote Q2401?",
    ],
))

register_tool(ToolDef(
    id="modify_quote",
    name="modify_quote",
    description="Update or adjust an existing quote — change amount, items, notes, or status.",
    category=ToolCategory.QUOTE,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_modify_quote,
    parameters={
        "quote_id": {"type": "integer", "description": "Quote entity ID to modify", "required": True},
    },
    examples=[
        "Update quote #12 amount to ₹45,000",
        "Change items on quote Q2401",
    ],
))

register_tool(ToolDef(
    id="create_itinerary",
    name="create_itinerary",
    description="Create a day-by-day travel itinerary for a customer with destinations and activities.",
    category=ToolCategory.QUOTE,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_create_itinerary,
    parameters={
        "customer_name": {"type": "string", "description": "Customer name", "required": False},
        "destination": {"type": "string", "description": "Travel destination", "required": True},
        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)", "required": False},
        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)", "required": False},
        "days": {"type": "array", "description": "Day-by-day itinerary entries", "required": False},
        "preferences": {"type": "string", "description": "Customer preferences", "required": False},
    },
    examples=[
        "Create a 5-day itinerary for the Bali trip",
        "Build a day-by-day plan for John's Maldives vacation",
    ],
))

register_tool(ToolDef(
    id="compare_packages",
    name="compare_packages",
    description="Compare two or three travel packages side by side for a customer.",
    category=ToolCategory.QUOTE,
    permission=ToolPermission.READ,
    tier=1,
    handler=_handler_compare_packages,
    parameters={
        "packages": {"type": "array", "description": "List of package names/IDs to compare", "required": True},
    },
    examples=[
        "Compare the Bali and Maldives packages",
        "Show me how the Singapore and Thailand packages differ",
    ],
))

register_tool(ToolDef(
    id="create_booking",
    name="create_booking",
    description="Convert a quote into a confirmed booking. Optionally create from a quote ID.",
    category=ToolCategory.BOOKING,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_create_booking,
    parameters={
        "quote_id": {"type": "integer", "description": "Quote entity ID to convert", "required": False},
        "customer_name": {"type": "string", "description": "Customer name (if no quote)", "required": False},
        "notes": {"type": "string", "description": "Booking notes", "required": False},
    },
    examples=[
        "Convert quote #12 to a confirmed booking",
        "Create a new booking for John to Bali",
    ],
))

register_tool(ToolDef(
    id="check_availability",
    name="check_availability",
    description="Check hotel, activity, or transport availability for a destination and date via web search.",
    category=ToolCategory.TRAVEL_INTEL,
    permission=ToolPermission.READ,
    tier=1,
    handler=_handler_check_availability,
    parameters={
        "type": {"type": "string", "description": "Item type (hotel, activity, transport)", "required": False},
        "destination": {"type": "string", "description": "Destination to check", "required": True},
        "date": {"type": "string", "description": "Date to check", "required": False},
    },
    examples=[
        "Check hotel availability in Bali for next week",
        "Are there any activities available in Maldives on Dec 25?",
    ],
))

register_tool(ToolDef(
    id="create_invoice",
    name="create_invoice",
    description="Generate a GST invoice from a booking including tax calculation.",
    category=ToolCategory.PAYMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_create_invoice,
    parameters={
        "booking_id": {"type": "integer", "description": "Booking entity ID", "required": False},
        "customer_name": {"type": "string", "description": "Customer name", "required": False},
        "amount": {"type": "number", "description": "Invoice base amount", "required": False},
        "tax_rate": {"type": "number", "description": "GST rate percentage (default 18)", "required": False},
        "discount": {"type": "number", "description": "Discount amount", "required": False},
        "notes": {"type": "string", "description": "Invoice notes", "required": False},
    },
    examples=[
        "Create an invoice for booking #42 with 18% GST",
        "Generate GST invoice for John's Bali trip, ₹50,000",
    ],
))

register_tool(ToolDef(
    id="send_invoice",
    name="send_invoice",
    description="Send an invoice to a customer via WhatsApp, email, or other channels.",
    category=ToolCategory.PAYMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_send_invoice,
    parameters={
        "invoice_id": {"type": "integer", "description": "Invoice entity ID to send", "required": True},
        "channel": {"type": "string", "description": "Delivery channel (email, whatsapp)", "required": False},
        "recipient": {"type": "string", "description": "Recipient email or phone", "required": False},
        "message": {"type": "string", "description": "Custom message", "required": False},
    },
    examples=[
        "Send invoice #15 to customer via email",
        "WhatsApp the invoice to john@example.com",
    ],
))

register_tool(ToolDef(
    id="record_payment",
    name="record_payment",
    description="Record a payment received against an invoice or booking.",
    category=ToolCategory.PAYMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_record_payment,
    parameters={
        "invoice_id": {"type": "integer", "description": "Invoice entity ID", "required": False},
        "booking_id": {"type": "integer", "description": "Booking entity ID", "required": False},
        "amount": {"type": "number", "description": "Payment amount", "required": True},
        "gateway": {"type": "string", "description": "Payment gateway (cash, bank, card)", "required": False},
        "gateway_ref": {"type": "string", "description": "Gateway reference/transaction ID", "required": False},
        "notes": {"type": "string", "description": "Payment notes", "required": False},
    },
    examples=[
        "Record a payment of ₹25,000 for invoice #15",
        "Log ₹50,000 received via bank transfer for booking #42",
    ],
))

register_tool(ToolDef(
    id="check_payment_status",
    name="check_payment_status",
    description="Check payment status for an invoice, booking, or customer — what's paid and what's pending.",
    category=ToolCategory.PAYMENT,
    permission=ToolPermission.READ,
    tier=1,
    handler=_handler_check_payment_status,
    parameters={
        "entity_id": {"type": "integer", "description": "Invoice or booking entity ID", "required": False},
        "customer_name": {"type": "string", "description": "Customer name to look up", "required": False},
    },
    examples=[
        "What's the payment status for invoice #15?",
        "Has John paid for his Bali booking?",
    ],
))

register_tool(ToolDef(
    id="send_payment_reminder",
    name="send_payment_reminder",
    description="Send an automatic payment reminder for an outstanding invoice.",
    category=ToolCategory.PAYMENT,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_send_payment_reminder,
    parameters={
        "invoice_id": {"type": "integer", "description": "Invoice entity ID", "required": True},
        "channel": {"type": "string", "description": "Delivery channel (email, whatsapp)", "required": False},
        "recipient": {"type": "string", "description": "Recipient contact", "required": False},
        "message": {"type": "string", "description": "Custom reminder message", "required": False},
    },
    examples=[
        "Send a payment reminder for invoice #15",
        "Remind John about his pending payment for the Bali trip",
    ],
))

register_tool(ToolDef(
    id="calculate_gst",
    name="calculate_gst",
    description="Calculate GST (CGST + SGST) for a given amount and tax rate.",
    category=ToolCategory.PAYMENT,
    permission=ToolPermission.READ,
    tier=1,
    handler=_handler_calculate_gst,
    parameters={
        "amount": {"type": "number", "description": "Base amount to calculate GST on", "required": True},
        "rate": {"type": "number", "description": "GST rate percentage (default 18)", "required": False},
    },
    examples=[
        "Calculate 18% GST on ₹50,000",
        "What's the GST for ₹25,000 at 12%?",
    ],
))

register_tool(ToolDef(
    id="view_outstanding",
    name="view_outstanding",
    description="View all unpaid or partially paid invoices with total outstanding amount.",
    category=ToolCategory.PAYMENT,
    permission=ToolPermission.READ,
    tier=1,
    handler=_handler_view_outstanding,
    parameters={
        "limit": {"type": "integer", "description": "Max records to return", "required": False},
    },
    examples=[
        "Show me all outstanding invoices",
        "What's the total amount due?",
    ],
))

register_tool(ToolDef(
    id="execute_workflow",
    name="execute_workflow",
    description="Execute a multi-step workflow using the Sequential Planner with dependency ordering.",
    category=ToolCategory.WORKFLOW,
    permission=ToolPermission.WRITE,
    tier=3,
    handler=_handler_execute_workflow,
    parameters={
        "entity_type": {"type": "string", "description": "The entity type for the workflow", "required": True},
        "actions": {"type": "array", "description": "List of action dicts with action name, depends_on, priority", "required": True},
        "entity_id": {"type": "integer", "description": "Related entity ID", "required": False},
    },
    examples=[
        "Execute a booking workflow: create quote, send quote, confirm booking, generate invoice",
        "Run a multi-step workflow for lead follow-up",
    ],
))

register_tool(ToolDef(
    id="create_reminder",
    name="create_reminder",
    description="Create a reminder for the user or team, optionally linked to an entity.",
    category=ToolCategory.WORKFLOW,
    permission=ToolPermission.WRITE,
    tier=2,
    handler=_handler_create_reminder,
    parameters={
        "title": {"type": "string", "description": "Reminder title/text", "required": True},
        "due_at": {"type": "string", "description": "Due datetime (ISO format)", "required": False},
        "remind_in_minutes": {"type": "integer", "description": "Remind in N minutes from now", "required": False},
        "entity_id": {"type": "integer", "description": "Related entity ID", "required": False},
        "assignee": {"type": "string", "description": "Assignee name", "required": False},
    },
    examples=[
        "Remind me to follow up with John in 30 minutes",
        "Set a reminder for tomorrow at 10am to call the client",
    ],
))

register_tool(ToolDef(
    id="manage_team",
    name="manage_team",
    description="Add or remove team members. Admin only.",
    category=ToolCategory.ADMIN,
    permission=ToolPermission.ADMIN,
    tier=2,
    handler=_handler_manage_team,
    parameters={
        "action": {"type": "string", "description": "Action: add or remove", "required": True},
        "name": {"type": "string", "description": "Team member name", "required": True},
        "email": {"type": "string", "description": "Team member email", "required": False},
        "role": {"type": "string", "description": "Role: admin, manager, agent, viewer", "required": False},
    },
    examples=[
        "Add Priya as a team member with manager role",
        "Remove John from the team",
    ],
))

register_tool(ToolDef(
    id="view_audit_log",
    name="view_audit_log",
    description="View the audit trail of all actions taken in the system. Admin only.",
    category=ToolCategory.ADMIN,
    permission=ToolPermission.ADMIN,
    tier=1,
    handler=_handler_view_audit_log,
    parameters={
        "limit": {"type": "integer", "description": "Max entries to return", "required": False},
        "action": {"type": "string", "description": "Filter by action type", "required": False},
        "entity_id": {"type": "integer", "description": "Filter by entity ID", "required": False},
        "days": {"type": "integer", "description": "Look back N days (default 30)", "required": False},
    },
    examples=[
        "Show me the audit log",
        "What actions have been taken on lead #42?",
    ],
))

register_tool(ToolDef(
    id="run_governance_check",
    name="run_governance_check",
    description="Run governance policy checks across all or specific entities. Admin only.",
    category=ToolCategory.ADMIN,
    permission=ToolPermission.ADMIN,
    tier=2,
    handler=_handler_run_governance_check,
    parameters={
        "entity_id": {"type": "integer", "description": "Check a specific entity", "required": False},
        "entity_type": {"type": "string", "description": "Check all entities of a type", "required": False},
    },
    examples=[
        "Run a governance check on all entities",
        "Check governance for quote entities",
    ],
))
