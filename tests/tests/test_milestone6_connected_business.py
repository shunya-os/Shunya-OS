"""Tests for Milestone 6 — Connected Business.

Covers:
- Notification creation, retrieval, read tracking, preferences
- Integration connection management
- API endpoints for all M6 features
- Regression tests for M1–M5
"""
from __future__ import annotations

from datetime import datetime


def _make_identity(app):
    from app.adapters.os_adapter import sign_in
    result = sign_in(email="m6@shunyaos.com", name="M6 Test")
    assert result["success"]
    return result["identity_id"]


# ===========================================================================
# 1. Notification Service
# ===========================================================================

class TestNotificationService:
    """Notification creation, retrieval, and management."""

    def test_create_notification(self, app):
        from app.integration.service import create_notification
        identity_id = _make_identity(app)
        notif = create_notification(
            identity_id=identity_id,
            notification_type="system",
            title="Test notification",
            body="This is a test",
        )
        assert notif.id is not None
        assert notif.title == "Test notification"
        assert not notif.is_read

    def test_create_notification_with_object(self, app):
        from app.integration.service import create_notification
        identity_id = _make_identity(app)
        notif = create_notification(
            identity_id=identity_id,
            notification_type="entity_updated",
            title="Object updated",
            object_id="obj_001",
            space_id="spc_001",
        )
        assert notif.object_id == "obj_001"
        assert notif.space_id == "spc_001"

    def test_get_notifications(self, app):
        from app.integration.service import create_notification, get_notifications
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="N1")
        create_notification(identity_id=identity_id, notification_type="test", title="N2")
        notifs = get_notifications(identity_id=identity_id)
        assert len(notifs) == 2

    def test_get_notifications_other_identity_excluded(self, app):
        from app.integration.service import create_notification, get_notifications
        id1 = _make_identity(app)
        _make_identity(app)  # id2 — different identity
        create_notification(identity_id=id1, notification_type="test", title="N1")
        notifs = get_notifications(identity_id=id1)
        assert len(notifs) == 1

    def test_unread_count(self, app):
        from app.integration.service import (
            create_notification,
            get_unread_count,
            mark_as_read,
        )
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="N1")
        create_notification(identity_id=identity_id, notification_type="test", title="N2")
        assert get_unread_count(identity_id=identity_id) == 2
        notifs = __import__("app.integration.models", fromlist=["Notification"]).Notification.query.all()
        if notifs:
            mark_as_read(notifs[0].id)
            assert get_unread_count(identity_id=identity_id) == 1

    def test_mark_all_as_read(self, app):
        from app.integration.service import (
            create_notification,
            get_notifications,
            mark_all_as_read,
        )
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="N1")
        create_notification(identity_id=identity_id, notification_type="test", title="N2")
        count = mark_all_as_read(identity_id=identity_id)
        assert count == 2
        notifs = get_notifications(identity_id=identity_id)
        assert all(n["is_read"] for n in notifs)

    def test_notification_to_dict(self, app):
        from app.integration.service import create_notification
        identity_id = _make_identity(app)
        notif = create_notification(
            identity_id=identity_id, notification_type="test",
            title="Dict test", object_id="obj_001",
        )
        d = notif.to_dict()
        assert d["title"] == "Dict test"
        assert d["object_id"] == "obj_001"
        assert d["is_read"] is False

    def test_notification_preferences_defaults(self, app):
        from app.integration.service import get_preferences
        identity_id = _make_identity(app)
        prefs = get_preferences(identity_id=identity_id)
        assert prefs["email_notifications"] is True
        assert prefs["in_app_notifications"] is True
        assert prefs["digest_frequency"] == "immediate"

    def test_update_notification_preferences(self, app):
        from app.integration.service import get_preferences, update_preferences
        identity_id = _make_identity(app)
        result = update_preferences(
            identity_id=identity_id,
            email_notifications=False,
            digest_frequency="daily",
        )
        assert result["email_notifications"] is False
        assert result["digest_frequency"] == "daily"
        # Verify persisted
        prefs = get_preferences(identity_id=identity_id)
        assert prefs["email_notifications"] is False
        assert prefs["digest_frequency"] == "daily"


# ===========================================================================
# 2. Integration Connections
# ===========================================================================

