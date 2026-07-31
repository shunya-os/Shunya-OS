"""SHUNYA Phase A1 — Space Context Persistence.

Every Space remembers:
- Last position
- Collapsed sections
- Recent conversations
- Open documents
- Current execution
- AI reasoning context
- Pending work

Returning to a Space restores continuity.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.space.models import SpaceContext
from app.space.store import get_store, SpaceStore


class SpaceContextManager:
    """Manages context persistence for Spaces.

    Context is stored per-Space and restored on re-entry.
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    # ------------------------------------------------------------------
    # Context CRUD
    # ------------------------------------------------------------------

    def get_context(self, space_id: str) -> Optional[SpaceContext]:
        """Get the current context for a Space."""
        space = self._store.get(space_id)
        if not space:
            return None
        return space.context

    def update_context(self, space_id: str,
                       **kwargs) -> bool:
        """Update context fields for a Space.

        Usage:
            context_manager.update_context(
                space_id,
                last_position="timeline",
                collapsed_sections=["metrics", "knowledge"],
            )
        """
        space = self._store.get(space_id)
        if not space:
            return False
        for key, value in kwargs.items():
            if hasattr(space.context, key):
                setattr(space.context, key, value)
        space.context.updated_at = __import__(
            "datetime"
        ).datetime.now(__import__("datetime").timezone.utc).isoformat()
        return True

    # ------------------------------------------------------------------
    # Position
    # ------------------------------------------------------------------

    def save_position(self, space_id: str, position: str) -> bool:
        """Save the last scroll/panel position."""
        return self.update_context(space_id, last_position=position)

    def get_last_position(self, space_id: str) -> str:
        """Get the last saved position."""
        ctx = self.get_context(space_id)
        if not ctx:
            return ""
        return ctx.last_position

    # ------------------------------------------------------------------
    # Collapsed sections
    # ------------------------------------------------------------------

    def save_collapsed_sections(self, space_id: str,
                                sections: List[str]) -> bool:
        return self.update_context(space_id, collapsed_sections=sections)

    # ------------------------------------------------------------------
    # Open documents
    # ------------------------------------------------------------------

    def save_open_documents(self, space_id: str,
                            doc_ids: List[str]) -> bool:
        return self.update_context(space_id, open_documents=doc_ids)

    # ------------------------------------------------------------------
    # Recent conversations
    # ------------------------------------------------------------------

    def save_recent_conversations(self, space_id: str,
                                  conv_ids: List[str]) -> bool:
        return self.update_context(space_id, recent_conversations=conv_ids)

    # ------------------------------------------------------------------
    # Pending work
    # ------------------------------------------------------------------

    def save_pending_work(self, space_id: str,
                          work_items: List[str]) -> bool:
        return self.update_context(space_id, pending_work=work_items)

    # ------------------------------------------------------------------
    # AI reasoning context
    # ------------------------------------------------------------------

    def save_ai_reasoning_context(self, space_id: str,
                                  context: str) -> bool:
        return self.update_context(space_id, ai_reasoning_context=context)

    # ------------------------------------------------------------------
    # Full restore
    # ------------------------------------------------------------------

    def restore(self, space_id: str) -> Optional[Dict[str, Any]]:
        """Restore all context for a Space on re-entry.

        Returns a dict with all saved context, or None if not found.
        """
        ctx = self.get_context(space_id)
        if not ctx:
            return None
        return ctx.to_dict()


# =========================================================================
# Singleton
# =========================================================================

_manager: Optional[SpaceContextManager] = None


def get_context_manager() -> SpaceContextManager:
    global _manager
    if _manager is None:
        _manager = SpaceContextManager()
    return _manager


def reset_context_manager() -> None:
    global _manager
    _manager = None