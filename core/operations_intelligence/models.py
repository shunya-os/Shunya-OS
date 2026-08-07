"""Universal Operations Intelligence — Data Models.

Operations Intelligence models how individuals and organizations continuously
operate: processes, workflows, SOPs, resources, capacity, queues, bottlenecks,
throughput, service levels, operational health, continuous improvement.

It does not model ERP, workflow software, or business operations software.
It models Operations.

UCP-09 — Universal Operations Intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _generate_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ── Enums ─────────────────────────────────────────────────────────────────


class OperationsType(str, Enum):
    MANUFACTURING = "manufacturing"
    CUSTOMER_SERVICE = "customer_service"
    IT_OPERATIONS = "it_operations"
    SUPPLY_CHAIN = "supply_chain"
    HEALTHCARE = "healthcare"
    EDUCATIONAL = "educational"
    RETAIL = "retail"
    LOGISTICS = "logistics"
    FINANCIAL = "financial"
    HOSPITALITY = "hospitality"
    ENERGY = "energy"
    TELECOM = "telecom"
    OTHER = "other"


class OperationsStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ResourceType(str, Enum):
    HUMAN = "human"
    EQUIPMENT = "equipment"
    MATERIAL = "material"
    FACILITY = "facility"
    ENERGY = "energy"
    TIME = "time"
    INFORMATION = "information"
    FINANCIAL = "financial"
    SOFTWARE = "software"
    OTHER = "other"


class QueueDiscipline(str, Enum):
    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"
    SHORTEST_PROCESSING = "shortest_processing"
    LONGEST_PROCESSING = "longest_processing"
    DUE_DATE = "due_date"
    CUSTOM = "custom"


class ServiceLevelStatus(str, Enum):
    MET = "met"
    NEAR_MISS = "near_miss"
    VIOLATED = "violated"
    AT_RISK = "at_risk"
    NOT_MEASURED = "not_measured"


class HealthLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    AT_RISK = "at_risk"
    CRITICAL = "critical"


# ── Process Step ────────────────────────────────────────────────────────────


@dataclass
class ProcessStep:
    """A single step within an operational process."""
    step_id: str = field(default_factory=_generate_id)
    name: str = ""
    description: str = ""
    sequence_order: int = 0
    duration_minutes: float = 0.0
    variability_pct: float = 0.0
    resource_ids: list[str] = field(default_factory=list)
    input_ids: list[str] = field(default_factory=list)
    output_ids: list[str] = field(default_factory=list)
    decision_point: bool = False
    parallel: bool = False
    quality_check: bool = False
    rework_pct: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def effective_duration(self) -> float:
        return self.duration_minutes * (1 + self.rework_pct / 100.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "sequence_order": self.sequence_order,
            "duration_minutes": self.duration_minutes,
            "variability_pct": self.variability_pct,
            "resource_ids": list(self.resource_ids),
            "input_ids": list(self.input_ids),
            "output_ids": list(self.output_ids),
            "decision_point": self.decision_point,
            "parallel": self.parallel,
            "quality_check": self.quality_check,
            "rework_pct": self.rework_pct,
            "effective_duration": self.effective_duration,
            "evidence_ids": list(self.evidence_ids),
        }


# ── Process ─────────────────────────────────────────────────────────────────


@dataclass
class Process:
    """A series of actions or operations that convert inputs to outputs."""
    process_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    ops_type: str = OperationsType.OTHER.value
    status: str = OperationsStatus.ACTIVE.value
    name: str = ""
    purpose: str = ""
    scope: str = ""
    steps: list[ProcessStep] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    cycle_time_minutes: float = 0.0
    throughput_per_hour: float = 0.0
    defect_rate_pct: float = 0.0
    uptime_pct: float = 100.0
    setup_time_minutes: float = 0.0
    batch_size: int = 1
    resource_ids: list[str] = field(default_factory=list)
    agreement_ids: list[str] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)
    knowledge_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    initiative_ids: list[str] = field(default_factory=list)
    financial_ids: list[str] = field(default_factory=list)
    journey_ids: list[str] = field(default_factory=list)
    relationship_ids: list[str] = field(default_factory=list)
    queue_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_step_duration(self) -> float:
        return sum(s.effective_duration for s in self.steps)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def is_running(self) -> bool:
        return self.status == OperationsStatus.ACTIVE.value

    def effective_throughput(self) -> float:
        return self.throughput_per_hour * (1 - self.defect_rate_pct / 100.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "owner_id": self.owner_id,
            "ops_type": self.ops_type,
            "status": self.status,
            "name": self.name,
            "purpose": self.purpose,
            "scope": self.scope,
            "steps": [s.to_dict() for s in self.steps],
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "cycle_time_minutes": self.cycle_time_minutes,
            "throughput_per_hour": self.throughput_per_hour,
            "defect_rate_pct": self.defect_rate_pct,
            "uptime_pct": self.uptime_pct,
            "setup_time_minutes": self.setup_time_minutes,
            "batch_size": self.batch_size,
            "effective_throughput": self.effective_throughput(),
            "total_step_duration": self.total_step_duration,
            "step_count": self.step_count,
            "is_running": self.is_running,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Workflow Step ───────────────────────────────────────────────────────────


@dataclass
class WorkflowStep:
    """A step within a workflow, which may reference a process step or SOP."""
    workflow_step_id: str = field(default_factory=_generate_id)
    name: str = ""
    description: str = ""
    sequence_order: int = 0
    process_id: str = ""
    sop_id: str = ""
    assignee_ids: list[str] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    conditions: list[dict[str, Any]] = field(default_factory=list)
    timeout_minutes: float = 0.0
    auto_escalate: bool = False
    notification_trigger: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_step_id": self.workflow_step_id,
            "name": self.name,
            "description": self.description,
            "sequence_order": self.sequence_order,
            "process_id": self.process_id,
            "sop_id": self.sop_id,
            "assignee_ids": list(self.assignee_ids),
            "decisions": list(self.decisions),
            "conditions": list(self.conditions),
            "timeout_minutes": self.timeout_minutes,
            "auto_escalate": self.auto_escalate,
            "notification_trigger": self.notification_trigger,
            "evidence_ids": list(self.evidence_ids),
        }


# ── Workflow ────────────────────────────────────────────────────────────────


@dataclass
class Workflow:
    """A structured sequence of work activities with decision points."""
    workflow_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    ops_type: str = OperationsType.OTHER.value
    status: str = OperationsStatus.ACTIVE.value
    name: str = ""
    purpose: str = ""
    trigger: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    current_step_index: int = 0
    sla_minutes: float = 0.0
    escalation_path: list[str] = field(default_factory=list)
    completion_criteria: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def is_active(self) -> bool:
        return self.status == OperationsStatus.ACTIVE.value

    @property
    def progress_pct(self) -> float:
        total = len(self.steps)
        if total == 0:
            return 0.0
        return round((self.current_step_index / total) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "owner_id": self.owner_id,
            "ops_type": self.ops_type,
            "status": self.status,
            "name": self.name,
            "purpose": self.purpose,
            "trigger": self.trigger,
            "steps": [s.to_dict() for s in self.steps],
            "current_step_index": self.current_step_index,
            "sla_minutes": self.sla_minutes,
            "escalation_path": list(self.escalation_path),
            "completion_criteria": list(self.completion_criteria),
            "step_count": self.step_count,
            "is_active": self.is_active,
            "progress_pct": self.progress_pct,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── SOP (Standard Operating Procedure) ──────────────────────────────────────


@dataclass
class SOP:
    """A prescribed way of performing an operation — canonical instructions."""
    sop_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    ops_type: str = OperationsType.OTHER.value
    version: str = "1.0"
    name: str = ""
    purpose: str = ""
    scope: str = ""
    prerequisites: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)
    quality_criteria: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    trained_personnel: list[str] = field(default_factory=list)
    review_interval_days: int = 365
    last_reviewed: str = ""
    next_review: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_current(self) -> bool:
        if not self.next_review:
            return True
        try:
            review = datetime.fromisoformat(self.next_review.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) <= review
        except (ValueError, TypeError):
            return True

    @property
    def instruction_count(self) -> int:
        return len(self.instructions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sop_id": self.sop_id,
            "owner_id": self.owner_id,
            "ops_type": self.ops_type,
            "version": self.version,
            "name": self.name,
            "purpose": self.purpose,
            "scope": self.scope,
            "prerequisites": list(self.prerequisites),
            "instructions": list(self.instructions),
            "safety_notes": list(self.safety_notes),
            "quality_criteria": list(self.quality_criteria),
            "references": list(self.references),
            "trained_personnel": list(self.trained_personnel),
            "review_interval_days": self.review_interval_days,
            "last_reviewed": self.last_reviewed,
            "next_review": self.next_review,
            "is_current": self.is_current,
            "instruction_count": self.instruction_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Resource ────────────────────────────────────────────────────────────────


@dataclass
class Resource:
    """Anything used in operations — people, equipment, materials, facilities."""
    resource_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    resource_type: str = ResourceType.OTHER.value
    status: str = "available"
    name: str = ""
    description: str = ""
    capacity_per_hour: float = 0.0
    current_load: float = 0.0
    efficiency_pct: float = 100.0
    cost_per_hour: float = 0.0
    downtime_pct: float = 0.0
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    location: str = ""
    schedule: list[dict[str, Any]] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def effective_capacity(self) -> float:
        return self.capacity_per_hour * (self.efficiency_pct / 100.0) * (1 - self.downtime_pct / 100.0)

    @property
    def utilization_pct(self) -> float:
        if self.capacity_per_hour == 0:
            return 0.0
        return round((self.current_load / self.capacity_per_hour) * 100, 1)

    @property
    def is_available(self) -> bool:
        return self.status == "available" and self.utilization_pct < 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "owner_id": self.owner_id,
            "resource_type": self.resource_type,
            "status": self.status,
            "name": self.name,
            "description": self.description,
            "capacity_per_hour": self.capacity_per_hour,
            "current_load": self.current_load,
            "efficiency_pct": self.efficiency_pct,
            "cost_per_hour": self.cost_per_hour,
            "downtime_pct": self.downtime_pct,
            "effective_capacity": self.effective_capacity,
            "utilization_pct": self.utilization_pct,
            "is_available": self.is_available,
            "skills": list(self.skills),
            "certifications": list(self.certifications),
            "location": self.location,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Capacity Plan ───────────────────────────────────────────────────────────


@dataclass
class CapacityPlan:
    """Planned capacity allocation for a set of operations."""
    cap_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    name: str = ""
    period_start: str = ""
    period_end: str = ""
    resources: list[Resource] = field(default_factory=list)
    target_utilization_pct: float = 80.0
    buffer_pct: float = 20.0
    peak_demand_multiplier: float = 1.5
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def total_capacity(self) -> float:
        return sum(r.effective_capacity for r in self.resources)

    @property
    def total_load(self) -> float:
        return sum(r.current_load for r in self.resources)

    @property
    def overall_utilization_pct(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        return round((self.total_load / self.total_capacity) * 100, 1)

    @property
    def is_overloaded(self) -> bool:
        return self.overall_utilization_pct > self.target_utilization_pct + self.buffer_pct

    @property
    def headroom_pct(self) -> float:
        return max(0.0, 100.0 - self.overall_utilization_pct)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cap_id": self.cap_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "resources": [r.to_dict() for r in self.resources],
            "target_utilization_pct": self.target_utilization_pct,
            "buffer_pct": self.buffer_pct,
            "peak_demand_multiplier": self.peak_demand_multiplier,
            "total_capacity": self.total_capacity,
            "total_load": self.total_load,
            "overall_utilization_pct": self.overall_utilization_pct,
            "is_overloaded": self.is_overloaded,
            "headroom_pct": self.headroom_pct,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Queue ───────────────────────────────────────────────────────────────────


@dataclass
class Queue:
    """A queue of items waiting to be processed by a resource or process."""
    queue_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    process_id: str = ""
    name: str = ""
    discipline: str = QueueDiscipline.FIFO.value
    items: list[dict[str, Any]] = field(default_factory=list)
    max_length: int = 0
    average_wait_time_minutes: float = 0.0
    current_length: int = 0
    arrival_rate_per_hour: float = 0.0
    service_rate_per_hour: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def utilization(self) -> float:
        if self.service_rate_per_hour == 0:
            return 0.0
        return round((self.arrival_rate_per_hour / self.service_rate_per_hour) * 100, 1)

    @property
    def is_overloaded(self) -> bool:
        return self.arrival_rate_per_hour >= self.service_rate_per_hour

    @property
    def estimated_wait_minutes(self) -> float:
        """Little's Law: L = λW  => W = L/λ"""
        if self.arrival_rate_per_hour == 0:
            return 0.0
        return round((self.current_length / (self.arrival_rate_per_hour / 60)), 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "queue_id": self.queue_id,
            "owner_id": self.owner_id,
            "process_id": self.process_id,
            "name": self.name,
            "discipline": self.discipline,
            "items_count": len(self.items),
            "max_length": self.max_length,
            "average_wait_time_minutes": self.average_wait_time_minutes,
            "current_length": self.current_length,
            "arrival_rate_per_hour": self.arrival_rate_per_hour,
            "service_rate_per_hour": self.service_rate_per_hour,
            "utilization": self.utilization,
            "is_overloaded": self.is_overloaded,
            "estimated_wait_minutes": self.estimated_wait_minutes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Bottleneck ──────────────────────────────────────────────────────────────


@dataclass
class Bottleneck:
    """A constraint point that limits total system throughput."""
    bottleneck_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    process_id: str = ""
    step_id: str = ""
    resource_id: str = ""
    name: str = ""
    constraint_type: str = "capacity"
    current_throughput: float = 0.0
    max_throughput: float = 0.0
    impact_pct: float = 0.0
    queue_length: int = 0
    wait_time_minutes: float = 0.0
    contributing_factors: list[str] = field(default_factory=list)
    resolution: str = ""
    resolved_at: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def severity(self) -> str:
        if self.impact_pct >= 50:
            return "critical"
        elif self.impact_pct >= 25:
            return "high"
        elif self.impact_pct >= 10:
            return "medium"
        return "low"

    @property
    def is_resolved(self) -> bool:
        return bool(self.resolved_at)

    @property
    def throughput_gap(self) -> float:
        return self.max_throughput - self.current_throughput

    def to_dict(self) -> dict[str, Any]:
        return {
            "bottleneck_id": self.bottleneck_id,
            "owner_id": self.owner_id,
            "process_id": self.process_id,
            "step_id": self.step_id,
            "resource_id": self.resource_id,
            "name": self.name,
            "constraint_type": self.constraint_type,
            "current_throughput": self.current_throughput,
            "max_throughput": self.max_throughput,
            "impact_pct": self.impact_pct,
            "queue_length": self.queue_length,
            "wait_time_minutes": self.wait_time_minutes,
            "contributing_factors": list(self.contributing_factors),
            "resolution": self.resolution,
            "resolved_at": self.resolved_at,
            "severity": self.severity,
            "is_resolved": self.is_resolved,
            "throughput_gap": self.throughput_gap,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Throughput Measure ──────────────────────────────────────────────────────


@dataclass
class ThroughputMeasure:
    """A measurement of throughput over a period."""
    measure_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    process_id: str = ""
    period_start: str = ""
    period_end: str = ""
    units_processed: int = 0
    units_defective: int = 0
    total_time_hours: float = 0.0
    good_units: int = 0
    first_pass_yield: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def throughput_per_hour(self) -> float:
        if self.total_time_hours == 0:
            return 0.0
        return round(self.units_processed / self.total_time_hours, 2)

    @property
    def defect_rate_pct(self) -> float:
        if self.units_processed == 0:
            return 0.0
        return round((self.units_defective / self.units_processed) * 100, 2)

    @property
    def yield_pct(self) -> float:
        if self.units_processed == 0:
            return 0.0
        return round((self.good_units / self.units_processed) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "measure_id": self.measure_id,
            "owner_id": self.owner_id,
            "process_id": self.process_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "units_processed": self.units_processed,
            "units_defective": self.units_defective,
            "total_time_hours": self.total_time_hours,
            "good_units": self.good_units,
            "throughput_per_hour": self.throughput_per_hour,
            "defect_rate_pct": self.defect_rate_pct,
            "yield_pct": self.yield_pct,
            "first_pass_yield": self.first_pass_yield,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Service Level ───────────────────────────────────────────────────────────


@dataclass
class ServiceLevel:
    """An agreed or expected performance standard for an operation."""
    sl_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    process_id: str = ""
    name: str = ""
    description: str = ""
    metric: str = ""  # e.g., "response_time_minutes", "uptime_pct", "accuracy_pct"
    target: float = 0.0
    actual: float = 0.0
    warning_threshold: float = 0.0
    period: str = "daily"
    status: str = ServiceLevelStatus.NOT_MEASURED.value
    measurement_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def compliance_pct(self) -> float:
        if self.target == 0:
            return 0.0
        return round((self.actual / self.target) * 100, 1)

    @property
    def is_breached(self) -> bool:
        return self.status == ServiceLevelStatus.VIOLATED.value

    def compute_status(self) -> str:
        if self.target == 0:
            return ServiceLevelStatus.NOT_MEASURED.value
        ratio = self.actual / self.target
        if ratio >= 1.0:
            return ServiceLevelStatus.MET.value
        elif ratio >= 0.9:
            return ServiceLevelStatus.NEAR_MISS.value
        elif ratio >= 0.75:
            return ServiceLevelStatus.AT_RISK.value
        return ServiceLevelStatus.VIOLATED.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "sl_id": self.sl_id,
            "owner_id": self.owner_id,
            "process_id": self.process_id,
            "name": self.name,
            "description": self.description,
            "metric": self.metric,
            "target": self.target,
            "actual": self.actual,
            "warning_threshold": self.warning_threshold,
            "period": self.period,
            "status": self.status or self.compute_status(),
            "compliance_pct": self.compliance_pct,
            "is_breached": self.is_breached,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Operational Health ──────────────────────────────────────────────────────


@dataclass
class OperationalHealth:
    """Overall health snapshot of an operation or operating entity."""
    health_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    process_id: str = ""
    score: float = 0.5
    level: str = HealthLevel.FAIR.value
    throughput_score: float = 0.0
    quality_score: float = 0.0
    efficiency_score: float = 0.0
    capacity_score: float = 0.0
    service_level_score: float = 0.0
    improvement_momentum: float = 0.0
    risk_factors: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    assessment: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def is_healthy(self) -> bool:
        return self.level in (HealthLevel.EXCELLENT.value, HealthLevel.GOOD.value)

    @property
    def needs_intervention(self) -> bool:
        return self.level in (HealthLevel.AT_RISK.value, HealthLevel.CRITICAL.value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_id": self.health_id,
            "owner_id": self.owner_id,
            "process_id": self.process_id,
            "score": self.score,
            "level": self.level,
            "throughput_score": self.throughput_score,
            "quality_score": self.quality_score,
            "efficiency_score": self.efficiency_score,
            "capacity_score": self.capacity_score,
            "service_level_score": self.service_level_score,
            "improvement_momentum": self.improvement_momentum,
            "risk_factors": list(self.risk_factors),
            "strengths": list(self.strengths),
            "assessment": self.assessment,
            "is_healthy": self.is_healthy,
            "needs_intervention": self.needs_intervention,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Continuous Improvement ──────────────────────────────────────────────────


@dataclass
class ContinuousImprovement:
    """A tracked improvement initiative for an operation."""
    ci_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    process_id: str = ""
    name: str = ""
    description: str = ""
    methodology: str = "kaizen"  # kaizen, six_sigma, lean, tqm, agile, custom
    current_state: str = ""
    target_state: str = ""
    expected_benefit: str = ""
    metrics_before: dict[str, float] = field(default_factory=dict)
    metrics_after: dict[str, float] = field(default_factory=dict)
    status: str = "identified"
    priority: str = "medium"
    assigned_to: list[str] = field(default_factory=list)
    initiative_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    knowledge_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def improvement_pct(self) -> float:
        if not self.metrics_before or not self.metrics_after:
            return 0.0
        changes = []
        for key in self.metrics_after:
            if key in self.metrics_before and self.metrics_before[key] != 0:
                change = ((self.metrics_after[key] - self.metrics_before[key])
                          / abs(self.metrics_before[key])) * 100
                changes.append(change)
        if not changes:
            return 0.0
        return round(sum(changes) / len(changes), 1)

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ci_id": self.ci_id,
            "owner_id": self.owner_id,
            "process_id": self.process_id,
            "name": self.name,
            "description": self.description,
            "methodology": self.methodology,
            "current_state": self.current_state,
            "target_state": self.target_state,
            "expected_benefit": self.expected_benefit,
            "metrics_before": dict(self.metrics_before),
            "metrics_after": dict(self.metrics_after),
            "status": self.status,
            "priority": self.priority,
            "assigned_to": list(self.assigned_to),
            "improvement_pct": self.improvement_pct,
            "is_completed": self.is_completed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Operations Recommendation ───────────────────────────────────────────────


@dataclass
class OperationsRecommendation:
    """An explainable recommendation derived from operations intelligence."""
    rec_id: str = field(default_factory=_generate_id)
    title: str = ""
    description: str = ""
    priority: str = "medium"
    reasoning: str = ""
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    expected_impact: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    affected_process_ids: list[str] = field(default_factory=list)
    affected_resource_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rec_id": self.rec_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
            "alternatives": list(self.alternatives),
            "expected_impact": self.expected_impact,
            "evidence": list(self.evidence),
            "affected_process_ids": list(self.affected_process_ids),
            "affected_resource_ids": list(self.affected_resource_ids),
            "generated_at": self.generated_at,
        }


# ── Operations Profile ──────────────────────────────────────────────────────


@dataclass
class OperationsProfile:
    """Collection of operations for an individual or organization."""
    profile_id: str = field(default_factory=_generate_id)
    owner_id: str = ""
    label: str = ""
    processes: list[Process] = field(default_factory=list)
    workflows: list[Workflow] = field(default_factory=list)
    sops: list[SOP] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)
    capacity_plans: list[CapacityPlan] = field(default_factory=list)
    queues: list[Queue] = field(default_factory=list)
    bottlenecks: list[Bottleneck] = field(default_factory=list)
    throughput_measures: list[ThroughputMeasure] = field(default_factory=list)
    service_levels: list[ServiceLevel] = field(default_factory=list)
    improvement_items: list[ContinuousImprovement] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @property
    def active_processes(self) -> list[Process]:
        return [p for p in self.processes if p.is_running]

    @property
    def active_workflows(self) -> list[Workflow]:
        return [w for w in self.workflows if w.is_active]

    @property
    def total_bottlenecks(self) -> int:
        return len(self.bottlenecks)

    @property
    def unresolved_bottlenecks(self) -> list[Bottleneck]:
        return [b for b in self.bottlenecks if not b.is_resolved]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "owner_id": self.owner_id,
            "label": self.label,
            "processes": len(self.processes),
            "active_processes": len(self.active_processes),
            "workflows": len(self.workflows),
            "active_workflows": len(self.active_workflows),
            "sops": len(self.sops),
            "resources": len(self.resources),
            "capacity_plans": len(self.capacity_plans),
            "queues": len(self.queues),
            "bottlenecks": len(self.bottlenecks),
            "unresolved_bottlenecks": len(self.unresolved_bottlenecks),
            "throughput_measures": len(self.throughput_measures),
            "service_levels": len(self.service_levels),
            "improvement_items": len(self.improvement_items),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }