# Legacy Workspace Capability Audit — MX-01 Phase 1 Migration Impact

> **Date:** 2026-08-05  
> **Scope:** `/home/shunya-deploy/shunya_os` — Frontend + Backend  
> **Purpose:** Complete inventory of legacy workspace capabilities, routes, components, and APIs

---

## 1. UNIFIED OS HOMEPAGE — Space Registry & Mode Configuration

**File:** `frontend/src/components/public/homepage.tsx`

### 1.1 Modes (3 operational modes)
| Mode | Icon | ID | Spaces Included |
|------|------|----|-----------------|
| `Work` | 💼 | `work` | liveblock-io, business, proposals, invoices, contacts, email, calendar, tasks, customers, projects, employees, documents, knowledge |
| `Life` | 🏠 | `life` | personal, learning, hobbies, relationships, travel, notes, tasks, calendar |
| `Studio` | 🔧 | `studio` | content, media, integrations, files, settings, automation, ai-images |

### 1.2 Complete Space Registry (26 spaces)

| # | ID | Icon | Title | Description | Mode(s) |
|---|----|------|-------|-------------|---------|
| 1 | `liveblock-io` | 🧩 | LiveBlock IO | Build, preview, deploy visual blocks | Work |
| 2 | `business` | 🏢 | Business | Marketing, finance, sales, team, projects, reports | Work |
| 3 | `calendar` | 📅 | Calendar | Events, schedule, deadlines | Work, Life |
| 4 | `email` | 📧 | Email | Inbox, compose, triage | Work |
| 5 | `proposals` | 📋 | Proposals | Create, send, track proposals | Work |
| 6 | `contacts` | 👥 | Contacts | People, customers, relationships | Work |
| 7 | `tasks` | ✅ | Tasks | To-dos, priorities, tracking | Work, Life |
| 8 | `knowledge` | 🧠 | Knowledge | What SHUNYA knows about entities | Work |
| 9 | `invoices` | 📄 | Invoices | Billings, payments, receipts | Work |
| 10 | `customers` | 👤 | Customers | Client profiles, history, loyalty | Work |
| 11 | `projects` | 📊 | Projects | Plans, milestones, deliverables | Work |
| 12 | `employees` | 👨‍💼 | Employees | Team management, roles, payroll | Work |
| 13 | `documents` | 📄 | Documents | Files, contracts, reports | Work |
| 14 | `notes` | 📝 | Notes | Quick notes, ideas, meeting minutes | Life |
| 15 | `personal` | 👤 | Personal | Private space, journal, goals | Life |
| 16 | `learning` | 📚 | Learning | Courses, skills, knowledge | Life |
| 17 | `hobbies` | 🎨 | Hobbies | Interests, activities, collections | Life |
| 18 | `relationships` | 💞 | Relationships | Friends, family, social connections | Life |
| 19 | `travel` | ✈️ | Travel | Trips, itineraries, bookings | Life |
| 20 | `media` | 🎬 | Media Hub | Images, videos, audio, assets | Studio |
| 21 | `content` | ✍️ | Content Studio | Blogs, social, campaigns, SEO | Studio |
| 22 | `integrations` | 🔗 | Integrations | Cloudinary, PDF, payments | Studio |
| 23 | `files` | 🗂️ | Files | Documents, uploads, storage | Studio |
| 24 | `settings` | ⚙️ | Settings | Profile, appearance, account, payments | Studio |
| 25 | `automation` | ⚡ | Automation | When X happens, then do Y | Studio |
| 26 | `ai-images` | 🎨 | AI Images | Generate images via pollinations.ai | Studio |
| — | `whatsapp` | 💬 | WhatsApp | Messages, broadcast, automation | (standalone) |

### 1.3 SpacePanel — Rendered Components Per Space

