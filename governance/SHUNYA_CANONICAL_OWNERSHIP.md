# SHUNYA CANONICAL OWNERSHIP MAP

> **Permanent governance artifact.** Every core OS concept has exactly ONE canonical production authority. This map classifies all competing implementations and prescribes convergence actions.

**Created:** 2026-09-01 (ZGC-PR-17.1)
**Maintained by:** Hermes Agent (PERMANENT GOVERNANCE)
**Version:** 1.2.0 (corrected 2026-09-01, G1.1-R2 audit findings applied)

---

## Classification Legend

| Classification | Meaning | Action |
|---------------|---------|--------|
| **CANONICAL** | The single production authority | Preserve, enforce |
| **DUPLICATE** | Competes with canonical | Consolidate or convert to adapter |
| **LEGACY** | Historical, being replaced | Quarantine, migrate consumers |
| **COMPATIBILITY** | Wraps canonical for backward compat | Preserve as thin adapter |
| **TEST-ONLY** | Used only in test fixtures | Leave untouched |
| **ORPHAN** | No caller, no consumer | Wire or remove |
| **REMOVE** | Dead code, archived stub | Delete safely |

---

## Core Domain Concepts

### Identity

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| TeamMember | `app/auth.py` | **CANONICAL** | Primary auth model, Flask session bridge |
| OrgMember | `app/models.py` | **CANONICAL** | Organization membership, links identity to org |
| SHUNYAIdentity | `app/production/identity_repository.py` | **DUPLICATE** | Consolidate identity resolution into TeamMember |
| identity_runtime | `core/identity_runtime.py` | **ORPHAN** | YES (5 callers) — convert to thin adapter over app/auth.py TeamMember, or REMOVE per G1.1-R2 audit |
| identity_engine | `core/identity_engine.py` | **REMOVE** | Fully duplicated by TeamMember + app/context/ — remove per G1.1-R2 audit |
| IdentityRepository | `app/production/identity_repository.py` | **DUPLICATE** | Competes with TeamMember |
| IdentityInterface | `core/identity_interface.py` | **ORPHAN** | Tests-only (8 of 11 callers are tests) — move to tests/ or adapt if consumer emerges per G1.1-R2 audit |
| Session identity resolution | `app/__init__.py` (before_request) | **CANONICAL** | The unified g.identity_id middleware |

**Convergence:** TeamMember + OrgMember = CANONICAL. `identity_runtime.py` should be converted to a thin adapter over app/auth.py TeamMember. `identity_engine.py` marked for **REMOVE** — fully duplicated by TeamMember + app/context/ per G1.1-R2 audit. `IdentityInterface` moved to tests/ (no production consumer).

### User

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| TeamMember (auth.py) | `app/auth.py` | **CANONICAL** | Represents authenticated user |
| Identity (OrgMember) | `app/models.py` | **CANONICAL** | Represents user within org context |

**Convergence:** User = TeamMember (identity) + OrgMember (org membership). Already convergent.

### Organization

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Organization | `app/models.py` | **CANONICAL** | Primary org model, FK to all business data |
| CanonicalWorkspace | `app/workspace/models.py` | **DUPLICATE** | Overlaps with Organization — consolidate |
| Workspace (Phase 0) | `app/workspace/` | **COMPATIBILITY** | Workspace experience framework |
| workspace_runtime | `core/workspace_runtime/` | **ORPHAN** | No consumer |

**Convergence:** Organization = CANONICAL. CanonicalWorkspace should be consolidated into Organization or become a thin view. workspace_runtime evaluated for wiring.

### Tenant

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Tenant (session resolution) | `app/__init__.py` before_request | **CANONICAL** | Resolved from OrgMember → current_org_id |
| TenantPolicy | `app/authz/extended_models.py` | **CANONICAL** | Policy layer for tenant isolation |
| Tenant model | `app/tenant.py` | **CANONICAL** | Database tenant entity |

**Convergence:** Already convergent — one resolution path, one policy model, one DB entity.

### Session

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Flask session + g.identity_id | `app/__init__.py` | **CANONICAL** | Unified session resolution |
| X-Identity-Id header | `app/__init__.py` _check_auth | **COMPATIBILITY** | Backward compat for API clients |
| Cookie bridge (shunya_session) | `app/__init__.py` | **COMPATIBILITY** | Enterprise cookie auth |

