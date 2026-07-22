# Implementation Master Plan

**Phase 15 — SHUNYA OS**
**Classification: Engineering Planning**
**Status: PROPOSED**

---

## Preamble

### Authority

This document transforms the complete constitutional and implementation architecture into executable engineering work. It does NOT introduce new architecture, new concepts, or new design. Everything traces back to existing architecture documents.

### Input documents

| # | Document | Type | Lines | Sections |
|---|----------|------|-------|----------|
| D01 | UNIVERSAL_ONTOLOGY.md | Constitutional | 1246 | 20 |
| D02 | COGNITIVE_WORKSPACE_RUNTIME.md | Constitutional | 952 | 12 |
| D03 | ADAPTIVE_INTELLIGENCE_RUNTIME.md | Constitutional | 989 | 15 |
| D04 | UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md | Implementation | 969 | 15 |
| D05 | FOUNDER_WORKSPACE_SPECIFICATION.md | Product | 632 | 14 |
| D06 | EXECUTION_INTELLIGENCE_ARCHITECTURE.md | Implementation | 792 | 15 |
| D07 | UNIVERSAL_PERCEPTION_ARCHITECTURE.md | Implementation | 773 | 15 |
| D08 | DECISION_INTELLIGENCE_ARCHITECTURE.md | Implementation | 802 | 15 |
| D09 | ARCHITECTURE_GOVERNANCE_FRAMEWORK.md | Governance | 819 | 14 |

---

## PART 1 — Architecture Inventory

### Document inventory

| Document | Purpose | Dependencies | Priority | Complexity | Est. modules | Sequence |
|----------|---------|--------------|----------|------------|--------------|----------|
| **D01 — Ontology** | Canonical language. Every concept derives from this. | None | P0 | Medium | 3 | 1 |
| **D02 — Cognitive Runtime** | Cognition, attention, memory, intent pipeline, event bus | D01 | P0 | High | 8 | 2 |
| **D03 — Adaptive Runtime** | Learning, confidence, calibration, governance, evolution | D01, D02 | P0 | High | 7 | 3 |
| **D04 — Knowledge Graph** | Graph storage, traversal, projections, evidence graph | D01 | P0 | High | 10 | 1 (parallel with D02) |
| **D05 — Workspace** | Three-zone layout, object model, composer, projections | D02, D04 | P1 | Medium | 5 | 5 |
| **D06 — Execution Intelligence** | Execution model, planner, orchestrator, verification | D01, D02, D04 | P1 | High | 8 | 4 |
| **D07 — Perception** | Signal capture, observation pipeline, sources, conflict | D01, D04 | P1 | High | 7 | 3 (parallel with D03) |
| **D08 — Decision Intelligence** | Decision model, evaluation, ranking, governance | D01, D02, D03, D06 | P1 | High | 8 | 4 (parallel with D06) |
| **D09 — Governance Framework** | Repository, conformance, invariants, health | D01–D08 | P2 | Medium | 5 | 6 |

### Priority definitions

| Priority | Meaning | Timeline |
|----------|---------|----------|
| P0 | Foundation — everything depends on this | Sprint 1–4 |
| P1 | Core capability — required for minimum viable system | Sprint 3–10 |
| P2 | Quality — required for production readiness | Sprint 8–14 |

---

## PART 2 — Engineering Epics

### Epic inventory

| Epic ID | Name | Architecture source | Est. effort | Priority |
|---------|------|-------------------|-------------|----------|
| E-001 | Ontology Engine | D01 §1–§20 | 3 sprints | P0 |
| E-002 | Identity Engine | D01 §3, §3.5 | 2 sprints | P0 |
| E-003 | Knowledge Graph | D04 §1–§15 | 6 sprints | P0 |
| E-004 | Evidence Engine | D01 §7, D04 §4 | 3 sprints | P0 |
| E-005 | Cognitive Runtime | D02 §1–§12 | 5 sprints | P0 |
| E-006 | Memory Engine | D01 §17, D02 §5 | 3 sprints | P0 |
| E-007 | Attention Engine | D02 §2 | 2 sprints | P0 |
| E-008 | Intent Pipeline | D02 §4 | 2 sprints | P0 |
| E-009 | Event Bus | D02 §9 | 2 sprints | P0 |
| E-010 | Adaptive Runtime | D03 §1–§15 | 5 sprints | P0 |
| E-011 | Confidence Engine | D03 §2 | 2 sprints | P0 |
| E-012 | Perception Engine | D07 §1–§13 | 5 sprints | P1 |
| E-013 | Execution Engine | D06 §1–§14 | 5 sprints | P1 |
| E-014 | Decision Engine | D08 §1–§14 | 5 sprints | P1 |
| E-015 | Workspace Engine | D05 §1–§14 | 4 sprints | P1 |
| E-016 | Governance Engine | D09 §1–§14 | 3 sprints | P2 |
| E-017 | Policy Engine | D01 §16, D03 §7 | 2 sprints | P2 |
| E-018 | Relationship Engine | D01 §5, D04 §3 | 2 sprints | P0 |
| E-019 | Temporal Engine | D04 §5 | 2 sprints | P1 |
| E-020 | Projection Engine | D02 §3, D04 §8 | 3 sprints | P1 |

### Epic dependency graph

