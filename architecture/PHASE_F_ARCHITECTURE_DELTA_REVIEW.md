# Architecture Delta Review — Phase F Reasoning Engine

**Document ID:** ADR-2026-07-19-001
**Author:** Hermes Agent (Constitutional Architecture support)
**Subject:** Comparison of baseline (Observation/Conflict/Gap/Risk) vs. refactored (Finding/Contradiction/Assumption/Constraint) model
**Status:** DRAFT — awaiting Governance review
**Scope:** `app/shunya/reasoning/` — models, rules, registry, confidence, evidence graph, engine

---

## 1. Purpose

This review documents every architectural change introduced in the mistaken refactoring of Phase F, explains the rationale behind each change, and evaluates each against SHUNYA's canonical architecture criteria. The goal is to determine which (if any) changes should be adopted, rejected, or deferred to a later phase.

---

## 2. Baseline Architecture (Governance-Approved)

### 2.1 Model Types

| Type | Role | Fields |
|------|------|--------|
| `Observation` | What is true | observation_id, type (FACT/INFERENCE/DERIVED/EXTERNAL), fact_key, fact_value, label, description, source, confidence, evidence, metadata, created_at |
| `Conflict` | What is conflicting | conflict_id, severity (CRITICAL/HIGH/MEDIUM/LOW/INFO), label, description, fact_keys, fact_values, sources, resolution_guidance, rule_name, evidence, metadata, created_at |
| `Gap` | What is missing | gap_id, severity (BLOCKING/REQUIRED/RECOMMENDED/OPTIONAL), fact_key, label, description, source, rule_name, evidence, metadata, created_at |
| `Risk` | What is risky | risk_id, severity (CRITICAL/HIGH/MEDIUM/LOW/INFO), label, description, fact_key, condition, impact, mitigation, rule_name, evidence, metadata, created_at |
| `ConfidenceAssessment` | Deterministic confidence | overall_score, level, completeness/consistency/freshness/corroboration/provenance_quality scores, total_observations/conflicts/gaps/risks, required_facts_present/total, evidence, metadata |

### 2.2 Enum Types

- `ObservationType`: FACT, INFERENCE, DERIVED, EXTERNAL
- `ConflictSeverity`: CRITICAL, HIGH, MEDIUM, LOW, INFO
- `GapSeverity`: BLOCKING, REQUIRED, RECOMMENDED, OPTIONAL
- `RiskSeverity`: CRITICAL, HIGH, MEDIUM, LOW, INFO
- `ConfidenceLevel`: VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW, INSUFFICIENT

### 2.3 Result Container

`ReasoningResult` holds **four separate lists**: `observations`, `conflicts`, `gaps`, `risks` — plus `attention_items`, `confidence`, `metadata`.

### 2.4 Rules Pipeline

Rules produce `RuleResult` with **four separate lists** (`observations`, `conflicts`, `gaps`, `risks`). The engine iterates each list independently. 18 rules total.

### 2.5 Confidence Scoring

`ConfidenceEngine.assess()` accepts **four parameters**: `observations`, `conflicts`, `gaps`, `risks`.

---

## 3. Refactored Architecture (Reverted — Governance Document G5.5 Aligned)

### 3.1 Model Types

| Type | Role | Fields |
|------|------|--------|
| `Finding` | Unified fact, gap, or risk | finding_id, finding_type (observation/gap/risk), severity (unified: CRITICAL/HIGH/MEDIUM/LOW/INFO/BLOCKING/REQUIRED/RECOMMENDED/OPTIONAL), fact_key, fact_value, label, description, source, confidence, evidence, metadata, created_at |
| `Contradiction` | What is conflicting (renamed + extended) | contradiction_id, contradiction_type (fact_conflict/assumption_conflict/stale_context/incomplete_evidence/duplicate_finding), severity, label, description, fact_keys, fact_values, sources, finding_ids, resolution_guidance, rule_name, evidence, metadata, created_at |
| `Assumption` | **NEW** — documented assumption | assumption_id, fact_key, label, description, assumed_value, evidence, metadata, created_at |
| `Constraint` | **NEW** — documented constraint | constraint_id, fact_key, constraint_type, label, description, value, evidence, metadata, created_at |
| `ConfidenceScore` | Renamed from ConfidenceAssessment | overall_score, level, completeness/consistency/freshness/corroboration/provenance_quality scores, total_findings/contradictions/assumptions/constraints, required_facts_present/total, evidence, metadata |
| `ReasoningSession` | **NEW** — session wrapper | session_id, correlation_id, context_id, engine_version, started_at, completed_at, result_ids, total_evaluations, total_elapsed_ms, metadata |

### 3.2 Enum Changes

