# SHUNYA Phase 1 — Capability Consolidation & Exposure Plan

> **Derived from:** Phase 0 Universal Capability Audit
> **Governing Documents:** Addendum, Product Constitution (14), SHUNYA Constitution (02)
> **Principle:** Existing capability first. New implementation is always the final option.
> **Framework:** Every consolidation decision requires Evidence, Comparison, Risk, Canonical Justification, Founder Impact, and Verification.

---

## 1. Consolidation Strategy

Every consolidation decision in this document follows a 6-element framework:

1. **Evidence** — Objective proof of functionality, usage, dependencies, uniqueness, tests, consumers, runtime behaviour
2. **Comparison** — Capability-by-capability comparison, not directory or filename comparison
3. **Risk** — What breaks if removed? Who depends on it? Migration strategy. Rollback strategy.
4. **Canonical Justification** — Why this implementation becomes canonical. Why alternatives should not.
5. **Founder Impact** — How does this improve usability, discoverability, intelligence, simplicity, maintainability?
6. **Verification** — No unique capability lost, no hidden dependency broken, no architectural regression, constitutional principles satisfied.

No consolidation decision may proceed until all 6 elements demonstrate the decision is sound.

### Decision Hierarchy

1. ✅ Existing capability — keep as-is
2. 🔧 Existing capability requiring exposure — requires Founder exposure
3. 🔗 Existing capability requiring orchestration — requires evaluation for intelligence pipeline connection
4. 🎨 Existing capability requiring UX refinement — requires experience completion
5. 🔌 Existing capability requiring integration — requires evaluation for workspace runtime connection
6. 🏁 Existing capability requiring completion — requires implementation completion
7. ❌ New implementation — only if options 1-6 are exhausted

---

## 2. Consolidation Decision D1: Canonical Auth

### Evidence

| Dimension | Legacy Auth | Canonical Auth |
|-----------|-------------|----------------|
| **Implementation** | `app/auth_routes.py` — Blueprint `auth_bp` | `app/production/auth/` — 6 route files registered on `auth_bp` (same blueprint name) |
| **Models** | `TeamMember` — integer IDs, stored in `team_members` table | `SHUNYAIdentityModel` — string IDs (sid_xxx), stored in `identity_models` table |
| **Features** | Login, register, logout, basic session | Login, register, MFA, email verification, password reset, session management, device management, authorization middleware |
| **Routes** | `/auth/login`, `/auth/register`, `/auth/logout` | `/api/v1/auth/login`, `/api/v1/auth/register`, `/api/v1/auth/forgot-password`, `/api/v1/auth/reset-password/<token>`, `/api/v1/auth/request-verification`, `/api/v1/auth/verify-email/<token>`, `/api/v1/auth/revoke-sessions`, `/api/v1/auth/devices`, `/api/v1/auth/mfa/*` |
| **Dependencies** | `app.auth_routes` imported by `app/__init__.py` line 345 | `app.production.auth` imported by `app/__init__.py` line 349 (models only; routes registered via `__init__.py` imports) |
| **Tests** | No dedicated test file | `tests/production/identity/test_user_routes.py`, `tests/production/identity/test_org_routes.py` |
| **Consumers (who imports it)** | `app/__init__.py` registers `auth_bp` at line 355 | `app/production/auth/__init__.py` registers routes on same `auth_bp` at line 348; auth middleware at line 352 |
| **Runtime behaviour** | Both registered on same `auth_bp` blueprint — they share route namespace | Canonical routes use `/api/v1/auth/` prefix; legacy routes use `/auth/` prefix; they don't conflict |

### Comparison

| Capability | Legacy Auth | Canonical Auth | Winner |
|-----------|-------------|----------------|--------|
| Password login | ✓ | ✓ | Both |
| Password registration | ✓ | ✓ | Both |
| Password reset | ✗ | ✓ | Canonical |
| Email verification | ✗ | ✓ | Canonical |
| Multi-factor auth | ✗ | ✓ | Canonical |
| Session management | ✗ | ✓ | Canonical |
| Device management | ✗ | ✓ | Canonical |
| Authorization middleware | Basic role check | Full middleware | Canonical |
| Template-based UI | `templates/login.html`, `templates/shunya_login.html` | No template (API-only) | Legacy (has UI) |

