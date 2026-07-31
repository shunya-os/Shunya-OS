"""
SHUNYA Universal Planning Runtime — Dependency Graph

Universal dependency types: finish-to-start, start-to-start,
finish-to-finish, soft, hard, conditional, cross-domain.
No business assumptions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Dependency:
    dep_id: str
    source_id: str
    target_id: str
    dep_type: str
    """'finish_to_start', 'start_to_start', 'finish_to_finish',
       'soft', 'hard', 'conditional', 'cross_domain'"""
    label: str = ""
    is_satisfied: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "dep_id": self.dep_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "dep_type": self.dep_type,
            "label": self.label,
            "is_satisfied": self.is_satisfied,
        }


class DependencyGraph:
    def __init__(self):
        self._deps: dict[str, Dependency] = {}

    def add(self, dep: Dependency) -> None:
        self._deps[dep.dep_id] = dep

    def get(self, dep_id: str) -> Optional[Dependency]:
        return self._deps.get(dep_id)

    def get_dependencies_for(self, milestone_id: str) -> list[Dependency]:
        return [d for d in self._deps.values() if d.target_id == milestone_id]

    def get_dependents_of(self, milestone_id: str) -> list[Dependency]:
        return [d for d in self._deps.values() if d.source_id == milestone_id]

    def are_all_dependencies_satisfied(self, milestone_id: str) -> bool:
        deps = self.get_dependencies_for(milestone_id)
        if not deps:
            return True
        return all(d.is_satisfied for d in deps)

    def satisfy(self, dep_id: str) -> None:
        dep = self._deps.get(dep_id)
        if dep:
            dep.is_satisfied = True

    @property
    def count(self) -> int:
        return len(self._deps)

    def clear(self) -> None:
        self._deps.clear()


_graph: Optional[DependencyGraph] = None


def get_graph() -> DependencyGraph:
    global _graph
    if _graph is None:
        _graph = DependencyGraph()
    return _graph


def reset_graph() -> None:
    global _graph
    _graph = None