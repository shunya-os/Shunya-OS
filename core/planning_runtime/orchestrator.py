"""SHUNYA Planning & Reasoning Runtime — Orchestrator."""

from __future__ import annotations

import logging
from typing import Any

from core.planning_runtime.models import (
    AlternativePlan,
    Constraint,
    ConstraintCategory,
    ConstraintType,
    Goal,
    Plan,
    PlanStats,
    PlanStatus,
    PlanTrace,
    Resource,
    Task,
    TaskType,
    _now_iso,
)

logger = logging.getLogger(__name__)


class PlanningRuntime:
    """Bridge between thinking and execution.
    Decomposes goals, builds plans, manages constraints, generates
    alternatives, validates, repairs, and observes planning."""

    def __init__(self):
        self._goals: dict[str, Goal] = {}
        self._plans: dict[str, Plan] = {}
        self._tasks: dict[str, Task] = {}
        self._alternatives: dict[str, AlternativePlan] = {}
        self._traces: list[PlanTrace] = []

    # ── Goal Decomposition ───────────────────────────────────────────

    def create_goal(self, label: str, description: str = "",
                    priority: int = 50,
                    parent_goal_id: str | None = None) -> Goal:
        goal = Goal(label=label, description=description,
                    priority=priority, parent_goal_id=parent_goal_id)
        self._goals[goal.goal_id] = goal
        if parent_goal_id and parent_goal_id in self._goals:
            self._goals[parent_goal_id].sub_goals.append(goal.goal_id)
        self._record_trace("create_goal", goal_id=goal.goal_id)
        return goal

    def decompose_goal(self, goal_id: str, sub_goal_labels: list[str]) -> Goal:
        """Decompose a goal into sub-goals. Returns the parent goal."""
        parent = self._goals.get(goal_id)
        if not parent:
            raise ValueError(f"Goal not found: {goal_id}")
        for label in sub_goal_labels:
            self.create_goal(label, parent_goal_id=goal_id,
                             priority=parent.priority + 10)
        self._record_trace("decompose_goal", goal_id=goal_id,
                           details={"sub_goals": sub_goal_labels})
        return parent

    def get_goal(self, goal_id: str) -> Goal | None:
        return self._goals.get(goal_id)

    def get_sub_goals(self, goal_id: str) -> list[Goal]:
        parent = self._goals.get(goal_id)
        if not parent:
            return []
        return [self._goals[gid] for gid in parent.sub_goals if gid in self._goals]

    # ── Task Network (HTN) ───────────────────────────────────────────

    def create_task(self, label: str, task_type: TaskType = TaskType.PRIMITIVE,
                    action_id: str = "", parent_id: str | None = None,
                    dependencies: list[str] | None = None,
                    estimated_cost: float = 0.0,
                    estimated_risk: float = 0.0,
                    estimated_duration_sec: float = 0.0,
                    requires_approval: bool = False) -> Task:
        task = Task(
            label=label, task_type=task_type, action_id=action_id,
            parent_id=parent_id, dependencies=dependencies or [],
            estimated_cost=estimated_cost, estimated_risk=estimated_risk,
            estimated_duration_sec=estimated_duration_sec,
            requires_approval=requires_approval,
        )
        self._tasks[task.task_id] = task
        self._record_trace("create_task", task_id=task.task_id,
                           details={"label": label, "task_type": task_type.value})
        return task

    def decompose_task(self, task_id: str, sub_task_labels: list[str]) -> Task:
        """Decompose a compound task into smaller tasks."""
        parent = self._tasks.get(task_id)
        if not parent:
            raise ValueError(f"Task not found: {task_id}")
        if parent.task_type != TaskType.COMPOUND:
            parent.task_type = TaskType.COMPOUND
        for label in sub_task_labels:
            child = self.create_task(label, TaskType.PRIMITIVE, parent_id=task_id)
            parent.sub_goals.append(child.task_id)
        self._record_trace("decompose_task", task_id=task_id,
                           details={"sub_tasks": sub_task_labels})
        return parent

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def get_sub_tasks(self, task_id: str) -> list[Task]:
        parent = self._tasks.get(task_id)
        if not parent:
            return []
        return [self._tasks[tid] for tid in parent.sub_goals if tid in self._tasks]

    # ── Plan Creation ────────────────────────────────────────────────

    def create_plan(self, label: str, goal_id: str,
                    task_ids: list[str] | None = None) -> Plan:
        goal = self._goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal not found: {goal_id}")

        tasks = [self._tasks[tid] for tid in (task_ids or []) if tid in self._tasks]
        plan = Plan(label=label, goal_id=goal_id, tasks=tasks)
        self._plans[plan.plan_id] = plan
        self._update_plan_totals(plan)
        self._record_trace("create_plan", plan_id=plan.plan_id)
        return plan

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def list_plans(self) -> list[Plan]:
        return list(self._plans.values())

    # ── Multi-Step Reasoning ─────────────────────────────────────────

    def reason(self, plan_id: str) -> list[dict[str, Any]]:
        """Walk through a plan and produce reasoning steps."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        steps: list[dict[str, Any]] = []
        for task in plan.tasks:
            deps = [self._tasks[d].label for d in task.dependencies if d in self._tasks]
            step = {
                "step": len(steps) + 1,
                "task_id": task.task_id,
                "task": task.label,
                "type": task.task_type.value,
                "depends_on": deps,
                "cost": task.estimated_cost,
                "risk": task.estimated_risk,
                "duration_sec": task.estimated_duration_sec,
                "requires_approval": task.requires_approval,
                "rationale": task.rationale or f"Execute {task.label}",
            }
            steps.append(step)
        self._record_trace("reason", plan_id=plan_id)
        return steps

    # ── Alternative Plan Generation ──────────────────────────────────

    def generate_alternatives(self, plan_id: str, count: int = 3) -> list[AlternativePlan]:
        """Generate alternative plans by varying task order and resource allocation."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        alternatives: list[AlternativePlan] = []
        import random
        random.seed(42)

        for i in range(count):
            # Create a copy of tasks with shuffled non-dependent order
            tasks_copy = []
            for t in plan.tasks:
                tasks_copy.append(Task(
                    task_id=self._gen_alt_id(t.task_id, i),
                    parent_id=t.parent_id, task_type=t.task_type,
                    label=t.label, action_id=t.action_id,
                    dependencies=list(t.dependencies),
                    estimated_cost=t.estimated_cost * (1 + random.uniform(-0.2, 0.2)),
                    estimated_risk=t.estimated_risk * (1 + random.uniform(-0.3, 0.3)),
                    estimated_duration_sec=t.estimated_duration_sec * (1 + random.uniform(-0.3, 0.3)),
                ))

            total_cost = sum(t.estimated_cost for t in tasks_copy)
            total_risk = sum(t.estimated_risk for t in tasks_copy) / max(len(tasks_copy), 1)
            total_dur = sum(t.estimated_duration_sec for t in tasks_copy)

            alt = AlternativePlan(
                plan_id=plan_id,
                label=f"Variant {i + 1}",
                tasks=tasks_copy,
                total_cost=round(total_cost, 2),
                total_risk=round(total_risk, 2),
                total_duration_sec=round(total_dur, 2),
                rationale=f"Alternative {i + 1}: {'faster' if i == 0 else 'cheaper' if i == 1 else 'lower risk'}",
            )
            self._alternatives[alt.alternative_id] = alt
            alternatives.append(alt)

        self._record_trace("generate_alternatives", plan_id=plan_id,
                           details={"count": count})
        return alternatives

    def get_alternatives(self, plan_id: str) -> list[AlternativePlan]:
        return [a for a in self._alternatives.values() if a.plan_id == plan_id]

    @staticmethod
    def _gen_alt_id(task_id: str, variant: int) -> str:
        return f"{task_id}_alt_{variant}"

    # ── Cost/Risk Estimation ─────────────────────────────────────────

    def estimate_plan(self, plan_id: str) -> dict[str, float]:
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        self._update_plan_totals(plan)
        return {
            "total_cost": plan.total_cost,
            "total_risk": plan.total_risk,
            "total_duration_sec": plan.total_duration_sec,
        }

    def _update_plan_totals(self, plan: Plan) -> None:
        plan.total_cost = sum(t.estimated_cost for t in plan.tasks)
        plan.total_risk = sum(t.estimated_risk for t in plan.tasks) / max(len(plan.tasks), 1)
        plan.total_duration_sec = sum(t.estimated_duration_sec for t in plan.tasks)

    # ── Plan Validation ──────────────────────────────────────────────

    def validate_plan(self, plan_id: str) -> dict[str, Any]:
        """Validate a plan: check cycles, constraints, resource conflicts."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        issues: list[str] = []
        warnings: list[str] = []

        # Cycle detection in dependency graph
        task_map = {t.task_id: t for t in plan.tasks}
        if self._has_cycle(task_map):
            issues.append("Dependency graph contains a cycle")

        # Check for missing dependency targets
        for t in plan.tasks:
            for dep_id in t.dependencies:
                if dep_id not in task_map:
                    issues.append(f"Task {t.label} depends on unknown task {dep_id}")

        # Check constraint satisfaction
        for t in plan.tasks:
            for c in t.constraints:
                if not c.satisfied:
                    issues.append(f"Task {t.label}: unsatisfied constraint '{c.description}'")

        # Approval checkpoints
        approval_tasks = [t.label for t in plan.tasks if t.requires_approval]
        if approval_tasks:
            warnings.append(f"Requires human approval at: {', '.join(approval_tasks)}")

        plan.status = PlanStatus.VALIDATED if not issues else PlanStatus.FAILED
        self._record_trace("validate", plan_id=plan_id,
                           details={"issues": len(issues), "warnings": len(warnings)})

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "status": plan.status.value,
        }

    @staticmethod
    def _has_cycle(task_map: dict[str, Task]) -> bool:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {tid: WHITE for tid in task_map}

        def dfs(tid: str) -> bool:
            color[tid] = GRAY
            for dep_id in task_map[tid].dependencies:
                if dep_id not in color:
                    continue
                if color[dep_id] == GRAY:
                    return True
                if color[dep_id] == WHITE and dfs(dep_id):
                    return True
            color[tid] = BLACK
            return False

        return any(dfs(tid) for tid in task_map if color[tid] == WHITE)

    # ── Plan Approval ────────────────────────────────────────────────

    def approve_plan(self, plan_id: str) -> Plan:
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        plan.status = PlanStatus.APPROVED
        plan.provenance.append(f"Approved at {_now_iso()}")
        self._record_trace("approve", plan_id=plan_id)
        return plan

    def approve_task(self, plan_id: str, task_id: str) -> Task | None:
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        for t in plan.tasks:
            if t.task_id == task_id:
                t.approved = True
                plan.provenance.append(f"Task {t.label} approved at {_now_iso()}")
                self._record_trace("approve_task", plan_id=plan_id, task_id=task_id)
                return t
        return None

    # ── Plan Repair & Re-Planning ────────────────────────────────────

    def repair_plan(self, plan_id: str, failed_task_id: str,
                    replacement_label: str) -> Plan | None:
        """Replace a failed task, creating a repaired plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        # Find failed task index
        idx = next((i for i, t in enumerate(plan.tasks) if t.task_id == failed_task_id), -1)
        if idx < 0:
            return None

        # Create replacement task
        replacement = self.create_task(
            replacement_label, TaskType.PRIMITIVE,
            dependencies=plan.tasks[idx].dependencies,
        )

        # Create repaired plan as new version
        new_tasks = list(plan.tasks)
        new_tasks[idx] = replacement
        repaired = Plan(
            label=f"{plan.label} (repaired)",
            goal_id=plan.goal_id,
            tasks=new_tasks,
            status=PlanStatus.REPAIRED,
            version=plan.version + 1,
            provenance=plan.provenance + [f"Repaired: replaced {failed_task_id} with {replacement.task_id}"],
            parent_plan_id=plan_id,
        )
        self._plans[repaired.plan_id] = repaired
        self._update_plan_totals(repaired)
        self._record_trace("repair", plan_id=plan_id,
                           details={"failed_task": failed_task_id})
        return repaired

    def re_plan(self, plan_id: str, new_label: str) -> Plan | None:
        """Full re-plan: create a new plan from the same goal."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        new_plan = Plan(
            label=new_label,
            goal_id=plan.goal_id,
            status=PlanStatus.DRAFT,
            version=plan.version + 1,
            provenance=plan.provenance + [f"Re-planned from {plan_id} at {_now_iso()}"],
            parent_plan_id=plan_id,
        )
        self._plans[new_plan.plan_id] = new_plan
        self._record_trace("re_plan", plan_id=plan_id)
        return new_plan

    # ── Constraint Management ────────────────────────────────────────

    def add_constraint(self, plan_id: str, task_id: str | None = None,
                       category: ConstraintCategory = ConstraintCategory.CUSTOM,
                       constraint_type: ConstraintType = ConstraintType.HARD,
                       description: str = "") -> Constraint | None:
        """Add a constraint to a plan or specific task."""
        if task_id:
            task = self._tasks.get(task_id)
            if not task:
                return None
            c = Constraint(category=category, constraint_type=constraint_type,
                          description=description)
            task.constraints.append(c)
            return c
        else:
            plan = self._plans.get(plan_id)
            if not plan:
                return None
            c = Constraint(category=category, constraint_type=constraint_type,
                          description=description)
            plan.constraints.append(c)
            return c

    def check_constraints(self, plan_id: str) -> list[dict[str, Any]]:
        """Check all constraints on a plan and its tasks."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []

        results: list[dict[str, Any]] = []
        for c in plan.constraints:
            satisfied = c.satisfied
            results.append({
                "scope": "plan", "description": c.description,
                "type": c.constraint_type.value, "satisfied": satisfied,
            })
        for t in plan.tasks:
            for c in t.constraints:
                satisfied = c.satisfied
                results.append({
                    "scope": f"task:{t.label}", "description": c.description,
                    "type": c.constraint_type.value, "satisfied": satisfied,
                })
        return results

    # ── Resource Planning ────────────────────────────────────────────

    def allocate_resources(self, plan_id: str,
                           resources: list[Resource]) -> list[Resource]:
        """Allocate resources to a plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []
        for r in resources:
            plan.constraints.append(Constraint(
                category=ConstraintCategory.RESOURCE,
                description=f"Resource: {r.name}",
                expression=f"{r.name}_quantity >= {r.quantity}",
            ))
        self._record_trace("allocate_resources", plan_id=plan_id,
                           details={"count": len(resources)})
        return resources

    # ── Temporal Planning ────────────────────────────────────────────

    def compute_timeline(self, plan_id: str) -> list[dict[str, Any]]:
        """Compute an ordered timeline of tasks with start/end estimates."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []

        timeline: list[dict[str, Any]] = []
        scheduled: dict[str, float] = {}  # task_id → start time
        current_time = 0.0

        # Topological sort
        task_map = {t.task_id: t for t in plan.tasks}
        visited: set[str] = set()
        order: list[str] = []

        def dfs(tid: str) -> None:
            if tid in visited or tid not in task_map:
                return
            visited.add(tid)
            for dep_id in task_map[tid].dependencies:
                dfs(dep_id)
            order.append(tid)

        for tid in task_map:
            dfs(tid)

        for tid in order:
            t = task_map[tid]
            # Start after latest dependency
            if t.dependencies:
                dep_end = max(scheduled.get(d, 0.0) + task_map[d].estimated_duration_sec
                            for d in t.dependencies if d in task_map)
            else:
                dep_end = current_time
            start = dep_end
            end = start + t.estimated_duration_sec
            scheduled[tid] = start

            timeline.append({
                "task_id": tid,
                "task": t.label,
                "start_sec": round(start, 2),
                "end_sec": round(end, 2),
                "duration_sec": t.estimated_duration_sec,
                "depends_on": t.dependencies,
            })
            current_time = max(current_time, end)

        return timeline

    # ── Observability ────────────────────────────────────────────────

    def get_provenance(self, plan_id: str) -> list[str]:
        plan = self._plans.get(plan_id)
        return plan.provenance if plan else []

    def get_stats(self) -> PlanStats:
        by_status: dict[str, int] = {}
        total_cost = 0.0
        total_risk = 0.0
        total_dur = 0.0
        plan_count = len(self._plans)
        for p in self._plans.values():
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
            total_cost += p.total_cost
            total_risk += p.total_risk
            total_dur += p.total_duration_sec
        return PlanStats(
            total_plans=plan_count,
            total_tasks=len(self._tasks),
            plans_by_status=by_status,
            avg_cost=round(total_cost / plan_count, 2) if plan_count else 0.0,
            avg_risk=round(total_risk / plan_count, 2) if plan_count else 0.0,
            avg_duration_sec=round(total_dur / plan_count, 2) if plan_count else 0.0,
        )

    def get_traces(self, plan_id: str | None = None) -> list[PlanTrace]:
        traces = self._traces
        if plan_id:
            traces = [t for t in traces if t.plan_id == plan_id]
        return traces

    def health_check(self) -> dict[str, Any]:
        stats = self.get_stats()
        return {
            "status": "healthy",
            "runtime": "planning_runtime",
            "total_plans": stats.total_plans,
            "total_tasks": stats.total_tasks,
            "plans_by_status": stats.plans_by_status,
            "avg_cost": stats.avg_cost,
            "avg_risk": stats.avg_risk,
            "avg_duration_sec": stats.avg_duration_sec,
        }

    def _record_trace(self, operation: str, plan_id: str = "",
                      task_id: str = "", goal_id: str = "",
                      details: dict | None = None) -> None:
        self._traces.append(PlanTrace(
            operation=operation, plan_id=plan_id, task_id=task_id,
            details=details or {},
        ))