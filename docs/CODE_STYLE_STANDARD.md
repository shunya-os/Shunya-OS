# SHUNYA Code Style Standard

Version: 1.0.0

Status: Active

Depends On:

- SHUNYA Canon
- Engineering Execution Standard

---

# Purpose

This document defines the mandatory coding standards for every implementation inside SHUNYA.

Consistency is more valuable than personal preference.

Readable software outlives clever software.

---

# Core Principles

Code should be:

Readable.

Predictable.

Testable.

Composable.

Maintainable.

Observable.

Documented.

---

# General Rules

Write code for humans.

Optimize for maintainability.

Avoid unnecessary abstraction.

Avoid unnecessary optimization.

Avoid duplication.

Prefer explicit behavior.

Every function should have one responsibility.

---

# Naming

Names should describe intent.

Avoid abbreviations.

Avoid generic names.

Good examples:

CustomerRepository

RelationshipResolver

TimelineService

MemoryPromotionEngine

Poor examples:

Utils

Manager

Helper

DataService

ObjectThing

---

# Functions

Functions should:

Perform one responsibility.

Remain short.

Have descriptive names.

Return predictable values.

Avoid hidden side effects.

Avoid unnecessary parameters.

---

# Classes

Classes should:

Represent one concept.

Hide implementation details.

Expose clear interfaces.

Avoid becoming large.

Support composition.

---

# Files

One primary responsibility per file.

Avoid excessively large files.

Group related implementations together.

Follow consistent directory structure.

---

# Comments

Comments explain:

Why.

Not what.

Good code explains itself.

Avoid commented-out code.

Delete obsolete comments.

---

# Constants

Never hardcode business values.

Constants belong in:

Configuration.

Domain policies.

Shared definitions.

Magic numbers are prohibited.

---

# Error Handling

Errors should:

Be explicit.

Contain useful information.

Avoid exposing internals.

Support debugging.

Support recovery.

---

# Logging

Log:

Business events.

Errors.

Warnings.

Performance.

Security events.

Never log:

Passwords.

Secrets.

Tokens.

Sensitive personal data.

---

# Exceptions

Throw meaningful exceptions.

Catch only when recovery exists.

Never silently ignore failures.

---

# APIs

APIs should be:

Consistent.

Versioned.

Documented.

Permission-aware.

Idempotent where appropriate.

---

# Testing

Every important business rule requires tests.

Tests should be:

Independent.

Readable.

Fast.

Repeatable.

Reliable.

---

# Documentation

Public interfaces require documentation.

Complex algorithms require documentation.

Architectural decisions require documentation.

---

# Formatting

Consistent indentation.

Consistent spacing.

Consistent ordering.

Consistent imports.

Automated formatting is preferred.

---

# Security

Validate every input.

Escape every output where appropriate.

Protect every secret.

Verify every permission.

Assume hostile input.

---

# Performance

Measure before optimizing.

Optimize bottlenecks.

Avoid premature optimization.

Readability remains the default priority.

---

# Artificial Intelligence

AI-generated code is never trusted automatically.

Every generated implementation requires:

Review.

Testing.

Documentation.

Validation.

Architecture always overrides generated code.

---

# Refactoring

Refactoring should improve:

Clarity.

Maintainability.

Architecture.

Performance.

Testability.

Behavior should remain unchanged unless explicitly intended.

---

# Definition of Good Code

Good code is:

Easy to understand.

Easy to change.

Easy to test.

Easy to review.

Easy to remove.

Easy to extend.

---

# Final Rule

Future engineers should understand the purpose of every file without reading the entire repository.

Clarity is the highest engineering standard.

# End of Code Style Standard
