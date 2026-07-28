# SHUNYA Experience Canon

**Phase X1 — Foundational UX Architecture**

The authoritative experience architecture for SHUNYA. Every future frontend implementation must conform to these documents.

## Overview

The Experience Canon defines the complete interaction language of SHUNYA — from philosophy and information architecture to component design and frontend engineering. It is business-agnostic, object-first, and AI-native.

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Experience Philosophy](01_experience_philosophy.md) | What SHUNYA feels like, calm computing, executive workspace, object-first, AI-first, zero-noise, progressive disclosure, attention preservation |
| 02 | [Information Architecture](02_information_architecture.md) | Global hierarchy, workspace topology, navigation model, search architecture, object-centric organization |
| 03 | [Workspace Model](03_workspace_model.md) | 14 canonical workspaces with purpose, visible information, interaction rules, AI behavior, expandable regions |
| 04 | [Navigation Canon](04_navigation_canon.md) | Global/secondary/context navigation, breadcrumbs, keyboard, command palette, search, history, forward/back |
| 05 | [Object Workspace](05_object_workspace.md) | Universal object workspace architecture — every object follows the same layout, sections, and interactions |
| 06 | [AI Collaboration](06_ai_collaboration.md) | AI resident model, presence modes, suggestion system, conversation, memory, transparency, proactivity boundaries |
| 07 | [Component System](07_component_system.md) | Complete reusable component library — surfaces, sections, data, interaction, navigation, feedback, layout |
| 08 | [Motion System](08_motion_system.md) | Animation language, timing, easing, transitions, microinteractions, loading, reduced-motion accessibility |
| 09 | [Design System](09_design_system.md) | Design tokens — color, spacing, typography, grid, elevation, radius, shadows, dark/light mode |
| 10 | [Mobile Canon](10_mobile_canon.md) | Portrait-first experience, tablet behavior, responsive rules, touch interactions, bottom navigation |
| 11 | [Accessibility](11_accessibility.md) | Keyboard operation, ARIA, focus management, contrast, screen readers, reduced motion, zoom, i18n |
| 12 | [Frontend Engineering](12_frontend_engineering.md) | React architecture, component organization, state management, performance, rendering, animation, testing |

## Core Principles

- **Business agnostic** — No assumptions about industry, domain, or use case
- **Object-first** — Everything revolves around the object, not modules or pages
- **AI-native** — AI is resident in every workspace, not a chatbot beside the app
- **Calm computing** — The interface recedes. Attention is respected. Silence is the default.
- **Executive-grade** — Summary-first, decision-oriented, confidence-explicit
- **Universal architecture** — Every object type shares the same workspace layout and interaction model

## Reading Order

1. Start with **01 - Experience Philosophy** (the "why")
2. Read **02 - Information Architecture** (the "what goes where")
3. Read **05 - Object Workspace** (the "core interaction" — the most important document)
4. Read **03 - Workspace Model** (the "containers")
5. Read **04 - Navigation Canon** (the "how to move")
6. Read **06 - AI Collaboration** (the "intelligence layer")
7. Read **07-12** in any order (implementation details)

## Relationship to Other Canons

| Canon | Location | Relationship |
|-------|----------|--------------|
| Architecture Canon | `docs/canon/` | Defines the runtime, models, and invariants that the experience surfaces |
| Business Canon | `docs/canon/03_business_canon.md` | Defines object types that the Experience Canon renders |
| Engineering Canon | `docs/canon/11_engineering_canon.md` | Defines repository structure and engineering principles for implementation |
| AI Canon | `docs/canon/07_ai_canon.md` | Defines Cognitive OS engines that the AI Resident interfaces with |
| Data Canon | `docs/canon/06_data_canon.md` | Defines data flow, storage, and querying that feeds the experience |

## Frontend Implementation Rules

1. Every component is business-agnostic — no hardcoded references to object types or industries
2. Every screen follows the universal object workspace architecture
3. Every interaction has keyboard and screen reader support
4. Every animation respects `prefers-reduced-motion`
5. Every component has loading, empty, error, and success states
6. The design token system (CSS variables) is the single source of truth for all visual properties
7. No UI implementation is complete until it conforms to all 12 documents in this canon

---

*Canonical reference — Phase X1. Last updated: July 2026.*