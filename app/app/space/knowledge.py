"""SHUNYA Phase A1 — Space Knowledge Integration.

Knowledge is native to the Space.
Documents, emails, messages, notes, policies, images, files, research,
meeting transcripts, AI summaries — everything links into the Space.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.space.models import SpaceKnowledgeItem
from app.space.store import get_store, SpaceStore


class SpaceKnowledgeManager:
    """Manages knowledge items within a Space.

    Integrates with the existing Knowledge Runtime (app.knowledge)
    and the Intelligence Layer (app.intelligence).
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    # ------------------------------------------------------------------
    # Knowledge CRUD
    # ------------------------------------------------------------------

    def add_item(self, space_id: str, item_type: str, title: str,
                 content_summary: str = "",
                 source: str = "",
                 metadata: Optional[Dict[str, Any]] = None
                 ) -> Optional[SpaceKnowledgeItem]:
        """Add a knowledge item to a Space."""
        item = SpaceKnowledgeItem(
            item_id=f"kn_{__import__('uuid').uuid4().hex[:16]}",
            item_type=item_type,
            title=title,
            content_summary=content_summary,
            source=source,
            metadata=metadata or {},
        )
        success = self._store.add_knowledge(space_id, item)
        return item if success else None

    def get_items(self, space_id: str,
                  item_type: str = "") -> List[SpaceKnowledgeItem]:
        """Get all knowledge items for a Space."""
        return self._store.get_knowledge(space_id, item_type)

    def search(self, space_id: str, query: str) -> List[SpaceKnowledgeItem]:
        """Search knowledge items within a Space."""
        q = query.lower()
        space = self._store.get(space_id)
        if not space:
            return []
        results = []
        for item in space.knowledge:
            if q in item.title.lower() or q in item.content_summary.lower():
                results.append(item)
        return results

    # ------------------------------------------------------------------
    # Convenience methods for common item types
    # ------------------------------------------------------------------

    def add_document(self, space_id: str, title: str,
                     content_summary: str = "",
                     source: str = "") -> Optional[SpaceKnowledgeItem]:
        return self.add_item(
            space_id, "document", title, content_summary, source,
        )

    def add_email(self, space_id: str, title: str,
                  content_summary: str = "",
                  source: str = "") -> Optional[SpaceKnowledgeItem]:
        return self.add_item(
            space_id, "email", title, content_summary, source,
        )

    def add_note(self, space_id: str, title: str,
                 content_summary: str = "",
                 source: str = "") -> Optional[SpaceKnowledgeItem]:
        return self.add_item(
            space_id, "note", title, content_summary, source,
        )

    def add_meeting_transcript(self, space_id: str, title: str,
                               content_summary: str = "",
                               source: str = "") -> Optional[SpaceKnowledgeItem]:
        return self.add_item(
            space_id, "meeting_transcript", title, content_summary, source,
        )

    def add_ai_summary(self, space_id: str, title: str,
                       content_summary: str = "",
                       source: str = "SHUNYA"
                       ) -> Optional[SpaceKnowledgeItem]:
        return self.add_item(
            space_id, "ai_summary", title, content_summary, source,
        )

    def add_research(self, space_id: str, title: str,
                     content_summary: str = "",
                     source: str = "") -> Optional[SpaceKnowledgeItem]:
        return self.add_item(
            space_id, "research", title, content_summary, source,
        )

    def add_file(self, space_id: str, title: str,
                 content_summary: str = "",
                 source: str = "") -> Optional[SpaceKnowledgeItem]:
        return self.add_item(
            space_id, "file", title, content_summary, source,
        )

    # ------------------------------------------------------------------
    # Integration with Knowledge Runtime
    # ------------------------------------------------------------------

    def get_knowledge_summary(self, space_id: str) -> Dict[str, Any]:
        """Get a summary of all knowledge in this Space."""
        items = self.get_items(space_id)
        by_type = {}
        for item in items:
            by_type.setdefault(item.item_type, []).append(item)
        return {
            "space_id": space_id,
            "total": len(items),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "recent": [
                {"title": i.title, "type": i.item_type, "created": i.created_at}
                for i in sorted(items, key=lambda x: x.created_at, reverse=True)[:10]
            ],
        }


# =========================================================================
# Singleton
# =========================================================================

_manager: Optional[SpaceKnowledgeManager] = None


def get_knowledge_manager() -> SpaceKnowledgeManager:
    global _manager
    if _manager is None:
        _manager = SpaceKnowledgeManager()
    return _manager


def reset_knowledge_manager() -> None:
    global _manager
    _manager = None