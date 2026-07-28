# ADR Template

**File naming:** `ADR-NNN-title-with-hyphens.md`

---

```markdown
# ADR-NNN: Title

**Class:** Engineering | Architectural/Constitutional
**Status:** Proposed | Accepted | Superseded | Rejected
**Date:** YYYY-MM-DD
**Author:** Name
**Supersedes:** (optional) ADR-MMM
**Superseded by:** (optional) ADR-PPP

**Approval Authority:**
- If Engineering: Chief Software Architect
- If Architectural/Constitutional: Chief Constitutional Architect

---

## Context

What is the problem or decision that needs to be made?

What is the current state of the architecture?

What constraints or principles apply?

Cite evidence — code inspection, test results, document references.

---

## Decision

What is the decision?

Which option was chosen and why?

---

## Options Considered

### Option 1: (name)

- **Pros:**
- **Cons:**

### Option 2: (name)

- **Pros:**
- **Cons:**

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

List the constitutional principles from SHUNYA_ARCHITECTURE.md that this decision touches.

### Engineering Constitution Articles Affected

List the articles from SHUNYA_ENGINEERING_CONSTITUTION.md that this decision touches.

---

## Verification

How will compliance with this decision be verified?

- [ ] Code review checklist updated
- [ ] Tests added for affected layers
- [ ] Architecture documents updated
- [ ] Cross-references validated

---

## References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — section reference
- [SHUNYA_ENGINEERING_CONSTITUTION.md](/governance/SHUNYA_ENGINEERING_CONSTITUTION.md) — article reference
- [Source file](link) — relevant code
- [Test file](link) — relevant tests
```