# Constitutional Drift Audit

**Directive:** Z-09 Article IV
**Purpose:** Identify every area where implementation drifted away from the SHUNYA Constitution.
**Status:** Pre-Genesis Baseline

---

## Drift Categories

| Category | Drift Severity | Items |
|----------|---------------|-------|
| Terminology | ⚠️ Medium | 4 |
| UX | ⚠️ Medium | 3 |
| Architecture | ⚠️ Low | 2 |
| Navigation | ✅ None | 0 |
| Onboarding | ⚠️ Low | 1 |
| AI Behaviour | ⚠️ Low | 1 |
| Workspace Philosophy | ⚠️ Low | 1 |
| Object Modelling | ✅ None | 0 |
| Memory | ⚠️ Low | 1 |
| Execution | ✅ None | 0 |

---

## Detailed Drift Items

### Terminology Drift

| # | Constitutional Term | Current Implementation | Drift | Severity |
|---|-------------------|----------------------|-------|----------|
| T-01 | "Record" (Z-05) | "Object" in frontend (Create Object) | Minor — frontend uses "Object" instead of "Record" | Low |
| T-02 | "Commitment" (Z-05) | "Task", "Invoice", "Proposal" as separate types | Medium — these ARE commitments but not labelled as such to users. Acceptable per Human Language Layer. | None (intentional) |
| T-03 | "Identity" (Z-05) | "User" in some routes, "Identity" in others | Minor — mixed terminology in backend code | Low |
| T-04 | "Workspace" (Z-05) | "Space" in kernel, "Workspace" in frontend | Minor — two terms for same concept | Low |

### UX Drift

| # | Constitutional Requirement | Current Implementation | Drift | Severity |
|---|--------------------------|----------------------|-------|----------|
| U-01 | "No object terminology in founder-facing UI" (Z-05 Article IV) | "Create First Object" button replaced in Z-07A. "New Object" still exists in workspace context panel. | Medium — "New Object" button is visible to founders | ⚠️ |
| U-02 | "Every screen answers: what can the founder accomplish here?" (Z-07 Article I) | Executive Home, Workspace, AI Resident all answer this. Auth pages still ask "Sign In" / "Create Account" without context. | Low — auth pages are inherently transactional | Low |
| U-03 | "Explainability after every outcome" (Z-07 Article IX) | Implemented for Outcome Engine. Legacy route handlers (lead creation, etc.) don't return explainability. | Medium — legacy routes bypass the Outcome Engine | ⚠️ |

### Architecture Drift

| # | Constitutional Requirement | Current Implementation | Drift | Severity |
|---|--------------------------|----------------------|-------|----------|
| A-01 | "All objects inherit from kernel Record" (Z-06 Article I) | 32+ legacy SQLAlchemy models do NOT inherit from kernel Record. Only FounderObject and Identity do. | High — constitutional kernel is 2,586 LOC, 96% of code is custom | ⚠️ |
| A-02 | "Relationships are graph-based, not hardcoded FKs" (Z-06 Article III) | All 40+ relationships are hardcoded foreign keys. Only FounderObject uses Relationship engine. | High — graph querying is not possible | ⚠️ |

### Onboarding Drift

| # | Constitutional Requirement | Current Implementation | Drift | Severity |
|---|--------------------------|----------------------|-------|----------|
| O-01 | "No 'Create your first object' language" (Z-07 Article VI) | Removed from Executive Home empty state. Still present in some legacy templates. | Low — SPA is clean, legacy templates not used by new founders | Low |

### AI Behaviour Drift

| # | Constitutional Requirement | Current Implementation | Drift | Severity |
|---|--------------------------|----------------------|-------|----------|
| AI-01 | "AI never owns business logic" (Z-06 Article X) | CompanionEngine and CoachEngine have business logic embedded in AI prompts. Outcome Engine keeps business logic deterministic. | Medium — legacy AI engines need refactoring | ⚠️ |

### Workspace Philosophy Drift

| # | Constitutional Requirement | Current Implementation | Drift | Severity |
|---|--------------------------|----------------------|-------|----------|
| W-01 | "Intent → Context → Relationships → Memory → Workspace" (Z-05 Article V) | Current workspace loads Executive Home directly. No intent-based workspace generation. | Medium — intent routing is not yet the primary mode | ⚠️ |

### Memory Drift

| # | Constitutional Requirement | Current Implementation | Drift | Severity |
|---|--------------------------|----------------------|-------|----------|
| M-01 | "Memory is derived from Events → consolidate → Memory → Knowledge" (Z-06 Article IV) | No consolidation pipeline exists. Events are logged but not automatically consolidated into memory. | Medium — memory is passive, not active | ⚠️ |

---

## Drift Severity Summary

| Severity | Count | Items |
|----------|-------|-------|
| High | 2 | A-01 (kernel adoption), A-02 (graph relationships) |
| Medium | 5 | U-01 (object terminology), U-03 (legacy explainability), AI-01 (AI business logic), W-01 (intent workspace), M-01 (memory consolidation) |
| Low | 4 | T-01, T-03, T-04, O-01, U-02 |
| None (intentional) | 1 | T-02 (commitment naming) |

---

## Constitutional Compliance Score

**Overall: 65%** (9 of 14 constitutional articles fully implemented)

| Article | Drift Items | Score |
|---------|-------------|-------|
| Z-05 Universal Ontology | T-01, T-02, T-03, T-04 | 85% |
| Z-05 Workspace Philosophy | W-01 | 70% |
| Z-06 Universal Behavior | A-01, A-02, U-03 | 40% |
| Z-06 Universal Events | M-01 | 75% |
| Z-06 Universal Intelligence | AI-01 | 80% |
| Z-07 Outcome Engine | U-01, U-02 | 90% |
| Z-07 Onboarding | O-01 | 95% |
| Z-08 Founder Reality | All | 90% |

**Constitutional drift is concentrated in two areas:** kernel Record adoption (Z-06 Article I) and graph relationship migration (Z-06 Article III). These are the two fundamental architectural changes that Genesis Reset is designed to address — they are not implementation bugs, they are intentional pre-Genesis technical debt.