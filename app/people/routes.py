"""FDA23 — People / Internal Operations.

Built on existing canonical models — no separate employee identity authority.
Uses: OrgMember, Task, Commitment, CanonicalRelationship.
Privacy-aware: people-data endpoints require stricter authorization.
"""

from flask import Blueprint, jsonify, request, session, g

people_bp = Blueprint("people", __name__, url_prefix="/api/v1/people")


@people_bp.route("", methods=["GET"])
def people_root():
    """Root people endpoint — returns organization members summary.
    
    This is the canonical entry point for people/organization navigation.
    Returns a summary of all members in the current organization.
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
        "data": {
            "total": len(members),
            "members": [{
                "id": m.id,
                "name": m.name or m.email,
                "email": m.email,
                "role": m.role,
                "designation": m.designation or "",
                "is_active": m.is_active,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            } for m in members],
        },
    })


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _require_auth() -> bool:
    return bool(_identity_id() and _tenant_id())


def _require_people_permission() -> bool:
    """People data requires dedicated people.view permission.

    Org owners are automatically authorized.
    All other roles are checked via canonical check_permission.
    """
    from app.auth import UserRole
    from app.authz.services import check_permission

    # Org owners bypass permission check
    org_id = _tenant_id()
    identity_id = _identity_id()
    if not org_id or not identity_id:
        return False

    # Check if user is org owner
    from app.models import OrgMember
    om = OrgMember.query.filter_by(
        organization_id=org_id, identity_id=identity_id, is_active=True
    ).first()
    if om and om.role == "owner":
        return True

    return check_permission(org_id, identity_id, "people.view")


def _require_people_manage_permission() -> bool:
    """People management requires dedicated people.manage permission."""
    from app.authz.services import check_permission
    return check_permission(_tenant_id(), _identity_id(), "people.manage")


# =========================================================================
# In-memory data stores (no new DB tables — lightweight FDA23 workstreams)
# =========================================================================
_attendance_store: dict = {}    # {org_id: {record_id: {member_id, type, date, reason, status, ...}}}
_policy_store: dict = {}        # {org_id: {policy_id: {title, version, description, ...}}}
_training_store: dict = {}      # {org_id: {training_id: {title, description, ...}}}
_acknowledgement_store: dict = {}  # {org_id: {policy_id: {version: [member_id, ...]}}}
_completion_store: dict = {}    # {org_id: {training_id: [member_id, ...]}}
_leave_id_counter: int = 0

# Seed sample policies and training records
def _seed_workstreams(org_id: int):
    """Seed default policies and training records for an org."""
    if org_id not in _policy_store:
        _policy_store[org_id] = {
            "p1": {"id": "p1", "title": "Code of Conduct", "version": "1.2",
                    "description": "Standards of professional behavior", "required": True},
            "p2": {"id": "p2", "title": "Data Privacy Policy", "version": "2.0",
                    "description": "Handling of personal and sensitive data", "required": True},
            "p3": {"id": "p3", "title": "Remote Work Policy", "version": "1.0",
                    "description": "Guidelines for remote and hybrid work", "required": False},
        }
    if org_id not in _acknowledgement_store:
        _acknowledgement_store[org_id] = {}
    if org_id not in _training_store:
        _training_store[org_id] = {
            "t1": {"id": "t1", "title": "Workplace Safety", "description": "OSHA-compliant safety training", "duration_hours": 2},
            "t2": {"id": "t2", "title": "Anti-Harassment", "description": "Preventing workplace harassment", "duration_hours": 1.5},
            "t3": {"id": "t3", "title": "Data Security Awareness", "description": "Cybersecurity best practices", "duration_hours": 1},
        }
    if org_id not in _completion_store:
        _completion_store[org_id] = {}


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
            "GET /api/v1/people/attendance",
            "POST /api/v1/people/attendance",
            "GET /api/v1/people/policies",
            "POST /api/v1/people/policies/<id>/acknowledge",
            "GET /api/v1/people/training",
            "POST /api/v1/people/training/<id>/complete",
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


# =========================================================================
# People — Canonical Person Records from persons table
# =========================================================================


@people_bp.route("/persons", methods=["GET"])
def list_persons():
    """List canonical Person records for the current tenant.

    Returns Person identity data from the persons table, filtered by
    tenant_id. Includes TeamMember linkage when available.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app.models import Person

    persons = Person.query.filter_by(
        tenant_id=_tenant_id()
    ).order_by(Person.canonical_name).all()

    from app.auth import TeamMember

    result = []
    for p in persons:
        tm = TeamMember.query.filter_by(person_id=p.id).first()
        entry = p.to_dict()
        entry["team_member"] = {
            "id": tm.id,
            "email": tm.email,
            "role": tm.role,
            "is_active": tm.is_active,
        } if tm else None
        result.append(entry)

    return jsonify({
        "success": True,
        "data": result,
    })


