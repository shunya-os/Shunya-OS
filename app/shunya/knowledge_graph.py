"""Knowledge Graph — typed relationships between entities, actors, and assets.

Provides typed RelationshipType contracts, KnowledgeAsset/Actor models, a
KnowledgeGraph that builds from Shunya Entity+EntityLinker DB records, and
topological dependency traversal for dependency analysis.

Architecture mirrors the ported TS contracts from the Knowledge Graph package:
  graph/contracts/RelationshipType.ts
  graph/contracts/Relationship.ts
  graph/core/KnowledgeGraph.ts
  graph/diagnostics/GraphDiagnostics.ts
  contracts/KnowledgeAsset.ts
  contracts/KnowledgeRegistry.ts
  actor/Actor.ts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from app import db
from app.models import Entity, EntityDefinition
from app.shunya.entity_linker import EntityLinker
from app.shunya.foundation import NotFoundError, Result


# ════════════════════════════════════════════════════════════════════
# Typed RelationshipType — enum of all possible relationship kinds
# ════════════════════════════════════════════════════════════════════

class RelationshipType(str, Enum):
    """Typed semantic relationships between entities, actors, and assets.

    Mirrors the TS enum from graph/contracts/RelationshipType.ts.
    """
    OWNS = "owns"
    USES = "uses"
    PERFORMS = "performs"
    EXECUTES = "executes"
    CREATES = "creates"
    DEPENDS_ON = "depends_on"
    IMPROVES = "improves"
    REFERENCES = "references"

    @property
    def label(self) -> str:
        """Human-readable label for the relationship type."""
        return _RELATIONSHIP_LABELS[self]

    @property
    def is_directional(self) -> bool:
        """Whether this relationship has a defined direction (source → target)."""
        return True

    @property
    def is_dependency(self) -> bool:
        """Whether this represents a dependency relationship."""
        return self in (RelationshipType.DEPENDS_ON,)

    @staticmethod
    def from_string(value: str) -> "RelationshipType":
        """Parse a relationship type from a string, falling back to REFERENCES."""
        try:
            return RelationshipType(value.lower())
        except ValueError:
            return RelationshipType.REFERENCES


_RELATIONSHIP_LABELS: Dict[RelationshipType, str] = {
    RelationshipType.OWNS: "Owns",
    RelationshipType.USES: "Uses",
    RelationshipType.PERFORMS: "Performs",
    RelationshipType.EXECUTES: "Executes",
    RelationshipType.CREATES: "Creates",
    RelationshipType.DEPENDS_ON: "Depends On",
    RelationshipType.IMPROVES: "Improves",
    RelationshipType.REFERENCES: "References",
}


# ════════════════════════════════════════════════════════════════════
# Relationship — a typed edge between two nodes
# ════════════════════════════════════════════════════════════════════

@dataclass
class Relationship:
    """A typed, directional edge between two nodes in the knowledge graph.

    Mirrors the TS Relationship interface from graph/contracts/Relationship.ts.
    """
    source_id: int
    target_id: int
    type: RelationshipType
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: Optional[datetime] = None

    @property
    def label(self) -> str:
        return self.type.label


# ════════════════════════════════════════════════════════════════════
# KnowledgeAsset — a typed entity with metadata
# ════════════════════════════════════════════════════════════════════

@dataclass
class KnowledgeAsset:
    """A typed knowledge asset — the node payload in the graph.

    Mirrors KnowledgeAsset from contracts/KnowledgeAsset.ts.

    Attributes:
        id: Unique identifier (entity ID).
        type: The asset type (entity definition type).
        metadata: Arbitrary key-value payload.
        label: Human-readable label.
        icon: Visual icon for display.
    """
    id: int
    type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    label: str = ""
    icon: str = "📌"


# ════════════════════════════════════════════════════════════════════
# KnowledgeRegistry — in-memory registry of assets
# ════════════════════════════════════════════════════════════════════

class KnowledgeRegistry:
    """In-memory registry for KnowledgeAssets.

    Mirrors the registry contract from contracts/KnowledgeRegistry.ts.
    Provides register, find, exists, count operations.
    """

    def __init__(self) -> None:
        self._assets: Dict[int, KnowledgeAsset] = {}

    # ── Mutators ──

    def register(self, asset: KnowledgeAsset) -> KnowledgeAsset:
        """Register an asset in the registry."""
        self._assets[asset.id] = asset
        return asset

    def unregister(self, asset_id: int) -> None:
        """Remove an asset from the registry."""
        self._assets.pop(asset_id, None)

    def clear(self) -> None:
        """Clear all assets."""
        self._assets.clear()

    # ── Queries ──

    def find(self, asset_id: int) -> Optional[KnowledgeAsset]:
        """Find an asset by ID."""
        return self._assets.get(asset_id)

    def find_by_type(self, asset_type: str) -> List[KnowledgeAsset]:
        """Find all assets of a given type."""
        return [a for a in self._assets.values() if a.type == asset_type]

    def exists(self, asset_id: int) -> bool:
        """Check if an asset exists by ID."""
        return asset_id in self._assets

    def count(self) -> int:
        """Return the total number of registered assets."""
        return len(self._assets)

    def count_by_type(self) -> Dict[str, int]:
        """Return counts of assets grouped by type."""
        counts: Dict[str, int] = {}
        for asset in self._assets.values():
            counts[asset.type] = counts.get(asset.type, 0) + 1
        return counts

    def all(self) -> List[KnowledgeAsset]:
        """Return all registered assets."""
        return list(self._assets.values())


# ════════════════════════════════════════════════════════════════════
# Actor — a node representing a person, AI agent, system, or external party
# ════════════════════════════════════════════════════════════════════

class ActorType(str, Enum):
    """Type classification for actors."""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    EXTERNAL = "external"


@dataclass
class Actor:
    """An actor in the knowledge graph — human, AI, system, or external.

    Mirrors Actor from actor/Actor.ts.

    Attributes:
        id: Unique identifier (team_member ID or external ID).
        name: Display name.
        type: Classification (human, ai, system, external).
        organization_id: Optional org/tenant scope.
        metadata: Additional context.
    """
    id: int
    name: str
    type: ActorType = ActorType.HUMAN
    organization_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ════════════════════════════════════════════════════════════════════
# KnowledgeGraph — the core graph built from Entity + EntityLinker records
# ════════════════════════════════════════════════════════════════════

class KnowledgeGraph:
    """Formal knowledge graph built from Shunya Entity DB records.

    Mirrors the TS KnowledgeGraph from graph/core/KnowledgeGraph.ts.

    Builds nodes from Entity records and edges from EntityLinker links,
    augmented with typed RelationshipType semantics.

    Usage::

        kg = KnowledgeGraph.build_for_entity(entity_id=42)
        deps = kg.dependencies_of(42)
        report = kg.diagnostics()
    """

    def __init__(
        self,
        assets: Optional[Dict[int, KnowledgeAsset]] = None,
        relationships: Optional[List[Relationship]] = None,
    ) -> None:
        self._assets: Dict[int, KnowledgeAsset] = assets or {}
        self._relationships: List[Relationship] = relationships or []

        # Build adjacency index
        self._outgoing: Dict[int, List[Relationship]] = {}
        self._incoming: Dict[int, List[Relationship]] = {}
        self._rebuild_index()

    # ── Builders ──

    @classmethod
    def build_for_entity(
        cls,
        entity_id: int,
        tenant_id: Optional[int] = None,
        depth: int = 1,
    ) -> "KnowledgeGraph":
        """Build a knowledge graph centered on a specific entity.

        Args:
            entity_id: The central entity ID.
            tenant_id: Optional tenant filter. If omitted, inferred from entity.
            depth: How many levels of linked entities to traverse (default 1).

        Returns:
            A populated KnowledgeGraph instance.
        """
        assets: Dict[int, KnowledgeAsset] = {}
        relationships: List[Relationship] = []
        visited: Set[int] = set()

        entity = db.session.get(Entity, entity_id)
        if not entity:
            raise NotFoundError(f"Entity {entity_id} not found")

        tenant_id = tenant_id or entity.tenant_id
        cls._traverse(entity_id, tenant_id, assets, relationships, visited, depth, 0)
        return cls(assets=assets, relationships=relationships)

    @classmethod
    def build_for_tenant(cls, tenant_id: int, limit: int = 200) -> "KnowledgeGraph":
        """Build a tenant-wide knowledge graph from active entities.

        Args:
            tenant_id: The tenant to scan.
            limit: Max entities to include.

        Returns:
            A populated KnowledgeGraph instance.
        """
        assets: Dict[int, KnowledgeAsset] = {}
        relationships: List[Relationship] = []

        entities = (
            Entity.query
            .filter_by(tenant_id=tenant_id, is_archived=False)
            .order_by(Entity.created_at.desc())
            .limit(limit)
            .all()
        )

        for entity in entities:
            asset = cls._entity_to_asset(entity)
            assets[entity.id] = asset

            # Extract links from EntityLinker
            try:
                links = EntityLinker.get_linked_entities(entity.id)
                for link in links:
                    target_id = link["id"]
                    if target_id not in assets:
                        target_entity = db.session.get(Entity, target_id)
                        if target_entity:
                            assets[target_id] = cls._entity_to_asset(target_entity)

                    rel_type = cls._infer_relationship_type(
                        source_type=asset.type,
                        target_type=link.get("type", "unknown"),
                        direction=link.get("direction", "child"),
                    )
                    if link["direction"] == "child":
                        relationships.append(Relationship(
                            source_id=entity.id,
                            target_id=target_id,
                            type=rel_type,
                            weight=1.0,
                        ))
                    else:
                        relationships.append(Relationship(
                            source_id=target_id,
                            target_id=entity.id,
                            type=rel_type,
                            weight=1.0,
                        ))
            except Exception:
                continue

        return cls(assets=assets, relationships=relationships)

    @classmethod
    def build_from_entity_linker(
        cls,
        entity: Entity,
        links: List[dict],
    ) -> "KnowledgeGraph":
        """Build a graph from an entity and pre-fetched EntityLinker results."""
        assets: Dict[int, KnowledgeAsset] = {}
        relationships: List[Relationship] = []

        center_asset = cls._entity_to_asset(entity)
        assets[entity.id] = center_asset

        for link in links:
            target_id = link["id"]
            if target_id not in assets:
                target_entity = db.session.get(Entity, target_id)
                if target_entity:
                    assets[target_id] = cls._entity_to_asset(target_entity)
                else:
                    assets[target_id] = KnowledgeAsset(
                        id=target_id,
                        type=link.get("type", "unknown"),
                        label=link.get("label", "Record"),
                        icon=link.get("icon", "📌"),
                        metadata={
                            "code": link.get("code", ""),
                            "status": link.get("status", ""),
                            "display_name": link.get("display_name", ""),
                            "url": link.get("url", ""),
                        },
                    )

            rel_type = cls._infer_relationship_type(
                source_type=center_asset.type,
                target_type=link.get("type", "unknown"),
                direction=link.get("direction", "child"),
            )

            if link["direction"] == "child":
                relationships.append(Relationship(
                    source_id=entity.id,
                    target_id=target_id,
                    type=rel_type,
                    weight=1.0,
                    metadata={"label": link.get("label", ""), "status": link.get("status", "")},
                ))
            else:
                relationships.append(Relationship(
                    source_id=target_id,
                    target_id=entity.id,
                    type=rel_type,
                    weight=1.0,
                ))

        return cls(assets=assets, relationships=relationships)

    # ── Traversal ──

    def dependencies_of(self, asset_id: int) -> List[KnowledgeAsset]:
        """Topological dependency traversal — returns assets this one depends on.

        Walks the DEPENDS_ON and CREATES relationships to build a dependency
        chain, deduplicated and ordered by dependency depth (leaves first).

        Args:
            asset_id: The asset whose dependencies to resolve.

        Returns:
            List of KnowledgeAssets ordered leaf-first (deepest dep first).
        """
        visited: Set[int] = set()
        result: List[KnowledgeAsset] = []
        self._topological_dfs(asset_id, visited, result)
        # Remove self
        return [a for a in result if a.id != asset_id]

    def dependents_of(self, asset_id: int) -> List[KnowledgeAsset]:
        """Reverse dependency traversal — assets that depend on this one."""
        dependents: List[KnowledgeAsset] = []
        for rel in self._incoming.get(asset_id, []):
            if rel.type in (RelationshipType.DEPENDS_ON, RelationshipType.CREATES):
                asset = self._assets.get(rel.source_id)
                if asset:
                    dependents.append(asset)
        return dependents

    def neighbors(self, asset_id: int) -> List[Tuple[KnowledgeAsset, Relationship]]:
        """Get all neighboring assets and the relationships connecting them."""
        neighbors: List[Tuple[KnowledgeAsset, Relationship]] = []
        for rel in self._outgoing.get(asset_id, []):
            target = self._assets.get(rel.target_id)
            if target:
                neighbors.append((target, rel))
        for rel in self._incoming.get(asset_id, []):
            source = self._assets.get(rel.source_id)
            if source:
                neighbors.append((source, rel))
        return neighbors

    def find_path(
        self,
        source_id: int,
        target_id: int,
        max_depth: int = 5,
    ) -> Optional[List[Relationship]]:
        """BFS to find a path between two assets.

        Args:
            source_id: Start asset ID.
            target_id: End asset ID.
            max_depth: Maximum traversal depth.

        Returns:
            List of Relationships forming the path, or None if no path exists.
        """
        if source_id not in self._assets or target_id not in self._assets:
            return None

        from collections import deque

        visited: Set[int] = {source_id}
        queue: deque = deque()
        queue.append((source_id, []))

        while queue:
            current_id, path = queue.popleft()
            if current_id == target_id:
                return path

            if len(path) >= max_depth:
                continue

            for rel in self._outgoing.get(current_id, []):
                if rel.target_id not in visited:
                    visited.add(rel.target_id)
                    queue.append((rel.target_id, [*path, rel]))

            for rel in self._incoming.get(current_id, []):
                if rel.source_id not in visited:
                    visited.add(rel.source_id)
                    queue.append((rel.source_id, [*path, rel]))

        return None

    # ── Diagnostic queries ──

    def diagnostics(self) -> "GraphDiagnosticsReport":
        """Produce a diagnostics report for this graph.

        Returns:
            GraphDiagnosticsReport with version, capabilityCount, valid, issues.
        """
        from app.shunya.knowledge_graph import GraphDiagnostics
        return GraphDiagnostics.compute(self)

    def count_assets(self) -> int:
        return len(self._assets)

    def count_relationships(self) -> int:
        return len(self._relationships)

    def count_relationships_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for rel in self._relationships:
            counts[rel.type.value] = counts.get(rel.type.value, 0) + 1
        return counts

    def get_asset(self, asset_id: int) -> Optional[KnowledgeAsset]:
        return self._assets.get(asset_id)

    def get_relationships(self, asset_id: int) -> List[Relationship]:
        """Get all relationships involving a given asset."""
        return (
            self._outgoing.get(asset_id, [])
            + self._incoming.get(asset_id, [])
        )

    # ── Serialization ──

    def to_graph_json(self) -> dict:
        """Serialize to a JSON-ready dict suitable for graph visualization."""
        nodes = []
        for asset_id, asset in self._assets.items():
            nodes.append({
                "id": asset_id,
                "type": asset.type,
                "label": asset.label,
                "icon": asset.icon,
                "metadata": {
                    k: v for k, v in asset.metadata.items()
                    if k in ("code", "status", "display_name", "url")
                },
            })

        edges = []
        for rel in self._relationships:
            edges.append({
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "type": rel.type.value,
                "label": rel.label,
                "weight": rel.weight,
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }

    # ── Internal helpers ──

    @staticmethod
    def _entity_to_asset(entity: Entity) -> KnowledgeAsset:
        """Convert a Shunya Entity to a KnowledgeAsset."""
        definition = entity.definition
        return KnowledgeAsset(
            id=entity.id,
            type=definition.type if definition else "unknown",
            label=definition.label if definition else "Record",
            icon=definition.icon if definition else "📌",
            metadata={
                "code": entity.code or "",
                "status": entity.status,
                "display_name": entity.display_name,
                "url": f"/entities/{definition.type if definition else 'entity'}/{entity.id}",
                "assigned_to": entity.assigned_to,
                "created_at": entity.created_at.isoformat() if entity.created_at else None,
            },
        )

    @staticmethod
    def _infer_relationship_type(
        source_type: str,
        target_type: str,
        direction: str,
    ) -> RelationshipType:
        """Infer a RelationshipType from entity types and link direction."""
        # If direction is "parent", the target is the parent → source depends on target
        if direction == "parent":
            return RelationshipType.DEPENDS_ON

        # Try to infer from entity type name patterns
        type_map: Dict[str, RelationshipType] = {
            "lead": RelationshipType.CREATES,
            "booking": RelationshipType.CREATES,
            "itinerary": RelationshipType.REFERENCES,
            "invoice": RelationshipType.PERFORMS,
            "task": RelationshipType.EXECUTES,
            "project": RelationshipType.OWNS,
        }

        matched = type_map.get(target_type)
        if matched:
            return matched

        # Fall back to USES as a generic "connected to"
        return RelationshipType.USES

    @classmethod
    def _traverse(
        cls,
        entity_id: int,
        tenant_id: int,
        assets: Dict[int, KnowledgeAsset],
        relationships: List[Relationship],
        visited: Set[int],
        max_depth: int,
        current_depth: int,
    ) -> None:
        """Recursive BFS traversal for build_for_entity."""
        if current_depth > max_depth or entity_id in visited:
            return

        visited.add(entity_id)
        entity = db.session.get(Entity, entity_id)
        if not entity or entity.tenant_id != tenant_id:
            return

        assets[entity_id] = cls._entity_to_asset(entity)

        links = EntityLinker.get_linked_entities(entity_id)
        for link in links:
            target_id = link["id"]
            if target_id not in assets:
                target_entity = db.session.get(Entity, target_id)
                if target_entity:
                    assets[target_id] = cls._entity_to_asset(target_entity)

            rel_type = cls._infer_relationship_type(
                source_type=assets[entity_id].type,
                target_type=link.get("type", "unknown"),
                direction=link.get("direction", "child"),
            )

            if link["direction"] == "child":
                relationships.append(Relationship(
                    source_id=entity_id,
                    target_id=target_id,
                    type=rel_type,
                ))
            else:
                relationships.append(Relationship(
                    source_id=target_id,
                    target_id=entity_id,
                    type=rel_type,
                ))

            cls._traverse(
                target_id, tenant_id, assets, relationships,
                visited, max_depth, current_depth + 1,
            )

    def _rebuild_index(self) -> None:
        """Rebuild the adjacency index from current relationships."""
        self._outgoing.clear()
        self._incoming.clear()
        for rel in self._relationships:
            self._outgoing.setdefault(rel.source_id, []).append(rel)
            self._incoming.setdefault(rel.target_id, []).append(rel)

    def _topological_dfs(
        self,
        asset_id: int,
        visited: Set[int],
        result: List[KnowledgeAsset],
    ) -> None:
        """DFS topological sort helper."""
        if asset_id in visited:
            return
        visited.add(asset_id)

        # Visit dependencies first (outgoing DEPENDS_ON/CREATES edges)
        for rel in self._outgoing.get(asset_id, []):
            if rel.type in (RelationshipType.DEPENDS_ON, RelationshipType.CREATES):
                self._topological_dfs(rel.target_id, visited, result)

        asset = self._assets.get(asset_id)
        if asset:
            result.append(asset)


# ════════════════════════════════════════════════════════════════════
# GraphDiagnostics — validation and health report
# ════════════════════════════════════════════════════════════════════

@dataclass
class GraphDiagnosticsReport:
    """Health report for a KnowledgeGraph.

    Mirrors GraphDiagnostics from graph/diagnostics/GraphDiagnostics.ts.
    """
    version: str = "1.0.0"
    valid: bool = True
    capability_count: int = 0
    issues: List[str] = field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    type_counts: Dict[str, int] = field(default_factory=dict)


class GraphDiagnostics:
    """Static diagnostics computer for KnowledgeGraph instances.

    Reports on structure, health, and capability coverage.
    """

    VERSION = "1.0.0"

    @staticmethod
    def compute(graph: KnowledgeGraph) -> GraphDiagnosticsReport:
        """Compute a diagnostics report for the given graph.

        Checks:
        - Node and edge counts
        - Orphan edges (edges referencing non-existent nodes)
        - Type diversity
        - Capability coverage (how many relationship types are used)
        """
        issues: List[str] = []
        node_count = graph.count_assets()
        edge_count = graph.count_relationships()

        if node_count == 0:
            issues.append("Graph has no nodes")

        # Check for orphan edges
        orphan_count = 0
        for rel in graph._relationships:
            if rel.source_id not in graph._assets:
                orphan_count += 1
                issues.append(f"Orphan edge: source {rel.source_id} not in assets")
            if rel.target_id not in graph._assets:
                orphan_count += 1
                issues.append(f"Orphan edge: target {rel.target_id} not in assets")

        # Check type diversity
        type_counts = graph.count_relationships_by_type()
        all_types = {rt.value for rt in RelationshipType}
        used_types = set(type_counts.keys())
        unused_types = all_types - used_types

        # Capability count = number of distinct relationship types in use
        capability_count = len(used_types)

        report = GraphDiagnosticsReport(
            version=GraphDiagnostics.VERSION,
            valid=len(issues) == 0,
            capability_count=capability_count,
            issues=issues,
            node_count=node_count,
            edge_count=edge_count,
            type_counts=type_counts,
        )

        return report