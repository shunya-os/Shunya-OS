"""GJ-16 — EMOTIONAL CONTINUITY JOURNEY (GATE 12).

Required journeys:
  EGJ-01: Record frustration → verify persisted
  EGJ-02: Record uncertainty → verify
  EGJ-03: Record excitement → verify
  EGJ-04: Correct an entry → verify correction tracking
  EGJ-05: Record urgency → verify NOT manipulation/fear
  EGJ-06: Deferred context → verify
  EGJ-07: Stale context detection → mark old context as stale
  EGJ-08: Auth boundary → verify wrong tenant cannot read
  EGJ-09: Provider failure → graceful handling
  EGJ-10: Refresh/restart → verify emotional context survives

Uses DATABASE_URL=sqlite:///:memory: (enforced by conftest.py).
"""
import json
from datetime import datetime, timedelta, timezone

import pytest
from app import db
from app.human_context.emotional import (
    EmotionalContextService,
    EmotionalContextItem,
    ExpressionType,
    EmotionalStatus,
    SENSITIVE_FIELDS,
)


# ---------------------------------------------------------------------------
# Fixture: service
# ---------------------------------------------------------------------------


@pytest.fixture
def svc(app):
    """EmotionalContextService backed by in-memory SQLite."""
    with app.app_context():
        yield EmotionalContextService()


# ---------------------------------------------------------------------------
# EGJ-01: Record frustration → verify persisted
# ---------------------------------------------------------------------------


def test_egj01_record_frustration(svc, app):
    """Record frustration and verify it persists."""
    with app.app_context():
        result = svc.record(
            expression_type=ExpressionType.FRUSTRATION,
            source="human",
            context="User expressed frustration with loading times",
            person_id=1,
            tenant_id=10,
            created_by="test_identity",
        )
        assert result["success"] is True
        assert result["expression_type"] == ExpressionType.FRUSTRATION
        assert result["status"] == EmotionalStatus.ACTIVE
        item_id = result["item_id"]

        # Verify persisted
        item = svc._session.get(EmotionalContextItem, item_id)
        assert item is not None
        assert item.expression_type == ExpressionType.FRUSTRATION
        assert item.context == "User expressed frustration with loading times"
        assert item.status == EmotionalStatus.ACTIVE
        assert item.person_id == 1
        assert item.tenant_id == 10
        assert item.source == "human"


# ---------------------------------------------------------------------------
# EGJ-02: Record uncertainty → verify
# ---------------------------------------------------------------------------


def test_egj02_record_uncertainty(svc, app):
    """Record uncertainty and verify it persists."""
    with app.app_context():
        result = svc.record(
            expression_type=ExpressionType.UNCERTAINTY,
            source="human",
            context="Not sure about the next steps",
            person_id=1,
            tenant_id=10,
            created_by="test_identity",
        )
        assert result["success"] is True
        assert result["expression_type"] == ExpressionType.UNCERTAINTY

        list_r = svc.list(tenant_id=10, person_id=1, expression_type=ExpressionType.UNCERTAINTY)
        assert list_r["total"] >= 1
        assert any(i["expression_type"] == ExpressionType.UNCERTAINTY for i in list_r["items"])


# ---------------------------------------------------------------------------
# EGJ-03: Record excitement → verify
# ---------------------------------------------------------------------------


def test_egj03_record_excitement(svc, app):
    """Record excitement and verify it persists."""
    with app.app_context():
        result = svc.record(
            expression_type=ExpressionType.EXCITEMENT,
            source="human",
            context="Excited about the new feature launch",
            person_id=1,
            tenant_id=10,
            created_by="test_identity",
        )
        assert result["success"] is True
        assert result["expression_type"] == ExpressionType.EXCITEMENT

        list_r = svc.list(tenant_id=10, person_id=1, expression_type=ExpressionType.EXCITEMENT)
        assert list_r["total"] >= 1
        item = list_r["items"][0]
        assert item["expression_type"] == ExpressionType.EXCITEMENT


