# ES-006: Observer Engine

**Status:** Draft
**Phase:** Phase 2 (Observer Layer)
**Layer:** Observer
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters the Observer Engine

- **Execution outcomes** — complete execution results from the Executor Engine (ES-005). Task statuses, delivery confirmations, API responses, failure records, timestamps.
- **Execution evidence** — proof of execution collected by the Executor: delivery receipts, API response bodies, transaction IDs, signed confirmations.
- **Expected plans** — the governance-approved plan from the Planner Engine (ES-004) containing expected outcomes, schedules, costs, and resource allocations.
- **Expected results** — predicted results from the Reasoning Engine (ES-003): expected confidence, expected risk, expected outcome.
- **Context** — workspace context: tenant, actor, purpose, subject, correlation ID, trace ID.
- **Telemetry** — system-level metrics: CPU, memory, latency, throughput, error rates from the execution environment.
- **Metrics** — business-level metrics: conversion rates, completion rates, cycle times, resource utilization.
- **Logs** — application and system log entries relevant to the execution being observed.

### What Leaves the Observer Engine

- **Verified observations** — validated records of what actually happened, with confidence scores and evidence references.
- **Anomaly reports** — structured reports for observations that deviate from expected patterns beyond defined thresholds.
- **Deviation reports** — quantified differences between expected and actual outcomes for every measurable dimension.
- **Evidence bundles** — packaged evidence for each observation, linking the observation to its supporting execution records.
- **Learning signals** — structured inputs for the Learning Engine: what happened, what was expected, what the discrepancy was, and the confidence in the observation.
- **Execution assessments** — quality scores for each execution: accuracy of delivery, timeliness, cost adherence, resource efficiency.
- **Confidence updates** — revised confidence scores for facts and knowledge items based on observed outcomes.
- **Observation package** — the complete observation result packaged for downstream consumption (Knowledge Engine, Learning Engine, Governance Engine for policy feedback).

### What Intelligence Is Compounded

The Observer Engine compounds **observation accuracy** over time. Every observation cycle validates its own observation against subsequent outcomes. Patterns in observation accuracy (false positives, false negatives, missed observations) are fed back to improve observation thresholds, detection algorithms, and evidence validation rules.

The compounding mechanism is **self-validation**: when an observation leads to a learning signal that changes behaviour, the Observer observes the new behaviour too. The Observer can detect if its own observation was accurate or inaccurate by comparing multiple observation cycles over time.

### Which Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Learning Engine | Consumes observation outcomes and learning signals | **Critical** — cannot learn without observations |
| Knowledge Engine | Receives verified observations as new facts | **High** — observation without storage is lost |
| Governance Engine | Consumes execution assessments for policy refinement | **Medium** — can refine policies with or without assessments |
| Executor Engine | Receives observation feedback for execution improvement | **Low** — execution is not dependent on observation feedback |

### What Fails If It Becomes Unavailable

- **The compounding loop breaks** — no observations means no learning signals, means no improvement
- **The system becomes blind** — it can act but cannot see the results of its actions
- **Discrepancies go undetected** — failed executions are not detected, incorrect outcomes are assumed successful
- **Knowledge does not update** — verified observations never become facts, so the Knowledge Engine stagnates

---

## Section 1 — Mission

### Purpose of the Observer Inside SHUNYA

The Observer Engine transforms execution outcomes into verified observations. It is the bridge between *what actually happened* (Executor) and *what should change as a result* (Learning, Knowledge). The Observer collects execution evidence, compares actual outcomes to expected outcomes, detects anomalies and deviations, and produces verified, confidence-scored observations for downstream consumption.

The canonical lifecycle (SHUNYA System Flow §2) positions Observation after Execution and before Knowledge Update and Learning:

```
Governance → Execution → [Observation] → Knowledge Update → Learning
```

### The Observer SHALL

