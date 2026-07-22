# SHUNYA Supporting Architecture Justification

**Date:** 2026-07-18
**Authority:** G2.1 Architecture Findings Classification
**Objective:** Classify each proposed supporting component using architectural evidence. No new engine specifications. No architecture redesign.

---

## Classification Framework

| Classification | Definition | Governance | Compounding Intelligence? | Examples |
|---------------|------------|------------|--------------------------|----------|
| **Shared Infrastructure** | A cross-cutting capability used by multiple engines but not participating in the intelligence pipeline. Does not have its own inputs/outputs in the pipeline. | Architecture Standard or ADR | No | Event Bus, Credential Store, Database, Message Queue |
| **Engine** | A named layer in the Compounding Intelligence Architecture with defined responsibilities, inputs, outputs, state, and lifecycle. Participates in the intelligence pipeline. | Engine Specification (ES-NNN) | Yes or No (but is part of the pipeline) | ES-001 through ES-007 |
| **Internal Service** | A supporting service used by one or a few engines. Not a layer in the pipeline. May have its own data store. | Part of the owning engine's specification | No | PDF renderer, notification dispatcher |
| **Library** | Shared code used by multiple engines. No independent lifecycle, data store, or deployment. | Part of the codebase conventions | No | Confidence calculation library, evidence validation utilities |
| **Product Feature** | A user-facing capability that is built on top of the architecture. Not an architectural component. | Product roadmap | No | Dashboard, reports, client portal |

---

## Component 1: Event Bus

### Classification: Shared Infrastructure

### Justification

**Architectural responsibility:** Provide a publish/subscribe communication channel for asynchronous event delivery between engines. The Event Bus carries events formatted in the canonical event envelope (Core Models §8) from publishers to subscribers. It does not transform, validate, or interpret event payloads.

The Event Bus is the implementation mechanism for the Interaction Principles defined in SHUNYA System Flow §10 (Publish Rules, Consumption Rules, Async Behavior). It is a means, not an end.

**Ownership:** Shared infrastructure. No single engine owns the Event Bus. All engines publish and consume events through it. Operational responsibility belongs to the infrastructure/platform team.

**Lifecycle:** The Event Bus has an operational lifecycle (start, stop, health check, scaling) but no semantic lifecycle. It does not have states like "learning" or "planning." It is a transport layer.

**Inputs:** Canonical events published by any engine. Input validation (envelope structure) is performed by the Event Bus itself — payload validation is the consumer's responsibility.

**Outputs:** Same canonical events delivered to subscribed consumers. Delivery guarantees (at-least-once, at-most-once) are configuration parameters. No transformation.

**Dependencies:** None in the engine dependency graph. Engines depend on the Event Bus operating, but the Event Bus depends on no engine.

**Does it compound intelligence?** No. The Event Bus carries intelligence (events) but does not compound it. No learning, no improvement cycle. A faster Event Bus does not make the system smarter.

**Does it deserve independent governance?** No. The Event Bus is governed by a single Architecture Standard or ADR defining its configuration and operational characteristics. It does not require an independent specification with input/output contracts, state machines, constitutional mappings, or verification checklists. The canonical event envelope is already specified in Core Models §8.

### Decision

**Does this component require an independent Engine Specification?**

**NO**

**Recommendation:** Define the Event Bus as an Architecture Standard that extends Core Models §8. The standard shall cover:
- Instantiation and configuration (in-process vs distributed, partitioning, delivery guarantees)
- Operational characteristics (scaling, health, monitoring)
- Security model (tenant isolation on events, authentication for publishers/consumers)
- Dead-letter queue configuration

The Event Bus itself is plumbing. The canonical event envelope is the architecture. The envelope is already specified. The plumbing does not need an engine specification.

---

## Component 2: Credential Store

### Classification: Shared Infrastructure

### Justification

**Architectural responsibility:** Securely store and resolve credentials (API tokens, passwords, encryption keys, OAuth tokens) for external service authentication. The Credential Store is used exclusively by the Executor Engine (ES-005) to resolve credentials at execution time. No other engine accesses credentials (this is enforced by the constitutional principle of Least Authority — SHUNYA_ARCHITECTURE.md §6.3).

