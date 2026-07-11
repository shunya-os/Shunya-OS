"""Shunya OS — Proactive Intelligence Engine.

The AI doesn't wait to be asked. It detects patterns, suggests actions,
and identifies opportunities proactively.
"""
from typing import Optional
from datetime import datetime, timedelta
from flask import g
from app import db
from app.models import Entity, EntityDefinition, ActivityLog, KnowledgeEntry, AIFeedback


class ProactiveEngine:
    """Scans for patterns and generates proactive suggestions."""

    @staticmethod
    def get_suggestions(tenant_id: int, user_id: int, role: str = "agent") -> list[dict]:
        """Get proactive suggestions for a user based on current data."""
        suggestions = []

        # 1. Stale entities (no activity in 5+ days)
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        stale_entities = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["new", "pending", "proposal", "negotiation"]),
            Entity.updated_at < five_days_ago,
        ).limit(5).all()

        for e in stale_entities:
            def_label = e.definition.label if e.definition else "Record"
            suggestions.append({
                "type": "stale_entity",
                "icon": "⏰",
                "title": f"{def_label} needs attention",
                "message": f"{e.display_name} hasn't been updated in 5+ days. Status: {e.status}",
                "action": f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}",
                "priority": "medium",
            })

        # 2. High conversion opportunities (leads with high budget, no activity)
        if role in ("admin", "manager"):
            high_value = Entity.query.filter(
                Entity.tenant_id == tenant_id,
                Entity.is_archived == False,
                Entity.status.in_(["new", "proposal"]),
            ).order_by(Entity.created_at.desc()).limit(5).all()

            for e in high_value:
                budget = e.data.get("budget", 0)
                if budget and float(budget) > 100000:
                    suggestions.append({
                        "type": "high_value",
                        "icon": "💰",
                        "title": "High-value opportunity",
                        "message": f"{e.display_name} — Budget: ₹{float(budget):,.0f}",
                        "action": f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}",
                        "priority": "high",
                    })

        # 3. Recently resolved (ready for follow-up)
        resolved = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status.in_(["completed", "booked", "recovered", "delivered"]),
            Entity.updated_at >= datetime.utcnow() - timedelta(days=2),
        ).limit(3).all()

        for e in resolved:
            suggestions.append({
                "type": "recently_resolved",
                "icon": "✅",
                "title": "Recently completed",
                "message": f"{e.display_name} was marked as {e.status}. Follow up?",
                "action": f"/entities/{e.definition.type if e.definition else 'entity'}/{e.id}",
                "priority": "low",
            })

        # 4. Learning gaps (frequently corrected topics)
        corrections = db.session.query(AIFeedback).filter(
            AIFeedback.tenant_id == tenant_id,
            AIFeedback.correction.isnot(None),
        ).order_by(AIFeedback.created_at.desc()).limit(5).all()

        if corrections:
            topics = list(set(c.query[:60] for c in corrections))
            if topics:
                suggestions.append({
                    "type": "learning_gap",
                    "icon": "🧠",
                    "title": "AI knowledge gaps detected",
                    "message": f"Topics needing improvement: {', '.join(topics[:3])}",
                    "action": "/settings",
                    "priority": "low",
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 3))

        return suggestions[:10]

    @staticmethod
    def get_welcome_message(tenant_id: int, user_name: str) -> str:
        """Generate a personalized welcome message."""
        hour = datetime.utcnow().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        # Check for urgent items
        urgent_count = Entity.query.filter(
            Entity.tenant_id == tenant_id,
            Entity.is_archived == False,
            Entity.status == "new",
        ).count()

        if urgent_count > 0:
            return f"{greeting}, {user_name}! ☀️ You have {urgent_count} items needing attention."
        else:
            return f"{greeting}, {user_name}! ☀️ Ready to make today productive?"