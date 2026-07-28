# INTELLIGENCE CORE ROADMAP

**Epic Range:** E-004 → E-008
**Pipeline:** Evidence → Reasoning → Planning → Execution → Learning
**Status:** Architecture Specification — Pre-Implementation
**Classification:** Canonical Architecture Document

---

## Table of Contents

1. [Architectural Overview](#1-architectural-overview)
2. [E-004: Evidence](#2-e-004-evidence)
3. [E-005: Reasoning](#3-e-005-reasoning)
4. [E-006: Planning](#4-e-006-planning)
5. [E-007: Execution](#5-e-007-execution)
6. [E-008: Learning](#6-e-008-learning)
7. [Pipeline Dynamics](#7-pipeline-dynamics)
8. [Constitutional Invariants](#8-constitutional-invariants)
9. [Cross-Cutting Concerns](#9-cross-cutting-concerns)
10. [Appendices](#10-appendices)

---

## 1. Architectural Overview

### 1.1 The Intelligence Pipeline

The Intelligence Core is a five-stage sequential pipeline that transforms raw stimuli into autonomous action and, through reflection, into durable capability growth. Each stage is a distinct Epic with a well-defined contract, public API, and isolation boundary.

```
  E-004         E-005         E-006         E-007         E-008
  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
  │EVIDENCE│──>│REASONING│──>│PLANNING│──>│EXECUTION│──>│LEARNING│
  │        │   │        │   │        │   │        │   │        │
  │  Raw   │   │Beliefs │   │  Goals │   │ Actions│   │Insights│
  │ Signals│   │  Facts │   │Routes  │   │Effects │   │ Models │
  └────────┘   └────────┘   └────────┘   └────────┘   └────────┘
```

### 1.2 Pipeline Contract

Every Stage complies with:

| Property | Specification |
|---|---|
| **Input** | Precisely typed record from previous stage (or sensing layer) |
| **Output** | Precisely typed record consumed by next stage (or actuation / memory) |
| **Side Effects** | Zero — stages are pure transforms. Side effects happen only in Execution |
| **Failure Model** | Partial, recoverable, or terminal — each stage declares which |
| **Temporal Model** | Each tick is a single pass through the pipeline; stages may operate at different cadences |

### 1.3 Relationship to Previous Epics

| Preceding Epic | Relationship |
|---|---|
| **GENESIS I-III** (Kernel, Space, Relationship Engine) | Intelligence Core consumes the Space and Relationship primitives provided by GENESIS. Evidence attaches to objects in Space; Reasoning operates over Relationships. The Kernel provides scheduling and resource accounting. |
| **Milestone X** (Identity/Auth/Authorization) | Identity provides the agent persona under which the pipeline runs. Authorization gates Execution actions. |
| **SMS Volumes I.5 + II** | The Sensory-Motor System provides the raw ingress (E-004 inputs) and egress (E-007 outputs) channels. Intelligence Core is the cognitive loop between sense and act. |

---

## 2. E-004: Evidence

### 2.1 Purpose

Transform raw sensory data (signals, messages, state deltas, environmental readings) into structured **Evidence Records** — timestamped, source-attributed, confidence-weighted facts that the reasoning stage can operate on.

Evidence is the bridge between the world and the mind. It is not truth — it is the best current estimate.

### 2.2 Inputs

| Source | Type | Description |
|---|---|---|
| Sensory-Motor ingress channels | `Signal` | Raw bytes, frames, events from the environment |
| Internal state snapshots | `StateDelta` | Changes in kernel, space, or relationship state |
| External API responses | `Message` | Structured replies from external services |
| Timer / clock events | `Tick` | Scheduled or periodic wakeup signals |
| Feedback from Execution | `ActionResult` | Consequences of prior actions (success/failure/partial) |

### 2.3 Outputs

| Record | Schema | Description |
|---|---|---|
| `EvidenceRecord` | `{id, source, timestamp, payload, confidence: [0,1], tags[]}` | A single structured observation |

### 2.4 Dependencies

| Dependency | Nature |
|---|---|
| GENESIS Space | Evidence attaches to and references objects in Space |
| SMS ingress pipeline | Raw signal delivery |
| Clock service | Temporal anchoring |
| Channel registry | Source identification and capability advertisement |

### 2.5 Public API

```
EvidenceCore:
  + ingest(signal: Signal) → EvidenceId
  + query(filter: EvidenceFilter) → EvidenceSet
  + gc(ttl: Duration) → Pruned
  - classify(signal: Signal) → EvidenceRecord   (internal)
  - deduplicate(records: EvidenceRecord[]) → EvidenceRecord[]   (internal)
```

**Invariants:**
- Every ingested signal produces exactly one EvidenceRecord (no drops, no duplicates)
- EvidenceRecords are immutable once committed
- Confidence is never retroactively raised, only lowered or decayed

### 2.6 Constitutional Invariants

1. **Source attribution is mandatory.** Every EvidenceRecord carries an unforgeable source tag. Anonymous evidence is rejected.
2. **Confidence is bounded [0, 1].** No evidence is ever trusted at 1.0 (absolute certainty is a failure mode).
3. **Evidence does not self-delete.** Expiry and pruning are governed by the gc() method and configurable TTL policies — never by the evidence itself.
4. **No interpretation.** Evidence classifies the form (text, image, delta, event) but does not interpret meaning. Meaning is the domain of E-005.
5. **Retention is bounded.** Evidence storage is finite. A sliding window with configurable depth governs what survives.

### 2.7 Extension Points

| Point | Mechanism |
|---|---|
| New signal types | Register a classifier in the channel registry |
| Custom confidence heuristics | Plug a `ConfidenceScorer` function into the ingest pipeline |
| Evidence enrichment | Middleware chain on ingress before commit |
| Storage backend | Swap `EvidenceStore` implementation (memory, disk, database) |

### 2.8 Failure Modes

| Failure | Behaviour | Recovery |
|---|---|---|
| Signal malformed | Rejected with logged reason | Generator retransmits |
| Store full | Oldest records evicted per policy | Configurable watermark + alert |
| Source untrusted | Record dropped, audit log written | Operator revokes source credential |

---

## 3. E-005: Reasoning

### 3.1 Purpose

Operate on Evidence Records to produce **Beliefs** — evaluated, cross-referenced, contradiction-resolved propositions about the world. Reasoning is where raw observations become actionable understanding.

Reasoning does not decide what to do. It decides what is true, probable, or uncertain.

### 3.2 Inputs

| Source | Type | Description |
|---|---|---|
| E-004 | `EvidenceRecord[]` | Batch of evidence from current tick + historical window |
| Previous Beliefs | `BeliefGraph` | Persistent set of active beliefs from prior cycles |
| GENESIS Relationship Engine | `Relationships` | Known connections between objects, actors, spaces |
| Context store | `ContextFrame` | Working memory from recent pipeline passes |

### 3.3 Outputs

| Record | Schema | Description |
|---|---|---|
| `Belief` | `{id, proposition, confidence, supporting_evidence[], contradicting_evidence[], timestamp, expiry}` | A evaluated statement about the world |
| `Contradiction` | `{belief_a_id, belief_b_id, conflict_type, resolution_attempt}` | A detected inconsistency between beliefs |
| `ReasoningTrace` | `{chain[], provenance[], confidence_distribution}` | Audit trail of how a conclusion was reached |

### 3.4 Dependencies

| Dependency | Nature |
|---|---|
| E-004 Evidence | Primary input material |
| GENESIS Relationship Engine | Traversal and inference over known relationships |
| Context store | Short-term working memory for multi-step reasoning chains |
| Contradiction resolution policy | Configurable strategy for handling conflicting evidence |

### 3.5 Public API

```
ReasoningCore:
  + evaluate(evidence: EvidenceSet, context: ContextFrame) → BeliefSet
  + resolve(contradictions: Contradiction[]) → ResolutionReport
  + prune(threshold: float) → int   // decay beliefs below confidence threshold
  - compose(evidence: EvidenceRecord[]) → Proposition[]   (internal)
  - cross_reference(propositions: Proposition[], relationships: Relationships) → Belief[]   (internal)
  - check_contradictions(beliefs: Belief[]) → Contradiction[]   (internal)
```

**Invariants:**
- Every Belief references at least one EvidenceRecord as support
- No Belief is created without a cross-reference pass
- Contradictions are surfaced, never silently dropped

### 3.6 Constitutional Invariants

1. **Beliefs are provisional.** Every Belief carries an expiry. No permanent beliefs.
2. **Contradictions must be explicit.** A contradiction detection pass runs every tick. Silent conflicts are a design error.
3. **Provenance is required.** Every Belief exposes its full reasoning trace for audit.
4. **No action selection.** Reasoning does not generate goals, plans, or actions. It only produces statements of belief.
5. **Confidence decay is monotonic.** Beliefs lose confidence over time. Refresh requires new evidence.

### 3.7 Extension Points

| Point | Mechanism |
|---|---|
| Reasoning strategy | Replaceable `ReasoningEngine` (symbolic, probabilistic, neural, hybrid) |
| Contradiction resolution policy | Pluggable `ConflictStrategy` (majority, recency-weighted, authority-weighted) |
| Belief decay function | Configurable `DecayCurve` (linear, exponential, step) |
| Inference rules | Registry of `InferenceRule` for relationship-based deduction |

### 3.8 Interaction with E-004

E-005 subscribes to E-004's output stream. It does not call into E-004 directly. Evidence can be re-queried by ID for re-evaluation, but reasoning never triggers new evidence ingestion.

### 3.9 Failure Modes

| Failure | Behaviour | Recovery |
|---|---|---|
| Evidence insufficient | Beliefs produced at low confidence | Execution stage routes to information-seeking |
| Contradiction unresolvable | Both beliefs retained with contradiction flag | External intervention or additional evidence |
| Reasoning timeout | Partial BeliefSet returned, alert raised | Next tick continues from checkpoint |

---

## 4. E-006: Planning

### 4.1 Purpose

Translate Beliefs into **Goals** and **Plans** — ordered, conditioned sequences of actions that, if executed, would achieve a desired world state. Planning is where understanding becomes intention.

Planning does not act. It designs routes.

### 4.2 Inputs

| Source | Type | Description |
|---|---|---|
| E-005 | `BeliefSet` | Current evaluated understanding of the world |
| Directive store | `Directive[]` | Standing goals, user commands, constitutional imperatives |
| Object model | `Space` | Known objects and their capabilities |
| Relationship model | `Relationships` | How objects connect and constrain each other |
| Historical plans | `PlanArchive` | Previous plans for reference and reuse |

### 4.3 Outputs

| Record | Schema | Description |
|---|---|---|
| `Goal` | `{id, desired_state, priority, deadline, dependencies[]}` | A target world state to achieve |
| `Plan` | `{id, goal_id, steps[], conditions[], fallbacks[], risk_assessment}` | Ordered sequence of conditioned actions |
| `PlanFragment` | `{id, steps[], preconditions, effects}` | Reusable sub-plan (macro) |
| `RiskAssessment` | `{expected_cost, expected_success, failure_branches[]}` | Projected outcomes |

### 4.4 Dependencies

| Dependency | Nature |
|---|---|
| E-005 Beliefs | World understanding that grounds planning |
| GENESIS Space | Object capabilities and state space for precondition evaluation |
| Directive store | Source of goals when not reactive |
| Plan library | Cached/reusable plan fragments for efficiency |

### 4.5 Public API

```
PlanningCore:
  + derive_goals(beliefs: BeliefSet, directives: Directive[]) → GoalSet
  + plan(goal: Goal, context: Space, max_depth: int) → Plan | NoPlan
  + refine(plan: Plan, new_beliefs: BeliefSet) → Plan
  + select(plans: Plan[]) → Plan   // choose best plan to execute
  + cache(fragment: PlanFragment) → FragmentId
  - decompose(goal: Goal) → SubGoal[]   (internal)
  - sequence(subgoals: SubGoal[]) → Step[]   (internal)
  - evaluate_risk(plan: Plan) → RiskAssessment   (internal)
```

**Invariants:**
- Every Plan maps to exactly one Goal
- Every Plan step references an actionable capability in Space
- No Plan is selected without risk assessment
- Plans are always annotated with fallback branches

### 4.6 Constitutional Invariants

1. **Goals are traceable.** Every Goal originates from either a directive or a derived need. No orphan goals.
2. **Plans have preconditions.** Every step declares what must be true before execution. No blind steps.
3. **Fallbacks are mandatory.** Every Plan includes at least one alternative branch. No single-point-of-failure plans.
4. **Risk before selection.** No Plan is selected for execution without passing through risk assessment.
5. **No direct execution.** Planning does not call into Execution. It returns a Plan record for E-007 to consume.

### 4.7 Extension Points

| Point | Mechanism |
|---|---|
| Planner algorithm | Replaceable `PlannerEngine` (hierarchical, Monte Carlo, LLM-driven, STRIPS) |
| Goal prioritization | Pluggable `PriorityFunction` (urgency, importance, dependency order) |
| Plan fragment library | Extensible registry of reusable macros |
| Risk model | Configurable `RiskEvaluator` (simulation-based, heuristic, learned) |

### 4.8 Interaction with E-005

E-006 consumes E-005's BeliefSet but does not mutate it. During planning, if belief gaps are identified (precondition unknown), the plan may include information-seeking steps that, when executed, feed new evidence into E-004 and, through the pipeline, new beliefs into the next planning tick.

### 4.9 Failure Modes

| Failure | Behaviour | Recovery |
|---|---|---|
| No plan found | `NoPlan` returned, goal deferred | Alternative goal selected or information-seeking triggered |
| Plan too deep | Truncated at max_depth, partial plan returned | Refinement on next tick with sub-goal decomposition |
| All plans high-risk | Lowest-risk plan flagged for execution with warnings | Human-in-the-loop intervention configured |

---

## 5. E-007: Execution

### 5.1 Purpose

Activate the selected Plan in the real world — dispatching actions, monitoring their effects, handling failures, and reporting results back to the pipeline. Execution is where intention becomes impact.

Execution is the only stage that touches the outside world.

### 5.2 Inputs

| Source | Type | Description |
|---|---|---|
| E-006 | `Plan` | The selected plan to execute |
| E-006 | `RiskAssessment` | Expected outcomes and failure branches |
| Object capabilities | `Capability[]` | What each object in Space can do |
| SMS egress channels | `ActuatorMap` | Available output pathways |

### 5.3 Outputs

| Record | Schema | Description |
|---|---|---|
| `ActionResult` | `{action_id, step_id, status, output, duration, side_effects}` | Result of a single action |
| `ExecutionReport` | `{plan_id, step_results[], overall_status, summary}` | Aggregate report for the executed plan |
| `FeedbackSignal` | `{source, payload, timestamp}` | New observations from execution (fed back to E-004) |

### 5.4 Dependencies

| Dependency | Nature |
|---|---|
| E-006 Plan | The actions to execute |
| GENESIS Space | Object references and capability lookup |
| SMS motor channels | Actual actuator dispatch |
| Milestone X Authorization | Permission check before each action |
| Monitoring service | Step timeout, health check, failure detection |

### 5.5 Public API

```
ExecutionCore:
  + execute(plan: Plan, auth_token: AuthToken) → ExecutionReport
  + abort(plan_id: PlanId) → Status
  + step(action_id: ActionId) → ActionResult
  + monitor(plan_id: PlanId) → ExecutionStatus
  + retry(step_id: StepId, alternative: Step) → ActionResult
  - check_permissions(action: Action, token: AuthToken) → bool   (internal)
  - dispatch(action: Action, channel: Actuator) → ActionResult   (internal)
  - handle_failure(action: Action, result: ActionResult) → RecoveryAction   (internal)
```

**Invariants:**
- Every action is authorized before dispatch
- Every action has a timeout — no infinite blocks
- Every action produces exactly one ActionResult
- Failure results in recovery action, not silent abort

### 5.6 Constitutional Invariants

1. **All actions are authorized.** No action executes without passing through Milestone X authorization. Period.
2. **Actions are idempotent or guarded.** Every action declares whether it is safe to retry. Destructive actions carry an explicit guard.
3. **Timeouts are mandatory.** Every action has a configurable timeout. No unbounded execution.
4. **Failure is not silent.** Every failure produces a structured error record fed back into E-004.
5. **Side effects are logged.** Every action logs its full effect on Space and external systems.

### 5.7 Extension Points

| Point | Mechanism |
|---|---|
| Action dispatch | Pluggable `Actuator` per action type (HTTP, file, message, tool) |
| Failure recovery | Replaceable `RecoveryStrategy` (retry, fallback-step, abort, notify) |
| Monitoring/observability | Middleware chain around each action dispatch |
| Rate limiting | Configurable throttle per actuator channel |

### 5.8 Interaction with E-006

E-007 consumes E-006's Plan but does not modify it. At runtime, if a step fails beyond recovery, Execution reports the failure back through the pipeline (E-004 as feedback signal), and on the next tick E-006 may produce an alternative plan or E-005 may revise the beliefs that led to the failed plan.

### 5.9 Interaction with E-004 (Feedback Loop)

Every ActionResult and side-effect observation is packed as a FeedbackSignal and routed to E-004's ingress. This closes the loop: action → observation → new evidence → revised beliefs → new plan.

### 5.10 Failure Modes

| Failure | Behaviour | Recovery |
|---|---|---|
| Action unauthorized | Step skipped, reason logged, plan paused | Authorization updated or alternative step selected |
| Action timeout | Step marked failed, fallback step attempted | RecoveryStrategy applied |
| Channel unavailable | Step queued with backoff, alternative channel attempted | Channel re-connection in background |
| Partial success | Some steps complete, partial report generated | Next planning tick determines whether to retry or adapt |

---

## 6. E-008: Learning

### 6.1 Purpose

Reflect on pipeline execution history to produce durable improvements — updated models, new plan fragments, optimized policies, and refined confidence heuristics. Learning is where experience becomes capability.

Learning never changes the architecture. It improves the parameters.

### 6.2 Inputs

| Source | Type | Description |
|---|---|---|
| E-004–E-007 | `PipelineTrace` | Full audit trail of the tick: evidence → beliefs → plan → results |
| E-007 | `ExecutionReport` | What happened, what worked, what failed |
| Previous models | `LearnedModel[]` | Existing learned structures (heuristics, policies, fragments) |
| Performance metrics | `MetricsSnapshot` | Latency, accuracy, success rate, resource usage |

### 6.3 Outputs

| Record | Schema | Description |
|---|---|---|
| `LearnedModel` | `{id, type, parameters, version, provenance, timestamp}` | An updated or new learned artifact |
| `PolicyUpdate` | `{target, old_policy, new_policy, rationale}` | Recommended change to a pipeline policy |
| `SkillFragment` | `{preconditions, steps[], effects, success_rate}` | Reusable plan fragment extracted from successful execution |
| `LearningReport` | `{updates[], performance_delta, regressions[]}` | Summary of what changed |

### 6.4 Dependencies

| Dependency | Nature |
|---|---|
| Full pipeline trace | The data to learn from |
| Model store | Persistent storage for learned artifacts |
| Policy registry | Where policy updates are applied (or queued for review) |
| Plan fragment library | Where SkillFragments are registered for E-006 reuse |
| Performance baseline | Comparison point for measuring improvement |

### 6.5 Public API

```
LearningCore:
  + analyze(trace: PipelineTrace, baseline: MetricsSnapshot) → LearningReport
  + extract_skill(fragment: PlanFragment, success_rate: float) → SkillId
  + update_model(model_id: ModelId, parameters: dict) → ModelVersion
  + suggest_policy(current: Policy, evidence: EvidenceSet) → PolicyUpdate
  + rollback(model_id: ModelId, version: ModelVersion) → Status
  - evaluate_performance(report: ExecutionReport, baseline: MetricsSnapshot) → PerformanceDelta   (internal)
  - generalize(successes: Plan[], failures: Plan[]) → Heuristic[]   (internal)
  - detect_regression(old: MetricsSnapshot, new: MetricsSnapshot) → Regression[]   (internal)
```

**Invariants:**
- Learning is offline — never on the critical path of the pipeline
- Every learning update is versioned
- Every update is reversible (rollback supported)

### 6.6 Constitutional Invariants

1. **Learning is non-blocking.** The pipeline does not wait for learning. Learning operates on historical traces, not the current tick.
2. **All updates are versioned.** Every model, policy, or fragment change carries a version number. Overwrites are forbidden — append only.
3. **Regressions are detected.** Before any update is committed, a regression check runs against the performance baseline.
4. **Rollback is supported.** Every update can be reversed to the previous version. No unrecoverable learning.
5. **Learning does not modify architecture.** Learning tunes parameters, heuristics, and policies. It does not add, remove, or rewire stages.
6. **Human review slot.** Learning outputs may be queued for approval before activation (configurable per update type).

### 6.7 Extension Points

| Point | Mechanism |
|---|---|
| Learning algorithm | Replaceable `Learner` (reinforcement learning, Bayesian update, exemplar store, LLM distillation) |
| Skill extraction strategy | Pluggable `SkillExtractor` (frequency-based, utility-based, novelty-based) |
| Regression metric | Configurable `RegressionDetector` (threshold comparison, statistical test) |
| Approval workflow | Replaceable `ApprovalGate` (auto, manual, hybrid) |

### 6.8 Interaction with Previous Epics

| Epic | Learning's Relationship |
|---|---|
| **E-004 Evidence** | Learning refines confidence heuristics used by E-004's classifier |
| **E-005 Reasoning** | Learning produces new inference rules for E-005's reasoning engine |
| **E-006 Planning** | Learning creates skill fragments cached in E-006's plan library |
| **E-007 Execution** | Learning tunes timeout policies, retry strategies, and channel preferences for E-007 |

### 6.9 Failure Modes

| Failure | Behaviour | Recovery |
|---|---|---|
| Insufficient trace data | Learning skipped for this tick, no update | Accumulate more data |
| Regression detected | Update rejected, regression report generated | Manual review or alternative model candidate |
| Model corruption | Previous version restored, alert raised | Rollback to last stable version |
| Learning timeout | Partial LearningReport returned | Next tick completes with remaining data |

---

## 7. Pipeline Dynamics

### 7.1 Tick Model

A pipeline **tick** is one complete pass E-004 → E-005 → E-006 → E-007. E-008 runs asynchronously on historical traces and is not on the critical path.

```
  Tick N:
    E-004: ingest(signals) → evidence
    E-005: evaluate(evidence) → beliefs
    E-006: derive_goals(beliefs) → plan
    E-007: execute(plan) → results
    ─────────────────────────────
    E-008: analyze(trace_N, baseline) → updates   (async, may span multiple ticks)
```

### 7.2 Cadence

Each stage can operate at its own cadence:

| Stage | Default Cadence | Rationale |
|---|---|---|
| E-004 | Continuous / event-driven | Signals arrive at any time |
| E-005 | Per tick | Beliefs must be fresh for planning |
| E-006 | Per tick (or on demand) | Plans generated when goals exist |
| E-007 | Per action step | Actions complete on their own schedule |
| E-008 | Every N ticks or idle | Learning is opportunistic, not time-critical |

### 7.3 Back-Pressure

If E-005 is slower than E-004, evidence buffers. If E-006 is slower than E-005, beliefs accumulate without generating new plans. Each stage declares its max queue depth and overflow policy (drop-oldest, block, alert).

### 7.4 Error Propagation

Errors in one stage do not crash the pipeline. Each stage catches, wraps, and passes errors forward as structured records:

```
  E-005 error → E-005 returns a partial BeliefSet with error annotations
  E-006 receives partial BeliefSet → plans with lower confidence
  E-007 receives degraded plan → elevated risk assessment, conservative execution
  E-008 observes whole trace → may recommend adjustments
```

---

## 8. Constitutional Invariants

These invariants apply across ALL Intelligence Core Epics E-004 through E-008.

### 8.1 Do Not

1. **Do not** hardcode any model, algorithm, or framework. All reasoning, planning, and learning engines are replaceable via pluggable interfaces.
2. **Do not** allow any stage to bypass the pipeline. Evidence must pass through Reasoning. Plans must come from Planning. Actions must pass through Execution authorization.
3. **Do not** allow side effects in E-004, E-005, E-006, or E-008. Only E-007 touches the outside world.
4. **Do not** allow silent failures. Every failure produces a structured record consumed by the next tick or the learning stage.
5. **Do not** allow unbounded resource consumption. Every stage declares its resource budget (time, memory, storage) and is enforced by the Kernel.
6. **Do not** allow learning to modify the architecture. Parameter tuning only. Pipeline structure is constitutionally protected.

### 8.2 Do

1. **Every stage is independently testable.** Each stage receives its input type and produces its output type — no shared mutable state.
2. **Every stage exposes an audit trail.** ReasoningTrace, RiskAssessment, ExecutionReport, LearningReport — all serializable, all inspectable.
3. **Every stage has a performance contract.** Throughput, latency p99, and error rate are measured per stage.
4. **The pipeline is observable.** A runtime inspector can attach to any stage boundary, read current state, and replay historical traces.
5. **The pipeline is stoppable.** A `STOP` signal can be injected at any stage boundary, pausing the pipeline and saving checkpoint state.

---

## 9. Cross-Cutting Concerns

### 9.1 Security

- E-004 validates source authenticity before ingestion.
- E-007 authorizes every action via Milestone X.
- All inter-stage communication is within the Kernel's protected memory space.
- Learning outputs that modify policies may be subject to approval gates.

### 9.2 Observability

Each stage emits structured telemetry:

```
PipelineTelemetry {
  tick_id: Uuid,
  stage: StageType,
  input_size: usize,
  output_size: usize,
  duration_ms: u64,
  error: Option<ErrorRecord>,
  metrics: HashMap<String, f64>,
}
```

### 9.3 Testing Strategy

| Stage | Unit Test | Integration Test | Performance Test |
|---|---|---|---|
| E-004 | Ingest → verify EvidenceRecord fields | Pipeline integration: signal → EvidenceRecord | Throughput: signals/sec at max load |
| E-005 | Evidence Set → Belief Set with known contradictions | Full pipeline: signal → belief evaluation | Latency: time to produce BeliefSet |
| E-006 | Goal → Plan generation with known preconditions | Pipeline: evidence → plan | BFS depth vs time |
| E-007 | Plan execution → ActionResult per step | Pipeline: signal → action | Action dispatch throughput |
| E-008 | Trace analysis → LearningReport | Full pipeline + learning cycle | Convergence rate |

### 9.4 Resource Governance

| Resource | E-004 | E-005 | E-006 | E-007 | E-008 |
|---|---|---|---|---|---|
| Memory (evidence/beliefs) | Configurable sliding window | Configurable belief cap | Plan library size limit | Action queue depth | Model version limit |
| CPU time | Per-signal budget | Per-tick budget | Per-plan depth limit | Per-action timeout | Offline, no hard limit |
| Storage | Evidence TTL | Belief expiry | Fragment cache TTL | Result log TTL | Model version retention |

---

## 10. Appendices

### Appendix A: Epic Dependency Graph

```
  SMS ──> E-004 ──> E-005 ──> E-006 ──> E-007 ──> SMS
   │       │          │          │          │        │
   │       │          │          │          │        │
   v       v          v          v          v        v
  GENESIS ─────────────────────────────────────────────
   │                                                  │
   v                                                  v
  Milestone X ──────────────────────────────────> E-007
```

### Appendix B: Stage Maturity Model

| Level | E-004 | E-005 | E-006 | E-007 | E-008 |
|---|---|---|---|---|---|
| **Alpha** | Signal → structured record | Keyword/rule-based classification | Predefined plan library | Direct action dispatch | Log-based review |
| **Beta** | Confidence scoring | Symbolic reasoning with contradictions | Goal decomposition | Failure recovery | Skill extraction |
| **GA** | Plugable classifiers | Multiple reasoning engines | Full planning with risk | Authorization + monitoring | RL / Bayesian update |
| **Post-GA** | Predictive confidence | Meta-reasoning (reasoning about reasoning) | Multi-agent planning | Predictive execution | Cross-session transfer learning |

### Appendix C: Boundary Definitions

This roadmap defines the Intelligence Core in isolation. The following are explicitly **out of scope**:

| Topic | Rationale |
|---|---|
| User interface | The UI is a consumer of the pipeline's outputs, not part of it |
| Message routing | SMS handles channel-specific ingress/egress; Intelligence Core handles cognitive processing only |
| Conversation state | Managed by the Kernel and Context service above the pipeline |
| Multi-agent coordination | A future epic beyond E-008 that composes multiple Intelligence Core instances |
| Persistent memory | The Learning stage (E-008) produces durable artifacts, but long-term memory is a separate subsystem that consumes Learning outputs |

---

*End of Document — E-004 through E-008 Architecture Roadmap*
*Classification: Canonical Architecture Document*
*Next: Implementation Milestones derived from this roadmap*
