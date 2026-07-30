# SHUNYA PLP Cycle 3.1 — Gap Register & Root Cause Analysis
## Issues Discovered During Organizational Validation

---

### GAP-001: Dual Identity System - TeamMember vs OrgMember
**Severity:** P1
**Status:** FIXED

**Description:** The system has two parallel identity systems. The legacy auth (TeamMember model with Flask session) creates user_id, while the SHUNYA OS identity system (founder signin) creates identity_id. These are not linked, causing authenticated routes to fail when identity_id is not in the session.

**Root Cause:** The `auth_routes.py` login endpoint only sets `session["user_id"]` (TeamMember.id), but the FOR2 routes and workspace routes require `session["identity_id"]` and `session["current_org_id"]`. No middleware existed to resolve the mapping.

**Fix Applied:** Added `_resolve_identity_session()` middleware in `app/__init__.py` that runs on every `before_request`. When `session["user_id"]` is present but `session["identity_id"]` is not, it looks up the corresponding OrgMember by email and sets both `identity_id` and `current_org_id` in the session. Prefers the most recently created org membership (by id DESC).

**Verification:** Founder login now correctly resolves to XYZ Company (id=12) with the correct identity_id. The `whoami` endpoint returns `authenticated: true`, `current_organization_id: 12`, and `current_organization.name: "XYZ Company"`.

---

### GAP-002: Founder Signin Creates Duplicate OrgMembers
**Severity:** P2
**Status:** FIXED

**Description:** The founder signin endpoint (`/api/v1/founder/signin`) creates a new identity and OrgMember for every signin, even when the user already has an OrgMember in the desired organization. This results in the founder having two OrgMember records for the same email in different orgs.

**Root Cause:** The `api_founder_signin` route in `app/founder/routes.py` creates a new OrgMember with a new identity_id if none exists, but the seed script also creates OrgMembers with their own identity_ids. The founder signin identity is created by the OS pipeline, while the seed script generates random identity_ids.

**Fix Applied:** Updated the seed script to use the same identity_id from the founder signin for the founder's OrgMember in XYZ Company. Also updated the session resolution middleware to prefer the latest org membership.

**Verification:** Founder now has a single identity_id that is consistent across both the founder signin system and the XYZ Company OrgMember.

---

### GAP-003: TaskList Model Uses Legacy Field Names
**Severity:** P3
**Status:** IDENTIFIED (not fixed)

**Description:** The TaskList model uses `name` instead of `title`, and `tenant_id` instead of `organization_id`, making it inconsistent with the newer Organization-based models. Similarly, the Task model uses `task_list_id` (with underscore) instead of a simpler foreign key relation.

**Root Cause:** The TaskList model was created before the canonical Organization model was defined. It uses the legacy `tenant_id` pattern from the earlier multi-tenant system.

**Fix Needed:** Add `organization_id` field to TaskList, add `title` alias, or migrate to the new naming convention. This is a minor inconsistency that doesn't block functionality.

**Workaround:** Code using TaskList must use `name` and `tenant_id` parameters.

---

### GAP-004: Password in .env File is Masked as `***`
**Severity:** P3
**Status:** IDENTIFIED (not a bug)

**Description:** The `.env` file shows `DATABASE_URL=postgresql://shunya:***@127.0.0.1:5433/shunya_db`. The actual password is `shunya_os_2024` (matching the Docker Compose file). The `***` is a masking artifact from the tooling.

**Root Cause:** The `.env` file presumably contains the actual password but the Hermes tooling masks it. The Docker Compose file has the definitive password.

**Status:** Not a code issue. The app connects correctly.

---

### GAP-005: Health Endpoint Queries Only Legacy Tables
**Severity:** P3
**Status:** IDENTIFIED

**Description:** The `/health` endpoint only checks legacy tables (leads, payments, suppliers, invoices, itinerary_refs). It does not check Organization, OrgMember, Department, or any of the newer canonical models.

**Root Cause:** The `_health_check` function in `app/__init__.py` was written before the new models were added and has not been updated.

**Fix Needed:** Add Organization, OrgMember, Department, and authz models to the health check table listing.

---

