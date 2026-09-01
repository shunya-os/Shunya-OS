# SHUNYA OS — G1 DEPENDENCY GRAPH

**What unlocks what — the critical path to product completion.**

---

## PRINCIPLE

No gate may be entered until its dependencies are genuinely CLOSED. A gate is CLOSED when every capability in that gate has been proven end-to-end through the product, not merely through backend tests.

---

## GATE DEPENDENCY MAP

```
G1 ── CANONICAL CONVERGENCE (CURRENT)
 │
 ├── G2 ── DATA & INTEGRATION FABRIC
 │    │     (file upload, extraction, OAuth, webhooks, search, import/export)
 │    │
 │    ├── G3 ── SHUNYAAI INTELLIGENCE LAYER
 │    │    │     (capability registry, execution chain, pipeline, memory loop)
 │    │    │
 │    │    ├── G4 ── SALES / CRM
 │    │    │    │     (leads, pipeline, proposals, customer experience)
 │    │    │    │
 │    │    │    ├── G5 ── MARKETING (campaigns, content, analytics)
 │    │    │    │
 │    │    │    ├── G6 ── OPERATIONS / EXECUTION
 │    │    │    │    │     (workflows, jobs, automation)
 │    │    │    │    │
 │    │    │    │    ├── G7 ── FINANCE (invoices, ledger, payments, budget)
 │    │    │    │    │
 │    │    │    │    ├── G8 ── TAX / COMPLIANCE / AUDIT
 │    │    │    │    │
 │    │    │    │    └── G9 ── PEOPLE / ADMIN / GOVERNANCE
 │    │    │    │
 │    │    │    └── G10 ── FRONTEND / UX / PRODUCT COMPLETION
 │    │    │              │     (every surface, responsive, voice, i18n)
 │    │    │              │
 │    │    │              └── G11 ── SECURITY / RELIABILITY / SCALE
 │    │    │                        │     (diagnostics, degradation, rate limiting)
 │    │    │                        │
 │    │    │                        └── G12 ── FOUNDER ACCEPTANCE / LAUNCH
 │    │    │
 │    │    └── G3 BLOCKERS:
 │    │         • Identity convergence (G1)
 │    │         • Object store convergence (G1)
 │    │         • Knowledge API routes (G1)
 │    │         • Memory API routes (G1)
 │    │
 │    └── G2 BLOCKERS:
 │         • Object store convergence (G1)
 │         • Identity convergence (G1)
 │
 └── G1 INTERNAL DEPENDENCIES:
      • Identity convergence → object store convergence → data path
      • Knowledge API → knowledge browser works
      • Memory API → memory browser works
      • Finance frontend → finance API used
      • Operations domain → built from scratch
```

---

## CRITICAL PATH (Shortest path to launch-ready)

```
1. Identity convergence (G1-02) ─── 1 week
2. Object store convergence (G1-03) ─── 1 week
3. Knowledge API routes (G1-06) ─── 2 days
4. Memory API routes (G1-07) ─── 2 days
5. Finance frontend component (G1-08) ─── 3 days
6. Frontend ask URL fix (G1-01) ─── ✅ DONE
7. Operations domain (G1-09) ─── 1 week
8. Real-time conversations (G1-12) ─── 3 days
9. Task creation + per-lead (G1-13) ─── 2 days
10. Universal search (G1-05) ─── 1 week
─── After G1 complete ───
11. WhatsApp + client portal + payments (P-01/02/03) ─── 2 weeks
12. Mobile responsive (G1-20) ─── 1 week
13. i18n (P-08) ─── 1 week
14. Victory/celebration (P-05) ─── 3 days
```

---

## G1 ACCEPTANCE GATES

