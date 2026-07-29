# SHUNYA Governance Model

**Version:** 1.1
**Status:** Active
**Authority:** Derived from the SHUNYA Constitution (SHUNYA_ARCHITECTURE.md v2.0) and the SHUNYA Engineering Constitution

---

## Authority Hierarchy

```
Constitution                                          — SHUNYA Constitution
    ↓
Architecture                                          — Locked technical architecture
    ↓
Engineering Constitution                              — Engineering principles
    ↓
ADRs (Engineering | Architectural/Constitutional)     — Decision records
    ↓
Engine Specifications                                 — Design documents
    ↓
Implementation                                        — Code and configuration
    ↓
Verification                                          — Proof of conformance
```

---

## 1. Roles

### 1.1 Chief Constitutional Architect

The highest authority for SHUNYA's philosophy, Constitution, and architecture. Owns the SHUNYA Constitution — architectural philosophy, product direction, and constitutional principles. Does not participate in day-to-day engineering governance.

**Decision rights:**
- Approve or reject architecture modifications
- Approve or reject Architectural/Constitutional ADRs
- Resolve constitutional conflicts
- Define product direction

### 1.2 Chief Software Architect

Owns engineering excellence. Responsible for faithful implementation of the approved architecture. Reports divergence. Does not own constitutional decisions.

**Decision rights:**
- Approve engine specifications
- Approve Engineering ADRs
- Assign verification checklists
- Escalate to the Chief Constitutional Architect
- Stop work that violates the Constitution

### 1.3 Engineering Team

Implements engines, phases, and components per approved specifications. Responsible for identifying divergence.

**Decision rights:**
- Technical implementation decisions within approved scope
- Filing ADRs for observed divergence
- Proposing engine specifications for review

---

## 2. Decision Types

### 2.1 Architecture Decisions

Changes to the architecture itself — new layers, removed layers, modified layer responsibilities, changed constitutional principles.

**ADR Class:** Architectural/Constitutional
**Process:** ADR → CSA Review → Chief Constitutional Architect Approval

**Required for:**
- New layer creation
- Layer boundary changes
- Constitutional principle modifications
- Pipeline architecture changes

### 2.2 Engineering Decisions

Changes within the existing architecture — new engines, interfaces, implementation approaches.

**ADR Class:** Engineering
**Process:** ADR → CSA Review → CSA Approval

**Required for:**
- New engine within an existing layer
- Significant refactoring of an existing engine
- Integration between two engines
- New API surface
- Resolution of divergence that does not affect constitutional principles

### 2.3 Engine Specifications

Detailed design documents for implementation units within the existing architecture.

**Process:** Engine Spec → CSA Review → Approval

**Required for:**
- All new engines
- All significant refactoring
- All integrations between engines

### 2.4 Implementation Changes

Code changes within an approved engine specification.

**Process:** Implementation → Verification → Approval

**Required for:**
- All code changes
- Test additions
- Configuration changes (within approved scope)

### 2.5 Divergence Reports

Documented gaps between implementation and the Constitution.

**Process:** Observation → ADR Filing → CSA Review → Escalation (if needed)

---

## 3. Approval Hierarchy

```
Chief Constitutional Architect
        │
        │  Architecture modifications, constitutional decisions,
        │  Architectural/Constitutional ADRs
        │
Chief Software Architect
        │
        │  Engine specs, Engineering ADRs, verification sign-off
        │
Engineering Team
        │
        │  Implementation, testing, divergence reporting
```

---

## 4. ADR Approval Model

### 4.1 Engineering ADRs

Approved by the Chief Software Architect. Covers:

- New engines within existing layers
- New interfaces between existing engines
- Implementation approach decisions
- Divergence resolutions that do not affect constitutional principles

### 4.2 Architectural / Constitutional ADRs

Require approval from the Chief Constitutional Architect. Covers:

- New layers or layer boundary changes
- Constitutional principle modifications
- Pipeline architecture changes
- Divergence resolutions that affect constitutional principles
- Any decision the Chief Software Architect determines requires constitutional judgment

### 4.3 ADR Classification

Every ADR must declare its class in the header:

- `Class: Engineering` — Approved by Chief Software Architect
- `Class: Architectural/Constitutional` — Approved by Chief Constitutional Architect

If classification is ambiguous, the Chief Software Architect determines the class. If the CSA determines constitutional judgment is needed, the ADR is escalated to Architectural/Constitutional class.

---

## 5. Governance Workflow

### 5.1 Standard Change Flow

```
1. Requirement Identified
2. ADR Filed (if architecture-adjacent — Engineering or Architectural/Constitutional)
3. ADR Approved by appropriate authority
4. Engine Spec Created (if new engine)
5. Engine Spec Approved by CSA
6. Implementation Begins
7. Verification Checklist Completed
8. Implementation Reviewed by CSA
9. Approval or Rejection
```

