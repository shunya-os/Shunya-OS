# Layout Matrix (DNA-01.6)

**Status:** Design — Not Yet Ratified  
**Version:** 2.1  
**Dependency:** DNA-01 Device-Native Architecture

---

## 1. Principle

Every page defines a **Primary Object** (the reason the user is here), a **Secondary Object** (supporting focus), and **Supporting Context** (reference material). The runtime rearranges these intentionally per experience class. No CSS auto-layout determines information architecture.

The constitution defines **compositional behaviour** — which object occupies which position relative to the others — not exact pixel widths. Column sizing, grid definitions, and exact spacing belong in a design system.

## 2. Page Types and Their Composition

### Home / Landing

| Experience Class | Primary | Secondary | Context |
|-----------------|---------|-----------|---------|
| Compact Experience | Full-viewport scroll narrative | — | — |
| Personal Experience | Full-viewport scroll narrative | Scene navigation (compact side) | — |
| Shared Experience | Full-viewport scroll narrative | Scene navigation (side) | — |
| Workstation Experience | Full-viewport scroll narrative | Scene navigation (side) | Footer |
| Studio Experience | Full-viewport scroll narrative | Scene navigation (side) | Footer |
| Orchestration Experience | Full-viewport scroll narrative | Scene navigation (side) | Footer |

### Workspace

| Experience Class | Primary | Secondary | Context |
|-----------------|---------|-----------|---------|
| Compact Experience | Workspace content (full width) | Bottom sheet overlay | — |
| Personal Experience | Workspace content (dominant) | Compact panel (split) | Drawer |
| Shared Experience | Content (flex) | Left panel (compact) | Context panel |
| Workstation Experience | Content (flex) | Left rail (labelled) | Context panel (collapsible) |
| Studio Experience | Content (flex) | Left rail (sections) | Context panel (metadata + intelligence) |
| Orchestration Experience | Content (flex, capped width) | Left rail (expanded) | Context panel (dual-pane) |

### Object Detail

| Experience Class | Primary | Secondary | Context |
|-----------------|---------|-----------|---------|
| Compact Experience | Object card (full width) | Sheet: timeline | — |
| Personal Experience | Object (dominant) | Timeline (compact panel) | — |
| Shared Experience | Object (flex) | Related objects (left) | Timeline + Intelligence |
| Workstation Experience | Object (flex) | Related objects (left) | Timeline + Intelligence |
| Studio Experience | Object (flex) | Related objects (left) | Timeline + Intelligence |
| Orchestration Experience | Object (flex) | Related objects (left) | Timeline + Intelligence (dual) |

### Search

| Experience Class | Primary | Secondary | Context |
|-----------------|---------|-----------|---------|
| Compact Experience | Results list (full width) | — | Filter chips (collapsible) |
| Personal Experience | Results (dominant) | Preview (slide panel) | — |
| Shared Experience | Results (flex) | — | Preview panel |
| Workstation Experience | Results (flex) | Filters (left sidebar) | Preview panel |
| Studio Experience | Results (flex) | Filters (left sidebar) | Preview panel |
| Orchestration Experience | Results (flex) | Filters (left sidebar) | Preview panel (expanded) |

### AI / Copilot

| Experience Class | Primary | Secondary | Context |
|-----------------|---------|-----------|---------|
| Compact Experience | Chat thread (full screen) | — | — |
| Personal Experience | Chat (dominant) | — | Context sheet |
| Shared Experience | Chat (flex) | History (left) | Context (right) |
| Workstation Experience | Chat (flex) | History (left) | Context (right) |
| Studio Experience | Chat (flex) | History (left rail) | Context (right panel) |
| Orchestration Experience | Chat (flex, capped width) | History (left) | Context (right, expanded) |

### Settings

| Experience Class | Primary | Secondary | Context |
|-----------------|---------|-----------|---------|
| Compact Experience | Settings list | Detail (push navigation) | — |
| Personal Experience | Settings list (proportional) | Detail (flex) | — |
| Shared Experience | Settings list (left) | Detail (flex) | Help (right) |
| Workstation Experience | Settings list (left) | Detail (flex) | Help (right) |
| Studio Experience | Settings list (left) | Detail (flex) | Help (right panel) |
| Orchestration Experience | Settings list (left) | Detail (flex) | Help (right, expanded) |

### Authentication

| Experience Class | Primary | Secondary | Context |
|-----------------|---------|-----------|---------|
| Compact Experience | Auth form (centred, full-width) | — | Compact brand strip |
| Personal Experience | Auth form (centred card) | — | Brand strip |
| Shared Experience | Auth form (centred card) | — | Full brand strip |
| Workstation Experience | Auth form (centred card) | — | Full brand strip |
| Studio Experience | Auth form (centred card) | — | Full brand strip |
| Orchestration Experience | Auth form (centred card) | — | Full brand strip |

## 3. Composition Rules

### Column Behaviour
- Columns are described as **fixed** (content-determined width), **flex** (fills remaining space), **proportional** (fraction of viewport), or **capped** (flex with maximum width)
- No column dimension shall be defined as `auto` or `min-content` for layout-critical dimensions
- Max-width constraints on primary content columns prevent excessively wide text on large screens

### Grid Behaviour
- Where grids are used, column count is explicitly specified per experience class
- Grid column count is determined by experience class, not by available space
- The implementation chooses the grid mechanism (CSS grid, flexbox, or other), but the column count is constitutionally fixed

### Prohibited Patterns
- `auto-fit` / `auto-fill` grids that leave column count to the browser
- Layouts that depend on element order without explicit experience-class rearrangement
- Identical column counts for Compact and Studio Experience

## 4. Layout Transformations (Allowed)

These are the only constitutional layout transformations — the behavioural changes that occur when moving between experience classes:

| Transformation | Description | Applies When |
|---------------|-------------|-------------|
| Column reduction | 3-column → 2-column → 1-column | Studio/Shared → Personal → Compact |
| Panel to overlay | Fixed panel becomes slide-up sheet or overlay | Studio/Personal → Compact |
| Rail to tabs | Persistent side rail becomes bottom tab bar | Studio/Personal → Compact |
| Rail compaction | Labelled rail becomes icon-only rail | Studio → Shared |
| Context drawer | Fixed context panel becomes drawer | Studio/Personal → Compact/Personal portrait |
| Content capping | Primary content width is capped | Orchestration Experience |
| Grid reduction | 4-column → 3-column → 2-column → 1-column | Orchestration → Studio → Shared → Compact |

## 5. Capability Parity in Layout

Every page type must be functional on every experience class. Compact Experience may not omit a panel that exists on Studio Experience — it must present that panel's content in an appropriate form. See DNA-01 §13.