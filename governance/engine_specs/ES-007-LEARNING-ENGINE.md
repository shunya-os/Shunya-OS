# ES-007: Learning Engine

**Status:** Draft
**Phase:** Phase 2 (Learning Layer)
**Layer:** Learning
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters the Learning Engine

- **Verified observations** — validated, confidence-scored records of what actually happened, from the Observer Engine (ES-006). Include expected vs actual comparisons, deviation reports, and anomaly reports.
- **Learning signals** — structured observations packaged for learning consumption by the Observer Engine. Pre-extracted insights ready for pattern analysis.
- **Execution assessments** — quality scores for each execution from the Observer Engine: delivery accuracy, timeliness, cost adherence, resource efficiency.
- **Evidence bundles** — packaged evidence supporting each observation, from the Observer Engine.
- **Historical outcomes** — past observations and their resulting knowledge changes, retrieved from the Knowledge Engine (ES-002) for longitudinal analysis.
- **Knowledge references** — current facts, policies, and patterns from the Knowledge Engine that the learning engine may propose updates to.
- **Policies** — active governance policies from the Governance Engine (ES-001) that constrain what learning recommendations are permissible.
- **Context** — workspace context: tenant, actor, purpose, correlation ID, trace ID.

### What Leaves the Learning Engine

- **Learning recommendations** — structured proposals for improvement: what to change, why, and with what expected impact.
- **Knowledge update proposals** — proposed new facts, modified facts, or superseded facts for the Knowledge Engine, with supporting evidence and confidence scores.
- **Policy improvement proposals** — proposed changes to governance policies for the Governance Engine, with rationale and expected impact analysis.
- **Confidence calibration updates** — revised confidence scores for the Knowledge Engine, reflecting observed outcome accuracy.
- **Pattern library** — catalogued recurring patterns (success patterns, failure modes, behavioral trends) with frequency, confidence, and impact scores.
- **Outcome models** — predictive models that estimate the likelihood of success for different action types, channels, and contexts.
- **Performance insights** — aggregated performance metrics across observations: success rates, improvement trends, degradation signals.
- **Learning package** — the complete learning result packaged for downstream consumption (Knowledge Engine, Governance Engine).

### What Intelligence Is Compounded

The Learning Engine is the **compounding mechanism itself**. It is the engine that closes the loop: observe → learn → improve → observe again → learn more → improve further. Every learning cycle makes the next one more effective because:

- The pattern library grows richer with each observation
- Confidence calibration becomes more precise
- Outcome models become more predictive
- The system knows what works, what doesn't, and why

The compounding mechanism is **recursive improvement**: the Learning Engine learns how to learn better. It tracks which learning recommendations were accepted, which were rejected, and which led to actual improvement. Over time, it learns to prioritize recommendation types that have a higher acceptance rate and a higher impact.

### Which Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Knowledge Engine | Consumes knowledge update proposals and confidence calibrations | **High** — knowledge evolution depends on learning |
| Governance Engine | Consumes policy improvement proposals | **Medium** — policies can be updated manually |
| Reasoning Engine | Consumes improved confidence models and patterns | **Medium** — reasoning quality improves with learning |
| Planner Engine | Consumes improved outcome models for planning | **Low** — planning quality improves with learning |

### What Fails If It Becomes Unavailable

- **The compounding loop stops** — the system can observe and act but cannot improve
- **Knowledge does not evolve** — facts remain static, confidence scores never calibrate to actual outcomes
- **Policies never improve** — suboptimal policies continue indefinitely
- **Patterns go undetected** — recurring successes and failures are never identified
- **The system plateaus** — initial performance is maintained but never improved

---

## Section 1 — Mission

### Purpose of the Learning Inside SHUNYA

The Learning Engine transforms verified observations into long-term improvement. It is the engine that closes the Compounding Intelligence Loop. The Learning Engine does not modify knowledge directly, bypass governance, rewrite history, fabricate learning, execute actions, or approve changes. It analyzes observations, discovers patterns, evaluates outcomes, and produces recommendations for improvement that are validated through the same governance process as any other change.

The canonical lifecycle (SHUNYA System Flow §2) positions Learning after Observation and before Continuous Improvement:

