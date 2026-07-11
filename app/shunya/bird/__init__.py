"""Bird — Shunya's AI Assistant interaction layer.

Bird is the assistant through which Shunya's intelligence becomes approachable.
It should feel caring, precise, context-aware, and grounded in company knowledge.

Interaction pattern: understand → clarify → explain → recommend → guide → act
"""
from typing import Optional, List
from app.shunya.foundation import Result, NextAction, Priority
from app.shunya.knowledge import KnowledgePipeline
from app.shunya.next_best_action import NextBestActionEngine


class Bird:
    """The AI Assistant interface — routes intent to the right Shunya layer."""

    def __init__(self, tenant_id: int, user_id: int, user_role: str = "agent",
                 user_name: str = ""):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.user_role = user_role
        self.user_name = user_name

    def greet(self) -> dict:
        """Personalized greeting with context."""
        from datetime import datetime
        hour = datetime.utcnow().hour

        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        from app.models import Entity
        urgent_count = Entity.query.filter_by(
            tenant_id=self.tenant_id, is_archived=False
        ).filter(Entity.status.in_(["new", "pending"])).count()

        return {
            "greeting": f"{greeting}, {self.user_name}!",
            "icon": "🧠",
            "message": f"You have {urgent_count} items needing attention." if urgent_count > 0
                       else "Ready to make today productive?",
            "suggestions": self._quick_suggestions(),
        }

    def _quick_suggestions(self) -> list:
        """Quick action suggestions for the greeting."""
        from app.models import EntityDefinition, Entity
        suggestions = []
        defs = EntityDefinition.query.filter_by(
            tenant_id=self.tenant_id, is_active=True
        ).limit(4).all()
        for d in defs:
            count = Entity.query.filter_by(
                tenant_id=self.tenant_id, definition_id=d.id, is_archived=False
            ).count()
            suggestion = f"Review {d.label_plural or d.label} ({count})"
            suggestions.append({
                "icon": d.icon,
                "text": suggestion,
                "action": f"/entities/{d.type}",
            })
        return suggestions

    def handle_query(self, query: str) -> dict:
        """Process a natural language query through the Shunya layers."""
        # 1. Search internal knowledge
        knowledge = KnowledgePipeline.search(query, self.tenant_id)

        context_data = None
        if knowledge["has_internal_data"]:
            context_data = knowledge

        # 2. Get next best action context
        nba = NextBestActionEngine.get_for_user(
            self.tenant_id, self.user_id, self.user_role
        )

        return {
            "query": query,
            "context": context_data,
            "next_actions": nba[:3] if nba else [],
            "response_type": "knowledge" if knowledge["has_internal_data"] else "needs_web_search",
        }

    def explain(self, action: str, details: dict) -> dict:
        """Explain a recommendation with trade-offs and reasoning."""
        explanation = {
            "observation": details.get("observation", ""),
            "trade_offs": details.get("trade_offs", []),
            "recommendation": details.get("recommendation", ""),
            "reason": details.get("reason", ""),
            "next_action": details.get("next_action", ""),
            "confidence": details.get("confidence", 0.5),
        }
        return explanation

    def format_message(self, template: str, **kwargs) -> str:
        """Format a message following the Bird interaction pattern."""
        templates = {
            "attention": (
                "🧠 **{title}**\n\n"
                "What I see: {observation}\n"
                "Why it matters: {reason}\n"
                "What I recommend: {recommendation}\n"
                "Next step: {next_action}"
            ),
            "correction": (
                "📝 Noted! I've updated my understanding.\n\n"
                "{detail}\n\n"
                "I'll get this right going forward."
            ),
            "decision": (
                "✅ **{title}**\n\n"
                "Here's what I did:\n{summary}\n\n"
                "What happens next: {next_step}\n"
                "Anything else?"
            ),
        }
        formatter = templates.get(template, templates["attention"])
        return formatter.format(**kwargs)