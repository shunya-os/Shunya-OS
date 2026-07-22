# ES-004: Planner Engine

**Status:** Draft
**Phase:** Phase 2 (Planner Layer)
**Layer:** Planner
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters the Planner Engine

- **Reasoning result** — justified conclusions, confidence scores, evidence chains, risk flags, alternatives, and open questions from the Reasoning Engine (ES-003)
- **Knowledge references** — pointers to relevant facts in the Knowledge Engine (ES-002) for plan data (destinations, suppliers, pricing, schedules, policies)
- **Policies** — active governance policies that constrain what plans are permissible (from ES-001)
- **Constraints** — explicit boundaries on the plan: budget, time, resources, compliance requirements, human preferences
- **Resources** — available capacity: people, systems, time, money, external services
- **Context** — workspace context from Context Fusion (Phase 10): tenant, actor, purpose, subject, current object
- **Human objectives** — the expressed goals from the user or external system, normalized by the Interface Layer

### What Leaves the Planner Engine

- **Execution plans** — structured, sequenced actions with dependencies, timelines, resource allocations, and cost estimates
- **Alternative plans** — multiple viable options ranked by desirability, risk, and confidence
- **Decision trees** — branching structures showing decision points and their consequences
- **Resource allocations** — what resources are required, when, and for how long
- **Dependency graphs** — the ordering constraints between tasks in the plan
- **Schedules** — time-bound execution sequences with start times, durations, and deadlines
- **Estimated risk** — per-plan and per-task risk assessments (canonical confidence scale)
- **Estimated confidence** — overall confidence that the plan will succeed (canonical 0.0–1.0)
- **Governance package** — the complete plan packaged for Governance Engine validation, including all evidence, reasoning, and estimates

### What Intelligence Is Compounded

The Planner Engine compounds **planning precision** over time. Every plan that is executed produces an outcome that is observed and fed back. Successful plan structures are reinforced; unsuccessful ones are weakened. Over time, the engine learns which planning strategies produce executable, high-confidence plans for which types of problems.

The compounding mechanism is **outcome-feedback via the Learning Engine**: planning patterns that lead to successful execution are stored as knowledge. Future planning cycles retrieve these patterns and apply them to similar problems.

### Which Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Governance Engine | Consumes plans for policy validation | **Critical** — cannot govern without a plan to evaluate |
| Executor Engine | Consumes approved plans for execution | **Critical** — cannot execute without a plan |
| Observer Engine | Compares actual outcomes to planned outcomes | **High** — cannot detect discrepancies without expected outcomes |
| Learning Engine | Analyzes plan-vs-outcome discrepancies | **Medium** — can learn from execution alone, but richer with plan comparison |

### What Fails If It Becomes Unavailable

- **Governance has nothing to validate** — no plans reach the Governance Engine, so no actions can be approved
- **Execution halts** — the Executor Engine has nothing to execute
- **The compounding loop breaks** — planning is the bridge between reasoning and execution; without it, the system can reason but cannot act
- **User experience degrades to template-based** — the system can still respond with pre-defined templates, but cannot generate novel, context-appropriate plans

---

## Section 1 — Mission

### Purpose of the Planner Inside SHUNYA

The Planner Engine transforms justified reasoning into executable plans. It is the bridge between *what should be done* (Reasoning Engine) and *how to do it* (Executor Engine). The Planner does not execute, approve, change knowledge, learn, or bypass governance. It takes reasoning results, constraints, and resources, and produces structured, sequenced, costed, and risk-assessed plans.

The canonical lifecycle (SHUNYA System Flow §2) positions Planning after Reasoning and before Governance:

```
Reasoning → Planning → Governance → Execution → Observation
```

### The Planner SHALL

- Generate executable plans from reasoning results
- Compare multiple alternative plans and rank them
- Optimize plans for time, cost, risk, resources, and business objectives
- Decompose high-level goals into sequenced tasks with dependencies
- Estimate cost, time, risk, and resource requirements for every plan
- Package plans for Governance Engine validation