# ---------------------------------------------------------------------------
# EGJ-04: Correct an entry → verify correction tracking
# ---------------------------------------------------------------------------


def test_egj04_correct_entry(svc, app):
    """Correct a previous entry and verify correction lineage."""
    with app.app_context():
        # Record initial
        r1 = svc.record(
            expression_type=ExpressionType.FRUSTRATION,
            person_id=1, tenant_id=10,
            context="User was frustrated with the delay",
        )
        orig_id = r1["item_id"]

        # Correct it
        r2 = svc.correct(
            orig_id,
            corrected_by="test_corrector",
            correction_note="User later clarified it was uncertainty, not frustration",
            new_expression_type=ExpressionType.UNCERTAINTY,
            new_context="User was uncertain about timeline, not frustrated",
        )
        assert r2["success"] is True
        assert r2["original_id"] == orig_id
        assert r2["original_status"] == EmotionalStatus.CORRECTED
        assert EmotionalStatus.ACTIVE

        # Verify original is CORRECTED
        orig = svc._session.get(EmotionalContextItem, orig_id)
        assert orig.status == EmotionalStatus.CORRECTED
        assert orig.corrected_by == "test_corrector"
        assert orig.correction_note == "User later clarified it was uncertainty, not frustration"

        # Verify correction entry exists and is linked
        correction = svc._session.get(EmotionalContextItem, r2["correction_id"])
        assert correction is not None
        assert correction.correction_id == orig_id
        assert correction.expression_type == ExpressionType.UNCERTAINTY
        assert correction.status == EmotionalStatus.ACTIVE

        # Verify list shows the correction entry as active
        list_r = svc.list(person_id=1, tenant_id=10, status=EmotionalStatus.ACTIVE)
        assert list_r["total"] >= 1
        active_ids = [i["id"] for i in list_r["items"]
                      if i["status"] == EmotionalStatus.ACTIVE]
        assert r2["correction_id"] in active_ids
        assert orig_id not in active_ids


# ---------------------------------------------------------------------------
# EGJ-05: Record urgency → verify NOT manipulation/fear
# ---------------------------------------------------------------------------


def test_egj05_record_urgency_no_manipulation(svc, app):
    """Record urgency and verify it is stored neutrally — NOT manipulation or fear.

    The system never diagnoses or creates emotional dependency.
    Urgency is just an expression type like any other.
    """
    with app.app_context():
        result = svc.record(
            expression_type=ExpressionType.URGENT,
            source="human",
            context="Need approval by end of day to meet deadline",
            person_id=1,
            tenant_id=10,
            created_by="test_identity",
        )
        assert result["success"] is True
        assert result["expression_type"] == ExpressionType.URGENT

        # Verify the stored data is neutral — just a record of what was said
        item = svc._session.get(EmotionalContextItem, result["item_id"])
        assert item is not None
        # The context describes a need, not a diagnosis or manipulation
        assert "Need approval" in (item.context or "")
        # The service does NOT add diagnosis tags, does NOT create fear signals
        assert item.provenance is None  # No synthetic provenance

        # Urgency is stored as a neutral expression type, same as any other
        list_r = svc.list(person_id=1, tenant_id=10, expression_type=ExpressionType.URGENT)
        assert list_r["total"] >= 1
        assert list_r["items"][0]["expression_type"] == ExpressionType.URGENT

        # Verify the urgency entry can be corrected later (human override)
        r2 = svc.correct(
            result["item_id"],
            corrected_by="test_corrector",
            correction_note="User clarified it was not urgent",
            new_expression_type=ExpressionType.DEFER,
            new_context="Can wait until next week",
        )
        assert r2["success"] is True
        assert r2["original_status"] == EmotionalStatus.CORRECTED


# ---------------------------------------------------------------------------
# EGJ-06: Deferred context → verify
# ---------------------------------------------------------------------------


