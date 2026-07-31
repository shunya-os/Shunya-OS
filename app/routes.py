"""
SHUNYA OS — Routing & API

Dashboard CRUD + Telegram webhook + Shunya API + activity logging.
All mutating operations log to ActivityLog for audit trail.
"""

import os
import pdfkit
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, g
from app import db
from app.models import (
    Lead, Payment, Supplier, Invoice, ItineraryRef, TaskList, Task, Document,
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
# SPA helper
# ---------------------------------------------------------------------------

_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


def _serve_spa_shell():
    """Serve the built React SPA shell at /frontend/dist/index.html.

    Use this for every route where the SPA should handle rendering,
    including root, auth paths, and any client-side-routed path.
    """
    idx = os.path.join(_FRONTEND_DIST, "index.html")
    if os.path.exists(idx):
        return send_from_directory(_FRONTEND_DIST, "index.html")
    return "Frontend not built. Run `cd frontend && npm run build`", 503


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@main.route("/")
def index():
    # Serve the built React SPA for all visitors — the SPA handles auth,
    # routing, and workspace rendering entirely client-side.
    return _serve_spa_shell()


# Auth SPA shell routes — these paths exist so the Flask router doesn't
# 404 when the React SPA handles client-side routing for auth pages.
# The SPA itself renders login/register content via React Router.
@main.route("/auth/login")
@main.route("/auth/")
@main.route("/auth")
@main.route("/auth/register")
@main.route("/auth/signup")
@main.route("/auth/forgot-password")
@main.route("/auth/reset-password")
@main.route("/auth/invitation")
@main.route("/auth/verify-email")
def auth_spa_shell():
    return _serve_spa_shell()

    s = get_summary("today")
    recent = Lead.query.order_by(Lead.created_at.desc()).limit(8).all()
    # Companion greeting
    companion_greeting = "Hey! Ready to make today productive? 🚀"
    ai_insight = "Your team is active. Your pipeline is moving. Let's make today count."
    ai_tip = "Your team's conversion rate improves when leads get first response within 5 minutes. Consider assigning a dedicated intake agent."
    companion_suggestions_data = [
        {"icon": "📋", "text": "Review pending leads", "action": "/leads"},
        {"icon": "💰", "text": "Check payments", "action": "/payments"},
        {"icon": "📊", "text": "View reports", "action": "/reports"},
    ]
    try:
        from app.companion import CompanionEngine
        c = CompanionEngine()
        if g.user:
            companion_greeting = c.greet(g.user.name).get("text", companion_greeting)
            companion_suggestions_data = c.companion_suggestions(role=g.user.role)
    except Exception:
        pass
    from app.models import ActivityLog
    activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # Business-type adaptive data
    from app.ontology import registry
    business_type = "travel"  # Tenant-configured
    ontology = registry.get(business_type)
    lead_counts = {"new": 0, "active": 0, "won": 0}
    for l in recent:
        status = l.status or "new"
        if status in ("new", "inquiry", "application"): lead_counts["new"] += 1
        elif status in ("in_progress", "proposal", "negotiation", "active", "enrolled"): lead_counts["active"] += 1
        elif status in ("converted", "booked", "completed", "graduated", "won"): lead_counts["won"] += 1
    quick_actions = [{"icon": m.icon, "label": m.label, "route": m.route} for m in ontology.modules if m.enabled][:4]
    
    return render_template("dashboard.html", summary=s, recent=recent,
                           greeting={
                               "greeting": companion_greeting,
                               "message": ai_insight,
                               "suggestions": companion_suggestions_data,
                               "reasoning_trace": None,
                           },
                           ai_insight=ai_insight, ai_tip=ai_tip,
                           journey={
                               "stages": [
                                   {"stage": type("obj", (), {"value": "lead"}), "count": len(recent), "next_entity_type": "lead", "next_action": "Create Quote"},
                                   {"stage": type("obj", (), {"value": "quote"}), "count": 0, "next_entity_type": "lead", "next_action": "Create Booking"},
                                   {"stage": type("obj", (), {"value": "booking"}), "count": 0, "next_entity_type": "booking", "next_action": "Start Trip"},
                                   {"stage": type("obj", (), {"value": "payment"}), "count": 0, "next_entity_type": "payment", "next_action": "Record Payment"},
                                   {"stage": type("obj", (), {"value": "trip"}), "count": 0, "next_entity_type": "trip", "next_action": "Collect Feedback"},
                                   {"stage": type("obj", (), {"value": "feedback"}), "count": 0, "next_entity_type": "feedback", "next_action": "Retention"},
                                   {"stage": type("obj", (), {"value": "retention"}), "count": 0, "next_entity_type": "feedback", "next_action": "Campaign"},
                               ],
                               "current_focus": "conversion" if lead_counts.get("new", 0) > 0 else None,
                               "total_active": lead_counts.get("new", 0),
                           },
                           vertical_metrics=[],
                           def_counts={"lead": {"icon": "📋", "label": "Leads", "count": len(recent)}},
                           next_actions=[],
                           recent_activities=activities,
                           tenant=None,
                           companion_suggestions=companion_suggestions_data,
                           activities=activities, ontology=ontology,
                           lead_counts=lead_counts, quick_actions=quick_actions,
                           recent_items=[{"name": l.customer_name, "detail": l.destination, "date": l.created_at.strftime('%d %b') if l.created_at else ''} for l in recent],)


@main.route("/welcome")
def welcome():
    """Welcome screen with logo, greeting, voice."""
    from app.companion import CompanionEngine
    c = CompanionEngine()
    employee_name = g.user.name if hasattr(g, "user") and g.user else "there"
    welcome_data = c.greet(employee_name)
    stats = [
        {"value": "4", "label": "Today's Leads"},
        {"value": "₹45K", "label": "Revenue"},
        {"value": "6", "label": "Team Online"},
    ]
    return render_template("welcome.html",
        greeting=welcome_data["text"],
        message="Your team is ready. Your pipeline is active. Let's make today count.",
        voice_text=welcome_data["voice_text"],
        stats=stats,
        company_name="SHUNYA",
        company_emoji="🏝️",
        bg_color="#0f172a",
        sidebar_bg="#1e293b",
        primary_color="#2563eb",
        accent_color="#7c3aed",
        logo_style="circle",
        logo_path="",
        cta_text="Start Your Day",
    )


# ---------------------------------------------------------------------------
# Calendar View
# ---------------------------------------------------------------------------


@main.route("/calendar")
def calendar_view():
    """Full-page calendar view showing trips, tasks, and events."""
    return render_template("calendar.html")


@api.route("/calendar/events")
def calendar_events():
    """JSON feed of events for the calendar. Requires start= and end= params."""
    from datetime import date as dt_date
    start_str = request.args.get("start", "")
    end_str = request.args.get("end", "")
    import datetime
    try:
        start = datetime.date.fromisoformat(start_str) if start_str else dt_date.today().replace(day=1)
        end = datetime.date.fromisoformat(end_str) if end_str else dt_date.today()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    from app.calendar_service import CalendarService
    svc = CalendarService()
    events = svc.get_events(start, end)
    return jsonify(events)


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
    # Check if pipeline view is requested
    if request.args.get("view") == "pipeline":
        from collections import defaultdict
        pipeline_counts = defaultdict(int)
        for l in leads:
            pipeline_counts[l.status or "new"] += 1
        pipeline_total = sum(l.budget or 0 for l in leads)
        return render_template("pipeline.html", leads=leads,
                               pipeline_counts=dict(pipeline_counts),
                               pipeline_total={"value": f"₹{pipeline_total:,.0f}"})
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
    return render_template("lead_form.html", code=code, lead=None)


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
    json_data = request.get_json(silent=True)
    if json_data:
        new_status = json_data.get("status", "")
    else:
        new_status = request.form.get("status", "")

    if new_status and new_status in [s.value for s in LeadStatus]:
        old = lead.status
        lead.status = new_status
        db.session.commit()
        _log_activity(lead_id, "status_changed", f"{old} → {new_status}")

        # Auto-celebrate on lead conversion
        if new_status == LeadStatus.CONVERTED.value and old != LeadStatus.CONVERTED.value:
            try:
                from app.celebrations import CelebrationEngine
                ce = CelebrationEngine()
                celeb = ce.celebrate_lead_conversion(lead_id, user=getattr(g, "user", ""))
            except Exception:
                pass

        # Return JSON for API calls (kanban drag-drop), redirect for form posts
        if json_data:
            return jsonify({"success": True, "status": new_status})
        flash(f"Status updated: {new_status}", "success")
    else:
        if json_data:
            return jsonify({"success": False, "error": f"Invalid status: {new_status}"}), 400
        flash(f"Invalid status: {new_status}", "error")
    return redirect(url_for("main.lead_detail", lead_id=lead_id))


# API endpoint for kanban drag-and-drop
@api.route("/leads/<int:lead_id>/status", methods=["POST"])
def api_lead_status(lead_id):
    return lead_update_status(lead_id)


# Creative AI — generate content on demand
@api.route("/creative/generate", methods=["POST"])
def creative_generate():
    """Generate a creative asset from user input."""
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "")
    created_by = data.get("created_by", "AI Assistant")

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    from app.creative import CreativeEngine
    engine = CreativeEngine()

    intent = engine.understand_intent(user_input)
    copy_text = engine.generate_copy(intent)

    # Try to generate an image
    image_path = ""
    image_url = ""
    try:
        from hermes_tools import terminal
        result = terminal(f"Generate image for: {intent['topic']}")
        if result and result.get("output"):
            image_url = result["output"].strip()
    except Exception:
        pass

    asset = engine.save_asset(intent, copy_text, image_path=image_path,
                               image_url=image_url, created_by=created_by)
    response = engine.preview_response(asset)
    return jsonify(response)


