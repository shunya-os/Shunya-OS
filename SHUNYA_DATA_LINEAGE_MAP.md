# SHUNYA OS — Data Lineage Map

**Generated:** 2026-08-29  
**Methodology:** Repository code analysis, DB schema inspection (82+ tables across PostgreSQL), API route tracing, and end-to-end flow reconstruction.

---

## Lineage Pipeline Stages

| # | Stage | Description | Verification Method |
|---|-------|-------------|---------------------|
| 1 | **SOURCE** | Where raw data enters the system | Table columns, integration adapters |
| 2 | **INGESTION** | How raw data is captured and structured | ingestion/ modules, webhooks, API endpoints |
| 3 | **IDENTITY** | Identity resolution — who/what is this data about? | identity/service.py, core/identity_interface.py |
| 4 | **PERSISTENCE** | Where the data lives (table) | SQLAlchemy models |
| 5 | **RETRIEVAL** | How data is queried / read back | routes, service layers |
| 6 | **UI** | How data is surfaced to the user | frontend routes, templates |
| 7 | **AI** | AI processing of the data | intelligence/ modules, copilot, reasoning |
| 8 | **DECISION** | Decisions made based on the data | decision/ engine, decision_runtime |
| 9 | **EXECUTION** | Actions taken from the data | execution/ runtime, execution_engine |
| 10 | **EVIDENCE** | Proof of what happened | evidence/ models, models_db |
| 11 | **OUTCOME** | The result — was it successful? | Outcome (sh_outcomes), memory records |

---

## 1. Document

### Source → Ingestion → Identity → Persistence → Retrieval → UI → AI → Decision → Execution → Evidence → Outcome

#### SOURCE
- **User upload:** `app/upload/routes.py`, `app/objects/upload.py` → file stored in `uploads/` or cloudinary
- **External email attachment:** `app/communication/email.py`, `app/integration/gmail_ingest.py` → attachment from Gmail
- **API import:** `app/import_api/routes.py`, `app/import_export/service.py`
- **Text extraction:** `app/document_reader.py` — extracts text from uploaded files
- **Media upload:** `app/media.py` → `media_files` table, `app/media/models.py` → `m6_media_assets`

#### INGESTION
- `app/ingestion/` (empty module, not wired)
- `app/intake/` — candidate intake pipeline (`intake_sessions`, `intake_candidates`, `intake_field_mappings`)
- `app/integration/gmail_ingest.py` — Gmail message → document
- `app/documents_knowledge/` — document-knowledge bridge
- `app/content_studio/` — content generation → document

#### IDENTITY
- **Partial** — documents are scoped to tenant_id but only weakly linked to persons
- `app/document/models.py` — `DocumentRecord` has no `person_id` or `identity_id` field
- `app/models.py:Document` (legacy) — has no identity resolution
- **❌ CHAIN BREAKS HERE** — Uploaded documents are NOT routed through `IdentityResolutionInterface`. No identity claim is created for document authorship/ownership.

#### PERSISTENCE
- **Canonical:** `document_records` (`app/document/models.py`)
- **Legacy (still active):** `documents` (`app/models.py`)
- **Workspace-scoped:** `sh_objects` with `object_type='document'`
- **Relationship-scoped:** `rel_documents` (`app/relationship/models.py`)
- **Knowledge:** `knowledge_documents` (`app/models.py`)
- **Evidence-attached:** `evidence_records.target_id` may reference a document

#### RETRIEVAL
- `app/document_runtime/routes.py` — document runtime API
- `app/documents_knowledge/routes.py` — knowledge-scoped document retrieval
- `app/documents_api.py` — legacy document API
- `app/workspace_objects/service.py` — workspace-scoped object retrieval
- `app/objects/routes.py` — generic object CRUD

#### UI
- `frontend/` — React frontend (document viewer, upload dialog)
- `templates/` — legacy Jinja2 templates

#### AI
- `app/intelligence/` — document analysis via reasoning traces
- `app/ai/copilot.py` — AI copilot analyzes document content
- `app/document/models.py` — `ExtractedField` — AI-extracted fields from documents
- `app/search/` — document search

#### DECISION
- `app/decision/engine.py` — decision engine may reference documents as evidence
- `app/intelligence/decision_engine.py` — duplicate decision engine

#### EXECUTION
- Documents are inputs to execution but not directly executed
- `app/execution/runtime.py` — execution context may load documents

#### EVIDENCE
- `app/evidence/models.py` — Evidence records can reference documents via `target_id`
- `EvidenceRecord` in `evidence_records` documents evidence about document changes

