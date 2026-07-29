"""Pipeline Adapters — wrap real runtimes as RuntimeInterface for the canonical pipeline.

Each adapter bridges a real core runtime (sync or async) into the synchronous
RuntimeInterface contract. Async runtimes use asyncio.run() to bridge.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from core.runtime_pipeline import (
    PipelineContext,
    PipelineStage,
    RuntimeInterface,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Memory & Knowledge Runtime Adapter
# ---------------------------------------------------------------------------


class MemoryKnowledgeRuntimeAdapter(RuntimeInterface):
    """Pipeline adapter for MemoryKnowledgeRuntime.

    Handles KNOWLEDGE_GRAPH_UPDATE and MEMORY_UPDATE stages.
    Wraps core/memory_knowledge_runtime/ into the canonical pipeline.
    """

    name: str = "memory_knowledge"
    stages: list[PipelineStage] | None = None

    def __init__(self) -> None:
        from core.memory_knowledge_runtime import MemoryKnowledgeRuntime
        self._runtime = MemoryKnowledgeRuntime()
        self.stages = [
            PipelineStage.KNOWLEDGE_GRAPH_UPDATE,
            PipelineStage.MEMORY_UPDATE,
        ]

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        if stage == PipelineStage.KNOWLEDGE_GRAPH_UPDATE:
            return self._knowledge_graph_update(context)
        if stage == PipelineStage.MEMORY_UPDATE:
            return self._memory_update(context)
        return {"status": "noop", "stage": stage.value}

    def _knowledge_graph_update(self, context: PipelineContext) -> dict[str, Any]:
        """Store intent and object info into the knowledge graph.

        Records the current intent, parameters, and identity as a memory
        object in the knowledge store so the graph has context about
        what the user is doing.
        """
        intent = context.intent
        params = context.parameters or {}
        identity_id = context.identity_id or "anonymous"
        object_id = context.object_id or ""

        stored = []
        # Store the intent as a knowledge entry
        obj = self._runtime.store(
            key=f"intent:{context.intent_id}",
            value={"intent": intent, "parameters": params},
            namespace=f"pipeline:{identity_id}",
            tags=["intent", "pipeline"],
            provenance=context.intent_id,
        )
        stored.append(obj.memory_id)

        if object_id:
            # Link the object to this intent
            obj2 = self._runtime.store(
                key=f"object:{object_id}",
                value={"object_id": object_id, "last_intent": intent},
                namespace=f"objects:{identity_id}",
                tags=["object", "reference"],
                provenance=context.intent_id,
            )
            stored.append(obj2.memory_id)

        return {
            "status": "completed",
            "runtime": self.name,
            "stage": PipelineStage.KNOWLEDGE_GRAPH_UPDATE.value,
            "stored_count": len(stored),
            "memory_ids": stored,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _memory_update(self, context: PipelineContext) -> dict[str, Any]:
        """Record the pipeline execution as an episodic memory.

        Stores the full pipeline trace as a memory object so the system
        can recall past interactions.
        """
        identity_id = context.identity_id or "anonymous"
        trace_summary = context.status_summary

        obj = self._runtime.store(
            key=f"trace:{context.intent_id}",
            value={
                "intent": context.intent,
                "state": context.state,
                "stages": trace_summary,
                "total_duration_ms": context.total_duration_ms,
            },
            namespace=f"memory:{identity_id}",
            tags=["pipeline", "trace", context.state],
            provenance=context.intent_id,
        )

        return {
            "status": "completed",
            "runtime": self.name,
            "stage": PipelineStage.MEMORY_UPDATE.value,
            "memory_id": obj.memory_id,
            "trace_stages": len(context.trace),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": self.name,
            "object_count": len(self._runtime._objects),
        }


# ---------------------------------------------------------------------------
# Cognitive Runtime Adapter
# ---------------------------------------------------------------------------


class CognitiveRuntimeAdapter(RuntimeInterface):
    """Pipeline adapter for CognitiveRuntime.

    Handles REASONING_UPDATE stage.
    Wraps core/cognitive_runtime/ into the canonical pipeline.
    CognitiveRuntime is async — the adapter bridges via asyncio.run().
    """

    name: str = "cognitive"
    stages: list[PipelineStage] | None = None

    def __init__(self) -> None:
        from core.cognitive_runtime import CognitiveRuntime
        self._runtime = CognitiveRuntime()
        self._runtime.register_default_engines()
        self.stages = [
            PipelineStage.REASONING_UPDATE,
        ]

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        if stage == PipelineStage.REASONING_UPDATE:
            return self._reasoning_update(context)
        return {"status": "noop", "stage": stage.value}

    def _reasoning_update(self, context: PipelineContext) -> dict[str, Any]:
        """Run the cognitive pipeline on the current intent.

        Creates a cognitive session from the pipeline context and executes
        all registered intelligence engines.
        """
        identity_id = context.identity_id or "anonymous"
        objective = f"Process intent: {context.intent}"

        session = self._runtime.create_session(
            actor=identity_id,
            objective=objective,
            triggering_event=context.intent_id,
        )

        # Execute the cognitive pipeline (async → sync bridge)
        try:
            result = asyncio.run(self._runtime.execute(session))
        except Exception as exc:
            logger.error("Cognitive runtime execution failed: %s", exc)
            return {
                "status": "failed",
                "runtime": self.name,
                "stage": PipelineStage.REASONING_UPDATE.value,
                "error": str(exc),
                "session_id": session.session_id,
            }

        return {
            "status": "completed",
            "runtime": self.name,
            "stage": PipelineStage.REASONING_UPDATE.value,
            "session_id": session.session_id,
            "session_state": result.state.value if result else "unknown",
            "engine_count": len(self._runtime.list_plugins()),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": self.name,
            "engine_count": len(self._runtime.list_plugins()),
        }


# ---------------------------------------------------------------------------
# Planning Runtime Adapter
# ---------------------------------------------------------------------------


class PlanningRuntimeAdapter(RuntimeInterface):
    """Pipeline adapter for PlanningRuntime.

    Handles PLANNING_UPDATE stage.
    Wraps core/planning_runtime/ into the canonical pipeline.
    """

    name: str = "planning"
    stages: list[PipelineStage] | None = None

    def __init__(self) -> None:
        from core.planning_runtime import PlanningRuntime
        self._runtime = PlanningRuntime()
        self.stages = [PipelineStage.PLANNING_UPDATE]

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        if stage == PipelineStage.PLANNING_UPDATE:
            return self._planning_update(context)
        return {"status": "noop", "stage": stage.value}

    def _planning_update(self, context: PipelineContext) -> dict[str, Any]:
        """Create or update a plan from the pipeline context.

        If the intent is structured enough, creates a goal and plan.
        Otherwise records the intent as a lightweight planning observation.
        """
        intent = context.intent
        params = context.parameters or {}
        identity_id = context.identity_id or "anonymous"

        plans = []
        if intent in ("create_object", "execute_work", "talk_to_customer"):
            goal = self._runtime.create_goal(
                label=f"Process: {intent}",
                description=str(params),
                priority=50,
            )
            plan = self._runtime.create_plan(
                goal_id=goal.goal_id,
                label=f"Plan for {intent}",
            )
            plans.append(plan.plan_id)

        return {
            "status": "completed",
            "runtime": self.name,
            "stage": PipelineStage.PLANNING_UPDATE.value,
            "plan_count": len(plans),
            "plan_ids": plans,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": self.name,
            "goal_count": len(self._runtime._goals),
            "plan_count": len(self._runtime._plans),
        }


# ---------------------------------------------------------------------------
# Execution Runtime Adapter
# ---------------------------------------------------------------------------


class ExecutionRuntimeAdapter(RuntimeInterface):
    """Pipeline adapter for ExecutionRuntime.

    Handles EXECUTION_UPDATE stage.
    Wraps core/execution_runtime/ into the canonical pipeline.
    ExecutionRuntime is async — the adapter bridges via asyncio.run().
    """

    name: str = "execution"
    stages: list[PipelineStage] | None = None

    def __init__(self) -> None:
        from core.execution_runtime import ExecutionRuntime
        self._runtime = ExecutionRuntime()
        self._runtime.register_default_actions()
        self.stages = [PipelineStage.EXECUTION_UPDATE]

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        if stage == PipelineStage.EXECUTION_UPDATE:
            return self._execution_update(context)
        return {"status": "noop", "stage": stage.value}

    def _execution_update(self, context: PipelineContext) -> dict[str, Any]:
        """Schedule an execution instance from the pipeline context.

        For known intents, creates an execution instance and schedules it.
        For unknown intents, returns noop to avoid hard pipeline failures.
        """
        intent = context.intent
        params = context.parameters or {}
        identity_id = context.identity_id or "anonymous"

        # Check if this intent maps to a registered action
        if self._runtime.get_action(intent) is None:
            return {
                "status": "noop",
                "runtime": self.name,
                "stage": PipelineStage.EXECUTION_UPDATE.value,
                "reason": f"Action '{intent}' not registered — no execution needed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        instance = self._runtime.create_instance(
            action_id=intent,
            actor=identity_id,
            objective=str(params),
        )

        try:
            result = asyncio.run(self._runtime.schedule(instance))
        except Exception as exc:
            logger.error("Execution runtime scheduling failed: %s", exc)
            return {
                "status": "failed",
                "runtime": self.name,
                "stage": PipelineStage.EXECUTION_UPDATE.value,
                "error": str(exc),
                "instance_id": instance.instance_id,
            }

        return {
            "status": "completed",
            "runtime": self.name,
            "stage": PipelineStage.EXECUTION_UPDATE.value,
            "execution_id": result.execution_id if result else "unknown",
            "execution_state": result.state.value if result else "unknown",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": self.name,
            "action_count": len(self._runtime._actions),
        }


# ---------------------------------------------------------------------------
# Automation Runtime Adapter
# ---------------------------------------------------------------------------


class AutomationRuntimeAdapter(RuntimeInterface):
    """Pipeline adapter for AutomationRuntime.

    Handles AUTOMATION_EVALUATION stage.
    Wraps core/automation_runtime/ into the canonical pipeline.
    AutomationRuntime uses async publish — the adapter bridges via asyncio.run().
    """

    name: str = "automation"
    stages: list[PipelineStage] | None = None

    def __init__(self) -> None:
        from core.automation_runtime import AutomationRuntime
        self._runtime = AutomationRuntime()
        self.stages = [PipelineStage.AUTOMATION_EVALUATION]

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        if stage == PipelineStage.AUTOMATION_EVALUATION:
            return self._automation_evaluation(context)
        return {"status": "noop", "stage": stage.value}

    def _automation_evaluation(self, context: PipelineContext) -> dict[str, Any]:
        """Evaluate automation rules against the completed pipeline execution.

        Publishes a pipeline completion event to the automation event bus,
        which triggers any matching rules.
        """
        from core.automation_runtime.models import Event, EventPriority

        event = Event(
            event_type="pipeline.completed",
            source="runtime_pipeline",
            payload={
                "intent": context.intent,
                "state": context.state,
                "identity_id": context.identity_id,
                "object_id": context.object_id,
                "intent_id": context.intent_id,
                "trace_summary": context.status_summary,
            },
            priority=EventPriority.NORMAL,
            idempotency_key=f"pipeline:{context.intent_id}",
        )

        try:
            result = asyncio.run(self._runtime.publish(event))
        except Exception as exc:
            logger.error("Automation runtime publish failed: %s", exc)
            return {
                "status": "failed",
                "runtime": self.name,
                "stage": PipelineStage.AUTOMATION_EVALUATION.value,
                "error": str(exc),
            }

        # Evaluate any matching rules
        rule_count = len(self._runtime._rules)
        triggered = []
        if rule_count > 0 and context.state == "completed":
            for rule_id, rule in self._runtime._rules.items():
                triggered.append(rule_id)

        return {
            "status": "completed",
            "runtime": self.name,
            "stage": PipelineStage.AUTOMATION_EVALUATION.value,
            "event_id": result.event_id if result else "unknown",
            "rule_count": rule_count,
            "triggered_rules": triggered,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": self.name,
            "rule_count": len(self._runtime._rules),
            "event_count": len(self._runtime._events),
        }


# ---------------------------------------------------------------------------
# Workspace Runtime Adapter
# ---------------------------------------------------------------------------


class WorkspaceRuntimeAdapter(RuntimeInterface):
    """Pipeline adapter for WorkspaceRuntime.

    Handles WORKSPACE_UPDATE stage.
    Wraps core/workspace_runtime/ into the canonical pipeline.
    """

    name: str = "workspace"
    stages: list[PipelineStage] | None = None

    def __init__(self) -> None:
        from core.workspace_runtime import WorkspaceRuntime
        self._runtime = WorkspaceRuntime()
        self.stages = [PipelineStage.WORKSPACE_UPDATE]

    def process(self, context: PipelineContext, stage: PipelineStage) -> dict[str, Any]:
        if stage == PipelineStage.WORKSPACE_UPDATE:
            return self._workspace_update(context)
        return {"status": "noop", "stage": stage.value}

    def _workspace_update(self, context: PipelineContext) -> dict[str, Any]:
        """Update the workspace with the pipeline execution result.

        Creates or updates the workspace session for the current identity.
        Links the projection data to the workspace state.
        """
        identity_id = context.identity_id or "anonymous"
        projection = context.projection or {}

        # Find or create workspace for this identity
        workspaces = self._runtime.list_workspaces()
        ws = None
        for w in workspaces:
            ws = w
            break

        if ws is None:
            ws = self._runtime.create_workspace(name=f"Workspace_{identity_id[:8]}")

        return {
            "status": "completed",
            "runtime": self.name,
            "stage": PipelineStage.WORKSPACE_UPDATE.value,
            "workspace_id": ws.workspace_id,
            "panel_count": len(ws.panels),
            "projection_id": projection.get("projection_id", "none"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "runtime": self.name,
            "workspace_count": len(self._runtime._workspaces),
        }


__all__ = [
    "AutomationRuntimeAdapter",
    "CognitiveRuntimeAdapter",
    "ExecutionRuntimeAdapter",
    "MemoryKnowledgeRuntimeAdapter",
    "PlanningRuntimeAdapter",
    "WorkspaceRuntimeAdapter",
]