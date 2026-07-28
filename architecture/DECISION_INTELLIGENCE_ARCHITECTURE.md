# Decision Intelligence Architecture

**Phase 12 — SHUNYA OS**
**Classification: Implementation Architecture**
**Status: PROPOSED**
**Version: 1.0**

---

## Preamble

### Authority

This document defines the implementation architecture for Decision Intelligence. It defines how SHUNYA chooses between multiple possible actions. It does NOT redefine constitutional concepts — it references them.

### First principles

1. **Execution changes reality. Decision determines how reality should be changed.**
2. **Decision sits between Prediction and Execution.** Every execution begins as a decision.
3. **Every decision is explainable.** A founder should always know why a decision was made, why another was not, what assumptions exist, what evidence supports it, and what uncertainty remains.
4. **Every decision is evidence-driven.** No decision exists without referenced evidence, knowledge, and predictions.
5. **Every decision is reversible.** Decisions can be revisited when new evidence arrives.

### Dependency chain position

```
Reality
  ↓
Perception
  ↓
Knowledge
  ↓
Reasoning
  ↓
Prediction
  ↓
DECISION (this architecture)
  ↓
Execution
  ↓
Reality
```

### Constitutional sources

| Document | What it provides | How this architecture references it |
|----------|-----------------|--------------------------------------|
| UNIVERSAL_ONTOLOGY.md | Action (§10), Event (§8), Commitment (§9), Evidence (§7), Object (§1) | Defines the constitutional types that decisions consume and produce |
| COGNITIVE_WORKSPACE_RUNTIME.md | Intent Pipeline (§4), Attention Engine (§2), Memory (§5), Event Bus (§9) | Defines how decisions integrate with cognition |
| ADAPTIVE_INTELLIGENCE_RUNTIME.md | Confidence Engine (§2), Policy Evolution (§7), Human Governance (§13), Calibration (§6) | Defines how decisions are evaluated and governed |
| UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md | Evidence Graph (§4), Temporal Graph (§5), Projections (§8) | Defines how decision data is stored and projected |
| UNIVERSAL_PERCEPTION_ARCHITECTURE.md | Observation Pipeline (§3), Attention Trigger (§6) | Defines how perception feeds decision signals |
| EXECUTION_INTELLIGENCE_ARCHITECTURE.md | Execution Object Model (§1), Execution Planner (§5), Execution Governance (§13) | Defines how decisions trigger execution |

---

## 1. Decision Object Model

### 1.1 Ontology mapping

The Decision Object Model derives from constitutional definitions in UNIVERSAL_ONTOLOGY.md §10 (Action), §8 (Event), §15 (Prediction), and §7 (Evidence).

| Ontology concept | Decision implementation | Relationship |
|------------------|------------------------|--------------|
| Action (§10) | Decision | A Decision is a choice about which Action to execute |
| Event (§8) | Decision Lifecycle Event | A change in decision state |
| Commitment (§9) | Decision Outcome | The result of a decision may be a commitment |
| Prediction (§15) | Decision Input | Decisions consume predictions |
| Evidence (§7) | Decision Evidence | Decisions reference supporting evidence |
| Object (§1) | Decision Identity | Every decision has a permanent identity |

### 1.2 Decision primitives

| Primitive | Definition | Constitutional source |
|-----------|------------|----------------------|
| **Decision** | A choice about which action to execute. The bridge between prediction and execution. | Action §10 |
| **Decision Candidate** | A potential decision that has been detected but not yet analysed | — |
| **Decision Context** | The circumstances, knowledge, and state surrounding a decision | Context §13 |
| **Decision Constraint** | A rule that limits which options are valid | Policy §16 |
| **Decision Objective** | A goal the decision should satisfy | — |
| **Decision Option** | A possible course of action being evaluated | Action §10 |
| **Decision Outcome** | The result of executing the chosen option | Event §8 (Outcome) |
| **Decision Confidence** | The estimated reliability of the decision recommendation | Confidence (Adaptive §2) |
| **Decision Identity** | A permanent, unique identifier for the decision | Identity §3 |
| **Decision Owner** | The entity responsible for making or approving the decision | Ownership §1.6 |
| **Decision Horizon** | The time period over which the decision's effects will be evaluated | Prediction §15 (Horizon) |

