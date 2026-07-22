# ES-003: Reasoning Engine

**Status:** Draft
**Phase:** Phase 2 (Reasoning Layer)
**Layer:** Reasoning
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters the Reasoning Engine

- **Workspace context** — bounded, fingerprinted context from Context Fusion (Phase 10). Includes identity, relationships, conversations, human context, memory, evidence, and document references relevant to the current request.
- **Knowledge facts** — versioned, confidence-scored facts from the Knowledge Engine. Retrieved by key, domain, temporal range, or relationship traversal.
- **Evidence chains** — provenance-verified fact bundles linking claims to their supporting or contradicting sources.
- **Policies** — active governance policies that constrain what conclusions are permissible. The Reasoning Engine reads policies to ensure its recommendations align with governance boundaries.
- **User intent** — the expressed goal from the human or external system, normalized by the Interface Layer.
- **Historical outcomes** — past decisions and their outcomes, retrieved from the Knowledge Engine for similarity-based reasoning.
- **Confidence values** — existing confidence scores on all input facts, used as priors for probabilistic reasoning.

### What Leaves the Reasoning Engine

- **Hypotheses** — candidate explanations or interpretations of the observed situation.
- **Alternatives** — multiple viable options ranked by desirability, risk, and confidence.
- **Recommendations** — the primary recommended course of action with justification.
- **Risk assessments** — identified risks per alternative, with severity and likelihood.
- **Confidence scores** — overall and per-step confidence in the reasoning result (canonical 0.0–1.0 scale).
- **Explanation graph** — a structured graph of the reasoning path: premises → inferences → conclusions, with every edge labelled by the reasoning type used.
- **Evidence chains** — the subset of evidence that supports or contradicts each conclusion.
- **Planning candidates** — structured inputs for the Planner Engine, including decision, confidence, evidence, alternatives, and risk flags.
- **Open questions** — explicitly identified gaps in knowledge that, if filled, would increase confidence.
- **Unknowns** — areas where the engine consciously acknowledges insufficient information.
- **Contradictions** — points where available evidence conflicts, requiring resolution before planning.

### What Intelligence Is Compounded

The Reasoning Engine compounds **inferential precision** over time. Every reasoning cycle produces outcomes that are observed, verified, and fed back as knowledge. The next cycle starts from a richer evidence base and a more refined understanding of what inferences are reliable.

The compounding mechanism is **outcome-feedback**: when a reasoning result leads to a successful outcome, the evidence and inference patterns that produced it are reinforced. When it leads to failure, the patterns are weakened. Over time, the engine learns which reasoning strategies produce reliable results for which types of problems.

### Which Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Planner Engine | Consumes reasoning results to create executable plans | **Critical** — cannot plan without justified conclusions |
| Governance Engine | Consumes evidence chains and confidence scores for validation | **High** — governance evaluates reasoning quality |
| Knowledge Engine | Receives derived knowledge (learned inference patterns) | **Medium** — can operate without derived knowledge |
| Context Fusion | Receives reasoning context requirements for next cycle | **Low** — context requirements are advisory |

### What Fails If It Becomes Unavailable

- **Planning halts** — no justified conclusions to plan from
- **Governance is blind** — policy evaluation continues but without evidence chains and confidence scores, every decision effectively has zero evidence
- **The compounding loop breaks** — reasoning is the bridge between knowledge and action; without it, knowledge exists but no conclusions are drawn
- **User experience degrades to rule-based** — the system can still respond with template-based answers, but cannot handle novel situations, resolve ambiguities, or provide evidence-grounded recommendations

---

## Section 1 — Mission

### Purpose of Reasoning Inside SHUNYA

Reasoning is the transformation of knowledge into justified conclusions. It is the bridge between *what is known* (Knowledge Engine) and *what should be done* (Planner Engine). The Reasoning Engine does not execute, govern, learn, or mutate knowledge. It takes facts, evidence, context, and intent, and produces justified, confidence-scored, explainable conclusions.

The canonical lifecycle (SHUNYA System Flow §2) positions Reasoning after Context Fusion and before Planning:

```
Context Fusion → Reasoning → Planning → Governance → Execution
```

### Clarification of Boundaries

| Activity | Belongs To | Reasoning Engine Role |
|----------|-----------|----------------------|
| **Execute** | Executor Engine | Never. Reasoning produces conclusions, not actions. |
| **Govern** | Governance Engine | Never. Reasoning does not evaluate policies or make approval decisions. |
| **Learn** | Learning Engine | Never. Reasoning does not generate learning signals or update knowledge from outcomes. |
| **Mutate knowledge** | Knowledge Engine | Never. Reasoning reads knowledge but does not write, version, or supersede facts. |
| **Transform knowledge into conclusions** | Reasoning Engine | This is the sole purpose. |

