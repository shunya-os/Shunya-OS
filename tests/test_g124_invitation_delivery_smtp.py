"""G1.24 — invitation delivery through the REAL SMTP path to a local capture sink.

G1.22 could only verify up to the provider boundary: with no authorized
non-production provider, it correctly refused to claim inbox delivery. The
missing piece was a *safe* place for a message to land. This suite provides one:
a loopback ESMTP server with STARTTLS and AUTH, so the production send code path
(``smtplib.SMTP`` → ``starttls()`` → ``login()`` → ``sendmail()``) runs
unmodified, and the message is then read back from the sink.

What this proves
----------------
* the message is actually transmitted, over TLS, authenticated;
* it arrives at the intended recipient with exactly one accept URL;
* the accept URL carries the invitation token;
* the durable ``EmailRecord`` is ``accepted``;
* the API reports ``accepted: true`` but **not** ``delivered`` — acceptance by a
  mail server is not inbox delivery (G1.24 truthfulness rule).

What it does not prove
----------------------
Delivery to a real external inbox. That needs an authorized provider and is
reported as BLOCKED, not inferred from this test.

Nothing here leaves the machine: the sink binds 127.0.0.1, the certificate is
generated per run, and every address is synthetic.
"""

import email
import uuid
from email import policy
from urllib.parse import parse_qs, urlsplit

import pytest

from app import db

PASSWORD = "G1.24-delivery-password"
ID = "/api/v1/orgs"


def _decode_body(raw: str) -> str:
    """Standards-compliant MIME decode of a captured message.

    The production code sends ``MIMEMultipart('alternative')`` with a base64
    ``text/plain`` part, so a substring search on the raw envelope finds nothing.
    Decoding happens here, in the harness — production behaviour is unchanged.
    """
    message = email.message_from_string(raw, policy=policy.default)
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
        return ""
    return message.get_content()


def _messages_to(server, recipient: str) -> list[dict]:
    """Only the messages addressed to ``recipient``.

    The sink is shared with the signup verification email, which is also a real
    send. Filtering by envelope recipient keeps the assertion exact instead of
    loosening the expected count.
    """
    return [m for m in server.messages if recipient in (m.get("to") or [])]


def _token_from_url(url: str) -> str:
    return parse_qs(urlsplit(url).query).get("token", [""])[0]


@pytest.fixture(scope="function")
def capture(tmp_path):
    from tests._smtp_capture import SMTPCaptureServer, generate_self_signed

    cert, key = generate_self_signed(tmp_path)
    server = SMTPCaptureServer(cert, key).start()
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture(scope="function")
def smtp_capture(monkeypatch, capture, _no_external_email):
    """Point the canonical send module at the capture sink.

    ``_no_external_email`` is requested explicitly so the harness's neutraliser
    runs *before* this fixture (fixture dependencies are set up first) and cannot
    wipe the configuration mid-test.
    """
    from app.communication import email_core

    monkeypatch.setattr(email_core, "_PROVIDER", "smtp")
    monkeypatch.setattr(email_core, "_HOST", "127.0.0.1")
    monkeypatch.setattr(email_core, "_PORT", capture.port)
    monkeypatch.setattr(email_core, "_USER", "g124-capture")
    monkeypatch.setattr(email_core, "_PASSWORD", "g124-capture-not-a-credential")
    monkeypatch.setattr(email_core, "_FROM", "shunya@localhost")
    monkeypatch.setattr(email_core, "_MAX_RETRIES", 0)
    return capture


def _signup_verify_login(client, tag):
    from app.auth import TeamMember

    email = f"{tag}-{uuid.uuid4().hex[:8]}@g124.test"
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


