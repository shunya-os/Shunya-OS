"""Conversation Runtime — maintains continuous conversation context across navigation.

Now supports optional DB persistence via a wired provider.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from .types import ContextFrame


class ConversationRuntime:
    """Manages conversation continuity across workspaces, objects, and modules.

    Uses an in-memory store by default. When a persistence provider is
    wired via set_persistence_provider(), messages are also saved to
    the database for survival across restarts.
    """

    def __init__(self):
        self._conversations: dict[str, list[dict]] = {}
        self._max_history = 50
        self._save_message_fn: Callable | None = None
        self._load_history_fn: Callable | None = None

    def set_persistence_provider(self, save_fn: Callable, load_fn: Callable) -> None:
        """Wire persistence for conversation survival across restarts.

        Args:
            save_fn: Called with (session_id, role, content) to persist a message.
            load_fn: Called with (session_id, limit) to load persisted history.
        """
        self._save_message_fn = save_fn
        self._load_history_fn = load_fn

    def start_conversation(self, session_id: str, context: ContextFrame) -> str:
        """Start a new conversation for a session."""
        conv_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context.to_dict(),
            "messages": [],
        }
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        self._conversations[session_id].append(conv_entry)
        return f"conv_{len(self._conversations[session_id])}"

    def add_message(self, session_id: str, role: str, content: str,
                    context: ContextFrame | None = None) -> dict:
        """Add a message to the current conversation and persist if wired."""
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        convs = self._conversations[session_id]
        if not convs:
            convs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context.to_dict() if context else {},
                "messages": [],
            })

        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        convs[-1]["messages"].append(msg)

        # Persist to DB if wired
        if self._save_message_fn is not None:
            try:
                self._save_message_fn(session_id, role, content)
            except Exception:
                pass  # Persistence failure is non-critical

        # Trim oldest messages if exceeding limit
        all_msgs = sum(len(c["messages"]) for c in convs)
        if all_msgs > self._max_history:
            while all_msgs > self._max_history and convs:
                excess = all_msgs - self._max_history
                msgs = convs[0]["messages"]
                if len(msgs) <= excess:
                    all_msgs -= len(msgs)
                    convs.pop(0)
                else:
                    convs[0]["messages"] = msgs[excess:]
                    break

        return msg

    def get_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """Get conversation history, merging in-memory and persisted history."""
        # Load persisted history first (if wired)
        persisted: list[dict] = []
        if self._load_history_fn is not None:
            try:
                persisted = self._load_history_fn(session_id, limit) or []
            except Exception:
                pass

        # Get in-memory history
        convs = self._conversations.get(session_id, [])
        in_memory = []
        for conv in convs:
            in_memory.extend(conv["messages"])

        # Merge: persisted first, then in-memory (which may have newer messages),
        # deduplicated by timestamp + role + content
        seen = set()
        merged = []
        for msg in persisted + in_memory:
            key = (msg.get("timestamp", ""), msg.get("role", ""), msg.get("content", "")[:100])
            if key not in seen:
                seen.add(key)
                merged.append(msg)

        return merged[-limit:]

    def get_context_continuity(self, session_id: str, current_context: ContextFrame) -> dict[str, Any]:
        """Get continuity information when user navigates."""
        history = self.get_history(session_id, 5)
        previous_contexts = []
        for conv in self._conversations.get(session_id, []):
            if conv.get("context"):
                previous_contexts.append(conv["context"])

        return {
            "previous_contexts": previous_contexts[-3:],
            "last_messages": [m["content"] for m in history[-3:]] if history else [],
            "context_shifted": self._detect_shift(current_context, previous_contexts),
        }

    def _detect_shift(self, current: ContextFrame, previous: list[dict]) -> bool:
        """Detect if the context has shifted significantly."""
        if not previous:
            return False
        last = previous[-1]
        if last.get("active_workspace") and current.active_workspace:
            return last["active_workspace"] != current.active_workspace
        if last.get("active_module") and current.active_module:
            return last["active_module"] != current.active_module
        return False

    def clear(self) -> None:
        self._conversations.clear()