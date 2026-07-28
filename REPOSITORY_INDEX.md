# SHUNYA OS — Repository Index

> **Generated:** 2026-07-28  
> **Repository root:** `/home/shunya-deploy/shunya_os`  
> **Purpose:** Master index of every document, directory, engine, runtime, phase, ADR, canon, and report with metadata and ownership.

---

## 1. Repository Overview

| Attribute | Value |
|-----------|-------|
| **Name** | Shunya Business OS |
| **Type** | AI Business OS — market-ready product |
| **Language** | Python (Flask backend) + TypeScript/React (frontend) |
| **Python version** | 3.12 (via `runtime.txt`) |
| **Deployment** | Heroku-ready (Procfile, runtime.txt, config.yaml) |
| **Testing** | pytest (~137+ test files across 30+ directories) |
| **Infrastructure** | Docker, nginx, environment-specific configs |
| **Phase count** | 14 phases (A–N) with implementation reports |
| **Core runtimes** | 23 runtime modules |
| **Architecture docs** | 30+ architecture documents |
| **Governance docs** | 25+ governance documents |
| **Canon docs** | 34 canon documents |
| **Design docs** | 26 design/experience documents |
| **App modules** | 338+ Python modules |
| **Frontend** | 30+ TypeScript/JS components + 16 TSX components |

---

## 2. Root Documents

### Strategic & Vision Documents

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `README.md` | Product Vision | Active | Market-ready product description, one-sentence pitch |
| `PROJECT.md` | Project Overview | Active | Project-level description and scope |
| `DESIGN.md` | Design Overview | Active | Design philosophy and approach |
| `ARCHITECTURE.md` | Architecture Overview | Active | Top-level architecture documentation |
| `ARCHITECTURAL_VALIDATION.md` | Validation Report | Active | Architecture validation findings |
| `FINAL_PRODUCT_VISION.md` | Vision Document | Active | Final product vision statement |
| `ORCHESTRATION_GUIDE.md` | Operations Guide | Active | System orchestration and operational guide |
| `COGNITIVE_VALIDATION_REPORT.md` | Validation Report | Active | Cognitive architecture validation |
| `PREDICTION_PHILOSOPHY_v1.0.md` | Philosophy Doc | Active | Prediction philosophy and approach v1.0 |
| `SHUNYA_ARCHITECTURE.md` | Architecture Doc | Active | Core Shunya architecture |
| `SHUNYA_ARCHITECTURE_v1.0.md` | Architecture Doc | Active | Architecture v1.0 specification |
| `SHUNYA_ENGINEERING_DASHBOARD.md` | Dashboard | Active | Engineering metrics and status dashboard |
| `SHUNYA_HUMAN_OS_v1.0.md` | Specification | Active | Human OS integration specification v1.0 |
| `SHUNYA_IMPLEMENTATION_DEPENDENCY_GRAPH.md` | Technical Doc | Active | Implementation dependency graph |
| `SHUNYA_IMPLEMENTATION_PROGRAM.md` | Program Plan | Active | Implementation program and methodology |
| `SHUNYA_IMPLEMENTATION_REPORTING_STANDARD.md` | Standards Doc | Active | Reporting standards for implementation |
| `SHUNYA_OS_NEXT_PLAN.md` | Roadmap | Active | Next-phase planning for Shunya OS |
| `SHUNYA_PROGRAM_BACKLOG.md` | Backlog | Active | Program backlog and work items |
| `SHUNYA_SPRINT_PLAN.md` | Sprint Plan | Active | Current sprint planning |
| `SHUNYA_UNIVERSAL_PLATFORM.md` | Platform Doc | Active | Universal platform specification |
| `SHUNYA_UNIVERSAL_UI_PLAN.md` | UI Plan | Active | Universal UI planning |

### Configuration & Deployment

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `config.yaml` | Config | Active | Application configuration |
| `Procfile` | Heroku Config | Active | Heroku process type definitions |
| `runtime.txt` | Python Version | Active | Python runtime version (3.12) |
| `requirements.txt` | Dependencies | Active | Python package dependencies |
| `Dockerfile` | Docker Config | Active | Container build definition |
| `.gitignore` | Git Config | Active | Git ignore patterns |
| `.env.example` | Environment | Active | Example environment variables |
| `.env.audit` | Environment | Active | Audited environment variables |
| `app.py` | Entry Point | Active | Application entry point |

### Phase Implementation Reports (A–N)

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `PHASE_A_IMPLEMENTATION_REPORT.md` | Phase Report | Complete | Phase A — Foundation implementation |
| `PHASE_B_IMPLEMENTATION_REPORT.md` | Phase Report | Complete | Phase B — Core identity and relationships |
| `PHASE_C_IMPLEMENTATION_REPORT.md` | Phase Report | Complete | Phase C — Communication and hardening |
| `PHASE_D_IMPLEMENTATION_REPORT.md` | Phase Report | Complete | Phase D — Privacy and closure audit |
| `PHASE_E_IMPLEMENTATION_REPORT.md` | Phase Report | Complete | Phase E — Execution runtime |
| `PHASE_F_IMPLEMENTATION_REPORT.md` | Phase Report | Complete | Phase F — Canonical implementation |
| `PHASE_F_CANONICAL_IMPLEMENTATION_REPORT.md` | Phase Report | Complete | Phase F — Canonical report |
| `PHASE_G_COMPLETION_REPORT.md` | Phase Report | Complete | Phase G — Integration runtime |
| `PHASE_H_COMPLETION_REPORT.md` | Phase Report | Complete | Phase H — Memory/knowledge runtime |
| `PHASE_I_COMPLETION_REPORT.md` | Phase Report | Complete | Phase I — Planning runtime |
| `PHASE_I_IMPLEMENTATION_PLAN.md` | Phase Plan | Complete | Phase I — Planning runtime plan |
| `PHASE_J_COMPLETION_REPORT.md` | Phase Report | Complete | Phase J — Automation/event runtime |
| `PHASE_J_IMPLEMENTATION_PLAN.md` | Phase Plan | Complete | Phase J — Implementation plan |
| `PHASE_K_COMPLETION_REPORT.md` | Phase Report | Complete | Phase K — Projection engine |
| `PHASE_K_IMPLEMENTATION_PLAN.md` | Phase Plan | Complete | Phase K — Implementation plan |
| `PHASE_L_COMPLETION_REPORT.md` | Phase Report | Complete | Phase L — Convergence |
| `PHASE_L_IMPLEMENTATION_PLAN.md` | Phase Plan | Complete | Phase L — Implementation plan |
| `PHASE_M_COMPLETION_REPORT.md` | Phase Report | Complete | Phase M — Implementation |
| `PHASE_M_IMPLEMENTATION_PLAN.md` | Phase Plan | Complete | Phase M — Implementation plan |
| `PHASE_N_IMPLEMENTATION_PLAN.md` | Phase Plan | Planned | Phase N — Future implementation plan |

