"""Tool Execution Layer — unified interface for executing actions.

Lifecycle contract (intentional shared-singleton state)
------------------------------------------------------
``ToolExecutionLayer`` is instantiated exactly once, as
``IntelligenceRuntime.executor`` on the ``get_runtime()`` singleton
(``core.intelligence_runtime.runtime``). Handlers are ADDED to that single
instance, never removed, from two deterministic sources:

1. ``integration.ensure_runtime()`` wires the base action handlers
   (``answer``, ``clarify``, ``execute``, ``automate``). It is guarded by a
   module-level ``_initialized`` flag, so it wires at most once per process.
2. ``app.ai.tool_registry.register_tool_handlers()`` wires the business
   handlers (``create_customer``, ``create_supplier``, ``search_objects``)
   during application initialisation.

Consequence for callers: ``ActionType.EXECUTE`` (value ``"execute"``) IS a
registered action once ``ensure_runtime()`` has run — it is NOT an
"unregistered" key. Code that needs to observe the registry must use the
public introspection API (``registered_actions`` / ``is_registered``) instead
of reaching into ``_handlers``.

Because registration is process-global and monotonic, any assertion about
which keys are registered MUST either (a) call ``ensure_runtime()`` itself so
the state is pinned, or (b) use a fresh, isolated ``ToolExecutionLayer``. Do
not assume a key is absent merely because this layer has not wired it.
"""

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

    # ── Public introspection (no private access required) ────────────────

    def registered_actions(self) -> list[str]:
        """Return the sorted action keys that currently have a handler."""
        return sorted(self._handlers.keys())

    def is_registered(self, action_key: str) -> bool:
        """Whether a handler exists for ``action_key``."""
        return action_key in self._handlers

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