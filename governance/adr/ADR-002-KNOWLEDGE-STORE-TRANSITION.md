# ADR-002: Knowledge Store Transition

**Class:** Engineering
**Status:** Proposed
**Date:** 2026-07-18
**Author:** Chief Software Architect
**Supersedes:** (none)
**Superseded by:** (none)

**Approval Authority:**
- If Engineering: Chief Software Architect
- If Architectural/Constitutional: Chief Constitutional Architect

---

## Context

### Problem

The SHUNYA architecture baseline defines the Immutable Knowledge Store (IKS) as the canonical knowledge storage mechanism (ES-002: Knowledge Engine). However, the current implementation has two active knowledge store implementations:

1. **KnowledgeLayer** — a markdown-file-based knowledge base parser at `app/shunya/knowledge.py` (class `KnowledgeLayer`, ~189 lines). Currently wired into 5 production code paths: `workflow.py`, `interface.py`, `routes.py`, `reasoning.py`, and `client_portal.py`.

2. **ImmutableKnowledgeStore** — a versioned, SQLAlchemy-backed fact store at `app/shunya/knowledge_store.py` (class `ImmutableKnowledgeStore`, ~383 lines). Currently only used in `test_characterization.py`.

The architecture specification (ES-002) clearly targets IKS as the canonical store. KnowledgeLayer is a legacy implementation that does not satisfy the constitutional requirements of immutability, versioning, and traceability.

### Current State

**KnowledgeLayer (active, wired):**
- Parses `knowledge-base.md` — a single markdown file at `app/data/knowledge-base.md`
- `KnowledgeLayer.DESTINATIONS` is a class-level dict populated lazily by parsing the markdown file
- Returns `Destination` dataclass with fields: name, country, region, visa_info, best_months, weather_notes, currency, currency_note, local_taxes, wedding_requirements, transport_notes, transport_cost_range, top_venues, tips, raw_section
- Provides: `get_destination()`, `search_destinations()`, `list_all()`, `search()`, `reload()`
- Used directly in 5 call sites via `from app.shunya.knowledge import KnowledgeLayer`

**ImmutableKnowledgeStore (specified, unwired):**
- SQLAlchemy model `KnowledgeFact` backed by `knowledge_facts` table in PostgreSQL
- Fields: id, fact_key, version, domain, category, value (JSON text), confidence, evidence, provenance, created_at, superseded_at, status
- Methods: `set_fact()`, `get_fact()`, `get_fact_history()`, `search_facts()`, `delete_fact()`
- Fact keys follow `{domain}.{category}.{name}` convention (e.g., `destination.bali.visa`)
- Supports versioning: `set_fact()` creates a new version; `get_fact()` returns the latest active version; `get_fact_history()` returns all versions
- Implements immutable knowledge — no in-place updates (supersession pattern only)

### Constraints

- **ES-002 specifies IKS as canonical.** The Knowledge Engine specification explicitly targets the Immutable Knowledge Store. KnowledgeLayer is a legacy implementation.
- **Constitutional requirements demand immutability.** SHUNYA_ARCHITECTURE.md §6.4 (Immutable Knowledge) and SHUNYA_ENGINEERING_CONSTITUTION.md §4 (Immutability and Traceability) require versioned, never-deleted facts.
- **KnowledgeLayer does not satisfy constitutional requirements.** Markdown file parsing is mutable, unversioned, and untraceable. It is not a valid target for the final architecture.
- **Both implementations must coexist during migration.** The system must not break while transitioning from KnowledgeLayer to IKS.

### Evidence

- ES-002: Knowledge Engine — specifies IKS as canonical knowledge storage
- `app/shunya/knowledge.py` — KnowledgeLayer implementation (189 lines, wired in 5 places)
- `app/shunya/knowledge_store.py` — ImmutableKnowledgeStore implementation (383 lines, used in tests only)
- `tests/test_characterization.py` — only consumer of IKS
- `app/shunya/workflow.py:9` — `from .knowledge import KnowledgeLayer`
- `app/shunya/interface.py:11` — `from .knowledge import KnowledgeLayer`
- `app/routes.py:394,1138` — `from app.shunya.knowledge import KnowledgeLayer`
- `app/shunya/reasoning.py:15` — `from .knowledge import KnowledgeLayer, Destination`
- `app/client_portal.py:53` — `from app.shunya.knowledge import KnowledgeLayer`
- ARCHITECTURE_BASELINE_REVIEW.md — M4: "Knowledge Engine vs KnowledgeLayer Gap"
- ARCHITECTURE_FINDINGS_CLASSIFICATION.md — M4/ADR-002: "KnowledgeLayer vs ImmutableKnowledgeStore Gap"

---

## Decision

The Immutable Knowledge Store (IKS) is the canonical knowledge storage. KnowledgeLayer is a legacy migration source. The transition follows a four-phase migration path:

### Phase 1: Coexistence (Immediate — Non-Breaking)

Both implementations coexist. KnowledgeLayer remains wired for all existing functionality. IKS is wired alongside KnowledgeLayer in the Knowledge Engine but is not yet the primary data source.

