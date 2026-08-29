# M2C1 — SHUNYA OS Forensic Capability Matrix (DRAFT)

> **SHA**: c0ac336  
> **Generated**: 2026-08-29  
> **Methodology**: Direct inspection of frontend components, executive-home.tsx panel router, backend routes, data models, and PostgreSQL tables with row counts.

---

## Forensic Capability Matrix

| Domain | Frontend Component | Backend Routes | Data Model | Real Data Exists | Verdict |
|--------|-------------------|----------------|------------|-----------------|---------|
| **People** | `<OrganizationBrowser />` (from `organization/`) routed at `type==='people'` | `app/people/routes.py` — `/api/v1/people` | `OrgMember` (app.models) + in-memory FDA23 stores | `org_members: 2`, `organizations: 1` | **GREEN** |
| **Conversations** | `<ConversationWorkspace />` (from `conversation/`) routed at `type==='conversation'` | `app/communication/routes.py` — `/api/v1/communication` | `ExternalConversation`, `ExternalMessage` + `FounderConversation`, `FounderMessage` | `founder_conversations: 7`, `founder_messages: 13`, `messages: 0` | **GREEN** |
| **Work** | `<CommitmentWorkspace />` routed at `type==='commitment'` | `app/commitments/routes.py`, `app/execution/routes.py`, `app/execution_engine/routes.py` — `/api/v1/outcomes` | `Commitment`, `Task`, `Outcome`, `Execution` | `commitments: 5`, `tasks: 14`, `outcomes: 3`, `executions: 0` | **GREEN** |
| **Finance** | `DomainOverview` only — no dedicated component (`finance/` dir absent) | No dedicated backend routes module | `app/finance/models.py` — `Account`, `JournalEntry`, `LedgerEntry`, `Invoice`, etc. | `fin_invoices: 20`, other tables empty | **AMBER** |
| **Commercial** | `<CommercialWorkspace />` (from `commercial/`) routed at `objectId==='commercial'` | `app/commercial/routes.py` — `/api/v1/commercial` | `CommercialOpportunity`, `CommercialProposal`, `CommercialContext` (G4 models) | `g4_opportunities: 0`, `g4_proposals: 0`, `g4_contexts: 0` | **AMBER** |
| **Marketing** | `<MarketingChannels />` (from `marketing/`) routed at `objectId==='marketing'` | `app/marketing_os/routes.py` — `/api/v1/marketing`, `app/marketing_intelligence/routes.py` | `Campaign`, `AudienceDefinition` (marketing models) | `campaigns: 5`, `audience_definitions: 0` | **GREEN** |
| **Sales** | `<SalesPipeline />` + `<LeadManagement />` from `sales/` routed at `objectId==='sales'` | `app/sales_intelligence/routes.py` — `/api/v1/sales`, `app/crm/routes.py`, `app/leads/routes.py` | `Lead` (app.models), `Customer` | `leads: 6`, `opportunities: 0` | **AMBER** |
| **Operations** | `DomainOverview` only — no dedicated component (`operations/` dir absent) | No dedicated operations routes | No dedicated operations model | No specific operations tables | **RED** |
| **Knowledge** | `DomainOverview` only — `knowledge-browser-panel.tsx` EXISTS but is **NOT WIRED** in the panel router (JE gap) | `app/documents_knowledge/routes.py` — `/api/v1/knowledge` | `DocumentRecord`, `KnowledgeDocument`, `KnowledgeEntry` | `documents: 10`, `knowledge_documents: 0`, `knowledge_entries: 0` | **AMBER** |
| **Outputs** | `<OutputsBrowser />` from `outputs/` routed at `objectId==='outputs'` | Implicit via `app/execution/routes.py` — `/api/v1/outcomes` | `app/output/__init__.py` is an EMPTY STUB; `Outcome` from execution models | `outcomes: 3` | **AMBER** |
| **Memory** | `<MemoryBrowser />` from `memory/` routed at `objectId==='memory'` | `app/memory_api/routes.py` — `/api/v1/memory` | `MemoryRecord` (app.memory.models), UIR memory engine | `memory_records: 0` | **AMBER** |
| **Relationships** | `<RelationshipWorkspace />` from `relationship/` routed at `objectId==='relationships'` | Via commercial routes — `/api/v1/commercial` (uses CanonicalRelationship) | `CanonicalRelationship`, `RelationshipCategory`, `RelationshipTimeline` (FOR-2C models) | `rel_relationships: 0`, `relationships: 0`, `rel_categories: 0`, `rel_timeline: 0` | **AMBER** |
| **Content** | `<ContentStudio />` from `content/` routed at `objectId==='content'` | `app/content_studio/routes.py` — `/api/v1/content`, `app/creative_runtime/routes.py` — `/api/v1/creative` | Creative Runtime + content generation models | `m6_content_generations: 3`, `m6_media_assets: 1` | **GREEN** |
| **Entities** | `<EntityManager />` from `entities/` routed at `objectId==='entities'` | `app/api/entity_routes.py` | Entity definition models | `entities: 0`, `entity_definitions: 0` | **AMBER** |
| **Documents** | `<DocumentBrowser />` from `documents/` routed at `objectId==='documents'` | `app/document_runtime/routes.py`, `app/documents_knowledge/routes.py` | `DocumentRecord` (app.document.models) | `documents: 10`, `document_records: 0` | **GREEN** |

