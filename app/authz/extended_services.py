"""FDA22 — Admin & Permissions: Extended Services.

Extends the existing authorization services with:
- Service account management (create, verify, revoke)
- Delegation management (create, revoke, check)
- Tenant policy management
- Extended permission checking with delegation fallback
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def generate_api_token() -> str:
    """Generate a secure API token with identifiable prefix."""
    raw = secrets.token_hex(32)
    prefix = raw[:8]
    token = f"shunya_{prefix}_{raw[8:]}"
    return token, hashlib.sha256(token.encode()).hexdigest()


# =========================================================================
# Service Account Management
# =========================================================================


def create_service_account(
    organization_id: int,
    name: str,
    permissions: List[str],
    created_by: str = "system",
    description: str = "",
    allowed_scopes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a service account with scoped permissions.

    Returns the account details AND the raw token (one-time display).
    """
    from app import db
    from app.authz.extended_models import ServiceAccount

    raw_token, token_hash = generate_api_token()
    prefix = raw_token[:14]  # "shunya_" + 8 hex chars

    sa = ServiceAccount(
        organization_id=organization_id,
        name=name,
        description=description,
        token_hash=token_hash,
        token_prefix=prefix,
        permissions=__import__("json").dumps(permissions),
        allowed_scopes=__import__("json").dumps(allowed_scopes or ["organization"]),
        created_by=created_by,
    )
    db.session.add(sa)
    db.session.flush()

    # Audit
    from app.security.audit import log_audit
    log_audit("create", "service_account", str(sa.id),
              {"name": name, "organization_id": organization_id, "permissions": permissions})

    db.session.commit()

    result = sa.to_dict()
    result["token"] = raw_token  # One-time display only
    return result