### 1.3 Decision structure

```
Decision {
  decision_id: Identity
  status: DecisionState
  context: DecisionContext
  objectives: List[Objective]
  constraints: List[Constraint]
  options: List[Option]
  evaluation: EvaluationResult
  recommendation: Option
  evidence: List[EvidenceRef]
  confidence: float
  owner: Identity
  horizon: TimeRange
  lifecycle: List[LifecycleEvent]
}
```

---

## 2. Decision Lifecycle

### 2.1 Canonical lifecycle

```
                    ┌──────────────┐
                    │   DETECTED   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   ANALYSED   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ ALTERNATIVES │
                    │   GENERATED  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   EVALUATED  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  PRIORITISED │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ RECOMMENDED  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │ APPROVED  │ │ REJECTED  │ │ DEFERRED  │
       └─────┬─────┘ └───────────┘ └─────┬─────┘
             │                           │
             ▼                           │
       ┌───────────┐                     │
       │ EXECUTED  │                     │
       └─────┬─────┘                     │
             │                           │
             ▼                           ▼
       ┌───────────┐             ┌──────────────┐
       │ OBSERVED  │             │   RETIRED    │
       └─────┬─────┘             └──────────────┘
             │
             ▼
       ┌───────────┐
       │  LEARNED  │
       └───────────┘
```

### 2.2 State definitions

| State | Definition | Entered from | Exits to |
|-------|------------|-------------|----------|
| **DETECTED** | A potential decision has been identified | Perception, Prediction | ANALYSED |
| **ANALYSED** | The decision context, objectives, and constraints have been resolved | DETECTED | ALTERNATIVES_GENERATED |
| **ALTERNATIVES_GENERATED** | Possible options have been created or discovered | ANALYSED | EVALUATED |
| **EVALUATED** | Options have been scored against objectives and constraints | ALTERNATIVES_GENERATED | PRIORITISED |
| **PRIORITISED** | Options have been ranked by overall score | EVALUATED | RECOMMENDED |
| **RECOMMENDED** | A single option has been selected as the recommendation | PRIORITISED | APPROVED, REJECTED, DEFERRED |
| **APPROVED** | The recommendation has been accepted by the decision authority | RECOMMENDED | EXECUTED |
| **REJECTED** | The recommendation has been declined | RECOMMENDED | RETIRED |
| **DEFERRED** | The decision has been postponed to a later time | RECOMMENDED | ANALYSED (re-entry), RETIRED |
| **EXECUTED** | The chosen option has been executed | APPROVED | OBSERVED |
| **OBSERVED** | The outcome of the execution has been observed | EXECUTED | LEARNED |
| **LEARNED** | Insights from the outcome have been fed back to learning systems | OBSERVED | RETIRED |
| **RETIRED** | The decision lifecycle is complete | Any terminal transition | (terminal) |

### 2.3 Lifecycle invariants

1. Every decision follows exactly one lifecycle.
2. A decision is in exactly one state at any time.
3. Decisions cannot skip states — every state transition is sequential.
4. DEFERRED decisions re-enter at ANALYSED (context is re-evaluated).
5. Every state transition is an event on the Decision Event Bus.

---

## 3. Decision Context Engine

### 3.1 Purpose

Every decision inherits context from the full constitutional stack. The Decision Context Engine ensures that decisions are made with complete awareness of their surroundings.

### 3.2 Context inheritance

| Context | Inherited from | Used for |
|---------|----------------|----------|
| **Identity** | The resolved identities relevant to the decision | Ownership, permission, audit |
| **Knowledge** | Knowledge Graph (§14 of Ontology) | Option evaluation, feasibility |
| **Relationships** | Relationship Graph (§5 of Ontology) | Impact analysis, stakeholder identification |
| **Memory** | Working Memory, Session Memory (CWR §5) | Recent context, urgency |
| **Execution state** | Active executions (Execution Intelligence §1) | Conflict detection, resource contention |
| **Timeline** | Object timelines (Ontology §12) | Temporal constraints, deadlines |
| **Workspace** | Current workspace context (CWR §8) | Priority, relevance |
| **Policy** | Policy hierarchy (Ontology §16) | Constraint generation, approval routing |
| **Goals** | Active goals from projects, commitments, and founder direction | Objective alignment |