### The Planner SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never execute plans | Would violate Separation of Responsibilities | Executor Engine |
| Never approve plans | Would violate Governance Before Execution | Governance Engine |
| Never change knowledge | Would violate Layer Boundaries | Knowledge Engine |
| Never learn from outcomes | Would violate Layer Boundaries | Learning Engine |
| Never bypass governance | Would violate Constitutional Principle | Governance Engine |
| Never reason (generate new conclusions) | Would violate Layer Boundaries | Reasoning Engine |
| Never access credentials | Would violate Least Authority Principle | Credential Store |

---

## Section 2 — Inputs

All inputs conform to the canonical models defined in SHUNYA Core Models and the output contracts of the upstream engines.

### Input Contract

```
PlanningInput:
  reasoning_result: ReasoningResult   — From ES-003. Justified conclusions, confidence,
                                         evidence chains, alternatives, risk flags.
  knowledge_refs: KnowledgeRef[]      — Pointers to facts in ES-002. Retrieved as needed.
  policies: Policy[]                  — From ES-001. Active governance policies constraining
                                         permissible plans.
  constraints: Constraint[]           — Explicit boundaries: budget, time, resources,
                                         compliance, preferences.
  resources: Resource[]               — Available capacity: people, systems, time, money,
                                         external services.
  context: WorkspaceContext           — From Context Fusion (Phase 10). Tenant, actor,
                                         purpose, subject, current object.
  objectives: Objective[]             — Human or system goals, normalized.
  request_metadata: RequestInfo       — Tenant ID, actor ID, correlation ID, trace ID.
```

### Input Sources

| Input | Source | Retrieval Method |
|-------|--------|-----------------|
| Reasoning result | Reasoning Engine (ES-003) | Synchronous — output of the reasoning pipeline |
| Knowledge references | Reasoning result (embedded) | Retrieved from Knowledge Engine on demand |
| Policies | Governance Engine (ES-001) | In-memory policy registry snapshot |
| Constraints | Interface Layer, user preferences | Extracted during request normalization |
| Resources | Knowledge Engine, tenant configuration | Structured retrieval |
| Context | Context Fusion (Phase 10) | Pre-assembled before planning |
| Objectives | Human or external system | Normalized by Interface Layer |

### Input Validation

| Field | Constraint | Rejection |
|-------|-----------|-----------|
| `reasoning_result.confidence` | Must be > 0.0 (canonical scale) | `ZERO_CONFIDENCE` — cannot plan from zero-confidence reasoning |
| `reasoning_result.recommendation` | Non-empty | `EMPTY_RECOMMENDATION` — nothing to plan |
| `constraints` | May be empty (unconstrained planning) | Warning — plans may be infeasible |
| `resources` | May be empty (assume unlimited) | Warning — plans may be over-ambitious |
| `context.tenant_id` | Must match request tenant | `TENANT_MISMATCH` |

---

## Section 3 — Outputs

All outputs conform to the canonical models defined in SHUNYA Core Models.

### Output Contract

```
PlanningOutput:
  primary_plan: ExecutionPlan            — The recommended plan
  alternatives: ExecutionPlan[]          — Ranked alternative plans
  decision_tree: DecisionTree            — Branching decision points and consequences
  resource_allocation: ResourceAllocation[] — Required resources per task
  dependency_graph: DependencyGraph      — Ordering constraints between tasks
  schedule: Schedule                     — Time-bound execution sequence
  risk_assessment: RiskAssessment        — Per-plan and per-task risk
  confidence: float                      — Overall plan confidence (canonical 0.0–1.0)
  governance_package: GovernancePackage  — Complete plan packaged for ES-001 validation
  planning_metadata: PlanningInfo        — Engine version, planning types used, timings
```

### Output Destinations

| Output | Destination | Format |
|--------|-------------|--------|
| Primary plan (via governance package) | Governance Engine (ES-001) | `GovernancePackage` — plan + evidence + reasoning |
| Alternative plans | Governance Engine (for REVIEW comparison) | `GovernancePackage[]` |
| Dependency graph | Executor Engine (via approved plan) | Embedded in execution plan |
| Schedule | Executor Engine (via approved plan) | Embedded in execution plan |
| Resource allocation | Executor Engine (via approved plan) | Embedded in execution plan |
| Risk assessment | Governance Engine, Observer Engine | For validation and discrepancy detection |
| Planning metadata | Observer Engine | For observability and learning |

