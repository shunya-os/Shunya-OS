# M2C.5R — PHASE R6: PERSON/IDENTITY/RELATIONSHIP QUARANTINE + R7: DATASET REPAIR
## Authority: M2C.5R §8-9 — Canonical Truth Recovery

---

## QUARANTINE RULE (Permanent)

Document evidence ≠ canonical identity.

The pipeline MUST be:
```
Document → extraction → candidate entity → identity evidence → confidence/provenance → canonical Person
```

Currently the pipeline is:
```
Document → extraction → knowledge_fact → Person (DIRECT — bypassing confidence/provenance)
```

This is BROKEN. The enrichment script (`scripts/enrich_documents.py`) creates Person records directly from knowledge_facts without identity resolution, confidence thresholds, or provenance verification.

---

## CURRENT PERSON STATE

| Source | Count | Status |
|--------|-------|--------|
| Original persons (pre-M2C.5) | 10 | Presumed legitimate |
| M2C.5 enrichment (id 403-407) | 5 | 🔴 CONTAMINATED |
| — False positives deleted | 4 (404-407) | ✅ Removed |
| — Ambiguous retained (403 Patrick) | 1 | 🔴 UNCLEAN (wrong tenant=89) |
| **Total persons now** | **11** | **🔴 1 still contaminated** |

## CURRENT PERSON_IDENTITIES STATE

| Source | Count | Status |
|--------|-------|--------|
| Pre-M2C.5 | 0 | — |
| M2C.5 enrichment | 5 | ✅ Deleted (all) |
| **Total now** | **0** | ✅ Clean |

## CURRENT RELATIONSHIPS STATE

| Source | Count | Status |
|--------|-------|--------|
| Pre-M2C.5 | 0 | — |
| M2C.5 enrichment | 5 | ✅ Deleted (all) |
| **Total now** | **0** | ✅ Clean |

---

## RECONCILIATION TABLE (R7 §9)

| Entity | Before M2C.5 | M2C.5 Added | Removed | Contaminated | Remaining | Expected |
|--------|-------------|-------------|---------|-------------|-----------|----------|
| Person | 10 | 5 | 4 | 1 (Patrick) | 11 | 10 + Patrick needs resolution |
| Person Identity | 0 | 5 | 5 | 0 | 0 | 0 |
| Relationship | 0 | 5 | 5 | 0 | 0 | 0 |
| Object (UOP) | 0 | 85 | 0 | 85 | 85 | 0 or Canonical |
| Organization | 0 | 2 | 0 | 0 | 2 | 2 (test) |

**Discrepancies**:
1. Patrick Sarracin (id=403) has tenant_id=89, which has no proven relationship to Document 15 — 🔴 UNCLEAN
2. 85 UOP objects are unapproved migration artifacts — 🔴 UNCLEAN

---

## VERIFICATION: NO ORPHAN REFERENCES

Checked for FK references to deleted records:

| Deleted Entity | FK References Found | Status |
|----------------|-------------------|--------|
| Person 404-407 | None | ✅ |
| Person Identities 5-9 | None | ✅ |
| Relationships 11-15 | None | ✅ |

---

## PHASE R6-R7: COMPLETE
Proceeding to R8 — Restore Test Integrity.