# Foundation repair — execution checkpoint, not project certification

## Governing basis

The existing constitution and founding data remain unchanged. This repair derives
from docs/canon/02_shunya_constitution.md (human agency, explainability, privacy),
docs/canon/01_shunya_vision.md (human capability amplification and truth before
narrative), and governance/EXECUTION_DOCTRINE.md (evidence, persistence, fail closed).
No new engine or parallel runtime is introduced. Existing release governance and
deployment scripts are repaired. Human control, quietly helpful explanations,
and low-cost high-quality execution remain product requirements, not proven claims.

## Observed baseline

- Repository and public health: 94907a6fec132989db42ff9ef1be8fb4e90146cc.
- Actual GitHub Actions run 34446922166: test job succeeded; deployment failed.
- Job 102777753240 reached the host and failed the dirty-tree guard because
  tests/test_prod06.db existed. It was not a runner queue or SSH-input failure.
- Public homepage -> Get Started -> sign-in rendered. No authenticated journey
  was exercised; login, assistant execution, and responsive acceptance are open.
- /health advertised CI_CERTIFIED while deployment provenance was dated earlier
  than the build. Code supplied certification when evidence was absent/invalid.

## Changes

- Missing, malformed, incomplete, or different-build provenance becomes
  UNVERIFIED, without rewriting the record. Health compares against the loaded
  application SHA rather than mutable checkout HEAD. Availability stays separate
  from release certification.
- Normal deployments can record the true previous SHA for rollback.
- Deployment now requires a PostgreSQL custom-format backup and catalog check
  before migrations. Backup failure stops execution. Credentials use a private
  temporary pgpass file, never command arguments or logs.
- Health verification uses network -> local file -> JSON parsing and rejects a
  missing SHA. Provenance recording failure is fatal, not a warning.
- The existing process-isolation test's database path is relocated to pytest's
  temporary directory; production .env loading is removed. Assertions and its
  existing skip marker are not weakened or expanded.

## Actual validation evidence so far

- Release tests demonstrated baseline failures for invented certification,
  malformed records, stale records, loaded-build mismatch, and rollback identity.
- New targeted tests: 14 passed; legacy process-isolation case remains skipped on
  SQLite. That skip does not prove PostgreSQL execution correctness.
- Frontend build/typecheck succeeded. Vitest: 39 passed. Lint governance succeeded.
- Real production backup created outside the checkout at
  /home/shunya-deploy/backups/shunya/foundation-repair-20260911/predeploy.dump.
- Backup restored successfully using pg_restore --exit-on-error into a separate
  private Unix-socket PostgreSQL validation cluster: 216 public tables;
  sh_objects count 483. This is backup/restore evidence, not a product journey.
- Old test database and sidecars preserved with verified SHA256SUMS under
  /home/shunya-deploy/backups/shunya/foundation-repair-20260911/test-artifacts/.
- Full regression/remote CI/deployment are separate gates; consult completed tool
  outputs and exact-SHA Actions run, not this checkpoint, for their outcome.

## Open defects and limits (not an exhaustive project inventory)

1. app/ai/routes.py: chat uses conv_system/space_system, legacy object existence
   checks, a first-membership organization lookup and organization_id=0 fallback;
   conversation persistence exceptions are logged while inference continues.
   Canonical ownership and fail-closed persistence require a separate repair.
2. app/founder/workspace_intelligence.py and insight_engine.py still query
   FounderObject; read convergence is not complete.
3. app/ai/routes.py: explain synthesizes a fresh request instead of loading the
   original result; user-facing explanation provenance is not established.
4. Inference fallback paths exist alongside the kernel. Per-request budget,
   provider consent, retrieval scoping and context continuity need end-to-end
   verification. Provider-name heuristics are not proof of free inference.
5. tests/test_prod06_process_isolation.py declares a PostgreSQL contract but uses
   SQLite and is skipped in SQLite CI. Its concurrency certification is open.
6. Existing port-5433 validation cluster returned a missing shared-memory-segment
   error. It was not restarted or used for the restore proof; a private cluster
   was created instead, leaving existing infrastructure untouched.
7. Migration schema changes are not part of this patch. The existing media-tenancy
   migration was rehearsed successfully against the restored backup. All
   founding/customer records and constitutional documents remain preserved.
8. Snapshot reconciliation found 167 canonical objects with NULL organization_id,
   all linked to non-personal sh_workspaces. All 483 canonical objects resolve to
   sh_workspaces, none to founder_spaces/user_workspaces. One legacy object has
   no canonical counterpart. These are snapshot observations requiring ownership
   investigation, NOT authorization to guess tenants or rewrite records.

Project status: IN PROGRESS. R6B and full founder acceptance are not certified.
