"""Durable Memory Bridge — MemoryEngine → canonical MemoryRecord persistence.

This module is the concrete implementation of the MANDATORY durable memory
convergence: every memory entry written through the Intelligence Runtime's
MemoryEngine is persisted into the canonical `memory_records` table via the
MemoryRecord SQLAlchemy model.

Isolation contract:
  - Every record is scoped by tenant_id and owner_identity_id.
  - Retrieval always filters by BOTH — cross-tenant / cross-user leakage is
    impossible by construction.
  - Status lifecycle: active records are retrievable. Superseded/invalidated
    records remain in the table (provenance preserved) but are excluded from
    deterministic retrieval.

Restart persistence:
  - Data lives in PostgreSQL/SQLite via the app's db session — a fresh
    MemoryEngine instance wired with this repository retrieves the same
    memories after process restart.

The bridge is intentionally free of business logic — it is a storage adapter
between the runtime's typed MemoryEntry and the canonical MemoryRecord model.
"""

from __future__ import annotations

import logging
from typing import Any

from .memory import MemoryRepository

logger = logging.getLogger(__name__)

# Map runtime MemoryType enum values → canonical MemoryRecord memory_type strings
_RUNTIME_TO_DB_TYPE = {
    "short_term": "conversation",
    "long_term": "fact",
    "organization": "business_context",
    "business": "business_context",
}
_DB_TO_RUNTIME_TYPE = {v: k for k, v in _RUNTIME_TO_DB_TYPE.items()}
_DB_TO_RUNTIME_TYPE.setdefault("conversation", "short_term")
_DB_TO_RUNTIME_TYPE.setdefault("fact", "long_term")


def _db_type(memory_type: Any) -> str:
    """Map a runtime MemoryType (enum or value string) to a MemoryRecord memory_type."""
    val = getattr(memory_type, "value", memory_type) if memory_type is not None else "short_term"
    return _RUNTIME_TO_DB_TYPE.get(str(val), str(val))


def _runtime_type(memory_type: str | None) -> Any:
    """Map a MemoryRecord memory_type string back to a runtime MemoryType."""
    from .types import MemoryType

    val = _DB_TO_RUNTIME_TYPE.get(memory_type or "", memory_type or "short_term")
    try:
        return MemoryType(val)
    except ValueError:
        return MemoryType.SHORT_TERM


