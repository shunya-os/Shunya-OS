"""Tests for Workspace CRUD API (Milestone X, D1.2).

Fully self-contained fixtures.
"""

import json
import pytest


@pytest.fixture(scope="function")
def _db(app):
    from app import db
    with app.app_context():
        yield db


@pytest.fixture(scope="function")
def admin_user(app, _db):
    from app.auth import TeamMember
    user = TeamMember(
        name="Admin User", email="admin@test.com",
        role="admin", is_active=True,
    )
    user.set_password("password123")
    user.generate_token()
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def logged_in_client(app, client, admin_user, _db):
    from tests.auth_helper import seed_rbac
    org_id = seed_rbac(_db, identity_id="admin@test.com")
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["identity_id"] = "admin@test.com"
        session["current_org_id"] = org_id
        session["_fresh"] = True
    return client


@pytest.fixture(scope="function")
def org(app, _db):
    from app.models import Organization, OrgMember
    o = Organization(name="Workspace Test Org", slug="ws-test-org", is_active=True)
    _db.session.add(o)
    _db.session.flush()
    # ZG-03 B4: the org under test must have the caller as an ACTIVE member —
    # cross-org access is now denied (403) by the membership gate.
    om = OrgMember(organization_id=o.id, identity_id="admin@test.com",
                   email="admin@test.com", role="owner", is_active=True)
    _db.session.add(om)
    _db.session.commit()
    return o


