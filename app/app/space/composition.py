"""SHUNYA Phase A1A — Composite Spaces.

Extends nested Spaces into composable Spaces.
Every child remains an independent Space.
Relationships remain graph-driven.

Company
  Customer
  Supplier
  Projects
  Contracts
  Meetings

Project
  Tasks
  Documents
  Risks
  Milestones
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.space.store import get_store, SpaceStore
from app.space.models import UniversalSpace


class CompositeSpaceManager:
    """Manages composite (nested) Space structures.

    Every child remains an independent Space.
    Relationships remain graph-driven.
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    # ------------------------------------------------------------------
    # Composition management
    # ------------------------------------------------------------------

    def compose(self, parent_id: str, child_id: str) -> bool:
        """Compose a child Space into a parent Space.

        Both Spaces remain independent.
        The relationship is stored as a parent-child link.
        """
        return self._store.add_child(parent_id, child_id)

    def decompose(self, parent_id: str, child_id: str) -> bool:
        """Remove a child Space from its parent.

        The child Space remains independent.
        """
        parent = self._store.get(parent_id)
        child = self._store.get(child_id)
        if not parent or not child:
            return False
        parent.child_space_ids = [
            cid for cid in parent.child_space_ids if cid != child_id
        ]
        child.parent_space_id = ""
        return True

    def get_children(self, space_id: str) -> List[UniversalSpace]:
        """Get all direct children of a Space."""
        return self._store.list_children(space_id)

    def get_ancestors(self, space_id: str) -> List[UniversalSpace]:
        """Get all ancestors of a Space (parent, grandparent, etc.)."""
        ancestors = []
        current_id = space_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            space = self._store.get(current_id)
            if not space or not space.parent_space_id:
                break
            parent = self._store.get(space.parent_space_id)
            if parent:
                ancestors.append(parent)
                current_id = parent.space_id
            else:
                break

        return ancestors

    def get_siblings(self, space_id: str) -> List[UniversalSpace]:
        """Get all sibling Spaces (same parent)."""
        space = self._store.get(space_id)
        if not space or not space.parent_space_id:
            return []
        return [
            s for s in self._store.list_children(space.parent_space_id)
            if s.space_id != space_id
        ]

    def get_subtree(self, space_id: str,
                    max_depth: int = 5) -> Dict[str, Any]:
        """Get the full subtree rooted at a Space.

        Returns a nested dict structure.
        """
        space = self._store.get(space_id)
        if not space:
            return {}

        def _build(space_id: str, depth: int) -> Dict[str, Any]:
            if depth > max_depth:
                return {}
            s = self._store.get(space_id)
            if not s:
                return {}
            children = self._store.list_children(space_id)
            return {
                "space_id": s.space_id,
                "name": s.name,
                "entity_type": s.entity_type,
                "depth": depth,
                "children": [
                    _build(c.space_id, depth + 1) for c in children
                ],
                "child_count": len(children),
            }

        return _build(space_id, 0)

    def get_composition_summary(self, space_id: str) -> Dict[str, Any]:
        """Get a summary of the composition structure."""
        space = self._store.get(space_id)
        if not space:
            return {}
        children = self.get_children(space_id)
        ancestors = self.get_ancestors(space_id)
        siblings = self.get_siblings(space_id)
        return {
            "space_id": space_id,
            "name": space.name,
            "entity_type": space.entity_type,
            "child_count": len(children),
            "children": [c.to_summary() for c in children],
            "ancestor_count": len(ancestors),
            "ancestors": [a.to_summary() for a in ancestors],
            "sibling_count": len(siblings),
            "parent_space_id": space.parent_space_id or None,
        }


# =========================================================================
# Singleton
# =========================================================================

_manager: Optional[CompositeSpaceManager] = None


def get_composite_manager() -> CompositeSpaceManager:
    global _manager
    if _manager is None:
        _manager = CompositeSpaceManager()
    return _manager


def reset_composite_manager() -> None:
    global _manager
    _manager = None