"""R6B-2.7 Window 5 — canonical workspace-membership provisioning.

Proves the membership bridge that did not previously exist:

    identity → sh_workspace_memberships → sh_workspaces → organization

Every assertion here is an AUTHORIZATION decision. Nothing is inferred:
a missing authorization context must fail closed.
"""
import pytest

ORG = 901
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


class TestGrant:
    def test_system_scope_grant_creates_canonical_membership(self, app):
        from app.authz.workspace_membership import grant
        from app.objects.legacy_models import ShWorkspaceMembership
        _org(); _workspace()

        result = grant(WS, TARGET, "owner", system_scope=True)

        assert result["is_active"] is True
        assert result["role"] == "owner"
        assert ShWorkspaceMembership.query.filter_by(
            workspace_id=WS, identity_id=TARGET, is_active=True).count() == 1

    def test_granted_membership_authorizes_the_workspace(self, app):
        """The bridge must actually work: authorized_workspace_ids sees it."""
        from app.authz.workspace_membership import grant
        from app.authz.workspace_context import authorized_workspace_ids
        _org(); _workspace(); _org_member(ORG, TARGET, "owner")

        assert authorized_workspace_ids(TARGET, ORG) == []
        grant(WS, TARGET, "member", system_scope=True)
        assert authorized_workspace_ids(TARGET, ORG) == [WS]

    def test_assert_object_access_passes_after_grant(self, app):
        from app.authz.workspace_membership import grant
        from app.authz.workspace_context import assert_object_access
        _org(); _workspace(); _org_member(ORG, TARGET, "owner")

        with pytest.raises(Exception):
            assert_object_access(TARGET, ORG, WS)  # fail-closed before

        grant(WS, TARGET, "member", system_scope=True)
        assert_object_access(TARGET, ORG, WS)      # authorized after

    def test_grant_is_idempotent(self, app):
        from app.authz.workspace_membership import grant
        from app.objects.legacy_models import ShWorkspaceMembership
        _org(); _workspace()

        grant(WS, TARGET, "member", system_scope=True)
        grant(WS, TARGET, "admin", system_scope=True)

        rows = ShWorkspaceMembership.query.filter_by(
            workspace_id=WS, identity_id=TARGET).all()
        assert len(rows) == 1
        assert rows[0].role == "admin"

    def test_org_owner_may_bootstrap_via_identity(self, app):
        from app.authz.workspace_membership import grant
        _org(); _workspace(); _org_member(ORG, OWNER, "owner")

        result = grant(WS, TARGET, "member", actor_identity_id=OWNER)
        assert result["is_active"] is True

    def test_org_admin_may_grant(self, app):
        from app.authz.workspace_membership import grant
        _org(); _workspace(); _org_member(ORG, ADMIN, "admin")
        assert grant(WS, TARGET, "member",
                     actor_identity_id=ADMIN)["role"] == "member"

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

    def test_no_authorization_context_fails_closed(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "member")
        assert e.value.code == "no_authorization_context"

    def test_identity_and_system_scope_are_exclusive(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "member", actor_identity_id=OWNER,
                  system_scope=True)
        assert e.value.code == "contradictory_authorization_context"

    def test_invalid_role_rejected(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "superuser", system_scope=True)
        assert e.value.code == "invalid_role"

    def test_unknown_workspace_rejected(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org()
        with pytest.raises(WorkspaceMembershipError) as e:
            grant("ws_does_not_exist", TARGET, "member", system_scope=True)
        assert e.value.code == "workspace_not_found"

    def test_inactive_workspace_rejected(self, app):
        from app.authz.workspace_membership import (
            grant, WorkspaceMembershipError)
        _org(); _workspace(status="archived")
        with pytest.raises(WorkspaceMembershipError) as e:
            grant(WS, TARGET, "member", system_scope=True)
        assert e.value.code == "workspace_inactive"

    def test_membership_for_other_org_does_not_authorize(self, app):
        """A membership in org A must not authorize a workspace in org B."""
        from app.authz.workspace_membership import grant
        from app.authz.workspace_context import authorized_workspace_ids
        _org(901, "Org A"); _org(902, "Org B")
        _workspace(WS, 901); _workspace(WS_OTHER_ORG, 902)
        _org_member(901, TARGET, "owner")

        grant(WS, TARGET, "member", system_scope=True)

        assert authorized_workspace_ids(TARGET, 901) == [WS]
        assert authorized_workspace_ids(TARGET, 902) == []


class TestRevoke:
    def test_revoke_deactivates_and_deauthorizes(self, app):
        from app.authz.workspace_membership import grant, revoke
        from app.authz.workspace_context import authorized_workspace_ids
        from app.objects.legacy_models import ShWorkspaceMembership
        _org(); _workspace(); _org_member(ORG, TARGET, "owner")

        grant(WS, TARGET, "member", system_scope=True)
        assert authorized_workspace_ids(TARGET, ORG) == [WS]

        assert revoke(WS, TARGET, system_scope=True) is True
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
        _org(); _workspace()
        assert revoke(WS, TARGET, system_scope=True) is False


class TestListMembers:
    def test_lists_memberships(self, app):
        from app.authz.workspace_membership import grant, list_members
        _org(); _workspace()
        grant(WS, TARGET, "owner", system_scope=True)
        members = list_members(WS, system_scope=True)
        assert len(members) == 1
        assert members[0]["identity_id"] == TARGET

    def test_requires_authorization(self, app):
        from app.authz.workspace_membership import (
            list_members, WorkspaceMembershipError)
        _org(); _workspace()
        with pytest.raises(WorkspaceMembershipError):
            list_members(WS)