**Convergence:** Already convergent — three methods with clear priority order.

### Object

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| sh_objects (Phase 0) | `app/objects/` | **CANONICAL** | Primary object store, `/api/v1/objects` |
| FounderObject | `app/founder/models.py` | **DUPLICATE** | Used by founder conversations — migrate to sh_objects |
| UOPObject | `app/kernel/models.py` | **DUPLICATE** | Universal Object Protocol — consolidate into sh_objects |
| Object (Object model) | `app/objects/models.py` | **CANONICAL** | SQLAlchemy model for sh_objects |

**Convergence:** sh_objects = CANONICAL. FounderObject and UOPObject consumers must be migrated to use the canonical object API. This is a migration task, not a new architecture.

### Person

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| People (FDA23) | `app/people/` | **CANONICAL** | People CRUD API |
| OrgMember (as person) | `app/models.py` | **CANONICAL** | Person within org context |
| Contact (CRM) | `app/crm/` | **CANONICAL** | Customer contact |
| Relationship | `core/relationship_intelligence/` | **ORPHAN** | Relationship intelligence not wired to SHUNYAAI |

**Convergence:** People = CANONICAL for person records. OrgMember for membership. Contact for CRM. Relationship intelligence needs wiring.

### Relationship

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| relationship_intelligence (UCP-02) | `core/relationship_intelligence/` | **CANONICAL** | Relationship profile, trust, sentiment |
| ObjectRelation | `app/graph/models.py` | **DUPLICATE** | Consolidate into relationship_intelligence |
| Relationship (app/relationship/) | `app/relationship/` | **DUPLICATE** | App-layer relationship routes — convert to adapter over UCP-02 |

**Convergence:** UCP-02 = CANONICAL. ObjectRelation and app/relationship/ should be consolidated.

### Document

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| DocumentRecord | `app/document/models.py` | **CANONICAL** | Primary document model |
| DocumentRuntime | `app/document_runtime/` | **CANONICAL** | Document processing API |
| KnowledgeDocument | `app/models.py` | **DUPLICATE** | Legacy document store — migrate to DocumentRecord |
| DocumentsKnowledge | `app/documents_knowledge/` | **CANONICAL** | Document extraction + knowledge |

**Convergence:** DocumentRecord = CANONICAL. KnowledgeDocument migration needed.

### Knowledge

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| knowledge_intelligence (UCP-04) | `core/knowledge_intelligence/` | **CANONICAL** | Knowledge graph, sources, gaps |
| Knowledge (app/knowledge/) | `app/knowledge/` | **CANONICAL** | Knowledge sufficiency evaluation |
| KnowledgeStore | `app/shunya/knowledge_store/` | **LEGACY** | Pre-canonical knowledge store |
| KnowledgeEngine | `app/shunya/knowledge_engine/` | **LEGACY** | Pre-canonical knowledge engine |

**Convergence:** UCP-04 = CANONICAL core. app/knowledge/ = CANONICAL app-layer computation. Legacy stores evaluated for removal.

### Memory

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| MemoryRecord (app/memory/) | `app/memory/models.py` | **CANONICAL** | Persistent DB memory |
| MemoryEngine (runtime) | `core/intelligence_runtime/memory.py` | **CANONICAL** | Runtime memory — 230 callers, IS the canonical in-memory memory engine. Bridged to MemoryRecord via memory_db.py. Apply pending migration zgc_pr_17c_durable_memory_fields |
| MemoryRuntime | `core/memory_knowledge_runtime/` | **ORPHAN** | No consumer — concept split across UCP-04 and app/memory/. DECOMMISSION per G1.1-R2 audit |
| MemoryAPI | `app/memory_api/` | **CANONICAL** | Memory REST API |

**Convergence:** MemoryRecord = CANONICAL persistence. MemoryEngine = CANONICAL runtime memory (classification corrected per G1.1-R2 audit — 230 callers, IS the runtime memory). Bridge via memory_db.py exists; apply pending migration zgc_pr_17c_durable_memory_fields. MemoryRuntime to be DECOMMISSIONED (concept split across UCP-04 and app/memory/).

