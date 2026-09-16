"""R6B-2.7 Window 5 — Object lifecycle test matrix.

Tests every lifecycle action (archive/restore/trash/recover/permanent_delete)
at BOTH the service boundary (direct invocation) and real HTTP routes.

State transitions:
  ACTIVE    → archive → ARCHIVED,  trash → TRASHED
  ARCHIVED  → restore → ACTIVE,    trash → TRASHED
  TRASHED   → recover → ACTIVE
  any       → permanent_delete → (removed) only from TRASHED

Tenancy: uses same matrix fixture as the authorization matrix (orgs 701-703).
"""

import pytest

from core.object_service import ObjectService, get_object_service

ORG_A, ORG_B, ORG_C = 701, 702, 703
WS_A1 = "ws_matrix_a1"
WS_B1 = "ws_matrix_b1"
ALICE = "matrix-alice@example.com"
BOB = "matrix-bob@example.com"
MALLORY = "matrix-mallory@example.com"
NOBODY = "matrix-nobody@example.com"
INACTIVE = "matrix-inactive@example.com"


# ── Fixture: reuse the matrix tenancy ─────────────────────────

@pytest.fixture(scope="module")
def app():
    from app import create_app, db
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "DISABLE_RATE_LIMIT": True,
        "SECRET_KEY": "test-secret",
    })
    with _app.app_context():
        db.create_all()
        yield _app
        db.drop_all()


@pytest.fixture(scope="module")
def tenancy(app):
    """Provision the matrix tenancy (same fixture as authorization_matrix)."""
    from app import db
    with app.app_context():
        from tests.test_r6b27_authorization_matrix import (
            _org, _ws, _member, _ws_member,
            ORG_A, ORG_B, ORG_C,
            WS_A1, WS_B1,
        )
        for oid in (ORG_A, ORG_B, ORG_C):
            _org(db, oid)
        _ws(db, ORG_A, WS_A1)
        _ws(db, ORG_B, WS_B1)
        _member(db, ORG_A, ALICE)
        _ws_member(db, WS_A1, ALICE)
        _member(db, ORG_B, BOB)
        _ws_member(db, WS_B1, BOB)
        _member(db, ORG_A, MALLORY)
        _ws_member(db, WS_A1, MALLORY)
        _member(db, ORG_A, INACTIVE)
        _ws_member(db, WS_A1, INACTIVE, active=False)
        _member(db, ORG_A, NOBODY)  # no ws membership
        db.session.commit()
    return


# ── Helper ─────────────────────────────────────────────────────

def _create_active(org_id=ORG_A, identity=ALICE, ws_id=WS_A1) -> int:
    """Create a doc object via ObjectService and return its integer ID."""
    svc = get_object_service()
    obj = svc.create(
        object_type="lifecycle-test",
        name="Lifecycle Test",
        organization_id=org_id,
        data={"test": "lifecycle"},
        created_by=identity,
        workspace_id=ws_id,
        identity_id=identity,
    )
    return obj["id"]


# ═══════════════════════════════════════════════════════════════
# 1. AUTHORIZED LIFECYCLE — service boundary
# ═══════════════════════════════════════════════════════════════

