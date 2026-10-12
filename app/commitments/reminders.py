"""Commitment due/overdue reminder producer.

Creates in-app Notification rows for commitments whose due_at has passed
while still active (not completed/failed) and that have not been reminded
yet. Each commitment fires at most one reminder (tracked via
``Commitment.reminded_at``), so repeated calls — from the execution loop or
the notifications bell — are idempotent and never re-spam the same item.

Wired into:
  * app/runtime/loop.py  (_run_commitments — background path)
  * app/notifications/routes.py (list_notifications — BEFORE returning, so
    the bell always reflects real overdue items)
"""

from datetime import datetime, timezone

from app import db
from app.commitments.models import Commitment

# Terminal states: once a commitment reaches these it stops being
# reminder-eligible regardless of due date. Everything else (pending,
# in_progress, open, ...) is still owed and can be reminded.
_TERMINAL_STATUSES = ("completed", "failed")


def _normalize_aware(dt: datetime) -> datetime:
    """SQLite drops tzinfo on round-trip; normalize to aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def raise_due_commitment_notifications() -> int:
    """Create reminder notifications for due/overdue commitments.

    Returns the number of Notification rows created this call.
    """
    now = datetime.now(timezone.utc)

    candidates = Commitment.query.filter(
        Commitment.due_at.isnot(None),
        Commitment.reminded_at.is_(None),
        Commitment.status.notin_(_TERMINAL_STATUSES),
    ).all()

    created = 0
    for c in candidates:
        due_at = _normalize_aware(c.due_at)
        if due_at > now:
            continue  # not due yet — leave reminded_at NULL for later

        c.reminded_at = datetime.now(timezone.utc)

        owner = (c.owner or "").strip()
        if not owner or owner.lower() == "system":
            # Nothing to notify — still mark reminded so the query does not
            # rescan this commitment on every bell fetch.
            db.session.add(c)
            continue

        from app.integration.models import Notification as NotificationRecord

        notif = NotificationRecord(
            identity_id=owner,
            notification_type="commitment_due",
            title=f"Commitment due: {c.title}",
            body=(
                f"This commitment was due on "
                f"{due_at.strftime('%d %b %Y %H:%M')} and is still "
                f"{c.status.replace('_', ' ')}. Update it to keep moving."
            ),
            object_id=str(c.id),
        )
        db.session.add(notif)
        created += 1

    if candidates:
        db.session.commit()
    return created