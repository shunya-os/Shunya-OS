"""Canonical Runtime Pipeline — the single authoritative execution path.

Every user action, regardless of source, flows through this pipeline.
No alternate execution paths may be introduced.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Pipeline stage identifiers — matches the OS Constitution §2.1
# ---------------------------------------------------------------------------


class PipelineStage(str, Enum):
    """The 11 canonical pipeline stages, in execution order."""

    INTENT_RESOLUTION = "intent_resolution"
    IDENTITY_RESOLUTION = "identity_resolution"
    OBJECT_RESOLUTION = "object_resolution"
    KNOWLEDGE_GRAPH_UPDATE = "knowledge_graph_update"
    MEMORY_UPDATE = "memory_update"
    PLANNING_UPDATE = "planning_update"
    REASONING_UPDATE = "reasoning_update"
    EXECUTION_UPDATE = "execution_update"
    AUTOMATION_EVALUATION = "automation_evaluation"
    PROJECTION_ASSEMBLY = "projection_assembly"
    WORKSPACE_UPDATE = "workspace_update"


# All stages in canonical order
CANONICAL_STAGES: list[PipelineStage] = [
    PipelineStage.INTENT_RESOLUTION,
    PipelineStage.IDENTITY_RESOLUTION,
    PipelineStage.OBJECT_RESOLUTION,
    PipelineStage.KNOWLEDGE_GRAPH_UPDATE,
    PipelineStage.MEMORY_UPDATE,
    PipelineStage.PLANNING_UPDATE,
    PipelineStage.REASONING_UPDATE,
    PipelineStage.EXECUTION_UPDATE,
    PipelineStage.AUTOMATION_EVALUATION,
    PipelineStage.PROJECTION_ASSEMBLY,
    PipelineStage.WORKSPACE_UPDATE,
]


# ---------------------------------------------------------------------------
# Pipeline execution data models
# ---------------------------------------------------------------------------


@dataclass
class StepRecord:
    """Record of a single pipeline step execution."""

    stage: str
    runtime: str
    status: str  # "completed", "noop", "failed", "skipped"
    started_at: str
    completed_at: str
    duration_ms: float = 0.0
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class PipelineContext:
    """Context passed through every stage of the canonical pipeline.

    Every intent produces exactly one PipelineContext.
    No step may be skipped — each stage must explicitly declare a result.
    """

    intent_id: str = ""
    intent: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    identity_id: str | None = None
    object_id: str | None = None
    state: str = "pending"  # pending, running, completed, failed
    trace: list[StepRecord] = field(default_factory=list)
    started_at: str = ""
    completed_at: str | None = None
    projection: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.intent_id:
            self.intent_id = uuid.uuid4().hex[:16]
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()

    @property
    def total_duration_ms(self) -> float:
        if not self.trace:
            return 0.0
        return sum(s.duration_ms for s in self.trace)

    @property
    def status_summary(self) -> dict[str, str]:
        return {s.stage: s.status for s in self.trace}


# ---------------------------------------------------------------------------
# Runtime interface — every runtime that participates in the pipeline
# ---------------------------------------------------------------------------


class RuntimeInterface:
    """Abstract interface for a runtime participating in the canonical pipeline.

    Every runtime must implement:
      - name: unique runtime identifier
      - process(context, stage) -> dict: process the pipeline stage
      - health_check() -> dict: return health status
    """

    name: str = ""
    stages: list[PipelineStage] | None = None

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        """Process the given pipeline stage.

        Must return a dict with at least:
          {"status": "completed" | "noop" | "failed", ...}
        """
        raise NotImplementedError

    def health_check(self) -> dict[str, Any]:
        """Return health status of this runtime."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------