@api.route("/creative/<int:asset_id>/approve", methods=["POST"])
def creative_approve(asset_id):
    """Approve a creative asset (mark as ready to post)."""
    from app.creative import CreativeAsset
    asset = db.session.get(CreativeAsset, asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
    asset.status = "approved"
    asset.approved_by = g.user.name if hasattr(g, "user") and g.user else "admin"
    db.session.commit()
    return jsonify({"success": True, "message": f"✅ '{asset.title}' approved! Ready to post on {asset.platform}."})


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


@main.route("/itineraries")
def itinerary_builder():
    """Itinerary builder — create, edit, share travel plans."""
    lead_id = request.args.get("lead_id", type=int)
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(50).all()
    selected_lead = None
    plan_days = []
    total_cost = 0
    plan_name = ""

    if lead_id:
        selected_lead = Lead.query.get(lead_id)
        if selected_lead:
            plan_name = f"{selected_lead.customer_name or 'Trip'} — {selected_lead.destination or 'Adventure'}"
            # Generate Shunya itinerary if one doesn't exist
            from app.shunya.knowledge import KnowledgeLayer
            from app.shunya._legacy_reasoning import ReasoningLayer
            from app.shunya.planner import PlannerLayer

            k = KnowledgeLayer()
            r = ReasoningLayer(k)
            p = PlannerLayer()
            inquiry = {
                "customer_name": selected_lead.customer_name or "",
                "destination": selected_lead.destination or "",
                "pax": selected_lead.pax or "2",
                "dates": selected_lead.dates or "",
                "notes": selected_lead.notes or "",
            }
            profile = r.analyze_inquiry(inquiry)
            strategy = r.suggest_approach(profile)
            plan = p.create_itinerary(profile, strategy)
            total_cost = plan.total_estimated_cost or 0

            for day in plan.days:
                plan_days.append({
                    "day": day.day_num,
                    "title": day.title or f"Day {day.day_num}",
                    "morning": day.morning or "",
                    "afternoon": day.afternoon or "",
                    "evening": day.evening or "",
                    "accommodation": day.accommodation or "",
                })

    return render_template("itinerary_builder.html", leads=leads,
                           selected_lead=selected_lead, plan_days=plan_days,
                           total_cost=total_cost, plan_name=plan_name)


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
            # Auto-celebrate
            try:
                from app.celebrations import CelebrationEngine
                ce = CelebrationEngine()
                ce.celebrate_payment(obj.lead_id, float(p.amount), user=getattr(g, "user", ""))
            except Exception:
                pass
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
# Payment Gateway — Checkout, Links, Receipts
# ---------------------------------------------------------------------------

@main.route("/payment/link/<int:lead_id>")
def payment_link(lead_id):
    """Generate a payment link page for a lead."""
    lead = Lead.query.get_or_404(lead_id)
    amount = request.args.get("amount", type=float) or float(lead.budget or 0)
    description = request.args.get("description", f"Payment for Lead {lead.code}")
    
    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    link_data = gw.create_payment_link(
        lead_id=lead.id,
        amount=amount,
        description=description,
        currency=request.args.get("currency", "INR"),
    )
    return redirect(url_for("main.payment_checkout", payment_id=link_data["payment_id"]))


@api.route("/payment/create", methods=["POST"])
def api_create_payment():
    """API: Create a payment intent."""
    data = request.get_json(silent=True) or {}
    lead_id = data.get("lead_id")
    amount = data.get("amount")
    description = data.get("description", "Payment")
    currency = data.get("currency", "INR")

    if not lead_id or not amount:
        return jsonify({"error": "lead_id and amount are required"}), 400

    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({"error": "Lead not found"}), 404

    try:
        from app.payment_gateway import PaymentGateway
        gw = PaymentGateway()
        result = gw.create_payment_link(
            lead_id=lead.id,
            amount=float(amount),
            description=description,
            currency=currency,
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api.route("/payment/verify", methods=["POST"])
def api_verify_payment():
    """API: Verify a payment."""
    data = request.get_json(silent=True) or {}
    payment_id = data.get("payment_id")
    if not payment_id:
        return jsonify({"error": "payment_id is required"}), 400

    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    result = gw.verify_payment(payment_id)
    return jsonify(result)


@main.route("/payment/checkout/<payment_id>")
def payment_checkout(payment_id):
    """Checkout page — simulated payment form."""
    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    payment = gw.get_payment(payment_id)

    if not payment:
        flash("Payment link invalid or expired.", "error")
        return redirect(url_for("main.payments"))

    lead = Lead.query.get(payment["lead_id"]) if payment.get("lead_id") else None

    return render_template(
        "payment_checkout.html",
        payment=payment,
        lead=lead,
        gateway_provider=gw.PROVIDER,
    )


@main.route("/payment/complete", methods=["POST"])
def payment_complete():
    """
    Complete payment (simulated). Creates a Payment record in the DB,
    logs activity, and triggers CompanionEngine celebration.
    """
    payment_id = request.form.get("payment_id", "")
    if not payment_id:
        flash("Missing payment reference.", "error")
        return redirect(url_for("main.payments"))

    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()

    # "Process" the payment
    verification = gw.verify_payment(payment_id)
    if not verification["verified"]:
        flash("Payment verification failed.", "error")
        return redirect(url_for("main.payment_checkout", payment_id=payment_id))

    payment_data = gw.get_payment(payment_id)
    if not payment_data:
        flash("Payment record not found.", "error")
        return redirect(url_for("main.payments"))

    # Create a real Payment record in the database
    p = Payment(
        lead_id=payment_data.get("lead_id"),
        type="guest_payment",
        amount=payment_data["amount"],
        method="online",
        ref_number=verification["transaction_id"],
        paid_at=datetime.utcnow(),
        notes=f"Online payment via {gw.PROVIDER}. Gateway ID: {payment_id}",
    )
    db.session.add(p)
    db.session.commit()

    # Log activity
    if p.lead_id:
        _log_activity(
            p.lead_id,
            "payment_received",
            f"Online payment: ₹{p.amount:.0f} · Txn: {p.ref_number}",
        )

    # Determine lead display code for messages
    lead_display = p.lead.code if p.lead else f"Lead #{p.lead_id}"

    # Companion celebration
    try:
        from app.companion import CompanionEngine
        c = CompanionEngine()
        celebration_msg = c.celebrate(
            achievement=f"Payment of ₹{p.amount:,.0f} received for {lead_display}!",
            name=getattr(g, "user", ""),
        )
        flash(celebration_msg, "success")
    except Exception:
        flash(f"Payment of ₹{p.amount:,.0f} completed successfully! 🎉", "success")

    # Create a notification
    try:
        from app.notifications import NotificationManager
        nm = NotificationManager()
        nm.create_notification(
            type="payment_received",
            title="Payment Received",
            message=f"Online payment of ₹{p.amount:,.0f} completed for {lead_display}",
            lead_id=p.lead_id,
            icon="💰",
        )
    except Exception:
        pass

    # Auto-celebrate via CelebrationEngine
    try:
        from app.celebrations import CelebrationEngine
        ce = CelebrationEngine()
        ce.celebrate_payment(p.lead_id, float(p.amount), user=getattr(g, "user", ""))
    except Exception:
        pass

    return redirect(url_for("main.payment_receipt", payment_id=payment_id))


@main.route("/payment/receipt/<payment_id>")
def payment_receipt(payment_id):
    """View payment receipt page."""
    from app.payment_gateway import PaymentGateway
    gw = PaymentGateway()
    payment = gw.get_payment(payment_id)

    if not payment:
        flash("Receipt not found.", "error")
        return redirect(url_for("main.payments"))

    lead = Lead.query.get(payment["lead_id"]) if payment.get("lead_id") else None

    # Get the associated Payment record from DB
    db_payment = None
    if payment.get("transaction_id"):
        db_payment = Payment.query.filter_by(ref_number=payment["transaction_id"]).first()

    return render_template(
        "payment_receipt.html",
        payment=payment,
        lead=lead,
        db_payment=db_payment,
        gateway_provider=gw.PROVIDER,
    )


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
# Tasks & Checklists
# ---------------------------------------------------------------------------

@main.route("/tasks")
def tasks_list():
    """Task dashboard — lists on left, tasks on right."""
    from app.tasks import TaskManager
    tm = TaskManager()
    all_lists = tm.get_all_lists()
    list_id = request.args.get("list", type=int)

    # Pre-compute counts for each list
    lists_data = []
    for lst in all_lists:
        total = lst.tasks.count()
        done = Task.query.filter(
            Task.task_list_id == lst.id, Task.status == "completed"
        ).count()
        lists_data.append({"id": lst.id, "name": lst.name,
                           "count": total, "done": done,
                           "created_by": lst.created_by})

    selected_list = None
    tasks = []
    total_count = done_count = pending_count = 0
    progress_pct = 0

    if list_id:
        selected_list = tm.get_list(list_id)
        if selected_list:
            tasks = tm.get_tasks_for_list(list_id)
            total_count = len(tasks)
            done_count = sum(1 for t in tasks if t.status == "completed")
            pending_count = total_count - done_count
            progress_pct = round(done_count / total_count * 100) if total_count else 0

    stats = tm.get_statistics()
    companion_greeting = "Stay on top of your tasks! Mark items done as you go. ✅"
    companion_suggestions = [
        {"icon": "📋", "text": "Review pending tasks", "action": "/tasks"},
        {"icon": "📊", "text": "View reports", "action": "/reports"},
        {"icon": "💰", "text": "Check payments", "action": "/payments"},
    ]

    return render_template("tasks.html",
                           lists_data=lists_data,
                           selected_list=selected_list,
                           tasks=tasks,
                           total_count=total_count,
                           done_count=done_count,
                           pending_count=pending_count,
                           progress_pct=progress_pct,
                           stats=stats,
                           today=date.today(),
                           companion_greeting=companion_greeting,
                           companion_suggestions=companion_suggestions)


@main.route("/tasks/create", methods=["POST"])
def tasks_create_list():
    """Create a new task list."""
    from app.tasks import TaskManager
    name = request.form.get("name", "").strip()
    if not name:
        flash("List name is required", "error")
        return redirect(url_for("main.tasks_list"))
    tm = TaskManager()
    tm.create_list(name=name, created_by=getattr(g, "user", ""))
    flash(f"List '{name}' created", "success")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/<int:id>/delete", methods=["POST"])
def tasks_delete_list(id):
    """Delete a task list and all its tasks."""
    from app.tasks import TaskManager
    tm = TaskManager()
    if tm.delete_list(id):
        flash("List deleted", "success")
    else:
        flash("List not found", "error")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/<int:id>/add", methods=["POST"])
def tasks_add_item(id):
    """Add a task to a list."""
    from app.tasks import TaskManager
    title = request.form.get("title", "").strip()
    if not title:
        flash("Task title is required", "error")
        return redirect(url_for("main.tasks_list", list=id))
    tm = TaskManager()
    task = tm.add_task(
        list_id=id,
        title=title,
        description=request.form.get("description", ""),
        assigned_to=request.form.get("assigned_to", ""),
        priority=request.form.get("priority", "medium"),
        due_date=request.form.get("due_date"),
    )
    if task:
        flash(f"Task '{title}' added", "success")
    else:
        flash("Could not add task — list not found", "error")
    return redirect(url_for("main.tasks_list", list=id))


@main.route("/tasks/item/<int:id>/status", methods=["POST"])
def tasks_update_status(id):
    """Update task status (checkbox toggle). Accepts JSON."""
    from app.tasks import TaskManager
    json_data = request.get_json(silent=True)
    if json_data:
        new_status = json_data.get("status", "")
    else:
        new_status = request.form.get("status", "")

    tm = TaskManager()
    task = tm.update_status(id, new_status)
    if task:
        if json_data:
            return jsonify({"success": True, "status": task.status})
        flash(f"Task updated: {task.status}", "success")
    else:
        if json_data:
            return jsonify({"success": False, "error": "Task not found or invalid status"}), 400
        flash("Task not found", "error")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/item/<int:id>/delete", methods=["POST"])
def tasks_delete_item(id):
    """Delete a task. Accepts JSON."""
    from app.tasks import TaskManager
    json_data = request.get_json(silent=True)
    tm = TaskManager()
    if tm.delete_task(id):
        if json_data:
            return jsonify({"success": True})
        flash("Task deleted", "success")
    else:
        if json_data:
            return jsonify({"success": False, "error": "Task not found"}), 400
        flash("Task not found", "error")
    return redirect(url_for("main.tasks_list"))


@main.route("/tasks/reorder", methods=["POST"])
def tasks_reorder():
    """Reorder tasks within a list (drag & drop). Accepts JSON."""
    from app.tasks import TaskManager
    data = request.get_json(silent=True) or {}
    order = data.get("order", [])
    tm = TaskManager()
    for idx, task_id in enumerate(order):
        tm.update_task(task_id, sort_order=idx)
    return jsonify({"success": True})


@api.route("/tasks")
def api_tasks():
    """JSON endpoint returning all tasks."""
    from app.tasks import TaskManager
    tm = TaskManager()
    all_lists = tm.get_all_lists()
    result = []
    for lst in all_lists:
        tasks = tm.get_tasks_for_list(lst.id)
        result.append({
            "id": lst.id,
            "name": lst.name,
            "tasks": [t.to_dict() for t in tasks],
        })
    return jsonify(result)


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
# WhatsApp Webhook — plug-and-play
# ---------------------------------------------------------------------------

@main.route("/whatsapp/webhook", methods=["GET", "POST"])
def whatsapp_webhook():
    """WhatsApp Business API webhook. GET = verification, POST = incoming msg."""
    if request.method == "GET":
        from app.whatsapp_webhook import handle_whatsapp_verification
        return handle_whatsapp_verification()

    from app.whatsapp_webhook import handle_whatsapp_incoming
    payload = request.get_json(silent=True) or {}
    return handle_whatsapp_incoming(payload)


@main.route("/whatsapp/setup", methods=["POST"])
def whatsapp_setup():
    """Configure WhatsApp Business API settings."""
    token = request.form.get("whatsapp_token", "")
    phone_id = request.form.get("phone_number_id", "")
    if token:
        os.environ["WHATSAPP_TOKEN"] = token
    if phone_id:
        os.environ["WHATSAPP_PHONE_ID"] = phone_id
    flash("WhatsApp settings saved. Webhook is ready at /whatsapp/webhook", "success")
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
# API: Notifications
# ---------------------------------------------------------------------------

@api.route("/notifications", methods=["GET"])
def api_get_notifications():
    """Get notifications for the current user (or all if no user)."""
    from app.notifications import NotificationManager
    limit = min(int(request.args.get("limit", 20)), 100)
    user_id = g.user.id if hasattr(g, "user") and g.user else None
    nm = NotificationManager()
    notifications = nm.get_for_user(user_id=user_id, limit=limit)
    return jsonify([n.to_dict() for n in notifications])


@api.route("/notifications/unread/count", methods=["GET"])
def api_unread_count():
    """Get unread notification count for the current user."""
    from app.notifications import NotificationManager
    user_id = g.user.id if hasattr(g, "user") and g.user else None
    nm = NotificationManager()
    count = nm.get_unread_count(user_id=user_id)
    return jsonify({"count": count})


@api.route("/notifications/<int:notification_id>/read", methods=["POST"])
def api_mark_read(notification_id):
    """Mark a single notification as read."""
    from app.notifications import NotificationManager
    nm = NotificationManager()
    success = nm.mark_read(notification_id)
    if not success:
        return jsonify({"error": "Notification not found"}), 404
    return jsonify({"success": True})


@api.route("/notifications/read-all", methods=["POST"])
def api_mark_all_read():
    """Mark all notifications as read for the current user."""
    from app.notifications import NotificationManager
    user_id = g.user.id if hasattr(g, "user") and g.user else None
    nm = NotificationManager()
    count = nm.mark_all_read(user_id=user_id)
    return jsonify({"success": True, "marked": count})


@api.route("/notifications/create", methods=["POST"])
def api_create_notification():
    """Create a notification (for system events / programmatic use)."""
    from app.notifications import NotificationManager
    data = request.get_json(silent=True) or {}
    required = ["type", "title"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400
    nm = NotificationManager()
    notif = nm.create_notification(
        type=data["type"],
        title=data["title"],
        message=data.get("message", ""),
        user_id=data.get("user_id"),
        lead_id=data.get("lead_id"),
        tenant_id=data.get("tenant_id"),
        icon=data.get("icon"),
        link=data.get("link"),
    )
    return jsonify(notif.to_dict()), 201


# ---------------------------------------------------------------------------
# Celebrations API
# ---------------------------------------------------------------------------

@api.route("/celebrations", methods=["GET"])
def api_get_celebrations():
    """Get recent celebrations."""
    from app.celebrations import CelebrationEngine
    limit = min(int(request.args.get("limit", 10)), 50)
    ce = CelebrationEngine()
    celebrations = ce.get_recent_celebrations(limit=limit)
    count = ce.get_celebration_count_since()
    return jsonify({"celebrations": celebrations, "count": count})


@api.route("/celebrations/scan", methods=["GET"])
def api_scan_celebrations():
    """Scan for new wins and record any that haven't been recorded yet."""
    from app.celebrations import CelebrationEngine
    ce = CelebrationEngine()
    new_celebrations = ce.scan_and_record()
    celebrations = ce.get_recent_celebrations(limit=10)
    count = ce.get_celebration_count_since()
    return jsonify({
        "new": new_celebrations,
        "celebrations": celebrations,
        "count": count,
    })


@api.route("/celebrations", methods=["POST"])
def api_create_celebration():
    """Manually create a celebration."""
    from app.celebrations import CelebrationEngine
    data = request.get_json(silent=True) or {}
    required = ["title"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    ce = CelebrationEngine()
    celebration = ce.record_celebration(
        celebration_type=data.get("type", "manual"),
        title=data["title"],
        message=data.get("message", ""),
        icon=data.get("icon", "🎉"),
        animation=data.get("animation", "woosh"),
        lead_id=data.get("lead_id"),
        created_by=data.get("created_by", ""),
    )
    return jsonify(celebration), 201


# ---------------------------------------------------------------------------
# PDF Generation (inline helper)
# ---------------------------------------------------------------------------

@api.route("/voice/process", methods=["POST"])
def voice_process():
    """Process voice input from the browser SpeechRecognition API.

    Accepts: {text: "user speech text", web_search: true}
    Returns: {response: "AI reply", action: "suggestions"|"redirect"|"none"|"info", redirect_url: ""}
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    web_search = data.get("web_search", False)

    if not text:
        return jsonify({"response": "I didn't catch that. Could you say it again?", "action": "none", "redirect_url": ""})

    # Web intelligence for travel/destination/weather queries
    if web_search or any(k in text.lower() for k in ["weather", "visa", "currency", "destination",
                                                       "bali", "thailand", "dubai", "maldives",
                                                       "time", "date", "today", "tell me about"]):
        from app.web_intel import WebIntelligence
        result = WebIntelligence.answer(text)
        if result["action"] == "info":
            return jsonify({"response": result["response"], "action": "none", "redirect_url": ""})
        # Check travel info
        for dest in ["bali", "thailand", "dubai", "maldives", "sri lanka"]:
            if dest in text.lower():
                result = WebIntelligence.search_travel_info(dest)
                return jsonify({"response": result["response"], "action": "none", "redirect_url": ""})

    from app.voice import VoiceProcessor
    user_name = getattr(g, "user", None)
    name = user_name.name if user_name else "there"
    processor = VoiceProcessor(user_name=name)
    result = processor.process(text)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Documents — AI Document Reading
# ---------------------------------------------------------------------------

@main.route("/documents")
def documents_page():
    """Document management page — upload, view, classify documents."""
    documents = Document.query.order_by(Document.created_at.desc()).limit(100).all()
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(300).all()
    return render_template("documents.html", documents=documents, leads=leads)


@main.route("/documents/upload", methods=["POST"])
def documents_upload():
    """Upload and process a document — extract text, classify, parse lead info."""
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("main.documents_page"))

    f = request.files["file"]
    if not f or not f.filename:
        flash("No file selected", "error")
        return redirect(url_for("main.documents_page"))

    # Determine file type
    ext = os.path.splitext(f.filename)[1].lower()
    file_type = "text"
    if ext in (".pdf",):
        file_type = "pdf"
    elif ext in (".docx", ".doc"):
        file_type = "docx"
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"):
        file_type = "image"
    elif ext in (".txt", ".csv", ".json", ".xml", ".md", ".log", ".ini", ".cfg"):
        file_type = "text"
    else:
        flash(f"Unsupported file type: {ext}", "error")
        return redirect(url_for("main.documents_page"))

    # Save file
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "documents")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{f.filename}"
    file_path = os.path.join(upload_dir, safe_name)
    try:
        f.save(file_path)
    except Exception as e:
        flash(f"Failed to save file: {e}", "error")
        return redirect(url_for("main.documents_page"))

    # Process document with DocumentReader
    from app.document_reader import DocumentReader
    reader = DocumentReader()
    result = reader.process_document(file_path, file_type)
    structured_json = json.dumps(result.get("structured_data", {}))

    # Optional lead association
    lead_id = request.form.get("lead_id", type=int)
    if not lead_id:
        lead_id = None

    doc = Document(
        lead_id=lead_id,
        filename=f.filename,
        file_path=file_path,
        file_type=file_type,
        extracted_text=result.get("extracted_text", ""),
        structured_data=structured_json,
        classification=result.get("classification", "other"),
        uploaded_by=getattr(g, "user", ""),
    )
    try:
        db.session.add(doc)
        db.session.commit()
        if doc.lead_id:
            _log_activity(doc.lead_id, "document_uploaded",
                          f"Document '{doc.filename}' uploaded ({doc.classification})")
        flash(f"✅ Document processed: {doc.filename} — classified as {doc.classification}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to save document record: {e}", "error")

    return redirect(url_for("main.documents_page"))


@main.route("/documents/<int:doc_id>")
def documents_detail(doc_id):
    """View document details — extracted text, structured data, classification."""
    doc = Document.query.get_or_404(doc_id)
    documents = [doc]
    leads = Lead.query.order_by(Lead.created_at.desc()).limit(300).all()
    return render_template("documents.html", view_doc=doc, documents=documents, leads=leads)


@main.route("/api/documents/extract", methods=["POST"])
def api_documents_extract():
    """API: Upload a file, return extracted text + structured data as JSON."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "No file provided"}), 400

    ext = os.path.splitext(f.filename)[1].lower()
    file_type = "text"
    if ext in (".pdf",):
        file_type = "pdf"
    elif ext in (".docx", ".doc"):
        file_type = "docx"
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"):
        file_type = "image"

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "documents")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{f.filename}"
    file_path = os.path.join(upload_dir, safe_name)
    try:
        f.save(file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {e}"}), 500

    from app.document_reader import DocumentReader
    reader = DocumentReader()
    result = reader.process_document(file_path, file_type)

    return jsonify({
        "filename": f.filename,
        "file_type": file_type,
        "extracted_text": result.get("extracted_text", ""),
        "summary": result.get("summary", ""),
        "classification": result.get("classification", "other"),
        "structured_data": result.get("structured_data", {}),
    })


@main.route("/api/documents/classify", methods=["POST"])
def api_documents_classify():
    """API: Classify a document (text-based classification)."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    from app.document_reader import DocumentReader
    reader = DocumentReader()
    classification = reader.classify_document(text)
    summary = reader.summarize_document(text)

    return jsonify({
        "classification": classification,
        "summary": summary,
        "text_length": len(text),
    })


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


# ---------------------------------------------------------------------------
# Executive Workspace
# ---------------------------------------------------------------------------

from app.auth_routes import login_required


@main.route("/executive")
@login_required
def executive_workspace():
    """Redirect to the canonical React SPA workspace (executive view handled client-side)."""
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Workspace Runtime API
# ---------------------------------------------------------------------------

from app.workspace_runtime import WorkspaceAPI, get_workspace_runtime, reset_workspace_runtime


@main.route("/api/workspace/object/<obj_type>/<obj_id>")
@login_required
def workspace_focus_object(obj_type, obj_id):
    """Focus the workspace on an object. Returns full object data + intelligence."""
    api = WorkspaceAPI()
    return jsonify(api.focus_object(obj_type, obj_id))


@main.route("/api/workspace/executive")
@login_required
def workspace_executive_data():
    """Get all executive intelligence data for the workspace."""
    api = WorkspaceAPI()
    return jsonify(api.get_executive_data())


@main.route("/api/workspace/conversation/<obj_type>/<obj_id>")
@login_required
def workspace_get_conversation(obj_type, obj_id):
    """Get conversation history for an object."""
    api = WorkspaceAPI()
    return jsonify(api.get_conversation(obj_type, obj_id))


@main.route("/api/workspace/conversation/<obj_type>/<obj_id>/send", methods=["POST"])
@login_required
def workspace_send_message(obj_type, obj_id):
    """Send a message in an object's conversation."""
    data = request.get_json() or {}
    text = data.get("text", "")
    api = WorkspaceAPI()
    return jsonify(api.send_message(obj_type, obj_id, text))


@main.route("/api/workspace/updates")
@login_required
def workspace_updates():
    """Get runtime updates since last check."""
    api = WorkspaceAPI()
    return jsonify(api.get_updates())


@main.route("/api/workspace/graph/<obj_type>/<obj_id>")
@login_required
def workspace_object_graph(obj_type, obj_id):
    """Get the object graph centered on an object."""
    api = WorkspaceAPI()
    return jsonify(api.get_object_graph(obj_type, obj_id))


@main.route("/api/workspace/recent")
@login_required
def workspace_recent():
    """Get recent objects across all types."""
    api = WorkspaceAPI()
    return jsonify(api.get_recent_objects())


@main.route("/api/workspace/types")
@login_required
def workspace_types():
    """Get available object types."""
    api = WorkspaceAPI()
    return jsonify(api.get_available_types())


@main.route("/api/workspace/state")
@login_required
def workspace_state():
    """Get current workspace runtime state."""
    api = WorkspaceAPI()
    return jsonify(api.get_state())


@main.route("/api/workspace/mode/<mode>")
@login_required
def workspace_set_mode(mode):
    """Set the current executive mode."""
    api = WorkspaceAPI()
    return jsonify(api.set_mode(mode))


@main.route("/api/workspace/attention/<layer>")
@login_required
def workspace_set_attention(layer):
    """Set the attention layer (executive, team, personal)."""
    api = WorkspaceAPI()
    return jsonify(api.set_attention_layer(layer))


@main.route("/api/workspace/stats")
@login_required
def workspace_stats():
    """Get workspace runtime statistics."""
    api = WorkspaceAPI()
    return jsonify(api.stats())