```
E-001 (Ontology)
  ├── E-002 (Identity)
  ├── E-003 (Knowledge Graph)
  │     ├── E-004 (Evidence)
  │     ├── E-018 (Relationship)
  │     └── E-019 (Temporal)
  ├── E-005 (Cognitive Runtime)
  │     ├── E-006 (Memory)
  │     ├── E-007 (Attention)
  │     ├── E-008 (Intent Pipeline)
  │     └── E-009 (Event Bus)
  ├── E-010 (Adaptive Runtime)
  │     ├── E-011 (Confidence)
  │     └── E-017 (Policy)
  ├── E-012 (Perception)
  ├── E-013 (Execution)
  ├── E-014 (Decision)
  ├── E-015 (Workspace)
  │     └── E-020 (Projection)
  └── E-016 (Governance)
```

---

## PART 3 — Epic Specifications

### E-001 — Ontology Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the canonical type system, object model, attributes, state, timeline, and context as defined in UNIVERSAL_ONTOLOGY.md |
| **Deliverables** | `app/kernel/object.py` (UniversalObject base), `app/kernel/types.py` (type registry), `app/kernel/state.py` (state machine), `app/kernel/timeline.py` (timeline), `app/kernel/context.py` (context) |
| **Interfaces** | `UniversalObject.create()`, `UniversalObject.load()`, `TypeRegistry.register()`, `StateMachine.transition()`, `Timeline.append()` |
| **Dependencies** | None (foundation) |
| **Acceptance criteria** | 1000 objects created in < 1s. All 20 ontology sections implementable. 43 invariants enforceable. |
| **Risks** | Type system may need extension for future types. Keep it generic. |

### E-002 — Identity Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement identity: permanent, external, derived, temporary, merged, split, deleted. Identity governance with merge/split rules. |
| **Deliverables** | `app/kernel/identity.py` (Identity, IdentityStore), `app/kernel/identity_governance.py` (merge, split, retirement, conflict resolution) |
| **Interfaces** | `IdentityStore.assign()`, `IdentityStore.resolve()`, `IdentityGovernance.merge()`, `IdentityGovernance.split()`, `IdentityGovernance.retire()` |
| **Dependencies** | E-001 (Ontology Engine) |
| **Acceptance criteria** | Identities are permanent. Merge preserves evidence. Split partitions evidence. Retired identities never reused. All governance operations auditable. |
| **Risks** | Identity resolution performance at scale (100M identities). |

### E-003 — Knowledge Graph

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the complete Knowledge Graph: nodes, edges, identity, labels, types, metadata, weights, confidence, versioning. Canonical node families, edge families, temporal graph, consistency model, security model. |
| **Deliverables** | `app/graph/node.py` (Node, NodeStore), `app/graph/edge.py` (Edge, EdgeStore), `app/graph/families.py` (node families, edge families), `app/graph/temporal.py` (temporal edges), `app/graph/consistency.py` (validation), `app/graph/security.py` (visibility, permissions, audit) |
| **Interfaces** | `NodeStore.create()`, `NodeStore.load()`, `EdgeStore.create()`, `EdgeStore.validate()`, `TemporalStore.query()`, `ConsistencyValidator.validate()` |
| **Dependencies** | E-001 (Ontology Engine), E-002 (Identity Engine) |
| **Acceptance criteria** | 1M nodes indexed. 10M edges stored. 1-hop traversal < 10ms. Temporal queries return correct results. Security model enforces visibility. |
| **Risks** | Storage backend choice. Graph database vs relational with graph layer. |

### E-004 — Evidence Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Evidence Graph: evidence creation, evidence chain, lineage, confidence traceability, contradiction detection, evidence validation. |
| **Deliverables** | `app/evidence/models.py` (Evidence, EvidenceRef, EvidenceChain), `app/evidence/engine.py` (EvidenceEngine, ContradictionDetector) |
| **Interfaces** | `EvidenceEngine.create_evidence()`, `EvidenceEngine.get_chain()`, `EvidenceEngine.trace_confidence()`, `ContradictionDetector.detect()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph) |
| **Acceptance criteria** | Every node has evidence chain. Evidence is immutable. Contradictions detected. Confidence traces to evidence. |
| **Risks** | Evidence chain length at scale. |

### E-005 — Cognitive Runtime

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Reality Runtime, Object Factory, Workspace Projection Engine, Context Transition Model, Synchronization, Failure Modes. |
| **Deliverables** | `app/cognitive/runtime.py` (RealityRuntime, ObjectFactory), `app/cognitive/projection.py` (ProjectionEngine), `app/cognitive/context.py` (ContextTransition), `app/cognitive/sync.py` (Synchronization), `app/cognitive/failures.py` (FailureModes) |
| **Interfaces** | `RealityRuntime.ingest()`, `ObjectFactory.create()`, `ProjectionEngine.project()`, `ContextTransition.transition()`, `Synchronization.sync()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph), E-006 (Memory Engine), E-007 (Attention Engine), E-008 (Intent Pipeline), E-009 (Event Bus) |
| **Acceptance criteria** | Object created from external input. Projection assembled in < 100ms. Context transitions in < 250ms. Multiple clients synchronised. |
| **Risks** | Complexity of coordinating all sub-engines. |

