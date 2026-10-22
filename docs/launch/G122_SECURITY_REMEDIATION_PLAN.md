# G1.22 — Historical Security Incident Remediation Plan

**Status:** evidence recorded, containment reviewed, remediation **not executed**.
Every destructive or credential action below requires explicit owner authorization
(`HISTORY_REWRITE_AUTHORIZED = NONE`, `CREDENTIAL_ROTATION_AUTHORIZED = NONE`).
No secret value was read, printed, copied, tested, rotated or transmitted while
producing this plan.

Three incidents are tracked separately. Nothing here asserts that an exposed token
is live or dead: that requires an authorized check against the issuing provider,
which this milestone is not permitted to perform.

---

## INC-1 — Telegram bot token in Git history

| Field | Evidence |
|---|---|
| Artifact | `data/telegram_bot_token.txt` — a single line, 46 characters, matching the bot-token shape `\d{6,10}:[A-Za-z0-9_-]{30,40}` |
| First committed | `4fe3f99` ("Initial commit: Panchi Club Travel OS") |
| Removed from tree | `5e1fcf2` ("chore: add data/ to gitignore, remove sensitive token file") |
| Present at HEAD | **No** (verified: `git ls-tree -r HEAD` contains no such path) |
| Exposure scope | Anyone who cloned or forked the repository between those commits; GitHub's own object store; any CI cache or mirror created in that window |
| Validity | **UNKNOWN** — determining whether the token still authenticates requires calling the Telegram Bot API with it. Not authorized, not attempted |

**Immediate containment (already in place):** `.gitignore` excludes
`data/telegram_bot_token.txt`; GitHub secret scanning and push protection were
enabled during the D4 containment work (read-back verified at the time — not
re-verified in G1.22).

**Required owner action (blocking):**

1. **Rotate via BotFather** — `/revoke` for the affected bot, generate a new token,
   set it in the production environment, restart the bot worker, confirm a message
   round-trips. Rotation is reversible-by-recreation and needs no history rewrite.
2. Only after rotation should the incident be marked *credential remediated*. The
   history exposure remains until INC-1b is decided.

**Residual exposure after rotation:** the old string stays readable in history; a
rotated token is inert, so the risk shifts from *usable credential* to
*false-positive noise* in scanners.

## INC-1b — History still contains the token (and INC-2 PII)

Both are the same class of action: rewriting published Git history.

| Option | Effect | Cost / risk | Who may authorize |
|---|---|---|---|
| A. Make the repository private | Stops new exposure immediately; history intact | Reversible; existing clones keep the data; does not satisfy any "remove the secret" audit requirement | Repository owner |
| B. Path-scoped history purge (`git filter-repo`) + force-push | Removes the blobs from the default branch's ancestry | **Irreversible for collaborators**, breaks every existing clone/fork, rewrites all downstream SHAs, requires coordinated re-clone | Repository owner, explicitly accepting force-push |
| C. GitHub Support purge of cached views | Removes GitHub-side cached blobs | Requires GitHub engagement; does not fix forks | Repository owner |

**Recommendation:** A immediately (cheap, reversible), then B only if a compliance
requirement demands object removal, executed with a documented pre-flight
(`git bundle` backup of all refs, checksum manifest of the removed paths, list of
known forks to notify).

**Verification after either action:** `git log --all --oneline -- <path>` returns
nothing; `git rev-list --objects --all | grep <path>` returns nothing; a fresh
clone contains no matching blob; secret scanning reports no open alerts.

---

## INC-2 — Founder PII in historical `uploads/`

| Field | Evidence |
|---|---|
| Artifact | Three founder itinerary PDFs, one internal audit PDF, eleven test files under `uploads/` |
| Commits | 4 commits touch `uploads/` in history |
| Present at HEAD | **No** (untracked since the L4 index-untrack; `.gitignore` covers `uploads/`) |
| Current copies | The originals exist on the production host under `backups/legacy_repo_uploads_20261013/`, sha256-verified against the untracked originals (D4 inventory) |
| Exposure scope | Same as INC-1b: clones/forks of that window |

**Handling decision required (owner):** PII is not a credential — rotation is not
applicable. The choice is whether the published history must be cleaned (option B
above) and whether the founder wishes the documents redacted or retained. No purge,
no deletion and no movement of those files was performed in G1.22.

