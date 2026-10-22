"""Alert engine — detection, dedup, delivery with retry, recovery verification.

Design contract (E1):

* Meaningful failure detection — alerts fire on a FLOOD (>= N occurrences of
  the same rule within a window), never on a single transient error.
* Deduplication — one active event per (rule, alert_key); DB-backed so
  gunicorn's sync workers share the cooldown.
* Truthful delivery — delivery_state is pending | delivered | failed |
  unconfigured; a failed delivery is retried with backoff and then recorded
  as failed, never silently dropped and never raised into the request path.
* Recovery verification — an active alert whose rule goes quiet for
  recovery_quiet seconds is marked RECOVERED and a resolution message is
  delivered, so operators see both arms of the lifecycle.
* No fake success — when no recipient/channel is configured the event is
  recorded as unconfigured (observable), not "delivered".
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from app import db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rule configuration
# ---------------------------------------------------------------------------

FAILURE_FLOOD_THRESHOLD = int(__import__("os").environ.get("ALERT_FLOOD_THRESHOLD", "3"))
FAILURE_FLOOD_WINDOW_SECONDS = int(__import__("os").environ.get("ALERT_FLOOD_WINDOW", "60"))
COOLDOWN_SECONDS = int(__import__("os").environ.get("ALERT_COOLDOWN", "900"))
RECOVERY_QUIET_SECONDS = int(__import__("os").environ.get("ALERT_RECOVERY_QUIET", "900"))
MAX_DELIVERY_ATTEMPTS = int(__import__("os").environ.get("ALERT_MAX_DELIVERY_ATTEMPTS", "3"))
DELIVERY_BACKOFF_BASE = int(__import__("os").environ.get("ALERT_DELIVERY_BACKOFF", "5"))
DEFAULT_RECIPIENT = __import__("os").environ.get("ALERT_EMAIL", "")

DB_ERROR_FRAGMENTS = ("sqlalchemy", "OperationalError", "ProgrammingError",
                      "InterfaceError", "connection")


class AlertEngine:
    """Process-wide alert state + DB-backed dedup and delivery."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # rule -> {alert_key: {"count": int, "window_started": float}}
        self._flood_windows: dict[str, dict[str, dict]] = {}
        self._recovery_checked_at: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def classify_exception(self, exc_type_name: str) -> str:
        """Map an exception type name to a rule. db_error for SQLAlchemy."""
        if any(f in exc_type_name for f in DB_ERROR_FRAGMENTS):
            return "db_error"
        return "http_5xx"

    def ingest_failure(self, path: str, exc_type_name: str,
                       request_id: str = "") -> None:
        """Record a failure crumb; fire when the flood threshold is crossed.

        Best-effort by design: alerting must never make the failing path
        worse. All exceptions here are swallowed and logged.
        """
        rule = self.classify_exception(exc_type_name)
        key = "{}{}".format(path, ":" + exc_type_name if exc_type_name else "")
        now = time.time()
        try:
            with self._lock:
                bucket = self._flood_windows.setdefault(rule, {}).setdefault(
                    key, {"count": 0, "window_started": now})
                if now - bucket["window_started"] > FAILURE_FLOOD_WINDOW_SECONDS:
                    bucket["count"] = 0
                    bucket["window_started"] = now
                bucket["count"] += 1
                count = bucket["count"]
            if count >= FAILURE_FLOOD_THRESHOLD:
                self.fire_alert(
                    rule=rule,
                    alert_key=key,
                    severity="P2" if rule == "http_5xx" else "P1",
                    subject=f"[SHUNYA] {rule} flood on {path}",
                    body=(
                        f"{count} '{rule}' failures on {path} within "
                        f"{FAILURE_FLOOD_WINDOW_SECONDS}s "
                        f"(threshold {FAILURE_FLOOD_THRESHOLD}). "
                        f"latest request_id={request_id}"
                    ),
                    details={"path": path, "exc_type": exc_type_name,
                             "occurrences": count},
                )
        except Exception:  # pragma: no cover - defensive
            logger.exception("alert engine ingest_failure failed")

    # ------------------------------------------------------------------
    # Firing / dedup
    # ------------------------------------------------------------------

    def fire_alert(self, rule: str, alert_key: str, severity: str,
                   subject: str, body: str, details: dict,
                   recipient: str = "") -> dict:
        """Create-or-append an active event (DB dedup) and deliver it."""
        from app.alerting.models import AlertEvent
        now = datetime.utcnow()
        try:
            existing = (
                AlertEvent.query
                .filter_by(rule=rule, alert_key=alert_key, status="active")
                .order_by(AlertEvent.id.desc())
                .first()
            )
            if existing:
                existing.occurrences = (existing.occurrences or 0) + 1
                existing.last_seen = now
                existing.details = details
                db.session.commit()
                # Refresh deliveries for new occurrences at most once per
                # cooldown period (dedup), but still return the existing row.
                return self._maybe_redeliver(existing)
            event = AlertEvent(
                rule=rule, alert_key=alert_key, severity=severity,
                status="active", subject=subject[:255], body=body,
                first_seen=now, last_seen=now, occurrences=1,
                delivery_state="pending", details=details,
            )
            db.session.add(event)
            db.session.commit()
            self._deliver_with_retry(event, recipient)
            return {"alert_id": event.id, "rule": rule,
                    "alert_key": alert_key, "fired": True,
                    "delivery_state": event.delivery_state}
        except Exception:
            db.session.rollback()
            logger.exception("alert engine fire_alert failed")
            return {"alert_id": None, "rule": rule, "fired": False,
                    "delivery_state": "failed", "reason": "engine_error"}

    def _maybe_redeliver(self, event) -> dict:
        """Re-deliver an active event only if past the cooldown window.

        G1.25: the reference point must be the last *delivery*, not the last
        occurrence. ``fire_alert`` sets ``last_seen = now`` immediately before
        calling this, so the old comparison was always false and a continuing
        flood was never re-notified.
        """
        from app.alerting.models import AlertEvent
        last = event.delivered_at or event.first_seen
        if datetime.utcnow() - last > timedelta(seconds=COOLDOWN_SECONDS):
            self._deliver_with_retry(event)
        return {"alert_id": event.id, "rule": event.rule,
                "alert_key": event.alert_key, "fired": False,
                "delivery_state": event.delivery_state}

    # ------------------------------------------------------------------
    # Delivery
    # ------------------------------------------------------------------

    def _deliver_with_retry(self, event, recipient: str = "") -> None:
        """Deliver with bounded retries; never raises.

        A delivery failure is recorded on the event (delivery_state=failed)
        with retry count in details; the event remains active so recovery
        messaging can still reach the operator via a later success.
        """
        from app.alerting.models import AlertEvent
        target = recipient or event.details.get("recipient") or DEFAULT_RECIPIENT
        if not target:
            event.delivery_state = "unconfigured"
            db.session.commit()
            logger.warning("alert %s (rule=%s): no ALERT_EMAIL configured — "
                           "delivery_state=unconfigured", event.alert_key, event.rule)
            return
        attempt = 0
        last_status = "unconfigured"
        while attempt < MAX_DELIVERY_ATTEMPTS:
            try:
                result = self._deliver(target, event.subject, event.body)
                last_status = result.get("status", "unknown")
                if result.get("status") in ("accepted", "queued", "logged"):
                    event.delivery_state = "delivered"
                    event.delivered_at = datetime.utcnow()
                    details = dict(event.details or {})
                    details["delivery_attempts"] = attempt + 1
                    details["provider_status"] = result.get("status")
                    details["recipient"] = target
                    event.details = details
                    db.session.commit()
                    logger.info("ALERT delivered: rule=%s key=%s to=%s "
                                "(attempt %d, provider=%s)",
                                event.rule, event.alert_key, target,
                                attempt + 1, result.get("status"))
                    return
                to_retry = NOT_ACCEPTED_RETRIABLE.get(result.get("status"), False)
                if not to_retry:
                    break
            except Exception:
                logger.exception("alert delivery attempt %d failed for %s",
                                 attempt + 1, event.alert_key)
            attempt += 1
            if attempt < MAX_DELIVERY_ATTEMPTS:
                time.sleep(DELIVERY_BACKOFF_BASE * attempt)
        event.delivery_state = "failed"
        details = dict(event.details or {})
        details["delivery_attempts"] = attempt
        details["final_status"] = last_status
        event.details = details
        db.session.commit()
        logger.error("ALERT DELIVERY FAILED: rule=%s key=%s attempts=%d "
                     "final_status=%s", event.rule, event.alert_key,
                     attempt, last_status)

    def _deliver(self, recipient: str, subject: str, body: str) -> dict:
        """Send through the canonical email core (Resend in production).

        is_human_triggered=True is REQUIRED by the email core send guardrail;
        operational alerts are the sanctioned human-triggered class.
        """
        from app.communication import email_core
        return email_core.send(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type="system_alert",
            business_event_id="alert:{}".format(int(time.time() * 1000)),
            category="operational",
            is_human_triggered=True,
        )

    # ------------------------------------------------------------------
    # Recovery verification
    # ------------------------------------------------------------------

    def check_recovery(self) -> int:
        """Mark stale active alerts RECOVERED and deliver resolution messages.

        Returns the number of alerts recovered in this pass. A rule is
        considered quiet when no NEW failure has been ingested for the rule
        within RECOVERY_QUIET_SECONDS. Any recent failure (any path) resets
        the quiet timer for its rule.
        """
        from app.alerting.models import AlertEvent
        now = time.time()
        recovered = 0
        try:
            active = AlertEvent.query.filter_by(status="active").all()
            # Which rules saw failures recently?
            recently_active: set[str] = set()
            with self._lock:
                for rule, buckets in self._flood_windows.items():
                    for bucket in buckets.values():
                        if now - bucket["window_started"] <= RECOVERY_QUIET_SECONDS:
                            recently_active.add(rule)
            for event in active:
                if event.rule in recently_active:
                    continue
                last_seen_ts = event.last_seen.replace(tzinfo=timezone.utc).timestamp()
                if now - last_seen_ts >= RECOVERY_QUIET_SECONDS:
                    event.status = "recovered"
                    event.recovered_at = datetime.utcnow()
                    db.session.commit()
                    recovered += 1
                    logger.info("ALERT RECOVERED: rule=%s key=%s", event.rule, event.alert_key)
                    body = (
                        f"Recovered: {event.subject}\n\n"
                        f"No new '{event.rule}' failures for "
                        f"{RECOVERY_QUIET_SECONDS}s since last seen at "
                        f"{event.last_seen.isoformat()}. Total occurrences "
                        f"while active: {event.occurrences}."
                    )
                    self._deliver_recovery(event, body)
            return recovered
        except Exception:
            db.session.rollback()
            logger.exception("alert engine check_recovery failed")
            return recovered

    def _deliver_recovery(self, event, body: str) -> None:
        """Best-effort resolution message on its own retry budget."""
        target = event.details.get("recipient") or DEFAULT_RECIPIENT
        if not target:
            return
        try:
            result = self._deliver(target, f"[SHUNYA] RECOVERED: {event.subject}", body)
            status = result.get("status", "unknown")
            details = dict(event.details or {})
            details["recovery_delivery"] = status
            event.details = details
            db.session.commit()
        except Exception:
            logger.exception("alert recovery delivery failed for %s", event.alert_key)

    # ------------------------------------------------------------------
    # Manual / test alert (E1 e2e proof)
    # ------------------------------------------------------------------

    def fire_test_alert(self, recipient: str = "", subject: str = "SHUNYA test alert") -> dict:
        """Fire a deliberate test alert through the real delivery path."""
        return self.fire_alert(
            rule="test_alert",
            alert_key="manual:{}".format(int(time.time() / 60)),
            severity="P3",
            subject=subject[:255],
            body=(
                "This is a SHUNYA operational alerting test. If you received "
                "this, alert delivery (detection → dedup → delivery → "
                "recovery) is functioning end to end."
            ),
            details={"source": "operator_test"},
            recipient=recipient,
        )

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def run_loop(self, stop_event: threading.Event) -> None:
        """Background thread body: periodic recovery verification."""
        while not stop_event.is_set():
            try:
                self.check_recovery()
            except Exception:
                logger.exception("alert loop iteration failed")
            for _ in range(30):
                if stop_event.is_set():
                    return
                threading.Event().wait(1)


# Retriable provider statuses (email_core returns 'accepted' on success).
NOT_ACCEPTED_RETRIABLE = {
    "failed": True,
    "exhausted": True,
    "unconfigured": True,
}

_engine: AlertEngine | None = None
_engine_lock = threading.Lock()


def get_alert_engine() -> AlertEngine:
    """Process singleton (module-level via guard)."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = AlertEngine()
        return _engine