---

## 3. Constitutional Program

Location: `constitution/`

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `constitution/FIRST_PRINCIPLES.md` | Constitution | Active | First principles of Shunya OS |
| `constitution/SHUNYA_CONSTITUTION.md` | Constitution | Active | Core constitutional document |
| `constitution/CANONICAL_DEFINITIONS.md` | Definitions | Active | Canonical term definitions |
| `constitution/CONSTITUTIONAL_COMPLIANCE.md` | Compliance | Active | Constitutional compliance framework |
| `constitution/HERMES_IMPLEMENTATION_CHARTER.md` | Charter | Active | Hermes agent implementation charter |
| `constitution/CONSTITUTIONAL_METADATA.md` | Metadata | Active | Constitutional metadata and versioning |
| `constitution/generate_pdf.py` | Script | Active | PDF generation script for constitution |
| `constitution/pdf/SHUNYA_CONSTITUTION_v1.0.pdf` | PDF | Active | Constitution v1.0 in PDF format |
| `constitution/html/SHUNYA_CONSTITUTION_v1.0.html` | HTML | Active | Constitution v1.0 in HTML format |

---

## 4. Architecture

Location: `architecture/`

### Core Architecture Documents

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `architecture/ADAPTIVE_INTELLIGENCE_RUNTIME.md` | Architecture | Active | Adaptive intelligence runtime design |
| `architecture/ARCHITECTURE_BASELINE_1_0_COMPLETE.md` | Baseline | Complete | Architecture baseline v1.0 complete |
| `architecture/ARCHITECTURE_BASELINE_FREEZE.md` | Baseline | Freeze | Architecture baseline freeze document |
| `architecture/ARCHITECTURE_BASELINE_REVIEW.md` | Review | Active | Architecture baseline review |
| `architecture/ARCHITECTURE_FINDINGS_CLASSIFICATION.md` | Findings | Active | Architecture findings classification |
| `architecture/ARCHITECTURE_GOVERNANCE_FRAMEWORK.md` | Governance | Active | Architecture governance framework |
| `architecture/COGNITIVE_WORKSPACE_RUNTIME.md` | Architecture | Active | Cognitive workspace runtime design |
| `architecture/CONSTITUTIONAL_ARCHITECTURE_AUDIT.md` | Audit | Active | Constitutional architecture audit |
| `architecture/CONSTITUTIONAL_REMEDIATION_REPORT.md` | Report | Active | Constitutional remediation findings |
| `architecture/D1_IDENTITY_AND_ORGANIZATIONS.md` | Architecture | Active | Identity and organizations architecture |
| `architecture/DECISION_INTELLIGENCE_ARCHITECTURE.md` | Architecture | Active | Decision intelligence architecture |
| `architecture/ENGINEERING_EXECUTION_SYSTEM.md` | Architecture | Active | Engineering execution system |
| `architecture/ENGINEERING_PROGRESS_REPORT_E001.md` | Report | Active | Engineering progress report E001 |
| `architecture/ENGINE_EVIDENCE_VALIDATION.md` | Validation | Active | Engine evidence validation |
| `architecture/EXECUTION_INTELLIGENCE_ARCHITECTURE.md` | Architecture | Active | Execution intelligence architecture |
| `architecture/FOUNDER_WORKSPACE_SPECIFICATION.md` | Specification | Active | Founder workspace specification |
| `architecture/GKF-000-GOVERNED-KNOWLEDGE-FRAMEWORK.md` | Framework | Active | Governed knowledge framework (GKF-000) |
| `architecture/IMPLEMENTATION_MASTER_PLAN.md` | Plan | Active | Implementation master plan |
| `architecture/PHASE_F_ARCHITECTURAL_IMPACT_ANALYSIS.md` | Analysis | Active | Phase F architectural impact analysis |
| `architecture/PHASE_F_ARCHITECTURE_DELTA_REVIEW.md` | Review | Active | Phase F architecture delta review |
| `architecture/PHASE_F_CANONICAL_ARCHITECTURE_AUDIT.md` | Audit | Active | Phase F canonical architecture audit |
| `architecture/PHASE_F_VERIFICATION_EVIDENCE_RECONCILIATION.md` | Verification | Active | Phase F verification evidence reconciliation |
| `architecture/SHUNYA_CONSTITUTION.md` | Constitution | Active | Architecture-level constitution |
| `architecture/SHUNYA_CORE_MODELS.md` | Models | Active | Core data models |
| `architecture/SHUNYA_SYSTEM_FLOW.md` | Flow | Active | System flow documentation |
| `architecture/SUPPORTING_ARCHITECTURE_JUSTIFICATION.md` | Justification | Active | Supporting architecture justification |
| `architecture/UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md` | Architecture | Active | Universal knowledge graph architecture |
| `architecture/UNIVERSAL_ONTOLOGY.md` | Ontology | Active | Universal ontology |
| `architecture/UNIVERSAL_PERCEPTION_ARCHITECTURE.md` | Architecture | Active | Universal perception architecture |

### DNA — Device-Native Architecture (9 docs)

| Path | Status | Description |
|------|--------|-------------|
| `architecture/dna-01-device-native-architecture.md` | Active | Device-native architecture foundation |
| `architecture/dna-01.2-runtime-context.md` | Active | Runtime context specification |
| `architecture/dna-01.3-device-matrix.md` | Active | Device matrix |
| `architecture/dna-01.4-component-adaptation-matrix.md` | Active | Component adaptation matrix |
| `architecture/dna-01.5-typography-matrix.md` | Active | Typography matrix |
| `architecture/dna-01.6-layout-matrix.md` | Active | Layout matrix |
| `architecture/dna-01.7-motion-and-transition-spec.md` | Active | Motion and transition specification |
| `architecture/dna-01.8-homepage-narrative-flow.md` | Active | Homepage narrative flow |
| `architecture/dna-01.9-implementation-roadmap.md` | Active | Implementation roadmap |

### SMS — Semantic Model Specifications (3 docs)

