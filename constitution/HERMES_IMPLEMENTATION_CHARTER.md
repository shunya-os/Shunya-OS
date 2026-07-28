# Volume V — Hermes Implementation Charter

> **SHUNYA Constitutional Program — Volume V**
> **Status: Candidate for Founder Review**
> **Version: 1.0**
> **Date: 2026-07-28**
> **Authority:** Volume I — Principles V (Architecture of Principle), VII (Discipline of Execution), VIII (Primacy of Governance)

---

## Preamble

This Charter defines how the SHUNYA Constitution governs implementation. It is the bridge between constitutional law and executable code. Implementation SHALL derive from constitutional law. Implementation SHALL NEVER redefine constitutional law.

This Charter binds every engineer, every AI agent (including Hermes), every CI/CD pipeline, and every deployment. It is the constitutional mandate for all implementation work.

The Charter does not create new constitutional principles. It operationalizes existing ones. Every obligation in this Charter traces to a specific article in Volume II and a specific First Principle in Volume I.

---

## Article I — Constitutional Derivation

### §1.1 Derivation Before Implementation

No implementation SHALL begin without a traceable derivation chain to the Constitution. The derivation chain SHALL be:

```
First Principle (Volume I, Principle N) →
Constitutional Article (Volume II, Article N, §N.N) →
Canonical Definition (Volume III, §N) →
Architecture Decision (ADR) →
Engine Specification →
Implementation
→ Verification (against upstream chain)
```

### §1.2 The Derivation Gate

Before any code is written, the implementer SHALL document:

1. **Which constitutional article(s)** authorize this implementation
2. **Which First Principle(s)** govern those articles
3. **Which canonical definitions** are relevant
4. **What compliance rules** apply (Volume IV)
5. **What verification** will demonstrate compliance

This documentation SHALL be reviewed before implementation proceeds.

### §1.3 No Implementation-Specific Constitutional Language

Implementation SHALL NOT use constitutional terms for implementation-specific concepts. The terms defined in Volume III are reserved for constitutional concepts. Implementation SHALL introduce its own terminology for implementation artifacts, clearly distinguished from constitutional terminology.

### §1.4 No Constitutional Redefinition by Implementation

Implementation SHALL NOT:

- Redefine a constitutional term
- Add new meanings to a constitutional term
- Create synonyms for constitutional terms
- Use constitutional terms in ways inconsistent with their definitions

---

## Article II — The Obligations of Implementation

### §2.1 Obligations of Every Engineer

Every engineer implementing SHUNYA SHALL:

1. **Know the Constitution** — read and understand Volumes I–IV before implementing
2. **Derive from authority** — trace every implementation decision to a constitutional source
3. **Verify compliance** — run compliance checks before submitting code
4. **Report violations** — escalate any detected constitutional violation immediately
5. **Preserve invariants** — never weaken Protected Guarantees (Volume II, Appendix A)
6. **Document decisions** — record architectural decisions with constitutional traceability
7. **Accept review** — submit to constitutional compliance review as part of the development process

### §2.2 Obligations of Every AI Agent (Including Hermes)

Every AI agent implementing SHUNYA SHALL:

1. **Load constitutional context** — load the relevant constitutional documents before implementing
2. **Derive before acting** — produce a derivation chain before writing code
3. **Compliance self-check** — verify own output against constitutional requirements
4. **No self-certification** — NEVER declare "Complete," "Finished," "Release Ready," "Production Ready," or "Final" — only "Candidate for Founder Review"
5. **Evidence over assertion** — support every claim with evidence; never fabricate results
6. **Escalate questions** — when constitutional interpretation is ambiguous, escalate to the Founder
7. **Preserve the hierarchy** — never modify constitutional documents except through the amendment process

### §2.3 Obligations of the Governance Engine

The Governance Engine SHALL:

1. **Enforce** constitutional compliance on every operation
2. **Verify** every engine-to-engine message against policy
3. **Block** operations that violate constitutional requirements
4. **Escalate** to human authority when unable to resolve
5. **Audit** all governance decisions
6. **Report** compliance metrics regularly

### §2.4 Obligations of CI/CD

The CI/CD pipeline SHALL:

1. **Run constitutional compliance checks** as part of every build
2. **Block deployments** that fail compliance checks
3. **Verify derivation chains** for new or modified components
4. **Check vocabulary compliance** (Volume III terms used correctly)
5. **Generate compliance reports** for every release

### §2.5 Obligations Regarding the Simulation Engine

Every implementation affecting the Simulation Engine, or producing outputs that the Simulation Engine consumes, SHALL:

