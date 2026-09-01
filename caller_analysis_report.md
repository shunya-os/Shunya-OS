# Production Caller Analysis: FounderObject / ShunyaObject / Object

## Model Summary

| Model | Table | Role |
|-------|-------|------|
| `FounderObject` | `founder_objects` | Legacy founder workspace objects |
| `ShunyaObject` (legacy_models) | `sh_objects` | Canonical object store (Phase 0 foundation, now "canonical") |
| `Object` (objects.models) | `objects` | Execution engine state / generic entity |

---

## WRITE Callers (Create / Update)

### FounderObject → `founder_objects`

| # | Caller File | Table Written | Concept Created | Classification | Justification |
|---|-------------|--------------|----------------|---------------|---------------|
| 1 | `app/founder/routes.py` (api_create_object, line 438) | `founder_objects` | General workspace objects (Documents, per user request) | **EXECUTION_ENGINE_STATE** | Dual-write from pipeline; workspace-level user objects, not canonical business entities |
| 2 | `app/automation/service.py` (_execute_action, line 248) | `founder_objects` | Auto-generated Task objects | **EXECUTION_ENGINE_STATE** | Automated execution engine state created by automation rules |
| 3 | `app/production/objects.py` (_create_typed_object_raw, line 161) | `founder_objects` | Typed business objects: customer, supplier, lead, invoice, task, proposal, employee, meeting, note, document, opportunity, quote, email, whatsapp, product, payment, expense, campaign, project, reminder | **MISCLASSIFIED — CANONICAL_BUSINESS_OBJECT** | Customers, invoices, proposals, etc. are **canonical business objects** but are being stored in `founder_objects` instead of `sh_objects`. This is the main migration target. |
| 4 | `app/ai/routes.py` (chat, line 328) | `founder_objects` | System conversation anchor objects | **EXECUTION_ENGINE_STATE** | Internal system state for AI chat persistence routing |
| 5 | `app/onboard.py` (onboard, line 81) | `founder_objects` | Initial onboarding objects: Document, Project, Lead (Company Overview, Getting Started Guide, etc.) | **MISCLASSIFIED — CANONICAL_BUSINESS_OBJECT** | Business-intent artifacts (documents, projects, leads) being stored in `founder_objects` |
| 6 | `app/production/identity/onboarding_routes.py` (mark_onboarding_complete, line 134) | `founder_objects` | 26 foundational objects: Customer, Supplier, Lead, Invoice, etc. | **MISCLASSIFIED — CANONICAL_BUSINESS_OBJECT** | These are canonical business object stubs being stored in `founder_objects` — should be `sh_objects` |
| 7 | `scripts/seed_demo.py` (seed, line 314-500) | `founder_objects` | Demo data: customers, suppliers, invoices, commitments, notes, conversations, timeline events for 3 orgs | **LEGACY_COMPAT** | Seed/demo script writing to legacy table |
| 8 | `scripts/seed_demo_m4.py` (line 45-132) | `founder_objects` | Demo data: Q3 Marketing Campaign, Acme Corp Partnership, Budget Spreadsheet | **LEGACY_COMPAT** | Seed/demo script writing to legacy table |
| 9 | `scripts/seed_panchi_club_demo.py` (insert_founder_object, raw SQL) | `founder_objects` | Demo data: personal notes, commitments, timeline events, conversations | **LEGACY_COMPAT** | Seed/demo script using raw SQL inserts to legacy table |

### ShunyaObject → `sh_objects`

| # | Caller File | Table Written | Concept Created | Classification | Justification |
|---|-------------|--------------|----------------|---------------|---------------|
| 10 | `app/objects/upload.py` (api_upload, line 103) | `sh_objects` | File upload document records | **CANONICAL_BUSINESS_OBJECT** ✅ | Correctly using `sh_objects` for document storage |
| 11 | `app/objects/seed.py` (seed_workspace, line 116) | `sh_objects` | Seed data: customers, invoices, proposals, tasks, contacts | **CANONICAL_BUSINESS_OBJECT** ✅ | Correctly using `sh_objects` for canonical business seed data |
| 12 | `app/objects/canonical.py` (create_canonical_object, line 131-168) | `sh_objects` | Canonical objects via object_service (org_id, workspace_id, etc.) | **CANONICAL_BUSINESS_OBJECT** ✅ | This IS the canonical write path — routes through core/object_service → sh_objects |

### Object (app.objects.models) → `objects`

| # | Caller File | Table Written | Concept Created | Classification | Justification |
|---|-------------|--------------|----------------|---------------|---------------|
| 13 | `scripts/seed_data.py` (seed, line 57) | `objects` | Lead entities with state (stage, deal_value) for awareness signal generation | **EXECUTION_ENGINE_STATE** ✅ | Seed data for execution engine signal generation; type="lead" stored in state field |
| 14 | `app/execution_engine/routes.py` (line 72-75) | `objects` | READ-only: documents, reports, files, notes from Object model (aliased as ShunyaObject) | **EXECUTION_ENGINE_STATE** (read) | Execution engine reading generic entities — reads from `objects` table |
| 15 | `app/communication/proposal_routes.py` (line 30) | `objects` | READ-only: reads Object by entity_id for proposal linking | **EXECUTION_ENGINE_STATE** (read) | Execution engine reading generic entities |
| 16 | `app/debug/routes.py` (line 112-218) | `objects` | READ/write on Object entities (get_trace, update_entity, get/save notes) | **EXECUTION_ENGINE_STATE** | Debug routes for execution engine generic entities |
| 17 | `app/operator/routes.py` (line 69-108) | `objects` | READ-only: entity detail and task lookup | **EXECUTION_ENGINE_STATE** (read) | Operator panel reading execution entities |
| 18 | `app/activation/routes.py` (line 62-83) | `objects` | READ-only: entity GET | **EXECUTION_ENGINE_STATE** (read) | Activation routes reading execution entities |

---

## Summary Counts

| Classification | Count | Callers |
|---|---|---|
| **CANONICAL_BUSINESS_OBJECT** (in correct table) | 3 | upload.py, seed.py, canonical.py → all write to `sh_objects` ✅ |
| **CANONICAL_BUSINESS_OBJECT** (misplaced in `founder_objects`) | 3 | production/objects.py, onboard.py, onboarding_routes.py → wrote business objects to wrong table ⚠️ |
| **EXECUTION_ENGINE_STATE** | 4 (+5 read-only) | founder/routes.py, automation/service.py, ai/routes.py, seed_data.py → correct in context |
| **LEGACY_COMPAT** (seed/demo scripts) | 3 | seed_demo.py, seed_demo_m4.py, seed_panchi_club_demo.py |

---

## Key Findings

### Critical: `app/production/objects.py` is the most significant misclassification
Creates 20+ canonical business object types (customer, supplier, lead, invoice, proposal, task, etc.) in `founder_objects` instead of `sh_objects`. This is the primary migration target.

### Critical: `onboarding_routes.py` creates 26 foundational object stubs in `founder_objects`
These are explicitly labeled as "foundational objects" (Article XII) but stored in the legacy table.

### Correct: `app/objects/canonical.py`, `app/objects/upload.py`, `app/objects/seed.py`
These already use `sh_objects` correctly for canonical business objects.

### Execution engine uses `objects` table separately
The `Object` model (table `objects`) is used for execution engine generic entities (leads as state machines, signal entities, etc.) and is separate from both the canonical store and founder workspace. This is appropriate.

### `app/automation/service.py` creates tasks in `founder_objects` — borderline
Automation-created tasks are execution engine state. Classification as EXECUTION_ENGINE_STATE is correct, but they could optionally be canonical objects.