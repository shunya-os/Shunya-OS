# ADR Template

**File naming:** `ADR-NNN-title-with-hyphens.md`

**Numbering sequence:** ADR-008 and beyond (ADR-001 through ADR-007 exist)

---

```markdown
# ADR-NNN: Title

**Class:** Engineering | Architectural/Constitutional | Product/Experience
**Status:** Proposed | Accepted | Superseded | Rejected
**Date:** YYYY-MM-DD
**Author:** Name
**Supersedes:** (optional) ADR-MMM
**Superseded by:** (optional) ADR-PPP

**Approval Authority:**
- If Engineering: Chief Software Architect
- If Architectural/Constitutional: Chief Constitutional Architect
- If Product/Experience: Founder

**Related Constitutional Directives:**
- SHUNYA Constitution (02) — Article references
- Product Constitution (14) — Section references
- Technical Constitution — Section references

---

## Context

What is the problem or decision that needs to be made?

What is the current state of the architecture?

What constraints or principles apply?

Cite evidence — code paths, route names, test results, document references with line numbers.

---

## Evidence Reviewed

List every piece of evidence that informed this decision:

| Evidence | Source | What It Proves |
|----------|--------|----------------|
| (file path, line ref) | Code inspection / test run / document | (finding) |

---

## Options Considered

### Option 1: (name)

- **Pros:**
- **Cons:**
- **Evidence for:**

### Option 2: (name)

- **Pros:**
- **Cons:**
- **Evidence for:**

---

## Decision

Which option was chosen and why?

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| (what could go wrong) | High/Medium/Low | High/Medium/Low | (how to prevent/recover) |

---

## Migration Plan

Step-by-step migration from current state to target state:

1.
2.
3.

---

## Rollback Plan

How to revert this decision if it proves wrong:

1.
2.
3.

---

## Consequences

### Positive

- What becomes easier or better?

### Negative

- What becomes harder or more complex?
- What technical debt is introduced?

### Neutral

- What changes but is neither better nor worse?

---

## Compliance

### Constitutional Principles Affected

List the constitutional principles this decision touches. Cite document and section.

### Engineering Constitution Articles Affected

List the articles from engineering constitution this decision touches.

---

## Verification

How will compliance with this decision be verified?

- [ ] Code review checklist updated
- [ ] Tests added for affected layers
- [ ] Architecture documents updated
- [ ] Cross-references validated
- [ ] Capability registry updated
- [ ] Capability lineage updated

---

## References

- [Source file](link) — relevant code
- [Test file](link) — relevant tests
- [Capability registry](link) — canonical entry
- [Audit report](link) — source evidence