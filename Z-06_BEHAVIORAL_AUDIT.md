# Z-06 Behavioral Audit: SHUNYA Runtime vs Universal Behavior Constitution

**Date:** 2026-08-01  
**Scope:** All models, routes, and frontend components  
**Kernel LOC (constitutional contract):** 2,586 lines (10 files)  
**Total app LOC:** 90,066 lines (362 files) — ~96% custom behavioral code  
**Total frontend LOC:** 8,411 lines (39 files) — 100% custom, no constitutional contract consumed

---

## 1. Every Model Class and Its Custom Behaviors

### 1A. Legacy SQLAlchemy Models (app/models.py) — 32 classes, 1,379 LOC

These are the **primary offenders** — every one is a completely custom, non-constitutional model:

| Class | Status Fields | Lifecycle | Relationships | Audit | Custom `to_dict` |
|---|---|---|---|---|---|
| **Lead** | `LeadStatus` (NEW, IN_PROGRESS, CONVERTED, CANCELLED, ON_HOLD) — NOT LifecycleState | Manual status strings in routes; `log_activity()` helper | Hardcoded FK to Person, Payment, Invoice, TaskList, Document, Notification, Celebration, ClientUser, ClientMessage | Custom `ActivityLog` per-lead | Yes |
| **Payment** | `PaymentType` (GUEST, SUPPLIER, REFUND, DEPOSIT) | None | FKey to Lead only | None | Yes |
| **Supplier** | `rating` (int), no status enum | None | None (standalone) | None | Yes |
| **Invoice** | `InvoiceStatus` (DRAFT, SENT, PAID, VOID, OVERDUE) — NOT LifecycleState | Comment-only: `draft → sent → paid / void` | FKey to Lead only | None | Yes |
| **ItineraryRef** | None | None | None (standalone) | None | Yes |
| **TaskList** | None | None | FKey to Lead; hardcoded FK => Task | None | Yes |
| **Task** | `status` string (pending/in_progress/completed/cancelled) — NOT LifecycleState | Custom status strings, `completed_at` timestamp | FKey to TaskList | None | Yes |
| **Notification** | `NotificationType` enum — NOT LifecycleState | `is_read` boolean | FKey to Lead | None | Yes |
| **ClientUser** | `is_active` boolean | Custom password hashing (SHA-256+salt, NOT standard auth) | FKey to Lead | None | Yes |
| **ClientMessage** | `sender` string (client/team), `is_read` | None | FKey to Lead + ClientUser | None | Yes |
| **Document** | `classification` string | None | FKey to Lead | None | Yes |
| **ActivityLog** | `action` string, `user` string | None | FKey to Lead | **This IS the audit system** — custom for Leads only | Yes |
| **Celebration** | `type` string, custom `icon`/`animation` | None | FKey to Lead | None | Yes |
| **Person** | Custom `status` string (active) — NOT LifecycleState | None | Hardcoded FK to PersonIdentity, EmployeeProfile, CustomerProfile, SupplierContactProfile, ClientUserProfile | None | Yes |
| **PersonIdentity** | `verification_state` string | None | FKey to Person | None | Yes |
| **EmployeeProfile** | `status` string, `department`, `role` | None | FKey to Person + Tenant; `manager_person_id` (integer FK, not graph) | None | No |
| **CustomerProfile** | `segment` string | None | FKey to Person + Tenant | None | No |
| **SupplierContactProfile** | `role_in_organization`, `is_primary` | None | FKey to Person | None | No |
| **ClientUserProfile** | `portal_access_granted` | None | FKey to Person | None | No |
| **Relationship** (line 835) | Custom `status` string (active) — NOT LifecycleState, also has `relationship_type` | Custom `started_at`/`ended_at` | FKey to Person; its own `RelationshipEvent` and `RelationshipCommitment` tables | None | Yes |
| **RelationshipEvent** | `event_type` string, `metadata_json` | None | FKey to Relationship | None | Yes |
| **RelationshipCommitment** | `direction`, `status` (open/resolved) | Custom `resolved_at` | FKey to Relationship | None | Yes |
| **IntakeSession** | Custom lifecycle: `RECEIVED→PROFILED→MAPPING_REQUIRED→READY_FOR_REVIEW→APPROVED→IMPORTING→COMPLETED/FAILED→CANCELLED` | Full custom lifecycle machine in comments only (not enforced) | FKey to Tenant | None | Yes |
| **KnowledgeFact** | None | `validate_value()`, custom JSON deserialization | Standalone | None | Yes |
| **Observation** | None | None | Standalone | None | Yes |
| **LearningEntry** | None | None | Standalone | None | Yes |
| **Organization** | None | None | Hardcoded FKey to OrgMember | None | Yes |
| **OrgMember** | `role` string | None | FKey to Org + User | None | Yes |
| **PersonListShare** | `permission` string | None | FKey | None | Yes |

