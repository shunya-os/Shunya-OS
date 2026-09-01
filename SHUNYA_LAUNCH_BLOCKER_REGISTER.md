# SHUNYA LAUNCH BLOCKER REGISTER

> **Date:** 2026-09-01
> **HEAD:** 272dbad
> **Directive:** FCR-01.1 Steps 44-46

---

## P0 — CRITICAL

None identified.

## P1 — LAUNCH BLOCKER

| ID | Area | Finding | User Impact | Evidence | Root Cause | Required Action | Dependencies |
|----|------|---------|-------------|----------|------------|----------------|--------------|
| LB-01 | Architecture | 4 object stores (sh_objects, sh_uop_objects, founder_objects, objects) — NOT canonical | AI, search, and execution may read/write different object stores, producing inconsistent results | 4 tables with 175 total objects; no ID overlap | Transitional dual-write bridge never completed | Merge all object stores into sh_objects; decommission others | None |
| LB-02 | Architecture | 3 identity tables (team_members, shunya_identities, person_identities) — divergent | User identity may resolve differently depending on table queried | 11 shunya_identities, 0 person_identities — divergent | Identity convergence incomplete | Consolidate identity writes into PersonIdentity; decommission SHUNYAIdentity | None |
| LB-03 | Frontend | CommandPalette client-only navigation, no AI connection | Users cannot invoke SHUNYA intelligence from Cmd+K | command-palette.tsx dispatches client events, never calls /api/v1/ai/chat | Original design used client-side navigation | Wire CommandPalette to IntelligenceRuntime | G10 closure |
| LB-04 | Frontend | Executive home does not display full signal cockpit | Founder sees domain workspace, not "What changed? / risks / next actions" | executive-home.tsx renders domain-selector, not full briefing | Backend API exists but frontend doesn't consume it | Wire executive-home.tsx to /api/v1/founder/executive-home | G10 closure |
| LB-05 | Data | Evidence chain broken: 0 executions, 0 decision_traces, 0 observations | No auditable record of AI decisions or system actions | execution_logs=0, decision_traces=0, observations=0 | Execution engine never triggered with real data, logging not wired | Wire execution → evidence → decision → observation pipeline | Object consolidation |
| LB-06 | Business | 8 domains have zero data: proposals, customers, suppliers, ledger, payments, budgets, notifications, knowledge_entries | Business simulation cannot run | proposals=0, customer=0, suppliers=0, fin_ledger=0, fin_payments=0, fin_budgets=0, notifications=0, knowledge_entries=0 | No demo/seed data across business verticals | Seed realistic demo data across all domains | None |
| LB-07 | Intelligence | 10 UCP engines + 8 intelligence engines not wired to SHUNYAAI | AI cannot reason about finance, operations, relationships, etc. | core/*_intelligence/ exist but no consumer | Engines built but never connected to retrieval pipeline | Wire UCP engines into ask() retrieval | None |

## P2 — CERTIFICATION GAP

| ID | Area | Finding | Evidence |
|----|------|---------|----------|
| CG-01 | DR | No automated backup schedule; no proven restore | Deploy.sh attempts pg_dump but fails on permissions; no restore test |
| CG-02 | Performance | No latency budgets, no load test | 3 gunicorn workers; no performance data collected |
| CG-03 | Browser | Formal browser certification not run | No browser matrix against current SHA |
| CG-04 | Security | No negative cross-tenant tests | No test for cross-tenant access, IDOR, replay |
| CG-05 | Security | No action classification registry | No READ/ANALYZE/CREATE/UPDATE/DELETE/EXECUTE registry |
| CG-06 | Business | Full business simulation not run | All routes exist but lifecycle not executed |
| CG-07 | E2E | 0 full A-K intelligence journeys | Only convergence tests exist (20) |
| CG-08 | Frontend | No sidebar surface has AI integration | Only Home/CommandSurface has AI |

## P3 — PRODUCT QUALITY

| ID | Area | Finding |
|----|------|---------|
| PQ-01 | Intelligence | 5 orphan runtimes without callers |
| PQ-02 | Intelligence | No cost-aware AI routing |
| PQ-03 | Frontend | AIResidentPanel status unknown |
| PQ-04 | Data | 0 knowledge_entries (knowledge not populated) |
| PQ-05 | Data | 0 document_records (canonical doc table empty) |

## P4 — MAINTENANCE

| ID | Area | Finding |
|----|------|---------|
| MT-01 | Code | TODO in homepage.tsx (hero artwork) |
| MT-02 | Code | NotImplementedError in base classes (expected) |
| MT-03 | Architecture | Orphan runtimes without consumers |
| MT-04 | Data | Legacy tables empty (lead, task, invoices) |
| MT-05 | Migration | Migration chain has multiple heads |