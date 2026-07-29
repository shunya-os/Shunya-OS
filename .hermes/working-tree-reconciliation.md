# Working Tree Reconciliation — Inventory & Classification

## A. MODIFIED TRACKED FILES (24 files)

All modifications to existing tracked files are legitimate changes made during the M1-M9 implementation. These will be committed.

| # | File | Nature | Disposition | Phase |
|---|------|--------|-------------|-------|
| 1 | .env.example | Expanded env config template | COMMIT | Infrastructure |
| 2 | CANONICAL_MANIFEST.yaml | Updated manifest w/ Governance Freeze 01 | COMMIT | Governance |
| 3 | RATIONALIZATION_REPORT.md | Updated duplicate analysis report | COMMIT | Governance |
| 4 | app.py | Debug mode conditional fix | COMMIT | Phase 1 |
| 5 | app/__init__.py | Import genesis blueprint | COMMIT | Phase 1/Genesis |
| 6 | app/auth_routes.py | Add /genesis to public paths | COMMIT | Phase 1/Genesis |
| 7 | architecture/ARCHITECTURE_GOVERNANCE_FRAMEWORK.md | Status: ratified | COMMIT | Governance |
| 8 | architecture/SHUNYA_CONSTITUTION.md | Mark SUPERSEDED, add canonical ref | COMMIT | Governance |
| 9 | core/os.py | Replace mock runtimes with real adapters | COMMIT | Phase 1 |
| 10 | docs/canon/INDEX.md | Add Product Constitution docs 14-15 | COMMIT | Governance |
| 11 | docs/canon/OS_CONSTITUTION.md | Add governance authority refs | COMMIT | Governance |
| 12 | frontend/index.html | Meta tags, OG, theme-color | COMMIT | Phase 1/Frontend |
| 13 | frontend/package-lock.json | Add playwright dep | COMMIT | Phase 1/Frontend |
| 14 | frontend/package.json | Add playwright dep | COMMIT | Phase 1/Frontend |
| 15 | governance/GOVERNANCE_CHANGELOG.md | Governance Freeze 01 entry | COMMIT | Governance |
| 16 | governance/SHUNYA_ENGINEERING_CONSTITUTION.md | Ratified status | COMMIT | Governance |
| 17 | governance/SHUNYA_GOVERNANCE_MODEL.md | Add §8 Conflict Resolution | COMMIT | Governance |
| 18 | governance/adr/ADR_TEMPLATE.md | Add Product/Experience class | COMMIT | Governance |
| 19 | static/css/landing.css | DELETED (intentional) | COMMIT deletion | Governance |
| 20 | static/js/workspace.js | M4 Intelligent Workspace Renderer | COMMIT | Later milestone |
| 21 | templates/shunya_login.html | Fix login form action URL | COMMIT | Phase 1 |
| 22 | tests/runtime_pipeline/test_identity_runtime.py | Runtime count 10→9 | COMMIT | Phase 1 |
| 23 | tests/runtime_pipeline/test_kernel_runtime.py | Runtime count 10→9 | COMMIT | Phase 1 |
| 24 | tests/runtime_pipeline/test_pipeline.py | Runtime count 10→9 | COMMIT | Phase 1 |

## B. UNTRACKED FILES

### B1. Phase 1 Implementation (COMMIT)

| # | File | Description |
|---|------|-------------|
| 1 | core/runtime_pipeline/adapters.py | 6 real runtime adapters replacing mocks |
| 2 | app/genesis_protection.py | Immutable audit log & protective safeguards |
| 3 | app/genesis_routes.py | Genesis API endpoints |

### B2. Constitutional Documents (COMMIT)

| # | File | Description |
|---|------|-------------|
| 4 | docs/canon/14_product_constitution.md | Product Constitution — 12 sections, 57 reqs |
| 5 | docs/canon/15_product_completion_checklist.md | 81 pass/fail certification tests |
| 6 | docs/canon/SHUNYA_FOUNDER_EXPERIENCE_ROADMAP_v1.0.md | 10-milestone founder experience roadmap |

### B3. Governance Reports & ADRs (COMMIT)

