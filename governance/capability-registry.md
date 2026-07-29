# SHUNYA Canonical Capability Registry

> **Living Document — Updated with every implementation PR**
> **Version:** 1.0 (Initial — Phase 0 Audit)
> **Date:** 2026-07-28
> **Maintainer:** Chief Software Architect
> **Update Rule:** Every PR that adds, modifies, or exposes a capability must update this registry.

---

## Registry Structure

Every capability entry records:

| Field | Description |
|-------|-------------|
| **ID** | Canonical capability identifier (machine-readable, lowercase-hyphenated) |
| **Name** | Human-readable capability name |
| **Canonical Owner** | Module/runtime that owns the canonical implementation |
| **Implementation Location** | File path(s) to the canonical implementation |
| **Entry Point** | How the capability is triggered (route, API endpoint, AI intent) |
| **AI Invocation Path** | How AI can invoke this capability |
| **Founder Access Path** | How the Founder discovers and uses this capability |
| **Related Tests** | Test file path(s) |
| **Governing ADR** | ADR that governs this capability |
| **Constitutional References** | SHUNYA Constitution + Product Constitution citations |
| **Status** | Hidden / Exposed / Foundry-Ready / Release-Ready |
| **Lineage** | Link to capability lineage record |

---

## Registry Entries

### Identity & Authentication

| Field | Value |
|-------|-------|
| **ID** | `user-registration` |
| **Name** | User Registration |
| **Canonical Owner** | `app/production/auth/` |
| **Implementation Location** | `app/production/auth/__init__.py` |
| **Entry Point** | `POST /api/v1/auth/register` |
| **AI Invocation Path** | Intent: "Create an account" → `process_intent()` |
| **Founder Access Path** | SPA login page → "Create account" link |
| **Related Tests** | `tests/production/identity/test_user_routes.py` |
| **Governing ADR** | ADR-009 |
| **Constitutional References** | §2.1 (Binding Authority) |
| **Status** | Exposed |
| **Lineage** | Legacy: `app/auth_routes.py` → Canonical: `app/production/auth/` → See ADR-009 |

---

| Field | Value |
|-------|-------|
| **ID** | `user-login` |
| **Name** | User Login (Password) |
| **Canonical Owner** | `app/production/auth/` |
| **Implementation Location** | `app/production/auth/__init__.py` |
| **Entry Point** | `POST /api/v1/auth/login` |
| **AI Invocation Path** | Intent: "Sign me in" → `process_intent()` |
| **Founder Access Path** | `/auth/login` → SPA login page |
| **Related Tests** | `tests/production/identity/test_user_routes.py` |
| **Governing ADR** | ADR-009 |
| **Constitutional References** | Article 2 (Human Agency) |
| **Status** | Exposed |
| **Lineage** | Legacy: `app/auth_routes.py` → Canonical: `app/production/auth/` → See ADR-009 |

---

| Field | Value |
|-------|-------|
| **ID** | `password-reset` |
| **Name** | Password Reset |
| **Canonical Owner** | `app/production/auth/password_reset_routes.py` |
| **Implementation Location** | `app/production/auth/password_reset_routes.py` |
| **Entry Point** | `POST /api/v1/auth/forgot-password`, `GET /api/v1/auth/reset-password/<token>` |
| **AI Invocation Path** | Intent: "Reset my password" → `process_intent()` |
| **Founder Access Path** | Login page → "Forgot password" |
| **Related Tests** | (no dedicated test — covered by auth integration tests) |
| **Governing ADR** | ADR-009 |
| **Constitutional References** | Article 4 (Privacy by Intention) |
| **Status** | Hidden (API only, no UI) |
| **Lineage** | New capability — no legacy equivalent |

---

| Field | Value |
|-------|-------|
| **ID** | `email-verification` |
| **Name** | Email Verification |
| **Canonical Owner** | `app/production/auth/email_verification_routes.py` |
| **Implementation Location** | `app/production/auth/email_verification_routes.py` |
| **Entry Point** | `POST /api/v1/auth/request-verification`, `GET /api/v1/auth/verify-email/<token>` |
| **AI Invocation Path** | (not AI-invokable — email-triggered) |
| **Founder Access Path** | Triggered by registration; email link |
| **Related Tests** | (no dedicated test) |
| **Governing ADR** | ADR-009 |
| **Constitutional References** | Article 4 (Privacy by Intention) |
| **Status** | Hidden (API only, email flow exists) |
| **Lineage** | New capability — no legacy equivalent |