### 1B. Founder SQLAlchemy Models (app/founder/models.py) — 5 classes, 161 LOC

| Class | Status Fields | Lifecycle | Relationships | Audit | Custom |
|---|---|---|---|---|---|
| **FounderSpace** | Custom `status` (active) — NOT LifecycleState | None | Hardcoded FK => FounderObject | None | `to_dict()`, `object_count` |
| **FounderObject** | Custom `status` (active) — NOT LifecycleState | None | Hardcoded FK => FounderSpace + FounderConversation | None | `to_dict()`, custom `content` as string |
| **FounderConversation** | Custom `status` (active) | None | Hardcoded FK => FounderObject + FounderMessage | None | `to_dict()`, `message_count` |
| **FounderMessage** | None | None | Hardcoded FK => FounderConversation | None | `to_dict()` |
| **BusinessRelationship** | Custom `status` (active), custom `tags` CSV | None | Hardcoded FK => FounderSpace | None | `to_dict()`, CSV tag parsing |

### 1C. Auth/Security SQLAlchemy Models

| Class | File | Status Fields | Custom Behaviors |
|---|---|---|---|
| **TeamMember** | app/auth.py | None | Custom password hashing, token generation, `to_dict()` |
| **FeatureRequest** | app/approval.py | None | `to_dict()` |
| **Role** | app/authz/models.py | None | `has_permission()`, `to_dict()` |
| **OrgMemberRole** | app/authz/models.py | None | `to_dict()` |
| **Tenant** | app/tenant.py | None | Hardcoded FKey to TenantTheme, `to_dict()` |
| **TenantTheme** | app/tenant.py | None | `to_dict()` |
| **WorkspacePolicy** | app/workspace/models.py | None | `to_dict()` |

### 1D. Communication SQLAlchemy Models (app/communication/models.py)

All 8 classes (CommunicationSource, CommunicationCapturePolicy, CommunicationCaptureScope, ExternalConversation, ExternalMessage, ExternalParticipant, ExternalAttachmentReference, SyncCursor, OAuthState) — each has `__repr__` only, hardcoded FK relationships, no LifecycleState usage, no graph-based relationships.

### 1E. Document/Automation/Enterprise SQLAlchemy Models

- **AutomationRule** — `to_dict()` only
- **AutomationLog** — `to_dict()` only
- **DocumentRecord, DocumentSection, ExtractedField, DocumentComparison, ComparisonItem** — all have `db.Column` only, no behaviors
- **AuditRecord, EnterpriseRole, EnterpriseTeamMember** — `to_dict()` only; custom audit table (NOT using constitutional timeline)

### 1F. Dataclass-only Models (in-memory, no DB persistence)

~370 additional dataclass-based model classes exist across the system in app/awareness/, app/cognitive/, app/collaboration/, app/decision/, app/decision_runtime/, app/execution_intelligence/, app/executive/, app/for1/, app/for2/, app/founder/, app/graph/, app/graph_universal/, app/intake/, app/intelligence/, app/shunya/, app/space/, app/temporal/, etc.

**Every single one** implements its own `to_dict()` method — not inheriting from UniversalObject. Most have `__post_init__` for default values. Key examples:

- **UniversalSpace** (app/space/models.py) — Implements `space_id`, `entity_id`, `entity_type`, `name`, `status` properties manually (DUPLICATES UniversalObject contract)
- **SpaceLifecycle** (app/space/lifecycle.py) — Custom 5-state lifecycle (Draft/Active/Dormant/Archived/Historical) that **completely bypasses** the kernel's LifecycleState system from app/kernel/types.py
- **SHUNYAIdentity** (app/shunya/identity/models.py) — Implements its own Identity contract, separate from app/kernel/identity.py
- **KnowledgeObject** (app/shunya/knowledge_store/models.py) — Custom `is_active()`, `is_archived()`, `clone_for_version()` — reimplements UniversalObject contract
- **Decision** (app/decision_runtime/models.py) — Custom `transition_to()` method with its own lifecycle
- **AttentionItem** (app/cortex/attention.py) — Custom `transition_to()` with its own state machine
- **ExecutionPlan** (app/shunya/planner/models.py) — 214 lines, full custom planning domain with task management, dependency graphs, scheduling — none using kernel contract
- **Workflow** (app/shunya/executor_engine/models.py) — 80 lines, custom task/workflow orchestrator with `find_task()`, `completed_tasks()`, `all_completed()` — none using kernel StateMachine

