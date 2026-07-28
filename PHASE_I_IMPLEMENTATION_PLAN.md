# PHASE_I_IMPLEMENTATION_PLAN.md

**Governance Directive:** G8.0 — Phase I Authorization
**Engine:** Executor Engine (ES-005)
**Layer:** Executor

---

## Phase I Objectives

1. Implement canonical Executor Engine data models (ES-005 §2–3)
2. Implement 9-stage deterministic execution pipeline (ES-005 §4)
3. Implement workflow model with task lifecycle, dependencies, retries, compensations, checkpoints
4. Implement channel adapter registry leveraging existing adapters
5. Implement evidence collection and outcome packaging for Observer Engine
6. Implement backward-compatible legacy wrapper
7. Write comprehensive test suite
8. Zero regressions on all prior phases

## Scope Boundaries

| In Scope | Out of Scope |
|----------|-------------|
| Workflow task model (pending→in_progress→completed/failed/skipped/cancelled) | Credential store integration (credential store not implemented yet) |
| Retry policy (max_attempts, backoff, timeout) | Event Bus integration (not available) |
| Compensation action model (defined, not wired to real adapters) | Observer Engine handoff (Observer not implemented yet) |
| Checkpoint model (defined, not wired to durable store) | Channel adapter modifications (reuse existing) |
| Task dependency verification (acyclic check) | Knowledge Engine write for evidence (Knowledge Engine not integrated) |
| Execution evidence collection model | Real external API calls beyond existing adapters |
| Outcome package model | Distributed execution, batch, streaming modes |
| 8 execution types: synchronous, asynchronous, human-assisted, long-running, scheduled, event-driven, transactional | Scheduled/event-driven triggers (cron integration deferred) |
| Determinism verification | Performance/latency benchmarking |
| Tenant isolation | |

## Dependency Analysis

| Dependency | Status | Impact |
|------------|--------|--------|
| Phase H (Governance Engine) | ✅ Complete | ExecutorInput consumes GovernanceVerdict (approved) |
| Phase G (Planner Engine) | ✅ Complete | ExecutionPlan model available from planner.models |
| Phase F (Reasoning Engine) | ✅ Complete | ReasoningResult available for provenance |
| `app/shunya/executor.py` | ✅ Existing (412 lines) | Legacy adapters reused; canonical package wraps them |

**No dependency on deferred ReasoningSession** — confirmed by Phase F and Phase G closures.

## Public Interfaces Consumed

### From Phase H (Governance Engine — GovernanceVerdict)

```python
verdict.decision        # VerdictDecision.APPROVE / REVIEW / REJECT
verdict.approved        # bool
verdict.audit_id        # str — governance audit reference
verdict.explanation     # str
```

### From Phase G (Planner Engine — ExecutionPlan)

```python
plan.plan_id            # str
plan.tasks              # List[PlanTask]
plan.dependencies       # List[Dependency]
plan.objectives         # List[Objective]
plan.total_duration_hours
plan.total_estimated_cost
```

### From existing executor.py

```python
ChannelAdapter.send(message) -> DeliveryResult
ChannelAdapter.parse_inbound(raw) -> InboundMessage
ChannelAdapter.channel_type -> ChannelType
OutboundMessage, InboundMessage, DeliveryResult, ChannelType
```

## Public Interfaces Exposed

```python
from app.shunya.executor_engine import (
    # Enums
    WorkflowState, TaskState, ExecutionType, BackoffStrategy, FailureType,

    # Models
    ExecutorInput, ExecutorOutput,
    Workflow, Task, RetryPolicy, Compensation,
    ExecutionEvidence, ExecutionFailure, OutcomePackage,
    Checkpoint, ExecutionMetrics,

    # Engine
    ExecutorEngine, get_executor_engine, reset_executor_engine,

    # Legacy
    ExecutorLayer,
)
```

## Migration Requirements

**None.** The existing `app/shunya/executor.py` is preserved untouched. The new canonical engine is a separate package. The legacy `ExecutorLayer` is re-exported from the new package for callers who want a unified import path.

## Compatibility Considerations

- `ExecutorLayer.send()` continues to work unchanged — the legacy file is preserved
- New code imports from `app/shunya.executor_engine`
- All channel adapters (WhatsAppAdapter, TelegramAdapter, EmailAdapter) remain usable
- `ExecutorLayer` can optionally wrap the canonical `ExecutorEngine` (or stay standalone)

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Credential store not available | Certain | Medium | Credentials referenced by ID, resolved at task time via interface |
| Observer Engine not implemented | Certain | Low | OutcomePackage is produced and stored; delivery deferred |
| Event Bus not available | Certain | Low | Events are structured and stored in outcome; delivery deferred |
| Channel adapters require network calls | High | Medium | Tests use mock adapters; real adapters have graceful fallback |

## Expected Testing Strategy

1. **Model tests** (15–20): Data model construction, serialization, defaults
2. **Engine pipeline tests** (20–25): 9-stage pipeline, validation, determinism
3. **Workflow tests** (5–10): lifecycle states, task transitions, dependency enforcement
4. **Retry policy tests** (5): max attempts, backoff calculation, timeout enforcement
5. **Evidence collection tests** (5): evidence capture, evidence query
6. **Outcome packaging tests** (3): outcome structure, metrics aggregation
7. **Concurrency tests** (2): thread safety, concurrent workflows
8. **Legacy backward compatibility tests** (3): import, basic API
9. **Determinism tests** (2): identical inputs produce identical outputs

---

**Plan approved. Implementation ready to begin.**