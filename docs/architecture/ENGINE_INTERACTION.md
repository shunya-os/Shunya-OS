# Shunya Engine Interaction Model

Version: 1.0 (Draft)

Status: Active

---

# Purpose

This document defines how platform engines communicate.

The objective is to maintain low coupling, high cohesion, and predictable system behavior.

No engine should acquire knowledge of another engine's internal implementation.

---

# Interaction Principles

## Principle 1 — Single Responsibility

Each engine owns one primary capability.

Examples

- Knowledge owns platform knowledge.

- Governance owns policy evaluation.

- Doctor owns health diagnostics.

- Runtime owns execution.

Responsibilities must never overlap.

---

## Principle 2 — Communication Through Contracts

Whenever practical, engines communicate through Runtime contracts instead of concrete implementations.

This allows engines to evolve independently.

---

## Principle 3 — Prefer Events

When no immediate response is required, communication should occur through Runtime events.

Examples

- runtime.started

- governance.validated

- doctor.completed

- knowledge.updated

This minimizes direct dependencies.

---

## Principle 4 — Direct Calls Only When Necessary

Synchronous calls are appropriate only when an immediate result is required.

Examples

- Resolve a capability

- Read configuration

- Retrieve runtime context

Long-running workflows should not rely on synchronous chains.

---

# Current Engine Relationships

```

Runtime

   │

   ├────────► Knowledge

   ├────────► Governance

   └────────► Doctor

Knowledge

   │

   └────────► Foundation

Governance

   │

   ├────────► Knowledge

   └────────► Foundation

Doctor

   │

   ├────────► Governance

   ├────────► Knowledge

   └────────► Foundation

```

---

# Event-Based Communication

Preferred pattern

```

Engine A

↓

Publish Event

↓

Runtime Event Bus

↓

Interested Engines

```

Example

```

Runtime

↓

runtime.started

↓

Knowledge

Governance

Doctor

```

---

# Future Interaction Examples

## Workflow

Workflow publishes

workflow.completed

AI may subscribe.

Memory may subscribe.

Analytics may subscribe.

Workflow should not know they exist.

---

## Memory

Memory publishes

memory.updated

Knowledge may subscribe.

Analytics may subscribe.

---

## AI

AI publishes

ai.response.generated

Workflow may subscribe.

API may subscribe.

Logging may subscribe.

---

# Forbidden Patterns

Engines must not:

- Access another engine's internal state.

- Import internal files from another engine.

- Modify another engine's data directly.

- Introduce circular dependencies.

- Depend on future engines.

---

# Recommended Interaction Matrix

| Source | Target | Preferred Mechanism |

|---------|--------|---------------------|

| Runtime | Engines | Lifecycle + Contracts |

| Engine | Runtime | Contracts |

| Engine | Engine | Events |

| Application | Runtime | Public API |

| Plugin | Runtime | Plugin Contract |

---

# Future Governance

The Governance Engine should eventually validate:

- Illegal package imports

- Circular dependencies

- Direct engine access where events are preferred

- Public API violations

- Runtime contract violations

---

# Design Goal

Engines should cooperate without becoming dependent upon one another.

The Runtime provides the coordination layer that allows engines to evolve independently while functioning as one platform.