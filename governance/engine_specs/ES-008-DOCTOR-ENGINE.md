# ES-008: Doctor Engine

**Status:** Draft
**Phase:** Phase 2
**Layer:** Doctor
**Author:** Chief Software Architect
**Date:** 2026-07-18
**Approver:** (filled on approval)

---

## Section 0 — Compounding Intelligence Position

### What Enters This Engine

- **Health data** — status, latency, error counts from every engine
- **Architecture document snapshots** — current vs baseline representations
- **Governance audit log** — compliance and policy evaluation history
- **Knowledge integrity reports** — checksum mismatches, version consistency
- **System configuration** — package versions, dependency declarations, deployment manifests

### What Leaves This Engine

- **DoctorReport** — structured check results with pass/fail/warning per check
- **Violation events** — architecture drift, compliance failure, integrity violation
- **Health summary** — aggregated health status across all engines

### What Intelligence Is Compounded

The Doctor Engine does **not** compound intelligence. It is a verification layer, not a compounding layer. It checks that the architecture has not drifted and that system integrity is maintained, but it does not improve the system's capabilities. Each check is independent of previous checks — a passing check today does not make tomorrow's check more likely to pass.

However, the Doctor Engine is critical to the compounding loop's **trust model**: without integrity verification, downstream engines cannot trust that their inputs are correct. Compounding intelligence built on corrupted data is worse than no compounding at all.

### Which Downstream Engines Depend Upon It

| Engine | Dependency | Criticality |
|--------|-----------|-------------|
| Observer Engine (ES-006) | Consumes health data for observation context | **Low** — observation does not require health data |
| Governance Engine (ES-001) | Consumes compliance reports for audit verification | **Low** — compliance is verified independently |
| Knowledge Engine (ES-002) | Knowledge Engine publishes `knowledge.integrity.violation` consumed by Doctor | **Low** — Doctor is the consumer, not the producer |

### What Fails If This Engine Becomes Unavailable

- **Architecture drift goes undetected** — implementation may diverge from the locked architecture without warning
- **Integrity violations are missed** — checksum mismatches, missing packages, broken dependencies may accumulate
- **Governance compliance is unverifiable** — no independent mechanism confirms governance policies are being enforced
- **Compounding trust erodes** — the system cannot prove it has not drifted

---

## 1. Objective

### Mission

The Doctor Engine verifies system integrity, checks architecture drift, validates package health, and confirms governance compliance. It is the architectural integrity checker — ensuring that the running system matches the locked architecture and that no component has silently diverged.

### Why It Exists

The SHUNYA Constitution (SHUNYA_ARCHITECTURE.md §5 — Doctor Layer) defines the Doctor Layer as an architectural integrity checker. The Engineering Constitution (Article 7 — Documentation Currency) requires that architecture documents match implementation. The Doctor Engine is the mechanism that enforces this — it checks that the system has not drifted, that required packages and governance policies exist, and that version compatibility is maintained.

Without the Doctor Engine, architecture drift can accumulate silently until the system no longer matches its specification. The compounding intelligence loop depends on a verifiably correct foundation — the Doctor Engine provides that verification.

### Architectural Responsibility

The Doctor Engine owns **integrity verification** within the Compounding Intelligence Architecture. It does not execute, govern, reason, learn, or observe — it inspects and reports.

Position in the architecture:

```
                    ┌─────────────┐
                    │   Doctor    │
                    │  Engine     │──────── Integrity checks → All engines
                    └─────────────┘
                           │
                    Reads health data from
                    all engines (observational)
                    │
                    ▼
              DoctorReport + Violation Events
```

---

## 2. Scope

### In Scope

- Verify system integrity — check that all required components are present and functional
- Check architecture drift — compare implementation against the locked architecture
- Validate package health — verify required packages, libraries, and dependencies exist at expected versions
- Confirm governance compliance — verify that governance policies are present and being enforced
- Aggregate health data from all engines and report overall system health
- Generate compliance reports for audit and governance verification
- Publish violation events when architecture drift, compliance failure, or integrity violation is detected
- Maintain a structured DoctorReport for every check cycle
- Run integrity checks on a configurable schedule (default: every 30 seconds — SHUNYA_SYSTEM_FLOW.md §11)

### Out of Scope

