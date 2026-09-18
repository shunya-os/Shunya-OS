"""Sign-in must resolve the organization DELIBERATELY, never by member count.

Defect (directive §22 — no arbitrary ownership resolution, no synthetic tenant):
`app/founder/routes.py` sign-in picked the organization with the MOST MEMBERS
(`max(org_counts, key=org_counts.get)`) and, for an account with no membership,
wrote `session["current_org_id"] = 0` — a synthetic tenant that does not exist.
`onboarding_complete` was also hardcoded truthy via `has_personal or True`.

These tests pin the replacement contract:
  * explicit caller choice wins (when the identity is a member),
  * then the organization already established in the session,
  * then a single membership,
  * otherwise a deterministic most-privileged-then-lowest-id pick, and the
    response REPORTS the ambiguity (`requires_org_selection`) instead of guessing,
  * membership-less accounts get NO organization (nothing synthetic),
  * `onboarding_complete` reflects reality.
"""
import pytest

PASSWORD = "org-resolution-pass-1"

# The org with the most members is deliberately the one the identity is NOT
# owner of, so a member-count heuristic would resolve to the wrong tenant.
ORG_BIG = 961      # most members, identity is only a 'member'
ORG_OWNED = 962    # identity is owner
ORG_OTHER = 963    # identity is a member


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


def _seed(app, email, memberships, with_workspace=True):
    """memberships: list of (org_id, role, member_count_filler)."""
    from app import db
    from app.auth import TeamMember
    from app.models import OrgMember, Organization
    from app.objects.legacy_models import ShWorkspaceMembership, Workspace

    with app.app_context():
        member = TeamMember.query.filter_by(email=email).first()
        if not member:
            member = TeamMember(name="Org Resolver", email=email,
                                role="owner", is_active=True)
            member.set_password(PASSWORD)
            member.verified = True
            db.session.add(member)
            db.session.flush()
        identity_id = str(member.id)

        for org_id, role, fillers in memberships:
            if not db.session.get(Organization, org_id):
                db.session.add(Organization(id=org_id, name=f"Org {org_id}",
                                            slug=f"org-{org_id}", is_active=True))
                db.session.flush()
            if not OrgMember.query.filter_by(organization_id=org_id,
                                             email=email).first():
                db.session.add(OrgMember(organization_id=org_id,
                                         identity_id=identity_id,
                                         name="Org Resolver", email=email,
                                         role=role, is_active=True))
            # fillers simulate other humans in the organization
            for i in range(fillers):
                filler_email = f"filler-{org_id}-{i}@example.com"
                if not OrgMember.query.filter_by(organization_id=org_id,
                                                 email=filler_email).first():
                    db.session.add(OrgMember(organization_id=org_id,
                                             identity_id=f"filler-{org_id}-{i}",
                                             name="Filler", email=filler_email,
                                             role="member", is_active=True))
            if with_workspace:
                ws_id = f"ws_org_{org_id}"
                if not db.session.get(Workspace, ws_id):
                    db.session.add(Workspace(id=ws_id, name=f"WS {org_id}",
                                             workspace_type="business",
                                             status="active",
                                             created_by="org_test",
                                             organization_id=org_id))
                if not ShWorkspaceMembership.query.filter_by(
                        workspace_id=ws_id, identity_id=identity_id).first():
                    db.session.add(ShWorkspaceMembership(
                        workspace_id=ws_id, identity_id=identity_id,
                        role="owner", is_active=True))
        db.session.commit()
        return identity_id


def _signin(client, email, body=None):
    return client.post("/api/v1/founder/signin",
                       json={"email": email, "password": PASSWORD, **(body or {})})


# ---------------------------------------------------------------------------
# The defect
# ---------------------------------------------------------------------------


def test_member_count_does_not_decide_the_organization(app, client):
    """The biggest org must NOT win — the identity's own role must."""
    email = "multi-org-resolver@example.com"
    _seed(app, email, [(ORG_BIG, "member", 5), (ORG_OWNED, "owner", 0)])
    resp = _signin(client, email)
    assert resp.status_code == 200, resp.get_data(as_text=True)[:200]
    body = resp.get_json()
    assert body["organization_id"] == ORG_OWNED, (
        "resolved to the organization with the most members instead of the "
        f"identity's owned organization: {body}"
    )


def test_ambiguous_memberships_are_reported_not_guessed(app, client):
    email = "ambiguous-resolver@example.com"
    _seed(app, email, [(ORG_BIG, "member", 3), (ORG_OTHER, "member", 0)])
    body = _signin(client, email).get_json()
    assert body["requires_org_selection"] is True
    assert {o["organization_id"] for o in body["organizations"]} == {ORG_BIG, ORG_OTHER}
    # deterministic even when ambiguous: lowest organization_id
    assert body["organization_id"] == ORG_BIG


def test_explicit_choice_is_honoured(app, client):
    email = "explicit-resolver@example.com"
    _seed(app, email, [(ORG_BIG, "member", 2), (ORG_OTHER, "member", 0)])
    body = _signin(client, email, {"org_id": ORG_OTHER}).get_json()
    assert body["organization_id"] == ORG_OTHER
    assert body["requires_org_selection"] is False
    with client.session_transaction() as sess:
        assert int(sess["current_org_id"]) == ORG_OTHER


def test_choice_for_an_organization_you_do_not_belong_to_is_ignored(app, client):
    email = "foreign-org-resolver@example.com"
    _seed(app, email, [(ORG_OWNED, "owner", 0)])
    body = _signin(client, email, {"org_id": ORG_BIG}).get_json()
    assert body["organization_id"] == ORG_OWNED, "accepted a foreign organization"


def test_existing_session_organization_is_kept(app, client):
    email = "session-resolver@example.com"
    _seed(app, email, [(ORG_BIG, "member", 1), (ORG_OTHER, "member", 0)])
    with client.session_transaction() as sess:
        sess["current_org_id"] = str(ORG_OTHER)
    body = _signin(client, email).get_json()
    assert body["organization_id"] == ORG_OTHER


def test_single_membership_needs_no_selection(app, client):
    email = "single-org-resolver@example.com"
    _seed(app, email, [(ORG_OWNED, "owner", 0)])
    body = _signin(client, email).get_json()
    assert body["organization_id"] == ORG_OWNED
    assert body["requires_org_selection"] is False


# ---------------------------------------------------------------------------
# No synthetic tenant
# ---------------------------------------------------------------------------


def test_membershipless_account_gets_no_synthetic_organization(app, client):
    email = "no-org-resolver@example.com"
    _seed(app, email, [], with_workspace=False)
    body = _signin(client, email).get_json()
    assert body["success"] is True
    assert body["organization_id"] is None
    assert body["requires_org_creation"] is True
    assert body["onboarding_complete"] is False
    with client.session_transaction() as sess:
        assert sess.get("current_org_id") is None, (
            "a synthetic organization id was written into the session: "
            f"{sess.get('current_org_id')!r}"
        )


def test_onboarding_complete_is_not_hardcoded_true(app, client):
    """With a membership but no created objects, onboarding must not claim done."""
    email = "fresh-org-resolver@example.com"
    _seed(app, email, [(ORG_OWNED, "owner", 0)])
    body = _signin(client, email).get_json()
    assert body["onboarding_complete"] is False


def test_wrong_password_still_denied(app, client):
    email = "wrong-password-resolver@example.com"
    _seed(app, email, [(ORG_OWNED, "owner", 0)])
    resp = client.post("/api/v1/founder/signin",
                       json={"email": email, "password": "definitely-wrong"})
    assert resp.status_code == 401
