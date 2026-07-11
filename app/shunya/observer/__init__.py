"""Shunya Observer — records outcomes and compares intention vs reality.

Executor reports what it attempted.
Observer records what actually happened.
These are different.

Do not treat "API returned 200" as "Business outcome succeeded."
"""
import json, logging
from datetime import datetime
from typing import Optional, Dict, Any
from app import db
from app.models import Entity, ActivityLog, KnowledgeEntry

logger = logging.getLogger("app.shunya.observer")


class Observer:
    """Records what happened and compares against what was intended."""

    OBSERVATION_TYPES = [
        "state_changed",
        "message_delivered",
        "user_responded",
        "deadline_missed",
        "transaction_completed",
        "transaction_failed",
        "customer_churned",
        "project_delayed",
        "employee_corrected_ai",
        "approval_rejected",
        "recommendation_ignored",
        "target_achieved",
        "anomaly_detected",
    ]

    @staticmethod
    def record(tenant_id, entity_id, observation_type: str,
               summary: str, detail: dict = None,
               user_id=None,
               expected_outcome: str = None,
               actual_outcome: str = None) -> dict:
        """Record an observation with outcome comparison."""
        detail = detail or {}
        
        # Log observation
        activity = ActivityLog(
            tenant_id=tenant_id,
            entity_id=entity_id,
            user_id=user_id,
            action=f"observed.{observation_type}",
            detail=json.dumps({
                "observation_type": observation_type,
                "summary": summary[:500],
                "expected": expected_outcome,
                "actual": actual_outcome,
                "metadata": detail,
            }),
        )
        db.session.add(activity)
        db.session.flush()
        
        # Compare outcome if both provided
        outcome_match = None
        if expected_outcome and actual_outcome:
            outcome_match = Observer._compare_outcomes(expected_outcome, actual_outcome)
        
        db.session.commit()
        
        return {
            "observation_id": activity.id,
            "observation_type": observation_type,
            "summary": summary,
            "outcome_match": outcome_match,
        }

    @staticmethod
    def _compare_outcomes(expected: str, actual: str) -> dict:
        """Compare intended vs actual outcome to identify learning opportunities."""
        expected_lower = expected.lower().strip()
        actual_lower = actual.lower().strip()
        
        # Simple outcome comparison
        if expected_lower == actual_lower:
            return {
                "match": True,
                "confidence": "high",
                "finding": "Outcome matched expectation",
            }
        
        # Check for keywords
        positive_words = ["success", "completed", "approved", "converted", "achieved"]
        negative_words = ["failed", "rejected", "cancelled", "lost", "missed"]
        
        expected_is_positive = any(w in expected_lower for w in positive_words)
        actual_is_positive = any(w in actual_lower for w in positive_words)
        
        if expected_is_positive == actual_is_positive:
            return {
                "match": True,
                "confidence": "medium",
                "finding": "Directional outcome matched",
            }
        
        return {
            "match": False,
            "confidence": "low",
            "finding": "Outcome differed from expectation — learning opportunity",
            "expected": expected,
            "actual": actual,
        }

    @staticmethod
    def record_state_change(entity: Entity, from_status: str, to_status: str,
                             reason: Optional[str] = None) -> dict:
        """Convenience: record a status transition observation."""
        return Observer.record(
            tenant_id=entity.tenant_id,
            entity_id=entity.id,
            observation_type="state_changed",
            summary=f"Status: {from_status} → {to_status}",
            detail={"from": from_status, "to": to_status, "reason": reason},
            expected_outcome=f"Move to {to_status}",
            actual_outcome=to_status,
        )

    @staticmethod
    def record_deadline(entity_id: int, tenant_id: int, deadline: str,
                         task_description: str, was_met: bool) -> dict:
        """Record whether a deadline was met or missed."""
        return Observer.record(
            tenant_id=tenant_id,
            entity_id=entity_id,
            observation_type="deadline_missed" if not was_met else "target_achieved",
            summary=f"Deadline {'met' if was_met else 'missed'}: {task_description}",
            detail={"deadline": deadline, "was_met": was_met},
            expected_outcome="On time" if was_met else "Deadline missed",
            actual_outcome="Completed" if was_met else "Overdue",
        )

    @staticmethod
    def get_observations(tenant_id: int, entity_id: Optional[int] = None,
                          limit: int = 50) -> list:
        """Get observations with outcome comparisons."""
        query = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.action.like("observed.%"),
        )
        if entity_id:
            query = query.filter(ActivityLog.entity_id == entity_id)
        
        logs = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
        
        return [{
            "id": log.id,
            "type": log.action.replace("observed.", ""),
            "summary": log.detail,
            "entity_id": log.entity_id,
            "user_id": log.user_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        } for log in logs]

    @staticmethod
    def compare_outcome(tenant_id: int, entity_id: int) -> dict:
        """Get the full outcome comparison for an entity."""
        entity = db.session.get(Entity, entity_id)
        if not entity:
            return {"error": "Entity not found"}
        
        observations = Observer.get_observations(tenant_id, entity_id, limit=10)
        
        # Gather all status changes
        status_changes = []
        for obs in observations:
            try:
                detail = json.loads(obs["summary"])
                if detail.get("observation_type") == "status_changed":
                    status_changes.append(detail)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            "entity_id": entity_id,
            "entity_code": entity.code,
            "current_status": entity.status,
            "total_observations": len(observations),
            "status_history": status_changes,
            "recent_observations": observations[:5],
        }