"""SHUNYA Automation & Event Runtime — data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _generate_id() -> str:
    from core.kernel.types import generate_uuid7
    return generate_uuid7()


class EventPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EventSchema:
    schema_id: str = field(default_factory=_generate_id)
    event_type: str = ""
    version: int = 1
    schema: dict[str, Any] = field(default_factory=dict)  # JSON Schema
    description: str = ""
    created_at: str = field(default_factory=_now_iso)


@dataclass
class Event:
    event_id: str = field(default_factory=_generate_id)
    event_type: str = ""
    topic: str = ""
    source: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    tenant_id: str = ""
    idempotency_key: str = ""
    version: int = 1
    correlation_id: str = ""
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class EventRecord:
    """Stored event for event sourcing/replay."""
    record_id: str = field(default_factory=_generate_id)
    event: Event = field(default_factory=Event)
    received_at: str = field(default_factory=_now_iso)
    processed: bool = False
    error: str = ""
    retry_count: int = 0
    provenance: list[str] = field(default_factory=list)


@dataclass
class Subscription:
    sub_id: str = field(default_factory=_generate_id)
    topic: str = ""
    handler: Any = None  # async callable(event) -> None
    filter_expression: str = ""  # Simple expression, e.g. "priority == 'high'"
    max_retries: int = 3
    timeout_ms: int = 30_000
    created_at: str = field(default_factory=_now_iso)


class TriggerType(str, Enum):
    EVENT = "event"
    SCHEDULED = "scheduled"
    CONDITION = "condition"


class TriggerStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


@dataclass
class Trigger:
    trigger_id: str = field(default_factory=_generate_id)
    name: str = ""
    trigger_type: TriggerType = TriggerType.EVENT
    topic: str = ""
    condition: str = ""  # e.g. "event.payload.value > 100"
    action: str = ""     # e.g. "integration:rest:POST:/webhook/alert"
    status: TriggerStatus = TriggerStatus.ACTIVE
    schedule: str = ""   # cron expression for scheduled triggers
    max_retries: int = 3
    timeout_ms: int = 30_000
    requires_approval: bool = False
    tenant_id: str = ""
    created_at: str = field(default_factory=_now_iso)


class RuleOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    IN = "in"
    MATCHES = "matches"


@dataclass
class RuleCondition:
    field: str = ""
    operator: RuleOperator = RuleOperator.EQUALS
    value: Any = None


@dataclass
class Rule:
    rule_id: str = field(default_factory=_generate_id)
    name: str = ""
    event_type: str = ""
    conditions: list[RuleCondition] = field(default_factory=list)
    action: str = ""
    priority: int = 50
    enabled: bool = True
    created_at: str = field(default_factory=_now_iso)


@dataclass
class WorkflowStep:
    step_id: str = field(default_factory=_generate_id)
    name: str = ""
    action: str = ""
    depends_on: list[str] = field(default_factory=list)
    requires_approval: bool = False
    approved: bool = False
    timeout_ms: int = 60_000
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Workflow:
    workflow_id: str = field(default_factory=_generate_id)
    name: str = ""
    trigger_event_id: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: int = 0
    tenant_id: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class ScheduledAutomation:
    schedule_id: str = field(default_factory=_generate_id)
    name: str = ""
    cron: str = ""  # cron expression
    action: str = ""
    enabled: bool = True
    tenant_id: str = ""
    last_run: str = ""
    created_at: str = field(default_factory=_now_iso)


@dataclass
class DeadLetterEvent:
    dlq_id: str = field(default_factory=_generate_id)
    event: Event = field(default_factory=Event)
    error: str = ""
    retry_count: int = 0
    failed_at: str = field(default_factory=_now_iso)
    tenant_id: str = ""


@dataclass
class AutomationTrace:
    operation: str = ""
    event_id: str = ""
    trigger_id: str = ""
    workflow_id: str = ""
    success: bool = True
    latency_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class AutomationStats:
    total_events: int = 0
    total_triggers: int = 0
    total_workflows: int = 0
    total_rules: int = 0
    events_by_topic: dict[str, int] = field(default_factory=dict)
    dead_letter_count: int = 0