### Event

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Events (CIR) | `app/events/` | **CANONICAL** | Delta events, SSE |
| Event system | `core/event/` | **TEST-ONLY** | Explicitly quarantined as test-only by its own `__init__.py`. Only test callers. Remove from production per G1.1-R2 audit |

**Convergence:** app/events/ = CANONICAL. core/event/ reclassified to TEST-ONLY per G1.1-R2 audit — explicitly quarantined production code; keep as test utility only.

### Observation

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Observations (PROD-15) | `app/observations/` | **CANONICAL** | Observation lifecycle |
| Signals | `app/signals/` | **CANONICAL** | Signal system for continuous loop |
| ObservationEngine | `app/shunya/observer_engine/` | **LEGACY** | Pre-canonical observer |

**Convergence:** Observations + Signals = CANONICAL. Legacy observer evaluated for removal.

### Decision

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| DecisionEngine (app/intelligence/) | `app/intelligence/decision_engine.py` | **CANONICAL** | Decision from awareness signals |
| decision_intelligence (UCP-05) | `core/decision_intelligence/` | **ORPHAN** | No consumer — wire into decision pipeline |
| DecisionRuntime (Phase Z4) | `app/decision_runtime/` | **CANONICAL** | Runtime decision lifecycle |

**Convergence:** DecisionEngine + DecisionRuntime = CANONICAL. UCP-05 wired as needed.

### Commitment

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Commitments (PROD-14) | `app/commitments/` | **CANONICAL** | Commitment lifecycle |
| agreement_intelligence (UCP-06) | `core/agreement_intelligence/` | **ORPHAN** | No consumer — wire into commitments |

**Convergence:** Commitments = CANONICAL. UCP-06 wired as needed.

### Plan

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Planning (Phase 14) | `app/planning/` | **CANONICAL** | Plan lifecycle, objectives, checkpoints |
| planning_runtime | `core/planning_runtime/` | **ORPHAN** | No consumer |
| Planner (app/shunya/) | `app/shunya/planner/` | **LEGACY** | Pre-canonical planner |

**Convergence:** app/planning/ = CANONICAL. planning_runtime evaluated for wiring. Legacy planner removed.

### BusinessExecutionInstance

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Execution (execution_engine/) | `app/execution_engine/models.py` | **CANONICAL** | Execution lifecycle |
| ExecutionRuntime | `core/execution_runtime/` | **ORPHAN** | No consumer — 8 UCP callers but none wired to production. DECOMMISSION and rewire to app/execution_engine/ per G1.1-R2 audit |
| Execution (execution/) | `app/execution/models.py` | **COMPATIBILITY** | NOT a competing execution engine — Outcome is user-facing outcome recording. Wraps execution_engine per G1.1-R2 audit |

**Convergence:** execution_engine = CANONICAL for execution process. core/execution_runtime/ DECOMMISSIONED — 8 UCP callers rewire to app/execution_engine/ per G1.1-R2 audit. execution/models.py Outcome reclassified to **COMPATIBILITY** — it is user-facing outcome recording, NOT a competing execution engine.

### Evidence

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| EvidenceRecord (app/evidence/) | `app/evidence/models_db.py` | **CANONICAL** | Evidence lifecycle |
| DecisionTrace | `app/evidence/decision_trace.py` | **CANONICAL** | Trace records |
| EvidenceSource | `core/intelligence_core.py` | **CANONICAL** | Core evidence model |

**Convergence:** Already convergent — app/evidence/ = CANONICAL persistence, core/intelligence_core.py = CANONICAL model.

### Output

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Outcome | `app/execution/models.py` | **CANONICAL** | Outcome records |
| ContentStudio | `app/content_studio/` | **CANONICAL** | Content output |
| CreativeRuntime | `app/creative_runtime/` | **CANONICAL** | Creative output |

**Convergence:** Already convergent — each output type has its canonical owner.

### Execution

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| ExecutionEngine | `app/execution_engine/` | **CANONICAL** | Execution gate, actions |
| ExecutionRuntime | `core/execution_runtime/` | **ORPHAN** | No consumer |
| Execution (execution/) | `app/execution/routes.py` | **DUPLICATE** | Second execution_bp registration |
| ContinuousLoop | `app/runtime/loop.py` | **CANONICAL** | Background execution loop |
| ExecutionIntelligence | `app/execution_intelligence/` | **REMOVE** | Archived stub |

