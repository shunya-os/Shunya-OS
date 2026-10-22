# G1.21 — First-use semantics & placeholder provenance (decision record)

**Status:** evidence gathered; implementation deliberately limited to what existing
constitution already mandates. Two owner decisions remain open (§6).
**Scope:** onboarding-provisioned records, the "first business object" predicate,
Executive Home / first-use CTA, and how AI treats provisioned records.
**Authority:** G1.21 Workstream D. No product policy was invented; no data was
deleted, converted or backfilled.

---

## 1. What is provisioned today (measured)

`POST /api/v1/orgs/onboarding/complete` creates **26** canonical objects through
`ObjectService.create()` (not the "~20" previously recorded):

    Customer, Supplier, Lead, Opportunity, Proposal, Invoice, Payment, Task,
    Meeting, Document, Note, Reminder, Commitment, Product, Service, Project,
    Knowledge, Calendar Event, Relationship, Memory, Email, WhatsApp,
    Conversation, Company, Employee, Quote

Each row is written with:

| Field | Value |
|---|---|
| `object_type` | the snake_case type (`customer`, `invoice`, …) |
| `name` | the display label (`Customer`, `Invoice`, …) |
| `data` | `{"content": ""}` |
| `created_by` | first 12 chars of the canonical identity id |
| `status` | `active` |
| `organization_id` / `workspace_id` | the caller's canonical org + workspace |
| `is_deleted` | `false` |

Verified in `tests/test_g121_onboarding_journey.py`: `objects_created == 26`, the
listing contains exactly those 26 rows, and every one has empty content.

## 2. What provenance is persisted today

| Fact | Persisted? | Where |
|---|---|---|
| Which identity created the row | yes | `sh_objects.created_by` |
| Which org / workspace owns it | yes | `sh_objects.organization_id`, `workspace_id` |
| When | yes | `sh_objects.created_at` |
| **That the row is a provisioned example, not user data** | **no** | — |
| Whether it came from import / manual / AI | **no explicit field** | partially inferable from `created_by` and `data` shape |
| Whether the user has ever edited it | **no** | `updated_at` changes on any write, no edit marker |

There is no `provenance`, `origin`, `source` or `is_example` column on `sh_objects`
(the model is `id, object_id, workspace_id, organization_id, object_type, name,
status, data, created_by, created_at, updated_at, is_deleted, content, space_id`).
`data` is a free-form JSON column that *could* carry a marker, but nothing writes
one and nothing reads one — so a marker added today would be unverifiable for the
26 rows created before it.

## 3. Consequence that is measurable today

`app/objects/first_object_state.py` counts **live rows** across `sh_objects`,
`rel_relationships`, `leads`, `suppliers` — it does not and cannot distinguish a
provisioned placeholder from a user-created record, because no such distinction is
persisted.

Therefore, immediately after onboarding completion:

* `GET /api/v1/objects` → `total: 26`
* `GET /api/v1/objects/first-object-state` → `has_business_data: true`

i.e. **the application reports that the user has business data before the user has
entered a single fact.** This is pinned by
`tests/test_g121_onboarding_journey.py::test_signup_verify_login_org_workspace_questionnaire_resume_and_first_object`
so the semantics cannot drift silently.

## 4. What the existing constitution/implementation already decides

These are not open questions — the code already answers them, and this record
only states them:

1. **Placeholders are canonical domain records, not templates.** They are written
   through `ObjectService.create()` into `sh_objects` with a real
   `organization_id`/`workspace_id`. They are therefore subject to the same
   authorization, tenant isolation, listing and AI-retrieval paths as user data.
   Nothing in the code treats them as a separate class.
2. **They are not onboarding metadata.** No onboarding table references them; the
   only record of the provisioning act is the rows themselves.
3. **Deleting them is not authorized and would be a data mutation.** They are
   ordinary rows with `is_deleted=false`; a mass-conversion or deletion is out of
   scope for this milestone and was not performed.
4. **Idempotency is now enforced** (G1.21): repeated completion creates only the
   missing placeholders, so the set cannot grow to 52/78/… any more.

## 5. Options for first-use semantics (not yet chosen)

