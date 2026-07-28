# PHASE_J_IMPLEMENTATION_PLAN.md

**Governance Directive:** G9.0 — Phase J Authorization
**Engine:** Observer Engine (ES-006)
**Layer:** Observer

---

## Objectives

1. Implement canonical Observer Engine data models (ES-006 §2–3, §6)
2. Implement 9-stage deterministic observation pipeline (ES-006 §4)
3. Implement 6-dimension evidence validation (ES-006 §7)
4. Implement outcome comparison (expected vs actual per dimension)
5. Implement deviation detection with configurable tolerance thresholds
6. Implement anomaly detection (pattern-based)
7. Implement confidence assessment from evidence quality + deviation severity
8. Implement observation packaging + learning signal extraction
9. Implement backward-compatible legacy wrapper
10. Comprehensive test suite + independent verification

## Scope Boundaries

| In Scope | Out of Scope |
|----------|-------------|
| 8 observation types (passive, active, continuous, scheduled, event-driven, comparative, predictive, human-assisted) | Knowledge Engine write (not yet available) |
| 6-dimension evidence validation (completeness, authenticity, consistency, correlation, timestamp integrity, provenance) | Learning Engine handoff (not yet available) |
| Per-dimension deviation detection with tolerance thresholds | Event Bus integration |
| Anomaly detection (pattern-based) | Historical pattern persistence (Knowledge Engine dependency) |
| Confidence assessment from evidence + deviation | SQLAlchemy database storage (legacy file preserved) |
| Learning signal extraction | Telemetry/business metrics ingestion |
| Immutable observations after creation | Cross-workspace correlation |

## ES-006 Requirement Mapping

| ES-006 § | Requirement | Phase J Implementation |
|----------|-------------|----------------------|
| §1 | Observe every execution outcome | `ObserverEngine.observe()` |
| §1 | Never execute, plan, reason, govern | 8 SHALL NEVER rules enforced |
| §2 | Input contract: OutcomePackage + expected plan | `ObserverInput` dataclass |
| §3 | Output: VerifiedObservation, AnomalyReport, DeviationReport, LearningSignal | 4 output types |
| §4 | 9-stage pipeline | 9 explicit stages |
| §5 | 8 observation types | Enum with types defined |
| §6 | Observation model with variance, tolerance | `VerifiedObservation`, `ObservationVariance`, `Tolerance` |
| §7 | 6-dimension evidence validation | `_validate_evidence()` |
| §8 | 7 failure modes | `FailureMode` enum, all handled |

## Dependency Analysis

| Dependency | Status | Impact |
|------------|--------|--------|
| Phase I (Executor Engine) | ✅ Complete | Consumes OutcomePackage with evidence, metrics |
| Phase H (Governance Engine) | ✅ Complete | Approved plans available for comparison |
| Phase G (Planner Engine) | ✅ Complete | ExecutionPlan available for expected outcomes |
| `app/shunya/observer_learning.py` | ✅ Existing (318 lines) | Legacy SQLAlchemy-bound code; preserved |
| Credential store, Event Bus | Not available | Deferred — Observer uses in-memory storage |

**No dependency on ReasoningSession** — confirmed by prior phases.

## Public Interfaces Consumed

- **Phase I OutcomePackage**: `outcome_id`, `workflow_id`, `workflow_state`, `tasks`, `evidence`, `failures`, `metrics`
- **Phase I ExecutionEvidence**: `evidence_id`, `task_id`, `action`, `success`, `response`, `channel`
- **Phase G ExecutionPlan** (optional): for expected-outcome comparison

## Public Interfaces Exposed

```python
from app.shunya.observer_engine import (
    ObservationType, ObservationSeverity, EvidenceValidationStatus,
    ObserverInput, ObserverOutput,
    VerifiedObservation, ObservationState, ObservationVariance,
    Tolerance, DeviationReport, AnomalyReport,
    LearningSignal, ObservationPackage,
    ObserverEngine, get_observer_engine, reset_observer_engine,
    ObserverLayer,  # legacy compat
)
```

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| No Knowledge Engine for persistence | Medium | Observations stored in-memory; interface defined for future write |
| No Learning Engine for handoff | Low | LearningSignal produced and stored; delivery deferred |
| No historical anomaly pattern store | Low | Anomaly detection uses per-cycle patterns only |

## Testing Strategy

1. **Model tests** (~20): Observation, variance, tolerance, evidence, anomaly, learning signal
2. **Evidence validation tests** (~6): Each dimension tested independently
3. **Deviation detection tests** (~5): Per-dimension calculations, threshold crossings
4. **Anomaly detection tests** (~4): Pattern matching, edge cases
5. **Pipeline integration tests** (~8): Full observe() flow, intake through handoff
6. **Determinism tests** (~2): Identical inputs produce identical observations
7. **Immutability tests** (~2): Observations cannot be modified after creation
8. **Backward compatibility tests** (~2): Legacy ObserverLayer interface
9. **Concurrency tests** (~2): Thread safety

---

**Plan approved. Implementation ready to begin.**