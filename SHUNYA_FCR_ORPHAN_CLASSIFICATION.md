# SHUNYA FCR-01.1-C: ORPHAN ENGINE CLASSIFICATION

> **Date:** 2026-09-01
> **HEAD:** c018c1b
> **Directive:** FCR-01.1-C Step 4 — Orphan Classification

---

## Classification Legend

| Classification | Meaning |
|---------------|---------|
| **CANONICAL + MUST CONNECT** | Core capability, must be wired to AI/retrieval |
| **INTERNAL ONLY** | Used internally by other modules, not a public API |
| **DUPLICATE → MERGE** | Competes with a canonical implementation, must be merged |
| **SUPERSEDED** | Replaced by a newer implementation |
| **DEPRECATED** | No longer recommended, removal planned |
| **REMOVE** | Dead code, no callers, safe to delete |

---

## 10 UCP Engines (core/*_intelligence/)

| Engine | Location | Callers | Classification | Evidence |
|--------|----------|---------|---------------|----------|
| relationship_intelligence (UCP-02) | core/relationship_intelligence/ | app/authz/models.py, app/intelligence_routes.py, app/organizational/engine.py | **CANONICAL + MUST CONNECT** | Has callers in app/ but not wired to AI retrieval |
| financial_intelligence (UCP-03) | core/financial_intelligence/ | app/authz/models.py, app/intelligence/mixed_router.py, app/intelligence/routes.py | **CANONICAL + MUST CONNECT** | Referenced by intelligence routes but not wired to ask() |
| knowledge_intelligence (UCP-04) | core/knowledge_intelligence/ | app/authz/models.py, app/decision/engine.py, app/organizational/engine.py | **CANONICAL + MUST CONNECT** | Has callers, not wired to AI retrieval |
| decision_intelligence (UCP-05) | core/decision_intelligence/ | app/decision/engine.py, app/decision/models.py, app/decision/__init__.py | **INTERNAL ONLY** | Used by app/decision/ — internal domain |
| agreement_intelligence (UCP-06) | core/agreement_intelligence/ | app/intelligence/decision_engine.py, app/intelligence/comparator.py, app/intelligence/scenario.py | **INTERNAL ONLY** | Used by intelligence modules, not a public API |
| asset_intelligence (UCP-07) | core/asset_intelligence/ | app/creative_runtime/routes.py, app/creative_runtime/runtime.py, app/outcome_library.py | **INTERNAL ONLY** | Used by creative runtime |
| initiative_intelligence (UCP-08) | core/initiative_intelligence/ | app/creative_runtime/runtime.py, app/founder/insight_engine.py, app/onboard.py | **INTERNAL ONLY** | Used by insight engine |
| operations_intelligence (UCP-09) | core/operations_intelligence/ | app/authz/extended_models.py, app/jobs/manager.py, app/genesis_protection.py | **INTERNAL ONLY** | Used by job manager |
| health_intelligence (UCP-10) | core/health_intelligence/ | app/authz/admin_routes.py, app/integration/gmail_adapter.py, app/intelligence_routes.py | **INTERNAL ONLY** | Used by admin routes |
| learning_intelligence (UCP-11) | core/learning_intelligence/ | app/decision/engine.py, app/decision/models.py, app/intelligence/routes.py | **CANONICAL + MUST CONNECT** | Separate from learning_loop.py — needs connection |

## 8 Core Runtimes

| Runtime | Location | Callers | Classification | Evidence |
|---------|----------|---------|---------------|----------|
| automation_runtime | core/automation_runtime/ | app/integration/models.py, app/core/shadow_runner.py, app/ubme/evolution.py | **INTERNAL ONLY** | Used by integration and shadow runner |
| cognitive_runtime | core/cognitive_runtime/ | app/cognitive/engine.py, app/cognitive/models.py, app/cognitive/__init__.py | **INTERNAL ONLY** | Used by app/cognitive/ |
| execution_runtime | core/execution_runtime/ | app/decision/engine.py, app/decision/models.py, app/integration/gmail_ingest.py | **INTERNAL ONLY** | Used by decision engine |
| integration_runtime | core/integration_runtime/ | app/authz/models.py, app/voice.py, app/integration/routes.py | **INTERNAL ONLY** | Used by integration routes |
| intelligence_runtime | core/intelligence_runtime/ | app/decision/engine.py, app/decision/models.py, app/intelligence_routes.py | **CANONICAL** | THE canonical intelligence kernel |
| memory_knowledge_runtime | core/memory_knowledge_runtime/ | core/os.py, itself | **SUPERSEDED** | Memory handled by app/memory/ (MemoryRecord) + app/memory_api/ (memory_db.py) |
| planning_runtime | core/planning_runtime/ | app/decision/__init__.py, app/intelligence/comparator.py, app/core/shadow_runner.py | **INTERNAL ONLY** | Used by decision engine |
| workspace_runtime | core/workspace_runtime/ | app/authz/decorators.py, app/intelligence_routes.py, app/watch/__init__.py | **INTERNAL ONLY** | Used by workspace models |

