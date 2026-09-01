# SHUNYA FCR REMEDIATION PLAN

> **Date:** 2026-09-01
> **HEAD:** 272dbad
> **Directive:** FCR-01.1 Step 58-60

---

## PATH C: SYSTEMIC REMEDIATION REQUIRED

**Decision:** The architecture is sound and converging. However, the evidence reveals **systemic gaps across data, frontend integration, and certification** that cannot be resolved with a single surgical fix. Multiple foundational domains lack data, the evidence chain is broken, and certification evidence is missing across 7 FDA gates.

---

## Remediation Priority Order

### PHASE 1 — Architecture Consolidation (P1)

| Item | Root Cause | Target | Effort | Depends On |
|------|-----------|--------|--------|------------|
| R1.1 | Consolidate 4 object stores → 1 (sh_objects) | Migrate sh_uop_objects, founder_objects, objects into sh_objects | 3-5 sessions | None |
| R1.2 | Consolidate 3 identity tables → 1 (PersonIdentity) | Migrate SHUNYAIdentity writes to PersonIdentity | 1-2 sessions | R1.1 |
| R1.3 | Wire 10 UCP engines into AI retrieval | Make ask() call UCP-02 through UCP-11 | 3-4 sessions | R1.1 |
| R1.4 | Wire 8 intelligence engines into learning loop | Connect core/intelligence/* to learning_loop.py | 2-3 sessions | R1.3 |

### PHASE 2 — Data Foundation (P1-P2)

| Item | Root Cause | Target | Effort | Depends On |
|------|-----------|--------|--------|------------|
| R2.1 | Seed cross-domain demo data | Populate proposals, customers, suppliers, ledger, payments, budgets with realistic data | 1-2 sessions | R1.1 |
| R2.2 | Wire execution → evidence pipeline | Ensure every execution creates evidence_records, decision_traces, observations | 2-3 sessions | R1.1 |
| R2.3 | Seed knowledge_entries | Populate knowledge graph with business data | 1 session | R2.1 |

### PHASE 3 — Frontend AI Integration (P1)

| Item | Root Cause | Target | Effort | Depends On |
|------|-----------|--------|--------|------------|
| R3.1 | Wire CommandPalette to IntelligenceRuntime | Convert from client-only navigation to AI-capable surface | 2-3 sessions | R1.3 |
| R3.2 | Wire executive home cockpit | Connect executive-home.tsx to /api/v1/founder/executive-home | 1-2 sessions | R2.1 |
| R3.3 | Add AI access to every sidebar surface | Every domain workspace gets contextual AI button | 3-4 sessions | R3.1, R1.3 |

### PHASE 4 — Certification (P2)

| Item | Root Cause | Target | Effort | Depends On |
|------|-----------|--------|--------|------------|
| R4.1 | Run full business simulation | Execute Marketing→Lead→Sales→Customer→Invoice→Payment→Finance→Audit | 1-2 sessions | R2.1 |
| R4.2 | Establish DR (backup + restore) | Automate pg_dump; prove clean-environment restore | 1 session | None |
| R4.3 | Performance baseline | Measure homepage, AI, search, API latency; set budgets | 1 session | None |
| R4.4 | Browser certification | Run desktop/tablet/mobile matrix against current SHA | 1-2 sessions | None |
| R4.5 | Negative security tests | Cross-tenant, IDOR, replay, expired session tests | 1 session | None |
| R4.6 | Full A-K E2E intelligence journeys | Write 11 E2E tests covering all intelligence paths | 2-3 sessions | R1.3 |
| R4.7 | Action classification registry | Implement READ/ANALYZE/CREATE/UPDATE/DELETE/EXECUTE registry | 1 session | None |
| R4.8 | Clean migration chain | Resolve multiple alembic heads | 1 session | None |

### PHASE 5 — Launch Rehearsal (P2-P3)

| Item | Root Cause | Target | Effort | Depends On |
|------|-----------|--------|--------|------------|
| R5.1 | Public launch rehearsal | Clean environment deployment, full smoke test, rollback test | 1 session | R4.1-4.8 |
| R5.2 | Founder acceptance | Independent founder verification | 1 session | R5.1 |

---

## Summary

| Phase | Items | Est. Effort | Priority |
|-------|-------|-------------|----------|
| PHASE 1 — Architecture Consolidation | 4 | 10-14 sessions | P0-P1 |
| PHASE 2 — Data Foundation | 3 | 4-6 sessions | P1-P2 |
| PHASE 3 — Frontend AI Integration | 3 | 6-9 sessions | P1 |
| PHASE 4 — Certification | 8 | 9-11 sessions | P2 |
| PHASE 5 — Launch Rehearsal | 2 | 2 sessions | P2-P3 |
| **TOTAL** | **20** | **31-42 sessions** | |

---

## Recommended Next Directive

**Do not issue another broad FCR directive.**

Issue a single **consolidated surgical remediation directive** covering:
1. Object store consolidation (R1.1)
2. Identity consolidation (R1.2)  
3. AI engine wiring (R1.3-R1.4)
4. Demo data seeding (R2.1)
5. Evidence pipeline wiring (R2.2)
6. Frontend AI integration (R3.1-R3.3)

Then issue a separate **certification directive** covering:
7. Business simulation (R4.1)
8. DR + performance + browser + security (R4.2-R4.7)
9. Migration cleanup (R4.8)
10. Launch rehearsal (R5.1)
11. Founder acceptance (R5.2)

This breaks the remaining work into two manageable directives rather than one giant directive.