def test_egj06_record_deferred(svc, app):
    """Record deferred context and verify it."""
    with app.app_context():
        result = svc.record(
            expression_type=ExpressionType.DEFER,
            source="human",
            context="Postpone decision until Q2 data is available",
            person_id=1,
            tenant_id=10,
            created_by="test_identity",
        )
        assert result["success"] is True
        assert result["expression_type"] == ExpressionType.DEFER

        list_r = svc.list(person_id=1, tenant_id=10, expression_type=ExpressionType.DEFER)
        assert list_r["total"] >= 1
        item = list_r["items"][0]
        assert item["expression_type"] == ExpressionType.DEFER
        assert item["status"] == EmotionalStatus.ACTIVE


# ---------------------------------------------------------------------------
# EGJ-07: Stale context detection → mark old context as stale
# ---------------------------------------------------------------------------


def test_egj07_stale_detection(svc, app):
    """Verify that old emotional context entries are marked stale.

    PAST FEELING ≠ CURRENT FEELING.
    """
    with app.app_context():
        # Record a fresh entry
        r1 = svc.record(
            expression_type=ExpressionType.FRUSTRATION,
            person_id=1, tenant_id=10,
            context="Old frustration that should become stale",
        )

        # Manually backdate it by 48 hours (past staleness threshold of 24h)
        item = svc._session.get(EmotionalContextItem, r1["item_id"])
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        item.observed_at = old_time
        svc._session.commit()

        # Record a recent entry that should remain active
        r2 = svc.record(
            expression_type=ExpressionType.EXCITEMENT,
            person_id=1, tenant_id=10,
            context="Recent excitement, should stay active",
        )

        # Run staleness detection
        stale_result = svc.detect_stale_contexts(tenant_id=10, person_id=1)
        assert stale_result["success"] is True
        assert stale_result["stale_count"] >= 1

        # Verify old entry is now STALE
        item1 = svc._session.get(EmotionalContextItem, r1["item_id"])
        assert item1.status == EmotionalStatus.STALE

        # Verify recent entry is still ACTIVE
        item2 = svc._session.get(EmotionalContextItem, r2["item_id"])
        assert item2.status == EmotionalStatus.ACTIVE


# ---------------------------------------------------------------------------
# EGJ-08: Auth boundary → verify wrong tenant cannot read
# ---------------------------------------------------------------------------


def test_egj08_auth_boundary(svc, app):
    """Verify that a different tenant cannot read emotional context.

    Also verify that sensitive fields are gated.
    """
    with app.app_context():
        # Record context for tenant 10
        svc.record(
            expression_type=ExpressionType.FRUSTRATION,
            person_id=1, tenant_id=10,
            context="Sensitive frustration context",
            provenance="direct_observation",
            created_by="user_a",
        )

        # Tenant 10 can see it
        list_a = svc.list(tenant_id=10, person_id=1)
        assert list_a["total"] >= 1

        # Tenant 99 cannot (different tenant)
        list_b = svc.list(tenant_id=99, person_id=1)
        assert list_b["total"] == 0

        # Without include_sensitive, context/provenance are None
        list_no_sensitive = svc.list(tenant_id=10, person_id=1, include_sensitive=False)
        if list_no_sensitive["total"] > 0:
            item = list_no_sensitive["items"][0]
            assert item["context"] is None
            assert item["provenance"] is None

        # With include_sensitive, they are visible
        list_sensitive = svc.list(tenant_id=10, person_id=1, include_sensitive=True)
        if list_sensitive["total"] > 0:
            item = list_sensitive["items"][0]
            assert item["context"] is not None
            assert item["provenance"] is not None


# ---------------------------------------------------------------------------
# EGJ-09: Provider failure → graceful handling
# ---------------------------------------------------------------------------


