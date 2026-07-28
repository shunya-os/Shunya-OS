# Engineering Execution System

**Phase 16 — SHUNYA OS**
**Classification: Engineering Operating Manual**
**Status: PROPOSED**
**Version: 1.0**

---

## Preamble

### Authority

This document defines the Engineering Execution System for SHUNYA OS. It is the permanent operating manual for every engineer. It governs execution. It does NOT introduce architecture. If implementation exposes a missing architectural concept, raise an Architecture Amendment Request instead of modifying architecture.

### Scope

This document governs all engineering work on SHUNYA OS. It applies to:

- All engineering epics defined in the Implementation Master Plan
- All code changes to the SHUNYA OS codebase
- All tests, documentation, and releases
- Every engineer, reviewer, and maintainer

### Reference documents

| Document | How it is used |
|----------|----------------|
| IMPLEMENTATION_MASTER_PLAN.md | Defines the epics, milestones, and sequencing this system executes |
| ARCHITECTURE_GOVERNANCE_FRAMEWORK.md | Defines the governance rules this system enforces |
| All architecture documents (D01–D08) | Defines the architecture that implementations must conform to |

---

## SECTION 1 — Engineering Lifecycle

### 1.1 Complete lifecycle

```
EPIC (strategic capability)
  ↓
FEATURE (user-visible capability within an epic)
  ↓
TASK (atomic unit of work)
  ↓
IMPLEMENTATION (code + tests + docs)
  ↓
TESTING (all test levels pass)
  ↓
VERIFICATION (architecture conformance, invariant tests, review)
  ↓
MERGE (into target branch)
  ↓
RELEASE (deployed to environment)
  ↓
MAINTENANCE (bug fixes, technical debt, monitoring)
```

### 1.2 Lifecycle rules

1. Every epic must be defined in the Implementation Master Plan before work begins.
2. Every feature must trace to exactly one epic.
3. Every task must trace to exactly one feature.
4. Implementation cannot begin before the task's ready criteria are met.
5. Merge cannot happen before verification passes.
6. Release cannot happen before all verification gates pass.

---

## SECTION 2 — Epic Workflow

### 2.1 Ready criteria

An epic is ready to begin when:

| Criterion | Evidence | Verified by |
|-----------|----------|-------------|
| Architecture document is AUTHORITATIVE | Status field in document header | Architecture lead |
| All sections are complete | Section completeness check | Architecture lead |
| All invariants are defined | Invariant index | Governance lead |
| Ownership is assigned | Ownership matrix | Engineering lead |
| Dependencies are identified | Dependency graph | Engineering lead |
| Effort is estimated | Effort estimate in Master Plan | Engineering lead |
| Implementation sequence is defined | Phase plan | Engineering lead |

### 2.2 Implementation checklist

For every epic implementation:

```
[ ] All modules exist at specified paths
[ ] All interfaces match architecture specification
[ ] All constitutional types are used correctly
[ ] All applicable invariants are enforced
[ ] All cross-references to architecture documents are valid
[ ] All dependencies are satisfied
[ ] All public interfaces are documented
[ ] All error paths are handled
[ ] All configuration is externalized
[ ] All tests are written (unit + integration + invariant)
```

### 2.3 Verification checklist

```
[ ] Architecture conformance verified
[ ] Code review completed (minimum 1 reviewer)
[ ] Static analysis passes (linter, type checker)
[ ] All unit tests pass (≥ 90% coverage on new code)
[ ] All integration tests pass
[ ] All invariant tests pass
[ ] Regression tests pass (no new failures)
[ ] Performance validation passes (latency targets met)
[ ] Documentation review completed
```

### 2.4 Completion criteria

An epic is complete when:

1. All modules are implemented and merged
2. All tests pass
3. All invariants are tested
4. Architecture conformance is verified
5. Technical debt is documented
6. An implementation report is produced

### 2.5 Definition of Done

A task is done when:

| Criterion | Minimum | Target |
|-----------|---------|--------|
| Code written | All specified interfaces implemented | Including error paths and edge cases |
| Tests written | Unit tests for all public methods | Integration + invariant tests |
| Tests passing | 100% of new tests pass | No regressions in existing tests |
| Code reviewed | 1 reviewer | 2 reviewers for cross-cutting changes |
| Architecture conformance | Architecture document + sections identified | Invariant IDs also identified |
| Documentation | Docstrings on all public interfaces | Architecture trace in module header |

---

## SECTION 3 — Task Decomposition

### 3.1 Epic decomposition pattern

Every epic decomposes into:

```
Epic
  ├── Models module (data structures, types, enums)
  ├── Engine module (business logic, algorithms)
  ├── Interface module (public API, service layer)
  ├── Configuration (defaults, environment variables)
  ├── Unit tests (per-module)
  ├── Integration tests (cross-module)
  └── Invariant tests (constitutional rules)
```

### 3.2 Canonical module structure

Every epic follows the canonical module pattern:

```
app/<epic_name>/
  __init__.py          → Public API exports, __all__, get/reset singletons
  models.py            → All data structures, dataclasses, enums
  engine.py            → All business logic, sub-engines, facade class
  config.py            → Configuration defaults, environment variables

tests/<epic_name>/
  __init__.py          → Test package marker
  test_models.py       → Unit tests for data structures
  test_engine.py       → Unit tests for business logic
  test_integration.py  → Integration tests (cross-module)
  test_invariants.py   → Constitutional invariant tests
```

### 3.3 Task types

| Task type | Definition | Estimated size | Review requirements |
|-----------|------------|----------------|---------------------|
| **Models** | Data structures, types, enums | 50–200 LOC | 1 reviewer |
| **Engine** | Business logic, algorithms | 200–800 LOC | 1 reviewer (2 for cross-cutting) |
| **Interface** | Public API, service layer | 50–200 LOC | 1 reviewer |
| **Configuration** | Defaults, env vars | 10–50 LOC | 1 reviewer |
| **Tests** | Unit, integration, invariant | 200–1000 LOC | 1 reviewer |
| **Documentation** | Docstrings, architecture references | 50–200 LOC | 1 reviewer |
| **Bug fix** | Defect correction | 10–200 LOC | 1 reviewer |

### 3.4 Task identification

Every task is identified by:

```
<EPIC_ID>-<TYPE>-<NNN>
```

Examples: `E-001-MOD-001` (Ontology Engine, Models, task 1), `E-003-ENG-005` (Knowledge Graph, Engine, task 5).

---

## SECTION 4 — Implementation Gates

### 4.1 Gate pipeline

```
┌─────────────┐
│  Gate 1     │  Architecture Conformance
│  (Manual)   │  Verify implementation matches architecture
└──────┬──────┘
       │
┌──────▼──────┐
│  Gate 2     │  Code Review
│  (Manual)   │  Minimum 1 reviewer. 2 for cross-cutting changes.
└──────┬──────┘
       │
┌──────▼──────┐
│  Gate 3     │  Static Validation
│  (Automated)│  Linter, type checker, import validation
└──────┬──────┘
       │
┌──────▼──────┐
│  Gate 4     │  Unit Tests
│  (Automated)│  All new + existing unit tests pass
└──────┬──────┘
       │
┌──────▼──────┐
│  Gate 5     │  Integration Tests
│  (Automated)│  Cross-module interaction tests pass
└──────┬──────┘
       │
┌──────▼──────┐
│  Gate 6     │  Regression Tests
│  (Automated)│  No new test failures. Existing failure count unchanged.
└──────┬──────┘
       │
┌──────▼──────┐
│  Gate 7     │  Performance Validation
│  (Automated)│  Latency targets met. No regressions.
└──────┬──────┘
       │
┌──────▼──────┐
│  Gate 8     │  Documentation Review
│  (Manual)   │  Docstrings, traceability, changelog
└──────┬──────┘
       │
       ▼
    MERGE
```

### 4.2 Gate failure behaviour

