"""Idempotency Guard — prevents duplicate event/execution processing.

Provides a simple mechanism to check whether an event or execution
request has already been processed, using evidence records as the
canonical idempotency store.

Usage:
    guard = IdempotencyGuard()
    if guard.is_duplicate(source_type, source_id):
        return {"status": "skipped", "reason": "duplicate"}
    guard.mark_processed(source_type, source_id, metadata={})
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class IdempotencyGuard:
    """Prevents duplicate processing of events and execution requests.

    Uses evidence records as the durable idempotency store.
    Thread-safe for single-process use; for multi-process deployments
    the database provides the mutual exclusion.
    """

    def is_duplicate(self, source_type: str, source_id: str) -> bool:
        """Check if a source_type + source_id combination has been processed.

        Args:
            source_type: Type of source (email, webhook, event, execution)
            source_id: Unique identifier within the source type

        Returns:
            True if already processed, False otherwise
        """
        try:
            from app.evidence.models_db import EvidenceRecord
            existing = EvidenceRecord.query.filter_by(
                source_type=source_type,
                source_id=source_id,
            ).first()
            return existing is not None
        except Exception as e:
            logger.warning("IdempotencyGuard: check failed: %s", e)
            return False  # Fail open — better to process than silently drop

    def mark_processed(
        self,
        source_type: str,
        source_id: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Mark a source_type + source_id as processed.

        Creates an evidence record. If the record already exists,
        it's a no-op (idempotent).

        Args:
            source_type: Type of source
            source_id: Unique identifier within the source type
            metadata: Optional metadata to store with the evidence

        Returns:
            True if newly created, False if already existed
        """
        if self.is_duplicate(source_type, source_id):
            return False  # Already processed

        try:
            from app.evidence.models_db import create_evidence
            create_evidence(
                source_type=source_type,
                source_id=source_id,
                raw_reference=metadata or {},
            )
            return True
        except Exception as e:
            logger.error("IdempotencyGuard: mark failed: %s", e)
            raise

    def guard(self, source_type: str, source_id: str, metadata: Optional[dict] = None) -> dict:
        """Combined guard: check, mark, and return result.

        This is the primary API. Call this at the start of any
        event/execution handler.

        Returns:
            dict with:
                - processed: True if this is the first time
                - skipped: True if this is a duplicate
                - reason: Explanation string
        """
        if self.is_duplicate(source_type, source_id):
            return {
                "processed": False,
                "skipped": True,
                "reason": f"Duplicate {source_type}:{source_id} — already processed",
            }

        try:
            self.mark_processed(source_type, source_id, metadata)
            return {
                "processed": True,
                "skipped": False,
                "reason": "First processing",
            }
        except Exception as e:
            logger.warning("IdempotencyGuard: guard failed: %s", e)
            return {
                "processed": False,
                "skipped": False,
                "reason": f"Guard error: {e}",
            }


# Singleton
_guard: Optional[IdempotencyGuard] = None


def get_guard() -> IdempotencyGuard:
    global _guard
    if _guard is None:
        _guard = IdempotencyGuard()
    return _guard