| Path | Status | Description |
|------|--------|-------------|
| `architecture/sms/SMS-VOLUME-I_5-CORE-SEMANTICS.md` | Active | Volume I — Core semantics |
| `architecture/sms/SMS-VOLUME-II-WORLD-MODEL-CONTRACTS.md` | Active | Volume II — World model contracts |
| `architecture/sms/SMS-VOLUME-II-WORLD-MODEL.md` | Active | Volume II — World model |

### ADRs — Architecture Decision Records

| Path | Status | Description |
|------|--------|-------------|
| `architecture/adr/ADR-004-UNIVERSAL-OBJECT-CONTRACT.md` | Active | Universal object contract |
| `architecture/adr/ADR-005-SHUNYA-UNIVERSAL-IDENTITY.md` | Active | Shunya universal identity |
| `architecture/adr/ADR-006-SPACE-ARCHITECTURE.md` | Active | Space architecture |
| `architecture/adr/ADR-007-RELATIONSHIP-CONTRACT.md` | Active | Relationship contract |

---

## 5. Governance

Location: `governance/`

### Core Governance Documents

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `governance/README.md` | Overview | Active | Governance directory overview |
| `governance/SHUNYA_ENGINEERING_CONSTITUTION.md` | Constitution | Active | Engineering constitution |
| `governance/SHUNYA_GOVERNANCE_MODEL.md` | Model | Active | Governance model specification |
| `governance/GOVERNANCE_CHANGELOG.md` | Changelog | Active | Governance change log |

### Governance Freeze 01 (4 docs)

| Path | Status | Description |
|------|--------|-------------|
| `governance/GOVERNANCE_FREEZE_01_REPORT.md` | Complete | Freeze 01 report |
| `governance/GOVERNANCE_FREEZE_01_CONFLICT_RESOLUTION.md` | Complete | Freeze 01 conflict resolution |
| `governance/GOVERNANCE_FREEZE_01_XREF_REPORT.md` | Complete | Freeze 01 cross-reference report |
| `governance/GOVERNANCE_FREEZE_01_RATIFICATION_PACKAGE.md` | Complete | Freeze 01 ratification package |

### Governance ADRs

| Path | Status | Description |
|------|--------|-------------|
| `governance/adr/README.md` | Active | ADR directory overview |
| `governance/adr/ADR_TEMPLATE.md` | Active | ADR template |
| `governance/adr/ADR-001-EVENT-BUS-STANDARD.md` | Active | Event bus standard |
| `governance/adr/ADR-002-KNOWLEDGE-STORE-TRANSITION.md` | Active | Knowledge store transition |
| `governance/adr/ADR-003-CREDENTIAL-STORE-STANDARD.md` | Active | Credential store standard |

### Approvals

| Path | Status | Description |
|------|--------|-------------|
| `governance/approvals/README.md` | Active | Approvals directory overview |
| `governance/approvals/ENGINE_APPROVAL_TEMPLATE.md` | Active | Engine approval template |
| `governance/approvals/PHASE_APPROVAL_TEMPLATE.md` | Active | Phase approval template |

### Engine Specifications (ES-001 through ES-010)

| Path | Status | Description |
|------|--------|-------------|
| `governance/engine_specs/README.md` | Active | Engine specs directory overview |
| `governance/engine_specs/ENGINE_SPEC_TEMPLATE.md` | Active | Engine spec template |
| `governance/engine_specs/ES-001-GOVERNANCE-ENGINE.md` | Active | Governance engine spec |
| `governance/engine_specs/ES-001-ENGINEERING-SUMMARY.md` | Active | ES-001 engineering summary |
| `governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md` | Active | Knowledge engine spec |
| `governance/engine_specs/ES-002-ENGINEERING-SUMMARY.md` | Active | ES-002 engineering summary |
| `governance/engine_specs/ES-003-REASONING-ENGINE.md` | Active | Reasoning engine spec |
| `governance/engine_specs/ES-003-ENGINEERING-SUMMARY.md` | Active | ES-003 engineering summary |
| `governance/engine_specs/ES-004-PLANNER-ENGINE.md` | Active | Planner engine spec |
| `governance/engine_specs/ES-004-ENGINEERING-SUMMARY.md` | Active | ES-004 engineering summary |
| `governance/engine_specs/ES-005-EXECUTOR-ENGINE.md` | Active | Executor engine spec |
| `governance/engine_specs/ES-005-ENGINEERING-SUMMARY.md` | Active | ES-005 engineering summary |
| `governance/engine_specs/ES-006-OBSERVER-ENGINE.md` | Active | Observer engine spec |
| `governance/engine_specs/ES-006-ENGINEERING-SUMMARY.md` | Active | ES-006 engineering summary |
| `governance/engine_specs/ES-007-LEARNING-ENGINE.md` | Active | Learning engine spec |
| `governance/engine_specs/ES-007-ENGINEERING-SUMMARY.md` | Active | ES-007 engineering summary |
| `governance/engine_specs/ES-008-DOCTOR-ENGINE.md` | Active | Doctor engine spec |
| `governance/engine_specs/ES-009-CONTEXT-FUSION-ENGINE.md` | Active | Context fusion engine spec |
| `governance/engine_specs/ES-010-IDENTITY-ENGINE.md` | Active | Identity engine spec |

### Verification

| Path | Status | Description |
|------|--------|-------------|
| `governance/verification/README.md` | Active | Verification directory overview |
| `governance/verification/VERIFICATION_CHECKLIST.md` | Active | Verification checklist |

### External Governance Documents

| Path | Status | Description |
|------|--------|-------------|
| `governance/archive-index.md` | Active | Archive index |
| `governance/constitutional-amendment-procedure.md` | Active | Constitutional amendment procedure |
| `governance/constitutional-compliance-checklist.md` | Active | Constitutional compliance checklist |
| `governance/constitutional-traceability-matrix.md` | Active | Constitutional traceability matrix |
| `governance/founder-ratification-package.md` | Active | Founder ratification package |

---

## 6. Core Runtimes

Location: `core/`