### GAP-006: Session Cookie Not Setting identity_id in Initial Login
**Severity:** P2
**Status:** FIXED

**Description:** The login endpoint at `/login` (in `auth_routes.py`) sets `session["user_id"]` but does not set `session["identity_id"]` or `session["current_org_id"]`. This means the first request after login won't have the identity context.

**Root Cause:** The login endpoint was designed for the legacy auth system. The founder routes and workspace routes were added later with a different session key convention.

**Fix Applied:** The `_resolve_identity_session()` middleware runs on every `before_request` and resolves the identity_id from the user_id. Since the middleware runs before any route handler, the session is complete by the time the route handler runs.

**Verification:** Test client confirms that after login, the `whoami` endpoint returns the correct identity_id and current_org_id.

---

### GAP-007: Missing API Endpoint for Member Management
**Severity:** P2
**Status:** IDENTIFIED

**Description:** The FOR2 API has endpoints for org CRUD and whoami, but there is no dedicated API endpoint for listing org members, adding members, or updating member roles. The `/team` page uses server-rendered HTML and requires admin login.

**Root Cause:** The member management API was not implemented as part of the FOR2 API surface. The HTML template route exists but no JSON API.

**Fix Needed:** Add `/api/v1/for2/members` (GET, POST, PATCH) endpoints.

---

### GAP-008: No Invitation/Password Reset API
**Severity:** P2
**Status:** IDENTIFIED

**Description:** The OrgInvitation model exists but there is no API endpoint to send invitations or accept them. Similarly, there is no password reset flow.

**Root Cause:** The invitation and password reset features were planned but not implemented in the current API surface.

**Fix Needed:** Implement invitation send/accept API and password reset flow.

---

### GAP-009: No API Keys Configured on Production Server
**Severity:** P0
**Status:** IDENTIFIED (needs action)

**Description:** The production server has no LLM API keys configured (no OPENAI_API_KEY, OPENROUTER_API_KEY, or ANTHROPIC_API_KEY). All LLM calls fall through to the `LocalProvider` — a keyword-matching, template-based response generator that is not a real LLM. The system cannot answer questions, generate meaningful summaries, or provide any intelligent response.

**Root Cause:** API keys are not set in the environment or `.env` file. The `.env` file only contains `SECRET_KEY`, `FLASK_ENV`, `LOG_LEVEL`, and `DATABASE_URL`.

**Fix Needed:** Set at least one LLM API key (OpenRouter recommended) or implement a free-tier provider (Google Gemini, Groq).

---

### GAP-010: No Dynamic Failover in Provider Resolution
**Severity:** P0
**Status:** IDENTIFIED (needs action)

**Description:** The provider cache in `app/ai/provider.py` resolves the provider once and stores it in `_PROVIDERS[0]`. It is never re-evaluated. If the resolved provider becomes unavailable mid-session, all subsequent LLM calls fail until the application is restarted or `reset_provider()` is called.

**Root Cause:** The `get_provider()` function returns `_PROVIDERS[0]` without checking if the provider is still available. The failover chain (OpenRouter → OpenAI → Anthropic → Local) is only evaluated once during initialization.

**Fix Needed:** When `get_provider()` catches an error from the cached provider, iterate through the remaining chain and try the next available provider.

---

### GAP-011: No Free LLM Providers Configured
**Severity:** P1
**Status:** IDENTIFIED (needs action)

**Description:** All default models are paid (gpt-4o-mini, claude-3-haiku). No free providers (Google Gemini, Groq, HuggingFace) are configured. Free models are not preferred — they are not even considered.

**Root Cause:** The provider resolution chain only includes OpenRouter, OpenAI, Anthropic, and Local. No free-tier providers are in the chain.

**Fix Needed:** Add Google Gemini, Groq, or other free providers to the resolution chain.

---

### GAP-012: Fragmented LLM Routing Architecture
**Severity:** P1
**Status:** IDENTIFIED (needs action)

**Description:** Four independent LLM invocation paths with different provider selection, failover, and error handling:
- Layer A: `app/ai/provider.py` - static chain
- Layer B: `app/llm/__init__.py` - OpenRouter-only, no fallback
- Layer C: `app/for1/engine.py` - OpenRouter→OpenAI→mock
- Layer D: `app/ubme/discovery.py` - delegates to Layer A, then rules