### Output Guarantees

- **Determinism:** Same inputs always produce the same primary plan. Alternatives may be ordered differently if optimization is non-deterministic.
- **Completeness:** Every plan includes a dependency graph, schedule, resource allocation, and risk assessment. No plan is produced without these components.
- **Governance-ready:** Every plan is packaged for Governance Engine validation. No plan bypasses governance.

---

## Section 4 — Planning Pipeline

### Canonical Stages

```
Goal Analysis
     │
     ▼
Constraint Resolution
     │
     ▼
Alternative Generation
     │
     ▼
Optimization
     │
     ▼
Risk Analysis
     │
     ▼
Resource Planning
     │
     ▼
Dependency Graph
     │
     ▼
Execution Graph
     │
     ▼
Governance Package
```

### Stage Definitions

| Stage | Purpose | Inputs | Outputs | Failure Condition |
|-------|---------|--------|---------|-------------------|
| **Goal Analysis** | Decompose high-level objectives into concrete, measurable planning goals | Reasoning result, objectives, context | Structured planning goals | Goals are too ambiguous to decompose |
| **Constraint Resolution** | Identify and resolve conflicts between constraints | Planning goals, constraints, policies | Resolved constraint set with documented trade-offs | Conflicting constraints cannot be resolved |
| **Alternative Generation** | Generate multiple viable plan structures | Resolved constraints, knowledge refs, resources | Candidate plan structures | Zero alternatives generated (over-constrained) |
| **Optimization** | Optimize each alternative against objectives (time, cost, risk, quality) | Candidate plans, optimization criteria | Optimized alternatives with scores | Optimization criteria too ambiguous |
| **Risk Analysis** | Assess risk per alternative and per task | Optimized alternatives, policies, historical outcomes | Risk-scored alternatives | Cannot estimate risk (no historical data) |
| **Resource Planning** | Allocate resources to tasks and verify availability | Risk-scored alternatives, resource pool | Resource-allocated plans | Resource conflict (over-allocation) |
| **Dependency Graph** | Build ordering constraints between tasks | Resource-allocated plans | Dependency graph with critical path | Circular dependency detected |
| **Execution Graph** | Produce the final time-bound execution sequence | Dependency graph, schedule constraints | Time-bound execution graph | Schedule cannot fit within constraints |
| **Governance Package** | Package the complete plan for Governance Engine validation | Complete plan, evidence, reasoning | GovernancePackage | Plan too large for governance validation |

### Transitions

| From | To | Condition | Fallback |
|------|----|-----------|----------|
| Goal Analysis | Constraint Resolution | Goals decomposed | Return "ambiguous goals" error |
| Constraint Resolution | Alternative Generation | Constraints resolved | Relax constraints, document trade-offs |
| Alternative Generation | Optimization | At least one alternative generated | Relax constraints, re-generate |
| Optimization | Risk Analysis | Alternatives optimized | Use un-optimized alternatives |
| Risk Analysis | Resource Planning | Risk assessed | Use default risk (0.5) |
| Resource Planning | Dependency Graph | Resources allocated | Use optimistic allocation |
| Dependency Graph | Execution Graph | No circular dependencies | Break cycle, add coordination task |
| Execution Graph | Governance Package | Schedule valid | Relax schedule, flag warning |
| Any stage | Failure | Unrecoverable error | Return error with stage and reason |

---

## Section 5 — Planning Types

The Planner Engine supports multiple planning types, applied composably. A single planning cycle may use multiple types.