- Observe every execution outcome without exception
- Compare actual outcomes to expected outcomes from plans and reasoning
- Detect anomalies (unexpected patterns, outliers, impossible states)
- Detect deviations (quantified differences between expected and actual)
- Collect and validate execution evidence
- Produce verified, confidence-scored observations
- Package and emit learning signals for the Learning Engine

### The Observer SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never execute actions | Would violate Separation of Responsibilities | Executor Engine |
| Never create or modify plans | Would violate Layer Boundaries | Planner Engine |
| Never reason (generate new conclusions) | Would violate Layer Boundaries | Reasoning Engine |
| Never govern (evaluate policies) | Would violate Layer Boundaries | Governance Engine |
| Never modify knowledge directly | Would violate Layer Boundaries | Knowledge Engine (writes must go through its API) |
| Never invent observations | Would violate Explainable Decisions | (observations must be grounded in evidence) |
| Never learn from observations | Would violate Layer Boundaries | Learning Engine |
| Never mutate evidence | Would violate Architectural Invariant | (evidence is immutable per Core Models §11) |

---

## Section 2 — Inputs

All inputs conform to the canonical models defined in SHUNYA Core Models and the output contracts of upstream engines.

### Input Contract

```
ObserverInput:
  execution_outcome: OutcomePackage     — From ES-005. Complete execution result with task
                                          statuses, failures, evidence, metrics.
  execution_evidence: ExecutionEvidence[] — Proof of execution: delivery confirmations, API
                                          responses, receipts, timestamps.
  expected_plan: ExecutionPlan          — From ES-004 (via governance). The approved plan
                                          with expected outcomes, schedules, costs.
  expected_results: ReasoningResult     — From ES-003. Expected confidence, risk, outcome.
  context: WorkspaceContext             — Tenant, actor, purpose, correlation ID, trace ID.
  telemetry: TelemetryBatch             — System-level metrics from execution environment.
  business_metrics: BusinessMetric[]    — Business-level metrics relevant to the observation.
  logs: LogEntry[]                      — Relevant log entries from execution.
  request_metadata: RequestInfo         — Correlation ID, trace ID, tenant ID.
```

### Input Sources

| Input | Source | Retrieval Method |
|-------|--------|-----------------|
| Execution outcome | Executor Engine (ES-005) | Outcome package delivered after execution completion |
| Execution evidence | Executor Engine (ES-005) | Embedded in outcome package |
| Expected plan | Governance Engine (ES-001) | The approved plan stored in governance audit log |
| Expected results | Reasoning Engine (ES-003) | The reasoning result stored with the plan |
| Context | Context Fusion (Phase 10) | Propagated through request lifecycle |
| Telemetry | Monitoring infrastructure | Pulled from metrics store or pushed via event bus |
| Business metrics | Business intelligence layer | Pulled on demand per observation cycle |
| Logs | Application logging infrastructure | Pulled by correlation or trace ID |

### Input Validation

| Field | Constraint | Rejection |
|-------|-----------|-----------|
| `execution_outcome.workflow_id` | Must match a known governance-approved plan | `UNKNOWN_WORKFLOW` |
| `expected_plan.tasks` | Must be non-empty for plan comparison | `NOT_AVAILABLE` — comparison skipped |
| `execution_evidence` | May be empty (execution produced no evidence) | Warning — reduced observation confidence |
| `context.tenant_id` | Must match request tenant | `TENANT_MISMATCH` |

---

## Section 3 — Outputs

All outputs conform to the canonical models defined in SHUNYA Core Models.

### Output Contract

```
ObserverOutput:
  verified_observations: VerifiedObservation[]  — Validated records of what happened.
  anomaly_reports: AnomalyReport[]              — Unexpected patterns or impossible states.
  deviation_reports: DeviationReport[]          — Quantified differences: expected vs actual.
  evidence_bundles: EvidenceBundle[]            — Packaged evidence per observation.
  learning_signals: LearningSignal[]            — Structured inputs for Learning Engine.
  execution_assessments: ExecutionAssessment[]  — Quality scores per execution.
  confidence_updates: ConfidenceUpdate[]        — Revised confidence for knowledge facts.
  observation_package: ObservationPackage       — Complete result for downstream consumption.
  observer_metadata: ObserverInfo               — Engine version, detection algorithms used.
```

