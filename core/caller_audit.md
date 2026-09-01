# Canonical Object Migration Audit — All Production Callers

## Audit Scope
- **FounderObject** (table: `founder_objects`): legacy founder journey / AI consumer
- **ShunyaObject** (table: `sh_objects`): legacy workspace / reality engine consumer
- **UOPObject** (table: `sh_uop_objects`): canonical kernel protocol (the target)
- **Target**: `core/object_service.py` → `ObjectService.create()` writes into `sh_objects`

---

## 1. `app/founder/routes.py` — `api_create_object()`

| Field | Value |
|---|---|
| **What it creates** | `FounderObject` (via dual-write: pipeline first, then `FounderObject(...)` row) |
| **Model used** | `FounderObject` |
| **Organization ID** | `None` — no org_id passed to object |
| **Can migrate?** | ✅ Partial — the route already delegates to `create_object()` in `os_adapter.py` (pipeline). The dual-write `FounderObject(...)` at line 438 is the legacy mirror. |
| **Migration plan** | Remove the dual-write `FounderObject(...)` block (lines 434–448). The pipeline via `core/object_service.py` already handles creation. Requires the pipeline's `create_object` intent to write through `ObjectService` (which writes to `sh_objects`) instead of going directly to `FounderObject`. Set `organization_id` on object from `session['current_org_id']` (available at line 423 context). |

## 2. `app/founder/routes.py` — `api_create_space()`

| Field | Value |
|---|---|
| **What it creates** | `FounderSpace` (not an object — a space model) |
| **Model used** | `FounderSpace` |
| **Organization ID** | `None` on space (organization_id is nullable on the model) |
| **Can migrate?** | ❌ Not applicable — this is a Space, not an Object. Separate migration needed for Spaces. |
| **Migration plan** | N/A for object audit. Space creation via `create_space()` in `os_adapter.py` already exists. |

## 3. `app/production/objects.py` — `_create_typed_object_raw()` (via `create_typed_object` route)

| Field | Value |
|---|---|
| **What it creates** | `FounderObject` with object_id like `obj_<uuid>` |
| **Model used** | `FounderObject` |
| **Organization ID** | `None` — uses `identity_id` only |
| **Can migrate?** | ✅ Yes — this is the SPA create-object-modal. Switch from `FounderObject(...)` to `ObjectService.create()`. |
| **Migration plan** | Replace `FounderObject(...)` instantiation (lines 161–170) with `ObjectService().create(object_type=..., name=..., organization_id=resolved_org, data=parsed_fields)`. Resolve `organization_id` from session or FounderSpace's linked org. Remove the auto-space-creation fallback (lines 147–158) — space should exist already. Keep event emission (advisory). |

## 4. `app/production/objects.py` — `update_typed_object()`

| Field | Value |
|---|---|
| **What it does** | Updates `FounderObject.content` by parsing/merging field dict |
| **Model used** | `FounderObject` |
| **Organization ID** | Not enforced |
| **Can migrate?** | ✅ Yes — migrate to `ObjectService.update()` |
| **Migration plan** | Replace `FounderObject.query.filter_by(object_id=...).first()` + `obj.content = ...` with `ObjectService().update(obj_id, organization_id, data=merged_fields)`. Need to resolve the sh_objects `id` from `object_id` (the canonical service uses integer ID, but the UI knows `object_id` string). Add a `get_by_object_id()` helper or use `obj = ShunyaObject.query.filter_by(object_id=object_id).first()` then pass `obj.id` to `ObjectService.update()`. |

## 5. `app/automation/service.py` — `_execute_action()` → `create_object` action

| Field | Value |
|---|---|
| **What it creates** | `FounderObject` with object_id like `auto_<uuid>` |
| **Model used** | `FounderObject` |
| **Organization ID** | `None` — resolves space via identity_id, no org on object |
| **Can migrate?** | ✅ Yes — this is an automated "create_object" action fired by rules |
| **Migration plan** | Replace `FounderObject(...)` (lines 248–256) with `ObjectService().create()`. Resolve `organization_id` from either the context or from the space's associated org. Set `created_by=rule.identity_id`. This is automated, so no session — need to resolve org via `FounderSpace` → `organization_id`. |

## 6. `app/ai/routes.py` — `chat()` (conversation persistence)