```
Observation → Knowledge Update → [Learning] → Continuous Improvement
```

### The Learning Engine SHALL

- Analyze verified observations to identify what worked, what didn't, and why
- Identify recurring patterns across observations (success patterns, failure modes, behavioral trends)
- Measure outcome quality: accuracy, timeliness, cost adherence, user satisfaction
- Recommend knowledge updates: new facts, modified facts, superseded facts
- Recommend policy improvements: more effective policies, retired ineffective policies
- Calibrate confidence scores based on observed outcome accuracy
- Improve future reasoning by refining confidence models and outcome predictions
- Improve future planning by refining outcome models and resource estimates

### The Learning Engine SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never modify knowledge directly | Would violate Layer Boundaries | Knowledge Engine (writes go through its API) |
| Never bypass governance | Would violate Constitutional Principle | Governance Engine (learning proposals must be validated) |
| Never rewrite history | Would violate Immutability | (observations and evidence are immutable) |
| Never fabricate learning | Would violate Explainable Decisions | (learning must be grounded in observations) |
| Never execute actions | Would violate Separation of Responsibilities | Executor Engine |
| Never approve changes | Would violate Governance Before Execution | Governance Engine |
| Never mutate evidence | Would violate Architectural Invariant | Core Models §11, Invariant 1 |
| Never learn from unverified observations | Would violate Evidence-Driven Engineering | Engineering Constitution Article 2 |

---

## Section 2 — Inputs

All inputs conform to the canonical models defined in SHUNYA Core Models and the output contracts of upstream engines.

### Input Contract

```
LearningInput:
  verified_observations: VerifiedObservation[]  — From ES-006. Validated, confidence-scored
                                                  records of what happened.
  learning_signals: LearningSignal[]            — From ES-006. Pre-extracted insights ready
                                                  for pattern analysis.
  execution_assessments: ExecutionAssessment[]  — From ES-006. Quality scores per execution.
  evidence_bundles: EvidenceBundle[]            — From ES-006. Packaged evidence per observation.
  historical_outcomes: OutcomeRecord[]          — From ES-002. Past observations and their
                                                  resulting knowledge changes.
  knowledge_refs: KnowledgeRef[]                — From ES-002. Current facts, policies, patterns
                                                  that may be updated.
  policies: Policy[]                            — From ES-001. Active governance policies
                                                  constraining learning recommendations.
  context: WorkspaceContext                     — Tenant, actor, purpose, correlation ID, trace ID.
  request_metadata: RequestInfo                 — Correlation ID, trace ID, tenant ID.
```

### Input Sources

| Input | Source | Retrieval Method |
|-------|--------|-----------------|
| Verified observations | Observer Engine (ES-006) | Delivered after observation completion |
| Learning signals | Observer Engine (ES-006) | Embedded in observation package |
| Execution assessments | Observer Engine (ES-006) | Embedded in observation package |
| Historical outcomes | Knowledge Engine (ES-002) | Temporal retrieval by similar context |
| Knowledge references | Knowledge Engine (ES-002) | Current active facts and policies |
| Policies | Governance Engine (ES-001) | In-memory policy registry snapshot |
| Context | Context Fusion (Phase 10) | Propagated through request lifecycle |

### Input Validation

| Field | Constraint | Rejection |
|-------|-----------|-----------|
| `verified_observations` | Non-empty (at least one observation per cycle) | `NO_OBSERVATIONS` — nothing to learn from |
| `learning_signals[].confidence` | Must be > 0.0 (canonical scale) | `ZERO_CONFIDENCE` — signal cannot be trusted |
| `historical_outcomes.context` | Must match current tenant | `TENANT_MISMATCH` |
| `policies` | May be empty (unconstrained learning) | Warning — recommendations may violate unknown policies |

---

## Section 3 — Outputs

All outputs conform to the canonical models defined in SHUNYA Core Models.

### Output Contract

