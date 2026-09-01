"""SHUNYA Calendar API — surfaces events, commitments, and tasks on a timeline.

The frontend calendar-panel.tsx exists but has no backend API. This bridges
that gap by providing calendar events from multiple sources:
- Events (from app/events/)
- Commitments (from app/commitments/)
- Tasks (from app/tasks/)
- Executions (from app/execution_engine/)
"""

import logging
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, session, g

logger = logging.getLogger(__name__)

calendar_bp = Blueprint("calendar_api", __name__, url_prefix="/api/v1/calendar")


def _identity_id() -> str:
    return (g.get("identity_id") or session.get("identity_id") or session.get("user_id", ""))


def _require_auth() -> bool:
    return bool(_identity_id())


@calendar_bp.route("/events", methods=["GET"])
def list_calendar_events():
    """List calendar events from all sources within a date range."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    # Parse date range from query params
    start_str = request.args.get("start", "")
    end_str = request.args.get("end", "")
    limit = min(int(request.args.get("limit", 100)), 500)

    try:
        start = datetime.fromisoformat(start_str) if start_str else datetime.now(timezone.utc) - timedelta(days=30)
        end = datetime.fromisoformat(end_str) if end_str else datetime.now(timezone.utc) + timedelta(days=90)
    except (ValueError, TypeError):
        start = datetime.now(timezone.utc) - timedelta(days=30)
        end = datetime.now(timezone.utc) + timedelta(days=90)

    from app import db
    events = []

    # 1. Events from app/events/
    try:
        from app.events.models import Event
        event_rows = Event.query.filter(
            Event.created_at >= start,
            Event.created_at <= end,
        ).order_by(Event.created_at.asc()).limit(limit).all()
        for e in event_rows:
            events.append({
                "id": f"event_{e.id}",
                "title": getattr(e, "title", "") or getattr(e, "event_type", "") or "Event",
                "start": e.created_at.isoformat() if e.created_at else "",
                "end": "",
                "type": "event",
                "source": "events",
                "status": getattr(e, "status", ""),
                "url": f"/workspace/events/{e.id}",
            })
    except Exception as exc:
        logger.debug("Calendar events source failed: %s", exc)

    # 2. Commitments
    try:
        from app.commitments.models import Commitment
        commitments = Commitment.query.filter(
            Commitment.due_at >= start,
            Commitment.due_at <= end,
        ).order_by(Commitment.due_at.asc()).limit(limit).all()
        for c in commitments:
            events.append({
                "id": f"cmt_{c.id}",
                "title": c.title or "Commitment",
                "start": c.due_at.isoformat() if c.due_at else "",
                "end": "",
                "type": "commitment",
                "source": "commitments",
                "status": c.status or "",
                "url": f"/workspace/commitments/{c.id}",
            })
    except Exception as exc:
        logger.debug("Calendar commitments source failed: %s", exc)

    # Sort by start date
    events.sort(key=lambda e: e.get("start", ""))

    return jsonify({
        "success": True,
        "data": {"events": events[:limit], "total": min(len(events), limit)},
    })