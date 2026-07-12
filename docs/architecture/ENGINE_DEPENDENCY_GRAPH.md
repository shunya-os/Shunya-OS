# # Shunya Engine Dependency Graph

Version: 1.0 (Draft)

Status: Active

---

# Purpose

This document defines the allowed dependencies between Shunya packages.

Every package must comply with these rules.

The Governance Engine may validate these rules automatically in future releases.

---

# Current Package Graph

                    Applications

                          │

                          ▼

                  @shunya/runtime

                          │

        ┌─────────────────┼─────────────────┐

        ▼                 ▼                 ▼

 @shunya/knowledge  @shunya/governance  @shunya/doctor

        │                 │                 │

        └─────────────────┼─────────────────┘

                          ▼

               @shunya/foundation

                          │

                          ▼

               Node.js / TypeScript

---

# Allowed Dependencies

## @shunya/foundation

May Depend On

- Node.js

- TypeScript

Must Not Depend On

- Runtime

- Knowledge

- Governance

- Doctor

- Future engines

---

## @shunya/knowledge

May Depend On

- Foundation

Must Not Depend On

- Runtime

- Governance

- Doctor

---

## @shunya/governance

May Depend On

- Foundation

- Knowledge

Must Not Depend On

- Runtime

- Doctor

---

## @shunya/doctor

May Depend On

- Foundation

- Knowledge

- Governance

Must Not Depend On

- Runtime

---

## @shunya/runtime

May Depend On

- Foundation

- Knowledge

- Governance

- Doctor

Must Not Depend On

- Host applications

- Future application packages

---

# Future Engines

The following engines will follow the same dependency rules.

- Memory

- Workflow

- AI

- Scheduler

- Analytics

- Integration

Each engine should depend only on the minimum set of engines required to perform its responsibility.

---

# Architectural Rules

Rule 1

Dependencies flow downward.

---

Rule 2

Circular dependencies are prohibited.

---

Rule 3

Foundation is the lowest Shunya package.

---

Rule 4

Runtime orchestrates engines but should not contain business logic.

---

Rule 5

Engines communicate through Runtime contracts whenever practical.

---

# Enforcement

Future versions of the Governance Engine should validate:

- Package imports

- Circular dependencies

- Forbidden dependencies

- Layer violations

- Runtime contract violations