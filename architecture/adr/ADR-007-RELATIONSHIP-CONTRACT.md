# ADR-007 — Relationship Contract

**Status:** Proposed (in SMS Volume II)
**Date:** 2026-07-22
**Author:** Hermes Agent

## Context

GENESIS II requires a formal Relationship Contract as part of the World Model. Relationships must be first-class, graph-navigable, and language-agnostic.

## Decision

Adopt the Relationship Contract defined in SMS Volume II §4. The existing `RelationshipEngine` implementation becomes the Relationship Service.

## Key Points

- Relationships are typed, bidirectional, and graph-traversable
- 15 canonical relationship types defined
- BFS/DFS traversal with type filtering and depth limiting
- No cycles without detection

## Consequences

- Existing `app/kernel/relationship.py` conforms to this contract
- Rename: `RelationshipEngine` → `RelationshipService`