class TestWorkspaceList:
    """GET /api/v1/orgs/<id>/workspaces"""

    def test_list_empty(self, logged_in_client, org):
        resp = logged_in_client.get(f"/api/v1/orgs/{org.id}/workspaces")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == []

    def test_list_with_data(self, logged_in_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Test WS", slug="test-ws")
        _db.session.add(ws)
        _db.session.commit()
        resp = logged_in_client.get(f"/api/v1/orgs/{org.id}/workspaces")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Test WS"


class TestWorkspaceMembershipGate:
    """ZG-03 B4 — every /orgs/<org_id>/workspaces route must verify the caller
    is an ACTIVE OrgMember of the target org; non-members are denied 403 even
    though the org exists."""

    @pytest.fixture(scope="function")
    def intruder(app, _db):
        from app.auth import TeamMember
        user = TeamMember(
            name="Intruder", email="intruder@test.com",
            role="member", is_active=True,
        )
        user.set_password("password123")
        _db.session.add(user)
        _db.session.commit()
        return user

    @pytest.fixture(scope="function")
    def intruder_client(app, client, intruder, _db):
        with client.session_transaction() as session:
            session["user_id"] = intruder.id
            session["identity_id"] = "intruder@test.com"
            session["current_org_id"] = 99999  # no membership anywhere
            session["_fresh"] = True
        return client

    def test_list_denied_for_non_member(self, intruder_client, org):
        resp = intruder_client.get(f"/api/v1/orgs/{org.id}/workspaces")
        assert resp.status_code == 403, resp.get_json()
        assert resp.get_json()["error"]  # truthful denial message present

    def test_create_denied_for_non_member(self, intruder_client, org):
        resp = intruder_client.post(
            f"/api/v1/orgs/{org.id}/workspaces", json={"name": "Sneak"}
        )
        assert resp.status_code == 403

    def test_get_denied_for_non_member(self, intruder_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Private", slug="private-ws")
        _db.session.add(ws)
        _db.session.commit()
        resp = intruder_client.get(f"/api/v1/orgs/{org.id}/workspaces/{ws.id}")
        assert resp.status_code == 403

    def test_update_denied_for_non_member(self, intruder_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Private", slug="private-ws2")
        _db.session.add(ws)
        _db.session.commit()
        resp = intruder_client.put(
            f"/api/v1/orgs/{org.id}/workspaces/{ws.id}", json={"name": "HiJacked"}
        )
        assert resp.status_code == 403

    def test_delete_denied_for_non_member(self, intruder_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Private", slug="private-ws3")
        _db.session.add(ws)
        _db.session.commit()
        resp = intruder_client.delete(f"/api/v1/orgs/{org.id}/workspaces/{ws.id}")
        assert resp.status_code == 403
        # row untouched
        assert _db.session.get(Workspace, ws.id).is_active is True

    def test_member_still_served(self, logged_in_client, _db, org):
        """Members keep full access (existing behavior preserved)."""
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Mine", slug="mine")
        _db.session.add(ws)
        _db.session.commit()
        resp = logged_in_client.get(f"/api/v1/orgs/{org.id}/workspaces")
        assert resp.status_code == 200
        names = [w["name"] for w in resp.get_json()["data"]]
        assert "Mine" in names

    def test_legacy_bridge_rows_listed(self, app, logged_in_client, _db):
        """Org with a recorded legacy_tenant_id sees workspaces on both sides
        of the tenancy split (canonical org id + legacy tenant id)."""
        from app.models import Organization
        from app.production.identity.workspace_model import Workspace
        from tests.auth_helper import seed_rbac

        org_id = seed_rbac(_db, identity_id="admin@test.com")  # member org
        org = _db.session.get(Organization, org_id)
        org.legacy_tenant_id = 98765  # legacy side of the split
        _db.session.commit()
        _db.session.add(Workspace(tenant_id=org_id, name="Canonical WS", slug="canonical-ws"))
        _db.session.add(Workspace(tenant_id=98765, name="Legacy WS", slug="legacy-ws"))
        _db.session.commit()

        resp = logged_in_client.get(f"/api/v1/orgs/{org_id}/workspaces")
        assert resp.status_code == 200
        names = {w["name"] for w in resp.get_json()["data"]}
        assert "Canonical WS" in names
        assert "Legacy WS" in names


class TestWorkspaceCreate:
    """POST /api/v1/orgs/<id>/workspaces"""

    def test_create_success(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/workspaces",
            json={"name": "My Workspace"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["name"] == "My Workspace"
        assert data["data"]["slug"] == "my-workspace"
        assert data["data"]["is_active"] is True

    def test_create_with_description(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/workspaces",
            json={"name": "Dev", "description": "Development workspace"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["data"]["description"] == "Development workspace"

    def test_create_missing_name(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/workspaces", json={}
        )
        assert resp.status_code == 400

    def test_create_org_not_found(self, logged_in_client):
        resp = logged_in_client.post(
            "/api/v1/orgs/99999/workspaces",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404

    def test_create_duplicate_slug(self, logged_in_client, org):
        logged_in_client.post(
            f"/api/v1/orgs/{org.id}/workspaces",
            json={"name": "Duplicate"},
        )
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/workspaces",
            json={"name": "Duplicate"},
        )
        assert resp.status_code == 201
        slug = resp.get_json()["data"]["slug"]
        assert slug != "duplicate"  # should have a suffix


class TestWorkspaceGet:
    """GET /api/v1/orgs/<id>/workspaces/<id>"""

    def test_get_success(self, logged_in_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Get Test", slug="get-test")
        _db.session.add(ws)
        _db.session.commit()
        resp = logged_in_client.get(
            f"/api/v1/orgs/{org.id}/workspaces/{ws.id}"
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["name"] == "Get Test"

    def test_get_not_found(self, logged_in_client, org):
        resp = logged_in_client.get(
            f"/api/v1/orgs/{org.id}/workspaces/99999"
        )
        assert resp.status_code == 404

    def test_get_wrong_org(self, logged_in_client, _db, org):
        from app.models import Organization
        from app.production.identity.workspace_model import Workspace
        other_org = Organization(name="Other", slug="other", is_active=True)
        _db.session.add(other_org)
        _db.session.flush()
        ws = Workspace(tenant_id=other_org.id, name="Hidden", slug="hidden")
        _db.session.add(ws)
        _db.session.commit()
        resp = logged_in_client.get(
            f"/api/v1/orgs/{org.id}/workspaces/{ws.id}"
        )
        assert resp.status_code == 404


class TestWorkspaceUpdate:
    """PUT /api/v1/orgs/<id>/workspaces/<id>"""

    def test_update_name(self, logged_in_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Original", slug="original")
        _db.session.add(ws)
        _db.session.commit()
        resp = logged_in_client.put(
            f"/api/v1/orgs/{org.id}/workspaces/{ws.id}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["name"] == "Updated"

    def test_update_partial(self, logged_in_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Partial", slug="partial",
                       description="Old desc")
        _db.session.add(ws)
        _db.session.commit()
        resp = logged_in_client.put(
            f"/api/v1/orgs/{org.id}/workspaces/{ws.id}",
            json={"description": "New desc"},
        )
        assert resp.status_code == 200
        d = resp.get_json()["data"]
        assert d["description"] == "New desc"
        assert d["name"] == "Partial"

    def test_update_not_found(self, logged_in_client, org):
        resp = logged_in_client.put(
            f"/api/v1/orgs/{org.id}/workspaces/99999",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404


class TestWorkspaceDelete:
    """DELETE /api/v1/orgs/<id>/workspaces/<id>"""

    def test_delete_soft(self, logged_in_client, _db, org):
        from app.production.identity.workspace_model import Workspace
        ws = Workspace(tenant_id=org.id, name="Delete Me", slug="delete-me")
        _db.session.add(ws)
        _db.session.commit()
        resp = logged_in_client.delete(
            f"/api/v1/orgs/{org.id}/workspaces/{ws.id}"
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "deactivated"
        _db.session.expire_all()
        deleted = _db.session.get(Workspace, ws.id)
        assert deleted is not None
        assert deleted.is_active is False