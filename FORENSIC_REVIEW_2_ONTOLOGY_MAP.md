============================================================
FORENSIC REVIEW #2 — FDA12-15 ONTOLOGY MAP
============================================================

============================================================================
PART 1: REPOSITORY-WIDE MODEL INVENTORY
============================================================================

| Concept | Existing Table | Existing Model | Existing Service | Authority |
|---------|---------------|---------------|------------------|-----------|
| Identity | persons | Person (app/models.py) | None | Canonical |
| Identity Claim | person_identities | PersonIdentity (app/models.py) | None | Canonical |
| Relationship | rel_relationships | CanonicalRelationship (app/relationship/models.py) | create_relationship | Canonical |
| Timeline | rel_timeline | TimelineEntry (app/relationship/models.py) | _add_timeline_entry | Canonical |
| Lead | leads | Lead (app/models.py) | CRM service | Canonical |
| Customer | customer | Customer (app/customers/models.py) | CRM service | Canonical |
| Proposal | proposals | Proposal (app/models.py) | CRM service | Canonical |
| Task | tasks | Task (app/models.py) | None | Canonical |
| Task List | task_lists | TaskList (app/models.py) | None | Canonical |
| Outcome | sh_outcomes | Outcome (app/execution/models.py) | Execution runtime | FDA2 spine |
| Execution | executions | Execution (app/execution_engine/models.py) | Execution engine | FDA2 spine |
| Execution Instance | execution_instances | None (no model) | Execution runtime | FDA2 spine |
| Commitment | commitments | Commitment (app/commitments/models.py) | None | Canonical |
| Rel Commitment | relationship_commitments | None (no model) | None | Specialized |
| Evidence | evidence_records | EvidenceRecord (app/evidence/models_db.py) | Evidence service | Canonical |
| Decision Trace | decision_traces | DecisionTrace (app/evidence/decision_trace.py) | None | Canonical |
| Ad Campaign | m6_ad_campaigns | AdCampaign (app/integration/models.py) | None | Specialized |
| Communication | communication_sources | CommunicationSource (app/communication/models.py) | Capture service | Canonical |
| Entity | entities | Entity (app/core/entity.py) | Entity service | Canonical |
| Entity Def | entity_definitions | None (no model) | Entity service | Canonical |
| Notification | notifications | Notification (app/models.py) | None | Canonical |
| Business Rel | None | BusinessRelationship (app/founder/models.py) | None | Specialized |
| Content Gen | None | ContentGeneration (app/integration/models.py) | None | Specialized |
| Workspace | sh_workspaces | None (no model) | Workspace runtime | Canonical |
| Workspace Event | wksp_events | WorkspaceEvent (app/founder/workspace_models.py) | None | Specialized |
| Context Prop | context_proposals | ContextProposal (app/human_context/models.py) | None | Specialized |
| Financial Evid | None | FinancialEvidence (app/finance/evidence.py) | None | Specialized |
| Learning Event | None | LearningEvent (app/intelligence/models.py) | None | Specialized |

============================================================================
PART 2: CONCEPT → OWNER MAPPING FOR FDA12-15
============================================================================

FDA12 — SALES INTELLIGENCE

| Concept | Decision | Owner | Action |
|---------|----------|-------|--------|
| LEAD SCORE | DERIVED INTELLIGENCE | Lead (app/models.py) | Compute from evidence, store in Lead.outcome field. No new model. |
| QUALIFICATION | EXISTING CANONICAL OWNER | Lead (app/models.py) | Lead.status + Lead.stage already handle qualification. Extend qualification state machine. |
| NEXT-BEST-ACTION | CONTEXTUAL MEMORY | TimelineEntry + Task | Recommendations are derived from evidence. No new model. |
| FOLLOW-UP INTELLIGENCE | CANONICAL TASK | Task (app/models.py) | Follow-ups are Tasks. SLA detection is computed. |
| PIPELINE HEALTH | RETRIEVAL DERIVED VIEW | Lead (app/models.py) | Pipeline stage distribution is computed. No new model. |
| FORECAST | DERIVED INTELLIGENCE | Lead + Proposal | Forecast is computed from pipeline. No new model. |
| SALESPERSON INTEL | RETRIEVAL DERIVED VIEW | Lead + Task | Computed from lead assignments and task completion. |
| CONVERSION/LOSS | EVENT/EVIDENCE | TimelineEntry + Lead | Computed from lead status changes and timeline events. |

