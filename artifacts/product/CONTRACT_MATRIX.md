# SHUNYA CONTRACT MATRIX — §27

Every meaningful user-facing capability, traced from UI entry through to
persistence and AI context. Blank cells are explicit gaps.

Last updated: 2026-09-18

Legend:
✅ = IMPLEMENTED AND VERIFIED
🟡 = IMPLEMENTED, NOT VERIFIED
🔴 = NOT IMPLEMENTED OR BROKEN
⚪ = INTENTIONALLY NOT APPLICABLE (documented why)

---

## 1. AUTHENTICATION & ENTRY

### 1.1 Sign In (email/password)

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| UI entry | Login page at `/auth/login` | ✅ | app.tsx line 355 |
| User action | Enter email + password, click Sign In | ✅ | login-page.tsx |
| Frontend handler | `api.signin(email, password)` → POST /api/v1/founder/signin | ✅ | client.ts:24 |
| API route | `POST /api/v1/founder/signin` | ✅ | app/founder/routes.py |
| Authentication | Password verification via werkzeug check_password_hash | ✅ | |
| Authorization | N/A (public endpoint) | ⚪ | |
| Service | IdentityService.authenticate() | ✅ | |
| Canonical object | Identity record | ✅ | sh_identities table |
| Persistence | sh_identities + sessions | ✅ | |
| Evidence | Session cookie set | ✅ | |
| Event | signin event emitted | 🔴 | No event bus notification |
| AI context | Identity available | ✅ | SessionManager, whoami |
| Execution | Redirect to workspace or onboarding | ✅ | |
| Outcome | Phase transitions to 'ready' or 'onboarding' | ✅ | |
| Observation | User sees workspace or onboarding | ✅ | |
| Attention | N/A | ⚪ | |
| Success | HTTP 200 + name/identity_id/redirect | ✅ | |
| Failure | HTTP 401 with error message | ✅ | |
| Recovery | Try again | ✅ | |
| Refresh continuity | Session cookie persists; auto-restore by fetch /api/v1/auth/session | ✅ | app.tsx:299-321 |
| Restart continuity | Session cookie survives service restart | ✅ | Tested by systemctl restart |
| Responsive behavior | Login page is responsive | 🟡 | Not tested on mobile |
| Accessibility | Touch targets ≥44px | ✅ | Verified on production |
| Tests | Integration tests exist | ✅ | test_r6b27_* |

### 1.2 OAuth Sign In (Google, GitHub)

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| UI entry | OAuth buttons on login page | ✅ | |
| User action | Click Google/GitHub button | ✅ | |
| Frontend handler | OAuth redirect flow | 🟡 | Not fully verified |
| API route | OAuth callback endpoints | ✅ | |
| Authentication | OAuth token verification | ✅ | |
| Service | OAuth service | ✅ | |
| Canonical object | Identity + external auth link | ✅ | |
| Persistence | sh_identities + external_auth table | ✅ | |
| Evidence | Session created post-OAuth | ✅ | |
| Tests | touch targets verified | ✅ | b80e811 |

### 1.3 Sign Up

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| UI entry | Signup page at `/auth/signup` | ✅ | |
| API route | POST /api/v1/auth/signup | ✅ | |
| Authentication | Password hashing | ✅ | |
| Persistence | New Identity created | ✅ | |
| Post-signup | Creates default org | 🔴 | Unverified path |
| Event | signup event | 🔴 | |

### 1.4 Invitation Journey

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| UI entry | Invitation page at `/auth/invitation?token=X` | ✅ | app.tsx:408 |
| API route | GET /api/v1/orgs/invitations/<token> | ✅ | F-05 fix verified |
| API route | POST /api/v1/orgs/invitations/<token>/accept | ✅ | |
| Persistence | Invitation + membership created | ✅ | |
| Full journey | Invited user → accept → workspace | 🟡 | Not fully tested as end-to-end journey |

---

## 2. ONBOARDING