**Residual risk if left:** names, travel details and itineraries of real people
remain readable in history by anyone with a clone.

---

## INC-3 — `.env` blobs in history

| Field | Evidence |
|---|---|
| Artifact | `.env` (repository root) in 2 commits |
| Content | Previously inventoried as placeholder/empty values only (values ≤8 characters or `your_key_here`); no production value was ever committed |
| Present at HEAD | **No** (only `.env.example` templates are tracked) |
| Current host file | `/home/shunya-deploy/.env` is untracked, mode 0600 |

**Assessment:** low severity — placeholder-era content. **Not** proof that no
credential was ever committed; the claim rests on the D4 inventory of every blob in
those commits.

**Required action:** none beyond INC-1b if history is purged for other reasons.
Re-run the blob inventory before declaring the incident closed.

---

## INC-4 (new, found during G1.22) — tests reached a live email provider

| Field | Evidence |
|---|---|
| What happened | With `RESEND_API_KEY` present in the host environment, a signup inside the test suite issued a **real** call to `api.resend.com` (`Email accepted by Resend: id=01a160…`, followed by 429 retries) for a synthetic `@g122.test` address |
| Root cause | `email_service.send_email()` passes `is_human_triggered=True` (correct for production), and nothing in the test configuration removed the provider credentials — so any test that triggers a verification or invitation email made an outbound request |
| Data exposed | None: the recipient domain does not exist, the body contains a token for a synthetic account, and nothing was delivered |
| Containment applied | `tests/conftest.py` now **forces** `EMAIL_PROVIDER=smtp` and removes `RESEND_API_KEY`, `EMAIL_USER`, `EMAIL_PASSWORD` from the test process before the app is imported; a regression test asserts the non-sending mode and that `status != accepted` |
| Verified | Re-ran the email-related suites: **0** occurrences of `api.resend.com` in the logs |

**Residual risk:** the same hazard exists in any other harness that boots the app
with host credentials (certification scripts, ad-hoc `python -c`, the local test
server). Those must set `EMAIL_PROVIDER=smtp` with no credentials, as the G1.22
test server run did.

**Owner action:** none for this incident. Note that the production key itself was
never exposed and does not need rotation on the basis of this finding.

---

## INC-5 — live Resend API key surfaced in a local test log

| Field | Evidence |
|---|---|
| What | A regression assertion in the test suite rendered a **live** `RESEND_API_KEY` into `f_fullsuite.log` (3 occurrences) |
| Root cause | `create_app()` calls `load_dotenv()`, which re-reads the host `.env` **after** `conftest` cleared the environment; `email_core` had already bound the value at import, so the "tests cannot send mail" protection did not hold and the guard test printed what it found |
| Scope | One local log file under the agent scratch directory. Not committed, not pushed, not in the repository, not transmitted anywhere |
| Live? | **Yes** — treat as a valid credential until the owner rotates it |
| Containment applied | `conftest` now neutralises `email_core`'s module state and re-asserts it in an autouse fixture before/after every test. Verified: delivery suite 6 passed in 8.45 s with **0** provider/network lines (previously 116 s of real 429 retries) |
| Evidence handling | Original log preserved unmodified; a redacted working copy was written by streaming (`f_fullsuite.redacted.log`, 1168 lines, 0 key-shaped occurrences). No further copies made |
| Owner action (blocking) | Rotate the Resend key, update the production environment, then delete the original log through the approved process. Rotation and deletion are **not** authorized here |
| Structural fix (deferred) | Skip `load_dotenv()` when `TESTING` is set, so test processes never inherit production secrets. This is a production configuration change and needs its own review |

**Why this is recorded as an incident and not as a test bug:** the test did what it
was written to do — it detected that the protection had silently lapsed. The defect
is that a production secret can enter a test process at all, and that its value can
reach a log when an assertion fails.

---

## Prevention review (Workstream A3)