### E-006 — Memory Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the canonical memory model: Working Memory, Conversation Memory, Relationship Memory, Knowledge Memory, Historical Memory, Constitutional Memory. Promotion, decay, consolidation. |
| **Deliverables** | `app/memory/models.py` (MemoryLayer, MemoryItem), `app/memory/engine.py` (MemoryEngine, ConsolidationEngine) |
| **Interfaces** | `MemoryEngine.store()`, `MemoryEngine.retrieve()`, `MemoryEngine.promote()`, `ConsolidationEngine.consolidate()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph) |
| **Acceptance criteria** | 6 layers with correct lifetimes. Promotion works. Decay follows formulas. Consolidation runs on schedule. |
| **Risks** | Memory capacity at scale. |

### E-007 — Attention Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Attention Engine: attention levels (Active, Background, Ambient, Interrupted, Returning), scoring, decay, promotion, demotion, interruption policy. |
| **Deliverables** | `app/attention/engine.py` (AttentionEngine, AttentionScorer, InterruptionPolicy) |
| **Interfaces** | `AttentionEngine.focus()`, `AttentionEngine.score()`, `AttentionEngine.get_attention_queue()`, `InterruptionPolicy.evaluate()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph) |
| **Acceptance criteria** | Attention scores are deterministic. Decay follows formulas. Promotion/demotion works. Interruption policy enforced. |
| **Risks** | Scoring performance at scale. |

### E-008 — Intent Pipeline

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Universal Intent Pipeline: natural language, intent classification, object resolution, relationship resolution, policy evaluation, deterministic execution, reasoning escalation, workspace update. |
| **Deliverables** | `app/intent/pipeline.py` (IntentPipeline), `app/intent/classifier.py` (IntentClassifier), `app/intent/resolver.py` (ObjectResolver, RelationshipResolver) |
| **Interfaces** | `IntentPipeline.process()`, `IntentClassifier.classify()`, `ObjectResolver.resolve()`, `RelationshipResolver.resolve()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph), E-018 (Relationship Engine) |
| **Acceptance criteria** | 10 intents classified correctly. Object resolution in < 100ms. Policy evaluation in < 50ms. Deterministic execution in < 200ms. |
| **Risks** | NLU quality without LLM dependency. |

### E-009 — Event Bus

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Cognitive Event Bus: event envelope, canonical events, publishing, subscribing, ordering, retention, consumer registry. |
| **Deliverables** | `app/eventbus/bus.py` (EventBus), `app/eventbus/events.py` (canonical events), `app/eventbus/registry.py` (ConsumerRegistry) |
| **Interfaces** | `EventBus.publish()`, `EventBus.subscribe()`, `EventBus.unsubscribe()`, `ConsumerRegistry.register()` |
| **Dependencies** | E-001 (Ontology Engine) |
| **Acceptance criteria** | Events published in < 10ms. Consumers receive events in < 50ms. Ordering preserved. Retention enforced. |
| **Risks** | Event throughput at scale. |

### E-010 — Adaptive Runtime

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Adaptive Learning Engine, Execution Learning Engine, Knowledge Evolution Engine, Reasoning Calibration, Prediction Evolution, Self-Calibration, Evolution Timeline. |
| **Deliverables** | `app/adaptive/learning.py` (AdaptiveLearningEngine), `app/adaptive/execution.py` (ExecutionLearningEngine), `app/adaptive/knowledge.py` (KnowledgeEvolutionEngine), `app/adaptive/calibration.py` (ReasoningCalibration, SelfCalibration), `app/adaptive/prediction.py` (PredictionEvolution), `app/adaptive/timeline.py` (EvolutionTimeline) |
| **Interfaces** | `AdaptiveLearningEngine.learn()`, `KnowledgeEvolutionEngine.promote()`, `ReasoningCalibration.calibrate()`, `SelfCalibration.run()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph), E-004 (Evidence Engine), E-011 (Confidence Engine) |
| **Acceptance criteria** | Learning follows 6 stages. Promotion thresholds enforced. Calibration runs on schedule. Evolution timeline operates at all 6 timescales. |
| **Risks** | Over-learning. False pattern detection. |

### E-011 — Confidence Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Confidence Engine: initial confidence, derived confidence, relationship confidence, prediction confidence, execution confidence, confidence decay, promotion, inheritance, combination. |
| **Deliverables** | `app/confidence/engine.py` (ConfidenceEngine), `app/confidence/models.py` (ConfidenceScore, ConfidenceExplanation) |
| **Interfaces** | `ConfidenceEngine.assign()`, `ConfidenceEngine.propagate()`, `ConfidenceEngine.combine()`, `ConfidenceEngine.decay()`, `ConfidenceEngine.explain()` |
| **Dependencies** | E-001 (Ontology Engine), E-004 (Evidence Engine) |
| **Acceptance criteria** | All 5 confidence types computed. Propagation formula correct. Combination formula correct. Decay follows λ. Confidence always explainable. |
| **Risks** | Over-confidence. Confidence inflation. |

### E-012 — Perception Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Universal Perception Architecture: Observation Pipeline (capture, validation, classification, deduplication, normalisation, identity resolution, confidence, evidence, KG update), Reality Detection, Continuous Observation, Attention Trigger Engine, Context Extraction, Conflict Resolution. |
| **Deliverables** | `app/perception/pipeline.py` (ObservationPipeline), `app/perception/sources.py` (SourceRegistry, Sensor), `app/perception/reality.py` (RealityDetection), `app/perception/continuous.py` (ContinuousObservation), `app/perception/attention.py` (AttentionTrigger), `app/perception/context.py` (ContextExtraction), `app/perception/conflict.py` (ConflictResolution) |
| **Interfaces** | `ObservationPipeline.process()`, `SourceRegistry.register()`, `RealityDetection.detect()`, `ContinuousObservation.start()`, `AttentionTrigger.score()`, `ConflictResolution.resolve()` |
| **Dependencies** | E-001 (Ontology Engine), E-002 (Identity Engine), E-003 (Knowledge Graph), E-004 (Evidence Engine), E-009 (Event Bus) |
| **Acceptance criteria** | 9-stage pipeline completes in < 500ms. 11 source types supported. 6 detection types correct. 6 observation modes work. 5 conflict types resolved. |
| **Risks** | Noise from unstructured sources. Signal volume. |

