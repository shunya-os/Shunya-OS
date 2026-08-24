# ZGC-PR-11: Execution Governance Framework

Status: Ratified
Authority: Founder Directive (P0 — MANDATORY)
SHA: 23c971e

This directory contains the execution governance framework mandated by ZGC-PR-11.
Referenced by the Course-Change Ledger and obstacle protocol.

## Framework Files

Located in `.hermes/scratch/` (outside repository working tree):

| File | Purpose |
|------|---------|
| COURSE_CHANGE_LEDGER.md | Every material execution deviation with evidence |
| PROOF_HIERARCHY.md | Evidence layers: code → service → API → UI → journey |
| OBSTACLE_PROTOCOL.md | Required action when proof fails |
| CHECKPOINT_PROTOCOL.md | Resume-only when platform limits reached |
| QUALITY_REGISTRY.md | Unified signal register across all quality dimensions |
| SKIP_REGISTRY.md | All 107 skipped tests classified with ownership |
| WARNING_CENSUS_COMPARISON.md | 15,147 anomaly reproduction analysis |
| TEMPORAL_CONTRACT.md | Canonical SHUNYA temporal model |
| ENV_MATRIX.md | Capability matrix across local/CI/production |
| STATUS_REPORT.md | Current milestone progress |
| EVIDENCE/shunyaos_public.png | Fresh browser evidence (SHA 23c971e) |

## Key Milestones

### Execution Truth
- M0-M3: SHA provenance established (HEAD = origin/master = production = 23c971e)
- M4-M9: Governance framework operational

### Quality
- M10: Suite command frozen
- M11-M14: CI warning baseline (11,551) established; 15,147 anomaly open (environment no longer reproducible)
- M15: 107 skips classified
- M16: Isolation defect resolved (PostgreSQL 5433 env-specific)
- M17-M18: Temporal contract and env matrix documented

### Release
- M19-M20: Tree boundaries clean (stale process killed, untracked files removed)
- M21-M23: CI/CD deploy pending (clean tree ready, requires push trigger)