### Output Destinations

| Output | Destination | Format |
|--------|-------------|--------|
| Verified observations | Knowledge Engine (ES-002) | New fact versions or updates to existing facts |
| Anomaly reports | Governance Engine, human review queue | Structured anomaly reports with evidence |
| Deviation reports | Learning Engine, Governance Engine | Quantified deviation data |
| Evidence bundles | Knowledge Engine (ES-002) | Immutable evidence records |
| Learning signals | Learning Engine | Structured learning signal per canonical model |
| Execution assessments | Governance Engine (ES-001) | Quality scores for policy refinement feedback |
| Confidence updates | Knowledge Engine (ES-002) | Confidence revision requests (applied per Knowledge Engine rules) |

### Output Guarantees

- **Every execution produces at least one observation:** No execution passes without being observed.
- **Observations are immutable after creation:** A verified observation is never modified. If a correction is needed, a new observation supersedes the old one.
- **Deviation is quantified:** Every deviation report includes a numeric value for the difference and a confidence score for the deviation measurement.

---

## Section 4 — Observation Pipeline

### Canonical Stages

```
Observation Intake
     │
     ▼
Evidence Validation
     │
     ▼
Outcome Comparison
     │
     ▼
Deviation Detection
     │
     ▼
Anomaly Detection
     │
     ▼
Confidence Assessment
     │
     ▼
Observation Packaging
     │
     ▼
Learning Handoff
     │
     ▼
Knowledge Notification
```

### Stage Definitions

| Stage | Purpose | Inputs | Outputs | Failure Condition |
|-------|---------|--------|---------|-------------------|
| **Observation Intake** | Receive and validate the execution outcome and evidence | Outcome package, evidence, expected plan | Validated intake with matched expected plan | Outcome package malformed; expected plan not found |
| **Evidence Validation** | Validate completeness, authenticity, consistency, and timestamp integrity of evidence | Execution evidence, expected evidence schema | Validated evidence with quality score | Evidence missing; evidence tampered; timestamp out of range |
| **Outcome Comparison** | Compare actual outcomes to expected outcomes for each task and dimension | Validated evidence, expected plan, expected results | Compared outcomes per dimension | Expected plan missing dimensions for comparison |
| **Deviation Detection** | Quantify differences between expected and actual for every measurable dimension | Compared outcomes, tolerance thresholds | Deviation reports with severity | Tolerance thresholds not defined for a dimension |
| **Anomaly Detection** | Detect unexpected patterns, outliers, or impossible states not captured by simple deviation | Deviation reports, historical patterns, anomaly models | Anomaly reports | Anomaly detection model unavailable |
| **Confidence Assessment** | Compute confidence in each observation based on evidence quality, deviation severity, and historical accuracy | Deviations, anomalies, evidence quality scores | Confidence-scored observations | Cannot compute confidence (missing historical baseline) |
| **Observation Packaging** | Package all observations, deviations, anomalies, and evidence into a structured observation package | All previous stage outputs | ObservationPackage | Package too large |
| **Learning Handoff** | Extract learning signals from deviations and anomalies, deliver to Learning Engine | ObservationPackage | LearningSignal[] | Learning Engine unavailable (retry with backoff) |
| **Knowledge Notification** | Notify Knowledge Engine of new verified observations for fact creation or update | Verified observations | Notification confirmation | Knowledge Engine unavailable (retry with backoff) |

---

## Section 5 — Observation Types