The Reasoning Engine **transforms knowledge into justified conclusions.** It does nothing else.

---

## Section 2 — Inputs

All inputs conform to the canonical models defined in SHUNYA Core Models. The Reasoning Engine does not redefine input structures.

### Input Contract

```
ReasoningInput:
  context: WorkspaceContext        — From Context Fusion (Phase 10). Bounded, fingerprinted.
                                    Contains identity, relationships, conversations, human
                                    context, memory, evidence, document references.
  knowledge_facts: KnowledgeFact[] — From Knowledge Engine (ES-002). Versioned, confidence-scored.
  evidence_chains: EvidenceChain[] — From Knowledge Engine. Provenance-verified fact bundles.
  policies: Policy[]               — From Governance Engine (ES-001). Active policies constraining
                                    what conclusions are permissible.
  user_intent: Intent              — Normalized goal from the Interface Layer.
  historical_outcomes: Outcome[]   — Past decisions with results, from Knowledge Engine.
  request_metadata: RequestInfo    — Tenant ID, actor ID, purpose code, correlation ID, trace ID.
```

### Input Sources

| Input | Source | Retrieval Method |
|-------|--------|-----------------|
| Workspace context | Context Fusion (Phase 10) | Synchronous API call; cached for request lifetime |
| Knowledge facts | Knowledge Engine (ES-002) | Structured retrieval by key, domain, or relationship traversal |
| Evidence chains | Knowledge Engine (ES-002) | `get_evidence_chain()` API |
| Policies | Governance Engine (ES-001) | In-memory policy registry snapshot |
| User intent | Interface Layer | Extracted during request normalization |
| Historical outcomes | Knowledge Engine (ES-002) | Temporal retrieval — outcomes for same/similar context |
| Tenant/actor metadata | Request context | Propagated through the event envelope |

### Input Validation

| Field | Constraint | Rejection |
|-------|-----------|-----------|
| `context.tenant_id` | Must match request tenant | `TENANT_MISMATCH` |
| `context.actor_id` | Must resolve to a valid identity | `UNRESOLVED_ACTOR` |
| `knowledge_facts` | May be empty (reasoning without facts has low confidence) | Warning only |
| `user_intent.goal` | Non-empty | `EMPTY_INTENT` |
| `evidence_chains` | May be empty | Warning — reduced confidence |
| `policies` | At least one policy must be readable | `NO_POLICIES_AVAILABLE` |

---

## Section 3 — Outputs

All outputs conform to the canonical models defined in SHUNYA Core Models.

### Output Contract

```
ReasoningResult:
  recommendation: Recommendation       — Primary recommended course of action
  alternatives: Alternative[]          — Ranked alternatives with trade-offs
  confidence: float                    — Overall confidence (canonical 0.0–1.0)
  explanation: ExplanationGraph        — Structured reasoning path
  evidence_chains: EvidenceChain[]     — Evidence supporting recommendations
  risk_assessments: RiskAssessment[]   — Per-alternative risk analysis
  open_questions: OpenQuestion[]       — Knowledge gaps that would increase confidence
  unknowns: Unknown[]                  — Conscious acknowledgement of insufficient information
  contradictions: Contradiction[]      — Conflicting evidence points
  planning_candidates: PlanningInput[] — Structured inputs for the Planner Engine
  reasoning_metadata: ReasoningInfo    — Engine version, reasoning types used, timings
```

### Output Destinations

| Output | Destination | Format |
|--------|-------------|--------|
| Primary recommendation | Planner Engine | `PlanningInput` — decision, confidence, evidence, alternatives, risk flags |
| Explanation graph | Governance Engine | For evidence chain verification during policy evaluation |
| Evidence chains | Governance Engine | For policy evaluation and audit |
| Contradictions | Governance Engine | For REVIEW classification when contradictions exist |
| Open questions / unknowns | Interface Layer | For user-facing clarification requests |
| Reasoning metadata | Observer Layer | For observability and learning |

### Output Guarantees

- **Determinism:** Same inputs always produce the same reasoning result. No randomness.
- **Idempotency:** Repeated reasoning with identical inputs produces identical output. No state mutation.
- **Explainability:** Every output includes a complete explanation graph (see Section 7).

---

## Section 4 — Reasoning Pipeline

### Canonical Stages

