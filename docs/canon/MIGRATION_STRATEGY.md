# SHUNYA Migration Strategy

> **Phase L · Canonical Document**
> **Status: ACTIVE — Incremental migration rules and invariants.**

---

## 1. Guiding Principles

### 1.1 No Destructive Rewrites

Every migration step must be:
- **Additive first** — new code is added alongside old code
- **Verifiable** — old tests must pass after every change
- **Reversible** — rollback must be possible within one commit
- **Incremental** — no "flag day" migrations

### 1.2 Strangler Fig Pattern

Old code is not removed until the new code has been proven in production:

```
Step 1: Add new interface  (adapter)
Step 2: Route traffic through new interface  (routing switch)
Step 3: Remove old interface  (cleanup)
```

### 1.3 Preservation Rules

| Must preserve | Until |
|--------------|-------|
| All existing Flask routes and templates | Phased out in L+2/L+3 |
| All existing tests | Test coverage proven on new code |
| All `app.models.*` SQLAlchemy models | Adapter layer verified |
| All existing `core/` runtime tests | Always — regression rule |
| All `templates/*.html` files | Canonical workspace operational |

## 2. Migration Pattern: Model Migration

### Step 1: Adapter
```python
# Add adapter that writes to both old and new
class ObjectAdapter:
    def create(self, data):
        old_obj = FounderObject(**data)  # old path
        new_obj = UniversalObject(**data)  # new path
        return new_obj
```

### Step 2: Dual-write
```python
# Write to both, read from new
class ObjectAdapter:
    def create(self, data):
        old = FounderObject(**data)
        db.session.add(old)
        new = os.process_intent("create_object", data)
        return new
```

### Step 3: Read from new
```python
# Read from new only, old for rollback
class ObjectAdapter:
    def get(self, object_id):
        return os.process_intent("view_object", {"object_id": object_id})
```

### Step 4: Remove old
```python
# Delete FounderObject model, DB table, and adapter paths
```

## 3. Migration Pattern: Route Migration

### Step 1: Add OS route alongside existing route
```
/app/founder/routes.py (existing CRUD)
/app/os_routes.py (new OS-pipeline routes)
```

### Step 2: Route all new traffic through OS
```
All new features → /api/v1/os/*
Old features → /api/v1/founder/* (unchanged)
```

### Step 3: Migrate old routes one by one
```
Update founder routes to call os.process_intent() internally
```

### Step 4: Remove old routes
```
Delete /api/v1/founder/* once all consumers migrated
```

## 4. Rollback Protocol

| Failure | Rollback action | Recovery time |
|---------|----------------|---------------|
| OS kernel fails | Revert to Flask-only routing | < 1 minute |
| Adapter returns wrong data | Disable adapter, fall through to direct DB | < 5 minutes |
| Pipeline timeout | Bypass pipeline for affected route | < 5 minutes |
| New route breaks | `git revert` the commit | < 10 minutes |

## 5. Verification Gates

Every migration step must pass before proceeding:

| Gate | Check | Tool |
|------|-------|------|
| G1 | All existing tests pass | `pytest` |
| G2 | No regression in test count | Compare counts |
| G3 | Ruff 0 errors | `ruff check` |
| G4 | MyPy 0 errors | `mypy` |
| G5 | Dual-write produces identical data | Custom assertion |
| G6 | Pipeline trace produced | Assert on PipelineContext |
| G7 | Adapter tests pass | `pytest app/adapters/` |
| G8 | Integration test passes | `pytest tests/production/` |