# FINAL REMEDIATION BASELINE

**Date:** 2026-08-14T17:15  
**Captured:** Before any remediation action

---

## GIT STATE

| Field | Value |
|-------|-------|
| HEAD | b1545c9edd9b691f5c1c17cabd02c8783cd03604 |
| Branch | master |
| Origin | git@github.com:shunya-os/Shunya-OS.git |
| Ahead/behind | 0 ahead, 0 behind |
| Last commit | FDA26-FDA30: Developer platform, web app, observability, security, AI safety |

## WORKING TREE

| Type | Count |
|------|-------|
| Modified | 25 files |
| Untracked | 34 files |
| Deleted | 6 files |

## DEPLOYMENT

| Component | Detail |
|-----------|--------|
| Gunicorn | 4 processes (1 master + 3 workers) |
| Bind | 127.0.0.1:5001 |
| nginx | Could not read via nginx -T (permission) |
| Service | systemd shunya.service |
| Frontend bundle | index-DtnOsvt5.js (hash: 3accea0f...) |
| Database | PostgreSQL 16, 25 MB, 192 tables |
| Migration | 0006_fda12_15_marketing_sales |
| Environment | SHUNYA_ENVIRONMENT=production, FLASK_ENV=production, DEBUG=false |

## DATA STATE

| Table | Rows |
|-------|------|
| team_members | 71 |
| shunya_identities | 35 |
| sh_objects | 605 |
| founder_objects | 508 |
| objects | 31 |
| evidence_records | 7 |
| act_execution_logs | 1769 |
| leads | 20 |
| customer | 4 |
| commitments | 0 |
| document_records | 0 |
| memory_records | 35 |

## BACKUP

| Item | Detail |
|------|--------|
| File | shunya_os_20260814_120259.sql.gz |
| Format | pg_dump custom (Fc) |
| Valid | YES |
| Entries | 1968 |
| Restore tested | NO |

## WORKING TREE FILE INVENTORY

### Modified files (25) — classified

| File | Classification | Notes |
|------|---------------|-------|
| app/__init__.py | **REQUIRED FIX** | Session cookie security, icon routes, public paths |
| app/ai/provider.py | PRE-EXISTING | Not part of this session |
| app/ai/routes.py | **REQUIRED FIX** | Evidence commit, web_search fix |
| app/auth.py | PRE-EXISTING | Not part of this session |
| app/auth_routes.py | **REQUIRED FIX** | url_for serve_index → main.index (login 500 fix) |
| app/awareness/engine.py | PRE-EXISTING | Not part of this session |
| app/communication/models.py | PRE-EXISTING | Not part of this session |
| app/evidence/service.py | **REQUIRED FIX** | log_evidence now writes to evidence_records |
| app/intelligence/awareness.py | PRE-EXISTING | Not part of this session |
| app/orchestrator/engine.py | PRE-EXISTING | Not part of this session |
| config/inference.yaml | PRE-EXISTING | Not part of this session |
| core/inference_governance.py | PRE-EXISTING | Not part of this session |
| core/inference_orchestrator/execution.py | PRE-EXISTING | Not part of this session |
| core/inference_orchestrator/provider_registry.py | PRE-EXISTING | Not part of this session |
| frontend/src/components/public/homepage.tsx | **REQUIRED FIX** | Semantic headings (h1-h3) |
| frontend/src/components/onboarding/step-first-object.tsx | **REQUIRED FIX** | Object type descriptions |
| app/objects/routes.py | **REQUIRED FIX** | Object creation writes to sh_objects |
| migrations/versions/0001_initial_schema.py | PRE-EXISTING | Not part of this session |
| scripts/generate_audit_report.py | PRE-EXISTING | Not part of this session |
| .env | **REQUIRED FIX** | Production environment config |

### Deleted files (6)

| File | Classification | Notes |
|------|---------------|-------|
| app/execution_runtime/routes.py | OBSOLETE | Legacy module, not imported |
| app/execution_runtime/runtime.py | OBSOLETE | Legacy module, not imported |
| app/object_composer/composer.py | OBSOLETE | Legacy module, not imported |
| app/object_composer/routes.py | OBSOLETE | Legacy module, not imported |
| app/object_workspace/routes.py | OBSOLETE | Legacy module, not imported |
| app/object_workspace/workspace.py | OBSOLETE | Legacy module, not imported |

### Untracked files (34)

| Category | Count | Notes |
|----------|-------|-------|
| FDA/FORENSIC reports | 15 | Historical closure documents |
| _archive/ | 4 | Legacy variant archives |
| docs/ | 5 | FDA33, FDA34, FDA36, launch audit docs |
| scripts/ | 7 | Browser QA, diagnostics, PDF generation |
| node_modules/ | 1 | Playwright dependency |
| app/execution_runtime/__init__.py | 1 | Needed for deleted module |
| oauth_fix.py | 1 | OAuth fix script |

## IMMEDIATE REQUIRED ACTIONS

1. Commit the REQUIRED FIX files (8 Python files + 2 TSX files + .env)
2. Delete the 6 OBSOLETE files from git tracking
3. Build frontend from clean tree
4. Deploy the committed release
5. Verify production matches Git

---

*End of baseline*