```
Observation
     │
     ▼
Context Assembly
     │
     ▼
Evidence Collection
     │
     ▼
Hypothesis Generation
     │
     ▼
Evaluation
     │
     ▼
Conflict Detection
     │
     ▼
Confidence Calculation
     │
     ▼
Explanation Generation
     │
     ▼
Planning Candidate
```

### Stage Definitions

| Stage | Purpose | Inputs | Outputs | Failure Condition |
|-------|---------|--------|---------|-------------------|
| **Observation** | Receive and normalize the raw stimulus | Incoming request, user intent, channel metadata | Normalized observation for reasoning | Malformed request; missing tenant context |
| **Context Assembly** | Select the subset of workspace context relevant to this reasoning problem | Full workspace context, request purpose code | Filtered context relevant to the reasoning goal | Context too sparse to determine relevance |
| **Evidence Collection** | Retrieve facts and evidence chains from the Knowledge Engine | Filtered context, knowledge fact keys | Complete set of evidence for the problem | Knowledge Engine unavailable; partial evidence retrieved |
| **Hypothesis Generation** | Generate candidate interpretations, explanations, or recommendations | Evidence, context, user intent | Ranked list of hypotheses | Zero hypotheses generated (insufficient evidence) |
| **Evaluation** | Score each hypothesis against evidence, context, and constraints | Hypotheses, evidence, policies | Evaluated hypotheses with scores | All hypotheses fail minimum confidence threshold |
| **Conflict Detection** | Identify contradictory evidence or incompatible hypotheses | Evaluated hypotheses, evidence chains | Conflict-annotated hypotheses | Circular reasoning detected |
| **Confidence Calculation** | Compute overall and per-step confidence using the canonical confidence model | Evaluated hypotheses, conflicts, prior confidences | Confidence-scored result | Cannot compute confidence (prior missing) |
| **Explanation Generation** | Build the explanation graph tracing every conclusion to its evidence | Full reasoning state | Structured, human-readable explanation graph | Explanation exceeds size budget |
| **Planning Candidate** | Package the result for the Planner Engine | Complete reasoning result | Structured PlanningInput | Result too ambiguous to package |

### Transitions

| From | To | Condition | Fallback |
|------|----|-----------|----------|
| Observation | Context Assembly | Input validated | Return error to caller |
| Context Assembly | Evidence Collection | Context not empty | Use minimal context |
| Evidence Collection | Hypothesis Generation | At least one evidence source available | Low-confidence reasoning from context alone |
| Hypothesis Generation | Evaluation | At least one hypothesis generated | Return "insufficient evidence" with open questions |
| Evaluation | Conflict Detection | Evaluation completed | All hypotheses below threshold → return open questions |
| Conflict Detection | Confidence Calculation | Conflicts resolved or documented | Flag contradictions, proceed with reduced confidence |
| Confidence Calculation | Explanation Generation | Confidence computed | Use default confidence (0.3) |
| Explanation Generation | Planning Candidate | Explanation generated | Return minimal explanation |

---

## Section 5 — Reasoning Types

The Reasoning Engine supports multiple reasoning types, applied composably. A single reasoning cycle may use multiple types in sequence or in parallel.

| Reasoning Type | Description | When Used | Example |
|----------------|-------------|-----------|---------|
| **Deductive** | Derive certain conclusions from general rules and specific facts. Conclusions are guaranteed true if premises are true. | Policy compliance, mathematical constraints, deterministic rule application | "If this booking exceeds ₹1,00,000, approval is required. This booking is ₹1,50,000. Therefore, approval is required." |
| **Inductive** | Derive general principles from specific observations. Conclusions are probabilistic. | Pattern recognition, trend analysis, customer behaviour modelling | "Three customers from Mumbai preferred direct flights. Therefore, Mumbai customers likely prefer direct flights." |
| **Abductive** | Infer the most likely explanation for observed facts. Conclusion is the best explanation, not guaranteed truth. | Diagnostic reasoning, intent inference, root cause analysis | "Customer asked about beach resorts in June. Most likely explanation: they want a beach vacation in June." |
| **Probabilistic** | Apply Bayesian or statistical reasoning under uncertainty. | Risk assessment, confidence computation, outcome prediction | "Given that 70% of similar inquiries convert, the probability of conversion is 0.7." |
| **Constraint-based** | Reason within explicit boundaries defined by policies or resource limits. | Feasibility checking, scheduling, resource allocation | "Within the budget of ₹50,000, the feasible options are A, B, and C." |
| **Policy-aware** | Reason while considering active governance policies as constraints on permissible conclusions. | Pre-governance filtering, compliance-aware recommendations | "Policy X prohibits booking this hotel. Therefore, this alternative is not recommended." |
| **Temporal** | Reason about sequences, durations, deadlines, and time-dependent relationships. | Scheduling, planning, expiry checking | "The trip starts on 15 Dec and ends on 20 Dec. Five days available. Activities must fit within this window." |
| **Comparative** | Compare multiple options against defined criteria and rank them. | Option selection, trade-off analysis, vendor comparison | "Option A is cheaper but farther from the venue. Option B is more expensive but closer. Recommendation depends on priority." |
| **Counterfactual** | Reason about what would happen under different conditions. | What-if analysis, risk simulation, contingency planning | "If the flight is delayed by 3 hours, the connecting transport must be rebooked." |
| **Multi-step** | Chain multiple reasoning steps where each step's output feeds the next. | Complex problem solving, multi-stage decision making | "Step 1: Determine destination. Step 2: Determine travel dates. Step 3: Check visa requirements. Step 4: Recommend itinerary." |

