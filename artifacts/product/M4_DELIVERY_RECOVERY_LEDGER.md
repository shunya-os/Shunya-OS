# M4 DELIVERY RECOVERY — EXECUTION LEDGER

**M4 STATUS:** BLOCKED — DELIVERY CERTIFICATION FAILED (runtime recovered, CI/CD gate NOT yet green)
**CURRENT BLOCKER:** no successful exact-SHA CI/CD run since the runtime recovery
**CURRENT SHA:** 8738d29 (HEAD = origin/master; production content = 8738d29)
**LAST UPDATED:** 2026-09-18 08:40 CEST

> M4 is NOT complete. A deployed application, passing tests, or a healthy public
> endpoint is NOT sufficient by itself. M4 closes only on a fresh GitHub Actions
> run whose OVERALL conclusion is SUCCESS for the deployed exact SHA.

---

## Git truth (verified 2026-09-18 08:33 CEST)

| Ref | SHA |
|-----|-----|
| HEAD | 8738d29b45608d97288139c5afe7d460438d5954 |
| origin/master | 8738d29 (matches) |
| CI latest (8738d29) | run 35288107886 — **FAILURE** (deploy step "Verify local health SHA") |
| Production git_commit (local **and** public /health) | 8738d29b45608d97288139c5afe7d460438d5954 |

Preserved commits: 023233e, bc0656d, 93c689a, 8738d29, c6bca28, d2b3fc8, 8479135.

Superseded entry (kept for history): at 01:35 CEST this ledger recorded HEAD/origin = 93c689a
with production running bc0656d content. Both values are now historical; commit 8738d29
(corrected release-governance test + CI readiness/latency gate) is the current certified candidate.

---

## RUNTIME RECOVERY (verified 2026-09-18) — this is the new evidence

### 1. Live systemd unit changed to gthread

- `/etc/systemd/system/shunya.service` mtime `2026-09-18 02:34:26 CEST`.
- Live unit is **byte-identical** (`diff` → no output) to
  `deploy/shunya.service.staged`, whose header documents the reason: sync workers
  let one long-lived SSE response (`/api/v1/reality/stream`) block a whole worker;
  with 3 workers a few concurrent SSE clients starve the site and the arbiter
  SIGKILLs blocked workers (111 kills observed in two hours).
- Effective ExecStart (live process argv, `ps`):
  `gunicorn --workers 3 --worker-class gthread --threads 8 --bind 127.0.0.1:5001
  --timeout 120 --graceful-timeout 30 --keep-alive 5 --max-requests 1000
  --max-requests-jitter 100 wsgi:app`

### 2. Restart completed

| Evidence | Value |
|----------|-------|
| systemd `ActiveEnterTimestamp` / `ExecMainStartTimestamp` | Fri 2026-09-18 02:35:08 CEST |
| systemd `MainPID` | 621802 |
| systemd `NRestarts` | 0 |
| Old master | 620293 — `Handling signal: term` 02:34:38, `Shutting down: Master` 02:35:08 |
| New master | 621802 — `Starting gunicorn 26.0.0` 02:35:09 |
| Workers booted | 621804, 621805, 621806 at 02:35:09 |

### 3. Running process verified as gthread

- `journalctl -u shunya` at 02:35:09: `Using worker: gthread`.
- `ps -eo pid,ppid,lstart,cmd` on 2026-09-18 08:30 CEST: master 621802 (started
  02:35:08) plus three gthread workers, all with `--worker-class gthread
  --threads 8` in argv.
- Worker 631058 was recycled by `--max-requests` at 08:08:28 and re-booted
  cleanly as a gthread worker → **restart/recycle survival confirmed**.
- `SIGKILL` / `Worker … killed` occurrences in the journal since the restart:
  **0** (previously 111 in two hours).

### 4. Three NEW-connection local /health results (measured 2026-09-18T06:31Z)

