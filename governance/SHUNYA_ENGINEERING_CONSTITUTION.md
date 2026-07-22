# SHUNYA Engineering Constitution

**Version:** 1.0
**Status:** Active
**Authority:** Derived from the SHUNYA Constitution (SHUNYA_ARCHITECTURE.md v2.0)

---

## Preamble

This Engineering Constitution derives engineering-specific principles from the SHUNYA Constitution. It does not create new constitutional principles. It operationalizes existing ones for the engineering team.

**Authority Hierarchy:**

```
Constitution          — SHUNYA Constitution (SHUNYA_ARCHITECTURE.md)
    ↓
Architecture          — Locked technical architecture
    ↓
Engineering Constitution — This document. Engineering principles derived from the Constitution.
    ↓
ADRs                  — Architecture Decision Records
    ↓
Engine Specifications — Detailed design documents
    ↓
Implementation        — Code and configuration
    ↓
Verification          — Proof of conformance
```

The SHUNYA Constitution (SHUNYA_ARCHITECTURE.md) is the highest authority. The Architecture is the authoritative technical realization of the Constitution. Where this document conflicts with the Constitution, the Constitution governs.

---

## Article 1 — Architecture Fidelity

### 1.1 Implementation Must Match the Locked Architecture

The architecture defined in `SHUNYA_ARCHITECTURE.md` is locked. Implementation must be faithful to it. When implementation diverges from the architecture, the divergence must be:

1. Documented in an Architecture Decision Record (ADR)
2. Reported to the Chief Software Architect
3. Resolved only with Chief Constitutional Architect approval (for Architectural/Constitutional ADRs) or Chief Software Architect approval (for Engineering ADRs)

### 1.2 No Convenience-Driven Architecture Changes

Architecture must not be changed because implementation is inconvenient. The correct response to implementation difficulty is:

1. Determine whether the difficulty is inherent (architecture is correct but hard) or a design flaw
2. If inherent, invest in better implementation
3. If a design flaw, file an ADR and escalate — do not silently modify

### 1.3 Layer Boundaries Are Inviolable

Each layer has exactly one responsibility:

- **Knowledge Layer** — fact storage and retrieval. Never executes actions.
- **Reasoning Layer** — analysis, inference, decision. Never accesses credentials.
- **Planner Layer** — plan creation. Never executes.
- **Governance Layer** — policy validation. Never stores facts.
- **Executor Layer** — action execution. Never reasons.
- **Observer Layer** — reality recording. Never plans.
- **Learning Layer** — improvement. Never accesses live credentials or payment data.

No layer may perform another layer's responsibility.

---

## Article 2 — Evidence-Driven Engineering

### 2.1 All Decisions Must Cite Evidence

Every engineering decision — architecture choice, implementation approach, tool selection — must be supported by evidence. Evidence includes:

- Code inspection results
- Test outputs
- Document references
- Performance measurements
- Security analysis

### 2.2 Assumptions Are Explicit and Temporary

When evidence is unavailable, assumptions must be:

1. Explicitly stated as assumptions
2. Documented with a clear "assumed until" condition
3. Validated before the dependent work is considered complete

### 2.3 Verification Before Trust

No engine, layer, or component is trusted until it passes verification. Verification includes:

- Unit tests covering all state transitions
- Integration tests covering all dependencies
- Security review for any eval/exec patterns
- Performance benchmarks for any latency-sensitive path

---

## Article 3 — Separation of Concerns

### 3.1 No Dual Responsibilities

A module may not have two responsibilities. Examples of violations:

- A model class that also contains business logic
- A route handler that also performs data transformation
- A service that both reads and writes without clear separation

### 3.2 No Business Logic in Configuration

Business rules belong in the Governance Layer's policy registry, Knowledge Layer's fact store, or domain-specific engine modules. They do not belong in:

- Environment variables
- Configuration files
- Hardcoded constants in routing code

### 3.3 No Credential Leakage Across Layers

Credentials, secrets, and sensitive data must never cross layer boundaries:

- Reasoning Layer does not access API tokens
- Planner Layer does not access payment credentials
- Learning Layer does not access live authentication data

---

## Article 4 — Immutability and Traceability

### 4.1 Knowledge Is Never Silently Overwritten

All knowledge mutations must follow the Immutable Knowledge Store pattern:

1. Create a new version
2. Mark the previous version as superseded
3. Never update in place

### 4.2 Every Decision Is Traceable

Every recommendation, plan, action, and observation must be traceable to its source evidence. The chain must be:

```
Decision → Evidence Links → Source References → Original Data
```

### 4.3 No Disappearing Evidence

No data deletion is permitted without a documented Privacy/Forget workflow. Soft-delete patterns are preferred. Hard deletes require Phase 4 (Privacy) approval.

---

## Article 5 — Governance Before Execution

### 5.1 No Action Without Policy Validation

No action may be executed without passing through the Governance Layer. This applies to:

- Outbound messages (proposals, notifications)
- Data mutations (create, update, delete)
- Financial operations (payments, invoices)
- External API calls (bookings, supplier communication)

### 5.2 AI Proposes, Humans Dispose

For decisions classified as `REVIEW` severity by the Governance Layer:

- The system must wait for human approval before proceeding
- The human must be presented with the evidence chain, not just the recommendation
- The human's decision must be recorded for audit

### 5.3 Governance Audit Trail

All governance decisions — approved, blocked, warned, or review-required — must be logged with:

- Timestamp
- Decision context (plan, actor, domain)
- Policies evaluated
- Verdict
- Approving authority (human or automated)

---

## Article 6 — Testing Integrity

### 6.1 Tests Must Match the Architecture

Test structure should mirror the layer architecture. Unit tests test one layer in isolation. Integration tests test the boundaries between layers.

### 6.2 No Tests That Always Pass

Every test must assert a meaningful condition. Tests that pass without exercising the code under test are worse than no test — they create false confidence.

### 6.3 Test Collection Errors Are Blocking

A test suite with collection errors is not runnable. Collection errors must be resolved before any production change to the affected modules.

---

## Article 7 — Documentation Currency

### 7.1 Architecture Documents Must Be Current

When implementation changes the architecture, the corresponding architecture documents must be updated as part of the same change. Outdated documents are a divergence.

### 7.2 ADRs Are Permanent

Architecture Decision Records are never deleted. They may be superseded by a newer ADR, but the original record remains for historical traceability.

### 7.3 Cross-References Must Be Valid

All cross-references between documents must point to existing files and sections. Broken references are documentation debt.

---

## Article 8 — Divergence Protocol

### 8.1 Identifying Divergence

Every engineer is responsible for identifying divergence between implementation and the Constitution. Divergence includes:

- A layer performing another layer's responsibility
- Business logic in configuration
- Missing governance check before execution
- Non-immutable knowledge mutation
- Unexplained deviation from the locked architecture

### 8.2 Escalation

Divergence must be escalated to the Chief Software Architect. The Chief Software Architect:

1. Documents the divergence in an ADR
2. Determines severity (critical, high, medium, low)
3. Recommends a resolution path
4. Escalates to the Chief Constitutional Architect when the resolution requires constitutional judgment

### 8.3 No Silent Resolution

No engineer may silently resolve a divergence. All resolutions require:

1. An ADR documenting the divergence
2. A verification checklist confirming the resolution
3. Approval per the governance model

---

## Article 9 — Scope Discipline

### 9.1 Narrow Scope, Never Broaden

Every change must be scoped to its minimal required surface. No silent refactoring of unrelated code. No "while we're here" changes.

### 9.2 One Change Per Directive

A single directive authorizes a single change. If additional changes are needed, a new directive must be requested.

### 9.3 No Unauthorized Modifications

The following are never permitted without explicit authorization:
- Application code changes
- Test changes
- Configuration changes
- Database schema changes
- Refactoring
- Commits, pushes, branches
- Deletions
- Architecture modifications