---

| Field | Value |
|-------|-------|
| **ID** | `mfa` |
| **Name** | Multi-Factor Authentication |
| **Canonical Owner** | `app/production/auth/mfa_routes.py` |
| **Implementation Location** | `app/production/auth/mfa_routes.py` |
| **Entry Point** | `POST /api/v1/auth/mfa/*` |
| **AI Invocation Path** | (not AI-invokable — security critical) |
| **Founder Access Path** | No UI surface — needs settings panel |
| **Related Tests** | (no dedicated test) |
| **Governing ADR** | ADR-009 |
| **Constitutional References** | Article 3 (Permission Before Action) |
| **Status** | Hidden (API only, no UI) |
| **Lineage** | New capability — no legacy equivalent |

---

| Field | Value |
|-------|-------|
| **ID** | `session-management` |
| **Name** | Session Management |
| **Canonical Owner** | `app/production/auth/session_routes.py` |
| **Implementation Location** | `app/production/auth/session_routes.py` |
| **Entry Point** | `POST /api/v1/auth/revoke-sessions`, `GET /api/v1/auth/devices` |
| **AI Invocation Path** | Intent: "Show my active sessions" → `process_intent()` |
| **Founder Access Path** | No UI surface — needs settings panel |
| **Related Tests** | (no dedicated test) |
| **Governing ADR** | ADR-009 |
| **Constitutional References** | Article 3 (Permission Before Action) |
| **Status** | Hidden (API only, no UI) |
| **Lineage** | New capability — no legacy equivalent |

---

### Organization & Identity

| Field | Value |
|-------|-------|
| **ID** | `organization-crud` |
| **Name** | Organization CRUD |
| **Canonical Owner** | `app/production/identity/` |
| **Implementation Location** | `app/production/identity/org_routes.py` |
| **Entry Point** | `GET/POST/PUT/DELETE /orgs` |
| **AI Invocation Path** | Intent: "Create my organization" → `process_intent()` |
| **Founder Access Path** | No UI surface — needs org creation flow |
| **Related Tests** | `tests/production/identity/test_org_routes.py` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §12 (Universal Organization Adaptation), Article 8 (Identity Before Organization) |
| **Status** | Hidden (API only, no UI) |
| **Lineage** | New capability — no legacy equivalent in main app |

---

| Field | Value |
|-------|-------|
| **ID** | `workspace-crud` |
| **Name** | Workspace CRUD |
| **Canonical Owner** | `app/production/identity/` |
| **Implementation Location** | `app/production/identity/workspace_routes.py` |
| **Entry Point** | `GET/POST/PUT/DELETE /orgs/{id}/workspaces` |
| **AI Invocation Path** | Intent: "Create a workspace" → `process_intent()` |
| **Founder Access Path** | No UI surface — needs workspace creation flow |
| **Related Tests** | `tests/production/identity/test_workspace_routes.py` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §12 (Universal Organization Adaptation) |
| **Status** | Hidden (API only, no UI) |
| **Lineage** | New capability — no legacy equivalent |

---

### Space System (Universal Space)

