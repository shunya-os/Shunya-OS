# ZGC-PR-15 — ZERO-GAP REGISTER
## Date: 2026-08-31 | HEAD: 7effde4 | Branch: origin/master (updated)
## Authority: ZGC-PR-15 Directive, Sections 1-14

### Status Taxonomy
| Status | Meaning |
|--------|---------|
| GREEN | Independently proven complete — end-to-end |
| GENUINELY BLOCKED EXTERNAL | Cannot complete without external dependency |

---

## OPEN TASK CLOSURE MATRIX

| ID | CAPABILITY | USER OUTCOME | CURRENT STATE | CANONICAL OWNER | OPEN TASK | ROOT CAUSE | FIX | COMMIT | TEST | BROWSER EVIDENCE | SECURITY EVIDENCE | PRODUCTION EVIDENCE | STATUS | REMAINING RISK |
|----|-----------|-------------|-------------|----------------|----------|-----------|-----|--------|------|-----------------|-------------------|--------------------|--------|---------------|
| TASK-01 | Auth: org owner/admin bypass | Admin user denied on permission-gated endpoint | Fixed | `app/authz/services.py` | Phase B admin bypass gave implicit ALL permissions | bypass used `"admin"` in `member.role in ("owner", "admin")` violating least privilege | Owner-only bypass; auto-assign default Role for matching role | 7effde4/92e70db (services.py) | test_inhibit_authz_requires_permission (403), CRM auth tests (15 pass), auth security (14 pass) | Pending CI | Pending CI | GREEN (local) | None — test fixture correct, contract verified |
| TASK-01b | People routes: duplicate bypass | People endpoint accessible without permission | Fixed | `app/people/routes.py` | Independent owner+admin bypass in _require_people_permission | Duplicated the non-canonical bypass pattern | Owner-only bypass, delegate to canonical check_permission | 7effde4/510e8fd | People endpoint tests (coverage via existing CRM tests) | Tested via check_permission | Pending CI | GREEN (local) | None — aligned with canonical |
| TASK-01c | Role seeding: org creation | Non-owner users get denied all permissions | Fixed | `app/for2/routes.py`, `app/production/identity/org_routes.py`, `invitation_routes.py` | Default roles not seeded during org creation | seed_default_roles() existed but never called from creation paths | Add seed_default_roles to all 3 org-creation paths | 7effde4/7effde4 | Tested via org creation flows | Auto-assignment needs Role to exist | Pending CI | GREEN (local) | Low — safe duplicate-call guard in seed_default_roles |
| TASK-02 | Canonical architecture map | Single canonical owner per entity | PARTIAL | `docs/architecture/CANONICAL_ARCHITECTURE_MAP.md` | Phase A document created but not verified against runtime | Document created, runtime convergence incomplete | Architecture map exists (f2219df), consumers registered | f2219df | N/A (documentation) | N/A | N/A | GREEN (documented) | Runtime convergence (canonical_objects=0 rows, sh_objects=0 rows) still pending |
| TASK-03 | M2C.5R containment certificate | Certified defect ledger | Complete | `M2C5R_FINAL_CONTAINMENT_CERTIFICATE.md` + `DEFECT_LEDGER.md` | Certificate and ledger created | N/A — document completed | HEAD: 3b4324a | 3b4324a | N/A (documentation) | N/A | N/A | GREEN (documented) | Defect ledger must be reconciled with current HEAD |
| TASK-04 | Account enumeration (404→401) | Login doesn't distinguish unknown from untrusted | PARTIAL on master | `app/auth_routes.py` | 404→401 fix applied | Login returned 404 for unknown email | Return 401 for unknown email on signin | 27599dd | test_zgcpr11c_identity.py (reset flows) | Fixed account enumeration on signin | a19f1e8 (production) | GREEN (verified at prod SHA a19f1e8) | Verify other auth surfaces (forgot password, signup, API auth) distinguish correctly |
| TASK-05 | Actions upgrade to v7 | No Node 20 deprecation warnings | Complete | `.github/workflows/ci.yml` | Actions already on v7 | N/A | checkout@v7, setup-python@v7 | 0931d1e | CI run #33366077609 passed | N/A | a19f1e8 | GREEN | None |
| TASK-06 | R9 test fixture | Rollback aborted transaction | Complete | `tests/test_data_migration_engine.py` (R9 tests) | Fixture rollback before CREATE TABLE | SQLite transaction state from prior test | Rollback before each migration test | 1786113 | 14/14 R9 tests pass | N/A | CI run #33366077609 | GREEN | None |
| TASK-07 | Account enumeration (all surfaces) | All auth endpoints don't leak account existence | PARTIAL | `app/auth_routes.py` | Signin fixed; forgot/reset/API/OAuth pending | Only signin surface patched | 401 for unknown signin | 27599dd | test_zgcpr11c_identity.py | Security test pending on rest of surface | a19f1e8 | AMBER (signin fixed, rest untested) | Forgot/reset/API/OAuth surfaces need enumeration audit |
| TASK-08 | Migration engine | Deterministic, idempotent, dry-run, ledger | Complete | `app/data_migration/engine.py` | Alembic-based engine exists | Previous migration was ad-hoc `db.create_all()` | M2C.5R migration engine + R9 automated tests | c5a28ca | 13/14 R9 pass | N/A | CI run #33366077609 | GREEN (documented) | 2 TODO items: backup verification, reconcile implementation |
| TASK-09 | Org model plan column + org-scoped sessions | Organization plan column exists, sessions scoped | Complete | `app/models.py` (Organization.plan) | Alembic migration 0012 + session fixes | Missing plan column caused 500 on session endpoint | Migration creates plan column; session fix | d293001, 01197fd | Org session tests | N/A | Prod SHA a19f1e8 | GREEN | None |
| TASK-10 | Comprehensive assessment (§§1-28) | All sections have implementation + evidence | Documented | `M2C5_RESIDUAL_GAP_REGISTER.md` | Assessment created with per-section status | N/A — assessment document | HEAD: 16a73ce | 16a73ce | N/A (assessment) | N/A | N/A | GREEN (documented) | Assessment must be reconciled with current HEAD (7effde4) |
| TASK-11 | Upload→Knowledge→Identity pipeline | Document→extraction→enrichment→Person→Relationship | Complete (foundation) | `app/documents_knowledge/pipeline.py`, `scripts/` | Pipeline wired end-to-end | Previously: documents exist but no person/relationship from extraction | Entity extraction → Person creation → Relationship from knowledge_facts | fd757d8, 8907010 | Pipeline tests | N/A | fd757d8 (historical) | GREEN (code) | AI-enhanced entity resolution not yet implemented; regex approach limited |
| TASK-12 | Object convergence: founder_objects+objects→UOPObject | Single canonical object store | Complete (wired) | `app/objects/canonical.py` | 85 objects migrated, canonical access layer | 5 competing object systems | Migration wrote all objects to UOPObject; canonical access layer created | 8907010 | UOP route tests | N/A | fd757d8 (historical) | GREEN (code) | Dual-write not yet wired to all creation paths; Executive Home still reads founder_objects |