- **Never modify system state.** The Doctor Engine detects violations but does not fix them.
- **Never execute user actions.** The Doctor Engine does not send messages, create records, or call external APIs.
- **Never govern real-time decisions.** The Doctor Engine verifies governance compliance — it does not participate in individual governance decisions.
- **Never learn.** The Doctor Engine does not improve from past check results.
- **Never reason about causes.** The Doctor Engine reports what is wrong, not why.
- **Never monitor operational health.** The Doctor Engine verifies architecture integrity — operational health monitoring is the responsibility of the infrastructure/platform team.
- **Never perform self-healing.** The Doctor Engine reports violations for human or automated resolution — it does not fix them.

---

## 3. Dependencies

### Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| All engines | Input | Reads health and integrity data from every engine |
| Knowledge Engine (ES-002) | Input | Reads integrity data for knowledge facts (checksums, version consistency) |
| Governance Engine (ES-001) | Input | Reads audit log for compliance verification |
| Engine specifications | Reference | Compares implementation against specification-defined contracts |

### External Dependencies

- Filesystem access (read) — for checking package existence, version manifests, and file integrity
- Python import system — for verifying that required modules are importable
- Database connection (read) — for verifying schema and table presence

---

## 4. Inputs

### Input Contract

```
DoctorInput:
  check_type: string              — "integrity" | "drift" | "package_health" | "compliance"
  scope: string[]                 — List of engines or layers to check (or "all")
  baseline_snapshot: dict         — Expected state (package versions, document checksums, configuration)
  health_data: HealthReport[]     — Current health data from each engine
  governance_audit: AuditEntry[]  — Recent governance decisions (for compliance checks)
  timestamp: datetime             — When the check was initiated
```

### Input Sources

| Source | Type | Trigger |
|--------|------|---------|
| All engines | Health API (read) | On check schedule (every 30s) or on-demand |
| Knowledge Engine (ES-002) | Integrity API (read) | On knowledge integrity violation event |
| Governance Engine (ES-001) | Audit Log API (read) | On compliance check request |
| System configuration | Filesystem (read) | On startup and on configuration change |
| Package manager | System query | On package health check |

### Input Validation

| Field | Constraint | Default | Rejection |
|-------|-----------|---------|-----------|
| `check_type` | Must be one of: integrity, drift, package_health, compliance | None (required) | `INVALID_CHECK_TYPE` |
| `scope` | Must be non-empty when check_type is not "integrity" | ["all"] | Warning only |
| `baseline_snapshot` | Must be present for drift checks | None (required for drift) | `MISSING_BASELINE` |
| `health_data` | May be empty (no engines reporting) | [] | Warning only — degraded report |

---

## 5. Outputs

### Output Contract

```
DoctorReport:
  check_id: string               — Unique identifier for this check cycle
  timestamp: datetime            — When the check was performed
  check_type: string             — Type of check performed
  overall_status: string         — "pass" | "fail" | "degraded"
  checks: DoctorCheck[]
  passed: int                    — Count of passed checks
  failed: int                    — Count of failed checks
  warnings: int                  — Count of warnings

DoctorCheck:
  name: string                   — Check name (e.g., "architecture_drift.documentation_currency")
  status: string                 — "pass" | "fail" | "warning"
  detail: string                 — Human-readable result description
  evidence: string               — Supporting evidence (file path, checksum, version)
  timestamp: datetime            — When this check was performed

ViolationEvent:
  violation_id: string           — Unique violation identifier
  engine: string                 — Affected engine
  severity: string               — "critical" | "high" | "medium" | "low"
  category: string               — "architecture_drift" | "integrity" | "compliance" | "package_health"
  description: string            — Human-readable violation description
  evidence: string               — Supporting evidence reference
  detected_at: datetime          — When the violation was detected
```

### Output Destinations

| Destination | Consumer | Delivery Guarantee |
|-------------|----------|-------------------|
| Event Bus | All engines | At-least-once |
| Audit Log | Governance Engine | At-least-once |
| Alerting system | Operators | Best-effort |

### Output Guarantees

- **Determinism:** Same inputs always produce the same check results. No randomness.
- **Freshness:** Each check cycle produces a fresh report. No cached results.
- **Idempotency:** Publishing the same violation event twice produces the same effect.

---

## 6. State Machine

### States