Each result is a separate `curl --no-keepalive` invocation → a genuinely new TCP
connection to gunicorn (the exact case that stalled before).

| Trial | HTTP | time_total |
|-------|------|-----------|
| 1 | 200 | **0.007824s** |
| 2 | 200 | **0.011915s** |
| 3 | 200 | **0.012599s** |

Earlier founder-reported set (same day, post-restart): 0.043s, 0.014s, 0.015s.
All three are ≤ 0.043s against a 5s CI limit, and against pre-fix behaviour of
4.9 / 9.0 / 14.3 / 22.2s on a new connection.

Body identical on all three trials: `status=ok`,
`git_commit=8738d29b45608d97288139c5afe7d460438d5954`, `build_id=8738d29`,
`release_type=CI_CERTIFIED`, `release_health_verified=true`,
`frontend_release_matches_backend=true`, `frontend_dist_mode=immutable_release`.

### 5. Three public /health results (measured 2026-09-18T06:31Z, HTTPS)

| Trial | HTTP | time_total |
|-------|------|-----------|
| 1 | 200 | 0.082251s |
| 2 | 200 | 0.052563s |
| 3 | 200 | 0.065556s |

Body: `status=ok`, `build_id=8738d29`, `git_commit=8738d29…`,
`release_type=CI_CERTIFIED`, `release_health_verified=true`,
`frontend_release_matches_backend=true`, `environment=production`,
`database=connected`.

### 6. CI run 35288107886 — FAILURE and the exact reason

- Run 35288107886, workflow CI-CD, commit **8738d29**, event `push`,
  started 2026-09-17T23:43:37Z, duration 23m29s, conclusion **FAILURE**.
- `test` job: **SUCCESS** (18m39s).
- `Deploy to Production` job (4m45s): `Set up job` ✓, `Record certified SHA` ✓,
  `Deploy via SSH` ✓, **`Verify local health SHA` ✗**, `Verify public health SHA`
  **skipped**, `Final provenance check` **skipped**, `Complete job` ✓.
- Exact failing log lines (from `gh run view 35288107886 --log-failed`):

```
Attempt 1/12: health not ready yet — retrying in 5s
Health responded on attempt 2/12 in 18.7829s
ERROR: /health took 18.7829s (limit 5s) — the app is accepting connections slowly
Process exited with status 1
```

- **Cause:** the pre-restart sync-worker stall measured by the new CI latency gate.
  The gate behaved correctly (fail-closed): it refused to certify a deployment
  whose new connections were queueing behind sync workers.
- The run is permanently concluded FAILURE and cannot be re-run; the only path to
  certification is a **new exact SHA** pushed to `master`.

### 7. Deploy-side record — stated honestly

The `Deploy via SSH` step of run 35288107886 completed and wrote a release record
for 8738d29 (`release_deployed_at=2026-09-18T00:06:16.998742+00:00`,
`release_authorized_by=CI/CD`, `release_reason="Normal deployment via CI pipeline"`,
`release_type=CI_CERTIFIED`) **before** the verification step failed at
`00:07:03Z`. So production genuinely runs 8738d29 — but the RUN's overall
conclusion is FAILURE, therefore this is **not** certification and must not be
reported as such.

---

## Resolution status of the previous ledger items (history preserved below)

