"""
G1.1-R4 — Negative/failure tests for organization context, authorization, and object operations.

Tests that operation rejection is deterministic — no fallback to org 1.
"""
import pytest
from datetime import datetime, timezone


@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "WTF_CSRF_ENABLED": False})
    with _app.app_context():
        db.create_all()
    return _app


@pytest.fixture
def client(app):
    return app.test_client()


def _ensure_team_member(app, email, name, identity_id, tenant_id=1):
    """Create a team_member row if not exists. Returns id."""
    from app import db
    from sqlalchemy import text
    now = datetime.now(timezone.utc)
    row = db.session.execute(
        text("SELECT id FROM team_members WHERE email = :e"), {"e": email}
    ).first()
    if not row:
        db.session.execute(
            text("""INSERT INTO team_members (name, email, identity_id, tenant_id, created_at)
                    VALUES (:name, :email, :identity_id, :tenant_id, :now)"""),
            {"name": name, "email": email, "identity_id": identity_id,
             "tenant_id": tenant_id, "now": now},
        )
        db.session.commit()
        row = db.session.execute(
            text("SELECT id FROM team_members WHERE email = :e"), {"e": email}
        ).first()
    return row[0]


class TestMissingOrgContext:
    """Every authenticated request MUST have organization context — no silent fallback to org 1."""

    def test_create_object_rejects_missing_org(self, app, client):
        """POST /api/v1/objects/customer without org context must reject."""
        with client.session_transaction() as sess:
            sess["identity_id"] = "no_org_user_r4_unique_test_only"
            # Deliberately NOT setting current_org_id — identity has NO OrgMember
            # so _resolve_org_id returns None → route rejects

        resp = client.post("/api/v1/objects/customer", json={
            "company_name": "Test Corp",
        })
        assert resp.status_code in (400, 403), f"Expected denial (400/403), got {resp.status_code}"
        data = resp.get_json()
        assert not data.get("success")
        if resp.status_code == 400:
            assert "organization" in str(data.get("error", "")).lower() or "org" in str(data.get("error", "")).lower()
        else:
            # 401, 403, etc. — any denial is acceptable
            assert resp.status_code in (400, 401, 403)

        # Verify no object was created despite the request
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            count = ShunyaObject.query.filter_by(created_by="no_org_user_r4_unique_test_only").count()
            assert count == 0, "Zero objects should exist — request was rejected"

    def test_update_object_rejects_missing_org(self, app, client):
        """PUT /api/v1/objects/customer/some-id without org context must reject."""
        with app.app_context():
            from app import db
            _ensure_team_member(app, "nou@test.com", "No Org Update", "no_org_update_r4b")

        with client.session_transaction() as sess:
            sess["identity_id"] = "no_org_update_r4b_unique_test"
            # Deliberately NOT setting current_org_id — identity has NO OrgMember

        resp = client.put("/api/v1/objects/customer/nonexistent", json={
            "name": "New Name",
        })
        assert resp.status_code in (400, 401, 403), f"Expected denial (400/401/403), got {resp.status_code}"
        if resp.status_code == 400:
            data = resp.get_json()
            assert "organization" in str(data.get("error", "")).lower()


class TestInvalidIdentity:
    """Unauthenticated requests must be rejected across all object endpoints."""

    def test_get_objects_rejects_unauthenticated(self, app, client):
        resp = client.get("/api/v1/objects/customer/some-id")
        assert resp.status_code == 401

    def test_create_objects_rejects_unauthenticated(self, app, client):
        resp = client.post("/api/v1/objects/customer", json={"company_name": "Test"})
        assert resp.status_code == 401

    def test_update_objects_rejects_unauthenticated(self, app, client):
        resp = client.put("/api/v1/objects/customer/some-id", json={"name": "Test"})
        assert resp.status_code == 401


