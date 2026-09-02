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
    from app.authz.decorators import _resolve_org_id
    tenant_id = _resolve_org_id()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 400
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


@execution_bp.route("/work", methods=["GET"])
def list_work_items():
    """Return execution work items for the ExecutionWorkspace component.

    Provides a unified view of outcomes, tasks, and commitments with
    summary counts. Returned shape matches the WorkItem interface:

      { success: true, data: { items: WorkItem[], summary: { total_outcomes, total_tasks, total_commitments } } }

    Each WorkItem:
      id, type (outcome|task|commitment), title, status, progress,
      owner, source, priority, due_date, created_at, updated_at,
      completed_at, result, error, drilldown
    """
    from datetime import datetime, timezone
    from app import db
    from app.execution.models import Outcome
    from app.models import Task
    from app.commitments.models import Commitment

    from app.authz.decorators import _resolve_org_id
    tenant_id = _resolve_org_id()
    if not tenant_id:
        return jsonify({"success": False, "error": "No organization context"}), 400
    items: list[dict] = []

    # 1. Outcomes
    outcomes = Outcome.query.filter(
        Outcome.identity_id == str(tenant_id)
    ).order_by(Outcome.created_at.desc()).limit(50).all()
    for o in outcomes:
        state = o.state or {}
        stage = state.get("stage", "pending")
        status = "completed" if stage == "completed" else "failed" if stage == "failed" else "active" if stage == "accepted" else stage
        items.append({
            "id": o.outcome_id,
            "type": "outcome",
            "title": o.intention or f"Outcome {o.outcome_id[:12]}",
            "status": status,
            "progress": 1.0 if status == "completed" else 0.5 if status == "active" else 0.0,
            "context": state.get("context", ""),
            "owner": state.get("owner", "system"),
            "source": "execution",
            "priority": state.get("priority", "medium"),
            "due_date": None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            "completed_at": None,
            "result": state.get("result", ""),
            "error": state.get("error", ""),
            "drilldown": f"/api/v1/outcomes/{o.outcome_id}",
        })

    # 2. Tasks
    tasks = Task.query.order_by(Task.created_at.desc()).limit(50).all()
    for t in tasks:
        items.append({
            "id": f"task_{t.id}",
            "type": "task",
            "title": t.title,
            "status": t.status,
            "progress": 1.0 if t.status == "completed" else 0.5 if t.status == "in_progress" else 0.0,
            "context": "",
            "owner": t.assigned_to or "unassigned",
            "source": "workspace",
            "priority": t.priority or "medium",
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "result": "",
            "error": "",
            "drilldown": f"/api/v1/tasks/{t.id}",
        })

    # 3. Commitments
    commitments = Commitment.query.order_by(Commitment.created_at.desc()).limit(50).all()
    for c in commitments:
        meta = c.meta or {}
        items.append({
            "id": f"cmt_{c.id}",
            "type": "commitment",
            "title": c.title,
            "status": c.status,
            "progress": 1.0 if c.status == "completed" else 0.5 if c.status == "in_progress" else 0.0,
            "context": meta.get("context", ""),
            "owner": c.owner or "system",
            "source": "decision",
            "priority": meta.get("priority", "medium"),
            "due_date": c.due_at.isoformat() if c.due_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "completed_at": None,
            "result": "",
            "error": "",
            "drilldown": f"/api/v1/commitments/{c.id}",
        })

    # Sort by created_at desc, then by id-based fallback
    def _sort_key(item):
        ts = item.get("created_at")
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError):
                pass
        return 0

    items.sort(key=_sort_key, reverse=True)

    summary = {
        "total_outcomes": len(outcomes),
        "total_tasks": len(tasks),
        "total_commitments": len(commitments),
    }

    return jsonify({
        "success": True,
        "data": {
            "items": items[:100],
            "summary": summary,
        }
    })