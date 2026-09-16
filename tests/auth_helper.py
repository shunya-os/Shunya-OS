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


def ensure_org_workspace(db, org_id: int, identity_id: str) -> str:
    """Ensure the organization owns an active workspace in sh_workspaces.

    Canonical tenancy is organization *and* workspace: objects carry a
    workspace that is part of their canonical identity, and the application
    fails closed when an organization owns no workspace. A fixture that
    exercises tenant behaviour must therefore provision a real one rather than
    relying on a default.

    Returns the workspace id.
    """
    import hashlib
    from app.objects.legacy_models import Workspace, ShWorkspaceMembership

    existing = Workspace.query.filter_by(organization_id=org_id, status="active").first()
    if existing:
        ws_id = existing.id
    else:
        digest = hashlib.sha1(identity_id.encode("utf-8")).hexdigest()[:8]
        ws_id = f"ws{org_id}-{digest}"[:20]
        db.session.add(Workspace(
            id=ws_id,
            name=f"Test Workspace {org_id}",
            workspace_type="business",
            status="active",
            created_by=identity_id,
            organization_id=org_id,
        ))
        db.session.flush()

    # Canonical authorization (R6B-2.7). Tenancy is organization AND workspace
    # AND an explicit membership granting this identity access to that
    # workspace; without it the identity is correctly denied.
    member = ShWorkspaceMembership.query.filter_by(
        workspace_id=ws_id, identity_id=identity_id).first()
    if not member:
        db.session.add(ShWorkspaceMembership(
            workspace_id=ws_id,
            identity_id=identity_id,
            role="owner",
            is_active=True,
        ))
        db.session.flush()
    return ws_id


def seed_canonical_tenancy(db, org_id: int, identity_id: str,
                           org_name: str | None = None) -> str:
    """Provision canonical tenancy at an EXACT organization id.

    Organization + active OrgMember + canonical workspace owned by that
    organization + the identity→workspace membership that authorizes it.
    Returns the workspace id.

    This is the single canonical test fixture for anything that needs a real
    authorization boundary (R6B-2.7). It never manufactures a synthetic
    organization, never reuses a workspace owned by another organization, and
    never grants a universal membership — the identity is authorized for
    exactly one workspace in exactly one organization.
    """
    from app.models import Organization, OrgMember

    org = db.session.get(Organization, org_id)
    if not org:
        org = Organization(
            id=org_id,
            name=org_name or f"Canonical Org {org_id}",
            slug=f"canonical-org-{org_id}",
            is_active=True,
        )
        db.session.add(org)
        db.session.flush()

    member = OrgMember.query.filter_by(
        identity_id=identity_id, organization_id=org_id).first()
    if member is None:
        member = OrgMember(
            organization_id=org_id,
            identity_id=identity_id,
            role="admin",
            is_active=True,
        )
        db.session.add(member)
        db.session.flush()
    elif not member.is_active:
        member.is_active = True
        db.session.flush()

    ws_id = ensure_org_workspace(db, org_id, identity_id)
    db.session.commit()
    return ws_id


def seed_rbac(db, identity_id: str = "test_identity", role_name: str = "admin") -> int:
    """Create Organization + OrgMember + Role + OrgMemberRole + canonical workspace.

    Idempotent: if identity_id already has an OrgMember, returns its org_id
    instead of creating a duplicate (and still ensures the workspace exists).

    Returns the created (or existing) organization_id.
    """
    from app.models import Organization, OrgMember
    from app.authz.models import Role, OrgMemberRole

    # Idempotent: reuse existing member for this identity
    existing = OrgMember.query.filter_by(identity_id=identity_id, is_active=True).first()
    if existing:
        ensure_org_workspace(db, existing.organization_id, identity_id)
        db.session.commit()
        return existing.organization_id

    # Unique slug per identity — emails can share first 8 chars (slug is unique)
    import hashlib
    digest = hashlib.sha1(identity_id.encode("utf-8")).hexdigest()[:8]
    slug = f"test-org-{digest}"
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

    ensure_org_workspace(db, org_id, identity_id)
    db.session.commit()
    return org_id