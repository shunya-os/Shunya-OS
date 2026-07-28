# SHUNYA Master Execution Roadmap v1.0

> **Status: GOVERNING — All future implementation work must originate from this roadmap.**
> **Date: 2026-07-25**
> **Classification: Execution Roadmap — Not a specification.**

---

## 1. Roadmap Overview

### 1.1 Mission

Transform SHUNYA from a collection of independently-tested modules into a single, coherent, operational AI Operating System for human organizations, publicly launched as Version 1.0.

### 1.2 Current State

```
Capability maturity:    22% Operational, 66% Implemented, 0% Integrated, 12% Designed
Execution paths:        Fragmented (Flask routes, founder API, direct model queries)
Object models:          5+ parallel representations (FounderObject, UniversalObject,
                        MemoryObject, Graph Node, Flask models)
Frontend-backend:       0% connected (Next.js uses hardcoded demo data)
AI pipeline:            0% wired (scenario-based demo responses only)
Core runtimes wired:    0 of 16 (all behind MockRuntime in pipeline)
Total tests:            ~4,364 passing
```

### 1.3 Remaining Directive Count

| Milestone | Directives | Est. complexity | Founder preview |
|-----------|-----------|-----------------|-----------------|
| L — OS Convergence | 4 | High | FP1 |
| M — Living Workspace | 4 | High | FP2 |
| N — Connected Business | 3 | High | FP3 |
| O — Executive Intelligence | 4 | Very High | FP4 |
| P — Enterprise Platform | 3 | Very High | FP5 |
| Q — Production Infrastructure | 2 | Medium | — |
| R — Security & Compliance | 2 | Medium | — |
| S — Founder Experience | 2 | Medium | FP6 |
| T — Public Launch | 1 | Low | — |
| **Total** | **25** | — | **6 previews** |

---

## 2. Milestone L — Operating System Convergence

### 2.1 Directive L-01: Wire Kernel Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the kernel MockRuntime with the real `core/kernel/` implementation. The kernel handles `intent_resolution` and `object_resolution` pipeline stages. |
| **Why** | The kernel (types, objects, state, space) is the foundation. Every other runtime depends on it. Until it's wired, the pipeline is a simulation. |
| **Dependencies** | Phase L foundation (canonical pipeline, OS kernel) |
| **Deliverables** | `app/adapters/kernel_adapter.py`, `core/os.py` replacement call |
| **Success** | `process_intent("create_object")` creates a UniversalObject in the kernel registry |
| **Founder validation** | Create an object via Flask → OS pipeline → verify it appears in kernel registry |
| **Complexity** | High — requires adapter between Flask session/kernel/DB |

### 2.2 Directive L-02: Wire Identity Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the identity MockRuntime with the real `core/identity/` implementation. Identity handles `identity_resolution`. |
| **Why** | Every action needs an actor. Until identity is wired, the pipeline does not know who is acting. |
| **Dependencies** | L-01 |
| **Deliverables** | `app/adapters/identity_adapter.py`, `core/os.py` replacement call |
| **Success** | `process_intent(identity_id="...")` resolves to a valid SHUNYAIdentity |
| **Founder validation** | Sign in → verify identity appears in pipeline trace |
| **Complexity** | High — existing auth has 3 parallel identity systems to converge |

### 2.3 Directive L-03: Wire Flask Founder Routes Through OS Kernel

| Aspect | Definition |
|--------|-----------|
| **Objective** | Every founder API route (`/api/v1/founder/*`) calls `os.process_intent()` instead of direct model operations. |
| **Why** | This is the first end-to-end user flow through the canonical pipeline. It proves the architecture. |
| **Dependencies** | L-01, L-02 |
| **Deliverables** | Modified `app/founder/routes.py`, Flask route updates |
| **Success** | All founder CRUD flows through pipeline; all existing tests pass |
| **Founder validation** | Create space, create object, open object — verify pipeline trace in logs |
| **Complexity** | High — requires careful strangler fig to avoid breaking existing flows |