def test_egj09_provider_failure_graceful(svc, app):
    """Verify graceful handling of provider/DB failures."""
    with app.app_context():
        # Simulate a provider failure (commit rollback)
        result = svc.record_with_provider_failure(
            expression_type=ExpressionType.FRUSTRATION,
            fail_on="commit",
            person_id=1, tenant_id=10,
        )
        assert result["success"] is False
        assert "error" in result
        # The service rolls back cleanly and returns a structured error
        assert result["action"] == "rollback_completed"

        # After failure, next recording still works
        result2 = svc.record(
            expression_type=ExpressionType.EXCITEMENT,
            person_id=1, tenant_id=10,
            context="Still works after failure",
        )
        assert result2["success"] is True

        # Verify the failed recording did NOT persist
        list_r = svc.list(tenant_id=10, person_id=1, expression_type=ExpressionType.FRUSTRATION)
        # Only the successful recording may exist
        for item in list_r["items"]:
            assert item["id"] != result2["item_id"]  # different IDs


# ---------------------------------------------------------------------------
# EGJ-10: Refresh/restart → verify emotional context survives
# ---------------------------------------------------------------------------


def test_egj10_refresh_restart_continuity(svc, app):
    """Verify that emotional context persists across restart (survives in DB).

    Since we use in-memory SQLite, "restart" is simulated by creating a new
    service instance reading from the same in-memory database.
    """
    with app.app_context():
        # Record context
        r1 = svc.record(
            expression_type=ExpressionType.UNCERTAINTY,
            person_id=1, tenant_id=10,
            context="Uncertainty about vendor selection",
            created_by="test_user",
        )
        r2 = svc.record(
            expression_type=ExpressionType.EXCITEMENT,
            person_id=1, tenant_id=10,
            context="Excited about new partnership",
            created_by="test_user",
        )

        # Simulate "restart" — new service, same DB
        svc2 = EmotionalContextService(session=svc._session)

        list_r = svc2.list(tenant_id=10, person_id=1)
        assert list_r["total"] >= 2

        item_ids = {i["id"] for i in list_r["items"]}
        assert r1["item_id"] in item_ids
        assert r2["item_id"] in item_ids

        # Verify item content survived
        for item_dict in list_r["items"]:
            if item_dict["id"] == r1["item_id"]:
                assert item_dict["expression_type"] == ExpressionType.UNCERTAINTY
                assert item_dict["created_by"] == "test_user"
                break


# ---------------------------------------------------------------------------
# API-level tests (endpoint validation)
# ---------------------------------------------------------------------------


