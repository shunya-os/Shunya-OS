"""SQL-backed EvidenceStore — bridges the canonical Evidence dataclass to production persistence.

The Evidence dataclass (app/evidence/models.py) is the canonical domain model.
The EvidenceRecord SQLAlchemy model (app/evidence/models_db.py) is the canonical
persistence layer. This SqlEvidenceStore implements the EvidenceStore interface
using EvidenceRecord, replacing the development-only InMemoryEvidenceStore.

Usage:
    from app.evidence.sql_store import SqlEvidenceStore
    store = SqlEvidenceStore()
    ev = store.create(Evidence(target_id="t1", target_type="Node"))
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app import db
from app.evidence.models import (
    Evidence, EvidenceStore, EvidenceStatus,
    EvidenceSource, Provenance,
)
from app.evidence.models_db import EvidenceRecord

logger = logging.getLogger(__name__)


class SqlEvidenceStore(EvidenceStore):
    """Production evidence store backed by the evidence_records SQL table.

    Maps the canonical Evidence dataclass to/from EvidenceRecord rows.
    Version history is stored as JSON in the raw_reference column.
    """

    def create(self, evidence: Evidence) -> Evidence:
        """Persist a new Evidence record.

        Raises ValueError if evidence_id already exists.
        """
        existing = EvidenceRecord.query.filter_by(
            source_type="evidence",
            source_id=evidence.evidence_id,
        ).first()
        if existing:
            raise ValueError(
                f"Evidence '{evidence.evidence_id}' already exists in the store"
            )
        ev = EvidenceRecord(
            source_type="evidence",
            source_id=evidence.evidence_id,
            raw_reference=self._evidence_to_dict(evidence),
        )
        db.session.add(ev)
        db.session.commit()
        logger.info("Evidence %s persisted (id=%d)", evidence.evidence_id, ev.id)
        return evidence

    def get(self, evidence_id: str) -> Optional[Evidence]:
        """Get an Evidence record by identity. Returns None if not found."""
        record = EvidenceRecord.query.filter_by(
            source_type="evidence",
            source_id=evidence_id,
        ).order_by(EvidenceRecord.id.desc()).first()
        if not record:
            return None
        return self._dict_to_evidence(record.raw_reference or {})

    def get_version(self, evidence_id: str, version: int) -> Optional[Evidence]:
        """Get a specific version of an Evidence record.

        Version history is stored as a JSON list in the raw_reference['versions'].
        """
        record = EvidenceRecord.query.filter_by(
            source_type="evidence",
            source_id=evidence_id,
        ).order_by(EvidenceRecord.id.desc()).first()
        if not record:
            return None
        ref = record.raw_reference or {}
        if version == 1:
            return self._dict_to_evidence(ref)
        versions = ref.get("versions", [])
        for v in versions:
            if v.get("version") == version:
                return self._dict_to_evidence(v)
        return None

    def get_history(self, evidence_id: str) -> list[Evidence]:
        """Get the full version history for an Evidence record.

        Returns versions in ascending order (oldest first).
        """
        record = EvidenceRecord.query.filter_by(
            source_type="evidence",
            source_id=evidence_id,
        ).order_by(EvidenceRecord.id.desc()).first()
        if not record:
            return []
        ref = record.raw_reference or {}
        base = self._dict_to_evidence(ref)
        if base is None:
            return []
        results = [base]
        for v in ref.get("versions", []):
            ev = self._dict_to_evidence(v)
            if ev:
                results.append(ev)
        return results

    def count(self) -> int:
        """Total number of evidence records (base identities, not versions)."""
        return EvidenceRecord.query.filter_by(source_type="evidence").count()

    def all(self) -> list[Evidence]:
        """Get all evidence records (latest version of each)."""
        records = EvidenceRecord.query.filter_by(
            source_type="evidence"
        ).order_by(EvidenceRecord.id.desc()).all()
        results = []
        seen = set()
        for r in records:
            eid = r.source_id
            if eid in seen:
                continue
            seen.add(eid)
            ev = self._dict_to_evidence(r.raw_reference or {})
            if ev:
                results.append(ev)
        return results

    # ── Serialization helpers ──────────────────────────────────────────

    def _evidence_to_dict(self, ev: Evidence) -> dict:
        """Convert an Evidence dataclass to a dict for JSON storage."""
        d = {
            "evidence_id": ev.evidence_id,
            "target_id": ev.target_id,
            "target_type": ev.target_type,
            "observation_id": ev.observation_id,
            "evidence_type": ev.evidence_type,
            "status": ev.status,
            "version": ev.version,
            "created_at": ev.created_at,
            "supersedes": ev.supersedes,
        }
        if ev.provenance:
            d["provenance"] = {
                "created_by": ev.provenance.created_by,
                "created_at": ev.provenance.created_at,
                "source": {
                    "category": ev.provenance.source.category.value,
                    "identifier": ev.provenance.source.identifier,
                    "description": ev.provenance.source.description,
                },
                "process": ev.provenance.process,
                "supersedes": ev.provenance.supersedes,
                "derived_from": ev.provenance.derived_from,
                "rationale": ev.provenance.rationale,
            }
        if ev.confidence:
            d["confidence"] = {
                "score": ev.confidence.score,
                "label": ev.confidence.label,
                "reason": ev.confidence.reason,
            }
        if ev.metadata:
            d["metadata"] = dict(ev.metadata)
        return d

    def _dict_to_evidence(self, d: dict) -> Optional[Evidence]:
        """Reconstruct an Evidence dataclass from a dict."""
        if not d or not d.get("evidence_id"):
            return None
        try:
            return Evidence(
                evidence_id=d.get("evidence_id", ""),
                target_id=d.get("target_id", ""),
                target_type=d.get("target_type", ""),
                observation_id=d.get("observation_id", ""),
                evidence_type=d.get("evidence_type", "observed"),
                status=d.get("status", "active"),
                version=d.get("version", 1),
                created_at=d.get("created_at", ""),
                supersedes=d.get("supersedes", ""),
                metadata=d.get("metadata", {}),
            )
        except Exception as e:
            logger.warning("Failed to reconstruct Evidence from dict: %s", e)
            return None


# Singleton
_sql_store: Optional[SqlEvidenceStore] = None


def get_sql_evidence_store() -> SqlEvidenceStore:
    global _sql_store
    if _sql_store is None:
        _sql_store = SqlEvidenceStore()
    return _sql_store