# SHUNYA Duplicate Analysis Report
> **Part of the Canonical Repository & Knowledge Runtime Directive**
> **Date:** 2026-07-28
> **Status:** Candidate for Founder Review

## Methodology

This report identifies potential duplicates, conflicts, and consolidation opportunities
across the repository. The analysis is automated — nothing is deleted without founder
approval.

---

## 1. Duplicate Document Names

Files with identical names in different directories may indicate duplicate content,
obsolete copies, or intentional mirrors.

| File Name | Locations | Risk | Recommendation |
|-----------|-----------|------|----------------|
| `SHUNYA_CONSTITUTION.md` | `constitution/`, `architecture/` | MEDIUM | `architecture/SHUNYA_CONSTITUTION.md` is likely an older copy. Compare content; if superseded, mark as `@superseded` in knowledge graph. |
| `SHUNYA_ARCHITECTURE.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies of the same named file across sub-projects. These are likely stale copies of the canonical architecture document. |
| `SHUNYA_OS_NEXT_PLAN.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies. Each sub-project has its own copy — likely stale. |
| `SHUNYA_UNIVERSAL_PLATFORM.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies. |
| `SHUNYA_UNIVERSAL_UI_PLAN.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies. |
| `ARCHITECTURE.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies. |
| `DESIGN.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies. |
| `FINAL_PRODUCT_VISION.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies. |
| `PROJECT.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/` | HIGH | 6 copies. |
| `README.md` | `./`, `shunya_os_crm/`, `shunya_os_dashboard/`, `shunya_os_documents/`, `shunya_os_gmail/`, `shunya_os_workflow/`, `governance/`, `governance/adr/`, `governance/approvals/`, `governance/engine_specs/`, `governance/verification/`, `design/visual-design-bible/`, `design/experience/`, `infrastructure/environments/` | MEDIUM | 17+ README.md files — expected pattern but some may be stale. |
| `SHUNYA_ARCHITECTURE_v1.0.md` | `./`, `architecture/` | MEDIUM | Two copies. Root-level may be the canonical reference. |
| `knowledge-base.md` | `app/data/`, `shunya_os_crm/app/data/`, `shunya_os_dashboard/app/data/`, `shunya_os_documents/app/data/`, `shunya_os_gmail/app/data/`, `shunya_os_workflow/app/data/` | HIGH | 6 copies of a knowledge-base file. Likely stale sub-project mirrors. |
| `CAPABILITY_MATRIX.md` | `docs/canon/`, `governance/` | MEDIUM | Two copies possible — check if one is canonical. |
| `CONVERGENCE_PLAN.md` | `docs/canon/`, `docs/governance/` | LOW | Two convergence plans in different docs directories. |

## 2. Conflicting Definitions

| Term | Source 1 | Source 2 | Conflict |
|------|----------|----------|----------|
| Cognitive Architecture | CONST-III (§5) — "ten-engine structure" | ARCHITECTURE_v1.0 — may reference older 9-engine count | RESOLVED by CAP-01. Verify all documents reflect 10 engines. |
| Engine Count | architecture/SHUNYA_CONSTITUTION.md (legacy) | constitution/SHUNYA_CONSTITUTION.md (current) | Legacy copy in architecture/ may still reference 9 engines. |
| Phases | SHUNYA_IMPLEMENTATION_PROGRAM.md (15 phases) | SHUNYA_PROGRAM_BACKLOG.md (may differ) | Verify phase count consistency. |

## 3. Superseded ADRs

| ADR | Status | Superseded By | Notes |
|-----|--------|---------------|-------|
| ADR-001 (Event Bus) | Proposed | — | Check if implemented in core/event/ |
| ADR-002 (Knowledge Store) | Proposed | — | Check if knowledge_store/ implements this |
| ADR-003 (Credential Store) | Proposed | — | Check if infrastructure/credential_store.py implements this |
| ADR-004 (Universal Object Contract) | Draft | — | Check if core/kernel/object.py implements this |
| ADR-005 (Universal Identity) | Draft | — | Check if core/identity/ implements this |
| ADR-006 (Space Architecture) | Draft | — | Check if app/space/ implements this |
| ADR-007 (Relationship Contract) | Draft | — | Check if core/relationship/ implements this |

**Recommendation:** Update ADR status to reflect actual implementation state.

## 4. Obsolete Reports

| Report | Date | Phase Age | Recommendation |
|--------|------|-----------|----------------|
| PHASE_A_IMPLEMENTATION_REPORT.md | Unknown | Oldest phase | Keep for historical reference |
| All PHASE reports through PHASE_N | Unknown | Sequential | All are source material for the implementation program. Mark completed phases as `@superseded` in knowledge graph. |
| ENGINEERING_PROGRESS_REPORT_E001.md | Unknown | Pre-baseline | May be superseded by later reports |

## 5. Sub-Project Duplication

The following sub-projects appear to be duplicates of the main project:

| Directory | Files | Likely Status |
|-----------|-------|---------------|
| `shunya_os_crm/` | ~100 files | Stale copy of main project |
| `shunya_os_dashboard/` | ~100 files | Stale copy of main project |
| `shunya_os_documents/` | ~100 files | Stale copy of main project |
| `shunya_os_gmail/` | ~100 files | Stale copy of main project |
| `shunya_os_workflow/` | ~100 files | Stale copy of main project |

**Observation:** These appear to be workspace-specific variants of the primary project,
created during parallel development. Each contains a full copy of the app, templates,
and docs. The canonical code lives in the root `app/`, `core/`, and `templates/`
directories.

**Recommendation:** Consolidate into a single project. Archive sub-project directories
after verifying no unique code exists in them.

## 6. Multiple Canonical Owners

| Concept | Apparent Owners | Risk |
|---------|-----------------|------|
| SHUNYA Constitution | `constitution/` (canonical), `architecture/` (copy) | HIGH — stale copy may diverge |
| Architecture | SHUNYA_ARCHITECTURE.md, SHUNYA_ARCHITECTURE_v1.0.md, architecture/*.md | MEDIUM — hierarchy unclear |
| Governance | governance/ (canonical), docs/governance/ (external) | MEDIUM — ensure docs/governance/ is canonical |

## 7. Recommendations

### Immediate (No Architecture Change)
1. Remove stale copies from sub-project directories (`shunya_os_crm/`, etc.) after verifying no unique content
2. Remove `architecture/SHUNYA_CONSTITUTION.md` if it's a stale copy
3. Update ADR status fields to reflect actual implementation

### Short-Term (Requires Verification)
4. Audit all 6 copies of SHUNYA_ARCHITECTURE.md for unique content
5. Consolidate governance docs into a single canonical directory
6. Mark superseded phase reports in the knowledge graph

### Long-Term (Requires Founder Decision)
7. Decide whether to delete or archive sub-project directories
8. Establish a canonical document hierarchy to prevent future duplication

---

## Appendix: Detection Methodology

- **Duplicate names:** `find . -name "*.md" | sed 's|.*/||' | sort | uniq -d`
- **Conflicting definitions:** Manual cross-reference of key terms across documents
- **Superseded ADRs:** Comparison of ADR status with actual code implementation
- **Sub-project duplication:** Directory structure comparison
- **Multiple owners:** Cross-reference of document paths vs canonical declarations