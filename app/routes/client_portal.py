"""Shunya OS — Client Portal API (itinerary, payments, documents, chat)."""
from flask import Blueprint, request, jsonify, render_template, session, g, send_file
from app import db
from app.models import Entity, EntityDefinition, ClientUser, Payment, Message, File, Invoice
from app.routes.auth import login_required
from datetime import datetime
import io, os, functools

client_bp = Blueprint("client", __name__, url_prefix="/client")


# ---------------------------------------------------------------------------
# Client auth helpers
# ---------------------------------------------------------------------------

def _get_client():
    cid = session.get("client_user_id")
    if not cid:
        return None
    return db.session.get(ClientUser, cid)


def client_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        client = _get_client()
        if not client or not client.is_active:
            return render_template("client/login.html"), 401
        g.client_user = client
        return view(**kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Client view entity by code (magic link)
# ---------------------------------------------------------------------------

@client_bp.route("/<code>")
def client_view(code):
    """Premium client portal — personalized view of their booking/patient record."""
    entity = Entity.query.filter_by(code=code, is_archived=False).first()
    if not entity:
        return render_template("client/404.html"), 404

    definition = db.session.get(EntityDefinition, entity.definition_id) if entity.definition_id else None
    tenant = entity.tenant  # relationship

    # Payments
    payments = Payment.query.filter_by(entity_id=entity.id).all()
    total_paid = sum(float(p.amount) for p in payments if p.status == "completed")
    total_due = max(0, float(entity.data.get("budget", 0)) - total_paid)

    # Messages
    messages = Message.query.filter_by(entity_id=entity.id).order_by(Message.created_at.desc()).limit(50).all()

    # Documents
    docs = File.query.filter_by(entity_id=entity.id).order_by(File.created_at.desc()).all()

    # Invoices
    invoices = Invoice.query.filter_by(entity_id=entity.id).order_by(Invoice.created_at.desc()).all()

    return render_template("client/portal.html",
        entity=entity, definition=definition, tenant=tenant,
        payments=payments, total_paid=total_paid, total_due=total_due,
        messages=messages, docs=docs, invoices=invoices)


# ---------------------------------------------------------------------------
# Client auth (passwordless OTP)
# ---------------------------------------------------------------------------

@client_bp.route("/api/send-otp", methods=["POST"])
def client_send_otp():
    data = request.get_json(silent=True) or request.form
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()

    # Find client by phone or entity code
    client = ClientUser.query.filter_by(phone=phone).first()
    if not client and code:
        entity = Entity.query.filter_by(code=code).first()
        if entity:
            client = ClientUser(
                tenant_id=entity.tenant_id,
                entity_id=entity.id,
                name=data.get("name", "Client"),
                phone=phone,
            )
            db.session.add(client)
            db.session.commit()

    if not client:
        return jsonify({"error": "No account found"}), 404

    import hashlib, random
    otp = "".join(str(random.randint(0, 9)) for _ in range(6))
    client.otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    client.last_login = datetime.utcnow()
    db.session.commit()

    # TODO: Send OTP via WhatsApp/SMS
    print(f"[CLIENT-OTP] {phone}: {otp}")

    return jsonify({"success": True})


@client_bp.route("/api/verify-otp", methods=["POST"])
def client_verify_otp():
    data = request.get_json(silent=True) or request.form
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()

    import hashlib
    client = ClientUser.query.filter_by(phone=phone).first()
    if not client:
        return jsonify({"error": "No account found"}), 404
    if client.otp_hash != hashlib.sha256(otp.encode()).hexdigest():
        return jsonify({"error": "Invalid OTP"}), 401

    client.last_login = datetime.utcnow()
    db.session.commit()
    session["client_user_id"] = client.id
    session["client_entity_id"] = client.entity_id
    return jsonify({"success": True, "redirect": f"/client/{client.entity.code if client.entity else ''}"})


# ---------------------------------------------------------------------------
# Client messages (two-way chat)
# ---------------------------------------------------------------------------

@client_bp.route("/api/messages", methods=["GET", "POST"])
@client_required
def client_messages():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        content = data.get("content", "").strip()
        if not content:
            return jsonify({"error": "Message required"}), 400

        msg = Message(
            tenant_id=g.client_user.tenant_id,
            entity_id=g.client_user.entity_id,
            sender_type="client",
            sender_id=g.client_user.id,
            channel="app",
            content=content,
            is_from_client=True,
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify({"success": True, "message": {
            "id": msg.id, "content": msg.content, "from_client": True,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }})

    messages = Message.query.filter_by(
        entity_id=g.client_user.entity_id
    ).order_by(Message.created_at.desc()).limit(50).all()

    return jsonify({"messages": [{
        "id": m.id, "content": m.content, "from_client": m.is_from_client,
        "channel": m.channel,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in reversed(messages)]})


# ---------------------------------------------------------------------------
# Client documents
# ---------------------------------------------------------------------------

@client_bp.route("/api/documents")
@client_required
def client_documents():
    docs = File.query.filter_by(entity_id=g.client_user.entity_id).all()
    return jsonify({"documents": [{
        "id": d.id, "filename": d.filename, "file_type": d.file_type,
        "file_size": d.file_size, "created_at": d.created_at.isoformat() if d.created_at else None,
    } for d in docs]})


@client_bp.route("/api/documents/<int:doc_id>/download")
@client_required
def client_download_document(doc_id):
    doc = File.query.filter_by(id=doc_id, entity_id=g.client_user.entity_id).first()
    if not doc:
        return jsonify({"error": "Not found"}), 404
    if not os.path.exists(doc.file_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(doc.file_path, as_attachment=True, download_name=doc.filename)


# ---------------------------------------------------------------------------
# Client payments
# ---------------------------------------------------------------------------

@client_bp.route("/api/payments")
@client_required
def client_payments():
    payments = Payment.query.filter_by(entity_id=g.client_user.entity_id).all()
    entity = db.session.get(Entity, g.client_user.entity_id)
    total_budget = float(entity.data.get("budget", 0)) if entity else 0
    total_paid = sum(float(p.amount) for p in payments if p.status == "completed")

    return jsonify({
        "payments": [{
            "id": p.id, "amount": float(p.amount), "currency": p.currency,
            "status": p.status, "gateway": p.gateway,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        } for p in payments],
        "total_budget": total_budget,
        "total_paid": total_paid,
        "total_due": max(0, total_budget - total_paid),
    })


@client_bp.route("/api/pay", methods=["POST"])
@client_required
def client_initiate_payment():
    data = request.get_json(silent=True) or request.form
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    payment = Payment(
        tenant_id=g.client_user.tenant_id,
        entity_id=g.client_user.entity_id,
        amount=amount,
        gateway="razorpay",
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    # TODO: Generate real payment link from gateway API
    return jsonify({
        "success": True,
        "payment_id": payment.id,
        "payment_link": f"https://pay.shunya/{payment.id}",
        "amount": amount,
    })


# ---------------------------------------------------------------------------
# Client logout
# ---------------------------------------------------------------------------

@client_bp.route("/logout")
def client_logout():
    session.pop("client_user_id", None)
    session.pop("client_entity_id", None)
    return render_template("client/login.html")