**Convergence:** execution_engine + ContinuousLoop = CANONICAL. core/execution_runtime/ DECOMMISSIONED — phantom dependency chain (8 UCP callers not wired to production) per G1.1-R2 audit. execution_intelligence/ removed.

### Audit

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| Audit (FDA21) | `app/audit/` | **CANONICAL** | Audit records, governance |
| AuditLog | `app/genesis_protection/` | **CANONICAL** | Genesis audit log |
| SecurityAuditLog | `app/security/audit/` | **CANONICAL** | Security audit log |

**Convergence:** Already convergent — each audit type has its canonical owner.

---

## Intelligence & AI Layer

### Provider / Model Routing

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| InferenceOrchestrator | `core/inference_orchestrator/` | **CANONICAL** | 5-stage pipeline, policy, learning router |
| app/ai/provider.py | `app/ai/provider.py` | **DUPLICATE** | Parallel provider chain — convert to adapter over orchestrator |

**Convergence:** InferenceOrchestrator = CANONICAL. app/ai/provider.py converted to adapter: `get_provider()` returns a thin wrapper that delegates `complete()` to the orchestrator.

### AI Query Entry Points

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| `/api/v1/ai/chat` | `app/ai/routes.py` | **CANONICAL** | Frontend's primary AI entry point |
| `/api/v1/intelligence/ask` | `app/intelligence/routes.py` | **CANONICAL** | Executive intelligence, company-first pipeline |
| `/api/intelligence/ask` | `app/intelligence_routes.py` | **ORPHAN** | UIR blueprint UNREGISTERED — keep as internal API, not a public surface |
|| `/api/v1/cross-boundary` | `core/intelligence_runtime/cross_boundary_routes.py` | **CANONICAL** | FDA9/FDA10 security boundary — REGISTERED via cb_bp at app.__init__:935 |
| `/search/ai/analyze` | `app/search/routes.py` | **COMPATIBILITY** | Search-specific adapter — acceptable |

**Convergence:** `/api/v1/ai/chat` = CANONICAL front door. Internally delegates to (3-tier fallback):
1. `core.intelligence_runtime.integration.ask()` (SHUNYAAI kernel — primary)
2. InferenceOrchestrator (canonical provider routing — secondary)
3. app/ai/provider.py registry (direct provider chain — tertiary resilience)

M8 `/api/v1/intelligence/ask` stays as company-first executive intelligence but delegates its model call through the orchestrator. `/api/v1/cross-boundary` (cb_bp) IS registered as the canonical security boundary for execution authorization at app.__init__:935. `app/intelligence_routes.py` (UIR blueprint) remains UNREGISTERED — legacy file exists but blueprint is explicitly not mounted per app.__init__:948 comment "removed — single canonical path."

### Intelligence Runtimes

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
| IntelligenceRuntime | `core/intelligence_runtime/` | **CANONICAL** | Kernel runtime — intent, context, memory, retrieval, reasoning, planner, execution, conversation, suggestions, explain |
| 8 Intelligence Engines | `core/intelligence/{perception,context_assembly,reasoning,planning,decision,reflection,learning,confidence}` | **ORPHAN** | Orchestrated by CognitiveRuntime (CANONICAL). Wire into learning loop as CognitiveRuntime plugins per G1.1-R2 audit |
| CognitiveRuntime | `core/cognitive_runtime/` | **CANONICAL** | Canonical orchestrator for the 8 intelligence engines — feeds into IntelligenceRuntime per G1.1-R2 audit |
| M8 Intelligence service | `app/intelligence/service.py` | **CANONICAL** | Executive intelligence service |
| MixedRouter | `app/intelligence/mixed_router.py` | **DUPLICATE** | Parallel routing abstraction — converge into orchestrator |

**Convergence:** IntelligenceRuntime = CANONICAL kernel. CognitiveRuntime = CANONICAL orchestrator for the 8 intelligence engines (classification corrected per G1.1-R2 audit). The 8 engines wired as CognitiveRuntime plugins. MixedRouter evaluated for convergence.

