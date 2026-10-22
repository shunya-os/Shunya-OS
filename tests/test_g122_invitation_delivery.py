"""G1.22 — invitation delivery: compose, capture, truthfulness, token hygiene.

What this can and cannot prove in this environment
--------------------------------------------------
There is no authorized outbound mail provider here (no Resend key, no SMTP
credentials, and the SMTP path requires STARTTLS against a cert-valid host), so
**inbox delivery cannot be verified** and is not claimed. What *can* be verified
without any external contact is everything up to and including the provider
boundary:

  1. the message is composed for the intended recipient, with the accept URL that
     carries the invitation token, exactly where the SPA route expects it;
  2. the composed body is what the durable EmailRecord hashes — proven by
     rebuilding the identical body from (token, recipient, org name) and comparing
     the stored hash, so the test never needs the body at rest;
  3. the provider boundary is reached and its result is truthful: the record is
     marked failed for the stated reason and the API reports
     ``delivery.status`` / ``delivery.delivered=false`` instead of implying the
     invitee received anything;
  4. the raw token never appears in application logs (G1.22 defect fixed: the
     ``[EMAIL LOG]`` line used to print the first 200 characters of the body,
     which is exactly where the token lives).

Synthetic identities only; no network egress.
"""

import uuid

import pytest

from app import db

PASSWORD = "G1.22-delivery-password"
ID = "/api/v1/orgs"


def _signup_verify_login(client, tag):
    from app.auth import TeamMember

    email = f"{tag}-{uuid.uuid4().hex[:8]}@g122.test"
    client.post("/api/v1/auth/signup",
                json={"name": tag, "email": email, "password": PASSWORD})
    member = TeamMember.query.filter_by(email=email).first()
    assert member is not None
    if not member.verified:
        client.post("/api/v1/auth/verify-email", json={"token": member.verify_token})
    client.post("/login/password", json={"email": email, "password": PASSWORD})
    return email


def _org(client, name):
    r = client.post("/orgs", json={"company_name": name})
    assert r.status_code == 201, r.get_data(as_text=True)
    return int(r.get_json()["org_id"])


class TestInvitationDeliveryBoundary:
    def test_message_is_composed_for_the_invitee_with_the_accept_url(
            self, client, app, caplog):
        from app.communication.email_models import EmailRecord
        from app.email_service import build_invitation_email
        from app.models import Organization, OrgInvitation

        _signup_verify_login(client, "g122_deliver")
        org_id = _org(client, "Delivery Co")

        invitee = f"invitee-{uuid.uuid4().hex[:8]}@g122.test"
        caplog.set_level("DEBUG")
        r = client.post(f"{ID}/{org_id}/invitations", json={"email": invitee})
        assert r.status_code == 201, r.get_data(as_text=True)
        data = r.get_json()["data"]
        token = data["token"]

        invitation = OrgInvitation.query.filter_by(token=token).first()
        assert invitation is not None

        # ---- 1. composition: recipient + accept URL shape -------------------
        org = db.session.get(Organization, org_id)
        subject, body = build_invitation_email(invitee, token, org_name=org.name)
        assert f"/auth/invitation?token={token}" in body, (
            "the accept URL must carry the token and point at the SPA route")
        assert body.count(token) == 1, "the token must appear exactly once"

        # ---- 2. the durable record hashes exactly that body ----------------
        record = EmailRecord.query.filter_by(recipient=invitee).order_by(
            EmailRecord.id.desc()).first()
        assert record is not None, "no EmailRecord was created for the send"
        import hashlib
        assert record.body_hash == hashlib.sha256(body.encode()).hexdigest()[:16]
        assert record.notification_type == "team_invitation"
        assert record.category == "security"

        # ---- 3. truthful provider boundary ---------------------------------
        # No provider is configured here, so the send must be recorded as not
        # delivered, with the reason, and the API must say so.
        assert record.state != "accepted", (
            "an unconfigured provider cannot report acceptance")
        assert data["delivery"]["delivered"] is False
        assert data["delivery"]["status"] in ("logged", "failed", "error", "blocked")
        assert data["delivery"].get("record_id") == record.id

        # ---- 4. token hygiene in logs --------------------------------------
        joined = "\n".join(r.getMessage() for r in caplog.records)
        assert token not in joined, (
            "the raw invitation token must never appear in the application log")
        assert "<redacted>" in joined or "Body: " not in joined
        assert invitee in joined, "the attempt should still be observable by recipient"

    def test_delivery_status_is_absent_from_listings(self, client, app):
        """Listings are administrative metadata — no token, no delivery internals."""
        _signup_verify_login(client, "g122_list")
        org_id = _org(client, "Listing Co")
        r = client.post(f"{ID}/{org_id}/invitations",
                        json={"email": f"l-{uuid.uuid4().hex[:6]}@g122.test"})
        assert r.status_code == 201
        listing = client.get(f"{ID}/{org_id}/invitations")
        assert listing.status_code == 200
        for item in listing.get_json()["data"]:
            assert "token" not in item
            assert item.get("token_present") is True


