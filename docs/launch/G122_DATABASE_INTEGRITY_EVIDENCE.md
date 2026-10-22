# G1.22 — Deferred Database Constraints & Indexes: Evidence Review

**Scope:** the 7 foreign keys, 1 on-delete difference and 36 indexes that G1.21
recorded as intentionally deferred. For each candidate this records the domain
invariant, the actual write path, whether an equivalent guarantee already exists,
and the decision. **No constraint was added in G1.22**; every deferred item failed
at least one evidence test below, and forcing an ORM/database match would have
introduced wrong semantics or rejected legitimate rows.

Method: ORM declaration read from the model; write path traced to the code that
creates/updates the column; existing constraints taken from the G1.21 audit
snapshot of the migrated schema (database `shunya_g121_final`, head
`r6b37_onboarding_sessions`, captured in `pg_schema_after.json`). No new database
was started for this review — the schema did not change in G1.22.

---

## 1. Foreign keys

| Candidate | Declared target | Actual write path | Why not added |
|---|---|---|---|
| `workspaces.tenant_id` | `tenants.id` | `production/identity/workspace_routes.py`: `Workspace(tenant_id=org_id, …)` — stores an **organization id** | The FK target is wrong for the domain. Adding it would reject every legitimate row on any system where `org.id` is not also a `tenants.id`. Correct fix is a retarget to `organizations.id` **plus** a rename, which is a schema decision (E-3 in the workspace ADR), not a constraint fix |
| `memory_records.tenant_id` | `tenants.id` | callers pass a `tenant_id` parameter through `app/memory/__init__.py`; the meaning (organization id vs legacy tenant id) is not established anywhere | Unresolved semantics. The tenancy-convergence revisions deliberately dropped legacy `tenants` FKs; re-adding one would contradict that decision without evidence |
| `memory_provenances.tenant_id` | `tenants.id` | same as above | same |
| `invitation_tokens.org_id` | `tenants.id` | **no writer exists** — `InvitationToken` is defined in `app/auth.py` and never instantiated anywhere in `app/` or `core/` | Constraining a dead table adds maintenance without protecting any write |
| `organizations.legacy_tenant_id` | `tenants.id` | `c_org_legacy_bridge` migration; read by `authz/workspace_context.py` as the compatibility bridge | Deliberately excluded from the tenancy convergence. An FK would block future legacy-tenant cleanup and break the bridge's dual-id tolerance |
| `rel_relationships.legacy_person_id` | `persons.id` | legacy compatibility column, written only by migration-era rows | Same class: constraining a legacy column would freeze a cleanup path. No live writer depends on it |
| `founder_objects.space_id` | `founder_spaces.id` | `app/founder/…` writes founder objects for legacy spaces | `founder_spaces` is a retirement candidate (workspace ADR §5). Hardening the link before deciding the retirement would add cost to the eventual removal |
| `sh_objects.organization_id` (ondelete) | — | `SET NULL` in PostgreSQL, ORM declares default `NO ACTION` | Not a missing guarantee but a *difference*. `SET NULL` on organization deletion is arguably safer than `RESTRICT`; changing it is a policy decision. Recorded, not changed |

**What would close each:** a decided domain meaning for `tenant_id` (org vs legacy
tenant), an owner decision on the `workspaces` retarget/rename, and the
`founder_spaces` retirement decision. None is a code fix in isolation.

## 2. Indexes (36 remaining)

All 36 are **non-unique** indexes on table columns, with no foreign key behind them:
filter/search columns (`leads.status`, `leads.destination`, `rel_relationships.email`,
`memory_records.memory_key`, `suppliers.city`, …) on tables that are empty or
near-empty in every environment available here.

Adding them would be a guess: PostgreSQL would maintain 36 writes per insert for
queries nobody has demonstrated. The evidence test for an index is a query plan on
realistic data volume (`EXPLAIN (ANALYZE)` showing a sequential scan that matters),
and no production query log or dataset is available to this milestone.