```
LearningOutput:
  learning_recommendations: LearningRecommendation[]  — Proposals for improvement.
  knowledge_proposals: KnowledgeProposal[]            — Proposed fact updates for ES-002.
  policy_proposals: PolicyProposal[]                  — Proposed policy changes for ES-001.
  confidence_calibrations: ConfidenceCalibration[]    — Revised confidence scores for ES-002.
  pattern_library: Pattern[]                          — Catalogue of recurring patterns.
  outcome_models: OutcomeModel[]                      — Predictive models for planning.
  performance_insights: PerformanceInsight[]          — Aggregated performance metrics.
  learning_package: LearningPackage                   — Complete result for downstream.
  learning_metadata: LearningInfo                     — Engine version, algorithms used.
```

### Output Destinations

| Output | Destination | Format |
|--------|-------------|--------|
| Learning recommendations | Governance Engine (ES-001) | Structured proposals for governance validation |
| Knowledge proposals | Governance Engine (ES-001 via governance) | Proposed fact updates, validated before execution |
| Policy proposals | Governance Engine (ES-001) | Proposed policy changes, validated before activation |
| Confidence calibrations | Knowledge Engine (ES-002) | Revised confidence scores applied per Knowledge Engine rules |
| Pattern library | Knowledge Engine (ES-002) | Stored as knowledge facts for future reasoning |
| Outcome models | Planning Engine (ES-004) | Predictive models for plan optimization |
| Performance insights | Governance Engine, human review | Aggregated insights for system oversight |

### Output Guarantees

- **Every learning recommendation is evidence-based:** Every proposal includes a reference to the observations that support it.
- **Learning recommendations are proposals, not commands:** Every recommendation passes through governance validation before being applied.
- **No learning recommendation is applied without governance approval:** The Learning Engine proposes; the Governance Engine disposes.

---

## Section 4 — Learning Pipeline

### Canonical Stages

```
Learning Intake
     │
     ▼
Pattern Discovery
     │
     ▼
Correlation Analysis
     │
     ▼
Outcome Evaluation
     │
     ▼
Confidence Calibration
     │
     ▼
Improvement Recommendation
     │
     ▼
Knowledge Proposal
     │
     ▼
Governance Review Package
     │
     ▼
Continuous Learning Archive
```

### Stage Definitions

| Stage | Purpose | Inputs | Outputs | Failure Condition |
|-------|---------|--------|---------|-------------------|
| **Learning Intake** | Receive and validate observations and learning signals | Verified observations, learning signals, historical outcomes | Validated intake with matched historical context | No observations to process |
| **Pattern Discovery** | Identify recurring patterns across observations: success patterns, failure modes, trends | Validated intake, historical patterns | Discovered patterns with frequency and confidence | Insufficient observations for pattern discovery |
| **Correlation Analysis** | Correlate observations with context, action types, channels, and other dimensions to identify causal relationships | Patterns, observations, context | Correlated insights with attribution strength | Confounding variables prevent clear correlation |
| **Outcome Evaluation** | Evaluate the quality of outcomes: did the system achieve its objectives? | Correlated insights, expected outcomes | Outcome quality scores with trend analysis | Objectives not measurable |
| **Confidence Calibration** | Adjust confidence scores based on observed accuracy: overconfident conclusions are reduced, underconfident ones are increased | Outcome evaluations, current confidence models | Calibrated confidence scores | Insufficient outcome data for calibration |
| **Improvement Recommendation** | Generate specific, actionable improvement recommendations | Confidence calibrations, patterns, correlations | Prioritized improvement recommendations | No actionable improvements identified |
| **Knowledge Proposal** | Package recommendations as concrete knowledge update proposals for the Knowledge Engine | Improvement recommendations, current knowledge state | KnowledgeProposal[] with evidence and confidence | Proposal conflicts with existing knowledge |
| **Governance Review Package** | Package all proposals for governance validation | All proposals, evidence, reasoning | Governance-ready learning package | Package too large |
| **Continuous Learning Archive** | Archive learning outputs for future analysis and longitudinal tracking | Complete learning package | Archived learning records | Archive failure (non-critical) |

---

## Section 5 — Learning Types