### 3.3 Context resolution

```
Decision detected
  ↓
Resolve relevant identities
  ↓
Load knowledge about each identity
  ↓
Load relationships between identities
  ↓
Load current workspace context
  ↓
Load active policies
  ↓
Load active goals and commitments
  ↓
Load active executions (for conflict detection)
  ↓
Attach resolved context to decision
  ↓
Decision context ready for analysis
```

### 3.4 Context invariants

1. Context is resolved at decision detection time.
2. Context is immutable once attached to the decision — re-evaluation requires a new decision lifecycle.
3. If context cannot be fully resolved, the decision proceeds with partial context.
4. Partial context is flagged in the decision record.

---

## 4. Alternative Generation

### 4.1 Purpose

Alternative Generation creates the set of possible courses of action for a decision. It is the creative stage of decision intelligence.

### 4.2 Generation strategies

| Strategy | Description | When used |
|----------|-------------|-----------|
| **Single option** | Only one viable course of action exists | Routine decisions, constrained situations |
| **Multiple options** | Several distinct courses are possible | Most decisions |
| **Exploration** | Options include novel or untested approaches | Strategic decisions, innovation |
| **Safe alternatives** | Options are ranked by risk, with at least one low-risk option | High-stakes decisions |
| **Human alternatives** | Options are generated by the founder, not by the system | Founder-initiated decisions |

### 4.3 Option structure

```
Option {
  option_id: Identity
  description: string
  type: OptionType  (SINGLE, MULTIPLE, EXPLORATION, SAFE, HUMAN)
  actions: List[Action]
  expected_outcome: Prediction
  confidence: float
  evidence: List[EvidenceRef]
  assumptions: List[Assumption]
}
```

### 4.4 Generation rules

1. Every decision must have at least one option.
2. Options must be distinct — no two options may describe the same course of action.
3. Options must be feasible — every option must be executable within known constraints.
4. Options must be evidence-backed — every option must reference at least one piece of evidence.
5. When exploration is enabled, at least one option must be novel (not previously attempted).

---

## 5. Decision Evaluation

### 5.1 Purpose

Decision Evaluation scores each option against multiple dimensions. It is the analytical core of decision intelligence.

### 5.2 Evaluation dimensions

| Dimension | What it measures | Source | Weight |
|-----------|-----------------|--------|--------|
| **Benefit** | The expected positive impact of the option | Prediction Engine | Configurable |
| **Cost** | The expected resources required | Execution Planner | Configurable |
| **Risk** | The probability and impact of failure | Prediction Engine, Execution Risk | Configurable |
| **Uncertainty** | The confidence range of the expected outcome | Confidence Engine | Configurable |
| **Confidence** | The reliability of the evidence supporting the option | Confidence Engine | Configurable |
| **Resource impact** | The effect on system and human resources | Execution Planner | Configurable |
| **Time impact** | The expected duration and deadline alignment | Temporal analysis | Configurable |
| **Relationship impact** | The effect on existing relationships | Relationship Graph | Configurable |
| **Knowledge impact** | The effect on existing knowledge | Knowledge Graph | Configurable |

### 5.3 Evaluation formula

Each option receives a composite score:

```
option_score = Σ(dimension_score_i × weight_i) × confidence_factor
```

Where:

- `dimension_score_i` = the score for dimension i (normalised 0.0 – 1.0)
- `weight_i` = the configurable weight for dimension i
- `confidence_factor` = the combined confidence across all dimensions

### 5.4 Evaluation invariants

1. Every option is evaluated against every dimension.
2. Evaluation is deterministic — same option + same context → same scores.
3. Dimension weights are configurable by policy.
4. Evaluation results are immutable once recorded.

---

## 6. Decision Ranking Engine

### 6.1 Purpose

