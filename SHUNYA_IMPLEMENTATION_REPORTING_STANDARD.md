# SHUNYA Implementation Reporting Standard

**Authority:** Governance Addendum G5.1-A
**Date:** 2026-07-18
**Status:** Active — mandatory for all future phases
**Scope:** All phase implementation reports (Phase C onward)

---

## 1. Governance Authority

### 1.1 Phase Completion Protocol

Every implementation phase shall conclude with a three-part confirmation:

```
Implementation Complete
Verification Complete
Awaiting Governance Review
```

Engineering agents shall never state or imply that a subsequent phase is authorized to begin. Only Governance may authorize subsequent phases. The phrase "Phase X is authorized to begin" is prohibited.

### 1.2 Report Sign-Off

Every implementation report shall end with the following block:

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Implementation Complete                                            ║
║  Verification Complete                                               ║
║  Awaiting Governance Review                                          ║
║                                                                      ║
║  No further implementation work is authorized until                  ║
║  governance approval is received.                                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 2. Coverage Reporting

### 2.1 Module-Level Coverage Table

Overall coverage percentages alone are insufficient. Every report shall include a module-level coverage table with the following columns:

| Column | Description |
|--------|-------------|
| Module | Module path relative to project root |
| Lines | Total executable statements |
| Coverage % | Percentage of statements covered |
| Critical Behaviours Tested | What the covered tests exercise |
| Remaining Untested Behaviours | What is not covered and why |

### 2.2 Table Format

```
| Module | Lines | Coverage % | Critical Behaviours Tested | Remaining Untested Behaviours |
|--------|-------|-----------|---------------------------|-------------------------------|
| path/to/module.py | 100 | 85% | Core logic, error paths, edge cases X, Y, Z | Config path A (low risk), fallback B (requires external dep) |
```

### 2.3 Failure to Meet Target

If any module falls below the 90% coverage target, the report shall document:
- Which specific behaviours are uncovered
- The risk classification of each uncovered behaviour
- A plan for how coverage will be achieved in a future phase

---

## 3. Architecture Compliance Declaration

### 3.1 Required Sections

Every implementation report shall include an explicit **Architecture Compliance** section containing:

| Item | Required? |
|------|-----------|
| Files created | Yes |
| Files modified | Yes |
| Files deleted | Yes |
| Any modifications outside the authorised scope | Yes |
| Justification for every out-of-scope modification | If applicable |

### 3.2 Declaration Format

If no scope violations exist:

```
## Architecture Compliance

**Files created:** (list)
**Files modified:** (list)
**Files deleted:** (list)

**Out-of-scope modifications:** None

No modifications outside the authorised scope.
```

If scope violations exist, each violation must be documented with:
- What was changed
- Why it was necessary
- Whether it is a divergence per Engineering Constitution Article 8
- Whether it requires an ADR or escalation

---

## 4. Technical Debt Register

### 4.1 Register Requirements

Every implementation report shall include a Technical Debt Register with the following columns:

| Column | Description |
|--------|-------------|
| Identifier | Unique ID (TD-PHASE-NNN) |
| Description | What was deferred |
| Reason for Deferral | Why it was not addressed now |
| Risk | Low / Medium / High |
| Recommended Phase | Which phase should resolve it |

### 4.2 Declaration Format

If no intentional technical debt exists:

```
## Technical Debt Register

No intentional technical debt introduced.
```

If debt exists, list each item in the table format.

---

## 5. Critical Path Verification

### 5.1 Matrix Requirements

Every report shall include a Critical Path Verification matrix identifying every mission-critical capability implemented during the phase.

### 5.2 Matrix Format

| Capability | Result | Evidence |
|------------|--------|----------|
| (e.g. Event Bus publish/deliver) | PASS | Test: test_publish_delivers_to_subscriber |
| (e.g. Credential Store access control) | PASS | Test: test_resolve_access_denied |

### 5.3 Governance Gate

This verification is mandatory for governance approval. Every capability must be marked PASS. Any FAIL must be documented with:
- Why it failed
- Whether it blocks the phase
- Remediation plan

---

## 6. Performance Baseline

### 6.1 Baseline Requirements

Every implementation report shall establish measurable baseline metrics for the components implemented during the phase.

### 6.2 Baseline Dimensions

