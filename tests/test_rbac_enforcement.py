"""RBAC Enforcement Tests — deny-by-default security verification.

Verifies the canonical authorization architecture:
1. Unauthenticated requests → 401
2. Authenticated users without permission → 403
3. Org owner bypass → owner holds all permissions
4. Role assignment → permissions granted via OrgMemberRole
5. Cross-organization isolation → org A member cannot see org B data

The foundational rule: SHUNYA IS NOT BUILT TO MAKE TESTS GREEN.
SHUNYA IS BUILT TO MAKE THE PRODUCT WORK. Security must be deny-by-default.
These tests verify that deny-by-default actually holds.
"""

import json

import pytest

from app import db
from app.authz.models import Role, OrgMemberRole
from app.authz.services import check_permission, seed_default_roles
from app.models import Organization, OrgMember


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def org_a(app):
    org = Organization(name="Org A", slug="org-a-rbac")
    db.session.add(org)
    db.session.commit()
    seed_default_roles(org.id)
    return org


@pytest.fixture()
def org_b(app):
    org = Organization(name="Org B", slug="org-b-rbac")
    db.session.add(org)
    db.session.commit()
    seed_default_roles(org.id)
    return org


@pytest.fixture()
def owner_member(app, org_a):
    m = OrgMember(
        organization_id=org_a.id,
        identity_id="owner@test.com",
        name="Owner User",
        email="owner@test.com",
        role="owner",
        is_active=True,
    )
    db.session.add(m)
    db.session.commit()
    return m


@pytest.fixture()
def member_member(app, org_a):
    m = OrgMember(
        organization_id=org_a.id,
        identity_id="member@test.com",
        name="Member User",
        email="member@test.com",
        role="member",
        is_active=True,
    )
    db.session.add(m)
    db.session.commit()
    return m


@pytest.fixture()
def outsider_member(app, org_b):
    """A member of org B — should NOT access org A data."""
    m = OrgMember(
        organization_id=org_b.id,
        identity_id="outsider@test.com",
        name="Outsider User",
        email="outsider@test.com",
        role="member",
        is_active=True,
    )
    db.session.add(m)
    db.session.commit()
    return m


def _login(client, identity_id, org_id):
    """Set the session cookie identity + org for a test client."""
    with client.session_transaction() as sess:
        sess["identity_id"] = identity_id
        sess["user_id"] = identity_id
        sess["current_org_id"] = org_id
        sess["_fresh"] = True


# ---------------------------------------------------------------------------
# 1. Unauthenticated → 401
# ---------------------------------------------------------------------------

def test_unauthenticated_gets_401(client):
    """Deny-by-default: no session → 401 on protected endpoints."""
    resp = client.get("/api/v1/knowledge/documents")
    assert resp.status_code == 401

    resp = client.post("/api/v1/outcomes", json={"intention": "x"})
    assert resp.status_code == 401


def test_unauthenticated_public_ok(client, app):
    """Health and auth endpoints remain public."""
    resp = client.get("/health")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. Missing permission → 403
# ---------------------------------------------------------------------------

def test_missing_permission_gets_403(client, app, org_a, member_member):
    """A member without admin.view_audit gets 403 on audit routes."""
    _login(client, "member@test.com", org_a.id)
    resp = client.get("/api/v1/audit/list")
    assert resp.status_code == 403


def test_member_can_view_own_org_people(client, app, org_a, member_member):
    """Member with people.view (via default member role) can list members."""
    _login(client, "member@test.com", org_a.id)
    resp = client.get("/api/v1/people/members")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True


# ---------------------------------------------------------------------------
# 3. Owner bypass
# ---------------------------------------------------------------------------

def test_owner_bypass_all_permissions(client, app, org_a, owner_member):
    """Org owner holds ALL permissions — architectural truth."""
    _login(client, "owner@test.com", org_a.id)

    # Owner can access admin-level routes (audit)
    resp = client.get("/api/v1/audit/list")
    assert resp.status_code == 200

    # Owner can access people and knowledge
    resp = client.get("/api/v1/knowledge/documents")
    assert resp.status_code == 200

    # check_permission returns True for arbitrary permissions
    with app.app_context():
        assert check_permission(org_a.id, "owner@test.com", "admin.manage_roles") is True
        assert check_permission(org_a.id, "owner@test.com", "finance.reconcile") is True
        assert check_permission(org_a.id, "owner@test.com", "definitely.not.a.real.perm") is True


