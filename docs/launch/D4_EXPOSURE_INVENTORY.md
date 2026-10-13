# D4 — Historical Sensitive-Data Exposure Inventory (2026-10-13)

Status: INVENTORY COMPLETE + REVERSIBLE CONTAINMENT APPLIED.
No history rewrite, no force-push, no repository-visibility change, and no
data purge were performed — those are founder-authorized steps only (see
Section 3).

## 1. Inventory (read-only, presence/pattern checks — no secret values printed)

| Path in history | First seen | Last change | Exposure | Live credential? |
|---|---|---|---|---|
| `.env` | a1700b8 / initial-era (7 commits) | placeholder era | every API-key line + DATABASE_URL in all 7 historical blobs checked: **all placeholder/empty** (values ≤8 chars or `your_key_here`) | NO — production values never committed |
| `data/telegram_bot_token.txt` | **4fe3f99 (initial commit)** | 5e1fcf2 removed from tree ("remove sensitive token file") | blob pattern-matches a real Telegram bot token (`\d{6,10}:[A-Za-z0-9_-]{30,40}`) — 1 line, 46 chars | **YES — REAL TOKEN in public history** |
| `uploads/**` (3 founder itinerary PDFs, SHUNYAOS_FULL_AUDIT_2026.pdf, 11 test files) | initial-era commits (7 history commits) | 9eb71b4 (L4 index-untrack) | founder PII in public history | n/a (PII, not a secret) |
| `app/communication/credentials.py` | history | history | 0 real-looking assignments across all blobs | NO |
| `.env` at HEAD | — | — | **untracked** (only `.env.example` templates tracked) | NO |

## 2. Reversible containment applied (no history mutation)

- GitHub **secret scanning: ENABLED** (repo API, read-back verified).
- GitHub **secret scanning push protection: ENABLED** (blocks future pushes
  of matching secret patterns before they land; read-back verified).
- `.gitignore` already excludes `.env`, `.env.audit`, `uploads/` (any level),
  `static/uploads/`, `data/telegram_bot_token.txt` (added in 5e1fcf2).
- Production host `.env` perms 0600; HEALTH_TOKEN added 2026-10-13.

## 3. Founder-authorized next steps (NOT executed — require explicit sign-off)

| # | Action | Reversibility | Steps |
|---|---|---|---|
| F-1 | **Rotate the Telegram bot token** (history contains a real token) | Rotation is reversible-by-recreation | BotFather `/revoke` → generate new token → set `TELEGRAM_BOT_TOKEN` env → verify bot works → delete the old token key |
| F-2 | **Purge PII + token from history** (filter-repo or GitHub support purge) or **make the repo private** | History purge is irreversible; repo privacy is reversible | (a) `git-filter-repo` path-based removal + force-push (founder must accept force-push), or (b) `repos/shunya-os/Shunya-OS` → Settings → visibility: private. Recommend (a)+(b) per register §7-D4 |
| F-3 | Rotate any key if secret scanning flags an alert later | Rotation | follow the atomic rotation protocol (enterprise-security skill) |

## 4. Retention obligations

- No legal retention requirement forces keeping keys/PII in repo history.
- PII itineraries exist as originals on the production host
  (`/home/shunya-deploy/backups/legacy_repo_uploads_20261013/`, sha256-verified
  against the untracked originals) — a purge from history does NOT destroy
  the user's own files.
- Audit PDF is founder-owned internal material; purge decision is the
  founder's.

## 5. Verification commands (reproducibility)

```bash
git log --all --oneline -- .env                          # 7 placeholder commits
git show 4fe3f99:data/telegram_bot_token.txt | grep -cE '^[0-9]{6,10}:[A-Za-z0-9_-]{30,40}$'  # 1 (real token shape)
git ls-files | grep -E '(^|/)\.env'                      # .env.example only
gh api repos/shunya-os/Shunya-OS --jq '.security_and_analysis.secret_scanning.status'  # enabled