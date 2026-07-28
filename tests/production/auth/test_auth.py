"""Tests for Production Auth (Milestone X, D2).

Password reset, email verification, MFA, session revocation.
"""

import pytest


@pytest.fixture(scope="function")
def _db(app):
    from app import db
    with app.app_context():
        yield db


@pytest.fixture(scope="function", autouse=True)
def _clear_auth_state():
    """Clear module-level auth state between tests."""
    from app.production.auth import password_reset_routes
    from app.production.auth import email_verification_routes
    from app.production.auth import mfa_routes
    from app.production.auth import session_routes
    password_reset_routes._reset_tokens.clear()
    email_verification_routes._verification_tokens.clear()
    mfa_routes._mfa_state.clear()
    session_routes._session_versions.clear()
    session_routes._devices.clear()
    yield


@pytest.fixture(scope="function")
def admin_user(app, _db):
    from app.auth import TeamMember
    user = TeamMember(
        name="Admin", email="admin4@test.com",
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


class TestPasswordReset:
    """POST /auth/forgot-password and POST /auth/reset-password/<token>"""

    def test_forgot_password(self, client, admin_user):
        resp = client.post("/forgot-password",
                           json={"email": "admin4@test.com"})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_forgot_password_unknown(self, client):
        resp = client.post("/forgot-password",
                           json={"email": "unknown@test.com"})
        assert resp.status_code == 200  # don't reveal existence

    def test_forgot_password_missing_email(self, client):
        resp = client.post("/forgot-password", json={})
        assert resp.status_code == 400

    def test_reset_flow(self, client, admin_user):
        # Request reset
        reset_resp = client.post("/forgot-password",
                                 json={"email": "admin4@test.com"})
        token = reset_resp.get_json()["_reset_token"]

        # Verify token
        verify = client.get(f"/reset-password/{token}")
        assert verify.status_code == 200

        # Reset password
        reset = client.post(f"/reset-password/{token}",
                            json={"password": "newpassword"})
        assert reset.status_code == 200

        # Verify old password no longer works
        assert client.get(f"/reset-password/{token}").status_code == 404

    def test_reset_invalid_token(self, client):
        resp = client.post("/reset-password/bad-token",
                           json={"password": "newpassword"})
        assert resp.status_code == 404

    def test_reset_short_password(self, client, admin_user):
        reset_resp = client.post("/forgot-password",
                                 json={"email": "admin4@test.com"})
        token = reset_resp.get_json()["_reset_token"]
        resp = client.post(f"/reset-password/{token}",
                           json={"password": "12345"})
        assert resp.status_code == 400


class TestEmailVerification:
    """POST /request-verification and GET /verify-email/<token>"""

    def test_request_verification(self, client, admin_user):
        resp = client.post("/request-verification",
                           json={"email": "admin4@test.com"})
        assert resp.status_code == 200

    def test_verify_flow(self, client, admin_user):
        req = client.post("/request-verification",
                          json={"email": "admin4@test.com"})
        token = req.get_json()["_verify_token"]

        resp = client.get(f"/verify-email/{token}")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Email verified successfully"

    def test_verify_invalid_token(self, client):
        resp = client.get("/verify-email/bad-token")
        assert resp.status_code == 404

    def test_verify_twice_fails(self, client, admin_user):
        req = client.post("/request-verification",
                          json={"email": "admin4@test.com"})
        token = req.get_json()["_verify_token"]
        client.get(f"/verify-email/{token}")
        resp = client.get(f"/verify-email/{token}")
        assert resp.status_code == 404


class TestMFA:
    """MFA setup, verify, disable, challenge"""

    def test_mfa_setup(self, logged_in_client):
        resp = logged_in_client.post("/mfa/setup")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "secret" in data
        assert "uri" in data
        assert len(data["recovery_codes"]) == 10

    def test_mfa_setup_twice(self, logged_in_client):
        logged_in_client.post("/mfa/setup")
        resp = logged_in_client.post("/mfa/setup")
        assert resp.status_code == 400

    def test_mfa_verify_invalid_code(self, logged_in_client):
        logged_in_client.post("/mfa/setup")
        resp = logged_in_client.post("/mfa/verify",
                                     json={"code": "000000"})
        # Invalid code should fail
        assert resp.status_code == 400

    def test_mfa_disable(self, logged_in_client):
        logged_in_client.post("/mfa/setup")
        resp = logged_in_client.post("/mfa/disable",
                                     json={"password": "pass123456"})
        assert resp.status_code == 200

    def test_mfa_disable_wrong_password(self, logged_in_client):
        logged_in_client.post("/mfa/setup")
        resp = logged_in_client.post("/mfa/disable",
                                     json={"password": "wrong"})
        assert resp.status_code == 400


class TestSessionRevocation:
    """Session revocation and device management"""

    def test_revoke_sessions(self, logged_in_client):
        resp = logged_in_client.post("/revoke-sessions")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "All sessions have been revoked"

    def test_list_devices(self, logged_in_client):
        resp = logged_in_client.get("/devices")
        assert resp.status_code == 200
        assert "data" in resp.get_json()