def test_owner_bypass_rejected_for_other_org(client, app, org_a, org_b, owner_member):
    """Owner of org A is NOT authorized in org B."""
    _login(client, "owner@test.com", org_b.id)
    resp = client.get("/api/v1/people/members")
    # Owner is not a member of org B → no org membership permission
    assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# 4. Role assignment
# ---------------------------------------------------------------------------

def test_role_assignment_grants_permission(client, app, org_a, member_member):
    """Explicit OrgMemberRole assignment unlocks permission."""
    with app.app_context():
        role = Role.query.filter_by(organization_id=org_a.id, name="viewer").first()
        assert role is not None
        assignment = OrgMemberRole(
            organization_id=org_a.id,
            member_id=member_member.id,
            role_id=role.id,
            scope="organization",
            granted_by="test",
        )
        db.session.add(assignment)
        db.session.commit()

        # viewer role does NOT have people.view → denied
        assert check_permission(org_a.id, "member@test.com", "people.view") is False
        # viewer role HAS knowledge.view → granted
        assert check_permission(org_a.id, "member@test.com", "knowledge.view") is True

        db.session.delete(assignment)
        db.session.commit()


def test_auto_role_assignment_on_first_check(app, org_a, member_member):
    """Member with role='member' but no explicit assignment gets default role."""
    with app.app_context():
        # No OrgMemberRole exists yet
        assert OrgMemberRole.query.filter_by(member_id=member_member.id).count() == 0
        # First check auto-assigns the member role
        assert check_permission(org_a.id, "member@test.com", "people.view") is True
        # Assignment was created
        assert OrgMemberRole.query.filter_by(member_id=member_member.id).count() == 1


# ---------------------------------------------------------------------------
# 5. Cross-organization isolation
# ---------------------------------------------------------------------------

def test_cross_org_isolation(client, app, org_a, org_b, member_member, outsider_member):
    """User in org B cannot see org A members via people API."""
    _login(client, "outsider@test.com", org_b.id)

    resp = client.get("/api/v1/people/members")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("success") is True
    # Only org B members visible — org A's member must not leak
    # NOTE: /api/v1/people/members returns data as a flat list of member dicts
    members = data.get("data", [])
    org_b_members = [m for m in members if m.get("email") == "outsider@test.com"]
    org_a_members = [m for m in members if m.get("email") == "member@test.com"]
    assert org_b_members, "outsider should see themselves"
    assert not org_a_members, "org A member leaked into org B view"


def test_org_membership_required(client, app, admin_user):
    """Authenticated user with NO org membership → 403 (deny-by-default)."""
    with client.session_transaction() as sess:
        sess["identity_id"] = "ghost@test.com"
        sess["user_id"] = "ghost@test.com"
        sess["_fresh"] = True
        # NOTE: no current_org_id — must hit the org membership middleware

    resp = client.get("/api/v1/people/members")
    assert resp.status_code == 403


def test_inactive_member_denied(app, org_a):
    """Inactive members fail check_permission."""
    m = OrgMember(
        organization_id=org_a.id,
        identity_id="inactive@test.com",
        name="Inactive",
        email="inactive@test.com",
        role="owner",  # even owner bypass requires is_active=True
        is_active=False,
    )
    db.session.add(m)
    db.session.commit()

    with app.app_context():
        assert check_permission(org_a.id, "inactive@test.com", "any.perm") is False


# ---------------------------------------------------------------------------
# 6. Decorator denial logging (AUTHZ DENY)
# ---------------------------------------------------------------------------

def test_deny_logs_authz_message(client, app, org_a, member_member, caplog):
    """Permission denials are logged with the AUTHZ DENY marker."""
    import logging
    with caplog.at_level(logging.INFO):
        _login(client, "member@test.com", org_a.id)
        resp = client.get("/api/v1/audit/list")
        assert resp.status_code == 403

    deny_lines = [r.message for r in caplog.records if "AUTHZ DENY" in r.getMessage()]
    assert deny_lines, "Expected AUTHZ DENY log entry for denied request"
    assert "member@test.com" in deny_lines[0]