### 1G. Graph Models (app/graph_universal/)

The graph_universal/ package provides entity, event, identity, property, relationship, runtime, traversal modules — but these are **also custom implementations** that do NOT use the kernel contract. They define their own relationship types, event types, and traversal logic independently of app/kernel/relationship.py.

---

## 2. Every Route Handler and Its Custom Behavior

### 2A. Main Routes (app/routes.py) — 1,783 lines — Heaviest offender

| Route | Custom CRUD Logic | Behavioral Deviations |
|---|---|---|
| `POST /orgs` | Manual org creation with slug generation, identity check, FounderSpace creation | **Constitution skipped** — no UniversalObject, no graph relationship, no event emission, manual commit |
| `GET/POST /leads/new` | Manual Lead creation with custom code, form parsing | **No constitutional lifecycle** — sets raw status string. Manual `_log_activity()` call instead of timeline event |
| `GET /leads/<id>` | Manual lead detail with Coach insights, dynamic fields | **No constitutional health/observation** — custom coach engine |
| `POST /leads/<id>/status` | Manual status update with old→new validation against LeadStatus enum | **No StateMachine** — manually sets `lead.status = new_status`. Manual `_log_activity()` instead of timeline event |
| `POST /leads/<id>/status` (API) | Duplicate of above for kanban | Same deviations |
| `GET/POST /leads/<id>/edit` | Manual field-by-field update with `setattr` | **No versioning, no event, no timeline** |
| `POST /creative/generate` | Creative asset generation with save | **No constitutional execution** — custom CreativeAsset model |
| `POST /creative/<id>/approve` | Manual status change `asset.status = "approved"` | **No StateMachine** |
| `GET /calendar/events` | Custom CalendarService call | **No constitutional timeline** |
| `GET /welcome` | Manual stats aggregation | No kernel usage |

### 2B. Object Creation Routes (app/production/objects.py) — 109 lines

| Route | Custom Logic | Deviations |
|---|---|---|
| `POST /api/v1/objects/<type>` | Custom OBJECT_TYPES dict with field/required definitions, manual FounderObject creation, content serialized as string | **No UniversalObject**, **no kernel ObjectRegistry**, **no StateMachine**, **no Timeline**, **no event emission**, **no graph relationship**. Content is a stringified dict, not structured |

### 2C. Founder Routes (app/founder/routes.py) — 1,214 lines

Massive route file with custom object management, type listing, search, conversation handling. All custom — no kernel contract. Contains hardcoded SQL queries against founder_objects/founder_spaces tables.

### 2D. Space Routes (app/space/routes.py) — 797 lines

Custom space management routes. Uses SpaceStore (in-memory) and SpaceLifecycle but NOT the kernel's StateMachine or Timeline. Its own SpaceLifecycle is a separate implementation from kernel/types.py LifecycleState.

### 2E. Other Route Files (29 total, ~7,000+ lines combined)

