"""Tool Execution Layer — unified interface for executing actions."""

from __future__ import annotations

from typing import Any, Callable

from .types import ActionType, PlanStep


class ToolExecutionLayer:
    """Executes actions through registered tool handlers."""

    def __init__(self):
        self._handlers: dict[str, Callable] = {}

    def register(self, action_key: str, handler: Callable) -> None:
        """Register a handler for a specific action."""
        self._handlers[action_key] = handler

    def execute(self, step: PlanStep) -> dict[str, Any]:
        """Execute a plan step through its registered handler."""
        action_key = step.action.value
        if action_key in self._handlers:
            try:
                result = self._handlers[action_key](step.parameters)
                return {"status": "success", "result": result, "action": action_key}
            except Exception as e:
                return {"status": "error", "error": str(e), "action": action_key}
        return {"status": "skipped", "reason": f"No handler for {action_key}", "action": action_key}

    def execute_all(self, steps: list[PlanStep]) -> list[dict[str, Any]]:
        """Execute multiple plan steps."""
        results = []
        for step in steps:
            result = self.execute(step)
            results.append(result)
        return results

    def clear(self) -> None:
        self._handlers.clear()