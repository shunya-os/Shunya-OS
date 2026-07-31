"""SHUNYA — Planner Engine plan templates (Phase G — ES-004).

Planning type implementations and reusable plan templates for the
10 composable planning types defined in ES-004 Section 5.

Architectural authority: ES-004 — Planner Engine Specification
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.shunya.planner.models import (
    ExecutionPlan, PlanTask, PlanningConstraint, PlanningType,
    Resource, ResourceAllocation, RiskAssessment,
    Schedule, DependencyGraph, TaskStatus,
)


# ---------------------------------------------------------------------------
# Template Registry
# ---------------------------------------------------------------------------

_PLAN_TEMPLATES: Dict[str, Dict[str, Any]] = {}


def register_template(name: str, description: str,
                      task_generator: callable,
                      metadata: Dict[str, Any] = None) -> None:
    """Register a plan template by name."""
    _PLAN_TEMPLATES[name] = {
        "name": name,
        "description": description,
        "task_generator": task_generator,
        "metadata": metadata or {},
    }


def get_template(name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a registered plan template."""
    return _PLAN_TEMPLATES.get(name)


def list_templates() -> List[str]:
    """List all registered plan template names."""
    return list(_PLAN_TEMPLATES.keys())


# ---------------------------------------------------------------------------
# Planning Type Implementations
# ---------------------------------------------------------------------------


def create_reactive_plan(reasoning_result: Any,
                         context: Any = None,
                         tenant_id: int = None,
                         actor_id: str = "") -> ExecutionPlan:
    """Reactive planning: generate a minimal plan for immediate action.

    Reactive plans have minimal analysis, few tasks (1-3), and
    prioritize speed to execution.
    """
    plan = ExecutionPlan(
        name="Reactive Action Plan",
        planning_type=PlanningType.REACTIVE.value,
        reasoning_result_id=getattr(reasoning_result, "result_id", ""),
        context_id=getattr(context, "context_id", ""),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )

    # Extract attention items from reasoning result
    attention_items = getattr(reasoning_result, "attention_items", [])
    findings = getattr(reasoning_result, "findings", [])

    if attention_items:
        for i, item in enumerate(attention_items[:3]):
            task = PlanTask(
                label=f"Address: {item}",
                description=f"Immediate action required: {item}",
                task_type="action",
                estimated_duration_minutes=30.0,
                estimated_cost=0.0,
                reasoning_finding_id=getattr(findings[i], "finding_id", None) if i < len(findings) else None,
            )
            plan.add_task(task)
    else:
        plan.add_task(PlanTask(
            label="Process Reasoning Result",
            description="Process the reasoning result and determine next actions",
            task_type="action",
            estimated_duration_minutes=15.0,
        ))

    return plan


def create_operational_plan(reasoning_result: Any,
                            template_name: str = "standard",
                            context: Any = None,
                            tenant_id: int = None,
                            actor_id: str = "") -> ExecutionPlan:
    """Operational planning: generate standardized, repeatable plans.

    Template-driven. Uses registered plan templates where available.
    """
    plan = ExecutionPlan(
        name=f"Operational Plan ({template_name})",
        planning_type=PlanningType.OPERATIONAL.value,
        reasoning_result_id=getattr(reasoning_result, "result_id", ""),
        context_id=getattr(context, "context_id", ""),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )

    template = get_template(template_name)
    if template:
        task_generator = template["task_generator"]
        tasks = task_generator(reasoning_result, context)
        for task in tasks:
            plan.add_task(task)
    else:
        # Default: generate generic operational tasks
        plan.add_task(PlanTask(
            label="Review Reasoning Result",
            description="Review and understand the reasoning result",
            estimated_duration_minutes=10.0,
        ))
        plan.add_task(PlanTask(
            label="Execute Action",
            description="Execute the recommended action",
            estimated_duration_minutes=60.0,
            depends_on=[plan.tasks[0].task_id] if plan.tasks else [],
        ))

    return plan


def create_strategic_plan(reasoning_result: Any,
                          constraints: List[PlanningConstraint] = None,
                          context: Any = None,
                          tenant_id: int = None,
                          actor_id: str = "") -> ExecutionPlan:
    """Strategic planning: multi-step plans with dependencies and trade-offs.

    Produces plans with multiple sequenced tasks, considering
    dependencies, resource needs, and risk.
    """
    plan = ExecutionPlan(
        name="Strategic Plan",
        planning_type=PlanningType.STRATEGIC.value,
        reasoning_result_id=getattr(reasoning_result, "result_id", ""),
        context_id=getattr(context, "context_id", ""),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )

    # Analyze findings to build appropriate tasks
    findings = getattr(reasoning_result, "findings", [])
    constraints_list = constraints or []

    # Phase 1: Analysis tasks
    analyze = PlanTask(
        label="Analyze Situation",
        description="Analyze the current situation based on reasoning findings",
        estimated_duration_minutes=30.0,
    )
    plan.add_task(analyze)

    # Phase 2: Plan tasks based on findings
    for finding in findings[:5]:
        task = PlanTask(
            label=f"Address: {finding.label or finding.finding_type}",
            description=finding.description or f"Process {finding.finding_type} finding",
            estimated_duration_minutes=45.0,
            reasoning_finding_id=finding.finding_id,
            depends_on=[analyze.task_id] if plan.tasks else [],
        )
        plan.add_task(task)

    # Phase 3: Review and validate
    if plan.tasks:
        last_task_id = plan.tasks[-1].task_id
        review = PlanTask(
            label="Review and Validate",
            description="Review all completed tasks for correctness",
            estimated_duration_minutes=20.0,
            depends_on=[last_task_id],
        )
        plan.add_task(review)

    # Apply constraints as metadata
    for c in constraints_list:
        plan.metadata[f"constraint_{c.constraint_type}"] = c.label

    return plan


