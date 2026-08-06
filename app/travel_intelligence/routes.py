"""DCP-01 — Universal Travel Intelligence API."""

from flask import Blueprint, jsonify, request, g

from .travel import get_travel_intelligence

travel_bp = Blueprint("travel", __name__, url_prefix="/api/v1/travel")


def _require_identity():
    identity_id = getattr(g, 'identity_id', None)
    if identity_id:
        return identity_id
    return request.headers.get("X-Identity-Id")


@travel_bp.route("/trips", methods=["POST"])
def plan_trip():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    destination = data.get("destination", "").strip()
    if not title or not destination:
        return jsonify({"success": False, "error": "title and destination required"}), 400
    rt = get_travel_intelligence()
    trip = rt.plan_trip(title=title, destination=destination,
                        start_date=data.get("start_date", "2026-10-01"),
                        end_date=data.get("end_date", "2026-10-07"),
                        travelers=data.get("travelers", 2), budget=data.get("budget", 0))
    return jsonify({"success": True, "data": trip.to_dict()}), 201


@travel_bp.route("/trips", methods=["GET"])
def list_trips():
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    status = request.args.get("status")
    rt = get_travel_intelligence()
    trips = [t.to_dict() for t in rt.list_trips(status=status)]
    return jsonify({"success": True, "data": trips})


@travel_bp.route("/trips/<trip_id>", methods=["GET"])
def get_trip(trip_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_travel_intelligence()
    trip = rt.get_trip(trip_id)
    if not trip:
        return jsonify({"success": False, "error": "Trip not found"}), 404
    return jsonify({"success": True, "data": trip.to_dict()})


@travel_bp.route("/trips/<trip_id>/analyze", methods=["GET"])
def analyze_trip(trip_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_travel_intelligence()
    return jsonify({"success": True, "data": rt.analyze_trip(trip_id)})


@travel_bp.route("/trips/<trip_id>/proposal", methods=["GET"])
def generate_proposal(trip_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_travel_intelligence()
    proposal = rt.generate_proposal(trip_id)
    if not proposal:
        return jsonify({"success": False, "error": "Trip not found"}), 404
    return jsonify({"success": True, "data": {"proposal": proposal}})


@travel_bp.route("/trips/<trip_id>/supplier-comm/<supplier_type>", methods=["GET"])
def supplier_communication(trip_id: str, supplier_type: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    rt = get_travel_intelligence()
    comm = rt.generate_supplier_communication(trip_id, supplier_type)
    return jsonify({"success": True, "data": {"communication": comm}})


@travel_bp.route("/trips/<trip_id>/disruption", methods=["POST"])
def handle_disruption(trip_id: str):
    identity_id = _require_identity()
    if not identity_id:
        return jsonify({"success": False, "error": "Authentication required"}), 401
    data = request.get_json(silent=True) or {}
    disruption_type = data.get("type", "").strip()
    if not disruption_type:
        return jsonify({"success": False, "error": "type required"}), 400
    rt = get_travel_intelligence()
    result = rt.handle_disruption(trip_id, disruption_type, data.get("details"))
    return jsonify({"success": True, "data": result})