### Memory / Knowledge / Conversation Relationship

| Implementation | Location | Classification | Action |
|---------------|----------|---------------|--------|
|| MemoryEngine (runtime) | `core/intelligence_runtime/memory.py` | **CANONICAL** | In-memory 4-tier memory, connected to DB via memory_db.py bridge |
|| MemoryRecord (DB) | `app/memory/models.py` | **CANONICAL** | Persistent DB memory — bridge via app/memory_api/memory_db.py |
|| ConversationRuntime | `core/intelligence_runtime/conversation.py` | **CANONICAL** | 50-message rolling window |
|| MemoryRuntime | `core/memory_knowledge_runtime/` | **ORPHAN** | No consumer — evaluate |
| ExternalConversation (DB) | `app/communication/models.py` | **CANONICAL** | Persistent conversation |
| KnowledgeIntelligence (UCP-04) | `core/knowledge_intelligence/` | **CANONICAL** | Knowledge graph, gaps |

**Convergence:** Runtime memory + DB memory = connected (MemoryEngine uses MemoryRecord as backing store via app/memory_api/memory_db.py durable bridge). Migration `zgc_pr_17c_durable_memory_fields` exists but NOT YET APPLIED to production DB (alembic head at 0013, not at latest). ConversationRuntime + DB conversation = connected. Knowledge wired into retrieval.

---

## UCP Domain Modules (core/)

| UCP | Module | Classification | Action |
|-----|--------|---------------|--------|
| UCP-02 | relationship_intelligence | **CANONICAL** | Wire into SHUNYAAI retrieval |
| UCP-03 | financial_intelligence | **CANONICAL** | Wire into SHUNYAAI retrieval |
| UCP-04 | knowledge_intelligence | **CANONICAL** | Wire into SHUNYAAI retrieval |
| UCP-05 | decision_intelligence | **CANONICAL** | Wire into decision pipeline |
| UCP-06 | agreement_intelligence | **CANONICAL** | Wire into commitments |
| UCP-07 | asset_intelligence | **CANONICAL** | Wire into SHUNYAAI retrieval |
| UCP-08 | initiative_intelligence | **CANONICAL** | Wire into planning |
| UCP-09 | operations_intelligence | **CANONICAL** | Wire into SHUNYAAI retrieval |
| UCP-10 | health_intelligence | **CANONICAL** | Wire into SHUNYAAI retrieval |
| UCP-11 | learning_intelligence | **CANONICAL** | Wire into learning loop |

---

## Summary of Convergence Actions

|| Action | Count | Priority |
||--------|-------|----------|
|| **REGISTER** (blueprints) | 0 | CRITICAL (cross_boundary now registered; intelligence_routes intentionally suppressed) |
|| **APPLY** (DB migration) | 1 | HIGH (zgc_pr_17c_durable_memory_fields not applied) |
|| **CONNECT** (memory → DB, conversation → DB) | 2 | HIGH (code exists, migration pending) |
|| **WIRE** (UCP engines into SHUNYAAI retrieval) | 10 | MEDIUM |
|| **CONVERT** (app/ai/provider.py → orchestrator adapter) | 1 | HIGH |
|| **CONSOLIDATE** (object stores) | 1 | HIGH |
|| **MIGRATE** (FounderObject → sh_objects, KnowledgeDocument → DocumentRecord) | 2 | MEDIUM |
|| **DECOMMISSION** (execution_runtime, planning_runtime, memory_knowledge_runtime, workspace_runtime) | 4 | HIGH (phantom dependency chains) |
|| **REMOVE** (identity_engine, execution_intelligence stub, core/event/ from production) | 3 | MEDIUM |
|| **REVISE CLASSIFICATION** (MemoryEngine→CANONICAL, CognitiveRuntime→CANONICAL, core/event/→TEST-ONLY, Outcome→COMPATIBILITY) | 4 | HIGH (corrects ownership map) |
|| **WIRE** (8 intelligence engines → CognitiveRuntime plugins) | 1 | MEDIUM |

---

*This map is a permanent governance artifact. Future convergence work updates classification as implementations are consolidated. No new competing implementation may be created without explicit governance approval.*