def create_constraint_based_plan(reasoning_result: Any,
                                 constraints: List[PlanningConstraint],
                                 context: Any = None,
                                 tenant_id: int = None,
                                 actor_id: str = "") -> ExecutionPlan:
    """Constraint-based planning: generate plans satisfying explicit constraints.

    Uses hard constraints as mandatory and soft constraints as optimization
    targets. Produces a plan that satisfies all hard constraints.
    """
    plan = ExecutionPlan(
        name="Constraint-Based Plan",
        planning_type=PlanningType.CONSTRAINT_BASED.value,
        reasoning_result_id=getattr(reasoning_result, "result_id", ""),
        context_id=getattr(context, "context_id", ""),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )

    # Extract budget constraints
    budget_constraint = None
    time_constraint = None
    for c in constraints:
        if c.constraint_type == "budget":
            budget_constraint = c
        elif c.constraint_type == "time":
            time_constraint = c

    # Build tasks respecting constraints
    task = PlanTask(
        label="Execute Under Constraints",
        description=f"Execute plan with constraints: {', '.join(c.label for c in constraints)}",
        estimated_duration_minutes=float(getattr(time_constraint, "value", 60) or 60),
        estimated_cost=float(getattr(budget_constraint, "value", 0) or 0),
    )
    plan.add_task(task)

    # Budget metadata
    if budget_constraint:
        plan.metadata["budget_limit"] = str(budget_constraint.value)
    if time_constraint:
        plan.metadata["time_limit_minutes"] = str(time_constraint.value)

    return plan


def create_scenario_plan(reasoning_result: Any,
                         scenarios: List[Dict[str, Any]],
                         context: Any = None,
                         tenant_id: int = None,
                         actor_id: str = "") -> ExecutionPlan:
    """Scenario planning: generate plans for multiple possible futures.

    Each scenario produces its own set of tasks. The primary plan
    covers the most likely scenario.
    """
    primary_scenario = scenarios[0] if scenarios else {"name": "default"}

    plan = ExecutionPlan(
        name=f"Scenario Plan ({primary_scenario.get('name', 'default')})",
        planning_type=PlanningType.SCENARIO.value,
        reasoning_result_id=getattr(reasoning_result, "result_id", ""),
        context_id=getattr(context, "context_id", ""),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )

    plan.add_task(PlanTask(
        label=f"Execute Scenario: {primary_scenario.get('name', 'default')}",
        description=primary_scenario.get("description", "Execute the primary scenario plan"),
        estimated_duration_minutes=primary_scenario.get("estimated_minutes", 60),
        metadata={"scenario": primary_scenario},
    ))

    # Track alternative scenarios
    plan.metadata["scenarios"] = [s.get("name") for s in scenarios]

    return plan


def create_contingency_plan(reasoning_result: Any,
                            primary_plan: ExecutionPlan,
                            critical_task_ids: List[str] = None,
                            context: Any = None,
                            tenant_id: int = None,
                            actor_id: str = "") -> ExecutionPlan:
    """Contingency planning: primary plan + backups for critical path items.

    Adds contingency tasks for critical tasks that need fallback options.
    """
    plan = ExecutionPlan(
        name="Contingency Plan",
        planning_type=PlanningType.CONTINGENCY.value,
        reasoning_result_id=getattr(reasoning_result, "result_id", ""),
        context_id=getattr(context, "context_id", ""),
        tenant_id=tenant_id,
        actor_id=actor_id,
    )

    # Copy primary plan tasks
    for task in primary_plan.tasks:
        plan.add_task(task)

    critical_ids = set(critical_task_ids or [])
    for task in plan.tasks:
        if task.task_id in critical_ids:
            fallback = PlanTask(
                label=f"[Fallback] {task.label}",
                description=f"Contingency fallback for: {task.label}",
                estimated_duration_minutes=task.estimated_duration_minutes * 1.5,
                estimated_cost=task.estimated_cost * 1.2,
                depends_on=[task.task_id],
                metadata={"is_contingency": True, "primary_task_id": task.task_id},
            )
            plan.add_task(fallback)

    plan.metadata["contingency_count"] = len(critical_ids)
    return plan


# ---------------------------------------------------------------------------
# Built-in Plan Templates
# ---------------------------------------------------------------------------


