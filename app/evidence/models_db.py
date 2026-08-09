"""Evidence persistence model + enforcement.

PHASE 3: Strict evidence linking. Every signal/decision MUST trace to source.
DB-backed Evidence model with source_type, source_id, raw_reference.
"""

import logging
from typing import Any, Optional

from app.core.db import db
from app.core.time import now

logger = logging.getLogger(__name__)


class Evidence(db.Model):
    """DB-backed evidence record linking signals/decisions to their source."""

    __tablename__ = "evidence_records"

    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(50), nullable=False)  # email/pdf/contact/event/execution/ai/proposal
    source_id = db.Column(db.String(100), nullable=False)   # e.g., email_thread_id, object_id, proposal_id
    raw_reference = db.Column(db.JSON, default=dict)        # raw snippet/reference
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "raw_reference": self.raw_reference or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def create_evidence(
    source_type: str,
    source_id: str,
    raw_reference: Optional[dict] = None,
) -> Evidence:
    """Create and persist an evidence record.

    Args:
        source_type: email/pdf/contact/event/execution/ai/proposal
        source_id: Reference to the source (thread id, object id, proposal id)
        raw_reference: Raw snippet of the source

    Returns:
        The persisted Evidence record.
    """
    ev = Evidence(
        source_type=source_type,
        source_id=str(source_id),
        raw_reference=raw_reference or {},
    )
    db.session.add(ev)
    db.session.flush()
    logger.info(
        "Evidence created: type=%s source=%s id=%d",
        source_type, source_id, ev.id,
    )
    return ev


def require_evidence(source_type: str, source_id: str, raw_reference: Optional[dict] = None) -> Evidence:
    """Create evidence AND enforce that a signal cannot exist without it.

    HARD RULE: No awareness without evidence. No decision without evidence.
    This is the single enforcement point for evidence linking.

    Args:
        source_type: email/pdf/contact/event/execution/ai/proposal
        source_id: Reference to the source
        raw_reference: Raw snippet of the source

    Returns:
        The created Evidence record.

    Raises:
        RuntimeError: If evidence creation fails (signal must not proceed).
    """
    try:
        return create_evidence(source_type, source_id, raw_reference)
    except Exception as e:
        logger.error("EVIDENCE REQUIRED BUT FAILED: %s", e)
        raise RuntimeError(
            f"No evidence -> no signal. Failed to create evidence "
            f"({source_type}:{source_id}): {e}"
        ) from e


def get_evidence(evidence_id: int) -> Optional[Evidence]:
    """Fetch an evidence record by id."""
    return db.session.get(Evidence, evidence_id)


def list_evidence(source_type: Optional[str] = None, limit: int = 50) -> list:
    """List evidence records, optionally filtered by source_type."""
    q = Evidence.query.order_by(Evidence.id.desc())
    if source_type:
        q = q.filter(Evidence.source_type == source_type)
    return [e.to_dict() for e in q.limit(limit).all()]


def count_evidence() -> int:
    """Total evidence records."""
    return Evidence.query.count()