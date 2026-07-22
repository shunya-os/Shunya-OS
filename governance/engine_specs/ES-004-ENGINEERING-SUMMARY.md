# Planner Engine — Engineering Summary

**Engine:** Planner Engine (ES-004)
**Layer:** Planner
**Phase:** Phase 2 (Planner Layer)
**Status:** Draft specification

---

## One-Page Summary

### What It Is

The Planner Engine transforms justified reasoning into executable plans. It is the bridge between *what should be done* (Reasoning Engine) and *how to do it* (Executor Engine). It takes reasoning results, constraints, and resources, and produces structured, sequenced, costed, and risk-assessed plans packaged for Governance Engine validation.

### Position in the Pipeline

```
Reasoning → [Planner Engine] → Governance → Executor → Observer
```

### How It Works

The Planner Engine follows a 9-stage pipeline:

1. **Goal Analysis** — Decompose objectives into concrete planning goals
2. **Constraint Resolution** — Identify and resolve conflicts between constraints
3. **Alternative Generation** — Generate multiple viable plan structures
4. **Optimization** — Multi-objective optimization (time, cost, risk, resources, business objectives)
5. **Risk Analysis** — Per-alternative and per-task risk assessment
6. **Resource Planning** — Allocate resources, verify availability
7. **Dependency Graph** — Build ordering constraints, identify critical path
8. **Execution Graph** — Produce time-bound execution sequence
9. **Governance Package** — Package complete plan for validation

### Planning Types

10 planning types compose together: Reactive, Strategic, Operational, Hierarchical, Constraint-based, Resource-aware, Scenario, Contingency, Long-term, Multi-objective.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Optimization | Multi-objective Pareto frontier | Supports trade-off analysis without hardcoding priorities |
| Resource model | 5 resource types with capacity/availability | Covers all resource categories needed for any domain |
| Governance packaging | Mandatory for every plan | No plan reaches execution without governance validation |
| Alternatives | 3–5 per cycle | Enough for meaningful comparison without excessive computation |
| Pipeline stages | 9 deterministic stages | Testable, observable, composable |

### Current Implementation vs Specification

| Aspect | Current (`planner.py`) | Specification Target |
|--------|------------------------|---------------------|
| Planning types | Template-based (4 occasion templates) | 10 composable planning types |
| Optimization | Basic cost estimate only | Multi-objective Pareto optimization |
| Resource model | Not implemented | 5 resource types with capacity/availability |
| Dependency graph | Not implemented (linear day sequence) | Full dependency graph with critical path |
| Risk analysis | Not implemented | Per-alternative and per-task risk |
| Governance packaging | Not implemented | Mandatory governance package |

---

## Open Architectural Questions

1. **How does the Planner Engine retrieve resource availability data?** Resources may be stored in the Knowledge Engine, in external APIs (e.g., hotel inventory), or in tenant configuration. A unified resource provider interface is needed but not yet specified.

2. **How are plan alternatives presented to the Governance Engine?** Are all alternatives submitted for governance, or only the primary plan? If alternatives are submitted, does governance evaluate each one? Recommendation: submit only the primary plan; alternatives are stored for human review if governance returns REVIEW.

3. **What is the optimization objective priority when not specified?** If no explicit weights are provided, the default objective should be: risk minimization > cost minimization > time minimization. This is a product decision, not an engineering decision.

---

## Assumptions Made

| Assumption | Detail |
|------------|--------|
| Resource data is queryable from Knowledge Engine | No separate resource management system |
| Plans fit within 100 tasks | Larger plans are decomposed hierarchically |
| Optimization is deterministic for same inputs | Multi-objective optimization may produce non-deterministic orderings |
| Governance validation completes within latency budget | Complex plans may require extended governance evaluation |

---

## Risks and Dependencies

See full document for 8 failure modes and 7 cross-referenced specifications.

---

**End of Engineering Summary**