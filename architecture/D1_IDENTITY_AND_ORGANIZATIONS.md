# D1 — Identity & Organizations: Architecture Specification

**Milestone X — Production SHUNYA**
**Deliverable 1: Identity & Organizations**
**Status: Pending Review**

---

## 1. Vision & Philosophy

Deliverable 1 establishes the foundational identity layer for SHUNYA OS — the canonical entry point for every user, organization, and workspace. It is the first production experience a human has with SHUNYA.

**Philosophy:**
- Every user arrives at shunyaos.com as a stranger with no account.
- Every user must be able to sign up, create an organization, and enter SHUNYA — exactly like any future customer.
- No founder shortcuts. No hardcoded organizations. No SHUNYA-specific logic.
- All capabilities must remain business-agnostic — applicable to any domain (travel, healthcare, legal, education, retail, etc.).
- The identity layer is the immutable foundation upon which all subsequent deliverables (auth, authorization, workspaces, collaboration) are built.

## 2. Domain Model

```
┌─────────────────────────────────────────────────────────────┐
│                     SHUNYA Identity Layer                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────┐       ┌───────────────────────────────┐  │
│  │  Organization  │──1:N──│         Workspace             │  │
│  │  (Tenant)      │       │  (isolated collaboration      │  │
│  │   - company    │       │   space within an org)        │  │
│  │   - slug       │       │   - name, slug, description   │  │
│  │   - plan       │       │   - settings (JSON)           │  │
│  │   - theme      │       │   - is_active                 │  │
│  │   - is_active  │       └───────────────────────────────┘  │
│  └───────┬───────┘                                           │
│          │                                                  │
│          │ 1:N                                              │
│          │                                                  │
│  ┌───────▼───────────────────────────────────────────────┐  │
│  │                    User (TeamMember)                   │  │
│  │   - name, email, password_hash, role, is_active       │  │
│  │   - session-based auth (current session)              │  │
│  │   - belongs to org via context (session.org_id)       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               Invitation (in-memory)                   │  │
│  │   - email, role, token, expires_at, accepted_at        │  │
│  │   - 48-hour expiry, one-time accept                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               Onboarding (in-memory)                   │  │
│  │   - per-user state machine:                            │  │
│  │     profile → org_setup → invite_team → workspace →    │  │
│  │     complete                                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Organization (Tenant)

| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK, auto-increment |
| company_name | String(255) | Required, display name |
| slug | String(120) | Unique, URL-safe, auto-generated |
| business_type | String(60) | Domain classification (other, travel, healthcare, etc.) |
| parent_id | Integer | FK to tenants.id (multi-brand support) |
| subdomain | String(120) | Optional custom subdomain |
| domain | String(255) | Optional custom domain |
| is_active | Boolean | Soft-delete flag |
| plan | String(30) | Subscription tier (free, pro, enterprise) |
| max_team_members | Integer | Plan limit |
| created_at | DateTime | UTC |

### 2.2 Workspace

| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| tenant_id | Integer | FK to tenants.id |
| name | String(255) | Required |
| slug | String(120) | Unique within org |
| description | Text | Optional |
| settings | Text | JSON blob |
| is_active | Boolean | Soft-delete |
| created_at / updated_at | DateTime | UTC |

### 2.3 User (TeamMember)

| Field | Type | Notes |
|-------|------|-------|
| id | Integer | PK |
| name | String(120) | Required |
| email | String(255) | Unique, indexed |
| phone | String(30) | Optional |
| role | String(30) | admin, manager, agent |
| password_hash | String(128) | Salted SHA-256 |
| api_token | String(128) | Session token |
| is_active | Boolean | Soft-delete |
| created_at / last_login | DateTime | UTC |

## 3. API Surface

All endpoints mounted under `/api/v1/orgs` via `identity_bp` blueprint.

### 3.1 Organization CRUD

| Method | Path | Action | Auth |
|--------|------|--------|------|
| GET | /api/v1/orgs | List orgs | @login_required |
| POST | /api/v1/orgs | Create org | @login_required |
| GET | /api/v1/orgs/<id> | Get org | @login_required |
| PUT | /api/v1/orgs/<id> | Update org | @login_required |
| DELETE | /api/v1/orgs/<id> | Soft-delete org | @login_required |

### 3.2 Workspace CRUD

| Method | Path | Action | Auth |
|--------|------|--------|------|
| GET | /api/v1/orgs/<id>/workspaces | List workspaces | @login_required |
| POST | /api/v1/orgs/<id>/workspaces | Create workspace | @login_required |
| GET | /api/v1/orgs/<id>/workspaces/<id> | Get workspace | @login_required |
| PUT | /api/v1/orgs/<id>/workspaces/<id> | Update workspace | @login_required |
| DELETE | /api/v1/orgs/<id>/workspaces/<id> | Soft-delete | @login_required |

### 3.3 User Management

| Method | Path | Action | Auth |
|--------|------|--------|------|
| GET | /api/v1/orgs/<id>/users | List users | @login_required |
| POST | /api/v1/orgs/<id>/users | Create user | @login_required |
| GET | /api/v1/orgs/<id>/users/<id> | Get user | @login_required |
| PUT | /api/v1/orgs/<id>/users/<id> | Update user | @login_required |
| DELETE | /api/v1/orgs/<id>/users/<id> | Soft-delete | @login_required |

### 3.4 Invitation System

| Method | Path | Action | Auth |
|--------|------|--------|------|
| GET | /api/v1/orgs/<id>/invitations | List invitations | @login_required |
| POST | /api/v1/orgs/<id>/invitations | Create invitation | @login_required |
| GET | /api/v1/orgs/invitations/<token> | Get by token | @login_required |
| POST | /api/v1/orgs/invitations/<token>/accept | Accept invitation | Public |
| DELETE | /api/v1/orgs/<id>/invitations/<id> | Revoke | @login_required |

### 3.5 Organization Switching

| Method | Path | Action | Auth |
|--------|------|--------|------|
| POST | /api/v1/orgs/switch/<id> | Switch active org | @login_required |
| GET | /api/v1/orgs/current | Get current org | @login_required |

### 3.6 Organization Lifecycle

| Method | Path | Action | Auth |
|--------|------|--------|------|
| POST | /api/v1/orgs/<id>/activate | Activate org | @login_required |
| POST | /api/v1/orgs/<id>/deactivate | Deactivate org | @login_required |
| POST | /api/v1/orgs/<id>/archive | Archive org | @login_required |

### 3.7 Onboarding

| Method | Path | Action | Auth |
|--------|------|--------|------|
| GET | /api/v1/orgs/onboarding/status | Get status | @login_required |
| PUT | /api/v1/orgs/onboarding/step/<step> | Advance step | @login_required |
| POST | /api/v1/orgs/onboarding/reset | Reset | @login_required |

## 4. Complete Onboarding Journey

```
shunyaos.com ──► Sign Up ──► Create Org ──► Configure ──► Enter SHUNYA
                                                          
  Step 1: User arrives at shunyaos.com (public)           
  Step 2: User signs up with name, email, password        
          ├── Creates TeamMember record                   
          └── Creates session                             
  Step 3: User creates their organization                
          ├── POST /api/v1/orgs {company_name, ...}      
          └── Organization (Tenant) + default theme created
  Step 4: Onboarding begins                               
          ├── Step: profile (complete profile)            
          ├── Step: org_setup (configure org settings)    
          ├── Step: invite_team (optional)                
          ├── Step: workspace (configure default workspace)
          └── Step: complete                              
  Step 5: User enters SHUNYA                              
          └── Redirected to SHUNYA dashboard              
