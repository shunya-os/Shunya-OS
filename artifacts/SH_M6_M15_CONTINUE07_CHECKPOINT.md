# SH-M6→M15 CONTINUE-07 — CHECKPOINT (post-deploy runtime proofs)

**Campaign**: SH-M6→M15-CONTINUE-07 ("DO NOT CLOSE GAPS PREMATURELY")
**Date**: 2026-10-08
**Production SHA at campaign start**: 5e0720e

## SHA CHAIN (history — never a moving "current")

- `5e0720e` — production SHA at campaign start (CI_CERTIFIED, healthy)
- `618b3da` — CI run 37812844215 SUCCESS; deploy SUCCESS (deployed 17:20:42Z). Contents: documents page-route ownership fix (single owners, deep-link crash removed), live DuckDuckGo tests retry-aware + offline provider contract, CI Node 22 pin, CONTINUE-07 checkpoint.
- `1772ac4` — CI run 37817220980 SUCCESS; deploy SUCCESS (deployed 17:56:47Z). Contents: media canonical workspace-context fix (web journey was fail-closed 403), +4 web-journey contract tests, `scripts/verify_continue07_runtime.py`.
- Deployed SHA at proof time: `1772ac4` — health `backend_release_sha` matched, `build_identity_matches_running_build: true`, `database: connected`.

## WHAT WAS PROVEN — RUNTIME, OVER HTTPS, ON THE DEPLOYED BUILD

`scripts/verify_continue07_runtime.py` → **20/20 PASS** (raw output committed as
`artifacts/SH_M6_M15_CONTINUE07_RUNTIME_PROOF.txt`):

- unauthenticated `/documents` → 302 → `/login?next=/documents`
- certification sign-in (isolated tenant) → `/documents` → 200 SPA shell, no 500;
  `/documents/<id>` deep link 200 (the TemplateNotFound crash is gone); document API 200
- media: generate 200 (`runtime_state=description_only` — the truthful provider-unavailable
  path, no fake success), rename persisted, archive, trash-from-archived allowed,
  trash-from-trashed refused (404 state guard), restore cycles, permanent delete,
  irreversibility proven (GET after delete → 404), unauthenticated media API 401 fail-closed.

**New product defect found by this proof and fixed in `1772ac4`**: media mutations were
fail-closed 403 for EVERY real web user — `_workspace_id()` only accepted session/g values
that no product path sets (`/api/*` returns early in `_check_auth`; `session["workspace_id"]`
set nowhere). The CI fixtures masked it by injecting the session value. Fixed via the ONE
canonical authority (`app.authz.workspace_context.resolve_current_workspace`) + frontend
`fetchWithAuth` wiring (previously unwired); contract tests exercise the journey WITHOUT
the injected session key.

## CI TRUTH

- 37807894159 (`0b25c9c`): FAILED — single live-DDG failure (upstream refuses individual
  requests from datacenter IPs; canonical call refused while a raw probe served seconds later)
- 37812844215 (`618b3da`): **SUCCESS** (retry-aware classification + offline contract; frontend
  gates incl. pinned Node 22; deploy SUCCESS)
- 37817220980 (`1772ac4`): **SUCCESS**; deploy SUCCESS

## LOCAL FULL SUITE (directive L)

1923.15s (32:03), **5458 passed, 125 skipped, 9 failed** — all 9 classified and evidenced as
deploy-host artifact failures (health fail-closed because the working tree was ahead of the
deployed build_identity + immutable-release provenance; the identical content is CI-green and
the live service is healthy). The earlier "420s timeout" was a tool wait limit, not a hang.

## J — HISTORICAL CREDENTIAL: RESOLVED (independently verified)

Four historical credential literals found in history (verify-deployment.sh PGPASSWORD, script
DSNs, ci-cd.yml test DSN, docker-compose value). Hash-only comparison: **none match the live
database credential** (password auth enforced; postgres loopback-only; the 5433 test cluster no
longer exists; tracked tree clean). 0233254's recorded claim ("removed values do NOT match the
production DATABASE_URL password") independently CONFIRMED. **ROTATION NOT REQUIRED — evidenced.
No rotation performed; no founder decision required for this item.**

## E — SIGNAL→ATTENTION: GAP PROVEN (not closed)

The `emit_signal` push-bridge has **zero callers passing tenant context**
(`app/runtime/entry.py`, `app/runtime/loop.py`) — it never fires from the real runtime loop.

## WORKTREE (directive A)

Clean at every push. The media-generator 26px→44px change is the intentional WCAG fix from
`73a9d33`, CI-verified in the applied runs.

## RESTART-SURVIVAL — IN FLIGHT

Media asset `id=35` created 2026-10-08 (pre-restart). The next deploy's service restart must
preserve it (GET after restart), then it is cleaned up. Result recorded in the next ledger update.

## REMAINS UNPROVEN (explicit)

- restart-survival result (asset 35) + cleanup
- E wiring + end-to-end loop; F semantic M6 ingestion (NOT STARTED); G document-intelligence
  depth (real-document semantic hierarchy); H AI operating layer; I human-context behavioural
  proof; K browser journeys (media UI click-through, frontend refresh, logout/login)
- Observation (read-only diag, NOT touched): newest pre-existing media assets (ids 23–32,
  identity `sid_a3cd…`, org 0) include explicit prompts — a data-hygiene/provenance item
  surfaced by inspection; no autonomous action taken.

## NEXT EXECUTION BLOCK

1. Verify asset 35 survived the deploy restart → cleanup → record
2. E: wire `emit_signal` callers with tenant context and prove the real loop
3. F/G/H/I/K in directive order