| Field | Value |
|---|---|
| **What it creates** | `FounderObject` + `FounderSpace(system_space)` + `FounderConversation` |
| **Model used** | `FounderObject` (line 328), `FounderSpace` (line 320) |
| **Organization ID** | Not set — space is "space_system", identity_id used |
| **Can migrate?** | ⚠️ Partial — the FounderObject is a "conversation" type tracking FK reference. The canonical store doesn't currently support conversation-type objects with FK semantics. The FounderConversation/FounderMessage models are separate from the object model. |
| **Migration plan** | The `FounderObject` at line 328 is a FK target for `FounderConversation.object_id`. This is a relationship artifact, not a business object. Keep this pattern until conversations are migrated to a canonical conversation store. For the FK-object specifically: could use `ObjectService.create(object_type="conversation", ...)` with an appropriate org. The system space fallback should be eliminated — conversations should reference real spaces. |

## 7. `app/onboard.py` — `onboard()`

| Field | Value |
|---|---|
| **What it creates** | `FounderSpace` + multiple `FounderObject` (company overview, projects, leads) |
| **Model used** | `FounderObject` (up to 4 objects depending on business type) |
| **Organization ID** | Not set on objects — org is looked up via `OrgMember` but not placed on objects |
| **Can migrate?** | ✅ Yes — this is initial onboarding seeding |
| **Migration plan** | Replace `FounderObject(...)` at line 81 with `ObjectService().create(object_type=..., name=..., organization_id=org.id, data={"content": content})`. Resolve `organization_id` from the already-known `member.organization_id`. The pipeline already runs within `app.app_context()`. Remove the `FounderSpace` creation dependency for objects — objects reference org, not space, in canonical model. |

## 8. `app/objects/upload.py` — `api_upload()`

| Field | Value |
|---|---|
| **What it creates** | `ShunyaObject` (legacy model, type "document") |
| **Model used** | `ShunyaObject` (not FounderObject) |
| **Organization ID** | Not set — uses `workspace_id` |
| **Can migrate?** | ✅ Yes — this is a file upload endpoint creating document objects |
| **Migration plan** | Replace `ShunyaObject(...)` (lines 103–118) with `ObjectService().create(object_type="document", name=..., organization_id=..., data={...})`. Need to resolve `workspace_id` → `organization_id` mapping. Or add `organization_id` to the upload endpoint headers/session. Keep file storage logic (lines 90–96) unchanged — only the DB model changes. |

## 9. `app/objects/seed.py` — `_create_objects()` / `seed_workspace()`

| Field | Value |
|---|---|
| **What it creates** | Multiple `ShunyaObject` (customers, contacts, invoices, proposals, tasks, notes) |
| **Model used** | `ShunyaObject` — seeded with business data |
| **Organization ID** | Not set — uses `workspace_id` |
| **Can migrate?** | ✅ Yes — seed data should go through canonical path |
| **Migration plan** | Replace `ShunyaObject(...)` in `_create_objects()` (lines 116–126) with `ObjectService().create()`. Resolve `organization_id` from the workspace→org relationship. Each object's `data` dict becomes the canonical `data` parameter. The `name` is already extracted. Workspace filtering/skip check (line 147) can stay as an optimization. |

## 10. `app/objects/canonical.py` — `create_canonical_object()`

| Field | Value |
|---|---|
| **What it creates** | Triple-write: `UOPObject` + `ShunyaObject` + `FounderObject` |
| **Model used** | All three — this IS the migration bridge function |
| **Organization ID** | `tenant_id` on UOPObject; not set on ShunyaObject/FounderObject |
| **Can migrate?** | ✅ Already on the canonical path — this IS the migration. However, it should stop dual-writing to ShunyaObject (workspace compat) and FounderObject (founder compat) once consumers are migrated. |
| **Migration plan** | **Step 1**: Keep triple-write but flip consumers to read from `UOPObject` (already happens — `get_canonical_object()` reads UOP first). **Step 2**: Remove the `ShunyaObject` write (lines 179–192) after workspace consumers migrate to `UOPObject`. **Step 3**: Remove the `FounderObject` write (lines 195–207) after founder consumers migrate. **Step 4**: The function becomes a thin wrapper around `ObjectService.create()`. Set `tenant_id` as `organization_id`. The `ObjectService` already writes to `sh_objects` — note this is the SAME table as ShunyaObject's `__tablename__`. When step 2 is done, the `ObjectService` becomes the only write path to `sh_objects`. |

## 11. `scripts/seed_demo.py` — Phase 1 seed

| Field | Value |
|---|---|
| **What it creates** | `FounderSpace` + 150+ `FounderObject` (customers, suppliers, invoices, relationships, commitments, notes, conversations across 3 orgs) |
| **Model used** | `FounderObject` |
| **Organization ID** | Space has it; objects do not |
| **Can migrate?** | ✅ Yes — in a script context, import and use `ObjectService` |
| **Migration plan** | Replace `FounderObject(...)` (lines 494–499) with `ObjectService().create()`. Reorganize flow: create spaces first, then for each data item call service. The `content=json.dumps(item)` pattern becomes `data=item`. Need space_id→org_id mapping. |