**What would close them:** a query-profile capture from the production or staging
read path, or a specific slow-surface report. At that point each index is added
with its measured plan as justification.

## 3. What G1.21 *did* add (unchanged here)

20 foreign keys and 9 unique indexes on the canonical identity → organization →
workspace → object chain, each orphan-checked and duplicate-checked at migration
time, skipping (never deleting) when existing data would violate them. That set is
the part where a structural invariant was provable from the write paths.

## 4. Residual risks accepted

* An object can still be written with an `organization_id` that no longer exists
  (`SET NULL` only fires on deletion).
* `workspaces.tenant_id` continues to hold an organization id under a misleading
  name.
* Dead legacy tables (`invitation_tokens`) remain unconstrained.
* `founder_objects` can reference a deleted founder space.

Each is listed in the ledger with the decision that owns it. None blocks the
supported organization → workspace → object journey, which is FK-enforced end to
end and verified on PostgreSQL (G1.21 §22.6).

---

## 5. G1.24 — `r6b38_object_provenance` (no new constraint, no new index)

The only schema change in G1.24 is one nullable column,
`sh_objects.provenance VARCHAR(32)`. Reviewed against the same evidence tests:

| Question | Answer |
|---|---|
| Domain target | The row's creation origin: `user` / `import` / `ai` / `onboarding_seed` / `system` / NULL (unknown history) |
| Why a column and not a heuristic | Origin cannot be reconstructed after the fact: an edited placeholder and an unused one are identical once written |
| Constraint added | **None.** A `CHECK` on the vocabulary would reject historical NULL semantics and any future source the domain adds; validation is enforced at the single write path (`ObjectService.create` → `normalise_provenance`) |
| NOT NULL / default | **No.** Existing rows must keep NULL = unknown; a default would fabricate provenance for history |
| Index added | **None.** The first-use query filters on `organization_id` (already indexed) plus `is_deleted`; no `EXPLAIN` evidence exists showing a provenance index is needed, and an unproven index is write cost without a query |
| Backfill | **None in the migration.** Converting historical rows by pattern-matching the seed shape would be inference, not history; a user-created record named "Customer" with empty content would be misclassified and silently excluded from first-use and AI grounding |
| Downgrade | Drops the column. This is inherently lossy for provenance *values* (rows and all other columns survive) — recorded so a downgrade is never mistaken for a reversible data operation |

### Executed evidence (disposable PostgreSQL 16, port 55432)

Isolated cluster created with `initdb` under `/tmp/g124_pg`, database
`g124_migration`; production PostgreSQL on 5432 was never contacted.

| Check | Result |
|---|---|
| `alembic upgrade r6b37_onboarding_sessions` from zero | exit 0, revision `r6b37_onboarding_sessions` |
| Pre-upgrade row inserted (`sh_objects`, no `provenance` column) | 1 row |
| `alembic upgrade head` | exit 0, `r6b38_object_provenance` |
| Column shape after upgrade | `character varying(32)`, `is_nullable=YES`, `column_default=NULL` |
| Pre-existing row after upgrade | survived, `provenance = NULL` (unknown, not converted) |
| Grounding predicate on that row | counted as business data (unknown ≠ example) |
| Seed row (`onboarding_seed`) added | excluded from the groundable count, present in the example count |
| Repeat `upgrade head` | exit 0, no-op (guarded DDL) |
| `downgrade -1` → `upgrade head` | exit 0 both ways; head restored |
| Cluster state after test | stopped, port 55432 free; data dir preserved at `/tmp/g124_pg` (not deleted) |

Residual risk accepted: `provenance` is application-validated, not
database-constrained, so a direct SQL writer could store an out-of-vocabulary
value. The read paths treat any unknown non-NULL value as business data (never as
an example), which fails toward showing data rather than hiding it.
