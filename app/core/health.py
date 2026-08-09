"""System Health endpoint — /system/health

PHASE 3: Returns DB connectivity, integration status, last event, execution loop state.
"""

from flask import Blueprint, jsonify
from datetime import datetime, timezone

health_bp = Blueprint("system_health", __name__, url_prefix="/system")


@health_bp.route("/health", methods=["GET"])
def system_health():
    """Return system health status."""
    result = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # DB connectivity
    try:
        from app.core.db import db
        db.session.execute(db.text("SELECT 1"))
        result["db_connected"] = True
    except Exception:
        result["db_connected"] = False
        result["status"] = "degraded"

    # Integration status
    try:
        from app.integration.registry import registry
        ints = registry.list()
        result["integrations"] = {i["name"]: i["connected"] for i in ints}
    except Exception:
        result["integrations"] = {}

    # Last event processed
    try:
        from app.execution_log.models import ExecutionLog
        last = ExecutionLog.query.order_by(ExecutionLog.id.desc()).first()
        result["last_event_processed"] = last.timestamp.isoformat() if last else None
    except Exception:
        result["last_event_processed"] = None

    # Execution loop state
    try:
        # Check if the background thread is alive
        import threading
        loop_threads = [t for t in threading.enumerate() if "shunya-loop" in t.name]
        result["execution_loop_active"] = len(loop_threads) > 0
    except Exception:
        result["execution_loop_active"] = False

    return jsonify(result)