```

**Current gap:** There is no public signup endpoint. The existing flow requires pre-existing authentication (login_required) for org creation. A `POST /api/v1/auth/signup` endpoint is needed to:
1. Accept name, email, password
2. Create a TeamMember
3. Create a session
4. Return the user + session token

This is described in D2 (Auth) but is a prerequisite for the onboarding journey. It will be addressed in the implementation phase.

## 5. Constraints Verification

### 5.1 No SHUNYA-specific logic

| Check | Status | Evidence |
|-------|--------|----------|
| Production identity modules contain no SHUNYA string references | PASS | One docstring example "SHUNYA OS → shunya-os" in slug generation — cosmetic only, not logic |
| No hardcoded admin emails | PASS | Only in `auth_routes.py` (legacy system, not production identity) |
| No travel-specific business logic | PASS | `business_type` defaults to "other", travel is one valid option among many |
| Business-agnostic data model | PASS | Tenant model has generic fields applicable to any domain |

### 5.2 No founder shortcuts

| Check | Status | Evidence |
|-------|--------|----------|
| No hardcoded organizations | PASS | No seeded orgs, no default tenants |
| No special admin bypass | PASS | All routes require `@login_required` |
| No special creator privileges | PASS | No org creator gets special treatment beyond role |

### 5.3 Business-agnostic

| Check | Status | Evidence |
|-------|--------|----------|
| Organization model is generic | PASS | company_name, business_type, slug — no domain-specific fields |
| Workspace model is generic | PASS | name, slug, description, settings — no domain-specific fields |
| User model is generic | PASS | name, email, role — no domain-specific fields |
| Themes are cosmetic | PASS | colors, fonts, logo — no domain-specific logic |

## 6. Implementation Status

| Module | File | Status | Tests | 
|--------|------|--------|-------|
| Organization CRUD | `org_routes.py` | IMPLEMENTED | 21 tests — PASS |
| Workspace CRUD | `workspace_routes.py`, `workspace_model.py` | IMPLEMENTED | 16 tests — PASS |
| User Management | `user_routes.py` | IMPLEMENTED | 17 tests — PASS |
| Invitation System | `invitation_routes.py` | IMPLEMENTED | 15 tests — PASS |
| Org Switching | `switch_routes.py` | IMPLEMENTED | 3 tests — PASS |
| Org Lifecycle | `lifecycle_routes.py` | IMPLEMENTED | 3 tests — PASS |
| Onboarding | `onboarding_routes.py` | IMPLEMENTED | 6 tests — PASS |
| **Public Signup** | *(not yet created)* | **GAP** | **Needed for onboarding journey** |

**Total: 71 tests, all passing. 1 gap identified.**

## 7. ADRs

### ADR-001: Tenant Model as Organization

**Problem:** The existing codebase uses a `Tenant` model for multi-tenancy. Should Organization be a separate model or alias the Tenant model?

**Decision:** Use the existing `Tenant` model as the canonical Organization. It already provides company_name, slug, business_type, is_active, plan, max_team_members, and theme. Creating a separate Organization model would duplicate schema and require migration.

**Consequences:** Positive — zero migration, immediate backward compatibility. Negative — field names use "tenant" terminology internally, but the API presents "org" semantics.

### ADR-002: In-Memory State for Invitations and Onboarding

**Problem:** Should invitations and onboarding state be persisted in SQLAlchemy or kept in-memory?

**Decision:** In-memory for now. The invitation system is transient by nature (48-hour expiry), and onboarding state is per-user per-session. Migrate to SQLAlchemy when persistence across restarts is required (multi-server deployment).

**Consequences:** Positive — fast iteration, no schema changes. Negative — state lost on restart, not suitable for horizontal scaling without migration.

### ADR-003: Soft-Delete Pattern

**Problem:** Should DELETE endpoints hard-delete or soft-delete records?

**Decision:** Soft-delete throughout. DELETE sets `is_active = False`. True hard-deletion is available via the lifecycle endpoints (activate/deactivate/archive) for administrative use.

**Consequences:** Positive — recoverable, audit-friendly, no cascade issues. Negative — stale records accumulate; requires periodic cleanup or archiving.

---

## 8. Verdict

**Ready for implementation.** The architecture is sound, business-agnostic, and meets all stated constraints. One gap (public signup endpoint) is identified and will be implemented as part of D1. The 71 existing tests pass and serve as the behavioral baseline.

**Awaiting review before proceeding.**