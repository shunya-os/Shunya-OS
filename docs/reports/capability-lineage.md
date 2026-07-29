# SHUNYA Capability Lineage

> **Living Document — Updated with every implementation PR**
> **Version:** 1.0 (Initial — Phase 0 Audit)
> **Date:** 2026-07-28
> **Purpose:** Track every capability through its lifecycle stages so no capability loses its historical context.

---

## Lineage Format

Every capability follows this lineage:

```
Capability Name
  ↓ Original Implementation — Where the capability was first built
  ↓ Audit Findings — Phase 0 audit findings
  ↓ Consolidation Decision — ADR reference and decision summary
  ↓ Migration — How the capability was moved to canonical location
  ↓ Canonical Implementation — Where the capability lives now
  ↓ Founder Exposure — How the Founder discovers and uses it
```

---

## Lineage Records

### user-login

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/auth_routes.py` — legacy auth with TeamMember model, integer IDs |
| **Audit Findings** | 2 parallel auth systems (legacy + canonical). Legacy has UI template. Canonical has MFA, password reset, email verification. |
| **Consolidation Decision** | ADR-009: Parallel coexistence with redirects. Canonical becomes default. Legacy preserved until TeamMember consumers migrate. |
| **Migration** | SPA login → canonical auth API. Legacy routes redirect. |
| **Canonical Implementation** | `app/production/auth/__init__.py` — `POST /api/v1/auth/login` |
| **Founder Exposure** | `/auth/login` → SPA login page |

### user-registration

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/auth_routes.py` — legacy registration |
| **Audit Findings** | Dual system. Canonical has email verification. |
| **Consolidation Decision** | ADR-009: Canonical auth default. |
| **Migration** | SPA registration → canonical auth API |
| **Canonical Implementation** | `app/production/auth/__init__.py` — `POST /api/v1/auth/register` |
| **Founder Exposure** | `/auth/register` → SPA registration form |

### password-reset

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/production/auth/password_reset_routes.py` — new capability, no legacy equivalent |
| **Audit Findings** | API-only, no UI surface. Works end-to-end via email link. |
| **Consolidation Decision** | ADR-009: Keep as canonical. Needs UI exposure. |
| **Migration** | Not needed — already in canonical location. |
| **Canonical Implementation** | `app/production/auth/password_reset_routes.py` |
| **Founder Exposure** | Login page → "Forgot password" → email link. Needs settings panel for full exposure. |

### email-verification

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/production/auth/email_verification_routes.py` — new capability |
| **Audit Findings** | API-only, works via email link. |
| **Consolidation Decision** | ADR-009: Keep as canonical. |
| **Migration** | Not needed. |
| **Canonical Implementation** | `app/production/auth/email_verification_routes.py` |
| **Founder Exposure** | Triggered by registration → email link. Needs settings panel. |

### mfa

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/production/auth/mfa_routes.py` — new capability |
| **Audit Findings** | API-only, no UI. Security-critical. |
| **Consolidation Decision** | ADR-009: Keep as canonical. Needs settings UI. |
| **Migration** | Not needed. |
| **Canonical Implementation** | `app/production/auth/mfa_routes.py` |
| **Founder Exposure** | No UI surface — needs settings panel. |

### session-management

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/production/auth/session_routes.py` — new capability |
| **Audit Findings** | API-only, no UI. |
| **Consolidation Decision** | ADR-009: Keep as canonical. Needs settings UI. |
| **Migration** | Not needed. |
| **Canonical Implementation** | `app/production/auth/session_routes.py` |
| **Founder Exposure** | No UI surface — needs settings panel. |

### organization-crud

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/production/identity/org_routes.py` — new capability for canonical OS identity |
| **Audit Findings** | Full CRUD with org lifecycle (activate/deactivate/archive). API-only, no UI. |
| **Consolidation Decision** | ADR-008: No consolidation needed — sole implementation. Needs exposure. |
| **Migration** | Not needed. |
| **Canonical Implementation** | `app/production/identity/org_routes.py` |
| **Founder Exposure** | No UI surface — needs org creation flow. |

### workspace-crud

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/production/identity/workspace_routes.py` — new capability |
| **Audit Findings** | Full CRUD with PUT/DELETE. API-only, no UI. |
| **Consolidation Decision** | ADR-008: No consolidation needed. Needs exposure. |
| **Migration** | Not needed. |
| **Canonical Implementation** | `app/production/identity/workspace_routes.py` |
| **Founder Exposure** | No UI surface — needs workspace creation flow. |

