# Shunya Architecture Decisions

Version: 1.0

Status: Approved

---

# Purpose

This document records the enduring architectural decisions that define the Shunya Platform.

Unlike individual Architecture Decision Records (ADRs), which capture the context and rationale for a single decision, this document summarizes the permanent engineering principles that govern platform evolution.

Every new engine, package, and subsystem must comply with these decisions unless a future ADR explicitly revises them.

---

# AD-001 — Foundation is the Lowest Platform Layer

Foundation provides shared engineering primitives.

Foundation contains:

- Result

- Option

- Validation

- Error

- Time

- Configuration

- Logging

- Platform utilities

Foundation contains no business logic.

Foundation must never depend on any Shunya engine.

---

# AD-002 — Runtime Owns Platform Execution

Runtime is responsible for platform orchestration.

Responsibilities include:

- Startup

- Shutdown

- Lifecycle

- Dependency Injection

- Runtime Context

- Event Bus

- Engine Registry

- Plugin Management

Runtime coordinates engines but does not own business logic.

---

# AD-003 — Engines Own One Primary Responsibility

Every engine owns a single, well-defined capability.

Examples:

| Engine | Responsibility |

|--------|----------------|

| Knowledge | Knowledge management |

| Governance | Policy enforcement |

| Doctor | Diagnostics |

| Runtime | Platform execution |

| Memory | Persistent state (future) |

| Workflow | Orchestration (future) |

| AI | Intelligence services (future) |

Responsibilities should not overlap.

---

# AD-004 — Dependencies Flow Downward

Dependencies follow the platform layers.

```

Applications

        │

        ▼

Runtime

        │

        ▼

Platform Engines

        │

        ▼

Foundation

        │

        ▼

Node.js / TypeScript

```

Rules:

- Upward dependencies are prohibited.

- Circular dependencies are prohibited.

- Cross-layer shortcuts are prohibited.

---

# AD-005 — Public APIs are Contracts

Every package exposes a stable public API.

Internal implementation details remain private.

Breaking changes require:

- Architectural review

- Updated documentation

- ADR

- Major version increment

---

# AD-006 — Architecture Before Implementation

Major implementation work begins only after:

- Architecture documentation

- Design review

- Responsibility definition

Implementation should follow architecture, not define it.

---

# AD-007 — Event-Driven Collaboration

Whenever practical, engines communicate through Runtime events.

Direct synchronous calls should be reserved for cases where an immediate response is required.

This minimizes coupling and improves extensibility.

---

# AD-008 — Documentation is Part of the Product

Every engine maintains documentation alongside implementation.

Minimum documentation:

- README

- Architecture

- Public API

- Lifecycle

- Extension Guide

Architecture documentation evolves with the platform.

---

# AD-009 — Quality Gates are Mandatory

No milestone is considered complete until:

- Build passes

- Tests pass

- Doctor reports healthy

- Documentation updated

- Release notes written

- Git tag created

Quality gates are part of the engineering process, not post-release activities.

---

# AD-010 — Platform Growth Through Extension

New capabilities should be introduced by:

1. Architecture review

2. New engine or extension

3. Implementation

4. Integration

5. Release

Existing engines should not accumulate unrelated responsibilities.

---

# Governance

These architectural decisions form the baseline for future Governance policies.

Where practical, architectural constraints should be enforced automatically through tooling rather than relying solely on manual review.

---

# Review Policy

This document should change infrequently.

Any modification requires:

- Architectural review

- Updated ADR (where applicable)

- Documentation update

- Platform review

The objective is to preserve long-term architectural stability while allowing deliberate evolution.