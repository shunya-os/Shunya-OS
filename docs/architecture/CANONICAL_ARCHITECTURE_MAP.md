# CANONICAL ARCHITECTURE MAP — Zero-Gap PR-15, Phase A §4-6

**HEAD:** 3b4324a (a19f1e8 + 6 surgical commits)
**Date:** 2026-08-31
**Authority:** ZGC-PR-15 Phase A §4-6
**Rule:** Every architectural entity has exactly one canonical owner. Duplicates are registered with migration path.

---

## 1. OBJECT STORES

### Canonical Owner: `app/models.py` → `objects` table (41 rows)
- **Model file:** `app/objects/models.py` — ObjectModel
- **Relationship:** `ObjectModel` is the live UOP-flavored object store used by `/api/v1/objects/`
- **Consumers:** `/api/v1/objects/`, `app/objects/`, `app/objects_api.py`

| Store | Table | Rows | Model File | Status | Migration |
|-------|-------|------|------------|--------|-----------|
| **CANONICAL** | `objects` | 41 | `app/objects/models.py` | ACTIVE | — |
| `founder_objects` | `founder_objects` | 44 | `app/founder/models.py` | LEGACY | Consumers use it independently; no overlap with `objects` |
| `uop_objects` | `sh_uop_objects` | 85 | `app/kernel/models.py` | UOP SYSTEM | Kernel-level UOP, maps to/from objects via UOP HTTP API |
| `canonical_objects` | `canonical_objects` | 0 | `app/models.py` | EMPTY/VESTIGIAL | No consumers found; candidate for DROP |
| `sh_objects` | `sh_objects` | 0 | (unknown) | EMPTY/VESTIGIAL | No consumers found; candidate for DROP |

**Resolution:**
- `objects` (41 rows) = canonical live object store for web API
- `founder_objects` (44) = independent founder data (FounderObject), not duplicate — used for onboarding/seed data
- `sh_uop_objects` (85) = kernel UOP layer, architectural dependency of runtime pipeline
- `canonical_objects` (0) and `sh_objects` (0) = vestigial, no consumers found in codebase search

**Action:** Quarantine `canonical_objects` and `sh_objects` tables — mark as LEGACY in migration registry, no new code may write to them, schedule clean-up migration.

---

## 2. IDENTITY STORES

### Canonical Owner: `app/models.py` → `OrgMember` + `app/production/identity_repository.py` → SHUNYAIdentityModel

| Store | Table | Model File | Purpose | Status |
|-------|-------|------------|---------|--------|
| **CANONICAL ORG** | `organizations` + `OrgMember` (app/models.py:834) | `app/models.py` | Org membership + roles | ACTIVE |
| **CANONICAL IDENTITY** | `identity_profiles` | `app/production/identity_repository.py` | SHUNYAIdentityModel — canonical person identity | ACTIVE (0 rows) |
| `team_members` | `team_members` | `app/auth.py` | Legacy auth identity | LEGACY — being migrated away |
| `person_identities` + `persons` | `person_identities` + `persons` | `app/models.py` (389, 582) | Entity-focused person model | UNDER EVALUATION |

**Resolution:**
- Auth identity → `TeamMember` (legacy), migration target = SHUNYAIdentityModel
- Org membership → `OrgMember` (canonical)
- Person entities → `persons` + `person_identities` (canonical for entity extraction)
- `SHUNYAIdentityModel` has 0 rows — foundation for future identity convergence

---

## 3. MEMORY/KNOWLEDGE STORES

### Canonical Owner: `app/models.py` → `memory_records` + `knowledge_documents`

| Store | Table | Rows | Model File | Status |
|-------|-------|------|------------|--------|
| **CANONICAL MEMORY** | `memory_records` | 0 | `app/models.py` | ACTIVE (empty — memory pipeline not running) |
| **CANONICAL KNOWLEDGE** | `knowledge_documents` | 0 | `app/models.py:1027` | ACTIVE (empty — no documents ingested) |
| `rel_ai_memory` | `rel_ai_memory` | 0 | `app/relationship_engine/` | RELATIONSHIP-SCOPED |
| `founder_objects` (type=memory) | `founder_objects` | ~5 (type='memory') | `app/founder/models.py` | LEGACY |
| `knowledge_entries/facts` | `knowledge_entries/facts` | 0 | `app/models.py` | SUPPORTING (entry-level knowledge) |

**Resolution:**
- `memory_records` = canonical for AI memory
- `knowledge_documents` = canonical for document knowledge
- `founder_objects` with type='memory' → legacy, should migrate to `memory_records`
- `rel_ai_memory` = relationship-scoped, valid as domain-specific

---

## 4. TENANT/ORGANIZATION DUALITY

| Store | Table | Rows | Status |
|-------|-------|------|--------|
| **CANONICAL** | `organizations` | 2 | ACTIVE |
| Legacy orphan | `tenants` | 32 | DUPLICATE (multiple Panchi Club copies) |

**Resolution:** Tenant → Organization migration identified but not executed. 32 Tenants are duplicates of 2 real organizations. Requires migration plan, not yet scheduled.

---

## CONSUMER MAP

For each canonical store, all consuming files are registered:

| Canonical Store | Consumers |
|-----------------|-----------|
| `objects` | `app/objects_api.py`, `app/objects/routes.py`, `app/objects/models.py`, frontend object workspace |
| `OrgMember` | `app/people/routes.py`, `app/production/identity/org_routes.py`, `app/production/identity/invitation_routes.py` |
| `TeamMember` (transitioning) | `app/auth_routes.py`, `app/intelligence/routes.py`, various auth decorators |
| `memory_records` | `app/memory/routes.py`, `app/memory/service.py` |
| `knowledge_documents` | `app/knowledge/routes.py`, `app/knowledge/service.py` |