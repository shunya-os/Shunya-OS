# ADR-002 — Foundation Public Export Strategy

## Status

Accepted

## Context

As additional Foundation modules were introduced, multiple modules exposed functions with identical names (for example, `match`).

Flattening all exports into the package root caused naming conflicts.

## Decision

Foundation will expose modules through subpath exports rather than flattening all public APIs into the root package.

## Consequences

- Root package remains minimal.

- Module APIs remain independent.

- Naming conflicts are avoided.

- Foundation scales without breaking existing consumers.