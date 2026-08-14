# SHUNYA — Launch Blocker Register

**Date:** 2026-08-14  
**Status:** TRUTH ONLY — no implementation yet

---

## SEVERITY DEFINITIONS

| Level | Meaning |
|-------|---------|
| P0 | Cannot launch. Blocks core user journey. |
| P1 | Must fix before founder acceptance. Material product defect. |
| P2 | Must fix before public launch. Important but founder acceptance can continue if justified. |
| P3 | Maintenance. Does not represent missing foundational capability. |
| P4 | Growth. Future enhancement beyond launch scope. |

---

## P0 — CANNOT LAUNCH

| ID | Area | Finding | User Impact | Root Cause | Required Action |
|----|------|---------|-------------|------------|-----------------|
| LB-001 | PWA | icon-192.png, icon-512.png, favicon.ico served as 404. Files absent from dist after Vite rebuild. | PWA install fails. Browser tab shows no icon. manifest.json references broken URLs. | Icons were generated ephemerally, not committed to git or placed in frontend/public/. Vite clean rebuild deletes them. | Place icon files in `frontend/public/` so Vite copies them to dist on build. Regenerate icons. |
| LB-002 | Age/safety | No age verification or content safety policy implemented. | Cannot distinguish minors from adults. No policy gates for sensitive content. Model could be manipulated to bypass policy. | Feature never implemented. | Implement age/safety governance module. Integrate with inference_governance. |
| LB-003 | Signup | No signup link/button in login UI. `Signup` component exists in code but is unreachable. | New users cannot create accounts — there is no path to signup. Must use pre-created demo account. | Signup link not wired into login page UI. | Add "Create account" link to login page. Wire to Signup component. |
| LB-004 | nginx config | 4 server blocks including duplicate HTTPS with different cert (shunyaos.com-0001). Duplicate block lacks security headers. | Some requests may be served by the unhardened block. Cert renewal may update wrong block. | Certbot created duplicate during renewal. Consolidated config ready but not deployed. | Deploy consolidated nginx config. Verify single HTTPS block with correct cert. |
| LB-005 | Icons 404 | /icon-192.png, /icon-512.png, /favicon.ico → HTTP 404 on live and local. | All three icon endpoints return 404. PWA not installable; browser tab icon missing. | Files deleted on frontend rebuild. Routes exist but files don't. | See LB-001. |

## P1 — MUST FIX BEFORE FOUNDER ACCEPTANCE

| ID | Area | Finding | User Impact | Root Cause | Required Action |
|----|------|---------|-------------|------------|-----------------|
| LB-006 | Object stores | 4 independent object stores with 0 ID overlap. sh_objects(600), founder_objects(508), objects(29), canonical_objects(2). | Objects created in one store are invisible in another. Onboarding creates in sh_objects (fixed), but workspace uses sh_objects. | Historical architecture divergence. Each subsystem created its own store. | Prove or establish ONE canonical production object store. Deprecate or alias others. |
| LB-007 | Evidence chain | evidence_records had 0 rows. log_evidence wrote to act_execution_logs (wrong table) with FK violation. **NOW FIXED (6 rows)** but fix not deployed to production. | AI evidence was silently lost. Execution with evidence gate would block if evidence_records empty. | log_evidence wrote to wrong table with failing FK. | Deploy the evidence fix (already applied in working tree). |
| LB-008 | AuthMemberRole empty | auth_member_roles table has 0 rows. All 71 team_members are role=admin. | No permission differentiation. Every user has admin access. Authz system never exercised with non-admin. | AuthMemberRole model exists but no code path populates it during user creation. | Wire OrgMember creation to AuthMemberRole assignment. |
| LB-009 | Session cookie | **FIXED** — Secure, HttpOnly, SameSite=Lax now set. But fix not deployed to live. | Previously missing Secure/SameSite made cookies vulnerable. | Flask default config doesn't set these. | Deploy the session cookie fix (already applied in working tree). |
| LB-010 | Signup UI missing | No way for new user to create account from login page. | Launch requires users to create accounts. No path except existing demo credentials. | Signup component wired to route but not linked from login UI. | Add Create Account link to login form. |
| LB-011 | Environment | **FIXED** — .env now production. But live deployment must be verified after gunicorn restart. | Was reporting "development" in production. | .env had SHUNYA_ENVIRONMENT=development. | Already fixed. Verify /health reports production. |
| LB-012 | Login 500 | **FIXED** — url_for("serve_index") → url_for("main.index"). GET /login now 302 instead of 500. | Was P0 blocker. Now resolved. | Endpoint renamed from serve_index to index. | Already fixed. Verify GET /login returns 302. |

## P2 — MUST FIX BEFORE PUBLIC LAUNCH

