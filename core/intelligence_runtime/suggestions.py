"""Suggestions Engine — proactively identifies automations, reminders, and improvements."""

from __future__ import annotations

from typing import Any

from .types import ContextFrame, UniversalSuggestion


class SuggestionsEngine:
    """Generates proactive suggestions based on context and usage patterns."""

    def suggest(self, context: ContextFrame) -> list[UniversalSuggestion]:
        """Generate context-aware suggestions."""
        suggestions = []

        # 1. Based on active module
        if context.active_module:
            suggestions.append(UniversalSuggestion(
                key=f"explore_{context.active_module}",
                title=f"Explore {context.active_module.title()}",
                description=f"Would you like me to show you around {context.active_module}?",
                suggestion_type="action",
                confidence=0.5,
            ))

        # 2. Based on active object
        if context.active_object_type and context.active_object_id:
            suggestions.append(UniversalSuggestion(
                key="object_actions",
                title=f"Available actions for this {context.active_object_type}",
                description=f"I can help you update, view related items, or create reports for this {context.active_object_type}.",
                suggestion_type="action",
                confidence=0.6,
            ))

        # 3. Recent task context
        if context.current_task:
            suggestions.append(UniversalSuggestion(
                key="continue_task",
                title=f"Continue: {context.current_task}",
                description="You were working on this. Would you like to continue?",
                suggestion_type="reminder",
                confidence=0.7,
            ))

        # 4. General suggestions
        if not context.active_workspace:
            suggestions.append(UniversalSuggestion(
                key="start_exploring",
                title="Explore your workspace",
                description="You can ask me about your modules, search for objects, or create new records.",
                suggestion_type="action",
                confidence=0.4,
            ))

        return suggestions[:5]

    def suggest_for_query(self, query: str, context: ContextFrame) -> list[UniversalSuggestion]:
        """Generate suggestions relevant to a user query."""
        suggestions = self.suggest(context)
        q_lower = query.lower()

        # Boost relevance based on query keywords
        for s in suggestions:
            if any(word in q_lower for word in s.title.lower().split()):
                s.confidence = min(s.confidence + 0.2, 0.95)

        suggestions.sort(key=lambda s: -s.confidence)
        return suggestions[:5]