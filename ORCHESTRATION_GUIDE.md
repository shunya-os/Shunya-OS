# SHUNYA System Integration & Orchestration — Developer Documentation

> **Milestone IV — Architecturally Complete: 12 subsystems integrated**
>
> This document covers orchestration architecture, sequence diagrams, context lifecycle,
> module interaction diagrams, extension guidance, and best practices for future
> intelligence modules.

---

## 1. Orchestration Architecture

```
                    ┌─────────────────────────────────┐
                    │     OrchestratorEngine           │
                    │  (Facade — entry point)          │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────▼────────────────────┐
                    │       PipelineExecutor           │
                    │  (Deterministic pipeline flow)   │
                    └────────────┬────────────────────┘
                                 │
    ┌──────────────┬──────────────┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼              ▼
 ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
 │Context │  │Contract│  │Unified │  │Integ.  │  │Pipeline│  │Pipeline│
 │Propag. │  │Validat.│  │Explain │  │Profiler│  │Context │  │Result  │
 └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

## 2. Canonical Pipeline Sequence

```
OrchestratorEngine      PipelineExecutor        ContextPropagator       Subsystems
       │                       │                      │                    │
       │── run_pipeline() ────►│                      │                    │
       │                       │── propagate() ──────►│                    │
       │                       │   (BusinessEvent)    │                    │
       │                       │                      │──► Execution ─────►│
       │                       │── propagate() ──────►│                    │
       │                       │   (Execution)        │──► Awareness ─────►│
       │                       │── propagate() ──────►│                    │
       │                       │   (Awareness)        │──► Org ───────────►│
       │                       │── propagate() ──────►│                    │
       │                       │   (Organization)     │──► Learning ──────►│
       │                       │── propagate() ──────►│                    │
       │                       │   (Learning)         │──► Prediction ────►│
       │                       │── propagate() ──────►│                    │
       │                       │   (Prediction)       │──► Planner ───────►│
       │                       │── propagate() ──────►│                    │
       │                       │   (Planner)          │──► Governance ────►│
       │                       │── propagate() ──────►│                    │
       │                       │   (Response)         │                    │
       │◄────── PipelineResult───────────────────────│                    │
```

## 3. Context Lifecycle

### 3.1 State Machine

```
BUSINESS_EVENT ──► ENTITY_RESOLUTION ──► EXECUTION ──► EVIDENCE ──►
AWARENESS ──► ORGANIZATION ──► LEARNING ──► PREDICTION ──►
PLANNER ──► GOVERNANCE ──► RESPONSE
```

Each stage enriches context, never replaces:

```python
# Stage N output
ctx = propagator.propagate(ctx, "execution", {"exec_id": "e1", "state": "active"})
# Stage N+1 output — previous data preserved
ctx = propagator.propagate(ctx, "awareness", {"ingested": 1})
# ctx.execution_state still has {"exec_id": "e1", "state": "active"}
# ctx.awareness_state has {"ingested": 1}
```

### 3.2 Snapshot Fields

| Context Field | Populated By | Contains |
|---|---|---|
| `business_event` | Stage 0 | Raw event from caller |
| `execution_state` | Stage 2 | exec_id, state, commitment_type |
| `evidence_state` | Stage 3 | observation_ids |
| `awareness_state` | Stage 4 | ingestion result |
| `organization_state` | Stage 5 | org engine stats |
| `learning_snapshot` | Stage 6 | pattern/profile counts |
| `prediction_snapshot` | Stage 7 | prediction outputs |
| `planner_snapshot` | Stage 8 | planned step count |
| `governance_snapshot` | Stage 9 | governance verdict |

## 4. Module Interaction Diagram

```
ExecutionService ◄── ExecutionIntelligenceEngine
     │                        │
     │                        ▼
     │              PatternRecognitionEngine
     │              OutcomeLearningEngine
     │                        │
     ▼                        ▼
Operational           LearningIntelligenceEngine
Awareness                    │
     │                       ▼
     │              PredictionEngine
     │                       │
     ▼                       ▼
Organizational         ScenarioComparator
Intelligence                 │
     │                       ▼
     │              PlannerLayer
     │                       │
     ▼                       ▼
EvidenceRuntime        GovernanceLayer
Service                      │
                            ▼
                     OrchestratorEngine
                     (coordinates all above)
```

## 5. Canonical Pipeline Flow — Complete Sequence

```
Business Event
    │
    ▼
1. ENTITY RESOLUTION: Resolve entity_type, entity_id from event
    │
    ▼
2. EXECUTION: ExecutionService.activate() → BusinessExecutionInstance
   Create execution, establish state, set obligations
    │
    ▼