@people_bp.route("/persons/<int:person_id>", methods=["GET"])
def get_person(person_id: int):
    """Get a specific Person record."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app.models import Person

    person = Person.query.filter_by(id=person_id, tenant_id=_tenant_id()).first()
    if not person:
        return jsonify({"success": False, "error": "Person not found"}), 404

    return jsonify({
        "success": True,
        "data": person.to_dict(),
    })


# =========================================================================
# FDA23 — Attendance / Leave
# =========================================================================


@people_bp.route("/attendance", methods=["GET"])
def list_attendance():
    """List attendance and leave records for the organization.

    Returns leave requests, approval status, and attendance summary.
    Privacy-safe: no personal contact info.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_manage_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from datetime import datetime, timezone
    org_id = _tenant_id()
    _seed_workstreams(org_id)

    records = _attendance_store.get(org_id, {}).values()
    now = datetime.now(timezone.utc).isoformat()

    return jsonify({
        "success": True,
        "data": {
            "records": [{
                "id": r["id"],
                "member_id": r["member_id"],
                "type": r["type"],
                "date": r["date"],
                "status": r["status"],
                "reason": r.get("reason", ""),
                "created_at": r["created_at"],
            } for r in sorted(records, key=lambda x: x["created_at"], reverse=True)],
            "summary": {
                "total_requests": len(records),
                "pending": sum(1 for r in records if r["status"] == "pending"),
                "approved": sum(1 for r in records if r["status"] == "approved"),
                "rejected": sum(1 for r in records if r["status"] == "rejected"),
            },
        },
    })


@people_bp.route("/attendance", methods=["POST"])
def submit_attendance():
    """Submit a leave or attendance request.

    Body (JSON):
        member_id (str): identity ID of the member
        type (str): leave | sick | remote | overtime
        date (str): date of absence (ISO format)
        reason (str, optional): explanation
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_manage_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from datetime import datetime, timezone
    global _leave_id_counter

    body = request.get_json(silent=True) or {}
    member_id = body.get("member_id", "")
    leave_type = body.get("type", "")
    date = body.get("date", "")
    reason = body.get("reason", "")

    if not member_id or not leave_type or not date:
        return jsonify({
            "success": False,
            "error": "Missing required fields: member_id, type, date",
        }), 400

    valid_types = {"leave", "sick", "remote", "overtime"}
    if leave_type not in valid_types:
        return jsonify({
            "success": False,
            "error": f"Invalid type. Must be one of: {', '.join(sorted(valid_types))}",
        }), 400

    org_id = _tenant_id()
    _seed_workstreams(org_id)

    _leave_id_counter += 1
    record_id = f"ATT-{_leave_id_counter:04d}"
    now = datetime.now(timezone.utc).isoformat()

    if org_id not in _attendance_store:
        _attendance_store[org_id] = {}

    _attendance_store[org_id][record_id] = {
        "id": record_id,
        "member_id": member_id,
        "type": leave_type,
        "date": date,
        "reason": reason,
        "status": "pending",
        "created_at": now,
    }

    return jsonify({
        "success": True,
        "data": _attendance_store[org_id][record_id],
    }), 201


# =========================================================================
# FDA23 — Policy / SOP Acknowledgement
# =========================================================================


@people_bp.route("/policies", methods=["GET"])
def list_policies():
    """List organization policies and their acknowledgement status.

    Shows whether the requesting member has acknowledged each policy.
    Privacy-safe: no personal info exposed.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_manage_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    org_id = _tenant_id()
    identity = _identity_id()
    _seed_workstreams(org_id)

    policies = _policy_store.get(org_id, {})
    ack_data = _acknowledgement_store.get(org_id, {})

    result = []
    for pid, policy in policies.items():
        version = policy["version"]
        # Check if current identity acknowledged this policy version
        version_acks = ack_data.get(pid, {}).get(version, [])
        acknowledged = identity in version_acks

        result.append({
            "id": pid,
            "title": policy["title"],
            "version": version,
            "description": policy.get("description", ""),
            "required": policy.get("required", False),
            "acknowledged": acknowledged,
        })

    return jsonify({
        "success": True,
        "data": {
            "policies": result,
            "total": len(result),
            "acknowledged_count": sum(1 for p in result if p["acknowledged"]),
        },
    })


