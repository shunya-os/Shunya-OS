# SHUNYA — Domain Truth Matrix

> Generated: 2026-08-27 | Directive: M2B (Extended)
> Version: 1.0 — Live Production Audit

## Classification Legend

| Status | Meaning |
|--------|---------|
| **REAL** | Connected to a real backend/data path. Full workflow exists. |
| **PARTIAL** | Real UI exists but some required workflow is incomplete. |
| **PLACEHOLDER** | Informational or conceptual surface only. No substantive implementation. |
| **NOT IMPLEMENTED** | Does not exist or explicitly declared unimplemented. |

## Domain Matrix

| Domain | Route | Classification | Frontend | Backend API | Data Source | Last Verified |
|--------|-------|---------------|----------|-------------|-------------|---------------|
| **People** | `/workspace/people` | **REAL** | OrganizationBrowser (lazy) | GET /api/v1/objects/types + permissions | PostgreSQL (objects, org_members) | 2026-08-27 |
| **Work** | `/workspace/work` | **REAL** | ExecutionWorkspace + TasksWorkspace | GET /api/v1/intention, SSE (living-store) | PostgreSQL + SSE events | 2026-08-27 |
| **Finance** | `/workspace/finance` | **PLACEHOLDER** | DomainOverview (generic) | GET /api/v1/objects (filtered) | PostgreSQL (objects) | 2026-08-27 |
| **Commercial** | `/workspace/commercial` | **REAL** | CommercialWorkspace (lazy) | GET /api/v1/objects (opportunities/deals) | PostgreSQL | 2026-08-27 |
| **Marketing** | `/workspace/marketing` | **REAL** | MarketingDashboard (lazy) | POST /api/v1/ai/chat, campaign routes | PostgreSQL + AI | 2026-08-27 |
| **Sales** | `/workspace/sales` | **REAL** | SalesPipeline (lazy) + LeadManagement | GET /api/v1/objects (proposals/customers) | PostgreSQL | 2026-08-27 |
| **Operations** | `/workspace/operations` | **NOT IMPLEMENTED** | DomainOverview (generic) | — | — | 2026-08-27 |
| **Knowledge** | `/workspace/knowledge` | **PLACEHOLDER** | DomainOverview (generic) | SqlKnowledgeRepository (full CRUD) | PostgreSQL | 2026-08-27 |
| **Outputs** | `/workspace/outputs` | **REAL** | OutputsBrowser (lazy) | GET /api/v1/objects (filtered) | PostgreSQL | 2026-08-27 |
| **Memory** | `/workspace/memory` | **REAL** | MemoryBrowser (lazy) | SSE + living-store | In-memory + PostgreSQL | 2026-08-27 |
| **Relationships** | `/workspace/relationships` | **REAL** | RelationshipWorkspace (lazy) | GET /api/v1/objects (relations) | PostgreSQL | 2026-08-27 |
| **Content** | `/workspace/content` | **REAL** | ContentStudio (1646 lines, lazy) | POST /api/v1/content/generate, GET/DELETE /api/v1/content/history | PostgreSQL + AI | 2026-08-27 |
| **Entities** | `/workspace/entities` | **REAL** | EntityManager (lazy) | GET /api/v1/objects/types | PostgreSQL | 2026-08-27 |
| **Conversations** | `/workspace/conversations` | **REAL** | ConversationWorkspace (lazy) | GET /api/v1/objects (conversations) | PostgreSQL | 2026-08-27 |

## Summary

| Classification | Count | Domains |
|---------------|-------|---------|
| **REAL** | 10 | People, Work, Commercial, Marketing, Sales, Outputs, Memory, Relationships, Content, Entities, Conversations |
| **PLACEHOLDER** | 2 | Finance, Knowledge |
| **NOT IMPLEMENTED** | 1 | Operations |

## Required Actions

### Finance (PLACEHOLDER → REAL)
Backend has Objects API with finance type filtering. Needs a dedicated Finance workspace component (not DomainOverview). Budget: 2-3 days for full implementation.

### Knowledge (PLACEHOLDER → REAL)
Backend has SqlKnowledgeRepository with full CRUD. Needs a dedicated Knowledge workspace component. Budget: 1-2 days.

### Operations (NOT IMPLEMENTED → PLAN)
Explicitly not implemented. Needs product decision: build or deprecate from sidebar. Budget: TBD.

## Cross-Cutting Concerns

| Concern | Status | Notes |
|---------|--------|-------|
| Context isolation (org vs personal) | ✅ PASS | Browser-verified bidirectional switching |
| Data refresh on context switch | ✅ PASS | All domains re-fetch on context change |
| URL stability | ✅ PASS | SPA handles routing without page reloads |
| Refresh safety | ✅ PASS | Session persists, context restored |
| Back/Forward navigation | ✅ PASS | Browser history stack maintained |