| Space ID | Component | Import Source |
|----------|-----------|---------------|
| `proposals` | `LazyProposalsPanel` | space-registry |
| `files` | `LazyFileManager` | space-registry |
| `settings` | `LazySettingsPanel` | space-registry |
| `automation` | `LazyAutomationRulesPanel` | space-registry |
| `knowledge` | `LazyKnowledgeBrowserPanel` | space-registry |
| `ai-images` | `LazyPollinationsGenerator` | space-registry |
| `email` | `LazyGmailInbox` | space-registry |
| `whatsapp` | `LazyWhatsAppWebPanel` | space-registry |
| `business` | `LazyBusinessPanel` | space-registry |
| `media` | `LazyStockMediaHub` | space-registry |
| `content` | `LazyContentStudio` | space-registry |
| `integrations` | `LazyIntegrationHub` | space-registry |
| `invoices` | Placeholder (`Invoice workspace`) | inline |
| `contacts` | Placeholder (`Contact workspace`) | inline |
| `tasks` | Placeholder (`Task workspace`) | inline |
| Others | Default card with icon + title + desc | inline |

### 1.4 Executive Dashboard (in Unified OS)

The `DashboardSection` component renders a "Living Narrative (Cognitive Cycle)" with 5 phases:

1. **Reality — Current State:** KPI cards (Revenue MTD, Invoices Overdue, Active Proposals, Task Completion) with animated counters
2. **Understanding — What This Means:** AI-generated natural language summary of KPI state
3. **Recommendations — What Needs Action:** Clickable nudge cards (overdue invoices, proposals ready for review, calls to make)
4. **Activity — What Changed:** Chronological activity feed with timestamps
5. **Next Steps — What SHUNYA Recommends:** Action buttons (Send Overdue Reminders, Review Proposals, Ask AI)

Data sources: `GET /api/v1/founder/executive-home` (polled every 60s) + realtime delta events via `useRealtimeSync`

**Demo Fallback Data:**
- Fallback KPIs: Revenue MTD $45,200 (+12.4%), Invoices Overdue 3, Active Proposals 8 ($127K pipeline), Task Completion 76%
- Demo Nudges: INV-003 overdue, Proposal ready for review, Call Acme Corp
- Demo Activity: Generated invoice, Drafted email reply, Revenue report ready

### 1.5 Auth System
- Sign In / Sign Up modal (email + password)
- API endpoints: `api.signin`, `api.signup`
- Session managed via `SessionManager` (localStorage wrapper)
- Forgot password link

---

## 2. WORKSPACE CONTAINER — Panel Types

**File:** `frontend/src/components/workspace/workspace-container.tsx`

### 2.1 Rendered Panel Types

The `WorkspaceContainer` routes to different workspaces based on `active.identity.type`:

| Identity Type | Component | Description |
|---------------|-----------|-------------|
| `home` (default) | `ExecutiveHome` | Default landing workspace |
| `object` | `LivingWorkspace` (from `./living-workspace`) | Object detail / living cognitive workspace |
| `calendar` | `CalendarPanel` | Full calendar view |
| `proposals` | `MantineProposalsPanel` | Proposal management |
| `music` | `YouTubePlayer` | Music/media player |
| `email` | `GmailInbox` | Email inbox |
| Composed panels | `Panel` via `CompositionEngine` | Dynamic panel composition for unknown types |
| Error state | `WorkspaceErrorState` | Error with retry button |
| Loading state | `WorkspaceLoadingState` | Skeleton shimmer |

### 2.2 Composition Engine
When `active.layout` is set and the identity type is an object with data, the `CompositionEngine` generates a panel layout dynamically. Each panel gets `id`, `label`, `Component`, `props`, and optional `loading`/`error`.

### 2.3 Runtime Orchestration
- Uses `useActiveWorkspace` hook for current workspace identity
- Uses `useRuntimeHealth()` to wait for runtime readiness
- Uses `useWorkspaceStore` for error tracking
- Fetches object data from `GET /api/v1/founder/objects/{oid}`
- Emits bus events: `ObjectLoaded`, `TimelineLoaded`

---

## 3. HOME WORKSPACE — Executive Dashboard (Legacy)

**File:** `frontend/src/components/workspace/home-workspace.tsx`

### 3.1 Summary Cards (4 cards in a grid)
| Card | Data Source | Description |
|------|-------------|-------------|
| Total Records | `GET /api/v1/founder/objects/types` | Count across all object types |
| At Risk | Derived from object content JSON | Objects with `status === 'at_risk'` |
| Recent Decisions | Derived (min(total, 7)) | Estimated recent decisions in last 7 days |
| Active Tasks | Derived (total * 0.15) | Estimated active tasks across workspaces |

