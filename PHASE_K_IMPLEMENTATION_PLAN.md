# PHASE_K_IMPLEMENTATION_PLAN.md

**Governance Directive:** G10.0 — Phase K Authorization
**Engine:** Learning Engine (ES-007)
**Layer:** Learning

---

## 1. Objectives

1. Implement canonical Learning Engine data models (ES-007 §2–3, §6)
2. Implement 9-stage deterministic learning pipeline (ES-007 §4)
3. Implement pattern discovery across observation learning signals
4. Implement outcome evaluation against expected objectives
5. Implement confidence calibration via adjustment formula
6. Implement improvement recommendation generation
7. Implement knowledge proposal packaging
8. Implement governance review package
9. Implement backward-compatible legacy wrapper
10. Comprehensive test suite + architecture contract verification + invariant verification
11. Zero regressions on all prior phases

## 2. Scope Boundaries

| In Scope | Out of Scope |
|----------|-------------|
| 8 learning types (supervised, reinforcement-inspired, rule refinement, pattern, statistical, temporal, comparative, human-guided) | Knowledge Engine write (Knowledge Engine not available) |
| 9-stage learning pipeline | Governance Engine validation of proposals (engine exists but integration deferred) |
| Pattern discovery from learning signals (frequency, confidence, trend) | Historical Knowledge Engine retrieval for longitudinal analysis |
| Outcome evaluation (success vs expected) | Cross-tenant federated learning |
| Confidence calibration (formula: old + (accuracy - old) × rate) | Meta-learning or causal learning |
| Improvement recommendation generation | Event Bus integration |
| Knowledge proposal lifecycle (Proposed → Applied → Superseded) | Pattern library persistence (in-memory only) |
| Governance review package | Simulation-driven learning |

## 3. ES-007 Requirement Mapping

| § | Requirement | Implementation |
|---|-------------|---------------|
| §1 | Analyze observations for improvement | `LearningEngine.learn()` |
| §1 | Never modify knowledge, bypass governance, rewrite history, fabricate learning, execute, approve | 10 SHALL NEVER rules |
| §2 | Input: learning signals + observations | `LearningInput` dataclass |
| §3 | Output: recommendations, patterns, calibrations, proposals, package | 6 output types |
| §4 | 9-stage pipeline | 9 explicit stages |
| §5 | 8 learning types | `LearningType` enum, 6 exercised |
| §6 | Pattern model with scope, recurrence, frequency, impact | `Pattern`, `PatternScope`, `Recurrence` |
| §7 | Knowledge proposal lifecycle + confidence calibration formula | `KnowledgeProposal`, `_calibrate_confidence()` |
| §8 | 7 failure modes | `FailureMode` enum, all handled |

## 4. Dependency Analysis

| Dependency | Status | Impact |
|------------|--------|--------|
| Phase J (Observer Engine) | ✅ Complete | Consumes `LearningSignal` and `VerifiedObservation` |
| Phase H (Governance Engine) | ✅ Complete | Consumes policies (future), proposals go here |
| Phase G (Planner Engine) | ✅ Complete | Outcome models reference (future) |
| Phase F (Reasoning Engine) | ✅ Complete | Confidence models reference (future) |
| `app/shunya/observer_learning.py` LearningLayer | ✅ Existing | Legacy LearningLayer re-exported for backward compat |

**No dependency on ReasoningSession** — confirmed by all prior phases.

## 5. Public Interfaces Consumed

- **Phase J LearningSignal**: signal_id, signal_type, description, dimension, delta, delta_percentage, confidence, tenant_id
- **Phase J VerifiedObservation** (via to_dict): observation_id, workflow_id, confidence, severity, evidence_quality, variances, anomalies, deviations

## 6. Public Interfaces Exposed

```python
from app.shunya.learning_engine import (
    LearningType, PatternType, KnowledgeProposalState, FailureMode,
    LearningInput, LearningOutput,
    Pattern, PatternScope, Recurrence,
    LearningRecommendation, KnowledgeProposal, ConfidenceCalibration,
    OutcomeEvaluation, PerformanceInsight,
    LearningEngine, get_learning_engine, reset_learning_engine,
    LearningLayer,  # legacy compat
)
```

## 7. Engine Boundary Matrix

| Engine | Allowed Reads | Allowed Writes | Allowed Public APIs | Forbidden Imports | Forbidden Writes | Forbidden Side Effects |
|--------|-------------|-------------|-------------------|------------------|-----------------|----------------------|
| **Learning (K)** | LearningInput (signals, observations), current patterns | In-memory pattern library, recommendation store | `learn()`, `learn_from_signals()`, `get_pattern()`, `list_recommendations()`, `stats`, `get_learning_engine()` | `app.shunya.reasoning`, `app.shunya.planner`, `app.shunya.executor_engine`, `app.shunya.governance_engine` | Knowledge Engine facts, governance policies, execution state, observation records | No network calls, no file I/O beyond own package, no DB mutations |
| Reasoning (F) | — | — | — | Forbidden | Forbidden | Forbidden |
| Planner (G) | — | — | — | Forbidden | Forbidden | Forbidden |
| Governance (H) | — | — | `VerdictDecision` | Forbidden direct import | Forbidden | Forbidden |
| Executor (I) | — | — | — | Forbidden | Forbidden | Forbidden |
| Observer (J) | `LearningSignal` | — | `LearningSignal.to_dict()` | Forbidden direct observer_engine import | Forbidden | Forbidden |