**Conclusion:** Canonical auth has every capability of legacy auth plus MFA, email verification, password reset, session management, device management. The ONE thing legacy auth has that canonical lacks is a template-based UI (`templates/login.html`). The canonical auth only has API endpoints.

### Risk

| What breaks if removed? | Likelihood | Mitigation |
|------------------------|-----------|------------|
| Legacy login pages (Jinja2 templates) 404 | High if routes removed | Keep routes as redirects to SPA login |
| `TeamMember` model consumers break | Medium | `TeamMember` model is used by 15+ routes in `app/routes.py` for permission checks. Cannot remove until those routes are migrated. |
| Integer ID-based session lookups | High | Auth middleware at `app/__init__.py` line 425+ checks both integer and string user IDs. Requires both systems to coexist during migration. |

**Migration strategy:** 
1. Keep both auth systems running in parallel
2. Wire SPA login page to canonical auth API
3. Change legacy routes to redirect to SPA
4. Migrate `TeamMember` permission checks to canonical identity model
5. Only after no consumer depends on legacy auth, remove legacy routes

**Rollback strategy:** Keep legacy auth code intact but redirect routes. Rolling back = remove redirects, restore legacy routes.

### Canonical Justification

Canonical auth (`app/production/auth/`) should be the single auth system because:
- It has every capability of legacy auth plus MFA, email verification, password reset, session management
- It uses the canonical OS identity (string IDs) instead of legacy integer IDs
- It has proper authorization middleware
- It integrates with the OS identity engine in `core/identity/`

Legacy auth (`app/auth_routes.py`) should NOT be canonical because:
- Lacks MFA, email verification, password reset, session management
- Uses deprecated integer ID model
- No authorization middleware
- No integration with OS identity engine

### Founder Impact

| Dimension | Improvement |
|-----------|-------------|
| **Usability** | Password reset, email verification work — Founder can recover account |
| **Discoverability** | No change — auth flows are triggered by need |
| **Intelligence** | No direct change — auth is infrastructure |
| **Simplicity** | One auth system instead of two parallel systems |
| **Maintainability** | All auth logic in one place with proper middleware |

### Verification

- [ ] SPA login page calls canonical auth API successfully
- [ ] Password reset flow works end-to-end
- [ ] Email verification flow works end-to-end
- [ ] Legacy route redirects work (no 404 from bookmark)
- [ ] All existing routes that check `TeamMember` permissions continue to work
- [ ] No test regression

---

## 3. Consolidation Decision D2: Sub-Project Capabilities

### Evidence

**None of the 5 sub-projects are imported or registered by the main app.** They are independent Flask applications. They share the same requirements.txt structure and similar templates but have distinct backend capabilities.

| Sub-project | Unique Capabilities Not in Main App | Overlap with Main App |
|------------|--------------------------------------|----------------------|
| `shunya_os_crm/` | CRM entities (orgs, contacts, customers, suppliers, partners, hotels, transports), quotation engine (CRUD, revisions, line items, taxes, discounts, attachments, PDF generation), customer timeline, search providers (quotation, CRM, leads, knowledge) | Templates, auth pattern, basic routes |
| `shunya_os_dashboard/` | Executive widgets, KPI engine, insight providers, brief engine, dashboard layout, layout refresh | `app/executive/` overlaps with executive widgets |
| `shunya_os_documents/` | Document pipeline, document readers (DOCX, PDF, XLSX, CSV, OCR), knowledge graph engine, search index, metadata extraction | `app/document_reader.py` overlaps with document reading |
| `shunya_os_gmail/` | Gmail sync engine, Gmail watch, event bus | `app/adapters/gmail/` overlaps with Gmail integration |
| `shunya_os_workflow/` | Workflow engine (plugins, contracts, triggers, scheduler, retry, conditions, event bus, registry, actions) | No overlap — main app has no workflow engine |

**Key finding:** The sub-projects are NOT duplicates. They are independent implementations of capabilities that were built as separate apps rather than integrated into the canonical OS. The consolidation action is integration, not archival.