**Actions:**
1. Create a `KnowledgeEngine` facade that wraps both KnowledgeLayer and IKS
2. All existing call sites continue to function through the facade
3. `KnowledgeEngine.read()` first attempts IKS lookup; falls back to KnowledgeLayer if not found
4. `KnowledgeEngine.write()` writes to IKS only (KnowledgeLayer is read-only from this point)

### Phase 2: Seed (Post-Phase 1)

Seed IKS with data from KnowledgeLayer. This is a one-time data migration.

**Actions:**
1. Run a migration script that reads all data from KnowledgeLayer's markdown parser
2. For each `Destination`, create a corresponding `KnowledgeFact` in IKS:
   - `fact_key = "destination.{name}.description"` (and similar keys for each field)
   - `domain = "travel"`
   - `confidence = 0.7` (from verified source, but not independently verified — conservative)
   - `status = "active"`, `version = 1`
3. Verify that all KnowledgeLayer destinations are represented in IKS
4. Log any destinations that failed to migrate

### Phase 3: Cutover (Post-Phase 2)

Switch the KnowledgeEngine facade to use IKS as the primary source. KnowledgeLayer becomes a read-through fallback.

**Actions:**
1. `KnowledgeEngine.read()` reads from IKS primarily; falls back to KnowledgeLayer only for fact keys that do not exist in IKS
2. All KnowledgeLayer data sources are frozen (no more markdown file updates accepted)
3. New knowledge is written exclusively through IKS
4. KnowledgeLayer is read-only at this point

### Phase 4: Retirement (Post-Phase 3)

Remove KnowledgeLayer from the codebase.

**Actions:**
1. Verify that no code path depends on KnowledgeLayer for data not available in IKS
2. Remove KnowledgeLayer class and markdown file parser
3. Update all imports from `from app.shunya.knowledge import KnowledgeLayer` to `from app.shunya.knowledge_engine import KnowledgeEngine`
4. Remove the `knowledge-base.md` file (after confirming all data is migrated)
5. Remove KnowledgeLayer-specific tests
6. Verify end-to-end: all 5 previously KnowledgeLayer-dependent paths now function through IKS via the KnowledgeEngine facade

### KnowledgeEngine Facade Interface

```
class KnowledgeEngine:
    def __init__(self, iks: ImmutableKnowledgeStore, fallback: Optional[KnowledgeLayer] = None)

    def get_fact(self, fact_key: str, version: Optional[int] = None) -> Optional[KnowledgeFact]
        # Phase 1-2: try IKS, fall back to KnowledgeLayer (with on-the-fly conversion)
        # Phase 3: try IKS, fall back to KnowledgeLayer only for unmigrated keys
        # Phase 4: IKS only

    def set_fact(self, fact_key: str, value: Any, domain: str, category: str,
                 confidence: float, provenance: Provenance) -> KnowledgeFact
        # Always writes to IKS. KnowledgeLayer is never written.

    def search_facts(self, query: str, domain: Optional[str] = None,
                     category: Optional[str] = None) -> List[KnowledgeFact]
        # Phase 1-2: search both IKS and KnowledgeLayer, merge results
        # Phase 3-4: IKS only

    def get_fact_history(self, fact_key: str) -> List[KnowledgeFact]
        # IKS only (KnowledgeLayer has no versioning)

    def migrate_from_knowledge_layer(self) -> MigrationReport
        # Phase 2 only: one-time migration from KnowledgeLayer to IKS
```

### Fact Key Mapping (KnowledgeLayer → IKS)

KnowledgeLayer `Destination` fields map to IKS fact keys as follows:

| KnowledgeLayer Field | IKS Fact Key | Domain | Category |
|---------------------|--------------|--------|----------|
| `destination.name` | `destination.{name}.exists` | travel | destination |
| `destination.country` | `destination.{name}.country` | travel | destination |
| `destination.region` | `destination.{name}.region` | travel | destination |
| `destination.visa_info` | `destination.{name}.visa` | travel | visa |
| `destination.best_months` | `destination.{name}.best_months` | travel | seasonality |
| `destination.weather_notes` | `destination.{name}.weather` | travel | weather |
| `destination.currency` | `destination.{name}.currency` | travel | financial |
| `destination.local_taxes` | `destination.{name}.taxes` | travel | financial |
| `destination.wedding_requirements` | `destination.{name}.wedding` | travel | wedding |
| `destination.transport_notes` | `destination.{name}.transport` | travel | transport |
| `destination.top_venues` | `destination.{name}.venues` | travel | venues |

---

## Options Considered

### Option 1: KnowledgeLayer → IKS Transition (Chosen)

**Description:** Coexistence → Seed → Cutover → Retirement. Both implementations coexist during a phased migration.

**Pros:**
- No system downtime during migration
- Each phase independently verifiable
- Fallback path ensures no data loss
- KnowledgeEngine facade provides clean API regardless of backend
- Consistent with ES-002 specification

**Cons:**
- Temporary complexity — two implementations during migration
- Migration script must be verified for completeness
- KnowledgeLayer fallback must be removed in Phase 4 to avoid architectural debt