1. **Ensure multi-future generation** — no implementation SHALL constrain the Simulation Engine to produce a single projected future
2. **Provide uncertainty data** — all data sources consumed by the Simulation Engine SHALL carry confidence scores and uncertainty estimates as defined in Volume III, §31
3. **Support outcome comparison** — implementations SHALL capture actual outcomes in a form comparable to simulation projections
4. **Respect the simulation precedence** — the Simulation Engine SHALL execute before the Planner Engine (Volume II, §3.7.3) unless time-criticality is explicitly flagged and governance-approved
5. **Governance gate simulation outputs** — all simulation results SHALL pass through the Governance Engine before presentation to human decision-makers
6. **Log simulation-audit trails** — every simulation run SHALL produce an immutable audit trail per Volume II, §7.5

---

## Article III — Implementation Workflow

### §3.1 The Constitutional Implementation Workflow

Every implementation SHALL follow this workflow:

```
STEP 1: Constitutional Context
    ─ Load the relevant constitutional documents
    ─ Identify governing articles, principles, and definitions
    ─ Document the derivation chain

STEP 2: Compliance Check (Pre-Implementation)
    ─ Check Volume IV compliance rules for the affected components
    ─ Identify any Protected Guarantees that may be affected
    ─ Verify no existing violations in the affected area

STEP 3: Architecture Decision
    ─ Record the architecture decision with constitutional traceability
    ─ Document rejected alternatives and why they were rejected
    ─ Verify the decision does not violate any constitutional article

STEP 4: Implementation
    ─ Write production code
    ─ Write tests (unit, integration, compliance)
    ─ Ensure all new objects conform to the Universal Object Protocol

STEP 5: Verification
    ─ Run all tests (zero regressions)
    ─ Run constitutional compliance checks
    ─ Verify evidence chains, audit trails, and governance integration
    ─ Verify vocabulary compliance

STEP 6: Compliance Review
    ─ Produce a compliance statement
    ─ Submit for review
    ─ Address any violations found

STEP 7: Release
    ─ Candidate for Founder Review
    ─ Founder acceptance required for production release
```

### §3.2 The Evidence Hierarchy

When reporting implementation results, the following evidence hierarchy SHALL be used:

| Level | Evidence Type | Example |
|-------|-------------|---------|
| 1 (best) | Founder explicit acceptance | "Founder confirmed the workflow works" |
| 2 | Browser screenshot / recording | Screenshot of the rendered workspace |
| 3 | UI walkthrough script | "Opened login → typed credentials → pressed Enter → saw Executive Home" |
| 4 | API test output | `curl output: HTTP 200, 167 objects returned` |
| 5 | Test suite output | `pytest: 20/20 pass` |
| 6 | Build output | `vite build: 62 modules, 0 errors` |
| 7 | Compiler output | `tsc --noEmit: 0 errors` |

**Rule:** Never collapse levels. "Code compiled" is not "tests passed." "Tests passed" is not "behaviour observed." "Behaviour observed" is not "founder experience demonstrated." "Demonstrated" is not "accepted." These are five distinct milestones.

### §3.3 The Five Gates of Acceptance

Every implementation SHALL pass through five gates before acceptance:

| Gate | Meaning | Who Certifies |
|------|---------|--------------|
| **Compiled** | Code builds without errors | Automated build system |
| **Tested** | Test suite passes with zero regressions | Automated test runner |
| **Observed** | Behavior is verified through evidence | Implementer (with evidence) |
| **Demonstrated** | Founder experience is shown to work | Implementer (with walkthrough) |
| **Accepted** | Founder confirms the implementation meets requirements | **Founder only** |

### §3.4 The Self-Certification Prohibition

No engineer, AI agent, or automated system SHALL declare:

- Complete
- Finished
- Release Ready
- Production Ready
- v1.0 / Alpha / Beta / GA
- Final

Unless explicitly approved by the Founder. The only permissible declaration is:

- **Candidate for Founder Review** — Ready for the Founder to test and evaluate

---

## Article IV — Constitutional Compliance in Implementation

### §4.1 Compliance Verification Gates

Every implementation SHALL pass the following compliance gates:

| Gate | What It Checks | When |
|------|---------------|------|
| **Architecture Compliance** | Layer boundaries, engine responsibilities, protocol conformance | Every code change |
| **Identity Compliance** | Identity permanence, uniqueness, non-reuse | Every identity-related change |
| **Evidence Compliance** | Evidence chains, confidence computation, audit trails | Every cognitive path |
| **Privacy Compliance** | Privacy level integrity, consent enforcement | Every data access path |
| **Governance Compliance** | Governance Engine enforcement, policy derivation | Every execution path |
| **Vocabulary Compliance** | Term usage matches Volume III definitions | Every documentation change |

