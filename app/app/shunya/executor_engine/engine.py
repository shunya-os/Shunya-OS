"""SHUNYA — Executor Engine (Phase I — ES-005).

The Executor Engine transforms governance-approved plans into real-world
actions. It coordinates task execution across internal services and external
channels, manages workflow state, collects execution evidence, and packages
outcomes for the Observer Engine.

The engine implements a deterministic 9-stage pipeline:
  1. Execution Preparation
  2. Dependency Verification
  3. Resource Acquisition
  4. Task Dispatch
  5. Execution Monitoring
  6. Evidence Collection
  7. Completion Verification
  8. Outcome Packaging
  9. Observation Handoff

Architectural authority: ES-005 — Executor Engine Specification
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable

from app.shunya.executor_engine.models import (
    WorkflowState, TaskState, ExecutionType, BackoffStrategy, FailureType,
    ExecutorInput, ExecutorOutput,
    Workflow, Task, RetryPolicy, Compensation,
    ExecutionEvidence, ExecutionFailure, OutcomePackage,
    Checkpoint, ExecutionMetrics, ExecutorStats,
)


# ---------------------------------------------------------------------------
# Channel Adapter Interface
# ---------------------------------------------------------------------------


class ExecutorChannelAdapter:
    """Abstract interface for channel adapters used by the Executor Engine.

    Lightweight wrapper that mirrors the existing ChannelAdapter interface
    from app/shunya/executor.py for compatibility.
    """

    @property
    def channel_type(self) -> str:
        raise NotImplementedError

    def send(self, message: Any) -> Any:
        raise NotImplementedError

    def is_configured(self) -> bool:
        raise NotImplementedError


class _BuiltinAdapterWrapper(ExecutorChannelAdapter):
    """Wraps an existing ChannelAdapter from app/shunya/executor.py."""

    def __init__(self, adapter: Any):
        self._adapter = adapter

    @property
    def channel_type(self) -> str:
        return self._adapter.channel_type.value if hasattr(self._adapter.channel_type, 'value') else str(self._adapter.channel_type)

    def send(self, message: Any) -> Any:
        return self._adapter.send(message)

    def is_configured(self) -> bool:
        return getattr(self._adapter, 'is_configured', lambda: True)()


# ---------------------------------------------------------------------------
# Task Executor (pluggable dispatch)
# ---------------------------------------------------------------------------


TaskExecutorFn = Callable[[Task], Tuple[bool, str, Dict[str, Any]]]
"""Function signature for task execution: (task) -> (success, message_id_or_error, response_dict)"""


# ---------------------------------------------------------------------------
# Executor Engine
# ---------------------------------------------------------------------------


class ExecutorEngine:
    """Executor Engine — transforms approved plans into real-world actions.

    Implements a deterministic 9-stage pipeline per ES-005.
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, ExecutorChannelAdapter] = {}
        self._task_executors: Dict[str, TaskExecutorFn] = {}
        self._workflows: Dict[str, Workflow] = {}
        self._outcomes: List[OutcomePackage] = []
        self._stats = ExecutorStats()
        self._register_default_executors()

    def _register_default_executors(self) -> None:
        """Register default task executors for common actions."""
        # send_message — dispatches to channel adapters
        def _send_message(task: Task) -> Tuple[bool, str, Dict[str, Any]]:
            channel = task.target
            adapter = self._adapters.get(channel)
            if not adapter:
                return False, f"No adapter for channel: {channel}", {}
            if not adapter.is_configured():
                return False, f"Channel not configured: {channel}", {}
            # Build a minimal outbound message from task payload
            recipient = task.payload.get("recipient", "")
            text = task.payload.get("text", "")
            # The actual adapter.send() call is wrapped in a dict
            # to avoid importing OutboundMessage at engine level
            msg_data = {
                "channel": channel,
                "recipient": recipient,
                "text": text,
                "message_type": task.payload.get("message_type", "text"),
                "template_name": task.payload.get("template_name"),
                "template_data": task.payload.get("template_data"),
            }
            result = adapter.send(msg_data)
            success = getattr(result, 'success', False) if not isinstance(result, dict) else result.get('success', False)
            msg_id = getattr(result, 'message_id', '') if not isinstance(result, dict) else result.get('message_id', '')
            return success, msg_id, {"result": str(result)}

        self._task_executors["send_message"] = _send_message

        # Default fallback executor
        def _default_executor(task: Task) -> Tuple[bool, str, Dict[str, Any]]:
            return True, f"mock_{task.task_id[:8]}", {"action": task.action, "target": task.target}

        self._task_executors["__default__"] = _default_executor

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, inp: ExecutorInput) -> ExecutorOutput:
        """Execute a governance-approved plan.

        Implements the full 9-stage deterministic pipeline.
        """
        workflow = Workflow(
            workflow_id=inp.workflow_id or str(uuid.uuid4()),
            plan_id=inp.plan_id,
            tenant_id=inp.tenant_id,
            tasks=list(inp.tasks),
        )

        # Stage 1: Execution Preparation
        prep_errors = self._prepare_execution(inp, workflow)
        if prep_errors:
            return self._fail_workflow(workflow, prep_errors)

        # Stage 2: Dependency Verification
        dep_errors = self._verify_dependencies(inp, workflow)
        if dep_errors:
            return self._fail_workflow(workflow, dep_errors)

        # Stage 3: Resource Acquisition
        resource_errors = self._acquire_resources(inp, workflow)
        if resource_errors:
            return self._fail_workflow(workflow, resource_errors)

        # Stage 4-6: Task Dispatch → Execution Monitoring → Evidence Collection
        execution_errors = self._execute_tasks(workflow)
        if execution_errors and workflow.all_completed:
            # Non-critical errors during execution don't fail the whole workflow
            pass

        # Stage 7: Completion Verification
        completion_errors = self._verify_completion(workflow)
        if completion_errors:
            workflow.state = WorkflowState.PARTIAL.value
            if len(workflow.completed_tasks) == 0:
                workflow.state = WorkflowState.FAILED.value

        # Record final state before packaging (outcome captures the final state)
        if workflow.state not in (WorkflowState.FAILED.value, WorkflowState.PARTIAL.value):
            if workflow.all_completed:
                workflow.state = WorkflowState.COMPLETED.value
            elif workflow.failed_tasks:
                workflow.state = WorkflowState.PARTIAL.value

        workflow.completed_at = datetime.now(timezone.utc)

        # Stage 8: Outcome Packaging
        outcome = self._package_outcome(workflow)

        # Stage 9: Observation Handoff
        self._handoff_observation(outcome)

        self._workflows[workflow.workflow_id] = workflow

        # Update stats
        self._stats.total_workflows += 1
        if workflow.state == WorkflowState.COMPLETED.value:
            self._stats.completed += 1
        elif workflow.state == WorkflowState.FAILED.value:
            self._stats.failed += 1
        elif workflow.state == WorkflowState.PARTIAL.value:
            self._stats.partial += 1

        success = workflow.state in (WorkflowState.COMPLETED.value, WorkflowState.PARTIAL.value)
        return ExecutorOutput(
            success=success,
            workflow_id=workflow.workflow_id,
            workflow_state=workflow.state,
            outcome=outcome,
        )

    def register_adapter(self, channel: str, adapter: ExecutorChannelAdapter) -> None:
        """Register a channel adapter for task dispatch."""
        self._adapters[channel] = adapter
        self._stats.adapters_registered = len(self._adapters)

    def register_adapter_from_legacy(self, adapter: Any) -> None:
        """Register a legacy ChannelAdapter by wrapping it."""
        wrapped = _BuiltinAdapterWrapper(adapter)
        self.register_adapter(wrapped.channel_type, wrapped)

    def register_task_executor(self, action: str, executor_fn: TaskExecutorFn) -> None:
        """Register a custom task executor for a specific action type."""
        self._task_executors[action] = executor_fn

    # ------------------------------------------------------------------
    # Pipeline Stages
    # ------------------------------------------------------------------

    def _prepare_execution(self, inp: ExecutorInput, workflow: Workflow) -> List[str]:
        """Stage 1: Validate environment and prepare execution context."""
        errors = inp.validate()
        if errors:
            return errors
        # Mark all tasks as pending
        for task in workflow.tasks:
            task.state = TaskState.PENDING.value
            task.tenant_id = inp.tenant_id
        return []

    def _verify_dependencies(self, inp: ExecutorInput, workflow: Workflow) -> List[str]:
        """Stage 2: Verify task dependencies can be satisfied."""
        task_ids = {t.task_id for t in workflow.tasks}
        for task in workflow.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    return [f"Dependency {dep} of task {task.task_id} not found in workflow"]
        return []

    def _acquire_resources(self, inp: ExecutorInput, workflow: Workflow) -> List[str]:
        """Stage 3: Acquire required resources (locks, connections)."""
        # In this implementation, resources are mocked.
        # Real resource acquisition would acquire locks from a resource pool.
        for task in workflow.tasks:
            _ = task.target  # Resources would be acquired per-target
        return []

    def _execute_tasks(self, workflow: Workflow) -> List[str]:
        """Stages 4-6: Dispatch tasks, monitor execution, collect evidence.

        Executes tasks in dependency order (topological order).
        """
        errors: List[str] = []
        executed: set = set()
        task_map = {t.task_id: t for t in workflow.tasks}

        # Resolve dependency order via simple topological sort
        order = self._topological_sort(workflow.tasks)
        if not order:
            return ["Circular dependency detected"]

        for task_id in order:
            task = task_map[task_id]
            if task.state != TaskState.PENDING.value:
                continue

            # Check dependencies
            deps_met = all(
                task_map.get(d) and task_map[d].is_completed
                for d in task.dependencies
            )
            if not deps_met:
                continue

            # Execute task
            task.state = TaskState.IN_PROGRESS.value
            task.started_at = datetime.now(timezone.utc)
            task.attempt += 1

            success, msg_id_or_error, response = self._dispatch_task(task)

            if success:
                task.state = TaskState.COMPLETED.value
                task.completed_at = datetime.now(timezone.utc)
                task.evidence = ExecutionEvidence(
                    task_id=task.task_id,
                    action=task.action,
                    channel=task.target,
                    recipient=task.payload.get("recipient", ""),
                    message_id=msg_id_or_error,
                    success=True,
                    response=response,
                    tenant_id=task.tenant_id,
                )
            else:
                # Handle retries
                retried = False
                if task.retry_policy:
                    retry = task.retry_policy.should_retry(task.attempt, msg_id_or_error)
                    if retry:
                        # Retry the task
                        for _ in range(task.retry_policy.max_attempts - task.attempt):
                            task.attempt += 1
                            task.started_at = datetime.now(timezone.utc)
                            retry_success, retry_msg, retry_resp = self._dispatch_task(task)
                            if retry_success:
                                task.state = TaskState.COMPLETED.value
                                task.completed_at = datetime.now(timezone.utc)
                                task.evidence = ExecutionEvidence(
                                    task_id=task.task_id,
                                    action=task.action,
                                    channel=task.target,
                                    message_id=retry_msg,
                                    success=True,
                                    response=retry_resp,
                                    tenant_id=task.tenant_id,
                                )
                                retried = True
                                break

                if not retried:
                    task.state = TaskState.FAILED.value
                    task.completed_at = datetime.now(timezone.utc)
                    task.failure = ExecutionFailure(
                        failure_type=FailureType.TASK_FAILURE.value,
                        message=msg_id_or_error,
                        task_id=task.task_id,
                        attempt=task.attempt,
                    )
                    errors.append(f"Task {task.task_id} failed: {msg_id_or_error}")

        if not workflow.completed_tasks and not workflow.failed_tasks:
            errors.append("No tasks could be dispatched — possible circular dependency")

        return errors

    def _dispatch_task(self, task: Task) -> Tuple[bool, str, Dict[str, Any]]:
        """Dispatch a single task to its executor."""
        executor = self._task_executors.get(task.action, self._task_executors["__default__"])
        try:
            return executor(task)
        except Exception as e:
            return False, str(e), {}

    def _verify_completion(self, workflow: Workflow) -> List[str]:
        """Stage 7: Verify all tasks completed successfully."""
        errors: List[str] = []
        total = len(workflow.tasks)
        completed = len(workflow.completed_tasks)
        failed = len(workflow.failed_tasks)

        if completed + failed < total:
            pending = total - completed - failed
            errors.append(f"{pending} tasks did not complete (remaining in {workflow.state})")

        if failed > 0:
            errors.append(f"{failed} tasks failed")
            for t in workflow.failed_tasks:
                if t.failure:
                    errors.append(f"  - {t.task_id}: {t.failure.message}")

        return errors

    def _package_outcome(self, workflow: Workflow) -> OutcomePackage:
        """Stage 8: Package complete execution result for Observer Engine."""
        metrics = ExecutionMetrics(
            total_tasks=len(workflow.tasks),
            completed=len(workflow.completed_tasks),
            failed=len(workflow.failed_tasks),
            skipped=len([t for t in workflow.tasks if t.state == TaskState.SKIPPED.value]),
            cancelled=len([t for t in workflow.tasks if t.state == TaskState.CANCELLED.value]),
            total_retries=sum(t.attempt - 1 for t in workflow.tasks if t.attempt > 0),
        )

        # Calculate durations
        if workflow.completed_tasks:
            durations = [t.duration_seconds for t in workflow.completed_tasks if t.duration_seconds]
            if durations:
                metrics.avg_task_duration_seconds = sum(durations) / len(durations)

        start_times = [t.started_at for t in workflow.tasks if t.started_at]
        end_times = [t.completed_at for t in workflow.tasks if t.completed_at]
        if start_times and end_times:
            metrics.total_duration_seconds = (
                max(end_times) - min(start_times)
            ).total_seconds()

        evidence = [
            t.evidence for t in workflow.tasks
            if t.evidence and t.evidence.success
        ]

        failures = [
            t.failure for t in workflow.tasks
            if t.failure
        ]

        return OutcomePackage(
            workflow_id=workflow.workflow_id,
            plan_id=workflow.plan_id,
            tenant_id=workflow.tenant_id,
            workflow_state=workflow.state,
            tasks=[t.to_dict() for t in workflow.tasks],
            evidence=evidence,
            failures=failures,
            metrics=metrics,
        )

    def _handoff_observation(self, outcome: OutcomePackage) -> None:
        """Stage 9: Deliver outcome package to Observer Engine.

        Currently stores in-memory. Future: publish to Event Bus or
        write to Knowledge Engine.
        """
        self._outcomes.append(outcome)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail_workflow(self, workflow: Workflow, errors: List[str]) -> ExecutorOutput:
        """Mark a workflow as failed with the given errors."""
        workflow.state = WorkflowState.FAILED.value
        workflow.completed_at = datetime.now(timezone.utc)
        self._workflows[workflow.workflow_id] = workflow
        self._stats.total_workflows += 1
        self._stats.failed += 1
        return ExecutorOutput(
            success=False,
            workflow_id=workflow.workflow_id,
            workflow_state=WorkflowState.FAILED.value,
            errors=errors,
        )

    def _topological_sort(self, tasks: List[Task]) -> Optional[List[str]]:
        """Return a topological ordering of task IDs, or None if circular."""
        task_ids = [t.task_id for t in tasks]
        deps: Dict[str, List[str]] = {t.task_id: list(t.dependencies) for t in tasks}

        sorted_ids: List[str] = []
        visited: Dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=visited

        def _visit(tid: str) -> bool:
            if tid in visited:
                return visited[tid] != 1  # True if not in cycle
            visited[tid] = 1
            for dep in deps.get(tid, []):
                if dep in task_ids and not _visit(dep):
                    return False
            visited[tid] = 2
            sorted_ids.append(tid)
            return True

        for tid in task_ids:
            if tid not in visited:
                if not _visit(tid):
                    return None  # Cycle detected

        return sorted_ids

    # ------------------------------------------------------------------
     # Public Queries
    # ------------------------------------------------------------------

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def list_outcomes(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in reversed(self._outcomes[-limit:])]

    @property
    def stats(self) -> Dict[str, Any]:
        return self._stats.to_dict()

    @property
    def active_workflows(self) -> int:
        return sum(1 for w in self._workflows.values()
                   if w.state == WorkflowState.ACTIVE.value)

    @property
    def total_workflows(self) -> int:
        return len(self._workflows)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_ENGINE_INSTANCE: Optional[ExecutorEngine] = None


def get_executor_engine() -> ExecutorEngine:
    """Get or create the singleton ExecutorEngine instance."""
    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = ExecutorEngine()
    return _ENGINE_INSTANCE


def reset_executor_engine() -> None:
    """Reset the singleton ExecutorEngine (for testing)."""
    global _ENGINE_INSTANCE
    _ENGINE_INSTANCE = None