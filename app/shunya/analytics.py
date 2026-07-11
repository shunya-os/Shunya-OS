"""Shunya Analytics — founder visibility: revenue, conversions, pipeline, team.

The founder should see: company health, revenue movement, high-value
opportunities, execution risk, approvals, and systemic bottlenecks.
Not a wall of charts — actionable intelligence.
"""
from typing import List, Dict
from datetime import datetime, timedelta, date
from app import db
from app.models import Entity, EntityDefinition, ActivityLog, Payment, Invoice, TeamMember, Notification, AIFeedback


class AnalyticsEngine:
    """Business intelligence engine for founder/manager views."""

    @staticmethod
    def get_overview(tenant_id: int, days: int = 30) -> Dict:
        """Get high-level company health overview."""
        now = datetime.utcnow()
        since = now - timedelta(days=days)

        # Total entities
        total_entities = Entity.query.filter_by(
            tenant_id=tenant_id, is_archived=False
        ).count()

        # Active (non-terminal status)
        active_entities = Entity.query.filter_by(
            tenant_id=tenant_id, is_archived=False
        ).filter(~Entity.status.in_(["completed", "cancelled", "lost", "recovered"])).count()

        # Recently created
        new_this_period = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.created_at >= since,
        ).count()

        # Revenue
        total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.tenant_id == tenant_id,
            Payment.status == "completed",
        ).scalar() or 0

        period_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.tenant_id == tenant_id,
            Payment.status == "completed",
            Payment.paid_at >= since,
        ).scalar() or 0

        # Pipeline by status per entity type
        pipeline = {}
        definitions = EntityDefinition.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        for d in definitions:
            status_counts = {}
            for status in (d.statuses or []):
                count = Entity.query.filter_by(
                    tenant_id=tenant_id, definition_id=d.id, status=status, is_archived=False
                ).count()
                if count > 0:
                    status_counts[status] = count
            if status_counts:
                pipeline[d.label] = {
                    "icon": d.icon,
                    "statuses": status_counts,
                    "total": sum(status_counts.values()),
                }

        # Team stats
        team_count = TeamMember.query.filter_by(tenant_id=tenant_id, is_active=True).count()

        # Activity trend
        activity_counts = []
        for i in range(7):
            day = now - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day)
            day_end = day_start + timedelta(days=1)
            count = ActivityLog.query.filter(
                ActivityLog.tenant_id == tenant_id,
                ActivityLog.created_at >= day_start,
                ActivityLog.created_at < day_end,
            ).count()
            activity_counts.append({"date": day_start.strftime("%a"), "count": count})

        # AI accuracy
        feedback_total = db.session.query(AIFeedback).filter_by(tenant_id=tenant_id).count()
        feedback_pos = db.session.query(AIFeedback).filter_by(tenant_id=tenant_id, rating=1).count()
        accuracy = round(feedback_pos / feedback_total, 2) if feedback_total > 0 else 0

        return {
            "period": f"Last {days} days",
            "total_entities": total_entities,
            "active_entities": active_entities,
            "new_this_period": new_this_period,
            "total_revenue": float(total_revenue),
            "period_revenue": float(period_revenue),
            "team_count": team_count,
            "pipeline": pipeline,
            "activity_trend": activity_counts,
            "ai_accuracy": accuracy,
            "ai_feedback_count": feedback_total,
        }

    @staticmethod
    def get_entity_analytics(tenant_id: int, entity_type: str) -> Dict:
        """Get detailed analytics for a specific entity type."""
        definition = EntityDefinition.query.filter_by(
            tenant_id=tenant_id, type=entity_type, is_active=True
        ).first()
        if not definition:
            return {"error": "Entity type not found"}

        entities = Entity.query.filter_by(
            tenant_id=tenant_id, definition_id=definition.id, is_archived=False
        ).all()

        total = len(entities)
        status_counts = {}
        for s in (definition.statuses or []):
            status_counts[s] = sum(1 for e in entities if e.status == s)

        # Average time in each status
        status_times = {}
        for e in entities:
            if e.created_at:
                days = (datetime.utcnow() - e.created_at).days
                st = e.status
                status_times[st] = status_times.get(st, 0) + days

        avg_days_per_status = {
            s: round(status_times[s] / status_counts[s], 1)
            for s in status_counts if status_counts[s] > 0 and s in status_times
        }

        return {
            "entity_type": definition.label,
            "icon": definition.icon,
            "total": total,
            "status_counts": status_counts,
            "avg_days_per_status": avg_days_per_status,
            "layout": definition.layout,
        }

    @staticmethod
    def get_founder_insights(tenant_id: int) -> List[Dict]:
        """Generate actionable insights for the founder."""
        insights = []

        # High-value entities needing attention
        high_value = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "proposal", "negotiation"]),
        ).order_by(Entity.created_at.desc()).limit(5).all()

        for e in high_value:
            budget = e.data.get("budget", 0)
            if budget and float(budget) > 100000:
                days_old = (datetime.utcnow() - e.created_at).days if e.created_at else 0
                insights.append({
                    "type": "high_value_opportunity",
                    "icon": "💰",
                    "title": f"High-value {e.definition.label if e.definition else 'entity'}",
                    "description": f"{e.display_name} — ₹{float(budget):,.0f}, {days_old} days old",
                    "priority": "high" if days_old < 2 else "medium",
                    "action": f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}",
                })

        # Stuck workflows
        stuck_count = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending"]),
            Entity.created_at < datetime.utcnow() - timedelta(days=7),
        ).count()

        if stuck_count > 3:
            insights.append({
                "type": "stuck_workflows",
                "icon": "⛔",
                "title": f"{stuck_count} stuck workflows",
                "description": "Entities stuck in initial status for 7+ days",
                "priority": "high",
                "action": "/entities/lead?status=new",
            })

        # Low activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_activity = ActivityLog.query.filter(
            ActivityLog.tenant_id == tenant_id,
            ActivityLog.created_at >= week_ago,
        ).count()

        if week_activity < 10:
            insights.append({
                "type": "low_activity",
                "icon": "📉",
                "title": "Low team activity",
                "description": f"Only {week_activity} actions logged this week",
                "priority": "medium",
                "action": "/",
            })

        return insights[:10]