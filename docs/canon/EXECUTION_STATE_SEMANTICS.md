# Execution State Semantics

> **Canonical Document · Phase FA**
> **Status: CANONICAL — Execution State Specification**
> **Version: 1.0**

---

## 1. Purpose

Every execution instance in SHUNYA passes through a formal 12-state lifecycle. This document defines the precise semantics of every state, every transition, and every invariant that governs state changes. These semantics are the permanent contract between the Execution Runtime and every action executed within it.

---

## 2. State Definitions

### 2.1 State Catalog

| State | Symbol | Meaning | Correctness Invariant |
|-------|--------|---------|----------------------|
| CREATED | C | Instance exists but is not ready to run | No side effects have occurred. All metadata is mutable. |
| READY | R | Dependencies satisfied, awaiting scheduling | All preconditions validated. No side effects. |
| QUEUED | Q | Scheduled, waiting for execution slot | Concurrency policy applies. Not yet running. |
| EXECUTING | E | Action handler is executing | Handler may produce side effects. No other handler runs for this instance. |
| WAITING | W | Waiting for external signal | No progress possible until signal arrives. No timeout is running. |
| BLOCKED | B | Blocked by unsatisfied dependency or resource | Dependencies list is non-empty. At least one dependency is not COMPLETED. |
| PARTIALLY_COMPLETED | P | Some sub-executions succeeded, others pending | At least one child is COMPLETED and at least one is not. |
| COMPLETED | T | Terminally succeeded | All postconditions satisfied. Outputs are final. Evidence is immutable. |
| FAILED | F | Terminally failed | All preconditions or postconditions violated. May transition to ROLLED_BACK. |
| CANCELLED | X | Cancelled before or during execution | No further execution occurs. Side effects may have occurred. |
| ROLLED_BACK | Z | Execution reversed | All side effects compensated. May transition to COMPLETED after full compensation. |
| EXPIRED | D | Timed out while waiting | No further waiting occurs. Considered terminal. |

### 2.2 Classification

| Category | States |
|----------|--------|
| Pre-execution | CREATED, READY, QUEUED |
| Active | EXECUTING, WAITING, BLOCKED |
| Post-execution | PARTIALLY_COMPLETED, COMPLETED, FAILED, CANCELLED, ROLLED_BACK, EXPIRED |
| Terminal (no outgoing transitions) | COMPLETED, CANCELLED, EXPIRED |
| Compensation-capable | FAILED (→ ROLLED_BACK), ROLLED_BACK (→ COMPLETED) |

---

## 3. Transition Semantics

### 3.1 Formal Transition Table

Each transition T(s₁ → s₂) has preconditions P and postconditions Q.

```
T(C → R)    — ACTIVATE
  P: instance created, dependencies satisfied
  Q: instance is ready for scheduling

T(C → X)    — EARLY_CANCEL
  P: instance not yet started
  Q: instance cancelled with no side effects

T(R → Q)    — ENQUEUE
  P: scheduler has capacity
  Q: instance in scheduling queue

T(R → B)    — BLOCK
  P: at least one dependency not satisfied
  Q: instance blocked, not consuming resources

T(R → X)    — CANCEL_READY
  P: instance not yet executing
  Q: instance cancelled

T(Q → E)    — DISPATCH
  P: concurrency slot available
  Q: action handler invoked

T(Q → X)    — CANCEL_QUEUED
  P: instance not yet executing
  Q: instance cancelled

T(Q → F)    — QUEUE_FAILED
  P: scheduling infrastructure error
  Q: instance never executed

T(E → T)    — COMPLETE
  P: action handler returned successfully
  Q: outputs stored, postconditions satisfied, evidence recorded

T(E → F)    — FAIL
  P: action handler raised or returned error
  Q: error recorded. May be retried or rolled back.

T(E → B)    — BLOCK_DURING
  P: handler encountered blocking condition
  Q: instance blocked mid-execution

T(E → Q)    — RETRY
  P: retry policy permits, retry count not exhausted
  Q: instance re-queued with incremented retry_count

T(E → X)    — CANCEL_EXECUTING
  P: cancellation requested during execution
  Q: handler may or may not have produced side effects

T(B → W)    — WAIT
  P: blocking dependency identified
  Q: instance waiting for external signal

T(B → X)    — CANCEL_BLOCKED
  P: cancellation requested while blocked
  Q: instance cancelled

T(B → F)    — BLOCK_FAILED
  P: blocking dependency failed terminally
  Q: instance failed

T(B → R)    — UNBLOCK
  P: all dependencies satisfied
  Q: instance ready to schedule

T(W → R)    — RESUME
  P: external signal received
  Q: instance ready to schedule

T(W → X)    — CANCEL_WAITING
  P: cancellation requested while waiting
  Q: instance cancelled

T(W → D)    — EXPIRE
  P: timeout elapsed without signal
  Q: instance expired, no further execution

T(P → T)    — PARTIAL_COMPLETE
  P: all sub-executions now completed
  Q: parent completes

T(P → F)    — PARTIAL_FAIL
  P: sub-execution failed terminally
  Q: parent fails

T(P → X)    — PARTIAL_CANCEL
  P: cancellation while partially completed
  Q: parent cancelled

T(P → Z)    — PARTIAL_ROLLBACK
  P: rollback triggered while partially completed
  Q: parent rolled back

T(F → Z)    — COMPENSATE
  P: rollback policy enabled, rollback handler exists
  Q: rollback handler invoked, compensation evidence recorded

T(Z → T)    — COMPENSATION_COMPLETE
  P: compensation fully succeeded
  Q: instance marked complete with compensation note

T(Z → D)    — COMPENSATION_EXPIRED (defined for completeness)
  P: rollback timed out
  Q: instance expired

T(Z → D)    — COMPENSATION_EXPIRED (defined for completeness, currently unused)
```

