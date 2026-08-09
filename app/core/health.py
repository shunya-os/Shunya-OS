"""System Health endpoint — /system/health with real metrics.

PHASE 3: Returns DB connectivity + latency, integration status,
event processing lag, execution loop state.
"""

import logging
import threading
import time as _time

from flask import Blueprint, jsonify
from sqlalchemy import text

from app.core.db import get_session
from app.core.time import now

health_bp = Blueprint("system_health", __name__, url_prefix="/system")

logger = logging.getLogger(__name__)


@health_bp.route("/health", methods=["GET"])
def system_health():
    """Return system health status with real metrics."""
    result = {
        "status": "ok",
        "timestamp": now().isoformat(),
    }

    # DB connectivity + latency
    try:
        t0 = _time.monotonic()
        get_session().execute(text("SELECT 1"))
        db_latency_ms = round((_time.monotonic() - t0) * 1000, 2)
        result["db_connected"] = True
        result["db_latency_ms"] = db_latency_ms
    except Exception as e:
        result["db_connected"] = False
        result["db_latency_ms"] = None
        result["status"] = "degraded"
        logger.warning("Health check: DB connection failed: %s", e)

    # Integration status
    try:
        from app.integration.registry import registry
        ints = registry.list()
        result["integrations"] = {i["name"]: i["connected"] for i in ints}
        result["integration_token_valid"] = any(i["connected"] for i in ints)
    except Exception:
        result["integrations"] = {}
        result["integration_token_valid"] = False

    # Last event processed + processing lag
    try:
        from app.execution_log.models import ExecutionLog
        last = ExecutionLog.query.order_by(ExecutionLog.id.desc()).first()
        if last and last.timestamp:
            result["last_event_processed"] = last.timestamp.isoformat()
            lag_seconds = (now() - last.timestamp).total_seconds()
            result["event_processing_lag_s"] = round(max(0, lag_seconds), 1)
        else:
            result["last_event_processed"] = None
            result["event_processing_lag_s"] = None
    except Exception:
        result["last_event_processed"] = None
        result["event_processing_lag_s"] = None

    # Event queue backlog
    try:
        from app.communication.models import InboundEvent
        backlog = InboundEvent.query.filter_by(processed=False).count()
        result["event_queue_backlog"] = backlog
    except Exception:
        result["event_queue_backlog"] = 0

    # Execution loop state
    try:
        loop_threads = [t for t in threading.enumerate() if "shunya-loop" in t.name]
        result["execution_loop_active"] = len(loop_threads) > 0
    except Exception:
        result["execution_loop_active"] = False

    # Last successful sync
    try:
        from app.integration.registry import registry
        sync_times = [
            i.get("last_sync_at")
            for i in registry.list()
            if i.get("last_sync_at")
        ]
        result["last_successful_sync"] = max(sync_times) if sync_times else None
    except Exception:
        result["last_successful_sync"] = None

    return jsonify(result)