"""Learning — Consumes observations and identifies patterns to improve.

Learning should not directly rewrite critical policy. High-impact changes
require validation, evidence, and governance. The closed loop:
Knowledge → Reasoning → Planner → Workflow → Executor → Observer → Learning → Knowledge
"""
from typing import Optional
from datetime import datetime, timedelta
from app import db
from app.models import AIFeedback, KnowledgeEntry, ActivityLog, Entity


class LearningEngine:
    """Extracts patterns from observations and suggests improvements."""

    @staticmethod
    def extract_improvements(tenant_id: int) -> list[dict]:
        """Find patterns that suggest improvement opportunities."""
        improvements = []

        # 1. Knowledge gaps — frequently corrected topics
        corrections = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.correction.isnot(None),
        ).order_by(AIFeedback.created_at.desc()).limit(10).all()

        if corrections:
            topics = {}
            for c in corrections:
                topic = c.query[:60] if c.query else "unknown"
                topics[topic] = topics.get(topic, 0) + 1

            for topic, count in sorted(topics.items(), key=lambda x: -x[1])[:3]:
                improvements.append({
                    "type": "knowledge_gap",
                    "topic": topic,
                    "frequency": count,
                    "suggestion": f"Review and update knowledge about '{topic}'",
                    "confidence": min(count / 5, 1.0),
                })

        # 2. Stale workflow patterns
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        stale = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending", "proposal"]),
            Entity.updated_at < seven_days_ago,
        ).count()

        if stale > 5:
            improvements.append({
                "type": "workflow_bottleneck",
                "topic": "Stale leads",
                "frequency": stale,
                "suggestion": f"{stale} leads haven't been updated in 7+ days. Consider automating follow-up reminders.",
                "confidence": 0.8,
            })

        # 3. Response time patterns
        recent_activities = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.created_at >= seven_days_ago,
        ).count()

        if recent_activities < 5:
            improvements.append({
                "type": "engagement_drop",
                "topic": "Low team activity",
                "frequency": recent_activities,
                "suggestion": "Team activity is low this week. Check for blockers or training needs.",
                "confidence": 0.6,
            })

        return improvements

    @staticmethod
    def suggest_knowledge_update(tenant_id: int, topic: str, new_fact: str,
                                  source: str = "observation") -> KnowledgeEntry:
        """Suggest an update to the knowledge base from a learned pattern."""
        from app.shunya.knowledge import KnowledgePipeline
        return KnowledgePipeline.store_knowledge(
            tenant_id=tenant_id,
            question=topic,
            answer=new_fact,
            source=source,
            confidence=0.5,  # Low confidence — needs verification
        )