| Learning Type | Description | When Used | Example |
|---------------|-------------|-----------|---------|
| **Supervised** | Learning from labeled observations where the expected outcome is known. Compare actual to expected, adjust models accordingly. | Well-understood domains with clear success criteria | "Delivery success rate dropped from 95% to 80%. Identify the root cause." |
| **Reinforcement-inspired** | Learning from the cumulative reward signal across multiple actions. Optimize for long-term outcome, not individual action success. | Sequential decision-making, multi-step workflows | "Which channel sequence produces the highest conversion rate over 30 days?" |
| **Rule refinement** | Adjusting the parameters of deterministic rules based on observed outcomes. Threshold tuning, policy parameter adjustment. | Policy-based systems, governance rules | "The lead time warning threshold of 14 days is too conservative. Adjust to 7 days based on observed success rates." |
| **Pattern learning** | Discovering new patterns in observations without pre-defined categories. Unsupervised pattern discovery. | Novel situations, emerging behaviors | "A new failure mode is appearing in weekend deliveries. Create a new anomaly pattern." |
| **Statistical** | Applying statistical methods to observation data: trend analysis, regression, hypothesis testing. | Quantitative performance analysis | "Is the improvement in delivery time statistically significant?" |
| **Temporal** | Learning from time-series observation data: periodicity, trends, seasonality, drift detection. | Time-dependent processes, recurring cycles | "Delivery success rate shows a weekly pattern. Adjust expectations per day of week." |
| **Comparative** | Learning by comparing outcomes across different contexts, channels, or strategies. | A/B comparison, strategy evaluation | "WhatsApp delivery has 95% success rate vs Telegram's 88%. Recommend prioritizing WhatsApp." |
| **Human-guided** | Learning from human feedback, corrections, and annotations. | When automated learning is insufficient or needs validation | "Human reviewer corrected 15 false positive anomaly detections. Adjust anomaly detection model." |

---

## Section 6 — Pattern Model

### Pattern Record

```
Pattern:
  id: string                          — Unique pattern identifier
  name: string                        — Human-readable pattern name
  description: string                 — What this pattern represents
  pattern_type: string                — "success" | "failure" | "trend" | "anomaly" | "behavior"
  frequency: int                      — Number of observations matching this pattern
  frequency_trend: string             — "increasing" | "stable" | "decreasing" | "unknown"
  confidence: float                   — Confidence in this pattern's existence (canonical 0.0–1.0)
  impact: float                       — Estimated impact score (0.0–1.0)
  scope: PatternScope                — Where this pattern applies
  recurrence: Recurrence              — How often this pattern recurs
  evidence: Evidence[]                — Observations supporting this pattern
  first_observed: datetime            — When this pattern was first detected
  last_observed: datetime             — When this pattern was last detected
  status: string                      — "active" | "stale" | "superseded" | "archived"
```

### PatternScope

```
PatternScope:
  domains: string[]                   — Domains this pattern applies to
  channels: string[]                  — Channels this pattern applies to
  action_types: string[]              — Action types this pattern applies to
  tenant_ids: int[]                   — Tenants this pattern applies to (empty = all)
  context_tags: string[]              — Context tags this pattern applies to
```

### Recurrence

```
Recurrence:
  type: string                        — "continuous" | "periodic" | "sporadic" | "one_time"
  period: string | null               — For periodic: "daily" | "weekly" | "monthly"
  confidence: float                   — Confidence in recurrence pattern
  last_occurrence: datetime           — When this pattern last occurred
  predicted_next: datetime | null     — Predicted next occurrence (if periodic)
```

---

## Section 7 — Knowledge Evolution

### Knowledge Proposal Lifecycle

```
Proposed → Review → Approved → Applied → Verified → Superseded
              ↘          ↘
           Rejected    Rolled Back
```

| State | Meaning |
|-------|---------|
| **Proposed** | Learning Engine has generated a knowledge update proposal |
| **Review** | Proposal is under governance validation |
| **Approved** | Governance has approved the proposal |
| **Applied** | Knowledge Engine has applied the update (new fact version created) |
| **Verified** | Post-application observation confirms the update improved outcomes |
| **Superseded** | A newer learning cycle produced a better update |
| **Rejected** | Governance rejected the proposal |
| **Rolled Back** | Applied but later reverted due to negative outcomes |

### Versioning

All knowledge updates follow the Immutable Knowledge Store versioning model (ES-002 §15):

