# SH-M6→M15 CONTINUE-16 CHECKPOINT — Tenancy FK convergence (tier 1 deployed; tier 2 in this push)

Base: b9b1330 (CI-27, deployed). Tier 1: c_tenancy_fk_convergence_tier1
(dry-run verified, deployed via 60764e4, production-verified 65 -> 9). Tier 2:
c_tenancy_fk_convergence_tier2 (dry-run verified 9 -> 2 in-transaction,
rollback clean; rides this push).

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

## Tier 2 — shipped with this block

TIER 2 SHIPPED (c_tenancy_fk_convergence_tier2, dry-run: 9 -> 2 in-transaction,
rollback clean; 7 FKs dropped with rows preserved — no data rewrite):
campaigns, memory_provenances, memory_records, observations, outcomes,
tenant_themes, workspaces. The survivors after tier 2 are exactly the two
deliberate ones: organizations.legacy_tenant_id (bridge, org 7 <-> legacy 89)
and tenants.parent_id (self-referential).

Deferred by design — the historical-memory rewrite (89 -> 7 for 1,226 rows
across campaigns/memory_*/observations/outcomes/workspaces): value
distribution measured (89 is the only bridge-mappable legacy value; org 7 is
its owner); tenant_themes carries unmapped dead-demo values (91/97/113/...)
that stay as historical markers. The rewrite is a founder-reviewed product
decision (it changes what the intelligence engine can recall), NOT a schema
step; new writes already use organization ids everywhere.

## Verification (post-deploy, production)

- /health: 60764e4 CI_CERTIFIED; alembic head c_tenancy_fk_convergence_tier1
  applied; live FK inventory: 65 -> 9 survivors, exactly the documented set.
- CI-28 required two Docker-Hub-rate-limit retries (infrastructure, not
  code; the tests never ran on the failed attempts) — resolved on attempt 5.

## FINAL STATE (production-verified, 2026-10-09 late)

- /health: bca7e12 CI_CERTIFIED; alembic head c_tenancy_fk_convergence_tier2.
- Live FK inventory: **FKs referencing tenants: 2** — exactly the deliberate
  pair: the organizations.legacy_tenant_id bridge (org 7 <-> legacy 89) and
  tenants.parent_id (self-referential). Campaign total: **68 -> 2** stale
  legacy FKs eliminated (suppliers, documents, human-context x2 retargeted
  to organizations; 56 dropped on empty tables in tier 1; 7 dropped with rows
  preserved in tier 2). No row was rewritten by any tier.
