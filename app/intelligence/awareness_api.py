"""Awareness surface API — /api/v1/awareness, /api/v1/evidence, /api/v1/decisions.

PHASE 2C.2: Decision Intelligence.
All endpoints return structured, read-only intelligence data.
"""

from app.core.time import now

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
        now = now().isoformat()
        for s in signals:
            if "timestamp" not in s:
                s["timestamp"] = now

        # Sort: high > medium > low, then newest first (ISO strings compare correctly)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        signals.sort(key=lambda s: (
            severity_order.get(s.get("severity", "low"), 9),
            s.get("timestamp", "") or "",
        ), reverse=True)

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


@awareness_bp.route("/debug/state", methods=["GET"])
def api_debug_state():
    """Return system state counts and consistency verification.
    
    Returns:
        total_objects, total_proposals, total_execution_logs,
        total_awareness_signals, state_consistent flag.
    """
    try:
        from app.objects.models import Object
        from app.communication.models import MessageProposal
        from app.execution_log.models import ExecutionLog
        from app.intelligence.awareness import scan

        obj_count = Object.query.count()
        prop_count = MessageProposal.query.count()
        log_count = ExecutionLog.query.count()

        signals = scan()
        sig_count = len(signals)

        # Consistency verification
        # Expected: awareness count should be close to idle entities + failed cycles
        # Any large discrepancy indicates a session/connection issue
        state_consistent = True
        consistency_notes = []

        if obj_count == 0 and sig_count > 0:
            state_consistent = False
            consistency_notes.append("signals exist without objects — stale cache")
        if prop_count > 0 and sig_count == 0:
            state_consistent = False
            consistency_notes.append("proposals exist but no awareness signals — possible connection isolation")

        return jsonify({
            "total_objects": obj_count,
            "total_proposals": prop_count,
            "total_execution_logs": log_count,
            "total_awareness_signals": sig_count,
            "state_consistent": state_consistent,
            "consistency_notes": consistency_notes,
            "warning": "SQLite in-memory databases are per-connection. Use PostgreSQL for multi-connection consistency.",
        })
    except Exception as e:
        return jsonify({
            "total_objects": 0,
            "total_proposals": 0,
            "total_execution_logs": 0,
            "total_awareness_signals": 0,
            "state_consistent": False,
            "consistency_notes": [str(e)],
            "error": str(e),
        })

@awareness_bp.route("/decision-trace/<int:object_id>", methods=["GET"])
def api_decision_trace(object_id):
    """Return decision traces for a specific object."""
    try:
        from app.evidence.decision_trace import get_decision_traces
        traces = get_decision_traces(object_id=object_id, limit=20)
        return jsonify({"traces": traces, "total": len(traces)})
    except Exception as e:
        return jsonify({"traces": [], "total": 0, "error": str(e)})


@awareness_bp.route("/decision-trace", methods=["GET"])
def api_decision_traces_all():
    """Return all recent decision traces."""
    try:
        from app.evidence.decision_trace import get_decision_traces
        traces = get_decision_traces(limit=50)
        return jsonify({"traces": traces, "total": len(traces)})
    except Exception as e:
        return jsonify({"traces": [], "total": 0, "error": str(e)})


@awareness_bp.route("/ingest/gmail", methods=["POST"])
def api_ingest_gmail():
    """Trigger Gmail ingestion via canonical GmailAdapter pipeline.

    Uses the canonical GmailAdapter registered with IntegrationRegistry.
    Identity → evidence → decision pipeline.
    """
    try:
        from app.integration.gmail_adapter import GmailAdapter
        body = request.get_json(silent=True) or {}
        max_results = body.get("max_results", 100)

        adapter = GmailAdapter()
        summary = adapter.ingest_emails(max_results=max_results)
        return jsonify({
            "status": "ok",
            "summary": summary,
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


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