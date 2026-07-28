# Prediction Philosophy v1.0

> **Architectural Addendum to SHUNYA Architecture Specification v1.0**
>
> This document defines the philosophy, constraints, lifecycle, and
> architectural rules governing every predictive capability in SHUNYA.
>
> Prediction must remain deterministic-first, evidence-backed, explainable,
> and business-agnostic. Prediction must never become a hidden probabilistic
> decision engine.
>
> Review and approve this document before implementing Prediction & Simulation.

---

## Table of Contents

- [1. What Constitutes a Prediction](#1-what-constitutes-a-prediction)
- [2. Prediction Inputs](#2-prediction-inputs)
- [3. Prediction Lifecycle](#3-prediction-lifecycle)
- [4. Confidence Philosophy](#4-confidence-philosophy)
- [5. Explainability](#5-explainability)
- [6. Simulation Philosophy](#6-simulation-philosophy)
- [7. Failure Philosophy](#7-failure-philosophy)
- [8. Engineering Rules](#8-engineering-rules)
- [9. Extension Points](#9-extension-points)
- [Appendix A: Prediction Category Reference](#appendix-a-prediction-category-reference)
- [Appendix B: Confidence Factor Reference](#appendix-b-confidence-factor-reference)
- [Appendix C: ADRs](#appendix-c-architectural-decision-records)

---

# 1. What Constitutes a Prediction

## 1.1 Definition

A **prediction** is a derived intelligence artifact that asserts a future state or outcome based on historical evidence, current state, and explicit assumptions. A prediction is always:

- **Probabilistic in output**, not in method — the computation is deterministic, but the result includes a confidence interval.
- **Temporal** — every prediction has a prediction horizon.
- **Conditional** — every prediction depends on current state and explicit assumptions.
- **Recomputable** — given the same inputs, the same prediction is produced.
- **Non-authoritative** — predictions never modify canonical state.

## 1.2 What a Prediction Is Not

- A prediction is **not** a plan. Plans are governance-approved. Predictions are intelligence.
- A prediction is **not** a commitment. Commitments are external business obligations.
- A prediction is **not** a guarantee. A prediction with 95% confidence still has a 5% error bound.
- A prediction is **not** authoritative business state. No downstream system may treat a prediction as fact.

## 1.3 Prediction Categories

### 1.3.1 Completion Forecast

**Definition:** When will this execution reach a terminal state?

**Basis:** `TimelineIntelligenceEngine.predict_completion()` — current completion ratio, elapsed time, obligation satisfaction rate.

**Output:** Predicted datetime + optimistic/pessimistic range + confidence.

**Example:** "Execution exec_abc will be FULFILLED by 2026-07-25T14:00:00Z (optimistic: 2026-07-24, pessimistic: 2026-07-27, confidence: 0.72)."

### 1.3.2 Delay Forecast

**Definition:** Will this execution miss its deadline?

**Basis:** Completion forecast vs. obligation due dates. Overdue obligation count and trend.

**Output:** Delay probability + expected delay duration + contributing factors.

**Example:** "Delay of 3-5 days expected. 2 obligations overdue. Root cause: resource shortfall in budget."

### 1.3.3 Risk Forecast

**Definition:** What is the predicted risk trajectory?

**Basis:** `RiskDetectionEngine` current assessment + `PatternRecognitionEngine` historical patterns for similar executions.

**Output:** Risk level at forecast horizon + trajectory direction + key risk factors.

**Example:** "Risk will increase from MEDIUM to HIGH within 48h unless blocked obligation obl_456 is resolved."

### 1.3.4 Capacity Forecast

**Definition:** Does the organization have capacity to handle expected workload?

**Basis:** Active execution count, obligation density, resource allocation levels.

**Output:** Utilization percentage + bottleneck resources + recommended capacity action.

**Example:** "Budget resource at 85% utilization. Expected to reach 100% within 72h. 3 new executions queued."

### 1.3.5 Workload Forecast

**Definition:** How much work will be active at a future point?

**Basis:** Current active executions + typical duration from `OutcomeLearningEngine` profiles + incoming commitment rate.

**Output:** Active execution count at horizon + distribution by state + peak load timing.

**Example:** "Peak workload of 47 active executions expected on 2026-07-28 (+12 from current)."

### 1.3.6 Bottleneck Forecast

**Definition:** Where will the system block?

**Basis:** `DependencyGraphEngine` critical path + `SimilarityEngine` historical bottlenecks from similar executions.

**Output:** Predicted bottleneck node + expected duration + historical parallel.

**Example:** "Obligation obl_789 (payment_approval) is the predicted bottleneck. 3 of 5 similar executions blocked at this node."

### 1.3.7 Dependency Forecast

**Definition:** Which dependencies will fail or delay?

**Basis:** `ExecutionService` dependency graph + `OutcomeLearningEngine` historical success rates per obligation type.

**Output:** Dependency satisfaction probability + critical dependency chain + alternative paths.

**Example:** "Dependency chain A→B→C has 62% probability of completing on time. B→C is the weakest link."

### 1.3.8 Opportunity Forecast

**Definition:** What positive outcomes are statistically more likely given current conditions?

**Basis:** `PatternRecognitionEngine` high-success patterns + `RecommendationLearning` refined recommendations.

**Output:** Opportunity type + probability + recommended action + expected impact.

**Example:** "Early payment discount opportunity identified. 85% of similar executions that paid within 7 days received 5% discount."

### 1.3.9 Recommendation Forecast

**Definition:** What will happen if the recommended next action is taken?

**Basis:** `NextActionEngine` current recommendations + `OutcomeLearningEngine` historical outcomes for that action type.

**Output:** Action + predicted outcome + confidence + uncertainty range.

**Example:** "Unblocking obligation obl_456 has 78% probability of leading to execution completion within 48h (based on 23 historical samples)."

## 1.4 Prediction Categories Reference

Each prediction category is defined by its `prediction_type` string:

| Category | `prediction_type` | Input Engines | Primary Factors |
|---|---|---|---|
| Completion Forecast | `completion` | Timeline, OutcomeLearning | elapsed, completion_ratio, avg_duration |
| Delay Forecast | `delay` | Timeline, Health, Obligations | overdue_count, due_dates, resource_position |
| Risk Forecast | `risk_trajectory` | RiskDetection, PatternRecognition | current_risk, pattern_strength |
| Capacity Forecast | `capacity` | Portfolio, OutcomeLearning | active_count, resource_utilization |
| Workload Forecast | `workload` | Portfolio, Timeline | active_count, avg_duration, incoming_rate |
| Bottleneck Forecast | `bottleneck` | DependencyGraph, Similarity | critical_path, historical_bottlenecks |
| Dependency Forecast | `dependency` | DependencyGraph, OutcomeLearning | dep_chain, historical_success_rates |
| Opportunity Forecast | `opportunity` | PatternRecognition, Recommendation | pattern_success_rate, action_history |
| Recommendation Forecast | `recommendation_outcome` | NextAction, OutcomeLearning | action_type, context_signature |

---

# 2. Prediction Inputs

## 2.1 Allowable Sources

No prediction may depend upon data outside the documented inputs. Every prediction engine must declare its input sources explicitly.

### 2.1.1 Execution State

**Source:** `app.execution.ExecutionService`

**Allowable data:** `BusinessExecutionInstance` state, obligations, exceptions, resource allocations/consumptions/requirements, dependency graph.

**Used by:** Completion, Delay, Bottleneck, Dependency, Risk forecasts.

### 2.1.2 Evidence

**Source:** `app.evidence` (EvidenceLink, SourceReference, AssertionRecord)

**Allowable data:** Evidence quality scores, evidence-to-execution relationships.

**Used by:** All forecasts (confidence calibration).

### 2.1.3 Learning Intelligence

**Source:** `app.learning_intelligence` (PatternRecognitionEngine, OutcomeLearningEngine, RecommendationLearning, LearningMemory)

**Allowable data:** LearnedPattern, OutcomeProfile, RefinedRecommendation, LearningArtifact.

**Used by:** All forecasts (historical pattern matching, outcome profiling).

### 2.1.4 Organizational Intelligence

**Source:** `app.organizational` (ResponsibilityGraph, OwnershipIntelligence, OrgHealthEngine, OrgKnowledgeGraph)

**Allowable data:** OrgUnit, OrgRole, Responsibility, Ownership, OrgHealth, knowledge graph structure.

**Used by:** Capacity, Workload, Opportunity forecasts.

### 2.1.5 Operational Awareness

**Source:** `app.awareness` (AwarenessMemory, OrganizationalAwareness, ContinuousRiskMonitor)

**Allowable data:** Recent observations, awareness state, cached risk levels.

**Used by:** Risk, Delay, Bottleneck forecasts.

### 2.1.6 Knowledge

**Source:** `app.shunya.knowledge_store` (KnowledgeStore, KnowledgeObject)

**Allowable data:** Versioned facts, namespaced knowledge.

**Used by:** Opportunity, Recommendation forecasts.

### 2.1.7 Memory

**Source:** `app.memory` (MemoryService, MemoryRecord)

**Allowable data:** Active memories with effective dates.

**Used by:** All forecasts (context enrichment).

### 2.1.8 Planner

**Source:** `app.shunya.planner` (PlannerEngine)

**Allowable data:** Plan structure, task sequencing, expected outcomes.

**Used by:** Completion, Dependency, Workload forecasts.

### 2.1.9 Governance

**Source:** `app.shunya.governance_engine` (GovernanceEngine)

**Allowable data:** Policy constraints, approval decisions.

**Used by:** Risk, Delay forecasts.

## 2.2 Input Integrity Rules

1. **All inputs are read-only.** Prediction engines never mutate input sources.
2. **All inputs are snapshotted.** A prediction records the input state at creation time to enable reproducibility.
3. **Missing inputs degrade gracefully.** An engine produces a lower-confidence prediction rather than refusing entirely.
4. **No external API calls.** Predictions depend only on in-process SHUNYA state.

---

# 3. Prediction Lifecycle

## 3.1 States

```
PENDING → ACTIVE → EXPIRED
                → SUPERSEDED
                → WITHDRAWN
```

| State | Description |
|---|---|
| `PENDING` | Prediction created but not yet active (waiting on initial data). Rare. |
| `ACTIVE` | Prediction is current and queryable. |
| `EXPIRED` | The prediction horizon has passed. Prediction is archived. |
| `SUPERSEDED` | A newer prediction for the same entity+horizon has replaced this one. |
| `WITHDRAWN` | Prediction was explicitly invalidated by contradictory evidence. |

## 3.2 Creation

A prediction is created when:

1. **An explicit forecast is requested** via the Prediction Engine API.
2. **An intelligence output triggers re-forecasting** (e.g., a risk level change triggers a new risk forecast).
3. **A periodic re-forecast interval elapses** (configurable, default: every 6 hours of wall-clock time for active forecasts).

Creation produces:
- A `PredictionRecord` containing the prediction type, horizon parameters, input snapshot, computed output, and confidence assessment.
- An entry in `PredictionMemory` (ring buffer).
- A `CanonicalObservation` for the awareness pipeline (category: `intelligence_output`).

## 3.3 Revision

A prediction may be revised when:

1. **New evidence arrives** that changes the input state.
2. **The confidence assessment changes** by more than a threshold (configurable, default: ±0.10).
3. **An explicit re-forecast is requested.**

Revision produces a new `PredictionRecord` that supersedes the previous one. The previous record's state changes to `SUPERSEDED`.

## 3.4 Expiration

A prediction expires when:

1. **The prediction horizon is reached.** The `valid_until` timestamp passes.
2. **The execution reaches a terminal state.** No further predictions are meaningful.

Expired predictions are retained for audit but are not queryable by default.

## 3.5 Supersession

A prediction is superseded when a newer prediction for the same `(prediction_type, entity_id, horizon)` tuple exists. The supersession chain is:

```
Prediction v1 (ACTIVE) → Prediction v2 (SUPERSEDES v1) → Prediction v3 (SUPERSEDES v2)
```

Each supersession records:
- `superseded_by`: The ID of the superseding prediction.
- `reason`: Why the supersession occurred (new_evidence, re_forecast, confidence_change).

## 3.6 Withdrawal

A prediction is withdrawn when contradictory evidence proves the prediction impossible:

- The execution reaches a terminal state before the horizon that contradicts the prediction.
- An error in the input data is discovered.
- A manual withdrawal is issued.

Withdrawal preserves the original prediction for audit but marks it as invalid.

## 3.7 Auditability

Every prediction lifecycle event is recorded in an append-only audit log:

```json
{
  "prediction_id": "abc123",
  "event": "created",
  "timestamp": "2026-07-21T12:00:00Z",
  "input_snapshot": {"exec_id": "...", "state": "active", ...},
  "output": {"predicted_at": "...", "confidence": 0.72, ...}
}
```

The audit log is never modified. It is the authoritative record of every prediction ever made.

---

# 4. Confidence Philosophy

## 4.1 Confidence Factors

Every confidence score is decomposed into **explicit named factors**. The same 5-factor model used in Learning Intelligence (Milestone II) extends to predictions:

| Factor | Weight | Description |
|---|---|---|
| Sample Size | 25% | How many historical observations support this prediction? Calibrated to max at 50 samples. |
| Pattern Consistency | 25% | How consistent is the historical pattern? A 90% historical success rate produces higher consistency than a 55% rate. |
| Input Freshness | 20% | How recent is the input data? Decays over `prediction_freshness_hours` (configurable, default: 24h). |
| Evidence Quality | 15% | What is the quality of the underlying evidence? Derived from `EvidenceValidationResult.quality_score`. |
| Temporal Proximity | 15% | How close is the prediction horizon? Near-term predictions have higher confidence than far-term ones. Decays as `1 - (horizon_seconds / max_horizon_seconds)`. |

### 4.1.1 Factor Algebra

```
confidence = Σ(factor_weight × factor_value)
           = sample_size × 0.25 + consistency × 0.25
             + freshness × 0.20 + evidence_quality × 0.15
             + temporal_proximity × 0.15
```

Each factor value is in [0, 1]. The resulting confidence is in [0, 1].

## 4.2 Confidence Decomposition

Every prediction output includes the full factor decomposition:

```json
{
  "overall": 0.72,
  "factors": [
    {"factor": "sample_size", "value": 0.85, "weight": 0.25, "contribution": 0.2125, "detail": "23 historical samples"},
    {"factor": "consistency", "value": 0.78, "weight": 0.25, "contribution": 0.1950, "detail": "18/23 successful"},
    {"factor": "freshness", "value": 0.95, "weight": 0.20, "contribution": 0.1900, "detail": "input 2h old"},
    {"factor": "evidence_quality", "value": 0.82, "weight": 0.15, "contribution": 0.1230, "detail": "evidence quality 0.82"},
    {"factor": "temporal_proximity", "value": 0.66, "weight": 0.15, "contribution": 0.0990, "detail": "horizon 34h from now"}
  ]
}
```

## 4.3 Confidence Evolution

Confidence evolves over time as:

1. **Freshness decays.** Every hour without new input data reduces the freshness factor.
2. **Temporal proximity changes.** As the horizon approaches, temporal proximity increases, then drops to zero at the horizon.
3. **New evidence triggers re-assessment.** When new observations arrive, freshness resets.

The confidence evolution curve is:
- **Early**: Low confidence (low temporal proximity, low sample size).
- **Mid**: Peak confidence (balance of all factors).
- **Late**: Declining confidence (approaching horizon, uncertainty increases).
- **Post-horizon**: Zero confidence (prediction expired).

## 4.4 Minimum Confidence Thresholds

| Prediction Impact | Minimum Confidence | Behavior Below Threshold |
|---|---|---|
| **Informational** | 0.20 | Produce with warning. |
| **Operational** | 0.40 | Produce with warning; flag as low-confidence. |
| **Tactical** | 0.60 | Refuse; return insufficient-confidence error. |
| **Strategic** | 0.80 | Refuse; return insufficient-confidence error. |

These thresholds are configurable per tenant.

## 4.5 Refusal Conditions

The Prediction Engine must refuse to produce a prediction when:

1. **Insufficient historical data.** Fewer than `min_samples_for_prediction` (default: 3) historical observations exist for the prediction category and context.
2. **Input state is terminal.** The execution is already in a terminal state.
3. **No applicable pattern.** No `LearnedPattern` exists with the required signature for pattern-based predictions.
4. **Confidence below threshold.** The computed confidence is below the minimum for the prediction's impact level.
5. **Contradictory evidence.** Active evidence contradicts the prediction basis (e.g., execution already failed when a success prediction was requested).

Refusal produces a structured response explaining why:

```json
{
  "refused": true,
  "reason": "insufficient_historical_data",
  "detail": "Only 2 historical observations for commitment_type=booking, need 3",
  "available_samples": 2,
  "minimum_required": 3
}
```

---

# 5. Explainability

## 5.1 Mandatory Explanation Fields

Every prediction must be explainable via structured explanation containing:

| Field | Description | Required |
|---|---|---|
| `prediction_id` | The prediction being explained | Always |
| `conclusion` | Human-readable summary of the prediction | Always |
| `why` | The specific evidence that triggered this prediction | Always |
| `evidence_traces` | Traceable links to input evidence | Always |
| `historical_patterns` | Historical patterns used as basis | When pattern-based |
| `learning_artifacts` | Learning artifacts consulted | When available |
| `assumptions` | Explicit assumptions made | Always |
| `uncertainties` | Known uncertainties and their impact | Always |
| `alternatives` | Alternative scenarios considered | When applicable |
| `refusal_reason` | Why the prediction was refused | When refused |

## 5.2 Explanation Structure

```json
{
  "prediction_id": "pred_abc123",
  "type": "completion_forecast",
  "conclusion": "Execution exec_1 is predicted to complete within 72 hours with 72% confidence.",
  "why": "Current completion ratio of 0.45 and average duration of 48h for this commitment type suggest remaining time of 58h.",
  "evidence_traces": [
    {"source": "TimelineSnapshot", "claim": "completion_ratio=0.45", "evidence": "3/7 obligations satisfied", "confidence": 0.9},
    {"source": "OutcomeProfile", "claim": "avg_duration=48h", "evidence": "23 historical samples", "confidence": 0.78},
    {"source": "ExecutionState", "claim": "state=active", "evidence": "exec_id=exec_1", "confidence": 1.0}
  ],
  "historical_patterns": [
    {"pattern_id": "pat_456", "name": "booking_completion", "frequency": 23, "success_rate": 0.83}
  ],
  "learning_artifacts": [
    {"artifact_id": "art_789", "type": "outcome_profile", "dimension": "booking", "success_rate": 0.83}
  ],
  "assumptions": [
    "No new blocked obligations will appear.",
    "Resource allocation remains at current levels.",
    "Average duration of 48h is representative."
  ],
  "uncertainties": [
    {"factor": "sample_size", "impact": "23 samples, moderate uncertainty", "direction": "confidence may increase with more data"},
    {"factor": "temporal_proximity", "impact": "horizon 72h out, temporal decay factor 0.66", "direction": "confidence will increase as horizon approaches"}
  ]
}
```

## 5.3 Explanation Depth Levels

| Level | Detail | Use Case |
|---|---|---|
| `summary` | conclusion + confidence | Dashboard, portfolio view |
| `standard` | + why + evidence_traces | Operational review |
| `detailed` | + assumptions + uncertainties + alternatives | Audit, deep investigation |
| `full` | + historical_patterns + learning_artifacts + factor decomposition | Compliance, debugging |

---

# 6. Simulation Philosophy

## 6.1 What-If Analysis

A what-if analysis answers: "If condition X changes, what happens to prediction Y?"

**Constraints:**
- What-if analyses are read-only. They never modify canonical state.
- What-if analyses operate on a **forked copy** of execution state.
- What-if analyses produce a `SimulationResult` that compares the predicted outcome to the current-state prediction.

**Example:** "What if obligation obl_456 is unblocked now? Predicted completion advances from 72h to 48h."

## 6.2 Counterfactual Reasoning

Counterfactual reasoning answers: "If we had done X instead of Y, what would have happened?"

**Constraints:**
- Counterfactuals use historical data, not speculative state.
- Counterfactuals are clearly labeled as hypothetical.
- Counterfactuals cannot be used as evidence for new predictions.

**Example:** "If resource allocation had been approved 24h earlier, execution exec_1 would have completed 18h sooner (based on 12 similar historical cases)."

## 6.3 Scenario Comparison

Scenario comparison answers: "Given multiple possible actions, which produces the best predicted outcome?"

**Constraints:**
- All scenarios within a comparison use the same prediction engine and parameters.
- Scenarios differ only in their `assumptions` and `modified_state` fields.
- The comparison produces a ranked list with delta from baseline.

**Example:** "Scenario A (unblock obl_456): completion in 48h. Scenario B (increase budget): completion in 56h. Scenario C (no action): completion in 72h. Optimal: Scenario A."

## 6.4 Rollback Assumptions

Simulations are **not reversible** in the sense of "roll back a simulation." Instead:

1. Every simulation records its input assumptions.
2. A simulation can be re-run with different assumptions.
3. Previous simulation results are retained for comparison.
4. There is no `rollback` operation on a simulation — it is not a transaction.

## 6.5 State Isolation

Simulations operate under strict state isolation:

1. **Read-only access** to canonical state.
2. **Writable forked state** — the simulation creates a shallow copy of the relevant execution state.
3. **No persistence** — simulation results are stored as `SimulationResult` artifacts in Learning Memory, not in canonical execution state.
4. **No propagation** — simulations do not generate `CanonicalObservation` events.

## 6.6 Simulation Boundaries

A simulation is bounded by:

1. **Time horizon:** `max_simulation_horizon_hours` (configurable, default: 720h = 30 days).
2. **Scope:** `max_simulation_depth` (configurable, default: 3 levels of dependent entities).
3. **Resources:** `max_simulation_runtime_ms` (configurable, default: 5000ms).
4. **Refusal:** Simulations that exceed bounds are refused with an explanation.

---

# 7. Failure Philosophy

## 7.1 Prediction Evaluation

When a prediction's horizon passes, the Prediction Engine evaluates the prediction against the actual outcome:

1. Compute `error = |predicted_value - actual_value|` for quantitative predictions.
2. Compute `correct = (predicted_outcome == actual_outcome)` for categorical predictions.
3. Record an `EvaluationResult` with the error.
4. Store the evaluation in the prediction's audit log.

## 7.2 Learning Update

Incorrect predictions update the Learning Intelligence:

1. The evaluation result becomes an outcome observation for the `OutcomeLearningEngine`.
2. A new `LearnedPattern` is created or updated if the error pattern is recurrent.
3. The `RefinedRecommendation` for the prediction type is updated.
4. The `ConfidenceModel` factors are recalibrated.

## 7.3 Historical Correctness

Historical predictions are **never modified** after evaluation. The record shows:

```json
{
  "prediction_id": "pred_abc123",
  "output": {"predicted_completion_hours": 72, "confidence": 0.72},
  "actual": {"actual_completion_hours": 91},
  "error": 19,
  "error_pct": 0.26,
  "evaluated_at": "2026-07-24T12:00:00Z",
  "learning_update": {"pattern_id": "pat_456", "outcome": "underestimated_duration"}
}
```

This preserves the complete history of what was predicted vs. what happened, enabling:
- Accuracy tracking per prediction type.
- Systematic bias detection (is the engine systematically over- or under-estimating?).
- Confidence calibration improvement.

## 7.4 Confidence Recalibration

When a prediction is evaluated, the confidence model is recalibrated:

1. The prediction's confidence (e.g., 0.72) is compared to the outcome correctness (correct = 1.0, incorrect = 0.0).
2. A `calibration_delta` is computed: `delta = outcome_correctness - prediction_confidence`.
3. If `|delta| > calibration_threshold` (configurable, default: 0.20), the confidence model factors are adjusted:
   - `consistency` factor is adjusted by `learning_rate × delta` (configurable, default: 0.10).
   - `sample_size` factor weight is increased by `learning_rate × |delta|`.
4. The calibration adjustment is recorded as a `ConfidenceCalibration` artifact.

---

# 8. Engineering Rules

## 8.1 The Rules

Every engineer and AI agent building predictive capabilities in SHUNYA must follow these rules:

### Rule P1: Predictions never modify canonical state.

A prediction engine must never call `ExecutionService.transition()`, `AwarenessEngine.ingest()`, or any state-mutating method. Predictions are read-only intelligence.

### Rule P2: Predictions are derived intelligence.

Predictions are stored in `PredictionMemory` (ring buffer) and `LearningMemory`, never in canonical entity stores. A prediction is always recomputable from its input snapshot.

### Rule P3: Predictions must be reproducible.

Given the same input snapshot (recorded at creation time), the same prediction engine must produce the same output. This means prediction engines must be deterministic functions with no external dependencies.

### Rule P4: Predictions are versioned.

Every prediction has a `version` field that increments on revision. The version is included in the output so consumers can distinguish stale predictions from current ones.

### Rule P5: Predictions are timestamped.

Every prediction records its `created_at` and `valid_until` timestamps. Consumers must check `valid_until` before using a prediction.

### Rule P6: Predictions are evidence-traceable.

Every prediction must include `evidence_traces` linking to the specific state, patterns, and learning artifacts that produced it.

### Rule P7: Predictions declare assumptions.

Every prediction must include an `assumptions` field documenting the conditions under which the prediction is valid. If those conditions change, the prediction may be invalidated.

### Rule P8: Predictions never hardcode time horizons.

Time horizons are always configurable parameters, never hardcoded constants. Defaults must be documented.

### Rule P9: Predictions never depend on external state.

No prediction engine may call external APIs, read files, or depend on environment variables for computation. All dependencies must be in-process SHUNYA modules.

### Rule P10: Predictions never replace Governance.

A prediction cannot override a governance decision. Governance is about what should happen. Predictions are about what will happen. They are distinct concerns.

## 8.2 Module Separation

Predictions must live in a dedicated `app/prediction/` module. The module:

- Imports from intelligence modules (read-only).
- Never imports into intelligence modules.
- Exposes a `PredictionEngine` facade with the same singleton pattern as other engines.
- Stores prediction artifacts in `PredictionMemory` (ring buffer).

---

# 9. Extension Points

## 9.1 Executive Intelligence

**Attachment point:** `app/prediction/` → Portfolio-level aggregation of per-execution predictions.

**Design intent:** Aggregate all active predictions across a tenant into executive summaries:
- "Your portfolio has 12 at-risk executions. 8 are predicted to recover, 3 are predicted to fail, 1 is uncertain."
- "Predicted workload peak on Friday. Recommended: defer 2 non-critical executions."

## 9.2 Optimization

**Attachment point:** `app/prediction/` → Scenario comparison → optimal path recommendation.

**Design intent:** Given a set of possible actions and their predicted outcomes, recommend the optimal action sequence. Optimization is prediction + search, not prediction alone.

## 9.3 Scheduling

**Attachment point:** `app/prediction/` → Workload Forecast → capacity-aware scheduling.

**Design intent:** Use workload and capacity forecasts to recommend start times for new executions that minimize overall portfolio risk.

## 9.4 Autonomous Planning

**Attachment point:** `app/prediction/` → Recommendation Forecast → Planner Engine feedback.

**Design intent:** Predict the outcome of proposed plans before governance review. If a plan's predicted outcome is poor, suggest modifications to the planner before governance submission.

## 9.5 Human Operating System

**Attachment point:** `app/prediction/` → Capacity Forecast → `app/organizational/` role assignments.

**Design intent:** Predict workload against human capacity. Recommend role re-assignments or delegation before overload occurs.

---

# Appendix A: Prediction Category Reference

| `prediction_type` | Output Shape | Horizon Unit | Time-Sensitive |
|---|---|---|---|
| `completion` | `{predicted_at, optimistic_at, pessimistic_at}` | hours | Yes |
| `delay` | `{delay_probability, expected_delay_hours}` | hours | Yes |
| `risk_trajectory` | `{risk_at_horizon, direction, key_factors}` | hours | No |
| `capacity` | `{utilization_pct, bottleneck_resource}` | hours | Yes |
| `workload` | `{peak_count, peak_at, distribution}` | hours | Yes |
| `bottleneck` | `{node_id, expected_block_duration}` | hours | No |
| `dependency` | `{satisfaction_probability, critical_chain}` | hours | No |
| `opportunity` | `{opportunity_type, probability, expected_impact}` | days | No |
| `recommendation_outcome` | `{action, predicted_outcome, confidence}` | hours | Yes |

---

# Appendix B: Confidence Factor Reference

| Factor | Symbol | Weight | Implementation |
|---|---|---|---|
| Sample Size | `S` | 0.25 | `min(1.0, count / 50)` |
| Pattern Consistency | `C` | 0.25 | `1.0 - abs(rate - 0.5) × 2` |
| Input Freshness | `F` | 0.20 | `max(0.1, 1.0 - age_hours / freshness_hours)` |
| Evidence Quality | `E` | 0.15 | `quality_score from EvidenceValidationResult` |
| Temporal Proximity | `T` | 0.15 | `1.0 - (horizon_hours / max_horizon_hours)` |

**Formula:** `confidence = S × 0.25 + C × 0.25 + F × 0.20 + E × 0.15 + T × 0.15`

---

# Appendix C: Architectural Decision Records

## ADR-P1: Why Predictions Are Derived Intelligence, Not Canonical State

**Problem:** Predictions could be stored as canonical entities alongside executions. This would make them persistent and queryable without recomputation.

**Alternatives considered:**
1. Store predictions as canonical `Prediction` entities in `app/execution/`.
2. Store predictions as `LearningArtifact` entries in Learning Memory.
3. Store predictions as temporary in-memory objects.

**Decision:** Predictions are `LearningArtifact` entries in Learning Memory. They are derived intelligence, not canonical state.

**Consequences:**
- Positive: No new canonical entities needed. Learning Memory already supports versioning, supersession, and time-to-live.
- Positive: Learning Memory's ring buffer provides natural expiration.
- Positive: Predictions are automatically included in learning queries and explainability.
- Negative: Predictions are ephemeral (ring buffer eviction). Long-term prediction history must be explicitly exported.

**Trade-offs:** Predictions could be lost on ring buffer overflow. Mitigated by configurable capacity and explicit audit log.

## ADR-P2: Why 5-Factor Confidence Decomposition

**Problem:** Confidence scores without decomposition are opaque. Users cannot understand why a prediction has 72% confidence vs. 68%.

**Alternatives considered:**
1. Single scalar confidence (opaque).
2. Confidence with 2 factors (sample size + consistency).
3. Confidence with 5 explicit factors (current approach).

**Decision:** 5 explicit factors with named weights, calibrated to max at known thresholds.

**Consequences:**
- Positive: Every confidence score is fully decomposable.
- Positive: Factors map directly to actionable improvements ("need more samples," "data is stale").
- Positive: Calibration adjustments can target specific factors.
- Negative: Slightly more computation per prediction. Mitigated: trivial arithmetic.

## ADR-P3: Why Prediction Refusal with Structured Reasons

**Problem:** When a prediction cannot be made (insufficient data, terminal state), returning an opaque error or null is unhelpful.

**Alternatives considered:**
1. Return `null` or empty response.
2. Return error with generic message.
3. Return structured refusal with reason, detail, and remediation guidance.

**Decision:** Return structured refusal with `reason`, `detail`, `available_samples`, `minimum_required`, and suggested remediation.

**Consequences:**
- Positive: Consumers can understand why a prediction was not made.
- Positive: Consumers can take action to enable the prediction (collect more data, wait for non-terminal state).
- Positive: Refusal reasons can be aggregated for system health monitoring.

---

## Document Metadata

- **Title:** Prediction Philosophy v1.0
- **Status:** Draft — awaiting review
- **Addendum to:** SHUNYA Architecture Specification v1.0
- **Prediction categories defined:** 9
- **Confidence factors defined:** 5
- **Engineering rules defined:** 10
- **Extension points identified:** 5
- **ADRs recorded:** 3
- **Last updated:** 2026-07-21

---

*This document defines the philosophical and architectural foundation for all predictive capabilities in SHUNYA. No prediction engine shall be built until this document is reviewed, approved, and incorporated as an official addendum to SHUNYA Architecture Specification v1.0.*