**Ownership:** The Credential Store is owned by the security/infrastructure function, not by any engine. Operational policies (rotation, access control, audit) are defined by security policy, not by the architecture.

**Lifecycle:** The Credential Store has an operational lifecycle (credential creation, rotation, revocation, expiry) but no semantic lifecycle in the intelligence pipeline. It is not a participant in the compounding loop.

**Inputs:** Credential resolution requests from the Executor Engine only. Each request specifies a credential reference (ID or alias) and a tenant_id.

**Outputs:** Resolved credential values (memory-only, never logged, never stored in plan payloads). Credentials are discarded after the task completes.

**Dependencies:** Depended upon by the Executor Engine (ES-005). Depends on no other component.

**Does it compound intelligence?** No. Credentials do not participate in the intelligence cycle. Rotating a credential does not make the system smarter.

**Does it deserve independent governance?** No. The Credential Store's interface and security model should be defined as part of the Executor Engine specification (ES-005) or as a short Architecture Standard. It does not need its own engine specification with state machines, constitutional mappings, and verification checklists.

### Decision

**Does this component require an independent Engine Specification?**

**NO**

**Recommendation:** Define the Credential Store interface and security model within ES-005 (Executor Engine) as an internal service dependency. The specification shall cover:
- Credential resolution contract (input: reference + tenant_id, output: resolved value)
- Security model (audit logging, access control, encryption at rest)
- Phase 4 (Privacy) integration (eligibility gates on credential release)
- Supported credential types (API token, OAuth, Basic Auth, mTLS)

The Credential Store is a secure key-value store with access control. It is not an engine.

---

## Component 3: Doctor

### Classification: Engine

### Justification

**Architectural responsibility:** Verify system integrity, check architecture drift, validate package health, confirm governance compliance. The Doctor Engine is defined as a named architectural layer in SHUNYA System Flow §3 with defined responsibilities:

> "Verify system integrity; check architecture drift; validate package health; confirm governance compliance."

The Doctor Engine is referenced by:
- The Observer Engine (ES-006) — to verify that observed outcomes are consistent with system health
- The Governance Engine (ES-001) — to verify that governance policies are being enforced correctly
- The Engineering Constitution (Article 7 — Documentation Currency) — to verify that architecture documents match implementation

**Ownership:** The Doctor Engine owns integrity verification, architecture drift detection, and compliance checking. It does not own system health (that is operational monitoring) but it consumes health data to verify architecture compliance.

**Lifecycle:** The Doctor Engine follows a defined lifecycle: check scheduling → check execution → result reporting → violation escalation. This is distinct from the health check lifecycle of operational monitoring. The Doctor Engine has states: `idle`, `checking`, `violation_detected`, `reporting`.

**Inputs:**
- Health data from all engines (via Event Bus or direct API)
- Architecture document snapshots (current vs baseline)
- Governance audit log (for compliance verification)
- Knowledge Engine integrity reports (checksum mismatches)
- System configuration (package versions, dependencies)

**Outputs:**
- DoctorReport — structured report of all checks with pass/fail/warning per check
- Violation events — published when architecture drift, compliance violation, or integrity failure is detected
- Health summary — aggregated health status across all engines

**Dependencies:**
- All engines (reads health and integrity data from each)
- Knowledge Engine (reads integrity data for knowledge_facts)
- Governance Engine (reads audit log for compliance verification)

**Does it compound intelligence?** No. The Doctor Engine checks that the architecture has not drifted, but it does not improve the architecture. It is a verification layer, not a compounding layer. However, it is still an **engine** because it has a defined architectural responsibility, a lifecycle, inputs/outputs, and participates in the architectural trust model (SHUNYA_ARCHITECTURE.md §6 — Architectural Trust Principles).

**Does it deserve independent governance?** Yes. The Doctor Engine has a distinct responsibility that cannot be folded into another engine:
- It checks **all** engines, so it cannot be owned by any single engine (conflict of interest)
- It enforces the Engineering Constitution (Article 7 — Documentation Currency, Article 8 — Divergence Protocol)
- It is defined as a separate layer in the SHUNYA Architecture (SHUNYA_ARCHITECTURE.md §5 — Doctor Layer)
- A partial implementation exists (`app/shunya/doctor.py`) that demonstrates the concept

