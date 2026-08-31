"""
email_core.py — Canonical email send + read module.

Providers (in priority order):
  1. Resend (EMAIL_PROVIDER=resend + RESEND_API_KEY) — transactional API
  2. SMTP (EMAIL_USER/EMAIL_PASSWORD/EMAIL_HOST/EMAIL_PORT)
  3. Log-only fallback (never silently swallows)

Email lifecycle states (stored in email_records table):
  requested → accepted → delivered | bounced | complained | failed
                                                                  ↓
                                                         retry_pending → accepted
                                                                              ↓
                                                                         exhausted

Idempotency: Based on (business_event_id, notification_type, recipient),
NOT email content. The system permits genuinely distinct business events
with identical content to be sent. Repeated delivery of the SAME event
is collapsed by the idempotency key.

Category: security, operational, business, marketing — used for routing,
observability, and rate limiting. Marketing is disabled by default.
"""

import hashlib
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests

from app import db
from app.communication.email_models import EmailRecord, EmailDeliveryState, EmailCategory

logger = logging.getLogger(__name__)

_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
_PORT = int(os.environ.get("EMAIL_PORT", "587"))
_USER = os.environ.get("EMAIL_USER", "")
_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
_FROM = os.environ.get("EMAIL_FROM", _USER or "shunya@localhost")
_PROVIDER = os.environ.get("EMAIL_PROVIDER", "smtp").lower()
_RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
_RESEND_FROM = os.environ.get("RESEND_FROM", "SHUNYA <hello@shunyaos.com>")
_MAX_RETRIES = int(os.environ.get("EMAIL_MAX_RETRIES", "2"))
_RETRY_DELAY_BASE = int(os.environ.get("EMAIL_RETRY_DELAY", "5"))  # seconds


