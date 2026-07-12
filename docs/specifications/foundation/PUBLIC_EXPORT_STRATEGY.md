# PUBLIC EXPORT STRATEGY

## Objective

Foundation exposes independent modules through subpath exports.

This prevents namespace collisions and keeps the public API scalable.

## Rules

- The root package should remain minimal.

- Every module owns its own public API.

- Shared function names across modules are allowed.

- Consumers should import from module entry points.

## Examples

@shunya/foundation/platform

@shunya/foundation/result

@shunya/foundation/option

@shunya/foundation/validation

@shunya/foundation/errors

@shunya/foundation/ids

@shunya/foundation/time

@shunya/foundation/logging

@shunya/foundation/config

## Benefits

- No export collisions

- Clear module boundaries

- Better scalability

- Easier API evolution