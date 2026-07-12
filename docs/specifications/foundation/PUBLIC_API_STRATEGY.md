# Foundation Public API Strategy

Status: Approved

## Goals

- Stable public contracts

- Small ergonomic API

- Modular imports

- Private implementation details

## Public Entry Points

### Root

@shunya/foundation

Exports the most frequently used primitives.

### Module Entry Points

@shunya/foundation/result

@shunya/foundation/option

@shunya/foundation/validation

@shunya/foundation/error

@shunya/foundation/time

@shunya/foundation/config

@shunya/foundation/logging

@shunya/foundation/platform

@shunya/foundation/id

## Internal Files

Internal implementation files are not part of the public API.

Consumers must never import files beneath a module entry point.

## Versioning

Breaking changes to public entry points require:

- Architecture review

- ADR (if applicable)

- Major version increment