### 2.4 Directive L-04: Wire Projection Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the projection MockRuntime with the real `core/projection/`. The projection engine assembles workspace views from pipeline state. |
| **Why** | The projection engine is the bridge between runtime state and what the user sees. Until it's wired, the workspace shows raw data. |
| **Dependencies** | L-03 |
| **Deliverables** | `app/adapters/projection_adapter.py`, `core/os.py` replacement call |
| **Success** | Pipeline produces a `GraphProjection` as output; projection metadata shows `source: "assembled"` |
| **Founder validation** | Open object → projection assembled → verify timing and source in health check |
| **Complexity** | Medium |

### 2.5 Founder Preview 1 — Milestone L

| Aspect | Definition |
|--------|-----------|
| **Purpose** | Demonstrate that the canonical operating system pipeline processes real user actions end-to-end through wired runtimes. |
| **Available capabilities** | Sign in, create space, create object, open object — all flowing through the pipeline |
| **Expected limitations** | Only kernel + identity runtimes wired. Memory, planning, execution, automation still mocked. No AI responses. |
| **Testing workflow** | 1. Start app → 2. Sign in → 3. Create a space → 4. Create an object → 5. Open object → 6. View pipeline health → 7. View pipeline trace |
| **Exit criteria** | Pipeline trace shows `intent_resolution`, `identity_resolution`, `object_resolution`, `projection_assembly` stages with `status: "completed"` |

---

## 3. Milestone M — Living Workspace

### 3.1 Directive M-01: Wire Memory/Knowledge Graph Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the knowledge_graph and memory MockRuntimes with the real `core/memory_knowledge_runtime/`. Handles `knowledge_graph_update` and `memory_update` stages. |
| **Why** | The knowledge graph is the canonical data plane. Memory enables the OS to learn from past interactions. Without both, every action is isolated. |
| **Dependencies** | L-01 (kernel) |
| **Deliverables** | `app/adapters/memory_adapter.py`, `core/os.py` replacement call |
| **Success** | Pipeline updates knowledge graph after object mutation; memory stores interaction |
| **Complexity** | High — memory runtime has 6 layers; adapter must resolve which layer to write |

### 3.2 Directive M-02: Wire Planning Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the planning MockRuntime with the real `core/planning_runtime/`. Handles `planning_update`. |
| **Why** | Planning enables the OS to decompose goals into actionable plans. Without it, SHUNYA cannot commit to follow-up actions. |
| **Dependencies** | L-01, M-01 |
| **Deliverables** | `app/adapters/planning_adapter.py`, `core/os.py` replacement call |
| **Success** | Creating a commitment triggers plan creation in the planning runtime |
| **Complexity** | Medium |

### 3.3 Directive M-03: Connect Next.js Frontend to Live API

| Aspect | Definition |
|--------|-----------|
| **Objective** | Remove hardcoded demo data from `frontend/src/data/objects.ts`. Wire Next.js API layer to Flask OS endpoints. |
| **Why** | The frontend currently shows beautiful but fake data. No amount of backend work matters until the frontend shows real data. |
| **Dependencies** | L-03 (Flask → OS pipeline wired) |
| **Deliverables** | Modified `frontend/src/services/api.ts`, frontend components call real API |
| **Success** | Frontend shows live data from kernel objects, not hardcoded demo |
| **Founder validation** | Create object in backend → refresh frontend → object appears in workspace |
| **Complexity** | High — requires API contract alignment between Flask and Next.js |

### 3.4 Directive M-04: Canonical Workspace Consolidation

| Aspect | Definition |
|--------|-----------|
| **Objective** | Eliminate duplicate workspace implementations. There shall be one canonical workspace: the Next.js SPA rendering projections from the OS pipeline. |
| **Why** | Three workspace implementations exist. Every new feature must target one canonical surface. |
| **Dependencies** | M-03 |
| **Deliverables** | Removal of `templates/founder_workspace.html` duplicates; redirection to Next.js |
| **Success** | All workspace traffic routes through Next.js SPA |
| **Complexity** | Medium |

### 3.5 Founder Preview 2 — Milestone M

| Aspect | Definition |
|--------|-----------|
| **Purpose** | Demonstrate a living workspace that shows real data from the operating system. |
| **Available capabilities** | All L capabilities + live data in frontend, knowledge graph updates, memory storage, plan creation |
| **Expected limitations** | No execution, no automation, no AI reasoning — planning is deterministic only |
| **Testing workflow** | 1. Create object in backend → 2. Refresh frontend → 3. Object appears → 4. View object details → 5. Backend shows memory record of the interaction |
| **Exit criteria** | Frontend displays live OS data; pipeline trace shows knowledge_graph_update + memory_update as "completed" |