## 12. `scripts/seed_demo_m4.py` — M4 demo seed

| Field | Value |
|---|---|
| **What it creates** | `FounderObject` + `FounderSpace` + `FounderConversation` + `BusinessRelationship` |
| **Model used** | `FounderObject` |
| **Organization ID** | Not set |
| **Can migrate?** | ✅ Yes |
| **Migration plan** | Same as scripts/seed_demo.py — replace with `ObjectService().create()`. |

## 13. `scripts/seed_panchi_club_demo.py` — Panchi Club 2.0 Demo Seed

| Field | Value |
|---|---|
| **What it creates** | `FounderObject` (via raw SQL `INSERT INTO founder_objects`) |
| **Model used** | `founder_objects` table (raw psycopg2, not SQLAlchemy) |
| **Organization ID** | Not set on objects; `tenant_id=89` used for related tables (leads, commitments) |
| **Can migrate?** | ✅ Yes — the raw SQL INSERT should use `ObjectService` or the canonical table path |
| **Migration plan** | Replace `insert_founder_object()` function (lines 58–77) with calls to `ObjectService().create()`. The unique `object_id` constraint prevents duplicates — migrate to `ON CONFLICT (object_id) DO NOTHING` on `sh_objects`. This script bypasses the Flask app entirely (raw psycopg2) — would need to integrate with the app context. Alternative: add a bulk loader to `ObjectService`. |

## 14. `scripts/seed_conversations.py` — Demo conversation seed

| Field | Value |
|---|---|
| **What it creates** | `FounderObject` (one FK target for conversation), `FounderConversation`, `FounderMessage` |
| **Model used** | `FounderObject` (line 35 lookup/creation pattern) |
| **Organization ID** | Not set |
| **Can migrate?** | ⚠️ Partial — the FK-object is a conversation attachment target. Same caveat as `app/ai/routes.py`. |
| **Migration plan** | If the conversation FK-object is needed, use `ObjectService().create(object_type="conversation", ...)`. The conversation/message models are separate and need their own migration. |

## 15. `app/production/identity/onboarding_routes.py` — `mark_onboarding_complete()`

| Field | Value |
|---|---|
| **What it creates** | 26 `FounderObject` rows (foundational business objects: Customer, Supplier, Lead, etc.) |
| **Model used** | `FounderObject` |
| **Organization ID** | Not set — uses `identity_id` and `space_id`, but has access to `g.user` for org context |
| **Can migrate?** | ✅ Yes — this is onboarding completion seeding |
| **Migration plan** | Replace `FounderObject(...)` at lines 134–143 with `ObjectService().create()`. Resolve `organization_id` from `FounderSpace.query.filter_by(identity_id=identity_id).first()` → space's `organization_id` (if populated) or from the user's `OrgMember` record. Use `session.get('current_org_id')` or query `OrgMember` table. Each of the 26 rows gets its own `ObjectService().create()` call. |

---

## Summary Table

| # | Caller | Model | Object Type(s) | Org ID Present? | Can Migrate? | Difficulty |
|---|--------|-------|----------------|-----------------|--------------|------------|
| 1 | `app/founder/routes.py` — `api_create_object` | FounderObject | Document (dynamic) | ❌ | ✅ Partial — already pipeline | Easy |
| 2 | `app/founder/routes.py` — `api_create_space` | FounderSpace | Space (not object) | ❌ | ❌ Not applicable | Separate |
| 3 | `app/production/objects.py` — `_create_typed_object_raw` | FounderObject | customer, supplier, lead, invoice, task, etc. | ❌ | ✅ | Easy |
| 4 | `app/production/objects.py` — `update_typed_object` | FounderObject | customer, supplier, etc. | ❌ | ✅ | Medium |
| 5 | `app/automation/service.py` — auto-create | FounderObject | Task (dynamic) | ❌ | ✅ | Medium |
| 6 | `app/ai/routes.py` — chat persistence | FounderObject + FounderSpace | conversation | ❌ | ⚠️ Partial — FK dep | Hard |
| 7 | `app/onboard.py` — onboard() | FounderObject + FounderSpace | Document, Project, Lead | ❌ | ✅ | Easy |
| 8 | `app/objects/upload.py` — file upload | ShunyaObject | document | ❌ | ✅ | Easy |
| 9 | `app/objects/seed.py` — seed_workspace() | ShunyaObject | customer, contact, invoice, proposal, task | ❌ | ✅ | Medium |
| 10 | `app/objects/canonical.py` — triple-write | UOPObject + ShunyaObject + FounderObject | All types | ✅ (UOP tenant_id) | ⚠️ Already canonical — needs cleanup | Hard |
| 11 | `scripts/seed_demo.py` | FounderObject | customer, supplier, invoice, commitment, note, conversation | ❌ | ✅ | Medium |
| 12 | `scripts/seed_demo_m4.py` | FounderObject | Document, Contract, Spreadsheet | ❌ | ✅ | Easy |
| 13 | `scripts/seed_panchi_club_demo.py` | founder_objects (raw SQL) | note, commitment, timeline_event, conversation | ❌ | ✅ | Medium |
| 14 | `scripts/seed_conversations.py` | FounderObject | conversation FK target | ❌ | ⚠️ Partial | Hard |
| 15 | `app/production/identity/onboarding_routes.py` | FounderObject | Customer, Supplier, Lead, etc. (26 types) | ❌ | ✅ | Medium |

