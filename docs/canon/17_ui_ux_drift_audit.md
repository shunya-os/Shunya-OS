# SHUNYA UI/UX Constitutional Drift Audit

> **Phase C1 — Product Experience Recovery**
> **Date:** 2026-08-18
> **Status:** FOUNDER DIRECTIVE — Before correction
> **Baseline Commit:** bca5325

## Purpose

Compare the deployed SHUNYA frontend against the authoritative constitutional documents. Every identified deviation is a required correction.

## Documents Referenced

| Ref | Document | Version |
|-----|----------|---------|
| VDB | Visual Design Bible (design/visual-design-bible/1-visual-design-bible.md) | 1.0.0 |
| DT  | Design Tokens (design/visual-design-bible/2-design-tokens.md) | alpha |
| DS  | Design System (design/experience/09_design_system.md) | - |
| EX  | Experience Canon (docs/canon/08_experience_canon.md) | 2.0 |
| PC  | Presence Canon (design/experience/13_presence_canon.md) | - |/
| WM  | Workspace Model (design/experience/03_workspace_model.md) | - |
| NC  | Navigation Canon (design/experience/04_navigation_canon.md) | - |
| PFX | Product Constitution (docs/canon/14_product_constitution.md) | 1.0 |

## Drift Inventory

### 1. Brand Colour: Purple vs Gold

| Dimension | Constitutional (Required) | Current Implementation | Deviation | Severity |
|-----------|--------------------------|----------------------|-----------|----------|
| Brand primary | `#a4865f` / `#D4A843` gold (VDB §3.1, DS §2) | `#6C4AE2` purple (definitions.ts) | COMPLETE: wrong colour family | CRITICAL |
| theme-color meta | Not specified explicitly; implied gold per VDB | `#6C4AE2` purple (index.html) | DRIFTED: unrelated colour | HIGH |
| Surface bg | `#fbfaf8` (VDB §3.1, EX §3.2) | `#FAF8F5` (index.html, definitions.ts) | MINOR: 3-point hex shift | MEDIUM |

**Constitutional reference:**
- VDB §3.1: "Visual Language — The Four Pillars" specifies gold as the single brand accent
- EX §3.2: Surface = `#fbfaf8`, Accent = `#a4865f` gold
- DS §2: `--color-brand-primary` = `#D4A843` / `#B8923A` (gold tones)

**Correction:** Change `--sh-purple` to `--sh-gold` as the primary brand token. Remove purple colour family or relegate to semantic "relationship" use.

### 2. Typography: Playfair Display Missing

| Dimesion | Constitutional | Current | Deviaton | Severity |
|-----------|---------------|---------|-----------|----------|
| Hero font | Playfair Display (DT §typography) | Not loaded / not used | MISSING | HIGH |
| H1-H3 font | Playfair Display (DT §typography, VDB §5) | Inter only loaded | MISSING | HIGH |

**Constitutional reference:**
- DT: `fontFamily: "Playfair Display` for hero, h1, h2, h3
-DB §5.1: "Heading fonts use Playfair Display for editorial warmth"

**Correction:** Add Playfair Display font link to index.html. Apply `--sh-font-display` to all heading and hero elements.

### 3. Workspace Layout vs 3-Zone Architecture

| Dimension | Constitutional | Current | Deviation | Severity |
|-----------|---------------|---------|-----------|----------|
| Layout | 3-zone: Global Nav (Z1) + Context Panel (Z2) + Content (Z3) (WM §1, NC §2-4) | Single-column section list (universal-object-workspace.tsx) | DRIFTED: no three-zone architecture | CRITICAL |
| Navigation | Zone 1: fixed bar with Logo/Workspace Switcher/Breadcrumb/Search/Notifications/UserMenu (NC §2) | workspace-bar.tsx exists but no Zone 2 context panel | INCOMPLETE: navigation bar exists but workspace layout not implemented per spec | HIGH |

**Constitutional reference:**
- WM §1: "Every workspace follows this architecture" with explicit 3-zone diagram
- NC §2: Zone 1 = global navigation bar at top, always present, frosted glass
- NC §4: Zone 2 = Context Panel (left, 300px, collapsible)

