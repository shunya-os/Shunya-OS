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
def logged_in_client(app, client, admin_user):
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["_fresh"] = True
    return client


@pytest.fixture(scope="function")
def org(app, _db):
    from app.models import Organization
    o = Organization(name="Workspace Test Org", slug="ws-test-org", is_active=True)
    _db.session.add(o)
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