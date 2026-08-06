# SHUNYA OS — Backend Architectural Duplication Report (LX-06 Audit)

**Date:** 2026-08-05  
**Scope:** `/home/shunya-deploy/shunya_os/app/`  
**Files scanned:** 206 Python files across all directories  
**Classification:** Canonical / Duplicate / Legacy / Experimental / Dead  

---

## 1. AUTHENTICATION — ⚠️ MASSIVE DUPLICATION (4+ parallel systems)

| Component | Classification | Notes |
|---|---|---|
| `app/auth.py` — TeamMember model, AuthLayer, SHA256 hashing | **Legacy** | Table `team_members`. Still used by auth_routes for session login. Will be retained until all users migrate to kernel identity. |
| `app/auth_routes.py` — auth_bp, login_required, /login, /logout, /team/, /api/v1/auth/signup | **Legacy** | Actively wired. login_required decorator used dozens of places. Email verification endpoints DUPLICATED with production/auth/. |
| `app/auth_oauth.py` — oauth_bp, Google+GitHub OAuth | **Duplicate** (Migration bridge) | Creates identities via IdentityRepository. Sets both session['user_id'] AND session['identity_id']. Bridges legacy→kernel. |
| `app/production/auth/password_reset_routes.py` | **Duplicate** | Registers on auth_bp. In-memory token store. Duplicates pattern already in auth_routes.py. |
| `app/production/auth/email_verification_routes.py` | **Duplicate** | Registers `/request-verification` on auth_bp. auth_routes.py already has `/api/v1/auth/request-verification`. Two parallel in-memory token stores. |
| `app/production/auth/mfa_routes.py` | **Duplicate** | In-memory MFA state. Same pattern. |
| `app/production/auth/session_routes.py` | **Duplicate** | Session revocation, in-memory version tracking. |
| `app/authz/` — Role, OrgMemberRole, permission system | **Canonical** | Newer, cleaner authorization engine. Separates auth (who you are) from authorization (what you can do). Coexists with legacy UserRole. |
| `app/security/jwt.py` | **Canonical** | JWT utilities. |

**Key overlap:** Two email verification implementations (auth_routes.py lines 270-305 AND production/auth/email_verification_routes.py), both on the same `auth_bp` blueprint. Different in-memory stores.

---

## 2. IDENTITY — ⚠️ TRIPLICATION

| Component | Classification | Notes |
|---|---|---|
| `app/kernel/identity.py` — SHUNYAIdentity, AuthMethodType, IdentityStore | **Canonical** | Kernel-level identity contract. Frozen by design. |
| `app/production/identity_repository.py` — IdentityRepository, SHUNYAIdentityModel | **Canonical** (Bridge) | Persistence bridge. Exposes both legacy `find_by_auth()` and new `find_by_auth_core()` APIs. |
| `app/production/identity/` — org_routes, user_routes, workspace_routes, invitation_routes, lifecycle_routes, onboarding_routes, switch_routes | **Canonical** | Milestone X identity CRUD. All registered on identity_bp at `/orgs`. |
| `app/shunya/identity/engine.py` — IdentityEngine | **Duplicate** | Implements resolver, lifecycle, normalizer. Overlaps heavily with kernel.identity + identity_repository. |
| `app/shunya/identity/models.py` — IdentityType, IdentityStatus, ResolutionStatus enums | **Duplicate** | Different enum values from kernel/identity.py (AuthMethodType). Parallel enum hierarchy. |
| `app/gkf/identity.py` — GKF identity (collection/volume/chapter) | **Canonical** (for GKF) | Document-structural identity. Different domain, but same concept "identity" used differently. |
| `app/auth.py` TeamMember | **Legacy** | The original "identity as email+password". |

---

## 3. WORKSPACE MODELS — ⚠️ TRIPLICATION

| Component | Classification | Notes |
|---|---|---|
| `app/objects/models.py` — Workspace (table `sh_workspaces`, id='spc_xxx') | **Canonical** | Phase 0 foundation. Used by object routes. |
| `app/production/identity/workspace_model.py` — Workspace (table `workspaces`, id Integer, FK to tenants) | **Duplicate** | Milestone X production workspace. Different table, different schema, same concept. |
| `app/workspace/models.py` — Experience catalog (no SQL model) | **Canonical** | Experience framework only, not a persistence model. Different abstraction level. |

---

## 4. ENGINES — ⚠️ SIGNIFICANT OVERLAP (12+ engine classes)

