"""SHUNYA — Webhook Delivery Service (FDA26).

Server-side webhook delivery engine with:
- HMAC-SHA256 signature verification
- Idempotency key (unique per (subscription, event_id))
- Retry with exponential backoff (3 attempts)
- Delivery log for evidence/audit
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests as http_requests

from app import db
from app.platform.models import WebhookDelivery, WebhookSubscription

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 900]  # seconds: 1min, 5min, 15min
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT = 10  # seconds


def _compute_signature(secret: str, payload: str) -> str:
    """Compute HMAC-SHA256 signature for webhook delivery."""
    mac = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def deliver_webhook(
    subscription: WebhookSubscription,
    event_name: str,
    event_id: str,
    payload: dict,
) -> WebhookDelivery:
    """Deliver a webhook event to a subscription.

    Uses idempotency key (subscription_id, event_id) to prevent duplicates.
    Records every attempt in WebhookDelivery for audit/evidence.
    Returns the delivery record.
    """
    # Idempotency check: skip if already delivered
    existing = WebhookDelivery.query.filter_by(
        subscription_id=subscription.id,
        event_id=event_id,
    ).first()
    if existing and existing.status == "delivered":
        logger.info("Webhook %s already delivered for event %s", subscription.id, event_id)
        return existing

    # Create or update delivery record
    if existing:
        delivery = existing
        delivery.attempt = min(delivery.attempt + 1, MAX_ATTEMPTS)
        delivery.payload_json = json.dumps(payload)
    else:
        delivery = WebhookDelivery(
            subscription_id=subscription.id,
            event_id=event_id,
            event_name=event_name,
            payload_json=json.dumps(payload),
            attempt=1,
            max_attempts=MAX_ATTEMPTS,
            status="pending",
        )
        db.session.add(delivery)

    # Build the request
    body = json.dumps(
        {
            "event": event_name,
            "event_id": event_id,
            "timestamp": _now().isoformat(),
            "data": payload,
            "idempotency_key": f"{subscription.id}:{event_id}",
        }
    )
    signature = _compute_signature(subscription.secret, body)

    headers = {
        "Content-Type": "application/json",
        "X-SHUNYA-Webhook-Id": event_id,
        "X-SHUNYA-Signature": signature,
        "X-SHUNYA-Event": event_name,
        "X-SHUNYA-Idempotency-Key": delivery.event_id,
        "User-Agent": "SHUNYA-Webhook/1.0",
    }

    try:
        resp = http_requests.post(
            subscription.url,
            data=body,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        delivery.http_status = resp.status_code
        delivery.response_body = resp.text[:2000]
        delivery.status = "delivered" if 200 <= resp.status_code < 300 else "failed"
        delivery.delivered_at = _now()
        delivery.error = ""
    except Exception as e:
        delivery.http_status = None
        delivery.response_body = ""
        delivery.status = "failed"
        delivery.error = str(e)[:1000]
        logger.warning("Webhook delivery failed for %s: %s", subscription.id, e)

    # Update subscription stats
    subscription.last_delivery_at = _now()
    subscription.last_delivery_status = delivery.status
    subscription.delivery_count = (subscription.delivery_count or 0) + 1

    # Schedule retry if needed
    if delivery.status == "failed" and delivery.attempt < MAX_ATTEMPTS:
        delay = RETRY_DELAYS[min(delivery.attempt - 1, len(RETRY_DELAYS) - 1)]
        delivery.next_retry_at = _now() + timedelta(seconds=delay)
        logger.info("Webhook %s delivery attempt %d, retry at %s", subscription.id, delivery.attempt, delivery.next_retry_at)
    elif delivery.status == "failed" and delivery.attempt >= MAX_ATTEMPTS:
        delivery.status = "exhausted"
        delivery.error = (delivery.error or "") + " | All retries exhausted"

    db.session.commit()
    return delivery


def deliver_to_all(event_name: str, event_id: str, payload: dict, identity_id: Optional[str] = None) -> list[WebhookDelivery]:
    """Deliver the same event to all active subscriptions that match the event.

    If identity_id is provided, only delivers to subscriptions owned by that identity.
    """
    query = WebhookSubscription.query.filter_by(is_active=True)
    if identity_id:
        query = query.filter_by(identity_id=identity_id)

    # Eagerly load event filtering in Python (events_json is a Text column)
    subscriptions = query.all()
    matched = [s for s in subscriptions if event_name in s.events]

    results = []
    for sub in matched:
        try:
            delivery = deliver_webhook(sub, event_name, event_id, payload)
            results.append(delivery)
        except Exception as e:
            logger.error("Webhook delivery to %s: %s", sub.id, e)

    if not results:
        logger.debug("No matching webhook subscriptions for event %s (identity=%s)", event_name, identity_id)

    return results


def run_retry_cycle() -> int:
    """Retry all pending webhook deliveries whose next_retry_at has passed.

    Returns the number of retries attempted.
    """
    now = _now()
    pending = WebhookDelivery.query.filter(
        WebhookDelivery.status == "failed",
        WebhookDelivery.next_retry_at <= now,
        WebhookDelivery.attempt < WebhookDelivery.max_attempts,
    ).all()

    count = 0
    for delivery in pending:
        sub = WebhookSubscription.query.get(delivery.subscription_id)
        if not sub or not sub.is_active:
            delivery.status = "exhausted"
            delivery.error = "Subscription inactive"
            continue

        try:
            # Re-deliver with existing payload
            payload = json.loads(delivery.payload_json or "{}")
            deliver_webhook(sub, delivery.event_name, delivery.event_id, payload)
            count += 1
        except Exception as e:
            logger.error("Retry failed for webhook delivery %s: %s", delivery.id, e)

    db.session.commit()
    return count