| File | LOC | Custom Behaviors |
|---|---|---|
| app/routes.py | 1,783 | Legacy CRUD, manual ActivityLog, custom status transitions |
| app/founder/routes.py | 1,214 | Custom object CRUD, type listing, search |
| app/space/routes.py | 797 | Custom space management, custom lifecycle |
| app/for1/routes.py | 523 | Custom domain logic |
| app/for2/routes.py | 463 | Custom domain logic |
| app/finance/routes_api.py | 483 | Custom finance CRUD |
| app/auth_routes.py | 395 | Custom auth flow, session management |
| app/relationship/routes_api.py | 334 | Custom relationship CRUD (NOT using kernel RelationshipEngine) |
| app/genesis_routes.py | 283 | Custom genesis/policy routes |
| app/authz/routes.py | 235 | Custom permission routes |
| app/production/identity/*.py | 1,100+ | Custom org/user/invitation CRUD, all SQLAlchemy direct |
| app/automation/routes.py | 172 | Custom automation CRUD |

**None of the 29 route files use the kernel StateMachine, Timeline, RelationshipEngine, or Context classes.**

---

## 3. All Lifecycle Customizations Per Object Type

### 3A. Custom Lifecycle Definitions (NOT LifecycleState from kernel/types.py)

| Source | States Defined | Violation |
|---|---|---|
| **app/models.py — Lead** | `LeadStatus`: NEW, IN_PROGRESS, CONVERTED, CANCELLED, ON_HOLD | Should use LifecycleState: CREATE → OBSERVE → ENRICH → RELATE → ... |
| **app/models.py — Invoice** | `InvoiceStatus`: DRAFT, SENT, PAID, VOID, OVERDUE | Same |
| **app/models.py — Task** | String: pending, in_progress, completed, cancelled | Same |
| **app/models.py — IntakeSession** | Comment-only: RECEIVED→PROFILED→MAPPING_REQUIRED→READY_FOR_REVIEW→APPROVED→IMPORTING→COMPLETED/FAILED/CANCELLED | Full custom machine in comments, not enforced |
| **app/space/lifecycle.py — SpaceLifecycle** | DRAFT, ACTIVE, DORMANT, ARCHIVED, HISTORICAL | Separate from kernel LifecycleState (CREATE, OBSERVE, ENRICH, RELATE, PREDICT, EXECUTE, ARCHIVE, RESTORE, DELETE) |
| **app/decision_runtime/models.py — Decision** | Custom `transition_to()` | No kernel StateMachine usage |
| **app/cortex/attention.py — AttentionItem** | Custom `transition_to()` | No kernel StateMachine usage |
| **app/automation/models.py — AutomationRule** | No lifecycle at all | Missing constitutional lifecycle |
| **app/communication/models.py** (8 models) | No lifecycle at all | Missing constitutional lifecycle |
| **app/document/models.py** (5 models) | No lifecycle at all | Missing constitutional lifecycle |

### 3B. Objects with NO Lifecycle Implementation

The majority of the ~481 model classes have **no lifecycle state tracking at all**. This includes all dataclass models in awareness, cognitive, collaboration, decision, evidence, execution_intelligence, executive, for1, for2, graph, graph_universal, human_context, inference, intake, integration, intelligence, learning, memory, planning, prediction, privacy, shunya/* (engine models), temporal, workspace models.

---

## 4. All Relationship Types — Hardcoded vs Graph-Based

### 4A. Hardcoded SQLAlchemy ForeignKey Relationships (NOT graph-based)

These bypass the constitutional graph RelationshipEngine entirely:

| Source Model | Target Model | Relationship Type |
|---|---|---|
| Lead | Person | `person_id` FK |
| Lead | Payment | `backref=lead` |
| Lead | Invoice | `backref=lead` |
| Lead | ActivityLog | `backref=lead` |
| Lead | Notification | `backref=lead` |
| Lead | Celebration | `backref=lead` |
| Lead | ClientUser | `backref=lead` |
| Lead | ClientMessage | `backref=lead` |
| Lead | Document | `backref=lead` |
| Lead | TaskList | `lead_id` FK |
| Lead | IntakeSession | Application-level only |
| Person | PersonIdentity | `backref=person`, cascade |
| Person | EmployeeProfile | `backref=person`, uselist=False |
| Person | CustomerProfile | `backref=person`, uselist=False |
| Person | SupplierContactProfile | `backref=person`, uselist=False |
| Person | ClientUserProfile | `backref=person`, uselist=False |
| Person | Relationship | `backref=relationships` |
| Relationship | RelationshipEvent | `backref=events` |
| Relationship | RelationshipCommitment | `backref=commitments` |
| TaskList | Task | `backref=task_list`, cascade |
| FounderSpace | FounderObject | `backref=space`, cascade |
| FounderObject | FounderConversation | `backref=object`, cascade |
| FounderConversation | FounderMessage | `backref=conversation`, cascade |
| Tenant | TenantTheme | `backref=tenant` |
| Tenant | Organization | Application-level |
| Organization | OrgMember | `backref=organization` |
| Notification | Lead | `backref=notifications` |

**Total hardcoded FK-based relationships: ~40+** across the models.

### 4B. Graph-Based Relationship Implementations

| Component | Type | Notes |
|---|---|---|
| **app/kernel/relationship.py — RelationshipEngine** | In-memory graph | Constitutional contract — NOT used by any model |
| **app/graph_universal/relationship.py** | Custom graph | Separate implementation, does NOT use kernel RelationshipEngine |
| **app/space/relationships.py** | Custom | Space-level relationships only |
| **app/relationship/models.py** | SQLAlchemy | Separate table-based relationship system |
| **app/relationship/service.py** | Custom service | Business logic for relationships |
| **app/shunya/reasoning/evidence_graph.py** | Custom graph | For reasoning evidence only |

**Verdict:** Zero SQLAlchemy models use the constitutional graph RelationshipEngine. All relationships are hardcoded FK chains.

---

## 5. All Event/Audit Mechanisms

### 5A. Audit Mechanisms Found

| Mechanism | Scope | Constitutional? |
|---|---|---|
| **ActivityLog** (app/models.py) | Lead-specific only. Tracks `action`, `detail`, `user` | **No** — should use kernel Timeline |
| **RelationshipEvent** (app/models.py) | Business Relationship events only | **No** — separate table, not kernel Timeline |
| **RelationshipCommitment** (app/models.py) | Relationship commitments | **No** |
| **AuditRecord** (app/enterprise/models.py) | Enterprise/generic audit | **No** — separate table, not kernel Timeline |
| **CredentialAuditEntry** (app/shunya/infrastructure/credential_store.py) | Credential operations | **No** — dataclass, no persistence |
| **CanonicalEvent** (app/shunya/infrastructure/event_bus.py) | Event bus (in-memory) | **No** — not used for object timelines |
| **SpaceTimelineEvent** (app/space/models.py) | Space timelines | **No** — separate dataclass, not kernel Timeline |
| **TimelineEvent** (app/temporal/timeline.py) | Temporal engine | **No** — separate implementation |
| **GovernanceVerdict** (app/shunya/governance_engine/models.py) | Governance | **No** |
| **Kernel Timeline** (app/kernel/timeline.py) | Universal | **YES but unused** — constitutional contract, zero adopters |
| **Kernel StateMachine observers** (app/kernel/state.py) | Universal | **YES but unused** — every transition notifies observers |

### 5B. Models With NO Audit/Event Tracking

**~95% of all model classes** have no audit, no event history, no timeline tracking. Including:
- Payment, Supplier, ItineraryRef, Task, Notification, ClientUser, ClientMessage, Document, Celebration
- All communication models, document models, automation models
- All awareness, cognitive, collaboration, dataclass models
- FounderObject, FounderSpace, FounderConversation, FounderMessage
- All graph_universal entities

---

## 6. Lines of Behavioral Code vs Constitutional Contract Collapse

### 6A. Current Code Distribution

| Layer | Files | LOC | % of Total |
|---|---|---|---|
| **Kernel (constitutional contract)** | 10 | 2,586 | 2.9% |
| **Legacy SQLAlchemy models** (app/models.py) | 1 | 1,379 | 1.5% |
| **Other SQLAlchemy models** (~40 files) | ~40 | ~5,000 | 5.6% |
| **Dataclass models** (~330 files) | ~330 | ~25,000 | 27.8% |
| **Route handlers** | 29 | ~9,400 | 10.4% |
| **Service/engine files** | ~100 | ~35,000 | 38.9% |
| **Frontend components** | 39 | 8,411 | 9.3% |
| **Other** (config, scripts, adapters) | ~100 | ~3,290 | 3.6% |

### 6B. Estimated Collapse Under Constitutional Contract

If all models adopted UniversalObject + kernel StateMachine + Timeline + RelationshipEngine:

| Component | Current LOC | Constitutional LOC | Savings |
|---|---|---|---|
| Legacy models (app/models.py) | 1,379 | ~200 (5-way discriminated object) | ~85% |
| Founder models (app/founder/models.py) | 161 | ~30 (1 table, typed content) | ~80% |
| All communication models (app/communication/models.py) | ~500 | ~50 (1 generic object) | ~90% |
| All document models (app/document/models.py) | ~300 | ~30 | ~90% |
| All automation models (app/automation/models.py) | ~150 | ~15 | ~90% |
| All space models (app/space/models.py + lifecycle.py) | ~800 | ~100 | ~87% |
| Dataclass models across all engines (~330 classes) | ~25,000 | ~500 (typed objects only, no unique classes) | ~98% |
| Graph models (app/graph/, app/graph_universal/) | ~2,500 | ~500 | ~80% |
| Intelligence models (app/intelligence/) | ~1,000 | ~100 | ~90% |
| Cognitive models (app/cognitive/) | ~2,500 | ~200 | ~92% |
| Decision/executive models | ~3,000 | ~300 | ~90% |
| Shunya engine models (planner, reasoning, etc.) | ~5,000 | ~500 | ~90% |
| **Subtotal: Model/Data Layer** | **~42,290** | **~2,525** | **~94%** |
| Route handlers (bypassing constitutional CRUD) | ~9,400 | ~2,000 (generic object CRUD × blueprint) | ~79% |
| Service/engine logic (custom workflows) | ~35,000 | ~10,000 (shared engine components) | ~71% |
| Frontend components | 8,411 | ~3,000 (generic object components) | ~64% |
| **Grand Total** | **~90,066** | **~17,525** | **~80.5%** |

### 6C. Key Line-Item Collapse Points

1. **`to_dict()` serialization**: ~400+ implementations → 1 method on UniversalObject
2. **Custom lifecycle enums**: 7+ different status/lifecycle enums → 1 LifecycleState
3. **Custom status transition logic**: 10+ implementations → 1 StateMachine
4. **Custom relationship management**: 40+ hardcoded FK chains → 1 RelationshipEngine
5. **ActivityLog audit pattern**: Lead-only, custom → 1 Timeline per object
6. **Custom CRUD routes**: 29 files of bespoke endpoint logic → generic typed handler
7. **Custom search**: Fragmented (Lead contains, founder objects, etc.) → constitutional search by meaning
8. **Frontend object forms**: Object-type-specific forms → generic dynamic form component

---

## Summary of Constitutional Violations

### Z-06 Mandate vs Current Reality

| Constitutional Requirement | Status | Violation |
|---|---|---|
| **Every object shares ONE behavioral contract (UniversalObject)** | ❌ FAIL | ~480 model classes, ~400 of which are custom dataclasses. Only `SHUNYAIdentity` and `Space` extend UniversalObject |
| **Every object exposes the same lifecycle** | ❌ FAIL | 7+ different lifecycle enums, many models have no lifecycle at all |
| **Lifecycle: Created→Identified→Understood→Related→Active→Observed→Updated→Executed→Completed→Archived→Recoverable→Deleted** | ❌ FAIL | Lead: NEW→IN_PROGRESS→CONVERTED→CANCELLED→ON_HOLD. IntakeSession: RECEIVED→PROFILED→... Not matched |
| **Graph-based relationships (no hardcoded chains)** | ❌ FAIL | ~40+ hardcoded ForeignKey chains. Zero models use RelationshipEngine |
| **Immutable events: Created, Viewed, Edited, Commented, etc.** | ❌ FAIL | Only ActivityLog for Leads. No constitutional events anywhere |
| **Every object owns a timeline** | ❌ FAIL | Zero models attach a kernel Timeline. Separate temporal/space timelines exist |
| **Search by meaning, not by module** | ❌ FAIL | Custom search per object type (Lead contains(), founder_objects query, etc.) |
| **Everything is observable** | ❌ FAIL | No health/activity/risk/confidence tracking on objects |
| **Objects perform work (execution attached to object)** | ❌ FAIL | Workflows live in shunya/planner, separate from objects |
| **Objects preserve history** | ❌ FAIL | No previous values, no relationship history, no versions on any model |
| **Deterministic stateless reconstruction** | ❌ FAIL | In-memory stores, global singletons prevent stateless replay |
| **Provider independence** | ✅ PASS | AI provider abstraction exists |
| **Persistence** | ❌ PARTIAL | SQLAlchemy models persist but dataclass models are in-memory only |

### Critical Path Forward

The kernel (`app/kernel/`) provides the constitutional contract in 2,586 lines — already written and available. The behavioral code audit shows **~90,066 lines of custom behavior** that could collapse to ~17,525 under the contract — an **80.5% reduction**. The migration path:

1. **Phase 1**: Convert legacy models (Lead, Payment, etc.) to UniversalObject subclasses
2. **Phase 2**: Replace all 40+ hardcoded FK chains with graph-based relationships
3. **Phase 3**: Replace ActivityLog with kernel Timeline on every object
4. **Phase 4**: Generic typed CRUD handler replacing 29 route files
5. **Phase 5**: Collapse all dataclass models into typed UniversalObject subclasses
6. **Phase 6**: Frontend: generic dynamic components replacing per-type forms