| Planning Type | Description | When Used | Example |
|---------------|-------------|-----------|---------|
| **Reactive** | Generate a plan in response to an immediate stimulus. Minimal analysis, fastest path to execution. | Simple requests, well-understood problems, time-critical situations | "Customer wants hotel recommendations. Generate top 3 based on preferences." |
| **Strategic** | Generate plans that achieve long-term objectives. Considers multiple steps, dependencies, and trade-offs. | Complex goals, multi-step processes, resource-intensive actions | "Plan a 7-day trip to an unfamiliar destination with multiple activities." |
| **Operational** | Generate plans for day-to-day operations. Standardized, repeatable, template-driven. | Routine tasks, standard operating procedures | "Generate a standard invoice for a completed booking." |
| **Hierarchical** | Decompose high-level goals into sub-goals, sub-plans, and individual tasks. Each level has its own planner. | Complex, multi-level problems | "Plan the trip: decompose into flights, accommodation, activities, transport." |
| **Constraint-based** | Generate plans that satisfy a set of explicit constraints. Used when feasibility is the primary concern. | Budget-limited, time-limited, resource-limited scenarios | "Find a plan that fits within ₹50,000 budget and 5-day window." |
| **Resource-aware** | Generate plans that respect resource availability and capacity. | Shared resources, limited capacity, scheduling conflicts | "Schedule three parallel activities without exceeding vehicle capacity." |
| **Scenario** | Generate plans for multiple possible futures. Each scenario has its own plan. | Uncertainty about future conditions | "Generate plans for sunny weather, rainy weather, and mixed weather." |
| **Contingency** | Generate primary plan + backup plans for critical path items. | High-risk activities, irreversible decisions, tight deadlines | "Primary: flight to destination. Contingency: train to destination if flight cancelled." |
| **Long-term** | Generate plans that span extended time horizons with periodic re-evaluation. | Large projects, multi-phase initiatives | "Annual marketing plan with quarterly reviews and monthly campaigns." |
| **Multi-objective** | Generate plans that optimize for multiple, potentially conflicting objectives simultaneously. | Trade-off analysis, stakeholder negotiation | "Optimize for cost AND quality AND speed. Generate Pareto-optimal alternatives." |

---

## Section 6 — Optimization

### Optimization Dimensions

| Dimension | Description | Measurement | Trade-off |
|-----------|-------------|-------------|-----------|
| **Time** | Minimize total plan duration or meet a deadline | Days, hours, minutes | Faster may cost more or increase risk |
| **Cost** | Minimize total financial cost or stay within budget | Currency units | Cheaper may take longer or reduce quality |
| **Risk** | Minimize probability of failure or adverse outcomes | Canonical confidence (0.0–1.0) | Lower risk may cost more or take longer |
| **Resources** | Minimize resource consumption or balance load | Person-hours, system capacity, units | Efficient resource use may increase complexity |
| **Business objectives** | Maximize alignment with business goals | Weighted score per objective | May conflict with other dimensions |
| **Human preferences** | Maximize alignment with stated human preferences | Weighted score per preference | Subjective, may be inconsistent |

### Optimization Approach

The Planner Engine uses multi-objective optimization to generate Pareto-optimal alternatives. Each alternative is scored along all dimensions. The result is a set of non-dominated alternatives where no dimension can be improved without degrading another.

**Optimization function:**
```
score(plan) = Σ(weight_i * normalized_score(plan, dimension_i))
```

Where `weight_i` is the priority of dimension `i` (from constraints and preferences) and `normalized_score` maps the raw dimension value to a 0.0–1.0 scale.

### Trade-off Analysis

When dimensions conflict, the Planner Engine presents the trade-off explicitly:

- "Option A is 20% cheaper but takes 30% longer."
- "Option B has lower risk but costs 15% more."
- "Option C is fastest but exceeds the budget by 10%."

Trade-offs are included in the governance package so the Governance Engine and human reviewers can make informed decisions.

---

## Section 7 — Resource Model

### Resource Types

| Resource Type | Description | Measured In | Capacity Model |
|---------------|-------------|-------------|----------------|
| **People** | Human operators, team members, external personnel | Headcount, hours available | Per-person calendar with availability |
| **Systems** | Software systems, API endpoints, compute capacity | API calls, compute units, concurrent requests | Rate limits, throughput caps |
| **Time** | Wall-clock time, working hours, deadlines | Days, hours, minutes | Calendar with working hours and holidays |
| **Money** | Budget, funds, payment capacity | Currency units | Per-plan budget, per-task cost |
| **External services** | Third-party services: hotels, transport, venues | Units of service (room nights, seats, slots) | Supplier inventory, booking windows |

