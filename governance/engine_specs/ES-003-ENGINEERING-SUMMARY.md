# Reasoning Engine — Engineering Summary

**Engine:** Reasoning Engine (ES-003)
**Layer:** Reasoning
**Phase:** Phase 2 (Reasoning Layer)
**Status:** Draft specification

---

## One-Page Summary

### What It Is

The Reasoning Engine transforms knowledge into justified conclusions. It is the bridge between *what is known* (Knowledge Engine) and *what should be done* (Planner Engine). It receives facts, evidence, context, and intent, and produces confidence-scored, explainable recommendations with full provenance.

### Position in the Pipeline

```
Context Fusion → [Reasoning Engine] → Planner → Governance → Executor
```

The Reasoning Engine sits after Context Fusion (which assembles the workspace context) and before Planning (which creates executable plans from reasoning results). It does not execute, govern, learn, or mutate knowledge.

### How It Works

The Reasoning Engine follows a 9-stage pipeline:

1. **Observation** — Receive and normalize the stimulus
2. **Context Assembly** — Select relevant context for the reasoning problem
3. **Evidence Collection** — Retrieve facts and evidence chains from the Knowledge Engine
4. **Hypothesis Generation** — Generate candidate interpretations using 10 reasoning types
5. **Evaluation** — Score each hypothesis against evidence, context, and constraints
6. **Conflict Detection** — Identify contradictory evidence or incompatible hypotheses
7. **Confidence Calculation** — Compute overall and per-step confidence (canonical model)
8. **Explanation Generation** — Build a structured explanation graph
9. **Planning Candidate** — Package the result for the Planner Engine

### Reasoning Types

The engine supports 10 composable reasoning types: Deductive, Inductive, Abductive, Probabilistic, Constraint-based, Policy-aware, Temporal, Comparative, Counterfactual, and Multi-step. A single reasoning cycle may use multiple types in sequence or in parallel.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Reasoning types | 10 composable types | Covers all constitutional reasoning requirements without over-engineering |
| Hallucination prevention | Grounding check on every inference | Hard requirement — every inference must reference specific evidence |
| Explanation graph | Structured graph with nodes, edges, types | Machine-readable for audit, human-readable for explainability |
| Confidence | Canonical model (Core Models §7) | No redefinition — inherited from the architecture standard |
| Pipeline | 9 deterministic stages | Deterministic, testable, observable |
| Statelessness | No per-cycle caching | Each reasoning cycle is fresh; the compounding loop handles improvement |

### Current Implementation vs Specification

| Aspect | Current (`reasoning.py`) | Specification Target |
|--------|--------------------------|---------------------|
| Reasoning types | Rule-based pattern matching only | 10 composable reasoning types |
| Confidence | Simple scoring (0.3 or 0.9) | Full canonical model with propagation, combination, decay |
| Explainability | Text-based explanation | Structured explanation graph |
| Pipeline | Single `analyze_inquiry()` method | 9-stage pipeline with defined transitions |
| Hallucination prevention | Not implemented | Grounding check on every inference |
| Reasoning types | Hardcoded travel patterns | Extensible, configurable per domain |
| Multi-step reasoning | Not supported | Composition of reasoning types |

---

## Open Architectural Questions

1. **How are reasoning type implementations provided?** Ten reasoning types are defined. Are they all implemented as built-in logic, or are some provided by external models (e.g., probabilistic reasoning via a statistical engine, temporal reasoning via a constraint solver)? Recommendation: implement Deductive, Constraint-based, and Comparative as built-in logic first; defer Abductive, Inductive, and Probabilistic to Phase 2.

2. **Where does the explanation graph get stored?** The specification says explanation graphs are stored in the Knowledge Engine for audit and learning. This increases the Knowledge Engine's write volume significantly. Is the Knowledge Engine's write path designed for this? If not, explanation graphs may need a separate storage path.

3. **How does multi-step reasoning compose with the 9-stage pipeline?** Multi-step reasoning could mean: (a) a single reasoning cycle runs multiple types sequentially, or (b) the pipeline itself loops (output of one cycle feeds into the next). The specification assumes (a). If (b) is needed, the pipeline must support recursion.

4. **What is the hallucination prevention enforcement mechanism?** Grounding checks are specified but not implemented. Is this enforced at the reasoning type level (each type verifies its own grounding) or at the pipeline level (a post-hoc check after all types complete)? Pipeline-level enforcement is simpler but may catch errors later.

---

## Assumptions Made

| Assumption | Detail | Validated? | Assumed Until |
|------------|--------|-----------|---------------|
| Reasoning is synchronous | No async reasoning paths | No | First requirement for async reasoning |
| 10 hypotheses per cycle is sufficient | Hard limit prevents unbounded computation | No | Real-world testing reveals need for more |
| Evidence retrieval is fast (< 50ms) | Knowledge Engine latency is within budget | No | Production deployment with realistic data volumes |
| Explanation graphs fit in memory | No streaming or pagination needed | No | Graph exceeds 1000 nodes |
| Policy registry is read-only during reasoning | Policies don't change mid-cycle | Yes | Policy registry snapshot at cycle start |
| All reasoning types are deterministic | No randomness in any reasoning type | No | Probabilistic reasoning is inherently non-deterministic |
| Single-tenant per reasoning cycle | No cross-tenant reasoning | Yes | Constitutional requirement |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Hallucination prevention is incomplete** | Medium | Critical | Multiple layers of grounding check; explicit unknowns; Governance review of low-confidence results |
| **Reasoning is too slow for real-time use** | Medium | High | Parallel reasoning types; latency budgets; graceful degradation to simpler types |
| **10 reasoning types are too many to implement** | High | Medium | Implement in priority order: Deductive, Constraint-based, Comparative first |
| **Explanation graph storage overwhelms Knowledge Engine** | Medium | Medium | Separate explanation graph storage path; retention policy for graphs older than 90 days |
| **Policy-aware reasoning creates circular dependency with Governance** | Low | Medium | Reasoning reads policies (read-only); Governance evaluates plans (read-only). No circular mutation. |
| **Multi-step reasoning creates unmanageable complexity** | Medium | Medium | Limit to 5 sequential steps; enforce step-level timeout |

---

## Dependencies

| Dependency | Type | Status | Required By |
|------------|------|--------|-------------|
| Knowledge Engine (ES-002) | Read — facts, evidence | `knowledge_store.py` exists, not wired | Implementation phase |
| Context Fusion (Phase 10) | Read — workspace context | Computation-only | Future integration |
| Governance Engine (ES-001) | Read — policy registry | Production | Implementation phase |
| Canonical confidence model | Reference | Defined in Core Models §7 | Implementation phase |
| Canonical event envelope | Reference | Defined in Core Models §8 | Implementation phase |
| Explanation graph schema | Design | Defined in this spec | Implementation phase |
| Hallucination prevention checks | Implementation | Not yet implemented | Implementation phase |
| Reasoning type implementations (10) | Implementation | 1 exists (rule-based) | Implementation phase (priority order) |

---

**End of Engineering Summary**