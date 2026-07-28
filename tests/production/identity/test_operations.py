"""Tests for Org Switching, Onboarding, and Lifecycle APIs (D1.5-1.7).
"""

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
        name="Admin", email="admin3@test.com",
        role="admin", is_active=True,
    )
    user.set_password("pass123456")
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
    from app.tenant import Tenant, TenantTheme
    o = Tenant(company_name="Lifecycle Org", slug="lc-org", is_active=True)
    _db.session.add(o)
    _db.session.flush()
    _db.session.add(TenantTheme(tenant_id=o.id))
    _db.session.commit()
    return o


class TestOrgSwitch:
    """POST /api/v1/orgs/switch/<id>"""

    def test_switch_success(self, logged_in_client, org):
        resp = logged_in_client.post(f"/api/v1/orgs/switch/{org.id}")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["company_name"] == "Lifecycle Org"

    def test_switch_not_found(self, logged_in_client):
        resp = logged_in_client.post("/api/v1/orgs/switch/99999")
        assert resp.status_code == 404

    def test_get_current(self, logged_in_client, org):
        logged_in_client.post(f"/api/v1/orgs/switch/{org.id}")
        resp = logged_in_client.get("/api/v1/orgs/current")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["id"] == org.id


class TestOrgLifecycle:
    """POST /api/v1/orgs/<id>/activate|deactivate|archive"""

    def test_deactivate(self, logged_in_client, org):
        resp = logged_in_client.post(f"/api/v1/orgs/{org.id}/deactivate")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "deactivated"

    def test_activate(self, logged_in_client, _db, org):
        org.is_active = False
        _db.session.commit()
        resp = logged_in_client.post(f"/api/v1/orgs/{org.id}/activate")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "activated"

    def test_archive(self, logged_in_client, org):
        resp = logged_in_client.post(f"/api/v1/orgs/{org.id}/archive")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "archived"


class TestOnboarding:
    """Onboarding status and step management."""

    def test_get_status(self, logged_in_client):
        resp = logged_in_client.get("/api/v1/orgs/onboarding/status")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["current_step"] == "profile"
        assert not data["is_complete"]

    def test_advance_step(self, logged_in_client):
        resp = logged_in_client.put(
            "/api/v1/orgs/onboarding/step/org_setup"
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["current_step"] == "org_setup"
        assert "profile" in data["completed_steps"]

    def test_complete_onboarding(self, logged_in_client):
        for step in ["profile", "org_setup", "invite_team", "workspace"]:
            logged_in_client.put(f"/api/v1/orgs/onboarding/step/{step}")
        resp = logged_in_client.put(
            "/api/v1/orgs/onboarding/step/complete"
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["is_complete"]

    def test_invalid_step(self, logged_in_client):
        resp = logged_in_client.put(
            "/api/v1/orgs/onboarding/step/invalid_step"
        )
        assert resp.status_code == 400

    def test_reset(self, logged_in_client):
        logged_in_client.put("/api/v1/orgs/onboarding/step/org_setup")
        resp = logged_in_client.post("/api/v1/orgs/onboarding/reset")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["current_step"] == "profile"