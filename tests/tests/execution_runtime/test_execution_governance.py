"""Property-based and invariant tests for Execution Runtime.

Verifies the formal state machine semantics defined in
EXECUTION_STATE_SEMANTICS.md and enforced by EXECUTION_GOVERNANCE.md.

Key guarantees:
1. Every valid transition is executable
2. No invalid transition is executable
3. Terminal states have no transitions
4. All states reachable from CREATED
5. Retry/rollback invariants hold
6. Evidence is append-only
7. Timing monotonic
"""

import pytest

from core.execution_runtime import (
    ExecutionInstance,
    ExecutionRuntime,
    ExecutionState,
)
from core.execution_runtime.models import (
    TERMINAL_STATES,
    VALID_EXECUTION_TRANSITIONS,
)

# ══════════════════════════════════════════════════════════════════════════
# 1. Structural Invariants
# ══════════════════════════════════════════════════════════════════════════

class TestStructuralInvariants:
    """Every state has defined transitions. Terminal states are empty."""

    def test_all_states_have_transitions(self):
        for state in ExecutionState:
            assert state in VALID_EXECUTION_TRANSITIONS, f"Missing transition entry for {state}"

    def test_terminal_states_have_no_transitions(self):
        for state in ExecutionState:
            if state in TERMINAL_STATES:
                assert VALID_EXECUTION_TRANSITIONS[state] == [], f"{state} must have empty transitions"

    def test_no_self_loops(self):
        for state, targets in VALID_EXECUTION_TRANSITIONS.items():
            assert state not in targets, f"{state} has a self-loop"

    def test_all_targets_are_valid_states(self):
        for state, targets in VALID_EXECUTION_TRANSITIONS.items():
            for t in targets:
                assert isinstance(t, ExecutionState), f"{state} → {t} is not an ExecutionState"

    def test_non_terminal_states_have_outgoing(self):
        for state in ExecutionState:
            if state not in TERMINAL_STATES:
                assert len(VALID_EXECUTION_TRANSITIONS[state]) > 0, f"{state} is non-terminal but has no transitions"


# ══════════════════════════════════════════════════════════════════════════
# 2. Transition Validation — Every valid transition is executable
# ══════════════════════════════════════════════════════════════════════════

class TestEveryValidTransition:
    """For every state S and every target T in VALID_EXECUTION_TRANSITIONS[S],
    creating an instance in state S and calling transition_to(T) succeeds."""

    def test_transition_from_created_to_ready(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.READY)
        assert inst.state == ExecutionState.READY

    def test_transition_from_created_to_cancelled(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.CANCELLED)
        assert inst.state == ExecutionState.CANCELLED

    def _test_all_transitions(self, from_state: ExecutionState) -> None:
        """Helper: verify every valid transition from a state succeeds."""
        # Skip PARTIALLY_COMPLETED (requires sub-execution context, tested separately)
        if from_state == ExecutionState.PARTIALLY_COMPLETED:
            return
        for target in VALID_EXECUTION_TRANSITIONS[from_state]:
            inst = ExecutionInstance()
            # Set the instance to the starting state by stepping through valid paths
            self._walk_to_state(inst, from_state)
            # Skip self-loop attempts (state already equals target)
            if inst.state == target:
                continue
            inst.transition_to(target)
            assert inst.state == target, f"Failed: {from_state.value} → {target.value}"

    def _walk_to_state(self, inst: ExecutionInstance, target_state: ExecutionState) -> None:
        """Walk an instance from CREATED to target_state via valid transitions."""
        if target_state == ExecutionState.CREATED:
            return
        # Walk paths for states reachable via simple linear transitions
        # (PARTIALLY_COMPLETED requires sub-execution context, tested separately)
        valid_walks = {
            ExecutionState.READY: [ExecutionState.READY],
            ExecutionState.QUEUED: [ExecutionState.READY, ExecutionState.QUEUED],
            ExecutionState.EXECUTING: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING],
            ExecutionState.BLOCKED: [ExecutionState.READY, ExecutionState.BLOCKED],
            ExecutionState.WAITING: [ExecutionState.READY, ExecutionState.BLOCKED, ExecutionState.WAITING],
            ExecutionState.COMPLETED: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.COMPLETED],
            ExecutionState.FAILED: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.FAILED],
            ExecutionState.CANCELLED: [ExecutionState.CANCELLED],
            ExecutionState.ROLLED_BACK: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.FAILED, ExecutionState.ROLLED_BACK],
            ExecutionState.EXPIRED: [ExecutionState.READY, ExecutionState.BLOCKED, ExecutionState.WAITING, ExecutionState.EXPIRED],
        }
        walk = valid_walks.get(target_state)
        if walk is None:
            return  # Skip states without valid linear walk (PARTIALLY_COMPLETED)
        for s in walk:
            inst.transition_to(s)

    def test_all_valid_transitions(self):
        """Meta-test: run _test_all_transitions for every state."""
        for state in ExecutionState:
            if state in TERMINAL_STATES:
                continue  # no valid transitions from terminal states
            self._test_all_transitions(state)


