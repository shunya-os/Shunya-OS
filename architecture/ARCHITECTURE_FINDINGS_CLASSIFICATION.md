# SHUNYA Architecture Findings Classification

**Date:** 2026-07-18
**Authority:** G2.0 Architecture Baseline Review
**Objective:** Classify every finding from ARCHITECTURE_BASELINE_REVIEW.md into exactly one category.
**Decision Rule:** If a finding has multiple possible classifications, the highest-severity category wins.

---

## Classification Categories

| Category | Definition | Action Required | Example |
|----------|------------|----------------|---------|
| **A. Blocking architectural defect** | The architecture as specified cannot produce a correct, functional system without this being resolved. | Must be resolved before any implementation. Requires constitutional authority or Chief Software Architect decision. | Missing layer in the pipeline; circular dependency; constitutional principle violated. |
| **B. Required supporting architecture** | A supporting component, ADR, or standard that the architecture depends on but does not define. | Must be created before implementation of the dependent engine. Engineering ADR or short specification. | Event Bus specification; Credential Store interface; missing engine spec. |
| **C. Implementation concern** | An issue that will be resolved during implementation without requiring architecture changes. | Noted for the implementation team. May require a minor spec amendment (documentation clarification). | Formula clarification; documentation gap; observer sampling rate distinction. |
| **D. Product decision** | Requires input from product or constitutional authority. The architecture correctly identifies the decision point but cannot resolve it. | Escalated to the appropriate authority. The architecture defers the decision. | Human review queue location; optimization priority defaults. |
| **E. Future enhancement** | A desirable capability that is out of scope for the current architecture baseline. | Logged for future consideration. Does not block anything. | New reasoning type; additional optimization dimension. |

---

## Classification Results

### A. Blocking Architectural Defect

**None found.**

No findings in this category. The architecture is structurally sound, constitutionally compliant, and has no circular dependencies, missing layers, or orphaned interfaces.

---

### B. Required Supporting Architecture

| ID | Finding | Rationale | Impact | Recommended Resolution | Latest Phase |
|----|---------|-----------|--------|----------------------|--------------|
| **M1 / R2 / ADR-001** | Event Bus Not Specified | The Event Bus is referenced in every engine spec as the primary inter-engine communication mechanism, but no specification defines its instantiation, configuration, partitioning, delivery guarantees, or operational characteristics. | **Blocks** implementation of any engine that publishes or consumes events (all 7 pipeline engines). Without an Event Bus, engines cannot communicate asynchronously. The canonical event envelope exists (Core Models §8) but the bus itself does not. | File Engineering ADR defining the Event Bus as shared infrastructure. The envelope is already specified; this covers instantiation, partitioning, delivery guarantees, and operations. | **Phase 2** — must be resolved before any engine implementation begins |
| **M2 / R4 / ADR-003** | Credential Store Interface Not Defined | ES-005 (Executor Engine) specifies that credentials are resolved at execution time from a "credential store" but does not define the store's interface, security model, or Phase 4 (Privacy) integration. | **Blocks** Executor Engine implementation. Without a credential store, the Executor cannot authenticate to external services. | Define the credential store interface and security model via Engineering ADR. Integrate with Phase 4 (Privacy) eligibility gates. | **Before ES-005 implementation** |
| **M4 / ADR-002** | KnowledgeLayer vs ImmutableKnowledgeStore Gap | ES-002 (Knowledge Engine) defines the Immutable Knowledge Store as canonical, but the current implementation has both `KnowledgeLayer` (markdown KB parser, wired) and `ImmutableKnowledgeStore` (versioned DB, not wired). The spec does not resolve which survives. | **Blocks** Knowledge Engine implementation. The implementation team does not know which codebase to build on. The IKS is the correct target, but the migration path is not specified. | File Engineering ADR resolving the unification. The IKS wins; the KnowledgeLayer becomes a seed/migration tool. | **Before ES-002 implementation** |
| **M7 / ADR-004** | Doctor Engine Not Specified | SHUNYA System Flow §3 defines the Doctor Engine as one of 10 engines. It is referenced by the Observer Engine (es-006) and the Governance Engine (es-001) but has no engine specification. | **Blocks** Doctor Engine implementation. Partial implementation exists (`app/shunya/doctor.py`) but there is no specification defining its full scope, inputs, outputs, or constitutional responsibilities. | Create ES-008: Doctor Engine following the ENGINE_SPEC_TEMPLATE.md. | **Before ES-006/ES-007 integration** |
| **M7 / ADR-005** | Context Fusion Engine Not Specified | SHUNYA System Flow §3 defines Context Fusion as a required engine. It is referenced by Reasoning (ES-003), Planner (ES-004), Governance (ES-001), Executor (ES-005), Observer (ES-006), and Learning (ES-007). A computation-only implementation exists (`app/context/__init__.py` — Phase 10). | **Blocks** all downstream engine implementation. Every engine from Reasoning through Learning depends on Context Fusion for workspace context. Without a specification, the interface contract is undefined. | Create ES-009: Context Fusion Engine following the ENGINE_SPEC_TEMPLATE.md. | **Before ES-003 implementation** |
| **M7 / ADR-006** | Identity Engine Not Specified | SHUNYA System Flow §3 defines the Identity Engine as a required engine. It is referenced by Context Fusion and all engines that need identity resolution. An implementation exists (`app/shunya/identity/`). | **Blocks** Context Fusion and any engine that requires identity resolution. Without a specification, the resolution interface and identity lifecycle contract are undefined. | Create ES-010: Identity Engine following the ENGINE_SPEC_TEMPLATE.md. | **Before Context Fusion (ES-009) implementation** |

