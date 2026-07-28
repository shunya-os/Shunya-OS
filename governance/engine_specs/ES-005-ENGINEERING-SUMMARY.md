# Executor Engine — Engineering Summary

**Engine:** Executor Engine (ES-005)
**Layer:** Executor
**Phase:** Phase 2 (Executor Layer)
**Status:** Draft specification

---

## One-Page Summary

### What It Is

The Executor Engine transforms governance-approved plans into real-world actions. It coordinates task execution across internal services and external channels, manages workflow state (retries, timeouts, compensations, checkpoints), collects execution evidence, and packages outcomes for the Observer Engine. It is the bridge between *what should be done* and *what actually happens*.

### Position in the Pipeline

```
Governance → [Executor Engine] → Observer → Learning
```

### How It Works

The Executor Engine follows a 9-stage pipeline:

1. **Execution Preparation** — Validate environment, resolve credentials, initialize channels
2. **Dependency Verification** — Verify task dependencies can be satisfied
3. **Resource Acquisition** — Acquire locks, connections, rate limits
4. **Task Dispatch** — Dispatch tasks to the appropriate executor (channel adapter, internal service, API)
5. **Execution Monitoring** — Track progress, detect stalls, trigger retries, manage timeouts
6. **Evidence Collection** — Collect delivery confirmations, API responses, receipts
7. **Completion Verification** — Verify all tasks completed and outputs are consistent
8. **Outcome Packaging** — Package complete execution result for the Observer Engine
9. **Observation Handoff** — Deliver outcome package to the Observer Engine

### Execution Types

10 execution types: Synchronous, Asynchronous, Human-assisted, Long-running, Batch, Streaming, Scheduled, Event-driven, Distributed, Transactional.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workflow model | Task-based with dependencies, retries, checkpoints, compensations | Covers all execution patterns |
| Credential resolution | At execution time, not plan time | Secrets never leak into plan storage |
| Channel adapters | Pluggable adapter interface | New channels added without changing the Executor |
| Execution evidence | Collected per task, stored immutably | Constitutional audit requirement |
| Backpressure | Queue depth threshold with slow acceptance and rejection | Prevents overload cascade |
| Task execution guarantee | Exactly-once per workflow | Prevents duplicate side effects |

### Current Implementation vs Specification

| Aspect | Current (executor.py) | Specification Target |
|--------|-----------------------|---------------------|
| Workflow model | Single-message send only | Full workflow with tasks, dependencies, retries |
| Execution types | 3 adapters (WhatsApp, Telegram, Email) | 10 execution types |
| Credential resolution | Env vars at init | Credential store, resolved at execution time |
| Retry policy | None | Configurable RetryPolicy per task |
| Compensation | None | Compensation actions per task |
| Checkpoints | None | Full workflow checkpointing |
| Evidence collection | Delivery log in memory | Immutable evidence records in Knowledge Engine |

---

## Open Architectural Questions

1. **Where does the workflow state store live?** Checkpoints and workflow state need a durable store. Options: same PostgreSQL database as the Knowledge Engine, a dedicated workflow state table, or an external workflow engine. Recommendation: same PostgreSQL with a `workflow_state` table.

2. **How does the credential store integrate with Phase 4 (Privacy)?** Credentials are sensitive data. The credential store must integrate with Phase 4 eligibility gates before releasing credentials. This integration is not yet specified.

3. **How does the Executor handle idempotency for external API calls?** Exactly-once delivery to external systems requires idempotency keys. The Executor generates idempotency keys per task. External systems must support idempotency. For systems that don't, the Executor uses at-most-once delivery with compensation.

---

## Assumptions Made

| Assumption | Detail |
|------------|--------|
| External channels support idempotency keys | WhatsApp Business API supports them; Telegram does not |
| Credential store is available at execution time | No offline execution for credentialed tasks |
| Workflow state fits in a single DB row | Checkpoints under 1MB |
| Channel adapters are thread-safe | Multiple tasks may use the same adapter concurrently |

---

## Risks and Dependencies

See full document for 8 failure modes and 9 cross-referenced specifications.

---

**End of Engineering Summary**