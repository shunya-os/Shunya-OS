"""R6B-2.7 Window 6 — Batch B/D: canonical object authorization matrix.

Proves the authorization boundary for create/get/update/delete at BOTH the
service boundary (direct invocation, no HTTP) and the real HTTP routes.

Tenancy is built explicitly and minimally — no synthetic organization, no
`synthetic workspace` (spc_*), no universal membership, no `system_scope`.
Every denial asserted here is an AUTHORIZATION decision, never a
missing-parameter error and never a 404/405 from an absent route.

Layout
------
Org 701 (A): ws_matrix_a1 (alice, mallory, multi, inactive*)
             ws_matrix_a2 (alice)
             ws_matrix_a3 (NOBODY — owned by A, authorized to none)
Org 702 (B): ws_matrix_b1 (bob, multi)
Org 703 (C): ws_matrix_c1 (carol)

* `inactive` holds INACTIVE membership rows only.

Identities: alice (A), bob (B), mallory (A/a1), multi (A+B), carol (C),
nobody (no membership at all), inactive (A/a1 but inactive).
"""
import pytest
import uuid

ORG_A, ORG_B, ORG_C = 701, 702, 703

WS_A1 = "ws_matrix_a1"
WS_A2 = "ws_matrix_a2"
WS_A3 = "ws_matrix_a3"
WS_B1 = "ws_matrix_b1"
WS_C1 = "ws_matrix_c1"

ALICE = "matrix-alice@example.com"
BOB = "matrix-bob@example.com"
MALLORY = "matrix-mallory@example.com"
MULTI = "matrix-multi@example.com"
CAROL = "matrix-carol@example.com"
NOBODY = "matrix-nobody@example.com"
INACTIVE = "matrix-inactive@example.com"


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


# ---------------------------------------------------------------------------
# Minimal explicit tenancy construction
# ---------------------------------------------------------------------------

def _org(db, oid):
    from app.models import Organization
    org = db.session.get(Organization, oid)
    if not org:
        org = Organization(id=oid, name=f"Matrix Org {oid}",
                           slug=f"matrix-org-{oid}", is_active=True)
        db.session.add(org)
        db.session.flush()
    return org


def _member(db, oid, identity, role="owner", active=True):
    """OrgMember row. `owner` is used for identities that must also pass the
    HTTP RBAC decorator (owner holds all permissions in this product)."""
    from app.models import OrgMember
    m = (db.session.query(OrgMember)
         .filter_by(organization_id=oid, identity_id=identity).first())
    if not m:
        m = OrgMember(organization_id=oid, identity_id=identity,
                      role=role, is_active=active)
        db.session.add(m)
        db.session.flush()
    else:
        m.role = role
        m.is_active = active
        db.session.flush()
    return m


def _ws(db, oid, ws_id):
    from app.objects.legacy_models import Workspace
    w = db.session.get(Workspace, ws_id)
    if not w:
        w = Workspace(id=ws_id, name=ws_id, workspace_type="business",
                      status="active", created_by="matrix_fixture",
                      organization_id=oid)
        db.session.add(w)
        db.session.flush()
    return w


def _ws_member(db, ws_id, identity, active=True):
    from app.objects.legacy_models import ShWorkspaceMembership
    m = (db.session.query(ShWorkspaceMembership)
         .filter_by(workspace_id=ws_id, identity_id=identity).first())
    if not m:
        m = ShWorkspaceMembership(workspace_id=ws_id, identity_id=identity,
                                  role="owner", is_active=active)
        db.session.add(m)
        db.session.flush()
    else:
        m.is_active = active
        db.session.flush()
    return m


@pytest.fixture
def tenancy(app):
    """Idempotent canonical tenancy for the whole matrix."""
    from app import db
    with app.app_context():
        for oid in (ORG_A, ORG_B, ORG_C):
            _org(db, oid)
        _ws(db, ORG_A, WS_A1)
        _ws(db, ORG_A, WS_A2)
        _ws(db, ORG_A, WS_A3)
        _ws(db, ORG_B, WS_B1)
        _ws(db, ORG_C, WS_C1)

        # alice — Org A, authorized for a1 AND a2 (multi-workspace case)
        _member(db, ORG_A, ALICE)
        _ws_member(db, WS_A1, ALICE)
        _ws_member(db, WS_A2, ALICE)

        # bob — Org B only
        _member(db, ORG_B, BOB)
        _ws_member(db, WS_B1, BOB)

        # mallory — Org A, authorized ONLY for a1 (attacker with a valid org)
        _member(db, ORG_A, MALLORY)
        _ws_member(db, WS_A1, MALLORY)

        # multi — member of A and B (multi-organization case)
        _member(db, ORG_A, MULTI)
        _member(db, ORG_B, MULTI)
        _ws_member(db, WS_A1, MULTI)
        _ws_member(db, WS_B1, MULTI)

        # carol — Org C only
        _member(db, ORG_C, CAROL)
        _ws_member(db, WS_C1, CAROL)

        # inactive — rows exist but are INACTIVE
        _member(db, ORG_A, INACTIVE, active=False)
        _ws_member(db, WS_A1, INACTIVE, active=False)

        # nobody — deliberately no membership rows at all
        db.session.commit()
    yield