| Option | Mechanism | Cost | Risk |
|---|---|---|---|
| **A. Keep as-is, relabel the CTA** | Frontend/UX copy: "your workspace is ready — start with your first customer" instead of "no data yet". No schema change. | Low | The emptiness predicate stays untruthful for AI and reports; the CTA must never claim "empty". |
| **B. Persist provenance, exclude examples from "real data"** | Add nullable `provenance` (`user` / `onboarding_seed` / `import` / `ai`) to `sh_objects`; set it for new seeds; backfill only rows that match the exact seed signature (type + seed name + empty content + `created_by` = identity prefix); `first_object_state` counts `provenance != 'onboarding_seed'`. | Medium (one additive migration + predicate change) | Backfill is inference, not history: rows edited by a user since seeding cannot be distinguished, and a false "user" classification would silently keep them out of the count. |
| **C. Stop seeding placeholders** | Remove the 26-object seed; rely on the questionnaire answers to create real records. | Medium (product change) | Loses the "never-empty workspace" affordance that the questionnaire/Executive Home currently rely on; existing tenants keep their 26 rows (no deletion authorized), so new and old tenants would differ. |

**Recommendation:** **B, with an explicit `provenance` field and no backfill of
edited rows.** It is the only option that makes the predicate truthful for every
consumer (Executive Home, AI retrieval, reports) without deleting data. The
unbackfillable gap is narrow: a placeholder the user has *already* edited
(`updated_at > created_at`) can be treated as user data, which is the safe
direction (over-counting user data is better than hiding it).

## 6. Owner decisions required (smallest set)

1. **D-1 — Which option (§5)?** Recommend B. If A is chosen, the first-use CTA and
   AI prompt context must be specified so no surface claims the workspace is empty.
2. **D-2 — May AI treat provisioned examples as organizational knowledge?**
   Today it can (they are ordinary records and appear in retrieval). Recommendation:
   **no** — examples must be excluded from AI grounding until they have real content,
   otherwise the assistant asserts knowledge the organization never provided.
   This decision is independent of D-1 and is needed before any AI-answer
   certification.

## 7. What G1.21 implemented here

* Repeated onboarding completion no longer duplicates placeholders (verified).
* The onboarding-completion identity bug that silently seeded **zero** objects
  (`objects_created=0`) is fixed and verified — without it the same request either
  seeded nothing or seeded twice, both untruthfully.
* Current first-use semantics are pinned by a test, so any future change is a
  deliberate act rather than drift.
* No schema change, no deletion, no backfill, no conversion of existing rows.

---

## 8. DECISION TAKEN — G1.24 (owner's directive, authoritative)

The owner chose, in the G1.24 master directive:

* **D-1 = Option B** — system-generated placeholders must not count as
  meaningful user business data; provenance is persisted explicitly.
* **D-2 = NO** — provisioned examples must never be presented to AI as verified
  facts about the organization.

This section records the decision and what was implemented against it. Sections
1–7 above are the pre-decision evidence and are preserved unchanged.

### 8.1 What was implemented (code)

| Element | Where |
|---|---|
| Vocabulary + predicates (`user` / `import` / `ai` / `onboarding_seed` / `system` / NULL = unknown) | `app/objects/provenance.py` |
| Persisted column (nullable, no default, no backfill) | `sh_objects.provenance`, migration `r6b38_object_provenance` |
| Origin written at creation; invalid vocabulary rejected | `core/object_service.py::create` |
| Seeds marked as examples | onboarding completion (26 rows), `app/onboard.py`, `app/objects/seed.py` |
| User edit of an example promotes it to `user`; lifecycle-only writes do not | `core/object_service.py::update` |
| First-use predicate excludes examples and reports them separately | `app/objects/first_object_state.py` (`counts.examples`) |
| API exposes `provenance` / `is_example` / `provenance_label` | objects list, detail, create; typed-object detail |
| UI labels (badge + first-use banner) | knowledge browser panel |
| AI grounding excludes examples; a viewed example is labelled `[example]` | `core/intelligence/service.py` |

### 8.2 Answer to the sub-questions in §6

* **Imported / AI-created / draft records** count as business data (the user
  asked for them; only provisioned examples are excluded).
* **Unknown historical provenance** stays NULL and **counts** as business data.
  Nothing is hidden on a guess, and no backfill was performed.
* **Existing users**: an example the user has already edited becomes `user` data
  on the edit; untouched examples stay examples.

### 8.3 What this record does NOT claim

No historical row was converted. A tenant created before G1.24 keeps 26 rows with
NULL provenance, which the predicate counts as business data — the truthful
answer given that their origin cannot be proven from the stored state. An
operator backfill with evidence is possible but was deliberately not written into
the migration.