---

## 4. Milestone N — Connected Business

### 4.1 Directive N-01: Wire Execution Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the execution MockRuntime with the real `core/execution_runtime/`. Handles `execution_update`. |
| **Why** | Execution transforms intention into action. Without it, SHUNYA can think but cannot do. |
| **Dependencies** | L-01, M-01, M-02 |
| **Deliverables** | `app/adapters/execution_adapter.py`, `core/os.py` replacement call |
| **Success** | An `execute_work` intent creates an ExecutionInstance in the execution runtime with a valid lifecycle |
| **Complexity** | High — execution runtime has 12 states, DAG scheduler, batch, rollback |

### 4.2 Directive N-02: Wire Automation/Event Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the automation MockRuntime with the real `core/automation_runtime/`. Handles `automation_evaluation`. |
| **Why** | Automation enables event-driven behaviour: triggers, rules, workflows. Without it, SHUNYA is purely reactive. |
| **Dependencies** | N-01 |
| **Deliverables** | `app/adapters/automation_adapter.py`, `core/os.py` replacement call |
| **Success** | Executing a commitment fires an event that triggers an automation rule |
| **Complexity** | Medium |

### 4.3 Directive N-03: Wire Integration Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Wire `core/integration_runtime/` as a pipeline consumer. When execution requires external action (email, API call), it delegates to the Integration Runtime. |
| **Why** | SHUNYA must communicate with the outside world. Every external communication must pass through the Integration Runtime — no direct API calls. |
| **Dependencies** | N-01 |
| **Deliverables** | `app/adapters/integration_adapter.py`, integration route registration |
| **Success** | An execution step that requires "send email" delegates to the Integration Runtime and logs the integration trace |
| **Complexity** | High — requires connector configuration, rate limiting, circuit breaker wiring |

### 4.4 Founder Preview 3 — Milestone N

| Aspect | Definition |
|--------|-----------|
| **Purpose** | Demonstrate SHUNYA executing real actions through the pipeline. |
| **Available capabilities** | All L + M capabilities + execution lifecycle, automation triggers, integration connectors |
| **Expected limitations** | No AI reasoning — execution is deterministic. No learning from outcomes. |
| **Testing workflow** | 1. Create a task → 2. Execute it → 3. View execution trace → 4. Verify automation rule fired → 5. Verify integration was called |
| **Exit criteria** | Pipeline trace shows `execution_update`, `automation_evaluation` as "completed" with real runtime output |

---

## 5. Milestone O — Executive Intelligence

### 5.1 Directive O-01: Wire Reasoning Runtime into Pipeline

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace the reasoning MockRuntime with a real inference engine. Handles `reasoning_update`. |
| **Why** | Reasoning enables SHUNYA to infer relationships, detect patterns, evaluate risks, and explain recommendations. Without it, SHUNYA cannot answer "why." |
| **Dependencies** | L-01, M-01 |
| **Deliverables** | `app/adapters/reasoning_adapter.py`, `core/os.py` replacement call |
| **Success** | An `understand_opportunity` intent produces an inference with confidence score and explanation |
| **Complexity** | Very High — requires AI/LLM integration or deterministic rule engine |

### 5.2 Directive O-02: Wire LLM/AI as Inference Provider

| Aspect | Definition |
|--------|-----------|
| **Objective** | Replace scenario-based AI responses with real LLM inference. Wire an AI provider (OpenAI, Anthropic, or local model) through the Reasoning Runtime. |
| **Why** | Current AI responses are hardcoded demo data. Real inference is table-stakes for an AI Operating System. |
| **Dependencies** | O-01 |
| **Deliverables** | `core/inference/provider.py` (LLM abstraction), provider configuration |
| **Success** | Founder converse request returns a human-quality AI response generated by the LLM |
| **Complexity** | Very High — prompt engineering, context window management, streaming, cost control |

### 5.3 Directive O-03: Implement Learning from Outcomes

| Aspect | Definition |
|--------|-----------|
| **Objective** | After an execution completes, the OS updates its knowledge graph and memory with the outcome. Patterns are detected and confidence is adjusted. |
| **Why** | This closes the cognition loop: act → observe → learn. Without it, SHUNYA never improves. |
| **Dependencies** | O-01, N-01, M-01 |
| **Deliverables** | Learning adapter that processes execution outcomes |
| **Success** | After 3 similar executions, the reasoning runtime produces higher-confidence predictions |
| **Complexity** | Very High — requires confidence engine integration, pattern detection |

