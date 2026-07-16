# SHUNYA Repository Structure Standard

Version: 1.0.0

Status: Active

Depends On:

- SHUNYA Canon
- Engineering Execution Standard
- Code Style Standard

---

# Purpose

This document defines the permanent repository organization for SHUNYA.

Repository structure should communicate architecture.

Developers should understand where code belongs without discussion.

---

# Repository Philosophy

Folders represent architectural responsibility.

Never technology.

Never developers.

Never temporary implementation convenience.

The repository should remain understandable after ten years.

---

# Top-Level Structure

/docs

Canonical documentation.

Architecture.

Engineering standards.

Runbooks.

ADRs.

---

/backend

Business implementation.

APIs.

Services.

Domain.

Infrastructure.

Workers.

---

/frontend

User experience.

Components.

Layouts.

Pages.

Design system.

Localization.

Accessibility.

---

/shared

Code shared between backend and frontend.

Contracts.

Schemas.

Utilities.

Constants.

Shared types.

---

/ai

Artificial Intelligence.

Prompt library.

Context builders.

Reasoning.

Evaluation.

Model adapters.

Memory integration.

---

/automation

Workflow execution.

Automation engine.

Triggers.

Conditions.

Actions.

Schedulers.

---

/integrations

External systems.

Payment gateways.

Email.

WhatsApp.

Storage.

Authentication.

Calendars.

---

/infrastructure

Deployment.

Docker.

Terraform.

Nginx.

CI/CD.

Monitoring.

Scripts.

---

/tests

Unit.

Integration.

End-to-end.

Performance.

Security.

Regression.

---

/tools

Engineering utilities.

Migration tools.

Generators.

Developer scripts.

Validation.

---

# Backend Structure

/backend

/api

/controllers

/services

/domain

/repositories

/events

/memory

/search

/intelligence

/knowledge

/workflows

/automation

/notifications

/documents

/auth

/security

/config

/jobs

/workers

/utils

---

# Frontend Structure

/frontend

/app

/components

/features

/workspaces

/hooks

/context

/services

/api

/assets

/styles

/i18n

/utils

/tests

---

# Documentation Structure

/docs

BOOK_01_FOUNDATION.md

BOOK_02_UNIVERSAL_BLUEPRINT.md

BOOK_03_HUMAN_EXPERIENCE.md

BOOK_04_ENGINEERING.md

BOOK_05_BUSINESS_PATTERNS.md

BOOK_06_INTELLIGENCE.md

BOOK_07_MEMORY.md

BOOK_08_COMMUNICATION.md

BOOK_09_SECURITY_GOVERNANCE.md

BOOK_10_EVOLUTION.md

IMPLEMENTATION_MASTER_PLAN.md

ENGINEERING_EXECUTION_STANDARD.md

CODE_STYLE_STANDARD.md

REPOSITORY_STRUCTURE_STANDARD.md

ADR/

RUNBOOKS/

API/

ARCHITECTURE/

---

# Naming Rules

Directories use:

lowercase

hyphen-separated when appropriate.

Files use:

UPPERCASE for Canon documents.

PascalCase where language conventions require.

No ambiguous names.

---

# Module Rules

Every module should contain:

README

Implementation

Tests

Documentation

Configuration

Modules should remain independently understandable.

---

# Dependency Rules

Presentation depends upon Application.

Application depends upon Domain.

Domain depends upon nothing outside itself.

Infrastructure depends upon Domain.

No circular dependencies.

---

# AI Structure

Every AI capability belongs inside:

/ai

Subdirectories include:

providers/

prompts/

reasoning/

memory/

evaluation/

context/

skills/

No AI logic should scatter throughout the repository.

---

# Testing Structure

Tests mirror production structure.

Example:

backend/services/customer.py

↓

tests/backend/services/test_customer.py

Structure should remain predictable.

---

# Generated Files

Generated artifacts belong only inside designated output folders.

Generated code should never overwrite manually maintained architecture.

---

# Assets

Static assets belong under frontend/assets.

User-uploaded files never belong inside the repository.

---

# Configuration

Environment-specific configuration remains external.

Repository stores only templates.

No secrets.

No credentials.

No production tokens.

---

# Migration Scripts

Database migrations belong under:

backend/migrations

Every migration is:

Versioned.

Documented.

Repeatable.

Reversible where possible.

---

# Repository Health

The repository should continuously satisfy:

Consistent structure.

No duplicate architecture.

Clear ownership.

Predictable locations.

Minimal technical debt.

---

# Final Rule

If a developer cannot determine where a file belongs within one minute,

the repository structure requires improvement.

Architecture should be visible through organization.

# End of Repository Structure Standard