### E-013 — Execution Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Execution Intelligence Architecture: Execution Object Model, Lifecycle, Dependency Engine, Context Engine, Execution Planner, Orchestrator, Observation, Verification, Learning, Risk Engine, Event Bus, Projections, Governance. |
| **Deliverables** | `app/execution/models.py` (Execution, ExecutionPlan, ExecutionStep, ExecutionOutcome), `app/execution/lifecycle.py` (ExecutionLifecycle), `app/execution/dependency.py` (DependencyEngine), `app/execution/context.py` (ExecutionContext), `app/execution/planner.py` (ExecutionPlanner), `app/execution/orchestrator.py` (ExecutionOrchestrator), `app/execution/observation.py` (ExecutionObservation), `app/execution/verification.py` (ExecutionVerification), `app/execution/learning.py` (ExecutionLearning), `app/execution/risk.py` (ExecutionRiskEngine), `app/execution/governance.py` (ExecutionGovernance) |
| **Interfaces** | `ExecutionPlanner.plan()`, `ExecutionOrchestrator.execute()`, `ExecutionObservation.observe()`, `ExecutionVerification.verify()`, `ExecutionGovernance.authorise()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph), E-004 (Evidence Engine), E-005 (Cognitive Runtime), E-008 (Intent Pipeline), E-009 (Event Bus), E-010 (Adaptive Runtime), E-011 (Confidence Engine) |
| **Acceptance criteria** | 14-state lifecycle correct. 7 dependency types handled. Plan created in < 500ms. Parallel execution works. Rollback reverses steps. Verification passes. |
| **Risks** | Execution complexity. Rollback reliability. |

### E-014 — Decision Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Decision Intelligence Architecture: Decision Object Model, Lifecycle, Context Engine, Alternative Generation, Evaluation, Ranking, Governance, Evidence, Learning, Event Bus, Projections, Explainability. |
| **Deliverables** | `app/decision/models.py` (Decision, DecisionOption, DecisionOutcome), `app/decision/lifecycle.py` (DecisionLifecycle), `app/decision/context.py` (DecisionContext), `app/decision/alternatives.py` (AlternativeGeneration), `app/decision/evaluation.py` (DecisionEvaluation), `app/decision/ranking.py` (DecisionRanking), `app/decision/governance.py` (DecisionGovernance), `app/decision/evidence.py` (DecisionEvidence), `app/decision/learning.py` (DecisionLearning), `app/decision/explainability.py` (DecisionExplainability) |
| **Interfaces** | `DecisionEvaluation.evaluate()`, `DecisionRanking.rank()`, `DecisionGovernance.approve()`, `DecisionExplainability.explain()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph), E-004 (Evidence Engine), E-005 (Cognitive Runtime), E-010 (Adaptive Runtime), E-011 (Confidence Engine), E-013 (Execution Engine) |
| **Acceptance criteria** | 12-stage lifecycle correct. 9 evaluation dimensions scored. Ranking deterministic. 4 governance levels enforced. 5 explainability questions answered. |
| **Risks** | Evaluation quality without AI. |

### E-015 — Workspace Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Founder Workspace: Three-zone layout, Universal Object Model, State Management, Routing Model, Conversation Integration, Context Persistence, Relationship Navigation, Responsive Layouts, Accessibility, Performance Strategy. |
| **Deliverables** | `app/workspace/layout.py` (three-zone layout), `app/workspace/renderer.py` (UniversalObjectRenderer), `app/workspace/routing.py` (WorkspaceRouter), `app/workspace/composer.py` (UniversalComposer), `app/workspace/state.py` (WorkspaceState), `app/workspace/persistence.py` (ContextPersistence), `app/workspace/search.py` (SearchIntegration) |
| **Interfaces** | `WorkspaceRouter.route()`, `UniversalObjectRenderer.render()`, `UniversalComposer.process()`, `WorkspaceState.get()`, `ContextPersistence.save()` |
| **Dependencies** | E-005 (Cognitive Runtime), E-020 (Projection Engine) |
| **Acceptance criteria** | Three-zone layout renders. Object switching < 250ms. Composer processes intents. Responsive at 3 breakpoints. WCAG 2.1 AA compliant. |
| **Risks** | Browser compatibility. Template rendering performance. |

### E-016 — Governance Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Architecture Governance Framework: Repository, Conformance, Traceability, Change Process, ADRs, Dependency Governance, Invariant Enforcement, Reference Integrity, Health Metrics, Projection. |
| **Deliverables** | `app/governance/repository.py` (DocumentRegistry), `app/governance/conformance.py` (ConformanceChecker), `app/governance/traceability.py` (TraceabilityMatrix), `app/governance/changes.py` (ChangePipeline), `app/governance/adr.py` (ADRManager), `app/governance/dependencies.py` (DependencyValidator), `app/governance/invariants.py` (InvariantEnforcer), `app/governance/health.py` (HealthMetrics) |
| **Interfaces** | `ConformanceChecker.check()`, `TraceabilityMatrix.trace()`, `ChangePipeline.propose()`, `DependencyValidator.validate()`, `InvariantEnforcer.enforce()`, `HealthMetrics.scan()` |
| **Dependencies** | All previous epics (E-001 through E-015) |
| **Acceptance criteria** | All documents registered. Conformance verified. Traceability complete. ADRs created. Dependencies validated. Invariants enforced. 6 health metrics computed. |
| **Risks** | Governance overhead. False positives. |