### 5.4 Directive O-04: Explainability & Every Action Traceable

| Aspect | Definition |
|--------|-----------|
| **Objective** | Every business action has a complete trace: intent received → identity resolved → knowledge updated → memory updated → planning updated → execution updated → automation evaluated → projection generated → workspace updated. |
| **Why** | The OS Constitution requires explainability. Without traces, users cannot trust the system. |
| **Dependencies** | O-01, O-02, O-03 |
| **Deliverables** | Trace viewer in workspace UI, PipelineContext export |
| **Success** | Any action can be traced from intent to workspace update with sub-second latency |
| **Complexity** | High — requires trace persistence, query API, and UI rendering |

### 5.5 Founder Preview 4 — Milestone O

| Aspect | Definition |
|--------|-----------|
| **Purpose** | Demonstrate an intelligent OS that reasons, explains, and learns. |
| **Available capabilities** | All L + M + N capabilities + reasoning, LLM inference, learning, explainability traces |
| **Expected limitations** | No enterprise multi-tenancy. No production security hardening. |
| **Testing workflow** | 1. Ask a question about an object → 2. Receive AI-generated response → 3. View reasoning trace → 4. Create a follow-up → 5. View how knowledge changed → 6. Execute an action → 7. View explainability trace |
| **Exit criteria** | Pipeline trace shows all 11 stages as "completed" with real runtime output; explainability view shows intent-to-action trace |

---

## 6. Milestone P — Enterprise Platform

### 6.1 Directive P-01: Multi-Tenant Isolation

| Aspect | Definition |
|--------|-----------|
| **Objective** | Every runtime enforces tenant isolation. Organizations cannot see each other's data, objects, or execution traces. |
| **Why** | SHUNYA must support multiple organizations on the same OS instance. |
| **Dependencies** | L-01 through O-04 (all runtimes wired) |
| **Deliverables** | Tenant isolation enforcement in every runtime adapter |
| **Success** | Organization A cannot access Organization B's objects, even through the pipeline |
| **Complexity** | Very High — requires tenant context propagation through all 11 pipeline stages |

### 6.2 Directive P-02: RBAC & Permission System

| Aspect | Definition |
|--------|-----------|
| **Objective** | Every action is authorized by role-based permissions. Identity resolving includes permission resolution. The Execution Runtime enforces action-level permissions. |
| **Why** | Without permissions, any user can execute any action. Not acceptable for enterprise. |
| **Dependencies** | P-01 |
| **Deliverables** | Permission definitions, runtime enforcement, admin UI for role management |
| **Success** | A user with "viewer" role cannot execute destructive actions; rejected action produces authorization trace |
| **Complexity** | High — requires integration with Identity Runtime |

### 6.3 Directive P-03: Audit Trail & Immutable Logging

| Aspect | Definition |
|--------|-----------|
| **Objective** | Every pipeline execution is recorded in an immutable audit trail. Every object mutation has an audit entry. Every identity governance action has an audit entry. |
| **Why** | Enterprise compliance requires auditability. Without it, SHUNYA cannot be deployed in regulated industries. |
| **Dependencies** | L-01 through P-02 |
| **Deliverables** | Audit runtime wired to pipeline, audit query API, audit viewer |
| **Success** | Every action since deployment can be queried by intent, actor, object, and timestamp |
| **Complexity** | Medium |

### 6.4 Founder Preview 5 — Milestone P

| Aspect | Definition |
|--------|-----------|
| **Purpose** | Demonstrate enterprise-grade multi-tenant isolation and audit. |
| **Available capabilities** | All O capabilities + tenant isolation, RBAC, immutable audit trail |
| **Expected limitations** | No production-hardened infrastructure (scaling, HA, DR) |
| **Testing workflow** | 1. Sign in as Tenant A → 2. Create objects → 3. Sign in as Tenant B → 4. Verify Tenant B cannot see Tenant A's objects → 5. Execute action as restricted user → 6. Verify permission denial → 7. View audit trail |
| **Exit criteria** | Tenant isolation verified via cross-tenant access test; audit trail contains all actions |