| Directory/File | Type | Status | Description |
|----------------|------|--------|-------------|
| `core/os.py` | Runtime | Active | Shunya OS core — main operating system entry point |
| `core/kernel_runtime.py` | Runtime | Active | Kernel runtime — core system kernel |
| `core/identity_runtime.py` | Runtime | Active | Identity runtime — identity management |
| `core/__init__.py` | Package | Active | Core package initialization |
| `core/automation_runtime/` | Runtime | Active | Automation runtime — automated workflows |
| `core/cognitive_runtime/` | Runtime | Active | Cognitive runtime — cognitive processing |
| `core/event/` | Runtime | Active | Event engine — event bus and event processing |
| `core/evidence/` | Runtime | Active | Evidence engine — evidence tracking and provenance |
| `core/execution_runtime/` | Runtime | Active | Execution runtime — task execution |
| `core/identity/` | Runtime | Active | Identity subsystem — identity store, engine, models |
| `core/integration_runtime/` | Runtime | Active | Integration runtime — external system integration |
| `core/intelligence/` | Engine | Active | Intelligence engine — perception, reasoning, planning, learning, confidence, context assembly, decision, reflection |
| `core/kernel/` | Runtime | Active | Kernel — types, objects, core abstractions |
| `core/memory_knowledge_runtime/` | Runtime | Active | Memory/knowledge runtime — storage and retrieval |
| `core/planning_runtime/` | Runtime | Active | Planning runtime — planning and scheduling |
| `core/projection/` | Runtime | Active | Projection engine — future projection, resolution, cache |
| `core/registry/` | Runtime | Active | Registry — module and service registry |
| `core/relationship/` | Runtime | Active | Relationship engine — entity relationships |
| `core/runtime/` | Runtime | Active | Base runtime — runtime engine, models |
| `core/runtime_pipeline/` | Pipeline | Active | Runtime pipeline — pipeline execution |
| `core/search/` | Runtime | Active | Search runtime — search functionality |
| `core/storage/` | Runtime | Active | Storage runtime — data persistence |
| `core/timeline/` | Runtime | Active | Timeline engine — temporal event tracking |
| `core/validation/` | Runtime | Active | Validation engine — validation and verification |
| `core/workspace_runtime/` | Runtime | Active | Workspace runtime — workspace management |
| `core/audit/` | Runtime | Active | Audit runtime — auditing and logging |

---

## 7. Documentation

Location: `docs/`

### Canons (34 docs)

| Path | Status | Description |
|------|--------|-------------|
| `docs/canon/INDEX.md` | Active | Canon index |
| `docs/canon/OS_CONSTITUTION.md` | Active | OS constitution canon |
| `docs/canon/00_universal_ontology.md` | Active | Universal ontology canon |
| `docs/canon/01_shunya_vision.md` | Active | Shunya vision canon |
| `docs/canon/02_shunya_constitution.md` | Active | Shunya constitution canon |
| `docs/canon/03_business_canon.md` | Active | Business canon |
| `docs/canon/04_universal_object_protocol.md` | Active | Universal object protocol canon |
| `docs/canon/05_runtime_canon.md` | Active | Runtime canon |
| `docs/canon/06_data_canon.md` | Active | Data canon |
| `docs/canon/07_ai_canon.md` | Active | AI canon |
| `docs/canon/08_experience_canon.md` | Active | Experience canon |
| `docs/canon/09_repository_canon.md` | Active | Repository canon |
| `docs/canon/10_migration_canon.md` | Active | Migration canon |
| `docs/canon/11_engineering_canon.md` | Active | Engineering canon |
| `docs/canon/12_launch_roadmap.md` | Active | Launch roadmap canon |
| `docs/canon/CAPABILITY_MATRIX.md` | Active | Capability matrix |
| `docs/canon/CONVERGENCE_PLAN.md` | Active | Convergence plan |
| `docs/canon/FOUNDER_JOURNEY.md` | Active | Founder journey |
| `docs/canon/INTEGRATION_ROADMAP.md` | Active | Integration roadmap |
| `docs/canon/MASTER_EXECUTION_ROADMAP_v1.0.md` | Active | Master execution roadmap v1.0 |
| `docs/canon/MIGRATION_STRATEGY.md` | Active | Migration strategy |
| `docs/canon/UNIVERSAL_OBJECT_MODEL.md` | Active | Universal object model |
| `docs/canon/AUTOMATION_EVENT_RUNTIME_CANON.md` | Active | Automation/event runtime canon |
| `docs/canon/COGNITIVE_RUNTIME_CANON.md` | Active | Cognitive runtime canon |
| `docs/canon/EXECUTION_GOVERNANCE.md` | Active | Execution governance canon |
| `docs/canon/EXECUTION_RUNTIME_CANON.md` | Active | Execution runtime canon |
| `docs/canon/EXECUTION_STATE_SEMANTICS.md` | Active | Execution state semantics canon |
| `docs/canon/INTEGRATION_RUNTIME_CANON.md` | Active | Integration runtime canon |
| `docs/canon/INTELLIGENCE_RUNTIME_CANON.md` | Active | Intelligence runtime canon |
| `docs/canon/MEMORY_KNOWLEDGE_RUNTIME_CANON.md` | Active | Memory/knowledge runtime canon |
| `docs/canon/PLANNING_RUNTIME_CANON.md` | Active | Planning runtime canon |
| `docs/canon/PROJECTION_ENGINE_CANON.md` | Active | Projection engine canon |
| `docs/canon/C1_COMPLETION_REPORT.md` | Active | C1 completion report |
| `docs/canon/C2_COMPLETION_REPORT.md` | Active | C2 completion report |

### Experience Docs (19 docs + README)

| Path | Status | Description |
|------|--------|-------------|
| `docs/experience/19_workspace_runtime.md` | Active | Workspace runtime experience doc |

### Frontend Docs

| Path | Status | Description |
|------|--------|-------------|
| `docs/frontend/COMPONENT_SPECIFICATION.md` | Active | Component specification |
| `docs/frontend/DESIGN_SYSTEM.md` | Active | Design system documentation |
| `docs/frontend/DESKTOP_INTERACTION_MODEL.md` | Active | Desktop interaction model |
| `docs/frontend/MOBILE_INTERACTION_MODEL.md` | Active | Mobile interaction model |
| `docs/frontend/INFORMATION_ARCHITECTURE.md` | Active | Information architecture |

### Architecture Docs

| Path | Status | Description |
|------|--------|-------------|
| `docs/architecture/FRONTEND_EXECUTION_CONSTITUTION.md` | Active | Frontend execution constitution |
| `docs/architecture/FRONTEND_EXECUTION_CONSTITUTION_PHASE2.md` | Active | Frontend execution constitution phase 2 |
| `docs/architecture/CONSTITUTIONAL_PLATFORM_MAP.md` | Active | Constitutional platform map |
| `docs/architecture/SHUNYA_PRODUCTION_ARCHITECTURE.md` | Active | Production architecture |