### E-017 — Policy Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Policy Engine: policy types, hierarchy, lifecycle, versioning, evaluation, audit. |
| **Deliverables** | `app/policy/models.py` (Policy, PolicyType), `app/policy/engine.py` (PolicyEngine, PolicyEvaluator), `app/policy/lifecycle.py` (PolicyLifecycle) |
| **Interfaces** | `PolicyEngine.evaluate()`, `PolicyEngine.create()`, `PolicyLifecycle.approve()`, `PolicyLifecycle.rollback()` |
| **Dependencies** | E-001 (Ontology Engine), E-010 (Adaptive Runtime) |
| **Acceptance criteria** | 6 policy types supported. Hierarchy enforced. Versioning works. Rollback restores previous version. All changes auditable. |
| **Risks** | Policy conflict resolution. |

### E-018 — Relationship Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Relationship Engine: canonical edge families, relationship lifecycle, validation, traversal, indexing. |
| **Deliverables** | `app/relationship/engine.py` (RelationshipEngine), `app/relationship/families.py` (edge families), `app/relationship/index.py` (RelationshipIndex) |
| **Interfaces** | `RelationshipEngine.create()`, `RelationshipEngine.get_neighbours()`, `RelationshipEngine.traverse()`, `RelationshipIndex.query()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph) |
| **Acceptance criteria** | 14 edge families supported. 1-hop traversal O(1). 2-hop traversal O(degree²). Lifecycle correct. |
| **Risks** | Index size at scale. |

### E-019 — Temporal Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Temporal Graph: historical edges, future edges, scheduled edges, expired edges, superseded edges, alternative timelines, point-in-time queries, range queries, change queries. |
| **Deliverables** | `app/temporal/engine.py` (TemporalEngine), `app/temporal/edges.py` (temporal edge types), `app/temporal/query.py` (TemporalQuery) |
| **Interfaces** | `TemporalEngine.create_temporal_edge()`, `TemporalQuery.point_in_time()`, `TemporalQuery.range()`, `TemporalQuery.changes()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph), E-018 (Relationship Engine) |
| **Acceptance criteria** | 6 temporal edge types. Point-in-time query correct. Range query correct. Change query correct. |
| **Risks** | Temporal query performance at scale. |

### E-020 — Projection Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Graph Projection Engine: 10 projection types, context resolution, assembly, caching, invalidation, degraded mode. |
| **Deliverables** | `app/projection/engine.py` (ProjectionEngine), `app/projection/types.py` (projection types), `app/projection/cache.py` (ProjectionCache), `app/projection/resolution.py` (ContextResolution) |
| **Interfaces** | `ProjectionEngine.project()`, `ContextResolution.resolve()`, `ProjectionCache.get()`, `ProjectionCache.invalidate()` |
| **Dependencies** | E-001 (Ontology Engine), E-003 (Knowledge Graph), E-018 (Relationship Engine) |
| **Acceptance criteria** | 10 projection types assemble correctly. Context resolution in < 200ms. Cache invalidation on relevant events. Degraded mode returns minimal projection. |
| **Risks** | Cache invalidation accuracy. |

---

## PART 4 — Implementation Order

### Critical path

```
Sprint 1-2:   E-001 (Ontology Engine) → Foundation
                ↓
Sprint 2-4:   E-003 (Knowledge Graph) + E-002 (Identity Engine) → Graph layer
                ↓
Sprint 3-5:   E-018 (Relationship Engine) + E-004 (Evidence Engine) → Graph capabilities
                ↓
Sprint 4-6:   E-005 (Cognitive Runtime) + E-009 (Event Bus) → Runtime
                ↓
Sprint 5-7:   E-006 (Memory) + E-007 (Attention) + E-008 (Intent) → Cognitive sub-engines
                ↓
Sprint 6-8:   E-010 (Adaptive Runtime) + E-011 (Confidence) → Learning
                ↓
Sprint 7-9:   E-012 (Perception) + E-013 (Execution) + E-014 (Decision) → Capabilities
                ↓
Sprint 9-11:  E-019 (Temporal) + E-020 (Projection) → Advanced capabilities
                ↓
Sprint 10-12: E-015 (Workspace) → User-facing surface
                ↓
Sprint 11-13: E-017 (Policy) → Governance
                ↓
Sprint 12-14: E-016 (Governance) → Meta-governance
```

### Parallel work

| Sprint | Parallel tracks |
|--------|----------------|
| 1-2 | E-001 (Ontology) |
| 2-4 | E-003 (Knowledge Graph) + E-002 (Identity) |
| 3-5 | E-018 (Relationships) + E-004 (Evidence) + E-009 (Event Bus) |
| 4-6 | E-005 (Cognitive Runtime) + E-006 (Memory) |
| 5-7 | E-007 (Attention) + E-008 (Intent) + E-011 (Confidence) |
| 6-8 | E-010 (Adaptive Runtime) + E-019 (Temporal) |
| 7-9 | E-012 (Perception) + E-013 (Execution) + E-014 (Decision) |
| 9-11 | E-020 (Projection) + E-017 (Policy) |
| 10-12 | E-015 (Workspace) |
| 12-14 | E-016 (Governance) |

