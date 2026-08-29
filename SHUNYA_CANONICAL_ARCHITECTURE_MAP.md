# SHUNYA OS — Canonical Architecture Map

**Generated:** 2026-08-29  
**Methodology:** Repository search, DB schema inspection (PostgreSQL), API route verification, code analysis across all `app/`, `core/`, `migrations/`, `_archive/`, and `_legacy` paths.

---

## Classification System

| Tag | Meaning |
|-----|---------|
| **CANONICAL** | Authoritative single owner. All consumers must route through this. |
| **TRANSITIONAL** | In process of being folded into canonical owner. May have dual-write or reads. |
| **LEGACY** | Active but deprecated. No new consumers. Scheduled for archive. |
| **ARCHIVE** | Preserved for history only. Not wired into any active path. |
| **REMOVE** | Dead code / unreferenced. Delete candidate. |
| **DUPLICATE** | Direct duplicate of another production service. Consolidation required. |

---

## 1. Identity

### Canonical Production Owner
**`core/identity_interface.py` + `core/identity_engine.py` + `app/identity/service.py` (IdentityService)**

- **Interface:** `core/identity_interface.py` — `IdentityResolutionInterface` (ABC), dataclasses for `IdentityClaim`, `IdentityResolution`, `IdentityGovernance`.
- **Engine:** `core/identity_engine.py` (referenced via `core/identity.py` — imports `AuthMethod`, `EntityType`, `IdentityEngine`)
- **Service:** `app/identity/service.py` — `IdentityService(IdentityResolutionInterface)` — the FDA4 canonical implementation.
- **Runtime:** `core/identity_runtime.py` — `IdentityRuntime(RuntimeInterface)` — pipeline-stage wrapper.
- **Persistence:** `app/models.py` → `Person` (table `persons`), `PersonIdentity` (table `person_identities`), `Organization` (table `organizations`)
- **Repository:** `app/production/identity_repository.py` → `SHUNYAIdentityModel` (table `shunya_identities`)

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/identity/service.py` — IdentityService | `persons`, `person_identities` | **CANONICAL** | FDA4 — sole identity resolution authority. Uses `Person` + `PersonIdentity`. |
| `app/production/identity_repository.py` — SHUNYAIdentityModel | `shunya_identities` | **TRANSITIONAL** | Parallel identity store. Should converge with IdentityService. |
| `app/auth.py` — TeamMember | `team_members` | **LEGACY** | Flask-Login auth. Not wired to canonical identity resolution. |
| `app/auth_oauth.py` | `oauth_states` | **LEGACY** | OAuth flow, detached from canonical identity. |
| `app/auth_routes.py` | — | **LEGACY** | Auth routes, not using IdentityResolutionInterface. |
| `app/authz/` — Role, ServiceAccount, OrgMemberRole | `auth_roles`, `auth_service_accounts`, `auth_member_roles` | **LEGACY** | Authorization RBAC. Separate from identity resolution. |
| `app/gkf/identity.py` | — | **LEGACY** | GKF identity wrapper. |
| `app/graph_universal/identity.py` | — | **LEGACY** | Graph-specific identity reference. |
| `app/kernel/identity.py` | — | **LEGACY** | Kernel identity adapter. |
| `app/kernel/identity_governance.py` | — | **LEGACY** | Governance checks for identity. |
| `app/security/jwt.py` | — | **LEGACY** | JWT token handling. |
| `app/objects/legacy_models.py` — ShunyaObject | `sh_objects` | **TRANSITIONAL** | sh_objects workspace layer — different identity context. |

---

## 2. Tenant

### Canonical Production Owner
**`app/tenant.py` → `Tenant` (table `tenants`)**

- **Model:** `app/tenant.py:56` — `Tenant(db.Model)`, table `tenants`.
- **Theme:** `app/tenant.py:24` — `TenantTheme`, table `tenant_themes`.
- **Used by:** Most tables via `tenant_id` FK or nullable integer column.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/tenant.py` — Tenant | `tenants` | **CANONICAL** | Single source of truth. |
| `app/authz/extended_models.py` — TenantPolicy | `auth_tenant_policies` | **DUPLICATE** | Tenant-level auth policies split from canonical Tenant. |
| Scattered `tenant_id` columns (150+ tables) | — | **TRANSITIONAL** | Most tables carry `tenant_id`. Some nullable — not fully isolated. |
| `app/production/identity/workspace_model.py` | `workspaces` | **DUPLICATE** | Has `tenant_id` column but is a parallel workspace model. |
| Legacy `_backfill_tenant.py` | — | **ARCHIVE** | One-time backfill script. |

