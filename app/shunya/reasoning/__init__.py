"""Reasoning — Consumes goals, facts, and context to produce decisions/recommendations.

Reasoning does NOT execute work. It produces:
- Outcome: decision or recommendation
- Confidence: how sure it is
- Evidence: what facts support this
- Explanation: why this makes sense
"""
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app import db
from app.models import Entity, EntityDefinition, KnowledgeEntry, ActivityLog


@dataclass
class Recommendation:
    """A reasoned recommendation with evidence."""
    title: str
    decision: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    explanation: str = ""
    trade_offs: List[str] = field(default_factory=list)
    alternatives: List[dict] = field(default_factory=list)
    next_action: str = ""


class ReasoningEngine:
    """Produces decisions and recommendations from context."""

    @staticmethod
    def recommend_next_action(tenant_id: int, entity_id: int) -> Recommendation:
        """Recommend the next best action for a specific entity."""
        entity = db.session.get(Entity, entity_id)
        if not entity:
            return Recommendation(title="Entity not found", decision="", confidence=0)

        definition = entity.definition
        entity_type = definition.label if definition else "Record"
        status = entity.status
        statuses = definition.statuses if definition else []

        # Find current position in the status flow
        current_idx = statuses.index(status) if status in statuses else -1
        next_status = statuses[current_idx + 1] if current_idx >= 0 and current_idx < len(statuses) - 1 else None

        evidence = []
        trade_offs = []

        # Check how long entity has been in current status
        days_in_status = 0
        if entity.updated_at:
            days_in_status = (datetime.utcnow() - entity.updated_at).days

        if days_in_status > 3:
            evidence.append(f"Has been in '{status}' for {days_in_status} days")
            trade_offs.append("Risk of losing momentum if not progressed")

        # Check budget
        budget = entity.data.get("budget", 0)
        if budget and float(budget) > 0:
            evidence.append(f"Budget: ₹{float(budget):,.0f}")
            if float(budget) > 200000:
                trade_offs.append("High-value — may need senior approval")

        # Check recent activity
        recent_activities = ActivityLog.query.filter_by(
            tenant_id=tenant_id, entity_id=entity_id
        ).count()

        if recent_activities == 0:
            evidence.append("No activity logged yet")
        else:
            evidence.append(f"{recent_activities} activities logged")

        # Build recommendation
        if next_status:
            decision = f"Move from '{status}' to '{next_status}'"
            explanation = f"This {entity_type} is ready to progress to the next stage."
            next_action_text = f"Update status to {next_status}"
        elif days_in_status > 5:
            decision = f"Review {entity_type} — no movement in {days_in_status} days"
            explanation = f"This {entity_type} needs attention to prevent it from going cold."
            next_action_text = "Follow up with the customer"
        else:
            decision = "Continue monitoring"
            explanation = f"No action needed at this time."
            next_action_text = ""

        return Recommendation(
            title=f"Next step for {entity.display_name}",
            decision=decision,
            confidence=0.8 if next_status else 0.5,
            evidence=evidence,
            explanation=explanation,
            trade_offs=trade_offs,
            next_action=next_action_text,
        )

    @staticmethod
    def compare_options(tenant_id: int, entity_type: str,
                        entity_ids: List[int]) -> dict:
        """Compare multiple entities (e.g., destinations, hotels) with trade-offs."""
        entities = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.id.in_(entity_ids),
        ).all()

        comparison = []
        for e in entities:
            comparison.append({
                "name": e.display_name,
                "data": e.data,
                "status": e.status,
            })

        return {
            "comparison": comparison,
            "recommendation": "Compare based on your priorities",
            "trade_offs": "Consider budget, timeline, and preferences",
        }