### Blocking dependencies

| Epic | Blocked by | Blocks |
|------|------------|--------|
| E-001 | — | All epics |
| E-002 | E-001 | E-005, E-012 |
| E-003 | E-001 | E-004, E-005, E-006, E-007, E-008, E-012, E-013, E-018, E-019, E-020 |
| E-004 | E-001, E-003 | E-010, E-011, E-012, E-013, E-014 |
| E-005 | E-001, E-003 | E-013, E-014, E-015 |
| E-009 | E-001 | E-005, E-012, E-013, E-014 |
| E-010 | E-001, E-003, E-004 | E-013, E-014, E-017 |
| E-015 | E-005, E-020 | — |
| E-016 | All | — |

### Independent work (no cross-blocking)

| Group | Epics | Can start |
|-------|-------|-----------|
| Foundation | E-001 | Sprint 1 |
| Graph | E-002, E-003, E-018, E-019 | Sprint 2 |
| Cognition | E-005, E-006, E-007, E-008, E-009 | Sprint 3 |
| Adaptation | E-010, E-011, E-017 | Sprint 4 |
| Capabilities | E-012, E-013, E-014 | Sprint 5 |
| Surface | E-015, E-020 | Sprint 7 |
| Governance | E-016 | Sprint 10 |

---

## PART 5 — Effort Estimation

### Estimated files per epic

| Epic | Modules | Core services | Tests | Config | Total files |
|------|---------|---------------|-------|--------|-------------|
| E-001 (Ontology) | 5 | 0 | 5 | 1 | 11 |
| E-002 (Identity) | 3 | 1 | 4 | 1 | 9 |
| E-003 (Knowledge Graph) | 8 | 2 | 8 | 2 | 20 |
| E-004 (Evidence) | 3 | 1 | 4 | 1 | 9 |
| E-005 (Cognitive Runtime) | 6 | 2 | 6 | 2 | 16 |
| E-006 (Memory) | 3 | 1 | 3 | 1 | 8 |
| E-007 (Attention) | 2 | 1 | 3 | 1 | 7 |
| E-008 (Intent Pipeline) | 3 | 1 | 4 | 1 | 9 |
| E-009 (Event Bus) | 3 | 1 | 3 | 1 | 8 |
| E-010 (Adaptive Runtime) | 6 | 2 | 6 | 2 | 16 |
| E-011 (Confidence) | 2 | 1 | 3 | 1 | 7 |
| E-012 (Perception) | 7 | 2 | 7 | 2 | 18 |
| E-013 (Execution) | 10 | 3 | 10 | 2 | 25 |
| E-014 (Decision) | 10 | 3 | 10 | 2 | 25 |
| E-015 (Workspace) | 7 | 1 | 5 | 3 | 16 |
| E-016 (Governance) | 6 | 1 | 5 | 1 | 13 |
| E-017 (Policy) | 3 | 1 | 3 | 1 | 8 |
| E-018 (Relationship) | 3 | 1 | 4 | 1 | 9 |
| E-019 (Temporal) | 3 | 1 | 4 | 1 | 9 |
| E-020 (Projection) | 4 | 1 | 4 | 1 | 10 |
| **Total** | **97** | **27** | **101** | **28** | **253** |

### Estimated lines of code

| Epic | Est. modules LOC | Est. tests LOC | Total |
|------|-----------------|----------------|-------|
| E-001 | 1500 | 1500 | 3000 |
| E-002 | 1200 | 1200 | 2400 |
| E-003 | 4000 | 3000 | 7000 |
| E-004 | 1200 | 1200 | 2400 |
| E-005 | 3000 | 2500 | 5500 |
| E-006 | 1200 | 1000 | 2200 |
| E-007 | 800 | 800 | 1600 |
| E-008 | 1200 | 1000 | 2200 |
| E-009 | 1000 | 800 | 1800 |
| E-010 | 3000 | 2500 | 5500 |
| E-011 | 800 | 800 | 1600 |
| E-012 | 3500 | 3000 | 6500 |
| E-013 | 5000 | 4000 | 9000 |
| E-014 | 5000 | 4000 | 9000 |
| E-015 | 3000 | 1500 | 4500 |
| E-016 | 2000 | 1500 | 3500 |
| E-017 | 1000 | 800 | 1800 |
| E-018 | 1200 | 1000 | 2200 |
| E-019 | 1200 | 1000 | 2200 |
| E-020 | 1500 | 1200 | 2700 |
| **Total** | **42,300** | **33,300** | **75,600** |

---

## PART 6 — Milestone Plan

### Milestone 1: Foundation (Sprints 1-2)

| Epic | Deliverables | Acceptance |
|------|-------------|------------|
| E-001 (Ontology) | Object model, type system, state machine, timeline, context | 1000 objects created. All types valid. State transitions correct. |
| E-002 (Identity) | Identity store, merge/split, retirement, governance | Identities permanent. Merge preserves history. |

### Milestone 2: Graph Layer (Sprints 2-4)

