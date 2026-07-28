"""SHUNYA Phase A1A — Cross-Space Reasoning.

A reasoning service able to traverse connected Spaces.
Answers questions by walking the Business Graph through Space connections.

No application-specific reasoning.
Everything operates through the Business Graph.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.space.store import get_store, SpaceStore
from app.space.models import UniversalSpace


# =========================================================================
# Reasoning Query
# =========================================================================


@dataclass
class ReasoningQuery:
    """A query for cross-Space reasoning."""
    question: str
    start_space_id: str
    max_depth: int = 3
    relationship_types: List[str] = field(default_factory=list)
    """If empty, traverse all relationship types."""
    max_results: int = 50

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "start_space_id": self.start_space_id,
            "max_depth": self.max_depth,
            "relationship_types": self.relationship_types,
            "max_results": self.max_results,
        }


@dataclass
class ReasoningStep:
    """A single step in a reasoning trail."""
    space_id: str
    entity_name: str
    entity_type: str
    relationship: str = ""
    """How we got to this Space"""
    depth: int = 0
    evidence: List[str] = field(default_factory=list)
    """Relevant facts found at this node"""
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "space_id": self.space_id,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "relationship": self.relationship,
            "depth": self.depth,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class ReasoningResult:
    """The result of a cross-Space reasoning query."""
    query: str
    start_space_id: str
    trail: List[ReasoningStep] = field(default_factory=list)
    paths: List[List[ReasoningStep]] = field(default_factory=list)
    """Multiple alternative paths found."""
    summary: str = ""
    confidence: float = 0.0
    total_spaces_visited: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "start_space_id": self.start_space_id,
            "trail": [s.to_dict() for s in self.trail],
            "paths": [
                [s.to_dict() for s in path] for path in self.paths
            ],
            "summary": self.summary,
            "confidence": self.confidence,
            "total_spaces_visited": self.total_spaces_visited,
        }


# =========================================================================
# Cross-Space Reasoner
# =========================================================================


class CrossSpaceReasoner:
    """Traverses connected Spaces to answer questions.

    Walks the Business Graph through Space relationships,
    child/parent connections, and timeline events.

    Questions like:
    "Why is this project delayed?"
    → Project → Tasks → Meetings → Communications → Commitments → Dependencies
    """

    def __init__(self, store: Optional[SpaceStore] = None):
        self._store = store or get_store()

    # ------------------------------------------------------------------
    # Graph traversal
    # ------------------------------------------------------------------

    def traverse(self, start_id: str,
                 max_depth: int = 3,
                 rel_types: Optional[List[str]] = None
                 ) -> List[ReasoningStep]:
        """Traverse the Space graph from a starting Space.

        Follows:
        - Relationships (graph edges to other entities)
        - Children (nested Spaces)
        - Parent (containing Space)

        Returns a list of ReasoningSteps found at each depth.
        """
        visited = {start_id}
        steps = []
        queue = [(start_id, 0, "")]

        while queue:
            current_id, depth, rel = queue.pop(0)
            if depth > max_depth:
                continue

            space = self._store.get(current_id)
            if not space:
                continue

            step = ReasoningStep(
                space_id=current_id,
                entity_name=space.name,
                entity_type=space.entity_type,
                relationship=rel,
                depth=depth,
                evidence=self._collect_evidence(space),
                confidence=max(0.5, 1.0 - (depth * 0.15)),
            )
            steps.append(step)

            if depth >= max_depth:
                continue

            # Follow relationships
            for rel_ref in space.relationships:
                if rel_types and rel_ref.rel_type not in rel_types:
                    continue
                target_id = self._store.get_by_entity(rel_ref.target_entity_id)
                if target_id and target_id.space_id not in visited:
                    visited.add(target_id.space_id)
                    queue.append((target_id.space_id, depth + 1, rel_ref.rel_type))

            # Follow children
            for child_id in space.child_space_ids:
                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, depth + 1, "contains"))

            # Follow parent
            if space.parent_space_id and space.parent_space_id not in visited:
                visited.add(space.parent_space_id)
                queue.append((space.parent_space_id, depth + 1, "part_of"))

        return steps

    # ------------------------------------------------------------------
    # Path finding
    # ------------------------------------------------------------------

    def find_paths(self, from_id: str, to_id: str,
                   max_depth: int = 5) -> List[List[ReasoningStep]]:
        """Find all paths between two Spaces.

        BFS-based path finding through relationships and nesting.
        """
        paths = []
        visited = {from_id}
        queue = [[(from_id, 0, "")]]

        while queue:
            path = queue.pop(0)
            current_id, depth, _ = path[-1]

            if depth >= max_depth:
                continue

            space = self._store.get(current_id)
            if not space:
                continue

            # Get neighbors
            neighbors = []

            # Through relationships
            for rel_ref in space.relationships:
                target = self._store.get_by_entity(rel_ref.target_entity_id)
                if target and target.space_id not in visited:
                    neighbors.append((target.space_id, rel_ref.rel_type))

            # Through children
            for child_id in space.child_space_ids:
                if child_id not in visited:
                    neighbors.append((child_id, "contains"))

            # Through parent
            if space.parent_space_id and space.parent_space_id not in visited:
                neighbors.append((space.parent_space_id, "part_of"))

            for nid, rel in neighbors:
                new_visited = set(visited)
                new_visited.add(nid)
                new_path = path + [(nid, depth + 1, rel)]

                if nid == to_id:
                    # Found a path — convert to ReasoningSteps
                    path_steps = []
                    for pid, pd, pr in new_path:
                        ps = self._store.get(pid)
                        if ps:
                            path_steps.append(ReasoningStep(
                                space_id=pid,
                                entity_name=ps.name,
                                entity_type=ps.entity_type,
                                relationship=pr,
                                depth=pd,
                                evidence=self._collect_evidence(ps),
                                confidence=max(0.5, 1.0 - (pd * 0.15)),
                            ))
                    paths.append(path_steps)
                else:
                    new_visited.add(nid)
                    queue.append(new_path)

        return paths

    # ------------------------------------------------------------------
    # Query answering
    # ------------------------------------------------------------------

    def answer(self, query: ReasoningQuery) -> ReasoningResult:
        """Answer a cross-Space reasoning question.

        Traverses the graph from the starting Space and
        collects evidence at each node.
        """
        steps = self.traverse(
            query.start_space_id,
            max_depth=query.max_depth,
            rel_types=query.relationship_types if query.relationship_types else None,
        )

        # Build summary
        total = len(steps)
        depth_counts = {}
        for s in steps:
            depth_counts[s.depth] = depth_counts.get(s.depth, 0) + 1

        types_found = set(s.entity_type for s in steps)
        type_names = ", ".join(sorted(types_found)[:5])

        summary = (
            f"Traversed {total} Spaces across {max(depth_counts.keys()) if depth_counts else 0} levels. "
            f"Found types: {type_names}."
        )

        # Average confidence
        avg_conf = (
            sum(s.confidence for s in steps) / len(steps)
            if steps else 0.0
        )

        return ReasoningResult(
            query=query.question,
            start_space_id=query.start_space_id,
            trail=steps,
            paths=self._find_all_paths_from_steps(steps, query.start_space_id),
            summary=summary,
            confidence=avg_conf,
            total_spaces_visited=total,
        )

    def _find_all_paths_from_steps(self, steps: List[ReasoningStep],
                                    start_id: str) -> List[List[ReasoningStep]]:
        """Group steps into paths by depth."""
        if not steps:
            return []
        by_depth: Dict[int, List[ReasoningStep]] = {}
        for s in steps:
            by_depth.setdefault(s.depth, []).append(s)
        # Each depth level is a path
        paths = []
        for depth in sorted(by_depth.keys()):
            if depth <= 1:
                continue
            paths.append(by_depth[depth])
        return paths

    # ------------------------------------------------------------------
    # Evidence collection
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_evidence(space: UniversalSpace) -> List[str]:
        """Collect relevant evidence from a Space."""
        evidence = []
        if space.timeline:
            recent = sorted(space.timeline,
                           key=lambda e: e.timestamp, reverse=True)[:3]
            for e in recent:
                evidence.append(f"{e.title} ({e.category})")
        if space.plans:
            for p in space.plans[:2]:
                evidence.append(f"Plan: {p.title} ({p.state})")
        if space.metrics:
            for m in space.metrics[:2]:
                evidence.append(f"Metric: {m.name}={m.value}")
        if space.ai_understanding.summary:
            evidence.append(f"AI: {space.ai_understanding.summary[:100]}")
        return evidence


# =========================================================================
# Singleton
# =========================================================================

_reasoner: Optional[CrossSpaceReasoner] = None


def get_reasoner() -> CrossSpaceReasoner:
    global _reasoner
    if _reasoner is None:
        _reasoner = CrossSpaceReasoner()
    return _reasoner


def reset_reasoner() -> None:
    global _reasoner
    _reasoner = None