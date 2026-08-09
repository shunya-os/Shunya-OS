"""Awareness surface API — /api/v1/awareness, /api/v1/evidence, /api/v1/decisions.

PHASE 2C.2: Decision Intelligence.
All endpoints return structured, read-only intelligence data.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

awareness_bp = Blueprint("awareness", __name__, url_prefix="/api/v1")


@awareness_bp.route("/awareness", methods=["GET"])
def api_awareness():
    """Return awareness signals sorted by severity + recency.
    
    PHASE 2C.1: Read-only intelligence surface.
    Each signal includes type, severity, entity_id, reason, suggested_action, timestamp.
    """
    try:
        from app.intelligence.awareness import scan
        signals = scan()

        # Ensure each signal has a timestamp
        now = datetime.now(timezone.utc).isoformat()
        for s in signals:
            if "timestamp" not in s:
                s["timestamp"] = now

        # Sort: high > medium > low, then newest first
        severity_order = {"high": 0, "medium": 1, "low": 2}
        signals.sort(key=lambda s: (
            severity_order.get(s.get("severity", "low"), 9),
            -(s.get("timestamp") or ""),
        ))

        return jsonify({
            "signals": signals,
            "total": len(signals),
            "priorities": {
                "high": len([s for s in signals if s["severity"] == "high"]),
                "medium": len([s for s in signals if s["severity"] == "medium"]),
                "low": len([s for s in signals if s["severity"] == "low"]),
            },
        })
    except Exception as e:
        return jsonify({"signals": [], "total": 0, "priorities": {}, "error": str(e)})


@awareness_bp.route("/evidence", methods=["GET"])
def api_evidence():
    """Return evidence logs for a given entity or type.
    
    Query params:
        entity_id: int (optional)
        type: str (execution_summary|proposal|ai|awareness_signal)
        limit: int (default 20)
    """
    try:
        entity_id = request.args.get("entity_id", type=int)
        obs_type = request.args.get("type") or None
        limit = request.args.get("limit", 20, type=int)

        from app.cortex.state_log import query
        records = query(
            observation_type=obs_type,
            entity_id=entity_id,
            limit=limit,
        )
        return jsonify({"records": records, "total": len(records)})
    except Exception as e:
        return jsonify({"records": [], "total": 0, "error": str(e)})


@awareness_bp.route("/decisions", methods=["GET"])
def api_decisions():
    """Return computed decision intelligence from awareness signals.
    
    PHASE 2C.2: For each signal, generates a structured decision
    with next_best_action, priority_score, and impact.
    """
    try:
        from app.intelligence.decision_engine import compute_decisions
        decisions = compute_decisions()
        return jsonify({
            "decisions": decisions,
            "total": len(decisions),
        })
    except Exception as e:
        return jsonify({"decisions": [], "total": 0, "error": str(e)})