| Previous item | Status |
|---------------|--------|
| §"Test change to correct" — weakened `assert status_code in (200, 503)` | **RESOLVED in 8738d29** — replaced by deterministic assertions: release-governance contract (200 + `release_type=UNVERIFIED`) plus two new explicit immutable-release tests (`503` fail-closed on SHA mismatch, `200` on match). The test was strengthened, not weakened. |
| §"CI deploy verification" — single unguarded `curl` | **RESOLVED in 8738d29** — bounded readiness (12 attempts × 5s), explicit `MAX_HEALTH_SECONDS=5` latency gate, `release_type == CI_CERTIFIED` assertion, public-health and provenance steps unchanged in strictness. |
| §"Diagnosis: production /health intermittent stall" | **ROOT CAUSE RESOLVED at runtime** — new-connection queueing behind sync workers; eliminated by the gthread unit (evidence §1–§5). The app-side SSE bound (`SSE_MAX_STREAM_SECONDS`) remains in place. |
| §"Deploy-tree contamination" | **PARTIAL** — the `artifacts/product/` ignore line was removed so governance ledgers are tracked, and the preflight (`infrastructure/scripts/deploy_preflight.sh`) fails closed on dirty/untracked trees. A scratch location separate from the production worktree is still not established (see Remaining risks). |
| §"BLOCKER requiring human action" (needed restart or ptrace) | **RESOLVED** — the controlled restart was performed 2026-09-18 02:34–02:35 CEST. |

---

## Diagnosis: production /health intermittent stall (HISTORICAL — kept verbatim)

### Confirmed facts (independently measured)

1. `/health` intermittently stalls **3–23 seconds**, then succeeds (HTTP 200). Repeated across many trials.
2. `/live` (no DB, no Redis, trivial handler) exhibits the **same stall** — so the stall is NOT route-specific.
3. During a 22.19s stall the worker consumed **0.04s CPU** (4 clock ticks) — the worker is **WAITING, not computing**.
4. Worker process state: `S (sleeping)`, wchan `futex_wait_queue`. Each worker holds one open `:5001` connection (the stalled request).
5. **PostgreSQL ruled out:** `pg_stat_activity` shows no active query longer than 0s during stalls; `pg_locks` shows 0 waiting locks; connections idle with last query `ROLLBACK`; PostgreSQL has `idle_session_timeout=0`, `idle_in_transaction_session_timeout=0`.
6. **Redis ruled out:** `redis-cli monitor` captured **zero commands** during a 22.9s stalled request.
7. **Not resource exhaustion:** load 1.0 on 4 CPUs; 4.5GB RAM free; disk 44% (41G free); 7% inodes; 10 FDs per worker (no leak); no file locks held by gunicorn (`/proc/locks`); journal 382MB.
8. Stall occurs on the **first request after idle** (60s idle → 14.3s, 22.9s, 3.7s across trials — highly variable).
9. Workers have **never recycled** in ~70 min despite many stalled requests (gunicorn `--timeout 60` did not fire).

### Measurements (first request after idle)

| Trial | Idle | Result |
|-------|------|--------|
| 1 | 60s | 200 in 14.26s |
| 2 | 55s | 200 in 22.88s |
| 3 | 62s | 200 in 3.72s |
| 4 | 62s | 200 in 22.19s (CPU delta 0.04s) |

### Ruled out

DB queries/locks, Redis, CPU, memory, disk, inodes, FD leaks, file locks, keep-alive (tested with `Connection: close` — same stall), rate limiter (no Redis traffic).

### DECISIVE FINDING (added 01:45)

The stall is **specific to NEW connections**, not to routes or the DB:

| Path | Result |
|------|--------|
| `https://shunyaos.com/health` (through nginx, warm upstream connection) | 0.077s, 0.054s, 0.077s — **always fast** |
| `http://127.0.0.1:5001/health` first request on a new connection | 4.9s / 9.0s / 14.3s / 22.2s — **stalls** |
| 2nd request on the SAME connection (curl `--next`) | **0.009s — instant** |

This is the signature of **gunicorn sync workers being occupied between requests** — with
`--worker-class` = sync (default) and `--keep-alive 5`, a worker that finishes a response
blocks waiting for the next request on that same connection, so a NEW connection must wait for a
worker to become free. New connections therefore queue; reused connections do not.
**→ Confirmed and eliminated by the gthread unit change (evidence §1–§5 above).**

Each worker additionally holds an idle Redis `subscribe` connection (event-bus relay,
`sub=1`, age 4378s) on a second thread blocked in `wait_woken` — the relay itself is stable and
issues no commands during stalls, so it is NOT the blocker, but it does occupy one thread and one
connection per worker.

