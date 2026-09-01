# SHUNYA OS — G1 CANONICAL ARCHITECTURE MAP

**Directive:** G1 — Canonical Convergence & Zero-Gap Product Foundation
**Date:** 2026-09-01
**Status:** RATIFIED — This is the single authoritative architecture diagram.

---

## 1. CANONICAL DATA LIFECYCLE

Every meaningful piece of information entering SHUNYA follows this path:

```
SOURCE
  │
  ▼
INGESTION ─── Identity Resolution ─── Canonical Object
  │                                         │
  │                                         ├── Relationship
  │                                         ├── Evidence
  │                                         ├── Observation
  │                                         ├── Memory (where appropriate)
  │                                         ├── SHUNYAAI Context
  │                                         ├── Decision
  │                                         ├── Execution (where applicable)
  │                                         ├── Outcome
  │                                         └── Learning
  │
  └── All paths: tenant_id + identity_id + provenance enforced at every step
```

**Rule:** No integration or data path may bypass this architecture. User input, imports, Gmail, WhatsApp, webhooks, APIs, documents, AI-generated content — all converge through the same canonical pipeline.

---

## 2. CANONICAL OBJECT OWNERSHIP

| Concept | Canonical Owner | Status |
|---------|----------------|--------|
| **Identity** | `app/auth.py` (TeamMember) + `app/models.py` (OrgMember) + `app/production/identity_repository.py` (SHUNYAIdentityModel) | ⚠️ **TO BE CONVERGED** — 3+ implementations |
| **Organization** | `app/models.py` (Organization) → `app/founder/models.py` (FounderSpace with space_type="organization") | ⚠️ DUPLICATE — needs consolidation |
| **Workspace** | `app/production/identity/workspace_model.py` (Workspace) | ✅ CANONICAL |
| **Person** | `app/people/` (Person, OrgMember) | ✅ CANONICAL |
| **Object** | `app/objects/` (ShunyaObject + sh_objects table) | ⚠️ **5 competing stores** — see §3 |
| **Lead** | `app/leads/` (Lead) + `app/crm/` (Lead) | ⚠️ DUPLICATE — cross-referenced |
| **Customer** | `app/customers/` (Customer) | ✅ CANONICAL |
| **Supplier** | `app/models.py` (Supplier) | ✅ CANONICAL |
| **Conversation** | `app/communication/` (ExternalConversation, ExternalMessage) | ✅ CANONICAL |
| **Task** | `app/tasks/` (Task) | ✅ CANONICAL |
| **Commitment** | `app/commitments/` (Commitment) | ✅ CANONICAL |
| **Project** | No canonical owner | ❌ MISSING |
| **Opportunity** | `app/commercial/` (CommercialOpportunity) | ✅ CANONICAL |
| **Quote** | `app/commercial/` (CommercialProposal) | ✅ CANONICAL |
| **Proposal** | `app/commercial/` (CommercialProposal) + `app/communication/` (MessageProposal) | ✅ CANONICAL |
| **Invoice** | `app/finance/models.py` (FinInvoice) | ✅ CANONICAL |
| **Payment** | `app/finance/models.py` (FinancePayment) | ✅ CANONICAL |
| **Expense** | `app/finance/models.py` (LedgerEntry with type=expense) | ✅ CANONICAL |
| **Document** | `app/document/` (DocumentRecord, DocumentSection) | ✅ CANONICAL |
| **Knowledge Item** | `app/models.py` (KnowledgeDocument) + `app/knowledge/` | ⚠️ PARTIAL — no API routes |
| **Memory** | `app/memory/models.py` (MemoryRecord) + `app/memory_api/` | ⚠️ PARTIAL — minimal API |
| **Campaign** | `app/campaign/` (Campaign) | ✅ CANONICAL |
| **Content** | `app/content_studio/` (ContentGeneration) | ✅ CANONICAL |
| **Event** | `app/events/` (Event) | ✅ CANONICAL |
| **Execution** | `app/execution_engine/` (Execution, ExecutionLog) | ✅ CANONICAL |
| **Evidence** | `app/evidence/models_db.py` (EvidenceRecord) + `app/evidence/decision_trace.py` (DecisionTrace) | ✅ CANONICAL |
| **Observation** | `app/shunya/observer_learning.py` (Observation) — 21 cols, reconciled | ✅ CANONICAL (FCR-02) |
| **Outcome** | `app/execution/models.py` (Outcome) | ✅ CANONICAL |
| **Learning Event** | `app/intelligence/models.py` (LearningEvent) | ✅ CANONICAL |
| **Pattern** | `app/intelligence/models.py` (Pattern) | ✅ CANONICAL |

