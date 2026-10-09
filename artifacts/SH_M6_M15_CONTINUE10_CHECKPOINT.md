# SH-M6→M15 CONTINUE-10 CHECKPOINT — M6 SEMANTIC INGESTION (Stage A)

Date: 2026-10-09 (session CONTINUE-10)
Campaign: SH-M6→M15 master directive — one continuous programme
Starting truth: HEAD/origin/production 62e4797 (reconciled live, matched the report)

## Delivery chain for this block (exact SHAs)

| SHA | Content | CI run | Result |
|-----|---------|--------|--------|
| e063908 | M6 semantic ingestion backend + 28 tests + journeys GJ-05/06/13 | (folded into 8993e4a's run 37904031672 — cancelled by supersession) | — |
| 8993e4a | M6 explainable import panel (frontend) | 37904031672 | CANCELLED (superseded by later push before deploy) |
| 0837926 | finance removed-model fixes (2 live 500s) + B3 ledger creation UI + 10 tests | folded into 6b68d92's run | — |
| 6b68d92 | M6 runtime proof script | 37905342098 | **SUCCESS** (test 19m53s + deploy 1m44s) — DEPLOYED |
| a5f931e | suppliers tenancy FK retarget migration + script fixes | 37908938873 | CANCELLED (superseded) — never deployed |
| c60403e | browser-journey defects: relationship title field + awareness shadowing + tests | 37909902938 | test PASSED; deploy REFUSED by pre-flight: untracked evidence files in the deploy tree ("no work destroyed", production untouched) — resolved by committing them (this file) |

## Production truth

- Production currently runs **6b68d92** (CI_CERTIFIED, DB connected, frontend match — verified live via /health).
- c60403e (carrying a5f931e's migration) deploys when run 37909902938 passes.

## What M6 delivered (Stage A of the master directive)

Extended the canonical import pipeline (app/import_export) — no competing importer:

- INSPECT/UNDERSTAND: per-column mapping explanation (target, method, confidence, reason) for every column; alias registry extended for realistic names (Client Name, Guest, Party Name, Vendor Name, DMC, operator...).
- AMBIGUITY: multiple-candidates (chosen column stated, alternatives marked conflicted and NOT applied), unmapped name/email/phone-like columns surfaced, conflicting in-file duplicates rejected with pointers. Human decisions via column_overrides honored by preview AND commit.
- IDENTIFY: match bases explained; similar-but-not-equal supplier names surfaced (difflib ≥0.82) and never merged.
- PREVIEW/CONFIRM: preview writes nothing; commit is the confirmed persistence step.
- PERSISTENCE: customers → CanonicalRelationship (type=customer); suppliers → Supplier (tenant=org).
- PROVENANCE: every record carries source file, row, import session, effective mapping, author, timestamp; GET /api/v1/data/provenance/<type>/<id>; UI drawer "Where did this come from?".
- CORRECTION: POST /api/v1/data/import/correct — auditable (who/old/new/when/why), relationship timeline entry, cross-tenant 404.
- RECOVERY: re-commit idempotent (noop + skipped bases), partial truthful, induced failures truthful, retry never duplicates.
- OBSERVABLE: ingestion:import canonical event per batch (feeds the M9 attention chain — observed live: sidebar attention pulse reacted to imports).

## Defects found by running the real product (each fixed, each with evidence)

1. **Suppliers unusable in production (blocking)** — `fk_suppliers_tenant_id_tenants`
   (legacy) vs org ids written by every current path: cert-org supplier import → 400
   `ForeignKeyViolation: Key (tenant_id)=(278) is not present in table "tenants"`.
   Suppliers table was empty in production. Fixed by guarded migration
   `m6_supplier_tenancy_retarget` (drop stale FK → create FK to organizations(id),
   data probe, skip-with-warning otherwise). Pre-verified by a transactional dry-run
   against production (DDL executed + rolled back; production confirmed untouched).
   Systemic finding: **68 FKs still reference the legacy tenants table** (memory_records,
   human_context_items, campaigns, communication external_*, invitation_tokens, ...) —
   recorded for per-stage remediation; each active subsystem must be verified on the
   real stack (SQLite tests cannot see this class).
2. **Relationships workspace titles degraded** — frontend read `rel.name`; the API
   returns `display_name`, so every row title silently fell back to company/email
   (observed: 'Cert Browser Aarti 36812' rendered as 'Shunya Travel Desk'). Fixed +
   type updated.
3. **GET /api/v1/awareness broken (200-with-error)** — `now = now().isoformat()`
   shadowed the imported function → UnboundLocalError swallowed by the broad except;
   the presence meter's signal source was permanently empty while looking healthy.
   Fixed; regression tests in tests/test_m6_closure_fixes.py.
4. **Finance direct invoice path 500'd** — `from app.models import Relationship`
   (removed model) in two routes + dormant document-enrichment crash; fixed to
   CanonicalRelationship / guarded skip-and-report.

## Local verification at exact HEAD (c60403e)

- 117/117 targeted: M6 semantic (30), B3 ledger (10), journeys GJ-05/GJ-06/GJ-13,
  import/ingestion suites, document intelligence; governance/mock-audit 42 pass.
- Frontend: tsc clean; eslint governance 460→450; production build OK.
  (vitest: onboarding-url-truth fails identically on pristine HEAD under local
  Node 26 — CI pins Node 22 where it is green; environment-specific, evidenced.)

## Runtime proof (deployed build)

- Run against 6b68d92 over HTTPS (cert tenant org 278): **20/23** — the 3 failures
  were each diagnosed: C9 (proof-script query not a contiguous substring — script
  fixed), S2 (tenancy FK — migration written), S5 (consequent of S2).
- Re-run against the c60403e deployment is the closing evidence (below).

## Browser journey evidence (real product, cert tenant, HTTPS)

Walked on the deployed 6b68d92 build (screenshots archived under artifacts/):

- Sign-in via vaulted certification login → authenticated workspace.
- "Bring your business into SHUNYA" continuation → Import panel → Paste CSV →
  Customers → preview: **"How SHUNYA reads your columns"** table rendered live with
  per-column SHUNYA interpretation + reasons (Client Name → Customer name (known
  column name), Mobile → Phone, Email → Email, Company → Company, City → City);
  per-row match basis ("no existing customer with this email/phone — row will create
  a new customer").
- Commit → "Import Complete — Created: 2 — Import session c9b31518" with per-record
  "Where did this come from?" buttons.
- Provenance drawer: origin row 1, timestamp, "Mapping used: City → City, Company →
  Company, Client Name → Customer name, Email → Email, Mobile → Phone", session id,
  reader identity.
- Correction via the drawer: city "Jaipur" → "Jaipur City" with reason — persisted,
  attributed (sid_a3cd655b...), visible under Corrections in the trail.
- "Open Relationships" → both records found (title degradation defect observed here,
  fixed in c60403e).
- Refresh (hard reload) → splash → re-login → **records and the correction persist**
  (verified via API from the page: 2 relationships, correction "city: Jaipur ->
  Jaipur City", record city "Jaipur City", origin "pasted content").
- Sidebar attention pulse reacted to the ingestion events ("Needs your attention ·
  3 to review"); Home section (canonical AttentionItems) correctly showed none —
  the two meters use different sources (attention items vs awareness observations);
  the awareness source was found broken (defect #3) and fixed.

Pending on the c60403e deployment (final round): supplier paste-import through the
UI (unblocked by the tenancy migration), ambiguity block ("Needs your decision")
rendered live, duplicate re-import → "Nothing New" state, corrected relationship
titles, awareness endpoint live payload.

## M6 completion gate — status per requirement

| Requirement | Status | Evidence |
|---|---|---|
| Import a representative customer source | VERIFIED | browser (paste) + HTTP journeys + runtime proof |
| Inspect SHUNYA's interpretation | VERIFIED | live mapping table + preview API |
| Review mappings and ambiguities | VERIFIED (ambiguity block pending final round screenshot) | API + tests + live table |
| Confirm the import | VERIFIED | live commit → created 2 |
| Find the resulting canonical customers | VERIFIED | Relationships surface live; title fix pending deploy verification |
| Inspect their provenance | VERIFIED | live drawer + provenance API |
| Correct an error | VERIFIED | live correction, audited |
| Resolve a duplicate or ambiguity | API-VERIFIED (noop + conflicts); browser noop pending final round | tests + runtime proof |
| Recover from a deliberately induced failure | API-VERIFIED; browser pending final round | tests + runtime proof |
| Refresh and re-login without losing truth | VERIFIED | live reload + re-login |
| Repeat for suppliers | PENDING c60403e deploy (migration) | — |
| Tenant isolation + persistence after restart | Runtime X3/X4 verified; restart-survival rides the checkpoint deploy | proofs below |


