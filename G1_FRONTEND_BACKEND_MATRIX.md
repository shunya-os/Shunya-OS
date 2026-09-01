# SHUNYA OS — G1 FRONTEND ↔ BACKEND CAPABILITY MATRIX

**Every route, surface, and action in SHUNYA with its backend contract.**

---

## LEGEND

| Status | Meaning |
|--------|---------|
| ✅ | Fully built and connected |
| ⚠️ | Partially built or partially connected |
| ❌ | Not built or not connected |
| — | Not applicable |

---

## 1. AUTH & IDENTITY

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Login | `login-page.tsx` | `/api/v1/auth/signin` | POST | ✅ | Email/password auth |
| Signup | `signup.tsx` | `/api/v1/auth/signup` | POST | ✅ | Registration |
| Forgot Password | `forgot-password.tsx` | `/api/v1/auth/forgot-password` | POST | ✅ | Reset flow |
| Reset Password | `reset-password.tsx` | `/api/v1/auth/reset-password` | POST | ✅ | Token-based |
| Verify Email | `verify-email.tsx` | `/api/v1/auth/verify-email` | POST | ✅ | Email verification |
| Invitation Accept | `invitation-accept.tsx` | `/api/v1/auth/invitation/:token` | GET | ✅ | Org invitation |
| Invitation Accept | `invitation-accept.tsx` | `/api/v1/auth/accept-invitation` | POST | ✅ | Accept with name/password |
| MFA Setup | `mfa-setup.tsx` | `/api/v1/auth/mfa/*` | POST | ✅ | MFA configuration |
| Session Restore | `app.tsx` | `/api/v1/auth/session` | GET | ✅ | Cookie-based session bridge |
| Logout | `app.tsx` | `/api/v1/auth/logout` | POST | ✅ | Session destroy |
| Auth Middleware | `app.tsx` | — | — | ✅ | Route protection |

---

## 2. WORKSPACE & NAVIGATION

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Workspace Shell | `workspace-shell.tsx` | — | — | ✅ | Three-zone layout |
| Workspace Bar | `workspace-bar.tsx` | — | — | ✅ | Tab navigation |
| Workspace Switcher | `workspace-switcher.tsx` | `/api/v1/workspace/switch` | POST | ✅ | Org switching |
| Context Selector | `context-selector.tsx` | `/api/v1/workspace/context` | GET | ✅ | Active context |
| Command Palette | `command-palette.tsx` | `/api/v1/founder/objects` | GET | ⚠️ | Frontend-only index, not backend-backed search |
| Universal Search | `universal-search.tsx` | `/api/v1/search` | POST | ⚠️ | Searches web, not internal objects |
| Onboarding Flow | `onboarding-flow.tsx` (10 steps) | `/api/v1/founder/*`, `/api/v1/orgs` | POST | ✅ | Full 10-step flow |
| Import/Export | `import-export-panel.tsx` | `/api/v1/import-export/*` | GET/POST | ✅ | Data portability |

---

## 3. DOMAIN WORKSPACES

| Domain | Frontend Component | Backend API | Routes | Status | Notes |
|---|---|---|---|---|---|
| **People** | `people-persons-panel.tsx` | `/api/v1/people` | 15 | ✅ | Members, persons, attendance, approvals |
| **Conversations** | `conversation-workspace.tsx` | `/api/v1/communication` | 11 | ✅ | Messages, proposals, real-time sync MISSING |
| **Work** | `execution-workspace.tsx`, `tasks-workspace.tsx` | `/api/v1/execution`, `/api/v1/tasks` | 8 | ⚠️ | Tasks read-only, execution visible |
| **Finance** | ❌ No component | `/api/v1/finance` | 86 | ❌ | **86 backend routes with no UI** |
| **Commercial** | `commercial-workspace.tsx` | `/api/v1/commercial` | 17 | ✅ | Deals, opportunities, proposals |
| **Marketing** | `marketing-dashboard.tsx`, `marketing-workspace.tsx` | `/api/v1/marketing`, `/api/v1/marketing-os` | 15 | ⚠️ | Dashboard only, campaigns partial |
| **Sales** | `sales-pipeline.tsx`, `lead-management.tsx` | `/api/v1/crm` | 59 | ✅ | Pipeline, leads, opportunities, proposals |
| **Operations** | ❌ No component | ❌ No API | 0 | ❌ | **Domain entirely missing** |
| **Knowledge** | `knowledge-browser-panel.tsx` | ❌ No API | 0 | ❌ | **Frontend exists, backend empty** |
| **Outputs** | `outputs-browser.tsx` | `/api/v1/execution-visibility` | 4 | ⚠️ | Minimal output listing |
| **Memory** | `memory-browser.tsx` | `/api/v1/memory` | 2 | ❌ | **Frontend exists, 2 minimal API routes** |
| **Relationships** | `relationship-workspace.tsx` | `/api/v1/relationship` | 5 | ⚠️ | Relationships viewable, not editable |
| **Content** | `content-studio.tsx`, `media-generator.tsx` | `/api/v1/content-studio` | 18 | ✅ | Full content generation suite |
| **Entities** | `entity-manager.tsx` | `/api/v1/objects` | 7 | ✅ | Object CRUD |
| **Documents** | `document-browser.tsx` | `/api/v1/documents` | 6 | ✅ | Document browser |

