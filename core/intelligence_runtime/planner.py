"""Action Planner — decides whether to answer, ask, execute, automate, or defer."""

from __future__ import annotations

from .types import ActionType, IntelligenceResponse, PlanStep, UserIntent


class ActionPlanner:
    """Decides the best course of action from reasoning results."""

    def decide(self, intent: UserIntent, response: IntelligenceResponse) -> list[PlanStep]:
        """Determine the action plan based on intent and reasoning."""
        if response.requires_clarification:
            return [PlanStep(action=ActionType.CLARIFY, description=response.clarification_question)]

        if response.actions:
            return response.actions

        # Default: answer
        return [PlanStep(action=ActionType.ANSWER, description="Provide information")]

    def should_execute(self, intent: UserIntent) -> bool:
        """Determine if a command should be executed immediately."""
        return (intent.category.value == "command"
                and intent.confidence >= 0.7
                and intent.urgency in ("critical", "high", "normal"))

    def should_defer(self, intent: UserIntent, confidence: float) -> bool:
        """Determine if we should defer to a human."""
        return (intent.category.value == "unknown"
                or confidence < 0.3
                or intent.ambiguity > 0.7)