---

## 7. Milestone Q — Production Infrastructure

### 7.1 Directive Q-01: Scalability & Performance

| Aspect | Definition |
|--------|-----------|
| **Objective** | All runtimes meet performance targets at scale. Define and test: pipeline latency < 500ms (no AI), projection assembly < 100ms (cached), execution scheduling < 100ms, 1000 concurrent users per tenant. |
| **Why** | A system that works for 1 user but fails at 100 is not a product. |
| **Dependencies** | P-01, P-02, P-03 |
| **Deliverables** | Performance benchmarks, bottleneck analysis, optimization pass |
| **Success** | All performance targets met under load testing |
| **Complexity** | Medium — optimization, not new features |

### 7.2 Directive Q-02: High Availability & Disaster Recovery

| Aspect | Definition |
|--------|-----------|
| **Objective** | SHUNYA runs in production with SLA guarantees. Define: deployment architecture, failover strategy, backup/restore, monitoring, alerting, runbook. |
| **Why** | Without HA/DR, SHUNYA cannot be a production system. |
| **Dependencies** | Q-01 |
| **Deliverables** | Deployment architecture document, runbook, HA tests |
| **Success** | Application survives single-node failure without data loss; RTO < 1 hour, RPO < 5 minutes |
| **Complexity** | Medium — infrastructure, not product features |

---

## 8. Milestone R — Security & Compliance

### 8.1 Directive R-01: Security Hardening

| Aspect | Definition |
|--------|-----------|
| **Objective** | Security audit and remediation: OWASP Top 10, dependency vulnerability scan, secrets management, rate limiting enforcement, DDoS protection, secure defaults. |
| **Why** | Security is not optional. A breach before 1.0 would be catastrophic. |
| **Dependencies** | Q-01, Q-02 |
| **Deliverables** | Security audit report, remediation plan, penetration test |
| **Success** | Zero critical or high-severity findings in security audit |
| **Complexity** | Medium — audit and remediation, not new features |

### 8.2 Directive R-02: Compliance Documentation

| Aspect | Definition |
|--------|-----------|
| **Objective** | Produce compliance documentation: SOC 2 controls mapping, GDPR compliance, data processing agreement, privacy policy, terms of service. |
| **Why** | Enterprise customers require compliance documentation before purchasing. |
| **Dependencies** | R-01 |
| **Deliverables** | Compliance documentation suite |
| **Success** | Documentation reviewed and approved by legal counsel |
| **Complexity** | Low — documentation, not code |

---

## 9. Milestone S — Founder Experience

### 9.1 Directive S-01: Onboarding Flow

| Aspect | Definition |
|--------|-----------|
| **Objective** | A guided onboarding that takes a new founder from sign-up to first meaningful action in under 5 minutes. The onboarding itself flows through the canonical pipeline. |
| **Why** | First impressions determine adoption. A 5-minute time-to-value is the target. |
| **Dependencies** | M-03 (frontend live), O-04 (explainability) |
| **Deliverables** | Onboarding wizard, sample data seeding, first-object creation flow |
| **Success** | New user creates first object within 5 minutes of sign-up |
| **Complexity** | Medium |

### 9.2 Directive S-02: Error Recovery & User Feedback

| Aspect | Definition |
|--------|-----------|
| **Objective** | Every pipeline failure produces a human-readable error message. Users can retry, escalate, or report failures. The OS learns from user feedback. |
| **Why** | Silent failures erode trust. The OS must communicate failures clearly and learn from them. |
| **Dependencies** | O-04 (explainability), Q-01 (reliability) |
| **Deliverables** | Error UI components, feedback capture, incident reporting |
| **Success** | Every pipeline error produces user-visible error with recovery action |
| **Complexity** | Medium |

### 9.3 Founder Preview 6 — Milestone S

| Aspect | Definition |
|--------|-----------|
| **Purpose** | Demonstrate a polished founder experience suitable for public launch. |
| **Available capabilities** | All capabilities through all milestones |
| **Expected limitations** | None planned — this is the final preview before launch |
| **Testing workflow** | Full end-to-end founder journey: sign up → onboarding → create → execute → analyze → learn → audit |
| **Exit criteria** | Founder can perform any supported action through the canonical pipeline end-to-end |

