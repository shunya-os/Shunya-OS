from flask import Blueprint, request, jsonify
from app import db
from app.models import Lead, next_inquiry_code

leads_bp = Blueprint("leads", __name__, url_prefix="/api/v1/leads")


@leads_bp.route("/", methods=["POST"])
def create_lead():
    data = request.json or {}
    code = next_inquiry_code(db.session)
    l = Lead(source=data.get("source", "direct"), code=code)
    db.session.add(l)
    db.session.commit()
    return jsonify({"id": l.id})