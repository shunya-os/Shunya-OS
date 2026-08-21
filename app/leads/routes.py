from flask import Blueprint, request, jsonify
from app import db
from app.models import Lead, next_inquiry_code

leads_bp = Blueprint("leads", __name__, url_prefix="/api/v1/leads")


@leads_bp.route("/", methods=["GET"])
def list_leads():
    """List all leads with optional status filter."""
    status = request.args.get("status")
    limit = min(request.args.get("limit", 100, type=int), 200)
    q = Lead.query.order_by(Lead.created_at.desc())
    if status:
        q = q.filter(Lead.status == status)
    leads = q.limit(limit).all()
    return jsonify({
        "leads": [{
            "id": l.id,
            "code": l.code,
            "source": l.source,
            "customer_name": l.customer_name or "",
            "phone": l.phone or "",
            "email": l.email or "",
            "destination": l.destination or "",
            "budget": float(l.budget or 0),
            "status": l.status,
            "stage": l.stage or "",
            "assigned_to": l.assigned_to or "",
            "outcome": l.outcome or "",
            "notes": (l.notes or "")[:200],
            "created_at": l.created_at.isoformat() if l.created_at else None,
        } for l in leads],
        "total": len(leads),
    })


@leads_bp.route("/", methods=["POST"])
def create_lead():
    data = request.json or {}
    code = next_inquiry_code(db.session)
    l = Lead(source=data.get("source", "direct"), code=code)
    db.session.add(l)
    db.session.commit()
    return jsonify({"id": l.id})