class TestCrossOrganizationIsolation:
    """Organization A cannot operate on Organization B's objects."""

    ORG_A = 101
    ORG_B = 102

    @pytest.fixture(autouse=True)
    def setup_orgs_and_user(self, app, request):
        with app.app_context():
            from app import db
            from sqlalchemy import text
            from tests.auth_helper import seed_rbac
            now = datetime.now(timezone.utc)

            # Ensure both orgs exist with RBAC roles
            org_a_id = seed_rbac(db, identity_id="cross_org", role_name="member")
            self.ORG_A = org_a_id
            for oid in (org_a_id, self.ORG_B):
                db.session.execute(
                    text("""INSERT INTO organizations (id, name, slug, created_at, updated_at)
                            VALUES (:id, :name, :slug, :now, :now)
                            ON CONFLICT (id) DO NOTHING"""),
                    {"id": oid, "name": f"Org {oid}", "slug": f"org-{oid}", "now": now},
                )
            db.session.commit()

            # Create test identity + membership in ORG_A only
            _ensure_team_member(app, "cross_org@test.com", "Cross Org",
                                "cross_org", tenant_id=self.ORG_A)

    def test_cross_org_object_creation_isolation(self, app, client):
        """User in ORG_A creates an object; ORG_B cannot read it."""
        with client.session_transaction() as sess:
            sess["identity_id"] = "cross_org"
            sess["current_org_id"] = str(self.ORG_A)

        # Create an object in ORG_A
        resp = client.post("/api/v1/objects/customer", json={"company_name": "Cross Org Corp"})
        assert resp.status_code == 201
        obj_id = resp.get_json().get("data", {}).get("object_id", "")

        # Verify the object was created with ORG_A scope
        with app.app_context():
            from app.objects.legacy_models import ShunyaObject
            obj = ShunyaObject.query.filter_by(object_id=obj_id).first()
            assert obj is not None
            assert obj.organization_id == self.ORG_A

        # Read as ORG_B — the update path must reject (canonical paths enforce org)
        with client.session_transaction() as sess:
            sess["identity_id"] = "cross_org"
            sess["current_org_id"] = str(self.ORG_B)

        resp = client.put(f"/api/v1/objects/customer/{obj_id}", json={"name": "Hijacked"})
        assert resp.status_code == 404, "Object from ORG_A should not be found in ORG_B update"

    def test_create_canonical_rejects_missing_tenant(self, app):
        """create_canonical_object without tenant_id must return error."""
        with app.app_context():
            from app.objects.canonical import create_canonical_object
            result = create_canonical_object(
                object_id="no_tenant_test",
                object_type="Document",
                name="No Tenant",
                created_by="test",
            )
            assert "error" in result
            assert "tenant_id" in str(result.get("error", "")).lower()


class TestObjectNotFoundBehavior:
    """Non-existent objects return 404, not fallback to legacy store."""

    def _ensure_user(self, app, email, name, identity_id):
        with app.app_context():
            _ensure_team_member(app, email, name, identity_id)

    def test_get_nonexistent_returns_404(self, app, client):
        with app.app_context():
            from app import db
            from tests.auth_helper import seed_rbac
            org_id = seed_rbac(db, identity_id="notfound_user", role_name="member")
        self._ensure_user(app, "notfound@test.com", "Not Found", "notfound_user")

        with client.session_transaction() as sess:
            sess["identity_id"] = "notfound_user"
            sess["current_org_id"] = str(org_id)

        resp = client.get("/api/v1/objects/customer/nonexistent-obj-id")
        assert resp.status_code == 404

    def test_update_nonexistent_returns_404(self, app, client):
        # Use existing RBAC from self._ensure_user but test non-existent object returns 404
        self._ensure_user(app, "nf2_r6b@test.com", "NF R6B Fix", "nf2_user_r6b_fix")
        with client.session_transaction() as sess:
            # Use an org that already has data in the DB — don't create a new one
            sess["identity_id"] = "nf2_user_r6b_fix"
            sess["current_org_id"] = 1

        resp = client.put("/api/v1/objects/customer/nonexistent-obj-id", json={"name": "Nope"})
        assert resp.status_code == 404