### Governance Docs

| Path | Status | Description |
|------|--------|-------------|
| `docs/governance/CONSTITUTION_v1.0.md` | Active | Constitution v1.0 |
| `docs/governance/CA-1_CONSTITUTIONAL_COMPLIANCE_AUDIT.md` | Active | Constitution compliance audit CA-1 |
| `docs/governance/CANONICAL_IDENTITY_DECISION.md` | Active | Canonical identity decision |
| `docs/governance/CANONICAL_PRODUCT_DECLARATION.md` | Active | Canonical product declaration |
| `docs/governance/CONSTITUTION_COMPLIANCE_REPORT.md` | Active | Constitution compliance report |
| `docs/governance/CONVERGENCE_PLAN.md` | Active | Convergence plan |
| `docs/governance/IDENTITY_DEPENDENCY_INVERSION.md` | Active | Identity dependency inversion |
| `docs/governance/IDENTITY_MODEL_CONSOLIDATION.md` | Active | Identity model consolidation |
| `docs/governance/REPOSITORY_AUDIT_REPORT.md` | Active | Repository audit report |

### Phase Reports

| Path | Status | Description |
|------|--------|-------------|
| `docs/reports/PHASE_C2_FINAL_VERIFICATION.md` | Active | Phase C2 final verification |
| `docs/reports/PHASE_C3_EXECUTION_REPORT.md` | Active | Phase C3 execution report |
| `docs/reports/PHASE_D_IMPLEMENTATION_REPORT.md` | Active | Phase D implementation report |
| `docs/reports/PHASE_D_CLOSURE_AUDIT.md` | Active | Phase D closure audit |
| `docs/reports/PHASE_D_AUTHORITATIVE_CLOSURE.md` | Active | Phase D authoritative closure |
| `docs/reports/PHASE_E_IMPLEMENTATION_REPORT.md` | Active | Phase E implementation report |
| `docs/reports/PHASE_F_EXECUTION_RUNTIME_REPORT.md` | Active | Phase F execution runtime report |
| `docs/reports/PHASE_G_INTEGRATION_RUNTIME_REPORT.md` | Active | Phase G integration runtime report |
| `docs/reports/PHASE_H_MEMORY_KNOWLEDGE_RUNTIME_REPORT.md` | Active | Phase H memory/knowledge runtime report |
| `docs/reports/PHASE_I_PLANNING_RUNTIME_REPORT.md` | Active | Phase I planning runtime report |
| `docs/reports/PHASE_J_AUTOMATION_EVENT_RUNTIME_REPORT.md` | Active | Phase J automation/event runtime report |
| `docs/reports/PHASE_K_PROJECTION_ENGINE_REPORT.md` | Active | Phase K projection engine report |
| `docs/reports/PHASE_L_CONVERGENCE_REPORT.md` | Active | Phase L convergence report |
| `docs/reports/PHASE_X4_WORKSPACE_RUNTIME_REPORT.md` | Active | Phase X4 workspace runtime report |
| `docs/reports/CURRENT_CAPABILITY_AUDIT.md` | Active | Current capability audit |
| `docs/reports/SHUNYA_SYSTEM_AUDIT_v1.0.md` | Active | System audit v1.0 |
| `docs/reports/FOUNDATION_ARCHITECTURAL_READINESS_REVIEW.md` | Active | Foundation architectural readiness review |
| `docs/reports/E-003-EPIC-CLOSURE-REPORT.md` | Active | E-003 epic closure report |

### Ops / Plans / Presentation

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `docs/ops/DEPLOYMENT_GUIDE.md` | Ops | Active | Deployment guide |
| `docs/ops/LAUNCH_DASHBOARD.md` | Ops | Active | Launch dashboard |
| `docs/plans/CORE_CONSOLIDATION_PLAN.md` | Plan | Active | Core consolidation plan |
| `docs/presentation/EXPERIENCE_BIBLE.md` | Presentation | Active | Experience bible |
| `docs/presentation/EXPERIENCE_CONSTITUTION_v2.md` | Presentation | Active | Experience constitution v2 |
| `docs/presentation/EXPERIENCE_CONSTITUTION_v3.md` | Presentation | Active | Experience constitution v3 |
| `docs/presentation/FOUNDER_DEMO_SCRIPT.md` | Presentation | Active | Founder demo script |

### Other Docs

| Path | Status | Description |
|------|--------|-------------|
| `docs/CANONICAL_SPEC.md` | Active | Canonical specification |
| `docs/DEVIATION_LIST.md` | Active | Deviation list |
| `docs/E-002-engineering-progress-report.md` | Active | E-002 engineering progress report |
| `docs/E-003-MOD-001-progress-report.md` | Active | E-003 MOD-001 progress report |
| `docs/E-003-MOD-002-progress-report.md` | Active | E-003 MOD-002 progress report |
| `docs/E-003-MOD-003-progress-report.md` | Active | E-003 MOD-003 progress report |
| `docs/E-003-MOD-004-progress-report.md` | Active | E-003 MOD-004 progress report |
| `docs/E-003-MOD-005-progress-report.md` | Active | E-003 MOD-005 progress report |
| `docs/E-003-MOD-005-architecture-clarification.md` | Active | E-003 MOD-005 architecture clarification |
| `docs/E-004-MOD-001-progress-report.md` | Active | E-004 MOD-001 progress report |
| `docs/E-004-MOD-002-progress-report.md` | Active | E-004 MOD-002 progress report |
| `docs/GKF-000-PHASE-2-progress-report.md` | Active | GKF-000 phase 2 progress report |
| `docs/GKF-001A-progress-report.md` | Active | GKF-001A progress report |

---

## 8. Design

Location: `design/`

### Experience Design Canons (18 canons + README)