| Field | Value |
|-------|-------|
| **ID** | `space-crud` |
| **Name** | Space CRUD |
| **Canonical Owner** | `app/space/` |
| **Implementation Location** | `app/space/routes.py` (create/get/update/delete), `app/space/store.py` |
| **Entry Point** | `POST/GET/PUT/DELETE /api/v1/space/` |
| **AI Invocation Path** | Intent: "Create a space for Project X" → `app/space/routes.py` |
| **Founder Access Path** | No UI surface (16 space APIs all hidden) |
| **Related Tests** | `tests/space/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §3 (Universal Intelligence Principle), §11 (Product Discoverability) |
| **Status** | Hidden (16 API endpoints, zero frontend consumption) |
| **Lineage** | Phase A1 implementation — complete runtime, no exposure yet |

---

| Field | Value |
|-------|-------|
| **ID** | `space-ai-resident` |
| **Name** | AI Resident (Per-Space Persistent AI) |
| **Canonical Owner** | `app/space/resident.py` |
| **Implementation Location** | `app/space/resident.py`, `app/space/routes.py` (get/update) |
| **Entry Point** | `GET/PUT /api/v1/space/{id}/ai-resident` |
| **AI Invocation Path** | AI reads/writes `AIResidentState` for current space |
| **Founder Access Path** | No UI surface |
| **Related Tests** | `tests/space/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §10 (Universal AI Presence), §11 (Product Discoverability) |
| **Status** | Hidden |
| **Lineage** | Phase A1A — complete, no exposure yet |

---

| Field | Value |
|-------|-------|
| **ID** | `cross-space-reasoning` |
| **Name** | Cross-Space Reasoning |
| **Canonical Owner** | `app/space/reasoning.py` |
| **Implementation Location** | `app/space/reasoning.py`, `app/space/routes.py` (reason, path) |
| **Entry Point** | `POST /api/v1/space/{id}/reason`, `POST /api/v1/space/reason/path` |
| **AI Invocation Path** | AI initiates reasoning across related spaces |
| **Founder Access Path** | No UI surface |
| **Related Tests** | `tests/space/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §3 (Universal Intelligence Principle) |
| **Status** | Hidden |
| **Lineage** | Phase A1A — complete, no exposure yet |

---

### Intelligence (Core)

| Field | Value |
|-------|-------|
| **ID** | `intelligence-perception` |
| **Name** | Perception Engine |
| **Canonical Owner** | `core/intelligence/perception/` |
| **Implementation Location** | `core/intelligence/perception/engine.py`, `core/intelligence/perception/models.py` |
| **Entry Point** | Via `ShunyaOS.process_intent()` → Intelligence Runtime |
| **AI Invocation Path** | Automatic — invoked as first stage of intelligence pipeline |
| **Founder Access Path** | No direct UI — output visible through AI reasoning traces |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §3 (Universal Intelligence Principle) |
| **Status** | Hidden (no pipeline connection to any UI) |
| **Lineage** | Core implementation complete — not wired to any pipeline |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-reasoning` |
| **Name** | Reasoning Engine (5 types) |
| **Canonical Owner** | `core/intelligence/reasoning/` |
| **Implementation Location** | `core/intelligence/reasoning/engine.py` |
| **Entry Point** | Via intelligence pipeline |
| **AI Invocation Path** | Automatic — invoked for reasoning-requiring intents |
| **Founder Access Path** | No direct UI — output visible through AI reasoning traces |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §3 (Universal Intelligence Principle) |
| **Status** | Hidden |
| **Lineage** | Core implementation complete — 5 reasoning types |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-planning` |
| **Name** | Planning Engine |
| **Canonical Owner** | `core/intelligence/planning/` |
| **Implementation Location** | `core/intelligence/planning/engine.py` |
| **Entry Point** | Via intelligence pipeline |
| **AI Invocation Path** | Automatic — invoked for planning intents |
| **Founder Access Path** | No direct UI |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §9 (Universal Action Principle) |
| **Status** | Hidden |
| **Lineage** | Core implementation complete |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-decision` |
| **Name** | Decision Engine |
| **Canonical Owner** | `core/intelligence/decision/` |
| **Implementation Location** | `core/intelligence/decision/engine.py` |
| **Entry Point** | Via intelligence pipeline |
| **AI Invocation Path** | Automatic — invoked for decision-making intents |
| **Founder Access Path** | No direct UI |
| **Related Tests** | `core/intelligence/decision/tests/test_decision_engine.py` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §9 (Universal Action Principle) |
| **Status** | Hidden |
| **Lineage** | Core implementation complete with dedicated tests |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-learning` |
| **Name** | Learning Engine |
| **Canonical Owner** | `core/intelligence/learning/` |
| **Implementation Location** | `core/intelligence/learning/engine.py` |
| **Entry Point** | Via intelligence pipeline |
| **AI Invocation Path** | Automatic — invoked for learning from outcomes |
| **Founder Access Path** | No direct UI |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §9 (Universal Action Principle) |
| **Status** | Hidden |
| **Lineage** | Core implementation complete |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-reflection` |
| **Name** | Reflection Engine |
| **Canonical Owner** | `core/intelligence/reflection/` |
| **Implementation Location** | `core/intelligence/reflection/engine.py` |
| **Entry Point** | Via intelligence pipeline |
| **AI Invocation Path** | Automatic — invoked for self-evaluation |
| **Founder Access Path** | No direct UI |
| **Related Tests** | `core/intelligence/reflection/tests/test_reflection_engine.py` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §9 (Universal Action Principle) |
| **Status** | Hidden |
| **Lineage** | Core implementation complete with dedicated tests |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-context-assembly` |
| **Name** | Context Assembly Engine |
| **Canonical Owner** | `core/intelligence/context_assembly/` |
| **Implementation Location** | `core/intelligence/context_assembly/engine.py` |
| **Entry Point** | Via intelligence pipeline |
| **AI Invocation Path** | Automatic — assembles context from multiple sources |
| **Founder Access Path** | No direct UI |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §4 (Universal Knowledge Routing) |
| **Status** | Hidden |
| **Lineage** | Core implementation complete |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-confidence` |
| **Name** | Confidence Scoring Engine |
| **Canonical Owner** | `core/intelligence/confidence/` |
| **Implementation Location** | `core/intelligence/confidence/engine.py` |
| **Entry Point** | Via intelligence pipeline |
| **AI Invocation Path** | Automatic — provides confidence scores for all AI outputs |
| **Founder Access Path** | No direct UI |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | Article 11 (Explainability Is Non-Negotiable) |
| **Status** | Hidden |
| **Lineage** | Core implementation complete |