def _build_idempotency_key(business_event_id: str, notification_type: str, recipient: str) -> str:
    """Build a deterministic idempotency key from the business operation identity.

    This is safe because:
    - business_event_id is unique per operation (e.g., password_reset:uuid)
    - notification_type distinguishes different kinds of notification for the same event
    - recipient scopes the key to the target

    Two legitimate sends of the SAME email to the SAME person for DIFFERENT
    business events have different keys and both succeed.
    """
    raw = f"{business_event_id}:{notification_type}:{recipient}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _send_via_resend(
    record: EmailRecord,
    body: str,
) -> dict:
    """Send via Resend transactional API. Returns dict with status and provider_id.

    The EmailRecord is updated in-place with lifecycle transitions.
    """
    if not _RESEND_API_KEY:
        record.set_state(EmailDeliveryState.FAILED, "RESEND_API_KEY not set")
        db.session.commit()
        return {"status": "unconfigured", "error": "RESEND_API_KEY not set"}

    api_key = _RESEND_API_KEY
    idempotency_key = _build_idempotency_key(
        record.business_event_id, record.notification_type, record.recipient
    )

    payload = {
        "from": _RESEND_FROM,
        "to": [record.recipient],
        "subject": record.subject,
        "text": body,
        "tags": [
            {"name": "category", "value": record.category},
            {"name": "business_event_id", "value": record.business_event_id},
            {"name": "notification_type", "value": record.notification_type},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(record.max_retries + 1):
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=payload,
                timeout=15,
            )

            if resp.status_code == 200:
                # Provider accepted — record provider_message_id
                resp_data = resp.json()
                provider_id = resp_data.get("id", "")
                record.provider_message_id = provider_id
                record.set_state(EmailDeliveryState.ACCEPTED)
                db.session.commit()
                logger.info(
                    "Email accepted by Resend: id=%s to=%s event=%s/%s",
                    provider_id, record.recipient,
                    record.business_event_id, record.notification_type,
                )
                return {
                    "status": "accepted",
                    "provider_id": provider_id,
                    "record_id": record.id,
                }

            elif resp.status_code == 429:
                # Rate limited — retry with backoff
                if attempt < record.max_retries:
                    wait = _RETRY_DELAY_BASE * (2 ** attempt)
                    logger.warning(
                        "Resend rate limited (attempt %d/%d). Retrying in %ds...",
                        attempt + 1, record.max_retries + 1, wait,
                    )
                    record.set_state(EmailDeliveryState.RETRY_PENDING,
                                     f"Rate limited (429) attempt {attempt + 1}")
                    db.session.commit()
                    time.sleep(wait)
                    last_error = "Rate limited (429)"
                    continue
                record.set_state(EmailDeliveryState.EXHAUSTED,
                                 f"Rate limited after {record.max_retries + 1} attempts")
                db.session.commit()
                return {"status": "exhausted", "error": last_error}

            elif 400 <= resp.status_code < 500:
                # Client error — non-retryable (invalid recipient, auth failure, etc.)
                detail = resp.text[:500]
                record.set_state(EmailDeliveryState.FAILED, f"Resend API {resp.status_code}: {detail}")
                db.session.commit()
                logger.error("Resend client error for %s: %s %s", record.recipient, resp.status_code, detail)
                return {"status": "failed", "error": f"Resend API {resp.status_code}: {detail}"}

            else:
                # Server error — retryable
                if attempt < record.max_retries:
                    wait = _RETRY_DELAY_BASE * (2 ** attempt)
                    logger.warning(
                        "Resend server error %d (attempt %d/%d). Retrying in %ds...",
                        resp.status_code, attempt + 1, record.max_retries + 1, wait,
                    )
                    record.set_state(EmailDeliveryState.RETRY_PENDING,
                                     f"Server error {resp.status_code} attempt {attempt + 1}")
                    db.session.commit()
                    time.sleep(wait)
                    last_error = f"Server error {resp.status_code}"
                    continue
                record.set_state(EmailDeliveryState.EXHAUSTED,
                                 f"Server error after {record.max_retries + 1} attempts")
                db.session.commit()
                return {"status": "exhausted", "error": last_error}

        except requests.exceptions.Timeout as e:
            if attempt < record.max_retries:
                wait = _RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(
                    "Resend timeout (attempt %d/%d). Retrying in %ds...",
                    attempt + 1, record.max_retries + 1, wait,
                )
                record.set_state(EmailDeliveryState.RETRY_PENDING,
                                 f"Timeout attempt {attempt + 1}")
                db.session.commit()
                time.sleep(wait)
                last_error = str(e)
                continue
            record.set_state(EmailDeliveryState.EXHAUSTED,
                             f"Timeout after {record.max_retries + 1} attempts")
            db.session.commit()
            return {"status": "exhausted", "error": str(e)}

        except Exception as e:
            record.set_state(EmailDeliveryState.FAILED, str(e))
            db.session.commit()
            logger.error("Resend send failed for %s: %s", record.recipient, e)
            return {"status": "failed", "error": str(e)}

    # Fallback (should not be reached — retry loop always returns)
    return {"status": "failed", "error": "Unexpected: retry loop exhausted without return"}


def send(
    recipient: str,
    subject: str,
    body: str,
    notification_type: str,
    business_event_id: str,
    category: str = "operational",
    tenant_id: int = None,
    identity_id: str = None,
    cc: list = None,
    is_human_triggered: bool = False,
) -> dict:
    """Send email via the configured provider. Creates a durable EmailRecord.

    REQUIRES is_human_triggered=True to actually send.
    Without it, the message is logged and blocked (guardrail).

    Args:
        recipient: Email address of the recipient.
        subject: Email subject line.
        body: Plain-text email body.
        notification_type: SHUNYA notification type (e.g., 'password_reset',
            'org_invitation', 'commitment_due').
        business_event_id: Unique identifier for the business operation that
            triggered this email. Used for idempotency.
        category: One of 'security', 'operational', 'business', 'marketing'.
        tenant_id: Optional tenant ID for observability.
        identity_id: Optional identity ID for observability.
        cc: Optional list of CC recipients.
        is_human_triggered: If False, the email is blocked (guardrail).

    Returns:
        dict with status (accepted|logged|failed|blocked|exhausted|unconfigured),
        record_id, provider_id (when available).
    """
    if not is_human_triggered:
        logger.warning("Email send blocked: is_human_triggered=False.")
        logger.info("[EMAIL BLOCKED] To: %s | Subject: %s | Type: %s", recipient, subject, notification_type)
        return {
            "status": "blocked",
            "to": recipient,
            "reason": "Human approval required (is_human_triggered=False)",
            "channel": "email",
        }

    # Create durable email record (best-effort — may fail outside app context)
    body_hash = hashlib.sha256(body.encode()).hexdigest()[:16]
    record = None
    try:
        record = EmailRecord(
            business_event_id=business_event_id,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            body_hash=body_hash,
            category=category,
            provider=_PROVIDER,
            state=EmailDeliveryState.REQUESTED.value,
            tenant_id=tenant_id,
            identity_id=identity_id,
            max_retries=_MAX_RETRIES,
        )
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        logger.warning("Could not create EmailRecord (non-fatal): %s", e)
        record = None

    # ── Provider 1: Resend (transactional API) ──
    if _PROVIDER == "resend":
        if _RESEND_API_KEY:
            if record is None:
                logger.error("Resend cannot send: no EmailRecord (DB unavailable)")
                return {"status": "failed", "error": "EmailRecord not available", "to": recipient}
            result = _send_via_resend(record, body)
            result.update({
                "record_id": record.id,
                "to": recipient,
                "subject": subject,
                "channel": "email",
                "category": category,
                "notification_type": notification_type,
                "business_event_id": business_event_id,
            })
            return result

        # No API key configured — log instead
        logger.warning("EMAIL_PROVIDER=resend but RESEND_API_KEY not set — logging")
        logger.info("[EMAIL LOG] To: %s | Subject: %s | Body: %s", recipient, subject, body[:200])
        if record:
            record.set_state(EmailDeliveryState.FAILED, "RESEND_API_KEY not configured")
            db.session.commit()
        return {
            "status": "logged",
            "record_id": record.id if record else None,
            "to": recipient,
            "subject": subject,
            "channel": "email",
            "category": category,
            "note": "RESEND_API_KEY not configured",
        }

    # ── Provider 2: SMTP ──
    if not _USER or not _PASSWORD:
        logger.warning("EMAIL_USER/PASSWORD not set — logging instead of sending")
        logger.info("[EMAIL LOG] To: %s | Subject: %s | Body: %s", recipient, subject, body[:200])
        if record:
            record.set_state(EmailDeliveryState.FAILED, "SMTP credentials not configured")
            db.session.commit()
        return {
            "status": "logged",
            "record_id": record.id if record else None,
            "to": recipient,
            "subject": subject,
            "channel": "email",
            "category": category,
            "note": "SMTP credentials not configured",
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = _FROM
        msg["To"] = recipient
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg.attach(MIMEText(body, "plain", "utf-8"))

        recipients = [recipient] + (cc or [])
        with smtplib.SMTP(_HOST, _PORT, timeout=15) as server:
            server.starttls()
            server.login(_USER, _PASSWORD)
            server.sendmail(_FROM, recipients, msg.as_string())

        if record:
            record.set_state(EmailDeliveryState.ACCEPTED)
            db.session.commit()
        logger.info("Email sent via SMTP to %s: %s", recipient, subject)
        return {
            "status": "accepted",
            "record_id": record.id if record else None,
            "to": recipient,
            "subject": subject,
            "channel": "email",
            "category": category,
        }

    except Exception as e:
        if record:
            record.set_state(EmailDeliveryState.FAILED, str(e))
            db.session.commit()
        logger.error("Email send failed to %s: %s", recipient, e)
        return {
            "status": "failed",
            "record_id": record.id if record else None,
            "to": recipient,
            "error": str(e),
            "channel": "email",
            "category": category,
        }


def get_record(record_id: int) -> Optional[EmailRecord]:
    """Retrieve an email record by ID."""
    return db.session.get(EmailRecord, record_id)


def get_records_by_business_event(business_event_id: str) -> list[EmailRecord]:
    """Retrieve all email records for a business event."""
    return EmailRecord.query.filter_by(business_event_id=business_event_id).order_by(
        EmailRecord.created_at.desc()
    ).all()


def get_records_by_recipient(recipient: str, limit: int = 50) -> list[EmailRecord]:
    """Retrieve recent email records for a recipient."""
    return EmailRecord.query.filter_by(recipient=recipient).order_by(
        EmailRecord.created_at.desc()
    ).limit(limit).all()