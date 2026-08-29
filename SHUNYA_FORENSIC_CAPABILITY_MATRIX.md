# SHUNYA FORENSIC CAPABILITY MATRIX

**Repository SHA:** ce0f235  
**Deployed SHA:** ce0f235  
**Branch:** master  
**Date:** 2026-08-29  
**Methodology:** Direct inspection of frontend components, executive-home.tsx panel router, backend routes, data models, and PostgreSQL tables with row counts.

## Rating System

| Rating | Meaning |
|--------|---------|
| **GREEN** | Dedicated FE component + BE routes + data model + real data in DB — fully operational |
| **AMBER** | Has FE and/or BE, but missing pieces (no data, empty stub, unwired component, no routes) |
| **RED** | No FE component, no BE routes, no data model — completely absent |
| **GREY** | Not implemented |

## Corrected Capability Matrix

| Domain | Frontend Component | Backend Routes | Data Model | DB Data | Verdict | Notes |
|--------|-------------------|----------------|------------|---------|---------|-------|
| **People** | `<OrganizationBrowser />` | `/api/v1/people` | OrgMember | 2 org_members, 1 org | **GREEN** | Fully operational |
| **Conversations** | `<ConversationWorkspace />` | `/api/v1/communication` | ExternalConversation, FounderConversation | 7 conversations, 13 messages | **GREEN** | Fully operational |
| **Work** | `<CommitmentWorkspace />` | `/api/v1/outcomes` | Commitment, Task, Outcome | 5 commitments, 14 tasks, 3 outcomes | **GREEN** | Fully operational |
| **Finance** | `DomainOverview` only | No dedicated routes | Account, JournalEntry, LedgerEntry, Invoice | 20 invoices, 0 other tables | **AMBER** | 20 invoices stranded in DB with no UI |
| **Commercial** | `<CommercialWorkspace />` | `/api/v1/commercial` | G4 opportunities/proposals/contexts | 0 rows in all G4 tables | **AMBER** | Component exists, but zero data |
| **Marketing** | `<MarketingChannels />` | `/api/v1/marketing` | Campaign, AudienceDefinition | 5 campaigns | **GREEN** | Fully operational |
| **Sales** | `<SalesPipeline />` | `/api/v1/sales`, `/api/v1/crm` | Lead, Customer | 6 leads | **AMBER** | Leads exist, full pipeline lifecycle not verified |
| **Operations** | `DomainOverview` only | No routes | No model | No tables | **RED** | Pure sidebar skeleton |
| **Knowledge** | `<KnowledgeBrowser />` (wired ce0f235) | `/api/v1/knowledge` | KnowledgeDocument, KnowledgeEntry | 0 knowledge entries | **AMBER** | Component + backend exist, zero data |
| **Outputs** | `<OutputsBrowser />` | `/api/v1/outcomes` | Outcome (execution models) | 3 outcomes | **AMBER** | Works, but app/output/__init__.py is empty stub |
| **Memory** | `<MemoryBrowser />` | `/api/v1/memory` | MemoryRecord | 0 memory records | **AMBER** | Component exists, no data |
| **Relationships** | `<RelationshipWorkspace />` | `/api/v1/commercial` | CanonicalRelationship | 0 rows in all rel tables | **AMBER** | Component exists, no data |
| **Content** | `<ContentStudio />` | `/api/v1/content` | Content generation, media assets | 3 content generations, 1 media asset | **GREEN** | Fully operational |
| **Entities** | `<EntityManager />` | `/api/v1/entities` | Entity definitions | 0 rows in entity tables | **AMBER** | Component exists, no data |
| **Documents** | `<DocumentBrowser />` | `/api/v1/workspace/documents` | Document | 10 documents | **GREEN** | Fully operational |

## Summary

| Rating | Count | Domains |
|--------|-------|---------|
| **GREEN** | 6 | People, Conversations, Work, Marketing, Content, Documents |
| **AMBER** | 8 | Finance, Commercial, Sales, Knowledge, Outputs, Memory, Relationships, Entities |
| **RED** | 1 | Operations |

