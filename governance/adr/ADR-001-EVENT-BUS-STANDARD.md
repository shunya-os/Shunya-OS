# ADR-001: Event Bus Standard

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

The Event Bus is referenced as the primary inter-engine communication mechanism in SHUNYA System Flow §5 and in every engine specification (ES-001 through ES-010). However, no specification defines the Event Bus itself — its instantiation, configuration, partitioning, delivery guarantees, or operational characteristics.

The canonical event envelope is already defined in Core Models §8. The Interaction Principles (Core Models §10) define publish rules, consumption rules, and async behavior. System Flow §5 defines event flow, ordering, idempotency, retry, and dead-letter handling. What is missing is the infrastructure specification that binds these to a concrete implementation.

### Current State

- SHUNYA System Flow §5 defines: event propagation, event ordering, idempotency, retry policy, dead-letter handling, correlation, traceability
- SHUNYA Core Models §8 defines: canonical event envelope format (event_id, correlation_id, trace_id, timestamp, tenant_id, actor, object, event_type, payload, evidence, confidence)
- SHUNYA Core Models §10 defines: publish rules, consumption rules, async behavior, circular dependency prevention, layer isolation, failure isolation
- Every engine specification includes events published/consumed sections using the canonical envelope
- A partial event bus implementation exists in the `shunya_os_gmail` worktree but is not wired into the main application (ARCHITECTURE_BASELINE_REVIEW.md — R2)
- No Event Bus exists in the main application codebase

### Constraints

- **Architecture Standard, not Engine Specification:** The Event Bus is shared infrastructure, not an engine. It must be specified as an Architecture Standard, not as an Engine Specification.
- **Canonical envelope is locked:** Core Models §8 defines the event envelope. This ADR must not modify the envelope.
- **Interaction Principles are locked:** Core Models §10 defines publish/consume rules. This ADR implements those rules, it does not redefine them.
- **System Flow §5 is locked:** Event ordering, idempotency, retry, and dead-letter handling are already specified. This ADR operationalizes those specifications.

### Evidence

- ARCHITECTURE_BASELINE_REVIEW.md — M1: "Event Bus Not Specified" — medium issue blocking implementation
- ARCHITECTURE_FINDINGS_CLASSIFICATION.md — M1/R2: "Event Bus Not Specified" — classified as B. Required Supporting Architecture
- SHUNYA_SYSTEM_FLOW.md — Section 5 (Event Flow) — event ordering, idempotency, retry, dead-letter handling
- SHUNYA_CORE_MODELS.md — Section 8 (Canonical Event Envelope) — envelope format
- SHUNYA_CORE_MODELS.md — Section 10 (Interaction Principles) — publish/consume rules
- ES-001 through ES-010 — each defines events published and consumed using the canonical envelope
- `shunya_os_gmail` worktree — partial event bus implementation (not wired)

---

## Decision

Define the Event Bus as an **Architecture Standard** extending Core Models §8 and implementing System Flow §5 and Core Models §10. The Event Bus shall be an in-process publish/subscribe dispatcher using the following specification:

### Instantiation

The Event Bus is instantiated as a singleton `EventBus` service within the application process. It is dependency-injected into all engines that publish or consume events. No separate process or external message broker is required for Phase 2.

Future phases may replace the in-process implementation with a distributed message broker (RabbitMQ, Kafka, or similar) without changing the API contract.

### API Contract

```
interface EventBus:
  publish(event: CanonicalEvent) -> EventId
    — Publishes an event to all subscribed consumers.
    — Returns the event_id for idempotency tracking.
    — Non-blocking — publisher does not wait for consumer processing.
    — Raises PublishError if the event envelope is invalid.

  subscribe(event_type: string | pattern, consumer: Consumer) -> SubscriptionId
    — Registers a consumer for events matching the given type or pattern.
    — Pattern matching supports wildcards: "knowledge.*", "governance.action.*"
    — Returns a subscription_id for unsubscription.
    — Raises SubscribeError if the consumer is already registered for this pattern.

  unsubscribe(subscription_id: SubscriptionId) -> bool
    — Removes a consumer subscription.
    — Returns true if the subscription was active.

interface Consumer:
  handle(event: CanonicalEvent) -> Result
    — Processes a delivered event.
    — Must be idempotent — same event delivered twice produces same result.
    — Returns Success or Failure.
    — Must not block for more than the consumer's configured timeout.
```