def _generate_notification_tasks(reasoning_result: Any,
                                 context: Any = None) -> List[PlanTask]:
    """Generate tasks for a notification plan."""
    tasks = []
    tasks.append(PlanTask(
        label="Compose Notification",
        description="Compose the notification content from reasoning result",
        estimated_duration_minutes=5.0,
    ))
    tasks.append(PlanTask(
        label="Send Notification",
        description="Deliver the notification via appropriate channel",
        estimated_duration_minutes=2.0,
        depends_on=[tasks[0].task_id],
    ))
    return tasks


def _generate_review_tasks(reasoning_result: Any,
                           context: Any = None) -> List[PlanTask]:
    """Generate tasks for a review plan."""
    tasks = []
    tasks.append(PlanTask(
        label="Gather Review Materials",
        description="Collect all materials needed for review",
        estimated_duration_minutes=15.0,
    ))
    tasks.append(PlanTask(
        label="Conduct Review",
        description="Review the reasoning results and context",
        estimated_duration_minutes=30.0,
        depends_on=[tasks[0].task_id],
    ))
    tasks.append(PlanTask(
        label="Document Review Outcome",
        description="Document the findings and recommendations from review",
        estimated_duration_minutes=10.0,
        depends_on=[tasks[1].task_id],
    ))
    return tasks


def _generate_investigation_tasks(reasoning_result: Any,
                                  context: Any = None) -> List[PlanTask]:
    """Generate tasks for an investigation plan."""
    tasks = []
    tasks.append(PlanTask(
        label="Identify Investigation Scope",
        description="Define the scope and boundaries of the investigation",
        estimated_duration_minutes=20.0,
    ))
    tasks.append(PlanTask(
        label="Gather Evidence",
        description="Collect relevant evidence and data",
        estimated_duration_minutes=60.0,
        depends_on=[tasks[0].task_id],
    ))
    tasks.append(PlanTask(
        label="Analyze Findings",
        description="Analyze collected evidence and draw conclusions",
        estimated_duration_minutes=45.0,
        depends_on=[tasks[1].task_id],
    ))
    tasks.append(PlanTask(
        label="Report Results",
        description="Document and report investigation results",
        estimated_duration_minutes=30.0,
        depends_on=[tasks[2].task_id],
    ))
    return tasks


# Register built-in templates
register_template("notification", "Send a notification or alert",
                  _generate_notification_tasks,
                  {"category": "communication", "typical_duration_min": 10})
register_template("review", "Review and evaluate a situation",
                  _generate_review_tasks,
                  {"category": "analysis", "typical_duration_min": 60})
register_template("investigation", "Investigate and report on a finding",
                  _generate_investigation_tasks,
                  {"category": "analysis", "typical_duration_min": 180})


# ---------------------------------------------------------------------------
# Planning Type Dispatcher
# ---------------------------------------------------------------------------

_PLANNING_DISPATCH: Dict[str, callable] = {
    PlanningType.REACTIVE.value: create_reactive_plan,
    PlanningType.OPERATIONAL.value: create_operational_plan,
    PlanningType.STRATEGIC.value: create_strategic_plan,
    PlanningType.CONSTRAINT_BASED.value: create_constraint_based_plan,
    PlanningType.SCENARIO.value: create_scenario_plan,
    PlanningType.CONTINGENCY.value: create_contingency_plan,
}


def dispatch_planning_type(planning_type: str) -> Optional[callable]:
    """Get the planner function for a given planning type."""
    return _PLANNING_DISPATCH.get(planning_type)


# ---------------------------------------------------------------------------
# Utility: Combine multiple plans
# ---------------------------------------------------------------------------


def merge_plans(plans: List[ExecutionPlan]) -> ExecutionPlan:
    """Merge multiple plans into one (for hierarchical planning).

    Combines tasks from all plans, adjusting dependencies to maintain
    ordering across plan boundaries.
    """
    if not plans:
        raise ValueError("Cannot merge empty plan list")

    base = plans[0]
    plan_ids_seen = {base.plan_id}

    for plan in plans[1:]:
        if plan.plan_id in plan_ids_seen:
            continue
        plan_ids_seen.add(plan.plan_id)

        # Map old task IDs to new task IDs (copy won't collide since we let __post_init__ generate them)
        for task in plan.tasks:
            base.add_task(task)

        # Aggregate costs and durations
        base.total_estimated_cost += plan.total_estimated_cost
        base.total_estimated_duration_minutes = max(
            base.total_estimated_duration_minutes,
            plan.total_estimated_duration_minutes,
        )

    base.name = f"Merged Plan ({len(plans)} sub-plans)"
    base.metadata["merged_plan_ids"] = list(plan_ids_seen)
    return base


__all__ = [
    # Template registry
    "register_template", "get_template", "list_templates",

    # Planning type implementations
    "create_reactive_plan", "create_operational_plan",
    "create_strategic_plan", "create_constraint_based_plan",
    "create_scenario_plan", "create_contingency_plan",

    # Dispatcher
    "dispatch_planning_type",

    # Utility
    "merge_plans",
]