---

## 3. OBJECT STORE CONVERGENCE (6 competing tables)

| Table | Location | Object Type | Status | API |
|-------|----------|-------------|--------|-----|
| `sh_objects` | `app/objects/` | Generic objects | ✅ CANONICAL | `/api/v1/objects` |
| `objects` | `app/objects/legacy_models.py` | Legacy workspace objects | ⚠️ MIGRATION SOURCE | `/objects/<id>` (legacy) |
| `founder_objects` | `app/founder/models.py` | Founder objects | ✅ CANONICAL (data) | `/api/v1/founder/objects` |
| `canonical_objects` | `core/object/` | Core domain objects | ⚠️ DUPLICATE | No frontend path |
| `sh_uop_objects` | `app/objects/uop_models.py` | UOP objects | ⚠️ DUPLICATE | `/api/v1/uop/objects` |
| `object_relations` | `app/graph/models.py` | Object relationships | ⚠️ MIGRATION SOURCE | No API |

**Migration plan:** All object data converges to `sh_objects` via `app/objects/` API. Legacy tables (`objects`, `object_relations`) become migration sources. `canonical_objects` and `sh_uop_objects` are DUPLICATE — their consumers are redirected to `sh_objects`.

---

## 4. IDENTITY CONVERGENCE (5 user/identity tables)

| Table | Role | Status |
|-------|------|--------|
| `team_members` | Primary auth identities | ⚠️ TO BE CANONICAL |
| `m9_team_members` | Auth identities (duplicate?) | ⚠️ DUPLICATE |
| `org_members` | Organization membership | ✅ CANONICAL |
| `persons` | People profiles | ✅ CANONICAL |
| `person_identities` | Identity→person links | ✅ CANONICAL |

**Target:** `team_members` → canonical identity authority. `org_members` → membership. `persons` → profile. `m9_team_members` → merged into team_members.

---

## 5. CANONICAL AI PIPELINE

```
Frontend Request
  │
  ▼
Canonical API (/api/v1/intelligence/ask)
  │
  ├── 1. Identity & Tenant Resolution
  ├── 2. Safety Governance (age + explicit + injection)
  ├── 3. Company Evidence Gathering (org, objects, documents, memory, finance)
  ├── 4. SHUNYAAI Multi-Engine Pipeline
  │     ├── PERCEPTION → structured observation
  │     ├── CONTEXT ASSEMBLY → evidence + memory enrichment
  │     ├── REASONING → deterministic deduction
  │     ├── PLANNING → action plan generation
  │     ├── DECISION → option selection
  │     ├── REFLECTION → outcome evaluation
  │     ├── LEARNING → pattern extraction
  │     └── CONFIDENCE → overall score
  ├── 5. Inference Governance (deterministic-first → LLM)
  ├── 6. Evidence Record
  ├── 7. Observation Record
  ├── 8. Memory Persistence (observation→memory bridge)
  └── 9. Response → Frontend
```

**Rule:** No surface may bypass this pipeline. Every AI capability uses this path. No duplicate AI routes.

---

## 6. DEPLOYMENT TOPOLOGY

```
Internet → Nginx (HTTPS) → Gunicorn (Flask) → PostgreSQL + Redis
                              │
                              ├── Serve SPA (frontend/dist/)
                              ├── API routes (82 blueprints, ~610 routes)
                              └── Static assets
```

---

## 7. CURRENT FRONTEND→BACKEND CONTRACTS

See `G1_FRONTEND_BACKEND_MATRIX.md` for the complete per-route capability matrix.
See `G1_PRODUCT_CAPABILITY_LEDGER.md` for the complete product promises.
See `G1_MISSING_CAPABILITY_REGISTER.md` for gaps classified by type.

---

*This document is the single authoritative architecture representation. No implementation, PRD, or design document may contradict it.*