### 3.2 Sections
- **Attention-Worthy Changes:** Shows alert for at-risk items or "Nothing requires your attention"
- **Recent Objects:** Clickable cards from `GET /api/v1/founder/objects?limit=8` showing type, name, status
- **Quick Access:** Single "Coming Soon" button

### 3.3 API Endpoints Consumed
- `GET /api/v1/founder/objects/types` — type breakdown counts
- `GET /api/v1/founder/objects` — recent objects list

---

## 4. WORKSPACE BAR — OS Command Center

**File:** `frontend/src/components/workspace/workspace-bar.tsx`

### 4.1 Capability Actions (7 quick actions)
| Action | Icon | Label | Shortcut | Action |
|--------|------|-------|----------|--------|
| Search | `Search` | Search everything | ⌘K | Opens command palette |
| AI | `Sparkles` | Ask AI | — | Toggles context panel |
| Email | `Mail` | Email | — | Opens Email workspace |
| Calendar | `CalendarDays` | Calendar | — | Opens Calendar workspace |
| Proposals | `FileText` | Proposals | — | Opens Proposals workspace |
| Music | `Music` | Music | — | Opens Music workspace |
| Home | `Home` | Home workspace | — | Activates home workspace |

### 4.2 Search Feature
- Debounced search input (300ms delay)
- Calls `GET /api/v1/search?q={query}`
- Shows dropdown with 8 results max
- Results show: icon (🌐 for internet, 📄 for documents), title, snippet (80 chars), type
- Keyboard shortcut: ⌘K
- Placeholder: "Search objects, invoices, people…"

### 4.3 Notifications System
- Fetches: `GET /api/notifications/unread/count` (on mount + every 30s)
- Fetches list: `GET /api/notifications?limit=5`
- Mark read: `POST /api/notifications/{id}/read`
- Mark all read: `POST /api/notifications/read-all`
- Dropdown shows: icon, title, message, timestamp, read/unread state

### 4.4 UI Components
- **Brand:** "शून्य" logo with gradient text
- **AI Presence:** Ambient context label (e.g. "Observing customer records")
- **Workspace Tabs:** Tab bar for open workspaces (max 6 visible), with dirty indicator, close button
- **Profile:** Avatar initial, dropdown with name/email, Home link, Sign out
- **Dark/Light mode** toggle
- **Responsive:** hides AI presence, actions, and KBD on mobile (<768px)

### 4.5 Session Management
- `POST /founder/logout` on sign out
- `SessionManager.load()` for session data
- `SessionManager.clear()` on logout

---

## 5. BACKEND API ROUTES

### 5.1 Route Files (43 total route modules)

#### Core Routes (`/app/`)
| File | Routes Served | Purpose |
|------|---------------|---------|
| `routes.py` | `/`, `/auth/*`, `/living`, `/welcome`, `/calendar`, `/leads/*`, `/payments/*`, `/invoices/*`, `/tasks/*`, `/reports`, `/settings`, `/telegram/*`, `/whatsapp/*` | Main Flask app — dashboards, CRUD, webhooks |
| `workspace_routes.py` | `/workspace/`, `/workspace/object/<id>` | Workspace SPA shell |
| `auth_routes.py` | Auth endpoints | Authentication |
| `genesis_routes.py` | Genesis routes | System bootstrap |
| `authz/routes.py` | Authorization | Permission checking |