## 8. Cross-Engine Dependency Audit

| Dependency | Type | Source | Direction |
|------------|------|--------|-----------|
| Phase J LearningSignal | Input data | `observer_engine.models.LearningSignal` | Observer → Learning |
| Phase J VerifiedObservation | Input data | `observer_engine.models.VerifiedObservation` | Observer → Learning |
| Governance Engine | Output target | `governance_engine.models.VerdictDecision` | Learning → Governance (future) |
| Planner Engine | Output target | `planner_engine.models` | Learning → Planner (future) |

**No internal implementations are accessed directly.** Only documented public contracts (dataclass models) are consumed via `to_dict()` serialization.

## 9. Architectural Invariants

| # | Invariant | Dedicated Test | Enforced By |
|---|----------|---------------|-------------|
| 1 | Observations are never modified by learning | `test_observations_not_mutated` | Input is `to_dict()` copy |
| 2 | Learning never writes to evidence | `test_no_evidence_write` | No import of observer_engine.evidence |
| 3 | Learning never modifies knowledge directly | `test_no_knowledge_write` | No Knowledge Engine import |
| 4 | Learning proposals are proposals, not commands | `test_recommendations_are_proposals` | `approved` flag on recommendations |
| 5 | Patterns are immutable after creation | `test_pattern_immutability` | Dataclass fields, no setters |
| 6 | Confidence calibration is deterministic | `test_calibration_determinism` | Same input → same output |
| 7 | Recommendations are traceable to observations | `test_recommendation_traceability` | `source_observation_ids` field |
| 8 | Tenant isolation on all learning data | `test_tenant_isolation` | `tenant_id` on all models |
| 9 | Evidence precedes learning | `test_no_fabricated_learning` | `_verify_evidence_grounding()` |

## 10. Public API Stability Review

| Existing API | Status | Notes |
|-------------|--------|-------|
| `LearningLayer.__init__(observer, knowledge_store, session)` | ✅ PRESERVED | Wraps LearningEngine internally |
| `LearningLayer.analyze(observation_id)` | ✅ PRESERVED | Delegates to canonical `learn_from_signals()` |
| `LearningLayer.analyze_batch(since_hours)` | ✅ PRESERVED | Loops over stored signals, calls analyze() |
| `LearningLayer.stats()` | ✅ PRESERVED | Returns dict from canonical engine.stats |

**No breaking changes.** Legacy LearningLayer is a wrapper; the canonical package is additive.

## 11. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| No Knowledge Engine for persistence | Medium | All outputs in-memory; interfaces defined for future write |
| No Governance Engine for validation | Low | Proposals produced; validation deferred |
| Cold start (no observations) | Low | Returns "insufficient data" with minimum count required |

## 12. Testing Strategy

1. **Model tests** (~20): Pattern, recommendation, proposal, calibration, scope, recurrence
2. **Pipeline integration tests** (~8): Full 9-stage learn() flow
3. **Pattern discovery tests** (~5): Success/failure/trend classification
4. **Outcome evaluation tests** (~3): Quality scoring per dimension
5. **Confidence calibration tests** (~4): Formula verification
6. **Recommendation tests** (~4): Generation, prioritization, traceability
7. **Architecture contract tests** (~5): Forbidden imports, boundary violations
8. **Architectural invariant tests** (~6): Immutability, no knowledge write, no evidence write
9. **Determinism tests** (~2): Identical inputs → identical outputs
10. **Backward compatibility tests** (~3): Legacy LearningLayer
11. **Singleton/tracking tests** (~3): Stats, accessors

## 13. Migration Strategy

**None required.** The existing `app/shunya/observer_learning.py` is preserved untouched. The new canonical `learning_engine` package is additive. Legacy `LearningLayer` is re-exported from the new package.

## 14. Architecture Contract Verification (Automated)

The verification script will:
1. Verify no imports from `app.shunya.reasoning`, `app.shunya.planner`, `app.shunya.executor_engine` exist in learning_engine code
2. Verify `learning_engine/engine.py` does not import `app.shunya.observer_engine` directly (uses to_dict() only)
3. Verify `learning_engine/models.py` has no Knowledge Engine references
4. Verify no `eval()`, `exec()`, or `__builtins__` usage
5. Verify all 10 SHALL NEVER rules have architectural coverage

---

**Plan approved. Implementation ready to begin.**