---

## Key Findings

### 1. No `UOPObject` direct production writes outside of `canonical.py`
The canonical `UOPObject` model is only written to by `app/objects/canonical.py` (`create_canonical_object`) and `app/kernel/routes.py` (kernel routes). All other callers write to `FounderObject` or `ShunyaObject`. This means the canonical path is already the correct consolidation target.

### 2. `organization_id` is universally missing
Across **all 15 callers**, only the UOPObject writes in `canonical.py` carry a `tenant_id` (which maps to `organization_id`). Every FounderObject and ShunyaObject write **lacks organization_id**, meaning legacy objects aren't tenant-scoped. This is the single biggest migration gap — every replacement with `ObjectService.create()` must resolve `organization_id`.

### 3. `ObjectService.create()` writes to `sh_objects` (same table as ShunyaObject)
The `ObjectService` in `core/object_service.py` writes to `sh_objects`, which is the **same table** as the `ShunyaObject` ORM model (`app/objects/legacy_models.py`). This means:
- During migration, both paths write to the same table — no data duplication risk.
- `ShunyaObject` is the ORM model; `ObjectService` uses raw SQL. They are two interfaces to the same table.
- `FounderObject` is a **separate table** (`founder_objects`) — this IS data duplication and must be migrated.

### 4. Triple-write in `canonical.py` is the bridge
`create_canonical_object()` writes to all three tables: UOPObject (canonical), ShunyaObject (legacy compat), FounderObject (legacy compat). During migration:
- **Phase 1**: New callers use `create_canonical_object()` → triple-write. Legacy consumers read from FounderObject/ShunyaObject.
- **Phase 2**: Migrate legacy consumers to read from UOPObject (via `get_canonical_object()`). ShunyaObject/FounderObject become read-only.
- **Phase 3**: Remove the ShunyaObject and FounderObject writes. `ObjectService.create()` handles the sole `sh_objects` write.

### 5. Recommended Consolidation Strategy

```
Phase A — Migrate callers with no org dependency (Easy):
  - app/objects/upload.py        → ObjectService.create()
  - app/objects/seed.py          → ObjectService.create()
  - app/onboard.py               → ObjectService.create()

Phase B — Migrate callers with session/org resolution (Medium):
  - app/production/objects.py    → ObjectService.create()
  - app/production/identity/onboarding_routes.py → ObjectService.create()
  - app/founder/routes.py        → remove dual-write (pipeline does it)

Phase C — Migrate automated/script callers (Medium):
  - app/automation/service.py    → ObjectService.create()
  - scripts/seed_demo.py         → ObjectService.create()
  - scripts/seed_demo_m4.py      → ObjectService.create()
  - scripts/seed_panchi_club_demo.py → ObjectService.create()

Phase D — Migrate conversation FK patterns (Hard):
  - app/ai/routes.py             → requires conversation model migration
  - scripts/seed_conversations.py → requires conversation model migration

Phase E — Cleanup triple-write (Hard):
  - app/objects/canonical.py     → remove ShunyaObject + FounderObject writes
  - Only after ALL consumers read from UOPObject
```

### 6. `app/objects/canonical.py` and `core/object_service.py` are redundant
Both write to `sh_objects`. `create_canonical_object()` in `canonical.py` adds UOPObject/FounderObject wrappers. `ObjectService.create()` in `core/object_service.py` is the standalone write. After Phase E, the canonical creation function should call `ObjectService.create()` internally for the `sh_objects` write, making `core/object_service.py` the sole SQL authority for `sh_objects`.