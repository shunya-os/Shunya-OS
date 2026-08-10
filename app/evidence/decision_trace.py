"""Decision Trace — persistent record of every decision with shadow comparison.

PHASE 3.2: Every execution stores:
- main_decision
- shadow_outputs
- comparison_result
- final_decision

Exposed via API: GET /api/v1/decision-trace/<object_id>
"""

import logging
from typing import Any, Optional

from app.core.db import get_session
from app.core.db import db
from app.core.time import now

logger = logging.getLogger(__name__)


class DecisionTrace(db.Model):
    """Persistent record of every decision cycle."""

    __tablename__ = "decision_traces"

    id = db.Column(db.Integer, primary_key=True)
    object_id = db.Column(db.Integer, index=True, nullable=True)
    main_decision = db.Column(db.JSON, default=dict)
    shadow_outputs = db.Column(db.JSON, default=list)
    comparison_result = db.Column(db.JSON, default=dict)
    final_decision = db.Column(db.JSON, default=dict)
    source = db.Column(db.String(50), default="rule")
    confidence = db.Column(db.Float, default=0.5)
    shadow_agreement_pct = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "object_id": self.object_id,
            "main_decision": self.main_decision or {},
            "shadow_outputs": self.shadow_outputs or [],
            "comparison_result": self.comparison_result or {},
            "final_decision": self.final_decision or {},
            "source": self.source or "rule",
            "confidence": self.confidence or 0.5,
            "shadow_agreement_pct": self.shadow_agreement_pct or 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def record_decision_trace(
    object_id: Optional[int],
    main_decision: dict,
    shadow_outputs: list,
    comparison_result: dict,
    final_decision: dict,
    source: str = "rule",
    confidence: float = 0.5,
) -> DecisionTrace:
    """Record a decision trace with full context."""
    trace = DecisionTrace(
        object_id=object_id,
        main_decision=dict(main_decision),
        shadow_outputs=list(shadow_outputs),
        comparison_result=dict(comparison_result),
        final_decision=dict(final_decision),
        source=source,
        confidence=confidence,
        shadow_agreement_pct=comparison_result.get("shadow_confidence", 0.0) * 100,
    )
    get_session().add(trace)
    get_session().flush()
    logger.info(
        "Decision trace #%d: object=%s source=%s confidence=%.2f",
        trace.id, object_id, source, confidence,
    )
    return trace


def get_decision_traces(object_id: Optional[int] = None, limit: int = 20) -> list:
    """Get decision traces, optionally filtered by object_id."""
    q = DecisionTrace.query.order_by(DecisionTrace.id.desc())
    if object_id is not None:
        q = q.filter(DecisionTrace.object_id == object_id)
    return [t.to_dict() for t in q.limit(limit).all()]