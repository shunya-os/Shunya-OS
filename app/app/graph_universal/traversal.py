"""
SHUNYA Universal Business Graph — Graph Query Engine

Universal graph traversal: entity lookup, relationship traversal,
shortest connection, neighborhood search, dependency expansion.
"""

from __future__ import annotations
from typing import Optional

from app.graph_universal.entity import Entity, get_store as get_entity_store
from app.graph_universal.relationship import get_store as get_rel_store


class GraphQueryEngine:
    """Deterministic graph query engine."""

    def __init__(self):
        pass

    def lookup(self, entity_id: str) -> Optional[Entity]:
        return get_entity_store().get(entity_id)

    def neighbors(self, entity_id: str, max_depth: int = 1) -> dict[str, list[dict]]:
        """Get neighbors at each depth level."""
        result = {}
        visited = {entity_id}
        current = [entity_id]
        rel_store = get_rel_store()
        es = get_entity_store()

        for depth in range(max_depth):
            next_level = []
            level_entities = []

            for eid in current:
                nbrs = rel_store.get_neighbors(eid)
                for nid in nbrs:
                    if nid not in visited:
                        visited.add(nid)
                        next_level.append(nid)
                        entity = es.get(nid)
                        if entity:
                            level_entities.append({
                                "entity_id": nid,
                                "name": entity.name,
                                "entity_type": entity.entity_type,
                                "depth": depth + 1,
                            })

            if level_entities:
                result[f"depth_{depth + 1}"] = level_entities
            current = next_level
            if not current:
                break

        return result

    def shortest_path(self, from_id: str, to_id: str) -> Optional[list[str]]:
        """BFS shortest path between two entities."""
        if from_id == to_id:
            return [from_id]

        rel_store = get_rel_store()
        visited = {from_id}
        queue = [[from_id]]

        while queue:
            path = queue.pop(0)
            last = path[-1]
            nbrs = rel_store.get_neighbors(last)

            for nid in nbrs:
                if nid == to_id:
                    return path + [nid]
                if nid not in visited:
                    visited.add(nid)
                    queue.append(path + [nid])

        return None

    def find_by_type(self, entity_type: str) -> list[Entity]:
        return get_entity_store().get_by_type(entity_type)

    def search(self, query: str) -> list[Entity]:
        """Simple text search across entity names and aliases."""
        q = query.lower()
        results = []
        for e in get_entity_store()._entities.values():
            if q in e.name.lower():
                results.append(e)
                continue
            for alias in e.aliases:
                if q in alias.lower():
                    results.append(e)
                    break
        return results


_engine: Optional[GraphQueryEngine] = None


def get_engine() -> GraphQueryEngine:
    global _engine
    if _engine is None:
        _engine = GraphQueryEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None