"""SHUNYA Phase A1 — Space Command Framework.

Commands are Space-centric. They operate on the current Space.
Commands are dynamically available based on Space type and context.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from app.space.models import UniversalSpace


# =========================================================================
# Command Definition
# =========================================================================


class SpaceCommand:
    """A command that operates on the current Space.

    Every command has:
        - name: The command identifier (e.g., "summarize")
        - label: Human-readable label (e.g., "Summarize")
        - description: What the command does
        - handler: The function that executes the command
        - applies_to: List of entity types this command applies to
                      (empty = applies to all)
    """

    def __init__(self, name: str, label: str, description: str,
                 handler: Callable,
                 applies_to: Optional[List[str]] = None,
                 icon: str = "⚡"):
        self.name = name
        self.label = label
        self.description = description
        self.handler = handler
        self.applies_to = applies_to or []
        self.icon = icon

    def applies(self, space: UniversalSpace) -> bool:
        if not self.applies_to:
            return True
        return space.entity_type in self.applies_to

    def execute(self, space: UniversalSpace,
                params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.handler(space, params or {})

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "icon": self.icon,
            "applies_to": self.applies_to,
        }


# =========================================================================
# Built-in Command Handlers
# =========================================================================


def _summarize(space: UniversalSpace, params: dict) -> dict:
    """Summarize the current Space."""
    return {
        "command": "summarize",
        "space_id": space.space_id,
        "name": space.name,
        "entity_type": space.entity_type,
        "summary": (
            f"{space.name} is a {space.entity_type} Space "
            f"with {len(space.relationships)} relationships, "
            f"{len(space.timeline)} timeline events, "
            f"{len(space.knowledge)} knowledge items, "
            f"and {len(space.plans)} plans."
        ),
        "ai_understanding": space.ai_understanding.to_dict(),
    }


def _explain(space: UniversalSpace, params: dict) -> dict:
    """Explain what this Space is about."""
    return {
        "command": "explain",
        "space_id": space.space_id,
        "name": space.name,
        "entity_type": space.entity_type,
        "explanation": (
            f"This Space represents '{space.name}', "
            f"an entity of type '{space.entity_type}' in the Business Graph."
            f" It is backed by the universal SHUNYA runtimes."
        ),
    }


def _create_plan(space: UniversalSpace, params: dict) -> dict:
    """Create a plan in this Space."""
    return {
        "command": "create_plan",
        "space_id": space.space_id,
        "plan": {
            "title": params.get("title", f"Plan for {space.name}"),
            "description": params.get("description", ""),
            "state": "proposed",
        },
        "message": f"Plan created for {space.name}",
    }


def _delegate(space: UniversalSpace, params: dict) -> dict:
    """Delegate an action to someone."""
    return {
        "command": "delegate",
        "space_id": space.space_id,
        "task": params.get("task", ""),
        "assignee": params.get("assignee", ""),
        "message": f"Task delegated to {params.get('assignee', 'unknown')}",
    }


def _compare(space: UniversalSpace, params: dict) -> dict:
    """Compare this Space with another."""
    return {
        "command": "compare",
        "space_id": space.space_id,
        "with": params.get("with", ""),
        "message": "Comparison not yet implemented",
    }


def _forecast(space: UniversalSpace, params: dict) -> dict:
    """Forecast outcomes for this Space."""
    return {
        "command": "forecast",
        "space_id": space.space_id,
        "horizon": params.get("horizon", "30d"),
        "message": "Forecast not yet implemented",
    }


def _generate(space: UniversalSpace, params: dict) -> dict:
    """Generate content related to this Space."""
    return {
        "command": "generate",
        "space_id": space.space_id,
        "content_type": params.get("content_type", "report"),
        "message": f"Generated {params.get('content_type', 'report')} for {space.name}",
    }


def _review(space: UniversalSpace, params: dict) -> dict:
    """Review the current state of this Space."""
    return {
        "command": "review",
        "space_id": space.space_id,
        "focus": params.get("focus", "all"),
        "state_summary": space.to_summary(),
    }


def _approve(space: UniversalSpace, params: dict) -> dict:
    """Approve a pending item in this Space."""
    return {
        "command": "approve",
        "space_id": space.space_id,
        "item_id": params.get("item_id", ""),
        "message": f"Item {params.get('item_id', 'unknown')} approved",
    }


def _schedule(space: UniversalSpace, params: dict) -> dict:
    """Schedule an action or event in this Space."""
    return {
        "command": "schedule",
        "space_id": space.space_id,
        "action": params.get("action", ""),
        "when": params.get("when", ""),
        "message": f"Scheduled '{params.get('action', '')}' for {params.get('when', '')}",
    }


def _analyze(space: UniversalSpace, params: dict) -> dict:
    """Analyze data in this Space."""
    return {
        "command": "analyze",
        "space_id": space.space_id,
        "dimension": params.get("dimension", "general"),
        "metrics": [m.to_dict() for m in space.metrics],
    }


def _find_risks(space: UniversalSpace, params: dict) -> dict:
    """Find risks in this Space."""
    return {
        "command": "find_risks",
        "space_id": space.space_id,
        "risks": space.ai_understanding.current_risks,
        "message": f"Found {len(space.ai_understanding.current_risks)} risks",
    }


def _show_dependencies(space: UniversalSpace, params: dict) -> dict:
    """Show dependencies of this Space."""
    return {
        "command": "show_dependencies",
        "space_id": space.space_id,
        "dependencies": [
            r.to_dict() for r in space.relationships
        ],
        "message": f"Showing {len(space.relationships)} dependencies",
    }


def _predict_outcome(space: UniversalSpace, params: dict) -> dict:
    """Predict outcome for this Space."""
    return {
        "command": "predict_outcome",
        "space_id": space.space_id,
        "scenario": params.get("scenario", "default"),
        "message": "Prediction not yet implemented",
    }


# =========================================================================
# Command Registry
# =========================================================================

BUILTIN_COMMANDS: Dict[str, SpaceCommand] = {
    "summarize": SpaceCommand(
        "summarize", "Summarize", "Summarize this Space", _summarize, icon="📝",
    ),
    "explain": SpaceCommand(
        "explain", "Explain", "Explain what this Space is about", _explain, icon="💡",
    ),
    "create_plan": SpaceCommand(
        "create_plan", "Create Plan", "Create a plan in this Space",
        _create_plan, icon="🎯",
    ),
    "delegate": SpaceCommand(
        "delegate", "Delegate", "Delegate an action", _delegate, icon="👤",
    ),
    "compare": SpaceCommand(
        "compare", "Compare", "Compare with another Space", _compare, icon="🔍",
    ),
    "forecast": SpaceCommand(
        "forecast", "Forecast", "Forecast outcomes", _forecast, icon="🔮",
    ),
    "generate": SpaceCommand(
        "generate", "Generate", "Generate content", _generate, icon="✨",
    ),
    "review": SpaceCommand(
        "review", "Review", "Review current state", _review, icon="📋",
    ),
    "approve": SpaceCommand(
        "approve", "Approve", "Approve a pending item", _approve, icon="✅",
    ),
    "schedule": SpaceCommand(
        "schedule", "Schedule", "Schedule an action", _schedule, icon="📅",
    ),
    "analyze": SpaceCommand(
        "analyze", "Analyze", "Analyze data", _analyze, icon="📊",
    ),
    "find_risks": SpaceCommand(
        "find_risks", "Find Risks", "Find risks", _find_risks, icon="⚠️",
    ),
    "show_dependencies": SpaceCommand(
        "show_dependencies", "Show Dependencies",
        "Show dependencies", _show_dependencies, icon="🔗",
    ),
    "predict_outcome": SpaceCommand(
        "predict_outcome", "Predict Outcome",
        "Predict outcome", _predict_outcome, icon="🔮",
    ),
}


# =========================================================================
# Command Executor
# =========================================================================


class CommandExecutor:
    """Executes commands on Spaces.

    Commands are resolved dynamically based on:
        - Space entity type
        - Available commands in the Space
        - User permissions
    """

    def __init__(self, commands: Optional[Dict[str, SpaceCommand]] = None):
        self._commands = commands or dict(BUILTIN_COMMANDS)

    def register_command(self, command: SpaceCommand) -> None:
        self._commands[command.name] = command

    def get_available_commands(self, space: UniversalSpace) -> List[dict]:
        """Get all commands available for this Space."""
        available = []
        for cmd in self._commands.values():
            if cmd.applies(space):
                available.append(cmd.to_dict())
        return available

    def execute(self, space: UniversalSpace,
                command_name: str,
                params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a command on this Space."""
        cmd = self._commands.get(command_name)
        if not cmd:
            return {
                "error": True,
                "message": f"Unknown command: {command_name}",
                "available_commands": list(self._commands.keys()),
            }
        if not cmd.applies(space):
            return {
                "error": True,
                "message": f"Command '{command_name}' does not apply to "
                           f"Space type '{space.entity_type}'",
            }
        try:
            result = cmd.execute(space, params or {})
            result["success"] = True
            return result
        except Exception as e:
            return {
                "error": True,
                "message": f"Command '{command_name}' failed: {e}",
            }


# =========================================================================
# Singleton
# =========================================================================

_executor: Optional[CommandExecutor] = None


def get_executor() -> CommandExecutor:
    global _executor
    if _executor is None:
        _executor = CommandExecutor()
    return _executor


def reset_executor() -> None:
    global _executor
    _executor = None