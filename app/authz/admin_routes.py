"""FDA22 — Admin & Permissions API Routes.

Provides admin API for:
- Service account CRUD
- Delegation management
- Tenant policy management
- Member role/permission inspection
- Permission auditing
"""

from flask import Blueprint, jsonify, request, session, g

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


def _identity_id() -> str:
    return g.get("identity_id") or session.get("identity_id") or session.get("user_id", "anonymous")


def _tenant_id() -> int:
    return session.get("current_org_id") or session.get("tenant_id", 0)


def _require_auth() -> bool:
    return bool(_identity_id() and _tenant_id())


def _require_permission(permission: str) -> bool:
    """Check that the authenticated user has the required permission."""
    from app.authz.services import check_permission
    return check_permission(_tenant_id(), _identity_id(), permission)


# =========================================================================
# Health
# =========================================================================


@admin_bp.route("/health", methods=["GET"])
def admin_health():
    return jsonify({
        "status": "ok", "service": "admin-permissions", "version": "1.0.0",
        "endpoints": [
            "GET /api/v1/admin/health",
            "GET /api/v1/admin/permissions",
            "GET /api/v1/admin/roles",
            "GET /api/v1/admin/members/<id>/permissions",
            "POST /api/v1/admin/service-accounts",
            "GET /api/v1/admin/service-accounts",
            "DELETE /api/v1/admin/service-accounts/<id>",
            "POST /api/v1/admin/delegations",
            "DELETE /api/v1/admin/delegations/<id>",
            "GET /api/v1/admin/delegations",
            "POST /api/v1/admin/policies",
            "GET /api/v1/admin/policies",
            "GET /api/v1/admin/policies/<key>",
        ],
    })


# =========================================================================
# Permission & Role Discovery
# =========================================================================


@admin_bp.route("/permissions", methods=["GET"])
def list_permissions():
    """List all available permission keys."""
    from app.authz.models import PERMISSIONS
    from app.authz.extended_models import EXTENDED_PERMISSIONS
    all_perms = {**PERMISSIONS, **EXTENDED_PERMISSIONS}
    return jsonify({
        "success": True,
        "data": [{"key": k, "description": v} for k, v in sorted(all_perms.items())],
    })


@admin_bp.route("/roles", methods=["GET"])
def list_roles():
    """List all roles for the current org."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app import db
    from app.authz.models import Role
    roles = db.session.query(Role).filter_by(organization_id=_tenant_id()).all()
    return jsonify({"success": True, "data": [r.to_dict() for r in roles]})


@admin_bp.route("/members/<int:member_id>/permissions", methods=["GET"])
def get_member_permissions_route(member_id: int):
    """Get all permissions for a specific member."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    try:
        from app.authz.extended_services import get_member_roles_with_permissions
        from app.models import OrgMember
        member = OrgMember.query.filter_by(id=member_id, organization_id=_tenant_id()).first()
        if not member:
            return jsonify({"success": False, "error": "Member not found"}), 404
        result = get_member_roles_with_permissions(_tenant_id(), member.identity_id)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================================
# Service Accounts
# =========================================================================


@admin_bp.route("/service-accounts", methods=["POST"])
def create_service_account():
    """Create a new service account."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_permission("admin.manage_service_accounts"):
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "name is required"}), 400

    permissions = data.get("permissions", [])
    if not isinstance(permissions, list):
        return jsonify({"success": False, "error": "permissions must be a list"}), 400

    try:
        from app.authz.extended_services import create_service_account
        result = create_service_account(
            organization_id=_tenant_id(),
            name=name,
            permissions=permissions,
            created_by=_identity_id(),
            description=data.get("description", ""),
            allowed_scopes=data.get("allowed_scopes"),
        )
        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/service-accounts", methods=["GET"])
def list_service_accounts():
    """List all service accounts."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_permission("admin.manage_service_accounts"):
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app.authz.extended_services import list_service_accounts
    accounts = list_service_accounts(_tenant_id())
    return jsonify({"success": True, "data": accounts})


