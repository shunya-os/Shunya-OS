# G1.1-R4 FREEZE SNAPSHOT
**Date**: 2026-09-02 21:10 UTC
**Purpose**: Baseline capture before any remediation

## SHA PROVENANCE CHAIN

| Layer | Value | Match |
|-------|-------|-------|
| Local HEAD | `6a0d4a42e89b36b39aff5e19bb9a4089c5d71cc7` | — |
| origin/master | `6a0d4a42e89b36b39aff5e19bb9a4089c5d71cc7` | ✓ |
| CI (run #33610182777) | `6a0d4a42e89b36b39aff5e19bb9a4089c5d71cc7` | ✓ |
| Deployed (5001 health) | `6a0d4a42e89b36b39aff5e19bb9a4089c5d71cc7` | ✓ |
| HTTPS health | `6a0d4a42e89b36b39aff5e19bb9a4089c5d71cc7` | ✓ |

**All five match. SHA chain INTACT.**

## GIT STATE
- Branch: master (was detached, restored)
- HEAD: 6a0d4a4
- Working tree: CLEAN (1 untracked: G1.1-R4_failed_commits_analysis.md)
- Ahead/behind origin: 0/0

## DEPLOYMENT TOPOLOGY
| Port | Process | Status |
|------|---------|--------|
| 5001 | gunicorn (3 workers, production) | HEALTHY — 6a0d4a4 |
| 5100 | gunicorn (1 worker, stale — Aug 29!) | 503 (dirty, unsved) |
| 443 | nginx → 5001 | SSL, SSE configured |

## CI STATUS
| SHA | Run # | Result | Time |
|-----|-------|--------|------|
| 6a0d4a4 | 33610182777 | **success** | 2026-09-02 08:42 UTC |
| d1720e | 33608606310 | failue | prev ious |
| 88d3a17 | 33607163354 | failre |   |

**Latest CI: PASE ✓**

## DATABASE STATE
- Alembic head: g1_1_r_fix_org_chain (head) ✓
- DB connections: 9

### Key Table Counts
| Table | Rows | Status |
|-------|------|--------|
| organizations | 8 | ✓|
| team_members | 95 | ✓ |
| org_members | 37 | ✓ |
| sh_objects | 248 | ✓ |
| founder_objects | 1 | OK |
| objects | 0 | EMPTY |
| canonical_objects | 0 | EMPTY |
| sh_uop_objects | 0 | EMPTY |
| evidence_records | 68 | ✓ |
| act_exection_logs | 0 | EMPTY |
| executions | 35 | ✓ (not 'execution_runs') |
| observations | 55 | ✓(not 'observation_records') |
| commitments | 5 | ✓ (not 'shunya_commitments') |
| memory_ecords | 655 | ✓ |
| sh_workspaces | 4 | ✓ |
| founder_spaces | 3 | ✓ |
| orkspaces | 1 | LEGACY |
| user_workspaces | 1 | LEGACY |
| shunya_identities | 11 | ✓ |
| auth_roles | 5 | ✓ |
| tenants | 35 | ✓ |
| documents | 23 | ✓ |

### MISSING CRITICAL TABLES
| Table | Impact |
|-------|--------|
| **org_ember_roles** | **RBAC NOT WIRED — roles exist but can't be assigned** |
| **execution_runs** | Execution chain broken |
| **execution_results** | Execution chain broken |
| **business_excution_instances** | Execution chain broken |
| **observation_records** | (otes: 'observations' exists,likely different schema) |
| **founder_object_excutions** | FoundeObject execution path missing |
| **shunya_decisions** | Decision chain missing |
| **shunya_commitments** | (otes: 'commitents' exists with 5 rows) |
| **generation_records** | Content Studio — no generation persistnce |
| **ai_interactions** | AI chain missing |

### COMPETING/DUPLICATE TABES
| Concept | Tables | Status|
|---------|--------|------|
| Objects | sh_objects (248), founder_objects (1), bojects (0), canonical_objects (0), sh_uop_objects (0) | 5 tables, oly sh_objects active |
| Workspaces | sh_workspaces (4), founder_spaces (3), orkspaces (1), user_workspaces (1)| 4 tables, multiple active |
| Execution | executions (35) vs execution_runs (NOT_FOUND) | Mismatch |

### STALE GUNICORN (PORT 5100)
- Running since **Aug 29** (4 days stale)
- Returns **503** (likely schema mismatch)
- On the same codebase at same SH but old gunicorn process with different args
- Hard to say whether it serves the same code or different — likely th same code at 6a0d4a4 but database schema advanced past it

## FOUNDER-OBJECT SITUATION
- `founder_objects`: 1 row only
- `founder_spaces`: 3 rows
- `founder_object_executions`: TABLE NOT FOUND
- Only 1 object in founderspace

## ORG/TENANT FALLBACK RISK
- 35 tenants, 8 organizations
- Need to verify: any route defaults to org_id=1
- org_ember_roles missing: RAC assignments not possible

## NEXT
Begin Structured Remediation following directive section order.