---

## 10. Milestone T — Public Launch

### 10.1 Directive T-01: Version 1.0 Launch

| Aspect | Definition |
|--------|-----------|
| **Objective** | Publicly launch SHUNYA OS Version 1.0. All capabilities at "Production Ready" state. |
| **Why** | This is the goal of the entire roadmap. |
| **Dependencies** | L through S (all milestones complete) |
| **Deliverables** | Public website, documentation, pricing, support channels, marketing materials |
| **Success** | Public launch completed; first enterprise customers onboarded |
| **Complexity** | Low — go-to-market, not technology |

---

## 11. Release Roadmap

### 11.1 Release Schedule

| Release | Included milestones | Capabilities | Founder testing goal |
|---------|-------------------|-------------|---------------------|
| **0.1 — OS Foundation** | L | Sign-in, space/object CRUD through OS pipeline, basic workspace | Validate that the pipeline exists and processes real actions |
| **0.2 — Living Workspace** | L, M | Live data in Next.js, knowledge graph, memory, planning, canonical workspace | Validate that the workspace shows real data from the OS |
| **0.3 — Connected Business** | L, M, N | Execution, automation, integration | Validate that SHUNYA can do real work |
| **0.5 — Executive Intelligence** | L, M, N, O | Reasoning, LLM inference, learning, explainability | Validate that SHUNYA is intelligent and explainable |
| **0.8 — Enterprise Candidate** | L, M, N, O, P | Multi-tenancy, RBAC, audit trail | Validate enterprise readiness with a real customer |
| **0.9 — Production Candidate** | L, M, N, O, P, Q, R | Scalability, HA/DR, security, compliance | Validate production readiness under load |
| **1.0 — Public Launch** | L, M, N, O, P, Q, R, S, T | All capabilities production-ready | Founder validates end-to-end journey |

### 11.2 Release Dependency Chain

```
0.1 ──→ 0.2 ──→ 0.3 ──→ 0.5 ──→ 0.8 ──→ 0.9 ──→ 1.0
(L)     (M)     (N)     (O)     (P)     (Q+R)   (S+T)
```

Each release is cumulative: 0.5 includes everything from 0.1, 0.2, and 0.3.

---

## 12. Dependency Graph

### 12.1 Directive Dependency Graph

```
L-01 (Kernel)
├── L-02 (Identity)
├── L-03 (Flask → OS) ← depends on L-01, L-02
├── L-04 (Projection) ← depends on L-03
│
├── M-01 (Memory/KG) ← depends on L-01
├── M-02 (Planning) ← depends on L-01, M-01
│
├── N-01 (Execution) ← depends on L-01, M-01, M-02
├── N-02 (Automation) ← depends on N-01
├── N-03 (Integration) ← depends on N-01
│
├── M-03 (Frontend Live) ← depends on L-03
├── M-04 (Canonical Workspace) ← depends on M-03
│
├── O-01 (Reasoning) ← depends on L-01, M-01
├── O-02 (LLM Provider) ← depends on O-01
├── O-03 (Learning) ← depends on O-01, N-01, M-01
├── O-04 (Explainability) ← depends on O-01, O-02, O-03
│
├── P-01 (Multi-Tenant) ← depends on all L-O
├── P-02 (RBAC) ← depends on P-01
├── P-03 (Audit) ← depends on all L-P
│
├── Q-01 (Scalability) ← depends on P
├── Q-02 (HA/DR) ← depends on Q-01
│
├── R-01 (Security) ← depends on Q
├── R-02 (Compliance) ← depends on R-01
│
├── S-01 (Onboarding) ← depends on M-03, O-04
├── S-02 (Error Recovery) ← depends on O-04, Q-01
│
└── T-01 (Launch) ← depends on all
```

### 12.2 Critical Path

```
L-01 → L-02 → L-03 → M-03 → M-04 → O-02 → O-04 → S-01 → T-01
```

This is the minimum path to Version 1.0. It is 9 directives long. All other directives can be parallelized or deferred without blocking launch, except that enterprise customers will require P-01 and P-02 before adoption.

---

## 13. Capability Evolution Map

### 13.1 Evolution Model

Every capability progresses through exactly 6 states:

```
Designed
    ↓ (architecture approved)
Implemented
    ↓ (code exists, unit tests pass)
Integrated
    ↓ (wired into canonical pipeline, adapter exists)
Operational
    ↓ (end-to-end tested through pipeline)
Founder Validated
    ↓ (founder verifies via Founder Preview)
Production Ready
    ↓ (performance targets met, security reviewed)
```

### 13.2 Current State (Phase L Baseline)

| Capability | Designed | Implemented | Integrated | Operational | Founder Validated | Production Ready |
|-----------|:--------:|:-----------:|:----------:|:-----------:|:----------------:|:----------------:|
| Type system | | ✅ | | | | |
| Object contract | | ✅ | | | | |
| State machine | | ✅ | | | | |
| Timeline | | ✅ | | | | |
| Identity store | | ✅ | | | | |
| Identity governance | | ✅ | | | | |
| Knowledge graph | | ✅ | | | | |
| Memory (6 layers) | | ✅ | | | | |
| Cognitive pipeline | | ✅ | | | | |
| Execution lifecycle | | ✅ | | | | |
| Planning (HTN) | | ✅ | | | | |
| Event bus / automation | | ✅ | | | | |
| Integration connectors | | ✅ | | | | |
| Projection engine | | ✅ | | | | |
| Workspace management | | ✅ | | | | |
| Canonical pipeline | ✅ | ✅ | | | | |
| OS kernel | ✅ | ✅ | | | | |
| Kernel adapter | | | | | | |
| Identity adapter | | | | | | |
| Pipeline wiring | | | | | | |
| Live frontend | | | | | | |
| Reasoning | | ✅ | | | | |
| Inference (LLM) | | | | | | |
| Learning | | ✅ | | | | |
| Explainability traces | | | ✅ | | | |
| Multi-tenancy | | | | | | |
| RBAC / permissions | | ✅ | | | | |
| Audit trail | | | | | | |
| Scalability | | | | | | |
| HA/DR | | | | | | |
| Security hardening | | | | | | |
| Compliance docs | | | | | | |
| Onboarding | | | | | | |
| Error recovery | | | | | | |

### 13.3 How Capability Tracking Replaces Phase Reporting

| Old (Phase-based) | New (Capability-based) |
|-------------------|----------------------|
| Reports on what was implemented | Reports on what state each capability is in |
| Binary: implemented / not yet | 6 states from Designed to Production Ready |
| Organized by implementation phase | Organized by capability domain |
| No integration status | Integration is explicitly a gate (state 3 of 6) |
| No founder validation gate | Founder validation is explicitly a gate (state 5 of 6) |
| No production readiness gate | Production readiness is explicitly a gate (state 6 of 6) |

The capability matrix (`docs/canon/CAPABILITY_MATRIX.md`) is the single source of truth for progress reporting. Phase reports become historical records only — they no longer drive planning.

---

## 14. Critical Path Analysis

### 14.1 Critical Path Timeline

```
L-01 (Kernel) ─── 1 sprint ──→ L-02 (Identity) ─── 1 sprint ──→ L-03 (Flask→OS) ─── 1 sprint
                                                                        │
                                                                        ▼
                                                                   M-03 (Frontend) ─── 2 sprints
                                                                        │
                                                                        ▼
                                                                   M-04 (Workspace) ─── 1 sprint
                                                                        │
                                                                        ▼
                                                                   O-02 (LLM) ─── 2 sprints
                                                                        │
                                                                        ▼
                                                                   O-04 (Explain) ─── 1 sprint
                                                                        │
                                                                        ▼
                                                                   S-01 (Onboarding) ─── 1 sprint
                                                                        │
                                                                        ▼
                                                                   T-01 (Launch) ─── 1 sprint
```

### 14.2 Parallel Tracks

```
Track A (Critical Path):   L-01 → L-02 → L-03 → M-03 → M-04 → O-02 → O-04 → S-01 → T-01
Track B (Execution):       M-01 → M-02 → N-01 → N-02 → N-03
Track C (Intelligence):    O-01 → O-03
Track D (Enterprise):      P-01 → P-02 → P-03
Track E (Infrastructure):  Q-01 → Q-02 → R-01 → R-02
Track F (Experience):      S-02
```

Tracks B-F can run in parallel with Track A once their dependencies are met. The critical path is 9 directives; full completion is 25 directives.

### 14.3 Earliest Launch Estimate