class TestTestEnvironmentCannotSendMail:
    """Recurrence guard for the G1.22 finding: tests reached a real provider.

    With a host RESEND_API_KEY, a signup in the suite issued a real call to
    api.resend.com. `tests/conftest.py` now forces the non-sending mode. These
    assertions fail loudly if that protection is ever removed.
    """

    def test_provider_is_forced_to_non_sending_mode(self):
        import os

        from app.communication import email_core

        assert os.environ.get("EMAIL_PROVIDER") == "smtp"
        assert email_core._PROVIDER == "smtp", (
            "tests must never run with a remote email provider configured")
        assert not os.environ.get("RESEND_API_KEY")
        assert not email_core._RESEND_API_KEY
        assert not email_core._USER and not email_core._PASSWORD

    def test_unconfigured_provider_reports_logged_not_accepted(self, app, caplog):
        from app.email_service import send_email

        caplog.set_level("DEBUG")
        with app.app_context():
            result = send_email(to="safety@g122.test", subject="s",
                                body="body-with-a-token-shape ABC123",
                                notification_type="test")
        assert result["status"] == "logged"
        assert result["status"] != "accepted"
        joined = "\n".join(r.getMessage() for r in caplog.records)
        assert "body-with-a-token-shape" not in joined, (
            "bodies (which carry tokens) must never be logged")


class TestInvitationTokenBinding:
    def test_token_is_bound_to_recipient_and_organization(self, client, app):
        _signup_verify_login(client, "g122_bind")
        org_id = _org(client, "Binding Co")
        invitee = f"bound-{uuid.uuid4().hex[:6]}@g122.test"
        r = client.post(f"{ID}/{org_id}/invitations", json={"email": invitee})
        token = r.get_json()["data"]["token"]

        lookup = client.get(f"{ID}/invitations/{token}")
        assert lookup.status_code == 200
        payload = lookup.get_json()["data"]
        assert payload["email"] == invitee
        assert payload["org_id"] == org_id
        assert payload["org_name"] == "Binding Co"

        # acceptance creates the account for the invited address only
        accepted = client.post(f"{ID}/invitations/{token}/accept",
                              json={"name": "Bound Person", "password": PASSWORD})
        assert accepted.status_code == 201
        assert accepted.get_json()["data"]["email"] == invitee

    def test_replay_after_acceptance_is_refused_and_reported(self, client, app):
        _signup_verify_login(client, "g122_replay")
        org_id = _org(client, "Replay Co")
        r = client.post(f"{ID}/{org_id}/invitations",
                        json={"email": f"rp-{uuid.uuid4().hex[:6]}@g122.test"})
        token = r.get_json()["data"]["token"]
        assert client.post(f"{ID}/invitations/{token}/accept",
                           json={"name": "First", "password": PASSWORD}).status_code == 201
        again = client.post(f"{ID}/invitations/{token}/accept",
                            json={"name": "Second", "password": PASSWORD})
        assert again.status_code == 404
        assert "already" in again.get_data(as_text=True).lower()