---

### Workspace & Navigation

| Field | Value |
|-------|-------|
| **ID** | `workspace-spa` |
| **Name** | Workspace SPA (Primary Founder Surface) |
| **Canonical Owner** | `app/workspace_routes.py` + `frontend/dist/` |
| **Implementation Location** | `app/workspace_routes.py` (backend), `frontend/dist/index.html`, `frontend/src/` (React source) |
| **Entry Point** | `GET /workspace/` (serves SPA shell), `GET /api/workspace/object/<type>/<id>` (JSON API) |
| **AI Invocation Path** | AI copilot component at `frontend/src/components/copilot/ai-copilot.tsx` |
| **Founder Access Path** | `/workspace/` or `/` (planned) |
| **Related Tests** | (no dedicated E2E tests) |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §10 (Universal AI Presence), §11 (Product Discoverability) |
| **Status** | Exposed (SPA built, AI copilot component exists, but backend APIs not fully consumed) |
| **Lineage** | SPA is primary target surface; founder routes also serve Jinja2 templates |

---

### App Intelligence (Routes & Service)

| Field | Value |
|-------|-------|
| **ID** | `intelligence-traces` |
| **Name** | Reasoning Traces |
| **Canonical Owner** | `app/intelligence/` |
| **Implementation Location** | `app/intelligence/service.py`, `app/intelligence/routes.py` |
| **Entry Point** | `GET /api/v1/intelligence/traces`, `GET /api/v1/intelligence/traces/<id>` |
| **AI Invocation Path** | Automatic — every AI response produces a trace |
| **Founder Access Path** | No UI surface — needs reasoning trace panel |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | Article 11 (Explainability Is Non-Negotiable) |
| **Status** | Hidden (API only) |
| **Lineage** | Part of M8 Executive Intelligence |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-learning-history` |
| **Name** | Learning History |
| **Canonical Owner** | `app/intelligence/` |
| **Implementation Location** | `app/intelligence/routes.py` — `/api/v1/intelligence/learning` |
| **Entry Point** | `GET /api/v1/intelligence/learning`, `GET /api/v1/intelligence/learning/summary` |
| **AI Invocation Path** | Automatic — learning from feedback |
| **Founder Access Path** | No UI surface |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | Article 12 (Data Is Evidence, Not Asset) |
| **Status** | Hidden (API only) |
| **Lineage** | Part of M8 Executive Intelligence |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-anomalies` |
| **Name** | Anomaly Detection |
| **Canonical Owner** | `app/intelligence/` |
| **Implementation Location** | `app/intelligence/routes.py` — `/api/v1/intelligence/anomalies` |
| **Entry Point** | `GET /api/v1/intelligence/anomalies`, `POST /api/v1/intelligence/anomalies/detect` |
| **AI Invocation Path** | Automatic — AI proactively detects anomalies |
| **Founder Access Path** | No UI surface |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §10 (Universal AI Presence — Monitor) |
| **Status** | Hidden (API only) |
| **Lineage** | Part of M8 Executive Intelligence |

