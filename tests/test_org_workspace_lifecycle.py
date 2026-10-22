"""G1.19 — organization → canonical workspace lifecycle.

Defect: ``POST /orgs`` created the organization, membership and roles but no
canonical ``sh_workspaces`` row, so every object surface failed closed
(``GET /api/v1/objects`` → ``403 no_authorized_workspace``), onboarding could not
attach foundational objects, and uploads/media/AI object creation had nowhere to
write. Organizations are supposed to be usable immediately after creation.

Contract pinned here:

* creating an organization provisions exactly one active canonical workspace,
  owned by the creator, in the same transaction;
* the provisioning helper is idempotent (retries never duplicate a workspace);
* it is membership- and role-gated (no elevation, no cross-tenant write);
* the object API is immediately usable for such an organization;
* an organization that still has no workspace (legacy/imported) fails with a
  distinguishable 403 — never a 500, and never reported as an empty success.
"""

import pytest


PASSWORD = "G1.19-lifecycle-password"


def _new_user(client, app, tag):
    """Real signup → verify → login.

    This is the bootstrap chain that makes POST /orgs reachable: a verified
    identity with a personal workspace (created at signup) is allowed to create
    its first organization. Returns ``(email, session_identity_id)``.
    """
    from app.auth import TeamMember

    email = f"{tag}@g119.test"
    signup = client.post("/api/v1/auth/signup", json={
        "name": tag, "email": email, "password": PASSWORD,
    })
    assert signup.status_code in (200, 201), signup.get_data(as_text=True)

    member = TeamMember.query.filter_by(email=email).first()
    assert member is not None
    if not member.verified:
        token = member.verify_token
        verified = client.post("/api/v1/auth/verify-email", json={"token": token})
        assert verified.status_code == 200, verified.get_data(as_text=True)

    login = client.post("/login/password", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.get_data(as_text=True)

    with client.session_transaction() as session:
        return email, session.get("identity_id")


def _create_org(client, name="Acme Trading"):
    return client.post("/orgs", json={"company_name": name})


def _workspaces(org_id):
    from app.objects.legacy_models import Workspace

    return Workspace.query.filter_by(organization_id=org_id, status="active").all()


def _memberships(workspace_id):
    from app.objects.legacy_models import ShWorkspaceMembership

    return ShWorkspaceMembership.query.filter_by(workspace_id=workspace_id).all()


class TestOrganizationCreationProvisionsWorkspace:
    def test_org_creation_creates_one_canonical_workspace(self, client, app):
        _email, identity = _new_user(client, app, "g119_owner")
        response = _create_org(client)
        assert response.status_code == 201, response.get_data(as_text=True)
        body = response.get_json()
        org_id = body["org_id"]
        assert body["workspace_id"]

        workspaces = _workspaces(org_id)
        assert len(workspaces) == 1
        assert workspaces[0].id == body["workspace_id"]

        memberships = _memberships(workspaces[0].id)
        assert len(memberships) == 1
        assert memberships[0].identity_id == identity
        assert memberships[0].role == "owner"
        assert memberships[0].is_active is True

    def test_object_api_is_usable_immediately_after_org_creation(self, client, app):
        _new_user(client, app, "g119_owner")
        created = _create_org(client, "Beta Trading")
        assert created.status_code == 201

        listing = client.get("/api/v1/objects")
        assert listing.status_code == 200, listing.get_data(as_text=True)
        assert listing.get_json()["total"] == 0

        made = client.post("/api/v1/objects/", json={"name": "First note", "object_type": "note"})
        # The create route's contract is 200 + success envelope (not 201); the
        # persisted row and the authorized listing below are the real evidence.
        assert made.status_code == 200, made.get_data(as_text=True)
        assert made.get_json()["success"] is True
        object_id = made.get_json()["object_id"]

        listing = client.get("/api/v1/objects")
        assert listing.status_code == 200
        names = [o["name"] for o in listing.get_json()["objects"]]
        assert "First note" in names

        detail = client.get(f"/api/v1/objects/by-id/{object_id}")
        assert detail.status_code == 200

        state = client.get("/api/v1/objects/first-object-state").get_json()
        assert state["has_business_data"] is True

    def test_two_organizations_never_share_a_workspace(self, client, app):
        _new_user(client, app, "g119_owner")
        first = _create_org(client, "First Co").get_json()
        second = _create_org(client, "Second Co").get_json()

        assert first["workspace_id"] != second["workspace_id"]
        w1 = _workspaces(int(first["org_id"]))[0]
        w2 = _workspaces(int(second["org_id"]))[0]
        assert w1.organization_id == int(first["org_id"])
        assert w2.organization_id == int(second["org_id"])
        assert w1.id != w2.id


class TestProvisioningIsIdempotentAndGated:
    def test_repeated_provisioning_creates_no_duplicate(self, client, app):
        from app.authz.org_provisioning import ensure_organization_workspace

        _email, identity = _new_user(client, app, "g119_owner")
        org_id = _create_org(client).get_json()["org_id"]
        before = [w.id for w in _workspaces(org_id)]

        again = ensure_organization_workspace(org_id, identity)
        assert again["created"] is False
        assert again["workspace_id"] == before[0]
        assert [w.id for w in _workspaces(org_id)] == before

    def test_non_member_cannot_provision(self, client, app):
        from app.authz.org_provisioning import (
            WorkspaceProvisioningError,
            ensure_organization_workspace,
        )

        _new_user(client, app, "g119_owner")
        org_id = _create_org(client).get_json()["org_id"]

        with pytest.raises(WorkspaceProvisioningError) as excinfo:
            ensure_organization_workspace(org_id, "g119_stranger")
        assert excinfo.value.code == "not_a_member"

    def test_member_role_cannot_provision(self, client, app):
        from app import db
        from app.authz.org_provisioning import (
            WorkspaceProvisioningError,
            ensure_organization_workspace,
        )
        from app.models import OrgMember

        _new_user(client, app, "g119_owner")
        org_id = _create_org(client).get_json()["org_id"]
        db.session.add(OrgMember(
            organization_id=org_id, identity_id="g119_member", role="member",
            is_active=True,
        ))
        db.session.commit()

        with pytest.raises(WorkspaceProvisioningError) as excinfo:
            ensure_organization_workspace(org_id, "g119_member")
        assert excinfo.value.code == "insufficient_role"
        assert len(_workspaces(org_id)) == 1  # no extra workspace appeared

    def test_invalid_organization_id_fails_closed(self, app):
        from app.authz.org_provisioning import (
            WorkspaceProvisioningError,
            ensure_organization_workspace,
        )

        with app.app_context():
            for bad in (0, None, -3):
                with pytest.raises(WorkspaceProvisioningError) as excinfo:
                    ensure_organization_workspace(bad, "g119_owner")
                assert excinfo.value.code == "invalid_organization"


class TestWorkspaceLessOrganizationIsDistinguishable:
    def test_legacy_org_without_workspace_gets_403_not_500_or_empty(self, client, app):
        """A tenant that still owns no workspace must be a clean authorization denial."""
        from app import db
        from app.models import Organization, OrgMember

        org = Organization(name="Legacy Co", slug="legacy-co", is_active=True)
        db.session.add(org)
        db.session.flush()
        db.session.add(OrgMember(
            organization_id=org.id, identity_id="g119_legacy", role="owner",
            is_active=True,
        ))
        db.session.commit()
        assert _workspaces(org.id) == []

        with client.session_transaction() as session:
            session["identity_id"] = "g119_legacy"
            session["current_org_id"] = org.id
        listing = client.get("/api/v1/objects")
        assert listing.status_code == 403
        body = listing.get_json()
        assert body["success"] is False
        assert "no_authorized_workspace" in (body.get("code") or "")

        # The emptiness predicate deliberately does not need a workspace, so it
        # still answers truthfully instead of returning the authorization error.
        state = client.get("/api/v1/objects/first-object-state")
        assert state.status_code == 200
        assert state.get_json()["has_business_data"] is False
