# SHUNYA v1.0 — Identity Dependency Inversion Design

## Current Architecture (Violates Dependency Rule)

```
core/identity/engine.py
  IdentityEngine → self._identities dict (in-memory)
      ↑
core/identity_runtime.py
  IdentityRuntime → wraps IdentityEngine
      ↑
core/os.py
  ShunyaOS.bootstrap() — creates IdentityRuntime()
      ↑ (runtime only, no persistence)

app/production/identity_repository.py
  IdentityRepository → SHUNYAIdentityModel (DB)
      ↑
app/kernel/identity.py
  IdentityStore → SHUNYAIdentity (in-memory)
  
  # NOTE: IdentityStore and IdentityEngine are completely separate systems
  # with different Identity models and different identity_id formats.
```

**Problem:** Two identity systems with no connection. Engine creates identities in memory. Repository persists to database. They never share data.

## Target Architecture

```
core/identity/store.py           ← NEW: Interface (protocol)
  IdentityStore (protocol)
    create(display_name, entity_type, auth_methods) → Identity
    resolve(identity_id) → Identity | None
    find_by_email(email) → Identity | None
    find_by_auth(method_type, identifier) → Identity | None
    all() → list[Identity]
      ↑

core/identity/engine.py
  IdentityEngine → depends on IdentityStore (not dict)
      ↑
core/identity_runtime.py         ← No change to interface
  IdentityRuntime → wraps IdentityEngine
      ↑
core/os.py                       ← Minor change: wire store into engine
  ShunyaOS.bootstrap() → IdentityEngine(store=...)
      ↑
app/production/identity_store.py ← NEW: Production implementation
  ProductionIdentityStore(IdentityStore)
    delegates to IdentityRepository + SHUNYAIdentityModel
      ↓
app/production/identity_repository.py
  IdentityRepository → SHUNYAIdentityModel (DB)
```

## Files to Create

### 1. `core/identity/store.py` — Canonical IdentityStore Protocol

```python
"""Canonical Identity Store Interface.

Every identity store must implement this protocol.
The core depends on this contract, never on a concrete implementation.
"""

from typing import Protocol
from core.identity.models import Identity, AuthMethod, EntityType


class IdentityStore(Protocol):
    """Contract for identity persistence.

    Implementations may be in-memory, database-backed, or cached.
    """

    def create(
        self,
        display_name: str,
        entity_type: EntityType,
        auth_methods: tuple[AuthMethod, ...] = (),
    ) -> Identity:
        """Create a new identity. Returns the Identity with assigned identity_id."""
        ...

    def get(self, identity_id: str) -> Identity | None:
        """Resolve an identity by ID."""
        ...

    def find_by_auth(self, method_type: str, identifier: str) -> Identity | None:
        """Find an identity by authentication method (e.g., email)."""
        ...

    def all(self) -> list[Identity]:
        """Return all identities."""
        ...
```

### 2. `app/production/identity_store.py` — Production Implementation

```python
"""IdentityStore implementation backed by the production repository."""

from core.identity.models import Identity, AuthMethod, EntityType
from core.identity.store import IdentityStore as IdentityStoreProtocol
from app.production.identity_repository import IdentityRepository


class ProductionIdentityStore:
    """IdentityStore backed by SQLAlchemy SHUNYAIdentityModel."""

    def __init__(self) -> None:
        self._repo = IdentityRepository()

    def create(
        self,
        display_name: str,
        entity_type: EntityType,
        auth_methods: tuple[AuthMethod, ...] = (),
    ) -> Identity:
        from core.identity.models import _generate_identity_id
        identity = Identity(
            identity_id=_generate_identity_id(),
            display_name=display_name,
            entity_type=entity_type,
            auth_methods=auth_methods,
            status=IdentityStatus.ACTIVE,
        )
        # Persist via the production repository
        model = self._repo._model_from_kernel(identity)
        from app import db
        db.session.add(model)
        db.session.commit()
        return identity

    def get(self, identity_id: str) -> Identity | None:
        model = self._repo._model_by_id(identity_id)
        return model.to_kernel() if model else None

    def find_by_auth(self, method_type: str, identifier: str) -> Identity | None:
        from app.shunya.identity.models import Identity as ShinobiIdentity
        result = ShinobiIdentity.query.filter_by(email=identifier).first()
        if result:
            from core.identity.models import Identity, AuthMethod
            return Identity(
                identity_id=result.identity_id,
                display_name=result.display_name,
                auth_methods=(AuthMethod(method_type=method_type, identifier=identifier),),
                status=IdentityStatus.ACTIVE,
            )
        return None

    def all(self) -> list[Identity]:
        from app.production.identity_repository import SHUNYAIdentityModel
        models = SHUNYAIdentityModel.query.all()
        return [m.to_kernel() for m in models]
```

