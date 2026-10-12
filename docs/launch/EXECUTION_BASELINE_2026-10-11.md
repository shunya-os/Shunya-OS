# SHUNYA — EXECUTION BASELINE (MASTER DIRECTIVE, 2026-10-11)

**Timestamp:** 2026-10-11 ~22:00 CEST (UTC+02)
**Directive:** SHUNYA MASTER EXECUTION DIRECTIVE — CLOSE ALL REMAINING GAPS, CERTIFY THE PRODUCT, PREPARE FOR PUBLIC LAUNCH
**Prepared by:** Hermes (execution agent) — baseline capture before Wave 0 edits.

---

## 1. GIT TRUTH

| Item | Value |
|------|-------|
| Branch | master |
| HEAD | c1db5367000e6e803758c9cad4998e3ed615268d |
| origin/master | c1db536 (in sync) |
| Working tree | CLEAN (no modified/untracked) |
| Latest CI run on HEAD | 38166859810 — SUCCESS (test + deploy), deployed 2026-10-11T19:36:31Z |
| Historical runs | 38153420213 (6b5767f) success; 38144386795 (3a2d3d3) success; 38141992443 (c6b0fa0) success |

### Commit chain (most recent first)

| SHA | Type | Content |
|-----|------|---------|
| c1db536 | docs | master gap & pending register (superset: blockers, session gaps, live defects, CI hygiene, founder decisions) |
| 6b5767f | docs | 100-gap register — 5-perspective forensic sweep |
| 3a2d3d3 | docs | certify LB-002 (safety governance) on c6b0fa0 — CI 38141992443 + production runtime proof |
| c6b0fa0 | **code** | certified code-fix: safety governance, cross-tenant read isolation, HTTPS contract, doc-500 journey (+2,160/−258, 24 files) |
| a57b7a1 | code | AI Resident Panel canonical ask endpoint |
| 6b9c0d3 | code | frontend-vs-backend SHA contract (CI FAILURE on this commit, fixed by a57b7a1) |

**Conclusion:** the last three commits are documentation-only. The last certified CODE state is c6b0fa0 (plus docs layered on top). Production is NOT behind master; prod == master == c1db536.

## 2. PRODUCTION TRUTH (verified live)