**However:** Each sub-project has a full copy of the main app's template set (~37 templates), which IS a duplicate. These template copies are not used by the main app.

### Comparison

| Capability Category | Main App | CRM Sub-project | Documents Sub-project | Dashboard Sub-project | Gmail Sub-project | Workflow Sub-project |
|-------------------|----------|-----------------|----------------------|----------------------|-------------------|---------------------|
| CRM / Quotations | No quotation engine | Full quotation engine | No | No | No | No |
| Document reading | Single `document_reader.py` | No | 6 reader types + pipeline | No | No | No |
| Knowledge graph | No | No | Yes (engine + traversal + query) | No | No | No |
| Executive widgets | `app/executive/engine.py` | No | No | `executive/widgets.py` + KPI + brief | No | No |
| Gmail sync | `app/adapters/gmail/` | No | No | No | `communication/gmail_sync.py` + watch | No |
| Workflow engine | No | No | No | No | No | Full engine (9 files) |
| Search index | `core/search/` | Custom search providers | `search_index/` | No | No | No |

### Risk

| Action | What breaks? | Mitigation |
|--------|-------------|------------|
| Move sub-project code to main app | Sub-project tests may reference `app` differently | Copy files, update imports, run both test suites |
| Archive sub-project template duplicates | Nothing — they're not served by the main app | Verify no route references them |
| Leave sub-projects as-is | Capabilities remain hidden from Founder (status quo) | Accept the status quo |

### Canonical Justification

No sub-project should be "archived" — they contain unique capabilities. Instead, each unique capability requires evaluation for integration into the canonical OS:

1. **CRM quotation engine** — Requires evaluation for integration into `app/` as it is the most complete business capability outside the main app. It has PDF generation, revision management, line items, taxes, discounts — all missing from the main app.
2. **Document pipeline** — Requires evaluation for partial integration (the main app already has `app/document_reader.py` and `app/artifact/`; readers and knowledge graph require evaluation for consolidation).
3. **Executive widgets** — Overlaps with `app/executive/`. Requires capability-by-capability comparison before consolidation.
4. **Gmail sync** — Overlaps with `app/adapters/gmail/`. Requires capability-by-capability comparison.
5. **Workflow engine** — Entirely unique. Requires evaluation for integration into `core/automation_runtime/` or `app/automation/`.

### Founder Impact

| Dimension | Improvement |
|-----------|-------------|
| **Usability** | Quotation generation, document processing, workflows become available to Founder |
| **Discoverability** | Capabilities move from hidden sub-projects to the canonical workspace |
| **Intelligence** | Knowledge graph and search index enhance AI capabilities |
| **Simplicity** | One codebase instead of 5 independent apps |
| **Maintainability** | Single test suite, single dependency set, single deployment |

### Verification

- [ ] Every unique capability from sub-projects is verified to exist in the canonical OS after integration
- [ ] No capability is lost during the move
- [ ] Sub-project test suites continue to pass during migration
- [ ] Main app test suite continues to pass
- [ ] No duplicate capability is created in the main app

---

## 4. Canonical Selection: Search

### Evidence

| Dimension | Universal Search (Frontend) | Space Search (Backend) | Core Search (Backend) |
|-----------|---------------------------|----------------------|----------------------|
| **Implementation** | `frontend/src/components/search/universal-search.tsx` | `app/space/routes.py` — `/api/v1/space/search` | `core/search/` |
| **Type** | Client-side substring filter | Server-side space search | General search engine |
| **Scope** | Pre-loaded object index | Space names, identities, metadata | All indexed objects |
| **Dependencies** | Static pre-loaded data | `app/space/store.py` | `core/search/` is standalone |

### Comparison

| Capability | Universal Search (FE) | Space Search (API) | Core Search |
|-----------|----------------------|-------------------|-------------|
| Search spaces | ✓ (client-side filter) | ✓ | ? |
| Search objects | ✓ (client-side filter) | ✗ (spaces only) | ? |
| Full-text search | ✗ | ✗ | ? (need to inspect) |
| Fuzzy search | ✗ | ✗ | ? |
| Ranking | ✗ | ✗ | ? |
| AI-powered | ✗ | ✗ | ? |

