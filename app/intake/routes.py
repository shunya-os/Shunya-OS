from flask import Blueprint, request, jsonify
from app.intake.service import IntakeService

intake_bp = Blueprint("intake", __name__, url_prefix="/api/v1/intake")


@intake_bp.route("/", methods=["POST"])
def receive():
    data = request.json or {}

    raw_input = data.get("input", "")
    input_type = data.get("type", "text")

    signal = IntakeService.receive_input(raw_input, input_type)

    return jsonify({
        "id": signal.id,
        "status": signal.status
    })


@intake_bp.route("/<int:signal_id>/process", methods=["POST"])
def process(signal_id):
    from app.intake.models import IntakeSignal

    signal = IntakeSignal.query.get_or_404(signal_id)

    processed = IntakeService.process_signal(signal)

    return jsonify({
        "id": processed.id,
        "status": processed.status,
        "structured_data": processed.structured_data
    })