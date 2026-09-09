"""Idempotency Guard — prevents duplicate event/execution processing.

Uses the dedicated execution_idempotency table which has a unique
constraint on idempotency_key (source_type + ":" + source_id) for
atomic check-then-create semantics under concurrent writes.

Evidence records are used for the actual evidence chain and do not
carry the idempotency constraint (multiple evidence records per
execution run are allowed for different evidence types).

The guard is FAIL-CLOSED: if the persistence layer is unavailable,
the guard returns a failure result rather than allowing potential
duplicate execution.
"""

import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


class IdempotencyGuard:
    """Prevents duplicate processing of events and execution requests.

    Uses the execution_idempotency table with a DB-level unique constraint
    on idempotency_key for atomic mutual exclusion. The key is derived
    from source_type + ":" + source_id.
    """

    def guard(self, source_type: str, source_id: str, metadata: Optional[dict] = None) -> dict:
        """Check idempotency and mark as processed in one logical operation.

        Uses DB-level unique constraint on the execution_idempotency table
        for atomicity: the database prevents two concurrent deliveries from
        both passing the check.

        Returns:
            dict with:
                - processed: True if first-time processing
                - skipped: True if this is a duplicate
                - idempotency_check_failed: True if the guard could not
                  establish idempotency (persistence unavailable)
                - reason: Explanation string
        """
        from app.execution.models import IdempotencyRecord
        from app.core.db import get_session
        from datetime import datetime, timezone

        idempotency_key = f"{source_type}:{source_id}"

        session = None
        try:
            from app.execution.models import IdempotencyRecord
            from app.core.db import get_session
            session = get_session()
            record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                outcome_id="pending",
                identity_id="system",
                created_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()

            logger.info("IdempotencyGuard: first-time %s", idempotency_key)
            return {
                "processed": True,
                "skipped": False,
                "idempotency_check_failed": False,
                "reason": "First processing",
            }

        except IntegrityError:
            if session:
                session.rollback()
            logger.info("IdempotencyGuard: duplicate %s", idempotency_key)
            return {
                "processed": False,
                "skipped": True,
                "idempotency_check_failed": False,
                "reason": f"Duplicate {source_type}:{source_id} — already processed",
            }

        except Exception as e:
            if session:
                try:
                    session.rollback()
                except Exception:
                    pass
            logger.error(
                "IdempotencyGuard: FAILED for %s — %s",
                idempotency_key, e,
            )
            # FAIL-CLOSED: cannot establish idempotency → must not authorize execution.
            return {
                "processed": False,
                "skipped": False,
                "idempotency_check_failed": True,
                "reason": f"Idempotency check failed: {e}",
            }


# Singleton
_guard: Optional[IdempotencyGuard] = None


def get_guard() -> IdempotencyGuard:
    global _guard
    if _guard is None:
        _guard = IdempotencyGuard()
    return _guard