### Reasoning Type Composition

Reasoning types are composed through a pipeline definition. A typical reasoning cycle may use:

1. Abductive reasoning to infer customer intent from the inquiry text
2. Deductive reasoning to check policy constraints on the inferred intent
3. Probabilistic reasoning to estimate likelihood of success for each option
4. Comparative reasoning to rank options
5. Temporal reasoning to verify scheduling feasibility
6. Counterfactual reasoning to produce contingency plans
7. Multi-step reasoning to chain all stages together

---

## Section 6 — Confidence Propagation

The Reasoning Engine uses the canonical confidence model defined in SHUNYA Core Models §7. It does not redefine the scale, propagation rules, combination rules, decay functions, or thresholds.

### Propagation Through the Reasoning Pipeline

Confidence propagates through each stage of the reasoning pipeline as follows:

| Stage | Confidence Rule | Formula |
|-------|----------------|---------|
| **Observation** | Initial confidence from the source | Confidence from Interface Layer (canonical scale) |
| **Context Assembly** | Confidence in context relevance | `min(confidence_of_context_sources) * context_relevance` |
| **Evidence Collection** | Confidence in evidence completeness | `combined_confidence(evidence_sources) * evidence_coverage` |
| **Hypothesis Generation** | Confidence per hypothesis | `min(evidence_confidence, reasoning_type_reliability)` |
| **Evaluation** | Confidence in each evaluation | `hypothesis_confidence * evaluation_method_reliability` |
| **Conflict Detection** | Confidence reduction for conflicting hypotheses | `base_confidence * (1 - conflict_severity)` |
| **Confidence Calculation** | Overall confidence in the reasoning result | See "Overall Confidence" below |
| **Explanation Generation** | Confidence unchanged from calculation | Same as overall confidence |

### Overall Confidence

The overall confidence in a reasoning result is computed as:

```
overall_confidence = evidence_completeness *
                     reasoning_coherence *
                     conflict_penalty *
                     min(hypothesis_confidences)
```

Where:

- `evidence_completeness` = fraction of required evidence that was available (0.0–1.0)
- `reasoning_coherence` = how well the reasoning path holds together (0.0–1.0)
- `conflict_penalty` = `1 - max(conflict_severity)` if conflicts exist, else 1.0
- `min(hypothesis_confidences)` = the lowest confidence among all hypotheses considered

### Per-Step Confidence

Every step in the reasoning pipeline produces a per-step confidence. These are included in the explanation graph so that downstream consumers and auditors can see exactly which steps had low confidence.

---

## Section 7 — Explainability

### Every Conclusion Shall Include

| Component | Description | Always Present? |
|-----------|-------------|-----------------|
| **Evidence** | All facts and sources that support the conclusion | Yes |
| **Reasoning path** | The sequence of reasoning steps from evidence to conclusion, with each step labelled by reasoning type | Yes |
| **Confidence** | Overall and per-step confidence (canonical 0.0–1.0) | Yes |
| **Alternative paths** | Other reasoning paths that were considered and why they were rejected | Yes (may be empty if no alternatives existed) |
| **Rejected hypotheses** | Hypotheses that were evaluated and rejected, with rejection reasons | Yes (may be empty) |
| **Unknown assumptions** | Assumptions made during reasoning that were not verified | Yes (may be empty if all assumptions verified) |

### Explanation Graph Structure

