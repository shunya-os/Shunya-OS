# Phase A1 — Universal SHUNYA Space Implementation Plan

**Goal:** Build the Universal SHUNYA Space — the primary interaction model for SHUNYA OS where every object renders through the same dynamic Space interface.

**Core Philosophy:** A Space is defined by its identity, not its type. Every object (Customer, Supplier, Employee, Project, Company, etc.) is simply a Space. The architecture never hardcodes type names.

**Architecture:** Space domain model → Space engine → API routes → SPA frontend. Reuses all existing kernel runtimes (Business Graph, Planning, Organization, Execution, Orchestration, Temporal, Intelligence). No duplicate data models.

---

## Implementation Phases

### Phase 1: Space Domain Model
**Files:** `app/space/models.py`

- `SpaceType` — registry of type strings, extensible, no hardcoded business names
- `SpaceConfig` — per-type configuration (panels, commands, context fields)
- `SpaceState` — per-instance state (last position, collapsed sections, recent conversations, open documents, current execution, AI reasoning context, pending work)
- `SpaceCommand` — universal command model (Summarize, Explain, Create Plan, Delegate, Email, Compare, Forecast, Generate, Review, Approve, Schedule, Analyze, Find Risks, Show Dependencies, Predict Outcome)
- `SpaceContext` — current Space context (identity, goal, plans, communications, responsibilities, risks, opportunities, knowledge)
- `SpaceRelationship` — typed relationship to another Space
- `SpaceTimelineEvent` — unified event for the Space timeline
- `SpaceKnowledgeItem` — linked knowledge (documents, emails, messages, notes, policies, images, files, research, transcripts, AI summaries)
- `SpaceCommandRegistry` — maps commands to handler functions
- `SpaceStore` — in-memory store for Space states and configurations

### Phase 2: Space Engine
**Files:** `app/space/engine.py`

- `SpaceIdentityEngine` — resolves Space identity from any entity type
- `SpaceContextEngine` — builds context for a Space (identity, relationships, health, metrics)
- `SpaceRelationshipEngine` — visualizes relationships as a graph
- `SpaceTimelineEngine` — unified timeline from temporal intelligence
- `SpaceKnowledgeEngine` — links knowledge items to Spaces
- `SpaceCommandEngine` — processes Space-centric commands
- `SpaceNavigationEngine` — search → select → open flow
- `SpacePersistenceEngine` — context persistence (last position, collapsed sections, etc.)
- `SpaceRenderer` — facade that composes all engines into a Space view
- `SpaceRuntimeService` — coordinates all sub-engines
- `SpaceRuntime` — facade + singleton management

### Phase 3: API Routes
**Files:** `app/space_routes.py`

- `GET /api/space/<space_id>` — full Space view
- `GET /api/space/<space_id>/timeline` — timeline events
- `GET /api/space/<space_id>/relationships` — relationship graph
- `GET /api/space/<space_id>/knowledge` — knowledge items
- `GET /api/space/<space_id>/commands` — available commands
- `POST /api/space/<space_id>/command` — execute a command
- `GET /api/space/search?q=<query>` — search spaces
- `GET /api/space/recent` — recent spaces
- `GET /api/space/types` — available space types
- `POST /api/space/<space_id>/state` — save Space state (persistence)
- `POST /api/space/<space_id>/conversation` — send message to Space conversation

### Phase 4: SPA Frontend
**Files:** `templates/space.html`

Single-file SPA that:
- Renders any Space dynamically (Identity → Context → Relationships → Panels → Actions)
- Three-zone layout: Navigation (left) → Space (center) → Intelligence (right)
- Identity strip with breadcrumb navigation
- Space header with type, name, health, meta
- Tabbed panels: Content, Timeline, Knowledge, Relationships, Conversation, Commands
- Timeline panel with unified events
- Knowledge panel with linked documents
- Relationship panel with graph visualization
- Command palette (Ctrl+K) with Space-centric commands
- Search overlay (built-in)
- Context persistence (remembers last position, collapsed sections)
- Responsive: three breakpoints (1200px+, 768-1200px, <768px)

### Phase 5: CSS
**Files:** `static/css/space.css`

Space-specific styling following the existing design system:
- Space header (type, name, health, meta)
- Timeline panel (events with dots, sources)
- Knowledge panel (knowledge items with sources)
- Relationship panel (graph visualization nodes)
- Command palette
- Search overlay
- Responsive breakpoints
- Empty states
- Conversations within Space

### Phase 6: App Factory Integration
**File:** `app/__init__.py` (edit)

- Register `space_bp` blueprint
- Load demo Space data
- Register space middleware

### Phase 7: Tests
**Files:** `tests/space/test_space.py`

- `TestSpaceModel` — SpaceType registration, SpaceConfig, SpaceState, SpaceCommand
- `TestSpaceIdentityEngine` — identity resolution, type inference
- `TestSpaceContextEngine` — context building for various types
- `TestSpaceRelationshipEngine` — relationship visualization
- `TestSpaceTimelineEngine` — timeline integration
- `TestSpaceKnowledgeEngine` — knowledge linking
- `TestSpaceCommandEngine` — command execution
- `TestSpaceNavigationEngine` — search, recent spaces
- `TestSpacePersistenceEngine` — state save/restore
- `TestSpaceRenderer` — full Space view composition
- `TestSpaceRuntime` — integration test
- `TestSpaceRoutes` — API endpoint tests
- `TestSpaceEdgeCases` — unknown types, missing data, boundary conditions

---

## Files to Create

| File | LOC (est) | Purpose |
|------|-----------|---------|
| `app/space/__init__.py` | 30 | Public API, facade, singleton |
| `app/space/models.py` | 450 | Domain model: SpaceType, SpaceConfig, SpaceState, SpaceCommand, SpaceContext, etc. |
| `app/space/engine.py` | 900 | Sub-engines: Identity, Context, Relationship, Timeline, Knowledge, Command, Navigation, Persistence |
| `app/space/runtime.py` | 200 | Middleware, demo data loading, singleton management |
| `app/space_routes.py` | 300 | JSON API: 11 endpoints |
| `templates/space.html` | 500 | SPA: dynamic Space renderer |
| `static/css/space.css` | 600 | Space-specific styling |
| `tests/space/__init__.py` | 1 | Package marker |
| `tests/space/test_space.py` | 800 | 50+ tests across 13 test classes |

## Verification

1. `pytest tests/space/ -q --tb=short` — all Space tests pass
2. `pytest tests/ -q --tb=no` — full regression, zero regressions
3. Flask app starts without errors
4. Space API endpoints return valid JSON
5. SPA renders any Space type dynamically