def verify_service_account_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a service account token and return account details if valid."""
    from app import db
    from app.authz.extended_models import ServiceAccount

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    sa = db.session.query(ServiceAccount).filter_by(token_hash=token_hash, is_active=True).first()
    if not sa:
        return None
    if sa.expires_at and sa.expires_at < datetime.now(timezone.utc):
        return None
    sa.last_used_at = datetime.now(timezone.utc)
    db.session.commit()
    return sa.to_dict()


def revoke_service_account(org_id: int, sa_id: int, revoked_by: str = "system") -> bool:
    """Revoke a service account."""
    from app import db
    from app.authz.extended_models import ServiceAccount

    sa = db.session.query(ServiceAccount).filter_by(id=sa_id, organization_id=org_id).first()
    if not sa:
        return False
    sa.is_active = False

    from app.security.audit import log_audit
    log_audit("update", "service_account", str(sa_id), {"action": "revoke", "revoked_by": revoked_by})
    db.session.commit()
    return True


def list_service_accounts(org_id: int) -> List[Dict[str, Any]]:
    """List all service accounts for an organization."""
    from app import db
    from app.authz.extended_models import ServiceAccount

    accounts = db.session.query(ServiceAccount).filter_by(organization_id=org_id).all()
    return [a.to_dict() for a in accounts]


# =========================================================================
# Delegation Management
# =========================================================================


def create_delegation(
    organization_id: int,
    delegator_id: int,
    delegate_id: int,
    permission_keys: List[str],
    reason: str = "",
    valid_until: Optional[str] = None,
    scope: str = "organization",
    scope_id: Optional[int] = None,
    created_by: str = "system",
) -> Dict[str, Any]:
    """Create an approval delegation."""
    from app import db
    from app.authz.extended_models import ApprovalDelegation

    until = None
    if valid_until:
        try:
            until = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    d = ApprovalDelegation(
        organization_id=organization_id,
        delegator_id=delegator_id,
        delegate_id=delegate_id,
        permission_keys=__import__("json").dumps(permission_keys),
        reason=reason,
        scope=scope,
        scope_id=scope_id,
        valid_until=until,
        created_by=created_by,
    )
    db.session.add(d)
    db.session.flush()

    from app.security.audit import log_audit
    log_audit("create", "delegation", str(d.id),
              {"delegator_id": delegator_id, "delegate_id": delegate_id,
               "permissions": permission_keys, "reason": reason})
    db.session.commit()
    return d.to_dict()


def revoke_delegation(org_id: int, delegation_id: int, revoked_by: str = "system") -> bool:
    """Revoke an approval delegation."""
    from app import db
    from app.authz.extended_models import ApprovalDelegation

    d = db.session.query(ApprovalDelegation).filter_by(id=delegation_id, organization_id=org_id).first()
    if not d:
        return False
    d.status = "revoked"
    d.revoked_by = revoked_by
    d.revoked_at = datetime.now(timezone.utc)

    from app.security.audit import log_audit
    log_audit("update", "delegation", str(d.id), {"action": "revoke", "revoked_by": revoked_by})
    db.session.commit()
    return True


def check_delegated_permission(org_id: int, member_id: int, permission: str) -> bool:
    """Check if a member has a permission via active delegation."""
    from app import db
    from app.authz.extended_models import ApprovalDelegation

    now = datetime.now(timezone.utc)
    delegations = db.session.query(ApprovalDelegation).filter_by(
        organization_id=org_id, delegate_id=member_id, status="active"
    ).all()

    for d in delegations:
        if d.valid_until and d.valid_until < now:
            continue
        perms = __import__("json").loads(d.permission_keys or "[]")
        if permission in perms:
            return True
    return False


# =========================================================================
# Tenant Policy Management
# =========================================================================


def set_tenant_policy(
    org_id: int,
    policy_key: str,
    policy_value: str,
    policy_type: str = "string",
    description: str = "",
    created_by: str = "system",
) -> Dict[str, Any]:
    """Set a tenant policy value."""
    from app import db
    from app.authz.extended_models import TenantPolicy

    existing = db.session.query(TenantPolicy).filter_by(
        organization_id=org_id, policy_key=policy_key
    ).first()

    if existing:
        old_value = existing.policy_value
        existing.policy_value = policy_value
        existing.policy_type = policy_type
        existing.description = description
    else:
        old_value = None
        p = TenantPolicy(
            organization_id=org_id, policy_key=policy_key, policy_value=policy_value,
            policy_type=policy_type, description=description, created_by=created_by,
        )
        db.session.add(p)

    db.session.flush()

    from app.security.audit import log_audit
    log_audit("update" if existing else "create", "tenant_policy", policy_key,
              {"organization_id": org_id, "old_value": old_value, "new_value": policy_value})
    db.session.commit()

    return (existing or p).to_dict()


def get_tenant_policy(org_id: int, policy_key: str) -> Optional[Dict[str, Any]]:
    """Get a tenant policy value."""
    from app import db
    from app.authz.extended_models import TenantPolicy

    p = db.session.query(TenantPolicy).filter_by(
        organization_id=org_id, policy_key=policy_key, is_active=True
    ).first()
    return p.to_dict() if p else None


def get_all_tenant_policies(org_id: int) -> List[Dict[str, Any]]:
    """Get all policies for a tenant."""
    from app import db
    from app.authz.extended_models import TenantPolicy

    policies = db.session.query(TenantPolicy).filter_by(
        organization_id=org_id, is_active=True
    ).all()
    return [p.to_dict() for p in policies]


# =========================================================================
# Extended Permission Check (with delegation fallback)
# =========================================================================


def check_permission_extended(org_id: int, identity_id: str, permission: str) -> bool:
    """Extended permission check with delegation fallback.

    Checks:
    1. Direct role-based permission (existing check_permission)
    2. Delegation-based permission
    """
    from app.authz.services import check_permission

    # 1. Direct role check
    if check_permission(org_id, identity_id, permission):
        return True

    # 2. Delegation check
    from app.models import OrgMember
    member = OrgMember.query.filter_by(
        organization_id=org_id, identity_id=identity_id, is_active=True
    ).first()
    if member and check_delegated_permission(org_id, member.id, permission):
        return True

    return False


# =========================================================================
# Admin utility: get member roles with permission details
# =========================================================================


def get_member_roles_with_permissions(org_id: int, identity_id: str) -> Dict[str, Any]:
    """Get all roles and resolved permissions for a member."""
    from app import db
    from app.models import OrgMember
    from app.authz.models import OrgMemberRole, Role
    from app.authz.services import get_member_permissions

    member = OrgMember.query.filter_by(
        organization_id=org_id, identity_id=identity_id, is_active=True
    ).first()
    if not member:
        return {"member": None, "roles": [], "permissions": [], "delegations": []}

    # Direct roles
    assignments = OrgMemberRole.query.filter_by(
        organization_id=org_id, member_id=member.id
    ).all()
    roles = []
    for a in assignments:
        role = db.session.get(Role, a.role_id)
        if role:
            roles.append({"role": role.name, "scope": a.scope, "scope_id": a.scope_id})

    # Permissions
    permissions = get_member_permissions(org_id, identity_id)

    # Delegations
    from app.authz.extended_models import ApprovalDelegation
    delegations = db.session.query(ApprovalDelegation).filter_by(
        organization_id=org_id, delegate_id=member.id, status="active"
    ).all()

    return {
        "member": {"id": member.id, "email": member.email, "role": member.role},
        "roles": roles,
        "permissions": permissions,
        "delegations": [d.to_dict() for d in delegations],
    }