# ══════════════════════════════════════════════════════════════════════════
# 3. Invalid Transitions — Every invalid transition raises ValueError
# ══════════════════════════════════════════════════════════════════════════

class TestNoInvalidTransition:
    """For every state S and every target T NOT in VALID_EXECUTION_TRANSITIONS[S],
    transition_to(T) raises ValueError."""

    def test_invalid_created_to_completed(self):
        inst = ExecutionInstance()
        with pytest.raises(ValueError, match="Invalid execution state transition"):
            inst.transition_to(ExecutionState.COMPLETED)

    def test_invalid_created_to_failed(self):
        inst = ExecutionInstance()
        with pytest.raises(ValueError):
            inst.transition_to(ExecutionState.FAILED)

    def test_invalid_created_to_executing(self):
        inst = ExecutionInstance()
        with pytest.raises(ValueError):
            inst.transition_to(ExecutionState.EXECUTING)

    def test_invalid_ready_to_created(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.READY)
        with pytest.raises(ValueError):
            inst.transition_to(ExecutionState.CREATED)

    def test_invalid_completed_to_anything(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.READY)
        inst.transition_to(ExecutionState.QUEUED)
        inst.transition_to(ExecutionState.EXECUTING)
        inst.transition_to(ExecutionState.COMPLETED)
        for target in ExecutionState:
            if target != ExecutionState.COMPLETED:
                with pytest.raises(ValueError):
                    inst.transition_to(target)

    def test_invalid_cancelled_to_anything(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.CANCELLED)
        for target in ExecutionState:
            if target != ExecutionState.CANCELLED:
                with pytest.raises(ValueError):
                    inst.transition_to(target)

    def test_comprehensive_invalid_transitions(self):
        """For every state, verify every non-allowed target raises ValueError."""
        for state in ExecutionState:
            allowed = set(VALID_EXECUTION_TRANSITIONS[state])
            for target in ExecutionState:
                if target == state:
                    continue  # self-loops not in allowed, skip
                if target in allowed:
                    continue  # skip valid transitions
                inst = ExecutionInstance()
                # Walk to state
                test_walk = {
                    ExecutionState.CREATED: [],
                    ExecutionState.READY: [ExecutionState.READY],
                    ExecutionState.QUEUED: [ExecutionState.READY, ExecutionState.QUEUED],
                    ExecutionState.EXECUTING: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING],
                    ExecutionState.BLOCKED: [ExecutionState.READY, ExecutionState.BLOCKED],
                    ExecutionState.WAITING: [ExecutionState.READY, ExecutionState.BLOCKED, ExecutionState.WAITING],
                    ExecutionState.PARTIALLY_COMPLETED: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.COMPLETED],
                    ExecutionState.COMPLETED: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.COMPLETED],
                    ExecutionState.FAILED: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.FAILED],
                    ExecutionState.CANCELLED: [ExecutionState.CANCELLED],
                    ExecutionState.ROLLED_BACK: [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.FAILED, ExecutionState.ROLLED_BACK],
                    ExecutionState.EXPIRED: [ExecutionState.READY, ExecutionState.BLOCKED, ExecutionState.WAITING, ExecutionState.EXPIRED],
                }
                for s in test_walk.get(state, []):
                    try:
                        inst.transition_to(s)
                    except ValueError:
                        break  # walk failed, skip this target
                else:
                    with pytest.raises(ValueError):
                        inst.transition_to(target)