| Observation Type | Description | When Used | Example |
|------------------|-------------|-----------|---------|
| **Passive** | Observe outcomes that are reported to the Observer. No active probing. | Default — execution outcomes from the Executor | "Message delivery confirmed by WhatsApp API" |
| **Active** | Observer actively probes for outcome information. Polling, health checks, verification calls. | When passive observation is insufficient or unreliable | "Call the booking API to verify the reservation was created" |
| **Continuous** | Ongoing observation over time. Stream of observations for a single entity or process. | Long-running executions, streaming processes | "Monitor the health of a long-running data migration every 30 seconds" |
| **Scheduled** | Observation triggered by a timer or calendar. | Periodic checks, SLA monitoring, compliance audits | "Verify all pending invoices were processed in the last hourly batch" |
| **Event-driven** | Observation triggered by an event from another engine or external system. | Reactive observation, chained monitoring | "When payment webhook arrives, observe the payment status" |
| **Comparative** | Compare observations across multiple entities, time periods, or dimensions. | Trend analysis, A/B comparison, cross-workspace analysis | "Compare this month's conversion rate to last month's" |
| **Predictive** | Compare actual outcomes to predicted outcomes from the Reasoning Engine. | Model validation, confidence calibration | "Reasoning predicted 0.85 confidence but actual outcome was 0.6" |
| **Human-assisted** | Human reviews the observation and provides additional context or correction. | High-severity deviations, ambiguous anomalies, first observations in a new domain | "Human confirms whether the observed anomaly is a real issue or a false positive" |

---

## Section 6 — Observation Model

### Observation Record

```
VerifiedObservation:
  id: string                          — Unique observation identifier
  workflow_id: string                 — Reference to the workflow being observed
  plan_id: string                     — Reference to the originating plan
  observed_at: datetime               — When the observation was made
  observation_type: string            — Type from Section 5
  expected_state: ObservationState    — What was expected (from plan and reasoning)
  actual_state: ObservationState      — What actually happened (from execution outcome)
  variance: ObservationVariance[]     — Differences between expected and actual
  tolerance: Tolerance                — Acceptable variance thresholds
  severity: string                    — "info" | "warning" | "error" | "critical"
  confidence: float                   — Observer's confidence in this observation (canonical 0.0–1.0)
  evidence: Evidence[]                — Evidence supporting this observation
  anomaly: Anomaly | null             — Anomaly report if anomaly detected
  created_at: datetime
```

### ObservationState

```
ObservationState:
  status: string                     — "success" | "partial" | "failed" | "pending" | "unknown"
  dimensions: StateDimension[]       — Measurable dimensions of the outcome
    - name: string                   — Dimension name: "delivery", "cost", "time", "quality", etc.
    - expected_value: any            — What was expected
    - actual_value: any              — What actually happened
    - unit: string                   — Unit of measurement
    - confidence: float              — Confidence in this dimension's measurement
```

### Variance

```
ObservationVariance:
  dimension: string                  — Which dimension is being measured
  expected: any                      — Expected value
  actual: any                        — Actual value
  delta: float                       — Numeric difference (if applicable)
  delta_percentage: float            — Percentage difference
  severity: string                   — Variance severity per tolerance thresholds
  explanation: string                — Why the variance occurred (if known)
```

### Tolerance

```
Tolerance:
  dimension: string                  — Which dimension this tolerance applies to
  warning_threshold: float           — Variance above this triggers warning
  error_threshold: float             — Variance above this triggers error
  critical_threshold: float          — Variance above this triggers critical
  unit: string                       — Unit for threshold values
```

---

## Section 7 — Evidence Validation

### Validation Dimensions

| Dimension | Method | Failure Consequence |
|-----------|--------|---------------------|
| **Completeness** | Check that all required evidence fields are present for the observation type | Missing evidence reduces observation confidence |
| **Authenticity** | Verify digital signatures, HMAC, or trusted sender identity | Evidence with failed authenticity is discarded; observation confidence set to 0.0 |
| **Consistency** | Cross-check evidence fields against each other and against known facts | Inconsistent evidence triggers deviation report |
| **Correlation** | Verify that evidence timestamps and identifiers correlate with the expected workflow | Evidence from wrong workflow is discarded |
| **Timestamp integrity** | Verify that evidence timestamps are within acceptable bounds (not future, not too old) | Evidence with invalid timestamps is discarded |
| **Provenance** | Verify that evidence can be traced to a known source with a known chain of custody | Evidence without provenance is flagged; confidence reduced |