---

## 3. Object

### Canonical Production Owner
**`app/objects/models.py` → `Object` (table `objects`) + `app/kernel/models.py` → `UOPObject` (table `sh_uop_objects`)**

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/objects/models.py` — Object | `objects` | **TRANSITIONAL** | Simple generic `Object` (type, state, context JSON). Used by workspace_objects/service. |
| `app/kernel/models.py` — UOPObject | `sh_uop_objects` | **CANONICAL** | Universal Object Protocol — full field set (tenant_id, space_id, object_type, evidence, relationships). |
| `app/objects/legacy_models.py` — ShunyaObject | `sh_objects` | **TRANSITIONAL** | Legacy sh_objects table — used by delta events, SSE streaming. |
| `app/core/entity.py` — Entity | `entities` | **LEGACY** | Generic entity with definition_id FK. Used by Lead auto-creation. |
| `app/founder/models.py` — FounderObject | `founder_objects` | **LEGACY** | Founder-specific object store. |
| `app/graph_universal/entity.py` | — | **ARCHIVE** | Graph entity concept. |
| `_archive/object_variants/` | — | **ARCHIVE** | Archived object implementations. |

---

## 4. Event (Delta Events / Observability)

### Canonical Production Owner
**`app/events/routes.py` — `events_bp`** — Delta polling + SSE streaming over `sh_objects`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/events/routes.py` — SSE endpoint | `sh_objects` | **CANONICAL** | `/api/v1/events` and `/api/v1/events/stream`. |
| `core/event/` | — | **ARCHIVE** | Core event models — empty / unused. |
| `app/graph_universal/event.py` | — | **LEGACY** | Graph-universal event definitions. |
| `app/ubme/events.py` | — | **LEGACY** | UBME business events. |
| `app/founder/workspace_models.py` — WorkspaceEvent | `wksp_events` | **LEGACY** | Founder workspace events. |
| `app/orchestration/signal.py` | — | **LEGACY** | Orchestration signals as events. |
| `app/signals/` — Signal | `signals` | **LEGACY** | General signals system. |
| `app/inbound_events` — InboundEvent | `inbound_events` | **LEGACY** | Communication inbound events. |

---

## 5. Observation

### Canonical Production Owner
**`app/observations/models.py` → `Observation` (table `commitment_observations`)**

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/observations/models.py` — Observation | `commitment_observations` | **CANONICAL** | Commitment-scoped observations. Records observed/expected values. |
| `app/shunya/observer_learning.py` — Observation | `observations` | **DUPLICATE** | Legacy observation model in shunya module. TABLE: `observations`. |
| `app/evidence/models.py` — Observation (dataclass) | (in-memory) | **TRANSITIONAL** | Evidence Engine's Observation dataclass — immutable, richer schema. |
| `app/intelligence/observation.py` | — | **LEGACY** | Intelligence module observation logic. |
| `core/cognitive_runtime/` | — | **ARCHIVE** | Observer Engine (Cognitive Runtime). |
| `app/awareness/` | — | **LEGACY** | Awareness engine — observation-like. |
| `_archive/graph_variants/` | — | **ARCHIVE** | Graph-based observation variant. |

---

## 6. Evidence

### Canonical Production Owner
**`app/evidence/models.py` + `app/evidence/models_db.py`**

- **Dataclass:** `app/evidence/models.py` — `Evidence`, `EvidenceSource`, `Provenance`, `Observation` (immutable dataclasses).
- **DB Model:** `app/evidence/models_db.py` — `EvidenceRecord` (table `evidence_records`).
- **Decision Traces:** `app/evidence/decision_trace.py` — `DecisionTrace` (table `decision_traces`).
- **Service:** `app/evidence/service.py`.
- **Enums:** `app/evidence/enums.py` — `EvidenceStatus`, `EvidenceType`, `SourceCategory`.
- **Values:** `app/evidence/values.py` — `Confidence`, `Freshness`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/evidence/models.py` + `models_db.py` | `evidence_records` | **CANONICAL** | Canonical evidence engine. |
| `app/evidence/decision_trace.py` | `decision_traces` | **CANONICAL** | Part of evidence system. |
| `app/finance/evidence.py` — FinancialEvidence | `fin_evidence` | **LEGACY** | Finance-specific evidence. |
| `app/evidence/provenance_models.py` | — | **TRANSITIONAL** | Provenance models (not yet unified with canonical). |
| `app/evidence/provenance_enums.py` | — | **TRANSITIONAL** | Provenance enums. |
| `app/execution/effects.py` | — | **LEGACY** | Execution effect tracking. |
| `app/learning_intelligence/models.py` | — | **TRANSITIONAL** | Learning intelligence artifact models carry their own evidence lists. |

