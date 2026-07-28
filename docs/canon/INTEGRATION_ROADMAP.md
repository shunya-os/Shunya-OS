# SHUNYA Integration Roadmap

> **Phase L · Canonical Document**
> **Status: ACTIVE — Phased runtime wiring plan from mock to operational.**

---

## Phase Overview

```
Phase L (Current)        Phase L+1               Phase L+2              Phase L+3
──────────────           ──────────              ──────────              ──────────
OS Constitution ✓        Wire kernel RT          Wire memory RT          Remove demo data
Canonical Pipeline ✓     Wire identity RT        Wire planning RT        Real LLM
OS Kernel ✓              Flask → OS bridge       Wire execution RT       Deprecate Flask models
All mocks deployed        Next.js → Flask API    Wire projection RT      All operational
```

## Phase L+1: Runtime Wired

### Objective
Replace the first two mocks with real runtimes. Wire Flask's founder routes through the OS kernel.

### Tasks

| # | Task | Files | Test count |
|---|------|-------|------------|
| 1 | Create `app/adapters/kernel_adapter.py` — wraps `core/kernel/` for Flask consumption | `app/adapters/kernel_adapter.py` | 10 |
| 2 | Create `app/adapters/identity_adapter.py` — wraps `core/identity/` for Flask consumption | `app/adapters/identity_adapter.py` | 10 |
| 3 | Update `app/founder/routes.py` to call `os.process_intent()` instead of direct model operations | `app/founder/routes.py` | Existing tests |
| 4 | Wire Next.js API layer (`frontend/src/services/api.ts`) to Flask endpoints | `frontend/src/services/api.ts`, new API routes | 5 |
| 5 | Add Flask routes that proxy through OS kernel | `app/os_routes.py` | 15 |
| 6 | Replace MockRuntime "kernel" with `core/kernel/` adapter | `core/os.py` | Existing tests |
| 7 | Replace MockRuntime "identity" with `core/identity/` adapter | `core/os.py` | Existing tests |

### Acceptance Criteria

- [ ] `POST /api/v1/os/intent` creates a PipelineContext with full trace
- [ ] Kernel adapter processes intent_resolution and object_resolution stages
- [ ] Identity adapter processes identity_resolution stage
- [ ] All existing Flask functional tests pass
- [ ] All core runtime tests still pass
- [ ] Next.js frontend shows live data for at least one page
- [ ] Ruff 0, MyPy 0

## Phase L+2: Full Pipeline

### Objective
All 10 mock runtimes replaced with real implementations. Canonical pipeline processes all founder intents end-to-end.

### Tasks

| # | Task | Files | Test count |
|---|------|-------|------------|
| 1 | Create adapter for `core/memory_knowledge_runtime/` | `app/adapters/memory_adapter.py` | 10 |
| 2 | Create adapter for `core/planning_runtime/` | `app/adapters/planning_adapter.py` | 10 |
| 3 | Create adapter for `core/execution_runtime/` | `app/adapters/execution_adapter.py` | 10 |
| 4 | Create adapter for `core/projection/` | `app/adapters/projection_adapter.py` | 10 |
| 5 | Create adapter for `core/automation_runtime/` | `app/adapters/automation_adapter.py` | 5 |
| 6 | Wire founder converse route through Reasoning engine | `app/founder/routes.py` | 5 |
| 7 | Wire object CRUD through OS pipeline | `app/founder/routes.py` | 10 |
| 8 | Replace all remaining mocks | `core/os.py` | Existing tests |

### Acceptance Criteria

- [ ] `talk_to_customer` intent flows through all 11 pipeline stages
- [ ] Execution trace records every stage with timing
- [ ] Projection assembled and returned
- [ ] Knowledge graph updated after every object mutation
- [ ] Memory updated after every interaction
- [ ] All existing tests pass
- [ ] Ruff 0, MyPy 0

## Phase L+3: Production

### Objective
Remove all demo data paths. Wire real LLM inference. Every capability at "Operational" state.

### Tasks

| # | Task | Files |
|---|------|-------|
| 1 | Remove demo data from Next.js (`frontend/src/data/objects.ts`) | `frontend/src/data/objects.ts` |
| 2 | Replace scenario-based AI responses with LLM integration | `app/intelligence/runtime.py` |
| 3 | Remove duplicate Flask workspace templates | `templates/founder_workspace.html` |
| 4 | Mark all capabilities as "Operational" | Capability Matrix |
| 5 | Full regression + performance benchmarks | — |

### Acceptance Criteria

- [ ] No hardcoded demo data in any code path
- [ ] All AI responses come from real inference
- [ ] One canonical workspace implementation
- [ ] Every capability at "Operational"
- [ ] Performance metrics meet targets