"""Observer — Records what happened and compares outcome with expected outcome.

Every execution creates an observation. Observations feed Learning.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from app import db
from app.models import ActivityLog, Entity


class Observer:
    """Records outcomes and compares real-world vs expected results."""

    @staticmethod
    def record(tenant_id: int, entity_id: Optional[int], user_id: Optional[int],
               action: str, detail: str = "", governance_level: str = "auto",
               expected_outcome: str = "", actual_outcome: str = "",
               metadata: dict = None) -> ActivityLog:
        """Record an action and its outcome."""
        log = ActivityLog(
            tenant_id=tenant_id,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            detail=detail[:500],
            governance_level=governance_level,
            metadata_json=metadata or {},
        )
        db.session.add(log)
        db.session.commit()

        # If expected vs actual provided, flag for learning
        if expected_outcome and actual_outcome and expected_outcome != actual_outcome:
            _flag_divergence(tenant_id, action, expected_outcome, actual_outcome)

        return log

    @staticmethod
    def get_history(tenant_id: int, entity_id: Optional[int] = None,
                    limit: int = 50) -> list:
        """Get observation history for context."""
        query = ActivityLog.query.filter_by(tenant_id=tenant_id)
        if entity_id:
            query = query.filter_by(entity_id=entity_id)
        logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
        return [{
            "id": l.id, "action": l.action, "detail": l.detail,
            "governance_level": l.governance_level,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        } for l in logs]


def _flag_divergence(tenant_id: int, action: str, expected: str, actual: str):
    """Log an expectation gap for the Learning layer to process."""
    from app.models import AIFeedback
    fb = AIFeedback(
        tenant_id=tenant_id,
        query=f"Expected: {expected}",
        response=f"Actual: {actual}",
        rating=-1,
        correction=f"Divergence detected: {action} — expected '{expected}', got '{actual}'",
    )
    db.session.add(fb)
    db.session.commit()

class PatternDetector:
    """Identifies patterns from observations."""

    @staticmethod
    def detect_frequent_actions(tenant_id: int, limit: int = 10) -> list:
        """Find the most common action types."""
        from sqlalchemy import func
        results = db.session.query(
            ActivityLog.action, func.count(ActivityLog.id).label("count")
        ).filter(
            ActivityLog.tenant_id == tenant_id
        ).group_by(ActivityLog.action).order_by(func.count(ActivityLog.id).desc()).limit(limit).all()
        return [{"action": r[0], "count": r[1]} for r in results]

    @staticmethod
    def detect_timing_patterns(tenant_id: int) -> list:
        """Detect how long entities typically spend in each status."""
        return [{"pattern": "Status timing analysis", "detail": "Available per entity type"}]