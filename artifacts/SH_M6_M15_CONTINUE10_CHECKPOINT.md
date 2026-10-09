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

Final round executed on the **7ada65b deployment** (CI-5, run 37913252096, SUCCESS):

- **Supplier paste-import through the UI**: Import panel → Import as: Suppliers → mapping
  table rendered with supplier fields (Vendor Name → Supplier name, Type → Category,
  Contact Person → Contact person, Email → Email, City → City, Payment Terms → Payment
  terms — each with "known column name" reasons) → row basis "no existing supplier with
  this name — row will create a new supplier" → **"Import Complete — Created: 1"**
  (Final Round Vendors 541200, session 4582741d). Screenshot: M6_FINAL_SUPPLIER_MAPPING.png,
  M6_FINAL_SUPPLIER_CREATED.png. (This exact flow failed with a tenancy FK 400 before the
  migration — the fix is verified through the real UI.)
- **Duplicate re-import through the UI**: preview "1 valid · 0 new · 1 matched", basis
  "supplier name 'Final Round Vendors 541200' already exists as #13" → commit →
  **"Nothing New — Created: 0 — Already existed: 1"** with "Skipped — already exists"
  detail and "Retrying the same file is safe: rows that already exist are skipped, not
  duplicated." Screenshot: M6_FINAL_DUPLICATE_NOOP.png.
- **Ambiguity block**: customer paste with two name-like columns → amber
  "⚠ Needs your decision: 2 columns could serve 'display_name': Name, Guest Name.
  SHUNYA will use 'Name'. If that is wrong, map the columns explicitly before
  importing." with Guest Name marked "not used for 'display_name' — 'Name' was chosen
  (override to change)". Screenshot: M6_FINAL_AMBIGUITY_DECISION.png.
- **Ambiguity RESOLVED by the human**: set Guest Name → Not imported, commit →
  "Import Complete — Created: 1"; provenance of record 239 shows
  field_mapping {display_name: "Name", phone: "Phone"} — the override is canonically
  recorded; Guest Name absent from the mapping.
- **Relationship titles corrected** on the deployed build: "Cert Browser Aarti 36812"
  and "Cert Browser Vikram 36812" render as row titles (no more company/email
  fallback). Screenshot: M6_FINAL_RELATIONSHIP_TITLES.png.
- **Awareness endpoint fixed**: GET /api/v1/awareness now returns a clean 200 payload
  (no error body; verified live from the page after deploy).
- **Attention integration observed**: sidebar accumulated "Needs your attention ·
  N to review" purely from the real ingestion canonical events.

## M6 completion gate — status per requirement

| Requirement | Status | Evidence |
|---|---|---|
| Import a representative customer source | VERIFIED | browser (paste) + HTTP journeys + runtime proof |
| Inspect SHUNYA's interpretation | VERIFIED | live mapping table + preview API |
| Review mappings and ambiguities | VERIFIED | live mapping table + live decision block + preview API + tests |
| Confirm the import | VERIFIED | live commit → created 2 (customer), 1 (supplier), 1 (ambiguity-resolved) |
| Find the resulting canonical customers | VERIFIED | Relationships surface live, titles corrected; runtime C9 |
| Inspect their provenance | VERIFIED | live drawer + provenance API (customer + supplier) |
| Correct an error | VERIFIED | live correction, audited (customer + supplier via runtime S4) |
| Resolve a duplicate or ambiguity | VERIFIED | live "Nothing New" noop + live override resolution with recorded mapping |
| Recover from a deliberately induced failure | VERIFIED | runtime C14 rejected + C15 recovery; unit tests + induced GJ-13 journey |
| Refresh and re-login without losing truth | VERIFIED | live reload + re-login (records + correction persisted) |
| Repeat for suppliers | VERIFIED | live UI import + runtime S1–S5 |
| Tenant isolation + persistence after restart | Runtime X1–X4 (401/404 on other tenant); restart survival pending CI-6 checkpoint deploy | proofs above |

## Post-migration production verification (7ada65b)

- alembic_version = m6_supplier_tenancy_retarget; suppliers tenant FK = → organizations;
  remaining FKs → tenants: 67 (was 68 — suppliers retargeted; recorded for per-stage
  remediation).
- Runtime proof re-run: **25/25 checks passed** (artifacts/M6_RUNTIME_PROOF.txt).
  Restart-survival record IDs for the closing check: customer [236, 237] + browser
  records; supplier [12] + 13.

## Fix carried in this commit

- scripts/verify_m6_ingestion_runtime.py: customer phones are now run-unique (customer
  matching is by email OR phone; fixed phones made the second run match the first run's
  records and — correctly — skip all rows, which failed C6 for the wrong reason). The
  observed product behavior during this investigation was itself correct: a phone-match
  with conflicting fields is skipped with its basis reported, never merged.


