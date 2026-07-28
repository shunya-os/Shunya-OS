"""
SHUNYA Planning Engine — In-Memory Implementation

The Planning Engine transforms objectives into actionable plans — sequences
of steps with dependencies, resources, risks, and success criteria.  It is
the strategy layer of the Intelligence Runtime.

**Deterministic work** (always computed in-memory):
  - Dependency graph validation (acyclic check)
  - Step ordering (topological sort)
  - Resource conflict detection
  - Risk classification by type

**AI-assisted work** (delegated to escalate()):
  - Step generation from objective
  - Duration estimation
  - Risk identification

Architecture rules:
  - The engine never imports from app/ (strangler-fig isolation).
  - Dependency validation uses Kahn's algorithm (BFS-based topological sort).
  - Resource conflicts are detected by overlapping step time windows and
    shared resource types.

References:
  - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §8 (Planning Engine)
  - docs/canon/07_ai_canon.md §9 (Planner Engine)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Any

from core.intelligence.planning.models import (
    EngineInput,
    EngineOutput,
    EscalationResult,
    Plan,
    PlanStep,
    Resource,
    Risk,
    RiskCategory,
    RiskSeverity,
)

logger = logging.getLogger(__name__)


# ── Confidence constants ──────────────────────────────────────────────────────


_PLAN_BASE_CONFIDENCE: float = 0.65
"""Base confidence for automatically generated plans (per Canon §4.3)."""

_VALIDATION_PASS_BOOST: float = 0.15
"""Confidence boost when plan passes all validation checks."""

_RESOURCE_CONFLICT_PENALTY: float = 0.10
"""Confidence penalty per resource conflict detected."""


# ── PlanningEngine ────────────────────────────────────────────────────────────


class PlanningEngine:
    """In-memory Planning Engine for SHUNYA.

    The engine implements the ``IntelligenceEngine`` interface (``process``,
    ``escalate``, ``get_capabilities``, ``health_check``) as specified in
    the Intelligence Runtime Canon §3.

    **Deterministic validations** (dependency graph, topological sort,
    resource conflict detection, risk classification) are computed entirely
    in-memory with no external dependencies.

    **Plan generation** is AI-assisted — the deterministic layer validates
    and orders plans, but the initial step generation from an objective
    is delegated to ``escalate()``.

    Usage::

        engine = PlanningEngine()

        # Create a plan with explicit steps
        step_a = PlanStep(step_id="step-1", order=1, action="Research", actor="alice")
        step_b = PlanStep(step_id="step-2", order=2, action="Develop", actor="bob",
                          depends_on=("step-1",))
        plan = engine.create_plan("Build feature X", [step_a, step_b])

        # Validate dependencies
        result = engine.validate_dependencies(plan)

        # Process through the engine interface
        output = engine.process(EngineInput(
            input_type="objective",
            payload={"objective": "Build feature X"},
            trace_id="trace-001",
        ))
    """

    # ── Engine identity ───────────────────────────────────────────────────────

    engine_id: str = "planning_engine"
    """Unique identifier for this engine instance."""

    engine_type: str = "planning"
    """Engine type per Intelligence Runtime classification."""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def __init__(self) -> None:
        self._plans: dict[str, Plan] = {}
        """In-memory store of generated plans, keyed by plan_id."""

    # ══════════════════════════════════════════════════════════════════════════
    # IntelligenceEngine Interface
    # ══════════════════════════════════════════════════════════════════════════

    def process(self, inp: EngineInput) -> EngineOutput:
        """Process an objective into a validated plan.

        The processing flow:

        1. Extract the objective from the payload.
        2. If explicit steps are provided, use them; otherwise escalate
           to AI for step generation.
        3. Validate the dependency graph (acyclic check).
        4. Topologically sort steps.
        5. Detect resource conflicts.
        6. Compute confidence and return.

        Args:
            inp: The ``EngineInput`` containing the objective, optional
                steps, and planning parameters.

        Returns:
            An ``EngineOutput`` with the validated plan payload.

        Raises:
            ValueError: If the objective is empty or the payload is
                malformed.
        """
        start = time.perf_counter()
        trace_id = inp.trace_id or ""
        objective = inp.payload.get("objective", "")
        steps_dicts: list[dict[str, Any]] = inp.payload.get("steps", [])
        explicit_steps: list[PlanStep] = inp.payload.get("plan_steps", [])

        if not objective:
            raise ValueError("A plan must have a non-empty objective")

        escalation_used = False
        deterministic = True

        # ── Step generation: explicit or AI-assisted ──────────────────────

        if explicit_steps:
            steps = list(explicit_steps)
        elif steps_dicts:
            steps = [self._step_from_dict(sd) for sd in steps_dicts]
            steps = self._resolve_depends_on_indices(steps)
        else:
            # No steps provided — escalate to AI for generation
            escalation = self._escalate_plan_generation(inp)
            escalation_used = True
            deterministic = False
            steps = [
                self._step_from_dict(s) for s in escalation.result.get("steps", [])
            ]
            steps = self._resolve_depends_on_indices(steps)
            if not steps:
                steps = self._generate_fallback_steps(objective)

        # ── Build plan ────────────────────────────────────────────────────

        plan = self.create_plan(objective, steps)

        # ── Deterministic validation ──────────────────────────────────────

        validation_results = self._validate_plan(plan)
        acyclic = validation_results["acyclic"]
        cycle_path = validation_results.get("cycle_path", [])
        sorted_step_ids = validation_results.get("sorted_step_ids", [])
        resource_conflicts = validation_results.get("resource_conflicts", [])
        risk_classifications = validation_results.get("risk_classifications", [])

        # ── Confidence computation ────────────────────────────────────────

        confidence = _PLAN_BASE_CONFIDENCE
        confidence_factors: dict[str, float] = {
            "base_confidence": _PLAN_BASE_CONFIDENCE,
            "steps_count": len(steps),
            "acyclic": 1.0 if acyclic else 0.0,
        }

        if acyclic:
            confidence += _VALIDATION_PASS_BOOST
            confidence_factors["validation_boost"] = _VALIDATION_PASS_BOOST

        conflict_penalty = len(resource_conflicts) * _RESOURCE_CONFLICT_PENALTY
        confidence -= conflict_penalty
        confidence_factors["resource_conflict_penalty"] = conflict_penalty

        if escalation_used:
            confidence_factors["escalation_used"] = 1.0

        confidence = max(0.0, min(1.0, confidence))
        confidence_factors["final_confidence"] = round(confidence, 6)

        elapsed = (time.perf_counter() - start) * 1000.0

        return EngineOutput(
            output_type="plan.generated",
            payload={
                "plan_id": plan.plan_id,
                "objective": objective,
                "steps": [
                    {
                        "step_id": s.step_id,
                        "order": s.order,
                        "action": s.action,
                        "actor": s.actor,
                        "depends_on": list(s.depends_on),
                        "status": s.status.value,
                    }
                    for s in plan.steps
                ],
                "sorted_step_ids": sorted_step_ids,
                "acyclic": acyclic,
                "cycle_path": cycle_path,
                "resource_conflicts": [
                    {"resource": rc["resource"], "steps": rc["steps"]}
                    for rc in resource_conflicts
                ],
                "risk_classifications": risk_classifications,
                "estimated_duration": plan.estimated_duration,
                "estimated_duration_seconds": plan.estimated_duration_seconds,
            },
            confidence=round(confidence, 6),
            confidence_factors=confidence_factors,
            deterministic=deterministic,
            trace_id=trace_id,
            escalation_used=escalation_used,
            processing_time_ms=round(elapsed, 2),
        )

    def escalate(self, inp: EngineInput) -> EscalationResult:
        """Bridge to external AI inference for plan generation.

        Called when no explicit steps are provided.  In a production
        deployment, this would call an LLM API to generate steps from
        the objective.  This placeholder returns a structured mock.

        Args:
            inp: The original ``EngineInput``.

        Returns:
            An ``EscalationResult`` with AI-generated plan steps.
        """
        return self._escalate_plan_generation(inp)

    def get_capabilities(self) -> list[str]:
        """Return list of capability strings for this engine.

        Returns:
            List of canonical capability identifiers.
        """
        return [
            "planning.generate",
            "planning.validate_dependencies",
            "planning.topological_sort",
            "planning.resource_conflict_detection",
            "planning.risk_classification",
        ]

    def health_check(self) -> dict[str, Any]:
        """Return engine health status.

        Returns:
            A dictionary with engine identity, plan count, and overall
            status.
        """
        return {
            "engine_id": self.engine_id,
            "engine_type": self.engine_type,
            "status": "healthy",
            "plans_count": len(self._plans),
        }

    # ══════════════════════════════════════════════════════════════════════════
    # Plan CRUD
    # ══════════════════════════════════════════════════════════════════════════

    def create_plan(
        self,
        objective: str,
        steps: list[PlanStep],
        estimated_duration: str = "",
        estimated_duration_seconds: float = 0.0,
        success_criteria: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Plan:
        """Create a new plan with the given objective and steps.

        Automatically assigns step orders, derives dependency maps, and
        aggregates resources and risks.

        Args:
            objective: What the plan achieves.
            steps: Ordered list of ``PlanStep`` instances.
            estimated_duration: Human-readable duration estimate.
            estimated_duration_seconds: Duration in seconds.
            success_criteria: Overall success criteria.
            metadata: Optional extensible metadata.

        Returns:
            A new ``Plan`` instance.

        Raises:
            ValueError: If the objective is empty or steps are invalid.
        """
        if not objective:
            raise ValueError("A plan must have a non-empty objective")
        if not steps:
            raise ValueError("A plan must have at least one step")

        # Assign orders if not already set
        ordered_steps: list[PlanStep] = []
        for i, step in enumerate(steps):
            if step.order == 0 and i > 0:
                # Auto-assign order
                step = PlanStep(
                    step_id=step.step_id,
                    order=i + 1,
                    action=step.action,
                    actor=step.actor,
                    estimated_duration=step.estimated_duration,
                    estimated_duration_seconds=step.estimated_duration_seconds,
                    depends_on=step.depends_on,
                    resources=step.resources,
                    risks=step.risks,
                    success_criteria=step.success_criteria,
                    notes=step.notes,
                    status=step.status,
                    metadata=step.metadata,
                )
            ordered_steps.append(step)

        # Derive dependency map
        dependencies: dict[str, list[str]] = {}
        for step in ordered_steps:
            dependencies[step.step_id] = list(step.depends_on)

        # Aggregate resources and risks
        all_resources: dict[str, Resource] = {}
        all_risks: dict[str, Risk] = {}
        for step in ordered_steps:
            for rsrc in step.resources:
                all_resources[rsrc.resource_id] = rsrc
            for rsk in step.risks:
                all_risks[rsk.risk_id] = rsk

        # Auto-compute duration from steps
        if estimated_duration_seconds <= 0.0:
            total_secs = sum(
                s.estimated_duration_seconds for s in ordered_steps
            )
        else:
            total_secs = estimated_duration_seconds

        plan = Plan(
            objective=objective,
            steps=tuple(ordered_steps),
            dependencies=dependencies,
            estimated_duration=estimated_duration or f"{total_secs:.0f}s",
            estimated_duration_seconds=total_secs,
            resources=tuple(all_resources.values()),
            risks=tuple(all_risks.values()),
            success_criteria=tuple(success_criteria or []),
            confidence=_PLAN_BASE_CONFIDENCE,
            metadata=metadata or {},
        )

        self._plans[plan.plan_id] = plan
        logger.info(
            "Created plan %s for objective %r with %d steps",
            plan.plan_id,
            objective,
            len(ordered_steps),
        )
        return plan

    def get_plan(self, plan_id: str) -> Plan | None:
        """Retrieve a plan by its ID.

        Args:
            plan_id: The plan's unique identifier.

        Returns:
            The ``Plan``, or ``None`` if not found.
        """
        return self._plans.get(plan_id)

    # ══════════════════════════════════════════════════════════════════════════
    # Dependency Graph Validation (§8.3)
    # ══════════════════════════════════════════════════════════════════════════

    def validate_dependencies(self, plan: Plan) -> dict[str, Any]:
        """Validate the dependency graph of a plan.

        Performs the following checks:
        1. **Acyclic check**: Uses Kahn's algorithm (BFS topological sort).
           If a cycle exists, the cycle path is identified.
        2. **Orphan check**: Identifies steps that are not reachable from
           the dependency graph.
        3. **Self-dependency check**: Identifies steps that depend on
           themselves.

        Args:
            plan: The ``Plan`` to validate.

        Returns:
            A dictionary with:
            - ``acyclic``: ``True`` if the graph has no cycles.
            - ``cycle_path``: List of step IDs forming a cycle, if found.
            - ``sorted_step_ids``: Topologically sorted step IDs (if acyclic).
            - ``orphan_steps``: Step IDs with no dependencies and no
              dependents.
            - ``self_dependencies``: Step IDs that depend on themselves.
        """
        dependencies = plan.dependencies
        step_ids = {s.step_id for s in plan.steps}

        # ── Self-dependency check ─────────────────────────────────────────
        self_deps = [
            sid for sid, deps in dependencies.items() if sid in deps
        ]

        # ── Kahn's algorithm for topological sort & cycle detection ────────
        # Build in-degree count and adjacency list
        in_degree: dict[str, int] = {sid: 0 for sid in step_ids}
        adjacency: dict[str, list[str]] = {sid: [] for sid in step_ids}

        for step_id, dep_list in dependencies.items():
            for dep_id in dep_list:
                if dep_id in adjacency and step_id in adjacency:
                    adjacency[dep_id].append(step_id)
                    in_degree[step_id] = in_degree.get(step_id, 0) + 1

        # BFS from nodes with zero in-degree
        queue: deque[str] = deque(
            sid for sid, deg in in_degree.items() if deg == 0
        )
        sorted_ids: list[str] = []
        visited_count = 0

        while queue:
            sid = queue.popleft()
            sorted_ids.append(sid)
            visited_count += 1
            for neighbor in adjacency.get(sid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        acyclic = visited_count == len(step_ids)

        # ── Cycle path extraction ─────────────────────────────────────────
        cycle_path: list[str] = []
        if not acyclic:
            remaining = set(step_ids) - set(sorted_ids)
            if remaining:
                # Find a cycle by following edges from a remaining node
                seed = next(iter(remaining))
                cycle_path = self._find_cycle(seed, dependencies, step_ids)

        # ── Orphan check ──────────────────────────────────────────────────
        all_deps = set()
        for deps in dependencies.values():
            all_deps.update(deps)
        dependent_ids = set(dependencies.keys()) | all_deps
        orphan_steps = sorted(step_ids - dependent_ids)

        return {
            "acyclic": acyclic,
            "cycle_path": cycle_path,
            "sorted_step_ids": sorted_ids if acyclic else [],
            "orphan_steps": orphan_steps,
            "self_dependencies": self_deps,
        }

    def _find_cycle(
        self,
        start_id: str,
        dependencies: dict[str, list[str]],
        all_step_ids: set[str],
    ) -> list[str]:
        """DFS-based cycle detection starting from a node.

        Args:
            start_id: Step ID to start traversal from.
            dependencies: Dependency map.
            all_step_ids: All valid step IDs.

        Returns:
            List of step IDs forming a cycle (empty if none found).
        """
        visited: set[str] = set()
        path: list[str] = []
        path_set: set[str] = set()

        def dfs(node: str) -> bool:
            if node in path_set:
                # Found a cycle: extract from the first occurrence of node
                path.append(node)
                return True
            if node in visited:
                return False
            if node not in all_step_ids:
                return False

            visited.add(node)
            path.append(node)
            path_set.add(node)

            for dep in dependencies.get(node, []):
                if dfs(dep):
                    return True

            path.pop()
            path_set.discard(node)
            return False

        if dfs(start_id):
            # Extract cycle from the path
            last = path[-1]
            try:
                cycle_start_idx = path.index(last)
                return path[cycle_start_idx:]
            except ValueError:
                return path
        return []

    # ══════════════════════════════════════════════════════════════════════════
    # Topological Sort (§8.3)
    # ══════════════════════════════════════════════════════════════════════════

    def topological_sort(self, plan: Plan) -> list[str]:
        """Return the topologically sorted order of plan steps.

        Delegates to ``validate_dependencies`` and returns the sorted
        order only if the graph is acyclic.

        Args:
            plan: The ``Plan`` to sort.

        Returns:
            List of step IDs in topological order, or an empty list if
            a cycle exists.
        """
        result = self.validate_dependencies(plan)
        return result.get("sorted_step_ids", [])

    # ══════════════════════════════════════════════════════════════════════════
    # Resource Conflict Detection (§8.3)
    # ══════════════════════════════════════════════════════════════════════════

    def detect_resource_conflicts(self, plan: Plan) -> list[dict[str, Any]]:
        """Detect resource conflicts across plan steps.

        A resource conflict occurs when two steps that can run concurrently
        (no dependency between them) require the same non-shareable resource.

        This implementation checks for:
        - Same resource name used by steps that are not in a dependency
          chain (i.e., could run in parallel).
        - Resource type conflicts (e.g., two steps claiming the same
          "person" or "tool" resource).

        Args:
            plan: The ``Plan`` to check.

        Returns:
            List of conflict dictionaries, each containing:
            - ``resource``: The resource name.
            - ``steps``: List of step IDs conflicting over this resource.
            - ``resource_type``: The type of the resource.
        """
        dependencies = plan.dependencies
        conflicts: list[dict[str, Any]] = []

        # Build a map: resource_name -> list of (step_id, resource)
        resource_map: dict[str, list[tuple[str, Resource]]] = defaultdict(list)
        for step in plan.steps:
            for resource in step.resources:
                key = f"{resource.name}::{resource.resource_type}"
                resource_map[key].append((step.step_id, resource))

        # For each resource, check if the steps using it are parallel
        for key, usages in resource_map.items():
            if len(usages) < 2:
                continue

            name, rtype = key.split("::", 1)
            step_ids = [s for s, _ in usages]

            # Check if any pair of steps could run in parallel
            parallel_pairs = self._find_parallel_pairs(step_ids, dependencies)
            if parallel_pairs:
                conflicts.append({
                    "resource": name,
                    "resource_type": rtype,
                    "steps": step_ids,
                    "parallel_pairs": parallel_pairs,
                })

        return conflicts

    def _find_parallel_pairs(
        self,
        step_ids: list[str],
        dependencies: dict[str, list[str]],
    ) -> list[tuple[str, str]]:
        """Find pairs of steps that could run in parallel.

        Two steps are parallel if neither depends on the other (directly
        or transitively).

        Args:
            step_ids: List of step IDs to check.
            dependencies: Dependency map for the plan.

        Returns:
            List of (step_a, step_b) tuples that are parallel.
        """
        # Build reachability set for each step
        reachable_from: dict[str, set[str]] = {}
        for sid in step_ids:
            reachable = set()
            stack = [sid]
            visited = {sid}
            while stack:
                current = stack.pop()
                for dep in dependencies.get(current, []):
                    if dep not in visited:
                        visited.add(dep)
                        reachable.add(dep)
                        stack.append(dep)
            reachable_from[sid] = reachable

        # Reverse reachability: what depends on this step?
        depended_by: dict[str, set[str]] = defaultdict(set)
        for sid, reachable in reachable_from.items():
            for r in reachable:
                depended_by[r].add(sid)

        parallel_pairs: list[tuple[str, str]] = []
        for i in range(len(step_ids)):
            for j in range(i + 1, len(step_ids)):
                a, b = step_ids[i], step_ids[j]
                a_can_reach_b = b in reachable_from.get(a, set())
                b_can_reach_a = a in reachable_from.get(b, set())
                if not a_can_reach_b and not b_can_reach_a:
                    parallel_pairs.append((a, b))

        return parallel_pairs

    # ══════════════════════════════════════════════════════════════════════════
    # Risk Classification (§8.3)
    # ══════════════════════════════════════════════════════════════════════════

    def classify_risks(self, plan: Plan) -> list[dict[str, Any]]:
        """Classify risks by category and severity.

        For each risk in the plan, computes the risk score and assigns
        a severity category based on the score.

        Args:
            plan: The ``Plan`` whose risks to classify.

        Returns:
            List of risk classification dictionaries, each containing:
            - ``risk_id``: The risk's unique ID.
            - ``description``: Risk description.
            - ``category``: The risk category.
            - ``severity``: The severity level.
            - ``probability``: Probability [0, 1].
            - ``impact``: Impact [0, 1].
            - ``risk_score``: Computed probability * impact.
            - ``mitigation``: Mitigation strategy.
        """
        classifications: list[dict[str, Any]] = []
        for risk in plan.risks:
            classifications.append({
                "risk_id": risk.risk_id,
                "description": risk.description,
                "category": risk.category.value,
                "severity": risk.severity.value,
                "probability": risk.probability,
                "impact": risk.impact,
                "risk_score": risk.risk_score,
                "mitigation": risk.mitigation,
                "contingency": risk.contingency,
                "owner": risk.owner,
            })
        return classifications

    # ══════════════════════════════════════════════════════════════════════════
    # Internal Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _validate_plan(self, plan: Plan) -> dict[str, Any]:
        """Run all deterministic validations on a plan.

        Args:
            plan: The ``Plan`` to validate.

        Returns:
            Combined validation results dictionary.
        """
        dep_result = self.validate_dependencies(plan)
        resource_conflicts = self.detect_resource_conflicts(plan)
        risk_classifications = self.classify_risks(plan)

        return {
            **dep_result,
            "resource_conflicts": resource_conflicts,
            "risk_classifications": risk_classifications,
        }

    def _escalate_plan_generation(self, inp: EngineInput) -> EscalationResult:
        """Escalate plan generation to an AI inference provider.

        In a production deployment, this would call an LLM API to generate
        steps from the objective.  This placeholder returns a structured
        mock result.

        Args:
            inp: The original engine input.

        Returns:
            An ``EscalationResult`` with AI-generated steps.
        """
        objective = inp.payload.get("objective", "unknown objective")
        result = {
            "steps": [
                {
                    "action": "Analyse requirements",
                    "actor": "system",
                    "estimated_duration": "1h",
                    "estimated_duration_seconds": 3600,
                    "depends_on": [],
                    "success_criteria": ["Requirements documented"],
                },
                {
                    "action": f"Design solution for: {objective}",
                    "actor": "system",
                    "estimated_duration": "2h",
                    "estimated_duration_seconds": 7200,
                    "depends_on": [0],  # depends on first step (index-based)
                    "success_criteria": ["Design approved"],
                },
                {
                    "action": "Implement solution",
                    "actor": "system",
                    "estimated_duration": "4h",
                    "estimated_duration_seconds": 14400,
                    "depends_on": [1],
                    "success_criteria": ["Implementation complete"],
                },
                {
                    "action": "Test and verify",
                    "actor": "system",
                    "estimated_duration": "1h",
                    "estimated_duration_seconds": 3600,
                    "depends_on": [2],
                    "success_criteria": ["All tests pass"],
                },
            ],
            "estimated_duration": "8h",
            "estimated_duration_seconds": 28800,
            "confidence_note": "AI-generated plan, verify independently",
        }
        return EscalationResult(
            result=result,
            confidence=0.65,
            provider="placeholder_llm",
            processing_time_ms=0.0,
        )

    def _generate_fallback_steps(self, objective: str) -> list[PlanStep]:
        """Generate deterministic fallback steps when AI escalation fails.

        Args:
            objective: The plan objective.

        Returns:
            A minimal list of ``PlanStep`` instances.
        """
        return [
            PlanStep(
                step_id=f"step-{i}",
                order=i + 1,
                action=action,
                actor="system",
                depends_on=(),
                success_criteria=("Complete",),
            )
            for i, action in enumerate(
                [f"Analyse: {objective}", "Plan execution", "Execute", "Verify"]
            )
        ]

    @staticmethod
    def _step_from_dict(data: dict[str, Any]) -> PlanStep:
        """Convert a dictionary to a ``PlanStep``.

        Args:
            data: Dictionary with step fields.

        Returns:
            A ``PlanStep`` instance.
        """
        kwargs: dict[str, Any] = {
            "action": data.get("action", ""),
            "actor": data.get("actor", ""),
            "estimated_duration": data.get("estimated_duration", ""),
            "estimated_duration_seconds": data.get("estimated_duration_seconds", 0.0),
            "notes": data.get("notes", ""),
            "metadata": data.get("metadata", {}),
        }

        # Handle depends_on: can be list of indices or list of step IDs
        depends_on = data.get("depends_on", [])
        if depends_on and all(isinstance(d, int) for d in depends_on):
            # Index-based references — store as-is; will be resolved later
            kwargs["depends_on"] = tuple(str(d) for d in depends_on)
        else:
            kwargs["depends_on"] = tuple(depends_on)

        # Handle success_criteria
        kwargs["success_criteria"] = tuple(
            data.get("success_criteria", [])
        )

        # Handle resources
        resources = data.get("resources", [])
        kwargs["resources"] = tuple(
            Resource(
                name=r.get("name", ""),
                resource_type=r.get("resource_type", ""),
                quantity=r.get("quantity", 1.0),
            )
            for r in resources
        )

        # Handle risks
        risks = data.get("risks", [])
        kwargs["risks"] = tuple(
            Risk(
                description=r.get("description", ""),
                severity=RiskSeverity(r.get("severity", "medium")),
                category=RiskCategory(r.get("category", "operational")),
                probability=r.get("probability", 0.5),
                impact=r.get("impact", 0.5),
            )
            for r in risks
        )

        # Handle explicit step_id and order
        if "step_id" in data:
            kwargs["step_id"] = data["step_id"]
        if "order" in data:
            kwargs["order"] = data["order"]

        return PlanStep(**kwargs)

    @staticmethod
    def _resolve_depends_on_indices(
        steps: list[PlanStep],
    ) -> list[PlanStep]:
        """Resolve index-based dependency references to actual step IDs.

        When steps are created from dicts with ``depends_on`` as index
        integers (e.g. ``[0]``, ``[1]``), this method replaces those
        indices with the actual step IDs of the referenced steps.

        Args:
            steps: List of ``PlanStep`` instances, possibly with index-
                based ``depends_on``.

        Returns:
            New list of ``PlanStep`` instances with resolved dependencies.
        """
        resolved: list[PlanStep] = []
        for i, step in enumerate(steps):
            new_depends: list[str] = []
            for dep in step.depends_on:
                if dep.isdigit() and int(dep) < len(steps):
                    # Index-based reference: resolve to the actual step ID
                    idx = int(dep)
                    if idx < i:
                        # Reference to an earlier step
                        new_depends.append(steps[idx].step_id)
                    else:
                        # Forward reference — keep the index as-is for now
                        # (will be resolved if the referenced step is earlier)
                        new_depends.append(dep)
                else:
                    new_depends.append(dep)

            if new_depends != list(step.depends_on):
                step = PlanStep(
                    step_id=step.step_id,
                    order=step.order,
                    action=step.action,
                    actor=step.actor,
                    estimated_duration=step.estimated_duration,
                    estimated_duration_seconds=step.estimated_duration_seconds,
                    depends_on=tuple(new_depends),
                    resources=step.resources,
                    risks=step.risks,
                    success_criteria=step.success_criteria,
                    notes=step.notes,
                    status=step.status,
                    metadata=step.metadata,
                )
            resolved.append(step)
        return resolved


# ── Singleton accessor ────────────────────────────────────────────────────────


_planning_engine_instance: PlanningEngine | None = None


def get_planning_engine() -> PlanningEngine:
    """Return the singleton PlanningEngine instance.

    Creates the instance on first call.  Use this for production scenarios
    where a single shared engine instance is desired.

    Returns:
        The shared ``PlanningEngine`` instance.
    """
    global _planning_engine_instance
    if _planning_engine_instance is None:
        _planning_engine_instance = PlanningEngine()
    return _planning_engine_instance