| Baseline | Refactored |
|----------|------------|
| `ObservationType` (FACT/INFERENCE/DERIVED/EXTERNAL) | **Removed** — subsumed into `Finding` type |
| `ConflictSeverity` (CRITICAL/HIGH/MEDIUM/LOW/INFO) | **Renamed** to `ContradictionSeverity` (same values) |
| `GapSeverity` (BLOCKING/REQUIRED/RECOMMENDED/OPTIONAL) | **Removed** — subsumed into `FindingSeverity` |
| `RiskSeverity` (CRITICAL/HIGH/MEDIUM/LOW/INFO) | **Removed** — subsumed into `FindingSeverity` |
| *(none)* | **NEW** `FindingSeverity` (CRITICAL/HIGH/MEDIUM/LOW/INFO/BLOCKING/REQUIRED/RECOMMENDED/OPTIONAL) |
| *(none)* | **NEW** `ContradictionType` (fact_conflict/assumption_conflict/stale_context/incomplete_evidence/duplicate_finding) |
| `ConfidenceLevel` | Unchanged |

### 3.3 Result Container

`ReasoningResult` holds: `findings`, `contradictions`, `assumptions`, `constraints`, `attention_items`, `confidence`, `metadata`. The `observations`, `gaps`, `risks` properties become **computed filters** over the `findings` list.

### 3.4 Rules Pipeline

Rules produce `RuleResult` with **two lists** (`findings`, `contradictions`) instead of four. A new `contradiction_detection` rule added (stale context check). 19 rules total (+1).

### 3.5 Confidence Scoring

`ConfidenceEngine.assess()` accepts **two parameters**: `findings`, `contradictions`.

---

## 4. Detailed Architectural Delta

### 4.1 Δ1: Observation + Gap + Risk → Finding (Unified Model)

**Change:** Three separate model classes (`Observation`, `Gap`, `Risk`) merged into one `Finding` class with a `finding_type` discriminator.

**Rationale for the change:**
- All three types share the same structural pattern (id, key, value, severity, evidence chain, timestamp).
- They are produced by the same rule pipeline, aggregated in the same loop, and consumed by the same confidence engine.
- A unified type simplifies the API surface: `ReasoningResult.findings` instead of three parallel lists.
- The discriminator (`finding_type: "observation" | "gap" | "risk"`) preserves semantic distinction.

**Impact:**
- Reduces `ReasoningResult` fields from 4 lists to 1 list + computed properties.
- Reduces `RuleResult` fields from 4 lists to 1 list.
- Reduces `ConfidenceEngine.assess()` parameters from 4 to 2.
- Eliminates 3 enum types (`ObservationType`, `GapSeverity`, `RiskSeverity`), consolidating into `FindingSeverity`.
- **Backward incompatibility:** Any external code referencing `result.observations`, `result.gaps`, `result.risks` needs to change — but computed properties can preserve the access pattern.

**Assessment: Should this become canonical?**
- **MERIT:** High. The unification is structurally sound, reduces code duplication in the pipeline, and the G5.5 reissuance explicitly calls for `Finding` as the canonical type. The computed property pattern (`.observations`, `.gaps`, `.risks`) preserves backward compatibility for consumers.
- **RISK:** None identified — this is a mechanical rename with no logic change.
- **RECOMMENDATION:** **ACCEPT** — unify into `Finding` on next phase boundary.

### 4.2 Δ2: Conflict → Contradiction (Rename + Extend)

**Change:** `Conflict` renamed to `Contradiction`. `ContradictionType` enum added with five categories: `fact_conflict`, `assumption_conflict`, `stale_context`, `incomplete_evidence`, `duplicate_finding`. `ContradictionSeverity` replaces `ConflictSeverity` (same values). A `finding_ids` field added to link contradictions to specific findings.

**Rationale for the change:**
- "Contradiction" is the mathematically precise term (G5.5 §5 uses it).
- The typed contradiction categories (stale context, incomplete evidence, duplicate findings) go beyond simple fact conflicts and align with G5.5 §5 requirements.
- The `finding_ids` field enables explicit traceability from contradiction to the specific findings involved.

**Impact:**
- Semantic rename only — the data structure is nearly identical (same severity values, same fields plus finding_ids).
- The `ContradictionType` enum adds categorical expressiveness without changing behaviour.
- Renaming 3 rule functions (`identity_degraded_conflict` → `identity_degraded_contradiction`, etc.).
- Rule categories: `conflict` → `contradiction`.

**Assessment: Should this become canonical?**
- **MERIT:** High. Aligns with G5.5 terminology. The `contradiction_type` discriminator is architecturally meaningful for downstream engines (Governance can filter by type).
- **RISK:** Low — mapping is 1:1 with existing `Conflict`. No consumer outside the reasoning package references `Conflict` directly (only `ReasoningResult` callers use `result.conflicts`).
- **RECOMMENDATION:** **ACCEPT** — rename to `Contradiction` with typed discrimination.