#### Domain Module Routes (`/app/<domain>/routes.py`)
| Domain Directory | Route Module | Purpose |
|-----------------|--------------|---------|
| `ai/` | `routes.py` | AI interaction endpoints |
| `automation/` | `routes.py` | Automation rules CRUD |
| `cloudinary/` | `routes.py` | Cloudinary media integration |
| `communication/` | `routes.py` | Email/WhatsApp communication |
| `enterprise/` | `routes.py` | Enterprise features |
| `events/` | `routes.py` | Event management |
| `execution/` | `routes.py` | Execution engine |
| `finance/` | `routes_api.py` | Financial operations |
| `for1/` | `routes.py` | FOR-1 features |
| `for2/` | `routes.py` | FOR-2 features |
| `founder/` | `routes.py` | Founder-specific endpoints |
| `integration/` | `routes.py` | Third-party integrations |
| `intelligence/` | `routes.py` | AI intelligence/insights |
| `intention/` | `routes.py` | Intention recognition |
| `jobs/` | `routes.py` | Background jobs |
| `objects/` | `routes.py`, `file_routes.py` | Universal object CRUD + file ops |
| `onboarding/` | `routes.py` | User onboarding |
| `pdf/` | `routes.py` | PDF generation |
| `razorpay/` | `routes.py` | Razorpay payment gateway |
| `reality_engine/` | `routes.py` | Reality Engine (projections, events) |
| `relationship/` | `routes_api.py`, `routes_ui.py` | Relationship management |
| `search/` | `routes.py` | Unified search |
| `space/` | `routes.py` | Space management |
| `upload/` | `routes.py` | File upload |
| `workspace/` | `routes.py` | Workspace config |

#### Production Identity Routes (`/app/production/identity/`)
| File | Purpose |
|------|---------|
| `onboarding_routes.py` | User onboarding flows |
| `org_routes.py` | Organization CRUD |
| `workspace_routes.py` | Workspace identity management |
| `switch_routes.py` | Identity/org switching |
| `invitation_routes.py` | Team invitations |
| `lifecycle_routes.py` | Identity lifecycle |
| `user_routes.py` | User profile management |

#### Production Auth Routes (`/app/production/auth/`)
| File | Purpose |
|------|---------|
| `session_routes.py` | Session management |
| `email_verification_routes.py` | Email verification |
| `password_reset_routes.py` | Password reset |
| `mfa_routes.py` | Multi-factor auth |

### 5.2 Key API Endpoints (consumed by frontend)

| Endpoint | Method | Purpose | Consumed By |
|----------|--------|---------|-------------|
| `GET /api/v1/founder/executive-home` | GET | Executive dashboard data (KPIs, priorities, activity) | UnifiedOS homepage |
| `GET /api/v1/founder/objects/<oid>` | GET | Single object data | WorkspaceContainer |
| `GET /api/v1/founder/objects/types` | GET | Object type breakdown | HomeWorkspace |
| `GET /api/v1/founder/objects` | GET | Recent objects list | HomeWorkspace |
| `GET /api/v1/founder/objects?limit=8` | GET | Recent objects (limited) | HomeWorkspace |
| `GET /api/v1/founder/workspace/<oid>/missing-context` | GET | Missing context / recommendations | LivingWorkspace (Recommendations) |
| `GET /api/v1/founder/workspace/<oid>/next-actions` | GET | Next best actions | LivingWorkspace (NextActions) |
| `GET /api/v1/founder/workspace/<oid>/timeline` | GET | Object timeline/activity | LivingWorkspace (TimelineWidget) |
| `GET /api/v1/founder/workspace/<oid>/relationships` | GET | Related objects | LivingWorkspace (RelatedObjects) |
| `POST /api/v1/intelligence/mixed` | POST | Mixed intelligence query | LivingWorkspace (AIUnderstanding) |
| `GET /api/v1/reality` | GET | Reality Engine projection | LivingStore / useReality hook |
| `GET /api/v1/reality/stream` | SSE | Reality Engine streaming | useReality hook |
| `GET /api/v1/reality/object/<oid>` | GET | Object-specific reality | useReality hook |
| `GET /api/v1/ai/insights` | GET | AI observations/insights | LivingStore |
| `GET /api/v1/objects/types` | GET | Object types summary | LivingStore |
| `POST /api/v1/objects/<type>` | POST | Create object | LivingStore executeAction |
| `GET /api/v1/search` | GET | Unified search | WorkspaceBar search |
| `POST /outcomes/execute` | POST | Execute outcome by name/intent | LivingStore, UnifiedOS AI |
| `GET /outcomes/workflows` | GET | List workflows | Routes.py |
| `POST /outcomes/workflows/execute` | POST | Execute workflow | Routes.py |
| `GET /outcomes/list` | GET | List all outcomes | Routes.py |
| `GET /api/notifications` | GET | List notifications | WorkspaceBar |
| `GET /api/notifications/unread/count` | GET | Unread notification count | WorkspaceBar |
| `POST /api/notifications/<id>/read` | POST | Mark notification read | WorkspaceBar |
| `POST /api/notifications/read-all` | POST | Mark all notifications read | WorkspaceBar |
| `POST /api/notifications/create` | POST | Create notification | Routes.py |
| `POST /api/orgs` | POST | Create organization | UnifiedOS |
| `POST /founder/logout` | POST | Logout | WorkspaceBar |
| `POST /api/v1/objects/<type>` | POST | Create typed object | LivingStore |
| `GET /api/calendar/events` | GET | Calendar events feed | Calendar |

