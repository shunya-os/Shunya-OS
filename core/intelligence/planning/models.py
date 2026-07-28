"""
SHUNYA Planning Engine — Data Models

Defines the core data structures for the Planning Engine: plan structure,
steps with dependencies, resources, risks, success criteria, and the engine
input/output contract as specified in the Intelligence Runtime Canon.

All models are fully immutable after creation (frozen dataclasses).

References:
    - docs/canon/INTELLIGENCE_RUNTIME_CANON.md §3, §8
    - docs/canon/07_ai_canon.md §9 (Planner Engine)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.kernel.types import generate_uuid7

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Plan Step Status
# ---------------------------------------------------------------------------


class PlanStepStatus(Enum):
    """Lifecycle states for a plan step.

    Values:
        PENDING: Not yet started.
        IN_PROGRESS: Currently being executed.
        BLOCKED: Waiting on a dependency that is not yet complete.
        COMPLETED: Finished successfully.
        FAILED: Execution failed.
        SKIPPED: Explicitly skipped.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# Risk Severity & Category
# ---------------------------------------------------------------------------


class RiskSeverity(Enum):
    """Severity levels for plan risks.

    Values:
        CRITICAL: Could cause plan failure or significant harm.
        HIGH: Likely to cause significant delay or quality issues.
        MEDIUM: Moderate impact; manageable with mitigation.
        LOW: Minor impact; easily mitigated.
        NEGLIGIBLE: Virtually no impact.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class RiskCategory(Enum):
    """Categories for plan risks.

    Values:
        TECHNICAL: Technology, architecture, implementation risk.
        RESOURCE: Staffing, budget, equipment risk.
        SCHEDULE: Timeline, deadline, dependency risk.
        EXTERNAL: Third-party, regulatory, market risk.
        OPERATIONAL: Process, coordination, execution risk.
        QUALITY: Output, standard, compliance risk.
    """

    TECHNICAL = "technical"
    RESOURCE = "resource"
    SCHEDULE = "schedule"
    EXTERNAL = "external"
    OPERATIONAL = "operational"
    QUALITY = "quality"


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Resource:
    """A resource required by a plan step.

    Attributes:
        resource_id: Unique identifier.
        name: Human-readable resource name.
        resource_type: Category (e.g. "person", "tool", "budget", "material").
        quantity: Required quantity (default: 1).
        allocated: Whether this resource has been allocated (default: False).
        description: Optional description of the resource need.
    """

    resource_id: str = field(default_factory=generate_uuid7)
    name: str = ""
    resource_type: str = ""
    quantity: float = 1.0
    allocated: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        """Validate invariants."""
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Risk:
    """A risk identified for a plan.

    Attributes:
        risk_id: Unique identifier.
        description: What the risk is.
        severity: Severity level (RiskSeverity enum).
        category: Risk category (RiskCategory enum).
        probability: Probability of occurrence [0, 1].
        impact: Impact severity [0, 1].
        mitigation: Suggested mitigation strategy.
        contingency: Fallback plan if risk materialises.
        owner: Person or team responsible for managing this risk.
    """

    risk_id: str = field(default_factory=generate_uuid7)
    description: str = ""
    severity: RiskSeverity = RiskSeverity.MEDIUM
    category: RiskCategory = RiskCategory.OPERATIONAL
    probability: float = 0.5
    impact: float = 0.5
    mitigation: str = ""
    contingency: str = ""
    owner: str = ""

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError(
                f"probability must be in [0, 1], got {self.probability}"
            )
        if not 0.0 <= self.impact <= 1.0:
            raise ValueError(
                f"impact must be in [0, 1], got {self.impact}"
            )
        if not isinstance(self.severity, RiskSeverity):
            raise TypeError(
                f"severity must be a RiskSeverity enum, got {self.severity!r}"
            )
        if not isinstance(self.category, RiskCategory):
            raise TypeError(
                f"category must be a RiskCategory enum, got {self.category!r}"
            )

    @property
    def risk_score(self) -> float:
        """Compute overall risk score as probability * impact.

        Returns:
            Float in [0, 1].
        """
        return round(self.probability * self.impact, 6)


# ---------------------------------------------------------------------------
# Plan Step
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanStep:
    """A single step within a plan.

    Attributes:
        step_id: Unique identifier for this step.
        order: Ordinal position in the plan sequence.
        action: Description of the action to perform.
        actor: Who or what performs this step.
        estimated_duration: Human-readable duration estimate.
        estimated_duration_seconds: Duration in seconds for scheduling.
        depends_on: IDs of steps that must complete before this one.
        resources: Resources required by this step.
        risks: Risks specific to this step.
        success_criteria: Criteria for considering this step complete.
        notes: Additional notes or instructions.
        status: Current lifecycle status.
        metadata: Optional extensible metadata.
    """

    step_id: str = field(default_factory=generate_uuid7)
    order: int = 0
    action: str = ""
    actor: str = ""
    estimated_duration: str = ""
    estimated_duration_seconds: float = 0.0
    depends_on: tuple[str, ...] = ()
    resources: tuple[Resource, ...] = ()
    risks: tuple[Risk, ...] = ()
    success_criteria: tuple[str, ...] = ()
    notes: str = ""
    status: PlanStepStatus = PlanStepStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.action:
            raise ValueError("A plan step must have an action description")
        if self.order < 0:
            raise ValueError(f"order must be non-negative, got {self.order}")
        if not isinstance(self.status, PlanStepStatus):
            raise TypeError(
                f"status must be a PlanStepStatus enum, got {self.status!r}"
            )


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Plan:
    """An actionable plan generated by the Planning Engine.

    Attributes:
        plan_id: Unique identifier for this plan.
        objective: What the plan achieves.
        steps: Ordered list of ``PlanStep``.
        dependencies: Mapping of ``step_id -> list of dependency step_ids``.
        estimated_duration: Human-readable total duration estimate.
        estimated_duration_seconds: Total duration in seconds.
        resources: Aggregate list of all resources required across steps.
        risks: Aggregate list of all risks across steps.
        success_criteria: Overall success criteria for the plan.
        confidence: How confident the engine is in this plan [0, 1].
        alternatives: Other plans considered.
        created_at: ISO-8601 timestamp of creation.
        metadata: Optional extensible metadata.
    """

    plan_id: str = field(default_factory=generate_uuid7)
    objective: str = ""
    steps: tuple[PlanStep, ...] = ()
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    estimated_duration: str = ""
    estimated_duration_seconds: float = 0.0
    resources: tuple[Resource, ...] = ()
    risks: tuple[Risk, ...] = ()
    success_criteria: tuple[str, ...] = ()
    confidence: float = 0.0
    alternatives: tuple[str, ...] = ()
    created_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Auto-derive dependencies from steps and validate invariants."""
        if not self.objective:
            raise ValueError("A plan must have an objective")

        # Auto-derive dependencies if not explicitly provided
        if not self.dependencies and self.steps:
            deps: dict[str, list[str]] = {}
            for step in self.steps:
                deps[step.step_id] = list(step.depends_on)
            object.__setattr__(self, "dependencies", deps)

        # Validate: every dependency step_id must exist in the plan
        step_ids = {s.step_id for s in self.steps}
        for step_id, dep_list in self.dependencies.items():
            if step_id not in step_ids:
                raise ValueError(
                    f"Step {step_id!r} in dependencies does not exist in plan steps"
                )
            for dep_id in dep_list:
                if dep_id not in step_ids:
                    raise ValueError(
                        f"Dependency {dep_id!r} of step {step_id!r} "
                        f"does not exist in plan steps"
                    )


# ---------------------------------------------------------------------------
# Engine Input / Output (re-exported from reasoning.models for convenience)
# ---------------------------------------------------------------------------

# These are shared with the other intelligence engines and defined in
# core.intelligence.reasoning.models.  Re-export here for convenience.
from core.intelligence.reasoning.models import (
    EngineInput,
    EngineOutput,
    EscalationResult,
)

__all__ = [
    "EngineInput",
    "EngineOutput",
    "EscalationResult",
    "Plan",
    "PlanStep",
    "PlanStepStatus",
    "Resource",
    "Risk",
    "RiskCategory",
    "RiskSeverity",
]
