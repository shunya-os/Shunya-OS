"""Invitation contract — the last dead end in the entry journey.

The frontend asked for `GET /api/v1/auth/invitation/<token>` and
`POST /api/v1/auth/accept-invitation`. Neither exists, so a person following an
invitation hit "Could not connect…". The capability already exists canonically
under the identity blueprint:

    GET  /api/v1/orgs/invitations/<token>
    POST /api/v1/orgs/invitations/<token>/accept

These tests exercise those REAL routes anonymously (an invitee has no session),
prove the payload names the inviting organization, and prove acceptance creates
a real member — then that the invitation cannot be used twice.
"""
import uuid

import pytest

ORG_INV = 901


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with _app.app_context():
        db.create_all()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


def _make_invitation(app, *, name="Invitee Name", role="member", expires_at=None):
    """Create a real Organization + OrgInvitation; return (token, email, org_name)."""
    from app import db
    from app.models import Organization, OrgInvitation
    with app.app_context():
        org = db.session.get(Organization, ORG_INV)
        if not org:
            org = Organization(id=ORG_INV, name="Panchi Club Bali",
                               slug="panchi-inv", is_active=True)
            db.session.add(org)
            db.session.flush()
        token = uuid.uuid4().hex
        email = f"invitee-{token[:8]}@example.com"
        inv = OrgInvitation(organization_id=ORG_INV, email=email, name=name,
                            role=role, token=token, status="pending",
                            invited_by="owner@example.com", expires_at=expires_at)
        db.session.add(inv)
        db.session.commit()
        return token, email, org.name


# ---------------------------------------------------------------------------
# The route the product must use (and now does)
# ---------------------------------------------------------------------------


def test_invitation_route_is_mounted_at_the_canonical_path(app):
    rules = {(str(r.rule), m) for r in app.url_map.iter_rules()
             for m in (r.methods or ())}
    assert ("/api/v1/orgs/invitations/<token>", "GET") in rules
    assert ("/api/v1/orgs/invitations/<token>/accept", "POST") in rules


def test_get_invitation_returns_details_for_valid_token(client, app):
    token, email, org_name = _make_invitation(app)
    resp = client.get(f"/api/v1/orgs/invitations/{token}")
    assert resp.status_code == 200, resp.get_data(as_text=True)[:300]
    body = resp.get_json()
    assert body["success"] is True
    data = body["data"]
    assert data["email"] == email
    assert data["status"] == "pending"
    # the accept screen must be able to name the organization
    assert data["org_name"] == org_name


def test_get_invitation_unknown_token_is_404_not_405(client, app):
    resp = client.get("/api/v1/orgs/invitations/definitely-not-a-token")
    assert resp.status_code == 404
    assert resp.get_json().get("success") in (False, None)


# ---------------------------------------------------------------------------
# Acceptance creates a real member, exactly once
# ---------------------------------------------------------------------------


def test_accept_invitation_creates_member_records(client, app):
    token, email, _ = _make_invitation(app, name="Grace Hopper")
    resp = client.post(f"/api/v1/orgs/invitations/{token}/accept",
                       json={"name": "Grace Hopper", "password": "correct-horse-1"})
    assert resp.status_code == 201, resp.get_data(as_text=True)[:300]
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["email"] == email

    from app import db
    from app.auth import TeamMember
    from app.models import OrgInvitation, OrgMember
    with app.app_context():
        assert TeamMember.query.filter_by(email=email).first() is not None
        member = OrgMember.query.filter_by(email=email,
                                           organization_id=ORG_INV).first()
        assert member is not None
        assert member.name == "Grace Hopper"
        inv = OrgInvitation.query.filter_by(token=token).first()
        assert inv.status == "accepted"
        assert inv.accepted_at is not None


def test_invitation_cannot_be_accepted_twice(client, app):
    token, _, _ = _make_invitation(app)
    first = client.post(f"/api/v1/orgs/invitations/{token}/accept",
                        json={"name": "Once Only", "password": "correct-horse-2"})
    assert first.status_code == 201
    second = client.post(f"/api/v1/orgs/invitations/{token}/accept",
                         json={"name": "Once Only", "password": "correct-horse-2"})
    assert second.status_code == 404
    # and the details are no longer served
    assert client.get(f"/api/v1/orgs/invitations/{token}").status_code == 404


def test_accept_invitation_rejects_short_password(client, app):
    token, _, _ = _make_invitation(app)
    resp = client.post(f"/api/v1/orgs/invitations/{token}/accept",
                       json={"name": "Too Short", "password": "abc"})
    assert resp.status_code == 400
    assert resp.get_json().get("success") in (False, None)


def test_accept_invitation_requires_a_name(client, app):
    token, _, _ = _make_invitation(app)
    resp = client.post(f"/api/v1/orgs/invitations/{token}/accept",
                       json={"password": "correct-horse-3"})
    assert resp.status_code == 400