The Decision Ranking Engine ranks evaluated options to produce a recommendation. It considers weighted scores, constraints, policy compliance, goal alignment, and trade-offs.

### 6.2 Ranking pipeline

```
Evaluated options
  ↓
Filter by constraint satisfaction
  ↓
Score by weighted dimensions
  ↓
Score by policy compliance
  ↓
Score by goal alignment
  ↓
Compute trade-off matrix
  ↓
Rank options by composite score
  ↓
Select top option as recommendation
```

### 6.3 Ranking factors

| Factor | Description | Weight range |
|--------|-------------|-------------|
| **Weighted score** | The composite evaluation score from §5 | 0.0 – 1.0 |
| **Constraint satisfaction** | Whether the option satisfies all hard constraints | PASS/FAIL (hard), 0.0 – 1.0 (soft) |
| **Policy compliance** | How well the option aligns with active policies | 0.0 – 1.0 |
| **Goal alignment** | How well the option advances active goals | 0.0 – 1.0 |
| **Trade-off quality** | Whether the option has acceptable trade-offs | 0.0 – 1.0 |

### 6.4 Constraint satisfaction

| Constraint type | Behaviour on failure |
|-----------------|----------------------|
| **Hard constraint** | Option is excluded from ranking |
| **Soft constraint** | Option's score is reduced proportionally |
| **Aspirational constraint** | Option is flagged but not penalised |

### 6.5 Ranking invariants

1. Ranking is deterministic — same options + same weights → same ranking.
2. The top-ranked option is the recommendation.
3. If multiple options have equal scores, the recommendation is selected by: (a) higher confidence, then (b) lower risk, then (c) earlier detection.

---

## 7. Decision Governance

### 7.1 Purpose

Decision Governance ensures every decision is authorised, owned, auditable, and aligned with constitutional authority levels.

### 7.2 Governance levels

| Level | Authority | Can approve | Scope |
|-------|-----------|-------------|-------|
| L1 — Founder | Founder | All decisions | System-wide |
| L2 — Delegate | Founder-designated user | Operational decisions | Bounded by delegation |
| L3 — System | Automated decision engine | Routine, low-risk decisions | Bounded by policy |
| L4 — Constitutional | Constitutional amendment | System-wide invariant changes | Requires constitutional amendment |

### 7.3 Decision authority matrix

| Decision type | Auto-approve? | Required authority | Notes |
|--------------|---------------|-------------------|-------|
| Read-only query | Yes | L3 — System | No execution required |
| Routine operation | Yes | L3 — System | Policy-defined routine |
| Object creation | Yes | L3 — System | With identity governance |
| Object modification | Yes | L3 — System | Within existing schema |
| Object deletion | No | L1 — Founder | Irreversible |
| Commitment creation | No | L1 — Founder | Binds the organisation |
| Policy change | No | L1 — Founder (or L2) | Requires governance approval |
| High-risk execution | No | L1 — Founder | Risk score > 0.5 |
| Emergency action | Yes (immediate) | L3 — System | Must be logged and reviewed |

### 7.4 Governance operations

| Operation | Effect | Authority | Permanent? |
|-----------|--------|-----------|------------|
| **Approve** | Accept the recommendation and trigger execution | Per §7.3 | Yes |
| **Reject** | Decline the recommendation | Per §7.3 | Yes |
| **Defer** | Postpone the decision | Per §7.3 | No (re-enters lifecycle) |
| **Override** | Accept a recommendation that was rejected by automatic evaluation | Founder | Yes |
| **Escalate** | Route the decision to a higher authority | L3, L2 | Until resolved |
| **Veto** | Block an already-approved decision | Founder | Yes |

### 7.5 Audit trail

Every governance action is recorded:

| Action | Audit record |
|--------|-------------|
| Decision approved | Approver, timestamp, option, rationale |
| Decision rejected | Rejector, timestamp, rationale |
| Decision deferred | Deferred by, timestamp, new horizon |
| Decision overridden | Overrider, timestamp, override reason |
| Decision escalated | Escalated by, escalated to, reason |

---

## 8. Decision Evidence