### §4.2 Compliance Failure Response

When a compliance gate fails:

1. **Immediate notification** — the implementer is informed of the failure
2. **Violation classification** — severity is classified per Volume IV, Article II
3. **Blocking** — Critical and Major violations block further work in the affected area
4. **Remediation** — a remediation plan is required before work resumes
5. **Verification** — the fix is verified against the compliance gate
6. **Documentation** — the violation and remediation are recorded in the compliance manifest

### §4.3 Compliance Debt

Compliance debt is the accumulation of unresolved compliance violations. Compliance debt SHALL be tracked alongside technical debt. A component with outstanding Major violations SHALL NOT be released to production. A component with outstanding Critical violations SHALL be quarantined.

### §4.4 The Compliance Manifest

Every component SHALL maintain a compliance manifest in its repository. The manifest SHALL contain:

- Component name and version
- Governing constitutional articles
- Compliance status per dimension
- Outstanding violations (with severity, age, and remediation plan)
- Compliance verification history
- Last audit date and result

---

## Article V — Constitutional Archive and History

### §5.1 The Archive

All versions of the Constitution SHALL be preserved in the archive. The archive SHALL be:

- Read-only (no modifications to archived documents)
- Versioned (each version preserved with its ratification date)
- Referenceable (by version number in documentation and code)
- Complete (no document is ever deleted)

### §5.2 Archival Procedure

When a constitutional document is superseded:

1. The superseded document is copied to the archive directory
2. The copy is verified to be byte-identical to the original
3. The archive index is updated with the new entry
4. The original document is updated with the new version
5. A forward reference from the archived version to the new version is added

### §5.3 Archive Structure

```
archive/
├── first-principles/
│   └── v1.0/
├── shunya-constitution/
│   └── v1.0/
├── canonical-definitions/
│   └── v1.0/
├── constitutional-compliance/
│   └── v1.0/
├── hermes-implementation-charter/
│   └── v1.0/
└── INDEX.md
```

---

## Article VI — Implementation Boundaries

### §6.1 What Implementation MAY Do

Implementation MAY:

- Extend existing capabilities within constitutional boundaries
- Create new domain-specific modules that conform to the object protocol
- Optimize performance without changing constitutional behavior
- Refactor code without changing constitutional guarantees
- Add tests that verify constitutional compliance
- Improve UI without changing interaction guarantees

### §6.2 What Implementation MAY NOT Do

Implementation SHALL NOT:

- Violate any constitutional article
- Weaken any Protected Guarantee (Volume II, Appendix A)
- Bypass the Governance Engine for any operation
- Introduce duplicate definitions or representations
- Store data at a privacy level lower than its origin
- Execute actions without proper authorization
- Modify the timeline (append only)
- Reuse retired identities
- Assert confidence without computation
- Present observations as established facts
- Use constitutional terms for implementation-specific concepts

### §6.3 The Scope Discipline

Every implementation SHALL be scoped to its minimal required surface. No change SHALL include:

- Unrelated refactoring
- Silent modifications to untargeted components
- Architecture changes outside the authorized scope
- New constitutional concepts introduced through implementation

---

## Article VII — Verification and Review

### §7.1 Pre-Commit Verification

Before every commit, the implementer SHALL verify:

1. All tests pass (zero regressions)
2. Constitutional compliance checks pass
3. Vocabulary compliance is maintained
4. No Protected Guarantees are weakened
5. The derivation chain is documented

### §7.2 Pre-Release Verification

Before every release, the implementer SHALL verify:

1. Full test suite passes
2. Constitutional compliance audit is complete
3. Compliance manifest is up to date
4. No unresolved Critical or Major violations exist
5. Governance Engine integration is verified
6. Evidence chains are complete
7. Audit trails are functional

### §7.3 The Founder Review

The Founder SHALL review:

- Every constitutional amendment
- Every release candidate
- Every architectural change affecting constitutional guarantees
- Every escalation from the Governance Engine
- The compliance health report at every major milestone

### §7.4 The Review Timeline

| Review Type | Maximum Turnaround | Default Outcome If No Response |
|-------------|-------------------|-------------------------------|
| Compliance check | 2 business days | Proceed with caveats |
| Violation review | 5 business days | Escalate to Founder |
| Architecture decision | 5 business days | Proceed if no constitutional impact |
| Amendment review | 14 business days | Pending — no action |
| Founder review | 30 business days | Pending — no action |

