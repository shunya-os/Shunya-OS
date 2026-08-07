from flask import Blueprint, request, jsonify
from app.communication.inbound import InboundEvent
from app import db

webhook_bp = Blueprint("webhook_api", __name__, url_prefix="/api/v1/webhook")


@webhook_bp.route("/", methods=["POST"])
def ingest():
    data = request.json or {}

    event = InboundEvent(
        source=data.get("source", "unknown"),
        payload=data
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({"status": "received"})