### 2.1 Onboarding Flow

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| UI entry | Phase transitions to 'onboarding' | ✅ | |
| URL truth | URL says /onboarding, not /auth/login | ✅ | B-3 fixed this session |
| Direct navigation | GET /onboarding restores onboarding | ✅ | B-3 fixed |
| Refresh | Page refresh during onboarding resumes correctly | ✅ | Session + URL restore |
| Back/forward | Browser navigation works | 🟡 | popstate not fully tested |
| Authenticated revisit | Authenticated user cannot fall back to login | ✅ | post-auth.ts |

### 2.2 Onboarding Steps

| Step | UI | Backend | Persistence | Status |
|------|----|---------|-------------|--------|
| Welcome | step-welcome.tsx | None | None | ✅ |
| Purpose | step-purpose.tsx | None | localStorage | 🟡 B-2 unconfirmed |
| First object | step-first-object.tsx | auto-create | sh_objects | 🔴 Orphaned step |
| Import | step-import.tsx | /api/v1/upload | sh_objects | 🔴 Orphaned step |
| Auto objects | step-auto-objects.tsx | auto-create | sh_objects | 🔴 Orphaned step |
| AI intro | step-ai-intro.tsx | None | None | 🔴 Orphaned step |
| Identity | step-identity.tsx | None | None | 🔴 Orphaned step |
| Organization | step-organization.tsx | None | None | 🔴 Orphaned step |
| Team | step-team.tsx | None | None | 🔴 Orphaned step |
| Complete | step-complete.tsx | None | localStorage | ✅ |

---

## 3. AUTHENTICATED WORKSPACE (Home)

### 3.1 Navigation Rail

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| UI entry | Left sidebar (280px) | ✅ | executive-home.tsx |
| Domain navigation | Organization rail with People, Conversations, Documents, etc. | ✅ | |
| Icon style | Emoji-as-icons | 🔴 | B-4 in progress |
| Domain switching | Click → workspace routing | ✅ | |
| Active state | Current domain highlighted | ✅ | |

### 3.2 Object CRUD

| CREATE | | | | |
|--------|---|---|---|
| UI entry | Home page + object routes | ✅ | |
| API | POST /api/v1/objects | ✅ | |
| Auth | Tenant + workspace enforced | ✅ | |
| Service | ObjectService.create() | ✅ | |
| Canonical object | sh_objects | ✅ | |
| Persistence | sh_objects table | ✅ | |
| Event | ObjectCreated event | ✅ | |

| READ | | | | |
|------|---|---|---|
| API | GET /api/v1/objects/<type> | ✅ | Fixed F-02 |
| API | GET /api/v1/objects/types | ✅ | Fixed F-01 |
| API | GET /api/v1/objects?limit=&q= | ✅ | Fixed F-03 |
| Auth | Tenant + workspace scoped | ✅ | ObjectService.list_authorized() |

| UPDATE | | | | |
|------|---|---|---|
| API | PUT /api/v1/objects/<id> | ✅ | |
| Auth | Object owner + workspace | ✅ | |

| DELETE / ARCHIVE | | | | |
|---|---|---|---|---|
| API | DELETE /api/v1/objects/<id> | ✅ | |
| Soft delete | objects.deleted_at set | 🔴 | Not verified for all paths |
| Archive | Archive state | 🔴 | Not implemented for all domains |

---

## 4. CUSTOMER / CRM

| Capability | Status | Notes |
|-----------|--------|-------|
| CREATE | 🔴 | CRM leads in own table, not sh_objects |
| VIEW | 🟡 | CRM routes exist |
| EDIT | 🔴 | |
| RELATE | 🔴 | No canonical relationship to other objects |
| ARCHIVE | 🔴 | |
| PERSISTENCE | 🟡 | Legacy `leads` table, not canonical |
| CANONICAL OBJECT | 🔴 | Not converged to ObjectService |
| CANONICAL STATE | 🔴 | Each lead is not a sh_object |
| AI CONTEXT | 🔴 | Not visible to AI |
| EVENT | 🔴 | |
| ATTENTION | 🔴 | |
| REFRESH | 🟡 | |
| RESTART | 🟡 | |

---

## 5. COMMITMENTS