| # | File | Description |
|---|------|-------------|
| 7 | docs/reports/capability-lineage.md | Capability lineage report |
| 8 | docs/reports/phase0-universal-capability-audit.md | Phase 0 capability audit |
| 9 | docs/reports/phase1-consolidation-and-exposure-plan.md | Phase 1 consolidation plan |
| 10 | governance/GOVERNANCE_FREEZE_01_CONFLICT_RESOLUTION.md | GF-01 conflict resolution |
| 11 | governance/GOVERNANCE_FREEZE_01_RATIFICATION_PACKAGE.md | GF-01 ratification package |
| 12 | governance/GOVERNANCE_FREEZE_01_REPORT.md | GF-01 report |
| 13 | governance/GOVERNANCE_FREEZE_01_XREF_REPORT.md | GF-01 cross-reference |
| 14 | governance/adr/ADR-008-CAPABILITY-AUDIT-AND-EVIDENCE-PRESERVATION.md | ADR-008 |
| 15 | governance/adr/ADR-009-AUTH-CONSOLIDATION-FRAMEWORK.md | ADR-009 |
| 16 | governance/adr/ADR-010-SUBPROJECT-CAPABILITY-INTEGRATION.md | ADR-010 |
| 17 | governance/capability-registry.md | Capability registry |

### B4. Static Evidence & Visualizations (COMMIT)

| # | File | Description |
|---|------|-------------|
| 18 | static/FAA-01-AUDIT-REPORT.md | Founder acceptance audit |
| 19 | static/FAA-01B-REPORT.md | Experience consolidation report |
| 20 | static/SEC-01-CONVERGENCE-REPORT.md | Experience convergence report |
| 21 | static/phase1-implementation-evidence.md | Phase 1 implementation evidence |
| 22 | static/phase1-pipeline-activation-evidence.md | Phase 1 pipeline activation evidence |
| 23 | static/shunya-architecture.html | Architecture visualization |
| 24 | static/shunya-founder-experience-roadmap.html | Roadmap visualization |
| 25 | static/shunya-production-roadmap.html | Production roadmap visualization |

### B5. Verification Scripts — Permanent Assets (COMMIT)

| # | File | Description |
|---|------|-------------|
| 26 | scripts/check_js_syntax.py | JS syntax verification |
| 27 | scripts/genesis_verify.py | Genesis state verification |
| 28 | scripts/seed_demo_m4.py | M4 demo data seeding |
| 29 | static/phase1-verify.py | Phase 1 verification kit (5 tests) |
| 30 | static/scripts/phase1_bootstrap.py | Bootstrap verification |
| 31 | static/scripts/phase1_cognitive_count.py | Cognitive runtime count |
| 32 | static/scripts/phase1_pipeline_trace.py | Pipeline execution trace |
| 33 | static/scripts/phase1_unknown_intent.py | Unknown intent noop verification |

### B6. Generated/Compiled/Derived Artifacts (IGNORE via .gitignore)

| # | Pattern | Reason |
|---|---------|--------|
| 1 | frontend/src/*.js | Compiled JS output from .ts sources |
| 2 | frontend/screenshots/*.png | Screenshot artifacts |
| 3 | frontend/verify-screenshots/*.png | Verification screenshot artifacts |
| 4 | .env.audit | Generated environment audit |
| 5 | infrastructure/environments/*.env | Environment configs (not secrets) |
| 6 | backups/*.db | Database backups |
| 7 | instance/*.db | Local SQLite databases |
| 8 | media/ | Uploaded media files |
| 9 | public_site/genesis/ | Generated static site |

### B7. Generated Reports (IGNORE via .gitignore)

| # | File | Reason |
|---|------|--------|
| 1 | ARCHITECTURE_REVIEW_REPORT.md | Generated report |
| 2 | CERTIFICATION_RECOMMENDATION.md | Generated report |
| 3 | CLOSURE_AUDIT_REPORT.md | Generated report |
| 4 | CLOSURE_PACKAGE.md | Generated package |
| 5 | CONSTITUTIONAL_COMPLIANCE_REPORT.md | Generated report |
| 6 | DATABASE_BACKUP_REPORT.md | Generated report |
| 7 | DATABASE_RUNTIME_DECISION.md | Generated decision |
| 8 | DATA_PROTECTION_REPORT.md | Generated report |
| 9 | FOUNDER_PROTECTION_REPORT.md | Generated report |
| 10 | FREEZE_NOTICE.md | Generated notice |
| 11 | GENESIS_PREPARATION_REPORT.md | Generated report |
| 12 | GENESIS_RESET_REPORT.md | Generated report |
| 13 | GENESIS_VERIFICATION_REPORT.md | Generated report |
| 14 | SECURITY_ASSESSMENT.md | Generated report |
| 15 | TECHNICAL_DEBT_REGISTER.md | Generated register |

### B8. Hermes Plans (IGNORE — already in .gitignore?)

| # | File | Reason |
|---|------|--------|
| 1 | .hermes/plans/*.md | Hermes agent working plans |