#### OUTCOME
- `Outcome` (sh_outcomes) — execution outcome may reference document-related intent
- **❌ CHAIN BREAKS HERE** — No deterministic link from document creation/modification to an Outcome record. Document operations lack end-to-end outcome tracking.

---

## 2. Lead

### Source → Ingestion → Identity → Persistence → Retrieval → UI → AI → Decision → Execution → Evidence → Outcome

#### SOURCE
- **Telegram:** `app/telegram_webhook` (referenced in config, no direct file found) — Lead source = `telegram`
- **Manual entry:** `app/crm/routes.py`, `app/leads/routes.py` — manual lead creation
- **API:** `app/import_api/routes.py` — source = `api`
- **Email:** `app/communication/email.py`, `app/integration/gmail_ingest.py` — source = `email`
- **Intake pipeline:** `app/intake/` — `intake_signals` → `intake_sessions`

#### INGESTION
- `app/intake/service.py` — intake service processes raw signals
- `app/intake/mapper.py` — maps intake data to lead fields
- `app/intake/profiler.py` — lead profiling
- `app/intake/matcher.py` — lead matching (duplicate detection)

#### IDENTITY
- `app/models.py:Lead` — has `person_id` FK to `persons` and `entity_id` to `entities`
- `app/identity/service.py` — leads create Person + PersonIdentity claims
- **✅ CHAIN PASSES** — Lead creation triggers identity resolution via `Lead.__init__` event → auto-creates Entity + Person linkage

#### PERSISTENCE
- **Canonical:** `leads` (`app/models.py:Lead`)
- **Entity linkage:** `entities` via `entity_id`
- **Person linkage:** `persons` via `person_id`
- **Activity:** `activity_logs` — lead-scoped activity trail
- **Task/TaskList:** `tasks`, `task_lists` — lead-scoped tasks
- **Campaign attribution:** `leads.campaign_id` → `campaigns`
- **Relationship linkage:** `rel_relationships` via `commitments.relationship_id`

#### RETRIEVAL
- `app/leads/routes.py` — lead API endpoints
- `app/crm/service.py` — CRM service
- `app/sales_intelligence/service.py` — sales AI insights
- Lead `to_dict()` method serializes with optional payment/invoice expansion

#### UI
- `frontend/` — React CRM components
- `app/frontend/` — frontend app

#### AI
- `app/ai/copilot.py` — lead analysis
- `app/intelligence/insight.py` — lead insights
- `app/prediction/engine.py` — lead scoring / conversion prediction
- `app/sales_intelligence/` — sales-specific AI

#### DECISION
- `app/decision/engine.py` — decisions about leads (follow up, quote, convert)
- `app/decision_runtime/policy.py` — decision policies for lead handling
- `app/marketing_intelligence/service.py` — marketing decisions

#### EXECUTION
- `app/execution/runtime.py` — execute actions on leads (send email, create invoice, assign task)
- `app/automation/` — `AutomationRule` — lead automation triggers
- `app/orchestration/` — orchestrated lead workflows

#### EVIDENCE
- `app/evidence/models.py` — evidence for lead-related actions
- `app/evidence/decision_trace.py` — `DecisionTrace` for lead decisions
- `activity_logs` — lead activity as lightweight evidence
- **❌ CHAIN BREAKS HERE** — Lead activity is logged to `activity_logs` but not as formal Evidence records with immutable provenance.

#### OUTCOME
- `Lead.outcome` — string field tracking lead outcome (converted, lost, cancelled)
- `Lead.stage` — lifecycle stage
- `app/execution/models.py:Outcome` — formal Outcome may reference lead via `intention` field
- **⚠️ WEAK CHAIN** — Lead does not have a canonical `outcome_id` FK to `sh_outcomes`. The `outcome` field is a legacy string.

---

## 3. Invoice

### Source → Ingestion → Identity → Persistence → Retrieval → UI → AI → Decision → Execution → Evidence → Outcome

#### SOURCE
- **Manual creation:** `app/commercial/service.py` → proposal → invoice
- **Lead conversion:** Lead → Invoice via CRM
- **Finance module:** `app/finance/models.py:FinInvoice` → `fin_invoices`
- **API/Import:** `app/import_export/service.py`

#### INGESTION
- `app/finance/routes_api.py` — invoice API endpoints
- `app/commercial/models.py` — CommercialProposal → CommercialTransition → invoice
- **❌ CHAIN BREAKS HERE** — No ingestion pipeline for invoices. They are manually created via API or finance module.