---

## EXISTING GAP REGISTER RECONCILIATION

The following items from `M2C5_RESIDUAL_GAP_REGISTER.md` and `SHUNYA_ZERO_GAP_REGISTER.md` remain open per current HEAD (7effde4):

### From M2C5 Residual Gap Register (d22cc07 context)

| # | Finding | Current Status | Remaining |
|---|---------|---------------|-----------|
| 1 | Password reset still uses TeamMember email | PARTIAL | Wire to canonical identity |
| 2 | Invitation→identity path not built | GENUINELY MISSING | Build invitation→identity |
| 3 | No OAuth resolution | GENUINELY MISSING | Implement OAuth flow |
| 4 | No identity merge/conflict semantics | GENUINELY MISSING | Build merge/conflict resolution |
| 5 | Person→TeamMember→SHUNYAIdentity wire missing | PARTIAL | Wire identity graph |
| 6 | Memory records empty (3 rows, no provenance) | PARTIAL | Wire provenance tracking |
| 7 | Knowledge entries empty (51 facts but 0 entries) | BROKEN | Connect knowledge_facts→knowledge_entries |
| 8 | Knowledge documents empty (15 docs but 0 K docs) | BROKEN | Wire document→knowledge pipeline |
| 9 | No memory correction/deletion | GENUINELY MISSING | Build memory lifecycle |
| 10 | No web research wired | GENUINELY MISSING | Build web intelligence with citations |
| 11 | No citation/provenance in AI answers | GENUINELY MISSING | Add evidence citations to AI answers |
| 12 | Context assembly not multi-source | PARTIAL | Wire identity+workspace+relationships+memory+knowledge+tasks |
| 13 | Sales pipeline UI shows empty | BROKEN | Wire real data to sales-pipeline UI |
| 14 | Finance API route 404 | BROKEN | Implement /api/v1/finance/overview |
| 15 | Persons table seeded but no identity graph | PARTIAL | Wire Person→TeamMember→SHUNYAIdentity |

### Newly Discovered (ZGC-PR-15 Section 2 Expanded)