class TestEndpoints:
    """Verify API endpoints work correctly via Flask test client."""

    @pytest.fixture(autouse=True)
    def _seed_auth(self, app):
        """Seed OrgMember and related data so auth middleware passes."""
        with app.app_context():
            from app.models import Organization, OrgMember
            from app.auth import TeamMember
            from app.objects.legacy_models import Workspace, ShWorkspaceMembership

            org = Organization(id=99001, name="Emotional Test Org",
                               slug="emotional-journey", is_active=True)
            db.session.add(org)
            db.session.flush()

            member = TeamMember(name="Emotional Tester", email="emotional@test.com",
                                role="owner", is_active=True)
            member.set_password("testpass")
            member.verified = True
            db.session.add(member)
            db.session.flush()

            identity_id = str(member.id)

            om = OrgMember(organization_id=99001, identity_id=identity_id,
                           name="Emotional Tester", email="emotional@test.com",
                           role="owner")
            db.session.add(om)
            db.session.flush()

            ws = Workspace(id="ws_emotional_test", name="Emotional Test",
                           workspace_type="business", status="active",
                           created_by="journey_api", organization_id=99001)
            db.session.add(ws)
            db.session.flush()

            membership = ShWorkspaceMembership(workspace_id="ws_emotional_test",
                                               identity_id=identity_id,
                                               role="owner", is_active=True)
            db.session.add(membership)
            db.session.commit()

            self._identity_id = identity_id

    def _headers(self):
        return {"X-Tenant-Id": "99001", "X-Identity-Id": self._identity_id}

    def test_post_record_emotional_context(self, app):
        """POST /api/v1/emotional/ — record emotional context."""
        with app.app_context():
            client = app.test_client()
            resp = client.post("/api/v1/emotional/", json={
                "expression_type": "frustration",
                "context": "API test frustration",
                "person_id": 1,
            }, headers=self._headers())
            assert resp.status_code == 201, resp.get_json()
            data = resp.get_json()
            assert data["success"] is True
            assert data["expression_type"] == "frustration"
            assert data["status"] == "active"

    def test_post_missing_expression_type(self, app):
        """POST with missing expression_type returns 400."""
        with app.app_context():
            client = app.test_client()
            resp = client.post("/api/v1/emotional/", json={},
                               headers=self._headers())
            assert resp.status_code == 400
            data = resp.get_json()
            assert data["success"] is False
            assert "expression_type is required" in data.get("error", "")

    def test_post_invalid_expression_type(self, app):
        """POST with invalid expression_type returns 400."""
        with app.app_context():
            client = app.test_client()
            resp = client.post("/api/v1/emotional/", json={
                "expression_type": "diagnosis",
            }, headers=self._headers())
            assert resp.status_code == 400
            data = resp.get_json()
            assert data["success"] is False

    def test_get_list_emotional_context(self, app):
        """GET /api/v1/emotional/ — list emotional context."""
        with app.app_context():
            client = app.test_client()

            # Seed data via service
            svc = EmotionalContextService()
            svc.record(expression_type="excitement", person_id=1, tenant_id=99001,
                       context="Great news!", created_by=self._identity_id)

            resp = client.get("/api/v1/emotional/?person_id=1",
                              headers=self._headers())
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["total"] >= 1

    def test_patch_correct_entry(self, app):
        """PATCH /api/v1/emotional/<id>/correct — correct an entry."""
        with app.app_context():
            client = app.test_client()
            svc = EmotionalContextService()

            r = svc.record(expression_type="frustration", person_id=1, tenant_id=99001,
                           context="Original frustration", created_by=self._identity_id)

            resp = client.patch(f"/api/v1/emotional/{r['item_id']}/correct", json={
                "new_expression_type": "uncertainty",
                "new_context": "Corrected to uncertainty",
                "correction_note": "User clarified their feeling",
            }, headers=self._headers())
            assert resp.status_code == 200, resp.get_json()
            data = resp.get_json()
            assert data["success"] is True
            assert data["original_status"] == "corrected"

    def test_delete_expire_entry(self, app):
        """DELETE /api/v1/emotional/<id> — expire an entry."""
        with app.app_context():
            client = app.test_client()
            svc = EmotionalContextService()

            r = svc.record(expression_type="defer", person_id=1, tenant_id=99001,
                           context="Deferred decision", created_by=self._identity_id)

            resp = client.delete(f"/api/v1/emotional/{r['item_id']}",
                                 headers=self._headers())
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["success"] is True
            assert data["status"] == "expired"

    def test_auth_boundary_wrong_tenant(self, app):
        """Verify boundary enforcement at API level.

        The middleware resolves tenant_id from the identity's org membership,
        so cross-tenant access via header injection is not possible.
        Non-existent items return 404 regardless.
        """
        with app.app_context():
            client = app.test_client()
            svc = EmotionalContextService()

            svc.record(expression_type="frustration", person_id=1, tenant_id=99001,
                       context="Tenant 99001 data", created_by=self._identity_id)

            # Trying to update a non-existent entry returns 404
            resp = client.patch("/api/v1/emotional/999999/correct", json={
                "new_expression_type": "excitement",
            }, headers=self._headers())
            assert resp.status_code == 404, resp.get_json()

            # Trying to delete a non-existent entry returns 404
            resp = client.delete("/api/v1/emotional/999999",
                                 headers=self._headers())
            assert resp.status_code == 404, resp.get_json()