FDA13 — CUSTOMER EXPERIENCE

| Concept | Decision | Owner | Action |
|---------|----------|-------|--------|
| CUSTOMER PROFILE | EXISTING CANONICAL OWNER — EXTEND | Customer (app/customers/models.py) | Add relationship_id, tenant_id, status, created_at, updated_at columns. |
| CUSTOMER HISTORY | EVENT/EVIDENCE | TimelineEntry | Already stored on relationship timeline. No new model. |
| ONBOARDING | EXISTING CANONICAL OWNER — COMPOSE | Commitment + Task | Onboarding states are commitments with tasks. Use existing Commitment model. |
| SERVICE COMMITMENTS | EXISTING CANONICAL OWNER — COMPOSE | Commitment (app/commitments/models.py) + relationship_commitments | Extend Commitment model. DO NOT create ServiceCommitment. |
| COMMUNICATIONS | EXISTING CANONICAL OWNER | CommunicationSource + TimelineEntry | Link communications to relationship timeline. No new model. |
| ISSUES | EXISTING CANONICAL OWNER — COMPOSE | Task + Commitment + TimelineEntry | Issue = governed task with commitment. No new Issue model. |
| SATISFACTION | EVENT/EVIDENCE | TimelineEntry | Customer satisfaction signals are timeline events. No new model. |
| ESCALATIONS | EXISTING CANONICAL OWNER — COMPOSE | Commitment + Task | Escalation = governed commitment with assignment. Use Commitment model. |
| RETENTION/REPEAT | DERIVED INTELLIGENCE | Lead + Customer + TimelineEntry | Computed from history. No new model. |
| CUSTOMER STATUS | RETRIEVAL DERIVED VIEW | Customer | Computed from customer state. No new model. |

FDA14 — MARKETING OS

| Concept | Decision | Owner | Action |
|---------|----------|-------|--------|
| CAMPAIGNS | MISSING CAPABILITY | NEW MODEL | AdCampaign exists but is platform-specific (m6_ad_campaigns). Create generic Campaign model. |
| AUDIENCES | MISSING CAPABILITY | NEW MODEL | No audience model exists. Create AudienceDefinition model. |
| CHANNELS | EXISTING CANONICAL OWNER | CommunicationSource | CommunicationSource already models external channels. Extend. |
| CONTENT PLANNING | MISSING CAPABILITY | NEW MODEL | ContentGeneration exists but is ad-specific. Create CampaignContent model. |
| LEAD CAPTURE | EXISTING CANONICAL OWNER | Lead (app/models.py) | Campaign leads enter the same Lead system. Add campaign_id to Lead. |
| SOURCE TRACKING | EXISTING CANONICAL OWNER — EXTEND | Lead (app/models.py) | Lead.source + Lead.utm_* fields. Add UTM/source metadata to Lead. |
| APPROVALS | EXISTING CANONICAL OWNER — COMPOSE | Commitment | Approval = governed commitment. Use Commitment model. |
| ASSET LINKAGE | EXISTING CANONICAL OWNER | Document/Entity system | Use existing document/entity systems. |

FDA15 — MARKETING INTELLIGENCE

