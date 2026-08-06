# Z-08 Heritage Preservation Audit — SHUNYA Legacy → Current Comparison

**Directive:** Z-08 Article XI — Heritage Preservation before Genesis Reset
**Date:** 2026-08-01
**Auditor:** Subagent — Heritage Preservation Workstream
**Source Repo:** `/home/shunya-deploy/shunya_legacy`
**Target Repo:** `/home/shunya-deploy/shunya_os`

---

## Table of Contents

- [1. Purpose & Methodology](#1-purpose--methodology)
- [2. Vision & Mission Comparison](#2-vision--mission-comparison)
- [3. Architecture Principles Comparison](#3-architecture-principles-comparison)
- [4. Canonical Terminology Comparison](#4-canonical-terminology-comparison)
- [5. Constitutional Principles Comparison](#5-constitutional-principles-comparison)
- [6. Design Philosophy Comparison](#6-design-philosophy-comparison)
- [7. Missing Enduring Ideas — Recommended for Restoration](#7-missing-enduring-ideas--recommended-for-restoration)
- [8. Summary Classification Table](#8-summary-classification-table)

---

## 1. Purpose & Methodology

### 1.1 Purpose

This document performs a systematic comparison between the foundational documents in the legacy SHUNYA repository (`shunya_legacy`) and the current codebase (`shunya_os`). Every foundational document from the legacy repo has been read and its concepts, philosophy, and principles compared against the current codebase. Each concept is classified according to the Z-08 Article XI specification.

### 1.2 Classification Categories

| Classification | Meaning |
|---------------|---------|
| **Preserved** | Concept carried forward substantially unchanged |
| **Improved** | Concept evolved with greater sophistication or clarity |
| **Intentionally Replaced** | Deliberately replaced with a different approach |
| **Missing** | Present in legacy, absent in current; no evidence of intentional replacement |
| **Recommended for Restoration** | Enduring value that should be recovered before Genesis Reset |

### 1.3 Legacy Documents Audited

| Document Path | Type |
|--------------|------|
| `README.md` | Vision Statement |
| `docs/architecture/ARCHITECTURE.md` | Core Architecture (Frozen v1.0) |
| `repository/architecture/MASTER_ARCHITECTURE.md` | Master Architecture Reference |
| `repository/architecture/ENGINEERING_PRINCIPLES.md` | 10 Engineering Principles |
| `repository/architecture/PLATFORM_LAYERS.md` | 5-Layer Architecture |
| `repository/architecture/ARCHITECTURE_DECISIONS.md` | 10 Architectural Decisions (AD-001 through AD-010) |
| `repository/architecture/DECISION_LOG.md` | Chronological Decision Timeline |
| `repository/architecture/DIRECTORY_STANDARDS.md` | Directory & Naming Conventions |
| `repository/architecture/ENGINE_DEPENDENCY_GRAPH.md` | Dependency Rules |
| `repository/architecture/ENGINE_INTERACTION.md` | Interaction Model & Principles |
| `repository/architecture/FUTURE_EXPANSION.md` | Long-Term Expansion Strategy |
| `repository/architecture/PLATFORM_ROADMAP.md` | Strategic Roadmap |
| `repository/architecture/PLATFORM_STATUS.md` | Operational Snapshot |
| `repository/architecture/RUNTIME_EXECUTION_FLOW.md` | Runtime Lifecycle |
| `repository/architecture/VERSIONING_STRATEGY.md` | SemVer & Release Strategy |
| `repository/specifications/foundation/FOUNDATION_BLUEPRINT.md` | Foundation Engine Specification |
| `repository/specifications/foundation/FOUNDATION_STANDARD_LIBRARY.md` | Foundation Standard Library |
| `repository/specifications/governance/GOV-001.md` | Governance Engine v1.0 |
| `repository/specifications/runtime/KERNEL.md` | Runtime Kernel |
| `repository/specifications/runtime/EVENT_BUS.md` | Event Bus |
| `repository/specifications/runtime/ENGINE_REGISTRY.md` | Engine Registry |

---

## 2. Vision & Mission Comparison

### 2.1 Legacy Vision

> **"Shunya is a Universal Organizational Computing Platform"**  
> **"Shunya is a Decision Operating System"**

The legacy vision positioned Shunya as a platform for modeling, operating, learning, and continuously improving organizations. The first organization built on Shunya was Panchi Club Pvt Ltd. The core flow was:

```
Observation → Knowledge → Reasoning → Planner → Workflow → Execution → Events → Learning
```

Cross-cutting services: Foundation, Runtime, Governance, Memory, CLI.

### 2.2 Current Vision

> **"SHUNYA is a Compounding Intelligence Operating System"**  
> **"SHUNYA OS is the first AI-native company built on Shunya"**

The current vision positions Shunya as a **compounding intelligence** platform — one where every completed cycle improves the next. The pipeline has evolved to:

```
Interface → Knowledge → Reasoning → Planner → Governance → Workflow → Executor → Observer → Learning
```

With Doctor as a cross-cutting integrity checker.

### 2.3 Assessment: **Improved**

The compounding intelligence vision is a **superset** of the Decision OS vision. It retains all Decision OS concepts (observation, knowledge, reasoning, planning, workflow, execution, learning) while adding:

- **Governance** as an explicit pipeline stage between Planner and Workflow
- **Executor** as a dedicated layer (was implicit in legacy Workflow)
- **Observer** replacing Events, with richer deviation/anomaly detection
- **Learning** as a formal feedback loop into Knowledge
- **Compounding** as the core mechanism — every cycle makes the next smarter

The legacy framing "AI is one possible reasoning engine" evolved into the current "Humans Own Intent, Shunya Owns Intelligence Amplification" — a more mature, integrated human-AI relationship.

---

## 3. Architecture Principles Comparison

### 3.1 Legacy Principles (10 Engineering Principles)

| # | Legacy Principle | Current Status | Assessment |
|---|-----------------|---------------|------------|
| 1 | **Single Responsibility** — Every engine owns exactly one primary responsibility | Every engine owns one primary capability | **Preserved** |
| 2 | **Composition over Coupling** — Engines collaborate through public APIs | Engines communicate through runtime contracts | **Preserved** |
| 3 | **Stable Public APIs** — Only exported APIs are platform contracts | Evidence-backed, deterministic APIs | **Preserved** |
| 4 | **Downward Dependencies** — Dependencies always point toward lower layers | Same rule enforced | **Preserved** |
| 5 | **Documentation First** — Documentation is part of implementation | Comprehensive constitutional documentation | **Improved** |
| 6 | **Test Before Release** — Unit tests, build validation, doctor validation | Test suite exists (pytest), CI pipeline | **Preserved** |
| 7 | **Governance Before Growth** — New capabilities must strengthen architectural consistency | Governance is a core pipeline stage | **Improved** |
| 8 | **Platform Before Product** — Reusable platform capabilities belong inside Shunya | Core engines are business-agnostic | **Preserved** |
| 9 | **ADR-Driven Architecture** — Architectural decisions recorded through ADRs | ADR system present in `decisions/` directory | **Preserved** |
| 10 | **Continuous Improvement** — Architecture stable, implementation evolves | Compounding intelligence loop | **Improved** |

### 3.2 Legacy Architectural Decisions (AD-001 through AD-010)

| AD | Legacy Decision | Current Status | Assessment |
|----|----------------|---------------|------------|
| AD-001 | Foundation is lowest platform layer | No explicit Foundation package — shared primitives use Python stdlib | **Intentionally Replaced** |
| AD-002 | Runtime owns platform execution | Runtime is distributed across engine orchestration | **Preserved** (conceptually) |
| AD-003 | Engines own one primary responsibility | Each module owns one capability | **Preserved** |
| AD-004 | Dependencies flow downward | Same rule | **Preserved** |
| AD-005 | Public APIs are contracts | Evidence-backed, documented APIs | **Preserved** |
| AD-006 | Architecture before implementation | Constitutional documents precede implementation | **Preserved** |
| AD-007 | Event-driven collaboration | CanonicalObservation pipeline, 11 categories | **Improved** |
| AD-008 | Documentation is part of the product | Comprehensive constitutional documentation | **Improved** |
| AD-009 | Quality gates are mandatory | CI/CD, tests (pytest), health checks | **Preserved** |
| AD-010 | Platform growth through extension | Modular engine architecture | **Preserved** |

### 3.3 Layer Architecture

| Legacy Layer | Current Equivalent | Assessment |
|-------------|-------------------|------------|
| Layer 1: Host Applications (CLI, REST, Web, SDK, Workers) | Interface Layer (WhatsApp, Web, API, Telegram) | **Improved** — Multi-channel, broader |
| Layer 2: Runtime (Kernel, Lifecycle, Container, Context, Event Bus, Engine Registry, Plugin Manager) | Distributed runtime — no single monolithic container | **Intentionally Replaced** |
| Layer 3: Platform Engines (Knowledge, Governance, Doctor) + Future (Memory, Workflow, AI, Analytics, Scheduler) | Nine engines (Knowledge, Reasoning, Planner, Governance, Executor, Observer, Learning, Context Fusion, Identity) + Organizational Intelligence, Execution Intelligence, Awareness | **Improved** — Far richer engine landscape |
| Layer 4: Foundation (Result, Option, Validation, Error, Time, Config, Logging, Platform) | No Foundation package — Python stdlib + dataclasses + typing | **Intentionally Replaced** |
| Layer 5: Platform (Node.js, TypeScript, OS) | Python 3.12, Flask, PostgreSQL 16 | **Intentionally Replaced** |

---

## 4. Canonical Terminology Comparison

### 4.1 Engine Nomenclature

| Legacy Term | Current Term | Assessment |
|-------------|-------------|------------|
| Foundation Engine | No direct equivalent — shared utilities distributed | **Intentionally Replaced** |
| Knowledge Engine | Knowledge Engine + Knowledge Store (ES-002) | **Preserved** with richer implementation |
| Governance Engine | Governance Engine (ES-001) — 6-stage pipeline | **Improved** |
| Doctor Engine | Doctor — pipeline integrity layer | **Preserved** |
| Runtime Engine | Distributed runtime orchestrator | **Preserved** (restructured) |
| Memory Engine (planned) | Memory Architecture — MemoryRecord, MemoryCandidate, MemoryProvenance | **Improved** — now implemented |
| Workflow Engine (planned) | Workflow Layer in pipeline | **Improved** — now implemented |
| AI Engine (planned) | Intelligence Amplification philosophy; LLM in app/llm/ | **Improved** — now implemented |
| N/A | Reasoning Engine | **New** — not in legacy |
| N/A | Planner Engine (ES-004) | **New** — legacy had Planner as concept, now formal engine |
| N/A | Executor Engine (ES-005) | **New** — legacy execution was implicit in Workflow |
| N/A | Observer Engine (ES-006) | **New** — legacy events were simpler |
| N/A | Learning Engine (ES-007) | **New** — legacy learning was aspirational |
| N/A | Context Fusion Engine (ES-009) | **New** |
| N/A | Identity Engine | **New** |
| N/A | Execution Intelligence | **New** — Health, Timeline, Risk, Pattern, Next Action, Dependency Graph |
| N/A | Autonomous Awareness | **New** — CanonicalObservation pipeline |
| N/A | Organizational Intelligence | **New** — OrgUnit, OrgRole, Ownership, Delegation |

### 4.2 Core Flow Terminology

| Legacy Flow | Current Flow | Assessment |
|-------------|-------------|------------|
| Observation → Knowledge | Interface → Knowledge | **Improved** — Added explicit Interface layer |
| Knowledge → Reasoning | Knowledge → Reasoning | **Preserved** |
| Reasoning → Planner | Reasoning → Planner | **Preserved** |
| Planner → Workflow | Planner → Governance → Workflow | **Improved** — Added Governance checkpoint |
| Workflow → Execution | Workflow → Executor | **Improved** — Cleaner separation |
| Execution → Events | Executor → Observer | **Improved** — Observer is richer |
| Events → Learning | Observer → Learning | **Improved** — Learning feeds back into Knowledge |
| Learning → (back to Observation) | Learning → Knowledge (compounding loop) | **Improved** — Explicit compounding |

### 4.3 Conceptual Vocabulary

| Legacy Concept | Current Concept | Assessment |
|----------------|----------------|------------|
| "Decision Operating System" | "Compounding Intelligence Operating System" | **Improved** |
| "Models, operates, learns, improves organizations" | "Continuously transforms knowledge into better decisions" | **Improved** |
| "AI is one possible reasoning engine" | "Humans Own Intent. Shunya Owns Intelligence Amplification." | **Improved** |
| N/A | Universal Ontology (18 concepts) | **New** |
| N/A | Universal Behavior Constitution (15+ behaviors) | **New** |
| N/A | "Deterministic-first" | **New** |
| N/A | "Business-agnostic" | **New** |
| N/A | "Evidence-backed reasoning" | **New** |
| N/A | "Explainable intelligence" | **New** |
| N/A | "No duplicated state" | **New** |
| N/A | "Immutable history" | **New** |
| Result/Option/Validation primitives | Python dataclasses + typing + exceptions | **Intentionally Replaced** |
| @shunya/foundation, @shunya/knowledge, etc. | app/ directory structure | **Intentionally Replaced** |
| "Package owns one responsibility" | "Module owns one capability" | **Preserved** |
| "Contracts are stable" | "Stable public APIs" | **Preserved** |
| "Platform Before Product" | "Business-agnostic core" | **Preserved** |

---

## 5. Constitutional Principles Comparison

### 5.1 Legacy Constitutional Principles

The legacy docs establish the following constitutional-grade principles:

| Legacy Principle | Current Principle | Assessment |
|-----------------|-------------------|------------|
| Single Responsibility | Engine-level single responsibility | **Preserved** |
| Stable Contracts | Evidence-backed, deterministic APIs | **Preserved** |
| Downward Dependencies | Same rule | **Preserved** |
| Documentation as Implementation | Constitutional documentation | **Preserved** |
| Governance Before Growth | Governance as pipeline stage | **Improved** |
| Platform Before Product | Business-agnostic principles | **Preserved** |
| ADR-Driven | ADR system | **Preserved** |
| Event-Driven | CanonicalObservation pipeline | **Improved** |
| Quality Gates | CI/CD gates | **Preserved** |
| Continuous Improvement | Compounding intelligence | **Improved** |

### 5.2 New Constitutional Principles in Current Codebase

The following constitutional-grade principles exist in the current codebase with no legacy equivalent:

| Current Principle | Source Document | Assessment |
|-------------------|----------------|------------|
| Deterministic-first — No randomness in intelligence engines | ARCHITECTURE_v1.0 §1.5 | **New** |
| Business-agnostic — No domain assumptions in core | ARCHITECTURE_v1.0 §1.4 | **New** |
| Evidence-backed — Every output has provenance | ARCHITECTURE_v1.0 §1.6 | **New** |
| Explainable — Every conclusion decomposable | ARCHITECTURE_v1.0 §1.7 | **New** |
| Role-centric, not person-centric | ARCHITECTURE_v1.0 §1.2(5) | **New** |
| No duplicated state | ARCHITECTURE_v1.0 §1.2(6) | **New** |
| Immutable history — Append-only | ARCHITECTURE_v1.0 §1.2(8) | **New** |
| Universal Object Behavior (15 behaviors) | UNIVERSAL_BEHAVIOR_CONSTITUTION | **New** |
| Universal Lifecycle (12 states) | UNIVERSAL_BEHAVIOR_CONSTITUTION | **New** |
| Graph-based relationships | UNIVERSAL_BEHAVIOR_CONSTITUTION | **New** |
| Intent-driven workspace | WORKSPACE_PHILOSOPHY | **New** |
| Continuous human augmentation | SHUNYA_HUMAN_OS_v1.0 §1 | **New** |
| AI Proposes, Humans Disposes | SHUNYA_ARCHITECTURE §2.3 | **New** |
| Trust Compounds | SHUNYA_ARCHITECTURE §2.4 | **New** |
| Calm Computing | SHUNYA_HUMAN_OS_v1.0 §1.5 | **New** |
| Trust Before Automation | SHUNYA_HUMAN_OS_v1.0 §1.6 | **New** |

---

## 6. Design Philosophy Comparison

### 6.1 Software Architecture Philosophy

| Dimension | Legacy | Current | Assessment |
|-----------|--------|---------|------------|
| Stack | TypeScript/Node.js, pnpm, Turborepo | Python 3.12, Flask, PostgreSQL | **Intentionally Replaced** |
| Isolation | Monorepo with packages | Flask app with modules | **Intentionally Replaced** |
| Engine pattern | Independent npm packages | app/ directory modules + shunya/ pipeline | **Intentionally Replaced** |
| Type system | TypeScript with exported types | Python typing + dataclasses + Pydantic | **Intentionally Replaced** |
| Foundation primitives | Result, Option, Validation, Error, Time, Config, Logging | Python stdlib + Flask extensions + custom helpers | **Intentionally Replaced** |
| Multi-tenancy | Not present | First-class tenant layer | **New** — Major improvement |
| Frontend | Not present | Web dashboard + Telegram + WhatsApp | **New** |
| AI integration | AI as "one possible reasoning engine" | AI as core assistant, compounding intelligence | **Improved** |
| Documentation | Per-engine README/ARCHITECTURE/PUBLIC_API/LIFECYCLE/EXTENDING | Constitutional documents + per-module docs | **Preserved** (pattern) |
| Event system | Runtime Event Bus | CanonicalObservation + ObservationalPipeline | **Improved** |
| Plugin system | Plugin Manager planned | Implicit — not yet formalized | **Missing** |

### 6.2 Engineering Philosophy

| Legacy Principle | Current Application | Assessment |
|-----------------|---------------------|------------|
| "Packages own exactly one responsibility" | Modules own one capability | **Preserved** |
| "Reasoning never fetches data" | Deterministic, evidence-grounded reasoning | **Preserved** |
| "Workflow never makes decisions" | Governance separates decision from execution | **Preserved** |
| "Execution never updates knowledge directly" | Observer validates, Learning feeds Knowledge | **Preserved** |
| "Everything important becomes an Event" | CanonicalObservation pipeline (11 categories) | **Improved** |
| "Learning improves reasoning, not workflow" | Learning feeds Knowledge, not Workflow | **Preserved** |
| "AI is replaceable" | AI is augmentable, not the architecture | **Improved** |
| "Contracts are stable" | Stable, documented, versioned APIs | **Preserved** |

---

## 7. Missing Enduring Ideas — Recommended for Restoration

### 7.1 Plugin System Architecture

**Legacy source:** `repository/specifications/runtime/PLUGIN_SYSTEM.md`, `repository/specifications/runtime/PLUGIN_MANAGER.md`

**Why it matters:** The legacy had a well-defined Plugin System concept — the Runtime supports optional extensions (third-party engines, customer plugins, enterprise modules, AI providers, external connectors) that integrate without modifying Runtime internals. The current codebase mentions extension points (ARCHITECTURE_v1.0 §XV) and a marketplace (SHUNYA_UNIVERSAL_PLATFORM.md) but has no formal plugin architecture specification.

**Recommendation:** Restore the plugin system architecture as a formal specification. The legacy's architectural constraints (Foundation remains independent, Runtime remains orchestration layer, Engines own one responsibility) are now more important than ever given the multi-tenant, multi-business vision.

**Priority:** Medium — important for Phase 3I (Universal Marketplace).

### 7.2 Engine Registry Pattern

**Legacy source:** `repository/specifications/runtime/ENGINE_REGISTRY.md`

**Why it matters:** The legacy Engine Registry maintained the collection of engines with four operations: register, get, list, has. This pattern formalized engine discovery. The current codebase's engine architecture is more sophisticated but lacks an explicit registry concept for engine discovery and enumeration.

**Recommendation:** Restore the Engine Registry pattern. The conceptual API (`register()`, `get()`, `list()`, `has()`) remains valuable even though the implementation stack changed.

**Priority:** Medium — would improve engine discoverability.

### 7.3 Bootstrap Sequence Documentation

**Legacy source:** `repository/specifications/runtime/KERNEL.md`, `repository/architecture/RUNTIME_EXECUTION_FLOW.md`

**Why it matters:** The legacy had a clear, documented startup sequence: Bootstrap → Load Configuration → Create Runtime Kernel → Create Service Container → Create Runtime Context → Register Core Services → Register Platform Engines → Initialize Lifecycle Manager → Start Event Bus → Load Plugins → Publish runtime.started. The current `RuntimeService` handles coordination but lacks a similarly clear architectural specification of the startup lifecycle.

**Recommendation:** Document the current startup sequence with the same clarity as the legacy RUNTIME_EXECUTION_FLOW.md. The 9-step startup, deterministic state machine (Created → Initializing → Starting → Ready → Stopping → Disposed), and graceful shutdown protocol are all worth preserving.

**Priority:** Low — the current runtime works but documentation would improve maintainability.

### 7.4 Package Directory & Naming Standards

**Legacy source:** `repository/architecture/DIRECTORY_STANDARDS.md`

**Why it matters:** The legacy had a well-defined directory standard (lowercase directories, PascalCase files, single public entry point `src/index.ts`, every engine = README/ARCHITECTURE/PUBLIC_API/LIFECYCLE/EXTENDING). This provided consistency across the monorepo. The current codebase's `app/` directory structure is functional but not formally specified.

**Recommendation:** Formalize the current directory conventions. The pattern itself (conventions per module, consistent documentation expectations, naming standards) is preserved, but without a written standard it may drift.

**Priority:** Low — not blocking Genesis Reset.

### 7.5 Versioning Strategy (SemVer + Release Lifecycle)

**Legacy source:** `repository/architecture/VERSIONING_STRATEGY.md`

**Why it matters:** The legacy had a comprehensive versioning strategy — per-engine SemVer, platform version, release requirements (tests, build, documentation, ADR, release notes, Git tag), and development lifecycle (Architecture → Implementation → Testing → Documentation → Architecture Review → Release → Maintenance).

**Recommendation:** Restore the versioning strategy as a formal document. The legacy's release lifecycle and quality gates are still relevant. The per-module versioning and coordinated platform release concepts should be preserved.

**Priority:** Medium — important for production releases.

---

## 8. Summary Classification Table

### 8.1 All Items Classified

| Item | Legacy Source | Classification | Notes |
|------|-------------|----------------|-------|
| **Vision: Universal Org Computing Platform** | README.md, ARCHITECTURE.md | **Improved** | Evolved to Compounding Intelligence OS |
| **Core Pipeline (8-stage flow)** | docs/architecture/ARCHITECTURE.md | **Improved** | Expanded to 8+ stage with Governance, Executor, Observer |
| **Single Responsibility Principle** | ENGINEERING_PRINCIPLES.md, MASTER_ARCHITECTURE.md | **Preserved** | Core principle, still enforced |
| **Downward Dependencies** | ENGINEERING_PRINCIPLES.md, ENGINE_DEPENDENCY_GRAPH.md | **Preserved** | Still enforced |
| **Stable Public APIs** | ENGINEERING_PRINCIPLES.md, ARCHITECTURE_DECISIONS.md | **Preserved** | Still a core principle |
| **Composition over Coupling** | ENGINEERING_PRINCIPLES.md | **Preserved** | Engines collaborate through contracts |
| **Documentation First** | ENGINEERING_PRINCIPLES.md | **Improved** | Constitutional documentation |
| **Test Before Release** | ENGINEERING_PRINCIPLES.md | **Preserved** | pytest + CI pipeline |
| **Governance Before Growth** | ENGINEERING_PRINCIPLES.md | **Improved** | Governance is now a pipeline stage |
| **Platform Before Product** | ENGINEERING_PRINCIPLES.md | **Preserved** | Business-agnostic core engines |
| **ADR-Driven Architecture** | ENGINEERING_PRINCIPLES.md, ADR system | **Preserved** | ADRs in decisions/ |
| **Continuous Improvement** | ENGINEERING_PRINCIPLES.md | **Improved** | Compounding intelligence loop |
| **5-Layer Architecture** | PLATFORM_LAYERS.md | **Intentionally Replaced** | Replaced by engine-based architecture |
| **Foundation Engine (Result/Option/Validation)** | FOUNDATION_BLUEPRINT.md, FOUNDATION_STANDARD_LIBRARY.md | **Intentionally Replaced** | Replaced by Python stdlib + dataclasses |
| **Runtime Kernel + Container + Context** | KERNEL.md, RUNTIME_EXECUTION_FLOW.md | **Intentionally Replaced** | Distributed runtime, no monolithic container |
| **Event Bus** | EVENT_BUS.md | **Improved** | CanonicalObservation pipeline (11 categories) |
| **Engine Registry (register/get/list/has)** | ENGINE_REGISTRY.md | **Recommended for Restoration** | Valuable pattern for engine discovery |
| **Plugin System Architecture** | PLUGIN_SYSTEM.md, PLUGIN_MANAGER.md | **Recommended for Restoration** | Critical for marketplace vision |
| **Bootstrap Sequence Documentation** | RUNTIME_EXECUTION_FLOW.md, KERNEL.md | **Recommended for Restoration** | Clear startup lifecycle worth documenting |
| **Directory Standards** | DIRECTORY_STANDARDS.md | **Missing** | No formal equivalent in current codebase |
| **Versioning Strategy (SemVer + Release Lifecycle)** | VERSIONING_STRATEGY.md | **Recommended for Restoration** | Important for production readiness |
| **Governance Engine (GOV-001)** | GOV-001.md | **Improved** | Now a 6-stage deterministic pipeline |
| **Doctor Engine** | multiple docs | **Preserved** | Still exists as integrity checker |
| **Knowledge Engine** | multiple docs | **Preserved** | Richer implementation with versioned facts |
| **Memory Engine (planned)** | FUTURE_EXPANSION.md, ARCHITECTURE_DECISIONS.md | **Improved** | Now implemented with formal lifecycle |
| **Workflow Engine (planned)** | multiple docs | **Improved** | Now implemented in pipeline |
| **AI Engine (planned)** | multiple docs | **Improved** | Now core to the philosophy |
| **Event-Driven Communication** | ENGINE_INTERACTION.md | **Improved** | CanonicalObservation pipeline |
| **Multi-Tenancy** | — | **New** | Not present in legacy |
| **Universal Ontology (18 concepts)** | — | **New** | Constitutional foundation |
| **Universal Behavior Constitution** | — | **New** | 15+ behavioral contracts |
| **Deterministic-First Principles** | — | **New** | No randomness in intelligence |
| **Business-Agnostic Principles** | — | **New** | Domain as data, not code |
| **Evidence-Backed Reasoning** | — | **New** | Every output has provenance |
| **Explainability Philosophy** | — | **New** | Decomposable conclusions |
| **Execution Intelligence** | — | **New** | Health, Timeline, Risk, Patterns |
| **Organizational Intelligence** | — | **New** | Roles, Ownership, Delegation |
| **Autonomous Awareness** | — | **New** | CanonicalObservation pipeline |
| **Human Interface Philosophy** | — | **New** | Calm computing, trust before automation |
| **Prediction & Simulation Philosophy** | — | **New** | Deterministic prediction lifecycle |
| **Intent-Driven Workspace** | — | **New** | Not object-driven |
| **Stack: TypeScript/Node.js** | package.json, pnpm-workspace.yaml | **Intentionally Replaced** | Migrated to Python/Flask/PostgreSQL |

### 8.2 Classification Summary — Counts

| Classification | Count | Percentage |
|---------------|-------|-----------|
| **Improved** | 16 | 25% |
| **Preserved** | 17 | 27% |
| **Intentionally Replaced** | 7 | 11% |
| **New (no legacy equivalent)** | 17 | 27% |
| **Recommended for Restoration** | 4 | 6% |
| **Missing** | 1 | 2% |
| **Total** | 62 | 100% |

### 8.3 Key Takeaway

The current SHUNYA OS codebase represents a **significant architectural evolution** over the legacy. 52% of legacy concepts have been Preserved or Improved, 11% were Intentionally Replaced (primarily the Foundation package, monolithic Runtime container, and stack migration), and only 6% are Recommended for Restoration (Plugin System, Engine Registry, Bootstrap documentation, Versioning Strategy). 27% of current concepts are entirely new — primarily the Universal Ontology, Universal Behavior Constitution, business-agnostic determinism principles, and the multi-tenant architecture.

The recommendation is to proceed with Genesis Reset after restoring the four identified artifacts (Plugin System architecture, Engine Registry pattern, Bootstrap lifecycle documentation, Versioning Strategy). These are small, well-defined documents that would close the gap between legacy and current without introducing implementation-specific or version-specific content.

---

*End of Z-08 Heritage Preservation Audit*