### space-crud (and 15 related space capabilities)

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `app/space/` (Phase A1/A1A) — 17 files, 16 routes |
| **Audit Findings** | Most complete hidden capability. Full universal space runtime with AI Resident, reasoning, lifecycle, commands, capabilities, composition, timeline, knowledge, relationships. Zero frontend consumption. |
| **Consolidation Decision** | ADR-008: No consolidation needed. Highest-priority exposure target. |
| **Migration** | Not needed. |
| **Canonical Implementation** | `app/space/routes.py`, `app/space/store.py`, `app/space/resident.py`, `app/space/reasoning.py` (17 files total) |
| **Founder Exposure** | No UI surface — needs workspace components that consume `/api/v1/space/` endpoints. |

### intelligence-perception (and 7 related intelligence engines)

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `core/intelligence/` — 8 sub-engines (perception, reasoning, planning, decision, learning, reflection, context_assembly, confidence) |
| **Audit Findings** | 8 complete engine implementations. No pipeline connection to any UI. |
| **Consolidation Decision** | ADR-008: No consolidation needed. Needs pipeline wiring. |
| **Migration** | Not needed. |
| **Canonical Implementation** | `core/intelligence/{perception,reasoning,planning,decision,learning,reflection,context_assembly,confidence}/engine.py` |
| **Founder Exposure** | No direct UI — output visible through AI reasoning traces and confidence scores once wired. |

### crm-quotation-engine

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `shunya_os_crm/app/crm/quotation/` — independent sub-project |
| **Audit Findings** | Full quotation engine with CRUD, revisions, line items, taxes, discounts, attachments, PDF generation. NOT in main app. NOT imported by main app. |
| **Consolidation Decision** | ADR-010: Integrate into main app (`app/`). Not archival. |
| **Migration** | Copy to canonical location in `app/`. Update import paths. Verify tests. Wire to Founder surface. |
| **Canonical Implementation** | (target) `app/crm/quotation/` |
| **Founder Exposure** | (target) Workspace → Sales → Quotations |

### workflow-engine

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `shunya_os_workflow/app/workflow_engine/` — 9 files (plugins, contracts, triggers, scheduler, retry, conditions, event bus, registry, actions) |
| **Audit Findings** | Full workflow engine. Entirely unique — main app has NO workflow engine. |
| **Consolidation Decision** | ADR-010: Integrate into `core/automation_runtime/`. Not archival. |
| **Migration** | Copy to `core/automation_runtime/`. Adapt imports. Verify 40 tests. Wire to AI: "Set up a workflow." |
| **Canonical Implementation** | (target) `core/automation_runtime/` |
| **Founder Exposure** | (target) Workspace → Settings → Automation |

### document-readers

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `shunya_os_documents/app/document/readers/` — DOCX, PDF, XLSX, TXT, CSV, OCR readers |
| **Audit Findings** | 6 reader types vs main app's single `app/document_reader.py`. Partially overlaps. |
| **Consolidation Decision** | ADR-010: Integrate into `app/artifact/`. Compare capability-by-capability first. |
| **Migration** | Copy to `app/artifact/readers/`. Deduplicate with existing `document_reader.py`. Verify 44 tests. |
| **Canonical Implementation** | (target) `app/artifact/readers/` |
| **Founder Exposure** | (target) Workspace → Documents → Upload → Auto-detect format |

### gmail-sync

| Stage | Detail |
|-------|--------|
| **Original Implementation** | `shunya_os_gmail/app/communication/gmail_sync.py`, `gmail_watch.py` |
| **Audit Findings** | Gmail sync/watch. Partially overlaps `app/adapters/gmail/`. |
| **Consolidation Decision** | ADR-010: Integrate into `app/adapters/gmail/`. Compare capability-by-capability first. |
| **Migration** | Compare with `app/adapters/gmail/`. Consolidate. Verify 42 tests. |
| **Canonical Implementation** | (target) `app/adapters/gmail/` |
| **Founder Exposure** | (target) Workspace → Settings → Integrations → Gmail |

---

## Lineage Update Procedure

When a capability changes state (new implementation, migration, exposure):

1. Find the capability in this lineage document
2. Add a new row to the lineage table for the new state
3. Reference the governing ADR
4. Update the capability registry entry
5. Include the lineage update in the implementation PR

If a capability is not yet in this document:
1. Create a new lineage record following the format above
2. Add all known lineage stages
3. Reference the earliest audit/ADR that identified the capability