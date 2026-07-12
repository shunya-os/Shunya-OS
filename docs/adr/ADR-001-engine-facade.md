# ADR-001 — Engine Façade Pattern

Status: Accepted

Date: 2026-07-08

---

## Context

As Shunya grows, each engine contains multiple internal components.

For example, the Knowledge Engine contains:

- CapabilityLoader
- CapabilityValidator
- CapabilityRegistry
- DependencyGraph
- TopologicalPlanner
- KnowledgeDiagnostics

If other engines directly depend on these internal components, the platform becomes tightly coupled and difficult to evolve.

---

## Decision

Every engine shall expose exactly one public façade.

Other engines may depend only on that façade.

Internal implementation classes are private implementation details.

For the Knowledge Engine, the public façade is:

- Knowledge

Consumers must not directly depend on:

- CapabilityLoader
- CapabilityRegistry
- CapabilityValidator
- DependencyGraph
- TopologicalPlanner
- KnowledgeDiacs

---

## Consequences

### Advantages

- Stable public APIs
- Loose coupling
- Easier refactoring
- Better encapsulation
- Clear ownership
- Simpler documentation

### Trade-offs

- Some functionality may require façade methods to be added over time.
- Internal classes cannot be reused directly across engines.

These trade-offs are acceptable because they preserve long-term maintainability.

---

## Status

Accepted.

This pattern shall be used for every Shunya engine.

Examples:

- Knowledge
- Governance
- Runtime
- Memory
- Workflow
- Applications

---

End of ADR-001
