"""FDA21 — Audit & Governance Routes.

Single API surface for audit reconstruction, approval recording,
evidence chain querying, and audit export.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request, session, g

audit_bp = Blueprint("audit", __name__, url_prefix="/api/v1/audit")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _require_auth() -> bool:
    return bool(_identity_id() and _tenant_id())


# ---------------------------------------------------------------------------
# Reconstruction
# ---------------------------------------------------------------------------


@audit_bp.route("/reconstruct/<object_type>/<int:object_id>", methods=["GET"])
def reconstruct(object_type: str, object_id: int):
    """Reconstruct a complete business outcome from canonical records.

    Traces: WHAT → WHO → WHEN → WHY → EVIDENCE → APPROVAL → EXECUTION → OUTCOME
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.audit.service import reconstruct_business_outcome
        result = reconstruct_business_outcome(object_id, object_type, _tenant_id())
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": f"Reconstruction failed: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# Approval Recording
# ---------------------------------------------------------------------------


@audit_bp.route("/approvals", methods=["POST"])
def record_approval():
    """Record a governed approval/rejection/authorization.

    Body:
        action: approve, reject, authorize
        resource_type: Type of the resource
        resource_id: ID of the resource
        basis: Reason/basis for the approval
        details: Optional JSON metadata
    """
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip()
    resource_type = (data.get("resource_type") or "").strip()
    resource_id = (data.get("resource_id") or "").strip()

    if not action or not resource_type or not resource_id:
        return jsonify({"success": False, "error": "action, resource_type, and resource_id are required"}), 400

    if action not in ("approve", "reject", "authorize", "cancel"):
        return jsonify({"success": False, "error": "action must be approve, reject, authorize, or cancel"}), 400

    try:
        from app.audit.service import record_approval
        result = record_approval(
            identity_id=_identity_id(),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            basis=data.get("basis", ""),
            details=data.get("details"),
        )
        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Decision Trace
# ---------------------------------------------------------------------------


@audit_bp.route("/decisions/<int:object_id>", methods=["GET"])
def get_decision_trace(object_id: int):
    """Get all decision traces for an object."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.audit.service import _get_decisions_for_object
        decisions = _get_decisions_for_object(object_id, _tenant_id())
        return jsonify({"success": True, "data": decisions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Evidence Chain
# ---------------------------------------------------------------------------


@audit_bp.route("/evidence/<int:object_id>", methods=["GET"])
def get_evidence_chain(object_id: int):
    """Get evidence chain for an object."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.audit.service import _get_evidence_chain
        evidence = _get_evidence_chain(object_id, _tenant_id())
        return jsonify({"success": True, "data": evidence})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Execution Trace
# ---------------------------------------------------------------------------


@audit_bp.route("/executions/<int:object_id>", methods=["GET"])
def get_execution_trace(object_id: int):
    """Get execution trace for an object."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    object_type = request.args.get("object_type", "lead")
    try:
        from app.audit.service import _get_executions_for_object
        executions = _get_executions_for_object(object_id, object_type, _tenant_id())
        return jsonify({"success": True, "data": executions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Audit Export
# ---------------------------------------------------------------------------


@audit_bp.route("/export/<object_type>/<int:object_id>", methods=["GET"])
def export_audit(object_type: str, object_id: int):
    """Export a complete audit package with full provenance."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.audit.service import export_audit_package
        package = export_audit_package(object_id, object_type, _tenant_id())
        return jsonify({"success": True, "data": package})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Audit Integrity Verification
# ---------------------------------------------------------------------------


@audit_bp.route("/verify/<object_type>/<int:object_id>", methods=["GET"])
def verify_audit(object_type: str, object_id: int):
    """Verify audit chain integrity for an object."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    try:
        from app.audit.service import verify_audit_chain
        result = verify_audit_chain(object_id, object_type, _tenant_id())
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Corrective Event
# ---------------------------------------------------------------------------


@audit_bp.route("/correct", methods=["POST"])
def record_corrective():
    """Record a corrective event that preserves original history."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}
    object_id = data.get("object_id")
    object_type = (data.get("object_type") or "").strip()
    correction_type = (data.get("correction_type") or "").strip()
    description = (data.get("description") or "").strip()

    if not all([object_id, object_type, correction_type, description]):
        return jsonify({"success": False, "error": "object_id, object_type, correction_type, and description are required"}), 400

    try:
        from app.audit.service import record_corrective_event
        result = record_corrective_event(
            original_object_id=int(object_id),
            object_type=object_type,
            correction_type=correction_type,
            description=description,
            identity_id=_identity_id(),
            details=data.get("details"),
        )
        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Audit List
# ---------------------------------------------------------------------------


@audit_bp.route("/list", methods=["GET"])
def list_audit_logs():
    """List recent audit log entries across all objects.

    Supports pagination via ?limit= and ?offset= query params.
    Returns the most recent audit entries first.
    """
    from app.security.audit import AuditLog

    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    limit = min(limit, 200)  # cap

    try:
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        total = AuditLog.query.count()
        return jsonify({
            "success": True,
            "data": {
                "logs": [l.to_dict() for l in logs],
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@audit_bp.route("/health", methods=["GET"])
def audit_health():
    """Health check for the audit API."""
    return jsonify({
        "status": "ok",
        "service": "audit-governance",
        "version": "1.0.0",
        "canonical_sources": [
            "sh_audit_logs",
            "decision_traces",
            "evidence_records",
            "sh_outcomes",
            "commitments",
            "rel_timeline",
        ],
        "endpoints": [
            "GET /api/v1/audit/reconstruct/<type>/<id>",
            "POST /api/v1/audit/approvals",
            "GET /api/v1/audit/decisions/<id>",
            "GET /api/v1/audit/evidence/<id>",
            "GET /api/v1/audit/executions/<id>",
            "GET /api/v1/audit/export/<type>/<id>",
            "GET /api/v1/audit/verify/<type>/<id>",
            "POST /api/v1/audit/correct",
            "GET /api/v1/audit/list",
        ],
    })