def _svc():
    from core.object_service import get_object_service
    return get_object_service()


def _ctx_err():
    from app.authz.workspace_context import OwnershipContextError
    return OwnershipContextError


class TestServiceCreateAuthorization:
    """§14/§16 — create() at the service boundary, no HTTP involved."""

    def test_create_positive(self, app, tenancy):
        with app.app_context():
            obj = _svc().create(object_type="doc", name="Create Positive",
                                organization_id=ORG_A, workspace_id=WS_A1,
                                identity_id=ALICE)
            assert obj["id"] > 0
            assert obj["organization_id"] == ORG_A
            assert obj["name"] == "Create Positive"

    def test_create_wrong_organization_denied(self, app, tenancy):
        """alice presents Org B, which she is not a member of → authorization denial."""
        with app.app_context():
            with pytest.raises(_ctx_err()):
                _svc().create(object_type="doc", name="Wrong Org",
                              organization_id=ORG_B, workspace_id=WS_B1,
                              identity_id=ALICE)

    def test_create_wrong_workspace_denied(self, app, tenancy):
        """WS_A3 belongs to Org A but alice holds no membership in it."""
        with app.app_context():
            with pytest.raises(_ctx_err()):
                _svc().create(object_type="doc", name="Wrong Workspace",
                              organization_id=ORG_A, workspace_id=WS_A3,
                              identity_id=ALICE)

    def test_create_cross_organization_workspace_rejected(self, app, tenancy):
        """Org A + a workspace owned by Org B violates the ownership invariant."""
        with app.app_context():
            with pytest.raises(ValueError):
                _svc().create(object_type="doc", name="Cross Org Workspace",
                              organization_id=ORG_A, workspace_id=WS_B1,
                              identity_id=ALICE)

    def test_create_missing_membership_denied(self, app, tenancy):
        """nobody has no membership rows at all."""
        with app.app_context():
            with pytest.raises(_ctx_err()):
                _svc().create(object_type="doc", name="No Membership",
                              organization_id=ORG_A, workspace_id=WS_A1,
                              identity_id=NOBODY)

    def test_create_inactive_membership_denied(self, app, tenancy):
        """inactive holds the rows but they are is_active=False."""
        with app.app_context():
            with pytest.raises(_ctx_err()):
                _svc().create(object_type="doc", name="Inactive",
                              organization_id=ORG_A, workspace_id=WS_A1,
                              identity_id=INACTIVE)

    def test_create_missing_identity_denied(self, app, tenancy):
        with app.app_context():
            with pytest.raises(ValueError):
                _svc().create(object_type="doc", name="No Identity",
                              organization_id=ORG_A, workspace_id=WS_A1)

    def test_create_contradictory_identity_and_system_scope_denied(self, app, tenancy):
        with app.app_context():
            with pytest.raises(ValueError):
                _svc().create(object_type="doc", name="Contradictory",
                              organization_id=ORG_A, workspace_id=WS_A1,
                              identity_id=ALICE, system_scope=True)


class TestServiceGetAuthorization:
    """§14/§16 — get() at the service boundary."""

    def test_get_positive(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Get Positive",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            got = svc.get(obj["id"], organization_id=ORG_A,
                          identity_id=ALICE)
            assert got is not None
            assert got["name"] == "Get Positive"

    def test_get_wrong_organization_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Get Wrong Org",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.get(obj["id"], organization_id=ORG_B,
                           identity_id=ALICE) is None

    def test_get_wrong_identity_denied(self, app, tenancy):
        """The object exists in ORG_A, but bob is not authorized for its workspace."""
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Get Wrong Identity",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=BOB) is None

    def test_get_missing_membership_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Get No Membership",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=NOBODY) is None

    def test_get_inactive_membership_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Get Inactive",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=INACTIVE) is None

    def test_get_missing_identity_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Get No Identity",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            with pytest.raises(ValueError):
                svc.get(obj["id"], organization_id=ORG_A)

    def test_get_contradictory_identity_and_system_scope_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Get Contradictory",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            with pytest.raises(ValueError):
                svc.get(obj["id"], organization_id=ORG_A,
                        identity_id=ALICE, system_scope=True)