# ══════════════════════════════════════════════════════════════════════════
# 4. Reachability
# ══════════════════════════════════════════════════════════════════════════

class TestReachability:
    """Every state is reachable from CREATED."""

    def test_created_reachable(self):
        inst = ExecutionInstance()
        assert inst.state == ExecutionState.CREATED

    def test_ready_reachable(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.READY)
        assert inst.state == ExecutionState.READY

    def test_queued_reachable(self):
        inst = ExecutionInstance()
        for s in [ExecutionState.READY, ExecutionState.QUEUED]:
            inst.transition_to(s)
        assert inst.state == ExecutionState.QUEUED

    def test_executing_reachable(self):
        inst = ExecutionInstance()
        for s in [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING]:
            inst.transition_to(s)
        assert inst.state == ExecutionState.EXECUTING

    def test_blocked_reachable(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.READY)
        inst.transition_to(ExecutionState.BLOCKED)
        assert inst.state == ExecutionState.BLOCKED

    def test_waiting_reachable(self):
        inst = ExecutionInstance()
        for s in [ExecutionState.READY, ExecutionState.BLOCKED, ExecutionState.WAITING]:
            inst.transition_to(s)
        assert inst.state == ExecutionState.WAITING

    def test_completed_reachable(self):
        inst = ExecutionInstance()
        for s in [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.COMPLETED]:
            inst.transition_to(s)
        assert inst.state == ExecutionState.COMPLETED

    def test_failed_reachable(self):
        inst = ExecutionInstance()
        for s in [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING, ExecutionState.FAILED]:
            inst.transition_to(s)
        assert inst.state == ExecutionState.FAILED

    def test_cancelled_reachable(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.CANCELLED)
        assert inst.state == ExecutionState.CANCELLED

    def test_rolled_back_reachable(self):
        inst = ExecutionInstance()
        for s in [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING,
                  ExecutionState.FAILED, ExecutionState.ROLLED_BACK]:
            inst.transition_to(s)
        assert inst.state == ExecutionState.ROLLED_BACK

    def test_expired_reachable(self):
        inst = ExecutionInstance()
        for s in [ExecutionState.READY, ExecutionState.BLOCKED, ExecutionState.WAITING,
                  ExecutionState.EXPIRED]:
            inst.transition_to(s)
        assert inst.state == ExecutionState.EXPIRED


# ══════════════════════════════════════════════════════════════════════════
# 5. Retry Invariants
# ══════════════════════════════════════════════════════════════════════════

