======================================================================
INTELLIGENCE DEPENDENCY AUDIT — SHUNYA OS
======================================================================

1. LEGACY IMPLEMENTATION STATUS
--------------------------------------------------
File                                     Status          Notes
----------------------------------------------------------------------
app/ai/copilot.py                        CONVERTED       Thin adapter over UIR (integration.ask())
app/ai/context.py                        SUPERSEDED      UIR context engine handles all context
app/ai/prompts.py                        SUPERSEDED      UIR intent engine handles classification
app/ai/provider.py                       RETAINED        Used by UBME discovery for LLM-based generation — UIR doesn't call LLMs
app/intelligence/runtime.py              DEPRECATED      Superseded by core.intelligence_runtime
app/intelligence/reasoning.py            DEPRECATED      Superseded by core.intelligence_runtime.reasoning
app/intelligence/insight.py              DEPRECATED      Superseded by core.intelligence_runtime.suggestions
app/intelligence/confidence.py           DEPRECATED      Superseded by core.intelligence_runtime.reasoning confidence
app/intelligence/provenance.py           DEPRECATED      Superseded by core.intelligence_runtime.explain
app/intelligence/observation.py          SUPERSEDED      UIR memory engine handles observations
app/intelligence/inspector.py            DEPRECATED      Superseded by core.intelligence_runtime.explain
app/intelligence/models.py               SUPERSEDED      UIR types are the canonical types
app/intelligence/routes.py               RETAINED        Still registered in app factory — serves legacy API consumers
app/intelligence/service.py              DEPRECATED      Superseded by core.intelligence_runtime.integration
app/intelligence/scenario.py             SUPERSEDED      UIR wire providers handle all data sources

2. SURFACE MIGRATION STATUS
--------------------------------------------------
Surface                   Entry Point                    Runtime         Status
----------------------------------------------------------------------
Executive Home            ask()                          UIR             full
Global Search             ask()                          UIR             full
Workspace Runtime         ask()                          UIR             full
Object Detail             ask()                          UIR             full
Universal Chat            ask() + conversation           UIR             full
Documents                 ask()                          UIR             full
Dashboards                ask() + suggestions            UIR             full
Timeline                  ask()                          UIR             full
Notifications             suggest()                      UIR             full
Business Discovery        ask() + workflow               UIR             full
Automation                suggest()                      UIR             full
Founder Copilot           process_message()              UIR             adapter
M8 Executive              legacy endpoints               DEPRECATED      legacy

3. DEPENDENCY GRAPH
--------------------------------------------------

  Every SHUNYA Surface
         │
         ├── app/intelligence_routes.py (11 endpoints)
         │         │
         │         └── core.intelligence_runtime.integration.ask()
         │                       │
         │                       ├── IntentEngine.classify()
         │                       ├── ContextEngine.update()
         │                       ├── RetrievalLayer.retrieve()
         │                       │       ├── Business Graph ✅
         │                       │       ├── Object instances ✅
         │                       │       └── Memory Engine ✅
         │                       ├── ReasoningEngine.reason()
         │                       ├── ActionPlanner.decide()
         │                       └── ToolExecutionLayer.execute()
         │
         └── app/ai/copilot.py (adapter, backward compat only)
                        │
                        └── core.intelligence_runtime.integration.ask()
                                        │
                                        └── (same pipeline as above)

  NO PARALLEL INTELLIGENCE PATHS.
  ONE RUNTIME. ONE ENTRY POINT.

4. RUNTIME SINGLETON VERIFICATION
--------------------------------------------------

  core.intelligence_runtime.runtime._INSTANCE (module-level singleton)
    ├── IntentEngine   — 1 instance
    ├── ContextEngine  — 1 instance
    ├── MemoryEngine   — 1 instance
    ├── RetrievalLayer — 1 instance
    ├── ReasoningEngine— 1 instance
    ├── ActionPlanner  — 1 instance
    ├── ToolExecLayer  — 1 instance
    ├── ConversationRt — 1 instance
    ├── SuggestEngine  — 1 instance
    └── ExplainEngine  — 1 instance

  get_runtime() returns the same object every time.
  reset_runtime() destroys and recreates (testing only).
  No duplicate engine instances exist.

5. DEAD CODE RETIREMENT PLAN
--------------------------------------------------

  Phase 1 (this cycle): Convert copilot.py to UIR adapter. Done.
  Phase 2 (next cycle): Remove app/ai/context.py, app/ai/prompts.py.
  Phase 3 (next cycle): Remove app/intelligence/ directory entirely.
  Phase 4 (next cycle): Update app/founder/routes.py to call UIR directly.
  Phase 5 (next cycle): Remove app/ai/copilot.py adapter.
  
  Files retained with reason:
  - app/ai/provider.py: Still used by UBME discovery for LLM generation.
  - app/intelligence/routes.py: Legacy API consumers still active.

6. SINGLE INTELLIGENCE RULE
--------------------------------------------------

  Every intelligence request passes through exactly one entry point:
  
    core.intelligence_runtime.integration.ask()
  
  No alternative reasoning path exists.
  Business understanding belongs to UBME.
  Reasoning belongs to the Universal Intelligence Runtime.
  Presentation belongs to the UI.