| Capability | Status | Notes |
|-----------|--------|-------|
| CREATE | 🟡 | Own table |
| VIEW | 🟡 | |
| EDIT | 🟡 | |
| RELATE | 🔴 | |
| ARCHIVE | 🔴 | |
| OVERDUE | 🟡 | Warning shown in UI |
| CANONICAL OBJECT | 🔴 | Not converged |
| AI CONTEXT | 🔴 | |
| EVENT | 🔴 | |
| ATTENTION | 🔴 | Could power attention items |

---

## 6. DOCUMENTS / KNOWLEDGE

| Capability | Status | Notes |
|-----------|--------|-------|
| UPLOAD | 🟡 | /api/v1/upload exists |
| VIEW | 🟡 | Document browser UI exists |
| SEMANTIC CLASSIFICATION | 🔴 | No document intelligence |
| HIERARCHICAL ORGANIZATION | 🔴 | |
| PROVENANCE | 🔴 | |
| AI RETRIEVAL | 🔴 | |
| CANONICAL OBJECT | 🔴 | Own table |
| RELATIONSHIPS | 🔴 | |

---

## 7. CONTENT GENERATION

| Capability | Status | Notes |
|-----------|--------|-------|
| CREATE | 🟡 | ContentStudio exists |
| VIEW | 🟡 | |
| EDIT | 🟡 | |
| ARCHIVE | 🟡 | |
| TRASH / SOFT DELETE | 🟡 | |
| PERMANENT DELETE | 🟡 | |
| REGENERATE | 🟡 | |
| CANONICAL OBJECT | 🔴 | ContentGeneration table, not sh_objects |
| GENERATION METADATA | 🟡 | Provider, prompt saved |
| AI CONTEXT | 🔴 | |

---

## 8. AI / INTELLIGENCE

### 8.1 Ask SHUNYA

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| UI entry | Resident AI panel with input | ✅ | |
| API | POST /api/v1/intelligence/ask | ✅ | Fixed F-04, F-06 |
| Provider fallback | 3-tier (primary → secondary → local) | ✅ | |
| Internet retrieval | DuckDuckGo integration | ✅ | |
| Evidence logging | Per-turn evidence | ✅ | |
| Company context | Single-object only | 🔴 | §7 requires aggregate context |
| Company-first | Internet fallback, not primary | 🔴 | No explicit company-first ordering |
| Provenance | Source separation | 🟡 | Partial |
| Auth | 401 on unauthenticated | ✅ | |
| Failure handling | Provider failure → fallback | ✅ | |
| Authenticated proof | Real user → correct org → correct context → AI path | 🔴 | Explicitly called out as unverified |

### 8.2 AI Execution / Action

| Capability | Status | Notes |
|-----------|--------|-------|
| INTENT RECOGNITION | 🟡 | |
| AUTHORITY CHECK | 🔴 | No explicit authority gate |
| CONFIRMATION | 🔴 | No confirmation step |
| EXECUTION | 🟡 | Task lifecycle exists |
| PERSISTENCE | 🟡 | |
| OUTCOME REPORTING | 🔴 | AI must not claim action that didn't happen |
| FAILURE REPORTING | 🔴 | "say so" requirement |

---

## 9. ATTENTION (M9 — NOT STARTED)

| Capability | Status | Notes |
|-----------|--------|-------|
| CHANGES | 🔴 | |
| ANOMALIES | 🔴 | |
| UNRESOLVED ITEMS | 🔴 | |
| OVERDUE | 🔴 | |
| OPPORTUNITIES | 🔴 | |
| RISKS | 🔴 | |
| DISMISS | 🔴 | |
| PERSISTENCE | 🔴 | |
| AUDITABILITY | 🔴 | |

---

## 10. REALTIME / PRESENCE (M10)

| Capability | Status | Notes |
|-----------|--------|-------|
| Heartbeat | ✅ | Every 10s SSE |
| Presence mode | ✅ | Derived from real signals |
| SSE stream | ✅ | /api/v1/reality/stream / /api/v1/events/stream |
| EventBus to browser | 🔴 | Bus events never reach UI |
| 5s poll only | 🟡 | Current mechanism — EventBus bridge missing |

