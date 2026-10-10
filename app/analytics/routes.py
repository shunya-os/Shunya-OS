"""SHUNYA System Analytics — dashboard data routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from flask import Blueprint, jsonify
from sqlalchemy import func

from app import db

analytics_bp = Blueprint("system_analytics", __name__, url_prefix="/api/v1/analytics")


@analytics_bp.route("/dashboard", methods=["GET"])
def dashboard():
    """
    GET /api/v1/analytics/dashboard

    Returns a system-wide analytics snapshot:
      - total_objects
      - total_relationships
      - total_documents
      - total_ai_queries
      - recent_activity (7-day timeline)
      - workspace_breakdown
      - top_ai_queries
    """
    from app.objects.models import Object
    from app.graph.models import ObjectRelation
    from app.document.models import DocumentRecord
    from app.observability.models import AIExecutionRecord
    from app.objects.legacy_models import Workspace

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    # ── Counts ──
    total_objects = db.session.query(func.count(Object.id)).scalar() or 0
    total_relationships = db.session.query(func.count(ObjectRelation.id)).scalar() or 0
    total_documents = db.session.query(func.count(DocumentRecord.id)).scalar() or 0
    total_ai_queries = db.session.query(func.count(AIExecutionRecord.id)).scalar() or 0

    # ── Recent activity (objects created in last 7 days, grouped by date) ──
    recent_rows = (
        db.session.query(
            func.date(Object.created_at).label("day"),
            func.count(Object.id).label("count"),
        )
        .filter(Object.created_at >= seven_days_ago)
        .group_by(func.date(Object.created_at))
        .order_by(func.date(Object.created_at))
        .all()
    )
    recent_activity: list[dict[str, Any]] = [
        {"date": str(row.day), "count": row.count} for row in recent_rows
    ]

    # ── Workspace breakdown ──
    try:
        ws_rows = (
            db.session.query(
                Workspace.workspace_type,
                func.count(Workspace.id).label("count"),
            )
            .group_by(Workspace.workspace_type)
            .all()
        )
        workspace_breakdown: list[dict[str, Any]] = [
            {"type": row.workspace_type or "unknown", "count": row.count}
            for row in ws_rows
        ]
    except Exception:
        workspace_breakdown = []

    # ── Top AI queries (by count) ──
    try:
        query_rows = (
            db.session.query(
                AIExecutionRecord.query_text,
                func.count(AIExecutionRecord.id).label("count"),
            )
            .filter(AIExecutionRecord.query_text.isnot(None))
            .filter(AIExecutionRecord.query_text != "")
            .group_by(AIExecutionRecord.query_text)
            .order_by(func.count(AIExecutionRecord.id).desc())
            .limit(10)
            .all()
        )
        top_ai_queries: list[dict[str, Any]] = [
            {"query": row.query_text[:100], "count": row.count}
            for row in query_rows
        ]
    except Exception:
        top_ai_queries = []

    return jsonify({
        "success": True,
        "data": {
            "total_objects": total_objects,
            "total_relationships": total_relationships,
            "total_documents": total_documents,
            "total_ai_queries": total_ai_queries,
            "recent_activity": recent_activity,
            "workspace_breakdown": workspace_breakdown,
            "top_ai_queries": top_ai_queries,
        },
    })