### 8.1 Purpose

Every decision must reference the evidence, knowledge, predictions, observations, assumptions, and confidence that support it.

### 8.2 Evidence structure

```
DecisionEvidence {
  decision_id: Identity
  knowledge_refs: List[KnowledgeRef]    // What knowledge supports this decision
  prediction_refs: List[PredictionRef]  // What predictions support this decision
  evidence_refs: List[EvidenceRef]      // What evidence supports this decision
  observation_refs: List[ObservationRef] // What observations triggered this decision
  assumptions: List[Assumption]          // What assumptions were made
  confidence: ConfidenceBreakdown        // How confidence was computed
}
```

### 8.3 Evidence chain

```
Observation (§6 of Ontology)
  ↓
Evidence (§7 of Ontology)
  ↓
Knowledge (§14 of Ontology)
  ↓
Prediction (§15 of Ontology)
  ↓
DECISION
  ↓
Execution
  ↓
Observation (outcome feeds back)
```

### 8.4 Evidence invariants

1. Every decision references at least one piece of evidence.
2. Every decision references at least one prediction.
3. Every decision explicitly lists its assumptions.
4. Every decision has a confidence breakdown by factor.
5. No decision exists without evidence — unsupported decisions are flagged as speculative.

---

## 9. Decision Learning

### 9.1 Purpose

Decision Learning connects decision outcomes to the Adaptive Intelligence Runtime, Knowledge Graph, Execution Intelligence, and Perception — without redefining any of them.

### 9.2 Learning connections

| Connection | Constitutional source | What is learned | How |
|------------|----------------------|-----------------|-----|
| **Adaptive Runtime** | Adaptive §1, §4, §6 | Decision accuracy, evaluation quality, ranking effectiveness | Decision outcomes feed the Learning Engine and Calibration subsystems |
| **Knowledge Graph** | KG §2, §4 | New facts about decision quality, option effectiveness | Decision outcomes are added to the Evidence Graph |
| **Execution Intelligence** | Execution Intelligence §7, §8 | Execution quality, verification accuracy | Decision outcomes validate execution observations |
| **Perception** | Perception §3, §6 | Observation relevance, attention trigger accuracy | Decision outcomes validate attention triggers |
| **Confidence Engine** | Adaptive §2 | Confidence calibration, factor weight adjustment | Decision accuracy vs decision confidence comparison |

### 9.3 Learning integration

```
Decision observed (OBSERVED state)
  ↓
Compare actual outcome to predicted outcome
  ↓
Compute decision accuracy
  ↓
(1) Evidence Graph: Add decision outcome observation
  ↓
(2) Adaptive Runtime: Update learning model
  ↓
(3) Confidence Engine: Calibrate confidence factors
  ↓
(4) Perception: Validate attention triggers
  ↓
(5) Knowledge Graph: Update decision quality knowledge
```

### 9.4 Learning invariants

1. Learning never modifies the original decision record (per Adaptive AI-01).
2. Learning is based on observed outcomes, not on the decision itself.
3. Learning is reversible — calibrated weights can be reset.
4. Learning never bypasses the Evidence Graph.

---

## 10. Decision Event Bus

### 10.1 Purpose

The Decision Event Bus is a domain-specific event bus for decision events. It feeds into the Cognitive Event Bus (CWR §9) and Knowledge Graph Events (KG §10).

### 10.2 Canonical decision events

| Event | Emitter | Payload | Consumers |
|-------|---------|---------|-----------|
| `DecisionCreated` | Decision Context Engine | decision_id, context, source | Governance, Projection Engine |
| `DecisionAnalysed` | Decision Context Engine | decision_id, context_complete | Evaluation Engine |
| `AlternativeGenerated` | Alternative Generation | decision_id, options | Evaluation Engine |
| `DecisionEvaluated` | Evaluation Engine | decision_id, option_scores | Ranking Engine |
| `DecisionRecommended` | Ranking Engine | decision_id, recommendation, ranking | Governance, Projection Engine |
| `DecisionApproved` | Governance | decision_id, approver, option | Execution Engine |
| `DecisionRejected` | Governance | decision_id, rejector, rationale | Projection Engine, Memory |
| `DecisionDeferred` | Governance | decision_id, deferred_by, new_horizon | Projection Engine |
| `DecisionExecuted` | Execution Engine | decision_id, execution_id, outcome | Observation, Learning |
| `DecisionObserved` | Observation | decision_id, actual_outcome, variance | Learning Engine, Confidence Engine |
| `DecisionRetired` | Learning | decision_id, retirement_reason | Memory, Knowledge Graph |

