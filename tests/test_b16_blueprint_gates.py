"""B16 — Adversarial gate tests for the nine historically-unguarded blueprints.

Covers B17 (customer_experience), B18 (marketing_intelligence),
B19 (sales_intelligence), B20 (marketing_os), B21 (entity API),
B22 (UOP kernel), B23 (reality engine), B24 (export), and the B16
middleware contract itself (no /api/* exemption; header identity is
NOT a trust source for the authz decorators).

Three adversarial shapes per surface, plus a positive control:

* NEGATIVE unauthenticated  — no session, no header            → 401/403
* NEGATIVE spoofed header   — X-Identity-Id set, NO session    → 401/403
                              (proves decorators are session-only:
                               the B16 "spoofable header" claim)
* NEGATIVE cross-tenant     — org A session requests org B data → 403/404
* POSITIVE control          — org owner session                 → 200

The route-security inventory (test_route_security_inventory.py) enforces
that every route carries an explicit policy; this suite proves the
policies behave adversarially.
"""
import pytest


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "b16-adversarial",
    })
    with _app.app_context():
        db.create_all()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, identity_id: str, org_id: int):
    """Establish a canonical session (what the real signin route sets)."""
    with client.session_transaction() as sess:
        sess["identity_id"] = identity_id
        sess["user_id"] = identity_id
        sess["current_org_id"] = org_id
        sess["_fresh"] = True


def _seed_org(app, identity_id: str, org_label: str):
    """Create an org + owner member + active workspace. Returns org id."""
    from app import db
    from tests.auth_helper import seed_rbac, ensure_org_workspace
    with app.app_context():
        org_id = seed_rbac(db, identity_id=identity_id, role_name="owner")
        ensure_org_workspace(db, org_id, identity_id)
    return org_id


# ---------------------------------------------------------------------------
# The nine surfaces — (path, method) representatives
# ---------------------------------------------------------------------------
# Each is exercised against the same three adversarial shapes.
SURFACES = [
    # (name, method, path, positive_session_role)
    ("B17 customer_experience", "GET", "/api/v1/customer/profile/1"),
    ("B18 marketing_intelligence", "GET", "/api/v1/analytics/channels"),
    ("B19 sales_intelligence", "GET", "/api/v1/sales/pipeline"),
    ("B20 marketing_os", "GET", "/api/v1/marketing/campaigns"),
    ("B21 entity_api", "GET", "/api/v1/entities/"),
    ("B22 uop_kernel", "GET", "/api/v1/uop/objects"),
    ("B23 reality_engine", "GET", "/api/v1/reality"),
    ("B24 export", "POST", "/api/v1/export"),
]


class TestSpoofedHeaderDenied:
    """The B16 middleware claim: X-Identity-Id alone must NEVER authenticate."""

    @pytest.mark.parametrize("name,method,path", SURFACES)
    def test_no_session_no_header_denied(self, client, name, method, path):
        resp = client.open(path, method=method)
        assert resp.status_code in (401, 403), (
            f"{name} {method} {path} unauthenticated: got {resp.status_code}"
        )

    @pytest.mark.parametrize("name,method,path", SURFACES)
    def test_spoofed_header_only_denied(self, app, client, name, method, path):
        """X-Identity-Id without a session must be denied (session-only authz).

        If any of these returns 200, the caller authenticated purely by the
        client-supplied header — the B16 spoofing hole is open again.
        """
        from tests.auth_helper import seed_rbac
        from app import db
        with app.app_context():
            seed_rbac(db, identity_id="sid_spoofed_member", role_name="owner")
        headers = {"X-Identity-Id": "sid_spoofed_member"}
        resp = client.open(path, method=method, headers=headers)
        assert resp.status_code in (401, 403), (
            f"{name} {method} {path} header-only: got {resp.status_code} — "
            "header identity was trusted"
        )


class TestCrossTenantIsolation:
    """Org A member claiming org B must be denied on all nine surfaces."""

    @pytest.mark.parametrize("name,method,path", SURFACES)
    def test_foreign_org_selection_denied(self, app, client, name, method, path):
        # owner_a is a member of org_a; we LOG THEM IN WITH org_b selected
        # (the adversarial shape: a legitimate org A user claims org B).
        org_a = _seed_org(app, "owner_a@test.com", "org_a")
        org_b = _seed_org(app, "owner_b@test.com", "org_b")
        _login(client, "owner_a@test.com", org_b)
        resp = client.open(path, method=method)
        # The org-resolution layer must fail closed: 400 (no org context /
        # selection), 401, 403 (not authorized), or 404 (scoped lookup).
        # NEVER 200 with org B's data.
        assert resp.status_code in (400, 401, 403, 404), (
            f"{name} {method} {path} with foreign org selection: "
            f"got {resp.status_code} — org B access was not denied"
        )


class TestPositiveControl:
    """An org owner in a real session still reaches the surface (200/4xx-with-context)."""

    @pytest.mark.parametrize("name,method,path", SURFACES)
    def test_owner_session_reaches_surface(self, app, client, name, method, path):
        org_id = _seed_org(app, "owner_ok@test.com", "org_ok")
        _login(client, "owner_ok@test.com", org_id)
        resp = client.open(path, method=method)
        # 200 for list/read surfaces; export POST is allowed to 400/422 for an
        # empty/invalid body, but a 401/403 would mean the gate blocks owners.
        assert resp.status_code != 401, f"{name} owner denied: {resp.status_code}"
        assert resp.status_code != 403, f"{name} owner denied: {resp.status_code}"