### 5.2 Divergence Flow

```
1. Divergence Observed
2. ADR Filed with appropriate class
3. CSA Reviews Divergence
4. Severity Assigned (Critical/High/Medium/Low)
5. Resolution Path Determined
6. If Architectural/Constitutional → Escalate to Chief Constitutional Architect
7. If Engineering-only → Resolve per CSA direction
```

### 5.3 Emergency Flow

For production-blocking issues where the standard flow would cause unacceptable delay:

```
1. Issue identified
2. CSA authorizes emergency fix (verbal or written)
3. Fix implemented with minimal scope
4. ADR filed within 24 hours documenting the divergence
5. Standard governance applied retroactively
```

---

## 6. Document Statuses

| Status | Meaning |
|--------|---------|
| `Draft` | In progress, not yet submitted for review |
| `Review` | Submitted for review, awaiting decision |
| `Approved` | Approved by the appropriate authority |
| `Rejected` | Rejected with documented reasoning |
| `Superseded` | Replaced by a newer document |
| `Active` | Currently in effect |
| `Archived` | Historical record, no longer active |

---

## 7. Cross-References

- **SHUNYA Constitution:** [`../docs/canon/02_shunya_constitution.md`](../docs/canon/02_shunya_constitution.md) — The SHUNYA Constitution (binding, supreme authority)
- **OS Constitution:** [`../docs/canon/OS_CONSTITUTION.md`](../docs/canon/OS_CONSTITUTION.md) — OS-level architectural unification constitution
- **Engineering Constitution:** [`SHUNYA_ENGINEERING_CONSTITUTION.md`](./SHUNYA_ENGINEERING_CONSTITUTION.md) — Engineering-specific principles
- **Governance Changelog:** [`GOVERNANCE_CHANGELOG.md`](./GOVERNANCE_CHANGELOG.md) — Permanent audit trail
- **Conflict Resolution:** [`GOVERNANCE_FREEZE_01_CONFLICT_RESOLUTION.md`](./GOVERNANCE_FREEZE_01_CONFLICT_RESOLUTION.md) — §8 Constitutional Conflict Resolution
- **ADR Process:** [`adr/ADR_TEMPLATE.md`](./adr/ADR_TEMPLATE.md) — Architecture Decision Record template
- **Engine Spec Process:** [`engine_specs/ENGINE_SPEC_TEMPLATE.md`](./engine_specs/ENGINE_SPEC_TEMPLATE.md) — Engine specification template
- **Approval Process:** [`approvals/`](./approvals/) — Approval templates and records
- **Verification Process:** [`verification/VERIFICATION_CHECKLIST.md`](./verification/VERIFICATION_CHECKLIST.md) — Verification checklists

---

## 8. Constitutional Conflict Resolution

*See [`GOVERNANCE_FREEZE_01_CONFLICT_RESOLUTION.md`](./GOVERNANCE_FREEZE_01_CONFLICT_RESOLUTION.md) for the full conflict resolution framework.*

### 8.1 Purpose

This section defines how conflicts between constitutional documents are resolved. It ensures that when two governing documents provide contradictory guidance, there is a deterministic resolution path.

### 8.2 Core Principles

1. **Resolve by satisfying both constitutions whenever possible.**
2. **The Product Constitution governs user experience, interaction philosophy, and behavioural intent.**
3. **The Technical Constitution governs implementation behaviour, runtime adaptation, and device-native architecture.**
4. **If a conflict changes a constitutional guarantee, implementation must pause and proceed through CAP-01 before continuing.**

### 8.3 Conflict Resolution Process

```
Step 1: Identify Conflict
Step 2: Classify Severity — Critical / Major / Minor
Step 3: Can both be satisfied? → YES: Adopt & record ADR
Step 4: Apply Domain Priority — Product > Technical > OS
Step 5: CRITICAL → Pause implementation → CAP-01
        MAJOR/MINOR → Chief Constitutional Architect resolves
Step 6: Record in ADR. Update Governance Changelog.
```

### 8.4 Constitutional Guarantee Protection

No conflict resolution may weaken:
- Article 1 (Human First)
- Article 2 (Human Agency)
- Article 3 (Permission Before Action)
- Article 4 (Privacy by Intention)
- Article 9 (Calm Before Complexity)

Any conflict affecting these automatically triggers CAP-01.

### 8.5 Conflict Resolution Classification

| Category | Resolution Authority |
|----------|---------------------|
| Product vs. Technical | Product Constitution governs |
| Technical vs. OS Architecture | OS Constitution governs |
| Constitution vs. Governance | SHUNYA Constitution governs |
| Version conflict | Latest ratified version governs |
| Cross-document duplicate | Authoritative owner governs |