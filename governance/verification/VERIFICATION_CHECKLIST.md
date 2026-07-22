# Verification Checklist

**Purpose:** Standard verification checklist for all engines and phases. Engine-specific checklists extend this document.

**Instructions:** For each item, mark ✅ (pass), ❌ (fail), or ⬜ (not applicable). Provide evidence for each pass/fail. An implementation is not approved until all applicable items pass.

---

## 1. Constitutional Compliance

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1.1 | Layer responsibility is correct — engine does not perform another layer's work | | |
| 1.2 | Governance check exists before any execution action | | |
| 1.3 | No credential leakage across layer boundaries | | |
| 1.4 | Knowledge mutations follow immutable pattern (versioned, not overwritten) | | |
| 1.5 | All decisions include evidence chain (Decision + Confidence + Evidence + Explanation) | | |
| 1.6 | AI Proposes, Humans Dispose — REVIEW severity decisions require human approval | | |
| 1.7 | No business logic in configuration, environment variables, or hardcoded constants | | |

---

## 2. Scope Integrity

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 2.1 | Repository is clean except for approved changes | | |
| 2.2 | No undocumented dependencies introduced | | |
| 2.3 | Scope exactly matches the approved directive or engine spec | | |
| 2.4 | No scope creep beyond authorized changes | | |

---

## 3. Test Coverage

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 3.1 | All state transitions have unit tests | | |
| 3.2 | All error paths have unit tests | | |
| 3.3 | Integration tests pass with real or verified-mock dependencies | | |
| 3.4 | No test collection errors in the affected module | | |
| 3.5 | No tests that always pass (assert meaningful conditions) | | |
| 3.6 | Test suite is runnable without external dependencies (DB, network) | | |

---

## 4. Security

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 4.1 | No eval() or exec() patterns without documented security review | | |
| 4.2 | Input validation on all public interfaces | | |
| 4.3 | Output sanitization where applicable | | |
| 4.4 | No hardcoded secrets, tokens, or credentials | | |
| 4.5 | Tenant isolation verified — no cross-tenant data leakage | | |
| 4.6 | Rate limiting applied to external-facing endpoints | | |

---

## 5. Backward Compatibility

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 5.1 | Backward compatibility verified where applicable | | |
| 5.2 | Existing interfaces unchanged unless explicitly authorized | | |
| 5.3 | Deprecation notices in place for any removed interfaces | | |

---

## 6. Documentation

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 6.1 | Engine spec is up to date with implementation | | |
| 6.2 | ADR filed for any architecture-adjacent decisions | | |
| 6.3 | Architecture documents cross-referenced correctly | | |
| 6.4 | Public API documented (if applicable) | | |
| 6.5 | Error states documented | | |

---

## 7. Code Quality

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 7.1 | No scope creep — changes are limited to the approved scope | | |
| 7.2 | No drive-by refactoring of unrelated code | | |
| 7.3 | Project coding conventions followed | | |
| 7.4 | Imports and dependencies are minimal and justified | | |
| 7.5 | No circular dependencies introduced | | |

---

## 8. Integration

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 8.1 | Phase 4 (Privacy) eligibility gates integrated where applicable | | |
| 8.2 | Phase 10 (Context Fusion) workspace context consumed where applicable | | |
| 8.3 | Phase 14C (Inference Control) routing integrated where applicable | | |
| 8.4 | Event Bus events defined (if applicable) | | |
| 8.5 | Timeline Engine events defined (if applicable) | | |
| 8.6 | Workflow Engine definitions affected (if any) | | |

---

## 9. Performance

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 9.1 | Latency within budget (specified in engine spec) | | |
| 9.2 | Memory within budget (specified in engine spec) | | |
| 9.3 | Resource usage under load meets requirements | | |
| 9.4 | Performance impact measured where applicable | | |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineer | | | |
| Reviewer | | | |
| Chief Software Architect | | | |

---

## References

- [SHUNYA_ENGINEERING_CONSTITUTION.md](../SHUNYA_ENGINEERING_CONSTITUTION.md) — Articles 1-9
- [SHUNYA_GOVERNANCE_MODEL.md](../SHUNYA_GOVERNANCE_MODEL.md) — Governance workflow
- [ENGINE_SPEC_TEMPLATE.md](../engine_specs/ENGINE_SPEC_TEMPLATE.md) — Engine specification template
- [ADR_TEMPLATE.md](../adr/ADR_TEMPLATE.md) — ADR template
- [GOVERNANCE_CHANGELOG.md](../GOVERNANCE_CHANGELOG.md) — Governance change history