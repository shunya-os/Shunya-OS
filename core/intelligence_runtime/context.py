"""Context Engine — continuously maintains user context across workspaces."""

from __future__ import annotations

from typing import Any

from .types import ContextFrame


class ContextEngine:
    """Maintains the current context — workspace, object, conversation, task."""

    def __init__(self):
        self._frames: dict[str, ContextFrame] = {}
        self._current_session: str = ""

    def update(self, session_id: str, **updates: Any) -> ContextFrame:
        """Update the context for a session."""
        if session_id not in self._frames:
            self._frames[session_id] = ContextFrame(conversation_id=session_id)
        frame = self._frames[session_id]
        for key, value in updates.items():
            if hasattr(frame, key):
                setattr(frame, key, value)
        self._current_session = session_id
        return frame

    def get(self, session_id: str | None = None) -> ContextFrame:
        """Get the current context frame."""
        sid = session_id or self._current_session
        if sid not in self._frames:
            self._frames[sid] = ContextFrame(conversation_id=sid)
        return self._frames[sid]

    def push_history(self, session_id: str, entry: str) -> None:
        """Add an entry to the recent history."""
        frame = self.get(session_id)
        frame.recent_history.append(entry)
        if len(frame.recent_history) > 20:
            frame.recent_history = frame.recent_history[-20:]

    def set_task(self, session_id: str, task: str) -> None:
        """Set the current task."""
        self.get(session_id).current_task = task

    def clear_task(self, session_id: str) -> None:
        """Clear the current task."""
        self.get(session_id).current_task = ""

    def navigate(self, session_id: str, workspace: str, object_type: str = "", object_id: str = "") -> None:
        """Update context after navigation."""
        self.update(session_id, active_workspace=workspace, active_object_type=object_type, active_object_id=object_id)
        if workspace:
            self.push_history(session_id, f"Navigated to {workspace}")

    def reset_session(self, session_id: str) -> None:
        """Reset a session's context."""
        self._frames[session_id] = ContextFrame(conversation_id=session_id)

    def clear(self) -> None:
        """Clear all context (testing)."""
        self._frames.clear()
        self._current_session = ""

    @property
    def current_session(self) -> str:
        return self._current_session