---

## 6. LIVING WORKSPACE (in workspace/) — Object Detail Panels

**File:** `frontend/src/components/workspace/living-workspace.tsx`

### 6.1 Object-Type-Specific Panel Configurations

| Object Type | Panels |
|-------------|--------|
| `customer` | AI Understanding, Recommendations, Next Best Actions, Risks & Opportunities, Activity Timeline, Related Objects |
| `trip` | Trip Intelligence, AI Recommendations, Next Steps, Trip Risks, Itinerary, Documents & Expenses |
| `invoice` | Invoice Intelligence, AI Recommendations, Required Actions, Payment Risk, Payment Timeline, Customer & Items |
| `document` | AI Summary, Suggestions, Actions, Version History, Related Objects |
| `project` | Project Intelligence, AI Recommendations, Next Actions, Risk Detection, Milestones, Team & Tasks |
| (default) | AI Understanding, Recommendations, Next Actions, Activity, Related |

### 6.2 Panel Components
| Panel ID | Component | API Endpoint |
|----------|-----------|-------------|
| `ai-understanding` | `AIUnderstanding` | `POST /api/v1/intelligence/mixed` |
| `recommendations` | `Recommendations` | `GET /api/v1/founder/workspace/{oid}/missing-context` |
| `next-actions` | `NextActions` | `GET /api/v1/founder/workspace/{oid}/next-actions` |
| `risks` | Inline placeholder | (No endpoint — static "No risks detected") |
| `timeline` | `TimelineWidget` | `GET /api/v1/founder/workspace/{oid}/timeline` |
| `related` | `RelatedObjects` | `GET /api/v1/founder/workspace/{oid}/relationships` |
| `capability` | `CapabilityBar` | (UI only — Search, Create, Voice, Upload) |

### 6.3 Capability Quick Bar (4 buttons)
- Search, Create, Voice, Upload

### 6.4 Object Identity Header
Shows: type badge, object ID, object name, status (Active), workspace context

---

## 7. LIVING WORKSPACE (LX-01) — `/frontend/src/components/living-workspace/`

**This is the experimental canonical UX (separate from workspace/ directory)**

### 7.1 File Inventory

| File | Purpose | Key APIs Consumed |
|------|---------|-------------------|
| `living-workspace.tsx` | Main layout — TopBar, ExecutiveBriefing, RealityStream, LivingObjects, AIPresenceSidebar, CommandSurface | Zustand store |
| `types.ts` | Core types: RealityEvent, AIObservation, AIRecommendation, Execution, LivingObject, LivingWorkspaceState, ExecutiveHomeResponse, AIInsightResponse | — |
| `living-store.ts` | Zustand store — state management, polling, execution, recommendations, LX-04 adaptation, LX-05 memory governance | `GET /api/v1/reality`, `GET /api/v1/ai/insights`, `GET /api/v1/objects/types`, `POST /outcomes/execute` |
| `ai-presence-panel.tsx` | Continuous companion — "What has SHUNYA already done? / What is SHUNYA doing now? / What is SHUNYA waiting for? / What does SHUNYA recommend next?" + 10-second countdown auto-execution | Zustand store |
| `reality-stream.tsx` | Continuous narrative stream — events with business-meaningful time narratives instead of timestamps | Zustand store |
| `living-object-card.tsx` | Expandable object cards — stage pipeline, time narrative, relationship stories, recommendation + quick action | Zustand store |
| `command-surface.tsx` | Persistent command bar — input, contextual suggestions (Create first object, Review AI insights, Ask SHUNYA, Generate report), ⌘K shortcut | `POST /outcomes/execute` |
| `executive-briefing.tsx` | Companion greeting — journey tracking (Briefing → Recommendation → Execution → Outcome → Follow-up), priority overview, execution progress, outcome display, follow-up suggestions | Zustand store |
| `memory-review.tsx` | LX-05 Memory Governance — session/founder/business memory tiers, adaptation level, preference display, reflection history, reset | Zustand store (client-side only) |
| `use-reality.ts` | Transport-agnostic Reality subscription hook — polling + SSE, fallback behavior, Object reality context | `GET /api/v1/reality`, `GET /api/v1/reality/stream`, `GET /api/v1/reality/object/{oid}` |
| `living-styles.css` | CSS styling for LX-01 components | — |
| `index.ts` | Barrel export | — |