3. EVIDENCE: Collect observations, link evidence to execution
   (Simulated in pipeline — real ingestion is app-specific)
    │
    ▼
4. AWARENESS: get_awareness_engine().ingest() → CanonicalObservation
   Update awareness state, trigger continuous risk monitor
    │
    ▼
5. ORGANIZATION: get_organizational_intelligence().stats()
   Assess org health, role assignments, responsibility coverage
    │
    ▼
6. LEARNING: get_learning_intelligence().learn_from_outcomes()
   Update patterns, outcome profiles, recommendation refinements
    │
    ▼
7. PREDICTION: get_prediction_engine().predict()
   Generate completion, delay, dependency forecasts
    │
    ▼
8. PLANNER: PlannerLayer()
   Generate execution plan with step sequencing
    │
    ▼
9. GOVERNANCE: GovernanceLayer()
   Validate plan against policies, approve/reject
    │
    ▼
10. RESPONSE: Aggregate recommendations and governance verdict
```

## 6. Cross-Module Contracts

### Contract Catalogue (6 contracts, machine-readable)

| ID | Source → Target | Rule | Severity |
|---|---|---|---|
| C1 | execution → all | No mutation of canonical state by intelligence layers | ERROR |
| C2 | prediction → all | Predictions remain derived | ERROR |
| C3 | learning → awareness | Learning consumes evidence only | WARNING |
| C4 | governance → response | Governance before actionable recommendations | ERROR |
| C5 | context → all | Context enriched, not replaced | WARNING |
| C6 | all → all | No cross-module ownership mutation | ERROR |

### Enforcement

Contracts are validated by `ContractValidator.validate(ctx)` which checks the
pipeline context provenance chain. Violations are returned as structured
`ContractViolation` objects with severity levels.

## 7. PipelineResult Structure

```python
@dataclass
class PipelineResult:
    pipeline_id: str        # Deterministic hash of pipeline execution
    success: bool            # True if no errors
    recommendations: List    # Final recommendations (governance-approved)
    governance_verdict: Dict # Approved/Rejected + reason
    errors: List[str]        # Any errors encountered
    latency_seconds: float   # Total pipeline wall-clock time
    stages_completed: int    # Number of stages that executed
    explanation: Dict        # End-to-end explanation graph
```

## 8. Extension Guidance for Future Intelligence Modules

### Adding a new pipeline stage

1. Add stage name to `PipelineStage` enum in `app/orchestrator/models.py`
2. Add stage handler in `PipelineExecutor.execute()`
3. Register stage in `ContextPropagator._enrich_snapshot()` field mapping
4. Add explanation node in `UnifiedExplainability.build_graph()`
5. Add any cross-module contracts to `ContractValidator._build_catalogue()`
6. Write integration tests

### Adding a new module that reads from existing modules

- Import the module's facade (e.g., `get_execution_intelligence()`)
- Use `read-only` access — never call `set`/`transition`/`mutate` methods
- Store results in `PipelineContext` via `ContextPropagator.propagate()`
- Add evidence traces to `UnifiedExplainability`

### Adding a new intelligence layer

- Must follow `app/<module>/` structure with `models.py` + `engine.py`
- Must expose a singleton facade (`get_<module>()` / `reset_<module>()`)
- Must not write to canonical execution state
- Must produce evidence-traced outputs
- Must be registered in the orchestrator's pipeline

## 9. Best Practices

1. **Always use `ContextPropagator.propagate()`** — never directly modify
   `PipelineContext` fields. The propagator ensures no data loss across stages.

2. **Validate contracts after every pipeline run** — run
   `engine.validate_contracts(ctx)` in non-production pipelines to catch
   violations early.

3. **Enable/disable stages via `OrchestratorConfig`** — don't comment out
   stage code. Use `config.enable_learning = False` etc.

4. **Check `result.success` before using recommendations** — a failed
   pipeline produces an empty recommendations list.

5. **Use `result.explanation` for debugging** — the explanation graph traces
   every stage's claims and evidence.

## 10. Performance Characteristics

| Metric | Expected | Notes |
|---|---|---|
| Full pipeline latency | < 50ms | All stages are in-memory deterministic functions |
| Context size | < 10KB per run | Provenance chain grows linearly with stages |
| Prediction overhead | < 1ms per category | O(n) where n = obligations |
| Learning overhead | < 2ms per batch | O(m) where m = outcome count |
| Simulation overhead | < 10ms per fork | copy.deepcopy() of ExecutionService |
| Memory per pipeline | < 1MB | No external allocations |