### Confirmed absent
- thread leak (2 threads/worker, constant), FD leak (10/worker, constant), RSS leak (168MB, constant)
- DNS/NSS slowness (`getent hosts localhost` = 4ms)
- disk/inode pressure, journal pressure, CPU starvation (load 1.0 / 4 CPUs)

### Tools unavailable (at diagnosis time)

`strace` attach → `Operation not permitted` (no ptrace capability). `py-spy` not installed. `sudo` blocked (no consent). `dmesg` blocked. nginx logs not readable. The exact blocking syscall/lock could not be captured — it was ultimately resolved at the configuration layer instead.

### Test change to correct (directive §2) — original text, now RESOLVED

`tests/test_release_governance.py::test_health_matches_record_to_loaded_build` was changed to
`assert result.status_code in (200, 503)` — this must be corrected to assert the ONE intended
behaviour deterministically. **Corrected in 8738d29:** the vaulted `in (200, 503)` assertion is
gone; the test now isolates frontend provenance to `worktree_build` and asserts 200 +
`release_type=UNVERIFIED` + `release_health_verified is False`, and two dedicated
immutable-release tests assert the 503 fail-closed and 200 match contracts.

### Deploy-tree contamination (directive §9) — original text

The deploy preflight correctly refused because audit artifacts were written **inside the
production checkout** (`artifacts/…`, `*.md` audit files, `scripts/prod_db_investigate.py`).
Those files were moved to `/tmp/shunya-audit-archive/` and `.gitignore` was extended. The
long-term fix (separate audit scratch location from the production worktree) is **NOT yet done**.

### CI deploy verification (directive §6) — original text, now RESOLVED

Current workflow: `curl -fsS --max-time 30 http://127.0.0.1:5001/health` in a single SSH step
with no readiness wait. Needs deterministic readiness (bounded retry) before the SHA comparison,
and must still FAIL on a genuine mismatch. **Implemented in 8738d29** — and it did fail closed,
on run 35288107886, against a genuinely slow application.

---

## Remaining risks observed (NOT fixed by this change)

1. **Credential exposure in logs:** the gunicorn app logs the SQLAlchemy URL including the
   database password at start-up (`"db": "postgresql://shunya:<redacted>"`). Anyone able to read
   the journal can read the production DB credential. Not addressed here (would be a product/
   config change).
2. **Audit scratch location:** the long-term fix separating audit scratch from the production
   worktree is still open; the deploy preflight will keep refusing if any untracked file appears
   in `/home/shunya-deploy/shunya_os`.
3. **Redis subscribe thread per worker:** each worker still holds one idle event-bus `subscribe`
   connection and one blocked thread. Not a blocker, but it caps effective thread headroom under
   gthread.

---

## M4 STATUS STATEMENT

**M4 remains BLOCKED.** The runtime defect that failed run 35288107886 is recovered and the
recovery is independently measured (§1–§5). However, M4 closure requires a **fresh CI/CD run for
a new exact SHA whose OVERALL conclusion is SUCCESS** — test job, deployment, local health SHA
match, latency < 5s, `release_type == CI_CERTIFIED`, public health SHA match, final provenance.
Individual green jobs do not close M4.

## NEXT ACTION

1. Commit + push this ledger update → new exact SHA.
2. Wait for the GitHub Actions run for that exact SHA; require **overall SUCCESS**.
3. Then independently verify: `HEAD == origin/master == GitHub certified SHA`; production local
   `/health` SHA == certified SHA; public `/health` SHA == certified SHA;
   `release_type == CI_CERTIFIED`; a new TCP connection to `/health` remains fast; restart survival.
4. Only then update this ledger to **M4 COMPLETE**.
5. **No M5 work under any circumstance until the complete M4 delivery gate is green.**
   If ANY gate fails → stop and report M4 BLOCKED with the exact failed gate.