```
Idle
 │
 │ [check_scheduled]
 ▼
Checking
 │
 ├──[all_pass]──→ Reporting
 │
 ├──[violation_detected]──→ Violation_Detected
 │                            │
 │                            └──[reported]──→ Reporting
 │
 └──[check_error]──→ Reporting
                        │
                        └──[report_published]──→ Idle
```

### State Definitions

| State | Meaning | Is Terminal? |
|-------|---------|-------------|
| Idle | Waiting for next check schedule or on-demand trigger | No |
| Checking | Performing integrity, drift, package, or compliance checks | No |
| Violation_Detected | One or more checks failed or produced warnings | No |
| Reporting | Assembling and publishing the DoctorReport | No |

### Transition Table

| From State | Event | Condition | To State | Action |
|------------|-------|-----------|----------|--------|
| Idle | check_scheduled | Timer or on-demand trigger | Checking | Begin check execution |
| Checking | all_pass | All checks pass | Reporting | Assemble report with pass status |
| Checking | violation_detected | Any check fails or warns | Violation_Detected | Log violation details |
| Checking | check_error | Error during check execution | Reporting | Assemble report with error status |
| Violation_Detected | reported | Violation event published | Reporting | Include violation in report |
| Reporting | report_published | DoctorReport delivered to Event Bus | Idle | Log completion |

---

## 7. Events

### Events Consumed

| Event | Source | Payload | Action Taken |
|-------|--------|---------|-------------|
| `knowledge.integrity.violation` | Knowledge Engine (ES-002) | `{fact_key, version, expected_checksum, actual_checksum}` | Flag as integrity violation in next check cycle |
| `governance.decision.logged` | Governance Engine (ES-001) | `{audit_id, verdict, policies_evaluated}` | Record for compliance verification |
| `doctor.check.requested` | Any engine or Operator | `{check_type, scope}` | Initiate on-demand check cycle |

### Events Produced

| Event | Destination | Payload | Trigger Condition |
|-------|-------------|---------|-------------------|
| `doctor.check.completed` | All engines, Event Bus | `{check_id, timestamp, overall_status, passed, failed, warnings}` | Check cycle completed |
| `doctor.violation.detected` | All engines, Alerting | `{violation_id, engine, severity, category, description, evidence}` | Any check fails or produces a warning |
| `doctor.health.summary` | All engines, Operator dashboard | `{timestamp, engine_health: {engine_name: status}, overall_health}` | At end of each health aggregation cycle |

---

## 8. Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Engine health data unavailable | Downstream engine not responding | Timeout on health API | Degraded report — missing engine health section | Return report with missing section flagged; retry on next cycle |
| Baseline snapshot missing | Configuration not loaded | Schema validation | Cannot perform drift check | Return warning; require baseline configuration |
| Filesystem read error | Permission denied, file not found | IOError | Check failure for affected paths | Log error; skip file check |
| Database connection failure | DB unavailable | Connection timeout | Cannot verify knowledge integrity | Return degraded report; retry on next cycle |
| Concurrent check conflict | Multiple check cycles overlapping | Lock contention | Serialize pending checks | Queue and execute sequentially |

---

## 9. Observability

### Logging

| Event | Log Level | Data | Privacy Constraint |
|-------|-----------|------|-------------------|
| Check cycle started | INFO | check_id, check_type, scope | None |
| Check passed | DEBUG | check_name, result | None |
| Check failed | WARN | check_name, detail, evidence | None |
| Violation detected | WARN | violation_id, severity, category, description | No personal data |
| Health summary published | INFO | overall_status, passed, failed, warnings | None |
| Engine health data unavailable | WARN | engine_name, error | None |
| Check error | ERROR | check_name, error_detail | No personal data |

### Tracing

- **Span: `doctor.check_cycle`** — Full check cycle lifecycle
  - Child span: `doctor.check_integrity` — Integrity verification phase
  - Child span: `doctor.check_drift` — Architecture drift detection phase
  - Child span: `doctor.check_packages` — Package health validation phase
  - Child span: `doctor.check_compliance` — Compliance verification phase
  - Child span: `doctor.aggregate_health` — Health data aggregation phase
- check_id propagated as a trace tag

### Alerting