@admin_bp.route("/service-accounts/<int:sa_id>", methods=["DELETE"])
def revoke_service_account(sa_id: int):
    """Revoke a service account."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_permission("admin.manage_service_accounts"):
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app.authz.extended_services import revoke_service_account
    if revoke_service_account(_tenant_id(), sa_id, _identity_id()):
        return jsonify({"success": True, "data": {"id": sa_id, "status": "revoked"}})
    return jsonify({"success": False, "error": "Service account not found"}), 404


# =========================================================================
# Delegations
# =========================================================================


@admin_bp.route("/delegations", methods=["GET"])
def list_delegations():
    """List all active delegations."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app import db
    from app.authz.extended_models import ApprovalDelegation
    delegations = db.session.query(ApprovalDelegation).filter_by(
        organization_id=_tenant_id()
    ).order_by(ApprovalDelegation.created_at.desc()).limit(50).all()
    return jsonify({"success": True, "data": [d.to_dict() for d in delegations]})


@admin_bp.route("/delegations", methods=["POST"])
def create_delegation():
    """Create an approval delegation."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_permission("delegation.create"):
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    data = request.get_json(silent=True) or {}
    delegator_id = data.get("delegator_id")
    delegate_id = data.get("delegate_id")
    permission_keys = data.get("permission_keys", [])

    if not all([delegator_id, delegate_id, permission_keys]):
        return jsonify({"success": False, "error": "delegator_id, delegate_id, and permission_keys are required"}), 400

    try:
        from app.authz.extended_services import create_delegation
        result = create_delegation(
            organization_id=_tenant_id(),
            delegator_id=int(delegator_id),
            delegate_id=int(delegate_id),
            permission_keys=permission_keys,
            reason=data.get("reason", ""),
            valid_until=data.get("valid_until"),
            created_by=_identity_id(),
        )
        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/delegations/<int:del_id>", methods=["DELETE"])
def revoke_delegation(del_id: int):
    """Revoke an approval delegation."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_permission("delegation.revoke"):
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    from app.authz.extended_services import revoke_delegation
    if revoke_delegation(_tenant_id(), del_id, _identity_id()):
        return jsonify({"success": True, "data": {"id": del_id, "status": "revoked"}})
    return jsonify({"success": False, "error": "Delegation not found"}), 404


# =========================================================================
# Tenant Policies
# =========================================================================


@admin_bp.route("/policies", methods=["GET"])
def list_policies():
    """List all tenant policies."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app.authz.extended_services import get_all_tenant_policies
    policies = get_all_tenant_policies(_tenant_id())
    return jsonify({"success": True, "data": policies})


@admin_bp.route("/policies/<path:policy_key>", methods=["GET"])
def get_policy(policy_key: str):
    """Get a specific tenant policy."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    from app.authz.extended_services import get_tenant_policy
    policy = get_tenant_policy(_tenant_id(), policy_key)
    if not policy:
        return jsonify({"success": False, "error": "Policy not found"}), 404
    return jsonify({"success": True, "data": policy})


@admin_bp.route("/policies", methods=["POST"])
def set_policy():
    """Set a tenant policy value."""
    if not _require_auth():
        return jsonify({"success": False, "error": "Authentication required"}), 401
    if not _require_permission("admin.manage_policies"):
        return jsonify({"success": False, "error": "Insufficient permissions"}), 403

    data = request.get_json(silent=True) or {}
    policy_key = (data.get("policy_key") or "").strip()
    policy_value = (data.get("policy_value") or "").strip()
    if not policy_key or policy_value is None:
        return jsonify({"success": False, "error": "policy_key and policy_value are required"}), 400

    try:
        from app.authz.extended_services import set_tenant_policy
        result = set_tenant_policy(
            org_id=_tenant_id(),
            policy_key=policy_key,
            policy_value=policy_value,
            policy_type=data.get("policy_type", "string"),
            description=data.get("description", ""),
            created_by=_identity_id(),
        )
        return jsonify({"success": True, "data": result}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500