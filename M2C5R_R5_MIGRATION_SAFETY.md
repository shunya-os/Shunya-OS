# M2C.5R — PHASE R5: MIGRATION SAFETY CONTRACT
## Authority: M2C.5R §7 — Safe Data Convergence

---

## MANDATORY MIGRATION LIFECYCLE

Every migration/enrichment operation that changes persistent data MUST follow this sequence:

```
DRY RUN → PREFLIGHT → BACKUP → MUTATE → RECONCILE → AUDIT
```

---

## A. DRY RUN REQUIREMENTS

Before any persistent mutation, the migration must support a dry-run mode that:
- Reads all source data
- Determines eligibility, collisions, ambiguities
- Outputs expected changes without writing
- Reports records discovered, eligible, skipped, rejected, ambiguous
- Reports collisions, tenant violations, identity conflicts
- Returns exit code 0 only if dry-run succeeds

A dry run is NOT optional.

---

## B. PREFLIGHT GATES

The mutation MUST refuse to start when:
- Backup cannot be verified
- Source identity is ambiguous
- Tenant provenance is missing
- Collision threshold is exceeded
- Schema assumptions are violated
- Required dependency is unavailable

Example precondition check:

```python
def preflight(source_table, target_table):
    assert backup_exists(), "No verified backup found"
    assert source_has_provenance(), "Source rows missing tenant provenance"
    assert target_is_empty_or_known(), "Target has unexpected data"
    assert not is_running_in_production_without_approval(), "Production requires approval"
```

---

## C. IDEMPOTENCY CONTRACT

The second execution MUST produce the same result as the first.

Implementation rules:
- Source identity MUST be stable and deterministic (not random UUIDs)
- Use source primary key as canonical identifier where possible
- Always include a `migration_version` or `run_id` for audit
- Idempotency check: lookup by source identity + migration version

```
Running once: N canonical records
Running twice: N canonical records (same N, same IDs)
Running three times: N canonical records
```

Prove this in a disposable environment before production.

---

## D. TRANSACTION / ROLLBACK

Where technically appropriate:
- Wrap mutation in a database transaction
- On failure: full rollback

Where a transaction cannot span the operation:
- Maintain a mutation ledger with before/after identity
- Create a deterministic compensating rollback script
- Test the rollback in a disposable environment

---

## E. AUDIT

Every mutation must record:
- who/what initiated it
- source revision (Git SHA)
- operation version
- timestamp
- tenant
- source record identity
- canonical record identity
- action (create/update/delete)
- result (success/failure/count)

---

## F. FORBIDDEN PATTERNS

| Pattern | Why | Instead |
|---------|-----|---------|
| Random UUID as canonical identity | Breaks idempotency, provenance, rollback | Deterministic hash of source PK + source table |
| "First tenant" fallback | Cross-tenant contamination | Reject/Quarantine |
| `git add -A` | Captures unintended changes | `git add <specific files>` |
| Mutation without backup | Irreversible data loss | Backup + verify before any mutation |
| SQL is "reversible" substitute | Theoretical reversibility ≠ proven rollback | Tested rollback script |

---

## PHASE R5: COMPLETE
Proceeding to R6 — Person/Identity/Relationship Quarantine.