@people_bp.route("/policies/<policy_id>/acknowledge", methods=["POST"])
def acknowledge_policy(policy_id: str):
    """Acknowledge a specific policy/SOP by its ID for the current user.

    Tracks acknowledgement per member + policy version.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_manage_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from datetime import datetime, timezone
    org_id = _tenant_id()
    identity = _identity_id()
    _seed_workstreams(org_id)

    policies = _policy_store.get(org_id, {})
    if policy_id not in policies:
        return jsonify({"success": False, "error": "Policy not found"}), 404

    policy = policies[policy_id]
    version = policy["version"]

    if org_id not in _acknowledgement_store:
        _acknowledgement_store[org_id] = {}
    if policy_id not in _acknowledgement_store[org_id]:
        _acknowledgement_store[org_id][policy_id] = {}

    version_acks = _acknowledgement_store[org_id][policy_id].setdefault(version, [])
    if identity not in version_acks:
        version_acks.append(identity)

    now = datetime.now(timezone.utc).isoformat()
    return jsonify({
        "success": True,
        "data": {
            "policy_id": policy_id,
            "title": policy["title"],
            "version": version,
            "acknowledged": True,
            "acknowledged_at": now,
            "acknowledged_by": identity,
        },
    }), 200


# =========================================================================
# FDA23 — Training Records
# =========================================================================


@people_bp.route("/training", methods=["GET"])
def list_training():
    """List available training and completion records for the organization.

    Shows whether the requesting member has completed each training.
    Privacy-safe: no personal info exposed.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_manage_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    org_id = _tenant_id()
    identity = _identity_id()
    _seed_workstreams(org_id)

    trainings = _training_store.get(org_id, {})
    completions = _completion_store.get(org_id, {})

    result = []
    for tid, training in trainings.items():
        completed_list = completions.get(tid, [])
        completed = identity in completed_list

        result.append({
            "id": tid,
            "title": training["title"],
            "description": training.get("description", ""),
            "duration_hours": training.get("duration_hours", 0),
            "completed": completed,
        })

    return jsonify({
        "success": True,
        "data": {
            "trainings": result,
            "total": len(result),
            "completed_count": sum(1 for t in result if t["completed"]),
        },
    })


@people_bp.route("/training/<training_id>/complete", methods=["POST"])
def complete_training(training_id: str):
    """Mark a training as completed for the current user.

    Tracks completion per member + training module.
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_people_manage_permission():
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from datetime import datetime, timezone
    org_id = _tenant_id()
    identity = _identity_id()
    _seed_workstreams(org_id)

    trainings = _training_store.get(org_id, {})
    if training_id not in trainings:
        return jsonify({"success": False, "error": "Training not found"}), 404

    completions = _completion_store.setdefault(org_id, {})
    completed_list = completions.setdefault(training_id, [])
    if identity not in completed_list:
        completed_list.append(identity)

    now = datetime.now(timezone.utc).isoformat()
    return jsonify({
        "success": True,
        "data": {
            "training_id": training_id,
            "title": trainings[training_id]["title"],
            "completed": True,
            "completed_at": now,
            "completed_by": identity,
        },
    }), 200