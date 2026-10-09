# SH-M6→M15 CONTINUE-16 CHECKPOINT — Tenancy FK convergence, tier 1

Base: b9b1330 (CI-27, deployed). This work: migration
c_tenancy_fk_convergence_tier1 (dry-run verified against production, then
deployed via this push).

## The convergence map (production, measured — not estimated)

65 FK constraints referenced the legacy `tenants` table (three retargeted
earlier this campaign: suppliers, documents, human-context x2 — the family
that produced the M6 supplier outage and the Stage C manual-classification
403/404). Inventory split:

- TIER 1 — table EMPTY (56 constraints): dropping the stale FK is pure
  hygiene; removes the latent "write an organization id -> FK violation"
  outage class with zero row risk.
- TIER 2 — table has rows carrying non-organization values (8 constraints):
  campaigns(5), memory_provenances(669), memory_records(778/602 non-org),
  observations(130/37), outcomes(3), tenant_themes(32/12), workspaces(1),
  tenants.parent_id (self-FK, intentional). These need a data-reconciliation
  decision per table (the memory engine's rows mostly carry LEGACY tenant
  semantics) — deliberately NOT touched here.
- TIER 3 — the deliberate bridge: organizations.legacy_tenant_id (its FK to
  tenants is intentional; excluded by name in the migration).

## What shipped

migrations/versions/c_tenancy_fk_convergence_tier1.py — self-guarding:
enumerates every FK referencing tenants at upgrade time, drops it ONLY when
its table is still completely empty, prints a truthful per-table note for
every kept constraint (no silent skips). organizations.legacy_tenant_id
excluded by name. Idempotent (second run = no-op). Downgrade is a DOCUMENTED
NO-OP with the reasoning inline (recreating the stale FKs would restore the
drifted state; a partial reconstruction would depend on guessed names).

Dry-run against production (transactional, own functions): 65 -> 9
in-transaction (dropped 56, kept 8 non-empty, excluded 1 bridge); rollback
returned the count to 65 — ROLLBACK CLEAN. Production alembic head confirmed
at c_human_context_tenancy_retarget before the chain link. `alembic heads`
shows a single new head (no branch). Migration-engine suite: 14 passed.

## Next increments (tier 2 planning inputs)

- memory_records / memory_provenances: decide the semantics (legacy values
  are historical; new writes should be organization-scoped) — likely a
  dual-read migration with a mapping for the organizations that HAVE a
  legacy bridge row, and an explicit "unmapped legacy" marker otherwise.
- campaigns / outcomes / tenant_themes / workspaces: same decision, small
  row counts.
- tenants.parent_id: keep (self-referential, intentional).