### Capacity and Availability

- Resources have a `total_capacity` and `available_capacity` at any point in time.
- Resource availability is queried from the Knowledge Engine (ES-002) and refreshed per planning cycle.
- If a resource is over-allocated, the Planner Engine either:
  - Rejects the plan (constraint violation)
  - Suggests alternative resources
  - Flags the conflict for human resolution

### Resource Allocation

Every task in an execution plan carries a resource allocation:

```
ResourceAllocation:
  task_id: string
  resource_type: string
  resource_id: string
  quantity: number
  unit: string
  start_time: datetime
  end_time: datetime
  cost: number
  currency: string
```

---

## Section 8 — Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Impossible plan | Constraints are too tight or contradictory | Constraint Resolution stage | No plan generated | Return "impossible plan" with explanation of which constraints conflict |
| Resource conflict | Two or more tasks require the same resource at the same time | Resource Planning stage | Plan cannot be scheduled | Suggest alternative scheduling or alternative resources |
| Policy conflict | Plan violates an active governance policy | Governance Package stage (pre-validation) | Plan rejected before governance submission | Remove policy-violating elements, document the constraint |
| Circular dependency | Task A depends on Task B which depends on Task A | Dependency Graph stage | Invalid dependency graph | Break the cycle by adding a coordination task or re-ordering |
| Missing resources | Required resource is not available or does not exist | Resource Planning stage | Plan cannot be completed | Suggest alternative resources or flag as infeasible |
| Uncertain estimates | Cost, time, or risk estimates have low confidence | Risk Analysis stage | Low-confidence plan | Return plan with confidence warning; governance may flag as REVIEW |
| Low confidence | Reasoning result confidence is below planning threshold | Pre-planning validation | Cannot generate reliable plan | Return "insufficient confidence" with reasoning gaps |
| Incomplete goals | Objectives are too ambiguous to decompose | Goal Analysis stage | Cannot generate structured goals | Request clarification from the human or Interface Layer |

---

## Section 9 — Interaction Matrix

| Layer / Engine | Reads | Writes | Events Published | Events Consumed |
|----------------|-------|--------|-----------------|-----------------|
| **Reasoning Engine** (ES-003) | Reasoning result | — | — | `reasoning.completed` |
| **Knowledge Engine** (ES-002) | Facts, policies, resource data, historical plans | — | — | — |
| **Governance Engine** (ES-001) | Policy definitions | — | `plan.created` | `governance.action.approved` (for confirmation), `governance.action.rejected` (for re-planning) |
| **Executor Engine** | — | Execution plans (via governance) | — | — |
| **Context Fusion** (Phase 10) | Workspace context | — | — | `context.fusion.completed` |
| **Observer Engine** | — | — | `plan.created` | — |
| **Learning Engine** | — | — | — | `learning.signal.generated` (for planning pattern updates) |

### Dependencies

| Dependency | Type | Criticality |
|------------|------|-------------|
| Reasoning Engine (ES-003) | Input | **Critical** — cannot plan without justified conclusions |
| Knowledge Engine (ES-002) | Read | **High** — cannot resource or cost plans without data |
| Governance Engine (ES-001) | Output / Read | **High** — must read policies and send plans for validation |
| Context Fusion (Phase 10) | Read | **Medium** — can plan with degraded context |

### Ownership

- The Planner Engine **owns** the planning pipeline, alternative generation, optimization, and governance packaging.
- It **does not own** facts, policies, resources, execution, or governance decisions.
- It **shares ownership** of plan confidence with the Reasoning Engine (input confidence) and the Governance Engine (validated confidence).

---

## Section 10 — Performance

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| **Latency p50** | < 500ms | Per planning cycle (simple plans) |
| **Latency p50 (complex)** | < 5s | Per planning cycle (multi-objective, hierarchical) |
| **Latency p99** | < 10s | Per planning cycle |
| **Alternatives per cycle** | 3–5 | Number of viable alternatives generated |
| **Tasks per plan** | < 100 | Maximum tasks in a single plan |
| **Optimization candidates** | < 50 | Candidate plans evaluated during optimization |
| **Resource allocation time** | < 200ms | Per resource allocation pass |

