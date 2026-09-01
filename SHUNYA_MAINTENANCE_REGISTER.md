# SHUNYA MAINTENANCE REGISTER

> **Date:** 2026-09-01
> **HEAD:** 272dbad
> **Directive:** FCR-01.1 Step 47-48

---

Items classified as MAINTENANCE only after passing the FCR-01.1 §46 five-question test:
1. Is the promised launch capability already usable? ✅
2. Does the real user journey work? ✅
3. Is canonical persistence correct? ✅
4. Is security/authorization correct? ✅
5. Would leaving this unchanged violate a launch promise? ❌

---

| ID | Domain | Item | Location | Impact | Evidence |
|----|--------|------|----------|--------|----------|
| M-01 | Frontend | TODO: hero artwork import | frontend/src/components/public/homepage.tsx:31 | Cosmetic — public homepage uses placeholder | 1 TODO in entire codebase |
| M-02 | Code | NotImplementedError in abstract base classes | app/integration/registry.py, app/shunya/executor.py, app/graph/edge.py, app/graph/node.py | Expected — base classes are never directly instantiated | Abstract base classes, concrete subclasses exist |
| M-03 | Architecture | 5 orphan runtimes without consumers | core/execution_runtime/, core/planning_runtime/, core/automation_runtime/, core/memory_knowledge_runtime/, core/workspace_runtime/ | No production impact — no consumer depends on them | Orphan runtimes classified in ownership map |
| M-04 | Architecture | core/event/ — orphan event system | core/event/ | No production impact — app/events/ is canonical | Orphan classification |
| M-05 | Data | Legacy tables empty (lead, task, invoices) | lead=0, task=0, invoices=0 | Expected — canonical tables are leads, tasks, fin_invoices | Legacy tables are read-only |
| M-06 | Migration | Migration chain has multiple heads | alembic heads: 0013 + zgc_pr_17c_durable_memory | Migration 'alembic upgrade head' fails due to multiple heads | Fix: merge migrations or clean up |
| M-07 | Intelligence | Agreement intelligence (UCP-06) orphan | core/agreement_intelligence/ | Not wired to commitments — acceptable for launch | Orphan classification |
| M-08 | Intelligence | Asset intelligence (UCP-07) orphan | core/asset_intelligence/ | Not wired — acceptable for launch | Orphan classification |
| M-09 | Intelligence | Initiative intelligence (UCP-08) orphan | core/initiative_intelligence/ | Not wired — acceptable for launch | Orphan classification |
| M-10 | Intelligence | Health intelligence (UCP-10) orphan | core/health_intelligence/ | Not wired — acceptable for launch | Orphan classification |
| M-11 | Intelligence | Learning intelligence (UCP-11) orphan | core/learning_intelligence/ | Learning loop exists in runtime — UCP-11 is separate | Learning loop implemented in runtime |
| M-12 | Intelligence | CognitiveRuntime orphan | core/cognitive_runtime/ | No consumer — acceptable for launch | Orphan classification |
| M-13 | Intelligence | MixedRouter duplicate | app/intelligence/mixed_router.py | Not actively used — InferenceOrchestrator is canonical | Duplicate classification |
| M-14 | Intelligence | Cost-aware intelligence not implemented | — | All requests use LLM — acceptable for initial launch | Not a launch promise |
| M-15 | Intelligence | Proactive signals not wired to SuggestionsEngine | app/signals/ | Not connected — acceptable for launch | Signals exist, wiring is enhancement |
| M-16 | Frontend | AIResidentPanel status unknown | components/living-workspace/ai-presence-panel.tsx | Component exists but mounting status unverified | Acceptable for launch |
| M-17 | Data | Knowledge entries empty (0) | knowledge_entries=0 | Knowledge_facts exist (53) — entries are different concern | Acceptable for launch |
| M-18 | Data | Document records empty (0) | document_records=0 | documents table has 16 records — legacy | Acceptable for launch |
| M-19 | Code | Deprecated copilot.py adapter | app/ai/copilot.py | Thin adapter over UIR — acceptable for backward compat | Documented as DEPRECATED |
| M-20 | Code | Legacy knowledge store/engine | app/shunya/knowledge_store/, app/shunya/knowledge_engine/ | Pre-canonical — awaited removal | Canonical replacement exists |