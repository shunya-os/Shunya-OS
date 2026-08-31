# M2C.5R Zero-Gap Register — Discovery Audit

**Date:** 2026-08-31  
**Local SHA:** 16a73ce  
**Production SHA:** 6986950  
**Origin/master SHA:** bdcf942  

---

## Core Findings

### Deployment Architecture — RED
- Local HEAD (16a73ce) ≠ Production (6986950) ≠ Origin/master (bdcf942)
- 25 commits ahead of origin/master (never pushed)
- Production SHA (6986950) has NO CI run — cannot certify provenance
- No staging/pre-production environment
- deploy.sh robust but SHA mismatch proves deployment divergence

### CI/CD — AMBER
- Last CI runs (3) were green on origin/master (bdcf942, 6a6024f, 09b735a)
- CI failure on SHA 90d0cd9: Frontend typecheck (step 12) is the only failure
- Current HEAD (16a73ce) has never run CI
- CI workflow uses correct canonical pattern (needs: test → deploy, serialized)
- Deploy requires DEPLOY_HOST/SSH secrets — not verified if configured in GitHub org

### Password Sign-In — RED (needs fix)
- Demo user `shunyaosapp@gmail.com` (Nishesh, founder role, id=184) EXISTS in DB
- Password `admin123` (from documentation) returns 401 — stale/rotated
- **Action:** Reset password via app.set_password(), never expose plaintext
- `/login/password` endpoint returns 401 on wrong credentials (correct safe failure)
- `/api/v1/founder/signin` exists and expects same credentials

