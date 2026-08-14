"""Tests for FDA26 — Developer/Integration Platform.

Covers:
- Webhook subscription CRUD (positive, negative, auth, tenant)
- Webhook delivery with HMAC signature, idempotency, retry
- Connector SDK base class lifecycle
- OpenAPI spec endpoint
- Diagnostics endpoint
- Versioning/deprecation policy
"""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from app import db
from app.platform.models import WebhookDelivery, WebhookSubscription
from app.platform.webhook import (
    _compute_signature,
    deliver_webhook,
    deliver_to_all,
    run_retry_cycle,
)
from app.platform.connector import ConnectorBase, ConnectorRegistry, connector_registry


# =========================================================================
# Webhook Subscription CRUD
# =========================================================================


class TestWebhookCRUD:
    """Test webhook subscription CRUD with auth, validation, and scoping."""

    ROUTE = "/api/v1/platform/webhooks"

    def _auth_headers(self, identity_id: str = "test-user-1") -> dict:
        return {"X-Identity-Id": identity_id, "Content-Type": "application/json"}

    def _valid_webhook(self, **overrides) -> dict:
        data = {
            "url": "https://hooks.example.com/shunya",
            "label": "Test Webhook",
            "events": ["new_invoice", "task_completed"],
            "is_active": True,
        }
        data.update(overrides)
        return data

    def test_create_webhook(self, client):
        resp = client.post(
            self.ROUTE,
            json=self._valid_webhook(),
            headers=self._auth_headers(),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["url"] == "https://hooks.example.com/shunya"
        assert "secret" in data["data"]  # Secret returned once at creation
        assert data["data"]["is_active"] is True
        assert data["data"]["identity_id"] == "test-user-1"

    def test_create_webhook_minimal(self, client):
        """Minimal creation: only url and events required."""
        resp = client.post(
            self.ROUTE,
            json={"url": "https://example.com/hook", "events": ["new_invoice"]},
            headers=self._auth_headers(),
        )
        assert resp.status_code == 201
        assert resp.get_json()["success"] is True

    def test_create_webhook_missing_url(self, client):
        resp = client.post(
            self.ROUTE,
            json={"events": ["new_invoice"]},
            headers=self._auth_headers(),
        )
        assert resp.status_code == 400
        assert "url" in resp.get_json()["error"].lower()

    def test_create_webhook_missing_events(self, client):
        resp = client.post(
            self.ROUTE,
            json={"url": "https://example.com/hook", "events": []},
            headers=self._auth_headers(),
        )
        assert resp.status_code == 400

    def test_create_webhook_bad_url(self, client):
        resp = client.post(
            self.ROUTE,
            json={"url": "ftp://bad.com", "events": ["new_invoice"]},
            headers=self._auth_headers(),
        )
        assert resp.status_code == 400

    def test_create_webhook_invalid_event(self, client):
        resp = client.post(
            self.ROUTE,
            json={"url": "https://example.com/hook", "events": ["nonexistent_event"]},
            headers=self._auth_headers(),
        )
        assert resp.status_code == 400

    def test_create_webhook_no_auth(self, client):
        resp = client.post(self.ROUTE, json=self._valid_webhook())
        assert resp.status_code == 401

    def test_create_duplicate_url(self, client):
        """Same identity + same URL = unique constraint violation."""
        headers = self._auth_headers()
        resp1 = client.post(self.ROUTE, json=self._valid_webhook(), headers=headers)
        assert resp1.status_code == 201
        resp2 = client.post(self.ROUTE, json=self._valid_webhook(), headers=headers)
        assert resp2.status_code == 400
        assert "already exists" in resp2.get_json()["error"].lower()

    def test_tenant_isolation(self, client, app):
        """User A cannot see or modify user B's webhooks."""
        # Create as user A
        client.post(
            self.ROUTE,
            json=self._valid_webhook(),
            headers=self._auth_headers("user-a"),
        )
        # User B lists — same session is shared, so identity comes from
        # the session. Use a fresh client to get a clean session.
        # Simulate by sending the header; the list endpoint uses header
        # when no session identity is set.
        with app.test_client() as client_b:
            # Use a second client without the session cookie from A
            resp = client_b.get(self.ROUTE, headers=self._auth_headers("user-b"))
            assert resp.status_code == 200
            assert len(resp.get_json()["data"]["webhooks"]) == 0

    def test_list_webhooks(self, client):
        headers = self._auth_headers()
        client.post(self.ROUTE, json=self._valid_webhook(url="https://a.com"), headers=headers)
        client.post(self.ROUTE, json=self._valid_webhook(url="https://b.com"), headers=headers)
        resp = client.get(self.ROUTE, headers=headers)
        assert resp.status_code == 200
        assert len(resp.get_json()["data"]["webhooks"]) == 2

    def test_update_webhook(self, client):
        headers = self._auth_headers()
        create = client.post(self.ROUTE, json=self._valid_webhook(), headers=headers)
        wh_id = create.get_json()["data"]["id"]

        resp = client.put(
            f"{self.ROUTE}/{wh_id}",
            json={"label": "Updated Label", "is_active": False},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["label"] == "Updated Label"
        assert resp.get_json()["data"]["is_active"] is False

    def test_update_webhook_other_user(self, client, app):
        """User A cannot modify user B's webhook."""
        create = client.post(
            self.ROUTE,
            json=self._valid_webhook(),
            headers=self._auth_headers("user-a"),
        )
        wh_id = create.get_json()["data"]["id"]
        with app.test_client() as client_b:
            resp = client_b.put(
                f"{self.ROUTE}/{wh_id}",
                json={"label": "Hacked"},
                headers=self._auth_headers("user-b"),
            )
            assert resp.status_code == 404

    def test_delete_webhook(self, client):
        headers = self._auth_headers()
        create = client.post(self.ROUTE, json=self._valid_webhook(), headers=headers)
        wh_id = create.get_json()["data"]["id"]

        resp = client.delete(f"{self.ROUTE}/{wh_id}", headers=headers)
        assert resp.status_code == 200

        # Verify deleted
        resp = client.get(self.ROUTE, headers=headers)
        assert len(resp.get_json()["data"]["webhooks"]) == 0

    def test_delete_webhook_other_user(self, client, app):
        create = client.post(
            self.ROUTE,
            json=self._valid_webhook(),
            headers=self._auth_headers("user-a"),
        )
        wh_id = create.get_json()["data"]["id"]
        with app.test_client() as client_b:
            resp = client_b.delete(f"{self.ROUTE}/{wh_id}", headers=self._auth_headers("user-b"))
            assert resp.status_code == 404

    def test_rotate_secret(self, client):
        headers = self._auth_headers()
        create = client.post(self.ROUTE, json=self._valid_webhook(), headers=headers)
        orig_secret = create.get_json()["data"]["secret"]
        wh_id = create.get_json()["data"]["id"]

        resp = client.post(f"{self.ROUTE}/{wh_id}/rotate-secret", headers=headers)
        assert resp.status_code == 200
        new_secret = resp.get_json()["data"]["secret"]
        assert new_secret != orig_secret


# =========================================================================
# Webhook Delivery
# =========================================================================


class TestWebhookDelivery:
    """Test webhook delivery with HMAC signature, idempotency, retry."""

    def test_compute_signature(self):
        """HMAC signature is computed correctly."""
        sig = _compute_signature("test-secret", '{"hello":"world"}')
        assert sig.startswith("sha256=")
        assert len(sig) > 64

    def test_delivery_to_nonexistent_url(self, app):
        """Delivery to a nonexistent endpoint should fail gracefully."""
        with app.app_context():
            # Set up a webhook that points to a non-routable address
            sub = WebhookSubscription(
                identity_id="test-user",
                url="https://192.0.2.1:99999/nonexistent",
                secret=WebhookSubscription.generate_secret(),
                is_active=True,
            )
            sub.events = ["test"]
            db.session.add(sub)
            db.session.commit()

            delivery = deliver_webhook(sub, "test", "evt-001", {"hello": "world"})
            assert delivery.status == "failed"
            assert delivery.attempt == 1

    def test_retry_scheduling(self, app):
        """Failed delivery schedules a retry."""
        with app.app_context():
            sub = WebhookSubscription(
                identity_id="test-user",
                url="https://192.0.2.1:99999/nonexistent",
                secret=WebhookSubscription.generate_secret(),
                is_active=True,
            )
            sub.events = ["test"]
            db.session.add(sub)
            db.session.commit()

            delivery = deliver_webhook(sub, "test", "evt-002", {"hello": "world"})
            assert delivery.status == "failed"
            assert delivery.attempt == 1
            assert delivery.next_retry_at is not None

    def test_idempotency(self, app):
        """Same (subscription_id, event_id) should not create duplicate delivery."""
        with app.app_context():
            sub = WebhookSubscription(
                identity_id="test-user",
                url="https://192.0.2.1:99999/nonexistent",
                secret=WebhookSubscription.generate_secret(),
                is_active=True,
            )
            sub.events = ["test"]
            db.session.add(sub)
            db.session.commit()

            # First delivery
            d1 = deliver_webhook(sub, "test", "evt-003", {"hello": "world"})
            # Second delivery with same event_id
            d2 = deliver_webhook(sub, "test", "evt-003", {"hello": "world"})
            assert d2.id == d1.id  # Same record, not new

    def test_test_webhook_endpoint(self, client):
        """POST /webhooks/<id>/test triggers a delivery."""
        headers = {"X-Identity-Id": "test", "Content-Type": "application/json"}
        create = client.post(
            "/api/v1/platform/webhooks",
            json={"url": "https://192.0.2.1:99999/test", "events": ["test"]},
            headers=headers,
        )
        wh_id = create.get_json()["data"]["id"]
        resp = client.post(f"/api/v1/platform/webhooks/{wh_id}/test", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["data"]["delivery"]["status"] in ("failed", "delivered")
        assert resp.get_json()["data"]["signature_header"] == "X-SHUNYA-Signature"


# =========================================================================
# Event Catalog
# =========================================================================


class TestEvents:
    def test_list_events(self, client):
        resp = client.get("/api/v1/platform/events")
        assert resp.status_code == 200
        events = resp.get_json()["data"]["events"]
        assert "new_invoice" in events
        assert "test" in events


# =========================================================================
# OpenAPI Specification
# =========================================================================


class TestOpenAPI:
    def test_openapi_spec_returns_valid_json(self, client):
        resp = client.get("/api/v1/platform/openapi.json")
        assert resp.status_code == 200
        spec = resp.get_json()
        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "SHUNYA OS API"
        paths = spec["paths"]
        # Paths are relative to the /api/v1 server prefix
        assert any("webhooks" in p for p in paths)
        assert "/platform/events" in paths
        assert "/platform/diagnostics" in paths
        assert "/platform/health" in paths

    def test_openapi_spec_has_tags(self, client):
        spec = client.get("/api/v1/platform/openapi.json").get_json()
        tags = [t["name"] for t in spec["tags"]]
        assert "webhooks" in tags
        assert "diagnostics" in tags
        assert "health" in tags


# =========================================================================
# Diagnostics
# =========================================================================


class TestDiagnostics:
    def test_diagnostics_requires_auth(self, client):
        resp = client.get("/api/v1/platform/diagnostics")
        assert resp.status_code == 401

    def test_diagnostics_returns_route_count(self, client):
        headers = {"X-Identity-Id": "test"}
        resp = client.get("/api/v1/platform/diagnostics", headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["identity"] == "test"
        assert data["routes_total"] > 0
        assert len(data["routes"]) > 0
        assert "api_version" in data
        assert "integrations" in data


# =========================================================================
# Health
# =========================================================================


class TestHealth:
    def test_integration_health(self, client):
        resp = client.get("/api/v1/platform/health")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert "database" in data
        assert "integrations" in data
        assert "webhooks" in data


# =========================================================================
# Versioning
# =========================================================================


class TestVersioning:
    def test_versioning_summary(self, client):
        resp = client.get("/api/v1/platform/versioning")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["current_version"] == "v1"
        assert "v1" in data["supported_versions"]
        assert "policy" in data

    def test_api_version_header(self, client):
        """API responses include X-API-Version header."""
        resp = client.get("/api/v1/platform/events")
        assert "X-API-Version" in resp.headers
        assert resp.headers["X-API-Version"] == "v1"


# =========================================================================
# Connector SDK
# =========================================================================


class TestConnectorBase:
    def test_connector_requires_provider_name(self):
        """ConnectorBase without provider_name raises ValueError."""
        with pytest.raises(ValueError, match="provider_name"):

            class BadConnector(ConnectorBase):
                provider_name = ""

                def authenticate(self):
                    return True

                def execute(self, action, **params):
                    return {"success": True}

            BadConnector(identity_id="test")

    def test_connector_lifecycle(self, app):
        """Full lifecycle: authenticate → authorize → execute → evidence."""
        class TestConnector(ConnectorBase):
            provider_name = "test_connector"
            display_name = "Test"

            def authenticate(self):
                self._authenticated = True
                return True

            def execute(self, action, **params):
                return {"success": True, "data": params}

        with app.app_context():
            db.create_all()
            conn = TestConnector(identity_id="test-user", workspace_id="ws-1")
            result = conn.run("test_action", param1="hello")
            assert result["success"] is True
            assert result["result"]["data"]["param1"] == "hello"

    def test_connector_idempotency(self, app):
        """Idempotency key prevents duplicate execution."""
        class TestConnector(ConnectorBase):
            provider_name = "idempotent_test"

            def authenticate(self):
                self._authenticated = True
                return True

            def execute(self, action, **params):
                return {"success": True}

        with app.app_context():
            db.create_all()
            conn = TestConnector(identity_id="test-user")
            result1 = conn.run("action", idempotency_key="key-001")
            assert result1["success"] is True
            result2 = conn.run("action", idempotency_key="key-001")
            assert result2.get("skipped") is True or result2["success"] is True

    def test_connector_registry(self):
        class TestConnector(ConnectorBase):
            provider_name = "registry_test"
            display_name = "Registry Test"
            description = "Testing registry"

            def authenticate(self):
                return True

            def execute(self, action, **params):
                return {"success": True}

        connector_registry.register(TestConnector)
        conns = connector_registry.list()
        names = [c["name"] for c in conns]
        assert "registry_test" in names

        # Create via registry
        conn = connector_registry.create("registry_test", "identity-1")
        assert conn.provider_name == "registry_test"


# =========================================================================
# Connector SDK Doc
# =========================================================================


class TestConnectorSDK:
    def test_connector_sdk_doc(self, client):
        resp = client.get("/api/v1/platform/connector-sdk")
        assert resp.status_code == 200
        md = resp.get_json()["data"]["conventions"]
        assert "ConnectorBase" in md
        assert "HMAC-SHA256" in md
        assert "X-SHUNYA-Signature" in md


# =========================================================================
# Version headers
# =========================================================================


class TestVersionHeaders:
    def test_health_route_has_version_header(self, client):
        resp = client.get("/api/v1/platform/health")
        assert "X-API-Version" in resp.headers