| Condition | Severity | Threshold |
|-----------|----------|-----------|
| Any critical violation detected | Pager | Immediate |
| More than 3 failed checks per cycle | Pager | Per cycle |
| Engine health data unavailable for 3 consecutive cycles | Warning | Per engine |
| Any compliance violation | Warning | Per occurrence |

---

## 10. Metrics

| Metric | Type | Unit | Target | Measurement |
|--------|------|------|--------|-------------|
| `doctor.checks_total` | Counter | checks | N/A | Per cycle, by check_type |
| `doctor.passed_total` | Counter | checks | N/A | Per cycle |
| `doctor.failed_total` | Counter | checks | N/A | Per cycle, by check_name |
| `doctor.warnings_total` | Counter | warnings | N/A | Per cycle |
| `doctor.violations_total` | Counter | violations | N/A | Per severity and category |
| `doctor.latency_p50` | Histogram | ms | < 200ms | Per check cycle |
| `doctor.latency_p99` | Histogram | ms | < 1s | Per check cycle |
| `doctor.cycle_duration` | Histogram | ms | < 5s | Per cycle |

---

## 11. Rollback Strategy

### Rollback Triggers

- Doctor Engine produces false positive violations (incorrect drift detection)
- Doctor Engine misses real violations (false negatives)
- Performance degradation impacts other engines (excessive health polling)

### Rollback Procedure

1. **Disable check schedule:** Stop accepting new check triggers.
2. **Drain in-flight:** Allow current check cycle to complete.
3. **Restore previous check configuration:** Load the baseline snapshot and check policy from before the faulty deployment.
4. **Verify:** Run a manual check cycle against the restored version.
5. **Resume:** Re-enable the check schedule with the restored version.

### Rollback Limitations

- Violation events already published cannot be recalled. Downstream consumers must handle retraction.
- The baseline snapshot history is append-only. Previous snapshots remain in the audit log.

---

## 12. Migration Strategy (when applicable)

### Migration Type

Configuration migration — baseline snapshot definitions.

### Migration Steps

1. **Pre-migration validation:** Verify that the new baseline snapshot is valid and loadable.
2. **Dual-check (if applicable):** Run checks against both old and new baselines, log discrepancies.
3. **Cutover:** Switch from old baseline to new baseline atomically.
4. **Post-migration verification:** Run a full check cycle, confirm results match expected outcomes.

### Rollback During Migration

- Point-in-time: The baseline snapshot before migration.
- Data consistency: All historical DoctorReports remain valid regardless of baseline changes.

---

## 13. Verification

### Unit Tests

- State transitions: 5 tests (one per transition in the transition table)
- Error handling: 5 tests (one per failure mode)
- Edge cases: 6 tests (empty health data, missing baseline, all-pass cycle, all-fail cycle, partial data, concurrent cycles)

### Integration Tests

- Integration with Knowledge Engine: 3 tests (integrity violation propagation, checksum mismatch detection)
- Integration with Governance Engine: 3 tests (compliance report generation, audit log reading)
- Integration with Event Bus: 2 tests (event publication, event consumption)

### Security Review

- [ ] No eval/exec patterns
- [ ] No credential leakage — Doctor Engine reads configuration only, never secrets
- [ ] No database writes — Doctor Engine is observation-only
- [ ] Input validation — all check inputs are validated before processing
- [ ] Output sanitization — violation events do not leak sensitive configuration details

### Performance

- Latency budget: 200ms p50, 1s p99 per check cycle
- Memory budget: 128MB steady-state, 256MB peak
- Check cycle interval: 30 seconds (configurable)
- Concurrent capacity: 1 check cycle at a time (serialized)

---

## 14. Security

### Tenant Isolation

The Doctor Engine checks system-wide integrity, not tenant-specific data. Health data and configuration are infrastructure-level, not tenant-scoped. However, if compliance checks involve tenant-specific policies, those checks are scoped per tenant.

### Auditability

Every check cycle produces an immutable DoctorReport containing:
- Unique check_id
- Timestamp
- All check results
- Violation details (if any)
- Overall status

Reports are persisted for historical analysis and compliance verification.

### No Write Access

The Doctor Engine has read-only access to:
- Engine health APIs
- Filesystem (configuration, package manifests)
- Governance audit log
- Knowledge integrity metadata

It has no write access to any engine's data store, no access to credentials, and no ability to modify system state.

---

## 15. Constitutional Mapping

