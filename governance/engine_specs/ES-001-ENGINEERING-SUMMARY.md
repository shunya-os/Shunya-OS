# Governance Engine — Engineering Summary

**Engine:** Governance Engine (ES-001)
**Layer:** Governance
**Phase:** Phase 2
**Status:** Draft specification

## One-Page Summary

### What It Is

The Governance Engine is the independent validation gate between Planning and Execution. Every proposed action — whether a complex plan from the Planner Layer or a single action request from the Interface — must pass through governance before reaching the Executor. The engine evaluates the proposal against constitutional principles, registered business policies, and risk thresholds, then returns one of three verdicts: **APPROVE**, **REVIEW** (requires human approval), or **REJECT**.

### Why It Exists

The SHUNYA Constitution mandates that no single component can independently compromise correctness, security, or execution. The Governance Engine is that guarantee. Even if the Reasoning Layer produces a bad recommendation, Governance can stop it. No action reaches execution without policy validation.

### How It Works

```
Proposal → Validate Context → Validate Constitution → Evaluate Policies → Assess Risk → Verdict
```

1. **Receiving** — Validates the input structure (action type, proposal, context, evidence chain)
2. **Validating Context** — Enriches the context with computed fields (pax count, lead time, estimated cost, international flag, wedding flag)
3. **Validating Constitution** — Checks constitutional compliance (e.g., "AI Proposes, Humans Dispose" for REVIEW-severity decisions)
4. **Evaluating Policies** — Runs all applicable policies from the Policy Registry against the enriched context
5. **Assessing Risk** — Computes overall risk from policy results, confidence scores, and evidence completeness
6. **Returning Verdict** — Delivers APPROVE, REVIEW, or REJECT with evidence chain, explanation, and audit trail

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Evaluation engine | Deterministic, no LLM calls | Governance must be 100% predictable and verifiable |
| Policy conditions | Safe expression evaluator (NOT eval()) | The existing eval() with restricted globals must be replaced |
| Audit log | Append-only, immutable | Every decision is permanently traceable |
| Tenant isolation | Per-tenant policy scoping | One tenant's policies never affect another's evaluations |
| Decision states | 3 verdicts (APPROVE, REVIEW, REJECT) | Covers all constitutional requirements |

### Current Implementation vs Specification

| Aspect | Current (app/shunya/governance.py) | Specification Target |
|--------|--------------------------------------|---------------------|
| Policy evaluation | eval() with restricted globals | Safe expression evaluator or compiled rule engine |
| Policy count | 9 default policies | Extensible, domain-specific policy sets |
| Human review workflow | REVIEW verdict possible but no delivery mechanism | REVIEW verdict triggers human review queue event |
| Audit log | In-memory list | Persistent, append-only audit log |
| Constitutional rules | None — all policies are business rules | Hard separation between constitutional rules and business policies |
| Integration | Called directly by ShunyaInterface | Event-driven via Event Bus |

### Architectural Position

```
Planner → [Governance Engine] → Executor → Observer
             ↑
        Reasoning (evidence chain)
```

Governance is **not** a pass-through. It is an independent validator that shares no state with the layers it evaluates. It receives a proposal, applies rules, and returns a verdict. It never modifies the proposal.

---

## Open Architectural Questions

1. **Where does the safe expression evaluator come from?** The existing implementation uses `eval()` with restricted globals. The specification requires replacing this. The question is: build a custom expression parser, adopt a minimal expression language (e.g., expr-lang, cel-go), or extend the current restricted-eval pattern with additional sandboxing? This is an **Engineering ADR** candidate.

2. **How are constitutional rules separated from business policies?** The specification defines a future Constitutional Rule Engine (Section 17.8). The question is whether this separation should exist from the start or be introduced when the first non-constitutional policy is written. A constitutional rule is one that cannot be overridden by any business policy — e.g., "No action may execute without governance approval." If all current policies are constitutional-equivalent, this distinction is future work.

3. **What is the data model for the persistent audit log?** The specification requires an immutable, append-only audit log. The question is: use the existing PostgreSQL database (with an append-only table), write-ahead log, or a separate immutable store (e.g., Event Store, AWS QLDB)? Using PostgreSQL with an append-only table (no UPDATE, no DELETE) is the simplest starting point.

4. **How does the human review workflow get notified?** The specification requires that REVIEW verdicts surface for human approval. The question is: does this happen through the existing notification system, a new human review queue table, or an event bus event consumed by a review UI? This depends on Phase 17 (Continuous Surface) which is deferred.

5. **What is the latency budget for the first implementation?** The specification targets 50ms p50 / 200ms p99. If the safe expression evaluator is slower than eval(), the budget may need adjustment. This should be measured during implementation.

---

## Assumptions Made

| Assumption | Detail | Validated? | Assumed Until |
|------------|--------|-----------|---------------|
| All governance decisions are synchronous | No asynchronous policy evaluation paths | No | Implementation begins |
| Policy registry is in-memory (not a separate service) | Policies are loaded at startup and updated via events | No | First deployment with >1 instance |
| Audit log uses the same PostgreSQL database | No separate audit store | No | Scale requires >10K decisions/day |
| Tenant isolation via tenant_id foreign key | No separate database per tenant | No | Multi-tenant audit requirement |
| Human review is out-of-band | Governance emits an event; a separate system handles the UI | No | Phase 17 implementation |
| Constitutional rules are implicit in policy design | No hard separation between constitutional and business rules | No | First constitutional conflict detected |
| All policies are evaluated every time | No short-circuit optimization for high-traffic paths | No | Performance testing reveals bottleneck |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **eval() replacement introduces regressions** | Medium | High | Comprehensive test suite for all 9 default policies before and after replacement |
| **Governance becomes a bottleneck** | Low | High | Stateless, no I/O, 50ms latency budget, horizontal scaling |
| **Policy conflicts produce unexpected verdicts** | Medium | Medium | Post-evaluation conflict detection, REVIEW on conflict, conflict documentation |
| **Tenant isolation violated by policy scope** | Low | Critical | Every policy evaluation explicitly scoped to tenant_id; integration test for cross-tenant leakage |
| **Human review queue grows unbounded** | Medium | Medium | REVIEW verdicts require time-boxed human response; auto-REJECT after timeout |
| **Governance bypassed by fast path** | Low | Critical | Executor Layer must always call Governance; integration test enforces this |
| **Audit log grows without bound** | High | Low | Append-only log with retention policy; archival after 90 days |
| **Specification diverges from implementation during development** | Medium | Medium | Specification is updated as architecture decisions are made; ADRs document significant changes |

---

## Dependencies

| Dependency | Type | Status | Required By |
|------------|------|--------|-------------|
| Safe expression evaluator | Implementation choice | **Open question** | Implementation phase |
| Policy Registry data model | Design decision | Defined in spec | Implementation phase |
| Immutable audit log table | Database migration | Not yet created | Implementation phase |
| Event Bus | Infrastructure | Exists in worktree | Implementation phase (for events) |
| Human review queue | Design decision | **Open question** | Phase 17 or earlier decision |
| Constitutional rule definitions | Policy content | 9 default policies exist | Implementation phase |
| Tenant model | Database | Exists (app/tenant.py) | Implementation phase |
| Phase 4 (Privacy) eligibility gates | Integration | Computation-only | Future integration |
| Phase 10 (Context Fusion) | Integration | Computation-only | Future integration |

---

**End of Engineering Summary**