| Gate | Failure | Action |
|------|---------|--------|
| Gate 1 — Conformance | Implementation does not match architecture | Amend implementation or raise Architecture Amendment Request |
| Gate 2 — Review | Reviewer rejects | Address comments, re-request review |
| Gate 3 — Static | Linter/type error | Fix error, re-run |
| Gate 4 — Unit | Test failure | Fix code or fix test, re-run |
| Gate 5 — Integration | Test failure | Fix integration issue, re-run |
| Gate 6 — Regression | New failure | Fix regression before merge |
| Gate 7 — Performance | Target not met | Optimize or document trade-off |
| Gate 8 — Documentation | Missing documentation | Add documentation before merge |

### 4.3 Gate automation

| Gate | Automated? | Tool |
|------|------------|------|
| Architecture Conformance | Partial (manual review + automated reference check) | Governance checker |
| Code Review | No (human) | Pull request review |
| Static Validation | Yes | Ruff (linter), mypy (types) |
| Unit Tests | Yes | pytest |
| Integration Tests | Yes | pytest |
| Regression Tests | Yes | pytest (baseline comparison) |
| Performance Validation | Yes | pytest-benchmark |
| Documentation Review | No (human) | Pull request review |

---

## SECTION 5 — Architecture Conformance

### 5.1 Pull request template

Every pull request must include:

```markdown
## Architecture Conformance

**Referenced Architecture Document:** [document name]
**Referenced Sections:** [§N.M, §N.M, ...]
**Affected Objects:** [type names]
**Affected Invariants:** [O-NNN, I-NNN, AI-NNN]
**Affected Tests:** [test file paths]
**Architecture Amendment Required?** [Yes/No]

## Description

[What does this change do?]

## Test Results

[Summary of test results]

## Checklist

- [ ] Architecture conformance verified
- [ ] Code reviewed
- [ ] Static validation passes
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Invariant tests pass
- [ ] Regression tests pass
- [ ] Performance targets met
- [ ] Documentation complete
```

### 5.2 Conformance verification

The architecture lead verifies:

1. The referenced architecture document exists and is AUTHORITATIVE
2. The referenced sections exist in the document
3. The affected objects are defined in the architecture
4. The affected invariants exist in the consolidated index
5. All affected invariants are tested
6. No architecture amendment is actually required (if "No" is checked)

### 5.3 Architecture amendment request

If an implementation exposes a missing architectural concept:

1. Close the pull request without merging
2. Create an Architecture Amendment Request as an ADR (see ARCHITECTURE_GOVERNANCE_FRAMEWORK.md §5)
3. Submit the ADR for review
4. Wait for the ADR to be ACCEPTED before proceeding
5. Update the architecture document
6. Re-open the pull request with updated conformance

---

## SECTION 6 — Testing Workflow

### 6.1 Test hierarchy

