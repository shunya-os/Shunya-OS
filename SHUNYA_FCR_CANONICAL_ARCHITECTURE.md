# SHUNYA FCR CANONICAL ARCHITECTURE

> **Date:** 2026-09-01
> **HEAD:** 272dbad
> **Directive:** FCR-01.1 Step 4 — Architecture Freeze

---

## Classification Legend

| Term | Meaning |
|------|---------|
| **CANONICAL** | The single production authority. All writes go here. |
| **DUPLICATE** | Competes with canonical. Consolidation target. |
| **LEGACY** | Historical, being replaced. Read-only. |
| **COMPATIBILITY** | Wraps canonical for backward compat. |
| **ORPHAN** | No caller, no consumer. |
| **REMOVE** | Dead code, archived stub. |

---

## Identity

| Property | Value |
|----------|-------|
| **Model** | TeamMember (app/auth.py) — CANONICAL |
| **Database** | team_members table |
| **Write owner** | app/auth.py, app/auth_routes.py |
| **Read owner** | app/__init__.py (before_request → g.identity_id) |
| **API owner** | auth_bp (/api/v1/auth/*) |
| **Event owner** | N/A |
| **AI owner** | core/intelligence_runtime/ (reads identity_id from session) |
| **Frontend owner** | components/auth/login-page.tsx |
| **Legacy** | SHUNYAIdentity (production/identity_repository.py) — DUPLICATE, 11 rows |
| | PersonIdentity (models.py) — CANONICAL, 0 rows |
| | identity_runtime (core/identity_runtime.py) — ORPHAN |
| | identity_engine (core/identity_engine.py) — DUPLICATE |

**Convergence status:** TeamMember beats SHUNYAIdentity for auth. PersonIdentity is canonical for claims but has 0 rows. Dual-write is transitional.

---

## Organization

| Property | Value |
|----------|-------|
| **Model** | Organization (app/models.py:763) — CANONICAL |
| **Database** | organizations table |
| **Write owner** | app/founder/routes.py, app/auth_routes.py |
| **Read owner** | Organization.query |
| **API owner** | founder_bp, auth_bp |
| **Event owner** | N/A |
| **AI owner** | core/intelligence_runtime/ (retrieval) |
| **Frontend owner** | components/organization/ |
| **Legacy** | CanonicalWorkspace (workspace/models.py) — DUPLICATE |
| | workspace_runtime (core/workspace_runtime/) — ORPHAN |

**Convergence status:** Organization is canonical. CanonicalWorkspace overlaps but is not actively conflicting.

---

## Tenant

| Property | Value |
|----------|-------|
| **Model** | Tenant resolution (app/__init__.py before_request) — CANONICAL |
| **Database** | TenantPolicy (authz/extended_models.py) |
| **Write owner** | authz_bp |
| **Read owner** | app/__init__.py (session → current_org_id → tenant_id) |
| **API owner** | authz_bp |
| **Event owner** | N/A |
| **AI owner** | core/intelligence_runtime/ (tenant_id in context) |
| **Frontend owner** | workspace/context-selector.tsx |
| **Legacy** | app/tenant.py — CANONICAL (DB entity) |

**Convergence status:** Already convergent. One resolution path, one policy model.

---

## Session

| Property | Value |
|----------|-------|
| **Model** | Flask session + g.identity_id (app/__init__.py) — CANONICAL |
| **Database** | user_sessions, flask sessions |
| **Write owner** | app/__init__.py before_request |
| **Read owner** | All routes read g.identity_id, session.get('tenant_id') |
| **API owner** | All routes |
| **Event owner** | N/A |
| **AI owner** | All AI routes read session |
| **Frontend owner** | api/session.ts |
| **Legacy** | X-Identity-Id header — COMPATIBILITY |
| | Cookie bridge (shunya_session) — COMPATIBILITY |

**Convergence status:** Three methods with clear priority order.

---

## Object

| Property | Value |
|----------|-------|
| **Model** | Object (app/objects/models.py) — CANONICAL |
| **Database** | sh_objects (4 rows), sh_uop_objects (85 rows), founder_objects (45 rows) |
| **Write owner** | objects_bp (app/objects/routes.py), canonical.py (dual-write bridge) |
| **Read owner** | objects_bp, canonical.py |
| **API owner** | /api/v1/objects (objects_bp), /api/v1/uop (uop_bp) |
| **Event owner** | app/events/ |
| **AI owner** | core/intelligence_runtime/retrieval.py |
| **Frontend owner** | workspace/object-workspace-viewer.tsx |
| **Legacy** | FounderObject (founder/models.py) — DUPLICATE |
| | UOPObject (kernel/models.py) — DUPLICATE |
| | Object (objects/models.py, legacy) — LEGACY |
| | ShunyaObject (objects/legacy_models.py) — LEGACY |

**Convergence status:** sh_objects is canonical. Dual-write bridge exists. FounderObject and UOPObject are parallel stores with transitional writes.

---

## Person

| Property | Value |
|----------|-------|
| **Model** | Person (app/models.py:580) — CANONICAL |
| **Database** | persons table |
| **Write owner** | app/people/ |
| **Read owner** | people_bp |
| **API owner** | people_bp (/api/v1/people) |
| **Event owner** | N/A |
| **AI owner** | core/intelligence_runtime/ (retrieval) |
| **Frontend owner** | components/people/ |
| **Legacy** | OrgMember (as person) — CANONICAL (org membership) |
| | Contact (CRM) — CANONICAL (customer contact) |

**Convergence status:** Three models with distinct purposes. No conflict.

---

## Relationship

| Property | Value |
|----------|-------|
| **Model** | relationship_intelligence (core/relationship_intelligence/) — CANONICAL |
| **Database** | rel_* tables (rel_relationships, rel_categories, rel_timeline, etc.) |
| **Write owner** | relationship_bp (app/relationship/) |
| **Read owner** | relationship_bp |
| **API owner** | relationship_bp |
| **Event owner** | N/A |
| **AI owner** | Not yet wired to intelligence retrieval |
| **Frontend owner** | components/relationship/ |
| **Legacy** | ObjectRelation (graph/models.py) — DUPLICATE |
| | Relationship (app/relationship/) — COMPATIBILITY (adapter over UCP-02) |

**Convergence status:** UCP-02 is canonical core. Wiring to AI retrieval is PENDING.

---

## Document

| Property | Value |
|----------|-------|
| **Model** | DocumentRecord (app/document/models.py) — CANONICAL |
| **Database** | document_records |
| **Write owner** | doc_bp (app/document_runtime/) |
| **Read owner** | doc_bp, documents_knowledge/ |
| **API owner** | /api/v1/documents/* |
| **Event owner** | N/A |
| **AI owner** | Not directly wired |
| **Frontend owner** | components/documents/ |
| **Legacy** | KnowledgeDocument (models.py:1023) — DUPLICATE |

**Convergence status:** DocumentRecord is canonical. KnowledgeDocument is legacy.

---

## Knowledge

| Property | Value |
|----------|-------|
| **Model** | knowledge_intelligence (core/knowledge_intelligence/) — CANONICAL |
| **Database** | knowledge_* tables |
| **Write owner** | app/knowledge/ |
| **Read owner** | app/knowledge/ |
| **API owner** | doc_knowledge_bp |
| **Event owner** | N/A |
| **AI owner** | UCP-04 not wired to retrieval |
| **Frontend owner** | components/knowledge/ |
| **Legacy** | KnowledgeStore (shunya/knowledge_store/) — LEGACY |
| | KnowledgeEngine (shunya/knowledge_engine/) — LEGACY |

**Convergence status:** UCP-04 is canonical core. app/knowledge/ is canonical app-layer. AI wiring PENDING.

---

## Memory

| Property | Value |
|----------|-------|
| **Model** | MemoryRecord (app/memory/models.py) — CANONICAL |
| **Database** | memory_records (3 records) |
| **Write owner** | MemoryEngine (core/intelligence_runtime/memory.py) → memory_db.py bridge |
| **Read owner** | memory_bp (app/memory_api/), MemoryEngine |
| **API owner** | /api/v1/memory (memory_bp) |
| **Event owner** | N/A |
| **AI owner** | core/intelligence_runtime/memory.py (MemoryEngine) |
| **Frontend owner** | components/memory/memory-browser.tsx |
| **Legacy** | MemoryRuntime (core/memory_knowledge_runtime/) — ORPHAN |

**Convergence status:** MemoryEngine → MemoryRecord bridge applied. Migration zgc_pr_17c applied. 3 records in production.

---

## Event

| Property | Value |
|----------|-------|
| **Model** | Events/CIR (app/events/) — CANONICAL |
| **Database** | wksp_events, inbound_events |
| **Write owner** | events_bp, event bus |
| **Read owner** | SSE streams, events_bp |
| **API owner** | /api/v1/events |
| **Event owner** | app/events/ (Continuous Intelligence Runtime) |
| **AI owner** | Not wired |
| **Frontend owner** | living-workspace/reality-stream.tsx (SSE) |
| **Legacy** | core/event/ — ORPHAN |

**Convergence status:** app/events/ is canonical. core/event/ is orphan.

---

## Observation

| Property | Value |
|----------|-------|
| **Model** | Observations (app/observations/) — CANONICAL |
| **Database** | observations, signals |
| **Write owner** | app/observations/, app/signals/ |
| **Read owner** | AI, continuous loop |
| **API owner** | N/A (internal) |
| **Event owner** | Continuous loop |
| **AI owner** | Not wired to learning loop |
| **Frontend owner** | N/A |
| **Legacy** | ObservationEngine (shunya/observer_engine/) — LEGACY |

**Convergence status:** Observations + Signals = CANONICAL. Not wired to learning loop.

---

## Decision

| Property | Value |
|----------|-------|
| **Model** | DecisionEngine (app/intelligence/decision_engine.py) — CANONICAL |
| **Database** | decision_traces |
| **Write owner** | app/intelligence/ |
| **Read owner** | app/intelligence/ |
| **API owner** | intelligence_bp |
| **Event owner** | N/A |
| **AI owner** | core/intelligence_runtime/ |
| **Frontend owner** | components/workspace/ |
| **Legacy** | decision_intelligence (core/decision_intelligence/) — ORPHAN |

**Convergence status:** DecisionEngine + DecisionRuntime = CANONICAL. UCP-05 orphan.

---

## Commitment

| Property | Value |
|----------|-------|
| **Model** | Commitments (app/commitments/) — CANONICAL |
| **Database** | commitments, commitment_observations |
| **Write owner** | app/commitments/ |
| **Read owner** | app/commitments/ |
| **API owner** | commitment routes |
| **Event owner** | N/A |
| **AI owner** | Not wired |
| **Frontend owner** | components/commitment/ |
| **Legacy** | agreement_intelligence (core/agreement_intelligence/) — ORPHAN |

**Convergence status:** Commitments = CANONICAL. UCP-06 orphan.

---

## Execution

| Property | Value |
|----------|-------|
| **Model** | ExecutionEngine (app/execution_engine/) — CANONICAL |
| **Database** | executions, execution_logs, job_records, execution_idempotency |
| **Write owner** | execution_bp |
| **Read owner** | execution_bp, execution_visibility_bp |
| **API owner** | /api/v1/execution |
| **Event owner** | ContinuousLoop (app/runtime/loop.py) |
| **AI owner** | core/intelligence_runtime/ (action execution) |
| **Frontend owner** | components/work/execution-workspace.tsx |
| **Legacy** | ExecutionRuntime (core/execution_runtime/) — ORPHAN |
| | Execution (execution/routes.py) — DUPLICATE (second bp) |
| | ExecutionIntelligence (execution_intelligence/) — REMOVE |

**Convergence status:** execution_engine + ContinuousLoop = CANONICAL. Outcome model in execution/models.py = CANONICAL.

---

## Evidence

| Property | Value |
|----------|-------|
| **Model** | EvidenceRecord (app/evidence/models_db.py) — CANONICAL |
| **Database** | evidence_records |
| **Write owner** | app/evidence/ |
| **Read owner** | app/evidence/ |
| **API owner** | audit_bp |
| **Event owner** | N/A |
| **AI owner** | core/intelligence_core.py |
| **Frontend owner** | components/audit/ |
| **Legacy** | DecisionTrace (evidence/decision_trace.py) — CANONICAL |
| | EvidenceSource (core/intelligence_core.py) — CANONICAL |

**Convergence status:** Already convergent.

---

## Audit

| Property | Value |
|----------|-------|
| **Model** | Audit (app/audit/) — CANONICAL |
| **Database** | sh_audit_logs, user_activity_logs |
| **Write owner** | audit_bp |
| **Read owner** | audit_bp |
| **API owner** | /api/v1/audit/* |
| **Event owner** | N/A |
| **AI owner** | N/A |
| **Frontend owner** | components/audit/ |
| **Legacy** | AuditLog (genesis_protection/) — CANONICAL |
| | SecurityAuditLog (security/audit/) — CANONICAL |

**Convergence status:** Three audit types, each with canonical owner. Already convergent.

---

## Intelligence / AI

| Property | Value |
|----------|-------|
| **Provider routing** | InferenceOrchestrator (core/inference_orchestrator/) — CANONICAL |
| **Provider fallback** | app/ai/provider.py — DUPLICATE (tertiary fallback) |
| **AI front door** | /api/v1/ai/chat (app/ai/routes.py) — CANONICAL |
| **Executive AI** | /api/v1/intelligence/ask (app/intelligence/routes.py) — CANONICAL |
| **AI security** | /api/v1/cross-boundary (cb_bp) — CANONICAL |
| **AI kernel** | core/intelligence_runtime/ — CANONICAL |
| **Learning loop** | core/intelligence_runtime/learning_loop.py — CANONICAL |
| **Inference governance** | core/inference_governance.py — CANONICAL |
| **Orphan AI paths** | app/intelligence_routes.py — UNREGISTERED (intentionally) |
| **8 Intelligence Engines** | core/intelligence/{perception,context_assembly,...,learning,confidence} — ORPHAN |
| **10 UCP engines** | core/*_intelligence/ — ORPHAN (not wired to retrieval) |

**Convergence status:** 3-tier fallback exists (kernel → orchestrator → provider). Executive AI routes through orchestrator. Cross-boundary gate registered. 8+10 orphan engines not wired.

---

## Provider / Model Routing

| Property | Value |
|----------|-------|
| **Canonical** | core/inference_orchestrator/ (5-stage pipeline) |
| **Fallback** | app/ai/provider.py (Groq→Gemini→OpenRouter→Cloudflare→HF→Local) |
| **Providers configured** | Groq (llama-3.3-70b), Gemini (gemini-2.0-flash), OpenRouter (deepseek-chat) |
| **Inference governance** | core/inference_governance.py (deterministic-first, capability routing) |

---

## Summary: Convergence Actions Still Open

| Action | Count | Priority |
|--------|-------|----------|
| Wire UCP engines to AI retrieval | 10 | MEDIUM |
| Wire 8 intelligence engines to learning loop | 1 | MEDIUM |
| Convert app/ai/provider.py → orchestrator adapter | 1 | HIGH |
| Consolidate object stores (FounderObject → sh_objects) | 1 | MEDIUM |
| Consolidate identity (SHUNYAIdentity → PersonIdentity) | 1 | LOW |
| Remove execution_intelligence stub | 1 | LOW |
| Evaluate orphan runtimes | 5 | LOW |
| Wire frontend AI (CommandPalette → IntelligenceRuntime) | 1 | LAUNCH BLOCKER |
| Wire executive home cockpit | 1 | LAUNCH BLOCKER |

---

*This file is the canonical architecture freeze for FCR-01.1. No new architecture or parallel systems may be introduced during this directive.*