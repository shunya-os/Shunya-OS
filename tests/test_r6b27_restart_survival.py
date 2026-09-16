"""R6B-2.7 Window 6 — G5/G8 restart-survival + failure certification.

Authorizations must survive a PROCESS RESTART and must be re-evaluated from
persisted state — never cached in memory. This module is executed TWICE against
the SAME persisted database (the disposable PostgreSQL cluster on :5433), in two
separate interpreter processes:

    R6B27_PHASE=1  tests/test_r6b27_restart_survival.py   # provision + prove access
    R6B27_PHASE=2  tests/test_r6b27_restart_survival.py   # prove survival, then revocation

Phase 2 proves:
  * the row written by phase 1 is still readable by its owner (persistence);
  * authorization is recomputed from persisted membership, not memory;
  * removing the membership denies access AFTER the restart;
  * re-granting the membership restores access;
  * a second identity that never had membership stays denied throughout.

It must never be run against production. If no phase is set the module skips, so
a normal full-suite run is unaffected.
"""
import os

import pytest

PHASE = os.environ.get("R6B27_PHASE", "").strip()

ORG_RS = 721
WS_RS = "ws_r6b27_restart"
OWNER = "r6b27-restart-owner@example.com"
OTHER = "r6b27-restart-other@example.com"
OBJECT_NAME = "r6b27-restart-survival-object"


pytestmark = pytest.mark.skipif(
    PHASE not in ("1", "2"),
    reason="restart-survival certification is run explicitly in two phases",
)


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    with _app.app_context():
        db.create_all()
    return _app


def _provision(app):
    """Canonical tenancy in the exact ids this certification asserts about."""
    from app import db
    from app.models import Organization, OrgMember
    from app.objects.legacy_models import ShWorkspaceMembership, Workspace
    with app.app_context():
        if db.session.get(Organization, ORG_RS) is None:
            db.session.add(Organization(id=ORG_RS, name="R6B27 Restart Org",
                                        slug="r6b27-restart-org", is_active=True))
            db.session.flush()
        if db.session.get(Workspace, WS_RS) is None:
            db.session.add(Workspace(id=WS_RS, name="R6B27 Restart WS",
                                     workspace_type="business", status="active",
                                     created_by="r6b27_restart_fixture",
                                     organization_id=ORG_RS))
            db.session.flush()
        if OrgMember.query.filter_by(organization_id=ORG_RS,
                                     identity_id=OWNER).first() is None:
            db.session.add(OrgMember(organization_id=ORG_RS, identity_id=OWNER,
                                     role="owner", is_active=True))
        if ShWorkspaceMembership.query.filter_by(
                workspace_id=WS_RS, identity_id=OWNER).first() is None:
            db.session.add(ShWorkspaceMembership(
                workspace_id=WS_RS, identity_id=OWNER, role="owner",
                is_active=True))
        db.session.commit()


def _svc():
    from core.object_service import get_object_service
    return get_object_service()


def _set_membership(active: bool):
    from app import db
    from app.objects.legacy_models import ShWorkspaceMembership
    m = ShWorkspaceMembership.query.filter_by(
        workspace_id=WS_RS, identity_id=OWNER).first()
    assert m is not None, "the membership row must persist across the restart"
    m.is_active = active
    db.session.commit()


def _ctx_err():
    from app.authz.workspace_context import OwnershipContextError
    return OwnershipContextError


class TestPhase1ProvisionAndAccess:
    def test_phase1_provisions_and_proves_access(self, app):
        if PHASE != "1":
            pytest.skip("phase 1 only")
        _provision(app)
        with app.app_context():
            obj = _svc().create(object_type="Document", name=OBJECT_NAME,
                                organization_id=ORG_RS, workspace_id=WS_RS,
                                identity_id=OWNER, created_by=OWNER,
                                data={"name": OBJECT_NAME})
            assert obj["id"] > 0
            # Authorized access works in this process…
            got = _svc().get_by_object_id(obj["object_id"], ORG_RS,
                                          identity_id=OWNER)
            assert got is not None and got["name"] == OBJECT_NAME
            # …and an identity with no membership is already denied.
            with pytest.raises(_ctx_err()):
                _svc().get_by_type("Document", ORG_RS, identity_id=OTHER)


class TestPhase2SurvivalAndRevocation:
    def test_object_and_membership_survived_the_restart(self, app):
        if PHASE != "2":
            pytest.skip("phase 2 only")
        with app.app_context():
            rows = _svc().get_by_type("Document", ORG_RS, identity_id=OWNER)
            assert any(r["name"] == OBJECT_NAME for r in rows), \
                "the object written in phase 1 must persist into a new process"

    def test_removing_the_membership_denies_after_the_restart(self, app):
        if PHASE != "2":
            pytest.skip("phase 2 only")
        with app.app_context():
            _set_membership(False)
            with pytest.raises(_ctx_err()) as exc:
                _svc().get_by_type("Document", ORG_RS, identity_id=OWNER)
            assert exc.value.code == "no_authorized_workspace"

    def test_regranting_the_membership_restores_access(self, app):
        if PHASE != "2":
            pytest.skip("phase 2 only")
        with app.app_context():
            _set_membership(True)
            rows = _svc().get_by_type("Document", ORG_RS, identity_id=OWNER)
            assert any(r["name"] == OBJECT_NAME for r in rows)

    def test_identity_without_membership_is_still_denied(self, app):
        if PHASE != "2":
            pytest.skip("phase 2 only")
        with app.app_context():
            with pytest.raises(_ctx_err()) as exc:
                _svc().get_by_type("Document", ORG_RS, identity_id=OTHER)
            assert exc.value.code == "no_authorized_workspace"