Assuming 2-week sprints and one directive per sprint per track:

- **Critical path (Track A):** 9 sprints = 18 weeks
- **Full completion (all tracks):** 14 sprints = 28 weeks
- **Founder Preview 1:** After L-03 (3 sprints = 6 weeks)
- **Release 0.1:** After L complete (4 sprints = 8 weeks)
- **Release 1.0:** After T-01 (14 sprints = 28 weeks)

---

## 15. Definition of SHUNYA Version 1.0

### 15.1 Functional Requirements

A system may call itself SHUNYA OS Version 1.0 **only when** all of the following are objectively true:

1. **Canonical Pipeline Operational** — All 11 pipeline stages process every user action. No action bypasses the pipeline.
2. **Universal Object Model** — Every business entity is a UniversalObject. No duplicate object representations exist in production code.
3. **One Workspace** — One canonical workspace (Next.js) renders all projections. No other workspace surface exists in the canonical code path.
4. **Live Frontend** — No hardcoded demo data. Every UI component renders data from the operating system through the pipeline.
5. **Real AI Inference** — All AI responses come from a real LLM or inference engine. No scenario-based or hardcoded responses in the codebase.
6. **Multi-Tenant** — Multiple organizations can use the same SHUNYA instance without data leakage.
7. **RBAC** — Every action is authorized. Unauthorized actions are rejected with an explainable trace.
8. **Audit Trail** — Every action is recorded in an immutable audit log.
9. **Explainability** — Every action has a traceable path: intent → identity → knowledge → memory → planning → execution → automation → projection → workspace.
10. **Learning** — The OS learns from outcomes. Repeated similar executions produce higher-confidence results.
11. **Production Infrastructure** — HA, DR, scalability, monitoring, alerting, and runbook exist and are tested.
12. **Security** — OWASP Top 10 remediated, secrets managed, rate limiting enforced.
13. **Compliance** — Documentation exists for SOC 2, GDPR, and data processing.
14. **Onboarding** — A new founder can create their first object within 5 minutes.
15. **No Demo Paths** — Zero demo data, zero mock implementations, zero placeholder logic in production code paths.

### 15.2 Quality Gates

| Gate | Requirement |
|------|-------------|
| Test suite | 100% pass rate on full suite (>4,500 tests) |
| Ruff | 0 errors |
| MyPy | 0 errors |
| Performance | Pipeline < 500ms (no AI), < 2s (with AI) |
| Load test | 1000 concurrent users |
| Security audit | Zero critical/high findings |
| Founder validation | Founder can complete full journey in < 10 minutes |

### 15.3 What is NOT required for 1.0

- Mobile apps (web-only is acceptable)
- Native desktop apps
- On-premise deployment (SaaS-only is acceptable)
- Third-party marketplace
- Custom theming
- Multi-language support beyond English
- API for external developers

---

## 16. Roadmap Governance

### 16.1 How to Use This Roadmap

1. **Every sprint begins with** selecting the next available directive from the roadmap.
2. **Every directive must be completed** (all success criteria met) before the next directive in its dependency chain begins.
3. **Parallel directives** may be worked on simultaneously if their dependency chains do not overlap.
4. **Completed directives** are marked "Done" in the capability matrix.
5. **Roadmap changes** require a documented justification and must preserve dependency integrity.

### 16.2 Roadmap Evolution

This roadmap supports:

| Operation | Rule |
|-----------|------|
| **Adding directives** | Must be inserted after all dependencies are met. Must not break existing dependency chains. |
| **Splitting a directive** | The new directives must collectively satisfy the original success criteria. |
| **Merging directives** | Dependencies of both originals must be met. The merged directive must satisfy all original success criteria. |
| **Reordering** | Dependency order must be preserved. Non-dependent directives may be reordered freely. |
| **Changing priority** | Priority changes do not affect dependency ordering. They affect scheduling order among non-dependent directives. |

### 16.3 Directive Completion Checklist

Every directive, when completed, must have:

- [ ] Architecture approved
- [ ] Implementation complete
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Integrated into canonical runtime pipeline
- [ ] Capability matrix updated
- [ ] Founder validation completed (where applicable)
- [ ] Independent verification completed

---

*This roadmap is the governing execution plan for SHUNYA from Phase L through Version 1.0. All future work originates from this document.*