| Component | Classification | Notes |
|---|---|---|
| `app/reality_engine/engine.py` — RealityEngine (LX-02) | **Canonical** | Highest-level composition engine. Composes events, attention, objects, execution, awareness, graph. "Single source from which interface derives." |
| `app/intelligence/` — Explainable Intelligence (observation, reasoning, insight, confidence, inspector, scenario) | **Canonical** | Explainability pipeline with provenance. Separate domain. |
| `app/awareness/engine.py` — Operational Awareness (8 sub-engines) | **Experimental** | Reads from execution, execution_intelligence. |
| `app/cognitive/engine.py` — Cognitive Validation (reasoning graphs, contradictions, replay) | **Experimental** | Validates cognitive pipeline. Heavy overlap with intelligence/ in concepts. |
| `app/execution_intelligence/engine.py` — Execution Intelligence (7 engines: health, risk, timeline, dependency, next_action, portfolio) | **Experimental** | Overlaps with awareness/ and executive/ in health/risk concepts. |
| `app/executive/engine.py` — Executive Intelligence | **Experimental** | Synthesizes organizational intelligence. Depends on orchestration, decision, cognitive. |
| `app/orchestrator/engine.py` — OrchestratorEngine | **Experimental** | Pipeline orchestration. |
| `app/prediction/engine.py` — Prediction & Simulation | **Experimental** | Read-only predictions. |
| `app/collaboration/engine.py` — Collaboration (presence, sessions, shared) | **Experimental** | Multi-user runtime. |
| `app/organizational/engine.py` — Organizational Intelligence | **Experimental** | |
| `app/learning_intelligence/engine.py` — Learning Intelligence | **Experimental** | |
| `app/orchestration/` — cycle, queue, signal, sync | **Experimental** | Orchestration runtime layer. |

**Overlap pattern:** intelligence/, awareness/, cognitive/, execution_intelligence/, executive/ all define engine classes with overlapping concepts (health scoring, risk detection, insight generation, attention scoring). Each has its own model classes and its own "engine" with get_*() singleton accessors.

---

## 5. RUNTIMES — ⚠️ SIGNIFICANT OVERLAP

| Component | Classification | Notes |
|---|---|---|
| `app/outcome_engine.py` — OutcomeEngine, WorkflowEngine | **Canonical** | Executes named outcomes via intent/name. Used by `/api/outcomes/execute`. |
| `app/execution/runtime.py` — OutcomeRuntime | **Duplicate** | Also manages outcomes from acceptance→completion. Different code path. Overlaps with outcome_engine.py. |
| `app/workspace_runtime.py` — WorkspaceRuntime | **Canonical** | Object registry, runtime-driven workspace state. |
| `app/decision_runtime/` — Decision middleware | **Experimental** | Decisions, policies, commitments. |
| `app/planning/runtime.py` | **Experimental** | Planning runtime. |
| `app/temporal/runtime.py` | **Experimental** | Temporal runtime. |
| `app/orchestration/runtime.py` | **Experimental** | Orchestration runtime. |
| `app/graph_universal/runtime.py` | **Experimental** | Universal graph runtime. |
| `app/space/runtime.py` | **Experimental** | Universal space runtime. |
| `app/organization/runtime.py` | **Experimental** | Organization runtime. |
| `app/cortex/runtime.py` — Cortex middleware | **Experimental** | Organizational cortex. |

**Key overlap:** outcome_engine.py and execution/runtime.py both implement outcome execution. The outcome_engine is invoked from routes.py (`/api/outcomes/execute`), while execution/runtime.py OutcomeRuntime is a separate implementation.

---

## 6. AI / LLM / INFERENCE — ⚠️ TRIPLICATION

| Component | Classification | Notes |
|---|---|---|
| `app/ai/` — ai_bp, chat endpoint, provider registry, copilot, context, prompts | **Canonical** | Active AI chat API. Provider chain: Groq→Gemini→OpenRouter→Cloudflare→HF→Local. |
| `app/llm/` — LLMRuntimeService | **Duplicate** | Separate provider adapter pattern. Has ModelRun persistence model. Does not use app/ai/provider.py. |
| `app/inference/` — InferenceControlPolicy | **Experimental** | Control-plane only (policy decisions). No provider calls. |

**Key overlap:** `app/ai/provider.py` has an LLMProvider abstraction with 6+ backends. `app/llm/__init__.py` has its own LLMRuntimeService with its own FakeProviderAdapter. Two separate LLM abstraction layers.

---

## 7. SEARCH — ⚠️ DUPLICATION

| Component | Classification | Notes |
|---|---|---|
| `app/search.py` — UniversalSearch class | **Legacy** | SQL LIKE queries across leads, payments, invoices, suppliers, knowledge, media. |
| `app/search/` — search_bp, providers, context builder | **Canonical** | DuckDuckGo web search, clean provider abstraction, company context builder. |

---

## 8. NOTIFICATIONS — ⚠️ DUPLICATION

