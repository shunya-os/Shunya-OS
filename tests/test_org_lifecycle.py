"""Durable regression coverage — organization lifecycle & tenant isolation.

Protects the G1.13 fixes:
  DEF-02  verified org-less user can bootstrap an organization
  DEF-03  invitation acceptance writes the canonical identity; login resolves it
  DEF-04  org-scoped user administration resolves Organization (not Tenant)
  roles   org creation seeds default roles (owner holds permissions)

All checks exercise the real Flask app through the test client, with real
sessions and the real authorization decorators. Only model rows needed as
starting state are created directly; no membership is patched to make an
authorization check pass.
"""
from __future__ import annotations

import json
import uuid

import pytest

from app import db
from app.auth import TeamMember


pytestmark = pytest.mark.usefixtures("app")


def _email(tag: str) -> str:
    return f"g114-{tag}-{uuid.uuid4().hex[:8]}@cert.local"


def _make_verified_user(email: str, password: str, name: str = "G1.14 User") -> TeamMember:
    user = TeamMember(name=name, email=email, role="admin", is_active=True, verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, email: str, password: str):
    return client.post("/login/password", json={"email": email, "password": password})


def _bootstrap_org(client, name: str) -> int:
    r = client.post("/orgs", json={"company_name": name})
    assert r.status_code == 201, r.get_data(as_text=True)
    return int(r.get_json()["org_id"])


def _create_object(client, name: str) -> dict:
    r = client.post("/api/v1/uop/objects", json={"object_type": "customer", "name": name})
    assert r.status_code == 201, r.get_data(as_text=True)
    return r.get_json()["object"]


def test_new_verified_user_can_bootstrap_an_organization(client):
    """DEF-02: the global org guard must not dead-end first-org creation."""
    email, pw = _email("boot"), "G1.14-password"
    _make_verified_user(email, pw)
    assert _login(client, email, pw).status_code == 200

    org_id = _bootstrap_org(client, f"G1.14 Bootstrap {uuid.uuid4().hex[:6]}")
    assert org_id > 0

    # Owner has permissions (roles seeded at creation) and org context resolves.
    obj = _create_object(client, "Bootstrap Object")
    assert int(obj["tenant_id"]) == org_id


def test_two_users_receive_separate_org_contexts_and_isolated_objects(client):
    users = []
    for tag in ("alpha", "beta"):
        email, pw = _email(tag), "G1.14-password"
        _make_verified_user(email, pw, name=tag)
        assert _login(client, email, pw).status_code == 200
        org_id = _bootstrap_org(client, f"G1.14 {tag} {uuid.uuid4().hex[:6]}")
        obj = _create_object(client, f"{tag} secret {uuid.uuid4().hex[:6]}")
        users.append({"email": email, "pw": pw, "org": org_id, "obj": obj})
        client.get("/logout")

    a, b = users
    assert a["org"] != b["org"]
    assert int(a["obj"]["tenant_id"]) != int(b["obj"]["tenant_id"])

    # A sees only its own object.
    assert _login(client, a["email"], a["pw"]).status_code == 200
    listing = client.get("/api/v1/uop/objects").get_data(as_text=True)
    assert a["obj"]["name"] in listing
    assert b["obj"]["name"] not in listing

    # Cross-tenant read and archive are denied and leak nothing.
    r = client.get(f"/api/v1/uop/objects/{b['obj']['object_id']}")
    assert r.status_code == 404
    assert b["obj"]["name"] not in r.get_data(as_text=True)
    r = client.post(f"/api/v1/uop/objects/{b['obj']['object_id']}/archive", json={})
    assert r.status_code == 404

    client.get("/logout")
    assert _login(client, b["email"], b["pw"]).status_code == 200
    r = client.get(f"/api/v1/uop/objects/{b['obj']['object_id']}")
    assert r.status_code == 200, "B's object must not be archived by A"


