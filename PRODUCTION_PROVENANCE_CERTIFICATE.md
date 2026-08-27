# SHUNYA — Production Provenance Certificate

> Generated: 2026-08-27 23:35 UTC | Directive: M2B (Extended)
> Purpose: Prove Git SHA = Deployed SHA = Running Health SHA

## Current State

| Metric | Value |
|--------|-------|
| **Canonical Branch** | `primary-workspace-recovery` |
| **Local HEAD** | `d4e38ff` |
| **Origin HEAD** | `d4e38ff` (pushed) |
| **Deployed SHA** | `d4e38ff` |
| **Health Status** | `ok` |
| **Database** | `connected` |
| **Working Tree** | CLEAN |

## Verification Chain

```
GIT COMMIT d4e38ff
    ↓ git push origin primary-workspace-recovery
ORIGIN d4e38ff
    ↓ sudo systemctl restart shunya
DEPLOYED d4e38ff
    ↓ curl http://localhost:5001/health
HEALTH {"git_commit_short": "d4e38ff", "status": "ok", "database": "connected"}
    ↓
ALL THREE SHAs IDENTICAL ✅
```

## Branch Topology

| Branch | SHA | Status |
|--------|-----|--------|
| **primary-workspace-recovery** 🏆 | d4e38ff | CANONICAL — deployed, live |
| origin/master | 2bfa630 | LEGACY — LivingWorkspace (to be merged) |
| master | a59b5cd | LEGACY — LivingWorkspace (to be merged) |
| main | a9d481f | HERITAGE FORK — WorkspaceContainer architecture |
| workspace-convergence | 2280f1f | LEGACY — LivingWorkspace parallel branch |

## Commits on Primary Workspace Recovery Branch

| SHA | Description | Category |
|-----|-------------|----------|
| d4e38ff | M2B-EXT: Auth verification gate + personal context switch + ownership/context docs | Authorized remediation |
| a4ba91d | M2B: Closure report — browser-accepted | Documentation |
| 83faba0 | M2B: Fix SPA routing — serve SPA for all /workspace/* paths | Authorized remediation |
| 6e104c1 | M2B: PrimaryWorkspace recovery — restore organizational domain architecture | Authorized application work |

## Security Fixes Applied

1. **Login verification gate** — `/login` now requires `verified=True` before allowing session creation. Previously, unverified accounts could log in after signup. (Fix in `app/auth_routes.py`)

2. **Personal context switch** — Added `POST /api/v1/for2/organizations/switch/personal` endpoint. Previously returned 404, breaking bidirectional context switching. (Add in `app/for2/routes.py`)

## Remaining Gaps (Explicit)

| Gap | Severity | Section | Action Required |
|-----|----------|---------|----------------|
| Finance workspace is PLACEHOLDER | Medium | §10 | Build dedicated Finance workspace component |
| Knowledge workspace is PLACEHOLDER | Medium | §10 | Build dedicated Knowledge workspace component |
| Operations workspace NOT IMPLEMENTED | Low | §10 | Product decision: build or deprecate |
| Session keys cleared on exempt-path requests | Low | §7 | Pre-existing bug in `_check_auth` middleware |
| Email SMTP credentials not configured | Low | §5.2 | Set EMAIL_USER/EMAIL_PASSWORD env vars |
| Production tests (Section 18) | Medium | §18 | Full suite running via subagent |
| Browser journeys (Section 20) | Medium | §20 | Basic journeys tested; full lifecycle pending |