**Summary: 6 items classified as B. Required Supporting Architecture**

These are not architecture defects — the architecture correctly identifies what is needed. The gap is that the supporting components (Event Bus, Credential Store, 3 missing engine specs, KnowledgeLayer migration) are referenced but not yet specified. Each requires an Engineering ADR or new engine specification.

---

### C. Implementation Concern

| ID | Finding | Rationale | Impact | Recommended Resolution | Latest Phase |
|----|---------|-----------|--------|----------------------|--------------|
| **M5** | Learning Engine Cold Start | ES-007 requires ~100 observations before pattern discovery. The cold start period is not addressed. | **Low.** The Learning Engine operates correctly during cold start — it simply produces no recommendations. No architecture change needed. | Add "cold start mode" to ES-007 during implementation. Document minimum observation threshold per domain. | **Phase 2 — during ES-007 implementation** |
| **M6** | Observer Sampling Rate | ES-006 §10 specifies 10% sampling for successful executions. This may appear to conflict with the "observation is continuous" invariant. | **Low.** The conflict is apparent, not real. "Continuous observation" means every execution produces a basic observation. The 10% sampling applies to detailed evidence validation. | Amend ES-006 to distinguish between "basic observation" (100% of executions) and "detailed evidence validation" (configurable sampling rate, default 10% for successful executions). Minor spec amendment. | **Before ES-006 implementation** |
| **i1** | "tool-based reasoning" not a reasoning type | ES-003 §5 does not include tool-based reasoning. | **Low.** The 10 defined reasoning types cover all constitutional requirements. Adding a type is a future extension. | Optionally add as a note in ES-003 §16 (Future Extensions). Not blocking. | **Anytime** |
| **i2** | Planner optimization formula references non-existent weight source | ES-004 §6's optimization formula references `weight_i` without specifying where weights come from. | **Low.** The implementation team needs to know the source of optimization weights. | Amend ES-004 §6 to state: "Weights come from constraints and human preferences provided in the PlanningInput." Minor spec amendment. | **Before ES-004 implementation** |
| **i3** | Observer evidence quality formula allows 0.0 cascade | ES-006 §7's evidence quality formula produces 0.0 if any dimension fails. This is correct behaviour but undocumented. | **Low.** The behaviour is correct — one failing dimension zeros the entire score. The documentation does not explain this. | Amend ES-006 §7 to document the cascading behaviour explicitly. Minor spec amendment. | **Before ES-006 implementation** |
| **i4** | Learning confidence calibration formula may oscillate | ES-007 §7's confidence calibration formula may oscillate if `learning_rate` is too high. | **Low.** Standard feedback control issue. Easily addressed with a damping factor. | Add damping factor to the confidence calibration formula in ES-007 §7. Minor spec amendment. | **During ES-007 implementation** |
| **i5** | No cross-reference from System Flow to individual engine specs | SHUNYA System Flow defines engine responsibilities and lifecycle stages but does not cite the individual engine specifications. | **Low.** Documentation quality issue. Does not affect correctness. | Add inline citations to ES-001 through ES-007 in SHUNYA System Flow §§2-3. Minor documentation update. | **Anytime** |
| **i6** | Engineer role not mentioned in Governance Model | SHUNYA_GOVERNANCE_MODEL.md defines Chief Constitutional Architect and Chief Software Architect but does not mention the Engineering Team role (which is described in the Engineering Constitution). | **Low.** Documentation gap. The Engineering Team role is defined in the Engineering Constitution but omitted from the Governance Model. | Add Engineering Team as a formal role in SHUNYA_GOVERNANCE_MODEL.md §1. Minor documentation update. | **Anytime** |
| **i7** | Engine specs reference canonical event envelope without citing Core Models | ES-003 and ES-004 reference the "canonical event envelope" but do not cite Core Models §8 as the definition source. | **Low.** Documentation quality issue. Does not affect correctness. Cross-references are conceptually correct but not explicit. | Add explicit citation to Core Models §8 in ES-003 and ES-004. Minor documentation update. | **Anytime** |
| **R1** | Implementation Gap | Large gap between current code (Panchi Club Travel OS) and specified architecture. | **Medium.** Not an architecture defect — the gap exists because the architecture baseline is new and implementation has not started. The architecture is correct; the code is outdated. | Implementation will close this gap over time. No architecture action needed. | **Throughout implementation** |
| **R5** | Pattern Library Storage | The Learning Engine's pattern library may not fit the Knowledge Engine's fact_key/value model. | **Low.** The Knowledge Engine supports JSON values, which can represent structured patterns. The storage model is flexible enough. | Evaluate during implementation. If patterns don't fit, extend the Knowledge Engine value model. | **During ES-007 implementation** |

