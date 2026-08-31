# M2C.5R — PHASE R4: OBJECT CONVERGENCE
## Authority: M2C.5R §6 — Canonical Truth Recovery

---

## FINDING: MIGRATION IS UNACCEPTABLE

### The Idempotency Bug

The migration script `scripts/migrate_objects_v4.py` generates object IDs as follows:

```python
object_id = f"obj_{uuid.uuid4().hex[:16]}"
```

The idempotency check compares against that *just-generated* random UUID:

```python
existing = UOPObject.query.filter_by(object_id=object_id).first()
```

Since the UUID was just generated, it will never match an existing record. **Rerunning the migration creates 85 duplicates every time.**

### Current UOP Object Inventory

| Metric | Value |
|--------|-------|
| Total UOP objects | 85 |
| From founder_objects | 44 (tenant_id=1) |
| From objects table | 41 (tenant_id varied: 89=37, 7=4) |
| From sh_objects | 0 (table import failed) |
| Object types | Document(40), customer(8), timeline_event(8), commitment(8), conversation(7), note(7), supplier(5), Customer(1), Generic(1) |

### Source→Target Mapping

There is **no stable mapping**. The object_id is a random UUID with no relationship to the source primary key. The metadata_json stores `migrated_from` (source table name) but not the source primary key ID. This means:

- Cannot trace a UOP object back to its source row without content comparison
- Cannot verify deduplication
- Cannot prove migration completeness
- Cannot roll back selectively

### Object System Comparison

| System | Rows | Production Readers | Production Writers | FK Dependencies | Tenant Isolation |
|--------|------|-------------------|-------------------|----------------|-----------------|
| objects | 41 | Genesis, onboard | Genesis, onboard | Minimal | tenant_id column |
| founder_objects | 44 | AI context, upload, Executive Home, founder routes | Upload, AI, founder routes | space_id→founder_spaces | None |
| sh_uop_objects | 85 | None (migration only) | Migration only | None | tenant_id column |
| sh_objects | 4 | Minimal | Minimal | None | None |
| canonical_objects | 0 | None | None | None | None |

### Migration Failure Analysis

| Requirement | Status | Detail |
|-------------|--------|--------|
| Idempotent (same input → same output) | 🔴 FAIL | Random UUIDs → 85 duplicates on rerun |
| Stable source identity | 🔴 FAIL | No deterministic mapping from source PK |
| Tenant provenance | 🔴 FAIL | Source rows had varied tenants; migration hardcoded tenant_id=1 for objects table |
| Rollback path | 🔴 FAIL | No mapping to identify UOP objects to delete |
| Dry-run safety | 🔴 FAIL | No dry-run mode implemented |
| Pre-mutation backup | 🔴 FAIL | Executed without backup |

---

## VERDICT

The 85 sh_uop_objects are **UNAPPROVED MIGRATION ARTIFACTS** with no canonical status.

**They must not be read by any production code until:**

1. A stable source→target mapping is established (using source primary key, not random UUIDs)
2. Idempotency is proven in a disposable environment
3. Canonical object owner is selected constitutionally
4. Migration is reviewed and approved

---

## PHASE R4: COMPLETE
Proceeding to R5 — Migration Safety Contract.