| Dimension | Unit | Description |
|-----------|------|-------------|
| Latency | ms | p50 and p99 for primary operations |
| Throughput | ops/sec | Maximum sustained operations per second |
| Memory usage | MB | Steady-state and peak memory |
| CPU utilisation | % | CPU time per operation |
| Resource consumption | varies | Disk I/O, network, DB connections |

### 6.3 Baseline Format

| Component | Operation | Latency (p50) | Latency (p99) | Throughput | Memory | Notes |
|-----------|-----------|---------------|---------------|------------|--------|-------|
| Event Bus | publish + deliver | 0.1ms | 0.5ms | 10,000/s | 2MB | Single consumer, in-process |
| Credential Store | resolve | 0.05ms | 0.2ms | 20,000/s | 1MB | In-memory provider |

### 6.4 Regression Detection

Future phases shall compare their performance against these baselines. Any regression exceeding 20% in any dimension must be documented and justified.

---

## 7. Timeout Classification

### 7.1 Classification Requirements

Any timeout, interrupted execution, infrastructure failure, or environmental issue encountered during implementation or verification shall be explicitly classified.

### 7.2 Classification Format

| Field | Description |
|-------|-------------|
| Type | Timeout / Infrastructure failure / Environmental issue / Interrupted execution |
| Cause | Root cause description |
| Functional impact | What functionality was affected (if any) |
| Resolution | How the issue was resolved |
| Correctness affected? | Yes / No — whether implementation correctness was affected |

### 7.3 Governance Note

Governance must never infer whether a timeout represents an implementation defect. The report shall explicitly state whether the timeout affected correctness.

### 7.4 Declaration Format

If no timeouts occurred:

```
## Timeout Classification

No timeouts, interrupted executions, infrastructure failures, or environmental issues encountered during implementation or verification.
```

---

## 8. Report Template Compliance

### 8.1 Mandatory Sections

All future implementation reports shall begin with a **Governance Compliance Checklist** that summarises compliance with all governance requirements and links each item to the evidence section within the report.

#### Checklist Format

```
## Governance Compliance Checklist

| Requirement | Compliant? | Evidence Section |
|-------------|------------|------------------|
| Phase completion protocol followed | ✅ / ❌ | §1 Executive Summary |
| Module-level coverage reported | ✅ / ❌ | §6 Module-Level Coverage |
| Architecture compliance declared | ✅ / ❌ | §3 Architecture Compliance |
| Technical debt registered | ✅ / ❌ | §4 Technical Debt Register |
| Critical path verified | ✅ / ❌ | §7 Critical Path Verification |
| Performance baseline established | ✅ / ❌ | §8 Performance Baseline |
| Timeouts classified | ✅ / ❌ | §9 Timeout Classification |
| No out-of-scope modifications | ✅ / ❌ / N/A | §3 Architecture Compliance |
| No self-authorisation of next phase | ✅ / ❌ | §14 Sign-Off Block |
```

This checklist shall appear as the first content section after the report header (immediately before the Executive Summary). Every compliance item must be traceable to the section that contains the evidence.

### 8.2 Mandatory Sections

All future implementation reports shall include these sections in order:

| # | Section | Authority |
|---|---------|-----------|
| 0 | Governance Compliance Checklist | G5.1-A |
| 1 | Executive Summary | G5.1-A |
| 2 | Files Created / Modified / Deleted | G5.1-A §3 |
| 3 | Architecture Compliance Declaration | G5.1-A §3 |
| 4 | Technical Debt Register | G5.1-A §4 |
| 5 | Test Results | G5.1-A |
| 6 | Module-Level Coverage Table | G5.1-A §2 |
| 7 | Critical Path Verification Matrix | G5.1-A §5 |
| 8 | Performance Baseline | G5.1-A §6 |
| 9 | Timeout Classification | G5.1-A §7 |
| 10 | Concurrency Results | G5.1-A |
| 11 | Security Review | G5.1-A |
| 12 | Known Limitations | G5.1-A |
| 13 | Dashboard Updates | G5.1-A |
| 14 | Sign-Off Block | G5.1-A §1 |

---

## 9. Backward Compatibility

This standard applies to all future implementation reports unless superseded by a later Governance Directive. Phases A and B are already approved and their reports are not affected by this addendum.

---

*End of SHUNYA_IMPLEMENTATION_REPORTING_STANDARD.md*

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Governance Addendum G5.1-A implemented.                            ║
║  Awaiting further governance authorization.                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```