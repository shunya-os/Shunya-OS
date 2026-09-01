# SHUNYA OS — G1 MISSING CAPABILITY REGISTER

**Every gap classified by type, with dependency and severity.**

---

## LEGEND

| Classification | Meaning |
|---------------|---------|
| 🔴 FOUNDATION BLOCKER | Blocks the entire architecture — must be fixed in G1 |
| 🟠 INTEGRATION BLOCKER | Blocks a major domain integration |
| 🟡 USER-WORKFLOW BLOCKER | Blocks a real user workflow |
| 🔵 UX BLOCKER | Blocks a complete user experience |
| 🟢 PRODUCT-PROMISE BLOCKER | Blocks a stated product promise |
| ⚪ MAINTENANCE | Cleanup, no user impact |
| 🔵 PROVIDER DEPENDENCY | Blocked by external provider |
| ⚫ OUT OF SCOPE | Not in scope for current product |

---

## FOUNDATION BLOCKERS (🔴)

| # | Gap | Component | Impact | Fix Path |
|---|-----|-----------|--------|----------|
| G1-01 | **Frontend ask() called wrong URL** | `frontend/src/api/client.ts:92` | Frontend AI calls dead endpoint | **FIXED in G1** — `/intelligence/ask` → `/api/v1/intelligence/ask` |
| G1-02 | **Identity convergence (3+ implementations)** | `app/auth.py`, `app/models.py`, `app/production/identity_repository.py` | Multiple auth authorities, risk of divergence | Merge into one canonical identity path |
| G1-03 | **Object store convergence (6 tables)** | `sh_objects`, `objects`, `founder_objects`, `canonical_objects`, `sh_uop_objects` | Data fragmentation, no single object truth | Migrate all to `sh_objects` + `app/objects/` API |
| G1-04 | **Execution_bp double-registration** | `app/__init__.py:671,844` | Flask startup naming conflict | **FIXED in G1** — renamed second import |
| G1-05 | **No canonical universal search** | `universal-search.tsx` | Search is frontend-only, not backend-backed | Build search API that indexes all canonical objects |

---

## INTEGRATION BLOCKERS (🟠)

| # | Gap | Component | Impact | Fix Path |
|---|-----|-----------|--------|----------|
| G1-06 | **Knowledge: 0 backend API routes** | `app/knowledge/` | Knowledge browser shows empty state | Build knowledge API routes |
| G1-07 | **Memory: 2 minimal API routes** | `app/memory_api/routes.py` | Memory browser shows empty state | Build memory API routes |
| G1-08 | **Finance: 86 backend routes, 0 frontend** | `frontend/src/components/finance/` | Users cannot see invoices, payments, ledger | Build finance workspace component |
| G1-09 | **Operations: entirely missing** | — | Domain label in sidebar, no code | Build operations domain |
| G1-10 | **IntegrationHub: mock localStorage** | `integration-hub.tsx` | Integration settings not persisted | Wire to real backend API |
| G1-11 | **Calendar: UI exists, no API** | `calendar-panel.tsx` | Calendar renders empty | Build calendar API |

---

## USER-WORKFLOW BLOCKERS (🟡)

| # | Gap | Component | Impact | Fix Path |
|---|-----|-----------|--------|----------|
| G1-12 | **Conversations: no real-time sync** | `conversation-workspace.tsx` | Users must refresh to see new messages | Implement SSE/WebSocket |
| G1-13 | **Tasks: read-only, not per-lead** | `tasks-workspace.tsx` | Cannot create tasks contextually | Wire task creation to execution engine |
| G1-14 | **Marketing: dashboard only, no campaigns** | `marketing-dashboard.tsx` | Cannot manage campaigns from UI | Build campaign management UI |
| G1-15 | **Relationships: viewable, not editable** | `relationship-workspace.tsx` | Cannot create/modify relationships | Wire relationship CRUD |
| G1-16 | **Outputs: minimal listing** | `outputs-browser.tsx` | Cannot manage outputs | Build full output lifecycle |
| G1-17 | **Pricing page: unreferenced** | `pricing.tsx` | Page exists but no route to it | Add to routing or remove |
| G1-18 | **Command palette: frontend-only search** | `command-palette.tsx` | Searches only local objects, not backend | Wire to canonical search API |

---

## UX BLOCKERS (🔵)

| # | Gap | Component | Impact | Fix Path |
|---|-----|-----------|--------|----------|
| G1-19 | **Dark mode: no user-facing toggle** | `theme-settings.tsx` | Theme infrastructure exists, no control | Add toggle UI |
| G1-20 | **Mobile responsive: missing** | All | Desktop-only layout | Add responsive CSS |
| G1-21 | **Loading states: incomplete** | Various | Some screens show spinner, some flash | Audit and complete all loading states |
| G1-22 | **Empty states: incomplete** | Various | Some empty screens show blank | Audit and complete all empty states |
| G1-23 | **Error states: incomplete** | Various | Some errors not user-friendly | Audit and complete all error states |

---

## PRODUCT-PROMISE BLOCKERS (🟢)

| # | Gap | Source | Impact | Fix Path |
|---|-----|--------|--------|----------|
| P-01 | WhatsApp Business API | FPV Persona 2 | Primary customer channel missing | Build WhatsApp integration |
| P-02 | Client portal | FPV Persona 2 | Clients cannot see/approve/pay | Build client-facing SPA |
| P-03 | Payment gateway client flow | FPV Persona 2 | Cannot collect money online | Complete Razorpay client flow |
| P-04 | WhatsApp notifications | FPV Persona 1 | No outbound WhatsApp | Build WhatsApp notification channel |
| P-05 | Celebration/victory system | FPV Persona 1 | No emotional engagement | Build auto-detect wins + broadcast |
| P-06 | AI document reading | FPV Persona 2 | Cannot forward WhatsApp→auto-extract | Build document AI pipeline |
| P-07 | Multi-brand onboarding | FPV Persona 1 | Cannot create multiple businesses at signup | Build multi-brand flow |
| P-08 | i18n / Hindi | FPV §2.2 | Cannot use in Hindi despite Hindi voice | Build i18n framework |
| P-09 | AI avatar | FPV §4 | No visual personality | Build avatar component |
| P-10 | Mobile responsive | FPV §4 | Cannot use on phone | Add responsive CSS |

---

## MAINTENANCE (⚪)

| # | Gap | Component | Impact | Fix Path |
|---|-----|-----------|--------|----------|
| M-01 | Supabase auth: requires .env config | `supabase.ts` | Unused code path | Either remove or configure |
| M-02 | m9_team_members: duplicate table | `app/m9_auth/` | Confusing duplicate | Merge into team_members |

---

## PROVIDER DEPENDENCY (🔵)

| # | Gap | Component | Impact | Fix Path |
|---|-----|-----------|--------|----------|
| PD-01 | Gmail OAuth: partial | `app/gmail_oauth/` | Initiate and callback need cleanup | Complete OAuth flow |
| PD-02 | Resend webhook: feature-gated | `app/communication/email_webhook.py` | Returns 501 when not configured | Configure in production |

---

*This register is the single authoritative gap inventory. No gap may be closed without evidence.*