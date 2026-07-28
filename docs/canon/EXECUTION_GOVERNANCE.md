# Execution Governance

> **Canonical Document · Phase FA**
> **Status: CANONICAL — Execution Governance Specification**
> **Version: 1.0**

---

## 1. Purpose

The Execution Runtime is the single authoritative layer for all real-world work in SHUNYA. This document defines the governance framework that ensures every execution capability — present and future — inherits the same correctness guarantees.

No future modification to the execution runtime may weaken these guarantees.

---

## 2. Governance Principles

| Principle | Statement | Enforcement |
|-----------|-----------|-------------|
| **State Correctness** | No execution instance may enter a state not permitted by the formal state machine | Runtime validates every transition against `VALID_EXECUTION_TRANSITIONS` |
| **Transition Safety** | Every transition preconditions are checked before execution | `transition_to()` enforces preconditions via allow-list |
| **Invariant Persistence** | All structural invariants hold for the lifetime of every instance | Property-based tests verify invariants under random transitions |
| **Evidence Integrity** | Execution evidence is append-only and immutable | `EvidenceRecord.immutable = True` is a class invariant |
| **Policy Isolation** | Execution policies are never hardcoded in action handlers | `ExecutionPolicies` is injected at runtime creation |
| **Plugin Guarantee** | Future actions inherit all runtime guarantees without modification | `register_action()` is the only API surface for new capabilities |
| **Deterministic Core** | The runtime's state machine is deterministic absent action handler or external signal | Validated by property-based testing |

---

## 3. Invariant Test Suite

### 3.1 Required Test Categories

Every commit affecting the execution runtime must pass:

| Category | Tests | Enforces |
|----------|-------|----------|
| Structural | Every state has transitions | SI-1, SI-2, SI-3, SI-4, SI-6 |
| Reachability | Every state reachable from CREATED | SI-5 |
| Transition validation | Invalid transitions raise ValueError | Safety |
| Retry invariants | monotonic count, max_retries bound | TI-1, TI-2 |
| Cancellation idempotency | Double cancel is safe | TI implicit |
| Evidence immutability | Records cannot be modified after creation | TI-5 |
| Completion finality | Outputs present, confidence in [0,1] | TI-7, TI-8 |
| Timing ordering | created ≤ started ≤ completed | TI-10 |
| Graph acyclicity | Cycles are detected | GI-1 |
| Graph consistency | All dependencies exist | GI-2 |
| Property-based | Random valid/invalid transition sequences | Safety + Liveness |

### 3.2 Property-Based Test Design

Property-based tests verify that:

1. **Every valid transition in the table is executable** — given an instance in state S, and a target state T in `VALID_EXECUTION_TRANSITIONS[S]`, calling `transition_to(T)` succeeds.

2. **No invalid transition is executable** — given an instance in state S, and a target state T not in `VALID_EXECUTION_TRANSITIONS[S]`, calling `transition_to(T)` raises `ValueError`.

3. **All states are reachable** — there exists a sequence of valid transitions from CREATED to every state.

4. **No terminal state has outgoing transitions** — for every terminal state T, `VALID_EXECUTION_TRANSITIONS[T]` is empty.

5. **Retry count is monotonic** — during retry sequences, `retry_count` never decreases.

6. **Evidence is append-only** — `instance.evidence` length increases monotonically and previously appended entries do not change.

---

## 4. Future Capability Guarantee

Any future action registered via `register_action()` inherits:

- The complete 12-state deterministic lifecycle
- All transition safety checks
- Retry with exponential backoff
- Rollback and compensation support
- Immutable evidence recording
- Full observability (trace, timing, critical path)
- Dependency graph integration (cycle detection, fan-out, fan-in)
- Cancellation at any point
- Expiration for waiting instances
- All policy controls (retry, timeout, concurrency, rate limit, permissions, rollback)

**No runtime code changes are required.** The action developer implements only the handler function and an `ActionContract`.

---

## 5. Change Governance

### 5.1 Allowed Changes

- Adding new states (must include entry in `VALID_EXECUTION_TRANSITIONS`)
- Adding new transitions from existing states (must not violate invariants)
- Adding new policy types
- Adding new evidence event types
- Performance optimisations (must not change state semantics)

### 5.2 Disallowed Changes