### Evidence Quality Score

The overall quality of evidence for an observation is computed as:

```
evidence_quality = completeness_score ×
                   authenticity_score ×
                   consistency_score ×
                   correlation_score ×
                   timestamp_integrity_score
```

Each dimension scores 1.0 (pass) or 0.0 (fail). If any dimension scores 0.0, the evidence quality is 0.0 and the observation confidence is set to 0.0 until independent verification is obtained.

---

## Section 8 — Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Missing evidence | Executor did not collect evidence for one or more tasks | Evidence validation stage | Reduced observation confidence; observation proceeds with warning | Request re-observation from Executor (if supported); flag for human review |
| Conflicting evidence | Two evidence sources provide contradictory information | Evidence validation stage | Observations flagged as conflicting; confidence reduced | Flag conflict for resolution; wait for additional evidence |
| Telemetry failure | Monitoring infrastructure unavailable or reporting stale data | Telemetry intake validation | Telemetry-based deviations skipped; observation continues without telemetry | Retry telemetry fetch; alert operator if persistent |
| False positive | Deviation detected but is actually within normal variation | Anomaly detection calibration | Unnecessary alert; reduced trust in detection | Adjust thresholds; feed back to anomaly detection model |
| False negative | Actual deviation not detected | Missed by tolerance thresholds or anomaly detection | Undetected issue; missed learning opportunity | Adjust thresholds; create new anomaly pattern |
| Observation timeout | Observation pipeline takes longer than the configured timeout | Timer | Observation recorded as incomplete; partial observation delivered | Extend timeout for long-running observations; retry complete observation |
| Partial observations | Some dimensions could not be observed (e.g., cost data unavailable) | Per-dimension validation | Observation produced with documented gaps; confidence reduced per dimension | Retry missing dimensions when data becomes available; flag for human review |

---

## Section 9 — Interaction Matrix

| Layer / Engine | Reads | Writes | Events Published | Events Consumed |
|----------------|-------|--------|-----------------|-----------------|
| **Executor Engine** (ES-005) | Execution outcomes, evidence | — | — | `execution.completed`, `execution.failed` |
| **Planner Engine** (ES-004) | Expected plans | — | — | — |
| **Reasoning Engine** (ES-003) | Expected results | — | — | — |
| **Governance Engine** (ES-001) | Approved plans | — | `observation.anomaly.detected` | — |
| **Knowledge Engine** (ES-002) | Existing facts for comparison | Verified observations as new facts | — | — |
| **Learning Engine** | — | Learning signals | `observation.completed` | — |
| **Context Fusion** (Phase 10) | Workspace context | — | — | — |

### Dependencies

| Dependency | Type | Criticality |
|------------|------|-------------|
| Executor Engine (ES-005) | Input — execution outcomes | **Critical** — cannot observe without execution outcomes |
| Planner Engine (ES-004) | Input — expected plans | **High** — cannot detect deviations without expected outcomes |
| Reasoning Engine (ES-003) | Input — expected results | **Medium** — can detect deviations without predicted results |
| Knowledge Engine (ES-002) | Write — verified observations | **High** — observations must be persisted |
| Learning Engine | Write — learning signals | **Medium** — signals can be queued if Learning is unavailable |

### Ownership

- The Observer Engine **owns** observation, deviation detection, anomaly detection, and evidence validation.
- It **does not own** execution outcomes, expected plans, knowledge facts, or learning outcomes.
- It **shares ownership** of observation quality with the Executor Engine (execution evidence quality affects observation quality).

---