| Path | Status | Description |
|------|--------|-------------|
| `design/experience/README.md` | Active | Experience design overview |
| `design/experience/01_experience_philosophy.md` | Active | Experience philosophy |
| `design/experience/02_information_architecture.md` | Active | Information architecture |
| `design/experience/03_workspace_model.md` | Active | Workspace model |
| `design/experience/04_navigation_canon.md` | Active | Navigation canon |
| `design/experience/05_object_workspace.md` | Active | Object workspace |
| `design/experience/06_ai_collaboration.md` | Active | AI collaboration |
| `design/experience/07_component_system.md` | Active | Component system |
| `design/experience/08_motion_system.md` | Active | Motion system |
| `design/experience/09_design_system.md` | Active | Design system |
| `design/experience/10_mobile_canon.md` | Active | Mobile canon |
| `design/experience/11_accessibility.md` | Active | Accessibility |
| `design/experience/12_frontend_engineering.md` | Active | Frontend engineering |
| `design/experience/13_presence_canon.md` | Active | Presence canon |
| `design/experience/14_human_principles.md` | Active | Human principles |
| `design/experience/15_interaction_language.md` | Active | Interaction language |
| `design/experience/16_design_system_foundation.md` | Active | Design system foundation |
| `design/experience/17_interaction_pattern_library.md` | Active | Interaction pattern library |
| `design/experience/18_frontend_foundation.md` | Active | Frontend foundation |

### Visual Design Bible (5 volumes + README)

| Path | Status | Description |
|------|--------|-------------|
| `design/visual-design-bible/README.md` | Active | Visual design bible overview |
| `design/visual-design-bible/1-visual-design-bible.md` | Active | Volume 1 — Visual design bible |
| `design/visual-design-bible/2-design-tokens.md` | Active | Volume 2 — Design tokens |
| `design/visual-design-bible/3-component-specification.md` | Active | Volume 3 — Component specification |
| `design/visual-design-bible/4-component-inventory.md` | Active | Volume 4 — Component inventory |
| `design/visual-design-bible/5-brand-identity-rules.md` | Active | Volume 5 — Brand identity rules |

### Living Notebook

| Path | Status | Description |
|------|--------|-------------|
| `design/living-notebook.md` | Active | Living design notebook |

---

## 9. Knowledge & Decisions

### Knowledge Base

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `knowledge/README.md` | Overview | Active | Knowledge directory overview |
| `knowledge/ai/INTELLIGENCE_CORE_ROADMAP.md` | Roadmap | Active | Intelligence core roadmap |

### Decisions

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `decisions/E-004-EVIDENCE-ARCHITECTURE.md` | ADR | Active | Evidence architecture decision E-004 |

---

## 10. Implementation Phases

### Root-level Phase Documents

| Path | Type | Status | Description |
|------|------|--------|-------------|
| `implementation/PHASE_01_FOUNDATION.md` | Foundation | Active | Phase 01 foundation plan |

### Static Reports

| Path | Status | Description |
|------|--------|-------------|
| `static/FAA-01-AUDIT-REPORT.md` | Active | FAA-01 audit report |
| `static/FAA-01B-REPORT.md` | Active | FAA-01B report |
| `static/SEC-01-CONVERGENCE-REPORT.md` | Active | SEC-01 convergence report |

---

## 11. Frontend

Location: `frontend/`

### Build & Config

| Path | Type | Description |
|------|------|-------------|
| `frontend/package.json` | Config | NPM package configuration |
| `frontend/package-lock.json` | Config | NPM lock file |
| `frontend/tsconfig.json` | Config | TypeScript configuration |
| `frontend/.eslintrc.json` | Config | ESLint configuration |
| `frontend/vite.config.ts` | Config | Vite build configuration |
| `frontend/next.config.ts` | Config | Next.js configuration |
| `frontend/index.html` | Entry | HTML entry point |
| `frontend/dist/` | Build | Compiled/built output |

### TypeScript Components (16 TSX files)

| Path | Description |
|------|-------------|
| `frontend/src/main.tsx` | Application entry point |
| `frontend/src/app.tsx` | Main app component |
| `frontend/src/components/public/homepage.tsx` | Public homepage |
| `frontend/src/components/auth/login-page.tsx` | Login page |
| `frontend/src/components/copilot/ai-copilot.tsx` | AI copilot component |
| `frontend/src/components/commitment/commitment-workspace.tsx` | Commitment workspace |
| `frontend/src/components/conversation/conversation-workspace.tsx` | Conversation workspace |
| `frontend/src/components/dev/runtime-console.tsx` | Runtime console (dev) |
| `frontend/src/components/executive/index.tsx` | Executive dashboard |
| `frontend/src/components/search/universal-search.tsx` | Universal search |
| `frontend/src/components/workspace/workspace-container.tsx` | Workspace container |
| `frontend/src/components/workspace/workspace-shell.tsx` | Workspace shell |
| `frontend/src/components/workspace/workspace-bar.tsx` | Workspace bar |
| `frontend/src/components/workspace/home-workspace.tsx` | Home workspace |
| `frontend/src/components/workspace/context-panel.tsx` | Context panel |
| `frontend/src/tokens/token-provider.tsx` | Design token provider |

### Frontend Runtimes (TypeScript)

| Path | Description |
|------|-------------|
| `frontend/src/runtimes/orchestrator.ts` | Runtime orchestrator |
| `frontend/src/runtimes/registration.ts` | Runtime registration |
| `frontend/src/runtimes/state-fabric.ts` | State fabric |
| `frontend/src/runtimes/event-bus.ts` | Event bus |
| `frontend/src/runtimes/module-registry.ts` | Module registry |
| `frontend/src/runtimes/composition/engine.ts` | Composition engine |
| `frontend/src/runtimes/conversation/engine.ts` | Conversation engine |
| `frontend/src/runtimes/commitment/engine.ts` | Commitment engine |
| `frontend/src/runtimes/experience/engine.ts` | Experience engine |
| `frontend/src/runtimes/graph/engine.ts` | Graph engine |
| `frontend/src/runtimes/intelligence/engine.ts` | Intelligence engine |
| `frontend/src/runtimes/layout/engine.ts` | Layout engine |
| `frontend/src/runtimes/object/engine.ts` | Object engine |
| `frontend/src/runtimes/timeline/engine.ts` | Timeline engine |
| `frontend/src/runtimes/modules/business.ts` | Business module |
| `frontend/src/runtimes/workspace/store.ts` | Workspace store |
| `frontend/src/runtimes/workspace/types.ts` | Workspace types |

### Frontend Hooks & API

| Path | Description |
|------|-------------|
| `frontend/src/hooks/runtime-hooks.ts` | Runtime React hooks |
| `frontend/src/hooks/workspace-hooks.ts` | Workspace React hooks |
| `frontend/src/api/client.ts` | API client |
| `frontend/src/api/session.ts` | Session API |

### Frontend Tokens & Types

