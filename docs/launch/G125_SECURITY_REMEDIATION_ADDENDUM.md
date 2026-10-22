# G1.25 — Security Incident Remediation Addendum

**Status:** evidence recorded; **no credential, evidence file, repository setting or
production system was changed**. Every action below is either (a) executable by the
owner in minutes, or (b) explicitly blocked on an authorization this milestone does
not hold.

Boundaries in force for this document:

```
CREDENTIAL_ROTATION_AUTHORIZED   = NONE
EVIDENCE_DELETION_AUTHORIZED     = NONE
HISTORY_REWRITE_AUTHORIZED       = NONE
PRODUCTION_MUTATION_AUTHORIZED   = NONE
DEPLOYMENT_AUTHORIZED            = NONE
```

No secret value was read, printed, copied, hashed for publication, tested,
transmitted or deleted while producing this addendum. All statements about log
contents are **counts and shapes only**; all statements about the repository are
metadata returned by `gh` / `git`.

---

## 0. What G1.25 established that was not previously recorded

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| 1 | **A second unredacted suite log exists** — `~/.hermes/cache/scratch/g123/f_fullsuite.log` (created 2026-10-22 00:35, i.e. after the G1.22 incident was recorded) contains **1** key-shaped token (`re_[A-Za-z0-9_-]{20,}`) | `grep -oE … \| wc -l` on the file | The G1.24 record names a single original log. The incident scope is **larger**: two unredacted copies, created in two different milestones. Neither was produced in G1.25. |
| 2 | The G1.22 original log holds **3 occurrences / 2 distinct** key-shaped tokens | same method on `g122/f_fullsuite.log` | Consistent with the recorded "3 occurrences"; the second distinct token means at least one non-key `re_…` identifier also matches. Not resolved to identity without reading values (not authorized). |
| 3 | **Directory and file permissions are wider than intended** — `…/scratch/g122` and `…/scratch/g123` are `0775`; the logs are `0664`, owner `shunya-deploy:shunya-deploy` | `ls -ld`, `ls -l` | Any local account in the group can read them. Parent `…/scratch` is `0700`, so exposure is limited to this host's group members — not remote. |
| 4 | **The repository is currently PUBLIC** — `shunya-os/Shunya-OS`, `visibility=PUBLIC`, `isPrivate=false` | `gh repo view --json nameWithOwner,visibility,isPrivate` | The owner's chosen containment (Option A: restrict access) **has not been executed**. Historical PII, the Telegram token and `.env` blobs remain readable by anyone with the URL. |
| 5 | `data/telegram_bot_token.txt` existed in exactly **2 commits** and is absent at HEAD | `git log --all --oneline -- data/telegram_bot_token.txt \| wc -l` → 2; `git ls-tree -r HEAD` → 0 | Matches the recorded first-commit / removal-commit pair. Value not read. |
| 6 | `~/.env` recorded in the G1.22 plan **does not exist**; the live file is `<repo>/.env`, mode `0600` | `ls -l` | The plan's host-file reference is stale — corrected here. Mode is already correct. |
| 7 | **GitHub secret scanning reports an OPEN alert** for `telegram_bot_token` (alert #1, created 2026-07-31, `resolution=null`) | `gh api repos/shunya-os/Shunya-OS/secret-scanning/alerts` (metadata fields only; the value field was never selected) | Platform-side confirmation that the token is still detectable in the repository. It does **not** establish that the credential is live — validity checks are disabled at the repository level. |
| 8 | Repository security settings: `secret_scanning=enabled`, `secret_scanning_push_protection=enabled`, `non_provider_patterns=disabled`, `validity_checks=disabled`, `dependabot_security_updates=disabled` | `gh api repos/shunya-os/Shunya-OS --jq .security_and_analysis` | Push protection is genuinely on (the G1.22 plan noted this was not re-verified). Validity checks and custom patterns are off, so GitHub will neither test whether a leaked credential works nor catch project-specific secret shapes. |

Nothing above changes the classification of INC-1/1b/2/3/5. It changes their
**scope** and the owner's checklist.

---

## 1. INC-5 — Resend API key in a local log

### 1.1 State

| Item | State at G1.25 exit |
|---|---|
| Credential | **Treated as live and exposed** until the owner rotates it. Validity not tested (no provider call authorized). |
| Unredacted copies | **2** — `scratch/g122/f_fullsuite.log`, `scratch/g123/f_fullsuite.log` |
| Redacted review copy | `scratch/g122/f_fullsuite.redacted.log` — retained; not a replacement for rotation |
| Permissions | `0664` files inside `0775` directories |
| Deletion | Not performed (`EVIDENCE_DELETION_AUTHORIZED = NONE`) |

### 1.2 Owner sequence (exact, in order)

1. **Revoke** the key in the Resend dashboard (API Keys → revoke). Record the
   revocation timestamp in the incident record.
2. **Create a narrowly scoped replacement** — sending permission only; no
   account-administration scope; label it with the environment and date.
3. **Update the production secret store** through the approved operational
   process (not by editing a tracked file, not by pasting into a shell that writes
   history).
4. **Reload the mail worker / service** through the approved deployment procedure.
5. **Verify functionality without disclosure** — trigger one transactional message
   to an owner-controlled address and confirm the provider reports acceptance;
   never echo the key, the request headers, or the provider response body into a
   terminal that logs.
6. **Verify the old credential is unusable** using provider-side evidence (the
   revoked key must fail an authenticated call). Do not paste the old value into
   any command; if provider evidence is unavailable, record the incident as
   *rotated, revocation unverified* rather than closed.
7. **Restrict and review the copies** (after step 1, so the values are inert):
   - `chmod 700` the two `g122` / `g123` scratch directories and `chmod 600` the
     logs (command prepared, **not executed** here);
   - review log shippers, backups, snapshotting, and shell history on this host
     for the same line;
   - confirm no copy was pushed, committed or transmitted — verified so far:
     both paths are inside the gitignored `.hermes/cache/` tree and are absent
     from `git status`.
8. **Dispose of the originals only under the retention procedure**, keeping the
   redacted copy. Disposal and redaction are separate decisions; a redacted copy
   does not authorize deleting the original evidence.

### 1.3 Prepared (not executed) restriction commands

```bash
chmod 700 /home/shunya-deploy/.hermes/cache/scratch/g122
chmod 700 /home/shunya-deploy/.hermes/cache/scratch/g123
chmod 600 /home/shunya-deploy/.hermes/cache/scratch/g122/f_fullsuite.log
chmod 600 /home/shunya-deploy/.hermes/cache/scratch/g123/f_fullsuite.log
```

These are an access restriction on evidence, not a deletion. They are not
executed here because evidence handling is gated by the incident procedure and
this milestone holds no authorization for it.

### 1.4 Residual risk that rotation does not remove

- The line was written **before** the G1.23 containment, so any backup, snapshot
  or shipper that read that file may hold the value.
- A `0664` file was readable by group members for at least the window between
  the two runs; whether any other account read it is not knowable from here.
- The `g123` copy proves the containment that G1.23 added did **not** cover every
  harness that booted the app in that window; the structural guards added since
  (factory `load_dotenv` skip, transport guard, test-server scrub) reduce
  recurrence but do not remediate this occurrence.

---

## 2. INC-1 — Telegram bot token in Git history

### 2.1 State

| Item | State |
|---|---|
| Present at HEAD | No (0 tracked paths) |
| Historical commits | 2 (first commit + removal commit) |
| Validity | **UNKNOWN** — no Bot API call was made, no value was read |
| Downstream dependencies | `TELEGRAM_BOT_TOKEN` environment variable; `app/services.py` falls back to `data/telegram_bot_token.txt` (absent); inbound webhook `POST /telegram/webhook` (public, no secret-token check); outbound only via `app/shunya/executor.py` |

### 2.2 Owner sequence

1. In BotFather: `/mybots` → the bot → **API Token → Revoke current token**.
2. Set the new token in the production environment through the approved process;
   restart the bot/webhook consumer.
3. **Verify without revealing the token**: send one message to the bot from an
   owner-controlled chat and confirm the inbound webhook records a lead for the
   expected organization (the route returns 200 and logs an activity). Optionally
   confirm `getMe` succeeds from the service layer — the response must be logged
   as status only, never with the token or URL.
4. Record: rotated at `<timestamp>`, inbound verified `<yes/no>`, outbound
   verified `<yes/no>`.
5. **Do not** treat rotation as removing the history exposure (see INC-1b).

### 2.3 Code observations relevant to the owner (not changed in G1.25)

- `POST /telegram/webhook` is registered as a **public** route and validates no
  `X-Telegram-Bot-Api-Secret-Token`; anyone who knows the URL can inject a lead
  into an organization resolved from the payload. This is a launch-relevant
  security gap independent of the token incident.
- The webhook **returns** a `sendMessage` object in the HTTP body; the Bot API does
  not act on that, so inbound messages are not actually answered. Recorded as a
  capability gap, not a security defect.

---

## 3. INC-1b / INC-2 / INC-3 — historical token, PII and `.env` in published history

### 3.1 Verified current state

| Check | Result |
|---|---|
| Repository visibility | **PUBLIC** (verified this milestone) |
| Owner's chosen option | A — restrict repository access first (recorded in G1.24) |
| Executed? | **No** |
| History rewrite | None performed; no force-push |

### 3.2 Owner action (repository owner only)

1. GitHub → repository → **Settings → General → Danger Zone → Change visibility →
   Make private**. Confirm the read-back shows `visibility=PRIVATE`.
2. Record the change time and the reason in the incident record.
3. Re-run the verification: `gh repo view --json visibility` must report
   `PRIVATE`; an unauthenticated `git clone` must fail.
4. Decide, separately, whether a purge is required (compliance or contractual).
   That decision needs its own pre-flight: `git bundle` of all refs, checksum
   manifest of the paths to remove, list of known forks/clones to notify, and an
   explicit acceptance of broken clones.

### 3.3 Limitations of access restriction (must be stated in the closure record)

- Existing clones, forks, CI caches, mirrors and backups keep the objects.
- GitHub-side cached views of already-public blobs are not guaranteed to be gone.
- Secret scanning alerts already raised remain in history.
- Access restriction therefore **reduces new exposure only**; the historical
  exposure stays OPEN until a purge is decided and executed.

---

## 4. What this milestone did NOT do

- No key or token was opened, printed, copied, tested, rotated or transmitted.
- No log, database, lock file or artifact was deleted or moved.
- No repository setting, visibility or access policy was changed.
- No history rewrite, force-push, object purge or branch operation was performed.
- No production service was restarted and no production secret store was touched.
