"""FOR-2C.2: Authorization Engine — Services."""

from app import db
from app.authz.models import Role, OrgMemberRole, DEFAULT_ROLES


def seed_default_roles(organization_id: int):
    """Seed default roles for a new organization."""
    if Role.query.filter_by(organization_id=organization_id).count() > 0:
        return
    import json
    for name, cfg in DEFAULT_ROLES.items():
        r = Role(organization_id=organization_id, name=name, display_name=cfg["display_name"],
            description=cfg["description"], permissions=json.dumps(cfg["permissions"]), is_system=cfg["is_system"])
        db.session.add(r)
    db.session.commit()


def check_permission(organization_id: int, identity_id: str, permission: str) -> bool:
    """Canonical authorization check. Every domain calls this.

    Org owners hold all permissions — bypasses the role assignment check.
    All other roles (admin, manager, member, etc.) are checked against
    their explicit permission set via OrgMemberRole → Role assignments.
    If a member has no role assignments but has a defined OrgMember.role,
    the matching default role is auto-assigned on first check.
    """
    from app.models import OrgMember
    member = OrgMember.query.filter_by(organization_id=organization_id, identity_id=identity_id, is_active=True).first()
    if not member:
        return False
    # Owner bypass — owner role holds all permissions
    if member.role == "owner":
        return True
    assignments = OrgMemberRole.query.filter_by(organization_id=organization_id, member_id=member.id).all()
    import json
    for a in assignments:
        role = db.session.get(Role, a.role_id)
        if role and permission in json.loads(role.permissions or "[]"):
            return True
    # Auto-assignment: if member has a role but no OrgMemberRole entries,
    # try to assign the matching Role if it already exists for this org.
    # Does NOT call seed_default_roles — that's the org creation path's job.
    if not assignments and member.role:
        role = Role.query.filter_by(organization_id=organization_id, name=member.role).first()
        if role:
            assignment = OrgMemberRole(
                organization_id=organization_id,
                member_id=member.id,
                role_id=role.id,
                scope="organization",
                granted_by="auto",
            )
            db.session.add(assignment)
            db.session.commit()
            if permission in json.loads(role.permissions or "[]"):
                return True
    return False


def get_member_permissions(organization_id: int, identity_id: str) -> list:
    """Get all permissions for a member."""
    from app.models import OrgMember
    member = OrgMember.query.filter_by(organization_id=organization_id, identity_id=identity_id, is_active=True).first()
    if not member:
        return []
    import json
    perms = set()
    for a in OrgMemberRole.query.filter_by(organization_id=organization_id, member_id=member.id).all():
        role = db.session.get(Role, a.role_id)
        if role:
            perms.update(json.loads(role.permissions or "[]"))
    return sorted(perms)


def get_all_permission_keys() -> list:
    """Get all canonical permission keys and descriptions."""
    from app.authz.models import PERMISSIONS
    return [{"key": k, "description": v} for k, v in sorted(PERMISSIONS.items())]