**Correction:** Restore three-zone layout with fixed top nav, collapsible left context panel (300px), and primary content area.

### 4. 70/20/10 Whitespace Rule

| Dimension | Constitutional | Current | Deviation | Severity |
|-----------|---------------|---------|-----------|----------|
| Information density | 70% whitespace / 20% content / 10% controls (EX §3.1, VDB §1.2) | Dense section-based layout with repeated panels (Identity, Reality, Timeline, Evidence, etc.) | VIOLATED: visual density exceeds constitutional limits | CRITICAL |

**Constitutional reference:**
- EX §3.1: "70% whitespace / 20% content / 10% controls"
- VDB §1.2: "Banished patters: Heavy borders, dense data tables"

**Correction:** Reduce section density. Primary focus on ONE object/context per view. Controls must consume <=10% of visual space.

###5. SHUNYA Presence: Calm vs Busy

| Dimension | Constitutional | Current | Deviation | Severity |
|-----------|---------------|---------|-----------|----------|
|  Idle state | "SHUNYA becomes quieter" (PC §10) | Unknown (frontend bundle not fully inspected) | NEEDS VERIFICATION | MEDIUM |
| Loading states | " Skeleton placeholders. No spammers." (PC §1.0) | Uses framer-motion animations | NEEDS VERIFICATION | MEDIUM |
| System activity | "Visual state must originate from actual application state" (§9) | AI Presence Panel exists | NEEDS VERIFICATION | MEDIUM |

**Correction:** Audit idle, loading, and activity states against Presence Canon §10-11.

### 6. Objects Counts and "Dashboard" Patterns

| Dimension | Constitutional | Current | Deviation | Severity |
|-----------|---------------|---------|-----------|----------|
| Primary question | "What maters to this peron right now?" (§4) | Section list shows Identity type/status/ID | DRIFTED: presents record metadata, not context | HIGH |
| Object counts | "Do not assume these deserve primary real estate" (§4) | Likely shows object data directly | NEEDS VERIFICATION | MEDIUM |

### 7. Command Bar

| Dimension | Constitutional | Current | Deviation | Severity |
|-----------|---------------|---------|-----------|----------|
| Primary interaction | Command bar for "ask/ instruct/ explore/ change context/ act" (§12) | workspace-bar.tsx + SearchBar + CommandSurface | NEEDS VERIFICATION | MEDIUM |

### 8. Mobile: Portrait-First

| Dimension | Constitutional | Current | Deviation | Severity |
|-----------|---------------|---------|-----------|----------|
| Mobile behavior | "Intentionally designed" "portrait-first" (§18) | app works on mobile via responsive meta tags | NEEDS VERIFICATION | MEDIUM |

### 9. Public → Authenticated Continuity

| Dimension | Constitutional | Current | Deviation | Severity |
|-----------|---------------|---------|-----------|----------|
| Visual continuity | Same "visual language, tone, motion language, typography" (§17) | public landing uses different stack | NEEDS VERIFICATION | MEDIUM |

## Required Corrections Summary

| Priority | Correction | Constitutional Ref |
|----------|-----------|-------------------|
| P0 | Replace purple brand colour with gold (#a4865f / #D4A843) | VDB §3.1, EX §3.2, DS §2 |
| P0 | Add Playfair Display for headings | DT §typography, VDB §5 |
| P1 | Fix background: #FAF8F5 → #fbfaf8 | VDB §3.1, EX §3.2 |
| P1 | Restore 3-zone workspace layout (Z1 + Z2 + Z3) | WM §1, NC §2-4 |
| P1 | Reduce information density to achieve 70/20/10 | EX §3.1, VDB §1.2 |
| P2 | Audit SHUNYA presence vs calm idle/active states | PC §10-11 |
| P2 | Replace object record display with object-centric context | EX §2.1, §4.1 |
| P2 | Audit mobile portrait rendering | EX §4.12 |
| P3 | Verify public→authenticated continuity | Product Directive §17 |