| Path | Description |
|------|-------------|
| `frontend/src/tokens/definitions.ts` | Design token definitions |
| `frontend/src/types/index.ts` | TypeScript type definitions |
| `frontend/src/lib/event-bus.ts` | Event bus library |
| `frontend/src/lib/component-registry.ts` | Component registry library |
| `frontend/src/data/objects.ts` | Object data definitions |

---

## 12. Backend (Flask App)

Location: `app/`

### Core Application

| Module | Files | Description |
|--------|-------|-------------|
| `app/__init__.py` | 1 | App factory and initialization |
| `app/routes.py` | 1 | Main route definitions |
| `app/models.py` | 1 | Core data models |
| `app/auth.py` | 1 | Authentication |
| `app/auth_routes.py` | 1 | Auth route definitions |
| `app/services.py` | 1 | Service layer |
| `app/tasks.py` | 1 | Background task definitions |
| `app/search.py` | 1 | Search functionality |
| `app/cache.py` | 1 | Caching layer |
| `app/monitoring.py` | 1 | System monitoring |
| `app/ontology.py` | 1 | Ontology definitions |
| `app/app.py` | 1 | Application alias |

### Domain Modules

| Module | Files | Description |
|--------|-------|-------------|
| `app/adapters/` | 5 | External adapters (gmail, whatsapp, os) |
| `app/assistant/` | 1 | Assistant module |
| `app/artifact/` | 1 | Artifact management |
| `app/authz/` | 4 | Authorization (routes, services, models) |
| `app/automation/` | 1 | Automation engine |
| `app/awareness/` | 3 | Awareness engine (engine, models) |
| `app/brand/` | 1 | Brand management |
| `app/cognitive/` | 3 | Cognitive engine (engine, models) |
| `app/collaboration/` | 3 | Collaboration (engine, models) |
| `app/communication/` | 7 | Communication (adapter, credentials, policy, models, oauth, ingestion, normalizer) |
| `app/context/` | 1 | Context management |
| `app/cortex/` | 5 | Cortex (runtime, state, health, brief, attention) |
| `app/decision/` | 2 | Decision engine (engine, models) |
| `app/decision_runtime/` | 6 | Decision runtime (runtime, policy, outcome, models, commitment, learning) |
| `app/document/` | 2 | Document management (models) |
| `app/evidence/` | 6 | Evidence (models, enums, values, provenance) |
| `app/execution/` | 1 | Execution management |
| `app/execution_intelligence/` | 3 | Execution intelligence (engine, models) |
| `app/executive/` | 3 | Executive dashboard (engine, models) |
| `app/finance/` | 8 | Finance (routes, intelligence, evidence, controls, governance, services, models, accounting) |
| `app/for1/` | 4 | FOR1 module (routes, engine, models) |
| `app/for2/` | 3 | FOR2 module (routes, models) |
| `app/founder/` | 3 | Founder (routes, models) |
| `app/gkf/` | 4 | Governed Knowledge Framework (models, enums, identity) |
| `app/graph/` | 6 | Graph (node, edge, families, temporal, security, consistency) |
| `app/graph_universal/` | 7 | Universal graph (entity, relationship, identity, property, event, traversal, runtime) |
| `app/growth/` | 1 | Growth module |
| `app/human_context/` | 2 | Human context (models) |
| `app/inference/` | 1 | Inference engine |
| `app/intake/` | 6 | Intake (session, proposal, matcher, validator, committer, profiler, mapper) |
| `app/intelligence/` | 8 | Intelligence (runtime, reasoning, provenance, insight, observation, inspector, confidence, scenario) |
| `app/kernel/` | 8 | Kernel (state, types, timeline, identity, object, context, relationship, space, identity_governance) |
| `app/knowledge/` | 1 | Knowledge management |
| `app/learning/` | 1 | Learning module |
| `app/learning_intelligence/` | 3 | Learning intelligence (engine, models) |
| `app/llm/` | 2 | LLM integration (models) |
| `app/media/` | 1 | Media handling |
| `app/memory/` | 2 | Memory (models) |
| `app/notifications/` | 1 | Notifications |
| `app/onboarding/` | 3 | Onboarding (routes, engine) |
| `app/orchestration/` | 6 | Orchestration (runtime, sync, signal, cycle, queue) |
| `app/orchestrator/` | 3 | Orchestrator (engine, models) |
| `app/organization/` | 5 | Organization (runtime, actor, coordination, responsibility, escalation) |
| `app/organizational/` | 3 | Organizational (engine, models) |
| `app/payment_gateway.py` | 1 | Payment gateway |
| `app/planning/` | 6 | Planning (runtime, plan, objective, checkpoint, dependency) |
| `app/prediction/` | 3 | Prediction (engine, models) |
| `app/privacy/` | 2 | Privacy (models) |
| `app/production/` | 10 | Production (identity routes, auth, session, MFA, email verification) |
| `app/relationship/` | 8 | Relationship (routes, services, models, search, integration, lead_association) |
| `app/relevance/` | 1 | Relevance engine |
| `app/runtime/` | 1 | Runtime module |
| `app/shunya/` | 30+ | Shunya core (reasoning, planning, learning, observer, knowledge, executor, governance, context, identity, infrastructure, config, di, doctor, etc.) |
| `app/space/` | 16 | Space (runtime, routes, models, store, timeline, resident, renderer, relationships, reasoning, navigation, knowledge, lifecycle, composition, context, commands, capabilities) |
| `app/temporal/` | 7 | Temporal (timeline, runtime, trajectory, snapshot, trend, forecast) |
| `app/tenant.py` | 1 | Tenant management |
| `app/voice.py` | 1 | Voice/audio |
| `app/watch/` | 1 | Watch module |
| `app/web_intel.py` | 1 | Web intelligence |
| `app/workspace/` | 3 | Workspace (routes, models) |
| `app/workspace_routes.py` | 1 | Workspace routing |
| `app/workspace_runtime.py` | 1 | Workspace runtime |
| `app/whatsapp_webhook.py` | 1 | WhatsApp webhook handler |

### Additional Modules

| Module | Files | Description |
|--------|-------|-------------|
| `app/approval.py` | 1 | Approval workflows |
| `app/calendar_service.py` | 1 | Calendar integration |
| `app/celery_worker.py` | 1 | Celery task worker |
| `app/celebrations.py` | 1 | Celebrations/events |
| `app/client_portal.py` | 1 | Client portal |
| `app/coach.py` | 1 | Coaching module |
| `app/companion.py` | 1 | Companion module |
| `app/creative.py` | 1 | Creative generation |
| `app/document_reader.py` | 1 | Document reading |
| `app/dynamic_fields.py` | 1 | Dynamic fields |
| `app/language.py` | 1 | Language processing |
| `app/module_builder.py` | 1 | Module builder |
| `app/shunya_public.py` | 1 | Public Shunya API |

