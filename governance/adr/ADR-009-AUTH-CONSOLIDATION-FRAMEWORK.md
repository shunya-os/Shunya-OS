# ADR-009: Evidence-Based Auth Consolidation Framework

**Class:** Product/Experience
**Status:** Accepted
**Date:** 2026-07-28
**Author:** Hermes Agent (per Founder directive)
**Supersedes:** (none)
**Superseded by:** (none)

**Approval Authority:**
- If Product/Experience: Founder

**Related Constitutional Directives:**
- Product Constitution (14) — §2 (Binding Authority), §4 (Universal Knowledge Routing)
- Addendum — Evidence-Based Consolidation & Canonical Selection (2026-07-28)
- ADR-008 — Capability Audit & Evidence Preservation

---

## Context

The SHUNYA codebase has two parallel authentication systems:
1. **Legacy auth** (`app/auth_routes.py`) — `TeamMember` model, integer IDs, basic login/register/logout
2. **Canonical auth** (`app/production/auth/`) — `SHUNYAIdentityModel`, string IDs (sid_xxx), MFA, email verification, password reset, session management, device management

Both are registered in the app factory and share the `auth_bp` blueprint name. The auth middleware at `app/__init__.py` (line 425+) checks both integer and string user IDs.

The initial consolidation analysis proposed deprecating legacy auth. However, evidence showed that `TeamMember` is consumed by 15+ routes in `app/routes.py` for permission checks and user lookups. A simple deprecation would break those routes.

---

## Evidence Reviewed

| Evidence | Source | What It Proves |
|----------|--------|----------------|
| Legacy auth routes | `app/auth_routes.py` — Blueprint `auth_bp` | Login, register, logout with integer IDs |
| Canonical auth routes | `app/production/auth/` — 6 route files on `auth_bp` | MFA, email verification, password reset, session management, device management |
| Auth model `TeamMember` | `app/auth.py` — integer ID model | Used by 15+ routes in `app/routes.py` for permission checks |
| Auth model `SHUNYAIdentityModel` | `app/production/identity_repository.py` — string IDs | Canonical OS identity model |
| Auth middleware | `app/__init__.py` lines 425-460 | Checks both integer and string user IDs |
| Blueprint registration | `app/__init__.py` lines 345-355 | Both auth systems registered on same blueprint |

---

## Options Considered

### Option 1: Deprecate legacy auth immediately

**Pros:**
- Single auth system
- Cleaner codebase

**Cons:**
- Breaks 15+ routes that depend on `TeamMember`
- No migration path for existing user sessions
- Rollback would be destructive

**Evidence for:** `TeamMember` is referenced by `app/routes.py` in permissions checks at lines 425-460.

### Option 2: Parallel coexistence with redirects (CHOSEN)

**Pros:**
- All existing routes continue to work
- No data migration needed immediately
- Users can be migrated incrementally
- Rollback is trivial (remove redirects)

**Cons:**
- Two auth systems remain in codebase temporarily
- Engineers need to know which system a route uses

**Evidence for:** Both systems already coexist without route conflicts (different URL prefixes: `/auth/` vs `/api/v1/auth/`).

### Option 3: Parallel coexistence with no changes

**Pros:**
- Zero risk of breaking anything

**Cons:**
- Founder sees two different auth experiences
- No canonical path for new capabilities (MFA, session management)

---

## Decision

**Option 2 — Parallel coexistence with redirects.** Both auth systems remain in place. The SPA login page will call the canonical auth API. Legacy routes that render Jinja2 login templates will redirect to the SPA login. The `TeamMember` permission checks remain intact until those routes are migrated to the canonical identity model.

This is NOT a deprecation decision. It is a deferral — the legacy auth system cannot be removed until every route that consumes `TeamMember` is migrated. A future ADR will govern that migration.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TeamMember consumers not tracked | Medium | High | Inventory every route that uses `TeamMember` before migration |
| Session confusion for users with both account types | Low | Medium | Unified session handling via auth middleware |
| New developers implement new auth on legacy system | Medium | Medium | Engineering governance: new auth uses canonical system |

---

## Migration Plan

1. Wire SPA login to canonical auth API (no code change — SPA already has login component)
2. Add redirect from legacy login pages to SPA login
3. Inventory all 15+ routes consuming `TeamMember` (future ADR)
4. Migrate routes one at a time to canonical identity
5. Only after no consumer depends on legacy auth, remove legacy routes

---

## Rollback Plan

1. Remove SPA login → canonical auth wiring
2. Remove legacy route redirects
3. Both auth systems remain intact — rollback is removing redirects

---

## Consequences

### Positive

- Existing routes continue to work
- New capabilities (MFA, session management, password reset) are available
- Redirects guide Founders to the canonical surface without breaking bookmarks

### Negative

- Two auth systems remain in codebase
- Migration requires tracking all `TeamMember` consumers

### Neutral

- No data migration required
- Both systems coexist today without conflicts

---

## Compliance

### Constitutional Principles Affected

- **Article 2 — Human Agency (02):** Auth is a consent mechanism. Canonical auth provides more consent control (session management, device revocation).
- **§12 — Universal Organization Adaptation (14):** Canonical auth supports multi-org identity, necessary for organization adaptation.

### Engineering Constitution Articles Affected

- **No regression without evidence:** Legacy auth is preserved because removing it has identified risk to 15+ routes.

---

## Verification

- [ ] SPA login calls canonical auth API
- [ ] Legacy login pages redirect to SPA login
- [ ] All 15+ routes using `TeamMember` continue to pass auth checks
- [ ] MFA configuration endpoint works (if MFA enabled)
- [ ] Password reset flow works end-to-end

---

## References

- [Legacy auth source](/home/shunya-deploy/shunya_os/app/auth_routes.py)
- [Canonical auth source](/home/shunya-deploy/shunya_os/app/production/auth/)
- [Auth middleware](/home/shunya-deploy/shunya_os/app/__init__.py) — lines 345-355, 425-460
- [Canonical Capability Registry](/home/shunya-deploy/shunya_os/governance/capability-registry.md) — entries: user-login, user-registration, mfa, password-reset, email-verification, session-management