## 8 Intelligence Engines (core/intelligence/)

| Engine | Location | Callers | Classification | Evidence |
|--------|----------|---------|---------------|----------|
| perception | core/intelligence/perception/ | None found | **REMOVE** | Abstract base, no callers, not wired |
| context_assembly | core/intelligence/context_assembly/ | None found | **REMOVE** | Abstract base, no callers, not wired |
| reasoning | core/intelligence/reasoning/ | None found | **REMOVE** | Abstract base, no callers, not wired |
| planning | core/intelligence/planning/ | None found | **REMOVE** | Abstract base, no callers, not wired |
| decision | core/intelligence/decision/ | None found | **REMOVE** | Abstract base, no callers, not wired |
| reflection | core/intelligence/reflection/ | None found | **REMOVE** | Abstract base, no callers, not wired |
| learning | core/intelligence/learning/ | None found | **REMOVE** | Abstract base, controlled learning loop is in runtime |
| confidence | core/intelligence/confidence/ | None found | **REMOVE** | Abstract base, no callers, not wired |

## App-Level Intelligence Modules

| Module | Location | Classification | Evidence |
|--------|----------|---------------|----------|
| app/intelligence/ | app/intelligence/ | **CANONICAL** | Executive intelligence, routes, decision engine |
| app/intelligence_routes.py | app/intelligence_routes.py | **REMOVE** | 217 lines, UNREGISTERED, no callers |
| app/ai/ | app/ai/ | **CANONICAL** | AI chat route, provider registry |
| app/learning_intelligence/ | app/learning_intelligence/ | **SUPERSEDED** | Learning loop exists in runtime, this is legacy |
| app/execution_intelligence/ | app/execution_intelligence/ | **REMOVE** | Archived stub, no content |
| app/marketing_intelligence/ | app/marketing_intelligence/ | **CANONICAL** | FDA15 marketing intelligence |
| app/sales_intelligence/ | app/sales_intelligence/ | **CANONICAL** | FDA12 sales intelligence |
| app/travel_intelligence/ | app/travel_intelligence/ | **CANONICAL** | Travel intelligence |

## Duplicate Routes

| Route | First Registration | Second Registration | Classification |
|-------|-------------------|-------------------|---------------|
| execution_bp | app/__init__.py:671 (app/execution_engine/routes.py) | app/__init__.py:844 (app/execution/routes.py) | **DUPLICATE → MERGE** |

---

## Summary

| Classification | Count |
|---------------|-------|
| CANONICAL + MUST CONNECT | 3 (UCP-02, UCP-03, UCP-04, UCP-11) |
| INTERNAL ONLY | 10 (UCP-05,06,07,08,09,10 + automation, cognitive, execution, integration, planning, workspace runtimes) |
| SUPERSEDED | 2 (memory_knowledge_runtime, app/learning_intelligence/) |
| DUPLICATE → MERGE | 1 (execution_bp) |
| REMOVE | 9 (8 intelligence engines + app/intelligence_routes.py + app/execution_intelligence/) |
| CANONICAL | 3 (intelligence_runtime, app/ai/, app/intelligence/) |

**Corrected finding:** Only 3 UCP engines need to be wired to AI (UCP-02, 03, 04, 11). The other 6 are internal-only. The 8 intelligence engines in core/intelligence/ are truly dead code (abstract bases, no callers). The previous FCR misclassified them as "orphans that need wiring" — they actually need removal.