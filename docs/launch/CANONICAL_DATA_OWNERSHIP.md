# Canonical Data Ownership

**Date:** 2026-08-14  
**Authority:** Foundational constitutional decision required

---

## Principle

One canonical production owner per core concept.

## Ownership Map

| Concept | Canonical Store | Writers | Readers | Legacy/Orphan Stores | Migration Strategy |
|---------|----------------|---------|---------|---------------------|-------------------|
| Object | **sh_objects** (ShunyaObject) | API: `/api/v1/objects/` → sh_objects. execution/recovery | reality_engine, events/SSE, search, workspace | founder_objects (508, founder workspace), objects (31, PROD-05), canonical_objects (2, orphan) | Alias founder_objects through sh_objects view. Deprecate objects table. Drop canonical_objects. |
| Person | **persons** (Persons) | CRM lead creation creates Person | identity resolution | person_identities (0, empty canonical) | Wire PersonIdentity into auth flow or deprecate. |
| Customer | **customer** (Customer, __tablename__="customer") | CRM: convert_to_customer | customer_experience/service | customers (0, orphan table, no model) | Drop `customers` table. Confirm __tablename__="customer" is intended. |
| Lead | **leads** (Lead) | CRM: create_lead, leads API | CRM routes, reports | — | Single store, working. |
| Commitment | **commitments** (Commitment) | API: POST /api/v1/commitments/ | Workspace, runtime/loop | relationship_commitments (0) | Use commitments as primary. |
| Task | **tasks** (Task) | Task API, follow-up creation | Workspace | — | Single store. |
| Evidence | **evidence_records** (EvidenceRecord) | log_evidence (AI, CRM), document_knowledge, execution idempotency, import_export | execution_engine (hard gate), audit | act_execution_logs (1769, execution traces), decision_traces (0) | **Now populated** (7 rows). act_execution_logs serves execution trace, not evidence. |
| Outcome | **outcomes** (Outcome) | execution_engine | Reports | sh_outcomes (3) | Merge sh_outcomes into outcomes. |
| Document | **document_records** (DocumentRecord) | documents_knowledge API | document runtime | documents (0), knowledge_documents (0), knowledge_facts (0) | Single store, empty (0 rows). Needs end-to-end exercise. |
| Knowledge | **knowledge_entries** | FOR-1 engine, search | app/search.py | knowledge_facts (0), knowledge_documents (0) | knowledge_entries works (43 rows). Deprecate others. |
| Audit | **user_activity_logs** (default) | Route middleware, actions | Admin | genesis_audit_log (0), sh_audit_logs (2), m9_audit_records (0), evidence_records (7) | Consolidate into one canonical audit store post-launch. |
| Identity | **team_members** (auth) + **shunya_identities** (kernel) | Login (TeamMember), OAuth (SHUNYAIdentityModel) | Auth middleware | person_identities (0, canonical but empty) | Current dual-store accepted. person_identities: wire into auth or deprecate. |

## Critical Decisions Required

1. **Confirm sh_objects as canonical object store.** alias/read founder_objects through sh_objects interface.
2. **Drop orphan tables:** `customers` (no model), `canonical_objects` (no code refs), `sh_outcomes` (after merge).
3. **Resolve identity:** accept current TeamMember + SHUNYAIdentity dual system, or invest in PersonIdentity.
4. **Consolidate audit:** which store is canonical? user_activity_logs is most populated (287 rows).
5. **Commitment → execution → evidence:** flow works in code but has 0 data. Needs end-to-end exercise.

---

*Proposed constitution: No new object, identity, customer, commitment, evidence, outcome, document, or audit store may be created. Extend existing canonical stores only.*