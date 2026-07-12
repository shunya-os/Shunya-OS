"""Sequential planner with dependency graph — port from half-done TypeScript.

Ports the DependencyGraph, topological sort, and SequentialPlanner from
/tmp/shunya-half/packages/planner/src/engine/SequentialPlanner.ts and
/tmp/shunya-half/packages/knowledge/src/planning/planner/TopologicalPlanner.ts.

Provides ordered execution plans based on step dependencies rather than
arbitrary ordering — ensures prerequisites run before their dependents.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class PlanStep:
    """A single step in a dependency-aware execution plan.

    Mirrors PlanStep from the TS planner contracts but enriched with
    entity context and dependency tracking for Bird AI integration.
    """
    id: str
    action: str
    entity_type: str
    depends_on: List[str] = field(default_factory=list)
    priority: int = 5
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("PlanStep requires a non-empty id")


@dataclass
class Plan:
    """An ordered execution plan — steps sorted in dependency order.

    Mirrors Plan from the TS planner contracts.
    """
    steps: List[PlanStep] = field(default_factory=list)

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def step_ids(self) -> List[str]:
        return [s.id for s in self.steps]


class DependencyGraph:
    """Topological dependency graph for action ordering.

    Ported from /tmp/shunya-half/packages/knowledge/src/planning/contracts/DependencyGraph.ts
    and /tmp/shunya-half/packages/knowledge/src/planning/planner/TopologicalPlanner.ts.

    Builds a directed graph from PlanStep.depends_on references and
    produces a topological ordering (dependencies first) via DFS.
    """

    def __init__(self, steps: List[PlanStep]):
        self.steps = steps
        self._graph: dict[str, List[str]] = {}
        self._build()

    def _build(self):
        for step in self.steps:
            self._graph[step.id] = list(step.depends_on)

    def dependencies_of(self, step_id: str) -> List[str]:
        """Return the dependency IDs for a given step."""
        return self._graph.get(step_id, [])

    def all_ids(self) -> List[str]:
        """Return all step IDs in the graph."""
        return list(self._graph.keys())

    def topological_sort(self) -> List[str]:
        """Return step IDs in dependency order (dependencies first).

        Uses DFS with cycle detection. Raises ValueError on circular deps.

        Ported from TopologicalPlanner.executionOrder() in the TS codebase.
        """
        visited: Set[str] = set()
        visiting: Set[str] = set()
        order: List[str] = []

        def _visit(node_id: str):
            if node_id in visited:
                return
            if node_id in visiting:
                raise ValueError(f"Circular dependency detected: {node_id}")
            visiting.add(node_id)
            for dep in self._graph.get(node_id, []):
                _visit(dep)
            visiting.remove(node_id)
            visited.add(node_id)
            order.append(node_id)

        for node_id in self._graph:
            _visit(node_id)

        return order  # topological order (DFS post-order = deps first)


class SequentialPlanner:
    """Creates ordered execution plans from a set of steps.

    The planner takes un-ordered steps (possibly with dependencies) and
    returns a Plan whose steps are sorted in dependency order.

    Ported from SequentialPlanner.ts (TS) — a concrete implementation of
    the Planner interface that produces ordered step sequences.
    """

    def __init__(self):
        self._goals: dict = {}

    def create_plan(self, steps: List[PlanStep]) -> Plan:
        """Sort steps by dependency order and return a Plan.

        Within the same dependency level, steps retain their original order.
        """
        if not steps:
            return Plan(steps=[])

        graph = DependencyGraph(steps)
        sorted_ids = graph.topological_sort()
        step_map = {s.id: s for s in steps}

        sorted_steps: List[PlanStep] = []
        for sid in sorted_ids:
            if sid in step_map:
                sorted_steps.append(step_map[sid])

        return Plan(steps=sorted_steps)

    def plan_for_actions(self, entity_type: str, actions: List[dict]) -> Plan:
        """Convenience: create a Plan from Bird AI action dicts.

        Each action dict should contain:
            - action (str): the action name
            - depends_on (List[str], optional): dependency step IDs
            - priority (int, optional): priority value (lower = higher)

        Steps are automatically assigned IDs (step_0, step_1, ...).
        """
        steps = []
        for i, a in enumerate(actions):
            deps = a.get("depends_on", [])
            steps.append(PlanStep(
                id=f"step_{i}",
                action=a.get("action", "follow_up"),
                entity_type=entity_type,
                depends_on=deps,
                priority=a.get("priority", 5),
                metadata=a,
            ))
        return self.create_plan(steps)

    def register_goal(self, goal_id: str, context: Optional[dict] = None):
        """Register a planning goal for context tracking."""
        self._goals[goal_id] = context or {}

    def get_goal(self, goal_id: str) -> Optional[dict]:
        return self._goals.get(goal_id)