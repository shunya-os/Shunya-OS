# Engine Specification Template

**File naming:** `ES-NNN-engine-name.md`

---

```markdown
# ES-NNN: Engine Name

**Status:** Draft | Review | Approved | Rejected | Superseded
**Phase:** Phase X (if applicable)
**Layer:** (Knowledge | Reasoning | Planner | Governance | Executor | Observer | Learning | Doctor | Other)
**Author:** Name
**Date:** YYYY-MM-DD
**Approver:** (filled on approval)

---

## 1. Objective

What does this engine do? One paragraph.

What problem does it solve? What capability does it add?

---

## 2. Scope

### In Scope

- List of capabilities this engine provides
- Explicit boundaries

### Out of Scope

- What this engine explicitly does NOT do
- Adjacent concerns that belong to other engines/layers

---

## 3. Dependencies

### Internal Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Engine A | Input | Provides data X |
| Engine B | Output | Consumes result Y |
| Layer C | Protocol | Uses interface Z |

### External Dependencies

- External APIs, libraries, services required

---

## 4. Inputs

### Input Contract

```
InputType:
  field1: type — description
  field2: type — description
```

### Input Sources

- Which engines, events, or external sources produce these inputs
- Trigger conditions that initiate processing

### Input Validation

- Required fields and their constraints
- Default values for optional fields
- Rejection criteria for invalid inputs

---

## 5. Outputs

### Output Contract

```
OutputType:
  field1: type — description
  field2: type — description
```

### Output Destinations

- Which engines, events, or external systems consume these outputs
- Success criteria for output delivery

### Output Guarantees

- At-least-once, exactly-once, or best-effort delivery
- Idempotency guarantees

---

## 6. State Machine

### States

```
StateA ──[event]──→ StateB ──[event]──→ StateC
  │                    │
  └──[error]──→ StateD └──[error]──→ StateD
```

### State Definitions

| State | Meaning | Is Terminal? |
|-------|---------|-------------|
| StateA | Description | No |
| StateB | Description | No |
| StateC | Description | Yes |
| StateD | Description | Yes |

### Transition Table

| From State | Event | Condition | To State | Action |
|------------|-------|-----------|----------|--------|
| StateA | event_1 | condition | StateB | action taken |

---

## 7. Events

### Events Consumed

| Event | Source | Payload | Action Taken |
|-------|--------|---------|-------------|
| event.name | Engine/Source | {fields} | Description |

### Events Produced

| Event | Destination | Payload | Trigger Condition |
|-------|-------------|---------|-------------------|
| event.name | Engine/Source | {fields} | When this happens |

---

## 8. Failure Modes

| Failure Mode | Cause | Detection | Effect | Recovery |
|--------------|-------|-----------|--------|----------|
| Input invalid | Malformed data | Schema validation | Rejection | Return error to caller |
| Dependency unavailable | Downstream outage | Timeout/circuit breaker | Degraded | Retry policy, fallback |
| State conflict | Concurrent mutation | Optimistic lock | Rejection | Retry with fresh state |
| Resource exhaustion | Memory/CPU limit | Health check | Crash | Restart, auto-scale |

---

## 9. Observability

### Logging

- Key events to log (start, completion, failure, state transitions)
- Log levels per event category
- Privacy constraints on logged data

### Tracing

- Distributed trace context propagation
- Span definitions for key operations

### Alerting

- Alert conditions (failure rate, latency spike, error count)
- Alert severity levels

---

## 10. Metrics

| Metric | Type | Unit | Target | Measurement |
|--------|------|------|--------|-------------|
| request_count | Counter | requests | N/A | Per second |
| latency_p50 | Histogram | ms | [value] | Per request |
| latency_p99 | Histogram | ms | [value] | Per request |
| error_rate | Gauge | % | [value] | Per minute |
| state_transition_count | Counter | transitions | N/A | Per state |
| throughput | Gauge | ops/sec | [value] | Per second |

---

## 11. Rollback Strategy

### Rollback Triggers

- Conditions that trigger a rollback (e.g., error rate > threshold, data corruption detected)
- Manual rollback authorization process

### Rollback Procedure

1. Step-by-step rollback instructions
2. Data migration rollback (if applicable)
3. Verification steps after rollback

### Rollback Limitations

- What cannot be rolled back
- Data loss acceptable vs unacceptable

---

## 12. Migration Strategy (when applicable)

### Migration Type

- Schema migration, data migration, configuration migration, or service migration

### Migration Steps

1. Pre-migration validation
2. Migration execution
3. Post-migration verification
4. Cutover procedure

### Rollback During Migration

- Point-in-time to which migration can be rolled back
- Data consistency guarantees during rollback

---

## 13. Verification

### Unit Tests

- State transitions: [count] tests
- Error handling: [count] tests
- Edge cases: [count] tests

### Integration Tests

- Integration with [Engine A]: [count] tests
- Integration with [Engine B]: [count] tests

### Security Review

- [ ] No eval/exec patterns
- [ ] No credential leakage
- [ ] Input validation
- [ ] Output sanitization

### Performance

- Latency budget: [ms]
- Memory budget: [MB]
- Concurrent capacity: [calls/second]

---

## 14. References

- [SHUNYA_ARCHITECTURE.md](/SHUNYA_ARCHITECTURE.md) — section reference
- [ADR-NNN](../adr/ADR-NNN.md) — related ADR
- [VERIFICATION_CHECKLIST.md](../verification/VERIFICATION_CHECKLIST.md) — verification protocol
- [GOVERNANCE_CHANGELOG.md](../GOVERNANCE_CHANGELOG.md) — governance change history
```