---

## Article VIII — Implementation and the Canonical Definitions

### §8.1 Term Reservation

The following terms are reserved for constitutional use and SHALL NOT be repurposed in implementation:

Constitution, Article, Principle, Violation, Compliance, Governance, Protected Guarantee, Canonical Source, Evidence Chain, Identity Invariant, Timeline, Audit Trail, Privacy Level, First Principle, Universal Object Protocol, Object Hierarchy, Constitutional Amendment, Derivation Chain

### §8.2 Implementation Terminology

Implementation SHALL introduce its own terminology for:

- Database table names
- API endpoint names
- UI component names
- Variable and function names
- Configuration keys
- Deployment artifacts

These terms SHALL be clearly distinct from the reserved constitutional terms.

### §8.3 Reference Convention

When implementation references a constitutional concept, it SHALL use the canonical reference format:

```
[Volume_N, Article_X, §Y.Y] or [Volume_III, §N]
```

For example:

```python
# This implements the Identity Invariant [Vol II, Art IV, §4.1]
# Identity is assigned at creation and never changes
```

---

## Article IX — The Constitutional Relationship

### §9.1 Constitution Governs Implementation

The Constitution is the supreme authority. Implementation is subordinate. The relationship is:

```
Constitution (law) → Implementation (execution of law)
```

Implementation SHALL NOT:
- Modify constitutional intent
- Interpret constitutional articles in ways that contradict their plain meaning
- Create exceptions to constitutional rules without amendment
- Use implementation convenience as justification for constitutional deviation

### §9.2 Implementation Feedback to Constitution

Implementation MAY identify:

- Ambiguities in constitutional text
- Gaps in constitutional coverage
- Conflicts between constitutional articles
- Practical difficulties in compliance

These observations SHALL be documented as feedback to the constitutional review process. They SHALL NOT be used as justification for non-compliance.

### §9.3 The Amendment Path

When implementation identifies a constitutional deficiency:

1. Document the deficiency with evidence
2. Propose an amendment through the CAP (Volume IV, Article IV)
3. Implement a workaround only if the deficiency is causing harm
4. The workaround SHALL be temporary and SHALL NOT weaken constitutional guarantees
5. The workaround SHALL be removed when the amendment is ratified

---

## Appendix A: Implementation Compliance Checklist

Every implementation SHALL use this checklist:

| # | Requirement | Compliant? | Evidence |
|---|------------|-----------|----------|
| 1 | Derivation chain documented | [ ] | |
| 2 | Constitutional articles governing the change identified | [ ] | |
| 3 | Volume III definitions respected | [ ] | |
| 4 | No Protected Guarantees weakened | [ ] | |
| 5 | No new constitutional concepts introduced | [ ] | |
| 6 | Governance Engine integration verified | [ ] | |
| 7 | Evidence chains complete | [ ] | |
| 8 | Audit trail functional | [ ] | |
| 9 | Privacy levels respected | [ ] | |
| 10 | Vocabulary compliance maintained | [ ] | |
|| 11 | All tests pass (zero regressions) | [ ] | |
|| 12 | Compliance manifest updated | [ ] | |
|| **13** | **Simulation Engine multi-future generation verified** | **[ ]** | |
|| **14** | **Uncertainty manifests complete for all simulation outputs** | **[ ]** | |
|| **15** | **Simulation-audit trail functional** | **[ ]** | |

## Appendix B: Pre-Commit Hook Template

Every repository SHALL implement a pre-commit hook that verifies:

```bash
# 1. Run constitutional compliance checks
# 2. Verify vocabulary compliance
# 3. Check for Protected Guarantee violations
# 4. Run test suite
# 5. Generate compliance report
```

## Appendix C: Derivation Chain Template

Every implementation SHALL document its derivation chain:

```
Implementation: [Component/Feature Name]

First Principle: Volume I, Principle [N] — [Title]
    ↓
Constitutional Article: Volume II, Article [N] — [Title], §[N.N]
    ↓
Canonical Definition: Volume III, §[N] — [Term]
    ↓
Architecture Decision: ADR-[NNN] — [Title]
    ↓
Implementation: [Module/File/Function]
    ↓
Verification: [Test file / Compliance check]
```

---

> **End of Volume V — Hermes Implementation Charter**
> **End of the SHUNYA Constitution — Version 1.0**

---

> **All five volumes of the SHUNYA Constitution are now complete.**
> **Status: Candidate for Founder Review**
> **Awaiting Founder ratification to become governing law.**