| ID | Area | Finding | User Impact | Root Cause | Required Action |
|----|------|---------|-------------|------------|-----------------|
| LB-013 | Migration 0007 | alembic at 0006. 0007_fda22_auth_extended.py unapplied. | auth_extended tables (service_accounts, delegations, tenant_policies) may have incorrect schema. | Migration never run. db.create_all() creates tables but may miss schema changes. | Review 0007 migration. Apply if safe. |
| LB-014 | Backup restore | shunya DB user lacks CREATEDB. Cannot perform restore to new database. | Recovery dependent on postgres superuser credentials. No tested restore procedure. | Non-superuser DB role. | Document exact restore procedure. Test with postgres user or establish equivalent recovery. |
| LB-015 | nginx install | Consolidated config file exists but not deployed. | nginx still using duplicate HTTPS blocks. | sudo access required but password-protected. | Install config. |
| LB-016 | Search performance | ~1.39s baseline. Web search adds DuckDuckGo latency. | Search results perceptibly delayed. | DuckDuckGo API call is synchronous. | Add result caching or async loading. |
| LB-017 | Object listing performance | ~1.16s for 508 objects. | Workspace object listing takes >1s. | No pagination, full table scan. | Add pagination to object listing API. |
| LB-018 | Cache-Control headers | No Cache-Control on /, /assets/* responses. | Browser cannot cache frontend assets; every page load re-fetches entire bundle. | Flask default doesn't set Cache-Control. | Add Cache-Control headers for static assets. |
| LB-019 | OAuth client IDs | Google/GitHub OAuth flows exist but no client IDs configured. | OAuth buttons non-functional. | .env missing GOOGLE_CLIENT_ID, GITHUB_CLIENT_ID. | Register OAuth apps, add client IDs to .env. |
| LB-020 | Semantic HTML | Login page uses "Tap to continue" button. Workspace uses div-based layouts. | Screen reader users may miss content. | SPA uses semantic heading fix (applied) but deeper ARIA may be incomplete. | ARIA audit for workspace components. |
| LB-021 | Workspace accessibility | Workspace panels (commitment, people, timeline) not screen-reader verified. | Keyboard-only and screen reader users may have degraded experience. | Accessibility was not verified for workspace UI. | Browser QA for workspace with screen reader. |
| LB-022 | tenant_id missing on sh_objects | sh_objects and founder_objects lack tenant_id column. | Cannot natively partition objects by tenant. Cross-tenant queries possible. | Legacy schema design. Objects use workspace_id/space_id instead. | Add tenant_id to sh_objects. Backfill. |

## P3 — MAINTENANCE

| ID | Area | Finding | User Impact | Root Cause | Required Action |
|----|------|---------|-------------|------------|-----------------|
| LB-023 | Empty canonical tables | person_identities(0), customers(0), document_records(0), commitments(0), decision_traces(0). | No data loss. Canonical tables are empty but working code paths exist. | Features not exercised end-to-end. Data emptiness, not broken architecture. | No action required. Tables populate when features used. |
| LB-024 | Model telemetry | model_runs(0). AI chat logs to evidence_records instead of model_runs. | No LLM telemetry tracking. | Two parallel logging systems. | Consolidate into model_runs or mark model_runs as legacy. |
| LB-025 | Audit store fragmentation | 6 audit tables. Only user_activity_logs(287) populated. | Audit data scattered. | Each subsystem created own audit store. | Consolidate audit into single canonical store. |
| LB-026 | Outcome store duplication | outcomes(5), sh_outcomes(3). | Outcome data split across tables. | Historical divergence. | Consolidate outcomes. |
| LB-027 | OpenAI/Anthropic keys missing | 2 of 9 providers not configured. | Those providers unavailable. 7 of 9 providers working. | API keys not in .env. | Add keys if those providers are needed. P4 for now. |
| LB-028 | model_runs telemetry | 0 rows. AI chat bypasses LLMRuntimeService. | No AI request telemetry. | Two separate code paths for AI. | Route AI chat through LLMRuntimeService or accept current logging. |
| LB-029 | PersonIdentity not populated | PersonIdentity(0). team_members(71) and shunya_identities(35) used instead. | Canonical identity model empty but working alternative exists. | PersonIdentity never wired into auth flow. | Wire PersonIdentity into user creation. |
| LB-030 | customers table orphan | `customers` table (0 rows) has no model defining it. CRM uses `customer` (singular, 4 rows). | No user impact. The `customer` table works. | Model defines __tablename__="customer" (singular). "customers" (plural) is a legacy orphan. | Drop customers table. Ensure all code uses correct table name. |

## P4 — GROWTH

| ID | Area | Finding | Required Action |
|----|------|---------|-----------------|
| LB-031 | Search caching | ~1.39s synchronous search | Add result caching layer |
| LB-032 | Object pagination | ~1.16s full-table scan | Add pagination to object listing |
| LB-033 | PWA features | manifest.json references missing icons | Generate and serve icons |
| LB-034 | CI/CD pipeline | No automated deploy pipeline | Set up CI/CD |
| LB-035 | Multi-region | Single-region deployment | Growth concern |
| LB-036 | Rate limit tuning | Default 200/day may be low | Tune based on expected traffic |

---

## SUMMARY

| Severity | Count | Action |
|----------|-------|--------|
| P0 | 5 | Cannot launch without fixing |
| P1 | 7 | Must fix before founder acceptance |
| P2 | 10 | Must fix before public launch |
| P3 | 8 | Maintenance items |
| P4 | 6 | Growth items |
| **Total** | **36** | |

## CORRECTION FROM EARLIER ANALYSIS

The previous FDA36 report listed "6 blockers." The actual truth audit reveals **36 findings**, of which **5 are P0 (cannot launch)** and **7 are P1 (must fix before founder acceptance)**. The remaining 24 are P2-P4.

This confirms the founder's correction: the "6 blockers" assessment was incomplete.

---

*End of Launch Blocker Register*