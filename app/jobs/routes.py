"""Job Manager API routes — REST endpoints for background operation tracking."""
from flask import Blueprint, jsonify, request, session
from app.jobs.manager import create_job, get_job, list_jobs, cancel_job, pause_job, resume_job, retry_job, count_active_jobs
from app.authz.decorators import require_permission

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/v1/jobs")


def _founder_required() -> bool:
    return bool(session.get("identity_id"))


@jobs_bp.route("", methods=["GET"])
@require_permission("admin.manage_integrations")
def api_list_jobs():
    """List all jobs, optionally filtered by category or status."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    category = request.args.get("category")
    status = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    jobs = list_jobs(category=category, status=status, limit=limit)
    active = count_active_jobs()
    return jsonify({"success": True, "data": jobs, "active_count": active})


@jobs_bp.route("/<job_id>", methods=["GET"])
@require_permission("admin.manage_integrations")
def api_get_job(job_id: str):
    """Get a single job by ID."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    job = get_job(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    return jsonify({"success": True, "data": job.to_dict()})


@jobs_bp.route("/<job_id>/cancel", methods=["POST"])
@require_permission("admin.manage_integrations")
def api_cancel_job(job_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    ok = cancel_job(job_id)
    return jsonify({"success": ok, "error": None if ok else "Job not found"})


@jobs_bp.route("/<job_id>/pause", methods=["POST"])
@require_permission("admin.manage_integrations")
def api_pause_job(job_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    ok = pause_job(job_id)
    return jsonify({"success": ok, "error": None if ok else "Job not found"})


@jobs_bp.route("/<job_id>/resume", methods=["POST"])
@require_permission("admin.manage_integrations")
def api_resume_job(job_id: str):
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    ok = resume_job(job_id)
    return jsonify({"success": ok, "error": None if ok else "Job not found"})


@jobs_bp.route("/active-count", methods=["GET"])
@require_permission("admin.manage_integrations")
def api_active_count():
    """Quick endpoint for the logout safety check."""
    if not _founder_required():
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    return jsonify({"success": True, "active_count": count_active_jobs()})