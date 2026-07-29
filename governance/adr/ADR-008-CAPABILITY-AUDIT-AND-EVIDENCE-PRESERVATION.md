# ADR-008: Universal Capability Audit & Evidence Preservation

**Class:** Product/Experience
**Status:** Accepted
**Date:** 2026-07-28
**Author:** Hermes Agent (per Founder directive)
**Supersedes:** (none)
**Superseded by:** (none)

**Approval Authority:**
- If Product/Experience: Founder

**Related Constitutional Directives:**
- SHUNYA Constitution (02) — Article 11 (Explainability): every system action must be explainable
- Product Constitution (14) — §15 (Measurability & Testability): every requirement must have a specific test
- Addendum — Evidence-Based Consolidation & Canonical Selection (2026-07-28)

---

## Context

The SHUNYA codebase had grown to 62+ inventoried capabilities across 20+ Flask blueprints, 5 independent sub-projects, 37+ Jinja2 templates, a React SPA, and 22 core modules. There was no single inventory of what capabilities existed, where they lived, how they were accessed, or whether they were Founder-accessible.

The Founder issued an addendum requiring a complete architectural audit before any implementation work, with evidence-based consolidation decisions.

### Constraints

- No implementation work may proceed until the audit is complete
- Every claim must be backed by objective evidence (file path, route name, test output)
- Percentages are false precision and must not be used
- Every consolidation decision requires 6-element framework: Evidence, Comparison, Risk, Canonical Justification, Founder Impact, Verification

---

## Evidence Reviewed

| Evidence | Source | What It Proves |
|----------|--------|----------------|
| Route files inventory | `find app core -name "*route*"` + `grep -rn "\.route\|Blueprint"` | 20+ route files, 20+ blueprints registered |
| Template inventory | `find . -name "*.html"` | 37 templates in main app + ~185 in 5 sub-projects |
| Frontend components | `find frontend/src -name "*.tsx"` | 18 React components + 14 runtime engines |
| Core modules | `find core -name "__init__.py"` | 22 core modules including intelligence (8 sub-engines) |
| Sub-project uniqueness | Per-file comparison: `find $d/app -name "*.py"` vs main app | CRM has unique quotation engine; workflow has unique workflow engine; documents has unique readers |
| Auth systems | `app/auth_routes.py` vs `app/production/auth/` | 2 parallel auth systems with different ID models |
| Space runtime | `app/space/routes.py` — 16 routes | Complete universal space system with AI Resident, reasoning, composition |
| Intelligence engine | `core/intelligence/*/engine.py` | 8 fully implemented engine modules |
| Sub-project imports in main app | `grep -rn "shunya_os_" app/__init__.py` | Zero — no sub-project is imported by the main app |
| Audit report | `docs/reports/phase0-universal-capability-audit.md` | Full inventory with evidence paths for every capability |

---

## Options Considered

### Option 1: Complete audit with capability-by-capability evidence (CHOSEN)

**Pros:**
- Every capability has documented evidence path
- Consolidation decisions are reproducible
- Future contributors can trace decisions
- No percentage claims — precise counts with definitions

**Cons:**
- Took significant time to complete

**Evidence for:** Full audit produced at `docs/reports/phase0-universal-capability-audit.md` with 62+ capabilities inventoried and documented.

### Option 2: Selective audit of only Founder-facing surfaces

**Pros:**
- Faster to produce
- Focused on visible gaps

**Cons:**
- Misses hidden capabilities (27 identified backend-only)
- Cannot detect duplicates without full inventory
- Decisions are not reproducible

### Option 3: No audit — proceed directly to implementation

**Pros:**
- Fastest path to code changes

**Cons:**
- Violates the Addendum
- Cannot distinguish existing vs. missing capabilities
- Risk of recreating what already exists

---

## Decision

**Option 1 — Complete audit with capability-by-capability evidence.** Every capability was inventoried against 6 criteria (backend, frontend, AI access, discoverability, Founder readiness, release readiness) with documented file path evidence.

Key findings:
- 62 capabilities inventoried
- 27 hidden (backend code exists, no Founder-facing surface)
- 5 sub-projects have unique capabilities (not duplicates)
- 2 parallel auth systems (cannot deprecate legacy until 15+ routes are migrated)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Audit goes stale as code changes | High | Medium | Update capability registry as part of every implementation PR |
| Sub-project analysis was initially wrong | Occurred | High | Corrected: CRM+workflow+documents have unique capabilities. Framework now requires 6-element evidence before any consolidation |
| Percentage claims create false precision | Occurred | Low | Removed all percentages. Replaced with precise counts and criterion definitions |

---

## Migration Plan

1. Audit complete → Phase 1 consolidation decisions documented
2. ADRs created for every significant decision
3. Capability registry created as single source of truth
4. Future PRs must reference capability registry entries

---

## Rollback Plan

Not applicable — this is a documentation decision with no code changes. The audit report and ADRs can be updated or superseded by future ADRs.

---

## Consequences

### Positive

- First complete inventory of SHUNYA capabilities
- Every hidden capability identified (27 backend-only)
- Duplicate analysis corrected (sub-projects are not duplicates)
- 6-element evidence framework prevents premature consolidation

### Negative

- Initial mistake on sub-project analysis had to be corrected
- Template and ADR system needed extension

### Neutral

- Audit is a snapshot in time; will need ongoing maintenance

---

## Compliance

### Constitutional Principles Affected

- **Article 11 — Explainability (02):** Every system action must be explainable. The capability registry makes every capability's "what, why, where, how" explainable.
- **§15 — Measurability & Testability (14):** Every requirement must have a specific test. The audit defines precise criteria for each capability metric.

### Engineering Constitution Articles Affected

- **Evidence Rule:** Every claim in the audit is backed by a documented file path.

---

## Verification

- [x] 62+ capabilities inventoried with evidence paths
- [x] 27 hidden capabilities identified with "why hidden" documented
- [x] Sub-project analysis corrected from "archive" to "integrate"
- [x] Percentage claims removed from all documents
- [x] Capability registry created
- [x] ADRs created for all significant decisions

---

## References

- [Phase 0 Audit Report](/home/shunya-deploy/shunya_os/docs/reports/phase0-universal-capability-audit.md)
- [Phase 1 Consolidation Plan](/home/shunya-deploy/shunya_os/docs/reports/phase1-consolidation-and-exposure-plan.md)
- [Canonical Capability Registry](/home/shunya-deploy/shunya_os/governance/capability-registry.md)
- [Evidence-Based Consolidation Framework (Founder Addendum)](/home/shunya-deploy/shunya_os/docs/canon/14_product_constitution.md)