**Summary: 11 items classified as C. Implementation Concern**

None of these are architecture defects. They are implementation considerations, documentation gaps, or clarifications that the implementation team can resolve without architectural changes. Most are Low impact.

---

### D. Product Decision

| ID | Finding | Rationale | Impact | Recommended Resolution | Latest Phase |
|----|---------|-----------|--------|----------------------|--------------|
| **M3 / R3** | Human Review Queue Location | Governance (ES-001), Observer (ES-006), and Learning (ES-007) all produce outputs requiring human review. The queue, UI, and response flow depend on Phase 17 (Continuous Surface), which is a product/constitutional decision about the user experience. | **Medium.** Does not block implementation of the engines themselves — they can emit REVIEW events without a consumer. But the system cannot operate autonomously until this is resolved because REVIEW verdicts are never acted upon. | Escalate to Chief Constitutional Architect. The decision is: does the human review queue belong to Phase 17 (deferred) or is there a minimum viable review mechanism that can be implemented earlier? The architecture correctly defers this decision; it is not an engineering decision. | **Phase 17 or earlier if product decides** |
| *(no others)* | | | | | |

**Summary: 1 item classified as D. Product Decision**

The Human Review Queue location is the only finding that requires product/constitutional authority input. The architecture correctly identifies and defers this decision.

---

### E. Future Enhancement

| ID | Finding | Rationale | Impact | Recommended Resolution | Latest Phase |
|----|---------|-----------|--------|----------------------|--------------|
| *(none from Architecture Baseline Review fall into this category)* | | | | | |

**Summary: 0 items classified as E. Future Enhancement**

All findings from the baseline review are actionable within the current scope. None are pure future enhancements.

---

## Consolidated Summary

| Category | Count | Items |
|----------|-------|-------|
| **A. Blocking architectural defect** | **0** | — |
| **B. Required supporting architecture** | **6** | Event Bus spec (M1), Credential Store interface (M2), KnowledgeLayer/IKS migration (M4), Doctor Engine spec (M7), Context Fusion spec (M7), Identity Engine spec (M7) |
| **C. Implementation concern** | **11** | Learning cold start (M5), Observer sampling (M6), tool-based reasoning (i1), weight source (i2), formula cascade (i3), oscillation (i4), cross-references (i5), Engineer role (i6), event envelope citation (i7), implementation gap (R1), pattern storage (R5) |
| **D. Product decision** | **1** | Human Review Queue location (M3 / R3) |
| **E. Future enhancement** | **0** | — |
| **Total** | **18** | All findings from the baseline review classified |

---

## Key Insight

**Zero blocking architectural defects were found.**

The architecture is structurally sound. Every finding is either:

- **B (Required supporting architecture):** Supporting components that the architecture correctly identifies but does not yet define in detail. These are the 6 items that must be created before implementation.
- **C (Implementation concern):** Documentation gaps, formula clarifications, and implementation considerations. These do not block implementation — they inform it.
- **D (Product decision):** One decision (Human Review Queue) that requires product/constitutional authority input. The architecture correctly defers this.

The original G2.0 decision stands: **APPROVED WITH REQUIRED AMENDMENTS**, with the clarification that the "required amendments" are the 6 B-category supporting architecture items (Event Bus ADR, Credential Store ADR, KnowledgeLayer/IKS ADR, ES-008, ES-009, ES-010), plus the product decision on the Human Review Queue.

---

*End of Architecture Findings Classification*