| Component | Classification | Notes |
|---|---|---|
| `app/notifications.py` — NotificationManager | **Legacy** | Works with `app.models.Notification` (old model). |
| `app/integration/models.py` — Notification model (table `m6_notifications`) | **Canonical** | Newer model with identity_id, notification_type, channels, email dispatch status. |

---

## 9. BLUEPRINT EXPLOSION — 34 registered blueprints

All blueprints registered in `create_app()` (most in `__init__.py`):

| Blueprint | URL Prefix | Classification |
|---|---|---|
| `auth_bp` | (none) | **Legacy** |
| `main` | (none) | **Legacy** |
| `api` | (none) | **Legacy** |
| `objects_bp` | `/api/v1/objects` | **Canonical** |
| `objects_upload_bp` | (implicit) | **Canonical** |
| `production_bp` | `/api/v1` | **Canonical** |
| `shunya_bp` | (none) | **Canonical** |
| `workspace_bp` (from workspace_routes.py) | `/workspace` | **Dead** (just serves SPA shell) |
| `founder_bp` | (implicit) | **Canonical** |
| `upload_bp` | (implicit) | **Canonical** |
| `search_bp` | `/api/v1` | **Canonical** |
| `jobs_bp` | (implicit) | **Canonical** |
| `intention_bp` | (implicit) | **Canonical** |
| `file_bp` | (implicit) | **Canonical** |
| `for1_bp` | `/for1` | **Legacy** |
| `for2_bp` | `/for2` | **Legacy** |
| `reality_bp` | (implicit) | **Canonical** |
| `relationship_bp` | (implicit) | **Canonical** |
| `authz_bp` | (implicit) | **Canonical** |
| `finance_bp` | (implicit) | **Canonical** |
| `onboarding_bp` | (implicit) | **Canonical** |
| `oauth_bp` | `/api/v1/auth` | **Duplicate** |
| `integration_bp` | (implicit) | **Canonical** |
| `cloudinary_bp` | (implicit) | **Canonical** |
| `pdf_bp` | (implicit) | **Canonical** |
| `razorpay_bp` | (implicit) | **Canonical** |
| `execution_bp` | (implicit) | **Experimental** |
| `automation_bp` | (implicit) | **Canonical** |
| `events_bp` | `/api/v1` | **Canonical** |
| `intelligence_bp` | (implicit) | **Canonical** |
| `communication_bp` | (implicit) | **Canonical** |
| `enterprise_bp` | (implicit) | **Canonical** |
| `ai_bp` | `/api/v1/ai` | **Canonical** |
| `genesis_bp` | (implicit) | **Canonical** |
| `space_bp` | `/api/v1/space` | **Experimental** |
| `workspace_bp` (from app.workspace) | `/api/v1/workspace` | **Canonical** |

---

## 10. SUMMARY OF OVERLAP CLUSTERS

### Highest priority for consolidation:

| Cluster | Files | Action |
|---|---|---|
| **Auth (4 systems)** | `auth.py`, `auth_routes.py`, `auth_oauth.py`, `production/auth/*`, `authz/` | Merge into `authz/` as canonical. Deprecate legacy TeamMember in favor of kernel Identity. |
| **Identity (3 systems)** | `kernel/identity.py`, `production/identity_repository.py`, `shunya/identity/` | `shunya/identity/` is fully duplicated. Remove it. |
| **Workspace (3 models)** | `objects/models.py`, `production/identity/workspace_model.py` | Unify into one model. Production model is newer; Phase 0 model has spc_xxx IDs. |
| **Engines (12+ engines)** | `intelligence/`, `awareness/`, `cognitive/`, `execution_intelligence/`, `executive/`, `orchestrator/` | Consolidate into RealityEngine as canonical. All others are experimental spin-offs. |
| **Outcome (2 impls)** | `outcome_engine.py`, `execution/runtime.py` | OutcomeEngine is canonical; OutcomeRuntime is overlapping. |
| **AI/LLM (2 abstractions)** | `ai/provider.py`, `llm/__init__.py` | LLMRuntimeService duplicates provider pattern from `ai/`. Merge or remove. |
| **Search (2 impls)** | `search.py`, `search/` | Remove legacy `search.py` (UniversalSearch). |
| **Notifications (2 models)** | `notifications.py`, `integration/models.py` | Retain `integration/models.py`. Remove `notifications.py` NotificationManager. |
| **Email verification (2 routes)** | `auth_routes.py`, `production/auth/email_verification_routes.py` | Two routes on same blueprint. Kill the production/auth version. |
| **Middleware (3 auth checks)** | `__init__.py` lines 378-388, 672-713; `auth_routes.py` login_required | Three separate auth middleware layers on the same app. Unify into one. |