---

## Verdict Legend

| Verdict | Meaning |
|---------|---------|
| **GREEN** | Dedicated FE + BE routes + data model + real data in DB — fully operational |
| **AMBER** | Has FE and/or BE, but missing pieces (no data, empty stub, unwired component, no routes) |
| **RED** | No FE component, no BE routes, no data model — completely absent |
| **GREY** | Not assessed |

---

## Detailed Findings

### Panel Router Routing Map

The `executive-home.tsx` `DomainWorkspaceRouter` routes domains as follows:

| Domain | wsType / objectId | Router Match | Component Rendered |
|--------|------------------|-------------|-------------------|
| People | `type='people'` | Line 874 | `<OrganizationBrowser />` |
| Conversations | `type='conversation'` | Line 908 | `<ConversationWorkspace />` |
| Work | `type='commitment'` | Line 899 | `<CommitmentWorkspace />` |
| Finance | `objectId='finance'` → DOMAIN_IDS.has() | Line 986 | `<DomainOverview domain={domain} />` |
| Commercial | `objectId='commercial'` | Line 929 | `<CommercialWorkspace />` |
| Marketing | `objectId='marketing'` | Line 937 | `<MarketingChannels />` |
| Sales | `objectId='sales'` | Line 945 | `<SalesPipeline />` |
| Operations | `objectId='operations'` → DOMAIN_IDS.has() | Line 986 | `<DomainOverview domain={domain} />` |
| Knowledge | `objectId='knowledge'` → DOMAIN_IDS.has() | Line 986 | `<DomainOverview domain={domain} />` |
| Outputs | `objectId='outputs'` | Line 961 | `<OutputsBrowser />` |
| Memory | `objectId='memory'` | Line 969 | `<MemoryBrowser />` |
| Relationships | `objectId='relationships'` | Line 933 | `<RelationshipWorkspace />` |
| Content | `objectId='content'` | Line 973 | `<ContentStudio />` |
| Entities | `objectId='entities'` | Line 977 | `<EntityManager />` |
| Documents | `objectId='documents'` | Line 981 | `<DocumentBrowser />` |

### JE (Junior Engineer) Gaps Identified

1. **Knowledge**: `knowledge-browser-panel.tsx` and `ai-analysis.tsx` exist in `frontend/src/components/knowledge/` but are **never routed to** by `DomainWorkspaceRouter`. There is only a comment `// Knowledge — browsing` (line 985) with no actual routing logic. This is an incomplete/forgotten implementation.

2. **Knowledge backdoor**: `/api/v1/knowledge` routes exist in `app/documents_knowledge/routes.py` — there IS a working backend. The FE component just needs to be wired.

3. **Finance**: Models exist with rich SQLAlchemy definitions (Account, JournalEntry, LedgerEntry, etc.) and 20 invoice records exist in the DB (`fin_invoices`), but there is no frontend component, no backend routes, and no way to access this data through the UI.

4. **Operations**: Completely absent — no component, no routes, no model, no tables. It is a sidebar skeleton only.

5. **Outputs module**: `app/output/__init__.py` is an empty file (0 bytes). The frontend `<OutputsBrowser />` works via the execution/outcomes routes, but the dedicated output module has no implementation.

### Real Data Summary

Tables with **actual data** (row count > 0):
- `organizations: 1`
- `org_members: 2`
- `commitments: 5`
- `tasks: 14`
- `outcomes: 3`
- `campaigns: 5`
- `leads: 6`
- `fin_invoices: 20`
- `objects: 41`
- `documents: 10`
- `founder_conversations: 7`
- `founder_messages: 13`
- `m6_content_generations: 3`
- `m6_media_assets: 1`
- `sh_objects: 4`
- `sh_workspaces: 3`

Tables with **zero rows** (structure exists, no data):
- `g4_opportunities`, `g4_proposals`, `g4_contexts`
- `rel_relationships`, `rel_categories`, `rel_timeline`, `rel_ai_memory`
- `fin_accounts`, `fin_ledger`, `fin_journal_entries`
- `audience_definitions`
- `memory_records`
- `entities`, `entity_definitions`
- `knowledge_documents`, `knowledge_entries`, `knowledge_facts`
- `document_records`
- `executions`

---

## Recommendations

1. **Immediate**: Wire `knowledge-browser-panel.tsx` into `DomainWorkspaceRouter` for `objectId==='knowledge'` — the component and backend already exist.
2. **High Priority**: Build Finance frontend (or at minimum wire the existing fin_invoices data into DomainOverview) — there are 20 invoices stranded in the DB with no UI.
3. **High Priority**: Seed relationship database and/or fix the routing so `Relationships` domain displays actual data.
4. **Medium**: Create dedicated backend routes for Finance domain to expose the rich financial model.
5. **Medium**: Implement `app/output/__init__.py` or remove the stub.
6. **Low**: Define Operations domain scope — currently a pure shell with no implementation.