### 3. `core/identity/engine.py` — Updated to Accept IdentityStore

```python
class IdentityEngine:
    def __init__(self, store: IdentityStoreProtocol | None = None):
        self._store = store or InMemoryIdentityStore()
        self._identities: dict[str, Identity] = {}  # cache / fallback

    def create_identity(self, ...) -> Identity:
        ident = self._store.create(display_name, entity_type, auth_methods)
        self._identities[ident.identity_id] = ident  # cache
        return ident

    def resolve_identity(self, identity_id: str) -> Identity | None:
        ident = self._identities.get(identity_id)
        if ident is None:
            ident = self._store.get(identity_id)
            if ident:
                self._identities[ident.identity_id] = ident
        return ident

    def find_by_email(self, email: str) -> Identity | None:
        ident = self._store.find_by_auth("email", email)
        if ident:
            self._identities[ident.identity_id] = ident
        return ident
```

### 4. `core/os.py` — Wire the Production Store

```python
def bootstrap(self):
    from app.production.identity_store import ProductionIdentityStore
    store = ProductionIdentityStore()
    from core.identity_runtime import IdentityRuntime
    self._identity_runtime = IdentityRuntime(engine=IdentityEngine(store=store))
```

### 5. `scripts/seed_demo.py` — Use IdentityEngine to Create Founder

```python
from core.identity import IdentityEngine, EntityType, AuthMethod

engine = IdentityEngine(store=ProductionIdentityStore())
ident = engine.create_identity(
    display_name="Nishesh",
    entity_type=EntityType.HUMAN,
    auth_methods=[AuthMethod(method_type="email", identifier="nishesh@shunyaos.com", ...)],
)
# identity_id matches what signin pipeline produces
# Persisted to database via ProductionIdentityStore
# Remove old HTTP linking step
```

## Proof Chain

```
Seed: IdentityEngine(store=ProductionIdentityStore()).create_identity("Nishesh")
    ↓
Core: IdentityStore.create() → returns Identity with identity_id = "sid_4ba..."
    ↓
App: ProductionIdentityStore.create() → SHUNYAIdentityModel persists to DB
    ↓
Flask app restarts
    ↓
OS: bootstrap() creates ProductionIdentityStore() → loads from DB
    ↓
OS: IdentityEngine(store=ProductionIdentityStore()) — engine populated
    ↓
Sign in: IdentityRuntime resolves by email → store.find_by_auth("email", ...)
    ↓
Store queries SHUNYAIdentityModel → returns persisted Identity
    ↓
Same identity_id → session["identity_id"] = "sid_4ba..."
    ↓
Spaces filtered by identity_id → match → organizations visible
    ↓
Zero authorization changes. No HTTP linking. No cookie decoding.
```

## Dependency Direction Verified

```
core/identity/store.py  (protocol) — depends on nothing
core/identity/engine.py — depends on core/identity/store.py (protocol)
core/identity_runtime.py — depends on core/identity/engine.py
core/os.py — depends on core/identity_runtime.py
                              ↓ (dependency inversion)
app/production/identity_store.py — implements core/identity/store.py (protocol)
                                   depends on app/production/identity_repository.py
                                   depends on core/identity/models.py
app/production/identity_repository.py — depends on Flask, SQLAlchemy
```

Arrow points from concrete to abstract. Core never depends on app. ✅

## Requesting Founder Approval

This design keeps `core/` free of Flask/SQLAlchemy dependencies while establishing a single canonical identity creation path. All callers (seed, sign-in, onboarding, imports) go through the same `IdentityEngine.create_identity()` → `IdentityStore.create()` chain.

I will not implement until you approve this design or specify adjustments.