| Concept | Decision | Owner | Action |
|---------|----------|-------|--------|
| ATTRIBUTION | DERIVED INTELLIGENCE | TimelineEntry + Lead + Campaign | Attribution is computed from canonical events. No new model. |
| PROVENANCE | EVENT/EVIDENCE | TimelineEntry | Existing timeline system. |
| CONVERSION | RETRIEVAL DERIVED VIEW | Lead + TimelineEntry | Computed from lead status. |
| CAC/CPA | DERIVED INTELLIGENCE | Campaign + Lead + Customer | Computed from campaign cost + conversion data. |
| REFERRAL/REPEAT | EXISTING CANONICAL OWNER — EXTEND | Lead + Customer | Track referral source in Lead. Repeat detection via Customer. |
| CHANNEL COMPARISON | RETRIEVAL DERIVED VIEW | Lead + CommunicationSource | Computed from lead source data. |
| EXPERIMENTS | MISSING CAPABILITY | NEW MODEL | Experiment metadata. Minimal model. |
| WASTE DETECTION | DERIVED INTELLIGENCE | Campaign + Lead | Computed from campaign performance. |
| REVENUE TRACE | RETRIEVAL DERIVED VIEW | Customer → Lead → Campaign | Traced via canonical FK chain. |

============================================================================
PART 3: NEW MODELS REQUIRED (MINIMAL)
============================================================================

| Proposed Model | Why Existing Cannot Support | Authority Type | Table |
|----------------|---------------------------|----------------|-------|
| Campaign | Generic marketing campaign. AdCampaign is platform-specific. | AUTHORITATIVE | campaigns |
| AudienceDefinition | No audience/segment model exists. | AUTHORITATIVE | audience_definitions |
| CampaignContent | Content planning. ContentGeneration is ad-specific. | AUTHORITATIVE | campaign_contents |
| Experiment | Experiment metadata. No existing experiment model. | AUTHORITATIVE | experiments |

============================================================================
PART 4: EXTENSIONS TO EXISTING OWNERS
============================================================================

| Owner | Extension | For FDA |
|-------|-----------|---------|
| Customer (app/customers/models.py) | Add relationship_id, tenant_id, lead_id, status, created_at, updated_at | FDA13 |
| Lead (app/models.py) | Add campaign_id, utm_source, utm_campaign, utm_medium, utm_term, utm_content | FDA14 |
| Commitment (app/commitments/models.py) | Add relationship_id, campaign_id, issue_type fields | FDA13 |
| TimelineEntry (app/relationship/models.py) | Add campaign_id, source_event references | FDA15 |

============================================================================
PART 5: DECISION SUMMARY
============================================================================

A. EXISTING CANONICAL OWNER — EXTEND: 
   Customer, Lead, Commitment, TimelineEntry, Task

B. EXISTING SPECIALIZED OWNER — COMPOSE/REFERENCE:
   CommunicationSource, EvidenceRecord, Outcome, Execution, AdCampaign

C. MISSING CAPABILITY — CREATE NEW MODEL:
   Campaign, AudienceDefinition, CampaignContent, Experiment

D. RETRIEVAL/DERIVED VIEW — DO NOT CREATE DURABLE TRUTH:
   LeadScore, Forecast, PipelineHealth, SalespersonIntel, Attribution,
   CAC/CPA, ChannelComparison, WasteDetection, CustomerStatus,
   RetentionScore, Conversion/Loss

============================================================================
PART 6: CUSTOMER DUPLICATION CHECK
============================================================================

Customer model: ONE canonical owner — app/customers/models.py (__tablename__="customer")
No duplicate. The 0001 migration was creating "customers" (plural) — FIXED to "customer" (singular).
Production database has "customer" table which matches the model.

============================================================================
PART 7: COMMITMENT ARCHITECTURE
============================================================================

Commitment is the canonical business execution spine:
- app/commitments/models.py: Commitment model (__tablename__="commitments")
- relationship_commitments table (no model) — for relationship-specific commitments
- FDA13 MUST use Commitment model, not create ServiceCommitment
- Customer promises → Commitment → Task → Outcome

============================================================================
DECISION: Proceed to FDA12-15 implementation with minimal new models.
4 new models (Campaign, AudienceDefinition, CampaignContent, Experiment).
Extend 5 existing owners (Customer, Lead, Commitment, TimelineEntry, Task).
ALL other capabilities are derived/retrieval views.