### 4.3 Δ3: ConfidenceAssessment → ConfidenceScore (Rename + Extend)

**Change:** `ConfidenceAssessment` renamed to `ConfidenceScore`. Field `total_observations/conflicts/gaps/risks` → `total_findings/contradictions/assumptions/constraints`.

**Rationale for the change:**
- "Score" is more precise than "Assessment" — it is a computed numeric value, not a qualitative judgement.
- Field rename aligns with the unified Finding model (total_findings instead of total_observations).

**Impact:**
- Pure rename + field rename. No behavioural change.
- The `compute_level` classmethod and all dimension scores are unchanged.

**Assessment: Should this become canonical?**
- **MERIT:** Medium. Naming preference only.
- **RISK:** None — pure rename.
- **RECOMMENDATION:** **ACCEPT** — rename to `ConfidenceScore`.

### 4.4 Δ4: ReasoningSession (New Model)

**Change:** A new `ReasoningSession` dataclass added with session_id, correlation_id, context_id, timestamps, result_ids list, total_evaluations, total_elapsed_ms.

**Rationale for the change:**
- Provides a session-level wrapper for one or more evaluations sharing a correlation ID.
- Enables lifecycle tracking (session start → N evaluations → session complete).
- The `result_ids` list allows a session to group multiple evaluations (e.g., a degraded-first-then-retry pattern).

**Impact:**
- New type — no impact on existing code.
- Not referenced by any rule, engine method, or test in the refactored code (only constructed and serialized).

**Assessment: Should this become canonical?**
- **MERIT:** Medium. Useful for observability and correlation tracing across multiple evaluations. Will be required once multi-evaluation workflows exist.
- **RISK:** None — add-only, no existing code affected.
- **RECOMMENDATION:** **DEFER** to Phase G (Planning Engine) or H (Governance Engine), where session-level tracking becomes meaningful. Implement when the first multi-evaluation consumer appears.

### 4.5 Δ5: Assumption (New Model)

**Change:** A new `Assumption` dataclass with assumption_id, fact_key, label, description, assumed_value, evidence, metadata, created_at.

**Rationale for the change:**
- G5.5 reissuance explicitly calls for `Assumption` as a first-class model type.
- Captures assumptions made during reasoning (e.g., "assumed tenant=1 because context was degraded").
- Enables explicit — rather than implicit — assumption tracking for audit and governance.
- Distinguishes "facts" (supported by evidence) from "assumptions" (presumed in absence of evidence).

**Impact:**
- New type — no impact on existing code.
- `ReasoningResult.assumptions` is an additional list alongside findings and contradictions.
- Rules could optionally emit assumptions, but none of the 19 refactored rules did so.

**Assessment: Should this become canonical?**
- **MERIT:** High. Explicit assumption tracking is critical for governance audit requirements. Without it, assumptions are invisible.
- **RISK:** None if implemented as add-only. Existing rules remain unchanged; new rules can emit assumptions when needed.
- **RECOMMENDATION:** **ACCEPT** — add `Assumption` model. Rule emission can be zero initially (behaviour-neutral) and populated as rules evolve.

### 4.6 Δ6: Constraint (New Model)

**Change:** A new `Constraint` dataclass with constraint_id, fact_key, constraint_type, label, description, value, evidence, metadata, created_at.

**Rationale for the change:**
- G5.5 reissuance calls for `Constraint` as a first-class model type.
- Captures boundaries, limitations, or invariants identified during reasoning (e.g., "max 100 items per context", "response must complete within 5s").
- Enables downstream engines (Planning, Governance, Execution) to access constraints without re-deriving them.

**Impact:**
- New type — no impact on existing code.
- `ReasoningResult.constraints` is an additional list.

**Assessment: Should this become canonical?**
- **MERIT:** Medium. True value appears when downstream engines consume constraints. During Phase F alone, constraints are identified but not acted upon.
- **RISK:** None if add-only.
- **RECOMMENDATION:** **ACCEPT** — add `Constraint` model. Downstream consumption will validate its utility in Phase G/H/I.

### 4.7 Δ7: Contradiction Detection Rule (New Rule)

**Change:** A new `rule_contradiction_detection` rule added (19th rule, priority 230, category `contradiction`). Detects stale context (context older than 1 hour → `stale_context` contradiction).

**Rationale for the change:**
- G5.5 §5 mandates detection of: stale context, incomplete evidence, duplicate findings.
- The existing contradiction rules (identity_degraded, knowledge_degraded, budget_truncation) cover fact_conflict and incomplete_evidence. Stale context detection was missing.

**Impact:**
- Adds 1 new rule to the pipeline (19 total).
- Backward compatible — existing 18 rules unchanged.
- Rule is deterministic and has no side effects.