| Epic | Deliverables | Acceptance |
|------|-------------|------------|
| E-003 (Knowledge Graph) | Node store, edge store, families, temporal, consistency, security | 1M nodes. 10M edges. 1-hop < 10ms. |
| E-018 (Relationship) | 14 edge families, lifecycle, validation, index | 1-hop O(1). All families supported. |
| E-004 (Evidence) | Evidence engine, chain, contradiction detection | Every node has evidence. Contradictions detected. |

### Milestone 3: Cognitive Runtime (Sprints 4-6)

| Epic | Deliverables | Acceptance |
|------|-------------|------------|
| E-009 (Event Bus) | Event bus, publishing, subscribing, retention | Events < 10ms. Consumers < 50ms. |
| E-005 (Cognitive Runtime) | Reality runtime, object factory, projection engine, context transition, sync, failures | Projection < 100ms. Context transition < 250ms. |
| E-006 (Memory) | 6 memory layers, promotion, decay, consolidation | Layers correct. Decay follows formula. |
| E-007 (Attention) | Attention scoring, levels, decay, interruption | Deterministic scoring. Interruption policy enforced. |
| E-008 (Intent Pipeline) | 8-stage pipeline, intent classification, resolution | 10 intents. Resolution < 100ms. |

### Milestone 4: Adaptation (Sprints 5-7)

| Epic | Deliverables | Acceptance |
|------|-------------|------------|
| E-011 (Confidence) | 5 confidence types, propagation, decay, explanation | All types computed. Explainable. |
| E-010 (Adaptive Runtime) | Learning engine, execution learning, knowledge evolution, calibration, prediction evolution, self-calibration, evolution timeline | 6 learning stages. Calibration on schedule. |
| E-019 (Temporal) | 6 temporal edge types, point-in-time/range/change queries | Queries correct. |

### Milestone 5: Capabilities (Sprints 7-9)

| Epic | Deliverables | Acceptance |
|------|-------------|------------|
| E-012 (Perception) | 9-stage pipeline, 11 sources, 6 detection types, 6 observation modes, 5 conflict types | Pipeline < 500ms. All sources supported. |
| E-013 (Execution) | 14-state lifecycle, 7 dependency types, planner, orchestrator, verification, governance | Plan < 500ms. Rollback works. Verification passes. |
| E-014 (Decision) | 12-stage lifecycle, 9 evaluation dimensions, ranking, governance, explainability | Ranking deterministic. 5 questions answerable. |

### Milestone 6: Surface (Sprints 9-11)

| Epic | Deliverables | Acceptance |
|------|-------------|------------|
| E-020 (Projection) | 10 projection types, context resolution, caching, degraded mode | Projections correct. Cache invalidates. |
| E-017 (Policy) | 6 policy types, hierarchy, lifecycle, versioning | Hierarchy enforced. Rollback works. |
| E-015 (Workspace) | Three-zone layout, object renderer, composer, routing, state, persistence, search | Object switch < 250ms. Composer works. Responsive. |

### Milestone 7: Governance (Sprints 12-14)

| Epic | Deliverables | Acceptance |
|------|-------------|------------|
| E-016 (Governance) | Repository, conformance, traceability, changes, ADRs, dependency validation, invariants, health | All documents registered. Invariants enforced. 6 health metrics. |

---

## PART 7 — Milestone-to-Architecture Mapping

| Milestone | Architecture documents | Sections |
|-----------|----------------------|----------|
| M1 — Foundation | D01 (Ontology) | §1–§20 |
| M2 — Graph Layer | D01 (Ontology), D04 (Knowledge Graph) | D01 §1–§7, D04 §1–§5 |
| M3 — Cognitive Runtime | D02 (Cognitive Runtime) | D02 §1–§12 |
| M4 — Adaptation | D03 (Adaptive Runtime) | D03 §1–§15 |
| M5 — Capabilities | D06 (Execution), D07 (Perception), D08 (Decision) | D06 §1–§14, D07 §1–§13, D08 §1–§14 |
| M6 — Surface | D05 (Workspace) | D05 §1–§14 |
| M7 — Governance | D09 (Governance Framework) | D09 §1–§14 |

---

## PART 8 — Implementation Risks

### Risk register

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R-01 | Knowledge Graph performance at 100M nodes | Medium | High | Start with in-memory graph, migrate to dedicated store at scale. Design for storage abstraction from day 1. |
| R-02 | Intent Pipeline quality without AI | Medium | High | Deterministic pattern matching handles 80%+ of intents. AI escalation for remaining 20%. Define clear deterministic/AI boundary. |
| R-03 | Perception noise from unstructured sources | High | Medium | Source confidence baseline filters low-confidence signals. Unstructured sources have lowest baseline (0.4). |
| R-04 | Execution rollback reliability | Medium | High | Every step defines rollback procedure. Rollback tested in CI. Emergency stop for non-rollbackable executions. |
| R-05 | Decision evaluation quality | Medium | Medium | 9 evaluation dimensions provide comprehensive coverage. Weights are configurable by policy. |
| R-06 | Event bus throughput at scale | Medium | Medium | Partitioned event bus. Subscription-based filtering. Background consumers. |
| R-07 | Memory capacity | Low | Medium | Temporal observation expiry. Layered storage (hot/warm/cold). |
| R-08 | Identity resolution at 100M identities | Medium | High | Indexed identity store. Resolution is O(1) for permanent identities. |
| R-09 | Cross-team coordination | Medium | Medium | Clear dependency graph. Parallel work tracks. Weekly sync. |
| R-10 | Architecture drift | Medium | Medium | Governance engine (E-016) detects drift. Health metrics scanned weekly. |

