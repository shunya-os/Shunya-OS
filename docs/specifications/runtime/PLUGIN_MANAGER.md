# Plugin Manager

Specification ID: SPEC-RUNTIME-008

Status: Draft

---

# Purpose

The Plugin Manager is responsible for managing Runtime plugins.

---

# Responsibilities

- Register plugins

- Validate plugins

- Load plugins

- Unload plugins

---

# Non-Responsibilities

- Dependency Injection

- Lifecycle Management

- Engine Registration

- Event Bus ownership

---

# Public API

register()

load()

unload()

list()

has()