class TestLifecycleAuthorized:
    """Every lifecycle action succeeds for an authorized caller."""

    def test_archive_active(self, app, tenancy):
        """ACTIVE → archive → ARCHIVED. Status changes, is_deleted stays false."""
        svc = get_object_service()
        obj_id = _create_active()
        ok = svc.archive(obj_id, ORG_A, identity_id=ALICE)
        assert ok is True
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["status"] == "archived"
        assert obj["is_deleted"] is False

    def test_restore_archived(self, app, tenancy):
        """ARCHIVED → restore → ACTIVE. Status resets, is_deleted stays false."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.archive(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.restore(obj_id, ORG_A, identity_id=ALICE)
        assert ok is True
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["status"] == "active"
        assert obj["is_deleted"] is False

    def test_trash_active(self, app, tenancy):
        """ACTIVE → trash → TRASHED. is_deleted becomes true."""
        svc = get_object_service()
        obj_id = _create_active()
        ok = svc.trash(obj_id, ORG_A, identity_id=ALICE)
        assert ok is True
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["is_deleted"] is True

    def test_trash_archived(self, app, tenancy):
        """ARCHIVED → trash → TRASHED. is_deleted becomes true."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.archive(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.trash(obj_id, ORG_A, identity_id=ALICE)
        assert ok is True
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["is_deleted"] is True

    def test_recover_trashed(self, app, tenancy):
        """TRASHED → recover → ACTIVE. is_deleted becomes false, status active."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.trash(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.recover(obj_id, ORG_A, identity_id=ALICE)
        assert ok is True
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["is_deleted"] is False
        assert obj["status"] == "active"

    def test_permanent_delete_from_trashed(self, app, tenancy):
        """TRASHED → permanent_delete → removed. Get returns None."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.trash(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.permanent_delete(obj_id, ORG_A, identity_id=ALICE)
        assert ok is True
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj is None


# ═══════════════════════════════════════════════════════════════
# 2. ILLEGAL TRANSITIONS — each must fail closed
# ═══════════════════════════════════════════════════════════════

class TestLifecycleIllegalTransitions:
    """Operations not permitted from the current state must return False."""

    def test_cannot_archive_archived(self, app, tenancy):
        """Already archived → archive → False (no-op)."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.archive(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.archive(obj_id, ORG_A, identity_id=ALICE)
        assert ok is False

    def test_cannot_restore_active(self, app, tenancy):
        """Already active → restore → False."""
        svc = get_object_service()
        obj_id = _create_active()
        ok = svc.restore(obj_id, ORG_A, identity_id=ALICE)
        assert ok is False

    def test_cannot_restore_trashed(self, app, tenancy):
        """TRASHED → restore → False (use recover instead)."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.trash(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.restore(obj_id, ORG_A, identity_id=ALICE)
        assert ok is False

    def test_cannot_trash_trashed(self, app, tenancy):
        """Already trashed → trash → False."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.trash(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.trash(obj_id, ORG_A, identity_id=ALICE)
        assert ok is False

    def test_cannot_recover_active(self, app, tenancy):
        """Not trashed → recover → False."""
        svc = get_object_service()
        obj_id = _create_active()
        ok = svc.recover(obj_id, ORG_A, identity_id=ALICE)
        assert ok is False

    def test_cannot_permanent_delete_active(self, app, tenancy):
        """ACTIVE → permanent_delete → False (only from TRASHED)."""
        svc = get_object_service()
        obj_id = _create_active()
        ok = svc.permanent_delete(obj_id, ORG_A, identity_id=ALICE)
        assert ok is False

    def test_cannot_permanent_delete_archived(self, app, tenancy):
        """ARCHIVED → permanent_delete → False (must trash first)."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.archive(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.permanent_delete(obj_id, ORG_A, identity_id=ALICE)
        assert ok is False


# ═══════════════════════════════════════════════════════════════
# 3. UNAUTHORIZED LIFECYCLE — every action must be denied
# ═══════════════════════════════════════════════════════════════

