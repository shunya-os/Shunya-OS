# UCP-02A — Universal Capability Consolidation: Improvement Report

**Date:** 2026-08-06
**Scope:** Future improvements identified during architectural self-audit

---

## Priority: High

### H1. Persistent Storage Adapter
**Issue:** All profiles and data live in memory (`self._profiles`).
**Impact:** Data loss on restart, single-process only, no query capabilities.
**Recommendation:** Build a `PersistentRelationshipIntelligenceRuntime` subclass that:
- Uses SQLite/PostgreSQL for profile, commitment, communication, and interaction storage
- Implements `initialize()` to open connections
- Implements `shutdown()` to flush and close
- Adds pagination and filtering to list methods
- Implements transaction wrapping for multi-step operations
**Effort:** 2-3 weeks

### H2. Batch Trust → Health Computation
**Issue:** `assess_relationship_health()` calls `compute_trust()` internally (in `engine.assess_health()`) and `generate_insights()` also calls `assess_health()` which recomputes trust. When the runtime's `assess_relationship_health()` calls both, trust is computed twice.
**Impact:** ~2x computation on health assessment calls.
**Recommendation:** Parameterize `generate_insights()` to accept an optional pre-computed health result. When called from `assess_relationship_health()`, pass the already-computed health.
**Effort:** 1 day

---

## Priority: Medium

### M1. Entity→Profile Index
**Issue:** `list_profiles_by_entity()` is O(n) — scans all profiles.
**Impact:** Performance degradation beyond ~10K profiles.
**Recommendation:** Add a reverse index: `self._entity_index: dict[str, set[str]]` mapping entity_id → set of profile_ids. Update on profile create, clear on shutdown.
**Effort:** 1 day

### M2. Profile ID Determinism with Role
**Issue:** `_resolve_profile_id()` uses only source + target, not role. Same entity pair with different roles overwrites.
**Impact:** One profile per entity pair regardless of role.
**Recommendation:** Include role in the hash key, or support multi-role profiles natively. Current behaviour is acceptable for the common case (one relationship type per pair).
**Effort:** 2 days

### M3. Health Assessment Caching
**Issue:** `assess_relationship_health()` always recomputes. No time-based cache expiration.
**Impact:** Repeated health assessment in the same session is wasteful.
**Recommendation:** Add a `cache_ttl_seconds` parameter. If the last assessment is fresher than TTL, return cached result.
**Effort:** 1 day

---

## Priority: Low

### L1. AI Provider Examples
**Issue:** `RelationshipAIProvider` ABC has no concrete LLM-backed implementation.
**Impact:** Users must write their own provider from scratch to use LLM-based analysis.
**Recommendation:** Create an `OpenAIProvider` or `GroqProvider` reference implementation.
**Effort:** 2-3 days

### L2. Multi-language Communication Analysis
**Issue:** `analyze_communication()` in DefaultAIProvider uses English-only word lists.
**Impact:** Poor quality for non-English communications.
**Recommendation:** Use the LLM provider for language-agnostic analysis, or add word lists for common languages.
**Effort:** 3-5 days

### L3. Audit Trail for Profile Changes
**Issue:** Profile changes (commitment status, sentiment, etc.) are not recorded as timeline events.
**Impact:** No change history or rollback capability.
**Recommendation:** Add an audit log or timeline to `RelationshipProfile` recording every mutation with timestamp and actor.
**Effort:** 1-2 days

---

## Summary

| Priority | Count | Estimated Effort |
|----------|-------|------------------|
| High | 2 | 2-3.5 weeks |
| Medium | 3 | 4 days |
| Low | 3 | 6-10 days |
| **Total** | **8** | **4-6 weeks** |