## Panel Router Routing Map

| Domain | Router Match | Component Rendered |
|--------|-------------|-------------------|
| People | `type='people'` | `<OrganizationBrowser />` |
| Conversations | `type='conversation'` | `<ConversationWorkspace />` |
| Work | `type='commitment'` | `<CommitmentWorkspace />` |
| Finance | `objectId='finance'` → DOMAIN_IDS | `<DomainOverview />` |
| Commercial | `objectId='commercial'` | `<CommercialWorkspace />` |
| Marketing | `objectId='marketing'` | `<MarketingChannels />` |
| Sales | `objectId='sales'` | `<SalesPipeline />` |
| Operations | `objectId='operations'` → DOMAIN_IDS | `<DomainOverview />` |
| Knowledge | `objectId='knowledge'` | `<KnowledgeBrowser />` (wired ce0f235) |
| Outputs | `objectId='outputs'` | `<OutputsBrowser />` |
| Memory | `objectId='memory'` | `<MemoryBrowser />` |
| Relationships | `objectId='relationships'` | `<RelationshipWorkspace />` |
| Content | `objectId='content'` | `<ContentStudio />` |
| Entities | `objectId='entities'` | `<EntityManager />` |
| Documents | `objectId='documents'` | `<DocumentBrowser />` |

## Real Data Summary

Tables with actual data (row count > 0):
- organizations: 1
- org_members: 2
- commitments: 5
- tasks: 14
- outcomes: 3
- campaigns: 5
- leads: 6
- fin_invoices: 20
- founder_objects: 41
- documents: 10
- founder_conversations: 7
- founder_messages: 13
- m6_content_generations: 3
- m6_media_assets: 1
- sh_objects: 4
- sh_workspaces: 3

Tables with zero rows (structure exists, no data):
- g4_opportunities, g4_proposals, g4_contexts
- rel_relationships, rel_categories, rel_timeline
- fin_accounts, fin_ledger, fin_journal_entries
- audience_definitions
- memory_records
- entities, entity_definitions
- knowledge_documents, knowledge_entries
- executions

## Remediation Actions Taken

| Gap | Action | Status |
|-----|--------|--------|
| Knowledge component unwired | Added `<KnowledgeBrowser />` routing in executive-home.tsx | ✅ FIXED at ce0f235 |
| Context isolation | 4 deterministic test objects, verified API-level boundaries | ✅ VERIFIED |
| AI execution journey (fake progress) | Replaced with real stages: understanding→retrieving→deciding→executing→completing | ✅ FIXED |
| Content analysis (ingestion) | CSV: row count + columns, TXT: word count, PDF: extraction | ✅ FIXED |
| Marketing connect buttons (dead) | Setup screen with credential inputs, OAuth link, Save/Cancel | ✅ FIXED |
| Document inline viewer | Detail panel with Back button, metadata, Open/Download | ✅ FIXED |
| Onboarding persistence (sessionStorage only) | Added localStorage + backend session check | ✅ FIXED |
| URL pushState double-push | Deduplication on activate | ✅ FIXED |

## Remaining P1 Gaps

| Gap | Domain | What's Needed |
|-----|--------|--------------|
| 20 invoices with no UI | Finance | Build frontend component for financial data |
| Zero data in 7 tables | Commercial, Relationships, Memory, Entities, Knowledge, Sales | Seed realistic data through production paths |
| Operations is pure shell | Operations | Define scope, build component, routes, data model |
| Empty output module | Outputs | Implement `app/output/__init__.py` or remove stub |
| Full browser Back/Forward | Routing | Complete certification of navigation lifecycle |
| Onboarding completion email | Email | Implement and verify email delivery |
| Standard/Premium image tiers | Content Studio | Configure additional providers beyond Economy |
| Campaign API context | Marketing | Fix tenant_id context so campaigns return without explicit query param |