```
┌──────────────────────────────────────────────────────────────────────┐
│  Acceptance Tests (end-to-end system behaviour)                      │
│  Frequency: Per release. Owner: QA.                                  │
├──────────────────────────────────────────────────────────────────────┤
│  System Tests (end-to-end flows across all subsystems)               │
│  Frequency: Per release. Owner: Engineering.                         │
├──────────────────────────────────────────────────────────────────────┤
│  Integration Tests (cross-subsystem interactions)                    │
│  Frequency: Per merge. Owner: Engineering.                           │
├──────────────────────────────────────────────────────────────────────┤
│  Component Tests (single epic's public interface)                    │
│  Frequency: Per merge. Owner: Engineering.                           │
├──────────────────────────────────────────────────────────────────────┤
│  Unit Tests (individual functions, classes, methods)                 │
│  Frequency: Per commit. Owner: Developer.                            │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 Test levels

| Level | What it verifies | Per test | Run frequency | Time budget |
|-------|-----------------|----------|---------------|-------------|
| **Unit** | Single function, class, method | < 100ms | Every commit | < 5 min (full suite) |
| **Component** | Single epic's public interfaces | < 500ms | Every merge | < 10 min |
| **Integration** | Cross-subsystem interactions | < 2s | Every merge | < 30 min |
| **System** | End-to-end flows | < 30s | Every release | < 2 hours |
| **Acceptance** | System behaviour against requirements | < 60s | Every release | < 4 hours |
| **Regression** | No regressions in existing behaviour | Baseline comparison | Every merge | < 30 min |
| **Performance** | Latency targets, throughput | < 30s | Every release | < 1 hour |
| **Failure recovery** | Degraded modes, rollback | < 60s | Every release | < 2 hours |

### 6.3 Test naming convention

```
test_<unit>_<behaviour>_<scenario>
```

Examples: `test_identity_never_changes`, `test_execution_rollback_reverses_steps`, `test_evidence_append_only`.

### 6.4 Test data

- Unit tests use synthetic data (factories, fixtures)
- Integration tests use in-memory databases
- System tests use a test database with seeded data
- Performance tests use generated data at scale
- Acceptance tests use production-like data (anonymized)

---

## SECTION 7 — Technical Debt

### 7.1 Debt classification

| Type | Definition | Tracking | Resolution |
|------|------------|----------|------------|
| **Intentional** | Known trade-off accepted for speed | Technical Debt Register in dashboard | Scheduled resolution in future sprint |
| **Unintentional** | Discovered during review or testing | Bug report | Fix before merge if gate-blocking; schedule otherwise |
| **Temporary** | Shortcut that will be resolved in a known future phase | Technical Debt Register with resolution phase | Resolve in specified phase |
| **Permanent** | Accepted architectural limitation that will never be resolved | Architecture Decision Record | Document as ADR |

### 7.2 Debt tracking

Every technical debt item is tracked with:

```markdown
| ID | Description | Type | Owner | Priority | Resolution plan | Created | Target resolution |
|----|-------------|------|-------|----------|----------------|---------|-------------------|
| TD-001 | ... | Intentional | ... | Medium | Phase 5 | 2026-07-22 | 2026-09-01 |
```

### 7.3 Debt priorities

| Priority | Definition | Resolution timeline |
|----------|------------|---------------------|
| **Critical** | Blocks functionality or violates architecture | Current sprint |
| **High** | Impacts quality or performance | Next sprint |
| **Medium** | Reduces maintainability | Within 3 sprints |
| **Low** | Cosmetic or non-functional | When convenient |

---

## SECTION 8 — Progress Reporting

### 8.1 Standard report format

Every report contains:

```
# <Report Type> — <Date>

## Epic Progress
| Epic | Status | % Complete | Sprint | Blockers |
|------|--------|------------|--------|----------|

## Sprint Progress
| Task | Status | Owner | Remaining | Blocked by |
|------|--------|-------|-----------|------------|

## Milestone Progress
| Milestone | Target | Current | % | ETA |
|-----------|--------|---------|---|-----|

## Coverage
| Metric | Target | Current | Trend |
|--------|--------|---------|-------|

## Risks
| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|

## Blocked Items
| Item | Blocked by | Since | Action |
|------|------------|-------|--------|

