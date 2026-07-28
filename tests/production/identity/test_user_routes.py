"""Tests for User Management API (Milestone X, D1.3).
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
    from app.tenant import Tenant, TenantTheme
    o = Tenant(company_name="User Test Org", slug="user-test-org", is_active=True)
    _db.session.add(o)
    _db.session.flush()
    _db.session.add(TenantTheme(tenant_id=o.id))
    _db.session.commit()
    return o


class TestUserList:
    """GET /api/v1/orgs/<id>/users"""

    def test_list_empty(self, logged_in_client, org):
        resp = logged_in_client.get(f"/api/v1/orgs/{org.id}/users")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_list_with_data(self, logged_in_client, _db, org):
        from app.auth import TeamMember
        u = TeamMember(name="List User", email="list@test.com",
                       role="agent", is_active=True)
        u.set_password("pass123456")
        _db.session.add(u)
        _db.session.commit()
        resp = logged_in_client.get(f"/api/v1/orgs/{org.id}/users")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        emails = [d["email"] for d in data]
        assert "list@test.com" in emails


class TestUserCreate:
    """POST /api/v1/orgs/<id>/users"""

    def test_create_success(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/users",
            json={"name": "New User", "email": "new@test.com",
                  "password": "secure123", "role": "agent"},
        )
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["name"] == "New User"
        assert data["email"] == "new@test.com"
        assert data["role"] == "agent"
        assert data["is_active"] is True

    def test_create_minimal(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/users",
            json={"name": "Minimal", "email": "min@test.com",
                  "password": "secure123"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["data"]["role"] == "agent"  # default

    def test_create_missing_name(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/users",
            json={"email": "no@name.com", "password": "secure123"},
        )
        assert resp.status_code == 400

    def test_create_missing_email(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/users",
            json={"name": "No Email", "password": "secure123"},
        )
        assert resp.status_code == 400

    def test_create_short_password(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/users",
            json={"name": "Bad Pass", "email": "bad@test.com",
                  "password": "12345"},
        )
        assert resp.status_code == 400

    def test_create_duplicate_email(self, logged_in_client, _db, org):
        from app.auth import TeamMember
        u = TeamMember(name="Existing", email="dup@test.com",
                       role="agent", is_active=True)
        u.set_password("pass123456")
        _db.session.add(u)
        _db.session.commit()
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/users",
            json={"name": "Dup", "email": "dup@test.com",
                  "password": "secure123"},
        )
        assert resp.status_code == 400

    def test_create_invalid_role(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/users",
            json={"name": "Bad Role", "email": "role@test.com",
                  "password": "secure123", "role": "superadmin"},
        )
        assert resp.status_code == 400


class TestUserGet:
    """GET /api/v1/orgs/<id>/users/<id>"""

    def test_get_success(self, logged_in_client, _db, org):
        from app.auth import TeamMember
        u = TeamMember(name="Get User", email="get@test.com",
                       role="manager", is_active=True)
        u.set_password("pass123456")
        _db.session.add(u)
        _db.session.commit()
        resp = logged_in_client.get(f"/api/v1/orgs/{org.id}/users/{u.id}")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["email"] == "get@test.com"

    def test_get_not_found(self, logged_in_client, org):
        resp = logged_in_client.get(f"/api/v1/orgs/{org.id}/users/99999")
        assert resp.status_code == 404


class TestUserUpdate:
    """PUT /api/v1/orgs/<id>/users/<id>"""

    def test_update_name(self, logged_in_client, _db, org):
        from app.auth import TeamMember
        u = TeamMember(name="Original", email="orig@test.com",
                       role="agent", is_active=True)
        u.set_password("pass123456")
        _db.session.add(u)
        _db.session.commit()
        resp = logged_in_client.put(
            f"/api/v1/orgs/{org.id}/users/{u.id}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["name"] == "Updated"

    def test_update_role(self, logged_in_client, _db, org):
        from app.auth import TeamMember
        u = TeamMember(name="Role User", email="roleup@test.com",
                       role="agent", is_active=True)
        u.set_password("pass123456")
        _db.session.add(u)
        _db.session.commit()
        resp = logged_in_client.put(
            f"/api/v1/orgs/{org.id}/users/{u.id}",
            json={"role": "manager"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["role"] == "manager"

    def test_update_password(self, logged_in_client, _db, org):
        from app.auth import TeamMember
        u = TeamMember(name="Pass User", email="passup@test.com",
                       role="agent", is_active=True)
        u.set_password("oldpassword")
        _db.session.add(u)
        _db.session.commit()
        old_hash = u.password_hash
        resp = logged_in_client.put(
            f"/api/v1/orgs/{org.id}/users/{u.id}",
            json={"password": "newpassword"},
        )
        assert resp.status_code == 200
        _db.session.refresh(u)
        assert u.password_hash != old_hash

    def test_update_not_found(self, logged_in_client, org):
        resp = logged_in_client.put(
            f"/api/v1/orgs/{org.id}/users/99999",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404


class TestUserDelete:
    """DELETE /api/v1/orgs/<id>/users/<id>"""

    def test_delete_soft(self, logged_in_client, _db, org):
        from app.auth import TeamMember
        u = TeamMember(name="Delete User", email="del@test.com",
                       role="agent", is_active=True)
        u.set_password("pass123456")
        _db.session.add(u)
        _db.session.commit()
        resp = logged_in_client.delete(f"/api/v1/orgs/{org.id}/users/{u.id}")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "deactivated"
        _db.session.expire_all()
        deleted = _db.session.get(TeamMember, u.id)
        assert deleted.is_active is False