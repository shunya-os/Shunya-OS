"""SHUNYA M9 — Enterprise Ready Service.

Immutable audit trail, RBAC enforcement, team/role management, tenant isolation.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app import db
from app.enterprise.models import AuditRecord, EnterpriseRole, EnterpriseTeamMember, SYSTEM_ROLES


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------

def record_audit(
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    entity_name: str = "",
    details: dict[str, Any] | None = None,
    ip_address: str = "",
    organization_id: str | None = None,
    actor_name: str = "",
) -> AuditRecord:
    """Record an immutable audit entry."""
    record = AuditRecord(
        actor_id=actor_id,
        actor_name=actor_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        details=json.dumps(details or {}),
        ip_address=ip_address,
        organization_id=organization_id,
    )
    db.session.add(record)
    db.session.commit()
    return record


def query_audit(
    organization_id: str | None = None,
    actor_id: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Query the audit trail with filters."""
    query = AuditRecord.query

    if organization_id:
        query = query.filter_by(organization_id=organization_id)
    if actor_id:
        query = query.filter_by(actor_id=actor_id)
    if entity_id:
        query = query.filter_by(entity_id=entity_id)
    if action:
        query = query.filter_by(action=action)

    total = query.count()
    records = query.order_by(AuditRecord.recorded_at.desc()).offset(offset).limit(limit).all()

    return {
        "records": [r.to_dict() for r in records],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ---------------------------------------------------------------------------
# Role Management
# ---------------------------------------------------------------------------

def seed_system_roles(organization_id: str) -> list[EnterpriseRole]:
    """Create system roles for an organization if they don't exist."""
    roles = []
    for role_data in SYSTEM_ROLES:
        existing = EnterpriseRole.query.filter_by(
            organization_id=organization_id, name=role_data["name"]
        ).first()
        if not existing:
            role = EnterpriseRole(
                organization_id=organization_id,
                name=role_data["name"],
                description=role_data["description"],
                permissions=json.dumps(role_data["permissions"]),
                is_system=role_data["is_system"],
            )
            db.session.add(role)
            roles.append(role)
        else:
            roles.append(existing)
    db.session.commit()
    return roles


def get_roles(organization_id: str) -> list[dict[str, Any]]:
    """Get all roles for an organization."""
    roles = EnterpriseRole.query.filter_by(organization_id=organization_id).all()
    return [r.to_dict() for r in roles]


def create_role(
    organization_id: str,
    name: str,
    description: str = "",
    permissions: list[dict[str, Any]] | None = None,
) -> EnterpriseRole:
    """Create a custom role."""
    role = EnterpriseRole(
        organization_id=organization_id,
        name=name,
        description=description,
        permissions=json.dumps(permissions or []),
    )
    db.session.add(role)
    db.session.commit()
    return role


# ---------------------------------------------------------------------------
# Team Management
# ---------------------------------------------------------------------------

def invite_member(
    organization_id: str,
    identity_id: str,
    name: str = "",
    email: str = "",
    role_id: int | None = None,
    invited_by: str | None = None,
) -> EnterpriseTeamMember:
    """Invite a member to an organization."""
    existing = EnterpriseTeamMember.query.filter_by(
        organization_id=organization_id, identity_id=identity_id
    ).first()
    if existing:
        existing.status = "active"
        if role_id:
            existing.role_id = role_id
        db.session.commit()
        return existing

    member = EnterpriseTeamMember(
        organization_id=organization_id,
        identity_id=identity_id,
        name=name,
        email=email,
        role_id=role_id,
        status="active",
        invited_by=invited_by,
        joined_at=datetime.utcnow(),
    )
    db.session.add(member)
    db.session.commit()
    return member


def get_team(organization_id: str) -> list[dict[str, Any]]:
    """Get all members of an organization."""
    members = EnterpriseTeamMember.query.filter_by(
        organization_id=organization_id
    ).all()
    return [m.to_dict() for m in members]


def remove_member(organization_id: str, identity_id: str) -> bool:
    """Remove a member from an organization."""
    member = EnterpriseTeamMember.query.filter_by(
        organization_id=organization_id, identity_id=identity_id
    ).first()
    if not member:
        return False
    member.status = "disabled"
    db.session.commit()
    return True


# ---------------------------------------------------------------------------
# RBAC Enforcement
# ---------------------------------------------------------------------------

def check_permission(
    identity_id: str,
    resource: str,
    action: str,
    organization_id: str | None = None,
) -> dict[str, Any]:
    """Check if an identity has permission to perform an action on a resource."""
    if not organization_id:
        members = EnterpriseTeamMember.query.filter_by(
            identity_id=identity_id, status="active"
        ).all()
        for member in members:
            if member.role_id:
                role = EnterpriseRole.query.get(member.role_id)
                if role and _role_has_permission(role, resource, action):
                    return {"granted": True, "reason": f"Role: {role.name}"}
        return {"granted": False, "reason": "No matching permission in any organization"}

    member = EnterpriseTeamMember.query.filter_by(
        organization_id=organization_id, identity_id=identity_id, status="active"
    ).first()
    if not member:
        return {"granted": False, "reason": "Not a member of this organization"}
    if not member.role_id:
        return {"granted": False, "reason": "No role assigned"}
    role = EnterpriseRole.query.get(member.role_id)
    if not role:
        return {"granted": False, "reason": "Role not found"}
    if _role_has_permission(role, resource, action):
        return {"granted": True, "reason": f"Role: {role.name}"}
    return {"granted": False, "reason": f"Role '{role.name}' lacks '{action}' on '{resource}'"}


def _role_has_permission(role: EnterpriseRole, resource: str, action: str) -> bool:
    """Check if a role's permission set includes the requested access."""
    try:
        permissions = json.loads(role.permissions) if isinstance(role.permissions, str) else role.permissions
    except (json.JSONDecodeError, TypeError):
        return False
    for perm in permissions:
        res = perm.get("resource", "")
        actions = perm.get("actions", [])
        if res == "*" or res == resource:
            if "*" in actions or action in actions:
                return True
    return False


# ---------------------------------------------------------------------------
# Tenant Isolation
# ---------------------------------------------------------------------------

def get_organization_for_identity(identity_id: str) -> str | None:
    """Get the primary organization ID for an identity."""
    member = EnterpriseTeamMember.query.filter_by(
        identity_id=identity_id, status="active"
    ).first()
    return member.organization_id if member else None


def assert_tenant_isolation(
    identity_id: str,
    object_organization_id: str | None,
) -> bool:
    """Verify that an identity can access data belonging to an organization."""
    if not object_organization_id:
        return True
    member_orgs = [
        m.organization_id for m in EnterpriseTeamMember.query.filter_by(
            identity_id=identity_id, status="active"
        ).all()
    ]
    return object_organization_id in member_orgs