#### IDENTITY
- **Weak** — FinanceInvoice has no `identity_id` or `person_id` column
- `FinInvoice.lead_id` — links back to Lead (which has person_id)
- **❌ CHAIN BREAKS HERE** — Invoices are NOT resolved through IdentityResolutionInterface. The payer/payee identity is implicit.

#### PERSISTENCE
- **Canonical (finance):** `fin_invoices` (`app/finance/models.py:FinInvoice`)
- **Legacy (models.py):** `Invoice` (SQLAlchemy model in `app/models.py` — not shown in schema dump, may be removed)
- **Invoice items:** `fin_invoice_items`
- **Payments:** `fin_payments`
- **Ledger:** `fin_ledger`
- **Journal:** `fin_journal_entries`
- **Purchase orders:** `fin_purchase_orders`
- **Budget:** `fin_budgets`

#### RETRIEVAL
- `app/finance/routes_api.py` — finance API
- `app/finance/services.py` — finance service layer
- Invoice `to_dict()` serialization

#### UI
- `frontend/` — invoice display components
- `app/invoices/` — invoice storage directory

#### AI
- `app/finance/intelligence.py` — financial intelligence
- `core/financial_intelligence/` — archived core module
- `app/prediction/engine.py` — payment prediction

#### DECISION
- `app/finance/controls.py` — `ApprovalRequest` — invoice approval decisions
- `app/finance/governance.py` — financial governance
- `app/decision/engine.py` — payment decisions

#### EXECUTION
- `app/finance/accounting.py` — accounting operations
- `app/execution/runtime.py` — payment execution
- `app/razorpay/` — Razorpay payment integration

#### EVIDENCE
- `app/finance/evidence.py` — `FinancialEvidence` (table `fin_evidence`)
- `app/finance/evidence.py` — `EvidencePolicy` (table `fin_evidence_policies`)
- **❌ CHAIN BREAKS HERE** — Financial evidence is stored in finance-specific tables (`fin_evidence`) instead of the canonical evidence store (`evidence_records`). Not linked to canonical `EvidenceRecord`.

#### OUTCOME
- `FinInvoice.status` — draft → sent → paid → void
- `Outcome` (sh_outcomes) — not directly linked
- **❌ CHAIN BREAKS HERE** — No direct link from FinInvoice to Outcome record. Payment outcome tracking is via `fin_payments`.

---

## 4. Person (Identity)

### Source → Ingestion → Identity → Persistence → Retrieval → UI → AI → Decision → Execution → Evidence → Outcome

#### SOURCE
- **Lead creation:** Lead → auto-creates Person via identity service
- **Gmail contact:** `app/identity/service.py` — resolves email to Person
- **Manual entry:** `app/routes.py`, `app/people/routes.py` — person CRUD
- **Import:** `app/import_export/` — contact import
- **Communication:** `app/communication/normalizer.py` — external participants → identities
- **Intake:** `app/intake/` — candidate → person

#### INGESTION
- `app/identity/service.py` — `IdentityService.add_claim()` — the canonical ingestion point
- `app/communication/inbound.py` — inbound communication → identity resolution
- `app/integration/gmail_ingest.py` — Gmail → identity claims

#### IDENTITY
- **✅ CHAIN PASSES** — IdentityService is the canonical identity resolution authority
- `Person` model (table `persons`) — canonical person storage
- `PersonIdentity` (table `person_identities`) — identity claims (email, phone, name)
- `SHUNYAIdentityModel` (table `shunya_identities`) — parallel identity store (TRANSITIONAL)
- `TeamMember` (table `team_members`) — legacy auth identity

#### PERSISTENCE
- **Canonical:** `persons` (app/models.py)
- **Claims:** `person_identities` (app/models.py)
- **Transitional:** `shunya_identities` (app/production/identity_repository.py)

#### RETRIEVAL
- `app/identity/service.py` — `resolve()`, `get_identity()`, `get_claims()`
- `app/people/routes.py` — people API
- `app/workspace/models.py:resolve_context()` — identity → workspace context

#### UI
- `frontend/` — contact/people display
- `app/workspace/models.py:AuthorizationContext` — UI context

#### AI
- `app/intelligence/` — identity-aware reasoning
- `app/ai/copilot.py` — AI knows who it's talking to via identity resolution

#### DECISION
- `app/decision/engine.py` — decisions about people (assign, promote, contact)
- `app/decision_runtime/policy.py` — identity-based policies