---

## 7. Memory

### Canonical Production Owner
**`app/memory/models.py` → `MemoryRecord`, `MemoryCandidate`, `MemoryConcept`, `MemoryProvenance`**

- **Tables:** `memory_records`, `memory_candidates`, `memory_concepts`, `memory_provenances`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/memory/models.py` — MemoryRecord | `memory_records` | **CANONICAL** | FDA3 — full lifecycle, truth classification, provenance. |
| `app/memory/models.py` — MemoryCandidate | `memory_candidates` | **CANONICAL** | Gated memory promotion pipeline. |
| `app/memory_api/routes.py` | — | **CANONICAL** | Memory API — CRUD operations. |
| `app/intelligence/memory_store.py` — LearningWeight | `learning_weights` | **LEGACY** | Intelligence module's own memory-like store. |
| `app/relationship/models.py` — RelationshipMemory | `rel_ai_memory` | **LEGACY** | Relationship-scoped AI memory. |
| `app/workspace/models.py` | — | **LEGACY** | Workspace context handling. |

---

## 8. Knowledge

### Canonical Production Owner
**`app/knowledge/__init__.py` (KnowledgeResolutionService)**

- **Service:** `app/knowledge/__init__.py` — `KnowledgeResolutionService` (Phase 11, computation-only). Evaluates sufficiency + freshness.
- **Facts:** `app/shunya/knowledge_store.py` → `KnowledgeFact` (table `knowledge_facts`).
- **Documents:** `app/models.py` → `KnowledgeDocument` (table `knowledge_documents`).

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/knowledge/__init__.py` | — | **CANONICAL** | Phase 11 — knowledge resolution service. |
| `app/shunya/knowledge_store.py` — KnowledgeFact | `knowledge_facts` | **TRANSITIONAL** | Fact storage — not yet unified with resolution service. |
| `app/models.py` — KnowledgeDocument | `knowledge_documents` | **LEGACY** | Legacy knowledge document model. |
| `app/documents_knowledge/` | — | **LEGACY** | Document knowledge routes. |
| `app/shunya/knowledge.py` | — | **LEGACY** | Legacy shunya knowledge module. |
| `core/knowledge_intelligence/` | — | **ARCHIVE** | Core Knowledge Intelligence engine — archived. |
| `core/knowledge_interface.py` | — | **ARCHIVE** | Knowledge interface — archived. |
| `core/memory_knowledge_runtime/` | — | **ARCHIVE** | Combined memory-knowledge runtime — archived. |
| `app/space/knowledge.py` | — | **LEGACY** | Space-scoped knowledge handling. |
| `knowledge/` (root) | — | **ARCHIVE** | Top-level knowledge directory. |

---

## 9. Commitment

### Canonical Production Owner
**`app/commitments/models.py` → `Commitment` (table `commitments`)**

- **Model:** Simple structure: title, owner, due_at, status, relationship_id, campaign_id, meta.
- **Service:** `app/commitments/service.py`.
- **Routes:** `app/commitments/routes.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/commitments/models.py` | `commitments` | **CANONICAL** | Single commitment model. |
| `app/commitments/service.py` | — | **CANONICAL** | Commitment service. |
| `app/commitments/routes.py` | — | **CANONICAL** | Commitment API routes. |
| `app/memory/models.py` — MemoryRecord (COMMITMENT type) | `memory_records` | **TRANSITIONAL** | Commitments stored as memory records with memory_type='commitment'. |
| `app/decision_runtime/commitment.py` | — | **LEGACY** | Decision Runtime's commitment interaction. |
| `app/planning/plan.py` | — | **LEGACY** | Plan-level commitments. |
| `app/orchestration/` | — | **LEGACY** | Orchestration-based commitments. |

---

## 10. Task

