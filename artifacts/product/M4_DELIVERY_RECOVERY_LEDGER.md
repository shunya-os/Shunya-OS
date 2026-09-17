# M4 DELIVERY RECOVERY — EXECUTION LEDGER

**M4 STATUS:** BLOCKED — DELIVERY CERTIFICATION FAILED  
**CURRENT BLOCKER:** production /health intermittent stall + CI verification  
**CURRENT SHA:** 93c689a (HEAD=origin), production running bc0656d content  
**LAST UPDATED:** 2026-09-18 01:35 CEST

---

## Git truth (verified)

| Ref | SHA |
|-----|-----|
| HEAD | 93c689ac4c372a405cf75478a197e75d2d04e738 |
| origin/master | 93c689a (matches) |
| CI latest (93c689a) | FAILURE — deploy verification step |
| Production git_commit | bc0656d0be9e7788e69c2e000a1af7181b64806c |

Preserved commits: 023233e, bc0656d, 93c689a, c6bca28, d2b3fc8, 8479135.

---

## Diagnosis: production /health intermittent stall

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

### Not yet determined

The exact in-process wait. The worker waits on a futex with ~0 CPU. Candidates:
- an in-process lock held by a background thread
- a C-extension-level thread wait
- a runtime/network primitive

### DECISIVE FINDING (added 01:45)

The stall is **specific to NEW connections**, not to routes or the DB:

| Path | Result |
|------|--------|
| `https://shunyaos.com/health` (through nginx, warm upstream connection) | 0.077s, 0.054s, 0.077s — **always fast** |
| `http://127.0.0.1:5001/health` first request on a new connection | 4.9s / 9.0s / 14.3s / 22.2s — **stalls** |
| 2nd request on the SAME connection (curl `--next`) | **0.009s — instant** |

So: a new TCP connection to gunicorn takes 5–23 s to serve its first request; reusing that
connection (or using nginx's warm upstream connection) is instant.

This is the signature of **gunicorn sync workers being occupied between requests** — with
`--worker-class` = sync (default) and `--keep-alive 5`, a worker that finishes a response
blocks waiting for the next request on that same connection, so a NEW connection must wait for a
worker to become free. New connections therefore queue; reused connections do not.

Each worker additionally holds an idle Redis `subscribe` connection (event-bus relay,
`sub=1`, age 4378s) on a second thread blocked in `wait_woken` — the relay itself is stable and
issues no commands during stalls, so it is NOT the blocker, but it does occupy one thread and one
connection per worker.

### Confirmed absent
- thread leak (2 threads/worker, constant), FD leak (10/worker, constant), RSS leak (168MB, constant)
- DNS/NSS slowness (`getent hosts localhost` = 4ms)
- disk/inode pressure, journal pressure, CPU starvation (load 1.0 / 4 CPUs)

### Tools unavailable

`strace` attach → `Operation not permitted` (no ptrace capability). `py-spy` not installed. `sudo` blocked (no consent). `dmesg` blocked. nginx logs not readable. So the exact blocking syscall/lock could not be captured.

---

## Test change to correct (directive §2)

`tests/test_release_governance.py::test_health_matches_record_to_loaded_build` was changed to
`assert result.status_code in (200, 503)` — this must be corrected to assert the ONE intended
behaviour deterministically. Present state: `monkeypatch _GIT_COMMIT='c'*40` +
`record_normal_deployment('a'*40)` → the immutable-release provenance check compares against the
real frontend release SHA, correctly producing a mismatch → 503. The test must express the
intended contract (what SHOULD happen when the loaded build SHA does not match the recorded
release) rather than accept both outcomes.

---

## Deploy-tree contamination (directive §9)

The deploy preflight correctly refused because audit artifacts were written **inside the
production checkout** (`artifacts/…`, `*.md` audit files, `scripts/prod_db_investigate.py`).
Those files were moved to `/tmp/shunya-audit-archive/` and `.gitignore` was extended. The
long-term fix (separate audit scratch location from the production worktree) is NOT yet done.

---

## CI deploy verification (directive §6)

Current workflow: `curl -fsS --max-time 30 http://127.0.0.1:5001/health` in a single SSH step
with no readiness wait. Needs deterministic readiness (bounded retry) before the SHA comparison,
and must still FAIL on a genuine mismatch.

---

## NEXT ACTION

1. Correct the weakened release-governance test to assert the intended contract deterministically.
2. Determine whether the /health stall is transient (runtime state) or persistent (code/config):
   perform a controlled restart via the sanctioned mechanism, then re-measure.
3. If persistent: continue root-cause on the in-process wait (needs ptrace/root or a reproducible
   local run).
4. Add deterministic readiness/retry to the CI deploy verification.
5. Re-run full regression (0 failures), then the delivery gate.

## BLOCKER requiring human action

The exact blocking primitive cannot be captured without ptrace capability or root. Either:
- grant approval to restart `shunya.service` (controlled), or
- grant ptrace capability / install py-spy, or
- run a reproduction locally.

Until then, M4 remains BLOCKED.
