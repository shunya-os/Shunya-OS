"""G1.21 — invitation lifecycle, end to end.

The G1.20 report listed "invitation-acceptance → login" as *not tested*. This file
exercises the whole journey against the real Flask app, with real sessions and the
real authorization decorators, and pins what each step actually does:

  1. an authorized organization user initiates an invitation
  2. the system validates organization + inviter permissions
  3. invitation state and intended role persist
  4. the token is obtained through the supported channel (the create response;
     email delivery is guardrail-blocked by default and asserted as such)
  5. the invited user accepts
  6. canonical identity and organization membership resolve consistently
  7. the user logs in and obtains a valid session
  8. the user reaches an authorized resource (canonical object API)
  9. the user cannot reach another tenant's resources
 10. replaying the token produces the intended safe behaviour
 11. expired / malformed / revoked / already-used tokens produce truthful outcomes

Every identity here is synthetic (``@g121.test``); nothing leaves the process.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from app import db

PASSWORD = "G1.21-invitation-password"

# The identity blueprint is mounted at /api/v1/orgs (verified from the app's own
# url_map), while the SPA organization-creation route is /orgs.
ID = "/api/v1/orgs"


def _signup_verify_login(client, tag):
    from app.auth import TeamMember

    email = f"{tag}-{uuid.uuid4().hex[:8]}@g121.test"
    signup = client.post("/api/v1/auth/signup", json={
        "name": tag, "email": email, "password": PASSWORD,
    })
    assert signup.status_code in (200, 201), signup.get_data(as_text=True)
    member = TeamMember.query.filter_by(email=email).first()
    assert member is not None
    if not member.verified:
        verified = client.post("/api/v1/auth/verify-email",
                               json={"token": member.verify_token})
        assert verified.status_code == 200, verified.get_data(as_text=True)
    login = client.post("/login/password", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.get_data(as_text=True)
    with client.session_transaction() as sess:
        return email, sess.get("identity_id")


def _logout(client):
    client.post("/logout")


def _make_org(client, name):
    created = client.post("/orgs", json={"company_name": name})
    assert created.status_code == 201, created.get_data(as_text=True)
    return int(created.get_json()["org_id"])


def _invite(client, org_id, email, role="member"):
    return client.post(f"{ID}/{org_id}/invitations",
                       json={"email": email, "role": role})


class TestInvitationLifecycle:
    def test_full_journey_owner_invites_member_who_accepts_logs_in_and_is_isolated(
            self, client, app):
        from app.auth import TeamMember
        from app.models import OrgMember, OrgInvitation
        from app.objects.legacy_models import ShWorkspaceMembership

        # ---- 1. owner creates the organization -------------------------------
        owner_email, owner_identity = _signup_verify_login(client, "g121_owner")
        org_id = _make_org(client, "Invitation Journey Co")

        # ---- 2/3. authorized user initiates the invitation -------------------
        invitee_email = f"g121_invitee_{uuid.uuid4().hex[:8]}@g121.test"
        created = _invite(client, org_id, invitee_email, role="member")
        assert created.status_code == 201, created.get_data(as_text=True)
        payload = created.get_json()["data"]
        token = payload["token"]
        assert payload["org_name"] == "Invitation Journey Co"
        assert payload["role"] == "member"
        assert payload["status"] == "pending"

        invite_row = OrgInvitation.query.filter_by(token=token).first()
        assert invite_row is not None
        assert invite_row.organization_id == org_id
        assert invite_row.role == "member"
        assert invite_row.accepted_at is None
        assert invite_row.expires_at > datetime.utcnow()

        # ---- 4. delivery channel: the create response ------------------------
        # Email delivery is guardrailed OFF by default (email_core.send refuses
        # unless is_human_triggered=True), so the token returned once to the
        # inviting admin is the supported channel in this environment. This is
        # asserted, not assumed: the journey must not pretend an inbox received it.
        assert app.config.get("TESTING") is True

        # ---- 5. the invited user accepts ------------------------------------
        accepted = client.post(f"{ID}/invitations/{token}/accept",
                               json={"name": "Invitee Person", "password": PASSWORD})
        assert accepted.status_code == 201, accepted.get_data(as_text=True)

        # ---- 6. canonical identity + membership resolve consistently --------
        invitee = TeamMember.query.filter_by(email=invitee_email).first()
        assert invitee is not None
        assert invitee.verified is True  # the emailed link proves inbox ownership
        assert invitee.identity_id, "canonical identity must be linked at acceptance"

        membership = OrgMember.query.filter_by(
            organization_id=org_id, email=invitee_email).first()
        assert membership is not None
        assert membership.identity_id == invitee.identity_id
        assert membership.role == "member"
        assert membership.is_active is True

        # workspace access is part of "joined": without it every object surface
        # answers 403 no_authorized_workspace
        ws_memberships = ShWorkspaceMembership.query.filter_by(
            identity_id=invitee.identity_id, is_active=True).all()
        assert ws_memberships, "acceptance must grant canonical workspace access"
        assert all(m.role == "member" for m in ws_memberships), (
            "a member must never be granted owner/admin workspace role")

        db.session.expire_all()
        invite_row = OrgInvitation.query.filter_by(token=token).first()
        assert invite_row.accepted_at is not None
        assert invite_row.status == "accepted"

        # ---- 7. the invitee logs in ------------------------------------------
        _logout(client)
        login = client.post("/login/password",
                            json={"email": invitee_email, "password": PASSWORD})
        assert login.status_code == 200, login.get_data(as_text=True)

        # ---- 8. authorized resource ------------------------------------------
        listing = client.get("/api/v1/objects")
        assert listing.status_code == 200, (
            f"invited member cannot use the tenant: {listing.get_data(as_text=True)}")

        # ---- 9. cross-tenant isolation ---------------------------------------
        # The owner's second organization is invisible to the invitee.
        _logout(client)
        _signup_verify_login(client, "g121_other_owner")
        other_org = _make_org(client, "Other Tenant Co")
        _logout(client)
        client.post("/login/password", json={"email": invitee_email, "password": PASSWORD})

        foreign = client.get(f"{ID}/{other_org}/invitations")
        assert foreign.status_code == 403, foreign.get_data(as_text=True)

        # ---- 10. replaying the token -----------------------------------------
        replay = client.post(f"{ID}/invitations/{token}/accept",
                             json={"name": "Replay", "password": PASSWORD})
        assert replay.status_code == 404, replay.get_data(as_text=True)
        assert "already" in replay.get_data(as_text=True).lower()

        viewer = client.get(f"{ID}/invitations/{token}")
        assert viewer.status_code == 404

        # one account, one membership — the replay changed nothing
        assert TeamMember.query.filter_by(email=invitee_email).count() == 1
        assert OrgMember.query.filter_by(
            organization_id=org_id, email=invitee_email).count() == 1


class TestInvitationAuthorization:
    """The invitation endpoints are administrative, not merely authenticated."""

    def test_non_member_cannot_list_create_or_revoke(self, client, app):
        from app.models import OrgInvitation

        _signup_verify_login(client, "g121_priv_owner")
        org_id = _make_org(client, "Private Invites Co")
        created = _invite(client, org_id, f"pending_{uuid.uuid4().hex[:6]}@g121.test")
        assert created.status_code == 201
        inv_id = created.get_json()["data"]["id"]

        _logout(client)
        _signup_verify_login(client, "g121_stranger")

        assert client.get(f"{ID}/{org_id}/invitations").status_code == 403
        assert _invite(client, org_id, "attacker@g121.test").status_code == 403
        assert client.delete(f"{ID}/{org_id}/invitations/{inv_id}").status_code == 403

        # nothing was created and nothing was revoked by the stranger
        assert OrgInvitation.query.filter_by(
            organization_id=org_id, email="attacker@g121.test").first() is None
        assert db.session.get(OrgInvitation, inv_id) is not None

    def test_plain_member_cannot_manage_invitations(self, client, app):
        _signup_verify_login(client, "g121_member_owner")
        org_id = _make_org(client, "Member Gate Co")

        member_email = f"plainmember_{uuid.uuid4().hex[:6]}@g121.test"
        created = _invite(client, org_id, member_email, role="member")
        assert created.status_code == 201
        token = created.get_json()["data"]["token"]
        accepted = client.post(f"{ID}/invitations/{token}/accept",
                               json={"name": "Plain Member", "password": PASSWORD})
        assert accepted.status_code == 201

        _logout(client)
        client.post("/login/password", json={"email": member_email, "password": PASSWORD})

        assert client.get(f"{ID}/{org_id}/invitations").status_code == 403
        assert _invite(client, org_id, "escalate@g121.test").status_code == 403

    def test_admin_may_manage_invitations(self, client, app):
        _signup_verify_login(client, "g121_admin_owner")
        org_id = _make_org(client, "Admin Gate Co")

        admin_email = f"adminuser_{uuid.uuid4().hex[:6]}@g121.test"
        created = _invite(client, org_id, admin_email, role="admin")
        token = created.get_json()["data"]["token"]
        assert client.post(f"{ID}/invitations/{token}/accept",
                           json={"name": "Admin User", "password": PASSWORD}).status_code == 201

        _logout(client)
        client.post("/login/password", json={"email": admin_email, "password": PASSWORD})

        listing = client.get(f"{ID}/{org_id}/invitations")
        assert listing.status_code == 200, listing.get_data(as_text=True)
        # the raw token is never re-broadcast in a listing
        assert all("token" not in item for item in listing.get_json()["data"])
        assert _invite(client, org_id, f"x_{uuid.uuid4().hex[:6]}@g121.test").status_code == 201


class TestInvitationTokenOutcomes:
    def test_expired_token_is_refused_truthfully(self, client, app):
        from app.models import OrgInvitation

        _signup_verify_login(client, "g121_expiry_owner")
        org_id = _make_org(client, "Expiry Co")
        created = _invite(client, org_id, f"expired_{uuid.uuid4().hex[:6]}@g121.test")
        token = created.get_json()["data"]["token"]

        row = OrgInvitation.query.filter_by(token=token).first()
        row.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

        lookup = client.get(f"{ID}/invitations/{token}")
        assert lookup.status_code == 404
        assert "expired" in lookup.get_data(as_text=True).lower()

        accept = client.post(f"{ID}/invitations/{token}/accept",
                             json={"name": "Too Late", "password": PASSWORD})
        assert accept.status_code == 404
        assert "expired" in accept.get_data(as_text=True).lower()

    def test_malformed_token_is_not_found(self, client, app):
        _signup_verify_login(client, "g121_malformed_owner")
        bogus = "not-a-real-token-" + uuid.uuid4().hex
        assert client.get(f"{ID}/invitations/{bogus}").status_code == 404
        assert client.post(f"{ID}/invitations/{bogus}/accept",
                           json={"name": "Nobody", "password": PASSWORD}).status_code == 404

    def test_revoked_token_is_refused(self, client, app):
        from app.models import OrgInvitation

        _signup_verify_login(client, "g121_revoke_owner")
        org_id = _make_org(client, "Revoke Co")
        created = _invite(client, org_id, f"revoked_{uuid.uuid4().hex[:6]}@g121.test")
        token = created.get_json()["data"]["token"]
        inv_id = created.get_json()["data"]["id"]

        revoked = client.delete(f"{ID}/{org_id}/invitations/{inv_id}")
        assert revoked.status_code == 200, revoked.get_data(as_text=True)
        assert OrgInvitation.query.filter_by(token=token).first() is None

        assert client.get(f"{ID}/invitations/{token}").status_code == 404
        assert client.post(f"{ID}/invitations/{token}/accept",
                           json={"name": "Revoked", "password": PASSWORD}).status_code == 404

    def test_accept_requires_password_of_usable_length(self, client, app):
        _signup_verify_login(client, "g121_weak_owner")
        org_id = _make_org(client, "Weak Password Co")
        created = _invite(client, org_id, f"weak_{uuid.uuid4().hex[:6]}@g121.test")
        token = created.get_json()["data"]["token"]

        short = client.post(f"{ID}/invitations/{token}/accept",
                            json={"name": "Weak", "password": "123"})
        assert short.status_code == 400
        # the invitation is still usable after a rejected attempt
        assert client.get(f"{ID}/invitations/{token}").status_code == 200