```
ExplanationGraph:
  nodes: ReasoningNode[]           — Evidence, inference, conclusion
  edges: ReasoningEdge[]           — Typed connections between nodes
  reasoning_types: ReasoningType[] — Which reasoning types were used
  confidence: float                — Overall confidence
  created_at: datetime             — When the explanation was generated

ReasoningNode:
  id: string                       — Unique node identifier
  type: "evidence" | "inference" | "hypothesis" | "conclusion" | "assumption" | "unknown"
  content: string                  — What this node represents
  confidence: float                — Node-level confidence
  source: string                   — Where this node came from (fact key, reasoning step, etc.)

ReasoningEdge:
  from_node: string                — Source node ID
  to_node: string                  — Target node ID
  reasoning_type: ReasoningType    — Which reasoning type produced this edge
  confidence: float                — Edge-level confidence
  rationale: string                — Why this edge exists
```

### Explainability Guarantees

- Every conclusion can be traced back to its supporting evidence through the explanation graph.
- Every inference step is labelled with its reasoning type.
- Every rejected hypothesis has a documented rejection reason.
- Every unknown assumption is explicitly listed.
- The explanation graph is machine-readable (structured JSON) and human-readable (natural language summary).

---

## Section 8 — Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Insufficient evidence | Knowledge Engine returns zero relevant facts | Post-retrieval count check | Low confidence reasoning; many open questions | Return reasoning result with explicit evidence gaps; request additional information |
| Contradictory evidence | Evidence chains contain mutually exclusive facts | Conflict detection stage | Reduced confidence; flagged contradictions | Return result with contradictions documented; Governance may flag as REVIEW |
| Low confidence | All hypotheses fall below minimum threshold | Confidence calculation stage | No actionable recommendation | Return "insufficient confidence" with explanation and open questions |
| Policy conflict | Reasoning produces a conclusion that violates an active policy | Policy-aware reasoning stage | Conclusion excluded from recommendations | Return policy-compliant alternatives with documented policy constraint |
| Circular reasoning | A conclusion depends on itself through the reasoning chain | Cycle detection in explanation graph | Invalid reasoning path | Prune circular path, return reduced-confidence result |
| Context ambiguity | Workspace context is too sparse to determine relevance | Context Assembly stage | Broad but shallow reasoning | Return result with low confidence; flag need for more context |
| Knowledge gap | Required knowledge does not exist in the Knowledge Engine | Evidence Collection stage | Hypothesis cannot be evaluated | Return open question requesting the missing knowledge |
| Hallucination | Inference not grounded in available evidence | Post-hoc verification against evidence set | **Critical failure** — invalid conclusion | Reject ungrounded inference; flag for governance review |
| Reasoning type failure | A specific reasoning type cannot produce a valid result | Per-type evaluation | Fall back to simpler reasoning type | Re-try with alternative reasoning type; document the failed attempt |

### Hallucination Prevention

Hallucination prevention is a hard requirement. Every inference must be traceable to specific evidence. The Reasoning Engine employs:

1. **Grounding check:** Every inference in the explanation graph must reference at least one evidence node. Ungrounded inferences are rejected.
2. **Source attribution:** Every conclusion references the specific facts and evidence chains that support it.
3. **Confidence penalty:** Inferences with shallow grounding receive reduced confidence.
4. **Explicit unknowns:** When the engine cannot ground a conclusion, it produces an "unknown" rather than fabricating an answer.

---

## Section 9 — Interaction Matrix

| Layer / Engine | Reads | Writes | Events Published | Events Consumed |
|----------------|-------|--------|-----------------|-----------------|
| **Knowledge Engine** (ES-002) | Facts, evidence chains, historical outcomes | — | — | `reasoning.completed` (to trigger follow-up knowledge queries) |
| **Context Fusion** (Phase 10) | Workspace context | — | — | `reasoning.context.required` (to request specific context) |
| **Governance Engine** (ES-001) | Policies (in-memory registry) | — | `reasoning.completed` | — |
| **Planner Engine** | — | Planning candidates | — | `reasoning.completed` |
| **Interface Layer** | User intent | — | — | `reasoning.insufficient.evidence` (for clarification) |
| **Observer Layer** | — | — | `reasoning.completed` | — |
| **Learning Engine** | — | — | — | `reasoning.completed` (outcome analysis) |

### Dependencies

| Dependency | Type | Criticality |
|------------|------|-------------|
| Knowledge Engine | Read | **Critical** — cannot reason without facts |
| Context Fusion (Phase 10) | Read | **High** — reduced quality without context |
| Governance Engine | Read | **High** — policy constraints enable policy-aware reasoning |
| Identity Engine | Read (via context) | **Medium** — identity needed for personalized reasoning |

### Ownership