- A knowledge proposal creates a new version of the affected fact
- The previous version is marked as superseded
- The learning proposal references the evidence that motivated the change
- The confidence of the new version reflects the learning engine's confidence in the proposal

### Confidence Adjustment

Confidence calibration adjusts the confidence score of facts based on observed outcome accuracy:

```
new_confidence = old_confidence + (outcome_accuracy - old_confidence) × learning_rate
```

Where:
- `outcome_accuracy` = 1.0 if the outcome matched the confidence prediction, 0.0 if it did not
- `learning_rate` = a configurable factor controlling how quickly confidence adapts (default: 0.1)

### Retention

- Learning proposals are retained for 90 days in active storage
- Applied proposals are retained permanently (as part of the fact version history)
- Rejected proposals are retained for 30 days for analysis, then archived
- The pattern library is retained indefinitely (patterns become stale but are not deleted)

### Rollback Support

Every knowledge proposal includes a rollback plan:

- What fact keys are affected
- What the previous version was
- How to revert (supersede with the previous version)
- What evidence supports the rollback

---

## Section 8 — Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Insufficient observations | Too few observations to identify meaningful patterns | Pattern Discovery stage | Cannot generate recommendations | Return "insufficient data" with minimum observation count required |
| Conflicting patterns | Two patterns suggest contradictory improvements | Correlation Analysis stage | Learning recommendations are ambiguous | Flag conflict for human review; return both patterns with confidence scores |
| Low confidence | Patterns have low statistical significance | Pattern Discovery stage | Recommendations are low-confidence | Return recommendations with low confidence; do not auto-apply |
| Overfitting | Learning model fits noise instead of signal | Cross-validation against held-out observations | Recommendations that don't generalize | Reduce model complexity; increase minimum observation threshold |
| False learning | Spurious correlation interpreted as causation | Post-application outcome evaluation | Knowledge update produces negative outcomes | Roll back the update; flag the false learning pattern |
| Concept drift | Previously valid patterns no longer apply | Pattern staleness detection | Outdated recommendations | Mark stale patterns as "superseded"; trigger re-discovery |
| Learning backlog | More observations than the Learning Engine can process | Queue depth monitoring | Learning latency increases; real-time improvement delayed | Scale learning instances; prioritize high-impact observations |

---

## Section 9 — Interaction Matrix

| Layer / Engine | Reads | Writes | Events Published | Events Consumed |
|----------------|-------|--------|-----------------|-----------------|
| **Observer Engine** (ES-006) | Verified observations, learning signals | — | — | `observation.completed` |
| **Knowledge Engine** (ES-002) | Current facts, historical outcomes, confidence models | Knowledge proposals (via governance) | `learning.recommendation.proposed` | — |
| **Governance Engine** (ES-001) | Policies | Policy proposals (via governance) | `learning.recommendation.proposed` | — |
| **Reasoning Engine** (ES-003) | Current confidence models | — | — | `learning.confidence.updated` |
| **Planner Engine** (ES-004) | Outcome models | — | — | `learning.outcome.model.updated` |
| **Context Fusion** (Phase 10) | Workspace context | — | — | — |

### Dependencies

| Dependency | Type | Criticality |
|------------|------|-------------|
| Observer Engine (ES-006) | Input — verified observations | **Critical** — cannot learn without observations |
| Knowledge Engine (ES-002) | Read/Write — facts, historical outcomes | **High** — cannot propose updates without current state |
| Governance Engine (ES-001) | Read/Write — policies, proposal validation | **High** — proposals must be validated |
| Reasoning Engine (ES-003) | Read — confidence models | **Medium** — can calibrate without reading current models |

### Ownership

- The Learning Engine **owns** pattern discovery, correlation analysis, outcome evaluation, confidence calibration, and improvement recommendations.
- It **does not own** observations, knowledge facts, policies, or governance decisions.
- It **shares ownership** of confidence scores with the Knowledge Engine (base confidence) and the Reasoning Engine (reasoning confidence).

---