### Scaling

- The Planner Engine is stateless. Horizontal scaling is achieved by adding instances behind a load balancer.
- No shared state between instances except the Knowledge Engine (read-mostly) and the policy registry (read-mostly).
- Complex planning (hierarchical, multi-objective, long-term) is compute-bound and may benefit from dedicated instances.

### Scheduling Complexity

| Planning Type | Complexity | Notes |
|---------------|------------|-------|
| Reactive | O(1) | Template-based, no optimization |
| Constraint-based | O(C × T) | C = constraints, T = tasks |
| Resource-aware | O(R × T) | R = resources, T = tasks |
| Hierarchical | O(L × P) | L = levels, P = plans per level |
| Multi-objective | O(A × D) | A = alternatives, D = dimensions |
| Contingency | O(P × C) | P = primary tasks, C = contingency branches |

### Optimization Complexity

| Optimization | Complexity | Notes |
|--------------|------------|-------|
| Single-objective (time, cost, or risk) | O(A log A) | Sort alternatives by objective |
| Multi-objective (Pareto) | O(A² × D) | Pairwise comparison, D dimensions |
| Constraint satisfaction | O(C × T²) | C = constraints, T = tasks |

---

## Section 11 — Security

### Tenant Isolation

- All planning is scoped to the requesting tenant's `tenant_id`.
- Resource data, policy definitions, and historical plans are retrieved per-tenant.
- No cross-tenant plan leakage.

### Privacy

- Plans may contain personal data (customer names, preferences, contact information). Personal data is included only when essential to the plan.
- Plans are stored in the Knowledge Engine with privacy classifications (via Phase 4 integration).
- The Planner Engine does not cache personal data between planning cycles.

### Authorization

- The Planner Engine does not enforce authorization. Authorization is enforced by the Governance Engine (ES-001) during plan validation.
- The Planner Engine assumes the request has passed authentication and authorization checks at the Interface Layer.

### Auditability

- Every plan is packaged with full provenance: reasoning result, evidence chains, constraints, resources, and optimization parameters.
- Plans are stored in the Knowledge Engine (ES-002) for audit.
- Plan-audit records are immutable after creation.

---

## Section 12 — Observability

### Metrics

| Metric | Type | Unit | Target |
|--------|------|------|--------|
| `planner.cycles_total` | Counter | cycles | Per second |
| `planner.latency_p50` | Histogram | ms | < 500ms |
| `planner.latency_p99` | Histogram | ms | < 10s |
| `planner.alternatives_generated` | Histogram | count | Per cycle |
| `planner.plans_optimized` | Counter | plans | Per second |
| `planner.failures_total` | Counter | failures | Per second (by failure type) |
| `planner.tasks_per_plan` | Histogram | count | Per plan |
| `planner.confidence_p50` | Histogram | float | Per plan |
| `planner.optimization_time` | Histogram | ms | Per optimization pass |
| `planner.plans_submitted_to_governance` | Counter | plans | Per second |
| `planner.plans_approved` | Counter | plans | Per second (from governance feedback) |
| `planner.plans_rejected` | Counter | plans | Per second (from governance feedback) |

### Tracing

- **Span: `planner.cycle`** — Full planning lifecycle
  - Child span: `planner.goal_analysis`
  - Child span: `planner.constraint_resolution`
  - Child span: `planner.alternative_generation`
  - Child span: `planner.optimization`
  - Child span: `planner.risk_analysis`
  - Child span: `planner.resource_planning`
  - Child span: `planner.dependency_graph`
  - Child span: `planner.execution_graph`
  - Child span: `planner.governance_packaging`
- Trace context propagated from caller (Reasoning Engine or Interface Layer)

### Planning Quality Metrics

