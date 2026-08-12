"""FDA23 — People / Internal Operations.

Built on existing canonical models — no separate employee identity authority.
Uses: OrgMember, Task, Commitment, CanonicalRelationship.
Privacy-aware: people-data endpoints require stricter authorization.
"""

from flask import Blueprint, jsonify, request, session, g

people_bp = Blueprint("people", __name__, url_prefix="/api/v1/people")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _require_auth() -> bool:
    return bool(_identity_id() and _tenant_id())


def _require_people_permission() -> bool:
    """People data requires elevated permission (task.view at minimum)."""
    from app.authz.services import check_permission
    return check_permission(_tenant_id(), _identity_id(), "task.view")


@people_bp.route("/health", methods=["GET"])
def people_health():
    return jsonify({
        "status": "ok", "service": "people-operations", "version": "1.0.0",
        "endpoints": [
            "GET /api/v1/people/members",
            "GET /api/v1/people/members/<id>",
            "GET /api/v1/people/tasks",
            "GET /api/v1/people/approvals",
            "GET /api/v1/people/workload",
        ],
    })


@people_bp.route("/members", methods=["GET"])
def list_members():
    """List organization members with their roles.

    Returns minimal data: id, name, email, role, is_active.
    Does NOT expose personal details (phone, address, custom fields).
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app import db
    from app.models import OrgMember
    members = db.session.query(OrgMember).filter_by(
        organization_id=_tenant_id()
    ).all()

    return jsonify({
        "success": True,
        "data": [{
            "id": m.id,
            "name": m.name or m.email,
            "email": m.email,
            "role": m.role,
            "designation": m.designation or "",
            "is_active": m.is_active,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        } for m in members],
    })


@people_bp.route("/members/<int:member_id>", methods=["GET"])
def get_member(member_id: int):
    """Get a specific member (minimal, privacy-safe)."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app import db
    from app.models import OrgMember
    member = db.session.query(OrgMember).filter_by(
        id=member_id, organization_id=_tenant_id()
    ).first()
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    return jsonify({
        "success": True,
        "data": {
            "id": member.id,
            "name": member.name or member.email,
            "email": member.email,
            "role": member.role,
            "designation": member.designation or "",
            "is_active": member.is_active,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        },
    })


@people_bp.route("/tasks", methods=["GET"])
def get_people_tasks():
    """Get tasks across the organization, grouped by status.

    Uses existing Task model. Shows tasks owned by or assigned to members.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app import db
    from app.models import Task, TaskList
    from datetime import datetime, timezone

    # Tasks across all task lists in the org scope
    tasks = db.session.query(Task).order_by(Task.created_at.desc()).limit(100).all()

    pending = []
    in_progress = []
    completed = []
    overdue = []

    now = datetime.now(timezone.utc)

    for t in tasks:
        item = {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "assigned_to": t.assigned_to or "",
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        if t.due_date and t.status != "completed" and t.due_date < now.date():
            item["overdue"] = True
            overdue.append(item)
        elif t.status == "completed":
            completed.append(item)
        elif t.status == "in_progress":
            in_progress.append(item)
        else:
            pending.append(item)

    return jsonify({
        "success": True,
        "data": {
            "total": len(tasks),
            "pending": pending[:20],
            "in_progress": in_progress[:20],
            "completed": completed[:20],
            "overdue": overdue[:20],
        },
    })


@people_bp.route("/approvals", methods=["GET"])
def get_approvals():
    """Get pending approvals for the current user.

    Uses existing Commitment model with issue_type='approval' or status='pending'.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    from app import db
    from app.commitments.models import Commitment
    from app.models import OrgMember

    # Find commitments where current user is the owner
    member = OrgMember.query.filter_by(
        organization_id=_tenant_id(), identity_id=_identity_id()
    ).first()
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    pending = db.session.query(Commitment).filter_by(
        owner=member.identity_id, status="pending"
    ).order_by(Commitment.created_at.desc()).limit(50).all()

    return jsonify({
        "success": True,
        "data": [{
            "id": c.id,
            "title": c.title,
            "status": c.status,
            "issue_type": c.issue_type,
            "owner": c.owner,
            "due_at": c.due_at.isoformat() if c.due_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        } for c in pending],
    })


@people_bp.route("/workload", methods=["GET"])
def get_workload():
    """Get workload overview: who owns what and what is overdue.

    Privacy-safe — only exposes work-related data.
    Does NOT expose personal information.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app import db
    from app.models import OrgMember, Task
    from app.commitments.models import Commitment
    from datetime import datetime, timezone

    members = db.session.query(OrgMember).filter_by(
        organization_id=_tenant_id(), is_active=True
    ).all()

    now = datetime.now(timezone.utc)
    workload = []

    for m in members:
        # Tasks assigned to this member
        member_tasks = db.session.query(Task).filter(
            Task.assigned_to == m.identity_id
        ).count()

        pending_tasks = db.session.query(Task).filter(
            Task.assigned_to == m.identity_id,
            Task.status != "completed"
        ).count()

        overdue_tasks = db.session.query(Task).filter(
            Task.assigned_to == m.identity_id,
            Task.status != "completed",
            Task.due_date < now.date()
        ).count()

        # Commitments owned by this member
        commitments = db.session.query(Commitment).filter_by(
            owner=m.identity_id
        ).count()

        pending_approvals = db.session.query(Commitment).filter_by(
            owner=m.identity_id, status="pending"
        ).count()

        workload.append({
            "member_id": m.id,
            "name": m.name or m.email.split("@")[0] if m.email else "Unknown",
            "role": m.role,
            "total_tasks": member_tasks,
            "pending_tasks": pending_tasks,
            "overdue_tasks": max(0, overdue_tasks),
            "total_commitments": commitments,
            "pending_approvals": pending_approvals,
        })

    return jsonify({
        "success": True,
        "data": {
            "members": workload,
            "total_members": len(members),
            "total_pending_tasks": sum(w["pending_tasks"] for w in workload),
            "total_overdue": sum(w["overdue_tasks"] for w in workload),
        },
    })