class TestServiceUpdateDeleteAuthorization:
    """§14/§16 — update() and delete() at the service boundary."""

    def test_update_positive(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Update Positive",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.update(obj["id"], ORG_A, identity_id=ALICE,
                              name="Updated") is True
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=ALICE)["name"] == "Updated"

    def test_update_wrong_organization_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Update Wrong Org",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.update(obj["id"], ORG_B, identity_id=ALICE,
                              name="pwned") is False
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=ALICE)["name"] == "Update Wrong Org"

    def test_update_wrong_identity_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Update Wrong Identity",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.update(obj["id"], ORG_A, identity_id=BOB,
                              name="pwned") is False
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=ALICE)["name"] == "Update Wrong Identity"

    def test_update_missing_membership_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Update No Membership",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.update(obj["id"], ORG_A, identity_id=NOBODY,
                              name="pwned") is False

    def test_update_inactive_membership_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Update Inactive",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.update(obj["id"], ORG_A, identity_id=INACTIVE,
                              name="pwned") is False

    def test_update_missing_identity_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Update No Identity",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            with pytest.raises(ValueError):
                svc.update(obj["id"], ORG_A, name="pwned")

    def test_update_contradictory_identity_and_system_scope_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Update Contradictory",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            with pytest.raises(ValueError):
                svc.update(obj["id"], ORG_A, identity_id=ALICE,
                           system_scope=True, name="pwned")

    def test_delete_positive(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Delete Positive",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.delete(obj["id"], organization_id=ORG_A,
                              identity_id=ALICE) is True
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=ALICE)["status"] == "archived"

    def test_delete_wrong_organization_denied(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Delete Wrong Org",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.delete(obj["id"], organization_id=ORG_B,
                              identity_id=ALICE) is False
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=ALICE)["status"] == "active"

    def test_delete_wrong_identity_denied(self, app, tenancy):
        """delete() delegates to update() — this proves the delegated gate is real.

        bob belongs to Org B; he is not authorized anywhere in Org A.
        (Authorization is org+workspace scoped: a genuine member of the SAME
        workspace is authorized for objects in it — that is the intended
        boundary and is asserted separately in TestPersistedOwnershipWins.)
        """
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Delete Wrong Identity",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            assert svc.delete(obj["id"], organization_id=ORG_A,
                              identity_id=BOB) is False
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=ALICE)["status"] == "active"

    def test_delete_missing_identity_denied(self, app, tenancy):
        """The historical defect: delete() → unauthenticated update(). Must raise."""
        with app.app_context():
            svc = _svc()
            obj = svc.create(object_type="doc", name="Delete No Identity",
                             organization_id=ORG_A, workspace_id=WS_A1,
                             identity_id=ALICE)
            with pytest.raises(ValueError):
                svc.delete(obj["id"], organization_id=ORG_A)
            assert svc.get(obj["id"], organization_id=ORG_A,
                           identity_id=ALICE)["status"] == "active"


