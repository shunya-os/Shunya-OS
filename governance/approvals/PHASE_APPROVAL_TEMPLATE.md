# Phase Approval Template

**File naming:** `PA-NNN-phase-name.md`

---

```markdown
# PA-NNN: Phase Approval — [Phase Name/Number]

**Status:** Approved | Rejected
**Date:** YYYY-MM-DD
**Approver:** [Name/Role]
**Related Engine Specs:** ES-NNN, ES-MMM, ES-PPP
**Related ADRs:** ADR-NNN, ADR-MMM

---

## Decision

- [ ] Approved
- [ ] Approved with conditions
- [ ] Rejected

## Conditions (if applicable)

1. Condition 1
2. Condition 2

## Reasoning

Why was this phase approved or rejected?

What evidence was considered?

---

## Scope

This approval authorizes the implementation of Phase [X] in its entirety, comprising:

| Engine | Spec | Status |
|--------|------|--------|
| Engine A | ES-NNN | [Approved] |
| Engine B | ES-MMM | [Pending] |
| Engine C | ES-PPP | [Approved] |

---

## Phase Dependencies

| Dependency | Phase | Status |
|------------|-------|--------|
| Required by Phase X | Phase Y | [Complete] |
| Required by Phase Z | Phase A | [In Progress] |

---

## Integration Points

This phase integrates with:

- **Phase 4 (Privacy):** [Description of integration]
- **Phase 10 (Context Fusion):** [Description of integration]
- **Event Bus:** [Events published/consumed]
- **Workflow Engine:** [Workflow definitions affected]

---

## Verification

- [ ] All engine verification checklists completed
- [ ] Phase-level integration tests pass
- [ ] No regression in existing tests
- [ ] Architecture documents updated
- [ ] Cross-references validated

## Final Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Chief Software Architect | | | |
| (if applicable) Chief Constitutional Architect | | | |
```