---

| Field | Value |
|-------|-------|
| **ID** | `intelligence-confidence-api` |
| **Name** | Confidence Scoring (API) |
| **Canonical Owner** | `app/intelligence/` |
| **Implementation Location** | `app/intelligence/routes.py` — `/api/v1/intelligence/confidence` |
| **Entry Point** | `POST /api/v1/intelligence/confidence` |
| **AI Invocation Path** | Automatic — scores every AI output |
| **Founder Access Path** | No UI surface |
| **Related Tests** | `tests/intelligence/` |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | Article 11 (Explainability Is Non-Negotiable) |
| **Status** | Hidden (API only) |
| **Lineage** | Part of M8 Executive Intelligence |

---

### Output Generation

| Field | Value |
|-------|-------|
| **ID** | `invoice-pdf` |
| **Name** | Invoice PDF Generation |
| **Canonical Owner** | `app/routes.py` |
| **Implementation Location** | `app/routes.py` — `/invoices/<int:invoice_id>/pdf` |
| **Entry Point** | `GET /invoices/<invoice_id>/pdf` |
| **AI Invocation Path** | Intent: "Generate invoice PDF" → `process_intent()` |
| **Founder Access Path** | Invoices page → "Download PDF" button |
| **Related Tests** | (no dedicated test) |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §8 (Universal Output Generation) |
| **Status** | Exposed |
| **Lineage** | Legacy CRM implementation |

---

| Field | Value |
|-------|-------|
| **ID** | `document-management` |
| **Name** | Document Management & Upload |
| **Canonical Owner** | `app/routes.py` |
| **Implementation Location** | `app/routes.py` — `/documents`, `/documents/upload` |
| **Entry Point** | `GET /documents`, `POST /documents/upload` |
| **AI Invocation Path** | Intent: "Upload a document" → `process_intent()` |
| **Founder Access Path** | `/documents` page |
| **Related Tests** | (no dedicated test) |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §8 (Universal Output Generation) |
| **Status** | Exposed |
| **Lineage** | Legacy CRM implementation |

---

| Field | Value |
|-------|-------|
| **ID** | `itinerary-builder` |
| **Name** | Itinerary Builder |
| **Canonical Owner** | `app/routes.py` |
| **Implementation Location** | `app/routes.py` — `/itineraries`, `templates/itinerary_builder.html` |
| **Entry Point** | `GET /itineraries` |
| **AI Invocation Path** | Intent: "Create a Bali itinerary" → `process_intent()` |
| **Founder Access Path** | `/itineraries` page |
| **Related Tests** | (no dedicated test) |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §8 (Universal Output Generation) |
| **Status** | Exposed (legacy Jinja2) |
| **Lineage** | Legacy CRM implementation |

---

### Finance

| Field | Value |
|-------|-------|
| **ID** | `payments` |
| **Name** | Payments Management |
| **Canonical Owner** | `app/routes.py` |
| **Implementation Location** | `app/routes.py` — create, verify, checkout, complete, receipt, link |
| **Entry Point** | `GET/POST /payments`, `/payment/*` |
| **AI Invocation Path** | Intent: "Process a payment" → `process_intent()` |
| **Founder Access Path** | `/payments` page |
| **Related Tests** | (no dedicated test) |
| **Governing ADR** | ADR-008 |
| **Constitutional References** | §12 (Universal Organization Adaptation) |
| **Status** | Exposed (legacy Jinja2) |
| **Lineage** | Legacy CRM implementation |

---

### Sub-Project Unique Capabilities

