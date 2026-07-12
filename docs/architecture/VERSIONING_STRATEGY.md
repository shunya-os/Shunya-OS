# Shunya Versioning Strategy

Version: 1.0 (Draft)

Status: Active

---

# Purpose

This document defines the versioning and release strategy for the Shunya Platform.

It establishes how versions are assigned, how compatibility is maintained, and how releases are governed across all platform packages.

The objective is to provide predictable evolution while minimizing disruption for consumers and contributors.

---

# Versioning Model

Shunya follows Semantic Versioning (SemVer).

```

MAJOR.MINOR.PATCH

```

Example

```

1.4.2

```

Where:

- MAJOR introduces incompatible public API changes.

- MINOR introduces backward-compatible functionality.

- PATCH contains backward-compatible fixes and improvements.

---

# Platform Version

The platform has an overall version representing the coordinated release of the complete system.

Example

```

Platform Version

1.0.0

```

The platform version represents the architectural baseline rather than the implementation status of individual engines.

---

# Engine Versioning

Each engine maintains its own version.

Examples

```

Foundation    1.0.0

Knowledge     1.0.0

Governance    1.0.0

Doctor        1.0.0

Runtime       0.1.0

```

Engines may evolve independently provided they maintain compatibility with the current platform architecture.

---

# Public API Compatibility

Public APIs should remain stable.

Breaking changes require:

- Architectural review

- Updated documentation

- ADR describing the change

- MAJOR version increment

Internal implementation changes do not require public version changes unless they affect published behavior.

---

# Release Requirements

A release is complete only when all of the following are satisfied:

- Implementation completed

- Tests passing

- Build passing

- Doctor reports healthy

- Documentation updated

- ADR published (if required)

- Release notes written

- Git tag created

---

# Git Tag Convention

Git tags follow a consistent format.

Examples

```

foundation-v1.0.0

knowledge-v1.0.0

governance-v1.0.0

runtime-v1.0.0

platform-v1.0.0

```

Every tagged release should correspond to release notes within the repository.

---

# Release Notes

Every release should include:

- Summary

- Features

- Improvements

- Breaking changes

- Migration guidance (if required)

- Quality status

Release notes are stored under:

```

repository/releases/

```

---

# Dependency Compatibility

Engine upgrades must preserve compatibility with dependent engines whenever practical.

Breaking dependency changes should be coordinated through Runtime and documented before implementation.

---

# Development Stages

The following lifecycle applies to every engine.

```

Architecture

↓

Implementation

↓

Testing

↓

Documentation

↓

Architecture Review

↓

Release

↓

Maintenance

```

No engine should bypass this lifecycle.

---

# Long-Term Support

Stable platform releases should prioritize compatibility over rapid change.

Experimental capabilities should remain isolated until architectural review is complete.

---

# Governance

Future Governance policies should validate:

- Version consistency

- Missing release notes

- Missing Git tags

- Missing documentation updates

- Missing ADRs for breaking changes

---

# Design Goal

Version numbers should communicate the maturity, compatibility, and stability of the platform.

Releases should be predictable, traceable, and reproducible.