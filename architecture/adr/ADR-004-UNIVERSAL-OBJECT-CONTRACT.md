# ADR-004 — Universal Object Contract Implementation

**Status:** Proposed
**Date:** 2026-07-21
**Author:** Hermes Agent (Nous Research)
**Supersedes:** N/A

## Context

The SHUNYA Core Models (AS-01) define a UniversalObject hierarchy with mandatory fields: `object_id`, `tenant_id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `status`, `version`, `confidence`, `evidence`, `metadata`, `relationships`. However, no runtime implementation enforces this contract. Each engine defines its own data structures independently.

## Decision

Implement a `UniversalObject` base class that:
1. Enforces the mandatory field contract via Python dataclass
2. Provides a registry for all object types
3. Generates UUID v7 identifiers automatically
4. Provides serialization, evidence attachment, and relationship traversal
5. All new entity types inherit from this base

## Consequences

- Positive: All objects have guaranteed consistent structure
- Positive: Relationship graph is navigable across types
- Positive: Evidence chains work uniformly
- Positive: Serialization is standardized
- Negative: Existing models need adapter wrappers
- Risk: UUID v7 requires Python 3.12+ support

## Implementation

A lightweight Python mixin that existing SQLAlchemy models can adopt via composition or inheritance.