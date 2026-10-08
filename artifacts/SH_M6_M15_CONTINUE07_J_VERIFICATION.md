# J — Historical credential exposure: independent verification (2026-10-08, CONTINUE-07)

Method: hash-only comparisons (sha256 of candidate substrings — values never echoed into any
report or command output). Read-only git history inspection; live-tree greps; runtime probes.

## Historical credential literals found (all removed from tracked files)

| # | Where committed | Target | Removed by | sha256(pwd) prefix |
|---|---|---|---|---|
| 1 | scripts/verify-deployment.sh (`PGPASSWORD=…`) | postgres `shunya@localhost:5432/shunya_os` | 0233254 | 304f69a5… |
| 2 | scripts/{fix_session,seed_demo,seed_organization,validation_test}.py DSNs | `shunya@127.0.0.1:5433/shunya_db` (test cluster) | 0233254 | c8faf2a3… |
| 3 | .github/workflows/ci-cd.yml DATABASE_URL | `shunya@localhost:5432/shunya_os_test` (ephemeral CI db) | ffb7c83 (file deleted a26ed3a) | 238c5440… |
| 4 | docker-compose.yml POSTGRES_PASSWORD (+ same value in prose in 2 audit docs) | compose-provisioned local pg | 7741c42 | fbca9c0d… |

## Validity / rotation decision

- LIVE database credential (password inside the deployment `.env` DATABASE_URL) hash: 3c9eb878…
- NONE of the historical values match the live credential (all four hashes distinct from live, and
  from each other). 0233254's recorded claim ("removed values do NOT match the production
  DATABASE_URL password") is therefore INDEPENDENTLY CONFIRMED.
- Password auth IS enforced on localhost (probe: `psql -w` → "fe_sendauth: no password supplied"),
  so "still valid" is a real question — and the answer is: the historical values do not
  authenticate the only live postgres (role `shunya`, one-password model; the app authenticates
  with the .env credential, prod healthy).
- The 5433 test cluster no longer exists (only 16/main on 5432). Postgres listens on loopback only
  (127.0.0.1 + ::1). No other database hosts appear anywhere in the repo's infrastructure.
- Current tracked tree: zero occurrences of the historical values or credential shapes
  (guard test + manual grep over tracked and untracked trees).
- Residual exposure: the values remain readable in public git history and possibly in old GitHub
  Actions logs — un-publishable (byte committed to a public repo). They are POWERLESS, which is the
  mitigation. Post-sweep-2, the guard also covers unquoted YAML assignments and prose disclosures.

## Decision
- ROTATION NOT REQUIRED by this exposure (nothing live accepts the values). No blind rotation.
- No founder approval needed (no rotation performed). If the founder wants defense-in-depth, the
  local `shunya` role password can be rotated at leisure — unrelated to this exposure.
- Standalone remediation complete; recorded as RUNTIME-VERIFIED at the "not valid anywhere live"
  level. Do NOT describe this as "credential rotation done" — it is "rotation not required,
  evidenced".
