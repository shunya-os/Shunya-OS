"""
Panchi Club Travel OS — Routing & API (Unit 3)

Dashboard CRUD + Telegram webhook + Shunya API + activity logging.
All mutating operations log to ActivityLog for audit trail.
"""

import os
import pdfkit
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, g
from app import db
from app.models import (
    Lead, Payment, Supplier, Invoice, ItineraryRef,
    LeadStatus, PaymentType, InvoiceStatus, next_inquiry_code,
)
from app.services import parse_inquiry_text, get_summary, _cached_or_new_code, format_inquiry_reply

main = Blueprint("main", __name__)
api = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _flash_if_error(obj, success_msg="Saved successfully"):
    """Add obj to session, commit, flash. Returns obj or None on error."""
    try:
        db.session.add(obj)
        db.session.commit()
        flash(success_msg, "success")
        return obj
    except Exception as e:
        db.session.rollback()
        flash(str(e), "error")
        return None


def _log_activity(lead_id: int, action: str, detail: str = ""):
    """Create an ActivityLog entry for a lead."""
    from app.models import ActivityLog
    log = ActivityLog(
        lead_id=lead_id,
        action=action,
        detail=detail[:500],
        user=getattr(g, "user", ""),
    )
    db.session.add(log)
    db.session.commit()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@main.route("/")
def index():
    s = get_summary("today")
    recent = Lead.query.order_by(Lead.created_at.desc()).limit(8).all()
    return render_template("dashboard.html", summary=s, recent=recent)


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

@main.route("/leads")
def leads_list():
    q = request.args.get("q", "")
    query = Lead.query
    if q:
        query = query.filter(
            Lead.code.contains(q)
            | Lead.destination.contains(q)
            | Lead.customer_name.contains(q)
            | Lead.phone.contains(q)
        )
    leads = query.order_by(Lead.created_at.desc()).limit(200).all()
    return render_template("leads.html", leads=leads, q=q)


@main.route("/leads/new", methods=["GET", "POST"])
def lead_new():
    if request.method == "POST":
        f = request.form
        with db.session.no_autoflush:
            code = _cached_or_new_code(db.session)
        lead = Lead(
            code=code,
            source=f.get("source", "telegram"),
            customer_name=f.get("customer_name"),
            phone=f.get("phone"),
            email=f.get("email"),
            destination=f.get("destination"),
            pax=f.get("pax"),
            dates=f.get("dates"),
            budget=float(f.get("budget") or 0),
            assigned_to=f.get("assigned_to"),
            notes=f.get("notes"),
            status=f.get("status", "new"),
        )
        obj = _flash_if_error(lead)
        if obj:
            _log_activity(obj.id, "created", f"Lead created via {obj.source}")
        return redirect(url_for("main.leads_list"))
    code = _cached_or_new_code(db.session)
    return render_template("lead_form.html", code=code)