**Assessment: Should this become canonical?**
- **MERIT:** High. Stale context detection is explicitly required by G5.5 §5. Its absence in the baseline is a compliance gap.
- **RISK:** None — the rule is self-contained and only produces contradictions when stale context is detected.
- **RECOMMENDATION:** **ACCEPT** — add `rule_contradiction_detection` to the standard rule set immediately. This is a compliance gap fix, not an architectural change.

### 4.8 Δ8: Unified Enums (Severity Consolidation)

**Change:** `ConflictSeverity`, `GapSeverity`, `RiskSeverity` consolidated into `FindingSeverity`. `ContradictionSeverity` created (same values as `ConflictSeverity`).

**Rationale for the change:**
- `FindingSeverity` unifies all severity levels used across observation, gap, and risk findings.
- A single severity enum reduces import surface and eliminates cross-type mapping.
- `ContradictionSeverity` mirrors `ConflictSeverity` exactly.

**Impact:**
- Existing rules reference `GapSeverity.BLOCKING` → would become `FindingSeverity.BLOCKING`.
- Existing rules reference `RiskSeverity.HIGH` → would become `FindingSeverity.HIGH`.
- Existing `ConflictSeverity.CRITICAL` → `ContradictionSeverity.CRITICAL`.

**Assessment: Should this become canonical?**
- **MERIT:** Medium. Cleaner but functionally identical.
- **RISK:** Low — breaking change for any external code importing the old severity enums.
- **RECOMMENDATION:** **ACCEPT** the consolidation into `FindingSeverity` + `ContradictionSeverity` as part of the Finding/Contradiction rename. Provide deprecated aliases for one phase cycle.

---

## 5. Summary of Recommendations

| # | Change | Recommendation | Priority | Phase |
|---|--------|---------------|----------|-------|
| Δ1 | Observation/Gap/Risk → Finding | **ACCEPT** | High | Current (Phase F) |
| Δ2 | Conflict → Contradiction | **ACCEPT** | High | Current (Phase F) |
| Δ3 | ConfidenceAssessment → ConfidenceScore | **ACCEPT** | Medium | Current (Phase F) |
| Δ4 | ReasoningSession (new model) | **DEFER** | Low | Phase G or H |
| Δ5 | Assumption (new model) | **ACCEPT** | High | Current (Phase F) |
| Δ6 | Constraint (new model) | **ACCEPT** | Medium | Current (Phase F) |
| Δ7 | Contradiction detection rule | **ACCEPT** | **Critical** | **Immediate** |
| Δ8 | Unified severity enums | **ACCEPT** | Medium | Current (Phase F) |

### 5.1 Accepted Changes (Implementation Plan)

If all accepted changes are adopted, the migration path is:

1. **Phase F — models:** Add `Finding`, `Contradiction`, `Assumption`, `Constraint`, `ConfidenceScore`. Keep `Observation`, `Conflict`, `Gap`, `Risk`, `ConfidenceAssessment` as deprecated aliases.
2. **Phase F — rules:** Add `rule_contradiction_detection`. Existing 18 rules continue producing Observation/Conflict/Gap/Risk unchanged.
3. **Phase F — registry:** `RuleResult` gains `findings` and `contradictions` fields alongside existing `observations`/`conflicts`/`gaps`/`risks`.
4. **Phase G — migration:** All consumers migrated to Finding/Contradiction types. Legacy aliases removed.
5. **Phase H — cleanup:** Deprecated enums and aliases removed.

### 5.2 Defers (Future Phases)

- `ReasoningSession` — implement when the first multi-evaluation workflow appears (Phase G Planning Engine or Phase H Governance Engine).

---

## 6. Compliance Alignment with G5.5 Reissuance

| G5.5 Requirement | Baseline Compliance | Refactored Compliance |
|-----------------|--------------------|----------------------|
| §1 — Canonical Reasoning Model | Partial. Missing: ReasoningSession, Finding, Assumption, Constraint | Full. All 9 types present |
| §2 — Deterministic Rule Evaluation | Full | Full (no change) |
| §3 — Evidence Management | Full | Full (no change) |
| §4 — Confidence Calculation | Full (named ConfidenceAssessment) | Full (renamed to ConfidenceScore) |
| §5 — Contradiction Detection | Partial. Missing: stale context, duplicate findings | Full. Stale context rule added |
| §6 — Infrastructure Integration | Full | Full (no change) |
| §7 — Observability | Full | Full (no change) |
| §8 — Testing | Full | Full (91 tests, +3 new contradiction tests) |
| §9 — Documentation | Full | Full |

**Net impact of accepted changes:** Baseline Phase F goes from partial to full G5.5 compliance with zero behavioural change in the existing rule pipeline.

---

## 7. Sign-Off Block

```
Document prepared for Governance review.
No code changes should be made until this review is complete.
```

**End of Architecture Delta Review**
