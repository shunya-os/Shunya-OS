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

The engine does NOT:
  - Execute plans (Executor Engine)
  - Approve plans (Governance Engine)
  - Change knowledge (Knowledge Engine)
  - Learn from outcomes (Learning Engine)
  - Bypass governance (Governance Engine)
  - Reason (generate new conclusions) (Reasoning Engine)
  - Access credentials (Credential Store)

Architectural authority: ES-004 — Planner Engine Specification
"""

from app.shunya.planner.models import (
    # Enums
    PlanningType, PlanState, TaskStatus,
    OptimizationDimension, ResourceType, FailureMode,

    # Resources
    Resource, ResourcePool,

    # Constraints & Objectives
    PlanningConstraint, Objective,

    # Tasks & Plans
    PlanTask, ExecutionPlan,

    # Dependencies & Scheduling
    Dependency, DependencyGraph, Schedule,

    # Resource Allocation
    ResourceAllocation,

    # Risk
    RiskAssessment,

    # Decision Trees
    DecisionNode, DecisionTree,

    # Governance
    GovernancePackage,

    # Input/Output Contracts
    PlanningInput, PlanningOutput,

    # Metadata
    PlanningMetadata,

    # Optimization
    OptimizationCriteria,

    # Error
    PlanningError,
)

from app.shunya.planner.engine import (
    PlannerEngine, get_planner_engine, reset_planner_engine,
)

from app.shunya.planner.templates import (
    register_template, get_template, list_templates,
    create_reactive_plan, create_operational_plan,
    create_strategic_plan, create_constraint_based_plan,
    create_scenario_plan, create_contingency_plan,
    dispatch_planning_type, merge_plans,
)

# Legacy backward-compatible exports (maintains existing call sites)
from app.shunya.planner._legacy_planner import (
    PlannerLayer, ItineraryDay, ItineraryPlan,
)

__all__ = [
    # Enums
    "PlanningType", "PlanState", "TaskStatus",
    "OptimizationDimension", "ResourceType", "FailureMode",

    # Resources
    "Resource", "ResourcePool",

    # Constraints & Objectives
    "PlanningConstraint", "Objective",

    # Tasks & Plans
    "PlanTask", "ExecutionPlan",

    # Dependencies & Scheduling
    "Dependency", "DependencyGraph", "Schedule",

    # Resource Allocation
    "ResourceAllocation",

    # Risk
    "RiskAssessment",

    # Decision Trees
    "DecisionNode", "DecisionTree",

    # Governance
    "GovernancePackage",

    # Input/Output Contracts
    "PlanningInput", "PlanningOutput",

    # Metadata
    "PlanningMetadata",

    # Optimization
    "OptimizationCriteria",

    # Error
    "PlanningError",

    # Engine
    "PlannerEngine", "get_planner_engine", "reset_planner_engine",

    # Templates
    "register_template", "get_template", "list_templates",
    "create_reactive_plan", "create_operational_plan",
    "create_strategic_plan", "create_constraint_based_plan",
    "create_scenario_plan", "create_contingency_plan",
    "dispatch_planning_type", "merge_plans",

    # Legacy exports (backward compatibility)
    "PlannerLayer", "ItineraryDay", "ItineraryPlan",
]