### Risk distribution

| Severity | Count | IDs |
|----------|-------|-----|
| High | 3 | R-01, R-02, R-04, R-08 |
| Medium | 5 | R-03, R-05, R-06, R-09, R-10 |
| Low | 1 | R-07 |

---

## PART 9 — Testing Roadmap

### Test architecture

| Test level | What it covers | Tooling | Frequency |
|------------|---------------|---------|-----------|
| **Unit tests** | Individual functions, classes, methods | pytest | Every commit |
| **Integration tests** | Cross-subsystem interactions | pytest + fixtures | Every merge |
| **System tests** | End-to-end flows | pytest + test app | Every release |
| **Invariant tests** | All 43 constitutional invariants | pytest + governance hooks | Every commit |
| **Performance tests** | Latency targets, throughput | pytest-benchmark | Every release |
| **Security tests** | Visibility, permissions, audit | pytest + security fixtures | Every release |

### Test estimation

| Epic | Unit tests | Integration tests | Invariant tests | Total tests |
|------|------------|-------------------|-----------------|-------------|
| E-001 | 50 | 10 | 20 | 80 |
| E-002 | 40 | 10 | 6 | 56 |
| E-003 | 100 | 30 | 15 | 145 |
| E-004 | 40 | 15 | 5 | 60 |
| E-005 | 80 | 25 | 15 | 120 |
| E-006 | 30 | 10 | 5 | 45 |
| E-007 | 25 | 10 | 5 | 40 |
| E-008 | 30 | 15 | 5 | 50 |
| E-009 | 25 | 15 | 5 | 45 |
| E-010 | 80 | 25 | 15 | 120 |
| E-011 | 25 | 10 | 5 | 40 |
| E-012 | 100 | 30 | 10 | 140 |
| E-013 | 120 | 40 | 15 | 175 |
| E-014 | 120 | 40 | 15 | 175 |
| E-015 | 50 | 20 | 10 | 80 |
| E-016 | 50 | 15 | 43 | 108 |
| E-017 | 25 | 10 | 5 | 40 |
| E-018 | 30 | 15 | 6 | 51 |
| E-019 | 30 | 15 | 5 | 50 |
| E-020 | 40 | 15 | 5 | 60 |
| **Total** | **1090** | **385** | **210** | **1685** |

### Testing milestones

| Milestone | Cumulative tests | Key test areas |
|-----------|-----------------|----------------|
| M1 — Foundation | 136 | Object creation, identity, state transitions |
| M2 — Graph Layer | 392 | Node/edge operations, traversal, evidence, relationships |
| M3 — Cognitive Runtime | 647 | Projection, attention, memory, intent pipeline, event bus |
| M4 — Adaptation | 847 | Confidence, learning, calibration, temporal queries |
| M5 — Capabilities | 1337 | Perception pipeline, execution lifecycle, decision evaluation |
| M6 — Surface | 1517 | Projections, policies, workspace rendering, composer |
| M7 — Governance | 1685 | Conformance, invariants, health metrics, ADRs |

---

## PART 10 — Deployment Roadmap

### Deployment phases

| Phase | Milestone | What ships | Deployment target |
|-------|-----------|------------|-------------------|
| **Alpha** | M1–M2 | Foundation + Graph layer | Internal development environment |
| **Beta** | M3–M4 | Cognitive Runtime + Adaptation | Staging environment, invited testers |
| **Preview** | M5 | Capabilities (Perception, Execution, Decision) | Limited production with selected founders |
| **General Availability** | M6–M7 | Surface + Governance | Production |

### Environment strategy

| Environment | Purpose | Deploys from | Data |
|-------------|---------|-------------|------|
| **Development** | Daily development, unit tests | Feature branches | Synthetic data |
| **Integration** | Cross-team integration, integration tests | Merge to develop | Synthetic data + limited real data |
| **Staging** | System tests, performance tests, acceptance tests | Release branch | Anonymized production data |
| **Production** | Live system | Main branch | Production data |

### CI/CD pipeline

```
Feature branch → Unit tests → Invariant tests → Build
  ↓
Merge to develop → Integration tests → Package
  ↓
Release branch → System tests → Performance tests → Security tests
  ↓
Deploy to staging → Acceptance tests → Smoke tests
  ↓
Deploy to production → Canary → Full rollout
```

### Deployment frequency

| Phase | Frequency | Rollback window |
|-------|-----------|-----------------|
| Alpha | Daily | Immediate |
| Beta | Weekly | 24 hours |
| Preview | Bi-weekly | 7 days |
| GA | Monthly | 30 days |

---

## Appendix A: Summary Statistics

| Metric | Value |
|--------|-------|
| Architecture documents | 9 |
| Engineering epics | 20 |
| Estimated modules | 97 |
| Estimated core services | 27 |
| Estimated test files | 101 |
| Estimated total files | 253 |
| Estimated lines of code | 75,600 |
| Estimated tests | 1,685 |
| Implementation milestones | 7 |
| Estimated sprints | 14 |
| Estimated team size | 4–6 engineers |
| Estimated timeline | 14 sprints (~7 months) |
| Critical path | E-001 → E-003 → E-005 → E-010 → E-013/E-014 → E-015 → E-016 |
| Most complex epic | E-013 (Execution Engine) — 25 files, 9,000 LOC |
| Most complex milestone | M5 (Capabilities) — 3 epics, 68 files, 24,500 LOC |