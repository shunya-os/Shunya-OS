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
from app.authz.decorators import require_permission

logger = logging.getLogger(__name__)

calendar_bp = Blueprint("calendar_api", __name__, url_prefix="/api/v1/calendar")


def _identity_id() -> str:
    return (g.get("identity_id") or session.get("identity_id") or session.get("user_id", ""))


def _require_auth() -> bool:
    return bool(_identity_id())


@calendar_bp.route("/events", methods=["GET"])
@require_permission("task.view")
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
    from app.authz.decorators import _resolve_org_id

    tenant_id = _resolve_org_id()
    events = []

    # 1. Commitments — tenant-scoped through the canonical relationship or
    #    campaign ownership (a commitment with neither is not org-provable
    #    and is excluded — fail closed).
    try:
        from app.commitments.models import Commitment
        from app.relationship.models import CanonicalRelationship
        from app.marketing.models import Campaign
        commitments_query = db.session.query(Commitment)
        if tenant_id:
            commitments_query = commitments_query.outerjoin(
                CanonicalRelationship,
                CanonicalRelationship.id == Commitment.relationship_id,
            ).outerjoin(
                Campaign, Campaign.id == Commitment.campaign_id,
            ).filter(
                db.or_(
                    CanonicalRelationship.organization_id == int(tenant_id),
                    Campaign.tenant_id == int(tenant_id),
                )
            )
        else:
            commitments_query = None
        commitments = commitments_query.filter(
            Commitment.due_at >= start,
            Commitment.due_at <= end,
        ).order_by(Commitment.due_at.asc()).limit(limit).all() if commitments_query else []
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