## Section 10 — Performance

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| **Observation latency p50** | < 100ms | Per observation cycle (simple) |
| **Observation latency p99** | < 500ms | Per observation cycle |
| **Evidence validation** | < 50ms | Per evidence item |
| **Deviation detection** | < 100ms | Per dimension per observation |
| **Anomaly detection** | < 200ms | Per observation cycle |
| **Concurrent observations** | 500 / instance | Per Observer instance |
| **Observation retention** | 90 days | Active observations in primary store; 7 years in archive |
| **Sampling rate** | 100% for executions with anomalies or failures; 10% for successful executions | Configurable |

### Scaling

- The Observer Engine is stateless for observation processing. Horizontal scaling is achieved by adding instances.
- Observation storage is handled by the Knowledge Engine (ES-002), which handles its own scaling.
- Anomaly detection models may require dedicated instances for computationally intensive pattern analysis.

### Correlation Cost

Correlation of observations across multiple dimensions is O(D × O) where D = number of dimensions and O = number of observations in the correlation window. For large correlation windows (>10,000 observations), windowed aggregation is used instead of point-by-point correlation.

---

## Section 11 — Security

### Auditability

- Every observation is auditable: observation ID, workflow ID, expected state, actual state, variance, evidence references, observer identity, timestamp.
- Audit records are stored in the Knowledge Engine (ES-002) as immutable evidence records.
- Observation audit records are never modified after creation.

### Privacy

- Observations may contain personal data (customer contact information, payment amounts, communication content). Personal data is included only when essential to the observation.
- Observations are classified per Phase 4 (Privacy) sensitivity levels.
- The Observer Engine does not cache personal data between observation cycles.

### Tenant Isolation

- All observations are scoped to the requesting tenant's `tenant_id`.
- Deviation and anomaly detection models are per-tenant (what is anomalous for one tenant may be normal for another).
- No cross-tenant observation leakage.

### Evidence Integrity

- Evidence is immutable after validation. Once an evidence record is validated and included in an observation, it is never modified.
- Evidence tampering is detected during the evidence validation stage.
- Tampered evidence is discarded; the observation is flagged for human review.

---

## Section 12 — Observability

### Metrics

| Metric | Type | Unit | Target |
|--------|------|------|--------|
| `observer.observations_total` | Counter | observations | Per second |
| `observer.observations_by_type` | Counter | observations | Per second, per type |
| `observer.observations_by_severity` | Counter | observations | Per second, per severity |
| `observer.latency_p50` | Histogram | ms | < 100ms |
| `observer.latency_p99` | Histogram | ms | < 500ms |
| `observer.deviations_detected` | Counter | deviations | Per second |
| `observer.anomalies_detected` | Counter | anomalies | Per second |
| `observer.evidence_validated_total` | Counter | evidence items | Per second |
| `observer.evidence_failures_total` | Counter | failures | Per second (by failure type) |
| `observer.learning_signals_emitted` | Counter | signals | Per second |
| `observer.false_positives_total` | Counter | false positives | Per day (fed back from Learning) |
| `observer.false_negatives_total` | Counter | false negatives | Per day (fed back from Learning) |

### Tracing

- **Span: `observer.cycle`** — Full observation lifecycle
  - Child span: `observer.evidence_validation`
  - Child span: `observer.outcome_comparison`
  - Child span: `observer.deviation_detection`
  - Child span: `observer.anomaly_detection`
  - Child span: `observer.confidence_assessment`
  - Child span: `observer.learning_handoff`
  - Child span: `observer.knowledge_notification`
- Trace context propagated from caller (Executor Engine or Event Bus)

### Observation Quality Metrics

| Metric | Purpose |
|--------|---------|
| **Detection accuracy** | Fraction of deviations/anomalies that are correct (not false positives) |
| **Detection coverage** | Fraction of actual deviations/anomalies that are detected (not false negatives) |
| **Evidence completeness rate** | Fraction of observations with complete evidence |
| **Observation freshness** | Time between execution completion and observation production |
| **Confidence calibration** | How well observation confidence scores predict actual observation correctness |

