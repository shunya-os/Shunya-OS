"""SHUNYA — Memory Store: Persist AI interaction memory into memory_records.

Provides a simple store_ai_memory() function that INSERTs into the
canonical memory_records table. Designed for /ask and other AI endpoints
so the Memory workspace shows data.
"""

import hashlib
import logging
from typing import Optional

from app import db
from app.memory.models import MemoryRecord

logger = logging.getLogger(__name__)


def store_ai_memory(
    tenant_id: int | str | None,
    *,
    memory_type: str = "ai_interaction",
    memory_key: str,
    value: str,
    summary: str = "",
    scope_type: str = "organization",
) -> MemoryRecord | None:
    """Persist an AI interaction as a memory_record.

    Handles string tenant_id values (common in API responses).
    Catches all exceptions and logs them — memory storage is non-critical.
    """
    try:
        # Normalise tenant_id: convert string to int, 0/falsy to None
        resolved_tenant = None
        if tenant_id:
            try:
                resolved_tenant = int(tenant_id)
            except (ValueError, TypeError):
                resolved_tenant = None

        # Rollback any stale transaction before creating new record
        db.session.rollback()

        record = MemoryRecord(
            tenant_id=resolved_tenant,
            memory_type=memory_type,
            memory_key=memory_key,
            value=value,
            summary=(summary or "")[:500],
            scope_type=scope_type,
            status="active",
            creation_mechanism="context_promoted",
            truth_classification="memory",
            created_by="ai_pipeline",
        )
        db.session.add(record)
        db.session.commit()
        logger.info(
            "Stored ai_interaction memory record %d (key=%s, tenant=%s)",
            record.id,
            memory_key,
            resolved_tenant,
        )
        return record
    except Exception:
        db.session.rollback()
        logger.exception("Failed to store ai_interaction memory")
        return None