class TestPersistedOwnershipWins:
    """§14 — caller-supplied organization/workspace must NOT override the
    object's PERSISTED ownership."""

    def test_update_uses_persisted_workspace_not_callers_org(self, app, tenancy):
        """mallory is a genuine member of ORG_A — and supplies it correctly —
        but the object lives in WS_A2, where she holds no membership."""
        with app.app_context():
            svc = _svc()
            victim = svc.create(object_type="doc", name="Persisted Victim",
                                organization_id=ORG_A, workspace_id=WS_A2,
                                identity_id=ALICE)
            # mallory's org is ORG_A and it matches the object's org exactly.
            assert svc.update(victim["id"], ORG_A, identity_id=MALLORY,
                              name="pwned") is False
            assert svc.get(victim["id"], organization_id=ORG_A,
                           identity_id=ALICE)["name"] == "Persisted Victim"

    def test_get_uses_persisted_workspace_not_callers_org(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            victim = svc.create(object_type="doc", name="Persisted Victim 2",
                                organization_id=ORG_A, workspace_id=WS_A2,
                                identity_id=ALICE)
            assert svc.get(victim["id"], organization_id=ORG_A,
                           identity_id=MALLORY) is None

    def test_attacker_own_workspace_membership_does_not_leak(self, app, tenancy):
        """mallory IS authorized for WS_A1. That must not spill over to WS_A2."""
        with app.app_context():
            svc = _svc()
            allowed = svc.create(object_type="doc", name="Mallory Own",
                                 organization_id=ORG_A, workspace_id=WS_A1,
                                 identity_id=MALLORY)
            assert allowed["id"] > 0
            with pytest.raises(_ctx_err()):
                svc.create(object_type="doc", name="Mallory Sneak",
                           organization_id=ORG_A, workspace_id=WS_A2,
                           identity_id=MALLORY)


class TestAdversarialOwnership:
    """§15 — attacker identity vs victim object/org/workspace.

    Every denial below must be the AUTHORIZATION decision. The calls therefore
    complete (returning a denial) rather than raising a missing-parameter
    error, and the victim's state is re-read afterwards to prove no mutation.
    """

    @staticmethod
    def _victim(svc):
        return svc.create(object_type="doc", name="Victim Asset",
                          organization_id=ORG_A, workspace_id=WS_A2,
                          identity_id=ALICE)

    def test_attacker_cannot_read_victim_object(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            victim = self._victim(svc)
            # Attacker supplies the victim's real org AND the victim's workspace.
            result = svc.get(victim["id"], organization_id=ORG_A,
                             identity_id=MALLORY)
            assert result is None

    def test_attacker_cannot_update_victim_object(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            victim = self._victim(svc)
            ok = svc.update(victim["id"], ORG_A, identity_id=MALLORY,
                            name="owned-by-attacker")
            assert ok is False
            after = svc.get(victim["id"], organization_id=ORG_A,
                            identity_id=ALICE)
            assert after["name"] == "Victim Asset"
            assert after["status"] == "active"

    def test_attacker_cannot_delete_victim_object(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            victim = self._victim(svc)
            ok = svc.delete(victim["id"], organization_id=ORG_A,
                            identity_id=MALLORY)
            assert ok is False
            assert svc.get(victim["id"], organization_id=ORG_A,
                           identity_id=ALICE)["status"] == "active"

    def test_attacker_cannot_create_inside_victim_workspace(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            with pytest.raises(_ctx_err()):
                svc.create(object_type="doc", name="Injected",
                           organization_id=ORG_A, workspace_id=WS_A2,
                           identity_id=MALLORY)


class TestMultiOrganizationAuthorization:
    """§18 — Org A / Org B / unauthorized Org C, no arbitrary `.first()`."""

    def test_explicit_org_a_resolves_a(self, app, tenancy):
        from app.authz.workspace_context import resolve_current_organization
        with app.app_context():
            assert resolve_current_organization(MULTI, ORG_A) == ORG_A

    def test_explicit_org_b_resolves_b(self, app, tenancy):
        from app.authz.workspace_context import resolve_current_organization
        with app.app_context():
            assert resolve_current_organization(MULTI, ORG_B) == ORG_B

    def test_no_selection_with_two_orgs_fails_closed(self, app, tenancy):
        from app.authz.workspace_context import (
            OwnershipContextError, resolve_current_organization,
        )
        with app.app_context():
            with pytest.raises(OwnershipContextError) as exc:
                resolve_current_organization(MULTI, None)
            assert exc.value.code == "organization_selection_required"

    def test_unauthorized_org_c_denied(self, app, tenancy):
        from app.authz.workspace_context import (
            OwnershipContextError, resolve_current_organization,
        )
        with app.app_context():
            with pytest.raises(OwnershipContextError) as exc:
                resolve_current_organization(MULTI, ORG_C)
            assert exc.value.code == "organization_not_authorized"

    def test_single_org_resolves_automatically(self, app, tenancy):
        from app.authz.workspace_context import resolve_current_organization
        with app.app_context():
            assert resolve_current_organization(ALICE, None) == ORG_A

    def test_zero_orgs_fails_closed(self, app, tenancy):
        from app.authz.workspace_context import (
            OwnershipContextError, resolve_current_organization,
        )
        with app.app_context():
            with pytest.raises(OwnershipContextError) as exc:
                resolve_current_organization(NOBODY, None)
            assert exc.value.code == "no_active_organization"


class TestMultiWorkspaceAuthorization:
    """§19 — Org A owns A1/A2/A3; alice is authorized for A1 and A2 only."""

    def test_explicit_a1_resolves_a1(self, app, tenancy):
        from app.authz.workspace_context import resolve_current_workspace
        with app.app_context():
            assert resolve_current_workspace(ALICE, ORG_A, WS_A1) == WS_A1

    def test_explicit_a2_resolves_a2(self, app, tenancy):
        from app.authz.workspace_context import resolve_current_workspace
        with app.app_context():
            assert resolve_current_workspace(ALICE, ORG_A, WS_A2) == WS_A2

    def test_multiple_workspaces_without_selection_fails_closed(self, app, tenancy):
        from app.authz.workspace_context import (
            OwnershipContextError, resolve_current_workspace,
        )
        with app.app_context():
            with pytest.raises(OwnershipContextError) as exc:
                resolve_current_workspace(ALICE, ORG_A, None)
            assert exc.value.code == "workspace_selection_required"

    def test_unauthorized_workspace_denied(self, app, tenancy):
        """A3 belongs to Org A but nobody is a member of it."""
        from app.authz.workspace_context import (
            OwnershipContextError, resolve_current_workspace,
        )
        with app.app_context():
            with pytest.raises(OwnershipContextError) as exc:
                resolve_current_workspace(ALICE, ORG_A, WS_A3)
            assert exc.value.code == "workspace_not_authorized"

    def test_other_organization_workspace_denied(self, app, tenancy):
        from app.authz.workspace_context import (
            OwnershipContextError, resolve_current_workspace,
        )
        with app.app_context():
            with pytest.raises(OwnershipContextError) as exc:
                resolve_current_workspace(ALICE, ORG_A, WS_B1)
            assert exc.value.code == "workspace_other_organization"

    def test_no_authorized_workspace_fails_closed(self, app, tenancy):
        from app.authz.workspace_context import (
            OwnershipContextError, resolve_current_workspace,
        )
        with app.app_context():
            with pytest.raises(OwnershipContextError) as exc:
                resolve_current_workspace(NOBODY, ORG_A, None)
            assert exc.value.code == "no_authorized_workspace"

    def test_single_workspace_resolves_automatically(self, app, tenancy):
        from app.authz.workspace_context import resolve_current_workspace
        with app.app_context():
            assert resolve_current_workspace(MALLORY, ORG_A, None) == WS_A1

    def test_object_isolation_between_a1_and_a2(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            in_a1 = svc.create(object_type="doc", name="Isolated A1",
                               organization_id=ORG_A, workspace_id=WS_A1,
                               identity_id=ALICE)
            in_a2 = svc.create(object_type="doc", name="Isolated A2",
                               organization_id=ORG_A, workspace_id=WS_A2,
                               identity_id=ALICE)
            a1_ids = [o["id"] for o in svc.list_by_workspace(
                WS_A1, ORG_A, identity_id=ALICE)]
            a2_ids = [o["id"] for o in svc.list_by_workspace(
                WS_A2, ORG_A, identity_id=ALICE)]
            assert in_a1["id"] in a1_ids and in_a1["id"] not in a2_ids
            assert in_a2["id"] in a2_ids and in_a2["id"] not in a1_ids


def _login(client, identity, org_id):
    with client.session_transaction() as sess:
        sess["identity_id"] = identity
        sess["user_id"] = identity
        sess["current_org_id"] = str(org_id)
        sess["_fresh"] = True
    return client


class TestHttpAuthorization:
    """§17 — the same decisions through the REAL routes.

    Every protected operation below is actually reached: the owner path returns
    200 on the very same route/method where the attacker path is denied, so a
    404/405 from an absent route can never be mistaken for authorization.
    """

    def test_http_create_positive(self, app, client, tenancy):
        _login(client, ALICE, ORG_A)
        resp = client.post("/api/v1/objects/", json={
            "name": "HTTP Matrix Object",
            "object_type": "doc",
            "workspace_id": WS_A1,
        })
        data = resp.get_json()
        assert resp.status_code == 200, f"Create failed: {data}"
        assert data["success"] is True
        assert data["organization_id"] == ORG_A
        obj_id = data["id"]
        with app.app_context():
            persisted = _svc().get(obj_id, organization_id=ORG_A,
                                   identity_id=ALICE)
            assert persisted is not None
            assert persisted["name"] == "HTTP Matrix Object"
            assert persisted["workspace_id"] == WS_A1
            assert persisted["organization_id"] == ORG_A

    def test_http_create_without_workspace_selection_denied(self, app, client, tenancy):
        """alice is authorized for two workspaces — she must select one."""
        _login(client, ALICE, ORG_A)
        resp = client.post("/api/v1/objects/", json={
            "name": "No Selection", "object_type": "doc",
        })
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["success"] is False
        assert data["code"] == "workspace_selection_required"

    def test_http_create_unauthorized_workspace_denied(self, app, client, tenancy):
        _login(client, ALICE, ORG_A)
        resp = client.post("/api/v1/objects/", json={
            "name": "Bad Workspace", "object_type": "doc",
            "workspace_id": WS_A3,
        })
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "workspace_not_authorized"

    def test_http_create_unauthorized_organization_denied(self, app, client, tenancy):
        _login(client, ALICE, ORG_A)
        resp = client.post("/api/v1/objects/", json={
            "name": "Bad Org", "object_type": "doc",
            "workspace_id": WS_A1,
        }, headers={"X-Organization-Id": str(ORG_B)})
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "organization_not_authorized"

    def test_http_create_unauthenticated_denied(self, app, client, tenancy):
        resp = client.post("/api/v1/objects/", json={
            "name": "Anon", "object_type": "doc",
        })
        assert resp.status_code == 401
        assert resp.get_json()["success"] is False

    def test_http_patch_owner_succeeds_and_attacker_denied(self, app, client, tenancy):
        """Same route, same method, same body. Owner 200; attacker denied; and the
        victim object is provably unchanged — so the denial is the authorization
        decision, not a missing route."""
        with app.app_context():
            victim = _svc().create(object_type="doc", name="HTTP Victim",
                                   organization_id=ORG_A, workspace_id=WS_A2,
                                   identity_id=ALICE)
            victim_id = victim["id"]

        # Owner path — reaches the operation and succeeds.
        _login(client, ALICE, ORG_A)
        ok = client.patch(f"/api/v1/objects/{victim_id}",
                          json={"name": "renamed-by-owner"},
                          headers={"X-Workspace-Id": WS_A2})
        assert ok.status_code == 200, f"owner PATCH failed: {ok.get_json()}"
        with app.app_context():
            assert _svc().get(victim_id, organization_id=ORG_A,
                              identity_id=ALICE)["name"] == "renamed-by-owner"

        # Attacker path — mallory is a genuine Org A member (WS_A1 only).
        _login(client, MALLORY, ORG_A)
        denied = client.patch(f"/api/v1/objects/{victim_id}",
                              json={"name": "owned-by-attacker"})
        assert denied.status_code in (403, 404), \
            f"attacker PATCH unexpectedly reached a write: {denied.get_json()}"
        with app.app_context():
            after = _svc().get(victim_id, organization_id=ORG_A,
                               identity_id=ALICE)
            assert after["name"] == "renamed-by-owner", \
                "attacker must not have mutated the victim object"

    def test_http_patch_attacker_unauthorized_workspace_denied(self, app, client, tenancy):
        """mallory explicitly requests the victim's workspace → denied at context."""
        _login(client, MALLORY, ORG_A)
        resp = client.patch("/api/v1/objects/1", json={"name": "x"},
                            headers={"X-Workspace-Id": WS_A2})
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "workspace_not_authorized"


class TestReadSurfaceAuthorization:
    """Batch E — all six non-CRUD read surfaces are authorization-gated.

    `search`, `get_by_type`, `count_by_type`, `list_by_workspace`,
    `list_by_creator`, `get_by_object_id` must each (a) work for an authorized
    identity and (b) deny wrong-org / wrong-workspace / wrong-identity, and must
    never leak an object outside the caller's authorized workspaces.
    """

    @staticmethod
    def _seed(svc):
        """Two uniquely-named objects in A1/A2, both CREATED BY alice.

        The name tag and the dedicated object_type isolate this class from
        objects created by other tests sharing the module's database, so the
        assertions below are exact rather than merely non-empty.
        """
        tag = uuid.uuid4().hex[:8]
        names = (f"R6B27-{tag}-A1", f"R6B27-{tag}-A2")
        a1 = svc.create(object_type="r6b27doc", name=names[0],
                        organization_id=ORG_A, workspace_id=WS_A1,
                        identity_id=ALICE, created_by=ALICE)
        a2 = svc.create(object_type="r6b27doc", name=names[1],
                        organization_id=ORG_A, workspace_id=WS_A2,
                        identity_id=ALICE, created_by=ALICE)
        return a1, a2, names

    @staticmethod
    def _tagged(rows, prefix, key="name"):
        return sorted(r[key] for r in rows if str(r.get(key, "")).startswith(prefix))

    # ---- authorized access ------------------------------------------------

    def test_search_authorized_and_workspace_scoped(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            _, _, names = self._seed(svc)
            prefix = names[0][:-2]
            hits = svc.search(prefix, organization_id=ORG_A,
                              identity_id=MALLORY)
            # mallory is authorized for WS_A1 only: A2 must NOT appear.
            assert self._tagged(hits, prefix) == [names[0]]

    def test_search_authorized_returns_exactly_the_authorized_set(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            _, _, names = self._seed(svc)
            prefix = names[0][:-2]
            hits = svc.search(prefix, organization_id=ORG_A,
                              identity_id=ALICE)
            assert self._tagged(hits, prefix) == sorted(names)

    def test_get_by_type_authorized_and_workspace_scoped(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            _, _, names = self._seed(svc)
            prefix = names[0][:-2]
            mallory_names = self._tagged(
                svc.get_by_type("r6b27doc", ORG_A, identity_id=MALLORY), prefix)
            alice_names = self._tagged(
                svc.get_by_type("r6b27doc", ORG_A, identity_id=ALICE), prefix)
            assert mallory_names == [names[0]]
            assert alice_names == sorted(names)

    def test_count_by_type_authorized_and_workspace_scoped(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            before_alice = svc.count_by_type(ORG_A, identity_id=ALICE)["r6b27doc"]
            before_mallory = svc.count_by_type(ORG_A, identity_id=MALLORY)["r6b27doc"]
            self._seed(svc)
            after_alice = svc.count_by_type(ORG_A, identity_id=ALICE)["r6b27doc"]
            after_mallory = svc.count_by_type(ORG_A, identity_id=MALLORY)["r6b27doc"]
            # alice gains both workspaces' objects; mallory only WS_A1's.
            assert after_alice - before_alice == 2
            assert after_mallory - before_mallory == 1

    def test_list_by_workspace_authorized(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            _, _, names = self._seed(svc)
            prefix = names[0][:-2]
            rows = svc.list_by_workspace(WS_A1, ORG_A, identity_id=ALICE)
            assert self._tagged(rows, prefix) == [names[0]]

    def test_list_by_creator_authorized(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            _, _, names = self._seed(svc)
            prefix = names[0][:-2]
            mine = svc.list_by_creator(ALICE, ORG_A, identity_id=MALLORY)
            assert self._tagged(mine, prefix) == [names[0]]

    def test_get_by_object_id_authorized(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            a1, _, names = self._seed(svc)
            got = svc.get_by_object_id(a1["object_id"], ORG_A, identity_id=ALICE)
            assert got is not None
            assert got["name"] == names[0]
            assert got["workspace_id"] == WS_A1

    # ---- denials ----------------------------------------------------------

    @staticmethod
    def _surfaces(svc):
        """(label, callable) for every read surface, bound to ORG_A."""
        return [
            ("search", lambda **kw: svc.search(
                "Read Surface", organization_id=kw.pop("org", ORG_A), **kw)),
            ("get_by_type", lambda **kw: svc.get_by_type(
                "doc", kw.pop("org", ORG_A), **kw)),
            ("count_by_type", lambda **kw: svc.count_by_type(
                kw.pop("org", ORG_A), **kw)),
            ("list_by_workspace", lambda **kw: svc.list_by_workspace(
                kw.pop("ws", WS_A1), kw.pop("org", ORG_A), **kw)),
            ("list_by_creator", lambda **kw: svc.list_by_creator(
                ALICE, kw.pop("org", ORG_A), **kw)),
        ]

    def test_wrong_organization_denied_on_every_surface(self, app, tenancy):
        """alice is not a member of ORG_B → every surface fails closed."""
        with app.app_context():
            svc = _svc()
            self._seed(svc)
            for label, call in self._surfaces(svc):
                with pytest.raises(_ctx_err()) as exc:
                    call(org=ORG_B, identity_id=ALICE)
                assert exc.value.code == "no_authorized_workspace", label

    def test_wrong_identity_denied_on_every_surface(self, app, tenancy):
        """bob belongs to ORG_B, so he has no workspace in ORG_A."""
        with app.app_context():
            svc = _svc()
            self._seed(svc)
            for label, call in self._surfaces(svc):
                with pytest.raises(_ctx_err()) as exc:
                    call(identity_id=BOB)
                assert exc.value.code == "no_authorized_workspace", label

    def test_missing_membership_denied_on_every_surface(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            self._seed(svc)
            for label, call in self._surfaces(svc):
                with pytest.raises(_ctx_err()) as exc:
                    call(identity_id=NOBODY)
                assert exc.value.code == "no_authorized_workspace", label

    def test_inactive_membership_denied_on_every_surface(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            self._seed(svc)
            for label, call in self._surfaces(svc):
                with pytest.raises(_ctx_err()) as exc:
                    call(identity_id=INACTIVE)
                assert exc.value.code == "no_authorized_workspace", label

    def test_missing_identity_denied_on_every_surface(self, app, tenancy):
        with app.app_context():
            svc = _svc()
            self._seed(svc)
            for label, call in self._surfaces(svc):
                with pytest.raises(ValueError):
                    call()
            with pytest.raises(ValueError):
                svc.get_by_object_id("any", ORG_A)

    def test_wrong_workspace_denied_on_list_by_workspace(self, app, tenancy):
        """WS_A2 exists in ORG_A but mallory holds no membership in it."""
        with app.app_context():
            svc = _svc()
            self._seed(svc)
            with pytest.raises(_ctx_err()) as exc:
                svc.list_by_workspace(WS_A2, ORG_A, identity_id=MALLORY)
            assert exc.value.code == "workspace_not_authorized"

    def test_wrong_workspace_object_denied_on_get_by_object_id(self, app, tenancy):
        """An object in WS_A2 is invisible to a WS_A1-only identity."""
        with app.app_context():
            svc = _svc()
            _, a2, names = self._seed(svc)
            assert svc.get_by_object_id(a2["object_id"], ORG_A,
                                        identity_id=MALLORY) is None
            # and the owner can still read it — the denial is authorization,
            # not an absent object.
            assert svc.get_by_object_id(a2["object_id"], ORG_A,
                                        identity_id=ALICE)["name"] == names[1]


class TestBackgroundIdentityPropagation:
    """§28 — request identity → captured job context → worker → canonical
    authorization. Background execution is NOT system execution."""

    def test_route_captures_and_forwards_the_session_identity(self, app):
        import ast
        import app.upload.routes as up

        with open(up.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next(n for n in tree.body
                  if isinstance(n, ast.FunctionDef) and n.name == "api_upload")
        run_calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "run_async"]
        assert len(run_calls) == 1, "api_upload must enqueue exactly one background job"
        # The identity is captured from the session and handed to the job; the
        # job does not rediscover it and does not fall back to a synthetic one.
        # (Asserted on the AST, not on unparsed quotes.)
        def _session_get_arg(node, key):
            if not isinstance(node, ast.Call):
                return False
            f = node.func
            if not (isinstance(f, ast.Attribute) and f.attr == "get"):
                return False
            base = f.value
            base_name = (base.id if isinstance(base, ast.Name)
                         else getattr(base, "attr", None))
            if base_name != "session":
                return False
            return bool(node.args and isinstance(node.args[0], ast.Constant)
                        and node.args[0].value == key)

        assert any(_session_get_arg(n, "identity_id") for n in ast.walk(fn)), \
            "the route must capture the authenticated identity from the session"
        assert "identity_id" in ast.unparse(run_calls[0]), (
            "the background job must RECEIVE the captured identity: "
            f"{ast.unparse(run_calls[0])}"
        )
        # And the worker must never invent an identity or a system scope.
        worker = next(n for n in tree.body
                      if isinstance(n, ast.FunctionDef) and n.name == "_process_upload")
        worker_src = ast.unparse(worker)
        assert "system_scope" not in worker_src, \
            "background execution must not silently become system execution"

    def test_worker_creates_the_object_with_the_captured_identity(self, app, monkeypatch, tenancy):
        import app.upload.routes as up

        class _Storage:
            @staticmethod
            def save(file_bytes, filename, content_type):
                return {"url": f"mem://{filename}", "size": len(file_bytes)}

        class _Job:
            def __init__(self):
                self.stages = []

            def update(self, **kw):
                self.stages.append(kw)

        monkeypatch.setattr("app.create_app", lambda *a, **k: app)
        monkeypatch.setattr(up, "resolve_storage_provider", lambda: _Storage())

        up._process_upload(_Job(), b"r6b27-upload-bytes", "r6b27-note.txt",
                           "text/plain", ORG_A, WS_A1, ALICE)

        with app.app_context():
            rows = _svc().list_by_workspace(WS_A1, ORG_A, identity_id=ALICE)
            mine = [r for r in rows if r["name"] == "r6b27-note.txt"]
            assert len(mine) == 1, f"expected exactly one uploaded object, got {mine}"
            assert mine[0]["created_by"] == ALICE, \
                "created_by must be the captured identity, never a synthetic 'system'"
            assert mine[0]["organization_id"] == ORG_A
            assert mine[0]["workspace_id"] == WS_A1

    def test_worker_fails_closed_when_the_identity_was_not_captured(self, app, monkeypatch, tenancy):
        """A lost identity must NOT be repaired with a synthetic identity or by
        promoting background execution to system execution."""
        import app.upload.routes as up

        class _Storage:
            @staticmethod
            def save(file_bytes, filename, content_type):
                return {"url": f"mem://{filename}", "size": len(file_bytes)}

        class _Job:
            def update(self, **kw):
                pass

        monkeypatch.setattr("app.create_app", lambda *a, **k: app)
        monkeypatch.setattr(up, "resolve_storage_provider", lambda: _Storage())

        with pytest.raises(ValueError):
            up._process_upload(_Job(), b"r6b27-orphan-bytes", "r6b27-orphan.txt",
                               "text/plain", ORG_A, WS_A1, "")