---

## 4. AI & INTELLIGENCE

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| AI Ask | `client.ts` | `/api/v1/intelligence/ask` | POST | ⚠️ | **Was calling wrong URL — FIXED in G1** |
| AI Insights | `ai-insights.tsx` | `/api/v1/intelligence/ask` | POST | ✅ | Proactive business insights |
| AI File Assistant | `file-assistant.tsx` | `/api/v1/intelligence/ask` | POST | ✅ | Document Q&A |
| Command Palette AI | `command-palette.tsx` | `/api/v1/intelligence/ask` | POST | ⚠️ | Frontend-only currently |
| AI Copilot Panel | `copilot-panel.tsx` | `/api/v1/intelligence/ask` | POST | ✅ | Context-aware sidebar |
| AI Resident Panel | `ai-resident-panel.tsx` | `/api/v1/intelligence/ask` | POST | ✅ | Persistent AI presence |
| AI Presence | `ai-presence-panel.tsx` | `/api/v1/intelligence/ask` | POST | ✅ | Awareness indicators |

---

## 5. SETTINGS & ADMIN

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Settings Panel | `settings-panel.tsx` | `/api/v1/authz` | GET/POST | ✅ | 7 tabs, all functional |
| Theme Settings | `theme-settings.tsx` | `/api/v1/authz/preferences` | PUT | ✅ | Light/dark theme toggle |
| Integration Hub | `integration-hub.tsx` | `/api/v1/integration` | GET/POST | ⚠️ | Mock localStorage, not real API |
| Webhook Config | `webhook-config.tsx` | `/api/v1/integration` | PUT | ✅ | Webhook key management |
| Admin Panel | `admin-panel.tsx` | `/api/v1/admin` | GET/POST | ✅ | Role and permission management |

---

## 6. NOTIFICATIONS

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Notification Bell | `notification-bell.tsx` | `/api/v1/notifications/unread-count` | GET | ✅ | Unread count badge |
| Notification History | `notification-history.tsx` | `/api/v1/notifications` | GET | ✅ | Full notification list |
| Notification Toast | `notification-toast.tsx` | — | — | ✅ | Real-time toast via SSE |
| Push Subscription | `main.tsx` | `/api/v1/notifications/subscribe` | POST | ✅ | PWA push notifications |

---

## 7. PROPOSALS

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Proposal List | `ProposalList.tsx` | `/api/v1/proposals` | GET | ✅ | Lists all proposals |
| Proposal Detail | `ProposalDetail.tsx` | `/api/v1/proposals/:id` | GET | ✅ | Full proposal view |
| Proposal Edit | `ProposalEdit.tsx` | `/api/v1/proposals/:id` | PUT | ✅ | Edit and customize |

---

## 8. VOICE & MEDIA

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Voice Input | `executive-home.tsx` (VoiceInput) | Browser Speech API | — | ✅ | Speech→text |
| TTS Output | `executive-home.tsx` (speakText) | Browser SpeechSynthesis | — | ✅ | Text→speech |
| Media Generator | `media-generator.tsx` | `/api/v1/media` | POST | ✅ | AI image generation |
| PDF Preview | `pdf-preview.tsx` | `/api/v1/pdf/generate` | POST | ✅ | PDF generation |

---

## 9. AUDIT & COMPLIANCE

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Audit Viewer | `audit-viewer.tsx` | `/api/v1/audit` | GET | ✅ | Audit trail |
| Audit Reconstruction | `audit-reconstruction.tsx` | `/api/v1/audit/reconstruct` | POST | ✅ | State reconstruction |

---

## 10. PUBLIC & MARKETING

| Frontend Surface | Frontend Component | Backend API | Method | Status | Notes |
|---|---|---|---|---|---|
| Homepage | `homepage.tsx` | — | — | ✅ | Cinematic landing |
| Pricing | `pricing.tsx` | — | — | ⚠️ | Exists but unreferenced in routing |

---

*This matrix is the single authoritative frontend↔backend contract. Every gap is actionable. Every missing connection is a bug.*
