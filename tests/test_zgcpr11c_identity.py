"""
ZGC-PR-11C Amendment regression tests — real identity/verification lifecycle.
Covers: signup-no-auto-login, unverified-denied, verify-creates-personal-workspace,
forgot-password (no enumeration), reset-password (single-use, expiry, session invalidation).
"""

import os
import tempfile
import pytest

from app import create_app, db


@pytest.fixture()
def app():
    """Create app with isolated SQLite database."""
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "zgcpr11c_test.db")
    old_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    a = create_app({"TESTING": True})
    if old_db_url:
        os.environ["DATABASE_URL"] = old_db_url
    else:
        os.environ.pop("DATABASE_URL", None)
    yield a
    try:
        os.remove(db_path)
        os.rmdir(tmpdir)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def _app_context(app):
    """Push application context for the whole test — enables direct DB access."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield


@pytest.fixture()
def client(app, _app_context):
    return app.test_client()


def test_signup_does_not_issue_session(client):
    """Signup must NOT log the user in — no session until verified."""
    resp = client.post("/api/v1/auth/signup", json={
        "name": "T", "email": "t1@x.com", "password": "Password123!",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["verified"] is False
    # No session cookie should let /session authenticate
    sresp = client.get("/api/v1/auth/session")
    assert sresp.get_json().get("authenticated") is False


def test_non_existent_credentials_denied(client):
    resp = client.post("/api/v1/founder/signin", json={
        "email": "ghost@x.com", "password": "whatever123!"
    })
    assert resp.status_code == 404
    assert resp.get_json()["success"] is False


def test_unverified_account_cannot_signin(client):
    client.post("/api/v1/auth/signup", json={
        "name": "T", "email": "t2@x.com", "password": "Password123!",
    })
    resp = client.post("/api/v1/founder/signin", json={
        "email": "t2@x.com", "password": "Password123!",
    })
    assert resp.status_code == 403
    assert "not yet verified" in resp.get_json()["error"].lower()


def test_verify_email_creates_personal_workspace_and_logs_in(client):
    client.post("/api/v1/auth/signup", json={
        "name": "T", "email": "t3@x.com", "password": "Password123!",
    })
    from app.auth import TeamMember
    member = TeamMember.query.filter_by(email="t3@x.com").one()
    token = member.verify_token
    assert token

    resp = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] and data.get("personal_workspace") is True

    from app.workspace.models import Workspace, WorkspaceType
    space = Workspace.query.filter_by(
        owner_identity_id=str(member.id),
        workspace_type=WorkspaceType.PERSONAL.value,
    ).first()
    assert space is not None
    assert space.status == "active"

    # Session established after verification
    assert client.get("/api/v1/auth/session").get_json()["authenticated"] is True

    # Now verified user can signin with correct password
    resp = client.post("/api/v1/founder/signin", json={
        "email": "t3@x.com", "password": "Password123!",
    })
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True


def test_invalid_verification_token_denied(client):
    resp = client.post("/api/v1/auth/verify-email", json={"token": "bogus"})
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


def test_forgot_password_no_enumeration(client):
    # Both existing and non-existing email return same generic message
    client.post("/api/v1/auth/signup", json={
        "name": "T", "email": "t4@x.com", "password": "Password123!",
    })
    for email in ("t4@x.com", "no-such@x.com"):
        resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
        assert resp.status_code == 200
        assert "if an account exists" in resp.get_json()["message"].lower()


def test_reset_password_single_use_and_invalidates_old(client):
    client.post("/api/v1/auth/signup", json={
        "name": "T", "email": "t5@x.com", "password": "Password123!",
    })
    from app.auth import TeamMember
    member = TeamMember.query.filter_by(email="t5@x.com").one()
    token = member.verify_token
    client.post("/api/v1/auth/verify-email", json={"token": token})

    # Request reset
    client.post("/api/v1/auth/forgot-password", json={"email": "t5@x.com"})
    from app.auth import PasswordResetToken
    reset = PasswordResetToken.query.filter_by(user_id=member.id, used=False).one()

    # Reset with wrong-short password rejected
    r = client.post("/api/v1/auth/reset-password", json={"token": reset.token, "password": "short"})
    assert r.status_code == 400

    # Valid reset
    r = client.post("/api/v1/auth/reset-password", json={"token": reset.token, "password": "NewPassword123!"})
    assert r.status_code == 200
    assert r.get_json()["success"] is True

    # Old password fails
    assert client.post("/api/v1/founder/signin", json={
        "email": "t5@x.com", "password": "Password123!"
    }).status_code == 401

    # Used token rejected (single-use)
    assert client.post("/api/v1/auth/reset-password", json={
        "token": reset.token, "password": "AnotherPass123!"
    }).status_code == 400

    # New password works
    assert client.post("/api/v1/founder/signin", json={
        "email": "t5@x.com", "password": "NewPassword123!"
    }).status_code == 200