## Velocity
| Sprint | Planned | Completed | Velocity |
|--------|---------|-----------|----------|
```

### 8.2 Report frequency

| Report type | Frequency | Audience |
|-------------|-----------|----------|
| Daily standup | Daily | Engineering team |
| Sprint review | End of sprint | Engineering + stakeholders |
| Milestone review | End of milestone | Engineering + governance |
| Release review | Per release | All stakeholders |

---

## SECTION 9 — Release Governance

### 9.1 Release phases

| Phase | Purpose | Entry criteria | Exit criteria | Rollback criteria |
|-------|---------|---------------|---------------|-------------------|
| **Alpha** | Internal validation | M1–M2 complete. Foundation + Graph implemented. | All unit + integration tests pass. Architecture conformance verified. | Any failing test. Any architecture violation. |
| **Beta** | Invited tester validation | M3–M4 complete. Runtime + Adaptation implemented. | Alpha exit criteria + system tests pass + performance targets met. | Critical bug. Performance regression > 20%. |
| **Preview** | Limited production | M5 complete. Capabilities implemented. | Beta exit criteria + acceptance tests pass + failure recovery tests pass. | Data loss. Security vulnerability. Invariant violation. |
| **GA** | Full production | M6–M7 complete. Surface + Governance implemented. | Preview exit criteria + documentation complete + technical debt documented. | Any of the above. |

### 9.2 Release process

```
Feature complete → Freeze → Test → Fix → Verify → Release → Monitor
```

| Stage | Duration | Activities |
|-------|----------|------------|
| **Freeze** | 24 hours | No new features. Bug fixes only. |
| **Test** | 48 hours | Full test suite. Performance tests. Failure recovery tests. |
| **Fix** | Until resolved | Address all blocking issues. |
| **Verify** | 24 hours | Re-run tests. Architecture conformance check. |
| **Release** | 1 hour | Deploy to target environment. Smoke tests. |
| **Monitor** | 72 hours | Watch metrics, logs, alerts. Rollback if needed. |

### 9.3 Rollback

A rollback is triggered when:

1. A critical bug is discovered post-release
2. Performance regresses beyond 20% of target
3. A constitutional invariant is violated
4. Data loss or corruption is detected

Rollback restores the previous version. Rollback is always available within the rollback window defined for the release phase.

---

## SECTION 10 — Engineering Dashboard

### 10.1 Dashboard widgets

| Widget | Content | Data source | Refresh |
|--------|---------|-------------|---------|
| **Current Epic** | Active epic name, status, % complete | Epic tracking | Daily |
| **Current Sprint** | Sprint number, start/end dates, tasks | Sprint tracking | Daily |
| **Implementation %** | % of epic modules implemented | Git history | Per commit |
| **Architecture Coverage** | % of architecture elements with implementation | Traceability matrix | Weekly |
| **Test Coverage** | Line coverage % per module | Coverage reports | Per merge |
| **Technical Debt** | Debt item count by priority | Debt register | Per sprint |
| **Open Risks** | Risk count by severity | Risk register | Per sprint |
| **Blocked Work** | Blocked task count and reason | Sprint board | Daily |

### 10.2 Dashboard display

The dashboard is displayed:

- On the engineering team's monitor (always visible)
- In the Founder Workspace as a projection (see ARCHITECTURE_GOVERNANCE_FRAMEWORK.md §13)
- In the daily standup channel

---

## SECTION 11 — Quality Metrics

### 11.1 Metrics definitions

| Metric | Definition | Target | Measurement |
|--------|------------|--------|-------------|
| **Architecture Conformance** | % of PRs that pass architecture conformance gate | 100% | Per PR |
| **Defect Density** | Defects per 1000 LOC | < 2 | Per release |
| **Regression Rate** | % of previously passing tests that fail | < 1% | Per merge |
| **Build Stability** | % of builds that pass all gates | > 95% | Per sprint |
| **Test Pass Rate** | % of tests passing | 100% | Per commit |
| **Documentation Coverage** | % of public interfaces with docstrings | 100% | Per merge |
| **Code Coverage** | Line coverage | ≥ 90% (new code), ≥ 70% (overall) | Per merge |
| **Invariant Coverage** | % of invariants with at least one test | 100% | Per release |
| **Technical Debt Ratio** | Debt resolution rate | > 80% of debt resolved within target | Per sprint |

### 11.2 Metric collection

| Metric | Collected by | Reported in | Frequency |
|--------|-------------|-------------|-----------|
| Architecture Conformance | Governance checker | PR review | Per PR |
| Defect Density | Bug tracker + LOC counter | Release report | Per release |
| Regression Rate | pytest baseline comparison | CI pipeline | Per merge |
| Build Stability | CI system | Engineering dashboard | Per sprint |
| Test Pass Rate | pytest | CI pipeline | Per commit |
| Documentation Coverage | Documentation linter | PR review | Per merge |
| Code Coverage | pytest-cov | Engineering dashboard | Per merge |
| Invariant Coverage | Governance checker + test scan | Release report | Per release |
| Technical Debt Ratio | Debt register | Engineering dashboard | Per sprint |

---

## SECTION 12 — Operational Cadence

### 12.1 Cadence structure

```
Daily (standup)
  ↓
Weekly (sprint cycle)
  ↓
Bi-weekly (milestone checkpoint)
  ↓
Monthly (release)
  ↓
