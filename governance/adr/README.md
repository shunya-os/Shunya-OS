# Architecture Decision Records

**Path:** `governance/adr/`

**Purpose:** Permanent, immutable record of all significant architecture decisions made during SHUNYA development.

---

## Principles

- **ADRs are never deleted.** They may be superseded by a newer ADR, but the original record remains.
- **ADRs are numbered sequentially.** Format: `ADR-NNN-title-with-hyphens.md`
- **Every ADR has a class.** See [ADR Classes](#adr-classes).
- **Every ADR has a status.** See [Statuses](#statuses).
- **ADRs are concise.** State the context, the decision, the consequences. Do not repeat specification content.

## ADR Classes

| Class | Authority | Scope |
|-------|-----------|-------|
| **Engineering** | Chief Software Architect | New engines within existing layers, integration between engines, implementation decisions, non-constitutional divergence |
| **Architectural / Constitutional** | Chief Constitutional Architect | New layers, layer boundary changes, constitutional principle modifications, pipeline architecture changes, constitutional divergence |

If classification is ambiguous, the Chief Software Architect determines the class.

## Statuses

| Status | Meaning |
|--------|---------|
| `Proposed` | Draft, not yet reviewed |
| `Accepted` | Approved by the appropriate authority (CSA for Engineering, CCA for Architectural/Constitutional) |
| `Superseded` | Replaced by a newer ADR (reference the superseding ADR) |
| `Rejected` | Rejected with documented reasoning |

## When to File an ADR

- Adding a new engine or layer (Architectural/Constitutional if new layer)
- Modifying an existing layer boundary (Architectural/Constitutional)
- Changing the pipeline architecture (Architectural/Constitutional)
- Adding an engine within an existing layer (Engineering)
- Integrating between two existing engines (Engineering)
- Resolving a divergence between implementation and the Constitution (class depends on severity)
- Any decision with lasting architectural consequences

## ADR Index

| # | Class | Title | Status | Date |
|---|-------|-------|--------|------|
| _(No ADRs yet)_ | | | | |

---

**Template:** [`ADR_TEMPLATE.md`](./ADR_TEMPLATE.md)