## Section 10 — Performance

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| **Learning latency (batch)** | < 5 minutes per batch | Per learning cycle (batch of up to 1000 observations) |
| **Learning latency (incremental)** | < 30 seconds per observation | Per single observation processed incrementally |
| **Pattern discovery** | < 1 minute per 10,000 observations | For pattern discovery across historical data |
| **Confidence calibration** | < 10 seconds per 1000 calibration events | Per calibration cycle |
| **Concurrent learning cycles** | 10 / instance | Per Learning Engine instance |
| **Observation processing rate** | 1000 / minute | Per instance (batch) |
| **Storage growth** | ~10KB per learning recommendation | Recommendation + evidence + metadata |

### Batch vs Incremental Learning

| Mode | Description | Latency | When Used |
|------|-------------|---------|-----------|
| **Batch** | Process accumulated observations in scheduled cycles | 1–5 minutes | Default for non-time-critical learning |
| **Incremental** | Process each observation as it arrives | < 30 seconds | For time-critical adjustments (confidence calibration, anomaly confirmation) |

### Scaling

- The Learning Engine supports horizontal scaling for batch processing (multiple instances process observation partitions in parallel).
- Incremental learning is per-instance (each instance processes its own observation stream).
- The pattern library is shared across instances via the Knowledge Engine.

---

## Section 11 — Security

### Auditability

- Every learning recommendation is auditable: recommendation ID, source observations, proposed changes, supporting evidence, confidence.
- Audit records are stored in the Knowledge Engine (ES-002) as immutable evidence records.
- Every accepted and rejected recommendation is recorded.

### Privacy

- Learning recommendations are based on aggregate patterns, not individual observations. No personal data is included in learning recommendations unless essential to the recommendation.
- Observation data used for learning is accessed through the Observer Engine's privacy filters.
- The Learning Engine does not cache personal data between learning cycles.

### Tenant Isolation

- All learning is scoped to the requesting tenant's `tenant_id`.
- Patterns, models, and recommendations are per-tenant.
- Cross-tenant learning (federated learning) is a future extension (Section 16) and requires explicit authorization.

### Data Governance

- Learning recommendations that modify knowledge facts are subject to the same data governance rules as any other knowledge mutation.
- Personal data is never included in pattern descriptions or recommendation rationales.
- Retention policies apply to learning outputs: 90 days active, 7 years archived.

---

## Section 12 — Observability

### Metrics

| Metric | Type | Unit | Target |
|--------|------|------|--------|
| `learning.cycles_total` | Counter | cycles | Per minute |
| `learning.observations_processed` | Counter | observations | Per minute |
| `learning.patterns_discovered` | Counter | patterns | Per cycle |
| `learning.recommendations_proposed` | Counter | recommendations | Per cycle |
| `learning.recommendations_accepted` | Counter | recommendations | Per cycle (by governance acceptance) |
| `learning.recommendations_rejected` | Counter | recommendations | Per cycle (by governance rejection) |
| `learning.confidence_calibrations` | Counter | calibrations | Per cycle |
| `learning.latency_batch_p50` | Histogram | ms | < 5 minutes |
| `learning.latency_incremental_p50` | Histogram | ms | < 30 seconds |
| `learning.patterns_active` | Gauge | patterns | Current active pattern count |
| `learning.patterns_stale` | Gauge | patterns | Current stale pattern count |
| `learning.backlog_depth` | Gauge | observations | Current observation backlog |

### Tracing

- **Span: `learning.cycle`** — Full learning lifecycle
  - Child span: `learning.pattern_discovery`
  - Child span: `learning.correlation_analysis`
  - Child span: `learning.outcome_evaluation`
  - Child span: `learning.confidence_calibration`
  - Child span: `learning.recommendation_generation`
- Trace context propagated from caller (Observer Engine or scheduled trigger)

### Learning Quality Metrics

| Metric | Purpose |
|--------|---------|
| **Recommendation acceptance rate** | Fraction of learning recommendations accepted by governance |
| **Recommendation impact** | Measurable improvement after applying accepted recommendations |
| **False learning rate** | Fraction of applied recommendations that were later rolled back |
| **Pattern accuracy** | How well discovered patterns predict future observations |
| **Confidence calibration error** | Average difference between predicted confidence and actual outcome accuracy |
| **Learning coverage** | Fraction of observations that result in a learning signal |