- The Reasoning Engine **owns** the reasoning pipeline, hypothesis generation, evaluation, and explanation generation.
- It **does not own** facts, evidence, context, policies, or execution outputs.
- It **shares ownership** of confidence scores with the Knowledge Engine (input confidence) and the Planner Engine (output confidence for planning).

---

## Section 10 — Performance

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| **Latency p50** | < 200ms | Per reasoning cycle |
| **Latency p99** | < 1s | Per reasoning cycle (complex multi-step reasoning may exceed) |
| **Memory per cycle** | < 50MB | Peak allocation during reasoning |
| **Concurrent cycles** | 50 / instance | Per reasoning engine instance |
| **Evidence retrieval** | < 50ms p99 | Per Knowledge Engine query (network overhead included) |
| **Explanation graph generation** | < 100ms | Per reasoning cycle |
| **Hypothesis limit** | 10 per cycle | Maximum hypotheses generated per reasoning invocation |
| **Evidence limit** | 100 per cycle | Maximum evidence items considered per reasoning invocation |

### Caching

- Reasoning results are **not cached** at the Reasoning Engine level. Each invocation produces fresh reasoning. The Knowledge Engine caches facts.
- Explanation graphs are **not cached**. They are generated fresh per cycle.
- The policy registry is cached in memory and refreshed on `policy.registry.updated` events.

### Parallel Reasoning

- Independent reasoning types (e.g., Deductive and Inductive applied to different evidence subsets) may execute in parallel.
- Dependent reasoning types execute sequentially (e.g., Temporal reasoning depends on the output of Deductive reasoning).
- The pipeline executor manages parallel execution within the stage boundaries defined in Section 4.

### Scaling

- The Reasoning Engine is stateless. Horizontal scaling is achieved by adding instances behind a load balancer.
- No shared state between instances except the Knowledge Engine and policy registry (which are read-mostly).

---

## Section 11 — Security

### Isolation

- The Reasoning Engine is tenant-aware. All reasoning is scoped to the tenant_id from the request context.
- No cross-tenant knowledge leakage. The Reasoning Engine only accesses facts for the requesting tenant.
- Reasoning is isolated per request. No state carries between reasoning cycles.

### Privacy

- The Reasoning Engine does not store or cache personal data.
- Inputs containing personal data (from workspace context) are used during the reasoning cycle and discarded after the explanation graph is produced.
- The explanation graph may reference personal data only if it is essential to the reasoning path. Minimal disclosure principle applies.

### Tenant Awareness

- Every reasoning cycle carries the tenant_id. All knowledge retrieval, policy lookup, and context assembly are scoped to the tenant.
- Reasoning models or strategies may differ per tenant (different domain, different policies). Tenant-specific configurations are loaded at cycle start.

### Policy Awareness

