# Repository Canon

> **Canonical Document · Phase C1A**
> **Status: CANONICAL — Derived from Universal Ontology + Business Canon + Runtime Canon**
> **Version: 2.0**

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Derivation from Architecture](#2-derivation-from-architecture)
3. [Repository Philosophy](#3-repository-philosophy)
4. [Desired Repository Structure](#4-desired-repository-structure)
5. [Derivation Mapping](#5-derivation-mapping)
6. [Current State Analysis](#6-current-state-analysis)
7. [Duplicate Architectures](#7-duplicate-architectures)
8. [Legacy Code](#8-legacy-code)
9. [Competing Patterns](#9-competing-patterns)
10. [Consolidation Plan](#10-consolidation-plan)
11. [Module Boundaries](#11-module-boundaries)
12. [Domain Separation](#12-domain-separation)
13. [Future Extensibility](#13-future-extensibility)
14. [Relationship to Other Canonical Documents](#14-relationship-to-other-canonical-documents)

---

## 1. Purpose

This document defines the desired repository structure for SHUNYA. Unlike the other canonical documents, this structure is not independently proposed — it is **derived** directly from the Universal Ontology (00), the Business Canon (03), and the Runtime Canon (05). The repository structure is a consequence of architecture, not an independent design choice.

---

## 2. Derivation from Architecture

### 2.1 Derivation Chain

```
Universal Ontology (00)  ────── defines the primitive kinds of things
        │
        ▼
Business Canon (03)     ────── defines universal business objects
        │
        ▼
Runtime Canon (05)      ────── defines how objects live and engines operate
        │
        ▼
Repository Canon (09)   ────── DERIVED: organizes code by ontological kind + engine function
```

### 2.2 Mapping: Ontology → Repository

| Ontological Concept (00) | Maps To | Repository Directory |
|--------------------------|---------|---------------------|
| Entity | Core primitive | `core/kernel/` |
| Identity | Core primitive | `core/identity/` |
| Relationship | Core primitive | `core/relationship/` |
| State | Core primitive | `core/kernel/` |
| Event | Core primitive | `core/event/` |
| Observation | Stored as evidence | `core/evidence/` |
| Evidence | Core primitive | `core/evidence/` |
| Decision | Intelligence engine input | `intelligence/decisions/` |
| Action | Execution | `intelligence/executive/` |
| Outcome | Evaluation | `intelligence/evaluator/` |
| Knowledge | Intelligence engine | `intelligence/knowledge/` |
| Memory | Intelligence engine | `intelligence/memory/` |
| Context | Intelligence engine | `intelligence/context/` |
| Workspace | Experience container | `experience/navigation/` |

### 2.3 Mapping: Cognitive Engines (07) → Repository

| Cognitive Engine | Repository Directory |
|-----------------|---------------------|
| Observer | `intelligence/observer/` |
| Memory | `intelligence/memory/` |
| Knowledge | `intelligence/knowledge/` |
| Reasoner | `intelligence/reasoner/` |
| Planner | `intelligence/planner/` |
| Executive | `intelligence/executive/` |
| Evaluator | `intelligence/evaluator/` |
| Learner | `intelligence/learner/` |
| Governance | `intelligence/governance/` |

### 2.4 Mapping: Business Objects (03) → Repository

| Business Object | Ontological Parent | Location |
|----------------|-------------------|----------|
| Identity | Identity (ontology) | `core/identity/` |
| Human | Entity | `core/kernel/` (base) + domain extensions |
| Organization | Entity | `core/organization/` |
| Workspace | Workspace (ontology) | `experience/navigation/` |
| Relationship | Relationship (ontology) | `core/relationship/` |
| Conversation | Container Entity | `experience/api/` |
| Commitment | Derived from Decision | `intelligence/decisions/` |
| Task | Derived from Action | `intelligence/executive/` |
| Event | Event (ontology) | `core/event/` |
| Observation | Observation (ontology) | `core/evidence/` |
| Evidence | Evidence (ontology) | `core/evidence/` |
| Document | Entity | `core/kernel/` (base) + domain extensions |
| FinancialObject | Entity | `core/kernel/` (base) + domain extensions |
| Decision | Decision (ontology) | `intelligence/decisions/` |
| Workflow | Composite | `intelligence/executive/` |
| Memory | Memory (ontology) | `intelligence/memory/` |
| Knowledge | Knowledge (ontology) | `intelligence/knowledge/` |
| Outcome | Outcome (ontology) | `intelligence/evaluator/` |

---

## 3. Repository Philosophy

### 3.1 Principles (Derived)

| Principle | Derivation | Description |
|-----------|-----------|-------------|
| **Core first** | Ontology §2.1 | `core/` contains the ontological primitives — things that exist |
| **Engine separation** | AI Canon (07) §3 | `intelligence/` contains the cognitive engines — things that process |
| **Experience surface** | Experience Canon (08) §4 | `experience/` contains the human interface — things that present |
| **Domain isolation** | Business Canon (03) §10 | `domains/` contains domain-specific extensions — things that vary |
| **Flat over nested** | Runtime Canon (05) §2 | Maximum 3 directory levels deep |
| **Explicit boundaries** | Runtime Canon (05) §9 | Module boundaries are enforced (not convention-based) |
| **Single responsibility** | 00 §2.5 Parsimony | Each module maps to exactly one ontological concept or engine |
| **Protocol, not inheritance** | 04 §1.1 | Modules communicate through protocols, not base classes |

### 3.2 Monorepo

SHUNYA uses a **monorepo** because:
- The core ontology, engines, experience, and domains evolve together
- Protocol contracts across ontological layers must be verifiable in a single change
- Atomic changes across concept boundaries are common
- Single source of truth for architecture

---

## 4. Desired Repository Structure

### 4.1 Top-Level Layout

```
shunya_os/
│
├── core/                          # ONTOLOGICAL PRIMITIVES (00_universal_ontology.md)
│   ├── kernel/                    # Entity, Object, State — the universal type system
│   ├── identity/                  # Identity resolution, management
│   ├── organization/              # Organization entity
│   ├── relationship/              # Relationship primitive: directed, typed connections
│   ├── event/                     # Event primitive: immutable happenings
│   ├── evidence/                  # Evidence primitive: support/contradict observations
│   ├── audit/                     # Immutable audit trail (cross-cutting)
│   ├── search/                    # Search index interface (cross-cutting)
│   └── storage/                   # Storage abstraction (cross-cutting)
│
├── intelligence/                  # COGNITIVE ENGINES (07_ai_canon.md)
│   ├── observer/                  # Observer Engine — captures Events as Observations
│   ├── memory/                    # Memory Engine — retains experiential records
│   ├── knowledge/                 # Knowledge Engine — verifies and structures facts
│   ├── reasoner/                  # Reasoner Engine — derives conclusions from evidence
│   ├── planner/                   # Planner Engine — generates action sequences
│   ├── decisions/                 # Decision Runtime — manages Decision lifecycle
│   ├── executive/                 # Executive Engine — dispatches and monitors Actions
│   ├── evaluator/                 # Evaluator Engine — measures Outcomes against intent
│   ├── learner/                   # Learner Engine — extracts patterns from Outcomes
│   ├── governance/                # Governance Engine — checks policies and permissions
│   ├── context/                   # Context Fusion Engine — assembles relevant context
│   ├── temporal/                  # Temporal Intelligence — trajectories, trends, forecasts
│   └── prediction/                # Prediction Engine — forecasts future states
│
├── experience/                    # EXPERIENCE LAYER (08_experience_canon.md)
│   ├── ui/                        # UI component library
│   │   ├── atoms/                 # Atomic components (Button, Input, Label, Icon)
│   │   ├── molecules/             # Molecular components (FormField, Card, Modal, Toast)
│   │   ├── organisms/             # Organism components (DataTable, Timeline, Kanban)
│   │   ├── templates/             # Page templates (Space layout, Dashboard, DetailView)
│   │   └── theme/                 # Theme system (colors, typography, spacing)
│   ├── navigation/                # Object-first navigation, workspace/space routing
│   ├── workspace/                 # Workspace model — space creation, membership, context
│   ├── objects/                   # Object renderers — how each Business Object is displayed
│   ├── collaboration/             # AI collaboration patterns, conversation UI
│   ├── api/                       # REST/GraphQL API — maps objects to endpoints
│   └── adapters/                  # Channel adapters (Telegram, Email, WebSocket, etc.)
│
├── domains/                       # DOMAIN SURFACES (03_business_canon.md extensions)
│   ├── travel/                    # Travel domain surface
│   │   ├── models/                # Domain-specific object extensions (Booking, Itinerary, etc.)
│   │   ├── workflows/             # Domain-specific workflows
│   │   ├── adapters/              # Domain-specific external integrations (GDS, etc.)
│   │   └── ui/                    # Domain-specific UI components
│   │
│   └── _template/                 # Template for creating new domain surfaces
│
├── infrastructure/                # DEPLOYMENT AND OPERATIONS
│   ├── config/                    # Configuration files
│   ├── deployment/                # Docker, k8s, terraform, etc.
│   ├── ci/                        # CI/CD pipeline definitions
│   └── monitoring/                # Observability: logging, metrics, tracing
│
├── tests/                         # TEST SUITES (mirrors source structure)
│   ├── core/                      # Tests for ontological primitives
│   ├── intelligence/              # Tests for cognitive engines
│   ├── experience/                # Tests for experience layer
│   ├── domains/                   # Tests for domain surfaces
│   └── integration/               # Cross-module integration tests
│
├── governance/                    # ARCHITECTURE GOVERNANCE
│   ├── constitution/              # Constitutional documents
│   ├── adr/                       # Architecture Decision Records
│   └── specs/                     # Engine specifications
│
├── docs/                          # DOCUMENTATION
│   ├── canon/                     # Canonical architecture (Phase C1)
│   ├── api/                       # API documentation
│   └── guides/                    # Developer guides
│
├── scripts/                       # Build and maintenance scripts
├── .github/                       # GitHub configuration
├── migrations/                    # Database migrations (alembic)
├── requirements/                  # Python package dependencies
│   ├── core.txt                   # Core has zero external dependencies
│   ├── intelligence.txt           # Intelligence adds inference library deps
│   ├── experience.txt             # Experience adds web framework deps
│   └── domains/                   # Per-domain dependency files
└── pyproject.toml                 # Project configuration
```

---

## 5. Derivation Mapping

### 5.1 How Every Directory Maps to Architecture

| Directory | Derived From | Architectural Basis |
|-----------|-------------|-------------------|
| `core/kernel/` | 00 §3, §5, §7 | Entity, Object, State — the fundamental kinds |
| `core/identity/` | 00 §4 | Identity — the "thisness" of Entities |
| `core/organization/` | 03 §3.3 | Organization — Entity subclass |
| `core/relationship/` | 00 §6, 03 §3.5 | Relationship — directed typed connections |
| `core/event/` | 00 §8 | Event — immutable happenings |
| `core/evidence/` | 00 §9, §10 | Observation and Evidence — support chains |
| `core/audit/` | 04 §16 | Audit — immutability requirement |
| `core/search/` | 04 §15 | Search — findability requirement |
| `core/storage/` | 05 (all) | Storage — persistence abstraction |
| `intelligence/observer/` | 07 §5 | Observer Engine — captures reality |
| `intelligence/memory/` | 00 §15, 07 §6 | Memory Engine — experiential records |
| `intelligence/knowledge/` | 00 §14, 07 §7 | Knowledge Engine — verified facts |
| `intelligence/reasoner/` | 07 §8 | Reasoner Engine — conclusion derivation |
| `intelligence/planner/` | 07 §9 | Planner Engine — action sequences |
| `intelligence/decisions/` | 00 §11, 03 §3.14 | Decision Runtime — Decision lifecycle |
| `intelligence/executive/` | 00 §12, 07 §10 | Executive Engine — Action dispatch |
| `intelligence/evaluator/` | 00 §13, 07 §11 | Evaluator Engine — Outcome measurement |
| `intelligence/learner/` | 07 §12 | Learner Engine — pattern extraction |
| `intelligence/governance/` | 07 §13 | Governance Engine — policy enforcement |
| `intelligence/context/` | 00 §16 | Context Fusion — situational awareness |
| `experience/navigation/` | 00 §17, 08 §4 | Workspace — bounded context |
| `experience/objects/` | 08 §4 (object-first) | Object renderers — object navigation |
| `experience/workspace/` | 08 §5 | Workspace model — workspace interaction |
| `experience/collaboration/` | 08 §6 | AI collaboration — human-AI interaction |
| `experience/api/` | 05 §2 | API layer — experience entry points |
| `experience/adapters/` | 05 §10.2 | Channel adapters — external connections |
| `domains/` | 03 (extensions) | Domain surfaces — business-specific code |

### 5.2 No Independent Design

Every directory in the target structure exists because the architecture requires it, not because it is a convenient organizational choice. If the architecture does not define a concept, there is no directory for it.

---

## 6. Current State Analysis

### 6.1 Current Directory Layout

```
shunya_os/                          # Root project
├── app/                            # Monolithic Flask app (core + CRM bundled)
│   ├── models.py                   # All core CRM models
│   ├── __init__.py                 # Flask app factory with everything
│   ├── cognitive/                  # Intelligence experiments
│   ├── collaboration/              # Collaboration models
│   ├── communication/              # Communication adapters
│   ├── cortex/                     # Organizational cortex → intelligence/context/
│   ├── decision/                   # Decision models (pre-runtime)
│   ├── decision_runtime/           # Decision runtime → intelligence/decisions/
│   ├── document/                   # Document handling → core/kernel/
│   ├── evidence/                   # Evidence models → core/evidence/
│   ├── execution/                  # Execution models → intelligence/executive/
│   ├── execution_intelligence/     # Execution intelligence → intelligence/executive/
│   ├── executive/                  # Executive models → intelligence/executive/
│   ├── founder/                    # Founder workspace → experience/workspace/
│   ├── graph/                      # Graph models → core/relationship/
│   ├── graph_universal/            # Universal graph → core/relationship/
│   ├── human_context/              # Human context → intelligence/context/
│   ├── intelligence/               # Explainable intelligence → intelligence/observer/ + reasoner/
│   ├── kernel/                     # Universal object kernel → core/kernel/
│   ├── knowledge/                  # Knowledge store → intelligence/knowledge/
│   ├── learning/                   # Learning store → intelligence/learner/
│   ├── learning_intelligence/      # Learning intelligence → intelligence/learner/
│   ├── llm/                        # LLM integration → intelligence/ (inference provider)
│   ├── memory/                     # Memory models → intelligence/memory/
│   ├── orchestration/              # Orchestration layer → intelligence/executive/
│   ├── orchestrator/               # Orchestrator models → intelligence/executive/
│   ├── organizational/             # Organizational models → core/organization/
│   ├── planning/                   # Planning engine → intelligence/planner/
│   ├── prediction/                 # Prediction models → intelligence/prediction/
│   ├── privacy/                    # Privacy models → core/audit/ + intelligence/governance/
│   ├── production/                 # Production identity/auth → core/identity/
│   ├── relationship/               # Relationship models → core/relationship/
│   ├── relevance/                  # Relevance engine → intelligence/context/
│   ├── routes/                     # Route definitions → experience/api/
│   ├── runtime/                    # Runtime (minimal) → intelligence/executive/
│   ├── shunya/                     # Legacy engine implementations (archive)
│   ├── space/                      # Space architecture → experience/navigation/
│   ├── temporal/                   # Temporal intelligence → intelligence/temporal/
│   ├── watch/                      # Watch engine → intelligence/observer/
│   └── world/                      # World models → core/kernel/
│
├── shunya_os_crm/                  # Separate CRM app (travel-specific → domains/travel/)
├── shunya_os_dashboard/            # Separate dashboard app (→ experience/ui/)
├── shunya_os_documents/            # Separate documents app (→ domains/travel/ + experience/)
├── shunya_os_gmail/                # Separate Gmail integration (→ experience/adapters/)
├── shunya_os_workflow/             # Separate workflow app (→ intelligence/executive/)
│
├── architecture/                   # Architecture documentation (→ docs/canon/)
├── docs/                           # Documentation
├── tests/                          # Test suites
├── governance/                     # Governance files
├── templates/                      # Jinja2 templates (→ experience/ui/)
├── static/                         # Static assets (→ experience/ui/)
└── ...                             # Config files
```

### 6.2 Key Issues

| Issue | Severity | Ontological Basis |
|-------|----------|-------------------|
| **Monolithic app/** | CRITICAL | Violates core/domain separation (00 §2.1) |
| **Separate sub-apps** | CRITICAL | Duplicates every layer — each should be a single module |
| **Mixed concerns** | HIGH | Ontological primitives mixed with domain concepts |
| **Deep nesting** | MEDIUM | app/shunya/ has 4+ levels — violates parsimony (00 §2.5) |
| **Duplicate patterns** | HIGH | Multiple implementations of same ontological concept |
| **No core/domain separation** | CRITICAL | Core runtime and domain extensions intermingled |
| **Inconsistent naming** | MEDIUM | cognitive vs intelligence, executive vs cortex — violates §2.1 "one concept, one definition" |

---

## 7. Duplicate Architectures

### 7.1 Identified Duplicates

Duplicate architectures arise from competing implementations of the same ontological concept:

| Ontological Concept | Implementation A | Implementation B | Target |
|--------------------|-----------------|-----------------|--------|
| Object/Entity | `app/kernel/object.py` | `app/models.py` (implicit) | `core/kernel/` |
| Decision | `app/decision_runtime/` | `app/decision/` (models only) | `intelligence/decisions/` |
| Event/Timeline | `app/temporal/` | `app/models.py` (ActivityLog) | `core/event/` |
| Memory | `app/memory/` | `app/models.py` (partial) | `intelligence/memory/` |
| Relationship | `app/kernel/relationship.py` | `app/relationship/` | `core/relationship/` |
| Knowledge | `app/knowledge/` | `app/gkf/` | `intelligence/knowledge/` |
| Execution | `app/execution/` | `app/execution_intelligence/` | `intelligence/executive/` |
| Orchestration | `app/orchestration/` | `app/orchestrator/` | `intelligence/executive/` |

### 7.2 App Duplicates

The following are separate Flask applications that duplicate every architectural layer:

| App | Core Duplicate | Engine Duplicate | Experience Duplicate | Action |
|-----|---------------|-----------------|---------------------|--------|
| `shunya_os_crm/` | Models, identity | Workflows | Routes, templates, static | Merge into `domains/travel/` |
| `shunya_os_dashboard/` | — | — | Routes, templates, static | Merge into `experience/ui/` |
| `shunya_os_documents/` | Document models | Document processing | Routes, templates | Merge into `domains/travel/` + `experience/` |
| `shunya_os_gmail/` | Message models | — | Adapter code | Merge into `experience/adapters/` |
| `shunya_os_workflow/` | Workflow models | Workflow engine | Routes | Merge into `intelligence/executive/` |

---

## 8. Legacy Code

### 8.1 Identified Legacy Code

| Code | Location | Superseded By | Action |
|------|----------|--------------|--------|
| Old engine specs | `app/shunya/` (context, governance, identity, knowledge, etc.) | `intelligence/*` engines | Archive |
| Pre-runtime decision models | `app/decision/models.py` | `intelligence/decisions/` | Remove |
| Standalone CRM template | `templates/` | `domains/travel/ui/` | Move |
| Pre-space navigation | `app/routes/` (some) | `experience/navigation/` | Consolidate |
| Old LLM wrappers | `app/llm/` | `intelligence/` (LLM as inference provider) | Reintegrate |
| Duplicate graph code | `app/graph/` + `app/graph_universal/` | `core/relationship/` | Consolidate |

---

## 9. Competing Patterns

### 9.1 Identified Competing Patterns

Competing patterns represent different implementation strategies for the same architectural concept:

| Pattern | Where Used A | Where Used B | Resolution |
|---------|-------------|-------------|------------|
| **Model definition** | SQLAlchemy `db.Model` in `app/models.py` | Dataclass in `app/kernel/` + `app/decision_runtime/` | UniversalObject protocol wraps both; new code uses protocol |
| **State management** | SQLAlchemy rows | In-memory stores (list/dict) | Repository pattern — abstract storage from logic |
| **Provenance** | `app/intelligence/provenance.py` | `app/kernel/object.py` (EvidenceRef) | Consolidate into `core/evidence/` |
| **Confidence** | `app/intelligence/confidence.py` | `app/kernel/object.py` (confidence field) | Unify as `core/evidence/confidence.py` |
| **Identity** | `app/kernel/identity.py` | `app/production/identity/` | Consolidate into `core/identity/` |

---

## 10. Consolidation Plan

### 10.1 Phase 1: Core — Ontological Primitives

Move all universal ontological primitives into `core/`:

| Current | Target | Ontological Basis |
|---------|--------|-------------------|
| `app/kernel/` | `core/kernel/` | Entity, Object, State (00 §3, §5, §7) |
| `app/kernel/identity.py` + `app/production/identity/` | `core/identity/` | Identity (00 §4) |
| `app/relationship/` + `app/graph/` + `app/graph_universal/` | `core/relationship/` | Relationship (00 §6) |
| `app/evidence/` + `app/intelligence/provenance.py` | `core/evidence/` | Observation + Evidence (00 §9, §10) |
| `app/temporal/` | `core/event/` | Event (00 §8) |
| New | `core/audit/` | Audit (04 §16) |
| New | `core/search/` | Search (04 §15) |
| New | `core/storage/` | Storage abstraction (05) |
| `app/organizational/` | `core/organization/` | Organization (03 §3.3) |

### 10.2 Phase 2: Intelligence — Cognitive Engines

Move all cognitive engine code into `intelligence/`, organized by engine type:

| Current | Target | Engine (07) |
|---------|--------|-------------|
| `app/intelligence/` (observation) | `intelligence/observer/` | Observer |
| `app/memory/` | `intelligence/memory/` | Memory |
| `app/knowledge/` + `app/gkf/` | `intelligence/knowledge/` | Knowledge |
| `app/intelligence/reasoning.py` | `intelligence/reasoner/` | Reasoner |
| `app/planning/` | `intelligence/planner/` | Planner |
| `app/decision_runtime/` | `intelligence/decisions/` | Decision |
| `app/execution/` + `app/execution_intelligence/` + `app/orchestration/` + `app/orchestrator/` | `intelligence/executive/` | Executive |
| `app/executive/` (evaluation) | `intelligence/evaluator/` | Evaluator |
| `app/learning/` + `app/learning_intelligence/` | `intelligence/learner/` | Learner |
| `app/shunya/governance_engine/` | `intelligence/governance/` | Governance |
| `app/cortex/` + `app/human_context/` + `app/context/` | `intelligence/context/` | Context |
| `app/temporal/` (trends/forecasts) | `intelligence/temporal/` | Temporal |
| `app/prediction/` | `intelligence/prediction/` | Prediction |

### 10.3 Phase 3: Experience — Human Interface

Move all experience-layer code into `experience/`:

| Current | Target | Experience Principle (08) |
|---------|--------|--------------------------|
| `templates/` + `static/` | `experience/ui/` | UI component library |
| `app/space/` | `experience/navigation/` | Object-first navigation |
| `app/founder/` | `experience/workspace/` | Workspace model |
| `app/routes/` | `experience/api/` | API layer |
| `app/adapters/` + `shunya_os_gmail/` | `experience/adapters/` | Channel adapters |
| `app/collaboration/` | `experience/collaboration/` | AI collaboration |
| New | `experience/objects/` | Object renderers |

### 10.4 Phase 4: Domain — Business Surfaces

Extract all domain-specific code into `domains/`:

| Current | Target | Business Canon (03) |
|---------|--------|---------------------|
| `shunya_os_crm/` | `domains/travel/` | Domain surface |
| Travel models from `app/models.py` | `domains/travel/models/` | Domain object extensions |
| Travel templates | `domains/travel/ui/` | Domain UI |
| `shunya_os_dashboard/` | `experience/ui/` + `domains/travel/` | Merge into canonical |
| `shunya_os_documents/` | `domains/travel/` + `experience/` | Merge into canonical |
| `shunya_os_workflow/` | `intelligence/executive/` + `domains/travel/` | Merge into canonical |

### 10.5 Phase 5: Cleanup

- Remove all adapter code that bridged old → new
- Archive `app/shunya/` legacy implementations
- Remove separate sub-app directories (`shunya_os_crm/`, etc.)
- Update all imports project-wide
- Remove `app/` monolithic directory once empty

---

## 11. Module Boundaries

### 11.1 Dependency Direction (Derived from Ontology)

```
core/ ───── provides ontological primitives
  │
  ▼
intelligence/ ───── provides cognitive processing
  │
  ▼
experience/ ───── provides human interface
  │
  ▼
domains/ ───── provides business-specific extensions
```

### 11.2 Boundary Rules

| Rule | Derivation | Description |
|------|-----------|-------------|
| **Core → Intelligence** | Ontology §18 | Core exports ontological primitives; intelligence imports them |
| **Intelligence → Experience** | 00 §16 → 08 §5 | Intelligence exports engine outputs; experience presents them |
| **Experience → Domains** | 03 §10 | Experience provides rendering framework; domains fill it |
| **Domains → Core** | 04 §1 | Domains extend core objects via protocol; never modify core |
| **No circular dependencies** | 00 §2.1 | Dependency direction is enforced at build time |
| **No core → domain imports** | 03 §2.2 | Core never knows about any domain |

---

## 12. Domain Separation

### 12.1 What Goes in `domains/`

- **Domain object extensions** — Business Objects from 03_business_canon.md extended with domain-specific attributes (e.g., Booking extends Commitment with check_in_date)
- **Domain workflows** — domain-specific process flows (e.g., travel booking workflow, healthcare diagnosis workflow)
- **Domain adapters** — domain-specific external system integrations (e.g., GDS for travel, EHR for healthcare)
- **Domain UI** — domain-specific components and copy (e.g., travel forms, healthcare dashboards)
- **Domain policies** — domain-specific compliance rules

### 12.2 Creating a New Domain Surface

1. Copy `domains/_template/`
2. Define domain object extensions extending Business Canon objects
3. Implement domain workflows using the Executive Engine
4. Implement domain adapters connecting to external systems
5. Create domain UI using the experience layer's component library
6. Register domain with the domain registry

---

## 13. Future Extensibility

### 13.1 Adding New Modules

| If the architecture defines... | Add to... | Example |
|------------------------------|-----------|---------|
| A new ontological primitive | `core/` | A new fundamental kind of thing |
| A new cognitive engine | `intelligence/` | A new way of processing |
| A new experience pattern | `experience/` | A new way of presenting |
| A new domain surface | `domains/` | A new industry vertical |

### 13.2 Package Dependencies

- `core/` — zero external dependencies beyond Python stdlib
- `intelligence/` — depends on `core/` + optional inference provider SDKs
- `experience/` — depends on `core/` + `intelligence/` + web framework
- `domains/` — depends on all of the above + domain-specific SDKs

---

## 14. Relationship to Other Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | **Primary derivation source** — every directory maps to an ontological primitive |
| **01_shunya_vision.md** | Repository structure enables the compounding intelligence vision |
| **02_shunya_constitution.md** | Core/domain separation enforces Constitutional boundaries |
| **03_business_canon.md** | **Secondary derivation source** — domain surfaces map to Business Objects |
| **04_universal_object_protocol.md** | Kernel module implements the protocol contract |
| **05_runtime_canon.md** | **Tertiary derivation source** — runtime layers map to repository layers |
| **06_data_canon.md** | Storage module boundaries match data architecture |
| **07_ai_canon.md** | **Key derivation source** — intelligence/ maps to the 9 Cognitive Engines |
| **08_experience_canon.md** | **Key derivation source** — experience/ implements the experience principles |
| **10_migration_canon.md** | Consolidation plan drives migration phases |
| **11_engineering_canon.md** | Module boundaries are enforced by engineering standards |
| **12_launch_roadmap.md** | Repository consolidation is a milestone |

---

> **This document is not an independent proposal. It is a direct consequence of 00, 03, 05, 07, and 08.**
> **If those documents change, this document must be updated to match.**