### Google OAuth — BLOCKED_EXTERNAL
- Code in `app/auth_oauth.py` is complete (362 lines — state/CSRF/identity resolution/session)
- GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are NOT configured in .env
- `/api/v1/auth/google/login` returns 501 "Google OAuth not configured"
- No gcloud CLI available; only local-dev "installed" type credentials exist at /home/shunya-deploy/credentials/credentials.json (redirect URI: http://localhost — unsuitable for production web)
- **Requires:** Founder to provision a Google Cloud Web OAuth 2.0 client, supply client ID/secret via secure channel

### Forgot Password — RED (broken delivery)
- Code for forgot-password and reset-password routes IS complete (stateful, rate-limited, safe)
- Reset tokens stored as plaintext in `password_reset_tokens` table (TOKEN clearly visible)
- Token has 1-hour expiry, used flag, user_id FK to team_members
- **CRITICAL:** `email_core.py` sends via SMTP (EMAIL_USER/EMAIL_PASSWORD) — which are NOT SET
- Returns `{"success": true, "message": "If an account exists..."}` even when email only logs
- RESEND_API_KEY exists in .env but `pip install resend` is NOT installed — nothing uses it
- **Result:** Frontend shows "Reset link sent!" but NO email ever goes out — false capability

### Password Reset — AMBER (untested)
- `/api/v1/auth/reset-password` endpoint exists and is fully coded
- Validates token expiry, uses flag, min password length
- Calls member.set_password() and invalidates sessions
- Cannot test live because forgot-password email never arrives

### Identity Integrity — AMBER
- Demo user has Person ID (389) and identity_id set
- Multiple test accounts exist (10 others): test-founder, test_m2b, journey-test, admin@shunyaos.com, etc.
- Per directive: "one and only one public demo user" — test users may be acceptable for dev but could be accidental exposure vectors
- Patrick Sarracin issue (from directive §9) — need to check unresolved identities

### Object Convergence — RED
- 85 records in sh_uop_objects confirmed
- Source→target mapping not established; primary keys, provenance unknown
- Random UUID migration problem identified in prior report — architectural defect

### Migration Idempotency — MISSING
- No migration engine with: deterministic source identity, idempotency, dry-run, preflight, backup, transaction/rollback, mutation ledger, reconciliation, failure recovery, tenant provenance, collision detection
- Migration engine is a design artifact, not implemented

### Tenant/Organization — RED
- 32 tenants (legacy) vs 2 organizations (canonical)
- Tenant is "real production dependency footprint" while Organization is "partially migrated"
- No definitive ownership/migration strategy enforced through schema/FK/repositories/services/APIs/auth/jobs/tests/integrations/migrations
- Current local changes add `plan` column to Organization — minor feature addition while architecturally the dual authority remains

### R9 Automated Tests — MISSING
- "Design specification" only — not real tests
- Required tests: missing tenant, invalid tenant, duplicate source ID, duplicate canonical ID, ambiguous identity, false-positive Person, database failure, partial migration, interrupted migration, rollback, retry, double execution, triple execution, dry-run, backup, cross-tenant access, cross-tenant write, authorization failure

### API Completeness — PARTIAL
- Person, Identity, Relationship search/update/delete capabilities classified as "missing or partial" in prior report
- Not every product-critical entity has a defined Create/Read/Update/Delete/Archive/Search/Permission/Isolation/Validation/Error/Audit capability matrix

### Security — RED
- Past credentials may remain in Hermes delegation cache files (not yet audited here)
- Reset tokens stored as plaintext (not hashed) in password_reset_tokens table
- RESEND_API_KEY exposed in .env (though .env is gitignored, it's readable on filesystem)
- No credential rotation audit performed yet

### Email Delivery — MISSING
- EMAIL_PROVIDER=resend and RESEND_API_KEY exist but `resend` Python package NOT installed
- email_core.py uses only SMTP (needs EMAIL_USER/EMAIL_PASSWORD) — neither set
- forgot-password, verification emails, onboarding emails all silently log instead of delivering
- Wire Resend into email_core OR configure SMTP credentials

### UX Constitutional Compliance — UNKNOWN
- Not yet browser-tested on current state
- Playwright available (Python + node_module)
- Scripts exist in .hermes/scratch/ for browser testing

---

## 25-Gate Certification Matrix (Initial Assessment)

| GATE | STATUS | BLOCKER |
|------|--------|---------|
| M2C.5R forensic truth | FAIL | See above — SHA mismatch, migration gaps, broken email delivery |
| Canonical ownership | FAIL | No definitive ownership map for objects/tenant/identity |
| Tenant integrity | FAIL | 32 tenants vs 2 orgs, no enforced strategy |
| Object convergence | FAIL | 85 unapproved artifacts, no source mapping |
| Migration idempotency | MISSING | Not implemented |
| Dry-run | MISSING | Not implemented |
| Backup verification | UNKNOWN | deploy.sh has backup step but not verified |
| Rollback | MISSING | Not implemented |
| Failure tests | MISSING | Not implemented |
| Identity integrity | AMBER | Demo user exists, multiple test users present |
| API completeness | PARTIAL | Person/Identity/Relationship gaps documented |
| Tenant isolation | FAIL | Dual Tenant/Organization authority |
| Security | FAIL | Plaintext reset tokens, credential exposure audit pending |
| CI | FAIL | HEAD has no CI run; prior typecheck failure |
| CD | FAIL | Production SHA ≠ Certified SHA |
| Runtime SHA | FAIL | 6986950 (prod) ≠ 16a73ce (certified local) |
| Staging/pre-prod | MISSING | No staging environment |
| Demo password login | FAIL | admin123 is stale, password needs reset |
| Google login | FAIL | 501 — not configured, needs founder action |
| Forgot password | FAIL | Email never actually sent — only logged |
| Password reset | UNVERIFIED | Code exists but untestable without email delivery |
| Logout | UNKNOWN | Not tested |
| Frontend acceptance | UNKNOWN | Not browser-tested |
| Responsive acceptance | UNKNOWN | Not browser-tested |
| UX constitutional compliance | UNKNOWN | Not verified |
| Git cleanliness | FAIL | 4 modified files, 25 commits ahead of remote, untracked M2C5R docs |
| Production verification | FAIL | SHA mismatch, deployment divergence, no staging |

---

## Execution Priority

**Immediate (NO founder dependency):**
1. Fix Git state — commit uncommitted changes, push to origin/master
2. Fix CI — reproduce & fix frontend typecheck failure
3. Push current HEAD → CI → green
4. Reset demo user password securely via app.set_password()
5. Fix email delivery — wire Resend into email_core (package + API call)
6. Verify demo password login → forgot password → email sent → reset → login cycle
7. Build migration engine skeleton (idempotency, dry-run, rollback)
8. Begin object convergence (source→target mapping)
9. R9 automated tests

**Founder-dependent:**
- Google OAuth — needs web client credentials from Google Cloud Console
- Production deployment — needs DEPLOY_HOST/SSH secrets configured in GitHub
- Staging environment provisioning
- Google Cloud Project for OAuth redirect URIs

**Verification required after each fix:**
- Every fix verified via real HTTP (curl), not just "tests pass"
- Browser acceptance on shunyaos.com (or local server)
- SHA provenance verified end-to-end