### Templates

| Path | Files | Description |
|------|-------|-------------|
| `templates/` | 30+ | Jinja2 HTML templates for workspace, auth, finance, CRM, etc. |
| `app/for1/templates/` | 3 | FOR1 proposal templates |
| `app/for2/templates/` | 2 | FOR2 workspace templates |
| `app/relationship/templates/` | 2 | Relationship workspace templates |

### CSS & Static Assets

| Path | Description |
|------|-------------|
| `static/css/app.css` | Main application styles |
| `static/css/design-system.css` | Design system styles |
| `static/css/auth.css` | Authentication styles |
| `static/css/workspace.css` | Workspace styles |
| `static/css/founder-workspace.css` | Founder workspace styles |
| `static/img/industry-icons.svg` | Industry icons SVG |
| `static/img/artwork-hero.svg` | Hero artwork SVG |

### Infrastructure

| Path | Files | Description |
|------|-------|-------------|
| `infrastructure/docs/` | 6 | Deployment, recovery, rollback, verification, environments, production config |
| `infrastructure/environments/` | 4 | Development, testing, production env configs + README |
| `infrastructure/scripts/` | 3 | Deploy, recover, rollback scripts |
| `infrastructure/nginx/` | 2 | Production and development nginx configs |

### Migrations

| Path | Description |
|------|-------------|
| `migrations/env.py` | Alembic migration environment |
| `migrations/script.py.mako` | Migration template |
| `migrations/README` | Migration instructions |
| `migrations/0002_schema_reconciliation.py` | Schema reconciliation migration |
| `migrations/phase1_migration.py` | Phase 1 migration |

### Scripts

| Path | Description |
|------|-------------|
| `scripts/seed_demo.py` | Demo data seeding |
| `scripts/init_alembic.py` | Alembic initialization |
| `scripts/repo-health-check.sh` | Repository health check |

---

## 13. Tests

Location: `tests/` (137+ test files)

### Test Categories

| Directory | Files | Description |
|-----------|-------|-------------|
| `tests/` | 40+ | Root-level tests (phase tests, models, routes, reasoning, planning, etc.) |
| `tests/conftest.py` | 1 | Shared test fixtures |
| `tests/adapters/` | 1 | OS adapter tests |
| `tests/automation_runtime/` | 1 | Automation runtime tests |
| `tests/awareness/` | 2 | Awareness engine tests |
| `tests/cognitive/` | 2 | Cognitive engine tests |
| `tests/cognitive_runtime/` | 1 | Cognitive runtime tests |
| `tests/collaboration/` | 2 | Collaboration tests |
| `tests/core/` | 2 | Core runtime and evidence engine tests |
| `tests/cortex/` | 1 | Cortex tests |
| `tests/decision/` | 3 | Decision engine and runtime tests |
| `tests/engines/` | 10+ | Engine tests (reasoning, relationship, planner, learning, observer, governance, knowledge, executor, context fusion, identity, knowledge store) |
| `tests/evidence/` | 2 | Evidence and provenance tests |
| `tests/execution_intelligence/` | 2 | Execution intelligence tests |
| `tests/execution_runtime/` | 2 | Execution runtime and governance tests |
| `tests/executive/` | 2 | Executive tests |
| `tests/gkf/` | 3 | Governed Knowledge Framework tests |
| `tests/graph/` | 6 | Graph tests (node, edge, families, temporal, consistency, security) |
| `tests/graph_universal/` | 1 | Universal graph tests |
| `tests/infrastructure/` | 8 | Infrastructure tests (config, event_bus, persistence, health, metrics, logging, credential_store, di) |
| `tests/integration_runtime/` | 1 | Integration runtime tests |
| `tests/intelligence/` | 3 | Intelligence tests (perception/context, learning/confidence, explainability) |
| `tests/kernel/` | 4 | Kernel tests (core kernel, identity governance, ontology engine) |
| `tests/learning_intelligence/` | 2 | Learning intelligence tests |
| `tests/memory_knowledge_runtime/` | 1 | Memory/knowledge runtime tests |
| `tests/orchestration/` | 1 | Orchestration tests |
| `tests/orchestrator/` | 2 | Orchestrator tests |
| `tests/organization/` | 1 | Organization tests |
| `tests/organizational/` | 2 | Organizational tests |
| `tests/planning/` | 1 | Planning tests |
| `tests/planning_runtime/` | 1 | Planning runtime tests |
| `tests/prediction/` | 2 | Prediction tests |
| `tests/production/` | 6 | Production tests (identity, auth, authorization) |
| `tests/projection/` | 1 | Projection tests |
| `tests/runtime_pipeline/` | 3 | Runtime pipeline tests (identity, kernel, pipeline) |
| `tests/space/` | 2 | Space tests |
| `tests/temporal/` | 1 | Temporal tests |
| `tests/workspace_runtime/` | 1 | Workspace runtime tests |

---

## A. Archive

| Path | Description |
|------|-------------|
| `archive/legacy/templates/` | 20 legacy Jinja2 templates (deprecated) |
| `archive/legacy/static_css/` | Legacy landing CSS |
| `archive/hero-v1/` | V1 hero artwork and CSS |

## B. Hermes Agent Configuration

| Path | Description |
|------|-------------|
| `.hermes/plans/SEC-01-CONVERGENCE-REPORT.md` | Hermes agent convergence report plan |
| `.hermes/plans/FAA-01B-REPORT.md` | Hermes agent FAA-01B report plan |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Root `.md` documents | 38 |
| Phase implementation documents | 20+ |
| Constitutional documents | 6 |
| Architecture documents | 30+ |
| Architecture ADRs | 4 |
| Governance documents | 25+ |
| Engine specifications | 10 |
| Governance ADRs | 3 |
| Canon documents | 34 |
| Design experience canons | 19 |
| Visual design bible volumes | 5 |
| Documentation (total `.md` files) | 266 |
| Python modules | 338+ (app) + 91 (core) |
| Test files | 137+ |
| Frontend TypeScript/JS files | 43+ |
| Frontend TSX components | 16 |
| HTML templates | 50+ |
| CSS files | 7 |
| Shell scripts | 4 |
| Infrastructure config files | 15+ |
| SVG illustrations | 4 |