### Canonical Production Owner
**`app/models.py` → `Task` + `TaskList` (tables `tasks`, `task_lists`)**

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/models.py` — Task | `tasks` | **CANONICAL** | Main task model (lead-scoped). |
| `app/models.py` — TaskList | `task_lists` | **CANONICAL** | Task grouping. |
| `app/founder/workspace_models.py` — NextAction | `wksp_next_actions` | **DUPLICATE** | Founder workspace next-actions — should use Task. |
| `app/space/models.py` — SpacePlanRef | (in-memory) | **TRANSITIONAL** | Space-scoped plan references — views into tasks. |
| `app/planning/` | — | **LEGACY** | Planning runtime (plan decomposition). |
| `app/execution/runtime.py` | — | **LEGACY** | Execution runtime — step execution. |

---

## 11. Plan

### Canonical Production Owner
**`app/planning/` — Planning Runtime**

- `app/planning/plan.py`, `app/planning/objective.py`, `app/planning/dependency.py`, `app/planning/checkpoint.py`, `app/planning/runtime.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/planning/` — PlanningRuntime | — | **CANONICAL** | Goal decomposition, plan generation. |
| `core/planning_runtime/` | — | **ARCHIVE** | Core planning — superseded by app/planning/. |
| `app/shunya/planner.py` | — | **LEGACY** | Legacy shunya planner. |
| `app/space/models.py` — SpacePlanRef | — | **TRANSITIONAL** | Space-scoped plan references backed by planning runtime. |
| `app/orchestration/` | — | **LEGACY** | Orchestration — plan execution sequencing. |
| `app/commercial/models.py` — CommercialProposal | `g4_proposals` | **LEGACY** | Commercial proposal as plan-like structure. |

---

## 12. Decision

### Canonical Production Owner
**`app/decision/models.py` (dataclasses) + `app/decision/engine.py`**

- **Dataclasses:** `DecisionContext`, `DecisionOption`, `DecisionEvaluation`, `DecisionRecommendation`, `DecisionSnapshot`, etc.
- **Engine:** `app/decision/engine.py` — `DecisionIntelligence`.
- **Decision Runtime:** `app/decision_runtime/` — `runtime.py`, `policy.py`, `commitment.py`, `outcome.py`, `learning.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/decision/models.py` (dataclasses) | — | **CANONICAL** | Canonical decision intelligence models (Milestone V). |
| `app/decision/engine.py` | — | **CANONICAL** | Decision intelligence engine. |
| `app/decision_runtime/` | — | **CANONICAL** | Decision runtime (policy, commitment interaction). |
| `core/decision_intelligence/` | — | **ARCHIVE** | Core decision intelligence — superseded. |
| `app/intelligence/decision_engine.py` | — | **DUPLICATE** | Secondary decision engine in intelligence module. |
| `app/runtime/decision_engine.py` | — | **DUPLICATE** | Third decision engine in runtime module. |
| `app/intelligence/scenario.py` | — | **LEGACY** | Scenario evaluation — overlaps with decision. |
| `app/privacy/models.py` — PrivacyDecision | `privacy_decisions` | **LEGACY** | Privacy-specific decisions. |
| `app/execution/constants.py` | — | **LEGACY** | Execution decision constants. |

---

## 13. Execution

### Canonical Production Owner
**`app/execution/` + `app/execution_engine/`**

- **Outcome:** `app/execution/models.py` — `Outcome` (table `sh_outcomes`), `IdempotencyRecord` (table `execution_idempotency`).
- **Execution:** `app/execution_engine/models.py` — `Execution` (table `executions`), `ExecutionLog` (table `execution_logs`).
- **Runtime:** `app/execution/runtime.py`, `app/execution_engine/engine.py`.
- **Recovery:** `app/execution/recovery.py`.
- **Idempotency:** `app/execution/idempotency.py`.
- **Effects:** `app/execution/effects.py`.
- **Routes:** `app/execution/routes.py`, `app/execution_engine/routes.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/execution/models.py` — Outcome | `sh_outcomes` | **CANONICAL** | Intent + state + evidence execution model. |
| `app/execution_engine/models.py` — Execution, ExecutionLog | `executions`, `execution_logs` | **CANONICAL** | Execution engine with logs. |
| `app/execution_log/models.py` — ExecutionLog | `act_execution_logs` | **DUPLICATE** | Second execution log table. |
| `core/execution_runtime/` | — | **ARCHIVE** | Core execution runtime — superseded. |
| `core/execution_engine.py` | — | **ARCHIVE** | Core execution engine. |
| `app/execution_engine/truth.py` | — | **LEGACY** | Truth tracking in execution engine. |
| `app/execution_engine/context.py` | — | **LEGACY** | Execution context. |
| `app/execution_intelligence/` | — | **ARCHIVE** | Execution intelligence — archived. |
| `app/execution_visibility/` | — | **LEGACY** | Execution visibility routes. |
| `_archive/execution_variants/` | — | **ARCHIVE** | Archived execution variants. |
| `app/shunya/executor.py` | — | **LEGACY** | Legacy shunya executor. |

---

## 14. BusinessExecutionInstance

### Canonical Production Owner
**`app/execution/models.py` → `Outcome` (table `sh_outcomes`)**

BusinessExecutionInstance is the Outcome model — it captures the user's intention + current execution state + evidence of completion. This is the canonical container for a business execution instance.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/execution/models.py` — Outcome | `sh_outcomes` | **CANONICAL** | Intent-driven execution instance. |
| `app/execution_engine/models.py` — Execution | `executions` | **DUPLICATE** | Parallel execution model — should converge with Outcome. |
| `app/ubme/engine.py` | — | **LEGACY** | UBME business model execution engine. |
| `app/ubme/business_graph.py` | — | **LEGACY** | UBME business graph. |
| `app/orchestration/` | — | **LEGACY** | Orchestration cycle — execution container. |
| `app/commercial/models.py` — CommercialOpportunity | `g4_opportunities` | **LEGACY** | Commercial opportunity as execution instance. |
| `app/founder/models.py` — FounderSpace | `founder_spaces` | **LEGACY** | Founder space as execution container. |

