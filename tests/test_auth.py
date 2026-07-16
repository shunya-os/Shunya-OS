"""Tests for authentication routes — login, signup, logout, session, and access control."""
import hashlib
import pytest
from flask import session


# ---------------------------------------------------------------------------
# Login page (GET)
# ---------------------------------------------------------------------------


class TestLoginPage:
    def test_login_page_returns_200(self, client):
        """GET /auth/login returns the login page."""
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert b"login" in resp.data.lower() or b"sign in" in resp.data.lower()

    def test_login_page_redirects_when_already_logged_in(self, logged_in_client):
        """GET /auth/login redirects to dashboard when user is authenticated."""
        resp = logged_in_client.get("/auth/login")
        assert resp.status_code == 302
        assert resp.location.endswith("/")


# ---------------------------------------------------------------------------
# Login — password (POST)
# ---------------------------------------------------------------------------


class TestLoginPassword:
    LOGIN_URL = "/auth/login/password"

    def test_valid_credentials_creates_session(self, client, db, tenant):
        """POST /auth/login/password with valid creds returns success and sets session token."""
        user = self._create_user(db, tenant, "valid@test.com", "correct-password")
        resp = client.post(
            self.LOGIN_URL,
            json={"email": "valid@test.com", "password": "correct-password"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "/" in data["redirect"]

        # Verify a session record was created in the DB
        from app.models import UserSession
        sess = UserSession.query.filter_by(user_id=user.id, is_active=True).first()
        assert sess is not None
        assert sess.expires_at is not None

    def test_invalid_password_returns_error(self, client, db, tenant):
        """POST /auth/login/password with wrong password returns 401."""
        self._create_user(db, tenant, "wrongpw@test.com", "secret123")
        resp = client.post(
            self.LOGIN_URL,
            json={"email": "wrongpw@test.com", "password": "wrong-password"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert "error" in data
        assert "invalid" in data["error"].lower()

    def test_nonexistent_email_returns_error(self, client):
        """POST /auth/login/password with unregistered email returns 401."""
        resp = client.post(
            self.LOGIN_URL,
            json={"email": "nobody@example.com", "password": "anything"},
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert "error" in data

    def test_missing_email_returns_error(self, client):
        """POST /auth/login/password without email returns 400."""
        resp = client.post(
            self.LOGIN_URL,
            json={"password": "somepass"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_missing_password_returns_error(self, client):
        """POST /auth/login/password without password returns 400."""
        resp = client.post(
            self.LOGIN_URL,
            json={"email": "test@test.com"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_empty_form_data_returns_error(self, client):
        """POST /auth/login/password with empty email and password returns 400."""
        resp = client.post(
            self.LOGIN_URL,
            json={"email": "", "password": ""},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _create_user(db, tenant, email, raw_password):
        from app.models import TeamMember
        user = TeamMember(
            tenant_id=tenant.id,
            name="Test User",
            email=email,
            role="admin",
        )
        user.set_password(raw_password)
        db.session.add(user)
        db.session.commit()
        return user


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class TestLogout:
    def test_logout_clears_session_and_redirects(self, logged_in_client):
        """GET /auth/logout clears the session and redirects to login page."""
        # Verify session is active before
        with logged_in_client.session_transaction() as sess:
            assert "session_token" in sess

        resp = logged_in_client.get("/auth/logout")

        # Redirect to login page
        assert resp.status_code == 302
        assert "auth/login" in resp.location

        # Session should be cleared
        with logged_in_client.session_transaction() as sess:
            assert "session_token" not in sess
            assert "user_id" not in sess

    def test_logout_deactivates_session_record(self, client, db, tenant):
        """POST /auth/login/password then GET /auth/logout marks the UserSession as inactive."""
        import hashlib

        # Create user with proper password
        from app.models import TeamMember
        user = TeamMember(
            tenant_id=tenant.id,
            name="Logout Tester",
            email="logouttest@test.com",
            role="admin",
        )
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()

        # Login to create a proper session
        resp = client.post(
            "/auth/login/password",
            json={"email": "logouttest@test.com", "password": "testpass"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        # Get the session token from Flask's session cookie
        from app.models import UserSession
        # There should be exactly one active session for this user
        sess = UserSession.query.filter_by(user_id=user.id, is_active=True).first()
        assert sess is not None
        assert sess.is_active is True

        # Logout
        client.get("/auth/logout")

        # Session record should now be inactive
        assert sess.is_active is False


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------


class TestSignupPage:
    def test_signup_page_returns_200(self, client):
        """GET /auth/signup returns the signup page."""
        resp = client.get("/auth/signup")
        assert resp.status_code == 200
        assert b"signup" in resp.data.lower() or b"sign up" in resp.data.lower()

    def test_signup_page_redirects_when_already_logged_in(self, logged_in_client):
        """GET /auth/signup redirects to dashboard when user is authenticated."""
        resp = logged_in_client.get("/auth/signup")
        assert resp.status_code == 302
        assert resp.location.endswith("/")


class TestSignupPost:
    SIGNUP_URL = "/auth/signup"

    def test_signup_creates_tenant_and_team_member(self, client, db):
        """POST /auth/signup creates a Tenant and TeamMember, returns success."""
        from app.utils import hash_token
        whatsapp = "+15551234567"
        with client.session_transaction() as sess:
            sess["signup_otp_verified"] = hash_token(whatsapp)  # Bypass OTP check

        resp = client.post(
            self.SIGNUP_URL,
            json={
                "name": "Jane Doe",
                "email": "jane@newco.com",
                "password": "securepass",
                "company_name": "NewCo",
                "whatsapp_phone": whatsapp,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "/" in data["redirect"]

        # Verify tenant was created
        from app.models import Tenant
        tenant = Tenant.query.filter_by(company_name="NewCo").first()
        assert tenant is not None

        # Verify team member was created
        from app.models import TeamMember
        user = TeamMember.query.filter_by(email="jane@newco.com").first()
        assert user is not None
        assert user.tenant_id == tenant.id
        assert user.role == "admin"
        assert user.check_password("securepass") is True

    def test_signup_duplicate_email_returns_error(self, client, db, tenant, admin_user):
        """POST /auth/signup with an already-registered email returns 409."""
        from app.utils import hash_token
        with client.session_transaction() as sess:
            sess["signup_otp_verified"] = hash_token(admin_user.whatsapp_phone or admin_user.phone or "+15551234567")

        resp = client.post(
            self.SIGNUP_URL,
            json={
                "name": "Duplicate",
                "email": admin_user.email,  # already exists from conftest
                "password": "whatever",
                "company_name": "DupCo",
                "whatsapp_phone": "+15551234567",
            },
        )
        assert resp.status_code == 409
        data = resp.get_json()
        assert "error" in data
        assert "already" in data["error"].lower()

    def test_signup_missing_fields_returns_error(self, client):
        """POST /auth/signup without required fields returns 400."""
        resp = client.post(
            self.SIGNUP_URL,
            json={"name": "No Email"},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_signup_password_hash_is_set(self, client, db):
        """POST /auth/signup stores a properly salted password hash."""
        from app.utils import hash_token
        whatsapp = "+15551234567"
        with client.session_transaction() as sess:
            sess["signup_otp_verified"] = hash_token(whatsapp)

        client.post(
            self.SIGNUP_URL,
            json={
                "name": "Hash Check",
                "email": "hash@test.com",
                "password": "mypassword",
                "company_name": "HashCo",
                "whatsapp_phone": whatsapp,
            },
        )
        from app.models import TeamMember
        user = TeamMember.query.filter_by(email="hash@test.com").first()
        assert user is not None
        assert user.password_hash is not None
        assert "$" in user.password_hash  # salt$hash format
        assert user.check_password("mypassword") is True
        assert user.check_password("wrong") is False


# ---------------------------------------------------------------------------
# Access control — protected routes
# ---------------------------------------------------------------------------


class TestAccessControl:
    def test_protected_route_redirects_to_login(self, client):
        """Accessing a page behind login_required without auth redirects to /auth/login."""
        resp = client.get("/settings")
        assert resp.status_code == 302
        assert "auth/login" in resp.location

    def test_protected_route_returns_json_401_for_api(self, client):
        """Accessing a login_required route with JSON Content-Type without auth returns 401 JSON."""
        # The auth middleware checks request.is_json, which requires
        # Content-Type: application/json, not just Accept header.
        resp = client.get(
            "/auth/sessions",
            content_type="application/json",
        )
        assert resp.status_code == 401
        data = resp.get_json()
        assert "Authentication required" in data.get("error", "")
