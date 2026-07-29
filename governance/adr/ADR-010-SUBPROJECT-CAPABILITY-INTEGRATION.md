# ADR-010: Sub-Project Capability Integration (Not Archival)

**Class:** Engineering
**Status:** Accepted
**Date:** 2026-07-28
**Author:** Hermes Agent (per Founder directive)
**Supersedes:** (none)
**Superseded by:** (none)

**Approval Authority:**
- If Engineering: Chief Software Architect

**Related Constitutional Directives:**
- Product Constitution (14) — §12 (Universal Organization Adaptation): same OS adapts to all org types
- Addendum — Evidence-Based Consolidation & Canonical Selection (2026-07-28)
- ADR-008 — Capability Audit & Evidence Preservation

---

## Context

The SHUNYA repository contains 5 independent Flask sub-projects:

| Sub-project | Python Files | Templates | Tests |
|------------|-------------|-----------|-------|
| `shunya_os_crm/` | 173 | 37 | 44 |
| `shunya_os_dashboard/` | 155 | 35 | 42 |
| `shunya_os_documents/` | 171 | 39 | 44 |
| `shunya_os_gmail/` | 150 | 37 | 42 |
| `shunya_os_workflow/` | 155 | 37 | 40 |

Initial analysis (Phase 0 draft) concluded these were "duplicate template sets" and proposed archival. Further evidence-based analysis revealed that each sub-project contains unique backend capabilities NOT present in the main app.

**None of the 5 sub-projects are imported or registered by the main app.** They are independent, non-running Flask applications.

---

## Evidence Reviewed

| Evidence | Source | What It Proves |
|----------|--------|----------------|
| CRM unique capabilities | `shunya_os_crm/app/crm/` — quotation service, timeline, CRM entities | Full quotation engine with revisions, PDF, line items, taxes, discounts — NOT in main app |
| Dashboard unique capabilities | `shunya_os_dashboard/app/executive/` — widgets, KPI, insight providers, brief engine | Partially overlaps `app/executive/` in main app |
| Documents unique capabilities | `shunya_os_documents/app/document/` — 6 reader types, pipeline, knowledge graph, search index | DOCX/PDF/XLSX/CSV/OCR readers NOT in main app (main app has one `document_reader.py`) |
| Gmail unique capabilities | `shunya_os_gmail/app/communication/` — gmail_sync.py, gmail_watch.py; `app/events/bus.py` | Gmail sync/watch partially overlaps `app/adapters/gmail/` |
| Workflow unique capabilities | `shunya_os_workflow/app/workflow_engine/` — 9 files (plugins, contracts, triggers, scheduler, retry, conditions, event bus, registry, actions) | Entirely unique — main app has NO workflow engine |
| Zero imports in main app | `grep -rn "shunya_os_" app/ --include="*.py"` | No sub-project is imported or registered by the main app |
| Template duplication | All 5 sub-projects have copies of the same 37 templates | Templates are duplicates but backend code is NOT |

---

## Options Considered

### Option 1: Archive all 5 sub-projects (INITIALLY PROPOSED, REJECTED)

**Pros:**
- Removes ~800 Python files from the repository
- Cleaner repository structure

**Cons:**
- **Loses unique capabilities:** quotation engine, document readers, workflow engine, Gmail sync, KPI engine
- No migration path for those capabilities
- Architectural knowledge is destroyed

**Evidence against:** Each sub-project has unique backend code not in the main app. Archival would destroy 5 independent capability sets.

### Option 2: Leave all 5 sub-projects as-is (STATUS QUO)

**Pros:**
- Zero risk of breaking anything
- Capabilities remain available for future integration

**Cons:**
- Capabilities remain hidden — no Founder can access quotation engine, workflow engine, etc.
- Repository clutter grows over time
- Duplicate templates waste space and create confusion

### Option 3: Integrate unique capabilities; preserve template duplicates (CHOSEN)

**Pros:**
- Capabilities become accessible through the canonical OS
- Each capability evaluated for integration individually
- No capability lost

**Cons:**
- Integration work required for each capability
- Template duplicates remain until main app templates are consolidated

**Evidence for:** Each sub-project's unique capabilities are well-defined and bounded. Integration can be done one capability at a time.

---

## Decision

**Option 3 — Integrate unique capabilities; no archival.** Each sub-project's unique backend capabilities will be evaluated for integration into the canonical OS. The template duplicates are a cosmetic issue that can be addressed later.

Priority order for integration:
1. **CRM quotation engine** (P1 — business capability, no overlap with main app, complete implementation with PDF generation)
2. **Workflow engine** (P1 — entirely unique, complete, enhances automation)
3. **Document readers** (P2 — partially overlaps main app's `document_reader.py`, but has 6 reader types vs 1)
4. **Gmail sync** (P2 — partially overlaps `app/adapters/gmail/`)
5. **Dashboard widgets** (P3 — overlaps `app/executive/`)
6. **Template duplicates** (P3 — cosmetic, no functional impact)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Sub-project code depends on sub-project's app factory, not main app's | High | Medium | Each integration requires import path updates and dependency resolution |
| Integration creates duplicate capabilities in main app | Medium | High | Comparison step before each integration: does main app already have this? |
| Sub-project tests break during migration | Medium | Low | Run both test suites; tests should adapt to new import paths |
| Some sub-project code is stale or incomplete | Medium | Low | Verify functionality before integration; defer if non-functional |

---

## Migration Plan

For each capability integration:

1. **Evidence** — Verify capability exists, functions, has tests
2. **Comparison** — Does main app have equivalent? Capability-by-capability
3. **Copy** — Move source files to canonical location in `app/` or `core/`
4. **Adapt** — Update import paths, app factory references
5. **Test** — Run sub-project tests + main app tests
6. **Wire** — Connect to Founder surface via workspace runtime

---

## Rollback Plan

Per capability: restore original files from git, remove canonical copies.

---

## Consequences

### Positive

- No capability lost
- Quotation engine, workflow engine, document readers become accessible
- Repository consolidation without data loss

### Negative

- Integration work required for each of 5 sub-projects
- Template duplicates remain until separate consolidation

### Neutral

- Sub-projects remain in repository during integration
- Can be removed individually after each capability is integrated

---

## Compliance

### Constitutional Principles Affected

- **§12 — Universal Organization Adaptation (14):** CRM (companies), workflow (all orgs), documents (all orgs) capabilities enable organization-type adaptation.

### Engineering Constitution Articles Affected

- **Evidence before action:** The initial "archive" conclusion was corrected when evidence showed unique capabilities. This ADR documents that correction.

---

## Verification

- [ ] Every unique sub-project capability is catalogued in capability registry
- [ ] No sub-project is archived without evidence that all capabilities are preserved
- [ ] Each integration PR demonstrates capability-by-capability comparison
- [ ] Sub-project test suites continue to pass during migration
- [ ] Main app test suite continues to pass after each integration

---

## References

- [Sub-project CRM quotation engine](/home/shunya-deploy/shunya_os/shunya_os_crm/app/crm/quotation/)
- [Sub-project workflow engine](/home/shunya-deploy/shunya_os/shunya_os_workflow/app/workflow_engine/)
- [Sub-project document readers](/home/shunya-deploy/shunya_os/shunya_os_documents/app/document/)
- [Phase 1 Consolidation Plan](/home/shunya-deploy/shunya_os/docs/reports/phase1-consolidation-and-exposure-plan.md)
- [Canonical Capability Registry](/home/shunya-deploy/shunya_os/governance/capability-registry.md) — entries for crm-quotation-engine, document-readers, workflow-engine, gmail-sync, dashboard-executive-widgets