#### EXECUTION
- `app/execution/runtime.py` — execution context includes identity_id
- `app/execution/models.py:Outcome.identity_id` — who requested the execution

#### EVIDENCE
- `app/evidence/models.py` — Evidence can reference persons via `target_id`
- **❌ CHAIN BREAKS HERE** — Evidence system has `target_id` but no formal FK/policy linking evidence to identity resolution. Evidence is created outside the identity resolution chain.

#### OUTCOME
- `Outcome.identity_id` — links outcome to the person who initiated it
- **✅ CHAIN PASSES** — Outcome records are linked to identity_id.

---

## 5. Commitment

### Source → Ingestion → Identity → Persistence → Retrieval → UI → AI → Decision → Execution → Evidence → Outcome

#### SOURCE
- **Manual creation:** `app/commitments/routes.py` — API endpoint
- **Communication-derived:** `app/communication/base.py` — commitments from conversations
- **AI-derived:** `app/ai/prompts.py` — AI suggests commitments
- **Lead-derived:** Lead → Task → Commitment
- **Orchestration:** `app/orchestration/` — orchestrated commitment creation

#### INGESTION
- `app/commitments/service.py` — commitment service
- `app/communication/processor.py` — communication → commitment extraction
- **❌ CHAIN BREAKS HERE** — No formal ingestion pipeline with provenance tracking. Commitment creation is ad-hoc via API.

#### IDENTITY
- `Commitment.owner` — string field (not FK to persons)
- `Commitment.relationship_id` — FK to `rel_relationships`
- **❌ CHAIN BREAKS HERE** — `owner` is a string, not a resolved identity_id. No identity claim is created for commitment ownership.

#### PERSISTENCE
- **Canonical:** `commitments` (app/commitments/models.py)
- **Observations:** `commitment_observations` (app/observations/models.py)
- **Memory records (TRANSITIONAL):** `memory_records` where `memory_type='commitment'`
- **Idempotency:** `execution_idempotency` (app/execution/models.py)

#### RETRIEVAL
- `app/commitments/routes.py` — commitment API
- `app/commitments/service.py` — commitment service
- `app/decision_runtime/commitment.py` — decision runtime reads commitments

#### UI
- `frontend/` — commitment views
- `app/cortex/brief.py` — brief includes commitments

#### AI
- `app/intelligence/` — commitment analysis
- `app/ai/copilot.py` — commitment-aware AI
- `app/learning_intelligence/models.py:OutcomeProfile` — learns from commitment outcomes

#### DECISION
- `app/decision/engine.py` — evaluates commitment feasibility
- `app/decision_runtime/policy.py` — commitment policy
- `app/decision/models.py:DecisionContext.execution_id` — references commitments via execution

#### EXECUTION
- `app/execution/runtime.py` — executes commitments
- `app/execution_engine/engine.py` — step-by-step execution
- `app/execution/idempotency.py` — ensures commitments execute exactly once
- `app/execution_engine/truth.py` — truth tracking
- **✅ CHAIN PASSES** — Commitment → execution via idempotency key is well-structured.

#### EVIDENCE
- `app/evidence/models.py` — evidence for commitment completion
- `commitment_observations` — observed vs expected values
- `app/evidence/decision_trace.py` — decision traces for commitment decisions
- **⚠️ WEAK CHAIN** — Observations are stored in `commitment_observations` (not canonical `evidence_records`). The two evidence stores are not unified.

#### OUTCOME
- `Outcome` (sh_outcomes) — commitment outcome tracked via `commitment_id` and `commitment_type`
- `app/execution/models.py:Outcome.stage` — pending → in_progress → completed → failed
- **✅ CHAIN PASSES** — Commitment outcomes link to Outcome records via idempotency_key/commitment_id.

---

## 6. Object (Universal Object Protocol)

### Source → Ingestion → Identity → Persistence → Retrieval → UI → AI → Decision → Execution → Evidence → Outcome

#### SOURCE
- **Workspace objects API:** `app/workspace_objects/routes.py`, `app/workspace_objects/service.py`
- **Generic objects API:** `app/objects/routes.py`, `app/objects/service.py`
- **Legacy sh_objects:** `app/objects/legacy_models.py` — `ShunyaObject` (table `sh_objects`)
- **UOP (Universal Object Protocol):** `app/kernel/models.py` — `UOPObject` (table `sh_uop_objects`)
- **Core entity:** `app/core/entity.py` — `Entity` (table `entities`)