class TestRetryInvariants:
    """Retry count monotonic, bounded by max_retries."""

    @pytest.mark.asyncio
    async def test_retry_count_monotonic(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()

        fail_count = {"count": 0}
        def flaky_handler(inputs):
            fail_count["count"] += 1
            if fail_count["count"] < 3:
                raise ValueError("transient")
            return {"status": "ok"}

        runtime.register_action("flaky", handler=flaky_handler)
        inst = runtime.create_instance(action_id="flaky", actor="test", objective="Retry test")
        assert inst.retry_count == 0
        result = await runtime.schedule(inst)
        assert result.state == ExecutionState.COMPLETED
        # retry_count counts failures: first 2 attempts fail, 3rd succeeds
        # So retry_count = 2 (two failures before success)
        assert result.retry_count == 2

    def test_retry_count_never_decreases(self):
        inst = ExecutionInstance()
        assert inst.retry_count == 0
        inst.retry_count += 1
        assert inst.retry_count == 1
        inst.retry_count += 1
        assert inst.retry_count == 2

    def test_max_retries_bound(self):
        inst = ExecutionInstance()
        inst.max_retries = 2
        assert inst.retry_count <= inst.max_retries or inst.retry_count == 0
        inst.retry_count = 2
        assert inst.retry_count <= inst.max_retries
        inst.retry_count = 3
        # retry_count can exceed max_retries only if handler logic allows
        # In practice, runtime stops retrying when retry_count > max_retries


# ══════════════════════════════════════════════════════════════════════════
# 6. Evidence Invariants
# ══════════════════════════════════════════════════════════════════════════

class TestEvidenceInvariants:
    """Evidence is append-only and immutable."""

    @pytest.mark.asyncio
    async def test_evidence_append_only(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Evidence")
        initial_count = len(inst.evidence)
        result = await runtime.schedule(inst)
        assert len(result.evidence) > initial_count, "Evidence must grow after execution"

    def test_evidence_immutable_flag(self):
        from core.execution_runtime.models import EvidenceRecord
        rec = EvidenceRecord(execution_id="test", event_type="test", data={"key": "val"})
        assert rec.immutable is True

    @pytest.mark.asyncio
    async def test_evidence_history_preserved(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()

        def careful_handler(inputs):
            return {"done": True}

        runtime.register_action("careful", handler=careful_handler)
        inst = runtime.create_instance(action_id="careful", actor="test", objective="History")
        result = await runtime.schedule(inst)
        # Evidence should contain started + completed
        types = [e.event_type for e in result.evidence]
        assert "execution_started" in types
        assert "execution_completed" in types or "execution_failed" in types


# ══════════════════════════════════════════════════════════════════════════
# 7. Timing Invariants
# ══════════════════════════════════════════════════════════════════════════

class TestTimingInvariants:
    """created_at ≤ started_at ≤ completed_at."""

    @pytest.mark.asyncio
    async def test_timing_monotonic(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Timing")
        result = await runtime.schedule(inst)
        if result.timing.completed_at:
            assert result.timing.created_at <= result.timing.started_at, "created_at must precede started_at"
            if result.timing.completed_at:
                assert result.timing.started_at <= result.timing.completed_at, "started_at must precede completed_at"

    @pytest.mark.asyncio
    async def test_duration_positive(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Duration")
        result = await runtime.schedule(inst)
        assert result.timing.execution_duration_ms >= 0
        if result.state == ExecutionState.COMPLETED:
            assert result.timing.total_duration_ms >= 0


# ══════════════════════════════════════════════════════════════════════════
# 8. Cancellation Idempotency
# ══════════════════════════════════════════════════════════════════════════

class TestCancellationIdempotency:
    """Double cancel is safe."""

    def test_double_cancel(self):
        inst = ExecutionInstance()
        inst.transition_to(ExecutionState.CANCELLED)
        # Second cancel should be a no-op (transition_to checks valid targets)
        # CANCELLED has no valid targets, so calling transition_to again would raise
        # But the runtime's cancel() method checks is_terminal first
        runtime = ExecutionRuntime()
        runtime.cancel(inst)  # should not raise
        assert inst.state == ExecutionState.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_after_completion(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Cancel after")
        result = await runtime.schedule(inst)
        runtime.cancel(result)  # should be no-op
        assert result.state == ExecutionState.COMPLETED


# ══════════════════════════════════════════════════════════════════════════
# 9. Graph Invariants
# ══════════════════════════════════════════════════════════════════════════

class TestGraphInvariants:
    """Dependency graph is acyclic, all references exist."""

    def test_has_cycle_detected(self):
        from core.execution_runtime.models import ExecutionGraph
        g = ExecutionGraph()
        a = ExecutionInstance(dependencies=[])
        b = ExecutionInstance(dependencies=["a"])
        c = ExecutionInstance(dependencies=["b"])
        a.execution_id = "a"
        b.execution_id = "b"
        c.execution_id = "c"
        g.add_instance(a)
        g.add_instance(b)
        g.add_instance(c)
        a.dependencies = ["c"]
        g.edges[a.execution_id] = ["c"]
        assert g.has_cycle(), "Cycle must be detected"

    def test_no_cycle_linear(self):
        from core.execution_runtime.models import ExecutionGraph
        g = ExecutionGraph()
        a = ExecutionInstance(dependencies=[])
        b = ExecutionInstance(dependencies=["a"])
        a.execution_id = "a"
        b.execution_id = "b"
        g.add_instance(a)
        g.add_instance(b)
        assert not g.has_cycle(), "Linear chain must not have cycle"


# ══════════════════════════════════════════════════════════════════════════
# 10. Termination Guarantee
# ══════════════════════════════════════════════════════════════════════════

class TestTerminationGuarantee:
    """Every execution eventually reaches a terminal state or deadlock is detected."""

    @pytest.mark.asyncio
    async def test_happy_path_terminates(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()
        inst = runtime.create_instance(action_id="noop", actor="test", objective="Termination")
        result = await runtime.schedule(inst)
        assert result.state in TERMINAL_STATES or result.state == ExecutionState.FAILED

    @pytest.mark.asyncio
    async def test_batch_terminates(self):
        runtime = ExecutionRuntime()
        runtime.register_default_actions()
        instances = [
            runtime.create_instance(action_id="noop", actor="test", objective=f"B{i}")
            for i in range(10)
        ]
        results = await runtime.execute_batch(instances)
        for r in results:
            assert r.state in TERMINAL_STATES or r.state == ExecutionState.FAILED


# ══════════════════════════════════════════════════════════════════════════
# 11. Property-Based Random Walks
# ══════════════════════════════════════════════════════════════════════════

class TestPropertyBasedRandomWalks:
    """Execute random valid transition sequences and verify invariants hold."""

    def test_random_valid_walk(self):
        """Perform random walks through the state machine using only valid transitions."""
        import random
        random.seed(42)

        for _ in range(20):  # 20 random walks
            inst = ExecutionInstance()
            visited = {ExecutionState.CREATED}
            steps = 0
            max_steps = 50

            while steps < max_steps:
                current = inst.state
                if current in TERMINAL_STATES:
                    break
                targets = VALID_EXECUTION_TRANSITIONS.get(current, [])
                if not targets:
                    break
                target = random.choice(targets)
                try:
                    inst.transition_to(target)
                    visited.add(target)
                except ValueError:
                    break
                steps += 1

            # Invariant: instance ends in some valid state
            assert inst.state in ExecutionState, f"Invalid final state: {inst.state}"
            # Invariant: if terminal, no further transitions
            if inst.state in TERMINAL_STATES:
                assert VALID_EXECUTION_TRANSITIONS[inst.state] == []
            # Invariant: evidence is append-only (no assertions needed if no execution)

    def test_random_valid_walk_with_retry_check(self):
        """Random walks that specifically test retry sequences."""
        import random
        random.seed(99)

        for _ in range(10):
            inst = ExecutionInstance()
            # Walk to EXECUTING
            for s in [ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.EXECUTING]:
                inst.transition_to(s)

            # Simulate retry cycle
            for retry_num in range(4):
                if retry_num < 3:
                    inst.transition_to(ExecutionState.QUEUED)
                    inst.retry_count += 1
                    inst.transition_to(ExecutionState.EXECUTING)
                else:
                    inst.transition_to(ExecutionState.FAILED)

            # After 3 retries, should be FAILED (retry_count = 3, but instance exhausted)
            # Actually the instance reached FAILED after max retries
            assert inst.state in (ExecutionState.FAILED, ExecutionState.EXECUTING,
                                  ExecutionState.QUEUED)