### 10.3 Event propagation

All decision events are:

1. Published to the Cognitive Event Bus (CWR §9)
2. Stored in the Knowledge Graph as Event nodes (KG §2)
3. Consumed by the Workspace Projection Engine
4. Used by the Adaptive Runtime for learning and calibration

---

## 11. Decision Projection

### 11.1 Purpose

The Founder Workspace receives decision projections. These are structured views of decision state — never raw decision data.

### 11.2 Projection types

| Projection | Content | Source | Consumer |
|------------|---------|--------|----------|
| **Decision Queue** | Decisions awaiting founder attention | Decision Event Bus | Workspace Intelligence Panel |
| **Recommended Decisions** | Decisions in RECOMMENDED state awaiting approval | Decision Event Bus | Workspace Center panel |
| **Alternative Comparison** | Side-by-side comparison of options with scores | Evaluation Engine | Workspace Intelligence Panel |
| **Confidence** | Confidence breakdown for the recommendation | Confidence Engine | Workspace Intelligence Panel |
| **Trade-offs** | Trade-off matrix showing option differences | Ranking Engine | Workspace Intelligence Panel |
| **Risks** | Risk assessment for each option | Evaluation Engine | Workspace Intelligence Panel |
| **Evidence** | Evidence chain supporting the recommendation | Decision Evidence | Workspace Evidence panel |

### 11.3 Projection rules

1. Projections are read-only — the workspace never writes to decision state.
2. Projections are context-filtered — only decisions relevant to the current workspace are shown.
3. Projections are assembled by the Workspace Projection Engine (CWR §3).

---

## 12. Decision Explainability

### 12.1 Purpose

A founder should always know: Why this decision? Why not another? What assumptions exist? What evidence supports it? What uncertainty remains?

### 12.2 Explanation structure

```
DecisionExplanation {
  decision_id: Identity
  why_this_decision: Explanation
    // Triggering observation, relevant context, detected need
  why_this_option: Explanation
    // Ranking factors, top option vs alternatives, key differentiators
  why_not_alternatives: List[Explanation]
    // For each alternative: why it was not selected
  assumptions: List[Assumption]
    // Explicit list of assumptions made during evaluation
  evidence: List[EvidenceRef]
    // Supporting evidence for the recommendation
  uncertainty: UncertaintyBreakdown
    // What is uncertain, by how much, and why
  confidence: ConfidenceBreakdown
    // How confidence was computed, per factor
}
```

### 12.3 Explanation generation

Every decision in RECOMMENDED or later state must be able to produce an explanation:

| Question | Answer sourced from |
|----------|---------------------|
| Why this decision? | Context Engine — trigger, objectives, constraints |
| Why this option? | Ranking Engine — weighted scores, factor breakdown |
| Why not another? | Ranking Engine — comparison by factor |
| What assumptions? | Alternative Generation — explicit assumptions |
| What evidence? | Decision Evidence — evidence chain |
| What uncertainty? | Evaluation Engine — confidence range per dimension |

### 12.4 Explainability invariants

1. Every decision in RECOMMENDED state has a complete explanation.
2. Explanations are deterministic — same decision → same explanation.
3. Explanations reference specific evidence, not general knowledge.
4. Explanations explicitly state assumptions.
5. Explanations include uncertainty — certainty is never claimed without qualification.

---

## 13. Scalability

### 13.1 Assumptions

The architecture supports: millions of concurrent decisions, hierarchical decisions (decisions that spawn sub-decisions), nested decisions (decisions within decisions), and continuous re-evaluation.

### 13.2 Scaling strategies

