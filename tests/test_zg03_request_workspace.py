"""ZG-03 — request-workspace resolution tolerates foreign-namespace ids.

The F1 reproduction: media/content actions failed closed with "No canonical
workspace context" because the SPA forwards workspace ids minted by the
older ``user_workspaces`` namespace (``ws_869bef2639f8`` style), which
``resolve_current_workspace`` correctly rejects — but they should never have
been forwarded as an explicit request at all.

``resolve_request_workspace`` fixes exactly that while keeping strict
fail-closed semantics for real (canonical) selections.
"""
import pytest

from app.authz.workspace_context import (
    OwnershipContextError,
    resolve_request_workspace,
)

ORG = 911
ORG_OTHER = 912
WS = "ws_zg03_a"
WS2 = "ws_zg03_a2"
WS_OTHER = "ws_zg03_b"
IDENT = "sid_zg03_ws"


def _seed(app):
    from app import db
    from app.models import Organization, OrgMember
    from app.objects.legacy_models import ShWorkspaceMembership, Workspace

    db.session.add_all([
        Organization(id=ORG, name="ZG03 Org", slug="zg03-org", is_active=True),
        Organization(id=ORG_OTHER, name="ZG03 Other", slug="zg03-other",
                     is_active=True),
    ])
    db.session.flush()
    db.session.add(OrgMember(organization_id=ORG, identity_id=IDENT,
                             role="owner", is_active=True))
    db.session.add_all([
        Workspace(id=WS, name="ZG03 WS", workspace_type="business",
                  created_by="system", organization_id=ORG, status="active"),
        Workspace(id=WS_OTHER, name="ZG03 Other WS", workspace_type="business",
                  created_by="system", organization_id=ORG_OTHER,
                  status="active"),
        ShWorkspaceMembership(workspace_id=WS, identity_id=IDENT,
                              role="owner", is_active=True),
    ])
    db.session.commit()


def test_foreign_namespace_candidate_is_skipped(app):
    """A user_workspaces-style id must not break resolution (the F1 repro)."""
    with app.app_context():
        _seed(app)
        resolved = resolve_request_workspace(
            IDENT, ORG, ["ws_869bef2639f8", None, "ws_869bef2639f8"])
        assert resolved == WS


def test_canonical_candidate_wins_when_authorized(app):
    with app.app_context():
        _seed(app)
        assert resolve_request_workspace(IDENT, ORG, [WS]) == WS


def test_known_foreign_candidate_fails_closed(app):
    """An EXISTING workspace id that is not authorized must deny, not skip."""
    with app.app_context():
        _seed(app)
        with pytest.raises(OwnershipContextError):
            resolve_request_workspace(IDENT, ORG, [WS_OTHER])


def test_legacy_organization_selection_is_canonicalized(app):
    """The founder's session carries legacy tenant 89-style ids."""
    with app.app_context():
        _seed(app)
        from app import db
        from app.models import Organization

        org = db.session.get(Organization, ORG)
        org.legacy_tenant_id = 991
        db.session.commit()
        assert resolve_request_workspace(IDENT, 991, ["ws_foreign_1"]) == WS


def test_ambiguous_context_with_junk_candidate_fails_closed(app):
    """Two authorized workspaces + no canonical candidate -> selection required."""
    with app.app_context():
        _seed(app)
        from app import db
        from app.objects.legacy_models import ShWorkspaceMembership, Workspace

        db.session.add_all([
            Workspace(id=WS2, name="ZG03 WS 2", workspace_type="business",
                      created_by="system", organization_id=ORG, status="active"),
            ShWorkspaceMembership(workspace_id=WS2, identity_id=IDENT,
                                  role="member", is_active=True),
        ])
        db.session.commit()
        with pytest.raises(OwnershipContextError):
            resolve_request_workspace(IDENT, ORG, ["ws_869bef2639f8"])
        # An explicit REAL selection still resolves.
        assert resolve_request_workspace(IDENT, ORG, [WS2]) == WS2
