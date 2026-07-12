# ADR-003 — Foundation Public API Freeze

## Status

Accepted

## Context

Foundation has reached feature completeness for version 1.0.

The public API must be frozen before release.

## Decision

Foundation exports modules through subpath entry points.

The package root remains minimal.

Each module owns its own API contract.

Only `index.ts` files are public.

## Consequences

- No symbol collisions.

- Stable imports.

- Independent module evolution.

- Clear separation between public and internal code.