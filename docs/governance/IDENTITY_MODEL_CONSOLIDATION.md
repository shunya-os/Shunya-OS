# SHUNYA v1.0 — Identity Domain Model Consolidation

## Current State: Two Identity Models

| Feature | `core/identity/models.py` `Identity` | `app/kernel/identity.py` `SHUNYAIdentity` |
|---------|--------------------------------------|-------------------------------------------|
| Location | `core/` (pure Python) | `app/kernel/` (depends on `UniversalObject`) |
| Identity ID | `sid_` + `secrets.token_hex(16)` = 32 hex chars | `sid_` + `uuid.uuid4().hex[:24]` = 24 hex chars |
| Mutability | Frozen dataclass | Mutable class with methods |
| Entity types | `EntityType` enum (HUMAN, ORGANIZATION, SYSTEM, SERVICE) | Via `AuthMethodType` enum |
| Auth methods | `AuthMethod` (frozen dataclass) | `AuthenticationMethod` (dataclass) |
| Status | `IdentityStatus` enum (ACTIVE, MERGED, SPLIT, RETIRED, PENDING) | Via `status` field |
| Linking | None | `LinkingSuggestion`, `detect_potential_links()` |
| Provenance | `Provenance` dataclass | None |
| Base class | None (standalone) | `UniversalObject` |
| Serialization | No `to_dict()` | `to_dict()` method |
| Used by | `IdentityEngine`, `IdentityRuntime`, pipeline | `IdentityStore`, `IdentityRepository`, `IdentityGovernance` |

## Decision: Option A — One Canonical Model

**`core/identity/models.py` `Identity` is the canonical model.**

The `SHUNYAIdentity` class in `app/kernel/` will be deprecated in favor of `Identity`.

### Rationale

1. **Location**: `core/` is the right place for canonical models. `app/kernel/` is a convergence artifact, not a permanent home.
2. **Immutability**: The `Identity` frozen dataclass enforces the constitutional rule that "Identity is immutable after creation" (§4.2 of Universal Ontology). The mutable `SHUNYAIdentity` allows side effects like `add_auth_method()` which can violate invariants.
3. **Security**: `secrets.token_hex(16)` (128-bit CSPRNG) is more secure than `uuid.uuid4().hex[:24]` (96-bit PRNG).
4. **Simplicity**: `Identity` has no dependencies. `SHUNYAIdentity` extends `UniversalObject` which brings the entire kernel object system.

### Migration

The `SHUNYAIdentity` linking features (`suggest_link`, `verify_and_link`, `detect_potential_links`) are not yet used by any production code. They were designed for a future identity linking flow. These features will be moved into a separate `IdentityLinkingService` when that flow is implemented.

### Conversion Boundary

The `IdentityRepository` (in `app/production/identity_repository.py`) will be updated to:

1. Accept/return `Identity` from `core/identity/models.py` instead of `SHUNYAIdentity`
2. Keep `SHUNYAIdentityModel` as the database model (no schema change)
3. Add conversion methods: `SHUNYAIdentityModel` ↔ `Identity`
4. The existing `to_kernel()` / `from_kernel()` methods for `SHUNYAIdentity` will be removed after migration

### Invariants

| Invariant | Enforced by |
|-----------|-------------|
| `identity_id` is unique and permanent | `Identity` field + DB unique constraint |
| `identity_id` format is `sid_` + 32 hex chars | `_generate_identity_id()` + `is_valid_identity_id()` |
| Identity is immutable after creation | `Identity` frozen dataclass |
| Retired IDs are never reused | Application logic in `IdentityEngine` |
| Auth methods are unique per identity | `IdentityEngine._validate_auth_methods()` |

### Proof Chain

```
Seed: IdentityEngine.create_identity("Nishesh")
    ↓
Returns: Identity(identity_id="sid_4ba702c24c8332f17f0221c1ff65f343", ...)
    ↓
ProductionIdentityStore.create() → SHUNYAIdentityModel(identity_id="sid_4ba...")
    ↓
Flask restart → OS bootstrap → ProductionIdentityStore loads DB
    ↓
IdentityEngine resolves by email → Identity(identity_id="sid_4ba...")
    ↓
Same identity_id → session["identity_id"] = "sid_4ba..."
    ↓
FounderSpace.identity_id = "sid_4ba..." → filter matches
    ↓
Zero authorization changes
```

## Files to Change

| File | Change |
|------|--------|
| `core/identity/models.py` | ✅ Canonical — no change needed |
| `core/identity/store.py` | NEW — protocol using `Identity` |
| `core/identity/engine.py` | Accept `IdentityStore` protocol, use `Identity` |
| `core/identity_runtime.py` | No change (already uses `Identity`) |
| `core/os.py` | Wire production store into engine |
| `app/production/identity_store.py` | NEW — implements `IdentityStore` protocol, converts `Identity` ↔ `SHUNYAIdentityModel` |
| `app/production/identity_repository.py` | Add `Identity` conversion methods, keep `SHUNYAIdentity` for backward compat during migration |
| `app/kernel/identity.py` | Mark `SHUNYAIdentity` as deprecated |
| `scripts/seed_demo.py` | Use `IdentityEngine` + `ProductionIdentityStore` |

## What Does NOT Change

- `SHUNYAIdentityModel` — database schema stays the same
- `FounderSpace.identity_id` — same string field
- `session["identity_id"]` — same string value
- Signin route — same behavior
- Spaces endpoint filter — same identity_id matching
- `app/kernel/identity.py` `IdentityStore` — stays for backward compat, marked deprecated

## Conclusion

**Option A is feasible.** The two models can be consolidated into one canonical `Identity` in `core/identity/models.py`. The `SHUNYAIdentity` in `app/kernel/` is a superset of `Identity` with linking features that are not yet used. The conversion boundary is the `IdentityRepository` which already has `to_kernel()`/`from_kernel()` patterns — it just needs to produce `Identity` instead of `SHUNYAIdentity`.

No database schema changes. No API changes. No authorization changes. The identity_id format (`sid_` + 32 hex chars) is already what the signin pipeline produces — the seed script just needs to use the same engine.