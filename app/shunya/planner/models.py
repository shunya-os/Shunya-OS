"""SHUNYA — Planner Engine canonical models (Phase G — ES-004).

Canonical plan data models: immutable representations of plans,
tasks, dependencies, resource allocations, schedules, risk assessments,
and governance packages. Every plan object retains provenance back to
the Reasoning Engine, Knowledge Engine, and Context Fusion.

Architectural authority: ES-004 — Planner Engine Specification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PlanningType(Enum):
    """Composable planning types supported by the Planner Engine."""
    REACTIVE = "reactive"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    HIERARCHICAL = "hierarchical"
    CONSTRAINT_BASED = "constraint_based"
    RESOURCE_AWARE = "resource_aware"
    SCENARIO = "scenario"
    CONTINGENCY = "contingency"
    LONG_TERM = "long_term"
    MULTI_OBJECTIVE = "multi_objective"


class PlanState(Enum):
    """Lifecycle state of an execution plan."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    REVIEW_REQUIRED = "review_required"


class TaskStatus(Enum):
    """Status of an individual task within a plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class OptimizationDimension(Enum):
    """Dimensions for multi-objective optimization."""
    TIME = "time"
    COST = "cost"
    RISK = "risk"
    RESOURCES = "resources"
    BUSINESS_OBJECTIVES = "business_objectives"
    HUMAN_PREFERENCES = "human_preferences"


class ResourceType(Enum):
    """Types of resources that can be allocated to tasks."""
    PEOPLE = "people"
    SYSTEMS = "systems"
    TIME = "time"
    MONEY = "money"
    EXTERNAL_SERVICES = "external_services"


class FailureMode(Enum):
    """Failure modes for the planning pipeline."""
    IMPOSSIBLE_PLAN = "impossible_plan"
    RESOURCE_CONFLICT = "resource_conflict"
    POLICY_CONFLICT = "policy_conflict"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MISSING_RESOURCES = "missing_resources"
    UNCERTAIN_ESTIMATES = "uncertain_estimates"
    LOW_CONFIDENCE = "low_confidence"
    INCOMPLETE_GOALS = "incomplete_goals"


# ---------------------------------------------------------------------------
# Resource Model
# ---------------------------------------------------------------------------


@dataclass
class Resource:
    """A resource available for planning.

    Resources represent people, systems, time, money, or external services
    that can be allocated to tasks.
    """
    resource_id: str = ""
    resource_type: str = ResourceType.PEOPLE.value
    label: str = ""
    description: str = ""
    total_capacity: float = 0.0
    available_capacity: float = 0.0
    unit: str = ""
    cost_per_unit: float = 0.0
    currency: str = "INR"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.resource_id:
            self.resource_id = str(uuid.uuid4())
        if self.available_capacity == 0.0 and self.total_capacity > 0.0:
            self.available_capacity = self.total_capacity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "label": self.label,
            "description": self.description,
            "total_capacity": self.total_capacity,
            "available_capacity": self.available_capacity,
            "unit": self.unit,
            "cost_per_unit": self.cost_per_unit,
            "currency": self.currency,
            "metadata": self.metadata,
        }


@dataclass
class ResourcePool:
    """A collection of available resources for a planning cycle."""
    resources: List[Resource] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def find_by_type(self, resource_type: str) -> List[Resource]:
        return [r for r in self.resources if r.resource_type == resource_type]

    def find_by_id(self, resource_id: str) -> Optional[Resource]:
        for r in self.resources:
            if r.resource_id == resource_id:
                return r
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resources": [r.to_dict() for r in self.resources],
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Constraint Model
# ---------------------------------------------------------------------------


@dataclass
class PlanningConstraint:
    """An explicit boundary on the planning process.

    Constraints represent limits on budget, time, resources, compliance,
    or preferences that must be respected.
    """
    constraint_id: str = ""
    constraint_type: str = ""
    label: str = ""
    description: str = ""
    value: Any = None
    unit: str = ""
    is_hard: bool = True  # Hard = must satisfy, soft = optimize toward
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.constraint_id:
            self.constraint_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.constraint_type,
            "label": self.label,
            "description": self.description,
            "value": str(self.value) if self.value is not None else None,
            "unit": self.unit,
            "is_hard": self.is_hard,
            "weight": self.weight,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Objective Model
# ---------------------------------------------------------------------------


@dataclass
class Objective:
    """A human or system goal to be achieved by the plan."""
    objective_id: str = ""
    label: str = ""
    description: str = ""
    priority: float = 1.0  # Higher = more important
    target_value: Any = None
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective_id:
            self.objective_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "label": self.label,
            "description": self.description,
            "priority": self.priority,
            "target_value": str(self.target_value) if self.target_value is not None else None,
            "unit": self.unit,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Plan Task Model
# ---------------------------------------------------------------------------


@dataclass
class PlanTask:
    """A single task within an execution plan.

    Each task carries provenance, resource allocation, time estimates,
    cost estimates, risk assessment, and status tracking.
    """
    task_id: str = ""
    label: str = ""
    description: str = ""
    parent_task_id: Optional[str] = None
    task_type: str = "action"
    status: str = TaskStatus.PENDING.value

    # Time estimates
    estimated_duration_minutes: float = 0.0
    estimated_start_time: Optional[datetime] = None
    estimated_end_time: Optional[datetime] = None

    # Cost estimates
    estimated_cost: float = 0.0
    currency: str = "INR"

    # Risk
    risk_score: float = 0.5  # Canonical 0.0-1.0
    risk_description: str = ""

    # Resource allocation
    resource_allocation: List[ResourceAllocation] = field(default_factory=list)

    # Dependencies
    depends_on: List[str] = field(default_factory=list)

    # Provenance
    reasoning_finding_id: Optional[str] = None
    knowledge_refs: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    @property
    def duration_hours(self) -> float:
        return self.estimated_duration_minutes / 60.0

    @property
    def is_ready(self) -> bool:
        return all(dep in ["", "completed"] for dep in self.depends_on)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "label": self.label,
            "description": self.description,
            "parent_task_id": self.parent_task_id,
            "task_type": self.task_type,
            "status": self.status,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "estimated_start_time": self.estimated_start_time.isoformat() if self.estimated_start_time else None,
            "estimated_end_time": self.estimated_end_time.isoformat() if self.estimated_end_time else None,
            "estimated_cost": self.estimated_cost,
            "currency": self.currency,
            "risk_score": self.risk_score,
            "risk_description": self.risk_description,
            "resource_allocation": [ra.to_dict() for ra in self.resource_allocation],
            "depends_on": self.depends_on,
            "reasoning_finding_id": self.reasoning_finding_id,
            "knowledge_refs": self.knowledge_refs,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Resource Allocation Model
# ---------------------------------------------------------------------------


@dataclass
class ResourceAllocation:
    """Allocation of a resource to a specific task."""
    allocation_id: str = ""
    task_id: str = ""
    resource_id: str = ""
    resource_type: str = ""
    quantity: float = 1.0
    unit: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cost: float = 0.0
    currency: str = "INR"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.allocation_id:
            self.allocation_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "task_id": self.task_id,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "quantity": self.quantity,
            "unit": self.unit,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "cost": self.cost,
            "currency": self.currency,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Dependency Graph Models
# ---------------------------------------------------------------------------


@dataclass
class Dependency:
    """A directed dependency between two tasks."""
    from_task_id: str = ""
    to_task_id: str = ""
    dependency_type: str = "finish_to_start"  # finish_to_start, start_to_start, etc.
    lag_minutes: float = 0.0
    description: str = ""
    is_critical: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_task_id": self.from_task_id,
            "to_task_id": self.to_task_id,
            "dependency_type": self.dependency_type,
            "lag_minutes": self.lag_minutes,
            "description": self.description,
            "is_critical": self.is_critical,
        }


@dataclass
class DependencyGraph:
    """The complete dependency structure of a plan.

    Includes the critical path — the longest sequence of dependent tasks
    that determines the minimum plan duration.
    """
    tasks: List[PlanTask] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)
    critical_path_duration_minutes: float = 0.0
    has_cycles: bool = False
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def find_upstream(self, task_id: str) -> List[PlanTask]:
        """Find all tasks that the given task depends on."""
        task_ids = {d.from_task_id for d in self.dependencies if d.to_task_id == task_id}
        return [t for t in self.tasks if t.task_id in task_ids]

    def find_downstream(self, task_id: str) -> List[PlanTask]:
        """Find all tasks that depend on the given task."""
        task_ids = {d.to_task_id for d in self.dependencies if d.from_task_id == task_id}
        return [t for t in self.tasks if t.task_id in task_ids]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "critical_path": self.critical_path,
            "critical_path_duration_minutes": self.critical_path_duration_minutes,
            "has_cycles": self.has_cycles,
            "depth": self.depth,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Schedule Model
# ---------------------------------------------------------------------------


@dataclass
class Schedule:
    """Time-bound execution sequence for a plan."""
    plan_id: str = ""
    tasks: List[PlanTask] = field(default_factory=list)
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    total_duration_minutes: float = 0.0
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration_hours(self) -> float:
        return self.total_duration_minutes / 60.0

    @property
    def total_duration_days(self) -> float:
        return self.total_duration_hours / 24.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "tasks": len(self.tasks),
            "planned_start": self.planned_start.isoformat() if self.planned_start else None,
            "planned_end": self.planned_end.isoformat() if self.planned_end else None,
            "total_duration_minutes": self.total_duration_minutes,
            "milestones": self.milestones,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Risk Assessment Model
# ---------------------------------------------------------------------------


@dataclass
class RiskAssessment:
    """Per-plan and per-task risk assessment.

    Risk is assessed on the canonical 0.0-1.0 confidence scale:
      0.0 = certain failure, 1.0 = certain success.
    """
    overall_risk_score: float = 0.5
    overall_confidence: float = 0.5
    per_task_risk: Dict[str, float] = field(default_factory=dict)
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_risk_score": round(self.overall_risk_score, 4),
            "overall_confidence": round(self.overall_confidence, 4),
            "per_task_risk": self.per_task_risk,
            "risk_factors": self.risk_factors,
            "assumptions": self.assumptions,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Execution Plan Model
# ---------------------------------------------------------------------------


@dataclass
class ExecutionPlan:
    """A complete, structured execution plan.

    The primary output of the Planner Engine. Contains tasks, dependencies,
    resource allocations, schedule, and risk assessment.
    """
    plan_id: str = ""
    name: str = ""
    description: str = ""
    planning_type: str = PlanningType.OPERATIONAL.value

    # Core structure
    tasks: List[PlanTask] = field(default_factory=list)
    dependency_graph: Optional[DependencyGraph] = None
    schedule: Optional[Schedule] = None
    resource_allocations: List[ResourceAllocation] = field(default_factory=list)

    # Estimates
    total_estimated_cost: float = 0.0
    total_estimated_duration_minutes: float = 0.0
    currency: str = "INR"

    # Risk and confidence
    risk_assessment: Optional[RiskAssessment] = None
    confidence: float = 0.5

    # State
    state: str = PlanState.DRAFT.value
    rank: int = 0  # Ranking among alternatives (1 = best)

    # Provenance
    reasoning_result_id: str = ""
    context_id: str = ""
    tenant_id: Optional[int] = None
    actor_id: str = ""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.plan_id:
            self.plan_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def add_task(self, task: PlanTask) -> None:
        self.tasks.append(task)

    def find_task(self, task_id: str) -> Optional[PlanTask]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    @property
    def total_duration_hours(self) -> float:
        return self.total_estimated_duration_minutes / 60.0

    @property
    def total_duration_days(self) -> float:
        return self.total_duration_hours / 24.0

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def completed_tasks(self) -> List[PlanTask]:
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED.value]

    @property
    def blocked_tasks(self) -> List[PlanTask]:
        return [t for t in self.tasks if t.status == TaskStatus.BLOCKED.value]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "planning_type": self.planning_type,
            "tasks": [t.to_dict() for t in self.tasks],
            "dependency_graph": self.dependency_graph.to_dict() if self.dependency_graph else None,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "resource_allocations": [ra.to_dict() for ra in self.resource_allocations],
            "total_estimated_cost": self.total_estimated_cost,
            "total_estimated_duration_minutes": self.total_estimated_duration_minutes,
            "currency": self.currency,
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "confidence": round(self.confidence, 4),
            "state": self.state,
            "rank": self.rank,
            "reasoning_result_id": self.reasoning_result_id,
            "context_id": self.context_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Decision Tree Model
# ---------------------------------------------------------------------------


@dataclass
class DecisionNode:
    """A single decision point in a decision tree."""
    node_id: str = ""
    label: str = ""
    description: str = ""
    parent_node_id: Optional[str] = None
    decision_type: str = "choice"  # choice, branch, outcome
    options: List[Dict[str, Any]] = field(default_factory=list)
    selected_option: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "description": self.description,
            "parent_node_id": self.parent_node_id,
            "decision_type": self.decision_type,
            "options": self.options,
            "selected_option": self.selected_option,
            "metadata": self.metadata,
        }


@dataclass
class DecisionTree:
    """A branching structure showing decision points and their consequences."""
    root_node: Optional[DecisionNode] = None
    nodes: List[DecisionNode] = field(default_factory=list)
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: DecisionNode) -> None:
        self.nodes.append(node)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_node": self.root_node.to_dict() if self.root_node else None,
            "nodes": [n.to_dict() for n in self.nodes],
            "depth": self.depth,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Governance Package Model
# ---------------------------------------------------------------------------


@dataclass
class GovernancePackage:
    """The complete plan packaged for Governance Engine validation.

    Contains the execution plan, alternatives, evidence chains, reasoning
    provenance, and all supporting data required for governance evaluation.
    """
    governance_package_id: str = ""
    plan: Optional[ExecutionPlan] = None
    alternatives: List[ExecutionPlan] = field(default_factory=list)

    # Reasoning provenance
    reasoning_result_id: str = ""
    reasoning_summary: str = ""

    # Evidence
    evidence_summary: Dict[str, Any] = field(default_factory=dict)

    # Constraints and objectives
    constraints: List[PlanningConstraint] = field(default_factory=list)
    objectives: List[Objective] = field(default_factory=list)

    # Trade-off analysis
    trade_offs: List[Dict[str, Any]] = field(default_factory=list)

    # Context
    context_id: str = ""
    tenant_id: Optional[int] = None
    actor_id: str = ""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.governance_package_id:
            self.governance_package_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_package_id": self.governance_package_id,
            "plan": self.plan.to_dict() if self.plan else None,
            "alternatives": [a.to_dict() for a in self.alternatives],
            "reasoning_result_id": self.reasoning_result_id,
            "reasoning_summary": self.reasoning_summary,
            "evidence_summary": self.evidence_summary,
            "constraints": [c.to_dict() for c in self.constraints],
            "objectives": [o.to_dict() for o in self.objectives],
            "trade_offs": self.trade_offs,
            "context_id": self.context_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Planning Input / Output Contracts
# ---------------------------------------------------------------------------


@dataclass
class PlanningInput:
    """The complete input contract for the Planner Engine.

    Conforms to ES-004 Section 2 — Input Contract.
    """
    reasoning_result: Any = None  # ReasoningResult from ES-003
    knowledge_refs: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[PlanningConstraint] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    context: Any = None  # WorkspaceContext from Context Fusion
    objectives: List[Objective] = field(default_factory=list)
    planning_types: List[str] = field(default_factory=lambda: [PlanningType.OPERATIONAL.value])
    tenant_id: Optional[int] = None
    actor_id: str = ""
    correlation_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning_result_id": getattr(self.reasoning_result, "result_id", ""),
            "knowledge_refs": self.knowledge_refs,
            "constraints": [c.to_dict() for c in self.constraints],
            "resources": [r.to_dict() for r in self.resources],
            "context_id": getattr(self.context, "context_id", ""),
            "objectives": [o.to_dict() for o in self.objectives],
            "planning_types": self.planning_types,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


@dataclass
class PlanningOutput:
    """The complete output contract for the Planner Engine.

    Conforms to ES-004 Section 3 — Output Contract.
    """
    primary_plan: Optional[ExecutionPlan] = None
    alternatives: List[ExecutionPlan] = field(default_factory=list)
    decision_tree: Optional[DecisionTree] = None
    dependency_graph: Optional[DependencyGraph] = None
    schedule: Optional[Schedule] = None
    risk_assessment: Optional[RiskAssessment] = None
    confidence: float = 0.0
    governance_package: Optional[GovernancePackage] = None
    planning_metadata: Optional[PlanningMetadata] = None
    error: Optional[str] = None
    failure_mode: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_plan_id": self.primary_plan.plan_id if self.primary_plan else None,
            "alternatives": len(self.alternatives),
            "decision_tree": self.decision_tree.to_dict() if self.decision_tree else None,
            "dependency_graph": self.dependency_graph.to_dict() if self.dependency_graph else None,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "confidence": round(self.confidence, 4),
            "governance_package_id": self.governance_package.governance_package_id if self.governance_package else None,
            "planning_metadata": self.planning_metadata.to_dict() if self.planning_metadata else None,
            "error": self.error,
            "failure_mode": self.failure_mode,
        }

    @property
    def is_success(self) -> bool:
        return self.error is None and self.primary_plan is not None

    @property
    def is_error(self) -> bool:
        return self.error is not None


# ---------------------------------------------------------------------------
# Planning Metadata Model
# ---------------------------------------------------------------------------


@dataclass
class PlanningMetadata:
    """Provenance and metadata for a planning cycle."""
    planning_id: str = ""
    planning_engine_version: str = "1.0.0"
    reasoning_result_id: str = ""
    context_id: str = ""
    correlation_id: str = ""
    planning_types_used: List[str] = field(default_factory=list)
    stages_executed: int = 0
    stages_passed: int = 0
    stages_failed: int = 0
    alternatives_generated: int = 0
    engine_name: str = "planner_engine"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.planning_id:
            self.planning_id = str(uuid.uuid4())
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        if self.completed_at is None:
            self.completed_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planning_id": self.planning_id,
            "planning_engine_version": self.planning_engine_version,
            "reasoning_result_id": self.reasoning_result_id,
            "context_id": self.context_id,
            "correlation_id": self.correlation_id,
            "planning_types_used": self.planning_types_used,
            "stages_executed": self.stages_executed,
            "stages_passed": self.stages_passed,
            "stages_failed": self.stages_failed,
            "alternatives_generated": self.alternatives_generated,
            "engine_name": self.engine_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Optimization Criteria Model
# ---------------------------------------------------------------------------


@dataclass
class OptimizationCriteria:
    """Criteria for multi-objective optimization.

    Each dimension has a weight (priority) and a target direction
    (minimize or maximize).
    """
    dimensions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    default_weights: Dict[str, float] = field(default_factory=lambda: {
        OptimizationDimension.RISK.value: 0.3,
        OptimizationDimension.COST.value: 0.25,
        OptimizationDimension.TIME.value: 0.2,
        OptimizationDimension.RESOURCES.value: 0.15,
        OptimizationDimension.BUSINESS_OBJECTIVES.value: 0.1,
    })

    def get_weight(self, dimension: str) -> float:
        dim_config = self.dimensions.get(dimension, {})
        return dim_config.get("weight", self.default_weights.get(dimension, 0.1))

    def get_direction(self, dimension: str) -> str:
        """Returns 'minimize' or 'maximize'."""
        dim_config = self.dimensions.get(dimension, {})
        return dim_config.get("direction", "minimize")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimensions": self.dimensions,
            "default_weights": self.default_weights,
        }


# ---------------------------------------------------------------------------
# Planning Error
# ---------------------------------------------------------------------------


class PlanningError(Exception):
    """Exception raised when planning fails."""
    def __init__(self, message: str, failure_mode: str = "",
                 stage: str = "", details: Dict[str, Any] = None):
        self.message = message
        self.failure_mode = failure_mode
        self.stage = stage
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.message,
            "failure_mode": self.failure_mode,
            "stage": self.stage,
            "details": self.details,
        }


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
]