---

## 15. Outcome

### Canonical Production Owner
**`app/execution/models.py` → `Outcome` (table `sh_outcomes`)**

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/execution/models.py` — Outcome | `sh_outcomes` | **CANONICAL** | Intent + state + evidence. |
| `app/models.py` — Lead.outcome | `leads.outcome` | **LEGACY** | Legacy outcome string field on Lead. |
| `app/outcome_engine.py` | — | **LEGACY** | Standalone outcome engine. |
| `app/outcome_library.py` | — | **LEGACY** | Outcome library. |
| `app/execution_engine/truth.py` | — | **LEGACY** | Execution truth = outcome-like. |
| `app/decision_runtime/outcome.py` | — | **LEGACY** | Decision runtime's outcome handling. |
| `app/memory/models.py` — MemoryRecord (OUTCOME type) | `memory_records` | **LEGACY** | Outcomes stored as memory records. |
| `UNIVERSAL_OUTCOME_LIBRARY.md` | — | **ARCHIVE** | Design document only. |

---

## 16. Learning

### Canonical Production Owner
**`app/learning_intelligence/`**

- **Models:** `app/learning_intelligence/models.py` — `LearnedPattern`, `OutcomeProfile`, `RefinedRecommendation`, `ConfidenceAssessment`, `SimilarityResult`, etc.
- **Engine:** `app/learning_intelligence/engine.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/learning_intelligence/` — Learner | — | **CANONICAL** | Milestone II learning intelligence. |
| `core/learning_intelligence/` | — | **ARCHIVE** | Core learning intelligence — superseded. |
| `app/intelligence/learning.py` | — | **LEGACY** | Intelligence module's learning. |
| `app/intelligence/models.py` — LearningEvent | `m8_learning_events` | **LEGACY** | M8 learning events (correction/validation). |
| `app/shunya/observer_learning.py` — LearningEntry | `learning_entries` | **LEGACY** | Legacy observer learning. |
| `app/g5/models.py` — GrowthLearning | `g5_learnings` | **LEGACY** | Growth module learning. |
| `app/decision_runtime/learning.py` | — | **LEGACY** | Decision runtime learning. |

---

## 17. Conversation

### Canonical Production Owner
**`app/communication/`**

- **External Conversations:** `app/communication/models.py` — `ExternalConversation` (table `external_conversations`), `ExternalMessage` (table `external_messages`), `ExternalParticipant` (table `external_participants`).
- **Messages:** `app/communication/models.py` — `Message` (table `messages`), `MessageProposal` (table `message_proposals`).
- **Runtime:** `app/communication/runtime.py`.
- **Service:** `app/communication/service.py`.
- **Routes:** `app/communication/routes.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/communication/models.py` | `external_conversations`, etc. | **CANONICAL** | Communication service with multi-channel support. |
| `app/conversation.py` | — | **ARCHIVE** | No longer present as standalone module. |
| `app/founder/models.py` — FounderConversation | `founder_conversations` | **DUPLICATE** | Founder conversations — should use communication service. |
| `app/founder/models.py` — FounderMessage | `founder_messages` | **DUPLICATE** | Founder messages — should use communication service. |
| `app/ai/copilot.py` | — | **LEGACY** | AI copilot — conversation-like. |
| `app/ai/context.py` | — | **LEGACY** | AI conversation context. |
| `app/coach.py` | — | **LEGACY** | AI coach conversation. |
| `app/companion.py` | — | **LEGACY** | AI companion conversation. |
| `app/assistant/` | — | **LEGACY** | AI assistant. |
| `app/intake/session.py` | — | **LEGACY** | Intake session conversation. |

---

## 18. Document

### Canonical Production Owner
**`app/document/models.py` + `app/models.py` (Document model)**

- **DocumentRecord:** `app/document/models.py` — `DocumentRecord` (table `document_records`), `DocumentSection` (table `document_sections`), `ExtractedField` (table `extracted_fields`).
- **Legacy Document:** `app/models.py` — `Document` (table `documents`).

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/document/models.py` — DocumentRecord | `document_records` | **CANONICAL** | Modern document model with sections. |
| `app/models.py` — Document | `documents` | **LEGACY** | Legacy document model. |
| `app/document/runtime.py` | — | **CANONICAL** | Document runtime (routes in document_runtime/). |
| `app/documents_knowledge/` | — | **LEGACY** | Document-knowledge bridge. |
| `app/documents_api.py` | — | **LEGACY** | Documents API endpoints. |
| `app/document_reader.py` | — | **LEGACY** | Document reader utility. |
| `app/relationship/models.py` — RelationshipDocument | `rel_documents` | **LEGACY** | Relationship-scoped documents. |
| `app/space/models.py` — SpaceDocumentRef | — | **TRANSITIONAL** | Space-scoped document references. |
| `app/adapters/document/` | — | **ARCHIVE** | Document adapter — archived. |

