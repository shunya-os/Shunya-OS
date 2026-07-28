"""SHUNYA Execution Runtime — Orchestrator.

The Execution Runtime is the authoritative orchestration layer for all
real-world work. No business capability may execute work directly.
The Cognitive Runtime decides. The Execution Runtime performs.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from core.execution_runtime.models import (
    ActionContract,
    EvidenceRecord,
    ExecutionGraph,
    ExecutionInstance,
    ExecutionPolicies,
    ExecutionState,
    ExecutionTrace,
    RegisteredAction,
    ScheduleType,
    _now_iso,
)

logger = logging.getLogger(__name__)


class ExecutionRuntime:
    """Authoritative execution layer. The only layer authorised to execute work."""

    def __init__(self, policies: ExecutionPolicies | None = None):
        self._actions: dict[str, RegisteredAction] = {}
        self._instances: dict[str, ExecutionInstance] = {}
        self._graph = ExecutionGraph()
        self._policies = policies or ExecutionPolicies()
        self._running: set[str] = set()
        self._semaphore: asyncio.Semaphore | None = None

    # ── Action Registration (Plugin Architecture) ──────────────────────

    def register_action(
        self,
        action_id: str,
        contract: ActionContract | None = None,
        handler: Any = None,
    ) -> None:
        """Register an executable action. No runtime code changes required."""
        if action_id in self._actions:
            raise ValueError(f"Action already registered: {action_id}")

        if contract is None:
            contract = ActionContract(action_id=action_id)

        self._actions[action_id] = RegisteredAction(
            action_id=action_id,
            contract=contract,
            handler=handler,
            handler_name=getattr(handler, "__name__", "unknown"),
        )

    def get_action(self, action_id: str) -> RegisteredAction | None:
        return self._actions.get(action_id)

    def list_actions(self) -> list[RegisteredAction]:
        return list(self._actions.values())

    # ── Instance Creation ──────────────────────────────────────────────

    def create_instance(
        self,
        action_id: str,
        actor: str = "",
        objective: str = "",
        inputs: dict[str, Any] | None = None,
        priority: int = 100,
        dependencies: list[str] | None = None,
        parent_execution_id: str | None = None,
        root_execution_id: str = "",
        session_id: str = "",
    ) -> ExecutionInstance:
        """Create a new execution instance ready to be scheduled."""
        action = self._actions.get(action_id)
        if action is None:
            raise ValueError(f"Unknown action: {action_id}")

        instance = ExecutionInstance(
            action_id=action_id,
            actor=actor,
            objective=objective or action.contract.description,
            inputs=inputs or {},
            priority=priority,
            dependencies=dependencies or [],
            parent_execution_id=parent_execution_id,
            root_execution_id=root_execution_id or "",
            session_id=session_id,
            max_retries=action.contract.default_retries,
            timeout_ms=action.contract.default_timeout_ms,
        )
        instance.timing.created_at = instance.created_at
        instance._record_event("ExecutionCreated", {
            "action_id": action_id,
            "actor": actor,
            "objective": instance.objective,
        })

        self._instances[instance.execution_id] = instance
        self._graph.add_instance(instance)

        return instance

    def get_instance(self, execution_id: str) -> ExecutionInstance | None:
        return self._instances.get(execution_id)

    # ── Scheduling ─────────────────────────────────────────────────────

    async def schedule(
        self,
        instance: ExecutionInstance,
        schedule_type: ScheduleType = ScheduleType.IMMEDIATE,
        scheduled_at: str | None = None,
        delay_ms: int | None = None,
    ) -> ExecutionInstance:
        """Schedule an execution instance."""
        if instance.state != ExecutionState.CREATED:
            raise ValueError(f"Cannot schedule instance in state: {instance.state.value}")

        # Check dependencies
        if instance.dependencies:
            unsatisfied = [
                dep_id for dep_id in instance.dependencies
                if dep_id not in self._instances
                or self._instances[dep_id].state not in (
                    ExecutionState.COMPLETED, ExecutionState.READY
                )
            ]
            if unsatisfied:
                instance.transition_to(ExecutionState.BLOCKED,
                                       reason=f"Unsatisfied dependencies: {unsatisfied}")
                return instance

        instance.transition_to(ExecutionState.READY)
        instance.timing.queued_at = _now_iso()

        if schedule_type == ScheduleType.IMMEDIATE:
            return await self._execute(instance)
        elif schedule_type == ScheduleType.DELAYED and delay_ms:
            await asyncio.sleep(delay_ms / 1000)
            return await self._execute(instance)
        elif schedule_type == ScheduleType.SCHEDULED and scheduled_at:
            # Simple delay: compute time difference
            # In production this would use a proper scheduler
            return instance  # Will be picked up by scheduler loop
        else:
            return instance

    # ── Execution ──────────────────────────────────────────────────────

    async def _execute(self, instance: ExecutionInstance) -> ExecutionInstance:
        """Execute an instance through its action handler."""
        if instance.state not in (ExecutionState.READY, ExecutionState.QUEUED):
            raise ValueError(f"Cannot execute instance in state: {instance.state.value}")

        action = self._actions.get(instance.action_id)
        if action is None:
            instance.transition_to(ExecutionState.FAILED, reason=f"Unknown action: {instance.action_id}")
            return instance

        # Concurrency limiting
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(
                self._policies.concurrency.max_concurrent_executions
            )

        if instance.state not in (ExecutionState.QUEUED, ExecutionState.EXECUTING):
            instance.transition_to(ExecutionState.QUEUED)
        instance.timing.started_at = _now_iso()

        async with self._semaphore:
            if instance.state == ExecutionState.QUEUED:
                instance.transition_to(ExecutionState.EXECUTING)
            self._running.add(instance.execution_id)
            start_time = time.time()

            # Record execution start evidence
            self._record_evidence(instance, "execution_started", {
                "action_id": instance.action_id,
                "inputs": instance.inputs,
            })

            try:
                # Check timeout policy
                timeout = instance.timeout_ms / 1000 if instance.timeout_ms > 0 else None

                if action.handler is not None:
                    handler_result = action.handler(instance.inputs)
                    if asyncio.iscoroutine(handler_result):
                        output = await asyncio.wait_for(handler_result, timeout=timeout)
                    else:
                        output = handler_result
                else:
                    # No handler: mark as success with no output
                    output = {}

                duration = (time.time() - start_time) * 1000
                instance.outputs = output if isinstance(output, dict) else {"result": output}
                instance.timing.execution_duration_ms = round(duration, 2)
                instance.timing.completed_at = _now_iso()
                instance.confidence = 1.0

                # Record completion evidence
                self._record_evidence(instance, "execution_completed", {
                    "outputs": instance.outputs,
                    "duration_ms": duration,
                })

                instance.transition_to(ExecutionState.COMPLETED)
                instance._record_event("ExecutionCompleted", {
                    "duration_ms": duration,
                    "action_id": instance.action_id,
                })

            except asyncio.TimeoutError:
                instance.timing.execution_duration_ms = (time.time() - start_time) * 1000
                self._record_evidence(instance, "execution_failed", {
                    "error": "timeout",
                    "duration_ms": instance.timing.execution_duration_ms,
                })
                await self._handle_failure(instance, "timeout")

            except (ValueError, TypeError, RuntimeError, OSError) as exc:
                instance.timing.execution_duration_ms = (time.time() - start_time) * 1000
                self._record_evidence(instance, "execution_failed", {
                    "error": str(exc),
                    "duration_ms": instance.timing.execution_duration_ms,
                })
                await self._handle_failure(instance, str(exc))

            except asyncio.CancelledError:
                instance.timing.execution_duration_ms = (time.time() - start_time) * 1000
                self._record_evidence(instance, "execution_failed", {
                    "error": "cancelled",
                })
                instance.transition_to(ExecutionState.CANCELLED)

            finally:
                self._running.discard(instance.execution_id)

            # Update timing
            start_ts = instance.timing.created_at or instance.timing.queued_at or instance.timing.started_at
            instance.timing.total_duration_ms = (time.time() - (
                time.mktime(time.strptime(start_ts[:19], "%Y-%m-%dT%H:%M:%S"))
                if start_ts else start_time
            )) * 1000

            # Update trace
            instance.trace.execution_duration_ms = instance.timing.execution_duration_ms
            instance.trace.total_duration_ms = instance.timing.total_duration_ms

            # Check dependents
            await self._check_dependents(instance)

        return instance

    async def _handle_failure(self, instance: ExecutionInstance, error: str) -> None:
        """Handle execution failure with retry/rollback logic."""
        instance.retry_count += 1
        instance._record_event("ExecutionFailed", {"error": error, "retry_count": instance.retry_count})

        if instance.retry_count <= instance.max_retries:
            # Retry — queue for re-execution
            logger.info("Retrying %s (attempt %d/%d)",
                       instance.execution_id, instance.retry_count, instance.max_retries)
            backoff = self._policies.retry.backoff_ms * (2 ** (instance.retry_count - 1))
            await asyncio.sleep(backoff / 1000)
            instance.transition_to(ExecutionState.QUEUED)
            await self._execute(instance)
        else:
            # Retries exhausted
            instance.transition_to(ExecutionState.FAILED, reason=error)

            if self._policies.rollback.auto_rollback_on_failure:
                await self._rollback(instance)

    # ── Rollback & Compensation ────────────────────────────────────────

    async def _rollback(self, instance: ExecutionInstance) -> None:
        """Roll back an execution and its children."""
        instance.transition_to(ExecutionState.ROLLED_BACK)
        instance.trace.rollback_count += 1

        action = self._actions.get(instance.action_id)
        if action and action.contract.has_rollback:
            try:
                # Invoke rollback handler
                if action.handler is not None and hasattr(action.handler, "rollback"):
                    await action.handler.rollback(instance.inputs, instance.outputs)
                logger.info("Rolled back %s", instance.execution_id)
            except (ValueError, TypeError, RuntimeError, OSError) as exc:
                logger.warning("Rollback failed for %s: %s", instance.execution_id, exc)

        self._record_evidence(instance, "execution_rolled_back", {
            "reason": "retries exhausted",
            "retry_count": instance.retry_count,
        })

        # Recursively roll back dependents
        dependents = self._graph.get_dependents(instance.execution_id)
        for dep_id in dependents:
            dep = self._instances.get(dep_id)
            if dep and not dep.state.is_terminal:
                await self._rollback(dep)

    # ── Cancellation ───────────────────────────────────────────────────

    def cancel(self, instance: ExecutionInstance, reason: str = "User requested cancellation") -> None:
        """Cancel an execution instance."""
        if instance.state.is_terminal:
            return
        instance.transition_to(ExecutionState.CANCELLED, reason=reason)
        instance._record_event("ExecutionCancelled", {"reason": reason})
        self._record_evidence(instance, "execution_cancelled", {"reason": reason})
        self._running.discard(instance.execution_id)

    # ── Blocking / Unblocking ──────────────────────────────────────────

    def block(self, instance: ExecutionInstance, reason: str = "") -> None:
        """Block an execution waiting for a dependency."""
        if instance.state == ExecutionState.READY:
            instance.transition_to(ExecutionState.BLOCKED, reason=reason)

    def unblock(self, instance: ExecutionInstance) -> None:
        """Unblock an execution."""
        if instance.state == ExecutionState.BLOCKED:
            instance.transition_to(ExecutionState.READY, reason="dependency resolved")

    # ── Dependency Management ──────────────────────────────────────────

    async def _check_dependents(self, completed_instance: ExecutionInstance) -> None:
        """Check and schedule any executions that depend on this one."""
        dependents = self._graph.get_dependents(completed_instance.execution_id)
        for dep_id in dependents:
            dep = self._instances.get(dep_id)
            if dep is None or dep.state != ExecutionState.BLOCKED:
                continue
            # Check if all dependencies are satisfied
            all_satisfied = all(
                self._instances.get(did) is not None
                and self._instances[did].state == ExecutionState.COMPLETED
                for did in dep.dependencies
                if did in self._instances
            )
            if all_satisfied:
                self.unblock(dep)
                await self.schedule(dep)

    # ── Evidence ───────────────────────────────────────────────────────

    def _record_evidence(
        self, instance: ExecutionInstance, event_type: str, data: dict[str, Any]
    ) -> EvidenceRecord:
        evidence = EvidenceRecord(
            execution_id=instance.execution_id,
            event_type=event_type,
            data=data,
        )
        instance.evidence.append(evidence)
        return evidence

    # ── Observability ──────────────────────────────────────────────────

    def get_trace(self, instance: ExecutionInstance) -> ExecutionTrace:
        """Compute complete execution trace for an instance."""
        trace = instance.trace
        trace.dependency_graph = {
            eid: list(inst.dependencies)
            for eid, inst in self._instances.items()
        }
        trace.critical_path = self._graph.compute_critical_path()
        return trace

    # ── Health ─────────────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """Return runtime health status."""
        return {
            "status": "healthy",
            "runtime": "execution_runtime",
            "actions_registered": len(self._actions),
            "active_instances": len(self._running),
            "total_instances": len(self._instances),
            "policies": {
                "retry_max": self._policies.retry.max_retries,
                "concurrency_max": self._policies.concurrency.max_concurrent_executions,
                "timeout_ms": self._policies.timeout.default_timeout_ms,
                "auto_rollback": self._policies.rollback.auto_rollback_on_failure,
            },
            "actions": {aid: {"description": ra.contract.description}
                        for aid, ra in self._actions.items()},
        }

    # ── Graph Validation ──────────────────────────────────────────────

    def validate_graph(self) -> list[str]:
        """Validate the execution graph. Returns list of issues."""
        issues: list[str] = []
        if self._graph.has_cycle():
            issues.append("Execution graph contains a cycle")
        for eid, instance in self._instances.items():
            for dep_id in instance.dependencies:
                if dep_id not in self._instances:
                    issues.append(f"Instance {eid} references unknown dependency {dep_id}")
        return issues

    # ── Batch execution ────────────────────────────────────────────────

    async def execute_batch(
        self, instances: list[ExecutionInstance]
    ) -> list[ExecutionInstance]:
        """Execute multiple instances, respecting dependencies."""
        if not instances:
            return []

        results: list[ExecutionInstance] = []
        pending = list(instances)

        while pending:
            batch: list[ExecutionInstance] = []
            remaining: list[ExecutionInstance] = []

            for inst in pending:
                dep_results = []
                for d in inst.dependencies:
                    r = next((r for r in results if r.execution_id == d), None)
                    dep_results.append(r is not None and r.state == ExecutionState.COMPLETED)
                deps_satisfied = all(dep_results)
                if deps_satisfied:
                    batch.append(inst)
                else:
                    remaining.append(inst)

            if not batch:
                # Cycle or deadlock
                remaining_ids = [e.execution_id for e in remaining]
                logger.warning("Deadlock detected: %s", remaining_ids)
                for inst in remaining:
                    inst.transition_to(ExecutionState.FAILED, reason="deadlock")
                    results.append(inst)
                break

            # Execute batch concurrently
            tasks = [self.schedule(inst) for inst in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    batch[i].transition_to(ExecutionState.FAILED, reason=str(result))
                    results.append(batch[i])
                else:
                    results.append(result)  # type: ignore[arg-type]

            pending = remaining

        return results

    # ── Convenience: register common actions ───────────────────────────

    def register_default_actions(self) -> None:
        """Register common execution actions for testing and basic workflows."""
        # No-op action (for testing)
        self.register_action(
            "noop",
            ActionContract(action_id="noop", description="No-operation action", idempotent=True),
            handler=lambda inputs: {"status": "ok", **inputs},
        )

        # Echo action
        self.register_action(
            "echo",
            ActionContract(action_id="echo", description="Echo inputs as outputs"),
            handler=lambda inputs: {"echo": inputs},
        )

        # Delay action
        async def delay_handler(inputs: dict[str, Any]) -> dict[str, Any]:
            delay_ms = inputs.get("delay_ms", 0)
            await asyncio.sleep(delay_ms / 1000)
            return {"delayed": True, "duration_ms": delay_ms}

        self.register_action(
            "delay",
            ActionContract(action_id="delay", description="Delay execution"),
            handler=delay_handler,
        )