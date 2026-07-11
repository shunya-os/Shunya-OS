"""Shunya OS — Client Portal."""
import functools
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, session, g
from app import db
from app.models import ClientUser, Entity, EntityDefinition, Payment, Message

client_bp = Blueprint("client", __name__)


def client_login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        cid = session.get("client_user_id")
        if not cid:
            return render_template("client/login.html"), 401
        client = db.session.get(ClientUser, cid)
        if not client or not client.is_active:
            session.pop("client_user_id", None)
            return render_template("client/login.html"), 401
        g.client_user = client
        return view(**kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Client entity view (one URL per booking/patient/order)
# ---------------------------------------------------------------------------

@client_bp.route("/<code>")
def client_view(code):
    """Public client portal page for a given entity code."""
    from app.models import Entity, EntityDefinition

    entity = Entity.query.filter_by(code=code, is_archived=False).first()
    if not entity:
        return "<h1>Link not found</h1><p>This link may have expired.</p>", 404

    definition = db.session.get(EntityDefinition, entity.definition_id) if entity.definition_id else None

    # Payment status
    payments = Payment.query.filter_by(entity_id=entity.id).all()
    total_paid = sum(float(p.amount) for p in payments if p.status == "completed")
    total_due = float(entity.data.get("budget", 0)) - total_paid

    messages = Message.query.filter_by(entity_id=entity.id).order_by(Message.created_at.desc()).limit(50).all()

    return render_template("client/portal.html",
        entity=entity, definition=definition,
        payments=payments, total_paid=total_paid, total_due=total_due,
        messages=messages)


# ---------------------------------------------------------------------------
# Client auth via OTP
# ---------------------------------------------------------------------------

@client_bp.route("/api/send-otp", methods=["POST"])
def client_send_otp():
    data = request.get_json(silent=True) or request.form
    phone = data.get("phone", "").strip()
    if not phone:
        return jsonify({"error": "Phone required"}), 400

    client = ClientUser.query.filter_by(phone=phone).first()
    if not client:
        # Auto-create client user if entity matches
        entity_code = data.get("code", "")
        entity = Entity.query.filter_by(code=entity_code).first()
        if entity:
            client = ClientUser(
                tenant_id=entity.tenant_id,
                entity_id=entity.id,
                name=data.get("name", "Client"),
                phone=phone,
            )
            db.session.add(client)
            db.session.commit()
        else:
            return jsonify({"error": "No account found"}), 404

    otp = "".join(str(__import__("random").randint(0, 9)) for _ in range(6))
    client.otp_hash = __import__("hashlib").sha256(otp.encode()).hexdigest()
    db.session.commit()

    # TODO: Send OTP via WhatsApp/SMS
    print(f"[CLIENT-OTP] {phone}: {otp}")

    return jsonify({"success": True})


@client_bp.route("/api/verify-otp", methods=["POST"])
def client_verify_otp():
    data = request.get_json(silent=True) or request.form
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()

    client = ClientUser.query.filter_by(phone=phone).first()
    if not client:
        return jsonify({"error": "No account found"}), 404
    if client.otp_hash != __import__("hashlib").sha256(otp.encode()).hexdigest():
        return jsonify({"error": "Invalid OTP"}), 401

    client.last_login = datetime.utcnow()
    db.session.commit()
    session["client_user_id"] = client.id
    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# Client payment
# ---------------------------------------------------------------------------

@client_bp.route("/api/pay", methods=["POST"])
def client_pay():
    data = request.get_json(silent=True) or request.form
    entity_id = data.get("entity_id")
    amount = float(data.get("amount", 0))
    gateway = data.get("gateway", "razorpay")

    entity = db.session.get(Entity, entity_id)
    if not entity:
        return jsonify({"error": "Entity not found"}), 404

    payment = Payment(
        tenant_id=entity.tenant_id,
        entity_id=entity.id,
        amount=amount,
        gateway=gateway,
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    # TODO: Generate payment link via gateway API
    return jsonify({"success": True, "payment_id": payment.id,
                    "payment_link": f"https://pay.shunya/{payment.id}"})