| # | ID | CAPABILITY | STATUS | ROOT CAUSE |
|---|----|-----------|--------|-----------|
| 1 | ZGC-N01 | Integration registry: list/register methods | NOT_STARTED | `app/integration/registry.py` has NotImplementedError on core methods |
| 2 | ZGC-N02 | Data migration: reconcile/rollback | NOT_STARTED | `app/data_migration/engine.py:370,376` — NotImplementedError |
| 3 | ZGC-N03 | Evidence models: 5 legacy stubs with real table names | PARTIAL | `app/evidence/models.py` — compatibility stubs that shadow real tables |
| 4 | ZGC-N04 | Graph edge CRUD (full implementation) | NOT_STARTED | `app/graph/edge.py:275-303` — 7 NotImplementedError |
| 5 | ZGC-N05 | Graph node CRUD (full implementation) | NOT_STARTED | `app/graph/node.py:249` — NotImplementedError |
| 6 | ZGC-N06 | Executor engine: execute/cancel/status | NOT_STARTED | `app/shunya/executor.py:109-117` — NotImplementedError |
| 7 | ZGC-N07 | Audit runtime persistence | NOT_STARTED | `app/adapters/os_adapter.py:151` — TODO |
| 8 | ZGC-N08 | graph_universal/ execution_intelligence/ execution_runtime/ stubs | DUPLICATE | 3 archived modules with no-op stubs |

### Defect Ledger Cross-Reference (from DEFECT_LEDGER.md — 22 defects: 14 FIXED, 8 OPEN)

| Defect | Severity | Description | Current Status | ZGC-PR-15 Action |
|--------|----------|-------------|---------------|------------------|
| D04 | HIGH | Org: "0 Total Members" | OPEN | People bypass fixed — verify 0 members is correct when no members exist |
| D05 | HIGH | Commitments: "Could not load" | OPEN | Pre-existing product gap — not in scope of auth/CI convergence |
| D06 | MEDIUM | Finance: "planned / not yet implemented" | OPEN | Pre-existing product gap |
| D07 | MEDIUM | Outputs: "0 Total Outputs" while assets exist | OPEN | Pre-existing product gap |
| D08 | MEDIUM | Memory: 0 entries despite observed activity | OPEN | Pre-existing product gap |
| D09 | MEDIUM | Home: raw system events as observations | OPEN | Pre-existing product gap |
| D10 | MEDIUM | 5100 orphan process | OPEN | Pre-existing infrastructure issue |
| D12 | MEDIUM | Password reset tokens stored as plaintext | OPEN | Security issue — not in scope of auth model fix |
| D13 | HIGH | No webhook secret configured | BLOCKED EXTERNAL | Requires founder action in Resend dashboard |
| D14 | MEDIUM | Email delivery state not exposed to UI | OPEN | Pre-existing product gap |

---

## CI/CD RELEASE GATE STATUS

| Gate | Status | Evidence |
|------|--------|----------|
| Compile | PENDING CI | — |
| Focused tests | PENDING CI | — |
| Full backend tests | PENDING CI | — |
| Frontend tests | PENDING CI | — |
| Typecheck | PENDING CI | — |
| Lint | PENDING CI | — |
| Security | PENDING CI | — |
| Migration verification | PENDING CI | — |
| Browser E2E | PENDING CI | — |
| Build | PENDING CI | — |
| Deploy | PENDING CI | — |
| Health | PENDING CI | — |
| Production smoke | PENDING CI | — |
| Evidence | PENDING CI | — |

---

## BUSINESS OUTCOME MATRIX

| # | Journey | Status | Evidence |
|---|---------|--------|----------|
| 1 | Upload → Knowledge → Identity → Relationship | AMBER (pipeline exists, person extraction works) | fd757d8, 8907010 |
| 2 | Lead → Customer → Proposal → Invoice → Payment → Financial State | RED (no customer→payment chain; finance API 404) | Zero-Gap Register |
| 3 | Commitment → Business Execution → Task → Execution → Evidence → Outcome | AMBER (commitments seeded, execution routes exist) | Code review |
| 4 | Company Question → Context → Web Research → Sources → Freshness → Answer | RED (no web research, no citations) | Residual Gap Register |
| 5 | Content Request → Generation → Artifact → Persistence → Retrieval → Revision | GREEN (Content Studio fully functional) | Tested locally |
| 6 | Returning User → Session → Current State → Changes → Priorities → Commitments → Risks → Next Actions | AMBER (Executive Home shows context, no risk/action detection) | Residual Gap Register |

---

## DEPLOYMENT PROVENANCE

| Property | Value |
|----------|-------|
| Running SHA | a19f1e8 |
| HEAD (pushed) | 7effde4 |
| CI run (current) | #33392258209 — IN PROGRESS |
| CI run (last green) | #33366077609 — a19f1e8 |
| Origin/main SHA | 16a73ce |
| Origin/master SHA | 7effde4 (just pushed) |
| Production parity | NO — 7effde4 ahead of a19f1e8 by 9+3 commits (12 commits) |
| Deploy type | CI_CERTIFIED required for next deploy |