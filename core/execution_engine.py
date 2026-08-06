"""SHUNYA Execution Engine — Stream C.

Every recommendation should become executable.
Orchestrates action execution, automation, scheduling, browser execution,
email/calendar/communication execution, human approval workflows.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ExecutionAction:
    """A single executable action with metadata."""
    def __init__(self, action_id: str, name: str, description: str,
                 handler: Callable | None = None):
        self.action_id = action_id
        self.name = name
        self.description = description
        self.handler = handler
        self.created_at = _now_iso()


class ExecutionEngine:
    """Orchestrates execution of recommendations across all channels."""

    def __init__(self) -> None:
        self._actions: dict[str, ExecutionAction] = {}
        self._history: list[dict[str, Any]] = []
        self._schedules: list[dict[str, Any]] = []
        self._max_history = 1000

    # ── Action Registration ────────────────────────────────────────────

    def register(self, action_id: str, name: str, description: str,
                 handler: Callable | None = None) -> ExecutionAction:
        action = ExecutionAction(action_id, name, description, handler)
        self._actions[action_id] = action
        return action

    def list_actions(self) -> list[dict[str, Any]]:
        return [{"id": a.action_id, "name": a.name, "description": a.description}
                for a in self._actions.values()]

    # ── Execution ──────────────────────────────────────────────────────

    def execute(self, action_id: str, params: dict[str, Any] | None = None,
                channel: str = "direct") -> dict[str, Any]:
        action = self._actions.get(action_id)
        if not action:
            return {"success": False, "error": f"Unknown action: {action_id}"}

        result = {"action_id": action_id, "channel": channel,
                  "timestamp": _now_iso(), "success": True, "output": None}

        try:
            if action.handler:
                result["output"] = action.handler(**(params or {}))
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        self._history.append(result)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        return result

    # ── Scheduling ─────────────────────────────────────────────────────

    def schedule(self, action_id: str, cron: str, params: dict[str, Any] | None = None,
                 name: str = "") -> str:
        import uuid
        job_id = str(uuid.uuid4())
        self._schedules.append({
            "job_id": job_id, "action_id": action_id, "cron": cron,
            "params": params or {}, "name": name or action_id,
            "created_at": _now_iso(), "active": True,
        })
        return job_id

    def list_schedules(self) -> list[dict[str, Any]]:
        return list(self._schedules)

    def cancel_schedule(self, job_id: str) -> bool:
        for s in self._schedules:
            if s["job_id"] == job_id:
                s["active"] = False
                return True
        return False

    # ── History ────────────────────────────────────────────────────────

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    # ── Built-in Actions ───────────────────────────────────────────────

    def register_builtins(self) -> None:
        """Register system-provided execution actions."""
        self.register("system.notify", "Notify", "Send a notification",
                      handler=lambda title, message="": logger.info(f"Notification: {title} - {message}"))
        self.register("system.log", "Log", "Write to system log",
                      handler=lambda level, message: logger.log(
                          getattr(logging, level.upper(), logging.INFO), message))
        self.register("system.sleep", "Sleep", "Wait for specified seconds",
                      handler=lambda seconds: __import__('time').sleep(seconds))

    # ── Lifecycle ──────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        return {"status": "healthy", "actions": len(self._actions),
                "history": len(self._history), "schedules": len(self._schedules)}

    def shutdown(self) -> None:
        self._actions.clear()
        self._history.clear()
        self._schedules.clear()