### Delivery Guarantees

| Property | Guarantee | Notes |
|----------|-----------|-------|
| Delivery | At-least-once | Consumer may receive duplicates; must handle via idempotency keys |
| Ordering | Per-producer, per-event-type | Events of same type from same producer delivered in order. Cross-type ordering not guaranteed |
| Persistence | In-memory (Phase 2) | Events not persisted after delivery. Future distributed implementation may persist |
| Scope | Process-local | Events are delivered only within the same process. Cross-process event bus is a future extension |
| Idempotency | 24-hour cache (event_id) | Consumers use event_id for idempotency. Cache TTL: 24 hours |

### Partitioning (Phase 2)

No partitioning. The in-process Event Bus delivers all events to all matching subscribers within the same process. Partitioning will be introduced when the Event Bus is replaced with a distributed implementation.

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_queue_size` | 10000 | Maximum number of events in the delivery queue |
| `consumer_timeout_ms` | 5000 | Maximum time a consumer may take to handle an event |
| `idempotency_cache_ttl_hours` | 24 | How long delivered event_ids are retained for deduplication |
| `retry_max_attempts` | 3 | Maximum retry attempts per consumer per event |
| `retry_backoff_ms` | [100, 500, 2000] | Exponential backoff intervals in milliseconds |
| `dead_letter_queue_size` | 1000 | Maximum events in the dead-letter queue |
| `health_check_interval_s` | 30 | How often the Event Bus health check runs |

### Event Types and Namespace Convention

All event types follow the `{source}.{action}` namespace convention:

```
knowledge.fact.created
knowledge.fact.superseded
governance.action.approved
governance.policy.violation
context.fusion.completed
identity.resolved
doctor.check.completed
execution.completed
observation.recorded
learning.signal.generated
```

Event types are registered in a central registry. No engine may publish an unregistered event type.

### Dead-Letter Queue

After `retry_max_attempts` failed delivery attempts, an event moves to the dead-letter queue. Dead-letter events are logged with full context (event, error, attempt history). An operator can replay dead-letter events manually. Dead-letter events older than 30 days are archived.

### Security

- Events carry `tenant_id`. Consumers filter by tenant. No engine processes events from another tenant
- Events are immutable after publication — no consumer may modify a received event
- Event payloads must not contain credentials, secrets, or sensitive data (SHUNYA_SYSTEM_FLOW.md §12 — Secrets)
- Event publishing requires authentication of the publisher (engine identity verified)
- Event subscription requires authorization (engines may only subscribe to event types relevant to their responsibilities)

### Health

The Event Bus exposes a health endpoint:
- Status: healthy / degraded / down
- Queue depth (current / max)
- Dead-letter queue count
- Consumer processing latency p50/p99
- Error count per consumer

---

## Options Considered

### Option 1: In-Process Event Bus (Chosen)

**Description:** A lightweight, in-process publish/subscribe dispatcher. Events are delivered synchronously within the same process using a queue-based delivery mechanism.

**Pros:**
- Simplest to implement — no external infrastructure
- Zero network latency — all delivery is in-process
- Easy to debug and test — single process
- Consistent with Phase 2 scope (no distributed infrastructure)
- Event envelope and interaction principles already specified — this is implementation-only

**Cons:**
- Not scalable beyond a single process
- Event delivery does not survive process restart
- No cross-process or cross-service communication
- Must be replaced with distributed broker for multi-instance deployment

### Option 2: Distributed Message Broker (Kafka/RabbitMQ)

**Description:** Deploy a dedicated message broker as an external service. All engines connect to the broker for publish/subscribe.

**Pros:**
- Production-ready scalability
- Persistent event storage
- Cross-process and cross-service communication
- Built-in partitioning, ordering, and replay

**Cons:**
- Requires infrastructure deployment and management (not available in Phase 2 on current Contabo VPS)
- Adds network latency to every event delivery
- Increases operational complexity
- Over-engineered for Phase 2 — the architecture specifies 10 engines in a single process

### Option 3: Hybrid (In-Process with External Bridge)

**Description:** Start with in-process Event Bus in Phase 2. Define a bridge interface that can connect to an external broker when needed. The bridge is a no-op in Phase 2.

**Pros:**
- Phase 2 simplicity with future-proofing
- Clean migration path to distributed broker
- All engines use the same EventBus API regardless of backend

**Cons:**
- Additional abstraction layer with no immediate benefit
- Bridge interface design may be premature

---

## Consequences

### Positive

- All 10 engines can now publish and consume events through a defined infrastructure
- Canonical event envelope (Core Models §8) is fully operationalized
- System Flow §5 event specifications are implemented
- No new architectural concepts introduced — Event Bus is explicitly shared infrastructure
- In-process design keeps Phase 2 implementation simple
- Dead-letter queue provides failure recovery

### Negative

- Single-process limitation means no cross-service event communication in Phase 2
- In-memory delivery means events are lost on process restart (consistent with System Flow §5 which defines idempotency cache TTL of 24h, not event persistence)
- Future migration to distributed broker will require engine configuration updates (Event Bus API remains stable)

### Neutral

- Engines already define events using the canonical envelope — no specification changes needed
- System Flow §5 already defines event ordering, retry, and dead-letter handling — this ADR implements those specifications
- The Event Bus is explicitly shared infrastructure (as classified by SUPPORTING_ARCHITECTURE_JUSTIFICATION.md — Component 1)

---

## Compliance

### Constitutional Principles Affected

- **§6.2 — Layered Validation:** Event Bus does not validate event payloads (payload validation is the consumer's responsibility). This preserves layered validation.
- **§6.9 — Architecture as Security Boundary:** Event Bus enforces tenant isolation on events and requires publisher authentication — maintaining engine boundaries.

### Engineering Constitution Articles Affected

- **Article 1 — Architecture Fidelity:** Event Bus implements System Flow §5 and Core Models §8/§10. No deviation.
- **Article 3 — Separation of Concerns:** Event Bus is shared infrastructure, not an engine. It does not perform any engine's responsibility.
- **Article 8 — Divergence Protocol:** No divergence introduced. Existing event specifications are implemented without modification.

---

## Verification

- [ ] EventBus API contract implemented — publish, subscribe, unsubscribe
- [ ] Canonical event envelope validation — all published events validated against Core Models §8 schema
- [ ] At-least-once delivery — consumer may receive duplicates; idempotency key deduplication verified
- [ ] Per-producer, per-event-type ordering — events of same type from same producer delivered in order
- [ ] Retry policy — 3 attempts with exponential backoff per consumer per event
- [ ] Dead-letter queue — events move to DLQ after max retries; replayable
- [ ] Tenant isolation — events carry tenant_id; consumers filter by tenant
- [ ] No credentials in event payloads — verified by schema validation
- [ ] Health endpoint — status, queue depth, latency, error count
- [ ] Idempotency cache — 24-hour TTL confirmed

---

## References

- [SHUNYA_SYSTEM_FLOW.md](/architecture/SHUNYA_SYSTEM_FLOW.md) — Section 5 (Event Flow)
- [SHUNYA_CORE_MODELS.md](/architecture/SHUNYA_CORE_MODELS.md) — Section 8 (Canonical Event Envelope), Section 10 (Interaction Principles)
- [ARCHITECTURE_BASELINE_REVIEW.md](/architecture/ARCHITECTURE_BASELINE_REVIEW.md) — M1 (Event Bus Not Specified), ADR-001
- [ARCHITECTURE_FINDINGS_CLASSIFICATION.md](/architecture/ARCHITECTURE_FINDINGS_CLASSIFICATION.md) — M1/R2/ADR-001
- [SUPPORTING_ARCHITECTURE_JUSTIFICATION.md](/architecture/SUPPORTING_ARCHITECTURE_JUSTIFICATION.md) — Component 1 (Event Bus — Shared Infrastructure)