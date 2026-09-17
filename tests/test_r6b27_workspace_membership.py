"""R6B-2.7 Window 5 — canonical workspace-membership provisioning.

Proves the membership bridge that did not previously exist:

    identity → sh_workspace_memberships → sh_workspaces → organization

Every assertion here is an AUTHORIZATION decision. Nothing is inferred:
a missing authorization context must fail closed.

NOTE ON ``system_scope``: these tests never grant through it. The audited
system-scope provisioning path belongs to the operator script, not to tests —
using it here would hide whether the real authorization path works. Grants in
this file go through the actor path (an active organization owner/admin), and
``system_scope=True`` appears only as a CONTRADICTORY probe that must be
rejected.
"""
import pytest

ORG = 901
ORG_B = 902
WS = "ws_cert_a"
WS_OTHER_ORG = "ws_cert_b"

OWNER = "sid_wm_owner"        # org owner (bootstraps)
ADMIN = "sid_wm_admin"        # org admin
MEMBER = "sid_wm_member"      # org member — may NOT administer
OUTSIDER = "sid_wm_outsider"  # no org membership at all
TARGET = "sid_wm_target"      # the identity being provisioned


def _org(org_id=ORG, name="Cert Org"):
    from app import db
    from app.models import Organization
    org = Organization(id=org_id, name=name, slug=f"cert-org-{org_id}")
    db.session.add(org)
    db.session.commit()
    return org


def _org_member(org_id, identity_id, role="member", active=True):
    from app import db
    from app.models import OrgMember
    om = OrgMember(organization_id=org_id, identity_id=identity_id,
                   role=role, is_active=active)
    db.session.add(om)
    db.session.commit()
    return om


def _workspace(ws_id=WS, org_id=ORG, status="active"):
    from app import db
    from app.objects.legacy_models import Workspace
    ws = Workspace(id=ws_id, name="Cert Workspace", workspace_type="custom",
                   created_by="system", organization_id=org_id, status=status)
    db.session.add(ws)
    db.session.commit()
    return ws


def _administering_actor(org_id=ORG):
    """Seed an active org owner — the legitimate granting actor."""
    _org_member(org_id, OWNER, "owner")
    return OWNER