| Strategy | Applied to | Description |
|----------|------------|-------------|
| **Stateless evaluation** | Evaluation Engine | Evaluation is stateless. All context is passed as input, not stored in memory. |
| **Incremental ranking** | Ranking Engine | Ranking is recomputed incrementally when options change, not from scratch. |
| **Deferred re-evaluation** | Decision Lifecycle | Decisions in DEFERRED state are stored with their context for later re-evaluation. |
| **Hierarchical decomposition** | All | Complex decisions are decomposed into sub-decisions. Each sub-decision has its own lifecycle. |
| **Batched observation** | Decision Learning | Decision outcomes are batched for learning (every 100 decisions or 1 hour). |
| **Projection caching** | Decision Projections | Decision projections are cached with TTL. Invalidated on state change. |

### 13.3 Latency targets

| Operation | Target | Degraded threshold |
|-----------|--------|-------------------|
| Context resolution | < 200ms | > 500ms |
| Alternative generation | < 500ms | > 2s |
| Full evaluation (10 options) | < 1s | > 3s |
| Ranking (10 options) | < 200ms | > 500ms |
| Recommendation | < 100ms | > 300ms |
| Explanation generation | < 200ms | > 500ms |
| Projection refresh | < 100ms | > 300ms |
| Approval processing | < 50ms | > 200ms |

---

## 14. Implementation Roadmap

### Phase 12A — Decision Objects

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Decision Object Model: Decision, DecisionCandidate, DecisionContext, DecisionConstraint, DecisionObjective, DecisionOption, DecisionOutcome |
| **Dependencies** | UNIVERSAL_ONTOLOGY.md (§10 Action, §8 Event, §15 Prediction), EXECUTION_INTELLIGENCE_ARCHITECTURE.md (§1 Execution Object Model) |
| **Deliverables** | Decision data model, decision identity, decision lifecycle state machine, decision timeline, decision evidence attachment |
| **Validation criteria** | 1000 decisions in < 1s. All lifecycle transitions valid. Every decision has identity and timeline. |

### Phase 12B — Decision Evaluation

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement Decision Evaluation: 9 evaluation dimensions, score computation, option scoring, confidence integration |
| **Dependencies** | Phase 12A, ADAPTIVE_INTELLIGENCE_RUNTIME.md (§2 Confidence Engine), EXECUTION_INTELLIGENCE_ARCHITECTURE.md (§10 Risk Engine) |
| **Deliverables** | Evaluation pipeline, 9 dimension evaluators, composite scoring, confidence integration |
| **Validation criteria** | Options are scored deterministically. Scores are reproducible. All 9 dimensions are evaluated. |

### Phase 12C — Decision Ranking

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement Decision Ranking: weighted ranking, constraint satisfaction, policy compliance, goal alignment, trade-off evaluation |
| **Dependencies** | Phase 12A, Phase 12B, UNIVERSAL_ONTOLOGY.md (§16 Policy), COGNITIVE_WORKSPACE_RUNTIME.md (§4 Intent Pipeline) |
| **Deliverables** | Ranking pipeline, constraint satisfaction, policy compliance scoring, goal alignment, trade-off matrix, recommendation selection |
| **Validation criteria** | Ranking is deterministic. Constraints filter correctly. Trade-off matrix is accurate. Recommendation is the top-ranked option. |

### Phase 12D — Decision Governance

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement Decision Governance: authority matrix, approval routing, delegation, override, escalation, audit trail |
| **Dependencies** | Phase 12A – Phase 12C, ADAPTIVE_INTELLIGENCE_RUNTIME.md (§13 Human Governance) |
| **Deliverables** | Authority enforcement, approval routing, delegation chain, override mechanism, escalation path, audit trail |
| **Validation criteria** | Authority enforcement blocks unauthorised approvals. Delegation works. Escalation routes correctly. All actions auditable. |

