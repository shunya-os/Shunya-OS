# SHUNYA v1.0 — Canonical Identity Authority Decision

## Architecture Choice: Option A

**IdentityEngine is canonical. Repository persists it. Runtime loads it.**

```
IdentityEngine (core/identity/engine.py)
    ↑  canonical create/resolve/lifecycle
    ↓
IdentityRepository (app/production/identity_repository.py)
    ↑  persistence bridge
    ↓
SHUNYAIdentityModel (database)
    ↑  SQLAlchemy storage
    ↓
IdentityRuntime (core/identity_runtime.py)
    ↑  wires engine + repository for pipeline
    ↓
ShunyaOS (core/os.py)
    ↑  bootstrap loads persisted identities into engine
```

## Current State (Problem)

Two separate identity systems exist with no connection:

| System | Location | Storage | Used by |
|--------|----------|---------|---------|
| `IdentityEngine` | `core/identity/engine.py` | In-memory dict | Signin pipeline, `IdentityRuntime` |
| `IdentityRepository` | `app/production/identity_repository.py` | Database (`SHUNYAIdentityModel`) | Production identity queries |

The engine creates identities with `identity_id = "sid_4ba..."` but never persists them.
The repository can persist/load identities but is never called by the engine or runtime.
The seed script hardcodes `identity_id = "demo-founder-001"` which matches neither.

## Proposed Fix

### 1. Add persistence to IdentityRuntime

The `IdentityRuntime` already sits between the pipeline and the engine. Add a repository reference:

```python
class IdentityRuntime(RuntimeInterface):
    def __init__(self, engine=None, repository=None):
        self._engine = engine or IdentityEngine()
        self._repository = repository  # IdentityRepository or None

    def bootstrap(self):
        """Load persisted identities into the engine on startup."""
        if not self._repository:
            return
        for model in self._repository.list_all():
            identity = model.to_kernel()
            self._engine._identities[identity.identity_id] = identity
```

### 2. Persist on create

When the engine creates an identity via `create_identity()`, the runtime also persists it:

```python
# In IdentityRuntime.process(), after engine.create_identity():
if self._repository and result.get("created"):
    model = SHUNYAIdentityModel.from_kernel(identity)
    db.session.add(model)
    db.session.commit()
```

### 3. Wire in ShunyaOS.bootstrap()

```python
from app.production.identity_repository import IdentityRepository

repo = IdentityRepository()
self._identity_runtime = IdentityRuntime(repository=repo)
self._identity_runtime.bootstrap()  # load persisted identities
```

### 4. Seed script uses the same engine

```python
from core.identity import IdentityEngine, EntityType, AuthMethod

engine = IdentityEngine()
ident = engine.create_identity(
    display_name="Nishesh",
    entity_type=EntityType.HUMAN,
    auth_methods=[AuthMethod(method_type="email", identifier="nishesh@shunyaos.com", ...)],
)
# identity_id matches what signin pipeline produces
# If repository is wired, it persists automatically
```

## Proof Chain

```
Seed script runs
    ↓
IdentityEngine.create_identity("Nishesh")
    ↓
identity_id = "sid_4ba702c24c8332f17f0221c1ff65f343"
    ↓
SHUNYAIdentityModel persists to database
    ↓
Flask app starts
    ↓
ShunyaOS.bootstrap() loads all persisted identities into engine
    ↓
Founder signs in with email
    ↓
IdentityRuntime resolves by email → finds persisted identity
    ↓
Same identity_id returned
    ↓
FounderSpace.identity_id matches → filter works
    ↓
Zero authorization changes
```

## Files Changed

1. `core/identity_runtime.py` — add repository parameter, `bootstrap()`, persist on create
2. `core/os.py` — wire repository into IdentityRuntime, call `bootstrap()`
3. `scripts/seed_demo.py` — use `IdentityEngine.create_identity()` instead of hardcoded identity_id
4. Remove HTTP linking step from seed script

## Risk Assessment

- **Low risk**: The IdentityRuntime already accepts optional engine. Adding optional repository is backward compatible.
- **No schema changes**: `SHUNYAIdentityModel` already exists with the correct columns.
- **No API changes**: The signin route behavior is unchanged. Identity_id in session will be the same string format.
- **Idempotent**: If the seed script creates an identity that already exists (by email), the engine's `resolve_identity` returns it instead of creating a duplicate.

## Requesting Founder Approval

This change affects the identity/authentication boundary. I will not implement until you approve Option A or specify an alternative.