---

## Section 13 — Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Analyze observations for improvement | 5 (Learning Layer) — Analyzes Observer data, identifies patterns, improvements, failure modes | SHUNYA_ARCHITECTURE.md §5 |
| Feed improvements back into Knowledge | 5 (Learning Layer) — Updates Knowledge with new facts | SHUNYA_ARCHITECTURE.md §5 |
| Improve Reasoning models | 5 (Learning Layer) — Improves Reasoning models | SHUNYA_ARCHITECTURE.md §5 |
| Never access live credentials or payment data | 5 (Learning Layer) — No access to live credentials or payment data | SHUNYA_ARCHITECTURE.md §5 |
| Never mutate evidence | 7 (Learning never mutates evidence) | SHUNYA Core Models §11, Invariant 7 |
| Learning proposals go through governance | 4 (Learning never bypasses governance) | SHUNYA System Flow §14, Invariant 4 |
| Evidence precedes learning | 3 (Evidence precedes learning) | SHUNYA System Flow §14, Invariant 3 |
| Every learning signal is traceable to observations | 4.2 Every Decision Is Traceable | SHUNYA_ENGINEERING_CONSTITUTION.md §4.2 |
| Tenant isolation on all learning data | 9 (Multi-Tenant Behaviour) | SHUNYA System Flow §9 |
| Continuous improvement is the goal | 2.7 Continuous Improvement — Every completed workflow makes both better | SHUNYA_ARCHITECTURE.md §2.7 |

---

## Section 14 — Layer Responsibilities

### The Learning Engine SHALL

- Analyze verified observations to identify what worked, what didn't, and why
- Discover recurring patterns across observations (success, failure, trends, anomalies)
- Correlate observations with context, action types, channels, and other dimensions
- Evaluate outcome quality against expected outcomes
- Calibrate confidence scores based on observed accuracy
- Generate specific, actionable improvement recommendations
- Package all recommendations as governance-validated proposals
- Respect tenant isolation on all learning data
- Archive learning outputs for longitudinal analysis

### The Learning Engine SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never modify knowledge directly | Would violate Layer Boundaries | Knowledge Engine |
| Never bypass governance | Would violate Constitutional Principle | Governance Engine |
| Never rewrite history | Would violate Immutability | (observations and evidence are immutable) |
| Never fabricate learning | Would violate Explainable Decisions | (learning must be grounded in observations) |
| Never execute actions | Would violate Separation of Responsibilities | Executor Engine |
| Never approve changes | Would violate Governance Before Execution | Governance Engine |
| Never mutate evidence | Would violate Architectural Invariant | Core Models §11, Invariant 1 |
| Never learn from unverified observations | Would violate Evidence-Driven Engineering | Engineering Constitution Article 2 |
| Never access live credentials or payment data | Would violate Constitutional Principle | SHUNYA_ARCHITECTURE.md §5 (Learning Layer) |
| Never cache personal data between cycles | Would violate Privacy | (per Phase 4 privacy requirements) |

---

## Section 15 — Complexity Analysis

### CPU Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Learning intake | O(O) | O = observations in batch |
| Pattern discovery | O(O × P) | O = observations, P = pattern dimensions |
| Correlation analysis | O(O × C²) | O = observations, C = correlation dimensions |
| Outcome evaluation | O(O × M) | O = observations, M = measurable dimensions |
| Confidence calibration | O(F) | F = facts to calibrate |
| Recommendation generation | O(Pr × Im) | Pr = patterns, Im = impact evaluation |
| Knowledge proposal | O(K) | K = proposals to generate |
| Governance packaging | O(L) | L = learning package size |

### Memory Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Observation batch buffer | O(O × avg_observation_size) | O = observations in batch |
| Pattern library (in memory) | O(P × avg_pattern_size) | P = active patterns, LRU eviction |
| Correlation matrix | O(C²) | C = correlation dimensions |
| Recommendation buffer | O(R) | R = pending recommendations |

### Pattern Growth

- Active patterns: bounded by pattern library size (configurable, default 10,000)
- Stale patterns: patterns not observed in 90 days are marked stale and moved to archival storage
- Pattern versioning: when a pattern is updated, the old version is superseded, not deleted

