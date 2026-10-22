"""Tests for Production Auth (Milestone X, D2).

Password reset, email verification, MFA, session revocation.

NOTE: the raw-token duplicate routes (/forgot-password, /reset-password/<token>,
/request-verification, /verify-email/<token>) were RETIRED — they never sent
email and leaked the raw token in the response body. These tests exercise the
canonical, rate-limited flow in app/auth_routes.py (/api/v1/auth/*), and
explicitly assert the token is NEVER returned to the client.
"""

import pytest


@pytest.fixture(scope="function")
def _db(app):
    from app import db
    with app.app_context():
        yield db


@pytest.fixture(scope="function", autouse=True)
def _clear_auth_state(app):
    """Clear auth state between tests — cleans DB-backed token tables."""
    with app.app_context():
        from app import db
        from app.auth import EmailVerificationToken, InvitationToken, PasswordResetToken
        db.session.query(PasswordResetToken).delete()
        db.session.query(EmailVerificationToken).delete()
        db.session.query(InvitationToken).delete()
        db.session.commit()
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
    """Canonical POST /api/v1/auth/forgot-password and /api/v1/auth/reset-password"""

    @pytest.fixture
    def mail_configured(self, monkeypatch):
        """Declare a configured mail transport for the token-lifecycle tests.

        G1.25 made an unconfigured transport a truthful 503 instead of "link has
        been sent". These tests assert the reset *token* lifecycle (creation,
        single use, expiry, minimum length), so they declare the configured case;
        the unconfigured case has its own test below. No message is sent: the
        suite's transport is non-sending by design.
        """
        from app.communication import email_transport_guard as guard

        monkeypatch.setattr(
            guard, "email_transport_state",
            lambda core=None: {
                "provider": "resend", "host": "", "has_resend_key": True,
                "has_smtp_credentials": False, "host_is_loopback": False,
            },
        )
        monkeypatch.setattr(guard, "isolation_verdict", lambda state: (True, "resend_with_key"))

    def test_forgot_password_unconfigured_mail_is_reported(self, client, admin_user):
        """Without a mail transport the endpoint must not claim an email was sent."""
        resp = client.post("/api/v1/auth/forgot-password",
                           json={"email": "admin4@test.com"})
        assert resp.status_code == 503
        body = resp.get_json()
        assert body["success"] is False
        assert body["delivery"] == "unconfigured"

    def test_forgot_password(self, client, admin_user, mail_configured):
        resp = client.post("/api/v1/auth/forgot-password",
                           json={"email": "admin4@test.com"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        # The raw reset token must NEVER be returned to the client (security)
        assert "_reset_token" not in body
        assert "token" not in body

    def test_forgot_password_unknown(self, client, mail_configured):
        resp = client.post("/api/v1/auth/forgot-password",
                           json={"email": "unknown@test.com"})
        assert resp.status_code == 200  # don't reveal existence

    def test_forgot_password_missing_email(self, client):
        resp = client.post("/api/v1/auth/forgot-password", json={})
        assert resp.status_code == 400

    def _latest_reset_token(self, _db):
        from app.auth import PasswordResetToken
        token_row = (
            PasswordResetToken.query
            .filter_by(email="admin4@test.com")
            .order_by(PasswordResetToken.created_at.desc())
            .first()
        )
        assert token_row is not None and not token_row.used
        return token_row.token

    def test_reset_flow(self, client, admin_user, _db, mail_configured):
        # Request reset — token is stored server-side ONLY
        reset_resp = client.post("/api/v1/auth/forgot-password",
                                 json={"email": "admin4@test.com"})
        assert reset_resp.status_code == 200
        token = self._latest_reset_token(_db)

        # Reset password with body token
        reset = client.post("/api/v1/auth/reset-password",
                            json={"token": token, "password": "newpassword"})
        assert reset.status_code == 200

        # Token is single-use — second attempt fails
        again = client.post("/api/v1/auth/reset-password",
                            json={"token": token, "password": "newpassword"})
        assert again.status_code == 400

    def test_reset_invalid_token(self, client):
        resp = client.post("/api/v1/auth/reset-password",
                           json={"token": "bad-token", "password": "newpassword"})
        assert resp.status_code == 400

    def test_reset_short_password(self, client, admin_user, _db, mail_configured):
        client.post("/api/v1/auth/forgot-password",
                    json={"email": "admin4@test.com"})
        token = self._latest_reset_token(_db)
        resp = client.post("/api/v1/auth/reset-password",
                           json={"token": token, "password": "12345"})
        assert resp.status_code == 400


class TestEmailVerification:
    """Canonical POST /api/v1/auth/request-verification and /api/v1/auth/verify-email"""

    def test_request_verification(self, client, admin_user):
        resp = client.post("/api/v1/auth/request-verification",
                           json={"email": "admin4@test.com"})
        assert resp.status_code == 200
        body = resp.get_json()
        # The raw verification token must NEVER be returned to the client
        assert "_verify_token" not in body
        assert "token" not in body

    def test_verify_flow(self, client, admin_user, _db):
        from app.auth import TeamMember
        req = client.post("/api/v1/auth/request-verification",
                          json={"email": "admin4@test.com"})
        assert req.status_code == 200

        member = TeamMember.query.filter_by(email="admin4@test.com").first()
        token = member.verify_token
        assert token  # a token was minted server-side

        resp = client.post("/api/v1/auth/verify-email", json={"token": token})
        assert resp.status_code == 200
        assert "Email verified successfully" in resp.get_json()["message"]
        _db.session.refresh(member)
        assert member.verified is True

    def test_verify_invalid_token(self, client):
        resp = client.post("/api/v1/auth/verify-email", json={"token": "bad-token"})
        assert resp.status_code == 400

    def test_verify_twice_fails(self, client, admin_user):
        from app.auth import TeamMember
        client.post("/api/v1/auth/request-verification",
                    json={"email": "admin4@test.com"})
        member = TeamMember.query.filter_by(email="admin4@test.com").first()
        token = member.verify_token

        first = client.post("/api/v1/auth/verify-email", json={"token": token})
        assert first.status_code == 200
        # Token is consumed — second attempt fails
        second = client.post("/api/v1/auth/verify-email", json={"token": token})
        assert second.status_code == 400


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
        # DB-backed MFA allows re-setup (replaces secret) — returns 200
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "secret" in data

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