| Control | State | Evidence |
|---|---|---|
| Secret detection before publication | Present at the platform level (GitHub secret scanning + push protection, enabled during D4) | Recorded in the D4 inventory; **not re-verified** in G1.22 (requires repository API access) |
| No real credentials in test fixtures | Enforced by `tests/test_no_plaintext_credentials.py` (passing in the full suite) | [executed] |
| No external email from tests | **Added in G1.22** — forced non-sending provider in `conftest.py` + regression test | [executed] |
| No external AI from tests | Pre-existing (`SHUNYA_AI_PROVIDERS=local`) | [source] |
| Endpoint isolation uses identity **and** execution context | Hardened in G1.21 (`app/safety/db_guard.py`): loopback only, production names refused on any port, port 5432 refused without an isolation marker, PostgreSQL refused outside a declared test context | [executed] — 58 tests |
| No silent production-URL fallback | `conftest.py` raises when `DATABASE_URL` is absent; guard module holds no default connection string; declared before any app import | [executed] |
| Log redaction of capability tokens | **Fixed in G1.22** — `[EMAIL LOG]` no longer prints the body (which carries verification/invitation/reset links); invitation route logs status only, never body or token | [executed] |
| Log redaction of connection strings / cookies / auth headers | Pre-existing `app/security/redaction.py` + `tests/test_log_secret_redaction.py` | [executed] |

**Deliberately not added:** a new secrets-scanning platform, a pre-commit hook
framework, or a vault. The existing controls cover the observed failure modes; the
gap was configuration, not tooling.

---

# G1.24 status (continuation)

**No credential action was taken in G1.24.** No key was opened, printed, copied,
tested, transmitted or rotated; no evidence was deleted; no history was rewritten.
The incidents remain separate records and are not closed.

## INC-5 — Resend key in a local log

| Item | State at G1.24 exit |
|---|---|
| Original evidence | unchanged; still mode `664`, still the only original copy |
| Redacted review copy | unchanged, used for diagnostics |
| Credential status | **Exposed until the owner says otherwise** — `CREDENTIAL_ROTATION_AUTHORIZED = NONE` |
| Evidence disposition | not performed — `EVIDENCE_DELETION_AUTHORIZED = NONE` |

**Owner sequence (unchanged, exact):** revoke in the Resend dashboard → create a
sending-scoped replacement → update the production secret store → restart the mail
worker → confirm a send from the production path without printing the value →
`chmod 600` then dispose of the original log per retention policy, keeping the
redacted copy → record residual exposure in any log shipper, backup or shell
history that captured the line.

**Residual risk that remains open:** the log predates the containment, so any
shipper/backup that read it before rotation may hold the value; the `664` mode
means any local account could have read it. Neither is verifiable from here.

**Structural preventions added since (these reduce recurrence, they do NOT
remediate the exposed key):**

1. `create_app()` skips `load_dotenv()` in a declared test run (G1.23).
2. The predicate now also honours `SHUNYA_ENVIRONMENT` (G1.24) — the same variable
   the SECRET_KEY guard reads, so the two guards can no longer disagree.
3. `migrations/env.py` applies the same predicate — alembic was a second entry
   point that reloaded `.env`.
4. `app/communication/email_transport_guard.py`: a declared test run refuses to
   boot with Resend enabled, with SMTP credentials to a non-loopback host, or with
   an unrecognised provider.
5. `scripts/test_server.py` forces the non-sending transport unless the sink is on
   loopback.

## INC-1 — Telegram token in history

Unchanged and separate. The value was not opened or tested, and its validity is
**unknown**. Owner action remains BotFather `/revoke` → replace → restart → verify
round-trip. History exposure remains until the repository decision below.

## INC-1b / INC-2 / INC-3 — history, PII, `.env`

Owner decision recorded in G1.24: **Option A first — restrict repository access**;
no history rewrite and no force-push in this milestone. Not executed here
(requires the repository owner's console access). Access restriction stops new
exposure only: existing clones, forks, caches and backups keep the objects, so
historical exposure stays **OPEN** until the owner decides on a purge with a full
coordination and recovery plan.

## Boundaries still in force

```
CREDENTIAL_ROTATION_AUTHORIZED   = NONE
EVIDENCE_DELETION_AUTHORIZED     = NONE
HISTORY_REWRITE_AUTHORIZED       = NONE
REPO_ACCESS_RESTRICTION          = OWNER ACTION (not performed here)
PRODUCTION_MUTATION_AUTHORIZED   = NONE
DEPLOYMENT_AUTHORIZED            = NONE
```