| Gate | Requirement | Status |
|------|-------------|--------|
| G1-ARCH-01 | One canonical identity owner | ❌ OPEN |
| G1-ARCH-02 | One canonical object owner | ❌ OPEN |
| G1-ARCH-03 | One canonical event/data path | ✅ CLOSED |
| G1-ARCH-04 | One canonical evidence path | ✅ CLOSED |
| G1-ARCH-05 | One canonical observation path | ✅ CLOSED (FCR-02) |
| G1-ARCH-06 | One canonical memory owner | ✅ CLOSED |
| G1-ARCH-07 | One canonical decision path | ✅ CLOSED |
| G1-ARCH-08 | One canonical execution path | ✅ CLOSED (FCR-02) |
| G1-ARCH-09 | All duplicates classified | ✅ CLOSED (this document) |
| G1-INT-01 | Frontend capability ledger exists | ✅ CLOSED (this document) |
| G1-INT-02 | Backend capability ledger exists | ✅ CLOSED (this document) |
| G1-INT-03 | Product promise ledger exists | ✅ CLOSED (this document) |
| G1-INT-04 | Every frontend feature has backend contract | ✅ CLOSED (this document) |
| G1-INT-05 | Every backend capability has product status | ✅ CLOSED (this document) |
| G1-INT-06 | Every visible action has real completion path | ❌ OPEN (finance, knowledge, memory, operations) |
| G1-INT-07 | No dead buttons | ❌ OPEN |
| G1-INT-08 | No dead-end workflows | ❌ OPEN |
| G1-AI-01 | All user-facing AI enters canonical fabric | ✅ CLOSED (FCR-02) |
| G1-AI-02 | Company context precedes external research | ✅ CLOSED (FCR-02) |
| G1-AI-03 | Facts/inference separated | ✅ CLOSED (FCR-02) |
| G1-AI-04 | Confidence meaningful | ✅ CLOSED (FCR-02) |
| G1-AI-05 | Tool permissions governed | ✅ CLOSED (FCR-02) |
| G1-AI-06 | AI outputs connect to evidence/observation | ✅ CLOSED (FCR-02) |
| G1-AI-07 | Learning influences future context | ✅ CLOSED (FCR-02) |
| G1-AI-08 | No duplicate AI authority | ⚠️ PARTIAL (3 duplicate AI routes remain) |
| G1-UX-01 | Visual constitution preserved | ✅ CLOSED |
| G1-UX-02 | Object-first principle preserved | ✅ CLOSED |
| G1-UX-03 | Loading states complete | ❌ OPEN |
| G1-UX-04 | Empty states complete | ❌ OPEN |
| G1-UX-05 | Error states complete | ❌ OPEN |
| G1-UX-06 | Recovery states complete | ❌ OPEN |
| G1-RL-01 | Idempotency | ✅ CLOSED (FCR-02) |
| G1-RL-02 | Retry safety | ✅ CLOSED (FCR-02) |
| G1-RL-03 | Reconnect | ❌ OPEN |
| G1-RL-04 | Partial failure | ✅ CLOSED (FCR-02) |
| G1-RL-05 | Provider failure | ✅ CLOSED (FCR-02) |
| G1-RL-06 | Model failure | ❌ OPEN |
| G1-RL-07 | Persistence failure | ✅ CLOSED |
| G1-RL-08 | Tenant isolation | ✅ CLOSED (FCR-02) |

---

## G1 INTERNAL WORK ORDER

| Order | Work Item | Depends On | Est. Effort |
|-------|-----------|-----------|-------------|
| 1 | Identity convergence | None | 1 week |
| 2 | Object store convergence | Identity | 1 week |
| 3 | Knowledge API routes | Object store | 2 days |
| 4 | Memory API routes | Object store | 2 days |
| 5 | Finance frontend | Object store | 3 days |
| 6 | Operations domain | Object store | 1 week |
| 7 | Real-time conversations | None | 3 days |
| 8 | Universal search engine | Object store | 1 week |
| 9 | Task creation/per-lead | Object store | 2 days |
| 10 | UX state audit (loading/empty/error) | None | 2 days |
| 11 | No-dead-end audit | All above | 2 days |

---

*This dependency graph is the single authoritative execution plan. Work must follow dependency order.*