### Canonical Justification

The search consolidation needs further investigation — I haven't inspected `core/search/` to understand its capabilities. **Deferred until core search is inspected.**

---

## 5. Exposure Decisions (No Consolidation — Evaluation Required)

The following capabilities need NO consolidation — they are the sole implementation and require evaluation for Founder exposure:

### E1: Space Runtime (16 capabilities, all hidden)

All 16 space capabilities exist only in backend (`app/space/`). No consolidation needed — they are the canonical implementation. Evaluation required:
- Frontend components that consume `/api/v1/space/` endpoints
- AI copilot integration with `AIResidentState` per space
- Navigation surface (breadcrumb, tree, siblings)

### E2: Core Intelligence (8 engines, all hidden)

All 8 intelligence engines exist only in `core/intelligence/`. No consolidation needed. Evaluation required:
- Pipeline connection from `ShunyaOS.process_intent()`
- AI copilot that invokes perception, reasoning, planning, decision, learning, reflection, context_assembly, confidence
- Workspace components that display reasoning traces, confidence scores, anomalies

### E3: Workspace Runtime (10 capabilities, all hidden)

The workspace runtime at `core/workspace_runtime/` has orchestrator, panels, tabs, docking, session restore. No consolidation needed. Evaluation required:
- Frontend that consumes `/api/workspace/` endpoints
- Consistent workspace state management

### E4: Organization Identity System (6 capabilities, all hidden)

Org CRUD, workspace CRUD, user management, invitations, lifecycle, onboarding — all at `app/production/identity/`. No consolidation needed. Evaluation required:
- UI for org creation
- UI for workspace management
- UI for user/invitation management

### E5: Enterprise Module (4 capabilities, all hidden)

Enterprise audit, roles, team, permissions — all at `app/enterprise/`. No consolidation needed. Evaluation required:
- Workspace settings UI
- Role/permission management surface

---

## 6. Identified Gaps (No Sequencing Implied)

The following capabilities require completion. The governance review identifies these gaps; it does not prescribe their execution order. Sequencing is a matter for implementation planning.

| Gap | What Exists | What Requires Completion |
|-----|------------|-------------------------|
| **Space Runtime exposure** | 16 backend API routes at `app/space/` | Founder-facing surface that consumes `/api/v1/space/` endpoints |
| **Intelligence engine exposure** | 8 core engines at `core/intelligence/` | Pipeline connection to `ShunyaOS.process_intent()` and AI copilot |
| **Workspace API exposure** | Backend API at `/api/workspace/` | Frontend that consumes all workspace endpoints |
| **Organization identity exposure** | Backend API at `app/production/identity/` | UI for org, workspace, user, and invitation management |
| **Enterprise module exposure** | Backend API at `app/enterprise/` | Workspace settings and role/permission management UI |
| **Sub-project capability evaluation** | 5 sub-projects with unique capabilities | Evaluation of each for integration path |
| **Legacy navigation migration** | Jinja2 template routes at `app/routes.py` | Evaluation of migration path to canonical SPA |
| **Legacy auth deprecation** | `TeamMember` model consumed by 15+ routes | Evaluation of deprecation path after all dependencies migrated |

---

## 7. What This Plan Does NOT Do

This plan does NOT:
- Archive any sub-project (they have unique capabilities)
- Deprecate legacy auth (cannot while `TeamMember` is consumed by 15+ routes)
- Remove any code (all changes require evaluation for additive exposure)
- Require backend implementation changes (all changes require evaluation for API connection, not rewrite)

---

## 8. Verification Gate

Before any implementation proceeds:

- [x] **Phase 0 audit complete** — 62 capabilities inventoried with evidence paths
- [x] **Sub-project analysis corrected** — 5 sub-projects have unique capabilities, not duplicates
- [x] **Auth analysis corrected** — legacy auth cannot be removed yet; parallel coexistence required
- [x] **Search analysis deferred** — `core/search/` needs inspection before consolidation decision
- [x] **Every claim in this plan has evidence** — file paths, route names, comparison tables
- [ ] **Awaiting Founder approval** before any implementation begins