---

## Section 13 — Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Observe every execution outcome | 6.7 Continuous Observation — Execution is never the end | SHUNYA_ARCHITECTURE.md §6.7 |
| Compare expected vs actual | 6.7 Continuous Observation — Compares vs expectation | SHUNYA_ARCHITECTURE.md §6.7 |
| Detect anomalies and discrepancies | 6.7 Continuous Observation — Detects anomalies, discrepancies, failures | SHUNYA_ARCHITECTURE.md §6.7 |
| Produce learning signals | 6.7 Continuous Observation — Feeds observations to Learning | SHUNYA_ARCHITECTURE.md §6.7 |
| Never execute actions | 5 (Observer Layer) — Records reality, never executes | SHUNYA_ARCHITECTURE.md §5 |
| Never invent observations | 6.5 Explainable Decisions | SHUNYA_ARCHITECTURE.md §6.5 |
| Evidence is immutable after validation | 4.3 No Disappearing Evidence | SHUNYA_ENGINEERING_CONSTITUTION.md §4.3 |
| Tenant isolation on all observations | 9 (Multi-Tenant Behaviour) | SHUNYA System Flow §9 |
| Observation is continuous (no gaps) | 5 (Observation is continuous) | SHUNYA System Flow §14 |
| Execution is observable (Executor reports) | 6 (Execution is observable) | SHUNYA System Flow §14 |

---

## Section 14 — Layer Responsibilities

### The Observer Engine SHALL

- Observe every execution outcome without exception
- Compare actual outcomes to expected outcomes from plans and reasoning
- Detect anomalies (unexpected patterns, outliers, impossible states)
- Detect deviations (quantified differences between expected and actual)
- Validate execution evidence for completeness, authenticity, consistency, and integrity
- Produce verified, confidence-scored observations
- Package and emit learning signals for the Learning Engine
- Notify the Knowledge Engine of new observations for fact creation or update
- Respect tenant isolation on all observation data
- Maintain observation audit records immutably

### The Observer Engine SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never execute actions | Would violate Separation of Responsibilities | Executor Engine |
| Never create or modify plans | Would violate Layer Boundaries | Planner Engine |
| Never reason (generate new conclusions) | Would violate Layer Boundaries | Reasoning Engine |
| Never govern (evaluate policies) | Would violate Layer Boundaries | Governance Engine |
| Never modify knowledge directly | Would violate Layer Boundaries | Knowledge Engine |
| Never invent observations | Would violate Explainable Decisions | (observations must be grounded in evidence) |
| Never learn from observations | Would violate Layer Boundaries | Learning Engine |
| Never mutate evidence after validation | Would violate Architectural Invariant | (evidence is immutable per Core Models §11) |
| Never cache personal data between cycles | Would violate Privacy | (per Phase 4 privacy requirements) |

---

## Section 15 — Complexity Analysis

### CPU Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Observation intake | O(E) | E = evidence items in outcome package |
| Evidence validation | O(E × D) | E = evidence items, D = validation dimensions |
| Outcome comparison | O(T × M) | T = tasks, M = measurable dimensions per task |
| Deviation detection | O(D × O) | D = dimensions, O = expected/actual pairs |
| Anomaly detection | O(H × P) | H = historical pattern count, P = pattern complexity |
| Confidence assessment | O(E + D) | Evidence quality + deviation severity |
| Observation packaging | O(S) | S = observation package size |
| Learning signal extraction | O(A + D) | A = anomalies, D = deviations |

### Memory Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Per-observation state | O(T × M + E) | T = tasks, M = dimensions, E = evidence |
| Evidence buffer | O(E × avg_evidence_size) | Per observation, freed after processing |
| Historical pattern cache | O(H × P) | H = patterns, P = pattern size (configurable, LRU eviction) |
| Deviation report | O(D) | D = deviations |

### Retention