class TestGrant:
    def test_org_owner_grant_creates_canonical_membership(self, app):
        from app.authz.workspace_membership import grant
        from app.objects.legacy_models import ShWorkspaceMembership
        _org(); _workspace(); _administering_actor()

        result = grant(WS, TARGET, "owner", actor_identity_id=OWNER)

        assert result["is_active"] is True
        assert result["role"] == "owner"
        assert ShWorkspaceMembership.query.filter_by(
            workspace_id=WS, identity_id=TARGET, is_active=True).count() == 1

    def test_granted_membership_authorizes_the_workspace(self, app):
        """The bridge must actually work: authorized_workspace_ids sees it."""
        from app.authz.workspace_membership import grant
        from app.authz.workspace_context import authorized_workspace_ids
        _org(); _workspace(); _administering_actor()

        assert authorized_workspace_ids(TARGET, ORG) == []
        grant(WS, TARGET, "member", actor_identity_id=OWNER)
        assert authorized_workspace_ids(TARGET, ORG) == [WS]

    def test_assert_object_access_passes_after_grant(self, app):
        from app.authz.workspace_membership import grant
        from app.authz.workspace_context import assert_object_access
        _org(); _workspace(); _administering_actor()

        with pytest.raises(Exception):
            assert_object_access(TARGET, ORG, WS)  # fail-closed before

        grant(WS, TARGET, "member", actor_identity_id=OWNER)
        assert_object_access(TARGET, ORG, WS)      # authorized after

    def test_grant_is_idempotent(self, app):
        from app.authz.workspace_membership import grant
        from app.objects.legacy_models import ShWorkspaceMembership
        _org(); _workspace(); _administering_actor()

        grant(WS, TARGET, "member", actor_identity_id=OWNER)
        grant(WS, TARGET, "admin", actor_identity_id=OWNER)

        rows = ShWorkspaceMembership.query.filter_by(
            workspace_id=WS, identity_id=TARGET).all()
        assert len(rows) == 1
        assert rows[0].role == "admin"

    def test_org_admin_may_grant(self, app):
        from app.authz.workspace_membership import grant
        _org(); _workspace()
        _org_member(ORG, ADMIN, "admin")
        assert grant(WS, TARGET, "member",
                     actor_identity_id=ADMIN)["role"] == "member"

    def test_existing_workspace_owner_may_grant(self, app):
        """A workspace owner (not necessarily an org owner) may add members."""
        from app.authz.workspace_membership import grant
        _org(); _workspace(); _administering_actor()
        grant(WS, OWNER, "owner", actor_identity_id=OWNER)

        assert grant(WS, TARGET, "member",
                     actor_identity_id=OWNER)["is_active"] is True

    def test_ordinary_member_may_not_grant(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace(); _org_member(ORG, MEMBER, "member")
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "member", actor_identity_id=MEMBER)
        assert e.value.code == "not_authorized_to_administer_workspace"

    def test_outsider_may_not_grant(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError):
            grant(WS, TARGET, "member", actor_identity_id=OUTSIDER)

    def test_inactive_org_member_may_not_grant(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace()
        _org_member(ORG, OWNER, "owner", active=False)
        with pytest.raises(WorkspaceMembershipError):
            grant(WS, TARGET, "member", actor_identity_id=OWNER)

    def test_org_admin_of_another_org_may_not_grant(self, app):
        """Administrating org B must not confer rights over org A's workspace."""
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace()
        _org(ORG_B, "Org B")
        _org_member(ORG_B, OWNER, "owner")
        with pytest.raises(WorkspaceMembershipError):
            grant(WS, TARGET, "member", actor_identity_id=OWNER)

    def test_no_authorization_context_fails_closed(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "member")
        assert e.value.code == "no_authorization_context"

    def test_identity_and_system_scope_are_exclusive(self, app):
        """A CONTRADICTORY probe: both contexts at once must be rejected."""
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace(); _administering_actor()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "member", actor_identity_id=OWNER,
                  system_scope=True)
        assert e.value.code == "contradictory_authorization_context"

    def test_invalid_role_rejected(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace(); _administering_actor()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "superuser", actor_identity_id=OWNER)
        assert e.value.code == "invalid_role"

    def test_unknown_workspace_rejected(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _administering_actor()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant("ws_does_not_exist", TARGET, "member",
                  actor_identity_id=OWNER)
        assert e.value.code == "workspace_not_found"

    def test_inactive_workspace_rejected(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace(status="archived"); _administering_actor()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "member", actor_identity_id=OWNER)
        assert e.value.code == "workspace_inactive"

    def test_membership_for_other_org_does_not_authorize(self, app):
        """A membership granted in org A must not authorize org B."""
        from app.authz.workspace_membership import grant
        from app.authz.workspace_context import authorized_workspace_ids
        _org(ORG, "Org A")
        _workspace(WS, ORG)
        _org_member(ORG, OWNER, "owner")

        grant(WS, TARGET, "member", actor_identity_id=OWNER)

        assert authorized_workspace_ids(TARGET, ORG) == [WS]
        assert authorized_workspace_ids(TARGET, ORG_B) == []


class TestRevoke:
    def test_revoke_deactivates_and_deauthorizes(self, app):
        from app.authz.workspace_membership import grant, revoke
        from app.authz.workspace_context import authorized_workspace_ids
        from app.objects.legacy_models import ShWorkspaceMembership
        _org(); _workspace(); _administering_actor()

        grant(WS, TARGET, "member", actor_identity_id=OWNER)
        assert authorized_workspace_ids(TARGET, ORG) == [WS]

        assert revoke(WS, TARGET, actor_identity_id=OWNER) is True
        assert authorized_workspace_ids(TARGET, ORG) == []

        # The row is retained (inactive), never deleted.
        row = ShWorkspaceMembership.query.filter_by(
            workspace_id=WS, identity_id=TARGET).one()
        assert row.is_active is False

    def test_revoke_requires_authorization(self, app):
        from app.authz.workspace_membership import (
            revoke, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError):
            revoke(WS, TARGET)

    def test_revoke_missing_membership_returns_false(self, app):
        from app.authz.workspace_membership import revoke
        _org(); _workspace(); _administering_actor()
        assert revoke(WS, TARGET, actor_identity_id=OWNER) is False


class TestListMembers:
    def test_lists_memberships(self, app):
        from app.authz.workspace_membership import grant, list_members
        _org(); _workspace(); _administering_actor()
        grant(WS, TARGET, "owner", actor_identity_id=OWNER)
        members = list_members(WS, actor_identity_id=OWNER)
        assert len(members) == 1
        assert members[0]["identity_id"] == TARGET

    def test_requires_authorization(self, app):
        from app.authz.workspace_membership import (
            list_members, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError):
            list_members(WS)