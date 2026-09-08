"""Test helper — seed RBAC context (Org + Member + Role) in test fixtures.

Usage in auth_headers fixture:
    from tests.auth_helper import seed_rbac
    org_id = seed_rbac(db)
    session["current_org_id"] = org_id

The function is idempotent per test function (SQLite in-memory is fresh each time).
"""
from __future__ import annotations

from typing import Any
from flask_sqlalchemy import SQLAlchemy


def seed_rbac(db: SQLAlchemy, identity_id: str = "test_identity", role_name: str = "admin") -> int:
    """Create Organization + OrgMember + Role + OrgMemberRole.

    Returns the created organization_id.
    """
    from app.models import Organization, OrgMember
    from app.authz.models import Role, OrgMemberRole

    slug = f"test-org-{identity_id[:8]}"
    org = Organization(name="Test Org", slug=slug, is_active=True)
    db.session.add(org)
    db.session.flush()
    org_id = org.id

    # Seed roles
    from app.authz.services import seed_default_roles
    seed_default_roles(org_id)

    # Lookup the role
    role = Role.query.filter_by(organization_id=org_id, name=role_name).first()
    if not role:
        role = Role.query.filter_by(organization_id=org_id).first()

    member = OrgMember(
        organization_id=org_id,
        identity_id=identity_id,
        role=role_name if role else "member",
        is_active=True,
    )
    db.session.add(member)
    db.session.flush()
    member_id = member.id

    if role:
        assignment = OrgMemberRole(
            organization_id=org_id,
            member_id=member_id,
            role_id=role.id,
            scope="organization",
            granted_by="test_setup",
        )
        db.session.add(assignment)

    db.session.commit()
    return org_id