@main.route("/leads/<int:lead_id>")
def lead_detail(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    activities = lead.activities.order_by(Lead.activities.property.mapper.class_.created_at.desc()).limit(50).all()

    # AI Coach insights
    from app.coach import CoachEngine
    coach = CoachEngine()
    coach_insights = coach.get_insights({
        "action": "lead_view",
        "customer": {
            "budget": str(lead.budget or 0),
            "first_time_traveler": not bool(lead.destination and lead.destination.strip()),
            "has_children": "kids" in (lead.pax or "").lower() or "child" in (lead.pax or "").lower(),
        }
    }, skill_level="new")

    # Dynamic field values
    try:
        from app.dynamic_fields import DynamicFieldManager
        dyn_fields = DynamicFieldManager.get_fields("lead")
        dyn_values = DynamicFieldManager.get_values(lead_id, entity="lead")
    except Exception:
        dyn_fields = []
        dyn_values = {}

    return render_template("lead_detail.html", lead=lead, activities=activities,
                           coach_insights=coach_insights, dyn_fields=dyn_fields, dyn_values=dyn_values)


@main.route("/leads/<int:lead_id>/status", methods=["POST"])
def lead_update_status(lead_id):
    """Update lead status and log the change."""
    lead = Lead.query.get_or_404(lead_id)
    new_status = request.form.get("status") or request.get_json(silent=True).get("status", "")
    if new_status and new_status in [s.value for s in LeadStatus]:
        old = lead.status
        lead.status = new_status
        db.session.commit()
        _log_activity(lead_id, "status_changed", f"{old} → {new_status}")
        flash(f"Status updated: {new_status}", "success")
    else:
        flash(f"Invalid status: {new_status}", "error")
    return redirect(url_for("main.lead_detail", lead_id=lead_id))


@main.route("/leads/<int:lead_id>/edit", methods=["GET", "POST"])
def lead_edit(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if request.method == "POST":
        f = request.form
        for attr in ("customer_name", "phone", "email", "destination", "pax",
                     "dates", "notes", "source", "assigned_to"):
            val = f.get(attr)
            if val is not None:
                setattr(lead, attr, val)
        if f.get("budget"):
            lead.budget = float(f["budget"])
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        _log_activity(lead_id, "updated", "Lead details updated")
        flash("Lead updated", "success")
        return redirect(url_for("main.lead_detail", lead_id=lead_id))
    return render_template("lead_form.html", lead=lead, editing=True)


@main.route("/leads/<int:lead_id>/delete", methods=["POST"])
def lead_delete(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    flash("Lead deleted", "success")
    return redirect(url_for("main.leads_list"))


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@main.route("/payments", methods=["GET", "POST"])
def payments():
    if request.method == "POST":
        f = request.form
        p = Payment(
            lead_id=int(f["lead_id"]) if f.get("lead_id") else None,
            type=f.get("type", "guest_payment"),
            amount=float(f.get("amount") or 0),
            method=f.get("method"),
            ref_number=f.get("ref_number"),
            notes=f.get("notes"),
        )
        obj = _flash_if_error(p)
        if obj and obj.lead_id:
            type_label = "Guest payment" if p.type == "guest_payment" else "Supplier payment"
            _log_activity(obj.lead_id, "payment_received", f"{type_label}: ₹{p.amount:.0f}")
        return redirect(url_for("main.payments"))
    payments = Payment.query.order_by(Payment.paid_at.desc()).limit(200).all()
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(300).all()
    return render_template("payments.html", payments=payments, leads=leads)


@main.route("/payments/<int:payment_id>/delete", methods=["POST"])
def payment_delete(payment_id):
    p = Payment.query.get_or_404(payment_id)
    lead_id = p.lead_id
    db.session.delete(p)
    db.session.commit()
    if lead_id:
        _log_activity(lead_id, "payment_removed", f"{p.type}: ₹{p.amount:.0f}")
    flash("Payment deleted", "success")
    return redirect(url_for("main.payments"))


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

@main.route("/invoices", methods=["GET", "POST"])
def invoices():
    if request.method == "POST":
        f = request.form
        total = float(f.get("total_amount") or 0)
        tax = float(f.get("tax") or 0)
        discount = float(f.get("discount") or 0)
        grand_total = total + tax - discount
        inv = Invoice(
            lead_id=int(f.get("lead_id")) if f.get("lead_id") else None,
            invoice_number=f.get("invoice_number"),
            total_amount=total,
            tax=tax,
            tax_rate=float(f.get("tax_rate") or 0),
            discount=discount,
            grand_total=grand_total,
            status=f.get("status", "draft"),
            currency=f.get("currency", "INR"),
        )
        try:
            due = f.get("due_date")
            if due:
                inv.due_date = datetime.strptime(due, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass
        db.session.add(inv)
        db.session.commit()
        try:
            os.makedirs("invoices", exist_ok=True)
            inv.pdf_path = os.path.join("invoices", f"{inv.id}_{inv.invoice_number}.pdf")
            _generate_invoice_pdf(inv.id, inv.pdf_path)
            db.session.commit()
            flash(f"Invoice {inv.invoice_number} created with PDF", "success")
        except Exception as e:
            flash(f"Invoice saved but PDF failed: {e}", "error")
        if inv.lead_id:
            _log_activity(inv.lead_id, "invoice_created",
                          f"Inv #{inv.invoice_number} ₹{inv.grand_total:.0f}")
        return redirect(url_for("main.invoices"))
    invoices = Invoice.query.order_by(Invoice.raised_at.desc()).limit(200).all()
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(300).all()
    return render_template("invoices.html", invoices=invoices, leads=leads)


@main.route("/invoices/<int:invoice_id>/pdf")
def invoice_pdf(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    if not inv.pdf_path or not os.path.exists(inv.pdf_path):
        try:
            os.makedirs("invoices", exist_ok=True)
            inv.pdf_path = os.path.join("invoices", f"{inv.id}_{inv.invoice_number}.pdf")
            _generate_invoice_pdf(inv.id, inv.pdf_path)
            db.session.commit()
        except Exception as e:
            flash(f"PDF generation failed: {e}", "error")
            return redirect(url_for("main.invoices"))
    return send_from_directory(
        os.path.dirname(os.path.abspath(inv.pdf_path)),
        os.path.basename(inv.pdf_path),
        as_attachment=True,
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@main.route("/reports")
def reports():
    from sqlalchemy import func, extract
    current_year = datetime.utcnow().year

    # Destination counts
    dest_counts = (
        db.session.query(Lead.destination, func.count(Lead.id))
        .filter(Lead.destination != None, Lead.destination != "")
        .group_by(Lead.destination)
        .order_by(func.count(Lead.id).desc())
        .limit(15)
        .all()
    )

    return render_template("reports.html", dest_counts=dest_counts, year=current_year)


# ---------------------------------------------------------------------------
# Settings / Suppliers
# ---------------------------------------------------------------------------

@main.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        f = request.form
        s = Supplier(
            name=f["name"],
            category=f.get("category"),
            contact=f.get("contact"),
            email=f.get("email"),
            phone=f.get("phone"),
            city=f.get("city"),
            gstin=f.get("gstin"),
            payment_terms=f.get("payment_terms"),
            notes=f.get("notes"),
        )
        _flash_if_error(s)
        return redirect(url_for("main.settings"))
    suppliers = Supplier.query.order_by(Supplier.created_at.desc()).limit(200).all()
    return render_template("settings.html", suppliers=suppliers)


@main.route("/settings/fields/add", methods=["POST"])
def settings_fields_add():
    """Superadmin: create a custom dynamic field."""
    from app.dynamic_fields import DynamicFieldManager
    f = request.form
    field_name = f.get("field_name", "").strip()
    field_label = f.get("field_label", "").strip()
    entity = f.get("entity", "lead")
    field_type = f.get("field_type", "text")
    options_raw = f.get("options", "")
    options = [o.strip() for o in options_raw.split("\n") if o.strip()] if options_raw else None
    searchable = f.get("searchable") == "1"
    try:
        DynamicFieldManager.create_field(
            entity=entity, field_name=field_name, field_label=field_label,
            field_type=field_type, options=options, searchable=searchable,
        )
        flash(f"Field '{field_label}' created for {entity}", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.settings"))


# ---------------------------------------------------------------------------
# Telegram webhook & Bot endpoints
# ---------------------------------------------------------------------------

@main.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    from app.services import parse_inquiry_text

    payload = request.get_json(silent=True) or {}
    message = payload.get("message") or {}
    text = str(message.get("text") or payload.get("text") or "")
    chat = message.get("chat") or payload.get("chat") or {}
    sender = str(chat.get("id") or payload.get("from", {}).get("id") or "")

    if not text:
        return jsonify({"status": "ignored"}), 200

    parsed = parse_inquiry_text(text)
    with db.session.no_autoflush:
        code = _cached_or_new_code(db.session)
    lead = Lead(
        code=code,
        source="telegram",
        customer_name=parsed.get("name") or sender,
        phone=sender,
        destination=parsed.get("destination"),
        pax=(
            f"{parsed.get('adults') or 0} adults, {parsed.get('kids') or 0} kids"
            if parsed.get("adults") or parsed.get("kids")
            else None
        ),
        dates=parsed.get("dates"),
        notes=text,
        status="new",
    )
    db.session.add(lead)
    db.session.commit()
    _log_activity(lead.id, "created", f"Lead created via Telegram inquiry: {text[:200]}")

    reply = {
        "method": "sendMessage",
        "chat_id": sender,
        "text": format_inquiry_reply(parsed, code),
    }
    return jsonify(reply), 200


@main.route("/telegram/setup", methods=["POST"])
def telegram_setup():
    from app.services import save_telegram_token
    token = request.form.get("bot_token")
    if not token:
        flash("Bot token required", "error")
        return redirect(url_for("main.settings"))
    try:
        save_telegram_token(token)
        flash("Telegram bot token saved. Use /telegram/setwebhook to register.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("main.settings"))


@main.route("/telegram/setwebhook", methods=["POST"])
def telegram_setwebhook():
    from app.services import get_telegram_token, set_telegram_webhook
    token = get_telegram_token()
    if not token:
        flash("No Telegram bot token configured. Save it in Settings first.", "error")
        return redirect(url_for("main.settings"))
    host = request.host_url.rstrip("/")
    url = f"{host}/telegram/webhook"
    ok, data = set_telegram_webhook(token, url)
    if ok:
        flash(f"Telegram webhook set: {url}", "success")
    else:
        flash(f"Webhook setup failed: {data}", "error")
    return redirect(url_for("main.settings"))


# ---------------------------------------------------------------------------
# Shunya Pipeline API
# ---------------------------------------------------------------------------

@api.route("/shunya/process", methods=["POST"])
def shunya_process():
    data = request.get_json(silent=True) or {}
    fmt = data.get("format", "text")
    inquiry = {
        "customer_name": data.get("customer_name", ""),
        "destination": data.get("destination", ""),
        "pax": data.get("pax", ""),
        "dates": data.get("dates", ""),
        "notes": data.get("notes", ""),
        "phone": data.get("phone", ""),
        "source": data.get("source", "api"),
    }
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    result = wf.process_inquiry(inquiry, fmt=fmt)
    if result.success() and data.get("create_lead"):
        lead_id = wf.create_lead_from_inquiry(inquiry)
        if lead_id:
            _log_activity(lead_id, "created", "Lead created via Shunya API")
        result.lead_id = lead_id
    resp = result.to_dict()
    if fmt in ("html", "all"):
        resp["proposal_html"] = result.proposal_html
    return jsonify(resp)


@api.route("/shunya/knowledge", methods=["GET"])
def shunya_knowledge():
    from app.shunya import KnowledgeLayer
    k = KnowledgeLayer(db.session)
    return jsonify({
        "knowledge_base_length": len(k.get_knowledge_base_text()),
        "past_itineraries": k.get_past_itineraries(limit=5),
    })


@api.route("/shunya/summary", methods=["GET"])
def shunya_summary():
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    return jsonify(wf.get_lead_status_summary(db.session))


@api.route("/shunya/proposal/<int:lead_id>", methods=["GET"])
def shunya_proposal(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    fmt = request.args.get("format", "text")
    inquiry = {
        "customer_name": lead.customer_name or "",
        "destination": lead.destination or "",
        "pax": lead.pax or "",
        "dates": lead.dates or "",
        "notes": lead.notes or "",
        "phone": lead.phone or "",
    }
    from app.shunya import WorkflowLayer
    wf = WorkflowLayer(db.session)
    result = wf.process_inquiry(inquiry, fmt=fmt)
    if result.success():
        _log_activity(lead_id, "proposal_sent",
                      f"Proposal generated ({fmt}, {result.plan.days[0].day_num if result.plan else 3}d itinerary)")
        resp = {
            "lead_code": lead.code,
            "format": fmt,
            "proposal": result.proposal_text,
            "itinerary": result.plan.to_dict() if result.plan else None,
        }
        if fmt in ("html", "all"):
            resp["proposal_html"] = result.proposal_html
        return jsonify(resp)
    return jsonify({"error": result.errors}), 400


# ---------------------------------------------------------------------------
# API: Activity log lookup
# ---------------------------------------------------------------------------

@api.route("/leads/<int:lead_id>/activities", methods=["GET"])
def api_lead_activities(lead_id):
    """Return activity log for a lead as JSON."""
    lead = Lead.query.get_or_404(lead_id)
    limit = min(int(request.args.get("limit", 50)), 200)
    activities = (
        lead.activities
        .order_by(Lead.activities.property.mapper.class_.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify([a.to_dict() for a in activities])


# ---------------------------------------------------------------------------
# PDF Generation (inline helper)
# ---------------------------------------------------------------------------

def _generate_invoice_pdf(invoice_id, path):
    inv = Invoice.query.get(invoice_id)
    lead = inv.lead
    due_str = inv.due_date.strftime("%d-%m-%Y") if inv.due_date else ""
    paid_str = inv.paid_at.strftime("%d-%m-%Y") if inv.paid_at else ""
    due_html = f"<p>Due: {due_str}</p>" if due_str else ""
    paid_html = f"<p>Paid: {paid_str}</p>" if paid_str else ""
    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
      body{{font-family:Arial,sans-serif;color:#111;padding:40px}}
      h1{{color:#2563eb;border-bottom:2px solid #2563eb;padding-bottom:8px}}
      table{{width:100%;border-collapse:collapse;margin:16px 0}}
      td,th{{border:1px solid #e5e7eb;padding:10px 8px;text-align:left}}
      th{{background:#f9fafb}}
      .grand{{font-size:18px}}
      .meta{{color:#6b7280;font-size:14px}}
    </style></head><body>
      <h1>Invoice {inv.invoice_number}</h1>
      <p class="meta">Raised: {inv.raised_at.strftime('%d-%m-%Y %H:%M')} · Status: {inv.status} · Currency: {inv.currency}</p>
      <h3>Customer</h3>
      <p>{lead.customer_name if lead else '-'}<br>{lead.email or ''}<br>{lead.phone or ''}<br>{lead.destination or ''}</p>
      <h3>Amounts</h3>
      <table>
        <tr><th>Total</th><td>₹{inv.total_amount:.2f}</td></tr>
        <tr><th>Tax ({inv.tax_rate:.1f}%)</th><td>₹{inv.tax:.2f}</td></tr>
        <tr><th>Discount</th><td>₹{inv.discount:.2f}</td></tr>
        <tr class="grand"><th><strong>Grand Total</strong></th><td><strong>₹{inv.grand_total:.2f}</strong></td></tr>
      </table>
      {due_html}
      {paid_html}
    </body></html>"""
    pdfkit.from_string(html, path)