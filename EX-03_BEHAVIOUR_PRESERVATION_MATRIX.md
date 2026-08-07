# EX-03 — Behaviour Preservation Matrix (Constitutional Rule)

**Established by:** Founder directive, 2026-08-05 (CDR-003-R1 review)
**Refined by:** Founder directive, 2026-08-05 (four behavioural states + founder-visible impact)
**Supersedes:** (none)
**Amends:** EX-00 (Execution Transition), CDR mandatory sections (LX-06D-R3)
**Applies to:** All infrastructure convergence CEPs — Event Bus, SSE, Auth, Notification, Engine consolidation, Runtime consolidation

---

## 1. The Rule

> Every infrastructure convergence shall include a **Behaviour Preservation Matrix** proving exactly which observable behaviours are **preserved**, **enhanced**, **redesigned**, or **removed**, together with constitutional justification for every non-preserved behaviour and an explicit statement of founder-visible impact.

## 2. The Four Constitutional Behavioural States

The matrix uses **four** states, not three. The former "Changed" state concealed two fundamentally different situations — intentional constitutional redesign versus unverified equivalence — which must never look the same.

| Status | Meaning |
|--------|---------|
| **Preserved** | Proven identical behaviour — the new implementation behaves exactly as the legacy one |
| **Enhanced** | Same behavioural contract, with an additive capability (new behaviour introduced without altering existing behaviour) |
| **Redesigned** | Behaviour intentionally changes to satisfy a constitutional requirement, with constitutional justification |
| **Removed** | Behaviour intentionally eliminated, with constitutional justification |

The distinction at the heart of this rule:

- **Enhanced** = the behavioural contract is unchanged; something new is *added* on top. Founder should expect identical behaviour plus the new capability.
- **Redesigned** = the behavioural contract itself changes (e.g., payload semantics differ, ordering guarantees change, delivery becomes async). The change is constitutional but the founder should expect different behaviour.
- **Removed** = a behaviour ceases to exist entirely.

These must never be conflated. A founder reads the matrix to know *whether to expect different behaviour* — the status column answers that directly.

## 3. Mandatory Section

Every CDR for an infrastructure convergence CEP must contain a section titled **Behaviour Preservation Matrix** with the following table for every externally observable behaviour of the subsystem under convergence:

| Behaviour | Status | Evidence | Constitutional Justification | Founder-visible Impact |
|-----------|--------|----------|------------------------------|------------------------|
| <behaviour> | Preserved | <evidence of equivalence> | <why preserved> | None |
| <behaviour> | Enhanced | <evidence of additive capability> | <why additive is constitutional> | <what the founder can now do, or None> |
| <behaviour> | Redesigned | <evidence of the change> | <article/rule/law authorizing the change> | <observable difference, or None> |
| <behaviour> | Removed | <evidence of previous existence> | <article/rule/law authorizing removal> | <observable difference, or None> |

### Column requirements

1. **Behaviour** — the externally observable behaviour. Behaviour is the unit of analysis, not APIs, files, or method names.
2. **Status** — one of the four constitutional states above.
3. **Evidence** — proof backing the classification (per EX-02 evidence levels: Proven / Supported / Inferred / Unknown).
4. **Constitutional Justification** — mandatory for every **Enhanced, Redesigned, or Removed** behaviour, citing the specific article, rule, or law that authorizes it. **Preserved** needs only a short note (e.g., "identical Set iteration").
5. **Founder-visible Impact** — mandatory for every **Enhanced, Redesigned, or Removed** behaviour. It answers the question: *"Will the founder actually notice this?"* Valid values include:
   - **None** — constitutionally significant but completely invisible to the founder (e.g., strong typing).
   - **Positive** — founder gains a capability or an experience improvement.
   - **Changed UX** — founder sees a subtle or significant difference in behaviour.
   - **Negative/Regression** — a behaviour the founder relied on is gone; must be flagged explicitly.

## 4. Requirements

