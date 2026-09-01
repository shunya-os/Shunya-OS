# Decommission Plan: `core/execution_runtime/`

**Status:** ORPHAN per governance ([SHUNYA_CANONICAL_OWNERSHIP.md](/home/shunya-deploy/shunya_os/governance/SHUNYA_CANONICAL_OWNERSHIP.md#L230))
**Canonical replacement:** `app/execution_engine/` + `app/runtime/loop.py`
**Verification alias:** `app/execution/__init__.py` (already has backward-compat wrappers delegating to `OutcomeRuntime` → `execution_engine`)

---

## 1. Module Contents

| File | Size | Role |
|------|------|------|
| `__init__.py` | 70 lines | Public API barrel — re-exports models + orchestrator |
| `models.py` | 404 lines | Data models: state machine, instances, contracts, policies, graph |
| `orchestrator.py` | 495 lines | `ExecutionRuntime` class: registration, scheduling, execution, rollback |

## 2. All Callers — Classification

### PRODUCTION (actually wired, but never executes real work)

| Caller | Import | Classification |
|--------|--------|---------------|
| `core/runtime_pipeline/adapters.py:308` | `from core.execution_runtime import ExecutionRuntime` | **PHANTOM** — `ExecutionRuntimeAdapter` is wired into the OS pipeline, **is invoked for every `process_intent()` call**, but always returns "noop" because no production intent is registered as an execution action. Only test actions (noop, echo, delay) are registered. |

### PHANTOM (try/except guarded, never invoked)

| Caller | Import | Why Phantom |
|--------|--------|-------------|
| `core/relationship_intelligence/runtime.py:646` | `from core.execution_runtime.models import ActionContract` | Inside `try/except ImportError`. The method `register_execution_actions()` is **never called** — zero `.register_execution_actions(` calls exist in the codebase. |
| `core/knowledge_intelligence/runtime.py:348` | Same | Same pattern — dead code path |
| `core/asset_intelligence/runtime.py:179` | Same | Same pattern — dead code path |
| `core/financial_intelligence/runtime.py:684` | Same | Same pattern — dead code path |
| `core/operations_intelligence/runtime.py:726` | Same | Same pattern — dead code path |
| `core/agreement_intelligence/runtime.py:203` | Same | Same pattern — dead code path |
| `core/decision_intelligence/runtime.py:337` | Same | Same pattern — dead code path |

All 7 use the same pattern:
```python
def register_execution_actions(self, execution_runtime: Any) -> None:
    try:
        from core.execution_runtime.models import ActionContract
    except ImportError:
        logger.warning("ExecutionRuntime not available — skipping")
        return
    execution_runtime.register_action(...)
```

No orchestrator ever calls `register_execution_actions()`.

### TEST-ONLY (no production impact)

| Caller | Notes |
|--------|-------|
| `tests/execution_runtime/test_execution_runtime.py` | 649-line test — exercises ExecutionRuntime directly |
| `tests/execution_runtime/test_execution_governance.py` | 545-line property-based test — state machine invariants |
| `tests/verify_dcp01_travel.py.skip` | Skipped — imports non-existent `core.execution_runtime.runtime` |
| `tests/verify_ep07a_adaptive.py.skip` | Skipped — imports non-existent `core.execution_runtime.runtime` |

## 3. Does the module have any production code path that actually runs?

**No.** Here's the chain:

1. The `ExecutionRuntimeAdapter` IS wired into the OS pipeline at `core/os.py:122`
2. The pipeline runs for every `process_intent()` call: `create_space`, `create_object`, `talk_to_customer`
3. But the adapter's `_execution_update()` method checks `self._runtime.get_action(intent)` — and these intents are **not registered**
4. The only registered actions are test-only: `noop`, `echo`, `delay` (via `register_default_actions()`)
5. Result: always returns `{"status": "noop", ...}` — zero actual work

The module's data models are used in tests. The orchestrator logic (scheduling, dependency DAG, retry, rollback) is tested but never exercised in production.

## 4. Compatibility Stub Status

`app/execution/__init__.py` **already** has backward-compatible wrappers:
- `ExecutionService` — thin wrapper around `OutcomeRuntime.get_runtime()`
- `BusinessExecutionInstance` — thin wrapper around `OutcomeRuntime`
- `ExecutionObligation` — backward-compatible obligation class
- `ExecutionException` — backward-compatible exception

The docstring explicitly states the canonical path is:
> `runtime/entry.py → execution_engine → Object / Execution / ExecutionLog`

These stubs do NOT import from `core/execution_runtime/`. They delegate to `app.execution.runtime.OutcomeRuntime` which persists outcomes via SQLAlchemy.

## 5. Decommissioning Steps

### Step 1: Remove `core/execution_runtime/` from the pipeline adapter

**File:** `core/runtime_pipeline/adapters.py`
**Action:** Remove `ExecutionRuntimeAdapter` class (lines 296–370) and remove it from the adapter imports.
**Rationale:** The pipeline stage `EXECUTION_UPDATE` will remain, but no runtime will be registered for it → the pipeline records it as "noop" automatically (see `pipeline.py:231-237`). Zero behavioral change.

Affected files:
- `core/runtime_pipeline/adapters.py` — remove class + import
- `core/os.py` — remove `ExecutionRuntimeAdapter` imports (line 100) and registration (lines 122-124)

### Step 2: Remove phantom try/except imports from 7 intelligence runtimes

**Files:**
- `core/relationship_intelligence/runtime.py` — lines 645-649
- `core/knowledge_intelligence/runtime.py` — lines 347-351
- `core/asset_intelligence/runtime.py` — lines 178-181
- `core/financial_intelligence/runtime.py` — lines 683-687
- `core/operations_intelligence/runtime.py` — lines 725-728
- `core/agreement_intelligence/runtime.py` — lines 202-205
- `core/decision_intelligence/runtime.py` — lines 336-340

Also remove unused methods from:
- `core/health_intelligence/runtime.py:361` — `register_execution_actions` (no body)
- `core/learning_intelligence/runtime.py:480` — `register_execution_actions` (no body)
- `core/initiative_intelligence/runtime.py:129` — `register_execution_actions` (stub: `pass`)

**Action:** Remove the `register_execution_actions` method entirely from each runtime class. These are dead code — no caller exists.

### Step 3: Remove the module directory

```bash
rm -rf core/execution_runtime/
```

Affected files:
- `core/execution_runtime/__init__.py`
- `core/execution_runtime/models.py`
- `core/execution_runtime/orchestrator.py`

### Step 4: Remove or archive test files

If the state machine models are still useful (e.g., for `execution_engine`), migrate them. Otherwise remove:

```bash
rm -rf tests/execution_runtime/
rm tests/verify_dcp01_travel.py.skip
rm tests/verify_ep07a_adaptive.py.skip
```

### Step 5: (Optional) Move useful models into `app/execution_engine/models.py`

The `ExecutionState` enum, transition matrix, and `ActionContract` dataclass may be reusable. Evaluate during removal. If unused in `execution_engine`, they can be safely deleted.

### Step 6: Update governance doc

The governance document (`SHUNYA_CANONICAL_OWNERSHIP.md`) already marks this as **ORCHAN** and "DECOMMISSIONED". Confirm that the doc's action items are resolved to **REMOVED**.

---

## 6. Verification

After decommissioning, verify:

1. `pytest tests/execution_runtime/` — should fail (directory removed)
2. Flask app starts: `gunicorn app:app` — no import errors
3. All three production routes work: create_object, create_space, talk_to_customer — pipeline completes with EXECUTION_UPDATE stage recorded as "noop"
4. `process_intent("fly_to_moon")` — should still produce a valid pipeline trace (all stages, execution = noop)

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Pipeline fails because EXECUTION_UPDATE has no runtime | None | Pipeline handles empty stage maps automatically — returns "noop" |
| Tests that depend on `core/execution_runtime` break | Certain — intentional | Tests are being decommissioned alongside the module |
| Phantom imports cause silent failures | None | Already guarded by `try/except ImportError` — they'll just skip silently (which they already do when the module is absent) |

---

*Generated by audit of core/execution_runtime/ — September 2026*