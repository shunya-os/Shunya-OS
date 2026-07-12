# Shunya Directory Standards

Version: 1.0 (Draft)

Status: Active

---

# Purpose

This document defines the standard directory structure for the Shunya Platform.

Every package, engine, specification, and document should follow these conventions.

Consistency improves discoverability, maintainability, and onboarding.

---

# Repository Structure

```

shunya/

├── packages/

├── repository/

├── scripts/

├── .github/

├── turbo.json

├── pnpm-workspace.yaml

└── package.json

```

---

# Packages

Each package follows the same structure.

```

package/

├── src/

├── tests/

├── package.json

├── tsconfig.json

└── [README.md](http://README.md)

```

Rules

- Source code belongs inside `src`.

- Public APIs are exposed through `src/index.ts`.

- Tests should be isolated from production code whenever practical.

- Internal modules should never be imported from outside the package.

---

# Source Structure

Modules should remain small and responsibility-focused.

Example

```

src/

result/

option/

validation/

error/

time/

logging/

config/

platform/

index.ts

```

Every module owns:

- Types

- Helpers

- Tests

- Public API

---

# Runtime Structure

```

runtime/

api/

bootstrap/

container/

context/

contracts/

events/

kernel/

lifecycle/

plugins/

registry/

```

Each directory owns one Runtime responsibility.

---

# Repository Documentation

```

repository/

architecture/

adr/

capabilities/

product/

releases/

roadmap/

specifications/

```

Purpose

- architecture → platform architecture

- adr → architectural decisions

- capabilities → capability catalog

- product → product definition

- releases → release history

- roadmap → platform roadmap

- specifications → engine specifications

---

# Naming Standards

Directories

- lowercase

- singular when representing one concept

- plural when representing collections

Files

- PascalCase for classes

- camelCase for helpers

- UPPER_CASE for global documents only when historically established

- Markdown filenames should clearly describe their purpose

---

# Public API

Every package exposes a single public entry point.

```

src/index.ts

```

Internal implementation files remain private.

---

# Documentation Rules

Every engine should maintain:

- README

- ARCHITECTURE

- PUBLIC_API

- LIFECYCLE

- EXTENDING

Additional documents may be added when justified.

---

# Future Evolution

New packages should adopt these standards unless a documented Architectural Decision Record explicitly defines an exception.