| Responsibility | Constitutional Principle | Source |
|---------------|------------------------|--------|
| Verify system integrity | §5 — Doctor Layer | SHUNYA_ARCHITECTURE.md §5 (Doctor Layer) |
| Check architecture drift | §7 — Documentation Currency | SHUNYA_ENGINEERING_CONSTITUTION.md §7 |
| Validate package health | §5 — Doctor Layer | SHUNYA_ARCHITECTURE.md §5 (Doctor Layer) |
| Confirm governance compliance | §8 — Divergence Protocol | SHUNYA_ENGINEERING_CONSTITUTION.md §8 |
| Aggregate engine health | §11 — Health (System Flow) | SHUNYA_SYSTEM_FLOW.md §11 |
| Generate compliance reports | §12 — Compliance (System Flow) | SHUNYA_SYSTEM_FLOW.md §12 |
| Never modify system state | §3 — Doctor Engine SHALL NEVER | SHUNYA_SYSTEM_FLOW.md §3 |
| Verify implementation matches architecture | §1.1 — Architecture Fidelity | SHUNYA_ENGINEERING_CONSTITUTION.md §1.1 |

---

## 16. Layer Responsibilities

### What the Doctor Engine Does

- Verifies system integrity across all engines
- Checks architecture drift against the locked architecture
- Validates package health and dependency integrity
- Confirms governance compliance
- Aggregates health data and reports overall system health
- Generates compliance reports
- Publishes violation events

### What the Doctor Engine May Never Do

| Prohibited Action | Rationale | Belongs To |
|-------------------|-----------|------------|
| Never modify system state | Would violate Separation of Responsibilities | Human operator or automated recovery |
| Never execute user actions | Would violate Layer Boundaries | Executor Layer |
| Never govern real-time decisions | Would violate Layer Boundaries | Governance Layer |
| Never learn from past checks | Would violate Layer Boundaries | Learning Layer |
| Never reason about causes | Would violate Layer Boundaries | Reasoning Layer |
| Never observe external reality | Would violate Layer Boundaries | Observer Layer |
| Never plan recovery actions | Would violate Layer Boundaries | Planner Layer |

---

## 17. Future Extensions

### 17.1 Package Signature Verification

Verifying that installed packages match signed cryptographic hashes from a trusted registry, preventing supply-chain attacks from going undetected.

### 17.2 Capability Registration Validation

Verifying that every registered capability (Phase 14D — Acquisition Engine) has a corresponding implementation and is not a stale capability registration.

### 17.3 Automated Drift Remediation

Notifying the Planner Engine with a remediation plan when drift is detected — the Planner could generate corrective actions that pass through Governance before execution.

### 17.4 Cross-Tenant Baseline Comparison

Comparing baseline snapshots across tenants to detect systemic drift patterns (e.g., "all tenants missing the same package").

### 17.5 Pre-Deployment Integrity Gate

Running a full Doctor check cycle as a pre-deployment gate in the CI/CD pipeline — preventing deployments that would introduce architecture drift.

---

## 18. References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — Sections 4 (Doctor Layer in diagram), 5 (Doctor Layer), 6.9 (Architecture as Security Boundary), 7 (Phase 2 build order)
- [SHUNYA_SYSTEM_FLOW.md](/architecture/SHUNYA_SYSTEM_FLOW.md) — Section 3 (Doctor Engine responsibilities), 11 (Health aggregation), 12 (Compliance reports)
- [SHUNYA_ENGINEERING_CONSTITUTION.md](/governance/SHUNYA_ENGINEERING_CONSTITUTION.md) — Articles 1, 7, 8
- [SHUNYA_CORE_MODELS.md](/architecture/SHUNYA_CORE_MODELS.md) — Section 8 (Event Envelope), Section 10 (Interaction Principles)
- [ARCHITECTURE_BASELINE_REVIEW.md](/architecture/ARCHITECTURE_BASELINE_REVIEW.md) — M7 (Missing Engine Spec), ADR-004
- [ENGINE_SPEC_TEMPLATE.md](/governance/engine_specs/ENGINE_SPEC_TEMPLATE.md) — Specification template
- [VERIFICATION_CHECKLIST.md](/governance/verification/VERIFICATION_CHECKLIST.md) — Standard verification protocol
- `app/shunya/doctor.py` — Current partial implementation (113 lines)
