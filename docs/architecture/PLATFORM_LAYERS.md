# Shunya Platform Layers

Version: 1.0 (Draft)

Status: Active

---

# Purpose

This document defines the architectural layers of the Shunya Platform.

Each layer has a clearly defined responsibility and dependency boundary.

No layer may bypass these boundaries.

---

# Layer 1 — Host Applications

Examples

- CLI

- REST API

- Future Web UI

- SDK

- Background Workers

Responsibilities

- Receive user input

- Present output

- Configure the Runtime

- Start and stop the platform

May Depend On

- Runtime

Must Not Depend On

- Foundation directly

- Knowledge directly

- Governance directly

---

# Layer 2 — Runtime

Components

- Runtime Kernel

- Lifecycle Manager

- Service Container

- Runtime Context

- Event Bus

- Engine Registry

- Plugin Manager

Responsibilities

- Platform execution

- Engine orchestration

- Dependency resolution

- Event coordination

- Startup

- Shutdown

May Depend On

- Foundation

- Knowledge

- Governance

- Doctor

Must Not Depend On

- Applications

---

# Layer 3 — Platform Engines

Current Engines

- Knowledge

- Governance

- Doctor

Future Engines

- Memory

- Workflow

- AI

- Analytics

- Scheduler

Responsibilities

Each engine owns one business capability.

Engines communicate through Runtime contracts.

May Depend On

- Foundation

Should Prefer

- Runtime events

- Runtime contracts

Must Not Depend On

- Host applications

---

# Layer 4 — Foundation

Responsibilities

Provide shared engineering primitives.

Examples

- Result

- Option

- Validation

- Error

- Time

- Configuration

- Logging

- Platform

Foundation contains no business logic.

Foundation has no knowledge of Runtime.

---

# Layer 5 — Platform

Components

- Node.js

- TypeScript

- Operating System

Responsibilities

Execution environment.

No Shunya-specific behavior exists at this layer.

---

# Dependency Rule

Dependencies always flow downward.

Applications

↓

Runtime

↓

Platform Engines

↓

Foundation

↓

Platform

Upward dependencies are prohibited.

Circular dependencies are prohibited.

Cross-layer shortcuts are prohibited.

---

# Design Philosophy

Every layer should be independently understandable.

Every layer should be independently testable.

Every layer should evolve independently whenever possible.