| Metric | Purpose |
|--------|---------|
| **Plan acceptance rate** | How often plans are approved by governance (vs rejected or flagged REVIEW) |
| **Plan success rate** | How often approved plans succeed during execution |
| **Estimate accuracy** | How accurate cost, time, and risk estimates turn out to be |
| **Optimization effectiveness** | How much better the optimized plan is vs the un-optimized baseline |
| **Constraint satisfaction** | How often plans satisfy all stated constraints |

---

## Section 13 — Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Generate executable plans from reasoning | 5 (Planner Layer) — Creates plans from reasoning, multi-format output | SHUNYA_ARCHITECTURE.md §5 |
| Multi-format output (text, HTML, structured data) | 5 (Planner Layer) — Multi-format output | SHUNYA_ARCHITECTURE.md §5 |
| Plans include timeline, cost, risk, alternatives | 5 (Planner Layer) — Plans include timeline, cost breakdown, risk assessment, alternatives | SHUNYA_ARCHITECTURE.md §5 |
| Never execute plans | 6.1 Separation of Responsibilities | SHUNYA_ARCHITECTURE.md §6.1 |
| Never approve plans | 6.6 Governance Before Execution | SHUNYA_ARCHITECTURE.md §6.6 |
| Plans are confidence-scored (canonical model) | 6.5 Explainable Decisions | SHUNYA_ARCHITECTURE.md §6.5 |
| Plans are packaged for governance validation | 6.6 Governance Before Execution | SHUNYA_ARCHITECTURE.md §6.6 |
| Plans carry provenance (reasoning → evidence → plan) | 4.2 Every Decision Is Traceable | SHUNYA_ENGINEERING_CONSTITUTION.md §4.2 |
| Tenant isolation on all planning data | 9 (Multi-Tenant Behaviour) | SHUNYA System Flow §9 |
| Resource allocations are auditable | 10 (Every workflow is auditable) | SHUNYA System Flow §14 |

---

## Section 14 — Layer Responsibilities

### The Planner Engine SHALL

- Generate executable plans from justified reasoning results
- Compare multiple alternative plans and rank them by confidence, cost, risk, and resource efficiency
- Optimize plans for time, cost, risk, resources, and business objectives
- Decompose high-level goals into sequenced, dependency-resolved tasks
- Estimate cost, time, risk, and resource requirements for every plan
- Package every plan for Governance Engine validation
- Include evidence chains, reasoning paths, and confidence scores in every governance package
- Respect tenant isolation on all planning data
- Produce plans that are auditable, explainable, and verifiable

### The Planner Engine SHALL NEVER

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never execute plans | Would violate Separation of Responsibilities | Executor Engine |
| Never approve plans | Would violate Governance Before Execution | Governance Engine |
| Never change knowledge | Would violate Layer Boundaries | Knowledge Engine |
| Never learn from outcomes | Would violate Layer Boundaries | Learning Engine |
| Never bypass governance | Would violate Constitutional Principle | Governance Engine |
| Never reason (generate new conclusions) | Would violate Layer Boundaries | Reasoning Engine |
| Never access credentials | Would violate Least Authority Principle | Credential Store |
| Never observe reality | Would violate Layer Boundaries | Observer Engine |
| Never modify plans after governance submission | Would violate Auditability | Governance Engine (plan is frozen post-submission) |

---

## Section 15 — Complexity Analysis

### CPU Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Goal analysis | O(G × D) | G = goals, D = decomposition depth |
| Constraint resolution | O(C²) | C = constraints, pairwise conflict detection |
| Alternative generation | O(A × T) | A = alternatives, T = tasks per alternative |
| Optimization (single-objective) | O(A log A) | Sort by objective |
| Optimization (multi-objective) | O(A² × D) | Pareto frontier, D dimensions |
| Risk analysis | O(A × T) | Per alternative, per task |
| Resource planning | O(R × T) | R = resources, T = tasks |
| Dependency graph | O(T²) | T = tasks, pairwise dependency check |
| Governance packaging | O(P) | P = plan size |

### Memory Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Plan storage per cycle | O(A × T) | Alternatives × tasks |
| Dependency graph | O(T + E) | T = tasks, E = edges |
| Resource allocation | O(R × T) | R = resources, T = tasks |
| Governance package | O(P) | P = plan size (serialized) |

### Storage Growth

