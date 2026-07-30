"""Business Graph — semantic graph representation of a discovered business.

Consumed by all runtimes (Intelligence, Search, Automation, Timeline, Command, Workspace).
No runtime duplicates business understanding.
"""

from __future__ import annotations

from app.ubme.ontology import BusinessOntology

# Stores business graphs keyed by module key
_graphs: dict[str, "BusinessGraph"] = {}


class BusinessGraph:
    """Semantic graph of a business for all runtimes to consume."""

    def __init__(self, ontology: BusinessOntology):
        self.ontology = ontology
        self._adjacency: dict[str, list[dict]] = {}

    def build(self) -> None:
        """Build the adjacency graph from ontology relationships."""
        self._adjacency.clear()
        for entity in self.ontology.entities:
            self._adjacency[entity.key] = []

        for rel in self.ontology.relationships:
            source = rel.source_entity
            target = rel.target_entity
            if source in self._adjacency and target in self._adjacency:
                self._adjacency[source].append({
                    "target": target,
                    "label": rel.label,
                    "inverse": rel.inverse_label,
                    "cardinality": rel.cardinality.value,
                })
                self._adjacency[target].append({
                    "target": source,
                    "label": rel.inverse_label or rel.label,
                    "inverse": rel.label,
                    "cardinality": rel.cardinality.value,
                })

    def get_neighbors(self, entity_key: str) -> list[dict]:
        return self._adjacency.get(entity_key, [])

    def get_path(self, from_key: str, to_key: str) -> list[str] | None:
        """Simple BFS to find a path between two entities."""
        if from_key not in self._adjacency or to_key not in self._adjacency:
            return None
        visited = {from_key}
        queue = [[from_key]]
        while queue:
            path = queue.pop(0)
            node = path[-1]
            for neighbor in self._adjacency.get(node, []):
                nk = neighbor["target"]
                if nk == to_key:
                    return path + [nk]
                if nk not in visited:
                    visited.add(nk)
                    queue.append(path + [nk])
        return None

    def search(self, query: str) -> list[dict]:
        """Search entities by name, synonym, or field."""
        q = query.lower()
        results = []
        for entity in self.ontology.entities:
            score = 0
            if q in entity.name.lower():
                score += 3
            if q in entity.key:
                score += 2
            for syn in entity.synonyms:
                if q in syn.lower():
                    score += 2
            if score > 0:
                results.append({
                    "key": entity.key,
                    "name": entity.name,
                    "icon": entity.icon,
                    "score": score,
                    "fields": len(entity.fields),
                    "confidence": entity.confidence.value,
                })
        results.sort(key=lambda r: -r["score"])
        return results[:10]

    def to_dict(self) -> dict:
        return {
            "key": self.ontology.key,
            "name": self.ontology.name,
            "entities": [
                {"key": e.key, "name": e.name, "icon": e.icon, "color": e.color,
                 "fields": len(e.fields), "lifecycle": len(e.lifecycle),
                 "synonyms": e.synonyms, "confidence": e.confidence.value}
                for e in self.ontology.entities
            ],
            "relationships": [
                {"source": r.source_entity, "target": r.target_entity,
                 "label": r.label, "cardinality": r.cardinality.value}
                for r in self.ontology.relationships
            ],
            "graph": {k: [{"target": n["target"], "label": n["label"]} for n in v]
                      for k, v in self._adjacency.items()},
        }


def register_graph(module_key: str, ontology: BusinessOntology) -> BusinessGraph:
    graph = BusinessGraph(ontology)
    graph.build()
    _graphs[module_key] = graph
    return graph


def get_graph(module_key: str) -> BusinessGraph | None:
    return _graphs.get(module_key)


def list_graphs() -> list[dict]:
    return [g.to_dict() for g in _graphs.values()]