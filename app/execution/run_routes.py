"""Execution Run + Task Lifecycle API routes.

Canonical end-to-end execution visibility:
- GET  /api/v1/execution/runs                 — list runs (org-scoped)
- GET  /api/v1/execution/runs/<execution_id>  — run detail w/ transitions
- POST /api/v1/execution/runs                 — create a run (task.create)
- POST /api/v1/execution/runs/<execution_id>/transition — advance phase
- POST /api/v1/execution/runs/<execution_id>/complete   — complete a run
- POST /api/v1/execution/runs/<execution_id>/fail       — fail a run
- GET  /api/v1/execution/tasks                — recent task lifecycles
- GET  /api/v1/execution/tasks/active         — active tasks
- GET  /api/v1/execution/tasks/attention      — tasks needing intervention
- GET  /api/v1/execution/tasks/<task_id>      — task detail (lifecycle)

Truthfulness rule: every response reflects persisted state. No fake
phases, no simulated progress.
"""
import logging
import uuid

from flask import Blueprint, g, jsonify, request

from app.authz.decorators import require_permission
from app.execution.run_service import get_run_service, RunServiceError

logger = logging.getLogger(__name__)

runs_bp = Blueprint("execution_runs", __name__, url_prefix="/api/v1/execution")


def _org_id() -> int:
    """Resolve the current organization id from the trusted context."""
    org_id = getattr(g, "current_org_id", None)
    if org_id:
        return int(org_id)
    from app.authz.decorators import _resolve_org_id
    resolved = _resolve_org_id()
    if not resolved:
        return 0  # deny-by-default: callers must check
    return int(resolved)


def _identity() -> str:
    return getattr(g, "identity_id", "") or ""


def _identity_int() -> int | None:
    """Resolve the current identity as an integer (shunya_identities.id), if possible."""
    raw = getattr(g, "identity_id", "") or ""
    if raw and str(raw).isdigit():
        return int(raw)
    # Fallback: try to resolve via session identity
    from flask import session
    sid = session.get("identity_id") or ""
    if str(sid).isdigit():
        return int(sid)
    return None


def _require_org(org_id: int):
    if not org_id:
        return jsonify({"success": False, "error": "No organization context"}), 400
    return None


# ── Runs ──────────────────────────────────────────────────────────────


@runs_bp.route("/runs", methods=["GET"])
@require_permission("task.view")
def list_runs():
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    limit = request.args.get("limit", 20, type=int)
    status = request.args.get("status", "").strip() or None
    service = get_run_service()
    runs = service.get_runs(org_id, limit=limit, status=status)
    return jsonify({"success": True, "data": [r.to_dict() for r in runs]})


@runs_bp.route("/runs/<execution_id>", methods=["GET"])
def get_run(execution_id: str):
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    service = get_run_service()
    run = service.get_run(execution_id)
    if not run or run.organization_id != org_id:
        return jsonify({"success": False, "error": "Run not found"}), 404
    return jsonify({"success": True, "data": run.to_dict(include_transitions=True)})


@runs_bp.route("/runs", methods=["POST"])
@require_permission("task.create")
def create_run():
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    intent = (data.get("intent") or "").strip()
    if not intent:
        return jsonify({"success": False, "error": "intent is required"}), 400
    service = get_run_service()
    run = service.create_run(
        organization_id=org_id,
        identity_id=_identity_int(),
        intent=intent,
        run_type=data.get("run_type", "task"),
        source=data.get("source", "user"),
        correlation_id=data.get("correlation_id") or str(uuid.uuid4()),
        commitment_id=data.get("commitment_id"),
        commitment_type=data.get("commitment_type"),
    )
    return jsonify({"success": True, "data": run.to_dict()}), 201


@runs_bp.route("/runs/<execution_id>/transition", methods=["POST"])
@require_permission("task.edit")
def transition_run(execution_id: str):
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    phase = (data.get("phase") or "").strip()
    if not phase:
        return jsonify({"success": False, "error": "phase is required"}), 400
    service = get_run_service()
    run = service.transition(execution_id, phase, reason=data.get("reason", ""))
    if not run or run.organization_id != org_id:
        return jsonify({"success": False, "error": "Run not found"}), 404
    return jsonify({"success": True, "data": run.to_dict()})


@runs_bp.route("/runs/<execution_id>/complete", methods=["POST"])
@require_permission("task.edit")
def complete_run(execution_id: str):
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    service = get_run_service()
    run = service.complete(
        execution_id,
        result=data.get("result"),
        summary=data.get("summary"),
    )
    if not run or run.organization_id != org_id:
        return jsonify({"success": False, "error": "Run not found"}), 404
    return jsonify({"success": True, "data": run.to_dict()})


@runs_bp.route("/runs/<execution_id>/fail", methods=["POST"])
@require_permission("task.edit")
def fail_run(execution_id: str):
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    service = get_run_service()
    run = service.fail(execution_id, error=data.get("error", ""))
    if not run or run.organization_id != org_id:
        return jsonify({"success": False, "error": "Run not found"}), 404
    return jsonify({"success": True, "data": run.to_dict()})


# ── Task Lifecycle ────────────────────────────────────────────────────


@runs_bp.route("/tasks", methods=["GET"])
def list_tasks():
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    limit = request.args.get("limit", 20, type=int)
    service = get_run_service()
    tasks = service.get_recent_tasks(org_id, limit=limit)
    return jsonify({"success": True, "data": [t.to_dict() for t in tasks]})


@runs_bp.route("/tasks/active", methods=["GET"])
def list_active_tasks():
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    service = get_run_service()
    tasks = service.get_active_tasks(org_id)
    return jsonify({"success": True, "data": [t.to_dict() for t in tasks]})


@runs_bp.route("/tasks/attention", methods=["GET"])
def list_attention_tasks():
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    service = get_run_service()
    tasks = service.get_tasks_needing_attention(org_id)
    return jsonify({"success": True, "data": [t.to_dict() for t in tasks]})


@runs_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id: str):
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    service = get_run_service()
    task = service.get_task(task_id)
    if not task or task.organization_id != org_id:
        return jsonify({"success": False, "error": "Task not found"}), 404
    return jsonify({"success": True, "data": task.to_dict()})


@runs_bp.route("/tasks", methods=["POST"])
@require_permission("task.create")
def create_task():
    org_id = _org_id()
    blocked = _require_org(org_id)
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400
    service = get_run_service()
    try:
        task = service.create_task(
            organization_id=org_id,
            identity_id=_identity_int(),
            title=title,
            description=data.get("description", ""),
            execution_run_id=data.get("execution_run_id"),
        )
    except RunServiceError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    return jsonify({"success": True, "data": task.to_dict()}), 201