- The Planner Engine does not maintain persistent storage. All state is per-cycle and ephemeral.
- Plans are stored by the Knowledge Engine (ES-002) for audit and learning.
- Historical plans grow at the rate of approximately 1KB per plan.

### Scaling Bottlenecks

| Bottleneck | Stage | Mitigation |
|------------|-------|------------|
| Constraint resolution | Constraint Resolution | Capped at 50 constraints; exceeding triggers simplification |
| Multi-objective optimization | Optimization | Capped at 50 alternatives and 5 dimensions |
| Resource allocation | Resource Planning | Capped at 100 tasks and 20 resource types |
| Dependency graph | Dependency Graph | Cycle detection is O(T²); capped at 100 tasks |

### Failure Isolation

- Each planning cycle is fully isolated. A failure in one cycle does not affect any other.
- Planning type failure is isolated to that type. Other types continue.
- Resource retrieval failure degrades quality but does not crash the engine.
- Reasoning Engine unavailability is detected at input validation; the cycle returns "cannot plan — no reasoning result."

---

## Section 16 — Future Extensions

The following capabilities are anticipated but not specified for implementation. They are documented here to inform the architecture and avoid design decisions that would preclude them.

### 16.1 Autonomous Planning

The Planner Engine autonomously determines when to initiate planning, when to re-plan, and when to escalate — without explicit triggering from the pipeline. Enabled by Watch/Monitoring (Phase 12A) signals.

### 16.2 Simulation-Based Planning

Plans are validated through discrete-event simulation before submission to governance. Simulation reveals hidden conflicts, resource contention, and schedule violations before they occur in production.

### 16.3 Monte Carlo Planning

Generate thousands of plan variants through random sampling, evaluate each against objectives, and select the best-performing distribution. Useful for high-uncertainty scenarios.

### 16.4 Predictive Planning

The Planner Engine anticipates future states and pre-generates plans for likely scenarios. When a scenario materializes, the pre-generated plan is available immediately.

### 16.5 Adaptive Planning

Plans that adapt in real-time based on execution feedback. If a task takes longer than estimated, the plan automatically adjusts subsequent tasks without requiring a full re-planning cycle.

### 16.6 Collaborative Planning

Multiple Planner Engines or human planners collaborating on a single plan, each contributing their domain expertise. Plans are merged through a reconciliation process.

### 16.7 Distributed Planning

Planning tasks are distributed across multiple Planner Engine instances, each responsible for a sub-plan. Sub-plans are merged into a coherent overall plan.

### 16.8 Goal Negotiation

When goals are infeasible, the Planner Engine negotiates with the goal-setter (human or system) to find acceptable trade-offs, rather than simply rejecting the goals.

---

## Section 17 — References

| Document | Relationship |
|----------|-------------|
| **SHUNYA Constitution** (`SHUNYA_ARCHITECTURE.md`) | Supersedes this specification where constitutional principles conflict |
| **SHUNYA Core Models** (`/architecture/SHUNYA_CORE_MODELS.md`) | Defines canonical confidence model (§7), evidence model (§5), provenance model (§6) — all inherited by this specification |
| **SHUNYA System Flow** (`/architecture/SHUNYA_SYSTEM_FLOW.md`) | Defines pipeline position (§2), planning stage in lifecycle (§2), engine responsibilities (§3) — this specification's behavioral context |
| **SHUNYA Engineering Constitution** (`/governance/SHUNYA_ENGINEERING_CONSTITUTION.md`) | Article 2 (Evidence-Driven Engineering), Article 8 (Divergence Protocol) — governs this specification |
| **ES-001: Governance Engine** (`/governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md`) | Defines the Governance Engine that validates plans |
| **ES-002: Knowledge Engine** (`/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md`) | Defines the Knowledge Engine that supplies facts and resource data |
| **ES-003: Reasoning Engine** (`/governance/engine_specs/ES-003-REASONING-ENGINE.md`) | Defines the Reasoning Engine that supplies justified conclusions for planning |
| `app/shunya/planner.py` | Current PlannerLayer implementation (354 lines) — v2 with template-based itinerary generation and proposal output |