"""Execution Engine routes — B8/CG-05: Output visibility endpoint.

Provides /api/v1/execution/outputs for the OutputsBrowser component.
Aggregates documents, proposals, and execution results into a unified
output feed linked to execution context.
"""

from flask import Blueprint, jsonify, request
from app import db
from app.models import Proposal
from app.execution_log.models import ExecutionLog

execution_bp = Blueprint("execution_engine", __name__, url_prefix="/api/v1/execution")


@execution_bp.route("/outputs", methods=["GET"])
def list_outputs():
    """Return aggregated output items for the OutputsBrowser.

    Sources:
      - Proposals (from commercial pipeline)
      - ExecutionLog entries with output-producing event types
      - Documents stored as Objects with document-like type

    Returns:
      { "success": true, "data": { "items": [...] } }
    """
    tenant_id = request.args.get("tenant_id", 1, type=int)
    items = []

    # 1. Proposals
    proposals = Proposal.query.filter(
        Proposal.organization_id == tenant_id
    ).order_by(Proposal.id.desc()).limit(50).all()
    for p in proposals:
        items.append({
            "id": f"prop_{p.id}",
            "type": "proposal",
            "title": p.title or f"Proposal #{p.id}",
            "description": f"Budget: {p.currency} {p.budget} — Status: {p.status}",
            "status": p.status,
            "source": "commercial",
            "value": float(p.budget) if p.budget else 0,
            "currency": p.currency or "INR",
            "has_artifact": False,
            "created_at": getattr(p, "created_at", None) or getattr(p, "created", None),
        })

    # 2. ExecutionLog output events
    output_events = ExecutionLog.query.filter(
        ExecutionLog.event_type.in_(["output_generated", "document_created", "result_produced"])
    ).order_by(ExecutionLog.timestamp.desc()).limit(50).all()
    for log in output_events:
        payload = log.payload or {}
        items.append({
            "id": f"exec_{log.id}",
            "type": "execution_result",
            "title": payload.get("title", f"Execution Output #{log.id}"),
            "description": payload.get("summary", f"Event: {log.event_type}"),
            "status": payload.get("status", "completed"),
            "source": payload.get("source", "execution"),
            "mime_type": payload.get("mime_type", ""),
            "file_size": payload.get("file_size", 0),
            "has_artifact": bool(payload.get("artifact_path")),
            "artifact_path": payload.get("artifact_path", ""),
            "created_at": log.timestamp.isoformat() if log.timestamp else None,
            "drilldown": f"/api/v1/execution/logs/{log.object_id}",
        })

    # 3. Documents (via Object model — type='document' in objects table)
    from app.objects.models import Object as ShunyaObject
    docs = ShunyaObject.query.filter(
        ShunyaObject.tenant_id == tenant_id,
        ShunyaObject.type.in_(["document", "report", "file", "note"])
    ).order_by(ShunyaObject.id.desc()).limit(50).all()
    for doc in docs:
        state = doc.state or {}
        items.append({
            "id": f"doc_{doc.id}",
            "type": "document",
            "title": state.get("title") or state.get("name") or f"Document #{doc.id}",
            "description": state.get("description", ""),
            "status": state.get("status", "ready"),
            "source": "workspace",
            "mime_type": state.get("mime_type", ""),
            "file_size": state.get("file_size", 0),
            "has_artifact": bool(state.get("file_path")),
            "artifact_path": state.get("file_path", ""),
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        })

    # Sort by most recent first (items with created_at first, then by id desc)
    def _sort_key(item):
        ts = item.get("created_at")
        if ts:
            try:
                from datetime import datetime
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError):
                pass
        # Fallback: extract numeric id
        raw_id = item.get("id", "")
        num = raw_id.split("_")[-1] if "_" in raw_id else raw_id
        try:
            return float(num)
        except (ValueError, TypeError):
            return 0

    items.sort(key=_sort_key, reverse=True)

    return jsonify({
        "success": True,
        "data": {
            "items": items[:100],
            "total": len(items),
        }
    })