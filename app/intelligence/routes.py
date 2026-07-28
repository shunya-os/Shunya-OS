"""SHUNYA M8 — Executive Intelligence Routes.

Reasoning traces, learning feedback, anomaly detection, confidence scoring.
"""
from flask import Blueprint, jsonify, request, session

intelligence_bp = Blueprint("intelligence", __name__, url_prefix="/api/v1/intelligence")


def _founder_required() -> bool:
    user_id = session.get("user_id")
    identity_id = session.get("identity_id")
    return bool(user_id and identity_id)


# ---------------------------------------------------------------------------
# Reasoning Traces
# ---------------------------------------------------------------------------

@intelligence_bp.route("/traces", methods=["GET"])
def api_list_traces():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    object_id = request.args.get("object_id")
    from app.intelligence.service import get_traces
    traces = get_traces(identity_id=identity_id, object_id=object_id)
    return jsonify({"success": True, "data": traces})


@intelligence_bp.route("/traces/<trace_id>", methods=["GET"])
def api_get_trace(trace_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.intelligence.service import get_trace
    trace = get_trace(trace_id=trace_id)
    if not trace:
        return jsonify({"success": False, "error": "Trace not found"}), 404
    return jsonify({"success": True, "data": trace})


@intelligence_bp.route("/traces/<trace_id>/correct", methods=["POST"])
def api_correct_trace(trace_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    corrected = data.get("corrected_response", "").strip()
    if not corrected:
        return jsonify({"success": False, "error": "corrected_response required"}), 400
    from app.intelligence.service import correct_trace
    result = correct_trace(trace_id=trace_id, corrected_response=corrected)
    return jsonify({"success": result})


# ---------------------------------------------------------------------------
# Learning
# ---------------------------------------------------------------------------

@intelligence_bp.route("/learning", methods=["GET"])
def api_learning_history():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.intelligence.service import get_learning_history
    history = get_learning_history(identity_id=identity_id)
    return jsonify({"success": True, "data": history})


@intelligence_bp.route("/learning/summary", methods=["GET"])
def api_learning_summary():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.intelligence.service import get_learning_summary
    summary = get_learning_summary(identity_id=identity_id)
    return jsonify({"success": True, "data": summary})


# ---------------------------------------------------------------------------
# Anomalies
# ---------------------------------------------------------------------------

@intelligence_bp.route("/anomalies", methods=["GET"])
def api_list_anomalies():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    status = request.args.get("status", "open")
    from app.intelligence.service import get_anomalies
    anomalies = get_anomalies(identity_id=identity_id, status=status)
    return jsonify({"success": True, "data": anomalies})


@intelligence_bp.route("/anomalies/detect", methods=["POST"])
def api_detect_anomalies():
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    identity_id = session.get("identity_id")
    from app.intelligence.service import detect_anomalies
    anomalies = detect_anomalies(identity_id=identity_id)
    return jsonify({"success": True, "data": anomalies, "count": len(anomalies)})


@intelligence_bp.route("/anomalies/<int:anomaly_id>/resolve", methods=["POST"])
def api_resolve_anomaly(anomaly_id: int):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    from app.intelligence.service import resolve_anomaly
    result = resolve_anomaly(anomaly_id=anomaly_id)
    return jsonify({"success": result})


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

@intelligence_bp.route("/confidence", methods=["POST"])
def api_confidence():
    """Compute confidence score from provided context."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    from app.intelligence.service import compute_confidence
    result = compute_confidence(data)
    return jsonify({"success": True, "data": result})