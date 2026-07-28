# Engine Specifications

**Path:** `governance/engine_specs/`

**Purpose:** Detailed design documents for implementation units (engines, phases, components). An engine specification is the bridge between the architecture and the code — it describes *what* to build and *why* within the existing architecture.

---

## Principles

- **Engine specs do not modify architecture.** They describe implementation within existing layer boundaries. If the architecture needs modification, file an ADR first.
- **Engine specs are approved before implementation begins.** No implementation work starts without an approved spec.
- **Engine specs are living documents.** They may be updated during implementation, but changes must be reviewed.
- **Every engine spec maps to a verification checklist.** Approval requires checklist completion.

## When to Write an Engine Spec

- A new engine within an existing layer (e.g., a new Policy type within Governance)
- A significant refactoring of an existing engine
- Integration between two existing engines
- A new API surface or external interface

## Spec Index

| # | Engine | Phase | Status | Approver | Date |
|---|--------|-------|--------|----------|------|
| _(No specs yet)_ | | | | | |

---

**Template:** [`ENGINE_SPEC_TEMPLATE.md`](./ENGINE_SPEC_TEMPLATE.md)