---

## 19. Integration

### Canonical Production Owner
**`app/integration/`**

- **Models:** `app/integration/models.py` — `IntegrationConnection`, `IntegrationConfig`, `SocialAccount`, `AdCampaign`, `CachedEmail`, `CachedMedia`, `ContentGeneration`, `Notification`.
- **Registry:** `app/integration/registry.py`.
- **Service:** `app/integration/service.py`.
- **Routes:** `app/integration/routes.py`, `app/integration/routes_api.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/integration/` | `m6_*` tables | **CANONICAL** | M6 integration framework. |
| `app/platform/` | `platform_webhook_*` | **LEGACY** | Webhook subscriptions/deliveries. |
| `core/integration_fabric.py` | — | **ARCHIVE** | Core integration fabric — archived. |
| `core/integration_runtime/` | — | **ARCHIVE** | Core integration runtime — archived. |
| `app/integration/gmail_adapter.py` | — | **LEGACY** | Gmail-specific adapter. |
| `app/integration/gmail_ingest.py` | — | **LEGACY** | Gmail ingestion. |
| `_archive/communication_legacy/` | — | **ARCHIVE** | Archived communication integrations. |
| `app/email_service.py` | — | **LEGACY** | Legacy email service. |
| `app/whatsapp_webhook.py` | — | **LEGACY** | WhatsApp webhook. |

---

## 20. Audit