### Storage

- Learning recommendations: ~10KB each (recommendation + evidence + metadata)
- Pattern library: ~1KB per pattern (description + scope + recurrence + evidence references)
- Outcome models: ~100KB per model (model parameters + metadata)
- Archived learning records: retained per tenant retention policy (default: 7 years)

### Failure Isolation

- Each learning cycle is fully isolated. A failure in one cycle does not affect any other.
- Pattern discovery failure is isolated to that cycle. Previous patterns remain valid.
- Knowledge Engine unavailability: recommendations are queued for retry.
- Governance Engine unavailability: proposals are held until governance is available.

---

## Section 16 — Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 16.1 Federated Learning

Learning across tenant boundaries without sharing raw observations. Only aggregate pattern updates are shared. Each tenant's observation data remains private.

### 16.2 Cross-Workspace Learning

Learning patterns that span workspaces within the same tenant, identifying organization-wide trends and optimization opportunities.

### 16.3 Simulation-Driven Learning

Learning from simulated outcomes rather than only real observations. The Learning Engine proposes actions, simulations predict outcomes, and the Learning Engine learns from the simulation results — enabling faster iteration without waiting for real-world outcomes.

### 16.4 Adaptive Policy Learning

The Learning Engine autonomously proposes policy adjustments based on observed outcomes, within bounds defined by the Governance Engine. Policies become self-tuning without requiring human intervention for routine adjustments.

### 16.5 Autonomous Optimization

The Learning Engine identifies optimization opportunities across all layers — knowledge, reasoning, planning, execution, governance — and autonomously applies improvements within constitutional bounds.

### 16.6 Meta-Learning

The Learning Engine learns how to learn better. It tracks which learning strategies produce the most effective recommendations and adjusts its own learning algorithms accordingly.

### 16.7 Causal Learning

The Learning Engine moves beyond correlation to causation — identifying not just what patterns exist, but what causes them. Enables more precise interventions and more reliable predictions.

---

## Section 17 — References

| Document | Relationship |
|----------|-------------|
| **SHUNYA Constitution** (`SHUNYA_ARCHITECTURE.md`) | Supersedes this specification where constitutional principles conflict |
| **SHUNYA Core Models** (`/architecture/SHUNYA_CORE_MODELS.md`) | Defines canonical confidence model (§7), evidence model (§5), provenance model (§6) — all inherited by this specification |
| **SHUNYA System Flow** (`/architecture/SHUNYA_SYSTEM_FLOW.md`) | Defines pipeline position (§2), learning stage in lifecycle (§2), engine responsibilities (§3), failure behaviour (§7) — this specification's behavioral context |
| **SHUNYA Engineering Constitution** (`/governance/SHUNYA_ENGINEERING_CONSTITUTION.md`) | Article 2 (Evidence-Driven Engineering), Article 4 (Immutability), Article 8 (Divergence Protocol) — governs this specification |
| **ES-001: Governance Engine** (`/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md`) | Validates learning proposals before application |
| **ES-002: Knowledge Engine** (`/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md`) | Stores knowledge facts that learning proposes to update; stores patterns and models |
| **ES-003: Reasoning Engine** (`/governance/engine_specs/ES-003-REASONING-ENGINE.md`) | Consumes improved confidence models from learning |
| **ES-004: Planner Engine** (`/governance/engine_specs/ES-004-PLANNER-ENGINE.md`) | Consumes improved outcome models from learning |
| **ES-005: Executor Engine** (`/governance/engine_specs/ES-005-EXECUTOR-ENGINE.md`) | Provides execution outcomes (via Observer) that learning analyzes |
| **ES-006: Observer Engine** (`/governance/engine_specs/ES-006-OBSERVER-ENGINE.md`) | Provides verified observations and learning signals that are the Learning Engine's primary input |
| `app/shunya/observer_learning.py` | Current LearningLayer implementation (co-located with ObserverLayer, 318 lines total) — v2 with 5 hardcoded pattern types |
| `app/learning/__init__.py` | Phase 15 Closed Learning Loop (computation-only, 469 lines) — extensive state machine for learning targets, outcomes, attribution, evaluation |