### 7.2 Layout Architecture
```
┌──────────────────────────────────────────────┐
│  Top Bar: शून्य · AI Status · Last Updated    │
├──────────────────────┬───────────────────────┤
│  Executive Briefing  │  AI Presence Panel    │
│  (journey stages)    │  (observations,       │
│  Reality Stream      │   recommendations,    │
│  (what changed)      │   execution)          │
│  Living Objects      │                       │
├──────────────────────┴───────────────────────┤
│  Command Surface (always visible)            │
└──────────────────────────────────────────────┘
```

### 7.3 LX-04 Adaptation System
- Tracks interaction history (last 100)
- Infers founder preferences per object type
- Generates reflection messages every 10th interaction
- Confidence grows with total interactions (max 0.95)
- Prepares actions with 10-second countdown auto-execute for high-confidence recommendations

### 7.4 LX-05 Memory Governance
- **Session Memory:** Discarded when founder closes (interactions, observations, reality events)
- **Founder Memory:** Explainable, reviewable, resettable (preferences, reflection messages)
- **Business Memory:** Permanent canonical truth (objects, relationships, outcomes)

### 7.5 Polling Architecture
- Reality Engine: every 15s (`REALITY_POLL_MS = 15_000`)
- SSE streaming as preferred transport with polling fallback
- AI Insights: polled separately via `fetchInsights()`

---

## 8. FOUNDER VALUE — Capability Mapping

### Legacy Workspace Capabilities Delivered

| Domain | Capabilities | UI Surface | Backend Routes |
|--------|-------------|------------|----------------|
| **Executive Dashboard** | KPI overview, priorities, activity, nudges | UnifiedOS DashboardSection, HomeWorkspace | `/api/v1/founder/executive-home`, `/api/v1/founder/objects/types` |
| **Object Management** | CRUD, type breakdown, relationship, timeline | LivingWorkspace panels, SpacePanel | `/api/v1/founder/objects/*`, `/api/v1/objects/*` |
| **Business Operations** | Proposals, Invoices, Customers, Projects, Employees | SpaceRegistry (Lazy panels) | `/outcomes/execute`, `/outcomes/workflows` |
| **Communication** | Email (Gmail), WhatsApp | LazyGmailInbox, LazyWhatsAppWebPanel | `/communication/routes.py` |
| **Calendar & Scheduling** | Events, deadlines | CalendarPanel, Calendar space | `/api/calendar/events` |
| **Media & Content** | Media Hub, Content Studio, AI Images | LazyStockMediaHub, LazyContentStudio, LazyPollinationsGenerator | `/cloudinary/routes.py` |
| **Search** | Unified search across objects | WorkspaceBar search | `/api/v1/search` |
| **AI Intelligence** | Object understanding, recommendations, next actions, insights | AIUnderstanding, Recommendations, NextActions panels | `/api/v1/intelligence/mixed`, `/api/v1/ai/insights`, `/outcomes/execute` |
| **Reality Engine** | Continuous projections, events, attention items | LivingStore, useReality, RealityStream | `/api/v1/reality`, `/api/v1/reality/stream` |
| **Notifications** | System notifications, badge count, mark read | WorkspaceBar NotificationsDropdown | `/api/notifications/*` |
| **Automation** | Rules engine (when X, then Y) | LazyAutomationRulesPanel | `/automation/routes.py` |
| **Knowledge Browser** | Entity knowledge | LazyKnowledgeBrowserPanel | `/founder/routes.py` |
| **Settings** | Profile, appearance, account, payments | LazySettingsPanel | routes.py settings |
| **Integrations** | Cloudinary, PDF, payments, Razorpay | LazyIntegrationHub | `/integration/routes.py`, `/pdf/routes.py`, `/razorpay/routes.py` |
| **File Management** | Documents, uploads, storage | LazyFileManager | `/upload/routes.py`, `/objects/file_routes.py` |
| **Onboarding & Auth** | Sign in/up, org creation, invitations | AuthModal, org flows | `auth_routes.py`, `production/auth/*`, `production/identity/*` |
| **Workspace Lifecycle** | Workspace tabs, switching, close | WorkspaceBar tabs | `workspace_routes.py`, `production/identity/workspace_routes.py` |
| **Background Jobs** | Async job monitoring | BackgroundJobs component | `/jobs/routes.py` |
| **Payments** | Create, verify, checkout, receipt | Invoice space, Payment flows | `/api/payment/*`, routes.py payments |
| **Telegram Bot** | Incoming leads via Telegram | — | `/telegram/webhook` |
| **Adaptation (LX-04)** | Founder preference learning | LivingStore (client-side) | (Client-side only, not persisted) |
| **Memory Governance (LX-05)** | Explainable, reviewable, resettable memory | MemoryReview | (Client-side only, not persisted) |
| **Travel/Shunya** | Itinerary builder, pipeline | — | `/api/shunya/*`, `/itineraries` |