### Option 2: Immediate Cutover

**Description:** Disable KnowledgeLayer, enable IKS in one deployment. Migrate all data in a single batch.

**Pros:**
- No coexistence period — immediate simplification

**Cons:**
- High risk — 5 production code paths depend on KnowledgeLayer
- No fallback — any migration error breaks production
- Testing confidence is low — IKS is only used in characterization tests
- High blast radius for a single deployment

### Option 3: KnowledgeLayer Is Canonical (Rejected)

**Description:** Accept KnowledgeLayer as the canonical store. Never implement IKS.

**Pros:**
- No migration needed
- Path of least resistance

**Cons:**
- **Constitutionally non-compliant.** KnowledgeLayer is mutable, unversioned, untraceable. It cannot satisfy SHUNYA_ARCHITECTURE.md §6.4 (Immutable Knowledge) or SHUNYA_ENGINEERING_CONSTITUTION.md §4 (Immutability and Traceability).
- **Architecturally divergent.** ES-002 specifies IKS. Keeping KnowledgeLayer as canonical would create divergence that requires a constitutional ADR to resolve.
- **No compounding intelligence.** Without versioning, facts cannot be traced, confidence cannot evolve, and the compounding loop is broken.

---

## Consequences

### Positive

- KnowledgeEngine facade provides a single, clean API for all knowledge access
- Constitutional requirements for immutability and traceability are satisfied
- ES-002 specification is faithfully implemented
- Phased migration minimizes risk
- All 5 existing KnowledgeLayer call sites continue to function during migration
- Future knowledge operations use versioned, immutable storage

### Negative

- Temporary complexity during coexistence (facade must handle two backends)
- Migration script must be maintained and verified
- KnowledgeLayer fallback may mask IKS issues during Phase 2 (data may appear to come from IKS but actually come from KnowledgeLayer)

### Neutral

- No engine specification changes — ES-002 already targets IKS
- No API contract changes — KnowledgeEngine facade preserves existing KnowledgeLayer interface patterns
- KnowledgeLayer is explicitly documented as legacy — prevents new code from depending on it

---

## Compliance

### Constitutional Principles Affected

- **§6.4 — Immutable Knowledge:** IKS provides versioned, never-deleted facts. KnowledgeLayer does not. This transition establishes compliance.
- **§6.5 — Explainable Decisions:** Versioned facts enable decision tracing. KnowledgeLayer's unversioned storage makes this impossible.
- **§4 (Immutability and Traceability — Engineering Constitution):** IKS's versioning pattern (supersede, never overwrite) satisfies Article 4 requirements.

### Engineering Constitution Articles Affected

- **Article 4 — Immutability and Traceability:** This transition directly implements Article 4.1 (no silent overwrites) and Article 4.2 (every decision traceable to evidence).
- **Article 8 — Divergence Protocol:** KnowledgeLayer was a pre-existing divergence (implementation did not match spec). This ADR documents and resolves that divergence.

---

## Verification

- [ ] KnowledgeEngine facade implemented with `get_fact`, `set_fact`, `search_facts`, `get_fact_history`
- [ ] Phase 1: All 5 existing KnowledgeLayer call sites function through the facade
- [ ] Phase 2: Migration script reads all KnowledgeLayer destinations and creates IKS KnowledgeFacts
- [ ] Phase 2: Migration report confirms all destinations migrated; any failures logged
- [ ] Phase 3: IKS is primary read source; KnowledgeLayer is read-through fallback only
- [ ] Phase 4: KnowledgeLayer removed; all call sites use KnowledgeEngine
- [ ] Fact key mapping verified — all KnowledgeLayer fields have corresponding IKS fact keys
- [ ] No data loss — IKS contains at least the same knowledge as KnowledgeLayer after migration
- [ ] KnowledgeLayer tests removed; KnowledgeEngine tests added

---

## References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — Section 6.4 (Immutable Knowledge), Section 5 (Knowledge Layer)
- [SHUNYA_ENGINEERING_CONSTITUTION.md](/governance/SHUNYA_ENGINEERING_CONSTITUTION.md) — Article 4 (Immutability and Traceability)
- [ES-002: Knowledge Engine](/governance/engine_specs/ES-002-KNOWLEDGE-ENGINE.md) — Immutable Knowledge Store specification
- [ARCHITECTURE_BASELINE_REVIEW.md](/architecture/ARCHITECTURE_BASELINE_REVIEW.md) — M4 (Knowledge Engine vs KnowledgeLayer Gap), ADR-002
- [ARCHITECTURE_FINDINGS_CLASSIFICATION.md](/architecture/ARCHITECTURE_FINDINGS_CLASSIFICATION.md) — M4/ADR-002
- [SUPPORTING_ARCHITECTURE_JUSTIFICATION.md](/architecture/SUPPORTING_ARCHITECTURE_JUSTIFICATION.md) — Component classification references
- `app/shunya/knowledge.py` — KnowledgeLayer implementation (189 lines)
- `app/shunya/knowledge_store.py` — ImmutableKnowledgeStore implementation (383 lines)
- `tests/test_characterization.py` — IKS usage in tests