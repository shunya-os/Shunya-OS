# FORENSIC BASELINE — ZERO-GAP-FORENSIC-RECONCILIATION-05

> **Created:** 2026-08-22
> **Directive:** ZERO-GAP-FORENSIC-RECONCILIATION-05
> **Rule:** This baseline must not be overwritten. All remediation is measured against this.

## A1 — REPOSITORY TRUTH

| Field | Value |
|-------|-------|
| Repository top-level | /home/shunya-deploy/shunya_os |
| Current branch | master |
| HEAD | daf17ff8396709cba11e46666ec93b5e43ca6cc9 |
| HEAD short | daf17ff |
| origin/master | daf17ff8396709cba11e46666ec93b5e43ca6cc9 |
| HEAD = origin/master | YES |
| Working tree | CLEAN (no diff, no staged) |
| Branches | docs, main, master, origin/master |
| Stashes | none |
| Worktrees | /home/shunya-deploy/shunya_os (master) |

## A2 — DEPLOYMENT TRUTH

| Field | Value |
|-------|-------|
| Service | shunya.service (gunicorn) |
| Gunicorn PID(s) | 428781 (master), 542978, 543239, 543658 (workers) |
| PATH | /home/shunya-deploy/shunya_os/.venv/bin/gunicorn |
| Workers | 3, bind 127.0.0.1:5001 |
| Service status | Running (systemctl inaccessible — sudo required) |
| Database | connected (PostgreSQL 16, localhost:5432) |
| Health endpoint | /health — status: ok, database: connected |
| Health: git_commit | daf17ff8396709cba11e46666ec93b5e43ca6cc9 |
| Health: build_id | EMPTY |
| Health: git_commit_short | daf17ff |
| Health: version | 1.0.0 |
| Health: environment | production |
| Health: uptime_seconds | 151 |
| Provenance: HEAD matches production | CONFIRMED — git_commit == HEAD |
| Journal: recent errors | WORKER TIMEOUT on /api/v1/reality/stream SSE |
| .env: DATABASE_URL | postgresql://shunya:***@localhost:5432/shunya_os |
| .env: RATELIMIT_STORAGE_URL | redis://127.0.0.1:6379 |
| .env: AI providers | GROQ: llama-3.3-70b-versatile (primary), GEMINI, OPENROUTER, CLOUDFLARE, HF |

## A2 — SERVICE CONFIGURATION

| Field | Value |
|-------|-------|
| Unit file | /etc/systemd/system/shunya.service |
| User | shunya-deploy |
| WorkingDirectory | /home/shunya-deploy/shunya_os |
| Environment PATH | /home/shunya-deploy/shunya_os/.venv/bin:/usr/bin:/bin |
| FLASK_ENV | production |
| ExecStart | gunicorn --workers 3 --bind 127.0.0.1:5001 --timeout 60 ... |
| Restart | always |
| Deploy script | infrastructure/scripts/deploy.sh — fetches main, installs, migrates, restarts |
| Deploy script note | DEPLOY SCRIPT USES `main` BRANCH, NOT `master` |

## A3 — TEST ENVIRONMENT STATE

| Field | Value |
|-------|-------|
| System Python | /usr/bin/python3 3.12.3 |
| Venv Python | .venv/bin/python3 3.12.3 |
| pip version | 26.1.2 |
| pytest version | 9.1.1 |
| pip freeze count | 181 packages |
| Requirements file | requirements.txt (simple deps, no lock file) |
| pyproject.toml | DOES NOT EXIST |
| pytest.ini | asyncio_mode=auto, timeout_method=thread, testpaths=tests |
| CI: ci.yml | pip install -r requirements.txt + pytest tests/ -q |
| CI: ci-cd.yml | Deploy via SSH on CI success |

## A3 — CI CONFIGURATION

- **ci.yml** — Runs on push/PR to main/master. Steps: checkout → setup python 3.12 → pip install deps → compile check → verification tests → adapter import → canonical test suite
- **ci-cd.yml** — Deploy to production after CI success on main/master
- CI canonical test suite: `PYTHONPATH=$PWD python -m pytest tests/ -q --tb=short`
- **No explicit skip/exclude flags in CI config** (but test collection itself may exclude)

## A3 — CURRENT GAP REGISTER

Source: docs/zero_gap/CANONICAL_GAP_REGISTER_04B.md (authored at 6a8c1e7)

### Capability counts (61 total):

**VERIFIED (60):**
- Foundation A: A-01 through A-09 (9 items)
- Core Domains B: B-01 through B-30 (34 items)
- Infrastructure C: C-01, C-02, C-04 through C-09 (8 items)
- Cross-Cutting D: D-01 through D-10 (10 items — note register says 9/9 but lists 10 items, arithmetic inconsistency flagged for review)

**PRIVILEGE-GATED (1):**
- C-03: Nginx/HTTPS

### Verification/Ops gaps (4):

| ID | Status | Description |
|----|--------|-------------|
| V-01 | PARTIAL | Full suite execution timeout |
| V-02 | PARTIAL | CI test suite completion |
| V-03 | PARTIAL | 7 remaining skip files |
| V-04 | PRIVILEGE-GATED | Production parity (service restart) |

### Register arithmetic:
- Claims: 60 VERIFIED + 0 PARTIAL + 0 MISSING + 1 PRIVILEGE-GATED = 61 capabilities
- Verification: 3 PARTIAL + 1 PRIVILEGE-GATED = 4
- Grand total: 60 VERIFIED + 3 PARTIAL + 2 PRIVILEGE-GATED = 65

**NOTE: D section lists 10 items (D-01 through D-10) but claims 9/9.  Item D-03 appears in both C and D.**
**NOTE: Register is at 6a8c1e7 but HEAD is now daf17ff — 4 intervening commits.**

## A3 — KNOWN SUPPRESSIONS (From commit history)

Based on commit messages:

| Commit | Suppression |
|--------|-------------|
| 5a003f7 | D-04 CI/CD: exclude pre-existing CRM test (401 vs 201) |
| cf7d1ab | D-04 CI/CD: exclude pre-existing loads_with_app tests from CI |
| cceec84 | D-04 CI/CD: exclude pre-existing orchestration test (503 vs 200) |
| 608c1fa | D-04 CI/CD: exclude pre-existing cortex test from CI (503 vs 200) |
| ab9d3c5 | D-04 CI/CD: fix CI pipeline — add flask-wtf dep, add untracked audit-viewer |
| b49fb0c | M3: Remove skip marks from 2 tests that actually pass |
| ffb7c83 | WORKSTREAM A: CI/CD canonicalization |
| fcdcc74 | C-07: Accessibility audit fixes — contrast, landmarks, skip-link, focus, reduced-motion |

**IMPORTANT**: Commit `5a003f7` "exclude pre-existing CRM test (401 vs 201)", `cf7d1ab`, `cceec84`, `608c1fa` explicitly suppressed tests. `b49fb0c` says "Remove skip marks from 2 tests that actually pass" — implying there were more than 2 skipped.

---

**THIS BASELINE IS IMMUTABLE. FORENSIC RECONCILIATION MUST NOT OVERWRITE IT.**