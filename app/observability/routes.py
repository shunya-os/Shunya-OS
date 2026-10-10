"""Observability API — record and query AI execution traces.

G3 Phase 7.2.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app import db
from app.observability.models import AIExecutionRecord

observability_bp = Blueprint("observability", __name__, url_prefix="/api/v1/observability")

logger = logging.getLogger(__name__)


def record_execution(
    request_id: str = "",
    session_id: str = "",
    query: str = "",
    action_class: str = "",
    provider: str = "",
    model: str = "",
    latency_ms: float = 0.0,
    confidence: float = 0.0,
    evidence_count: int = 0,
    error: str = "",
) -> AIExecutionRecord | None:
    """Persist an AI execution record to the database.

    Safe to call from anywhere — wraps all DB ops in try/except.
    Returns the created record on success, None on failure.
    """
    try:
        record = AIExecutionRecord(
            request_id=request_id or str(uuid.uuid4()),
            session_id=session_id or "",
            query=(query or "")[:2000],
            action_class=action_class or "",
            provider=provider or "",
            model=model or "",
            latency_ms=latency_ms,
            confidence=confidence,
            evidence_count=evidence_count,
            error=(error or "")[:500],
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(record)
        db.session.commit()
        return record
    except Exception as exc:
        logger.warning("Failed to record AI execution: %s", exc)
        db.session.rollback()
        return None


# ── Routes ─────────────────────────────────────────────────────────────────


@observability_bp.route("/record", methods=["POST"])
def api_record_execution():
    """POST /api/v1/observability/record — record an AI execution.

    Body (JSON):
      request_id (str)  — optional, auto-generated if omitted
      session_id (str)
      query (str)
      action_class (str)
      provider (str)
      model (str)
      latency_ms (float)
      confidence (float)
      evidence_count (int)
      error (str)
    """
    data = request.get_json(silent=True) or {}
    record = record_execution(
        request_id=data.get("request_id", ""),
        session_id=data.get("session_id", ""),
        query=data.get("query", ""),
        action_class=data.get("action_class", ""),
        provider=data.get("provider", ""),
        model=data.get("model", ""),
        latency_ms=float(data.get("latency_ms", 0)),
        confidence=float(data.get("confidence", 0)),
        evidence_count=int(data.get("evidence_count", 0)),
        error=data.get("error", ""),
    )
    if record is None:
        return jsonify({"success": False, "error": "Failed to persist record"}), 500
    return jsonify({"success": True, "record": record.to_dict()}), 201


@observability_bp.route("/history", methods=["GET"])
def api_list_history():
    """GET /api/v1/observability/history — list recent execution records.

    Query params:
      limit (int, default 50) — max records to return
      session_id (str)        — optional filter by session
    """
    limit = min(int(request.args.get("limit", 50)), 200)
    session_id = request.args.get("session_id", "")

    try:
        q = AIExecutionRecord.query.order_by(AIExecutionRecord.id.desc())
        if session_id:
            q = q.filter(AIExecutionRecord.session_id == session_id)
        records = q.limit(limit).all()
        return jsonify({
            "success": True,
            "count": len(records),
            "records": [r.to_dict() for r in records],
        })
    except Exception as exc:
        logger.warning("Failed to query execution history: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500