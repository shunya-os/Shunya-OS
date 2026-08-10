"""Idempotency Guard — prevents duplicate event/execution processing.

Uses evidence records as the canonical idempotency store with a
database-level unique constraint on (source_type, source_id) for
atomic check-then-create semantics.

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

    Uses the canonical evidence store with a DB-level unique constraint
    on (source_type, source_id). The database provides atomic mutual
    exclusion for concurrent deliveries.
    """

    def guard(self, source_type: str, source_id: str, metadata: Optional[dict] = None) -> dict:
        """Check idempotency and mark as processed in one logical operation.

        Uses DB-level unique constraint for atomicity: the database
        prevents two concurrent deliveries from both passing the check.

        Returns:
            dict with:
                - processed: True if first-time processing
                - skipped: True if this is a duplicate
                - idempotency_check_failed: True if the guard could not
                  establish idempotency (persistence unavailable)
                - reason: Explanation string

        Raises:
            RuntimeError: If persistence fails and idempotency cannot
                be established. The caller must NOT proceed with execution.
        """
        from app.evidence.models_db import EvidenceRecord
        from app.core.db import get_session

        # Try to create the evidence record atomically.
        # The DB-level unique constraint on (source_type, source_id)
        # ensures that only one of two concurrent deliveries succeeds.
        session = None
        try:
            from app.evidence.models_db import EvidenceRecord
            from app.core.db import get_session
            session = get_session()
            ev = EvidenceRecord(
                source_type=source_type,
                source_id=source_id,
                raw_reference=metadata if metadata else {},
            )
            session.add(ev)
            session.commit()

            logger.info("IdempotencyGuard: first-time %s:%s", source_type, source_id)
            return {
                "processed": True,
                "skipped": False,
                "idempotency_check_failed": False,
                "reason": "First processing",
            }

        except IntegrityError:
            if session:
                session.rollback()
            logger.info("IdempotencyGuard: duplicate %s:%s", source_type, source_id)
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
                "IdempotencyGuard: FAILED for %s:%s — %s",
                source_type, source_id, e,
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