- The Reasoning Engine reads active policies to constrain its conclusions. It does not evaluate policies (that is Governance's role), but it must be aware of policy boundaries to produce viable recommendations.
- Policy-unaware reasoning is permitted only for exploration. Policy-unaware results are flagged as such and confidence is reduced.

### Auditability

- Every reasoning cycle produces an explanation graph that is a complete, verifiable record of how conclusions were reached.
- Explanation graphs are stored in the Knowledge Engine for audit and learning.
- Explanation graphs are immutable after creation.

---

## Section 12 — Observability

### Metrics

| Metric | Type | Unit | Target |
|--------|------|------|--------|
| `reasoning.cycles_total` | Counter | cycles | Per second |
| `reasoning.latency_p50` | Histogram | ms | < 200ms |
| `reasoning.latency_p99` | Histogram | ms | < 1s |
| `reasoning.confidence_p50` | Histogram | float | Tracked for quality monitoring |
| `reasoning.confidence_p99` | Histogram | float | Tracked for quality monitoring |
| `reasoning.failures_total` | Counter | failures | Per second (by failure type) |
| `reasoning.hypotheses_generated` | Histogram | count | Per cycle |
| `reasoning.hypotheses_accepted` | Histogram | count | Per cycle |
| `reasoning.evidence_retrieved` | Histogram | count | Per cycle |
| `reasoning.type_usage` | Counter | invocations | Per reasoning type |
| `reasoning.contradictions_detected` | Counter | contradictions | Per cycle |

### Tracing

- **Span: `reasoning.cycle`** — Full reasoning lifecycle
  - Child span: `reasoning.context_assembly`
  - Child span: `reasoning.evidence_collection`
  - Child span: `reasoning.hypothesis_generation`
  - Child span: `reasoning.evaluation`
  - Child span: `reasoning.conflict_detection`
  - Child span: `reasoning.confidence_calculation`
  - Child span: `reasoning.explanation_generation`
- Trace context propagated from caller (Interface Layer or Context Fusion)

### Reasoning Quality Metrics

| Metric | Purpose |
|--------|---------|
| **Confidence accuracy** | How often high-confidence conclusions lead to successful outcomes |
| **Evidence coverage** | What fraction of reasoning steps are fully grounded in evidence |
| **Conflict resolution rate** | How often detected conflicts are successfully resolved |
| **Hypothesis acceptance rate** | What fraction of generated hypotheses survive evaluation |
| **Explanation completeness** | What fraction of conclusions have complete explanation paths |

### Failure Metrics

| Metric | Trigger |
|--------|---------|
| `reasoning.insufficient_evidence` | Zero relevant facts found |
| `reasoning.low_confidence` | All hypotheses below minimum threshold |
| `reasoning.circular_path_detected` | Circular dependency in reasoning chain |
| `reasoning.ungrounded_inference_rejected` | Hallucination prevention triggered |

---

## Section 13 — Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Transform knowledge into justified conclusions | 5 (Reasoning Layer) — Analyzes customer intent, outputs confidence + evidence + explanation | SHUNYA_ARCHITECTURE.md §5 |
| Every recommendation includes confidence score | 6.5 Explainable Decisions — Every recommendation must include Decision + Confidence + Evidence + Explanation | SHUNYA_ARCHITECTURE.md §6.5 |
| Every conclusion is traceable to its evidence | 6.5 Explainable Decisions — No black boxes | SHUNYA_ARCHITECTURE.md §6.5 |
| Never accesses credentials | 6.3 Principle of Least Authority — Reasoning doesn't need passwords, payment tokens, API secrets | SHUNYA_ARCHITECTURE.md §6.3 |
| Never executes actions | 6.1 Separation of Responsibilities — Each package has exactly one responsibility | SHUNYA_ARCHITECTURE.md §6.1 |
| Explanation graph is immutable after creation | 4.3 No Disappearing Evidence — Evidence is never silently lost | SHUNYA_ENGINEERING_CONSTITUTION.md §4.3 |
| Confidence uses canonical model | 7 (Confidence Model) — No engine may invent its own confidence model | SHUNYA Core Models §7 |
| Context scoped to tenant and purpose | 9 (Multi-Tenant Behaviour) — Tenant isolation, purpose gates | SHUNYA System Flow §9 |
| Hallucination prevention (grounding check) | 2.5 Architectural Trust — No single component can independently compromise correctness | SHUNYA_ARCHITECTURE.md §2.5 |
| Explainability of rejected hypotheses | 2.2 Every Human Should Become a Better Decision Maker — Every interaction leaves the user wiser | SHUNYA_ARCHITECTURE.md §2.2 |

---

## Section 14 — Layer Responsibilities

### The Reasoning Engine SHALL

- Transform knowledge facts, evidence chains, and context into justified, confidence-scored conclusions
- Support multiple reasoning types (deductive, inductive, abductive, probabilistic, constraint-based, policy-aware, temporal, comparative, counterfactual, multi-step)
- Produce a complete explanation graph for every reasoning cycle
- Apply the canonical confidence model (SHUNYA Core Models §7) for all confidence computation
- Detect and document contradictory evidence
- Enforce hallucination prevention through grounding checks
- Respect tenant isolation on all inputs and outputs
- Provide open questions and unknowns when evidence is insufficient
- Package reasoning results as structured planning candidates for the Planner Engine

### The Reasoning Engine SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never execute actions | Would violate Separation of Responsibilities | Executor Engine |
| Never govern (evaluate policies) | Would violate Layer Boundaries | Governance Engine |
| Never learn (generate learning signals) | Would violate Layer Boundaries | Learning Engine |
| Never mutate knowledge (write or supersede facts) | Would violate Layer Boundaries | Knowledge Engine |
| Never access credentials | Would violate Least Authority Principle | Credential Store |
| Never observe reality | Would violate Layer Boundaries | Observer Engine |
| Never plan (create executable plans) | Would violate Layer Boundaries | Planner Engine |
| Never cache reasoning results for reuse | Would violate Compounding Intelligence (each cycle is fresh) | (no caching at this layer) |
| Never fabricate evidence to fill gaps | Would violate Hallucination Prevention | (return unknowns instead) |

---

## Section 15 — Complexity Analysis

### CPU Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Context assembly | O(E × C) | E = evidence items, C = context sections |
| Evidence collection | O(K log N + M) | K = keys requested, N = total facts, M = retrieved |
| Hypothesis generation | O(H × E) | H = hypotheses, E = evidence per hypothesis |
| Evaluation | O(H × C) | H = hypotheses, C = criteria per hypothesis |
| Conflict detection | O(H² × E) | Pairwise comparison of hypotheses |
| Confidence calculation | O(H + E) | Per-hypothesis and per-evidence aggregation |
| Explanation generation | O(S + T) | S = explanation steps, T = trace depth |
| Multi-step reasoning | O(Σ P_i) | Sum of per-stage complexity across all steps |

### Memory Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Full reasoning cycle | O(E + H + S) | Evidence + hypotheses + explanation graph |
| Explanation graph | O(S + T) | Steps + trace depth |
| Evidence set | O(E × avg_evidence_size) | Per-cycle, freed after output |
| Hypothesis set | O(H × avg_hypothesis_size) | Per-cycle, freed after output |

### Storage Growth

- The Reasoning Engine does not maintain persistent storage. All state is per-cycle and ephemeral.
- Explanation graphs are stored by the Knowledge Engine (ES-002) for audit and learning.

### Scaling Bottlenecks

| Bottleneck | Stage | Mitigation |
|------------|-------|------------|
| Evidence retrieval latency | Evidence Collection | Batch evidence requests; parallelize independent queries |
| Hypothesis evaluation | Evaluation | Parallel per-hypothesis evaluation |
| Conflict detection | Conflict Detection | O(H²) — limit H to 10 hypotheses per cycle |
| Multi-step reasoning latency | Entire pipeline | Limit to 5 sequential reasoning steps |

### Failure Isolation

- Each reasoning cycle is fully isolated. A failure in one cycle does not affect any other.
- Reasoning type failure is isolated to that type. Other types continue.
- Context retrieval failure degrades quality but does not crash the engine.
- Knowledge Engine unavailability is detected at Evidence Collection; the cycle returns "insufficient evidence."

---

## Section 16 — Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 16.1 Multi-Model Reasoning

Multiple reasoning models operating on the same input, with results aggregated through voting, weighting, or meta-reasoning. Different models may be optimized for different reasoning types.

### 16.2 Specialist Reasoning Agents

Dedicated reasoning agents for specific domains (travel, healthcare, legal) or specific reasoning types (temporal, causal), invoked by a coordinator agent that routes problems to specialists.

### 16.3 Simulation-Based Reasoning

Reasoning that simulates possible futures using generative models or discrete-event simulation, then evaluates outcomes to select the best course of action.

### 16.4 Predictive Reasoning

Reasoning that forecasts future states based on historical patterns and current context, enabling proactive recommendations rather than reactive ones.

### 16.5 Causal Inference

Reasoning that identifies causal relationships (not just correlations) between events, enabling interventions that address root causes rather than symptoms.

### 16.6 Goal-Oriented Reasoning

Reasoning that works backward from a desired goal to identify the actions required to achieve it, with recursive subgoal decomposition.

### 16.7 Autonomous Deliberation

The Reasoning Engine autonomously decides when to engage in multi-step reasoning, when to request additional context, and when to defer to human judgment — without explicit triggering from the pipeline.

### 16.8 Meta-Reasoning

Reasoning about the reasoning process itself — evaluating which reasoning strategies are effective for which problem types, and dynamically selecting strategies based on past performance.

---

## Section 17 — References

| Document | Relationship |
|----------|-------------|
| **SHUNYA Constitution** (`SHUNYA_ARCHITECTURE.md`) | Supersedes this specification where constitutional principles conflict |
| **SHUNYA Core Models** (`/architecture/SHUNYA_CORE_MODELS.md`) | Defines canonical confidence model (§7), evidence model (§5), provenance model (§6), event envelope (§8) — all inherited by this specification |
| **SHUNYA System Flow** (`/architecture/SHUNYA_SYSTEM_FLOW.md`) | Defines pipeline position (§2), reasoning stage in lifecycle (§2), engine responsibilities (§3), event flow (§5) — this specification's behavioral context |
| **SHUNYA Engineering Constitution** (`/governance/SHUNYA_ENGINEERING_CONSTITUTION.md`) | Article 2 (Evidence-Driven Engineering), Article 8 (Divergence Protocol) — governs this specification |
| **ES-001: Governance Engine** (`/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md`) | Defines the Governance Engine that consumes reasoning results for policy validation |
| **ES-002: Knowledge Engine** (`/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md`) | Defines the Knowledge Engine that supplies facts and evidence chains to reasoning |
| `app/shunya/reasoning.py` | Current ReasoningLayer implementation (233 lines) — v3 with evidence chains and confidence scoring |