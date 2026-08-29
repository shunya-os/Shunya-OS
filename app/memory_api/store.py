"""SHUNYA — Memory Store: Persist AI interaction memory into memory_records.

Provides a simple `store_ai_memory()` function that INSERTs into the
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
    tenant_id: int | None,
    *,
    memory_type: str = "ai_interaction",
    memory_key: str,
    value: str,
    summary: str = "",
    scope_type: str = "organization",
) -> MemoryRecord | None:
    """Persist an AI interaction as a memory_record.

    Parameters
    ----------
    tenant_id : int | None
        The tenant (organization) this memory belongs to.
        Pass ``None`` or 0 when the tenant relationship is uncertain —
        the column is nullable in the database.
    memory_type : str
        Type of memory (default ``ai_interaction``).
    memory_key : str
        Unique-ish key for dedup / lookup (e.g. hash of the question).
    value : str
        The answer / body of the memory (e.g. the AI's response).
    summary : str
        Short human-readable label (e.g. the question, truncated).
    scope_type : str
        Scope of the memory (default ``organization``).

    Returns
    -------
    MemoryRecord | None
        The newly created record, or *None* on failure.
    """
    try:
        # Normalise tenant_id: treat 0 / falsy the same as None to
        # avoid FK violations when the value doesn't exist in tenants.
        resolved_tenant = tenant_id if tenant_id else None

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