class RuntimePipeline:
    """The canonical pipeline orchestrator.

    Orchestrates execution order, timing, trace recording, and error handling
    across all registered runtimes. Each runtime registers for the stages it
    handles. The pipeline executes all stages in canonical order.
    """

    def __init__(self) -> None:
        self._runtimes: dict[str, RuntimeInterface] = {}
        self._stage_map: dict[PipelineStage, list[str]] = {
            stage: [] for stage in CANONICAL_STAGES
        }

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, runtime: RuntimeInterface) -> None:
        """Register a runtime with the pipeline.

        The runtime's ``stages`` list determines which pipeline stages
        it will be invoked for.
        """
        self._runtimes[runtime.name] = runtime
        for stage in (runtime.stages or []):
            if stage in self._stage_map:
                self._stage_map[stage].append(runtime.name)

    def unregister(self, name: str) -> None:
        """Remove a runtime from the pipeline."""
        if name in self._runtimes:
            del self._runtimes[name]
        for stage in self._stage_map:
            self._stage_map[stage] = [n for n in self._stage_map[stage] if n != name]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        intent: str,
        parameters: dict[str, Any] | None = None,
        identity_id: str | None = None,
        object_id: str | None = None,
    ) -> PipelineContext:
        """Execute the canonical pipeline for the given intent.

        Args:
            intent: The business intent string (e.g. "talk_to_customer").
            parameters: Extracted intent parameters.
            identity_id: Pre-resolved identity (if available).
            object_id: Pre-resolved object (if available).

        Returns:
            A completed PipelineContext with full execution trace.
        """
        ctx = PipelineContext(
            intent=intent,
            parameters=parameters or {},
            identity_id=identity_id,
            object_id=object_id,
            state="running",
        )

        for stage in CANONICAL_STAGES:
            record = self._execute_stage(ctx, stage)
            ctx.trace.append(record)
            if record.status == "failed":
                ctx.state = "failed"
                ctx.completed_at = datetime.now(timezone.utc).isoformat()
                return ctx

        ctx.state = "completed"
        ctx.completed_at = datetime.now(timezone.utc).isoformat()
        return ctx

    def _execute_stage(self, ctx: PipelineContext, stage: PipelineStage) -> StepRecord:
        """Execute a single pipeline stage across all registered runtimes.

        Multiple runtimes may handle the same stage. Results are merged.
        If no runtime handles the stage, it is recorded as noop.
        """
        start = datetime.now(timezone.utc)
        start_ms = _now_ms()
        runtime_names = self._stage_map.get(stage, [])

        if not runtime_names:
            return StepRecord(
                stage=stage.value,
                runtime="none",
                status="noop",
                started_at=start.isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )

        merged_result: dict[str, Any] = {}
        errors: list[str] = []

        for name in runtime_names:
            runtime = self._runtimes.get(name)
            if runtime is None:
                continue
            try:
                result = runtime.process(ctx, stage)
                merged_result.update(result)
                if result.get("status") == "failed":
                    errors.append(f"{name}: {result.get('error', 'unknown error')}")
            except Exception as e:  # noqa: BLE001 — pipeline must catch all
                errors.append(f"{name}: {e}")

        duration = _now_ms() - start_ms
        status = "failed" if errors else "completed"
        return StepRecord(
            stage=stage.value,
            runtime=",".join(runtime_names),
            status=status,
            started_at=start.isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=round(duration, 2),
            result=merged_result,
            error="; ".join(errors) if errors else None,
        )

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    def list_runtimes(self) -> dict[str, list[str]]:
        """Return registered runtimes grouped by stage."""
        return {s.value: names for s, names in self._stage_map.items() if names}

    def health_check(self) -> dict[str, Any]:
        """Aggregate health across all registered runtimes."""
        runtime_health = {}
        overall = "healthy"
        for name, runtime in self._runtimes.items():
            try:
                h = runtime.health_check()
                runtime_health[name] = h
                if h.get("status") != "healthy":
                    overall = "degraded"
            except Exception as e:  # noqa: BLE001 — pipeline must catch all
                runtime_health[name] = {"status": "error", "error": str(e)}
                overall = "degraded"
        return {
            "status": overall,
            "component": "runtime_pipeline",
            "runtime_count": len(self._runtimes),
            "stage_count": len(CANONICAL_STAGES),
            "runtimes": runtime_health,
        }


def _now_ms() -> float:
    return datetime.now(timezone.utc).timestamp() * 1000


__all__ = [
    "CANONICAL_STAGES",
    "PipelineContext",
    "PipelineStage",
    "RuntimeInterface",
    "RuntimePipeline",
    "StepRecord",
]