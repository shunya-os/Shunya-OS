"""SHUNYA — Platform Routes (FDA26).

Developer/Integration Platform API:
- Webhook subscription CRUD + test + delivery log
- Developer diagnostics
- OpenAPI specification
- Integration health visibility
- Versioning summary

Every route uses canonical auth: session identity or X-Identity-Id header.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from app import db
from app.platform.models import WebhookDelivery, WebhookSubscription
from app.platform.webhook import deliver_webhook
from app.platform.versioning import version_summary

logger = logging.getLogger(__name__)

platform_bp = Blueprint("platform", __name__, url_prefix="/api/v1/platform")

AVAILABLE_EVENTS = [
    "new_invoice",
    "invoice_paid",
    "new_proposal",
    "proposal_accepted",
    "task_completed",
    "contact_added",
    "email_sent",
    "new_note",
    "test",
]

VALID_EVENT_NAMES = set(AVAILABLE_EVENTS)


def _require_identity() -> str | None:
    """Resolve the current identity: session first, then X-Identity-Id header."""
    from flask import session

    identity_id = session.get("identity_id") or session.get("user_id")
    if not identity_id:
        identity_id = request.headers.get("X-Identity-Id") or request.headers.get("X-User-Id")
    if not identity_id:
        return None
    return str(identity_id)


def _workspace_id() -> str:
    return request.headers.get("X-Workspace-Id") or request.args.get("workspace_id") or ""


def _ok(data, status=200):
    return jsonify({"success": True, "data": data}), status


def _err(message, status=400):
    return jsonify({"success": False, "error": message}), status


# ── Webhook subscription CRUD ──────────────────────────────────────────


@platform_bp.route("/webhooks", methods=["GET"])
def list_webhooks():
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)
    subscriptions = WebhookSubscription.query.filter_by(identity_id=identity_id).order_by(WebhookSubscription.id.desc()).all()
    return _ok({"webhooks": [s.to_dict() for s in subscriptions]})


@platform_bp.route("/webhooks", methods=["POST"])
def create_webhook():
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)

    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return _err("url is required")
    if not url.startswith(("http://", "https://")):
        return _err("url must be a valid http(s) URL")

    label = (data.get("label") or "").strip() or url
    events = data.get("events") or []
    if not isinstance(events, list) or not events:
        return _err("At least one event is required")
    invalid = [e for e in events if e not in VALID_EVENT_NAMES]
    if invalid:
        return _err(f"Unknown event(s): {', '.join(invalid)}")

    # Duplicate URL for same identity is prevented by unique constraint;
    # check explicitly for a friendly error.
    existing = WebhookSubscription.query.filter_by(identity_id=identity_id, url=url).first()
    if existing:
        return _err("A webhook with this URL already exists")

    sub = WebhookSubscription(
        identity_id=identity_id,
        workspace_id=_workspace_id() or None,
        label=label,
        url=url,
        secret=WebhookSubscription.generate_secret(),
        is_active=bool(data.get("is_active", True)),
    )
    sub.events = events
    db.session.add(sub)
    db.session.commit()

    # Audit: webhook created
    from app.security.audit import log_audit

    log_audit("create", "webhook_subscription", str(sub.id), {"url": url, "events": events})
    db.session.commit()

    return _ok(sub.to_dict(include_secret=True), 201)


@platform_bp.route("/webhooks/<int:webhook_id>", methods=["PUT"])
def update_webhook(webhook_id):
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)

    sub = WebhookSubscription.query.filter_by(id=webhook_id, identity_id=identity_id).first()
    if not sub:
        return _err("Webhook not found", 404)

    data = request.get_json(silent=True) or {}
    if "url" in data:
        url = (data.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return _err("url must be a valid http(s) URL")
        sub.url = url
    if "label" in data:
        sub.label = (data.get("label") or "").strip()
    if "events" in data:
        events = data.get("events") or []
        if not isinstance(events, list) or not events:
            return _err("At least one event is required")
        invalid = [e for e in events if e not in VALID_EVENT_NAMES]
        if invalid:
            return _err(f"Unknown event(s): {', '.join(invalid)}")
        sub.events = events
    if "is_active" in data:
        sub.is_active = bool(data.get("is_active"))

    db.session.commit()

    from app.security.audit import log_audit

    log_audit("update", "webhook_subscription", str(sub.id), {"changed": list(data.keys())})
    db.session.commit()

    return _ok(sub.to_dict())


@platform_bp.route("/webhooks/<int:webhook_id>", methods=["DELETE"])
def delete_webhook(webhook_id):
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)

    sub = WebhookSubscription.query.filter_by(id=webhook_id, identity_id=identity_id).first()
    if not sub:
        return _err("Webhook not found", 404)

    # Keep deliveries for audit, remove subscription
    sub_id = sub.id
    db.session.delete(sub)
    db.session.commit()

    from app.security.audit import log_audit

    log_audit("delete", "webhook_subscription", str(sub_id), {})
    db.session.commit()

    return _ok({"deleted": sub_id})


@platform_bp.route("/webhooks/<int:webhook_id>/rotate-secret", methods=["POST"])
def rotate_webhook_secret(webhook_id):
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)

    sub = WebhookSubscription.query.filter_by(id=webhook_id, identity_id=identity_id).first()
    if not sub:
        return _err("Webhook not found", 404)

    sub.secret = WebhookSubscription.generate_secret()
    db.session.commit()

    from app.security.audit import log_audit

    log_audit("rotate_secret", "webhook_subscription", str(sub.id), {})
    db.session.commit()

    return _ok(sub.to_dict(include_secret=True))


@platform_bp.route("/webhooks/<int:webhook_id>/test", methods=["POST"])
def test_webhook(webhook_id):
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)

    sub = WebhookSubscription.query.filter_by(id=webhook_id, identity_id=identity_id).first()
    if not sub:
        return _err("Webhook not found", 404)
    if not sub.is_active:
        return _err("Webhook is inactive", 400)

    delivery = deliver_webhook(
        sub,
        event_name="test",
        event_id=f"test-{uuid.uuid4().hex[:12]}",
        payload={"message": "This is a test webhook from SHUNYA OS"},
    )

    return _ok({"delivery": delivery.to_dict(), "signature_header": "X-SHUNYA-Signature"})


@platform_bp.route("/webhooks/<int:webhook_id>/deliveries", methods=["GET"])
def webhook_deliveries(webhook_id):
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)

    sub = WebhookSubscription.query.filter_by(id=webhook_id, identity_id=identity_id).first()
    if not sub:
        return _err("Webhook not found", 404)

    limit = min(int(request.args.get("limit", 50)), 200)
    deliveries = (
        WebhookDelivery.query.filter_by(subscription_id=sub.id)
        .order_by(WebhookDelivery.id.desc())
        .limit(limit)
        .all()
    )
    return _ok({"deliveries": [d.to_dict() for d in deliveries]})


# ── Events catalog ─────────────────────────────────────────────────────


@platform_bp.route("/events", methods=["GET"])
def list_events():
    return _ok({"events": AVAILABLE_EVENTS})


# ── OpenAPI specification ──────────────────────────────────────────────


@platform_bp.route("/openapi.json", methods=["GET"])
def openapi_spec():
    """Return a concise OpenAPI 3.0 spec for the platform surface."""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "SHUNYA OS API",
            "description": (
                "SHUNYA OS — One Operating System. "
                "The canonical API surface for developer integrations. "
                "Versioned: /api/v1 (stable), /api/v2 (next). "
                "All requests require session auth or X-Identity-Id header."
            ),
            "version": "1.0.0",
            "contact": {"name": "SHUNYA"},
        },
        "servers": [{"url": "/api/v1"}],
        "tags": [
            {"name": "platform", "description": "Developer & integration platform"},
            {"name": "webhooks", "description": "Webhook subscriptions and deliveries"},
            {"name": "events", "description": "Event catalog"},
            {"name": "diagnostics", "description": "Developer diagnostics"},
            {"name": "health", "description": "Integration health visibility"},
        ],
        "paths": {
            "/platform/webhooks": {
                "get": {
                    "tags": ["webhooks"],
                    "summary": "List webhook subscriptions for the current identity",
                    "responses": {"200": {"description": "Webhook list"}},
                },
                "post": {
                    "tags": ["webhooks"],
                    "summary": "Create a webhook subscription",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["url", "events"],
                                    "properties": {
                                        "url": {"type": "string", "format": "uri"},
                                        "label": {"type": "string"},
                                        "events": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Event names from /platform/events",
                                        },
                                        "is_active": {"type": "boolean", "default": True},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {"201": {"description": "Created; includes secret once"}},
                },
            },
            "/platform/webhooks/{webhook_id}": {
                "put": {
                    "tags": ["webhooks"],
                    "summary": "Update a webhook subscription",
                    "parameters": [{"name": "webhook_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "Updated"}},
                },
                "delete": {
                    "tags": ["webhooks"],
                    "summary": "Delete a webhook subscription (deliveries retained for audit)",
                    "parameters": [{"name": "webhook_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "Deleted"}},
                },
            },
            "/platform/webhooks/{webhook_id}/test": {
                "post": {
                    "tags": ["webhooks"],
                    "summary": "Send a test event to a webhook",
                    "parameters": [{"name": "webhook_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "Test delivery result"}},
                }
            },
            "/platform/webhooks/{webhook_id}/deliveries": {
                "get": {
                    "tags": ["webhooks"],
                    "summary": "Delivery log for a webhook (evidence)",
                    "parameters": [{"name": "webhook_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {"200": {"description": "Delivery log"}},
                }
            },
            "/platform/events": {
                "get": {
                    "tags": ["events"],
                    "summary": "List available webhook event names",
                    "responses": {"200": {"description": "Event catalog"}},
                }
            },
            "/platform/diagnostics": {
                "get": {
                    "tags": ["diagnostics"],
                    "summary": "Developer diagnostics: routes, health, integrations",
                    "responses": {"200": {"description": "Diagnostics payload"}},
                }
            },
            "/platform/health": {
                "get": {
                    "tags": ["health"],
                    "summary": "Integration health visibility",
                    "responses": {"200": {"description": "Health payload"}},
                }
            },
            "/platform/versioning": {
                "get": {
                    "tags": ["diagnostics"],
                    "summary": "API versioning and deprecation policy",
                    "responses": {"200": {"description": "Versioning summary"}},
                }
            },
        },
    }
    return jsonify(spec)


# ── Developer diagnostics ──────────────────────────────────────────────


@platform_bp.route("/diagnostics", methods=["GET"])
def diagnostics():
    """Developer diagnostics: route inventory, integration registry, health."""
    identity_id = _require_identity()
    if not identity_id:
        return _err("Authentication required", 401)

    # Route inventory
    routes = []
    for rule in current_app.url_map.iter_rules():
        if rule.rule.startswith("/api/"):
            routes.append(
                {
                    "path": rule.rule,
                    "methods": sorted(rule.methods - {"OPTIONS", "HEAD"}),
                    "endpoint": rule.endpoint,
                }
            )
    routes.sort(key=lambda r: r["path"])

    # Integration registry
    integrations = []
    try:
        from app.integration.registry import registry

        integrations = registry.list()
    except Exception as exc:
        integrations = [{"error": str(exc)}]

    return _ok(
        {
            "identity": identity_id,
            "environment": current_app.config.get("ENV", "unknown"),
            "api_version": version_summary(),
            "routes_total": len(routes),
            "routes": routes,
            "integrations": integrations,
        }
    )


# ── Integration health visibility ──────────────────────────────────────


@platform_bp.route("/health", methods=["GET"])
def integration_health():
    """Integration health visibility surface (operator-facing)."""
    health = {"database": "unknown", "integrations": [], "webhooks": {"total": 0, "failed_recent": 0}}

    # Database
    try:
        db.session.execute(db.text("SELECT 1"))
        health["database"] = "connected"
    except Exception as exc:
        health["database"] = f"error: {exc}"

    # Integration registry
    try:
        from app.integration.registry import registry

        for intg in registry.list():
            health["integrations"].append(
                {
                    "name": intg.get("name"),
                    "display_name": intg.get("display_name"),
                    "connected": intg.get("connected"),
                    "status": intg.get("status"),
                    "last_sync_at": intg.get("last_sync_at"),
                    "error": intg.get("error"),
                    "configured": intg.get("configured"),
                }
            )
    except Exception as exc:
        health["integrations"] = [{"error": str(exc)}]

    # Webhook stats
    try:
        health["webhooks"]["total"] = WebhookSubscription.query.count()
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        health["webhooks"]["failed_recent"] = WebhookDelivery.query.filter(
            WebhookDelivery.status.in_(["failed", "exhausted"]),
            WebhookDelivery.created_at >= cutoff,
        ).count()
    except Exception:
        pass

    return _ok(health)


# ── Versioning summary ─────────────────────────────────────────────────


@platform_bp.route("/versioning", methods=["GET"])
def get_versioning():
    return _ok(version_summary())


# ── Connector SDK conventions doc (markdown) ───────────────────────────


@platform_bp.route("/connector-sdk", methods=["GET"])
def connector_sdk_doc():
    """Return the connector SDK conventions as markdown (developer-facing)."""
    md = """# SHUNYA Connector SDK Conventions

