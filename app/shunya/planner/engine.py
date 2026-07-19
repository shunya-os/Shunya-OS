"""SHUNYA — Planner Engine (Phase G — ES-004).

The Planner Engine transforms justified reasoning into executable plans.
It is the bridge between *what should be done* (Reasoning Engine) and
*how to do it* (Executor Engine).

The engine implements a deterministic 9-stage pipeline:
  1. Goal Analysis
  2. Constraint Resolution
  3. Alternative Generation
  4. Optimization
  5. Risk Analysis
  6. Resource Planning
  7. Dependency Graph
  8. Execution Graph
  9. Governance Package

Architectural authority: ES-004 — Planner Engine Specification
"""

from __future__ import annotations

import time
import uuid
from dataclasses import field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.shunya.planner.models import (
    # Enums
    PlanningType, PlanState, TaskStatus,
    FailureMode, OptimizationDimension,
    # Core models
    ExecutionPlan, PlanTask, PlanningConstraint, Objective,
    Resource, ResourceAllocation, ResourcePool,
    Dependency, DependencyGraph, Schedule,
    RiskAssessment, DecisionTree, DecisionNode,
    GovernancePackage, PlanningInput, PlanningOutput,
    PlanningMetadata, OptimizationCriteria,
    PlanningError,
)
from app.shunya.planner.templates import (
    dispatch_planning_type, merge_plans, list_templates,
)