- Active observations: 90 days in primary store
- Archived observations: 7 years
- Learning signals: retained with the Learning Engine
- Evidence records: retained per Knowledge Engine retention policy

### Correlation Cost

- Cross-dimension correlation within a single observation: O(M²) where M = number of dimensions
- Cross-observation correlation for anomaly detection: O(O × D) per cycle where O = observations in window, D = dimensions
- For large windows, pre-computed aggregations are used instead of real-time correlation

### Failure Isolation

- Each observation cycle is fully isolated. A failure in one cycle does not affect any other.
- Evidence validation failure is isolated to that evidence item. Other evidence items are processed normally.
- Anomaly detection model failure degrades to deviation-only detection. Observations continue without anomaly detection.
- Knowledge Engine unavailability is handled by queuing observations for retry.

---

## Section 16 — Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 16.1 Predictive Observation

The Observer predicts expected observations before execution completes, based on historical patterns and the current execution trajectory. Deviations are detected in near-real-time rather than post-execution.

### 16.2 Behavioral Analytics

The Observer analyzes patterns across observations to identify behavioral trends — changing success rates, evolving failure modes, shifting user behavior — and surfaces these as intelligence signals.

### 16.3 Autonomous Anomaly Detection

Anomaly detection models that learn and adapt autonomously — adjusting thresholds, discovering new anomaly patterns, and retiring stale patterns — without requiring human model updates.

### 16.4 Digital Twins

A virtual representation of the observed system that mirrors its state in near-real-time. Deviations between the digital twin and the actual system are detected as soon as they occur.

### 16.5 Simulation Feedback

Observed outcomes are fed back into simulation models to improve their accuracy. The Observer validates simulation predictions against real outcomes and calibrates the simulation accordingly.

### 16.6 Cross-Workspace Analytics

The Observer correlates observations across workspaces within the same tenant to detect systemic patterns, shared failure modes, and organization-wide optimization opportunities.

### 16.7 Self-Diagnosis

The Observer diagnoses its own observation quality — detecting when observation accuracy is degrading, when detection thresholds are drifting, and when evidence validation rules are becoming stale — and triggers corrective action.

---

## Section 17 — References

| Document | Relationship |
|----------|-------------|
| **SHUNYA Constitution** (`SHUNYA_ARCHITECTURE.md`) | Supersedes this specification where constitutional principles conflict |
| **SHUNYA Core Models** (`/architecture/SHUNYA_CORE_MODELS.md`) | Defines canonical evidence model (§5), confidence model (§7), provenance model (§6) — all inherited by this specification |
| **SHUNYA System Flow** (`/architecture/SHUNYA_SYSTEM_FLOW.md`) | Defines pipeline position (§2), observation stage in lifecycle (§2), engine responsibilities (§3), failure behaviour (§7) — this specification's behavioral context |
| **SHUNYA Engineering Constitution** (`/governance/SHUNYA_ENGINEERING_CONSTITUTION.md`) | Article 4 (Immutability and Traceability), Article 8 (Divergence Protocol) — governs this specification |
| **ES-001: Governance Engine** (`/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md`) | Provides approved plans for expected-outcome comparison |
| **ES-002: Knowledge Engine** (`/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md`) | Stores verified observations as facts; provides historical data for anomaly detection |
| **ES-003: Reasoning Engine** (`/governance/engine_specs/ES-003-REASONING-ENGINE.md`) | Provides expected results for predictive comparison |
| **ES-004: Planner Engine** (`/governance/engine_specs/ES-004-PLANNER-ENGINE.md`) | Provides expected plans for outcome comparison |
| **ES-005: Executor Engine** (`/governance/engine_specs/ES-005-EXECUTOR-ENGINE.md`) | Provides execution outcomes and evidence for observation |
| `app/shunya/observer_learning.py` | Current ObserverLayer implementation (co-located with LearningLayer, 318 lines total) — v2 with observation CRUD and anomaly detection |