Quarterly (architecture review)
```

### 12.2 Daily cadence

| Time | Activity | Participants | Duration |
|------|----------|--------------|----------|
| 09:30 | Standup | Engineering team | 15 min |
| — | Implementation work | Engineers | Rest of day |
| — | Automated CI runs | CI system | Continuous |

Standup format:

```
1. What did I complete yesterday?
2. What am I working on today?
3. What is blocked?
4. Any architecture questions?
```

### 12.3 Sprint cadence

| Day | Activity | Participants | Duration |
|-----|----------|--------------|----------|
| Day 1 | Sprint planning | Engineering team | 2 hours |
| Days 2–N | Implementation | Engineers | — |
| Day N-1 | Sprint review | Engineering + stakeholders | 1 hour |
| Day N | Retrospective | Engineering team | 1 hour |

Sprint length: 2 weeks.

### 12.4 Milestone cadence

| Activity | Frequency | Participants | Duration |
|----------|-----------|--------------|----------|
| Milestone planning | Before milestone | Engineering + architecture leads | 4 hours |
| Mid-milestone check | Midpoint | Engineering team | 1 hour |
| Milestone review | End of milestone | All stakeholders | 2 hours |

Milestone length: 2–3 sprints (4–6 weeks).

### 12.5 Release cadence

| Activity | Frequency | Participants | Duration |
|----------|-----------|--------------|----------|
| Release planning | Before release | Engineering + governance | 2 hours |
| Release testing | During freeze | QA + engineering | 2–3 days |
| Release deployment | Release day | DevOps + engineering | 1 hour |
| Release monitoring | Post-release | Engineering | 72 hours |

Release frequency: Every 1–2 milestones (4–8 weeks).

### 12.6 Quarterly architecture review

| Activity | Frequency | Participants | Duration |
|----------|-----------|--------------|----------|
| Architecture conformance audit | Quarterly | Architecture lead | 1 day |
| Invariant compliance scan | Quarterly | Governance lead | 1 day |
| Architecture health assessment | Quarterly | Architecture + governance | 2 hours |
| Architecture amendment review | Quarterly | All stakeholders | 4 hours |
| Report production | Quarterly | Architecture lead | 1 day |

---

## Appendix A: Engineering Workflow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        ENGINEERING EXECUTION SYSTEM                          │
│                                                                              │
│  EPIC                                                                        │
│  Ready criteria → Implementation checklist → Verification checklist          │
│    → Completion criteria → Definition of Done                                │
│       │                                                                      │
│       ▼                                                                      │
│  FEATURE                                                                     │
│  Architecture conformance → Code review → Static validation                  │
│    → Unit tests → Integration tests → Regression tests                       │
│    → Performance validation → Documentation review → MERGE                   │
│       │                                                                      │
│       ▼                                                                      │
│  RELEASE                                                                     │
│  Alpha → Beta → Preview → GA                                                │
│    Freeze → Test → Fix → Verify → Deploy → Monitor → Rollback if needed     │
│       │                                                                      │
│       ▼                                                                      │
│  MAINTENANCE                                                                 │
│  Bug fixes → Technical debt → Monitoring → Quarterly review                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Quick Reference

### Pull request checklist (abbreviated)

```
[ ] Architecture document + sections identified
[ ] Affected objects + invariants listed
[ ] All automated gates pass
[ ] Reviewed by minimum 1 engineer
[ ] Architecture amendment required? (if Yes, create ADR first)
```

### Daily standup format

```
1. Completed yesterday: [task IDs]
2. Working on today: [task IDs]
3. Blocked by: [item IDs or "None"]
4. Architecture questions: [questions or "None"]
```

### Task ID format

```
<EPIC_ID>-<TYPE>-<NNN>
E-001-MOD-001  → Ontology Engine, Models, task 1
E-003-ENG-005  → Knowledge Graph, Engine, task 5
E-013-TST-010  → Execution Engine, Tests, task 10
```

### Gate failure quick reference

| Gate fails | Action |
|------------|--------|
| Architecture conformance | Fix implementation OR raise ADR |
| Code review | Address reviewer comments |
| Static validation | Fix linter/type errors |
| Unit/integration/regression tests | Fix code or fix test |
| Performance | Optimize OR document trade-off |
| Documentation | Add missing docs |