### Decision

**Does this component require an independent Engine Specification?**

**YES**

**Reasoning:** The Doctor Engine is already established in the SHUNYA Constitution as a distinct architectural layer (§5 — Doctor Layer), is referenced by multiple existing specifications, has a partial implementation, and has a unique responsibility that cannot be owned by any other engine (conflict of interest — it checks all engines). It requires ES-008 following the ENGINE_SPEC_TEMPLATE.md.

---

## Component 4: Context Fusion

### Classification: Engine

### Justification

**Architectural responsibility:** Assemble a bounded workspace context from all source providers: identity, relationships, conversations, human context, memory, evidence, and documents. Apply purpose-based eligibility gates (Phase 4). Enforce budget limits. Compute fingerprints.

Context Fusion is defined in SHUNYA System Flow §3 as one of 10 engines. It is positioned in the canonical lifecycle (System Flow §2) between Knowledge Resolution and Reasoning:

```
Knowledge Resolution → [Context Fusion] → Reasoning
```

Context Fusion is referenced by:
- Reasoning Engine (ES-003) — requires workspace context for evidence-grounded reasoning
- Planner Engine (ES-004) — requires context for constraint-aware planning
- Governance Engine (ES-001) — requires context for policy evaluation
- Executor Engine (ES-005) — requires context for execution
- Observer Engine (ES-006) — requires context for observation
- Learning Engine (ES-007) — requires context for pattern analysis

It is the most-depended-upon engine in the architecture (6 of 7 pipeline engines depend on it).

**Ownership:** Context Fusion owns the workspace context lifecycle: context request → source provider integration → purpose gate → budget enforcement → fingerprint → delivery. No other engine assembles context.

**Lifecycle:** Context Fusion has a defined pipeline:
```
Context Request → Source Provider Integration → Eligibility Gate → Budget Enforcement → Context Assembly → Fingerprint → Delivery
```

This is a processing pipeline with distinct stages, each with defined inputs and outputs.

**Inputs:**
- Context request from any pipeline engine (tenant_id, actor_id, purpose_code, subject_id, current_object_ref)
- Source provider data from Identity, Relationship, Conversation, Human Context, Memory, Evidence, Document providers
- Eligibility decisions from Phase 4 (Privacy) — purpose-based gates

**Outputs:**
- WorkspaceContext — bounded, fingerprinted set of context items with inclusion/exclusion reasons and budgets

**Dependencies:**
- Phase 4 (Privacy) — eligibility gates
- Identity Engine — person/actor resolution
- Knowledge Engine — evidence, memory, document facts
- Relationship Engine — relationship records

**Does it compound intelligence?** Indirectly. Context Fusion itself does not learn or improve, but the quality of context directly affects the quality of reasoning, planning, governance, and ultimately execution. Better context enables better decisions. However, the compounding happens in the downstream engines, not in Context Fusion itself. Despite this, Context Fusion qualifies as an engine because it is a named layer in the architecture with defined pipeline stages, inputs/outputs, and cross-cutting dependencies.

**Does it deserve independent governance?** Yes. Context Fusion:
- Is referenced by 6 of 7 pipeline engines — cannot be collapsed into any single one
- Has a defined pipeline (not just a single operation)
- Integrates with Phase 4 (Privacy) for purpose-based eligibility — a constitutional requirement
- Has distinct failure modes (source provider unavailable, eligibility denied, budget exceeded)
- Has a computation-only implementation (`app/context/__init__.py`, 334 lines) that proves the concept

### Decision

**Does this component require an independent Engine Specification?**

**YES**

**Reasoning:** Context Fusion is a named engine in the architecture, depended upon by 6 of 7 pipeline engines, has a defined processing pipeline, integrates with Phase 4 (Privacy), and cannot be owned by any single downstream engine without creating a circular dependency or overloading that engine's responsibilities. It requires ES-009 following the ENGINE_SPEC_TEMPLATE.md.

---

## Component 5: Identity

### Classification: Engine

### Justification