- Public health (https://shunyaos.com/health): `status=ok`, `database=connected`, `environment=production`
- git_commit / backend_release_sha / frontend_release_sha / build_id = c1db536 (all matching)
- release_type=CI_CERTIFIED, release_health_verified=true, frontend_release_verified=true, frontend_dist_mode=immutable_release
- Services: shunya (systemd, active), nginx (active), postgresql (active), redis (active)
- Gunicorn: 3 workers, gthread 8 threads, 127.0.0.1:5001, wsgi:app
- Listeners: 0.0.0.0:443, 0.0.0.0:80, 127.0.0.1:5001, 127.0.0.1:5432

## 3. DATABASE / MIGRATION TRUTH

| Item | Value |
|------|-------|
| DB name | shunya_os (127.0.0.1:5432) |
| Migration head (code) | r6b28_age_verification_fields |
| Migration head (live DB, alembic_version) | r6b28_age_verification_fields — MATCH |
| Live table count | 220 |
| **L1 defect** | `ai_execution_records` EXISTS as model (app/observability/models.py:20) but NO migration creates it; live DB lacks the table → /api/v1/analytics/dashboard raises relation-does-not-exist → HTTP 500 |

## 4. CI / RELEASE PROCESS

- Workflow: `.github/workflows/ci.yml` — one pipeline: `test` (compile → verification tests → canonical pytest suite with sqlite/redis/pg services → milestone validation → npm ci → eslint zero-new-warning → tsc → vitest → production build → pip-audit → committed-.env secret scan) then `deploy` (needs test; master/main only; concurrency `production-deploy` no-cancel).
- Deploy: SSH → `deploy.sh production <sha>` → local health SHA+release_type check (bounded retry, latency guard) → public health SHA check → HTTPS/HSTS contract grep.
- No CI exclusions remain in workflow; H1–H4 items are local-host divergences documented in the register.
- Push cancels in-flight test job (concurrency ci-${{ github.ref }} cancel-in-progress: true); deploy never cancels.

## 5. SECURITY / REPO VISIBILITY TRUTH

| Item | Value |
|------|-------|
| Repo visibility | PUBLIC (github.com/shunya-os/Shunya-OS) |
| Branch protection (master) | **ABSENT** — API 404 "Branch not protected"; zero rulesets |
| Tracked sensitive files | `app/communication/credentials.py` (needs review — appears env-based); **8 tracked files under uploads/** incl. PII itineraries (Nishesh Japan Zostel Itinerary PDFs ×3, audit PDF, test files) — L4 |
| .env in public history | YES — commits 6b02ac5, 80b60b2 (E6) |
| B16 auth middleware | app/__init__.py `_check_auth`: (1) trusts `X-Identity-Id` header to set `g.identity_id` AND session user_id; (2) exempts ALL `/api/*` plus a long static path list; (3) TESTING config bypasses everything |
| Unguarded blueprint families (B17–B24) | 7 of 8 source-verified auth-free today (customer_experience, marketing_intelligence, sales_intelligence, marketing_os, entity_routes, kernel, reality_engine); export has some decorators but B24 org-wide dump remains. Register says "nine" for B17–B24 (eight rows) — reconcile via route-inventory test. |

## 6. LIVE DEFECTS (observed this session)

| ID | Status | Evidence |
|----|--------|----------|
| L1 | CONFIRMED | analytics dashboard 500; model-vs-migration drift; live DB lacks table |
| L2 | CONFIRMED | journald: "Background outcome review failed: Working outside of application context." recurring hourly (18:05, 18:37, 19:37, 20:37, 21:36) |
| L3 | seen in workflow | public /health + /metrics unauth (E8) |
| L4 | CONFIRMED | 8 tracked PII files in uploads/, repo PUBLIC (E6) |

## 7. ALREADY-CERTIFIED (carried forward — verified, not re-proven this session)

- LB-002 age/safety governance: CI-certified on c6b0fa0 (run 38141992443) + production runtime proof (3a2d3d3).
- S-004 cross-tenant read isolation: 20 adversarial tests, CI green on c6b0fa0.
- S-001 HSTS, S-003 HTTPS-only contract: contract tests + deploy smoke step.
- 5,641 backend + 73 frontend tests passed on c1db536 run 38166859810 (128 skipped; lint warnings + ignored advisory PYSEC-2026-2860 retained).

## 8. EXECUTION DEPENDENCIES (founder-gated / external)

| Item | Dependency |
|------|------------|
| E6 history purge / repo visibility (D4) | requires explicit founder approval: exact files/commits/refs, rotation status, collaborators/forks, recovery plan (SECTION 2.3 boundary) — containment proceeds meanwhile |
| LB-001 founder acceptance (D1) | founder walkthrough + sign-off |
| E18 KYC method (D3) | policy decision; default = no documentary provider, admin-attested only |
| Email/WhatsApp live-provider acceptance (C-series) | provider credentials/approval as applicable |
| D2 branch protection | directive approves enabling; verify enforcement after |

## 9. CAMPAIGN PLAN (waves in dependency order)

1. Wave 0: B16 + B17–B24, L1 migration, E1/L2/E5 alerts, E6 containment, D2 protection, E8–E18/H-series ops
2. Wave 1: Email C1–C9/B8, WhatsApp C10–C14, connectors C15–C20
3. Wave 2: Journeys D1–D20, backend B1–B15
4. Wave 3: Frontend A1–A18 + visual/accessibility acceptance
5. Wave 4: Backup/recovery E2–E5/E14/E15–E17 + rollback proof
6. Wave 5: Decisions, milestones, orphans, gates reconciliation
7. Final certification + register reconciliation + completion report

**Closure standard (directive §9):** every gap ends VERIFIED / EXTERNALLY BLOCKED / OPEN — nothing else. Registers stay in agreement; counts recalculated from rows, not headlines.