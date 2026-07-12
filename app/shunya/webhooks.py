"""Shunya OS — Webhook Engine.

Dispatches HTTP POST to registered webhooks when entity events fire.
Events: entity.created, entity.updated, entity.deleted, status.changed
"""
import json, hmac, hashlib, logging, requests
from typing import Optional

logger = logging.getLogger("shunya.webhooks")


def dispatch_event(tenant_id: int, event: str, entity_type: str, entity_id: int, payload: dict):
    """Fire webhooks for an event."""
    from app.extensions import db as _db
    from app.models import Webhook

    hooks = _db.session.query(Webhook).filter(
        Webhook.tenant_id == tenant_id,
        Webhook.is_active == True,
        Webhook.event == event,
    ).all()

    for hook in hooks:
        if hook.entity_type != "*" and hook.entity_type != entity_type:
            continue

        body = {
            "event": event,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": payload,
            "tenant_id": tenant_id,
            "webhook_id": hook.id,
        }
        _send(hook, body)


def _send(hook, body: dict):
    """Send a single webhook request."""
    from app.extensions import db as _db
    from datetime import datetime

    body_json = json.dumps(body, default=str)
    headers = {"Content-Type": "application/json", "User-Agent": "ShunyaOS-Webhook/1.0"}
    for k, v in (hook.headers or {}).items():
        headers[k] = v

    if hook.secret:
        sig = hmac.new(hook.secret.encode(), body_json.encode(), hashlib.sha256).hexdigest()
        headers["X-Shunya-Signature"] = sig

    try:
        resp = requests.post(hook.url, data=body_json, headers=headers, timeout=15)
        hook.last_status = resp.status_code
        hook.last_sent_at = datetime.utcnow()
        if resp.status_code >= 400:
            hook.failure_count = (hook.failure_count or 0) + 1
            logger.warning(f"Webhook {hook.id} → {hook.url}: HTTP {resp.status_code}")
        else:
            hook.failure_count = 0
            logger.info(f"Webhook {hook.id} → {hook.url}: HTTP {resp.status_code}")
    except Exception as e:
        hook.last_status = None
        hook.failure_count = (hook.failure_count or 0) + 1
        logger.error(f"Webhook {hook.id} → {hook.url}: {e}")

    _db.session.commit()


def fire_webhook(webhook, event: str, payload: dict, session, log_model):
    """Fire a single webhook directly (used for test pings).

    Args:
        webhook: Webhook model instance.
        event: Event name (e.g. "test.ping").
        payload: JSON payload dict.
        session: DB session for logging.
        log_model: WebhookLog model class.
    """
    import json, hmac, hashlib, logging
    from datetime import datetime

    logger = logging.getLogger("shunya.webhooks")
    body_json = json.dumps(payload, default=str)
    headers = {"Content-Type": "application/json", "User-Agent": "ShunyaOS-Webhook/1.0"}
    for k, v in (webhook.headers or {}).items():
        headers[k] = v
    if webhook.secret:
        sig = hmac.new(webhook.secret.encode(), body_json.encode(), hashlib.sha256).hexdigest()
        headers["X-Shunya-Signature"] = sig

    try:
        resp = requests.post(webhook.url, data=body_json, headers=headers, timeout=15)
        webhook.last_status = resp.status_code
        webhook.last_sent_at = datetime.utcnow()
        if resp.status_code >= 400:
            webhook.failure_count = (webhook.failure_count or 0) + 1
            logger.warning(f"Webhook {webhook.id} → {webhook.url}: HTTP {resp.status_code}")
        else:
            webhook.failure_count = 0
            logger.info(f"Webhook {webhook.id} → {webhook.url}: HTTP {resp.status_code}")

        log = log_model(
            webhook_id=webhook.id, tenant_id=webhook.tenant_id,
            event=event, payload=payload, status_code=resp.status_code,
        )
        session.add(log)
    except Exception as e:
        webhook.last_status = None
        webhook.failure_count = (webhook.failure_count or 0) + 1
        logger.error(f"Webhook {webhook.id} → {webhook.url}: {e}")
        log = log_model(
            webhook_id=webhook.id, tenant_id=webhook.tenant_id,
            event=event, payload=payload, status_code=None, error=str(e),
        )
        session.add(log)

    session.commit()


AVAILABLE_EVENTS = [
    {"id": "entity.created", "label": "Entity Created"},
    {"id": "entity.updated", "label": "Entity Updated"},
    {"id": "entity.deleted", "label": "Entity Deleted"},
    {"id": "status.changed", "label": "Status Changed"},
]