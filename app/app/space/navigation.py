"""SHUNYA Phase A1 — Space Navigation Framework.

The Founder never opens applications. The Founder enters Spaces.
Navigation: Search → Select Object → Open Space.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.space.store import get_store, SpaceStore
from app.space.models import UniversalSpace


# =========================================================================
# Navigation Result
# =========================================================================


@dataclass
class NavigationResult:
    """Result of a navigation action."""
    space: Optional[UniversalSpace]
    found: bool = False
    transition_type: str = "instant"
    """instant, created, resumed"""
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "found": self.found,
            "transition_type": self.transition_type,
            "message": self.message,
            "space": self.space.to_summary() if self.space else None,
        }


# =========================================================================
# Space Navigator
# =========================================================================


class SpaceNavigator:
    """Search → Select Object → Open Space.

    The transition should feel instantaneous.
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search across all Spaces.

        Returns lightweight summaries for search results.
        """
        results = self._store.search(query)
        return [s.to_summary() for s in results]

    def search_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Find all spaces of a given entity type."""
        results = self._store.list_by_type(entity_type)
        return [s.to_summary() for s in results]

    def search_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recently accessed Spaces."""
        all_spaces = self._store.list_all()
        sorted_spaces = sorted(
            all_spaces,
            key=lambda s: s.identity.updated_at,
            reverse=True,
        )
        return [s.to_summary() for s in sorted_spaces[:limit]]

    # ------------------------------------------------------------------
    # Select / Open
    # ------------------------------------------------------------------

    def open(self, space_id: str) -> NavigationResult:
        """Open a Space by its ID.

        Returns the full Space with all panels.
        """
        space = self._store.get(space_id)
        if not space:
            return NavigationResult(
                space=None,
                found=False,
                message=f"Space '{space_id}' not found",
            )
        return NavigationResult(
            space=space,
            found=True,
            transition_type="instant",
            message=f"Opened Space: {space.name}",
        )

    def open_by_entity(self, entity_id: str) -> NavigationResult:
        """Open the Space for a given entity.

        If the Space doesn't exist, it is created on demand.
        """
        space = self._store.get_by_entity(entity_id)
        if not space:
            return NavigationResult(
                space=None,
                found=False,
                message=f"No Space found for entity '{entity_id}'",
            )
        return self.open(space.space_id)

    def open_or_create(self, entity_id: str, entity_type: str,
                       name: str, parent_space_id: str = "",
                       aliases: Optional[List[str]] = None,
                       ) -> NavigationResult:
        """Open a Space by entity — creates it if it doesn't exist.

        This is the primary entry point: the Founder types a name,
        SHUNYA finds or creates the Space.
        """
        existing = self._store.get_by_entity(entity_id)
        if existing:
            return NavigationResult(
                space=existing,
                found=True,
                transition_type="instant",
                message=f"Resumed Space: {existing.name}",
            )

        space = self._store.create(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            aliases=aliases,
            parent_space_id=parent_space_id,
        )
        return NavigationResult(
            space=space,
            found=True,
            transition_type="created",
            message=f"Created Space: {name}",
        )

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def navigate_to_relationship(self, space_id: str,
                                  rel: "SpaceRelationshipRef"
                                  ) -> NavigationResult:
        """Navigate from a Space to one of its related entities."""
        return self.open_by_entity(rel.target_entity_id)

    def navigate_to_child(self, space_id: str,
                          child_entity_id: str) -> NavigationResult:
        """Navigate to a child Space."""
        return self.open_by_entity(child_entity_id)

    def navigate_to_parent(self, space_id: str) -> NavigationResult:
        """Navigate to the parent Space."""
        space = self._store.get(space_id)
        if not space or not space.parent_space_id:
            return NavigationResult(
                space=None,
                found=False,
                message="No parent Space",
            )
        return self.open(space.parent_space_id)

    # ------------------------------------------------------------------
    # Breadcrumb
    # ------------------------------------------------------------------

    def breadcrumb(self, space_id: str) -> List[Dict[str, str]]:
        """Build a breadcrumb trail from this Space to the root."""
        trail = []
        current_id = space_id
        visited = set()
        max_depth = 10

        while current_id and len(trail) < max_depth:
            if current_id in visited:
                break
            visited.add(current_id)
            space = self._store.get(current_id)
            if not space:
                break
            trail.append({
                "space_id": space.space_id,
                "name": space.name,
                "entity_type": space.entity_type,
            })
            current_id = space.parent_space_id

        trail.reverse()
        return trail

    # ------------------------------------------------------------------
    # Space tree
    # ------------------------------------------------------------------

    def space_tree(self, root_id: str) -> Dict[str, Any]:
        """Build a tree of nested Spaces starting from a root."""
        root = self._store.get(root_id)
        if not root:
            return {}

        def _build_node(space_id: str) -> Dict[str, Any]:
            space = self._store.get(space_id)
            if not space:
                return {}
            children = self._store.list_children(space_id)
            return {
                "space_id": space.space_id,
                "name": space.name,
                "entity_type": space.entity_type,
                "children": [_build_node(c.space_id) for c in children],
            }

        return _build_node(root_id)


# =========================================================================
# Singleton
# =========================================================================

_navigator: Optional[SpaceNavigator] = None


def get_navigator() -> SpaceNavigator:
    global _navigator
    if _navigator is None:
        _navigator = SpaceNavigator()
    return _navigator


def reset_navigator() -> None:
    global _navigator
    _navigator = None