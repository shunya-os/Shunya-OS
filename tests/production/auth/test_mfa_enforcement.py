"""G1.29 — MFA is a second factor, never a login.

Contract under test (all through real HTTP + the real session cookie):

* password-only login for an account without MFA issues a session;
* password-only login for an MFA account issues **no** session, only a pending
  transaction;
* that pending transaction is the only thing a challenge can complete;
* the transaction is user-bound, expiring, attempt-capped and single-use;
* a completed challenge yields a session that the protected API accepts.

`_validate_totp` is monkeypatched where the subject is the transaction binding;
one test drives the real validator so the wiring is not mocked away entirely.
"""
import time

import pytest

from app import db
from app.auth import TeamMember
from app.production.auth.mfa_models import MFAConfig


def _user(email="mfa1@test.com", with_mfa=True, verified=True):
    user = TeamMember(email=email, name="MFA User", role="admin",
                      is_active=True, verified=verified)
    user.set_password("Password123!")
    db.session.add(user)
    db.session.flush()
    if with_mfa:
        db.session.add(MFAConfig(user_id=user.id, secret="JBSWY3DPEHPK3PXP",
                                 enabled=True, recovery_codes=["recovery-1"]))
    db.session.commit()
    return user


def _session(client):
    with client.session_transaction() as sess:
        return dict(sess)


def _age_pending(client, seconds):
    with client.session_transaction() as sess:
        if "mfa_pending_at" in sess:
            sess["mfa_pending_at"] = time.time() - seconds


def _login(client, email="mfa1@test.com", password="Password123!"):
    return client.post("/login/password", json={"email": email, "password": password})


# ── primary step ──────────────────────────────────────────────────────


def test_login_without_mfa_issues_a_session(client):
    _user("plain@test.com", with_mfa=False)
    resp = _login(client, "plain@test.com")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    body = resp.get_json()
    assert body["success"] is True
    assert not body.get("mfa_required")
    assert "user_id" in _session(client)


def test_login_with_mfa_issues_no_session(client):
    user = _user()
    resp = _login(client)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True and body["mfa_required"] is True
    sess = _session(client)
    assert "user_id" not in sess, "the password step must not authenticate"
    assert sess.get("mfa_pending_user_id") == user.id


def test_spa_signin_route_also_requires_the_second_factor(client):
    """The SPA signs in through /api/v1/founder/signin — the path users take.

    G1.29-P2 found this third login route ungated: /login and /login/password were
    covered while the product's own client used this one, so the bypass survived.
    """
    user = _user("spa@test.com")
    resp = client.post("/api/v1/founder/signin", json={"email": "spa@test.com", "password": "Password123!"})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    body = resp.get_json()
    assert body["success"] is True and body["mfa_required"] is True
    sess = _session(client)
    assert "user_id" not in sess, "the SPA sign-in must not authenticate an MFA account"
    assert sess.get("mfa_pending_user_id") == user.id


def test_pending_transaction_does_not_grant_api_access(client):
    _user()
    _login(client)
    # A protected endpoint must still refuse: no user_id, only pending state.
    resp = client.get("/api/v1/objects")
    assert resp.status_code in (401, 403), resp.status_code


# ── challenge ────────────────────────────────────────────────────────


def test_challenge_without_pending_transaction_is_refused(client, monkeypatch):
    _user()
    monkeypatch.setattr("app.production.auth.mfa_routes._validate_totp", lambda s, c: True)
    resp = client.post("/mfa/challenge", json={"email": "mfa1@test.com", "code": "123456"})
    assert resp.status_code == 403
    assert "user_id" not in _session(client)


def test_valid_pending_transaction_plus_valid_code_authenticates(client, monkeypatch):
    _user()
    _login(client)
    monkeypatch.setattr("app.production.auth.mfa_routes._validate_totp", lambda s, c: True)
    resp = client.post("/mfa/challenge", json={"email": "mfa1@test.com", "code": "123456"})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    sess = _session(client)
    assert sess.get("user_id"), "the second factor completes the login"
    assert "mfa_pending_user_id" not in sess, "the transaction is consumed"


def test_replay_is_refused(client, monkeypatch):
    _user()
    _login(client)
    monkeypatch.setattr("app.production.auth.mfa_routes._validate_totp", lambda s, c: True)
    assert client.post("/mfa/challenge",
                       json={"email": "mfa1@test.com", "code": "123456"}).status_code == 200
    replay = client.post("/mfa/challenge",
                         json={"email": "mfa1@test.com", "code": "123456"})
    assert replay.status_code == 403


def test_expired_transaction_is_refused(client, monkeypatch):
    _user()
    _login(client)
    _age_pending(client, 6 * 60)
    monkeypatch.setattr("app.production.auth.mfa_routes._validate_totp", lambda s, c: True)
    resp = client.post("/mfa/challenge", json={"email": "mfa1@test.com", "code": "123456"})
    assert resp.status_code == 403
    assert "user_id" not in _session(client)


def test_transaction_cannot_be_steered_to_another_user(client, monkeypatch):
    _user()
    _user("mfa2@test.com")
    _login(client)  # pending for mfa1
    monkeypatch.setattr("app.production.auth.mfa_routes._validate_totp", lambda s, c: True)
    resp = client.post("/mfa/challenge", json={"email": "mfa2@test.com", "code": "123456"})
    assert resp.status_code == 403
    assert "user_id" not in _session(client)


def test_invalid_code_does_not_authenticate(client, monkeypatch):
    _user()
    _login(client)
    monkeypatch.setattr("app.production.auth.mfa_routes._validate_totp", lambda s, c: False)
    resp = client.post("/mfa/challenge", json={"email": "mfa1@test.com", "code": "000000"})
    assert resp.status_code == 401
    assert "user_id" not in _session(client)


def test_attempts_are_capped_and_the_transaction_is_dropped(client, monkeypatch):
    _user()
    _login(client)
    monkeypatch.setattr("app.production.auth.mfa_routes._validate_totp", lambda s, c: False)
    codes = [client.post("/mfa/challenge",
                         json={"email": "mfa1@test.com", "code": f"00000{i}"}).status_code
             for i in range(5)]
    assert 429 in codes, f"the fifth wrong code must exhaust the transaction: {codes}"
    assert "mfa_pending_user_id" not in _session(client)


def test_recovery_code_completes_the_login_and_disables_the_factor(client):
    user = _user()
    _login(client)
    resp = client.post("/mfa/challenge",
                       json={"email": "mfa1@test.com", "recovery_code": "recovery-1"})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert "user_id" in _session(client)
    config = MFAConfig.query.filter_by(user_id=user.id).first()
    assert config.enabled is False, "a used recovery code invalidates the factor"


def test_real_totp_validator_rejects_a_wrong_code(client):
    """One test without the monkeypatch: the validator is genuinely wired in."""
    _user()
    _login(client)
    resp = client.post("/mfa/challenge", json={"email": "mfa1@test.com", "code": "000000"})
    assert resp.status_code in (401, 429)
    assert "user_id" not in _session(client)