### 3.2 Transition Categories

#### 3.2.1 Retry Transitions

A retry is the transition EXECUTING → QUEUED.

**Invariants:**
- `retry_count` is incremented exactly once per retry transition
- `max_retries` is checked before retry: `retry_count ≤ max_retries`
- Backoff delay is applied before re-queuing
- Evidence records `execution_failed` before retry
- The instance's outputs from the failed attempt are discarded
- Inputs remain unchanged across retries

**Maximum retry count:** after `max_retries` retries, the next failure transitions to FAILED.

#### 3.2.2 Rollback Transitions

A rollback is the transition FAILED → ROLLED_BACK (or PARTIALLY_COMPLETED → ROLLED_BACK).

**Invariants:**
- Rollback handler is invoked if one exists
- Rollback is recursive: all dependents are rolled back
- Rollback evidence is recorded before handler invocation
- A rollback failure does not prevent the instance from being ROLLED_BACK
- ROLLED_BACK may transition to COMPLETED if compensation succeeds

#### 3.2.3 Compensation Transitions

Compensation is the transition ROLLED_BACK → COMPLETED.

**Invariants:**
- Compensation only occurs after a rollback
- Compensation evidence is recorded
- Final state is COMPLETED with a compensation note in evidence

#### 3.2.4 Cancellation Transitions

Cancellation transitions originate from any non-terminal state and converge on CANCELLED.

**Invariants:**
- Cancellation is idempotent — calling cancel twice has no effect
- Cancellation records the reason
- Cancellation evidence is immutable
- No further execution occurs after cancellation
- Side effects that occurred before cancellation are preserved in evidence

#### 3.2.5 Expiration Transitions

Expiration is the transition WAITING → EXPIRED.

**Invariants:**
- Expiration only applies to WAITING instances
- Expiration records the timeout duration
- EXPIRED is terminal — no further transitions

#### 3.2.6 Completion Transitions

Completion is the transition EXECUTING → COMPLETED (or PARTIALLY_COMPLETED → COMPLETED, or ROLLED_BACK → COMPLETED).

**Invariants:**
- All outputs are stored and final
- All postconditions are satisfied
- Completion evidence is recorded
- Duration is recorded in timing
- Confidence is set to 1.0 for deterministic success
- COMPLETED is terminal — no outgoing transitions

---

## 4. State Machine Properties

### 4.1 Reachability

Every state is reachable from CREATED through a valid sequence of transitions.

Proof sketch:
```
CREATED → READY → QUEUED → EXECUTING → COMPLETED                                          (happy path)
CREATED → READY → QUEUED → EXECUTING → FAILED → ROLLED_BACK → COMPLETED                  (compensation)
CREATED → READY → QUEUED → EXECUTING → FAILED → ROLLED_BACK                              (uncompensated)
CREATED → READY → QUEUED → EXECUTING → BLOCKED → WAITING → READY → ...                   (block/resume)
CREATED → READY → QUEUED → EXECUTING → BLOCKED → WAITING → EXPIRED                       (timeout)
CREATED → READY → QUEUED → EXECUTING → QUEUED → EXECUTING → COMPLETED                    (retry)
CREATED → READY → BLOCKED → CANCELLED                                                     (cancel blocked)
CREATED → CANCELLED                                                                        (early cancel)
CREATED → READY → QUEUED → EXECUTING → BLOCKED → WAITING → READY → QUEUED → EXECUTING → COMPLETED  (resume)
```

