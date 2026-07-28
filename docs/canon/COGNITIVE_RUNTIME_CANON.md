# Cognitive Runtime Canon

> **Canonical Document · Phase E**
> **Status: CANONICAL — Implementation Specification**
> **Version: 1.0**

---

## 1. Purpose

Phase D implemented intelligence — eight specialised engines that each perform a cognitive function. Phase E implements **cognition** — the unified runtime through which every cognitive workflow executes.

The Cognitive Runtime is the canonical execution layer for all intelligent behaviour in SHUNYA. No future business capability may invoke intelligence engines directly. All execution passes through the Cognitive Runtime.

The runtime governs execution. The engines perform cognition.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     COGNITIVE RUNTIME                              │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    CognitiveSession                          │  │
│  │  session_id, trace_id, actor, event, objective, context,   │  │
│  │  confidence_history, reasoning_history, decisions, timing,  │  │
│  │  cancellation_state, escalation_state, completion_state     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Runtime Pipeline                          │  │
│  │                                                              │  │
│  │  RECEIVED → PERCEIVING → ASSEMBLING → REASONING → PLANNING  │  │
│  │  → DECIDING → REFLECTING → LEARNING → CONFIDENCE_UPDATE →   │  │
│  │  COMPLETED                                                   │  │
│  │                                                              │  │
│  │  ↓ FAILED ↓ CANCELLED ↓ ESCALATED ↓ PARTIAL                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Engine Orchestrator                        │  │
│  │  invokes engines, enforces ordering, parallelises safe      │  │
│  │  work, serializes dependent work, propagates confidence,    │  │
│  │  collects outputs, merges context, detects failures         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │
│  │ Policies │ │Escalation│ │  Events  │ │ Observability     │  │
│  │ retry    │ │ tracking │ │ canonical│ │ timelines, traces, │  │
│  │ timeout  │ │ auth     │ │ runtime  │ │ durations, memory  │  │
│  │ parallel │ │ cost     │ │ events   │ │                   │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Plugin Architecture                        │  │
│  │  register, capability declare, dependency declare,          │  │
│  │  confidence contribution, execution stage                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Cancellation & Recovery                        │  │
│  │  graceful cancellation, safe retries, partial completion,  │  │
│  │  resume, rollback, consistency enforcement                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Performance Instrumentation                    │  │
│  │  engine latency, pipeline latency, queue time, parallel    │  │
│  │  efficiency, escalation latency, memory usage              │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     INTELLIGENCE ENGINES (Phase D)                 │
│  Perception │ Context Assembly │ Reasoning │ Planning │ Decision  │
│  Reflection │ Learning │ Confidence                               │
└──────────────────────────────────────────────────────────────────┘
```

### 2.1 Runtime vs Engines Separation

| Responsibility | Cognitive Runtime (Phase E) | Intelligence Engine (Phase D) |
|---------------|----------------------------|-------------------------------|
| Session lifecycle | ✓ Ownership | — |
| Pipeline orchestration | ✓ Enforces | — |
| Engine invocation | ✓ Calls | — |
| Confidence propagation | ✓ Combines across engines | ✓ Produces per-engine score |
| Escalation authorization | ✓ Decides | ✓ Recommends |
| Policy enforcement | ✓ Centralized | — |
| Event emission | ✓ Runtime events | — |
| Tracing & observability | ✓ Session timeline | — |
| Cancellation & recovery | ✓ Owns | — |
| Performance measurement | ✓ Collects | — |
| Plugin registration | ✓ Manages | — |
| Cognitive work | — | ✓ Performs |
| Deterministic computation | — | ✓ Executes |
| Escalation prompt building | — | ✓ Generates |

### 2.2 Integration with Phase D

The Cognitive Runtime imports and invokes the 8 intelligence engines from `core/intelligence/`. It never bypasses them or reimplements their functionality. It also imports from `core/*` modules for event emission, identity, timeline, and evidence.

The runtime preserves the strangler-fig pattern — it does not import from `app/`.

---

## 3. CognitiveSession

### 3.1 Session Contract

```python
@dataclass
class CognitiveSession:
    session_id: str                    # Unique UUID7
    trace_id: str                      # Correlation ID
    actor: str                         # Initiating human/system identity
    triggering_event: str              # Event that started the session
    objective: str                     # What the session aims to achieve
    context: dict                      # Execution context (assembled at runtime)
    confidence_history: list           # Ordered confidence snapshots
    reasoning_history: list            # Ordered reasoning conclusions
    decisions: list                    # Decisions made during this session
    engine_results: dict               # Per-engine outputs keyed by engine_id
    timing: dict                       # {engine_id: {start, end, duration_ms}}
    state: SessionState                # Current lifecycle state
    cancellation: CancellationState    # Cancellation tracking
    escalation: EscalationState        # Escalation tracking
    completion: CompletionState        # Completion/outcome tracking
    errors: list                       # Errors encountered
    warnings: list                     # Warnings generated
    created_at: str                    # ISO timestamp
    updated_at: str                    # ISO timestamp
```

### 3.2 Session State

| State | Description |
|-------|-------------|
| RUNNING | Session is actively executing |
| WAITING | Session is waiting (e.g., for escalation) |
| PAUSED | Session is paused by policy |
| ESCALATED | Session has escalated to AI |
| RETRYING | Session is retrying a failed step |
| CANCELLED | Session was cancelled |
| COMPLETED | Session finished successfully |
| FAILED | Session failed terminally |

### 3.3 Nothing Executes Outside a Session

Every cognitive workflow receives a CognitiveSession. The runtime rejects any engine invocation that is not tied to a valid session. This is the primary enforcement mechanism for the Phase E architecture.

---

## 4. Runtime Pipeline

### 4.1 Pipeline Stages

The canonical execution lifecycle:

```
RECEIVED
    │
    ▼
PERCEIVING ─────────────────────────► PerceptionEngine.process()
    │                                   input → observation
    ▼
ASSEMBLING_CONTEXT ───────────────────► ContextAssemblyEngine.process()
    │                                   observation → context
    ▼
REASONING ───────────────────────────► ReasoningEngine.process()
    │                                   context → conclusions
    ▼
PLANNING ────────────────────────────► PlanningEngine.process()
    │                                   conclusions → plan
    ▼
DECIDING ────────────────────────────► DecisionEngine.process()
    │                                   plan → decision
    ▼
REFLECTING ──────────────────────────► ReflectionEngine.process()
    │                                   decision → reflection
    ▼
LEARNING ────────────────────────────► LearningEngine.process()
    │                                   reflection → patterns
    ▼
CONFIDENCE_UPDATE ───────────────────► ConfidenceEngine.compute()
    │                                   aggregate confidence
    ▼
COMPLETED
```

### 4.2 Terminal States

| State | Trigger |
|-------|---------|
| FAILED | Engine error, policy violation, unrecoverable |
| CANCELLED | User/system cancellation request |
| COMPLETED | All stages processed successfully |
| ESCALATED | Session escalated (may return to RUNNING) |

### 4.3 Transition Rules

- All transitions are deterministic
- PROGRESS transitions (PERCEIVING → ASSEMBLING_CONTEXT → etc.) execute in order
- FAILED can be entered from any stage
- CANCELLED can be entered from any non-terminal stage
- ESCALATED can be entered from any stage where confidence < threshold
- From ESCALATED, session may return to the originating stage or proceed to FAILED

### 4.4 Stage Execution Model

Each pipeline stage:
1. Invokes the corresponding engine
2. Captures engine output
3. Propagates confidence to session
4. Emits runtime event
5. Records timing
6. Checks for errors / escalation / cancellation

---

## 5. Engine Orchestration

### 5.1 Orchestrator Responsibilities

- **Invoke engines** in pipeline order
- **Parallelize safe work** — stages with no data dependency can execute concurrently
- **Serialize dependent work** — stages that consume prior output execute sequentially
- **Propagate confidence** — each engine output's confidence is merged into session
- **Collect outputs** — all engine results stored in session
- **Merge context** — context is enriched as pipeline progresses
- **Detect failures** — engine errors are captured and propagated
- **Enforce retry policy** — configurable retry on transient failures

### 5.2 Engine Invocation Contract

```python
async def invoke_engine(
    session: CognitiveSession,
    engine: IntelligenceEngine,
    stage: PipelineStage,
) -> EngineOutput:
```

The orchestrator wraps every engine call with timing, event emission, error handling, and confidence propagation.

### 5.3 Safe Parallelization

Only the following stages are safe to parallelize:
- REFLECTING and LEARNING (no data dependency between them)

All other stages are strictly sequential due to data dependencies.

---

## 6. Runtime State Management

### 6.1 Session States

The session state machine:

```
RUNNING ◄─────────────┐
    │                  │
    ├──► WAITING ──────┘
    ├──► PAUSED ───────┘
    ├──► ESCALATED ────┘
    ├──► RETRYING ─────┘
    │
    ├──► COMPLETED (terminal)
    ├──► FAILED (terminal)
    └──► CANCELLED (terminal)
```

### 6.2 State Observability

Every state transition:
1. Timestamps the transition
2. Records the reason
3. Emits a state-change event
4. Updates the session's state history

---

## 7. Confidence Propagation

### 7.1 Per-Engine Confidence

Each engine produces an `EngineOutput` with its own `confidence` and `confidence_factors`. These are recorded individually in the session's `confidence_history`.

### 7.2 Accumulated Confidence

The runtime computes an accumulated confidence after each stage:

```
accumulated_confidence = weighted_average(
    all_engine_confidences_so_far,
    weights = engine_weights  # defined by plugin registration
)
```

### 7.3 Downstream Propagation

Every downstream engine receives `accumulated_confidence` in its `EngineInput.context`. This allows each engine to know the runtime's overall confidence level when making its own computations.

### 7.4 Final Confidence

The final accumulated confidence after CONFIDENCE_UPDATE becomes the session's execution confidence. This is stored in `CompletionState.final_confidence`.

---

## 8. AI Escalation Runtime

### 8.1 Responsibilities

The runtime alone decides when escalation occurs. Engines recommend escalation (via `EngineOutput.escalation_used` or confidence < threshold), but only the runtime authorizes it.

### 8.2 Escalation Flow

```
Engine returns confidence >= threshold → Continue pipeline
Engine returns confidence < threshold → Runtime records escalation request
                                          Runtime checks escalation policy
                                          Policy allows? → Runtime authorizes escalation
                                          Policy denies? → Session FAILED with reason
```

### 8.3 Escalation Tracking

Every escalation records:

| Field | Description |
|-------|-------------|
| reason | Why escalation was triggered |
| engine | Which engine recommended it |
| confidence_threshold | Threshold at time of escalation |
| provider | AI provider (future) |
| request | EscalationResult prompt |
| response | AI response (future) |
| cost | Monetary cost (future) |
| latency_ms | Escalation duration (future) |
| outcome | What happened |

### 8.4 Escalation becomes observable

Escalations are recorded in:
- CognitiveSession.escalation
- Runtime event `EscalationRequested`
- Session timeline

---

## 9. Runtime Observability

### 9.1 Per-Session Trace

Every session produces a deterministic trace containing:

| Section | Contents |
|---------|----------|
| Timeline | Ordered list of events with timestamps |
| Engine Durations | Per-engine start/end/duration |
| Confidence Evolution | Confidence after each stage |
| Reasoning Chain | Ordered conclusions from Reasoning Engine |
| Decision Chain | Ordered decisions from Decision Engine |
| Escalations | Every escalation event |
| Warnings | Non-fatal issues |
| Errors | Fatal errors |
| Resource Usage | Memory, time (measured, not optimized) |

### 9.2 Deterministic Traces

Identical inputs with no escalation produce identical traces. Escalation is the only source of non-determinism.

---

## 10. Cancellation & Recovery

### 10.1 Graceful Cancellation

A session can be cancelled at any non-terminal state. Cancellation:
1. Sets session state to CANCELLED
2. Records cancellation reason
3. Emits SessionFailed event (with cancelled status)
4. Does not rollback completed stages (they are immutable)
5. Prevents further stage execution

### 10.2 Safe Retries

On transient errors (timeout, network):
1. Check retry policy
2. If retries remaining → set state to RETRYING
3. Re-invoke the failed engine stage
4. On success → resume pipeline
5. On retry exhaustion → FAILED

### 10.3 Partial Completion

If some stages succeed before failure:
- Completed stage outputs are preserved
- Session records which stages completed and which failed
- A partial session can be resumed later with `resume()`

### 10.4 Consistency Guarantee

The runtime never leaves inconsistent execution state. If a stage fails:
- State is updated to FAILED
- All completed stages remain as-is (immutable)
- No partial output from the failed stage is stored

---

## 11. Performance Budget

### 11.1 Measurement Points

Every engine invocation is instrumented:

| Metric | Unit | Collected |
|--------|------|-----------|
| Engine latency | ms | Yes |
| Pipeline latency | ms | Yes |
| Queue time | ms | Yes |
| Parallel efficiency | ratio | Yes |
| Escalation latency | ms | Yes |
| Memory usage | bytes | Yes |
| Session duration | ms | Yes |

### 11.2 No Optimization

Phase E measures only. No optimization is performed. Performance data is recorded in the session trace and emitted as runtime events.

---

## 12. Runtime Events

### 12.1 Canonical Event Types

```python
@dataclass
class RuntimeEvent:
    event_type: str          # e.g. "SessionStarted"
    session_id: str
    trace_id: str
    timestamp: str
    payload: dict
```

### 12.2 Event Catalog

| Event Type | Trigger | Payload |
|-----------|---------|---------|
| SessionStarted | New session created | actor, objective |
| StageStarted | Engine invocation begins | stage, engine_id |
| StageCompleted | Engine returns output | stage, engine_id, confidence, duration_ms |
| ConfidenceUpdated | After each stage | accumulated_confidence, stage |
| EscalationRequested | Engine confidence < threshold | engine, threshold, current_confidence |
| EscalationApproved | Runtime authorizes escalation | escalation_id |
| EscalationCompleted | Escalation returns (future) | outcome, latency, cost |
| DecisionMade | Decision Engine produces decision | decision_id, label, confidence |
| SessionCompleted | All stages done | final_confidence, total_duration_ms |
| SessionFailed | Terminal error | error, stage |
| SessionCancelled | Cancellation | reason |

### 12.3 Event Foundation

These events are the foundation for future:
- Monitoring dashboards
- Audit trails
- Replay analysis
- Performance trending
- Alerting

---

## 13. Plugin Architecture

### 13.1 Engine Registration

New engines register with the runtime:

```python
@dataclass
class EnginePlugin:
    engine: IntelligenceEngine
    stage: PipelineStage          # Which pipeline stage this engine serves
    capabilities: list[str]       # Declared capabilities
    dependencies: list[str]       # Engine IDs this engine depends on
    confidence_weight: float      # Weight for accumulated confidence
    parallel_safe: bool           # Can run in parallel with other stages?
```

### 13.2 Registration Process

```python
runtime.register_engine(engine, stage="perceiving",
                        capabilities=["input_validation"],
                        dependencies=[],
                        confidence_weight=0.15,
                        parallel_safe=False)
```

### 13.3 No Redesign Required

Adding a new engine requires:
1. Implement the IntelligenceEngine interface
2. Register it with the runtime via `register_engine()`
3. Declare its stage, dependencies, and confidence weight

No runtime core changes are needed.

---

## 14. Runtime Policies

### 14.1 Centralized Policy Store

```python
@dataclass
class RuntimePolicies:
    retry_policy: RetryPolicy
    timeout_policy: TimeoutPolicy
    escalation_policy: EscalationPolicy
    parallel_policy: ParallelPolicy
    confidence_policy: ConfidencePolicy
    failure_policy: FailurePolicy
```

### 14.2 Policy Catalog

| Policy | Controls | Default |
|--------|----------|---------|
| RetryPolicy | max_retries, backoff_ms, retryable_errors | 3 retries, 100ms backoff |
| TimeoutPolicy | engine_timeout_ms, pipeline_timeout_ms | 30s engine, 300s pipeline |
| EscalationPolicy | allow_escalation, max_escalations_per_session | True, 5 |
| ParallelPolicy | max_parallel_stages | 2 |
| ConfidencePolicy | minimum_acceptable_confidence | 0.3 |
| FailurePolicy | fail_fast (stop on first error) | True |

### 14.3 No Hardcoded Policies

All policies are configurable at runtime creation time. No policy is hardcoded inside any intelligence engine.

---

## 15. Deterministic Guarantees

### 15.1 Guarantees

1. **Identical inputs produce identical deterministic execution** (unless AI escalation occurs)
2. **Every transition is traceable** — session state history records all state changes
3. **Every decision has evidence** — decisions link to reasoning conclusions and observations
4. **Every escalation has justification** — escalation records the reason, engine, and threshold
5. **Every completion has an execution record** — session contains full trace

### 15.2 Enforcement

| Guarantee | Enforcement Mechanism |
|-----------|---------------------|
| Deterministic execution | Pipeline stages are deterministic when engines don't escalate |
| Traceable transitions | State history is append-only in CognitiveSession |
| Evidence-linked decisions | session.reasoning_history and session.decisions are ordered lists |
| Justified escalation | escalation.reason, escalation.engine recorded |
| Execution record | session persists all state |

---

## 16. Future Extensibility

- Additional pipeline stages can be inserted by registering new engines
- Custom event handlers can subscribe to runtime events
- Custom policies can be injected at session creation
- Observability can be extended by adding trace collectors
- AI providers can be integrated via the escalation runtime's provider interface

---

*End of Cognitive Runtime Canon*