class TestIntegrationConnections:
    """Integration connection management."""

    def test_save_connection(self, app):
        from app.integration.service import get_connections, save_connection
        identity_id = _make_identity(app)
        result = save_connection(
            identity_id=identity_id,
            provider="gmail",
            access_token="tok_abc123",
            label="My Gmail",
        )
        assert result["provider"] == "gmail"
        assert result["label"] == "My Gmail"
        assert result["is_active"] is True

    def test_get_connections(self, app):
        from app.integration.service import get_connections, save_connection
        identity_id = _make_identity(app)
        save_connection(identity_id=identity_id, provider="gmail", access_token="tok1")
        save_connection(identity_id=identity_id, provider="google_calendar", access_token="tok2")
        conns = get_connections(identity_id=identity_id)
        assert len(conns) == 2
        providers = [c["provider"] for c in conns]
        assert "gmail" in providers
        assert "google_calendar" in providers

    def test_remove_connection(self, app):
        from app.integration.service import (
            get_connections,
            remove_connection,
            save_connection,
        )
        identity_id = _make_identity(app)
        save_connection(identity_id=identity_id, provider="gmail", access_token="tok1")
        result = remove_connection(identity_id=identity_id, provider="gmail")
        assert result is True
        conns = get_connections(identity_id=identity_id)
        # Should be inactive, not deleted
        assert len(conns) == 1
        assert conns[0]["is_active"] is False

    def test_update_existing_connection(self, app):
        from app.integration.service import get_connections, save_connection
        identity_id = _make_identity(app)
        save_connection(identity_id=identity_id, provider="gmail", access_token="tok1")
        save_connection(identity_id=identity_id, provider="gmail", access_token="tok2")
        conns = get_connections(identity_id=identity_id)
        assert len(conns) == 1  # updated, not duplicated

    def test_remove_nonexistent_connection(self, app):
        from app.integration.service import remove_connection
        identity_id = _make_identity(app)
        result = remove_connection(identity_id=identity_id, provider="nonexistent")
        assert result is False


# ===========================================================================
# 3. API Endpoints
# ===========================================================================

class TestIntegrationAPI:
    """M6 API endpoints."""

    def test_get_notifications_api(self, app):
        from app.integration.service import create_notification
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="API Test")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.get("/api/v1/integration/notifications")
            data = resp.get_json()
            assert data["success"]
            assert data["count"] >= 1

    def test_unread_count_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.get("/api/v1/integration/notifications/unread-count")
            data = resp.get_json()
            assert data["success"]
            assert "unread_count" in data["data"]

    def test_mark_read_api(self, app):
        from app.integration.service import create_notification
        identity_id = _make_identity(app)
        notif = create_notification(identity_id=identity_id, notification_type="test", title="Mark")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.post(f"/api/v1/integration/notifications/{notif.id}/read")
            assert resp.get_json()["success"] is True

    def test_mark_all_read_api(self, app):
        from app.integration.service import create_notification
        identity_id = _make_identity(app)
        create_notification(identity_id=identity_id, notification_type="test", title="A1")
        create_notification(identity_id=identity_id, notification_type="test", title="A2")
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.post("/api/v1/integration/notifications/read-all")
            data = resp.get_json()
            assert data["success"]
            assert data["data"]["marked_read"] >= 1

    def test_get_preferences_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.get("/api/v1/integration/notifications/preferences")
            data = resp.get_json()
            assert data["success"]

    def test_update_preferences_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.put("/api/v1/integration/notifications/preferences", json={
                "email_notifications": False,
                "digest_frequency": "weekly",
            })
            data = resp.get_json()
            assert data["success"]
            assert data["data"]["email_notifications"] is False

    def test_get_connections_api(self, app):
        identity_id = _make_identity(app)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["identity_id"] = identity_id
                sess["user_id"] = identity_id
            resp = client.get("/api/v1/integration/connections")
            data = resp.get_json()
            assert data["success"]

    def test_list_providers_api(self, app):
        with app.test_client() as client:
            resp = client.get("/api/v1/integration/providers")
            data = resp.get_json()
            assert data["success"]
            assert len(data["data"]) >= 4

    def test_api_requires_auth(self, app):
        with app.test_client() as client:
            resp = client.get("/api/v1/integration/notifications")
            assert resp.status_code == 401


# ===========================================================================
# 4. Regression — Milestones 1–5
# ===========================================================================

class TestMilestoneRegression:
    """All prior milestones still pass."""

    def test_m1_signin(self, app):
        from app.adapters.os_adapter import sign_in
        result = sign_in(email="m6-reg@test.com", name="M6 Reg")
        assert result["success"]

    def test_m2_executive_home(self, app):
        from app.adapters.os_adapter import get_executive_home
        identity_id = _make_identity(app)
        result = get_executive_home(identity_id=identity_id)
        assert result["success"]

    def test_m3_insights(self, app):
        from app.founder.insight_engine import build_insights
        identity_id = _make_identity(app)
        result = build_insights(identity_id=identity_id)
        assert "summary" in result

    def test_m4_workspace(self, app):
        from app.founder.workspace_intelligence import build_full_workspace
        from app.founder.models import FounderObject, FounderSpace
        from app import db
        identity_id = _make_identity(app)
        space = FounderSpace(space_id="m6_spc", name="M6 Space", identity_id=identity_id)
        db.session.add(space)
        db.session.flush()
        obj = FounderObject(object_id="m6_obj", space_id="m6_spc", name="M6 Object",
                            object_type="Document", created_by=identity_id)
        db.session.add(obj)
        db.session.commit()
        result = build_full_workspace("m6_obj")
        assert "summary" in result

    def test_m5_ai_copilot(self, app):
        from app.ai.copilot import copilot_health
        health = copilot_health()
        assert "provider" in health

    def test_m5_ai_responds(self, app):
        from app.ai.provider import LocalProvider
        provider = LocalProvider()
        result = provider.complete([{"role": "user", "content": "Hello"}])
        assert result["content"]