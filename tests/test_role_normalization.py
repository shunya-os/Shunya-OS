"""DEF-05 — one canonical role vocabulary, with explicit boundaries.

Canonical org roles: owner, admin, manager, member, viewer (authorization truth
in OrgMember.role). Legacy TeamMember.role values (admin/agent/manager) remain
accepted as input aliases and are mapped deterministically; they never grant
permissions by themselves — permissions come from the seeded canonical role.
"""
from __future__ import annotations

import uuid

import pytest

from app import db
from app.auth import TeamMember
from app.authz.services import normalize_role
from app.models import OrgMember


pytestmark = pytest.mark.usefixtures("app")


def _email(tag: str) -> str:
    return f"g115-{tag.lower()}-{uuid.uuid4().hex[:8]}@cert.local"


def _login(client, email, password):
    return client.post("/login/password", json={"email": email, "password": password})


def _bootstrap(client, name):
    r = client.post("/orgs", json={"company_name": name})
    assert r.status_code == 201, r.get_data(as_text=True)
    return int(r.get_json()["org_id"])


def _owner(client, tag="owner"):
    email, pw = _email(tag), "G1.15-password"
    user = TeamMember(name=tag, email=email, role="admin", is_active=True, verified=True)
    user.set_password(pw)
    db.session.add(user)
    db.session.commit()
    assert _login(client, email, pw).status_code == 200
    return email, pw, _bootstrap(client, f"G1.15 {tag} {uuid.uuid4().hex[:6]}")


@pytest.mark.parametrize("label,canonical,legacy", [
    ("owner", "owner", "admin"),
    ("admin", "admin", "admin"),
    ("manager", "manager", "manager"),
    ("member", "member", "agent"),
    ("viewer", "viewer", "agent"),
    ("agent", "member", "agent"),      # legacy alias
    ("MEMBER", "member", "agent"),     # case handling
])
def test_normalize_role_mapping(label, canonical, legacy):
    assert normalize_role(label) == (canonical, legacy)


def test_unknown_role_label_is_rejected():
    with pytest.raises(ValueError):
        normalize_role("superuser")


@pytest.mark.parametrize("label,canonical,legacy,can_create", [
    ("member", "member", "agent", True),
    ("agent", "member", "agent", True),
    ("viewer", "viewer", "agent", False),
])
def test_created_user_gets_canonical_role_and_real_permission_boundary(
    client, label, canonical, legacy, can_create
):
    _, _, org_id = _owner(client)
    email = _email("created")
    r = client.post(f"/api/v1/orgs/{org_id}/users",
                    json={"name": "Role Probe", "email": email,
                          "password": "G1.15-member-pw", "role": label})

    assert r.status_code == 201, r.get_data(as_text=True)
    user = TeamMember.query.filter_by(email=email).first()
    member = OrgMember.query.filter_by(email=email).first()
    assert user is not None and member is not None
    assert member.role == canonical, "authorization role must be canonical"
    assert user.role == legacy, "identity-layer role uses the legacy mapping"

    # Real permission boundary.
    assert _login(client, email, "G1.15-member-pw").status_code == 200
    resp = client.post("/api/v1/uop/objects", json={"object_type": "customer", "name": "Role boundary"})
    if can_create:
        assert resp.status_code == 201, resp.get_data(as_text=True)
    else:
        assert resp.status_code == 403, "viewer must not create objects"


def test_user_administration_cannot_cross_tenants(client):
    email_a, _, org_a = _owner(client, "tenantA")
    client.get("/logout")
    email_b, _, _org_b = _owner(client, "tenantB")
    # B must not be able to list A's users.
    r = client.get(f"/api/v1/orgs/{org_a}/users")
    assert r.status_code in (403, 404)
    body = r.get_data(as_text=True)
    assert email_a not in body and email_b not in body