"""Message outbox — real delivery, no fake sent.

For every pending Message, resolve a channel adapter and attempt actual
delivery. A message is marked ``sent`` ONLY when the adapter returns success.
When no adapter exists for the channel, or the adapter fails, the message
stays ``pending`` and the failure is recorded in ``metadata_json``.

Constitutional boundary: this outbox delivers canonical outbox rows through
the channel adapters (app/communication/adapters.py). Human-gated sends
(MessageProposal) remain on the proposal flow — that gate is unchanged.
"""
import logging

from app.communication.models import Message
from app import db

logger = logging.getLogger(__name__)


def _safe_rollback():
    """Rollback only a genuinely aborted session (mirrors app/runtime/loop.py).

    The outbox runs inside run_cycle which carries uncommitted state from
    other sections — an unconditional rollback would destroy it. Only an
    already-aborted transaction is rolled back.
    """
    try:
        from sqlalchemy.exc import OperationalError, ProgrammingError
        db.session.execute(db.text("SELECT 1"))
    except (OperationalError, ProgrammingError) as e:
        msg = str(e)
        if "aborted" in msg.lower() or "current transaction" in msg.lower():
            try:
                db.session.rollback()
            except Exception:
                pass


def _adapter_for(channel: str):
    """Resolve a delivery adapter for a channel.

    Returns None when no adapter is registered — the message stays pending
    with a recorded failure rather than being falsely marked sent.
    """
    channel_lower = (channel or "").lower()
    try:
        from app.communication.adapters import EmailAdapter, InternalNotesAdapter
    except Exception:
        return None

    if channel_lower == "email":
        return EmailAdapter()
    if channel_lower in ("internal", "system", "note"):
        return InternalNotesAdapter()
    return None


def _recipient_for(msg) -> str:
    """Resolve the recipient from the message metadata or entity context."""
    meta = msg.metadata_json or {}
    if isinstance(meta, dict):
        to = meta.get("to") or meta.get("recipient") or meta.get("email")
        if to:
            return to
    return f"entity:{msg.entity_id}"


def _record_failure(msg, error: str):
    """Record a delivery failure on the message; keep it pending (no fake sent)."""
    meta = dict(msg.metadata_json or {}) if isinstance(msg.metadata_json, dict) else {}
    meta["delivery_error"] = str(error)[:1000]
    meta["delivery_attempts"] = int(meta.get("delivery_attempts", 0)) + 1
    msg.metadata_json = meta


# ── UI-facing delivery state ─────────────────────────────────────────────
# Values rendered by conversation-workspace: pending → sent → delivered |
# failed | bounced. Webhook delivery/bounce events land on EmailRecord; the
# resolver maps its lifecycle state onto the message payload.

EMAIL_STATE_TO_DELIVERY_STATUS = {
    "requested": "pending",
    "accepted": "sent",
    "sent": "sent",
    "delivered": "delivered",
    "bounced": "bounced",
    "complained": "bounced",
    "failed": "failed",
    "retry_pending": "pending",
    "exhausted": "failed",
    "cancelled": "failed",
}

MESSAGE_STATUS_TO_DELIVERY_STATUS = {
    "pending": "pending",
    "sent": "sent",
    "failed": "failed",
    "delivered": "delivered",
    "bounced": "bounced",
}


def resolve_delivery_status(message) -> str:
    """Resolve the UI-facing delivery_status for a message.

    Precedence:
      1. Explicit delivery_status already set on the message payload.
      2. Latest EmailRecord state, when linkable via provider_message_id
         (webhook delivered/bounced/complained events land there).
      3. The message's own lifecycle status (pending/sent/failed).
      4. Direction fallback: persisted outbound → sent, inbound → delivered.
    """
    explicit = getattr(message, "delivery_status", None)
    if not explicit:
        meta = getattr(message, "metadata", None) or getattr(message, "metadata_json", None) or {}
        explicit = meta.get("delivery_status") if isinstance(meta, dict) else None
    if explicit:
        return explicit

    provider_id = getattr(message, "provider_message_id", None)
    if provider_id:
        try:
            from app.communication.email_models import EmailRecord
            record = (
                EmailRecord.query.filter_by(provider_message_id=provider_id)
                .order_by(EmailRecord.updated_at.desc())
                .first()
            )
            if record:
                return EMAIL_STATE_TO_DELIVERY_STATUS.get(record.state, "sent")
        except Exception:
            pass

    status = getattr(message, "status", None)
    if status:
        return MESSAGE_STATUS_TO_DELIVERY_STATUS.get(status, "sent")

    if getattr(message, "direction", "") == "outbound":
        return "sent"
    return "delivered"


def deliver_messages():
    """Deliver all pending outbox messages through their channel adapters.

    Returns a summary dict. Messages are marked 'sent' only when the adapter
    reports success; otherwise they remain 'pending' with the failure recorded.
    """
    pending = Message.query.filter_by(status="pending").all()

    sent = 0
    failed = 0
    skipped = 0
    errors = []

    for msg in pending:
        adapter = _adapter_for(msg.channel)
        if adapter is None:
            _record_failure(
                msg,
                f"No delivery adapter registered for channel '{msg.channel}' — "
                "message remains pending.",
            )
            failed += 1
            errors.append({"message_id": msg.id, "channel": msg.channel,
                           "error": "no_adapter"})
            continue

        try:
            from app.communication.conversation import (
                Conversation,
                ChannelType,
                create_conversation,
            )
            chan_map = {
                "email": ChannelType.EMAIL,
                "internal": ChannelType.INTERNAL,
                "system": ChannelType.INTERNAL,
                "note": ChannelType.INTERNAL,
            }
            channel = chan_map.get((msg.channel or "").lower(), ChannelType.INTERNAL)
            conversation = create_conversation(
                title=_recipient_for(msg),
                channel=channel,
            )
            delivered = adapter.send(
                conversation,
                body=msg.content or "",
                subject=f"SHUNYA update for {_recipient_for(msg)}",
            )
            if delivered is not None:
                msg.status = "sent"
                meta = dict(msg.metadata_json or {}) if isinstance(msg.metadata_json, dict) else {}
                meta["delivery_status"] = "sent"
                msg.metadata_json = meta
                sent += 1
            else:
                _record_failure(msg, "Adapter returned no delivery confirmation.")
                failed += 1
                errors.append({"message_id": msg.id, "channel": msg.channel,
                               "error": "adapter_returned_none"})
        except Exception as e:  # noqa: BLE001 — outbox must never fake delivery
            _safe_rollback()
            _record_failure(msg, f"Delivery failed: {e}")
            failed += 1
            errors.append({"message_id": msg.id, "channel": msg.channel,
                           "error": str(e)[:500]})
            logger.warning("Outbox delivery failed for message %s: %s", msg.id, e)

    try:
        db.session.commit()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        logger.error("Outbox commit failed: %s", e)
        skipped = len(pending)

    summary = {
        "processed": len(pending),
        "sent": sent,
        "failed": failed,
        "remaining_pending": Message.query.filter_by(status="pending").count(),
        "errors": errors[:10],
    }
    if sent or failed:
        logger.info("Outbox cycle: %s", summary)
    return summary