| Field | Value |
|-------|-------|
| **ID** | `crm-quotation-engine` |
| **Name** | CRM Quotation Engine |
| **Canonical Owner** | `shunya_os_crm/app/crm/quotation/` (to be migrated to `app/`) |
| **Implementation Location** | `shunya_os_crm/app/crm/quotation/service.py`, `routes.py`, `pdf.py` |
| **Entry Point** | `GET/POST/PUT/DELETE /api/crm/quotations/*` (sub-project only) |
| **AI Invocation Path** | Not yet wired |
| **Founder Access Path** | Not yet available |
| **Related Tests** | `shunya_os_crm/tests/` — 44 tests |
| **Governing ADR** | ADR-010 |
| **Constitutional References** | §12 (Universal Organization Adaptation) |
| **Status** | Hidden (exists only in sub-project, not wired to main app) |
| **Lineage** | Independent sub-project → See ADR-010 for integration plan |

---

| Field | Value |
|-------|-------|
| **ID** | `workflow-engine` |
| **Name** | Workflow Engine |
| **Canonical Owner** | `shunya_os_workflow/app/workflow_engine/` (to be migrated to `core/automation_runtime/`) |
| **Implementation Location** | `shunya_os_workflow/app/workflow_engine/` — 9 files |
| **Entry Point** | Sub-project only |
| **AI Invocation Path** | Not yet wired |
| **Founder Access Path** | Not yet available |
| **Related Tests** | `shunya_os_workflow/tests/` — 40 tests |
| **Governing ADR** | ADR-010 |
| **Constitutional References** | §9 (Universal Action Principle — Execute) |
| **Status** | Hidden (exists only in sub-project) |
| **Lineage** | Independent sub-project → See ADR-010 for integration plan |

---

| Field | Value |
|-------|-------|
| **ID** | `document-readers` |
| **Name** | Document Readers (6 types) |
| **Canonical Owner** | `shunya_os_documents/app/document/readers/` (to be migrated to `app/artifact/`) |
| **Implementation Location** | DOCX reader, PDF reader, XLSX reader, TXT reader, CSV reader, OCR reader |
| **Entry Point** | Sub-project only |
| **AI Invocation Path** | Not yet wired |
| **Founder Access Path** | Not yet available |
| **Related Tests** | `shunya_os_documents/tests/` — 44 tests |
| **Governing ADR** | ADR-010 |
| **Constitutional References** | §8 (Universal Output Generation) |
| **Status** | Hidden (exists only in sub-project) |
| **Lineage** | Independent sub-project → See ADR-010 for integration plan |

---

| Field | Value |
|-------|-------|
| **ID** | `gmail-sync` |
| **Name** | Gmail Sync & Watch |
| **Canonical Owner** | `shunya_os_gmail/app/communication/` (to be migrated to `app/adapters/gmail/`) |
| **Implementation Location** | `shunya_os_gmail/app/communication/gmail_sync.py`, `gmail_watch.py` |
| **Entry Point** | Sub-project only |
| **AI Invocation Path** | Not yet wired |
| **Founder Access Path** | Not yet available |
| **Related Tests** | `shunya_os_gmail/tests/` — 42 tests |
| **Governing ADR** | ADR-010 |
| **Constitutional References** | §4 (Universal Knowledge Routing — Connected Applications) |
| **Status** | Hidden (exists only in sub-project) |
| **Lineage** | Independent sub-project → See ADR-010 for integration plan |

---

## Summary Counts

| Status | Count | Definition |
|--------|-------|-----------|
| **Exposed** | 5 | Founder can find and use this capability from the primary surface |
| **Hidden** | 33 | Backend code exists but has no Founder-facing surface |
| **Sub-project (hidden)** | 5+ | Exists only in an independent sub-project, not wired to main OS |
| **Total registered** | 43+ | (subset of 62 inventoried — only canonical implementations are registered) |

---

## Update Procedure

When adding or modifying a capability:

1. Assign a unique ID (`kebab-case-name`)
2. Fill all registry fields with file-path evidence
3. Reference the governing ADR
4. Reference constitutional citations
5. Update the capability lineage document
6. Include registry update in the implementation PR