# SHUNYA FCR-02 BASELINE

> **Date:** 2026-09-01
> **HEAD:** 26c68bd
> **Directive:** FCR-02 — Systemic Remediation

---

## Repository

| Item | Value |
|------|-------|
| Branch | master |
| HEAD | 26c68bd |
| Origin/master | 26c68bd (in sync) |
| Working tree | CLEAN |
| Production SHA | 26c68bd (verified) |

## Database

| Item | Count |
|------|-------|
| Alembic | zgc_pr_17c_durable_memory (applied) |
| sh_objects | 4 |
| sh_uop_objects | 85 |
| founder_objects | 45 |
| objects (legacy) | 41 |
| team_members | 11 |
| shunya_identities | 11 |
| person_identities | 0 |
| memory_records | 24 |
| executions | 0 |
| execution_logs | 0 |
| evidence_records | 14 |
| decision_traces | 0 |
| observations | 0 |
| job_records | 0 |

## Known Blockers

| ID | Area | Status |
|----|------|--------|
| LB-01 | 4 object stores, not canonical | OPEN |
| LB-02 | 3 identity tables, divergent | OPEN |
| LB-03 | CommandPalette client-only | OPEN |
| LB-04 | Executive home not fully wired | OPEN |
| LB-05 | Evidence chain broken (0 executions) | OPEN |
| LB-06 | 8 domains with zero data | OPEN |
| LB-07 | 3 UCP engines not wired to AI | OPEN |

## Dead Code to Remove

| Item | Location | Reason |
|------|----------|--------|
| intelligence_routes.py | app/intelligence_routes.py | UNREGISTERED, 217 lines, no callers |
| 8 intelligence engines | core/intelligence/{perception,context_assembly,...,confidence} | Abstract bases, zero callers, never wired |
| execution_bp duplicate | app/__init__.py:671 + 844 | Same blueprint registered twice |
| execution_intelligence | app/execution_intelligence/ | Archived stub, empty |
| app/learning_intelligence/ | app/learning_intelligence/ | Superseded by runtime learning loop |

## Launch Blockers

**7 P1 blockers remain from FCR-01.1-C. This directive begins remediation of all 7.**