class TestOrgInvitationReachesALocalInbox:
    def test_message_is_transmitted_over_tls_and_received(
            self, client, app, smtp_capture):
        from app.communication.email_models import EmailRecord

        _signup_verify_login(client, "g124_deliver")
        org_id = _org(client, "Capture Delivery Co")
        invitee = f"invitee-{uuid.uuid4().hex[:8]}@g124.test"

        response = client.post(f"{ID}/{org_id}/invitations", json={"email": invitee})
        assert response.status_code == 201, response.get_data(as_text=True)
        data = response.get_json()["data"]
        token = data["token"]

        # ---- the send path reported acceptance ---------------------------
        assert data["delivery"]["status"] == "accepted", data["delivery"]
        assert data["delivery"]["accepted"] is True
        assert data["delivery"]["delivered"] is False, (
            "acceptance by an MTA must never be reported as inbox delivery")

        # ---- the message really arrived ----------------------------------
        captured = _messages_to(smtp_capture, invitee)
        assert len(captured) == 1, (
            "expected exactly one invitation message for the invitee; "
            f"captured recipients: {[m.get('to') for m in smtp_capture.messages]}")
        message = captured[0]
        assert message["to"] == [invitee]
        assert message["tls"] is True, "the SMTP path must negotiate STARTTLS"
        assert message["auth_user"] == "g124-capture", "the send must authenticate"
        assert message["auth_password_present"] is True

        body = _decode_body(message["raw"])
        accept_url = f"/auth/invitation?token={token}"
        assert body.count(accept_url) == 1, (
            "the invitee must receive exactly one accept URL carrying the token")
        assert "You have been invited" in body

        # The verification email is a different message for a different address:
        # the invitation token must not leak into it.
        for other in smtp_capture.messages:
            if other is message:
                continue
            other_body = _decode_body(other["raw"])
            assert token not in other_body, (
                "the invitation token leaked into an unrelated message")

        # ---- durable record agrees ---------------------------------------
        record = EmailRecord.query.filter_by(recipient=invitee).order_by(
            EmailRecord.id.desc()).first()
        assert record is not None
        assert record.state == "accepted"
        assert data["delivery"]["record_id"] == record.id

    def test_token_in_the_message_is_the_one_that_accepts(
            self, client, app, smtp_capture):
        """The link the recipient receives must actually work end to end."""
        _signup_verify_login(client, "g124_link")
        org_id = _org(client, "Link Truth Co")
        invitee = f"linked-{uuid.uuid4().hex[:8]}@g124.test"

        created = client.post(f"{ID}/{org_id}/invitations", json={"email": invitee})
        data = created.get_json()["data"]
        token = data["token"]
        captured = _messages_to(smtp_capture, invitee)
        assert len(captured) == 1
        body = _decode_body(captured[0]["raw"])
        assert f"/auth/invitation?token={token}" in body
        assert body.count(token) == 1, "the token must appear exactly once in the message"

        # The recipient opens the link (anonymous session), then accepts.
        client.get("/logout")
        lookup = client.get(f"{ID}/invitations/{token}")
        assert lookup.status_code == 200, lookup.get_data(as_text=True)
        assert lookup.get_json()["data"]["email"] == invitee
        accepted = client.post(f"{ID}/invitations/{token}/accept",
                               json={"name": "Captured Recipient", "password": PASSWORD})
        assert accepted.status_code == 201, accepted.get_data(as_text=True)
        assert accepted.get_json()["data"]["email"] == invitee


class TestTeamInvitationReportsDeliveryTruthfully:
    """The UI path (/api/v1/team/invite) must not imply a send it did not make."""

    @pytest.fixture(scope="function")
    def owner_org(self, client, app):
        from tests.auth_helper import seed_rbac

        org_id = seed_rbac(db, identity_id="g124_team_owner", role_name="owner")
        with client.session_transaction() as session:
            session["identity_id"] = "g124_team_owner"
            session["current_org_id"] = org_id
        return org_id

    def test_accepted_delivery_is_reported_as_accepted_not_delivered(
            self, client, app, owner_org, smtp_capture):
        invitee = f"team-{uuid.uuid4().hex[:8]}@g124.test"
        response = client.post("/api/v1/team/invite",
                               json={"email": invitee, "role": "member"})
        assert response.status_code == 201, response.get_data(as_text=True)
        data = response.get_json()["data"]

        from app.models import OrgInvitation

        assert data["delivery"]["status"] == "accepted"
        assert data["delivery"]["accepted"] is True
        assert data["delivery"]["delivered"] is False

        # The team route deliberately does not return a raw `token` field — the
        # capability is delivered as the URL the admin can share. Assert against
        # the URL, and prove it points at the invitation that was persisted.
        token = _token_from_url(data["invite_url"])
        assert token, "invite_url must carry the accept token"
        assert "/auth/invitation?" in data["invite_url"]
        invitation = OrgInvitation.query.filter_by(token=token).first()
        assert invitation is not None and invitation.organization_id == owner_org
        assert invitation.email == invitee

        captured = _messages_to(smtp_capture, invitee)
        assert len(captured) == 1
        body = _decode_body(captured[0]["raw"])
        assert f"/auth/invitation?token={token}" in body, (
            "the emailed link must be the same capability the admin was given")
        assert body.count(token) == 1

    def test_unconfigured_transport_offers_the_link_instead_of_a_false_sent(
            self, client, app, owner_org, monkeypatch):
        """No usable transport: the admin still gets a recovery path."""
        from app.communication import email_core

        monkeypatch.setattr(email_core, "_PROVIDER", "smtp")
        monkeypatch.setattr(email_core, "_USER", "")
        monkeypatch.setattr(email_core, "_PASSWORD", "")

        invitee = f"nogate-{uuid.uuid4().hex[:8]}@g124.test"
        response = client.post("/api/v1/team/invite",
                               json={"email": invitee, "role": "member"})
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["delivery"]["status"] == "logged"
        assert data["delivery"]["accepted"] is False
        assert data["delivery"]["delivered"] is False
        assert "token=" in data["invite_url"], (
            "an undelivered invitation must still give the admin a usable link")