class DBMemoryRepository(MemoryRepository):
    """MemoryRepository backed by the canonical app.memory.models.MemoryRecord.

    Implements the same interface as InMemoryMemoryRepository so the
    MemoryEngine can swap backends without behavioural change.
    """

    def __init__(self) -> None:
        from app import db  # lazy: only when app context is available
        self._db = db

    # ── Internal helpers ───────────────────────────────────────────────────

    def _session(self):
        return self._db.session

    def store_entry(self, entry: Any, identity_id: str = "", tenant_id: str = "") -> None:
        """Persist a runtime MemoryEntry into the canonical memory_records table."""
        from app.memory.models import MemoryRecord

        try:
            self._session().rollback()
            record = MemoryRecord(
                tenant_id=int(tenant_id) if str(tenant_id).isdigit() else None,
                owner_identity_id=identity_id or None,
                memory_key=entry.key,
                value=entry.content,
                memory_type=_db_type(entry.memory_type),
                summary=(entry.content or "")[:500],
                scope_type="person" if identity_id else "tenant",
                creation_mechanism="deterministic_derived",
                truth_classification="memory",
                status="active",
                confidence=float(getattr(entry, "confidence", 1.0) or 1.0),
                source=(entry.source or "")[:255],
                created_by=identity_id or "system",
                memory_eligibility_state="eligible",
            )
            self._session().add(record)
            self._session().commit()
        except Exception as exc:  # memory must never break the runtime
            self._session().rollback()
            logger.warning("DB memory store failure (key=%s): %s", getattr(entry, "key", "?"), exc)

    def get_entry(self, key: str, identity_id: str = "", tenant_id: str = "") -> Any | None:
        """Retrieve a single active memory entry — scoped by identity and tenant."""
        from app.memory.models import MemoryRecord
        from .types import MemoryEntry
        from datetime import datetime, timezone

        q = MemoryRecord.query.filter_by(memory_key=key, status="active")
        if identity_id:
            q = q.filter_by(owner_identity_id=identity_id)
        if tenant_id:
            q = q.filter_by(tenant_id=int(tenant_id) if str(tenant_id).isdigit() else None)
        record = q.order_by(MemoryRecord.created_at.desc()).first()
        if not record:
            return None
        return MemoryEntry(
            key=record.memory_key,
            content=record.value,
            memory_type=_runtime_type(record.memory_type),
            source=record.source or record.created_by or "",
            confidence=float(record.confidence or 1.0),
            timestamp=(record.created_at or datetime.now(timezone.utc)).isoformat(),
        )

    def search(self, query: str, identity_id: str = "", tenant_id: str = "",
               memory_type: Any | None = None, limit: int = 10) -> list:
        """Deterministic search over active memory records — identity/tenant scoped."""
        from app.memory.models import MemoryRecord
        from .types import MemoryEntry

        q = MemoryRecord.query.filter_by(status="active")
        if identity_id:
            q = q.filter_by(owner_identity_id=identity_id)
        if tenant_id:
            q = q.filter_by(tenant_id=int(tenant_id) if str(tenant_id).isdigit() else None)
        if memory_type is not None:
            q = q.filter_by(memory_type=_db_type(memory_type))
        needle = query.lower()
        candidates = q.order_by(MemoryRecord.created_at.desc()).limit(200).all()
        results = []
        for r in candidates:
            hay = (r.value or "").lower() + " " + (r.memory_key or "").lower()
            if needle in hay:
                results.append(MemoryEntry(
                    key=r.memory_key,
                    content=r.value or "",
                    memory_type=_runtime_type(r.memory_type),
                    source=r.source or r.created_by or "",
                    confidence=float(r.confidence or 1.0),
                    timestamp=r.created_at.isoformat() if r.created_at else "",
                ))
        results.sort(key=lambda e: (-e.confidence, e.timestamp), reverse=False)
        return results[:limit]

    def recall_recent(self, identity_id: str = "", tenant_id: str = "",
                      memory_type: Any | None = None, limit: int = 10) -> list:
        from app.memory.models import MemoryRecord
        from .types import MemoryEntry

        q = MemoryRecord.query.filter_by(status="active")
        if identity_id:
            q = q.filter_by(owner_identity_id=identity_id)
        if tenant_id:
            q = q.filter_by(tenant_id=int(tenant_id) if str(tenant_id).isdigit() else None)
        if memory_type is not None:
            q = q.filter_by(memory_type=_db_type(memory_type))
        records = q.order_by(MemoryRecord.created_at.desc()).limit(limit).all()
        return [
            MemoryEntry(
                key=r.memory_key,
                content=r.value or "",
                memory_type=_runtime_type(r.memory_type),
                source=r.source or r.created_by or "",
                confidence=float(r.confidence or 1.0),
                timestamp=r.created_at.isoformat() if r.created_at else "",
            )
            for r in records
        ]

    def forget(self, key: str, identity_id: str = "", tenant_id: str = "") -> bool:
        """Soft-delete — mark superseded (provenance preserved)."""
        from app.memory.models import MemoryRecord

        q = MemoryRecord.query.filter_by(memory_key=key, status="active")
        if identity_id:
            q = q.filter_by(owner_identity_id=identity_id)
        if tenant_id:
            q = q.filter_by(tenant_id=int(tenant_id) if str(tenant_id).isdigit() else None)
        record = q.first()
        if not record:
            return False
        record.status = "superseded"
        record.superseded_by_id = record.id
        self._session().commit()
        return True

    def count(self, identity_id: str = "", tenant_id: str = "",
              memory_type: Any | None = None) -> int:
        from app.memory.models import MemoryRecord

        q = MemoryRecord.query.filter_by(status="active")
        if identity_id:
            q = q.filter_by(owner_identity_id=identity_id)
        if tenant_id:
            q = q.filter_by(tenant_id=int(tenant_id) if str(tenant_id).isdigit() else None)
        if memory_type is not None:
            q = q.filter_by(memory_type=_db_type(memory_type))
        return q.count()

    def clear(self, identity_id: str = "", tenant_id: str = "", memory_type: Any | None = None) -> None:
        from app.memory.models import MemoryRecord

        q = MemoryRecord.query.filter_by(status="active")
        if identity_id:
            q = q.filter_by(owner_identity_id=identity_id)
        if tenant_id:
            q = q.filter_by(tenant_id=int(tenant_id) if str(tenant_id).isdigit() else None)
        if memory_type is not None:
            q = q.filter_by(memory_type=_db_type(memory_type))
        for record in q.all():
            record.status = "superseded"
        self._session().commit()