### Phase 12E — Decision Learning

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement Decision Learning: outcome capture, accuracy computation, learning integration with Adaptive Runtime, Knowledge Graph, Execution, Perception |
| **Dependencies** | Phase 12A – Phase 12D, ADAPTIVE_INTELLIGENCE_RUNTIME.md (§1 Learning, §4 Execution Learning, §6 Calibration) |
| **Deliverables** | Outcome capture, accuracy computation, Evidence Graph integration, confidence calibration feedback, perception trigger validation |
| **Validation criteria** | Decision accuracy is computed correctly. Learning feeds back to confidence. Evidence Graph is updated. Outcomes are immutable. |

### Phase 12F — Decision Explainability

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement Decision Explainability: why this decision, why this option, why not alternatives, assumptions, evidence, uncertainty |
| **Dependencies** | Phase 12A – Phase 12E |
| **Deliverables** | Explanation generator, explanation structure, assumption listing, evidence chain, uncertainty breakdown, explainability API |
| **Validation criteria** | Every decision in RECOMMENDED state has an explanation. Explanations are deterministic. All 5 questions answerable. Assumptions are explicit. |

---

## Appendix A: Decision Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       DECISION INTELLIGENCE ARCHITECTURE                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  ANALYSIS LAYER                                                       │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │   │
│  │  │  Decision        │  │  Context         │  │  Alternative       │  │   │
│  │  │  Context Engine  │  │  Resolution      │  │  Generation        │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  EVALUATION LAYER              │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Decision        │  │  Decision        │  │  Trade-off         │  │   │
│  │  │  Evaluation      │  │  Ranking Engine  │  │  Analysis          │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  GOVERNANCE LAYER              │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Decision        │  │  Approval        │  │  Audit Trail       │  │   │
│  │  │  Governance      │  │  Routing         │  │  (all operations)  │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  EXPLAINABILITY LAYER          │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Explanation     │  │  Evidence        │  │  Uncertainty       │  │   │
│  │  │  Generator       │  │  Chain           │  │  Breakdown         │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  INTEGRATION LAYER             │                                      │   │
│  │  ┌──────────────────┐  ┌──────┴───────────┐  ┌────────────────────┐  │   │
│  │  │  Decision        │  │  Decision        │  │  Constitutional    │  │   │
│  │  │  Event Bus       │  │  Projections     │  │  Cross-References  │  │   │
│  │  └──────────────────┘  └──────────────────┘  └────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌────────────────────────────────┼─────────────────────────────────────┐   │
│  │  CONSTITUTIONAL CONSUMERS      │                                      │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │   │
│  │  │ Ont. │ │ K.G. │ │ Perc.│ │ C.R. │ │ A.R. │ │ E.I. │ │ Work.│   │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Constitutional Cross-References

| Subsystem | Constitutional references |
|-----------|--------------------------|
| Decision Object Model (§1) | Ontology §10 (Action), §8 (Event), §15 (Prediction), §7 (Evidence) |
| Decision Lifecycle (§2) | Ontology §11 (State), CWR §6 (Object Lifecycle) |
| Decision Context Engine (§3) | Ontology §13 (Context), CWR §8 (Context Transition), CWR §5 (Memory) |
| Alternative Generation (§4) | Ontology §10 (Action), Execution Intelligence §5 (Execution Planner) |
| Decision Evaluation (§5) | Adaptive §2 (Confidence Engine), Execution Intelligence §10 (Risk Engine), Prediction Engine |
| Decision Ranking (§6) | Ontology §16 (Policy), CWR §4 (Intent Pipeline) |
| Decision Governance (§7) | Adaptive §13 (Human Governance), Ontology §16 (Policy) |
| Decision Evidence (§8) | Ontology §7 (Evidence), KG §4 (Evidence Graph) |
| Decision Learning (§9) | Adaptive §1 (Learning Engine), §4 (Execution Learning), §6 (Calibration) |
| Decision Event Bus (§10) | CWR §9 (Cognitive Event Bus), KG §10 (Graph Events) |
| Decision Projection (§11) | CWR §3 (Projection Engine), KG §8 (Graph Projections) |
| Decision Explainability (§12) | Ontology §7 (Evidence), Adaptive §2 (Confidence), Adaptive §6 (Calibration) |
| Scalability (§13) | KG §11 (Scalability Strategy), Execution Intelligence §14 (Scalability) |