- Removing an existing state
- Removing an existing transition
- Making a previously invalid transition valid
- Weakening retry invariants (e.g., allowing unbounded retries)
- Making evidence mutable
- Removing terminal state enforcement

### 5.3 Change Protocol

1. Update `VALID_EXECUTION_TRANSITIONS` in `core/execution_runtime/models.py`
2. Update `EXECUTION_STATE_SEMANTICS.md` transition table
3. Update all invariant tests to cover new/removed transitions
4. Run property-based tests across all valid/invalid transition combinations
5. Run full regression suite
6. All three phases (D, E, F, FA) must remain satisfied

---

## 6. Enforcement Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    EXECUTION GOVERNANCE                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Static Enforcement (compile-time)              │  │
│  │  • Type checking (MyPy)                                    │  │
│  │  • Linting (Ruff)                                          │  │
│  │  • Transition table completeness check                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Dynamic Enforcement (runtime)                  │  │
│  │  • transition_to() validates against allow-list            │  │
│  │  • retry policy checked before retry                       │  │
│  │  • timeout policy checked during execution                  │  │
│  │  • concurrency policy checked before dispatch              │  │
│  │  • rollback policy checked before compensation             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Property-Based Enforcement (test-time)         │  │
│  │  • All valid transitions are executable                    │  │
│  │  • No invalid transition is executable                     │  │
│  │  • All states reachable from CREATED                        │  │
│  │  • Terminal states are truly terminal                       │  │
│  │  • Retry/rollback invariant sequences                       │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Invariant Assertion Matrix

| Transition | Valid Targets | Must Raise | Invariants Checked |
|-----------|---------------|------------|-------------------|
| CREATED | READY, CANCELLED | COMPLETED, FAILED, EXECUTING, QUEUED, BLOCKED, WAITING, PARTIALLY_COMPLETED, ROLLED_BACK, EXPIRED | SI-5 |
| READY | QUEUED, BLOCKED, CANCELLED | CREATED, COMPLETED, FAILED, EXECUTING, WAITING, PARTIALLY_COMPLETED, ROLLED_BACK, EXPIRED | TI implicit |
| QUEUED | EXECUTING, CANCELLED, FAILED | CREATED, READY, COMPLETED, BLOCKED, WAITING, PARTIALLY_COMPLETED, ROLLED_BACK, EXPIRED | PI-2 (concurrency) |
| EXECUTING | COMPLETED, FAILED, BLOCKED, CANCELLED, QUEUED | CREATED, READY, WAITING, PARTIALLY_COMPLETED, ROLLED_BACK, EXPIRED | TI-1, TI-2 (retry only) |
| BLOCKED | WAITING, CANCELLED, FAILED, READY | CREATED, COMPLETED, EXECUTING, QUEUED, PARTIALLY_COMPLETED, ROLLED_BACK, EXPIRED | GI-3 |
| WAITING | READY, CANCELLED, EXPIRED | CREATED, COMPLETED, FAILED, EXECUTING, QUEUED, BLOCKED, PARTIALLY_COMPLETED, ROLLED_BACK | TI-10 (timing) |
| PARTIALLY_COMPLETED | COMPLETED, FAILED, CANCELLED, ROLLED_BACK | CREATED, READY, EXECUTING, QUEUED, BLOCKED, WAITING, EXPIRED | GI-4 |
| COMPLETED | (none) | All | TI-7, TI-8, TI-10 |
| FAILED | ROLLED_BACK | All except ROLLED_BACK | TI-9, TI-5 |
| CANCELLED | (none) | All | TI implicit |
| ROLLED_BACK | COMPLETED | All except COMPLETED | TI-5 |
| EXPIRED | (none) | All | TI implicit |

---

## 8. Test Coverage Requirements

| Requirement | Minimum | Current |
|------------|---------|---------|
| Structural transition tests | 100% of states | 12/12 |
| Invalid transition tests | Each invalid pair | 132/144 |
| Retry invariant tests | 3 sequences | 3 |
| Cancellation idempotency | 2 sequences | 2 |
| Evidence immutability | 3 assertions | 3 |
| Timing ordering | 3 assertions | 3 |
| Graph consistency | 5 assertions | 5 |
| Property-based random sequences | 200 transitions | 200 |
| Reachability proof | All 12 states | 12 |

---

*End of Execution Governance*