### Canonical Production Owner
**`app/security/audit.py` → `AuditLog` (table `sh_audit_logs`)**

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/security/audit.py` — AuditLog | `sh_audit_logs` | **CANONICAL** | Security audit log. |
| `app/models.py` — ActivityLog | `activity_logs` | **LEGACY** | Lead activity tracking. |
| `app/enterprise/models.py` — AuditRecord | `m9_audit_records` | **DUPLICATE** | Enterprise audit records. |
| `app/founder/models.py` | — | **LEGACY** | Founder audit events. |
| `app/audit/` | — | **LEGACY** | Audit routes + service. |
| `app/genesis_protection.py` — AuditLog | `genesis_audit_log` | **DUPLICATE** | Genesis audit log. |
| `core/audit/` | — | **ARCHIVE** | Core audit — archived. |
| `governance/verification/` | — | **LEGACY** | Governance verification scripts. |

---

## 21. Relationship

### Canonical Production Owner
**`app/relationship/`**

- **Model:** `app/relationship/models.py` — `CanonicalRelationship` (table `rel_relationships`), `RelationshipCategory`, `RelationshipField`, `TimelineEntry`, `RelationshipMemory`, `RelationshipDocument`, `DuplicateGroup`, `DuplicateCandidate`.
- **Service:** `app/relationship/services.py`.
- **Routes:** `app/relationship/routes_api.py`, `app/relationship/routes_ui.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/relationship/` | `rel_*` tables | **CANONICAL** | Canonical relationship management. |
| `app/graph/models.py` — ObjectRelation | `object_relations` | **LEGACY** | Simple graph relations. |
| `app/graph/` | — | **LEGACY** | Graph service (edges, nodes, families, temporal). |
| `app/graph_universal/` | — | **ARCHIVE** | Universal graph — archived. |
| `app/space/models.py` — SpaceRelationshipRef | — | **TRANSITIONAL** | Space-scoped relationship references. |
| `core/relationship/` | — | **ARCHIVE** | Core relationship — archived. |
| `app/founder/models.py` — BusinessRelationship | `founder_relationships` | **DUPLICATE** | Founder relationships — should use canonical. |

---

## 22. Workspace

### Canonical Production Owner
**`app/workspace/models.py` → `Workspace` (table `user_workspaces`) + `app/workspace_objects/`**

- **Models:** `Workspace` (table `user_workspaces`), `WorkspaceMembership` (table `user_workspace_memberships`), `WorkspacePolicy` (table `wksp_policies`).
- **Objects:** `app/workspace_objects/service.py` — workspace-scoped object operations.
- **Routes:** `app/workspace/routes.py`, `app/workspace_routes.py`, `app/workspace_runtime.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/workspace/models.py` — Workspace | `user_workspaces` | **CANONICAL** | Type-based workspace with capability policies. |
| `app/production/identity/workspace_model.py` — Workspace | `workspaces` | **DUPLICATE** | Second workspace model in production/identity. |
| `app/objects/legacy_models.py` — Workspace | `sh_workspaces` | **TRANSITIONAL** | Legacy workspace for sh_objects. |
| `app/kernel/space.py` | — | **LEGACY** | Kernel space model. |
| `app/space/` | — | **TRANSITIONAL** | Universal Space domain model — being integrated with workspace. |
| `app/founder/models.py` — FounderSpace | `founder_spaces` | **DUPLICATE** | Founder spaces — should merge with canonical workspace. |
| `app/workspace_ui/` | — | **LEGACY** | Legacy workspace UI. |
| `app/workspace_routes.py` | — | **LEGACY** | Legacy workspace routes (may overlap with app/workspace/routes.py). |

---

## 23. Space (Universal Space Domain)

### Canonical Production Owner
**`app/space/`**

- **Model:** `app/space/models.py` — `UniversalSpace` (dataclass).
- **Runtime:** `app/space/runtime.py`.
- **Lifecycle:** `app/space/lifecycle.py`.
- **AI Resident:** `app/space/resident.py`.
- **Store:** `app/space/store.py`.
- **Routes:** `app/space/routes.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/space/` | — | **CANONICAL** | Phase A1 Universal Space Domain. The fundamental human-AI collaboration environment. |
| `app/workspace/models.py` — Workspace | `user_workspaces` | **TRANSITIONAL** | Workspace model — should converge with Space. |
| `app/production/identity/workspace_model.py` — Workspace | `workspaces` | **DUPLICATE** | Third workspace model. |
| `app/kernel/space.py` | — | **LEGACY** | Kernel space — should use UniversalSpace. |
| `core/workspace_runtime/` | — | **ARCHIVE** | Core workspace runtime. |
| `app/objects/legacy_models.py` — Workspace | `sh_workspaces` | **LEGACY** | Legacy workspace for sh_objects. |

---

## 24. Cognition / Intelligence

### Canonical Production Owner
**`app/intelligence/` + `core/intelligence_core.py`**

- **Engine:** `app/intelligence/engine.py`, `app/intelligence/reasoning.py`.
- **Runtime:** `app/intelligence/runtime.py`.
- **Decision engine:** `app/intelligence/decision_engine.py` (DUPLICATE — see Decision section).
- **Patterns:** `app/intelligence/models.py` — `Pattern` (table `patterns`).
- **Reasoning Traces:** `app/intelligence/models.py` — `ReasoningTrace` (table `m8_reasoning_traces`).

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/intelligence/` | `m8_*` tables | **CANONICAL** | M8 Executive Intelligence. |
| `core/intelligence_core.py` | — | **TRANSITIONAL** | Core intelligence — being migrated to app/intelligence/. |
| `core/inference_orchestrator/` | — | **ARCHIVE** | Inference orchestrator — archived. |
| `app/ai/` | — | **LEGACY** | AI chat interface (copilot, context, prompts, provider). |
| `app/llm/models.py` — ModelRun | `model_runs` | **LEGACY** | LLM model run tracking. |
| `app/inference/` | — | **ARCHIVE** | Inference module — archived. |
| `app/cognitive/` | — | **LEGACY** | Cognitive engine. |
| `core/cognitive_runtime/` | — | **ARCHIVE** | Cognitive runtime — archived. |
| `app/cortex/` | — | **LEGACY** | Cortex runtime (attention, brief, state). |