Every connector must extend `ConnectorBase` (app/platform/connector.py) and follow
the canonical provider fabric:

    authentication → authorization → tenant context → execution → retry/idempotency → evidence/audit

## Rules

1. **No duplicate systems.** A connector must never create a second identity, tenant,
   event, execution, or audit system. Use the canonical stores.
2. **Authentication** — `authenticate()` verifies credentials via the credential store.
   Never hardcode secrets.
3. **Authorization** — `authorize()` checks the identity has permission before any action.
4. **Tenant context** — `with_tenant()` scopes every operation to the current tenant.
5. **Execution** — `execute(action, **params)` runs the operation.
6. **Idempotency** — pass an `idempotency_key` to `run()` to prevent duplicates.
7. **Evidence** — `record_evidence()` writes to the canonical audit store. Every
   external action is auditable.

## Example

```python
from app.platform.connector import ConnectorBase, connector_registry

class MyConnector(ConnectorBase):
    provider_name = "my_connector"
    display_name = "My Connector"
    description = "Connects to an external service"

    def authenticate(self) -> bool:
        # Use the credential store, never hardcode
        self._authenticated = True
        return True

    def execute(self, action: str, **params) -> dict:
        # Perform the external API call
        return {"success": True, "data": params}

connector_registry.register(MyConnector)
```

## Webhook Events

Available events: %s

Webhook deliveries are signed with HMAC-SHA256 in the `X-SHUNYA-Signature` header.
Verification example:

```python
import hmac, hashlib

def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```
""" % (", ".join(AVAILABLE_EVENTS))
    return _ok({"conventions": md})