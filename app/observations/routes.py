from flask import Blueprint, request, jsonify
from app.observations.service import record_observation, evaluate_observation
from app.observations.models import Observation

observations_bp = Blueprint("observations", __name__, url_prefix="/api/v1/observations")


@observations_bp.route("/", methods=["POST"])
def create():
    data = request.json or {}

    obs = record_observation(
        commitment_id=data.get("commitment_id"),
        observed_value=data.get("observed_value"),
        expected_value=data.get("expected_value")
    )

    return jsonify({
        "id": obs.id,
        "status": obs.status
    })


@observations_bp.route("/<int:obs_id>/evaluate", methods=["POST"])
def evaluate(obs_id):
    obs = Observation.query.get_or_404(obs_id)

    evaluated = evaluate_observation(obs)

    return jsonify({
        "id": evaluated.id,
        "status": evaluated.status
    })