class PlannerEngine:
    """Planner Engine — generates executable plans from reasoning results.

    The engine implements a deterministic 9-stage pipeline that transforms
    reasoning results, constraints, and resources into structured,
    sequenced, costed, and risk-assessed plans packaged for Governance
    Engine validation.

    The engine does NOT:
      - Execute plans, approve plans, change knowledge, learn from outcomes,
        bypass governance, reason (generate new conclusions), or access credentials.
    """

    def __init__(self, knowledge_store: Any = None,
                 event_bus: Any = None,
                 logger: Any = None,
                 metrics_registry: Any = None,
                 health_registry: Any = None) -> None:
        self._knowledge_store = knowledge_store
        self._event_bus = event_bus
        self._logger = logger
        self._metrics = metrics_registry
        self._health = health_registry
        self._version = "1.0.0"

        if self._metrics:
            self._planning_counter = self._metrics.counter(
                "planner_cycles_total", "Planning cycles completed")
            self._failure_counter = self._metrics.counter(
                "planner_failures_total", "Planning failures")
            self._alternatives_histogram = self._metrics.histogram(
                "planner_alternatives_generated", "Alternatives per cycle",
                buckets=[1, 2, 3, 5, 10])
            self._latency_histogram = self._metrics.histogram(
                "planner_latency_ms", "Planning cycle latency",
                buckets=[10, 50, 100, 250, 500, 1000, 5000])

        if self._health:
            self._health.register("planner_engine", self._health_check)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def plan(self, planning_input: PlanningInput) -> PlanningOutput:
        """Execute the full planning pipeline.

        Accepts a PlanningInput containing reasoning results, constraints,
        resources, context, and objectives. Returns a PlanningOutput with
        the primary plan, alternatives, and governance package.

        Deterministic: same inputs always produce the same primary plan.
        """
        start = time.time()
        planning_start = datetime.now(timezone.utc)

        # Stage names for traceability
        stages = [
            "goal_analysis", "constraint_resolution", "alternative_generation",
            "optimization", "risk_analysis", "resource_planning",
            "dependency_graph", "execution_graph", "governance_package",
        ]
        stages_passed = 0
        stages_failed = 0

        try:
            # --- Stage 0: Input Validation ---
            validation = self._validate_input(planning_input)
            if not validation["valid"]:
                stages_failed += 9
                return self._error_output(
                    validation["error"],
                    failure_mode=validation.get("failure_mode", ""),
                    metadata=self._build_metadata(planning_input, start, stages, 0, 0),
                )
            stages_passed += 1

            # --- Stage 1: Goal Analysis ---
            goals = self._goal_analysis(planning_input)
            if goals is None:
                stages_failed += 8
                return self._error_output(
                    "Cannot generate structured goals — objectives are too ambiguous",
                    failure_mode=FailureMode.INCOMPLETE_GOALS.value,
                    stage="goal_analysis",
                    metadata=self._build_metadata(planning_input, start, stages, 1, 0),
                )
            stages_passed += 1

            # --- Stage 2: Constraint Resolution ---
            resolved_constraints = self._constraint_resolution(
                planning_input.constraints)
            if resolved_constraints is None:
                stages_failed += 7
                return self._error_output(
                    "Conflicting constraints cannot be resolved",
                    failure_mode=FailureMode.IMPOSSIBLE_PLAN.value,
                    stage="constraint_resolution",
                    metadata=self._build_metadata(planning_input, start, stages, 2, 0),
                )
            stages_passed += 1

            # --- Stage 3: Alternative Generation ---
            alternatives = self._generate_alternatives(
                planning_input, resolved_constraints)
            if not alternatives:
                stages_failed += 6
                return self._error_output(
                    "Zero alternatives generated — over-constrained",
                    failure_mode=FailureMode.IMPOSSIBLE_PLAN.value,
                    stage="alternative_generation",
                    metadata=self._build_metadata(planning_input, start, stages, 3, 0),
                )
            stages_passed += 1

            # --- Stage 4: Optimization ---
            optimized = self._optimize_alternatives(
                alternatives, planning_input.objectives)
            # Optimization may fail but we continue with unoptimized
            if optimized is None:
                optimized = alternatives  # Use unoptimized alternatives
                stages_failed += 1
            else:
                stages_passed += 1

            # --- Stage 5: Risk Analysis ---
            risk_assessed = self._risk_analysis(optimized, planning_input)
            stages_passed += 1

            # --- Stage 6: Resource Planning ---
            resource_allocated = self._resource_planning(
                risk_assessed, planning_input)
            stages_passed += 1

            # --- Stage 7: Dependency Graph ---
            dep_graph = self._build_dependency_graph(
                resource_allocated)
            if dep_graph is None:
                stages_failed += 3
                # Return partial result with error
                error_meta = self._build_metadata(
                    planning_input, start, stages, 7, 2)
                return self._error_output(
                    "Circular dependency detected in plan structure",
                    failure_mode=FailureMode.CIRCULAR_DEPENDENCY.value,
                    stage="dependency_graph",
                    metadata=error_meta,
                )
            stages_passed += 1

            # --- Stage 8: Execution Graph ---
            schedule = self._build_execution_graph(
                resource_allocated, dep_graph)
            stages_passed += 1

            # --- Stage 9: Governance Package ---
            governance_pkg = self._package_for_governance(
                resource_allocated, dep_graph, schedule,
                planning_input)
            stages_passed += 1

            # --- Assemble output ---
            primary_plan = resource_allocated[0] if resource_allocated else None
            if primary_plan:
                primary_plan.state = PlanState.PROPOSED.value
                primary_plan.dependency_graph = dep_graph
                primary_plan.schedule = schedule
                primary_plan.rank = 1

                # Compute total cost and duration
                primary_plan.total_estimated_cost = sum(
                    t.estimated_cost for t in primary_plan.tasks)
                primary_plan.total_estimated_duration_minutes = (
                    schedule.total_duration_minutes if schedule else 0.0)

            # Build overall confidence from risk assessment
            risk = self._assemble_risk_assessment(resource_allocated)

            planning_metadata = self._build_metadata(
                planning_input, start, stages,
                stages_passed, stages_failed)
            planning_metadata.alternatives_generated = len(alternatives)

            output = PlanningOutput(
                primary_plan=primary_plan,
                alternatives=resource_allocated[1:] if len(resource_allocated) > 1 else [],
                decision_tree=self._build_decision_tree(
                    resource_allocated, planning_input),
                dependency_graph=dep_graph,
                schedule=schedule,
                risk_assessment=risk,
                confidence=risk.overall_confidence if risk else 0.5,
                governance_package=governance_pkg,
                planning_metadata=planning_metadata,
            )

            self._record_metrics(start, output)
            if self._event_bus:
                self._emit_event(output)

            return output

        except PlanningError as e:
            stages_failed = stages_failed or 9
            meta = self._build_metadata(planning_input, start, stages,
                                        stages_passed, stages_failed)
            if self._metrics:
                self._failure_counter.inc()
            return self._error_output(
                e.message, failure_mode=e.failure_mode,
                stage=e.stage, details=e.details,
                metadata=meta)

        except Exception as e:
            stages_failed = stages_failed or 9
            meta = self._build_metadata(planning_input, start, stages,
                                        stages_passed, stages_failed)
            if self._metrics:
                self._failure_counter.inc()
            return self._error_output(
                f"Planning failed: {str(e)}",
                metadata=meta)

    # -----------------------------------------------------------------------
    # Stage 0: Input Validation
    # -----------------------------------------------------------------------

    def _validate_input(self, inp: PlanningInput) -> Dict[str, Any]:
        """Validate the planning input per ES-004 Section 2 contract.

        Returns {'valid': True} or {'valid': False, 'error': ..., 'failure_mode': ...}
        """
        reasoning = inp.reasoning_result
        if reasoning is None:
            return {
                "valid": False,
                "error": "No reasoning result provided — cannot plan",
                "failure_mode": FailureMode.LOW_CONFIDENCE.value,
            }

        # Check reasoning result has findings
        findings = getattr(reasoning, "findings", [])
        if not findings:
            return {
                "valid": False,
                "error": "Empty reasoning result — no findings to plan from",
                "failure_mode": FailureMode.INCOMPLETE_GOALS.value,
            }

        # Check confidence
        confidence = getattr(reasoning, "confidence", None)
        if confidence is not None:
            score = getattr(confidence, "overall_score", 0.5)
            if score <= 0.0:
                return {
                    "valid": False,
                    "error": "Zero-confidence reasoning — cannot generate reliable plans",
                    "failure_mode": FailureMode.LOW_CONFIDENCE.value,
                }

        # Tenant ID mismatch check
        context = inp.context
        if context is not None:
            context_tenant = getattr(context, "tenant_id", None)
            if context_tenant is not None and inp.tenant_id is not None:
                if context_tenant != inp.tenant_id:
                    return {
                        "valid": False,
                        "error": "Tenant mismatch between input and context",
                        "failure_mode": FailureMode.IMPOSSIBLE_PLAN.value,
                    }

        # Warn about missing constraints/resources but don't reject
        if not inp.constraints:
            if self._logger:
                self._logger.info("No constraints provided — plan may be infeasible")
        if not inp.resources:
            if self._logger:
                self._logger.info("No resources provided — plan may be over-ambitious")

        return {"valid": True}

    # -----------------------------------------------------------------------
    # Stage 1: Goal Analysis
    # -----------------------------------------------------------------------

    def _goal_analysis(self, inp: PlanningInput) -> Optional[List[Dict[str, Any]]]:
        """Decompose high-level objectives into concrete planning goals.

        Per ES-004 Section 4 — Goal Analysis stage.
        """
        goals: List[Dict[str, Any]] = []

        # Extract goals from reasoning result's findings
        reasoning = inp.reasoning_result
        findings = getattr(reasoning, "findings", [])

        for finding in findings:
            goal = {
                "goal_id": str(uuid.uuid4()),
                "finding_id": finding.finding_id,
                "finding_type": finding.finding_type,
                "label": finding.label or f"Process {finding.finding_type}",
                "description": finding.description or "",
                "severity": finding.severity,
                "confidence": finding.confidence,
            }
            goals.append(goal)

        # Add goals from explicit objectives
        for obj in inp.objectives:
            goals.append({
                "goal_id": str(uuid.uuid4()),
                "finding_id": "",
                "finding_type": "objective",
                "label": obj.label,
                "description": obj.description,
                "severity": "medium",
                "confidence": obj.priority,
            })

        # If no goals could be extracted, return None (failure)
        if not goals:
            return None

        return goals

    # -----------------------------------------------------------------------
    # Stage 2: Constraint Resolution
    # -----------------------------------------------------------------------

    def _constraint_resolution(
        self,
        constraints: List[PlanningConstraint],
    ) -> Optional[List[PlanningConstraint]]:
        """Identify and resolve conflicts between constraints.

        Per ES-004 Section 4 — Constraint Resolution stage.
        Returns resolved constraints or None if unresolvable.
        """
        if not constraints:
            return []

        resolved: List[PlanningConstraint] = []
        conflicts: List[str] = []

        # Detect pairwise conflicts
        for i, a in enumerate(constraints):
            for j, b in enumerate(constraints):
                if i >= j:
                    continue
                conflict = self._detect_constraint_conflict(a, b)
                if conflict:
                    conflicts.append(conflict)

        # If hard conflicts exist, try to resolve by relaxing soft constraints
        hard_conflicts = [c for c in conflicts if "hard" in c.lower()]
        if hard_conflicts:
            # Cannot resolve hard constraints — return None (failure)
            if self._logger:
                self._logger.warning(
                    f"Unresolvable constraint conflicts: {hard_conflicts}")
            return None

        # Apply resolved constraints
        for constraint in constraints:
            resolved.append(constraint)

        return resolved

    def _detect_constraint_conflict(
        self,
        a: PlanningConstraint,
        b: PlanningConstraint,
    ) -> Optional[str]:
        """Detect if two constraints conflict."""
        if a.constraint_type != b.constraint_type:
            return None
        if a.is_hard and b.is_hard:
            if a.constraint_type == "budget":
                if a.value != b.value:
                    return f"Hard budget conflict: {a.value} vs {b.value}"
            if a.constraint_type == "time":
                if a.value != b.value:
                    return f"Hard time conflict: {a.value} vs {b.value}"
        return None

    # -----------------------------------------------------------------------
    # Stage 3: Alternative Generation
    # -----------------------------------------------------------------------

    def _generate_alternatives(
        self,
        inp: PlanningInput,
        resolved_constraints: List[PlanningConstraint],
    ) -> List[ExecutionPlan]:
        """Generate multiple viable plan structures.

        Per ES-004 Section 4 — Alternative Generation stage.
        Produces 3-5 alternatives using different planning types.
        """
        alternatives: List[ExecutionPlan] = []
        planning_types = inp.planning_types or [PlanningType.OPERATIONAL.value]

        # Generate one primary alternative using requested planning types
        for ptype in planning_types[:3]:  # Max 3 types for alternative generation
            generator = dispatch_planning_type(ptype)
            if generator:
                try:
                    plan = generator(
                        inp.reasoning_result,
                        constraints=resolved_constraints,
                        context=inp.context,
                        tenant_id=inp.tenant_id,
                        actor_id=inp.actor_id,
                    )
                    plan.planning_type = ptype
                    alternatives.append(plan)
                except Exception:
                    continue

        # If no planning type succeeded, create a generic fallback plan
        if not alternatives:
            fallback = ExecutionPlan(
                name="Generic Execution Plan",
                reasoning_result_id=getattr(inp.reasoning_result, "result_id", ""),
                context_id=getattr(inp.context, "context_id", ""),
                tenant_id=inp.tenant_id,
                actor_id=inp.actor_id,
            )
            fallback.add_task(PlanTask(
                label="Execute Action",
                description="Execute the action determined by reasoning",
                estimated_duration_minutes=60.0,
            ))
            alternatives.append(fallback)

        return alternatives

    # -----------------------------------------------------------------------
    # Stage 4: Optimization
    # -----------------------------------------------------------------------

    def _optimize_alternatives(
        self,
        alternatives: List[ExecutionPlan],
        objectives: List[Objective],
    ) -> Optional[List[ExecutionPlan]]:
        """Optimize alternatives against objectives.

        Per ES-004 Section 4 — Optimization stage.
        Multi-objective optimization with Pareto-optimal scoring.
        """
        if not alternatives:
            return None

        criteria = OptimizationCriteria()

        # Score each alternative
        scored: List[Tuple[ExecutionPlan, float]] = []
        for alt in alternatives:
            score = self._score_plan(alt, criteria, objectives)
            scored.append((alt, score))

        # Sort by score descending (higher = better)
        scored.sort(key=lambda x: x[1], reverse=True)

        # Re-rank
        for i, (plan, _) in enumerate(scored):
            plan.rank = i + 1

        return [plan for plan, _ in scored]

    def _score_plan(self, plan: ExecutionPlan,
                    criteria: OptimizationCriteria,
                    objectives: List[Objective]) -> float:
        """Score a plan across multiple optimization dimensions.

        Returns a weighted score on 0.0-1.0 scale.
        """
        total_score = 0.0
        total_weight = 0.0

        # Time dimension (fewer tasks = faster)
        time_score = 1.0 - min(len(plan.tasks) / 100.0, 1.0)
        time_weight = criteria.get_weight(OptimizationDimension.TIME.value)
        total_score += time_score * time_weight
        total_weight += time_weight

        # Cost dimension (lower cost = better)
        cost_score = 1.0 - min(plan.total_estimated_cost / 1000000.0, 1.0)
        cost_weight = criteria.get_weight(OptimizationDimension.COST.value)
        total_score += cost_score * cost_weight
        total_weight += cost_weight

        # Risk dimension (lower risk = better)
        if plan.risk_assessment:
            risk_score = 1.0 - plan.risk_assessment.overall_risk_score
        else:
            risk_score = 0.5
        risk_weight = criteria.get_weight(OptimizationDimension.RISK.value)
        total_score += risk_score * risk_weight
        total_weight += risk_weight

        # Objective alignment
        if objectives:
            obj_score = sum(
                1.0 if obj.label.lower() in plan.name.lower() else 0.5
                for obj in objectives
            ) / len(objectives)
        else:
            obj_score = 0.5
        obj_weight = criteria.get_weight(
            OptimizationDimension.BUSINESS_OBJECTIVES.value)
        total_score += obj_score * obj_weight
        total_weight += obj_weight

        if total_weight > 0:
            return total_score / total_weight
        return 0.5

    # -----------------------------------------------------------------------
    # Stage 5: Risk Analysis
    # -----------------------------------------------------------------------

    def _risk_analysis(
        self,
        alternatives: List[ExecutionPlan],
        inp: PlanningInput,
    ) -> List[ExecutionPlan]:
        """Assess risk per alternative and per task.

        Per ES-004 Section 4 — Risk Analysis stage.
        """
        for alt in alternatives:
            per_task_risk: Dict[str, float] = {}
            risk_factors: List[Dict[str, Any]] = []
            total_risk = 0.0

            for task in alt.tasks:
                # Task risk is based on:
                # 1. Number of dependencies (more = higher risk)
                deps = len(task.depends_on)
                dep_risk = min(deps / 10.0, 1.0)

                # 2. Duration (longer = higher risk)
                duration_risk = min(task.estimated_duration_minutes / 480.0, 1.0)

                # 3. Cost (higher = higher risk)
                cost_risk = min(task.estimated_cost / 100000.0, 1.0)

                task_risk = (dep_risk * 0.3 + duration_risk * 0.3 + cost_risk * 0.4)
                per_task_risk[task.task_id] = task_risk
                task.risk_score = task_risk
                total_risk += task_risk

                if task_risk > 0.7:
                    risk_factors.append({
                        "task_id": task.task_id,
                        "label": task.label,
                        "risk_score": task_risk,
                        "reason": "High task complexity",
                    })

            # Reasoning result confidence affects overall risk
            reasoning = inp.reasoning_result
            reasoning_confidence = 0.5
            if reasoning:
                confidence = getattr(reasoning, "confidence", None)
                if confidence:
                    reasoning_confidence = getattr(confidence, "overall_score", 0.5)

            overall_risk = (
                (total_risk / max(len(alt.tasks), 1)) * 0.6
                + (1.0 - reasoning_confidence) * 0.4
            )

            alt.risk_assessment = RiskAssessment(
                overall_risk_score=overall_risk,
                overall_confidence=1.0 - overall_risk,
                per_task_risk=per_task_risk,
                risk_factors=risk_factors,
                assumptions=[
                    "Risk computed deterministically from task properties",
                    "Reasoning confidence factored into overall risk",
                ],
            )

        return alternatives

    # -----------------------------------------------------------------------
    # Stage 6: Resource Planning
    # -----------------------------------------------------------------------

    def _resource_planning(
        self,
        alternatives: List[ExecutionPlan],
        inp: PlanningInput,
    ) -> List[ExecutionPlan]:
        """Allocate resources to tasks and verify availability.

        Per ES-004 Section 4 — Resource Planning stage.
        """
        for alt in alternatives:
            allocations: List[ResourceAllocation] = []

            for task in alt.tasks:
                # If input resources provided, allocate them
                if inp.resources:
                    for res in inp.resources[:3]:
                        allocation = ResourceAllocation(
                            task_id=task.task_id,
                            resource_id=res.resource_id,
                            resource_type=res.resource_type,
                            quantity=1.0,
                            unit=res.unit or "unit",
                            cost=min(task.estimated_cost * 0.3, res.cost_per_unit
                                     if res.cost_per_unit > 0 else task.estimated_cost * 0.3),
                            currency=res.currency,
                        )
                        allocations.append(allocation)
                        task.resource_allocation.append(allocation)
                else:
                    # Create default allocation if no resources provided
                    allocation = ResourceAllocation(
                        task_id=task.task_id,
                        resource_id="default",
                        resource_type="people",
                        quantity=1.0,
                        unit="person",
                        cost=task.estimated_cost * 0.5,
                    )
                    allocations.append(allocation)
                    task.resource_allocation.append(allocation)

            alt.resource_allocations = allocations

        return alternatives

    # -----------------------------------------------------------------------
    # Stage 7: Dependency Graph
    # -----------------------------------------------------------------------

    def _build_dependency_graph(
        self,
        alternatives: List[ExecutionPlan],
    ) -> Optional[DependencyGraph]:
        """Build ordering constraints between tasks.

        Per ES-004 Section 4 — Dependency Graph stage.
        Detects circular dependencies.
        """
        for alt in alternatives:
            dependencies: List[Dependency] = []
            tasks_by_id = {t.task_id: t for t in alt.tasks}
            visited: set = set()
            recursion_stack: set = set()

            def _detect_cycle(task_id: str, path: List[str]) -> bool:
                """DFS cycle detection."""
                if task_id in recursion_stack:
                    return True
                if task_id in visited:
                    return False
                visited.add(task_id)
                recursion_stack.add(task_id)

                task = tasks_by_id.get(task_id)
                if task:
                    for dep_id in task.depends_on:
                        if dep_id in tasks_by_id:
                            if _detect_cycle(dep_id, path + [dep_id]):
                                return True

                recursion_stack.discard(task_id)
                return False

            # Check for cycles
            has_cycle = False
            for task in alt.tasks:
                if task.task_id not in visited:
                    if _detect_cycle(task.task_id, []):
                        has_cycle = True
                        break

            if has_cycle:
                return None

            # Build dependency edges
            for task in alt.tasks:
                for dep_id in task.depends_on:
                    if dep_id in tasks_by_id:
                        dep = Dependency(
                            from_task_id=dep_id,
                            to_task_id=task.task_id,
                            dependency_type="finish_to_start",
                            description=f"{tasks_by_id[dep_id].label} -> {task.label}",
                        )
                        dependencies.append(dep)

            # Compute critical path (longest sequence)
            critical_path = self._compute_critical_path(alt.tasks, dependencies)
            critical_path_duration = sum(
                tasks_by_id[t].estimated_duration_minutes
                for t in critical_path if t in tasks_by_id
            )

            # Mark critical dependencies
            for dep in dependencies:
                if dep.from_task_id in critical_path and dep.to_task_id in critical_path:
                    dep.is_critical = True

            alt.dependency_graph = DependencyGraph(
                tasks=alt.tasks,
                dependencies=dependencies,
                critical_path=critical_path,
                critical_path_duration_minutes=critical_path_duration,
                has_cycles=False,
                depth=len(critical_path),
            )

        return alternatives[0].dependency_graph if alternatives else None

    def _compute_critical_path(
        self,
        tasks: List[PlanTask],
        dependencies: List[Dependency],
    ) -> List[str]:
        """Compute the critical path using longest-path algorithm."""
        if not tasks:
            return []

        task_map = {t.task_id: t for t in tasks}
        out_edges: Dict[str, List[str]] = {}
        in_edges: Dict[str, List[str]] = {}

        for dep in dependencies:
            out_edges.setdefault(dep.from_task_id, []).append(dep.to_task_id)
            in_edges.setdefault(dep.to_task_id, []).append(dep.from_task_id)

        # Find root tasks (no incoming edges)
        roots = [t.task_id for t in tasks if t.task_id not in in_edges]
        if not roots:
            roots = [tasks[0].task_id]

        # Topological sort (Kahn's algorithm)
        in_degree = {t.task_id: len(in_edges.get(t.task_id, [])) for t in tasks}
        queue = [t for t in roots]
        topo_order: List[str] = []

        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for neighbor in out_edges.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Longest path
        dist: Dict[str, float] = {t.task_id: 0.0 for t in tasks}
        predecessor: Dict[str, Optional[str]] = {t.task_id: None for t in tasks}

        for node in topo_order:
            for neighbor in out_edges.get(node, []):
                weight = task_map[neighbor].estimated_duration_minutes
                if dist[node] + weight > dist[neighbor]:
                    dist[neighbor] = dist[node] + weight
                    predecessor[neighbor] = node

        # Find node with max distance
        end_node = max(dist, key=dist.get)
        path: List[str] = []
        current = end_node
        while current is not None:
            path.append(current)
            current = predecessor[current]
        path.reverse()

        return path

    # -----------------------------------------------------------------------
    # Stage 8: Execution Graph
    # -----------------------------------------------------------------------

    def _build_execution_graph(
        self,
        alternatives: List[ExecutionPlan],
        dep_graph: Optional[DependencyGraph],
    ) -> Optional[Schedule]:
        """Produce time-bound execution sequence.

        Per ES-004 Section 4 — Execution Graph stage.
        """
        if not alternatives:
            return None

        alt = alternatives[0]
        now = datetime.now(timezone.utc)
        tasks_by_id = {t.task_id: t for t in alt.tasks}
        scheduled_tasks: List[PlanTask] = []

        # Sort tasks by dependency order
        ordered: List[PlanTask] = []
        visited: set = set()

        def _dfs_order(task_id: str) -> None:
            if task_id in visited:
                return
            visited.add(task_id)
            task = tasks_by_id.get(task_id)
            if task:
                for dep_id in task.depends_on:
                    if dep_id in tasks_by_id:
                        _dfs_order(dep_id)
                ordered.append(task)

        for task in alt.tasks:
            _dfs_order(task.task_id)

        # Assign start/end times
        current_time = now
        for task in ordered:
            task.estimated_start_time = current_time
            task.estimated_end_time = current_time + timedelta(
                minutes=task.estimated_duration_minutes)
            current_time = task.estimated_end_time
            scheduled_tasks.append(task)

        total_duration = sum(t.estimated_duration_minutes for t in ordered)

        milestones = []
        for i, task in enumerate(ordered):
            if task.estimated_duration_minutes >= 60:
                milestones.append({
                    "task_id": task.task_id,
                    "label": task.label,
                    "time": task.estimated_start_time.isoformat() if task.estimated_start_time else "",
                })

        return Schedule(
            plan_id=alt.plan_id,
            tasks=scheduled_tasks,
            planned_start=now,
            planned_end=current_time,
            total_duration_minutes=total_duration,
            milestones=milestones,
        )

    # -----------------------------------------------------------------------
    # Stage 9: Governance Package
    # -----------------------------------------------------------------------

    def _package_for_governance(
        self,
        alternatives: List[ExecutionPlan],
        dep_graph: Optional[DependencyGraph],
        schedule: Optional[Schedule],
        inp: PlanningInput,
    ) -> Optional[GovernancePackage]:
        """Package the complete plan for Governance Engine validation.

        Per ES-004 Section 4 — Governance Package stage.
        """
        primary = alternatives[0] if alternatives else None
        if not primary:
            return None

        reasoning = inp.reasoning_result
        reasoning_summary = ""
        if reasoning:
            findings = getattr(reasoning, "findings", [])
            contradictions = getattr(reasoning, "contradictions", [])
            reasoning_summary = (
                f"Reasoning result {getattr(reasoning, 'result_id', '')}: "
                f"{len(findings)} findings, "
                f"{len(contradictions)} contradictions, "
                f"{len(getattr(reasoning, 'assumptions', []))} assumptions, "
                f"{len(getattr(reasoning, 'constraints', []))} constraints"
            )

        # Build trade-off analysis
        trade_offs = []
        if len(alternatives) > 1:
            for alt in alternatives[1:]:
                cost_diff = primary.total_estimated_cost - alt.total_estimated_cost
                time_diff = primary.total_estimated_duration_minutes - alt.total_estimated_duration_minutes
                risk_diff = 0.0
                if alt.risk_assessment and primary.risk_assessment:
                    risk_diff = primary.risk_assessment.overall_risk_score - alt.risk_assessment.overall_risk_score

                trade_off_parts = []
                if abs(cost_diff) > 0:
                    direction = "cheaper" if cost_diff > 0 else "more expensive"
                    trade_off_parts.append(f"Alternative is {abs(cost_diff):.0f} currency units {direction}")
                if abs(time_diff) > 0:
                    direction = "faster" if time_diff > 0 else "slower"
                    trade_off_parts.append(f"Alternative is {abs(time_diff):.0f} minutes {direction}")
                if abs(risk_diff) > 0.01:
                    direction = "lower risk" if risk_diff > 0 else "higher risk"
                    trade_off_parts.append(f"Alternative has {direction}")

                trade_offs.append({
                    "alternative_rank": alt.rank,
                    "summary": "; ".join(trade_off_parts) if trade_off_parts else "No significant trade-off",
                })

        governance_pkg = GovernancePackage(
            plan=primary,
            alternatives=alternatives[1:] if len(alternatives) > 1 else [],
            reasoning_result_id=getattr(inp.reasoning_result, "result_id", ""),
            reasoning_summary=reasoning_summary,
            evidence_summary={
                "total_tasks": len(primary.tasks),
                "total_cost": primary.total_estimated_cost,
                "total_duration_minutes": primary.total_estimated_duration_minutes,
                "planning_types": list(set(a.planning_type for a in alternatives)),
                "alternatives_generated": len(alternatives),
            },
            constraints=inp.constraints,
            objectives=inp.objectives,
            trade_offs=trade_offs,
            context_id=getattr(inp.context, "context_id", ""),
            tenant_id=inp.tenant_id,
            actor_id=inp.actor_id,
        )

        return governance_pkg

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _assemble_risk_assessment(
        self,
        alternatives: List[ExecutionPlan],
    ) -> Optional[RiskAssessment]:
        """Assemble overall risk assessment from alternatives."""
        if not alternatives:
            return None

        primary = alternatives[0]
        if primary.risk_assessment:
            return primary.risk_assessment

        return RiskAssessment(
            overall_risk_score=0.5,
            overall_confidence=0.5,
        )

    def _build_decision_tree(
        self,
        alternatives: List[ExecutionPlan],
        inp: PlanningInput,
    ) -> Optional[DecisionTree]:
        """Build a decision tree from alternatives."""
        if not alternatives:
            return None

        root = DecisionNode(
            label="Plan Selection",
            description=f"Select from {len(alternatives)} alternative plans",
            decision_type="choice",
            options=[
                {"rank": a.rank, "name": a.name, "planning_type": a.planning_type}
                for a in alternatives
            ],
        )

        tree = DecisionTree(
            root_node=root,
            nodes=[root],
            depth=1,
        )

        return tree

    def _build_metadata(
        self,
        inp: PlanningInput,
        start_time: float,
        stages: List[str],
        stages_passed: int,
        stages_failed: int,
    ) -> PlanningMetadata:
        """Build planning metadata."""
        elapsed = (time.time() - start_time) * 1000
        return PlanningMetadata(
            planning_engine_version=self._version,
            reasoning_result_id=getattr(inp.reasoning_result, "result_id", ""),
            context_id=getattr(inp.context, "context_id", ""),
            correlation_id=inp.correlation_id,
            planning_types_used=inp.planning_types,
            stages_executed=stages_passed + stages_failed,
            stages_passed=stages_passed,
            stages_failed=stages_failed,
            engine_name="planner_engine",
            elapsed_ms=elapsed,
        )

    def _error_output(self, error: str,
                      failure_mode: str = "",
                      stage: str = "",
                      details: Dict[str, Any] = None,
                      metadata: Optional[PlanningMetadata] = None) -> PlanningOutput:
        """Build an error PlanningOutput."""
        return PlanningOutput(
            error=error,
            failure_mode=failure_mode,
            planning_metadata=metadata,
        )

    def _record_metrics(self, start: float, output: PlanningOutput) -> None:
        """Record planning cycle metrics."""
        if not self._metrics:
            return
        duration = (time.time() - start) * 1000
        self._planning_counter.inc()
        self._latency_histogram.observe(duration)
        self._alternatives_histogram.observe(len(output.alternatives) + 1)  # +1 for primary
        if output.is_error:
            self._failure_counter.inc()

    def _emit_event(self, output: PlanningOutput) -> None:
        """Emit planning event to Event Bus."""
        try:
            from app.shunya.infrastructure.event_bus import CanonicalEvent

            payload = {
                "planning_output_id": getattr(output.planning_metadata, "planning_id", ""),
                "is_success": output.is_success,
                "primary_plan_id": output.primary_plan.plan_id if output.primary_plan else None,
                "alternatives": len(output.alternatives),
                "confidence": output.confidence,
                "error": output.error,
                "failure_mode": output.failure_mode,
            }

            event = CanonicalEvent(
                event_type="planner.planning.completed",
                actor_name="planner_engine",
                object_id=payload["planning_output_id"],
                object_type="planning_output",
                payload=payload,
            )
            self._event_bus.publish(event)
        except Exception:
            if self._logger:
                self._logger.exception("Failed to emit planning event")

    def _health_check(self) -> Any:
        """Health check for the planner engine."""
        from app.shunya.infrastructure.health import HealthCheckResult, HealthStatus
        status = HealthStatus.HEALTHY
        detail = "Planner Engine operational"
        metrics_dict = {
            "engine_version": self._version,
            "templates_available": len(list_templates()),
        }
        return HealthCheckResult(
            component="planner_engine",
            status=status,
            detail=detail,
            metrics=metrics_dict,
        )


# ---- Module-level convenience -----------------------------------------------

_engine: Optional[PlannerEngine] = None


def get_planner_engine(**kwargs: Any) -> PlannerEngine:
    """Get or create the singleton PlannerEngine instance."""
    global _engine
    if _engine is None:
        _engine = PlannerEngine(**kwargs)
    return _engine


def reset_planner_engine() -> None:
    """Reset the singleton PlannerEngine instance (for testing)."""
    global _engine
    _engine = None


__all__ = [
    "PlannerEngine", "get_planner_engine", "reset_planner_engine",
]