---

## 9. ROUTE DIRECTORY STRUCTURE (Summary)

```
app/
├── routes.py                        # Main routes — 1942 lines (dashboard, CRUD, webhooks)
├── workspace_routes.py              # SPA shell for workspace/{object}
├── auth_routes.py                   # Authentication
├── genesis_routes.py                # System bootstrap
├── ai/routes.py                     # AI endpoints
├── automation/routes.py             # Automation rules
├── authz/routes.py                  # Authorization
├── cloudinary/routes.py             # Media cloud
├── communication/routes.py          # Email/WhatsApp
├── enterprise/routes.py             # Enterprise features
├── events/routes.py                 # Event management
├── execution/routes.py              # Execution engine
├── finance/routes_api.py            # Financial operations
├── for1/routes.py, for2/routes.py   # FOR feature modules
├── founder/routes.py                # Founder endpoints
├── integration/routes.py            # Third-party integrations
├── intelligence/routes.py           # AI insights/intelligence
├── intention/routes.py              # Intention recognition
├── jobs/routes.py                   # Background jobs
├── objects/routes.py, file_routes.py # Universal object CRUD
├── onboarding/routes.py             # User onboarding
├── pdf/routes.py                    # PDF generation
├── razorpay/routes.py               # Razorpay payments
├── reality_engine/routes.py         # Reality Engine
├── relationship/routes_api.py, routes_ui.py  # Relationships
├── search/routes.py                 # Unified search
├── space/routes.py                  # Space management
├── upload/routes.py                 # File upload
├── workspace/routes.py              # Workspace config
├── production/identity/             # Identity management (6 route files)
└── production/auth/                 # Auth management (4 route files)
```

---

## 10. MIGRATION IMPACT NOTES

1. **Two parallel LivingWorkspace implementations exist:**
   - `workspace/living-workspace.tsx` (SX-11 style — object detail panels with AI)
   - `living-workspace/living-workspace.tsx` (LX-01 canonical — continuous companion, reality engine, adaptation)

2. **SpacePanel in UnifiedOS** uses lazy-loaded components from `space-registry` for 12 of 26 spaces; the rest are placeholders.

3. **WorkspaceContainer** routes by identity type only — no direct space-to-route mapping in the backend for individual spaces (only `/workspace/object/<id>` and `/workspace/` SPA shells).

4. **Reality Engine** is the primary backend for living workspace data, while legacy routes.py still serves traditional CRUD for leads/payments/invoices.

5. **LX-04 Adaptation** is entirely client-side (Zustand store) with no backend persistence until Launch Candidate.

6. **43 route modules** across the backend serve the legacy workspace — migration must account for each module's endpoints.

7. **API versioning:** Mix of `/api/v1/*`, `/api/*`, `/outcomes/*`, and unversioned `/workspace/*`, `/living` routes — no consistent scheme.