#### INGESTION
- `app/workspace_objects/service.py` — workspace-scoped object creation
- `app/kernel/object.py` — UniversalObject dataclass protocol
- `app/kernel/state.py` — state management
- `app/objects/upload.py` — file uploads → objects
- **❌ CHAIN BREAKS HERE** — Multiple parallel object stores (`objects`, `sh_objects`, `sh_uop_objects`, `entities`) with no single ingestion authority.

#### IDENTITY
- `objects.tenant_id` — tenant-scoped
- `sh_uop_objects.tenant_id`, `sh_uop_objects.created_by`, `sh_uop_objects.updated_by`
- `entities.tenant_id`
- **❌ CHAIN BREAKS HERE** — Objects are NOT resolved through IdentityResolutionInterface. `created_by`/`updated_by` are strings, not identity_ids.

#### PERSISTENCE
- **UOP Canonical:** `sh_uop_objects` (app/kernel/models.py) — full protocol with evidence, relationships, metadata
- **Transitional:** `objects` (app/objects/models.py) — simple type/state JSON
- **Legacy:** `sh_objects` (app/objects/legacy_models.py) — workspace-scoped objects
- **Legacy:** `entities` (app/core/entity.py) — generic entities
- **Object relations:** `object_relations` (app/graph/models.py)

#### RETRIEVAL
- `app/objects/routes.py` — generic object CRUD
- `app/workspace_objects/routes.py` — workspace-scoped object retrieval
- `app/workspace_objects/service.py` — workspace object service
- `app/space/store.py` — space-scoped object retrieval
- `app/kernel/routes.py` — kernel object API

#### UI
- `frontend/` — React object views
- `app/workspace_objects/` — workspace object UI

#### AI
- `app/intelligence/` — object-aware reasoning
- `app/ai/context.py` — object context in AI prompts
- `app/intelligence/observation.py` — object observations

#### DECISION
- `app/decision/engine.py` — decisions about objects
- `app/decision_runtime/` — object-based decisions

#### EXECUTION
- `app/execution/runtime.py` — execution context references objects
- `app/execution_engine/` — object-based execution steps

#### EVIDENCE
- `sh_uop_objects.evidence_json` — evidence stored inline on UOPObject
- `evidence_records.target_id` — canonical evidence references objects
- **⚠️ WEAK CHAIN** — Evidence is stored both inline (sh_uop_objects.evidence_json) and in canonical evidence_records. Dual storage without sync.

#### OUTCOME
- `Outcome` (sh_outcomes) — objects may be referenced via `intention` text
- **❌ CHAIN BREAKS HERE** — No direct FK/UUID link from Object/UOPObject to Outcome. The `intention` field is free-text.

---

## 7. Conversation / Communication

### Source → Ingestion → Identity → Persistence → Retrieval → UI → AI → Decision → Execution → Evidence → Outcome

#### SOURCE
- **Gmail:** `app/communication/email.py`, `app/integration/gmail_ingest.py`, `app/gmail_api_ingestion` (referenced)
- **WhatsApp:** `app/whatsapp_webhook.py`, `app/communication/whatsapp.py`
- **Internal message:** `app/communication/models.py` — `Message` (table `messages`)
- **Inbound webhook:** `app/communication/inbound.py` — `InboundEvent` (table `inbound_events`)
- **AI conversation:** `app/ai/copilot.py`, `app/companion.py`, `app/coach.py`

#### INGESTION
- `app/communication/processor.py` — communication processing pipeline
- `app/communication/normalizer.py` — normalizes external messages to canonical format
- `app/communication/inbound.py` — inbound event processing
- `app/integration/gmail_ingest.py` — Gmail ingestion pipeline
- `app/ingestion/` — empty module (not wired)
- **❌ CHAIN BREAKS HERE** — Gmail ingestion (`app/integration/gmail_ingest.py`) duplicates functionality with `app/communication/email.py`. Multiple ingestion paths without clear hierarchy.

#### IDENTITY
- `app/communication/base.py` — resolves sender/recipient identities
- `app/identity/service.py` — IdentityService resolves communication channels (email, phone)
- `ExternalParticipant` (table `external_participants`) — maps external identities
- `CommunicationSource` (table `communication_sources`) — source tracking
- **✅ CHAIN PASSES** — Communication channels are resolved through IdentityService (email → PersonIdentity).