**Architectural responsibility:** Resolve persons to canonical identities. Register and normalize identities from multiple sources (email, phone, channel IDs, document IDs, external references). Detect and flag ambiguous resolutions. Never silently merge uncertain identities.

Identity is defined in SHUNYA System Flow §3 as one of 10 engines. It is referenced by:
- Context Fusion — the first engine to need identity resolution when assembling workspace context
- All pipeline engines indirectly (through Context Fusion)

**Ownership:** Identity Engine owns the identity lifecycle: identity intake → normalization → resolution → verification → supersession → merge. No other engine resolves identities.

**Lifecycle:** Identity has a defined lifecycle:

```
Active → Verified → Superseded | Merged
```

This is a state machine with defined transitions and terminal states. Identity records are versioned (canonical model).

**Inputs:**
- Identity claims from multiple sources (email, phone, channel, document, external reference)
- Verification requests (confirm or reject an identity-to-person mapping)
- Merge/supersession requests (resolve ambiguous identities)

**Outputs:**
- ResolutionResult — MATCHED, NO_MATCH, or AMBIGUOUS with person reference and confidence
- Verified identity records — stored in the Knowledge Engine or Identity Engine's own store

**Dependencies:**
- Knowledge Engine (ES-002) — stores identity records and person records
- Channel adapters — extracts identity claims from incoming messages

**Does it compound intelligence?** No. Identity resolution is deterministic. The same input always produces the same output. Identity resolution does not improve over time through learning — it does not compound. However, identity is still an **engine** because it is a named architectural layer with defined responsibilities, a state machine, inputs/outputs, and is depended upon by other layers.

**Does it deserve independent governance?** Yes. Identity:
- Is a named layer in the SHUNYA Architecture (SHUNYA_ARCHITECTURE.md §5 does not explicitly name it, but SHUNYA System Flow §3 does as one of 10 engines)
- Has a defined state machine (Active → Verified → Superseded | Merged)
- Has distinct failure modes (ambiguous resolution, unverifiable identity, duplicate merge)
- Is constitutionally significant: "Identity is globally unique within a tenant" is an Architectural Invariant (Core Models §11, Invariant 8)
- Has a full implementation (`app/shunya/identity/__init__.py`, 270 lines) that proves the concept
- Cannot be folded into Context Fusion without overloading it — identity resolution is a prerequisite for context assembly, not a sub-function of it

### Decision

**Does this component require an independent Engine Specification?**

**YES**

**Reasoning:** Identity is a named engine in the architecture with a defined state machine, constitutional significance (unique identity invariant), distinct failure modes, and an existing implementation. It is a prerequisite for Context Fusion, not a sub-function of it. It requires ES-010 following the ENGINE_SPEC_TEMPLATE.md.

---

## Summary Table

| Component | Classification | Engine Spec Required? | What to Create |
|-----------|---------------|----------------------|----------------|
| **Event Bus** | **Shared Infrastructure** | **NO** | Architecture Standard extending Core Models §8 |
| **Credential Store** | **Shared Infrastructure** | **NO** | Interface definition within ES-005 or short Architecture Standard |
| **Doctor** | **Engine** | **YES** | ES-008 (Doctor Engine) |
| **Context Fusion** | **Engine** | **YES** | ES-009 (Context Fusion Engine) |
| **Identity** | **Engine** | **YES** | ES-010 (Identity Engine) |

---

## Dependency Chain for the 3 New Engine Specifications

```
Identity (ES-010)          Doctor (ES-008)
      │                          │
      │ (identity resolution)    │ (integrity verification)
      ▼                          │
Context Fusion (ES-009)          │
      │                          │
      │ (workspace context)      │
      ▼                          ▼
All Pipeline Engines      All Pipeline Engines
(ES-003 through ES-007)   (ES-001 through ES-007)
```

- **Identity (ES-010)** must be specified before Context Fusion (ES-009) because Context Fusion depends on identity resolution.
- **Context Fusion (ES-009)** must be specified before Reasoning (ES-003) through Learning (ES-007) because all downstream engines depend on workspace context.
- **Doctor (ES-008)** is independent of the pipeline order. It can be specified in parallel with the other two.

---

*End of Supporting Architecture Justification*