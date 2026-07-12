# Runtime Context

## Responsibility

RuntimeContext provides a shared execution environment for every Runtime component.

It is created once during startup and remains available throughout the lifetime of the Runtime.

## Responsibilities

- Expose shared services

- Expose platform metadata

- Expose configuration

- Expose runtime environment

## Non-Responsibilities

- Business logic

- Dependency creation

- Plugin loading

- Event dispatching