#### PERSISTENCE
- **External conversations:** `external_conversations` (app/communication/models.py)
- **External messages:** `external_messages` (app/communication/models.py)
- **External participants:** `external_participants` (app/communication/models.py)
- **Messages:** `messages` (app/communication/models.py)
- **Message proposals:** `message_proposals` (app/communication/models.py)
- **Inbound events:** `inbound_events` (app/communication/inbound.py)
- **Founder conversations:** `founder_conversations`, `founder_messages` (DUPLICATE)
- **Sync cursors:** `sync_cursors` — ingestion checkpoint tracking

#### RETRIEVAL
- `app/communication/routes.py` — communication API
- `app/communication/service.py` — communication service
- `app/intelligence/context.py` — conversation context in AI

#### UI
- `frontend/` — chat/message UI
- `app/communication/conversation.py` — conversation rendering

#### AI
- `app/ai/copilot.py` — AI copilot in conversations
- `app/intelligence/` — conversation analysis
- `app/cortex/brief.py` — conversation summaries for AI brief
- `app/intelligence/awareness.py` — conversation awareness

#### DECISION
- `app/decision/engine.py` — decisions from communication context
- `app/decision_runtime/` — communication-derived decisions
- `app/communication/policy.py` — send/receive policies

#### EXECUTION
- `app/communication/delivery.py` — message delivery execution
- `app/execution/runtime.py` — communication actions as execution steps
- `app/communication/safe_send.py` — safe send guard

#### EVIDENCE
- `app/evidence/models.py` — communication events as evidence
- `app/evidence/decision_trace.py` — communication-based decisions
- **❌ CHAIN BREAKS HERE** — Communication messages are not routinely recorded as Evidence records. They live in `external_messages`/`messages` but the Evidence Engine has no formal ingestion from communication sources.

#### OUTCOME
- `Outcome` (sh_outcomes) — communication-related outcomes (message sent, proposal accepted)
- **⚠️ WEAK CHAIN** — Communication outcome tracking is weak. `message_proposals` track proposal state but don't link to canonical Outcome records.

---

## Chain Break Summary

| # | Object | Where Chain Breaks | Severity | Impact |
|---|--------|-------------------|----------|--------|
| 1 | **Document** | IDENTITY (not resolved), OUTCOME (no outcome link) | 🔴 CRITICAL | Documents are orphan objects — no identity, no outcome. |
| 2 | **Lead** | EVIDENCE (activity_logs not canonical evidence) | 🟡 MEDIUM | Lead audit trail uses activity_logs instead of evidence_records. |
| 3 | **Invoice** | IDENTITY (not resolved), EVIDENCE (fin_evidence not canonical), OUTCOME (no outcome link) | 🔴 CRITICAL | Invoices live in finance silo with no identity resolution or canonical evidence linkage. |
| 4 | **Person** | EVIDENCE (no formal evidence link to identity) | 🟡 MEDIUM | Identity resolution works, but evidence of identity changes is not formally tracked. |
| 5 | **Commitment** | INGESTION (ad-hoc, no provenance), IDENTITY (owner is string), EVIDENCE (dual store) | 🔴 CRITICAL | Commitment ownership is string-based, not identity-resolved. Observations live in separate table. |
| 6 | **Object** | INGESTION (multiple stores), IDENTITY (string-based), OUTCOME (no link) | 🔴 CRITICAL | 4 parallel object stores with no single authority. |
| 7 | **Conversation** | INGESTION (duplicate paths), EVIDENCE (no evidence ingestion), OUTCOME (weak) | 🟡 MEDIUM | Gmail ingestion duplicates communication/email. No evidence chain. |

---

## Recommended Fixes (Priority Order)

1. **Unify object stores** — Merge `objects` → `sh_objects` → `sh_uop_objects` → `entities` into a single UOPObject authority.
2. **Identity resolution for all objects** — Every entity that has an owner/creator/assignee must resolve through `IdentityResolutionInterface`. Replace string fields with `identity_id` FKs.
3. **Canonical evidence ingestion** — `activity_logs`, `commitment_observations`, `fin_evidence` must converge on `evidence_records`. Add evidence source adapters.
4. **Outcome linkage** — Every business object (Document, Invoice, Lead) should carry an optional `outcome_id` FK to `sh_outcomes`.
5. **Gmail ingestion consolidation** — Merge `app/integration/gmail_ingest.py` into `app/communication/email.py` with a single ingestion authority.
6. **Founder module convergence** — `founder_*` tables (`founder_spaces`, `founder_objects`, `founder_conversations`, `founder_messages`, `founder_relationships`) must converge into their canonical counterparts.
7. **Provenance on ingestion** — All ingestion paths should create immutable provenance records tracking source, timestamps, and transformation steps.