1. **Every** externally observable behaviour must appear in the matrix — preserved, enhanced, redesigned, or removed. Omission is a constitutional violation.
2. **Every** non-preserved behaviour (Enhanced, Redesigned, or Removed) must carry both:
   - a **constitutional justification** citing the specific article, rule, or law; and
   - a **founder-visible impact** statement.
3. **Enhanced** applies only to genuinely additive capabilities where the existing behavioural contract is unchanged. If the contract itself changes, classify as **Redesigned** — never Enhanced.
4. **Redesigned** applies when observable semantics intentionally change (e.g., untyped events become strongly typed *and* the payload contract changes; delivery becomes asynchronous; ordering guarantees change).
5. **Removed** applies when behaviour ceases to exist entirely (e.g., a hidden auto-notification side effect).
6. Founder-visible impact must be honest: many infrastructure changes are constitutionally significant but completely invisible; others subtly change UX. The matrix makes that distinction explicit rather than implied.

## 5. Rationale

- Founders care about behaviour, not implementation detail. The matrix answers the question: *"Will the system still do what it did, and if not, why not — and will I notice?"*
- Four states distinguish *intentional redesign* from *unverified equivalence* and *additive capability* — decisions that carry different expectations for the founder.
- The founder-visible impact column forces the architect to confront whether a change is observable, preventing both silent regressions and unjustified alarm.
- It keeps every artifact **additive** — a CDR evolves constitutional truth rather than contradicting previous artifacts.
- It applies uniformly to infrastructure CEPs: Event Bus, SSE, Auth, Notification, Engine consolidation, Runtime consolidation.

## 6. Non-Exhaustive Behaviour Dimension List

The following dimensions are a starting point for identifying externally observable behaviours (from CDR-003-R1). Each CEP must enumerate the behaviours specific to its subsystem:

- Public API shape and call signatures
- Delivery semantics (sync/async, delivery guarantees)
- Ordering guarantees
- Synchronous/asynchronous execution model
- Listener lifecycle (register/unregister semantics)
- Cleanup/reset behaviour
- Error propagation and isolation
- Nested event / re-entrant dispatch behaviour
- Duplicate listener handling
- Memory behaviour (retention, leak surface)
- Timing behaviour (immediacy, debounce, throttle, scheduling)
- Identity semantics (event naming, typing, payload shape)
- Side effects (implicit emissions, hidden notification, auto-actions)

## 7. Example (from CDR-003-R1 — Event Bus Consolidation)

| Behaviour | Status | Evidence | Constitutional Justification | Founder-visible Impact |
|-----------|--------|----------|------------------------------|------------------------|
| Event ordering | Preserved | Proven — identical Set iteration | N/A (equivalent) | None |
| Sync dispatch | Preserved | Proven — no microtask deferral | N/A (equivalent) | None |
| Listener cleanup | Preserved | Proven — same unsubscribe lifecycle | N/A (equivalent) | None |
| Strong typing | Enhanced | Proven — `RuntimeEvent` union replaces untyped strings | Canonical typed architecture; additive contract | None (invisible) |
| Wildcard subscription (`onAny`) | Enhanced | Proven — additive method | Additive capability, existing contract unchanged | None (invisible, new capability available) |
| Payload model | Redesigned | Proven — variadic `...args` → single typed event object | Universal Event Law §14 — events reflect explicit intent; typed contract | None (consumers migrated; same semantic events) |
| Notification auto-emission | Removed | Proven — existed in legacy `api/event-bus.ts` lines 16–21 | Simplicity Rule §4 — one explicit path; explicit notifications already exist in `use-query.ts` | None (explicit notifications unchanged; hidden side effect removed) |

## 8. Compliance Marker

CDRs produced under EX-03 must include the line:

```
**EX-03 Compliance:** Behaviour Preservation Matrix included (four states: Preserved/Enhanced/Redesigned/Removed). Every non-preserved behaviour carries constitutional justification and a founder-visible impact statement.
```

---

*EX-03 established by SHUNYA Constitutional Chief Architect per founder directive.*
*Conforms to: CAS-01, LX-06D-R2, LX-06D-R3, EX-02 (evidence boundary, infrastructure topology)*