"""Tests for Invitation System (Milestone X, D1.4).
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
        name="Admin", email="admin@test.com",
        role="admin", is_active=True,
    )
    user.set_password("password123")
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
    o = Organization(name="Invite Org", slug="invite-org", is_active=True)
    _db.session.add(o)
    _db.session.commit()
    return o


class TestInviteCreate:
    """POST /api/v1/orgs/<id>/invitations"""

    def test_create_success(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "newuser@test.com", "role": "agent"},
        )
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "agent"
        assert data["status"] == "pending"
        assert "token" in data

    def test_create_default_role(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "default@test.com"},
        )
        assert resp.status_code == 201
        assert resp.get_json()["data"]["role"] == "agent"

    def test_create_missing_email(self, logged_in_client, org):
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"role": "admin"},
        )
        assert resp.status_code == 400

    def test_create_duplicate_user(self, logged_in_client, _db, org):
        from app.models import OrgMember
        u = OrgMember(
            organization_id=org.id, identity_id="test_dup",
            name="Existing", email="exists@test.com", role="member",
        )
        _db.session.add(u)
        _db.session.commit()
        resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "exists@test.com"},
        )
        assert resp.status_code == 400


class TestInviteGet:
    """GET /api/v1/orgs/invitations/<token>"""

    def test_get_invitation(self, logged_in_client, org):
        create_resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "get@test.com"},
        )
        token = create_resp.get_json()["data"]["token"]

        resp = logged_in_client.get(f"/api/v1/orgs/invitations/{token}")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["email"] == "get@test.com"

    def test_get_invalid_token(self, logged_in_client):
        resp = logged_in_client.get(
            "/api/v1/orgs/invitations/invalid-token-123"
        )
        assert resp.status_code == 404


class TestInviteAccept:
    """POST /api/v1/orgs/invitations/<token>/accept"""

    def test_accept_success(self, logged_in_client, org, _db):
        create_resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "accept@test.com", "role": "manager"},
        )
        token = create_resp.get_json()["data"]["token"]

        resp = logged_in_client.post(
            f"/api/v1/orgs/invitations/{token}/accept",
            json={"name": "Accepted User", "password": "secure123"},
        )
        assert resp.status_code == 201
        data = resp.get_json()["data"]
        assert data["email"] == "accept@test.com"
        assert data["role"] == "manager"

        from app.auth import TeamMember
        user = TeamMember.query.filter_by(email="accept@test.com").first()
        assert user is not None
        assert user.name == "Accepted User"

    def test_accept_missing_name(self, logged_in_client, org):
        create_resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "noname@test.com"},
        )
        token = create_resp.get_json()["data"]["token"]

        resp = logged_in_client.post(
            f"/api/v1/orgs/invitations/{token}/accept",
            json={"password": "secure123"},
        )
        assert resp.status_code == 400

    def test_accept_short_password(self, logged_in_client, org):
        create_resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "badpw@test.com"},
        )
        token = create_resp.get_json()["data"]["token"]

        resp = logged_in_client.post(
            f"/api/v1/orgs/invitations/{token}/accept",
            json={"name": "Bad PW", "password": "12345"},
        )
        assert resp.status_code == 400

    def test_accept_invalid_token(self, logged_in_client):
        resp = logged_in_client.post(
            "/api/v1/orgs/invitations/bad-token/accept",
            json={"name": "Test", "password": "secure123"},
        )
        assert resp.status_code == 404

    def test_accept_twice_fails(self, logged_in_client, org):
        create_resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "twice@test.com"},
        )
        token = create_resp.get_json()["data"]["token"]

        logged_in_client.post(
            f"/api/v1/orgs/invitations/{token}/accept",
            json={"name": "First", "password": "secure123"},
        )
        resp = logged_in_client.post(
            f"/api/v1/orgs/invitations/{token}/accept",
            json={"name": "Second", "password": "secure123"},
        )
        assert resp.status_code == 404  # already accepted


class TestInviteRevoke:
    """DELETE /api/v1/orgs/<id>/invitations/<id>"""

    def test_revoke_success(self, logged_in_client, org):
        create_resp = logged_in_client.post(
            f"/api/v1/orgs/{org.id}/invitations",
            json={"email": "revoke@test.com"},
        )
        inv_id = create_resp.get_json()["data"]["id"]

        resp = logged_in_client.delete(
            f"/api/v1/orgs/{org.id}/invitations/{inv_id}"
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "revoked"

    def test_revoke_not_found(self, logged_in_client, org):
        resp = logged_in_client.delete(
            f"/api/v1/orgs/{org.id}/invitations/99999"
        )
        assert resp.status_code == 404