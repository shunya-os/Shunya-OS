"""SHUNYA — Client Portal Blueprint

Customers can log in, view their itinerary, make payments,
and communicate with the team via a clean, light-themed portal.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g

from app import db
from app.models import Lead, ClientUser, ClientMessage, Payment, PaymentType, ActivityLog

client_bp = Blueprint("client", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def client_login_required(view):
    """Decorator: redirect to client login if not authenticated as a client user."""
    from functools import wraps

    @wraps(view)
    def wrapped_view(**kwargs):
        client_user_id = session.get("client_user_id")
        if not client_user_id:
            return redirect(url_for("client.client_login", next=request.path))
        user = db.session.get(ClientUser, client_user_id)
        if not user or not user.is_active:
            session.pop("client_user_id", None)
            return redirect(url_for("client.client_login"))
        g.client_user = user
        return view(**kwargs)

    return wrapped_view


def _get_lead_or_404(client_user):
    """Get the lead associated with a client user, or 404."""
    if not client_user.lead_id:
        return None
    lead = db.session.get(Lead, client_user.lead_id)
    return lead


def _get_itinerary_days(lead):
    """Parse itinerary days from the lead's notes (or return sample)."""
    if not lead or not lead.destination:
        return []

    # Try to extract structured itinerary from Shunya data via notes
    from app.shunya.knowledge import KnowledgeLayer
    from app.shunya._legacy_reasoning import ReasoningLayer
    from app.shunya.planner import PlannerLayer

    try:
        k = KnowledgeLayer()
        r = ReasoningLayer(k)
        p = PlannerLayer()
        inquiry = {
            "customer_name": lead.customer_name or "",
            "destination": lead.destination or "",
            "pax": lead.pax or "2",
            "dates": lead.dates or "",
            "notes": lead.notes or "",
        }
        profile = r.analyze_inquiry(inquiry)
        strategy = r.suggest_approach(profile)
        plan = p.create_itinerary(profile, strategy)
        days = []
        for day in plan.days:
            days.append({
                "day": day.day_num,
                "title": day.title or f"Day {day.day_num}",
                "morning": day.morning or "",
                "afternoon": day.afternoon or "",
                "evening": day.evening or "",
                "accommodation": day.accommodation or "",
            })
        return days
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@client_bp.route("/client/login", methods=["GET", "POST"])
def client_login():
    """Client login page."""
    # If already logged in, go to dashboard
    if session.get("client_user_id"):
        return redirect(url_for("client.client_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = ClientUser.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            session["client_user_id"] = user.id
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_url = request.args.get("next") or url_for("client.client_dashboard")
            return redirect(next_url)

        flash("Invalid email or password", "error")
        return render_template("client/client_login.html")

    return render_template("client/client_login.html")


@client_bp.route("/client/logout")
def client_logout():
    """Client logout."""
    session.pop("client_user_id", None)
    flash("You have been logged out", "success")
    return redirect(url_for("client.client_login"))


@client_bp.route("/client/register", methods=["GET", "POST"])
def client_register():
    """Quick registration form for clients."""
    if session.get("client_user_id"):
        return redirect(url_for("client.client_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        lead_code = request.form.get("lead_code", "").strip().upper()

        if not name or not email or not password:
            flash("Name, email, and password are required", "error")
            return render_template("client/client_register.html")

        # Check if email already registered
        if ClientUser.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please log in.", "error")
            return render_template("client/client_register.html")

        # Try to link to a lead
        lead = None
        if lead_code:
            lead = Lead.query.filter_by(code=lead_code).first()
            if not lead:
                flash(f"Lead code '{lead_code}' not found. You can register without one.", "warning")

        user = ClientUser(
            name=name,
            email=email,
            phone=phone,
            lead_id=lead.id if lead else None,
            is_active=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if lead:
            lead.log_activity(
                "client_registered",
                f"{name} ({email}) registered for client portal",
                "System",
            )

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("client.client_login"))

    return render_template("client/client_register.html")


@client_bp.route("/client/dashboard")
@client_login_required
def client_dashboard():
    """Client home — shows lead status, itinerary summary, quick links."""
    user = g.client_user
    lead = _get_lead_or_404(user)

    recent_activity = []
    if lead:
        recent_activity = (
            lead.activities.order_by(ActivityLog.created_at.desc()).limit(5).all()
        )

    # Unread message count
    unread_count = 0
    if lead:
        unread_count = ClientMessage.query.filter_by(
            lead_id=lead.id, sender="team", is_read=False
        ).count()

    return render_template(
        "client/client_dashboard.html",
        client_user=user,
        lead=lead,
        recent_activity=recent_activity,
        unread_count=unread_count,
    )


@client_bp.route("/client/itinerary")
@client_login_required
def client_itinerary():
    """View their itinerary plan."""
    user = g.client_user
    lead = _get_lead_or_404(user)
    plan_days = _get_itinerary_days(lead)

    return render_template(
        "client/client_itinerary.html",
        client_user=user,
        lead=lead,
        plan_days=plan_days,
    )


@client_bp.route("/client/payments", methods=["GET", "POST"])
@client_login_required
def client_payments():
    """View and make simulated payments."""
    user = g.client_user
    lead = _get_lead_or_404(user)
    payments = []
    total_paid = 0

    if lead:
        payments = (
            Payment.query.filter_by(lead_id=lead.id, type=PaymentType.GUEST.value)
            .order_by(Payment.paid_at.desc())
            .all()
        )
        total_paid = sum(float(p.amount or 0) for p in payments)

    if request.method == "POST" and lead:
        amount = float(request.form.get("amount", 0))
        method = request.form.get("method", "bank_transfer")
        notes = request.form.get("notes", "")

        if amount <= 0:
            flash("Please enter a valid amount", "error")
        else:
            # Create payment (simulated — no actual gateway)
            payment = Payment(
                lead_id=lead.id,
                type=PaymentType.GUEST.value,
                amount=amount,
                method=method,
                notes=notes,
            )
            db.session.add(payment)
            db.session.commit()
            lead.log_activity(
                "payment_received",
                f"Client portal payment: ₹{amount:,.0f} via {method}",
                user.name or "Client",
            )
            flash(f"Payment of ₹{amount:,.0f} recorded successfully!", "success")
        return redirect(url_for("client.client_payments"))

    return render_template(
        "client/client_payments.html",
        client_user=user,
        lead=lead,
        payments=payments,
        total_paid=total_paid,
    )


@client_bp.route("/client/messages", methods=["GET", "POST"])
@client_login_required
def client_messages():
    """Chat-style messaging with the team."""
    user = g.client_user
    lead = _get_lead_or_404(user)
    messages = []

    if lead:
        if request.method == "POST":
            text = request.form.get("message", "").strip()
            if text:
                msg = ClientMessage(
                    lead_id=lead.id,
                    client_user_id=user.id,
                    sender="client",
                    message=text,
                )
                db.session.add(msg)
                db.session.commit()

                # Auto-reply from team (makes it feel alive)
                auto_replies = [
                    "Thanks for your message! Our team will review this shortly.",
                    "We've received your message and will get back to you soon.",
                    "Thank you! A team member will respond to you shortly.",
                    "We've noted your request. Someone from our team will follow up.",
                ]
                import random
                auto_text = random.choice(auto_replies)
                auto_msg = ClientMessage(
                    lead_id=lead.id,
                    client_user_id=None,
                    sender="team",
                    message=auto_text,
                    is_read=True,
                )
                db.session.add(auto_msg)
                db.session.commit()

                # Mark all team messages as read
                ClientMessage.query.filter_by(
                    lead_id=lead.id, sender="team", is_read=False
                ).update({"is_read": True})
                db.session.commit()

                return redirect(url_for("client.client_messages"))

        # Fetch messages
        messages = (
            ClientMessage.query.filter_by(lead_id=lead.id)
            .order_by(ClientMessage.created_at.asc())
            .all()
        )

        # Mark all team messages as read when user views the page
        ClientMessage.query.filter_by(
            lead_id=lead.id, sender="team", is_read=False
        ).update({"is_read": True})
        db.session.commit()

    return render_template(
        "client/client_messages.html",
        client_user=user,
        lead=lead,
        messages=messages,
    )