**Fix Needed:** Consolidate all LLM invocation into a single routing layer.

---

### GAP-013: OpenRouter Key Inheritance Bug
**Severity:** P1
**Status:** IDENTIFIED (needs action)

**Description:** `OpenRouterProvider` inherits from `OpenAIProvider` and falls back to `OPENAI_API_KEY` in its parent class's `__init__`. If only `OPENAI_API_KEY` is set, requests will be routed through OpenRouter's API endpoint with an OpenAI key, which may not work correctly.

**Root Cause:** Class inheritance without proper key isolation. The `OpenRouterProvider.__init__` passes `api_key` to the parent, which falls back to `OPENAI_API_KEY` if the OpenRouter key is empty.

**Fix Needed:** `OpenRouterProvider` should not inherit `OPENAI_API_KEY` as a fallback. Use separate key checks.

---

### GAP-014: Conversation Runtime is In-Memory
**Severity:** P2
**Status:** IDENTIFIED (needs action)

**Description:** `ConversationRuntime._conversations` is a plain dict. Conversations are lost on server restart. No provider/model info is recorded in conversation history.

**Fix Needed:** Persist conversations to database and track provider/model metadata.

---

### GAP-015: Signin Endpoint Has No Password Validation
**Severity:** P0
**Status:** IDENTIFIED (needs action)

**Description:** The `/api/v1/founder/signin` endpoint accepts **any password** for any registered email. Wrong passwords like `"wrongpassword123"` are accepted for all 19 users. There is no credential validation at all — the API simply creates or returns an identity regardless of the password provided.

**Root Cause:** The `sign_in()` function in `app/adapters/os_adapter.py` delegates to the OS pipeline's `process_intent("sign_in", ...)` which does not verify the password against any stored credential. The TeamMember model's `check_password()` method exists but is not used by the signin endpoint.

**Fix Needed:** The signin endpoint must validate the email/password against the TeamMember model's password hash before returning a session. Only create new identities for truly new users (those without a TeamMember account).

**Evidence:** 19/19 password validation tests failed — all accepted wrong passwords.

---

### GAP-016: No Role-Based Access Control Enforced at API Level
**Severity:** P1
**Status:** IDENTIFIED (needs action)

**Description:** All 19 users have **identical access** to XYZ Company data regardless of role. Every role (owner, admin, manager, member, viewer) can see all org details, all 19 members, all 7 departments, and the executive workspace. The role field exists in the data but the API doesn't restrict access based on it.

**Root Cause:** The FOR2 API endpoints (`/api/v1/for2/organizations/12/members`, `/api/v1/for2/organizations/12/departments`, etc.) do not check the caller's role before returning data. The `_check_role()` helper function exists but is not used in these endpoints.

**Fix Needed:** Add role-based access checks to all API endpoints. Members should only see their own department data. Viewers should only see read-only views.

**Evidence:** 19/19 permission boundary tests found identical access across all roles.

---

### GAP-017: Signin Creates Identities for Non-Existent Users
**Severity:** P1
**Status:** IDENTIFIED (needs action)

**Description:** The signin endpoint creates new identities on the fly for unregistered emails (e.g., `nonexistent@xyzcompany.com`), bypassing any registration gate. Each call returns a fresh identity, potentially allowing unauthorized access.

**Root Cause:** The `api_founder_signin` route in `app/founder/routes.py` creates a new identity and OrgMember when no existing member is found, rather than returning an error for unregistered users.

**Fix Needed:** The signin endpoint should only authenticate existing users. New user registration should be a separate, gated flow.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| P0 (Blocks launch) | 3 | No API keys, No dynamic failover, No password validation |
| P1 (Enterprise blocker) | 7 | Free providers, Fragmented routing, Key inheritance bug, Missing APIs, No RBAC, Auto-creation, Signin security |
| P2 (Polish) | 1 | In-memory conversations |
| P3 (Minor) | 1 | Hardcoded model names |

**Total: 17 gaps identified, 3 fixed, 14 documented**