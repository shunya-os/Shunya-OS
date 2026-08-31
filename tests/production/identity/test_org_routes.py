"""Tests for Organization CRUD API (Milestone X, D1.1).

Uses the production app factory with in-memory SQLite database.
Fully self-contained fixtures — no dependencies on conftest fixtures
that may have missing fixture dependencies.
"""

import pytest


@pytest.fixture(scope="function")
def _db(app):
    """Provide the database instance within app context."""
    from app import db
    with app.app_context():
        yield db


@pytest.fixture(scope="function")
def admin_user(app, _db):
    """Create an admin TeamMember."""
    from app.auth import TeamMember
    user = TeamMember(
        name="Admin User",
        email="admin@test.com",
        role="admin",
        is_active=True,
    )
    user.set_password("password123")
    user.generate_token()
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def logged_in_client(app, client, admin_user):
    """Test client with active admin session."""
    with client.session_transaction() as session:
        session["user_id"] = admin_user.id
        session["_fresh"] = True
    return client


@pytest.fixture(scope="function")
def test_org(app, _db):
    """Create a sample organization for tests."""
    from app.models import Organization
    org = Organization(
        name="Test Org Inc",
        slug="test-org-inc",
        business_type="travel",
        is_active=True,
    )
    _db.session.add(org)
    _db.session.commit()
    return org


class TestOrgList:
    """GET /api/v1/orgs"""

    def test_list_orgs_empty(self, logged_in_client):
        """Should return empty list when no orgs exist."""
        resp = logged_in_client.get("/api/v1/orgs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_orgs_with_data(self, logged_in_client, test_org):
        """Should return existing orgs."""
        resp = logged_in_client.get("/api/v1/orgs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        first = data["data"][0]
        assert "id" in first
        assert "company_name" in first
        assert "slug" in first


class TestOrgCreate:
    """POST /api/v1/orgs"""

    def test_create_org_success(self, logged_in_client):
        """Should create a new organization."""
        resp = logged_in_client.post(
            "/api/v1/orgs",
            json={"company_name": "Test Organization"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["company_name"] == "Test Organization"
        assert data["data"]["slug"] == "test-organization"
        assert data["data"]["is_active"] is True
        assert data["data"]["plan"] == "free"

    def test_create_org_with_all_fields(self, logged_in_client):
        """Should create with optional fields."""
        resp = logged_in_client.post(
            "/api/v1/orgs",
            json={
                "company_name": "Full Test Corp",
                "business_type": "healthcare",
                "plan": "pro",
                "max_team_members": 50,
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["business_type"] == "healthcare"
        assert data["data"]["plan"] == "pro"
        assert data["data"]["max_team_members"] == 50

    def test_create_org_missing_name(self, logged_in_client):
        """Should reject creation without company_name."""
        resp = logged_in_client.post("/api/v1/orgs", json={})
        assert resp.status_code == 400

    def test_create_org_empty_name(self, logged_in_client):
        """Should reject creation with empty company_name."""
        resp = logged_in_client.post(
            "/api/v1/orgs", json={"company_name": ""}
        )
        assert resp.status_code == 400

    def test_create_org_duplicate_slug(self, logged_in_client, test_org):
        """Should handle duplicate company names with unique slugs."""
        resp = logged_in_client.post(
            "/api/v1/orgs",
            json={"company_name": "Test Org Inc"},
        )
        assert resp.status_code == 201
        slug1 = resp.get_json()["data"]["slug"]
        assert slug1 != "test-org-inc"  # should have a suffix


class TestOrgGet:
    """GET /api/v1/orgs/<id>"""

    def test_get_org_success(self, logged_in_client, test_org):
        """Should return an org by ID."""
        resp = logged_in_client.get(f"/api/v1/orgs/{test_org.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == test_org.id
        assert data["data"]["company_name"] == "Test Org Inc"

    def test_get_org_not_found(self, logged_in_client):
        """Should return 404 for non-existent org."""
        resp = logged_in_client.get("/api/v1/orgs/99999")
        assert resp.status_code == 404


class TestOrgUpdate:
    """PUT /api/v1/orgs/<id>"""

    def test_update_org_name(self, logged_in_client, test_org):
        """Should update the company name."""
        resp = logged_in_client.put(
            f"/api/v1/orgs/{test_org.id}",
            json={"company_name": "Updated Name"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["company_name"] == "Updated Name"

    def test_update_org_business_type(self, logged_in_client, test_org):
        """Should update business type."""
        resp = logged_in_client.put(
            f"/api/v1/orgs/{test_org.id}",
            json={"business_type": "retail"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["business_type"] == "retail"

    def test_update_org_partial(self, logged_in_client, test_org):
        """Should allow partial updates."""
        resp = logged_in_client.put(
            f"/api/v1/orgs/{test_org.id}",
            json={"business_type": "retail"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["business_type"] == "retail"
        assert data["data"]["company_name"] == "Test Org Inc"

    def test_update_org_not_found(self, logged_in_client):
        """Should return 404 for non-existent org."""
        resp = logged_in_client.put(
            "/api/v1/orgs/99999",
            json={"company_name": "Nope"},
        )
        assert resp.status_code == 404


class TestOrgDelete:
    """DELETE /api/v1/orgs/<id>"""

    def test_delete_org_soft(self, logged_in_client, test_org, _db):
        """Should soft-delete (deactivate) an org."""
        resp = logged_in_client.delete(f"/api/v1/orgs/{test_org.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["status"] == "deactivated"

        from app.models import Organization
        org = _db.session.get(Organization, test_org.id)
        assert org is not None
        assert org.is_active is False

    def test_delete_org_then_get_returns_404(self, logged_in_client, test_org):
        """Should return 404 for deleted orgs on GET."""
        logged_in_client.delete(f"/api/v1/orgs/{test_org.id}")
        resp = logged_in_client.get(f"/api/v1/orgs/{test_org.id}")
        assert resp.status_code == 404


class TestOrgAuth:
    """Endpoints should require authentication."""

    def test_list_requires_auth(self, client):
        """GET /api/v1/orgs without login should redirect."""
        resp = client.get("/api/v1/orgs")
        assert resp.status_code in (302, 401)

    def test_create_requires_auth(self, client):
        """POST /api/v1/orgs without login should be rejected."""
        resp = client.post(
            "/api/v1/orgs",
            json={"company_name": "Unauthenticated"},
        )
        assert resp.status_code in (302, 401)