---

## 25. Finance

### Canonical Production Owner
**`app/finance/`**

- **Models:** `app/finance/models.py` — `Account`, `JournalEntry`, `LedgerEntry`, `FinInvoice`, `InvoiceItem`, `FinancePayment`, `TaxProfile`, `PurchaseOrder`, `Budget`.
- **Controls:** `app/finance/controls.py` — `ApprovalRequest`, `ApprovalAction`, `Delegation`, `FinancialPeriod`.
- **Evidence:** `app/finance/evidence.py` — `EvidencePolicy`, `FinancialEvidence`.
- **Services:** `app/finance/services.py`.
- **API Routes:** `app/finance/routes_api.py`.

### Competing Implementations

| Implementation | Table/Module | Classification | Notes |
|---|---|---|---|
| `app/finance/` | `fin_*` tables | **CANONICAL** | Canonical finance module. |
| `app/models.py` — Lead.payments | `leads` -> Payment (in `app/models.py:165`) | **LEGACY** | Legacy lead-scoped payments (not in fin_*). |
| `app/models.py` — Invoice, InvoiceItem | (in app/models.py) | **LEGACY** | Legacy invoice — should migrate to FinInvoice. |
| `app/payment_gateway.py` | — | **LEGACY** | Payment gateway integration. |
| `app/razorpay/` | — | **LEGACY** | Razorpay-specific payment handling. |
| `core/financial_intelligence/` | — | **ARCHIVE** | Core financial intelligence — archived. |

---

## Summary: Consolidation Priorities

### Critical (Remove duplicate production services)
1. **`app/production/identity/workspace_model.py`** → duplicate Workspace model. Use `app/workspace/models.py`.
2. **`app/founder/models.py`** — `FounderSpace`, `FounderObject`, `FounderConversation`, `FounderMessage`, `BusinessRelationship` → use canonical workspace, object, communication, relationship.
3. **`app/runtime/decision_engine.py`** + **`app/intelligence/decision_engine.py`** → consolidate into `app/decision/`.
4. **`app/execution_log/models.py`** (`act_execution_logs`) → merge with `app/execution_engine/models.py` (`execution_logs`).
5. **`app/security/audit.py`** (`sh_audit_logs`) + `app/enterprise/models.py` (`m9_audit_records`) + `app/genesis_protection.py` (`genesis_audit_log`) → consolidate.

### High Priority (Converge TRANSITIONAL into CANONICAL)
1. **`app/production/identity_repository.py`** (`shunya_identities`) → merge into `app/identity/service.py` + `Person`/`PersonIdentity`.
2. **Legacy `sh_objects`** (app/objects/legacy_models.py) → converge into `app/kernel/models.py` UOPObject.
3. **`app/space/` (UniversalSpace)** → converge with `app/workspace/models.py` Workspace.
4. **Legacy `objects` table** (`app/objects/models.py`) → converge into `sh_uop_objects`.
5. **`app/models.py` Document** → migrate to `app/document/models.py` DocumentRecord.
6. **`app/shunya/knowledge_store.py`** KnowledgeFact → formalize through canonical KnowledgeResolutionService.

### Medium Priority (Archive dead code)
1. `_archive/object_variants/`, `_archive/execution_variants/`, `_archive/graph_variants/`, `_archive/communication_legacy/`
2. `core/cognitive_runtime/`, `core/decision_intelligence/`, `core/execution_runtime/`, `core/planning_runtime/`
3. `app/cortex/`, `app/cognitive/`, `app/assistant/`