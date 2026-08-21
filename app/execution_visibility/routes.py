"""SHUNYA Execution Visibility — unified work/output API.

Surfaces real canonical execution data from:
- Outcome (app.execution.models) — user intentions and execution state
- Task (app.models.Task) — task items with status, assigned_to, due_date
- Commitment (app.commitments.models) — commitments and obligations
- DocumentRecord (app.document.models) — ingested documents
- CommercialProposal (app.commercial.models) — proposals with rendered outputs

No new models. No fake data. Reuses canonical architecture.
"""
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session, g

logger = logging.getLogger(__name__)

execution_visibility_bp = Blueprint(
    "execution_visibility", __name__, url_prefix="/api/v1/execution"
)


def _identity_id() -> str:
    return (
        g.get("identity_id")
        or session.get("identity_id")
        or session.get("user_id", "")
    )


def _org_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _require_auth() -> bool:
    return bool(_identity_id())


# ── Unified Work View ─────────────────────────────────────────────


@execution_visibility_bp.route("/work", methods=["GET"])
def list_work():
    """List all execution work from canonical sources.

    Surfaces outcomes, tasks, and commitments in a unified view.
    No fabricated data — only what exists in canonical DB.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    identity = _identity_id()
    org_id = _org_id()
    limit = request.args.get("limit", 50, type=int)

    work_items = []

    # 1. Outcomes — user intentions and execution state
    from app.execution.models import Outcome
    outcomes = (
        Outcome.query.filter_by(identity_id=identity)
        .order_by(Outcome.created_at.desc())
        .limit(limit)
        .all()
    )
    for o in outcomes:
        s = o.state or {}
        work_items.append({
            "id": o.outcome_id,
            "type": "outcome",
            "title": o.intention[:120] + ("..." if len(o.intention) > 120 else ""),
            "status": s.get("status", "accepted"),
            "progress": s.get("progress", None),
            "context": s.get("context", ""),
            "owner": "SHUNYA",
            "source": "request",
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            "result": s.get("result", ""),
            "error": s.get("error", ""),
            "drilldown": f"/api/v1/outcomes/{o.outcome_id}",
        })

    # 2. Tasks — individual task items
    from app.models import Task
    tasks = (
        Task.query.order_by(Task.created_at.desc())
        .limit(limit)
        .all()
    )
    for t in tasks:
        work_items.append({
            "id": f"task_{t.id}",
            "type": "task",
            "title": t.title,
            "status": t.status,
            "progress": 1.0 if t.status == "completed" else 0.5 if t.status == "in_progress" else 0.0,
            "context": t.description or "",
            "owner": t.assigned_to or "unassigned",
            "source": "task_list",
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "drilldown": f"/api/v1/people/tasks",
        })

    # 3. Commitments — obligations and commitments
    commitments = []
    try:
        from app.commitments.models import Commitment
        commitments = (
            Commitment.query.order_by(Commitment.created_at.desc())
            .limit(limit)
            .all()
        )
        for c in commitments:
            work_items.append({
                "id": f"cmt_{c.id}",
                "type": "commitment",
                "title": c.title,
                "status": c.status,
                "progress": c.progress or 0.0,
                "context": c.objective or "",
                "owner": c.owner or "SHUNYA",
                "source": "commitment",
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "drilldown": f"/api/v1/commitments/{c.id}",
            })
    except Exception:
        logger.debug("Commitment model not available", exc_info=True)

    # Sort by created_at descending, most recent first
    work_items.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    cmt_count = len(commitments) if 'commitments' in dir() and commitments else 0

    return jsonify({
        "success": True,
        "data": {
            "total": len(work_items),
            "items": work_items[:limit],
            "summary": {
                "total_outcomes": len(outcomes),
                "total_tasks": len(tasks),
                "total_commitments": cmt_count,
            },
        },
    })


# ── Output / Artifact Discovery ────────────────────────────────────


@execution_visibility_bp.route("/outputs", methods=["GET"])
def list_outputs():
    """List all outputs/artifacts from canonical sources.

    Surfaces: documents, proposals (with rendered artifacts), outcomes with results.
    No fabricated data — only what exists in canonical DB.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    org_id = _org_id()
    limit = request.args.get("limit", 50, type=int)
    outputs = []

    # 1. Documents — ingested through DocumentService
    try:
        from app.document.models import DocumentRecord
        docs = (
            DocumentRecord.query.order_by(DocumentRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        for d in docs:
            outputs.append({
                "id": f"doc_{d.id}",
                "type": "document",
                "title": d.safe_display_name or d.original_filename or f"Document #{d.id}",
                "description": d.classification or "",
                "status": d.lifecycle or "received",
                "source": "ingestion",
                "mime_type": d.mime_type or "",
                "file_size": d.file_size or 0,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "drilldown": f"/api/v1/documents/{d.id}",
            })
    except Exception:
        logger.debug("Document model not available", exc_info=True)

    # 2. Proposals — commercial proposals with rendered output
    try:
        from app.commercial.models import CommercialProposal
        proposals = (
            CommercialProposal.query.order_by(CommercialProposal.created_at.desc())
            .limit(limit)
            .all()
        )
        for p in proposals:
            artifact_exists = bool(p.rendered_pdf_path or p.rendered_html)
            outputs.append({
                "id": f"prop_{p.id}",
                "type": "proposal",
                "title": p.title,
                "description": p.scope_description or "",
                "status": p.status,
                "source": "commercial",
                "value": float(p.total_value or 0),
                "currency": p.currency or "USD",
                "has_artifact": artifact_exists,
                "artifact_path": p.rendered_pdf_path or "",
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "drilldown": f"/api/v1/commercial/proposals/{p.id}",
            })
    except Exception:
        logger.debug("Proposal model not available", exc_info=True)

    # 3. Outcomes with results — completed outcomes that produced output
    from app.execution.models import Outcome
    identity = _identity_id()
    outcomes = (
        Outcome.query.filter_by(identity_id=identity)
        .order_by(Outcome.updated_at.desc())
        .limit(limit)
        .all()
    )
    for o in outcomes:
        s = o.state or {}
        result = s.get("result", "")
        if result and len(result) > 20:
            outputs.append({
                "id": f"out_{o.outcome_id}",
                "type": "execution_result",
                "title": o.intention[:120],
                "description": result[:300],
                "status": "completed",
                "source": "execution",
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "drilldown": f"/api/v1/outcomes/{o.outcome_id}",
            })

    # Sort by created_at desc
    outputs.sort(key=lambda x: x.get("created_at") or "", reverse=True)

    return jsonify({
        "success": True,
        "data": {
            "total": len(outputs),
            "items": outputs[:limit],
        },
    })