@pytest.mark.parametrize("mode", ["query", "header", "body"])
def test_client_supplied_tenant_identifiers_never_override_server_scope(client, mode):
    email, pw = _email("override"), "G1.14-password"
    _make_verified_user(email, pw)
    assert _login(client, email, pw).status_code == 200
    own_org = _bootstrap_org(client, f"G1.14 Override {uuid.uuid4().hex[:6]}")
    own = _create_object(client, "Own object")

    foreign = own_org + 999
    if mode == "query":
        r = client.get(f"/api/v1/uop/objects?tenant_id={foreign}&org_id={foreign}")
        assert r.status_code == 200
        payload = r.get_json()
        assert all(int(o["tenant_id"]) == own_org for o in payload["objects"])
    elif mode == "header":
        r = client.get(
            f"/api/v1/uop/objects/{own['object_id']}",
            headers={"X-Org-Id": str(foreign), "X-Tenant-Id": str(foreign)},
        )
        assert r.status_code == 200
        assert int(r.get_json()["object"]["tenant_id"]) == own_org
    else:
        r = client.post(
            "/api/v1/uop/objects",
            json={"object_type": "customer", "name": "Override probe",
                  "tenant_id": foreign, "organization_id": foreign},
            headers={"X-Org-Id": str(foreign)},
        )
        assert r.status_code == 201
        assert int(r.get_json()["object"]["tenant_id"]) == own_org


def test_missing_object_and_unauthenticated_access_are_denied(client):
    client.get("/logout")
    assert client.get("/api/v1/uop/objects").status_code in (401, 403)
    assert client.get("/api/v1/uop/objects/does-not-exist").status_code in (401, 403)


def test_invitation_acceptance_resolves_canonical_identity(client, monkeypatch):
    """DEF-03: invited users must resolve their membership after login."""
    # The invite path sends mail; suppress only the outbound side effect.
    import app.email_service as email_service
    monkeypatch.setattr(email_service, "send_email", lambda **kw: {"status": "logged"})

    owner_email, owner_pw = _email("owner"), "G1.14-password"
    _make_verified_user(owner_email, owner_pw, name="Owner")
    assert _login(client, owner_email, owner_pw).status_code == 200
    org_id = _bootstrap_org(client, f"G1.14 Invite {uuid.uuid4().hex[:6]}")

    invitee_email = _email("invitee")
    r = client.post("/api/v1/team/invite",
                    json={"email": invitee_email, "name": "Invitee", "role": "admin"})
    assert r.status_code == 201, r.get_data(as_text=True)

    from app.models import OrgInvitation, OrgMember
    inv = OrgInvitation.query.filter_by(email=invitee_email).order_by(OrgInvitation.id.desc()).first()
    assert inv is not None

    client.get("/logout")
    r = client.post(f"/api/v1/orgs/invitations/{inv.token}/accept",
                    json={"name": "Invitee", "password": "G1.14-invitee-pw"})
    assert r.status_code in (200, 201), r.get_data(as_text=True)

    assert _login(client, invitee_email, "G1.14-invitee-pw").status_code == 200
    member = OrgMember.query.filter_by(organization_id=org_id, email=invitee_email).first()
    assert member is not None
    assert member.identity_id.startswith("sid_"), (
        "acceptance must write the canonical identity, not the numeric TeamMember id"
    )

    obj = _create_object(client, "Invitee-visible object")
    r = client.get(f"/api/v1/uop/objects/{obj['object_id']}")
    assert r.status_code == 200


def test_org_scoped_user_administration_resolves_canonical_organization(client, monkeypatch):
    """DEF-04: /api/v1/orgs/<id>/users must find an Organization-created org."""
    import app.email_service as email_service
    monkeypatch.setattr(email_service, "send_email", lambda **kw: {"status": "logged"})

    owner_email, owner_pw = _email("admin"), "G1.14-password"
    _make_verified_user(owner_email, owner_pw, name="Admin")
    assert _login(client, owner_email, owner_pw).status_code == 200
    org_id = _bootstrap_org(client, f"G1.14 Admin {uuid.uuid4().hex[:6]}")

    new_email = _email("member")
    # Role vocabulary of this route is the legacy UserRole set (admin/agent/
    # manager); canonical roles (member/viewer/owner) are rejected here — a
    # recorded inconsistency, not exercised by this regression.
    r = client.post(f"/api/v1/orgs/{org_id}/users",
                    json={"name": "Org Member", "email": new_email,
                          "password": "G1.14-member-pw", "role": "agent"})
    assert r.status_code == 201, r.get_data(as_text=True)
    assert r.get_json()["data"]["email"] == new_email