---

## 11. FAILURE / RECOVERY (M11 — NOT STARTED)

| Failure mode | Tested? | Recovery |
|-------------|---------|----------|
| Network failure | 🔴 | |
| API failure 5xx | 🔴 | |
| 401 | ✅ | Redirects to login |
| 403 | 🔴 | |
| AI provider failure | 🟡 | 3-tier fallback |
| Upload failure | 🔴 | |
| Partial ingestion | 🔴 | |
| Real-time disconnect | 🔴 | |
| Service restart | ✅ | Restart survival verified |
| Browser refresh | ✅ | Session preserved |
| Database failure | 🔴 | |

---

## 12. EMOTIONAL / HUMAN CONTEXT (NOT STARTED)

| Capability | Status | Notes |
|-----------|--------|-------|
| Feeling signal model | 🔴 | |
| Explicit statement capture | 🔴 | |
| Temporal expiration | 🔴 | |
| User correction | 🔴 | |
| Behaviour change | 🔴 | |
| EGJ-01…EGJ-10 | 🔴 | |
| Privacy/auth | 🔴 | |

---

## 13. SECURITY

| Layer | Detail | Status | Evidence |
|-------|--------|--------|----------|
| Wrong org access | Must be blocked | 🟡 | Logic tested, DB isolation not |
| Wrong workspace | Must be blocked | 🟡 | |
| Wrong object | Must be blocked | 🟡 | |
| Direct API bypass | Must be blocked | 🟡 | |
| Inactive membership | Must be blocked | 🔴 | |
| Exposed credential | DB password in logs | 🔴 | Removed from log output, rotation pending |

---

## 14. VISUAL / DEVICE / ACCESSIBILITY (M12 — NOT STARTED)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Desktop | 🟡 | Not formally certified |
| Laptop | 🟡 | |
| Tablet | 🔴 | |
| Mobile | 🔴 | |
| Narrow viewport | 🔴 | |
| Touch targets ≥44px | ✅ | Public + auth verified |
| Keyboard tab order | 🔴 | |
| Focus visibility | 🔴 | |
| Screen reader | 🔴 | |
| Reduced motion | 🟡 | data-reduced-motion attribute set |
| Contrast | 🟡 | CTA verified 17.1:1 |

---

## 15. GOLDEN JOURNEYS

| Journey | Status | Evidence |
|---------|--------|----------|
| GJ-01 Entry → Workspace | 🟡 | 1 journey harness exists, not wired into CI |
| GJ-02 Create business object | 🔴 | |
| GJ-03 Import structured data | 🔴 | |
| GJ-04 Upload document | 🔴 | |
| GJ-05 AI document understanding | 🔴 | |
| GJ-06 Customer/contact | 🔴 | |
| GJ-07 Supplier | 🔴 | |
| GJ-08 Business engagement | 🔴 | |
| GJ-09 Content creation | 🔴 | |
| GJ-10 Content archive/trash/restore | 🔴 | |
| GJ-11 Ask SHUNYA (company context) | 🔴 | |
| GJ-12 Ask SHUNYA (internet) | 🔴 | |
| GJ-13 AI proposes/executes action | 🔴 | |
| GJ-14 Observe state/attention | 🔴 | |
| GJ-15 Failure/recovery | 🔴 | |
| GJ-16 Refresh/restart/continue | 🔴 | |
| EGJ-01…EGJ-10 | 🔴 | |

---

## 16. CANONICAL OBJECT CONVERGENCE

| Domain | Current home | Converged? | Blockers |
|--------|-------------|-----------|----------|
| Generic objects | sh_objects (ObjectService) | ✅ | |
| CRM leads | leads table | 🔴 | Own routes, own table |
| Commitments | commitments table | 🔴 | |
| Observations | observations table | 🔴 | |
| Documents/knowledge | documents_knowledge table | 🔴 | |
| Content generation | ContentGeneration table | 🔴 | |
| Tasks | TaskLifecycle table | 🔴 | |
| UOP objects | sh_uop_objects table | 🔴 | |
| Legacy Object | objects table (no tenant) | 🔴 | |