class TestLifecycleUnauthorized:
    """Wrong identity, wrong org, wrong workspace, inactive, missing."""

    def _create_victim(self) -> int:
        svc = get_object_service()
        obj = svc.create(
            object_type="lifecycle-test", name="Victim",
            organization_id=ORG_A, data={},
            created_by=ALICE, workspace_id=WS_A1, identity_id=ALICE,
        )
        return obj["id"]

    def test_wrong_identity_archive(self, app, tenancy):
        """Wrong identity → archive → False."""
        svc = get_object_service()
        obj_id = self._create_victim()
        ok = svc.archive(obj_id, ORG_A, identity_id=BOB)
        assert ok is False

    def test_wrong_organization_archive(self, app, tenancy):
        """Wrong org → archive → False."""
        svc = get_object_service()
        obj_id = self._create_victim()
        ok = svc.archive(obj_id, ORG_B, identity_id=ALICE)
        assert ok is False

    def test_inactive_membership_archive(self, app, tenancy):
        """Inactive membership → archive → False."""
        svc = get_object_service()
        obj_id = self._create_victim()
        ok = svc.archive(obj_id, ORG_A, identity_id=INACTIVE)
        assert ok is False

    def test_no_membership_archive(self, app, tenancy):
        """Org member but no workspace membership → archive → False."""
        svc = get_object_service()
        obj_id = self._create_victim()
        ok = svc.archive(obj_id, ORG_A, identity_id=NOBODY)
        assert ok is False

    def test_wrong_identity_restore(self, app, tenancy):
        svc = get_object_service()
        obj_id = self._create_victim()
        svc.archive(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.restore(obj_id, ORG_A, identity_id=BOB)
        assert ok is False

    def test_wrong_identity_trash(self, app, tenancy):
        svc = get_object_service()
        obj_id = self._create_victim()
        ok = svc.trash(obj_id, ORG_A, identity_id=BOB)
        assert ok is False

    def test_wrong_identity_recover(self, app, tenancy):
        svc = get_object_service()
        obj_id = self._create_victim()
        svc.trash(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.recover(obj_id, ORG_A, identity_id=BOB)
        assert ok is False

    def test_wrong_identity_permanent_delete(self, app, tenancy):
        svc = get_object_service()
        obj_id = self._create_victim()
        svc.trash(obj_id, ORG_A, identity_id=ALICE)
        ok = svc.permanent_delete(obj_id, ORG_A, identity_id=BOB)
        assert ok is False


# ═══════════════════════════════════════════════════════════════
# 4. TENANT ISOLATION — cross-tenant lifecycle denied
# ═══════════════════════════════════════════════════════════════

class TestLifecycleTenantIsolation:
    """Another tenant cannot see, modify, or delete objects across tenants."""

    def test_cross_tenant_archive_denied(self, app, tenancy):
        svc = get_object_service()
        # Bob owns object in ORG_B
        b_obj = svc.create(
            object_type="lifecycle-test", name="B's object",
            organization_id=ORG_B, data={},
            created_by=BOB, workspace_id=WS_B1, identity_id=BOB,
        )
        b_id = b_obj["id"]
        # Alice tries to archive Bob's object
        ok = svc.archive(b_id, ORG_B, identity_id=ALICE)
        assert ok is False

    def test_cross_tenant_trash_denied(self, app, tenancy):
        svc = get_object_service()
        b_obj = svc.create(
            object_type="lifecycle-test", name="B's object 2",
            organization_id=ORG_B, data={},
            created_by=BOB, workspace_id=WS_B1, identity_id=BOB,
        )
        b_id = b_obj["id"]
        ok = svc.trash(b_id, ORG_B, identity_id=ALICE)
        assert ok is False

    def test_cross_tenant_recover_denied(self, app, tenancy):
        svc = get_object_service()
        b_obj = svc.create(
            object_type="lifecycle-test", name="B's object 3",
            organization_id=ORG_B, data={},
            created_by=BOB, workspace_id=WS_B1, identity_id=BOB,
        )
        b_id = b_obj["id"]
        svc.trash(b_id, ORG_B, identity_id=BOB)
        ok = svc.recover(b_id, ORG_B, identity_id=ALICE)
        assert ok is False

    def test_cross_tenant_object_not_readable(self, app, tenancy):
        """Alice cannot even SEE Bob's object to know it exists."""
        svc = get_object_service()
        b_obj = svc.create(
            object_type="lifecycle-test", name="B's secret",
            organization_id=ORG_B, data={},
            created_by=BOB, workspace_id=WS_B1, identity_id=BOB,
        )
        b_id = b_obj["id"]
        obj = svc.get(b_id, ORG_B, identity_id=ALICE)
        assert obj is None


# ═══════════════════════════════════════════════════════════════
# 5. NO FAKE SUCCESS — unauthorized operations must not return success
# ═══════════════════════════════════════════════════════════════

class TestLifecycleNoFakeSuccess:
    """Every unauthorized call returns False. The object state does not change."""

    def test_unauthorized_does_not_mutate_state(self, app, tenancy):
        svc = get_object_service()
        obj_id = _create_active(ORG_A, ALICE, WS_A1)
        org_b_ws_b1_obj = svc.create(
            object_type="lifecycle-test", name="B witness",
            organization_id=ORG_B, data={},
            created_by=BOB, workspace_id=WS_B1, identity_id=BOB,
        )
        b_id = org_b_ws_b1_obj["id"]

        # Wrong-org archive should not affect Alice's object
        svc.archive(obj_id, ORG_B, identity_id=ALICE)
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj is not None
        assert obj["status"] == "active"

        # Wrong-identity archive should not affect Bob's object
        svc.archive(b_id, ORG_B, identity_id=ALICE)
        b_obj = svc.get(b_id, ORG_B, identity_id=BOB)
        assert b_obj is not None
        assert b_obj["status"] == "active"


# ═══════════════════════════════════════════════════════════════
# 6. FULL LIFECYCLE JOURNEY — one object goes through every state
# ═══════════════════════════════════════════════════════════════

class TestLifecycleJourney:
    """One object traverses the complete lifecycle."""

    def test_complete_state_machine(self, app, tenancy):
        svc = get_object_service()
        obj_id = _create_active()

        # ACTIVE
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["status"] == "active"
        assert obj["is_deleted"] is False

        # ACTIVE → ARCHIVED
        assert svc.archive(obj_id, ORG_A, identity_id=ALICE)
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["status"] == "archived"
        assert obj["is_deleted"] is False

        # ARCHIVED → ACTIVE
        assert svc.restore(obj_id, ORG_A, identity_id=ALICE)
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["status"] == "active"

        # ACTIVE → TRASHED
        assert svc.trash(obj_id, ORG_A, identity_id=ALICE)
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["is_deleted"] is True

        # TRASHED → ACTIVE
        assert svc.recover(obj_id, ORG_A, identity_id=ALICE)
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["is_deleted"] is False
        assert obj["status"] == "active"

        # ACTIVE → ARCHIVED → TRASHED
        assert svc.archive(obj_id, ORG_A, identity_id=ALICE)
        assert svc.trash(obj_id, ORG_A, identity_id=ALICE)
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj["is_deleted"] is True

        # TRASHED → ACTIVE → ARCHIVED
        assert svc.recover(obj_id, ORG_A, identity_id=ALICE)
        assert svc.archive(obj_id, ORG_A, identity_id=ALICE)

        # ARCHIVED → TRASHED → permanent_delete
        assert svc.trash(obj_id, ORG_A, identity_id=ALICE)
        assert svc.permanent_delete(obj_id, ORG_A, identity_id=ALICE)
        obj = svc.get(obj_id, ORG_A, identity_id=ALICE)
        assert obj is None

    def test_idempotent_deleted_get(self, app, tenancy):
        """Getting a permanently-deleted object returns None — consistent."""
        svc = get_object_service()
        obj_id = _create_active()
        svc.trash(obj_id, ORG_A, identity_id=ALICE)
        svc.permanent_delete(obj_id, ORG_A, identity_id=ALICE)
        assert svc.get(obj_id, ORG_A, identity_id=ALICE) is None
        assert svc.get(obj_id, ORG_A, identity_id=ALICE) is None


# ═══════════════════════════════════════════════════════════════
# 7. HTTP ROUTE — calls through the lifecycle endpoint
# ═══════════════════════════════════════════════════════════════

class TestLifecycleHttpRoutes:
    """Lifecycle actions through the real HTTP route."""

    @pytest.fixture
    def client(self, app, tenancy):
        with app.app_context():
            with app.test_client() as c:
                with c.session_transaction() as s:
                    s["identity_id"] = ALICE
                    s["current_org_id"] = ORG_A
                    s["current_workspace_id"] = WS_A1
                yield c

    def _create_via_http(self, client):
        resp = client.post("/api/v1/objects/", json={
            "object_type": "lifecycle-http", "name": "HTTP Lifecycle",
        }, headers={"X-Organization-Id": str(ORG_A),
                     "X-Workspace-Id": WS_A1})
        assert resp.status_code == 200
        return resp.get_json()["id"]

    def _lifecycle(self, client, obj_id, action):
        return client.post(f"/api/v1/objects/{obj_id}/lifecycle", json={
            "action": action,
        }, headers={"X-Organization-Id": str(ORG_A),
                     "X-Workspace-Id": WS_A1})

    def test_http_archive(self, client, app, tenancy):
        obj_id = self._create_via_http(client)
        resp = self._lifecycle(client, obj_id, "archive")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["state"]["status"] == "archived"

    def test_http_archive_then_restore(self, client, app, tenancy):
        obj_id = self._create_via_http(client)
        self._lifecycle(client, obj_id, "archive")
        resp = self._lifecycle(client, obj_id, "restore")
        assert resp.status_code == 200
        assert resp.get_json()["state"]["status"] == "active"

    def test_http_trash_then_recover(self, client, app, tenancy):
        obj_id = self._create_via_http(client)
        self._lifecycle(client, obj_id, "trash")
        resp = self._lifecycle(client, obj_id, "recover")
        assert resp.status_code == 200
        assert resp.get_json()["state"]["is_deleted"] is False
        assert resp.get_json()["state"]["status"] == "active"

    def test_http_permanent_delete(self, client, app, tenancy):
        obj_id = self._create_via_http(client)
        self._lifecycle(client, obj_id, "trash")
        resp = self._lifecycle(client, obj_id, "permanent_delete")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        # Getting the object should now be 404
        get_resp = client.get(f"/api/v1/objects/{obj_id}",
                              headers={"X-Organization-Id": str(ORG_A)})
        assert get_resp.status_code == 404

    def test_http_illegal_transition(self, client, app, tenancy):
        """Active → restore should be denied at the HTTP level (403)."""
        obj_id = self._create_via_http(client)
        resp = self._lifecycle(client, obj_id, "restore")
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["success"] is False

    def test_http_unknown_action(self, client, app, tenancy):
        obj_id = self._create_via_http(client)
        resp = client.post(f"/api/v1/objects/{obj_id}/lifecycle", json={
            "action": "nonexistent",
        }, headers={"X-Organization-Id": str(ORG_A)})
        assert resp.status_code == 400

    def test_http_unauthorized_wrong_org(self, app, tenancy):
        """Lifecycle action with wrong org returns 403."""
        with app.test_client() as c:
            with c.session_transaction() as s:
                s["identity_id"] = BOB
                s["current_org_id"] = ORG_B
            # Create an object as Alice first
            from app import db
            svc = get_object_service()
            obj = svc.create(
                object_type="lifecycle-test", name="Alice's",
                organization_id=ORG_A, data={},
                created_by=ALICE, workspace_id=WS_A1, identity_id=ALICE,
            )
            obj_id = obj["id"]
            db.session.commit()
            # Bob tries to archive it through ORG_A
            resp = c.post(f"/api/v1/objects/{obj_id}/lifecycle", json={
                "action": "archive",
            }, headers={"X-Organization-Id": str(ORG_A)})
            assert resp.status_code == 403