### 4.2 Determinism

All transitions are deterministic given the same preconditions. The only non-determinism comes from:
- Action handler results (business logic)
- External signals (WAITING → READY)

### 4.3 Terminality

A state is terminal if it has no outgoing transitions in `VALID_EXECUTION_TRANSITIONS`. The terminal states are:

- COMPLETED — no transitions out
- CANCELLED — no transitions out
- EXPIRED — no transitions out

FAILED and ROLLED_BACK are NOT terminal because they support compensation.

---

## 5. Invariant Definitions

### 5.1 Structural Invariants

| ID | Invariant | Enforced By |
|----|-----------|-------------|
| SI-1 | Every state has a defined entry in `VALID_EXECUTION_TRANSITIONS` | Static assertion in test |
| SI-2 | Every transition target in `VALID_EXECUTION_TRANSITIONS` is a valid `ExecutionState` enum value | Type system + test |
| SI-3 | Terminal states have empty transition lists | Static assertion |
| SI-4 | No self-loops (s → s) exist | Static assertion |
| SI-5 | CREATED is the unique initial state | Runtime enforces on creation |
| SI-6 | Every non-terminal state has at least one outgoing transition | Static assertion |

### 5.2 Transition Invariants

| ID | Invariant | Pre/Post |
|----|-----------|----------|
| TI-1 | `retry_count` is monotonic (never decreases) | Post: retry |
| TI-2 | `retry_count ≤ max_retries` for retry transitions | Pre: retry |
| TI-3 | `execution_id` is immutable after creation | Always |
| TI-4 | `root_execution_id` is immutable after creation | Always |
| TI-5 | `evidence` is append-only (never mutated) | Always |
| TI-6 | `history` is append-only (never mutated) | Always |
| TI-7 | On COMPLETED, `outputs` is non-None | Post: complete |
| TI-8 | On COMPLETED, `confidence` in [0, 1] | Post: complete |
| TI-9 | On FAILED, `retry_count` is the number of attempts made | Post: fail |
| TI-10 | `timing.created_at` ≤ `timing.started_at` ≤ `timing.completed_at` | Post: complete |

### 5.3 Graph Invariants

| ID | Invariant | Enforced By |
|----|-----------|-------------|
| GI-1 | The dependency graph is acyclic | `ExecutionGraph.has_cycle()` |
| GI-2 | All dependency targets exist as instance IDs | `validate_graph()` |
| GI-3 | A BLOCKED instance has at least one unsatisfied dependency | Pre: BLOCKED |
| GI-4 | Completing an instance checks all dependents | `_check_dependents()` |

### 5.4 Policy Invariants

| ID | Invariant | Enforced By |
|----|-----------|-------------|
| PI-1 | `retry.max_retries ≥ 0` | Type: dataclass default |
| PI-2 | `retry.backoff_ms ≥ 0` | Type: dataclass default |
| PI-3 | `timeout.default_timeout_ms > 0` | Type: dataclass default |
| PI-4 | `rollback.auto_rollback_on_failure` is checked before rollback | Runtime |

---

## 6. Formal Proof Elements

### 6.1 Safety

No instance can reach an invalid state from any valid state via the defined transitions.

Proof: every transition is validated against `VALID_EXECUTION_TRANSITIONS` before execution. If a target state is not in the allowed list, a `ValueError` is raised and the instance remains in its current state.

### 6.2 Liveness

Every instance eventually reaches a terminal state or is making progress toward one.

Proof sketch: retry count bounds failures, timeouts bound waiting, and the action handler is bounded by timeout policy. The only infinite loop possible is retry → EXECUTING → FAIL → retry → ... which is bounded by `max_retries`.

### 6.3 Non-Terminal Termination

FAILED and ROLLED_BACK are not terminal. An instance in FAILED may be rolled back. An instance in ROLLED_BACK may be compensated to completion. These states serve as intermediate checkpoints for recovery.

---

*End of Execution State Semantics*