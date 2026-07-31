"""SHUNYA Phase A1 — Space Relationship Visualization.

Every relationship is visualized.
The graph drives navigation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.space.models import SpaceRelationshipRef
from app.space.store import get_store, SpaceStore


class SpaceRelationshipManager:
    """Manages relationships for a Space.

    Integrates with the Business Graph (app.graph_universal.relationship)
    to provide a dynamic relationship graph for every Space.
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    # ------------------------------------------------------------------
    # Relationship management
    # ------------------------------------------------------------------

    def add_relationship(self, space_id: str, rel_id: str,
                         target_entity_id: str,
                         target_entity_name: str,
                         target_entity_type: str,
                         rel_type: str,
                         direction: str = "outgoing",
                         confidence: float = 1.0,
                         metadata: Optional[Dict[str, Any]] = None
                         ) -> bool:
        """Add a relationship to this Space."""
        rel = SpaceRelationshipRef(
            rel_id=rel_id,
            target_entity_id=target_entity_id,
            target_entity_name=target_entity_name,
            target_entity_type=target_entity_type,
            rel_type=rel_type,
            direction=direction,
            confidence=confidence,
            metadata=metadata or {},
        )
        return self._store.add_relationship(space_id, rel)

    def get_relationships(self, space_id: str) -> List[SpaceRelationshipRef]:
        """Get all relationships for this Space."""
        return self._store.get_relationships(space_id)

    def get_relationships_by_type(self, space_id: str,
                                  rel_type: str
                                  ) -> List[SpaceRelationshipRef]:
        """Filter relationships by type."""
        all_rels = self.get_relationships(space_id)
        return [r for r in all_rels if r.rel_type == rel_type]

    def get_relationships_by_direction(self, space_id: str,
                                       direction: str
                                       ) -> List[SpaceRelationshipRef]:
        """Filter relationships by direction."""
        all_rels = self.get_relationships(space_id)
        return [r for r in all_rels if r.direction == direction]

    # ------------------------------------------------------------------
    # Graph visualization data
    # ------------------------------------------------------------------

    def get_graph(self, space_id: str) -> Dict[str, Any]:
        """Get the full relationship graph for this Space.

        Returns nodes and edges for graph visualization.
        """
        space = self._store.get(space_id)
        if not space:
            return {"nodes": [], "edges": []}

        nodes = {space.identity.entity_id: {
            "id": space.identity.entity_id,
            "name": space.identity.name,
            "type": space.identity.entity_type,
            "is_center": True,
        }}
        edges = []

        for rel in space.relationships:
            # Add target node if not already present
            if rel.target_entity_id not in nodes:
                nodes[rel.target_entity_id] = {
                    "id": rel.target_entity_id,
                    "name": rel.target_entity_name,
                    "type": rel.target_entity_type,
                    "is_center": False,
                }
            edges.append({
                "source": space.identity.entity_id
                if rel.direction == "outgoing" else rel.target_entity_id,
                "target": rel.target_entity_id
                if rel.direction == "outgoing" else space.identity.entity_id,
                "type": rel.rel_type,
                "confidence": rel.confidence,
                "label": rel.rel_type,
            })

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "center_entity_id": space.identity.entity_id,
        }

    def get_neighborhood(self, space_id: str,
                         depth: int = 1) -> Dict[str, Any]:
        """Get the neighborhood graph with multiple depths."""
        graph = self.get_graph(space_id)
        return {
            "center": graph["center_entity_id"],
            "depth": depth,
            "nodes": graph["nodes"],
            "edges": graph["edges"],
        }

    # ------------------------------------------------------------------
    # Relationship summary
    # ------------------------------------------------------------------

    def get_relationship_summary(self, space_id: str) -> Dict[str, Any]:
        """Get a summary of all relationships."""
        rels = self.get_relationships(space_id)
        by_type = {}
        by_direction = {"outgoing": 0, "incoming": 0}
        for r in rels:
            by_type.setdefault(r.rel_type, []).append(r)
            by_direction[r.direction] = by_direction.get(r.direction, 0) + 1

        return {
            "space_id": space_id,
            "total": len(rels),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_direction": by_direction,
            "types": list(by_type.keys()),
        }


# =========================================================================
# Singleton
# =========================================================================

_manager: Optional[SpaceRelationshipManager] = None


def get_relationship_manager() -> SpaceRelationshipManager:
    global _manager
    if _manager is None:
        _manager = SpaceRelationshipManager()
    return _manager


def reset_relationship_manager() -> None:
    global _manager
    _manager = None