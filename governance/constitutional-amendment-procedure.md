# Constitutional Amendment Procedure (DNA-CAP-01)

**Status:** Governance — Active  
**Dependency:** SHUNYA Constitution (hierarchy); DNA-01 v2.1 (Under Founder Review)  
**Scope:** Changes to constitutional guarantees in any ratified constitutional document  

---

## 1. Principle

The SHUNYA Constitution is composed of multiple constitutional documents, each governing a distinct domain. DNA-01 is the **Technical Constitution** — the constitutional foundation for all adaptive behaviour. Other constitutional documents (Product Constitution, Experience Canon, Presence Canon, etc.) govern their respective domains with equal authority.

Constitutional principles are frozen. Routine engineering work shall not alter a constitutional guarantee. When change to a guarantee is necessary, this procedure governs how amendments are proposed, reviewed, ratified, and archived.

**Editorial corrections do not require an amendment.** Typos, formatting, broken references, and examples may be corrected freely — they do not alter constitutional guarantees. CAP-01 is required only when changing the substance of a constitutional principle, guarantee, or invariant.

**A constitutional amendment is a change to a ratified constitutional guarantee.**  
It is distinct from changes to the Experience Bible, Design System, or Implementation — those layers have their own governance.

---

## 2. When an Amendment Is Required

An amendment is required when:

| Condition | Example |
|-----------|---------|
| A constitutional principle is insufficient for a known use case | EXP-07 needed for a new form factor |
| A contradiction is discovered between two constitutional principles | Attention Adaptation conflicts with Failure Behaviour |
| A fundamentally new computing paradigm emerges | Neural interface, ambient computing |
| The Founder explicitly requests an amendment | Directive from Nishesh |

**An amendment is NOT required for:**

- **Editorial corrections:** typos, formatting, broken references, examples, whitespace
- UI polish
- Component improvements
- CSS refactoring
- Spacing adjustments
- Animation refinements
- Responsive adjustments
- Engineering optimisations
- Design System token updates
- Experience Bible narrative refinement
- Typographic scale refinement
- Any change that does not alter a constitutional guarantee

These belong in the Experience Bible, Design System, or Implementation layer respectively.

**Rule of thumb:** If the change alters what the constitution *guarantees* to the user, it requires CAP-01. If it only fixes how the guarantee is *expressed*, it does not.

---

## 3. Amendment Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                   1. Proposal                            │
│   Written amendment with rationale, impact, and scope   │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│                   2. Review                              │
│   Hermes evaluates against all other constitutional      │
│   principles for conflicts, unintended consequences      │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│                   3. Founder Review                      │
│   Founder reviews the amendment and either:             │
│   • Approves → proceeds to Ratification                 │
│   • Returns with corrections → revise                  │
│   • Rejects → amendment is closed                       │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│                   4. Ratification                        │
│   Founder ratifies the amendment. The current           │
│   constitution is archived. The new version takes effect│
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│                   5. Archival                            │
│   The previous version is archived under                │
│   docs/architecture/archive/ with exact content,        │
│   version, and ratification date preserved              │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Amendment Document Format

Every amendment proposal must include:

### 4.1 Header

```
Amendment: CAP-<NN>
Title: <descriptive title>
Date: <YYYY-MM-DD>
Author: <name or role>
Status: <Proposal | Under Founder Review | Ratified | Rejected | Superseded>
```

### 4.2 Sections

```
## Rationale
Why is this amendment necessary? Which condition from §2 applies?

## Proposed Change
Exact text change to the constitutional document.
Use diff format: show removed text (-) and added text (+).

## Impact Analysis
- Which constitutional principles are affected
- Which layers below are affected (Experience Bible, Design System, Implementation)
- Whether this weakens or strengthens any existing guarantee
- Whether this creates a contradiction with any other principle

## Compatibility
- Backward compatible? (Does this break any existing constitutional guarantee?)
- Migration required? (What must existing implementations change?)
- Scope: (Does this affect all experience classes or a specific one?)

## Foundational Principles Affirmed
Which of the six Experience Invariants (Calm, Continuity, Object Centrality,
Context Awareness, Predictability, Capability Parity) are preserved,
and how.
```

---

## 5. Amendment Numbering

Amendments are numbered sequentially: **CAP-01**, **CAP-02**, **CAP-03**, etc.

- Numbers are never reused
- Rejected amendments retire their number (no reuse)
- Superseded amendments keep their number in the archive

After ratification, the constitutional document's version increments to reflect the amendment (e.g., DNA-01 v2.1 → DNA-01 v2.2 for a minor amendment, DNA-01 v3.0 for a major one).

---

## 6. Archive Rule

Per DNA-01 §18 (Constitutional Archival Policy):

**Every time a constitutional amendment is ratified, the previous version of the affected document is archived.**

Archive path: `docs/architecture/archive/<document-name>-v<version>.md`

Archived documents are:
- Read-only (no edits)
- Preserved with exact content, version, and ratification date
- Referencable by version number
- Never deleted

The archive is the evidence of SHUNYA's constitutional evolution.

---

## 7. Emergency Amendments

In exceptional circumstances (security vulnerability, legal requirement, critical data loss), an amendment may bypass the standard review timeline.

**Procedure:**
1. Founder declares emergency
2. Amendment is drafted and ratified in a single step
3. Within 7 days, a full retrospective review is conducted
4. If the emergency amendment introduced a contradiction, a follow-up amendment is required within 30 days

**Emergency amendments are rare.** This procedure exists to protect SHUNYA — not to circumvent governance.

---

## 8. Current Amendment Registry

| ID | Title | Status | Ratified |
|----|-------|--------|----------|
| — | — | — | — |

*No amendments have been proposed or ratified as of the Constitutional Freeze.*

---

## 9. Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | Initial creation per Constitutional Freeze directive | Hermes Agent |