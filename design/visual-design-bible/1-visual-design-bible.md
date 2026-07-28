# SHUNYA Visual Design Bible v1.0

> **Founder Directive (Authoritative)**
> This directive supersedes every previous visual instruction.
> From this point forward, SHUNYA's visual identity shall be governed by this document.
> No new screen, component, animation, illustration, or interface may be introduced unless it conforms to this Visual Design Bible.

**Status:** Living Document · **Version:** 1.0.0 · **Last Updated:** 2026-07-24
**Canonical Reference:** `static/shunya_canonical_visual.png`
**Source of Truth CSS:** `static/css/design-system.css` · `static/css/workspace.css`

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [The Emotional Hierarchy](#2-the-emotional-hierarchy)
3. [Visual Language](#3-visual-language)
4. [Layout System](#4-layout-system)
5. [Typography](#5-typography)
6. [Colour System](#6-colour-system)
7. [Light & Depth](#7-light--depth)
8. [Iconography](#8-iconography)
9. [Illustration System](#9-illustration-system)
10. [Motion](#10-motion)
11. [Components](#11-components)
12. [SHUNYA Identity Elements](#12-shunya-identity-elements)
13. [Screen Templates](#13-screen-templates)
14. [Design Review Checklist](#14-design-review-checklist)

---

## 1. Design Philosophy

### 1.1 What SHUNYA Is

SHUNYA is not a SaaS product. SHUNYA is not a dashboard. SHUNYA is not a chatbot.

**SHUNYA is an operating system for human organizations.**

Every visual decision must reinforce four feelings, in this order:

| Feeling | Why |
|---------|-----|
| **Calm** | The user should feel at ease. No visual noise, no urgency-driven design. |
| **Clarity** | Information should be immediately understandable. Hierarchy is not optional. |
| **Intelligence** | The system should feel perceptive, not obtrusive. It reveals what matters. |
| **Trust** | Every pixel should communicate reliability. The user should never doubt the system. |

### 1.2 What to Remove

If a UI element makes the experience feel busier, louder, or more "software-like," it should be removed or redesigned.

**Banished patterns:**
- Heavy borders and box shadows on every card
- Vibrant accent colours used for decoration
- Skeleton screens that stutter and shift
- Confetti, animations that celebrate trivial actions
- Dense data tables with alternating row colours
- "Delightful" micro-interactions that add cognitive load

### 1.3 Design Principles

1. **Whitespace is a feature.** Every element should have room to breathe. Margins and padding are not waste — they are the most important spatial signal.
2. **Typography carries hierarchy.** Weight, size, and tracking do the work that other products delegate to colour, icons, and borders.
3. **Light creates depth, not borders.** Elevation is expressed through subtle shadows and translucency, never through hard outlines.
4. **Restraint over decoration.** If an element exists only because it "looks nice," question whether it belongs.
5. **One system, everywhere.** The layout grid, spacing scale, radii, and rhythm are universal. No screen invents its own geometry.

---

## 2. The Emotional Hierarchy

### 2.1 The Order of Communication

Every screen must communicate in this order:

```
1. CALM       → The user feels at ease. The screen is not demanding.
2. UNDERSTANDING → The user sees what matters. Context is clear.
3. INTELLIGENCE  → The system reveals insight. The user is impressed.
4. CAPABILITY    → The user can act. The interface is ready.
```

### 2.2 Never Reverse the Order

The user should first feel comfortable, then understood, then impressed. A screen that leads with capability (dense toolbars, aggressive CTAs, overwhelming data) before establishing calm and understanding has failed.

### 2.3 Cognitive Load Budget

Every screen has a cognitive load budget. The addition of any new element requires justification against the Four Feelings. If an element does not serve at least one of the four feelings, it must be removed.

---

## 3. Visual Language

### 3.1 The Four Pillars

The visual language consists of exactly four tools:

| Tool | Purpose |
|------|---------|
| **Whitespace** | Separation, hierarchy, breathing room |
| **Typography** | Voice, hierarchy, information density |
| **Light** | Depth, focus, atmosphere |
| **Proportion** | Balance, rhythm, structure |

### 3.2 Restraint

Decoration is not part of the visual language. If an element exists only because it "looks nice," question whether it belongs. Elements must earn their place through utility.

### 3.3 The SHUNYA Aesthetic

- **Minimal but not cold.** The palette is warm-neutral. The whites are paper-toned, not sterile.
- **Quiet but not mute.** Gold accents punctuate without shouting.
- **Spacious but not empty.** Whitespace is intentional, not abandoned.
- **Refined but not precious.** Everything is crafted, but nothing is ornamental.

### 3.4 What SHUNYA Does NOT Look Like

- Not a Bootstrap/Tailwind utility-class dashboard
- Not a dark-mode terminal hacker aesthetic
- Not a colourful, playful consumer app
- Not a dense, enterprise ERP interface
- Not a "modern" glassmorphism-heavy design system

---

## 4. Layout System

### 4.1 Universal Grid

SHUNYA uses a single layout system that applies everywhere — homepage, login, workspace, CRM, calendar, files, intelligence, memory, mobile, tablet.

**Spacing, margins, radii, alignment, and rhythm come from one shared system. No screen invents its own geometry.**

### 4.2 Executive Grid

| Property | Value | CSS Variable |
|----------|-------|--------------|
| Base unit | 4px | `--shunya-unit` |
| Rhythm | 8px increments | `--shunya-space-2` through `--shunya-space-32` |
| Spacing scale | 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 80, 96, 128 | `--shunya-space-1` through `--shunya-space-32` |
| Default gutter | 24px | `--shunya-gutter` |
| Max content width | 1200px | `--shunya-max-width` |

### 4.3 Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--shunya-space-1` | 4px | Smallest gap, icon-to-text |
| `--shunya-space-2` | 8px | Tight group, label-to-input |
| `--shunya-space-3` | 12px | Button padding, chip padding |
| `--shunya-space-4` | 16px | Card padding, element gap |
| `--shunya-space-5` | 20px | Panel padding |
| `--shunya-space-6` | 24px | Section gutter, group separation |
| `--shunya-space-8` | 32px | Section padding |
| `--shunya-space-10` | 40px | Wide separation |
| `--shunya-space-12` | 48px | Major section spacing |
| `--shunya-space-16` | 64px | Page section padding |
| `--shunya-space-20` | 80px | Hero padding |
| `--shunya-space-24` | 96px | Large hero section |
| `--shunya-space-32` | 128px | Maximum section spacing |

### 4.4 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--shunya-radius-sm` | 10px | Buttons, inputs, cards |
| `--shunya-radius-md` | 16px | Panels, modals, artwork container |
| `--shunya-radius-lg` | 24px | Large containers |
| `--shunya-radius-xl` | 32px | Hero panels |
| `--shunya-radius-full` | 9999px | Avatars, badges, pills |

### 4.5 Layout Zones (Workspace)

The authenticated workspace uses a three-zone layout:

```
┌─────────────────────────────────────────────────────────┐
│  Identity Strip (44px)                                   │
├─────────────┬───────────────────────────┬────────────────┤
│  Zone Left  │     Zone Center           │  Zone Right    │
│  280px      │     flex: 1               │  340px         │
│             │                           │                │
│  Graph /    │   Object Workspace /      │  Intelligence  │
│  Search /   │   Morning Zero /          │  Insights /    │
│  Navigation │   Conversation            │  Context       │
│             │                           │                │
│  bg: #f3f2f2│   bg: #fafaf8             │  bg: #ebebea   │
└─────────────┴───────────────────────────┴────────────────┘
```

- **Zone Left (280px):** Navigation, search, object graph, spaces
- **Zone Center (flex: 1):** Primary workspace (object view, conversation, Morning Zero)
- **Zone Right (340px):** SHUNYA Intelligence pane, context, insights, related objects

### 4.6 Responsive Behaviour

| Breakpoint | Behaviour |
|------------|-----------|
| > 1024px | Three zones visible |
| 769–1024px | Zone Right hidden, Zone Left collapses to 220px |
| ≤ 768px | Zone Left hidden, single-column layout |

---

## 5. Typography

### 5.1 Font Families

| Role | Family | CSS Variable | Fallback |
|------|--------|--------------|----------|
| Display | Playfair Display | `--shunya-font-display` | Georgia, Times New Roman, serif |
| Body | Inter | `--shunya-font-body` | -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif |
| Mono | SF Mono / Fira Code | `--shunya-font-mono` | Cascadia Code, monospace |
| Identity (Devanagari) | Noto Sans Devanagari | `--shunya-font-devanagari` | Nirmala UI, Sanskrit Text, Mukta, serif |

### 5.2 Type Scale

The type scale follows the golden ratio (1.618), rounded to conventional sizes.

| Token | Size | Weight | Leading | Tracking | Usage |
|-------|------|--------|---------|----------|-------|
| `--shunya-text-5xl` | 72px | 400 | 1.08 | -0.025em | Hero headline (rare) |
| `--shunya-text-4xl` | 56px | 400 | 1.08 | -0.025em | Large hero |
| `--shunya-text-3xl` | 42px | 400 | 1.08 | -0.025em | Hero headline (standard) |
| `--shunya-text-2xl` | 32px | 400 | 1.1 | -0.02em | Section heading |
| `--shunya-text-xl` | 24px | 300 | 1.2 | -0.02em | Object name, display heading |
| `--shunya-text-lg` | 18px | 300 | 1.3 | -0.01em | Subheading |
| `--shunya-text-md` | 16px | 400 | 1.5 | 0 | Body large |
| `--shunya-text-base` | 14px | 400 | 1.5 | 0 | Body text (default) |
| `--shunya-text-sm` | 12px | 400 | 1.5 | 0 | Secondary text, metadata |
| `--shunya-text-xs` | 10px | 600 | 1.2 | 0.06em | Labels, uppercase, captions |

### 5.3 Typography Rules

**Display typography (Playfair Display):**
- Reserved for hero headlines, major section headings, and the SHUNYA wordmark in display contexts
- Always use regular weight (400) or italic (400 italic)
- Never use bold weight in Playfair Display
- Leading: `--shunya-leading-tight` (1.08)
- Tracking: `--shunya-tracking-tight` (-0.025em)

**Body typography (Inter):**
- Primary text at 14px (`--shunya-text-base`), weight 400
- Object names at 24px, weight 300 for calm, spacious feel
- Navigation and labels at 11px–13px with wider tracking
- Use weight 300 for spacious, editorial feel in large text
- Use weight 500 sparingly for emphasis in lists and navigation active states
- Use weight 600 for labels, tabs, and uppercase headings

**Editorial typography:**
- Line height: 1.7 for reading comfort
- Max width: 600–700px for reading columns
- Paragraph spacing: 1.5× the font size

**Data typography:**
- Use tabular-nums (`font-variant-numeric: tabular-nums`) for all numerical data
- Mono font for code, system logs, and structured data
- Data labels: 10px uppercase, 0.06em tracking

### 5.4 Tracking Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--shunya-tracking-tight` | -0.025em | Display text, hero headlines |
| `--shunya-tracking-normal` | 0 | Body text |
| `--shunya-tracking-wide` | 0.02em | Navigation, buttons |
| `--shunya-tracking-wider` | 0.06em | Labels, captions, uppercase |
| `--shunya-tracking-widest` | 0.12em | Section labels, tagline |
| `--shunya-tracking-ultra` | 0.2em | "Infinite Intelligence. Zero Noise." |

### 5.5 Prohibited Typography

- No bold Playfair Display
- No all-caps body text (all-caps is for labels ≤ 10px only)
- No font sizes below 10px
- No line-height below 1.08 for display text
- No font-family mixing within the same text block (except for Devanagari in identity)

---

## 6. Colour System

### 6.1 Palette

The palette is intentionally small. Every colour has a defined purpose.

#### 6.1.1 Background Whites

| Token | Value | Usage |
|-------|-------|-------|
| `--shunya-bg` | `#fbfaf8` | Page background (warm white) |
| `--shunya-surface` | `#ffffff` | Card, panel, modal surface |
| `--shunya-nav-bg` | `#fefefe` | Navigation bar background |
| `--shunya-artwork-bg` | `#f3ebe2` | Artwork panel background |
| `--shunya-glass` | `rgba(255,255,255,0.6)` | Glassmorphism surface |

#### 6.1.2 Zone Surfaces (Workspace)

| Token | Value | Usage |
|-------|-------|-------|
| `--zone-left-bg` | `#f3f2f2` | Left navigation zone |
| `--zone-center-bg` | `#fafaf8` | Center workspace zone |
| `--zone-right-bg` | `#ebebea` | Right intelligence zone |
| `--top-bar-bg` | `#faf9f8` | Identity strip |

#### 6.1.3 Text Colours

| Token | Value | Opacity | Usage |
|-------|-------|---------|-------|
| `--shunya-text` | `#1a1c1d` (or `#191b1c`) | 100% | Primary text, headings |
| `--shunya-text-secondary` | `rgba(26,28,29,0.55)` | 55% | Secondary text, body |
| `--shunya-text-tertiary` | `rgba(26,28,29,0.35)` | 35% | Metadata, hints |
| `--shunya-text-faint` | `rgba(26,28,29,0.15)` | 15% | Placeholder, disabled |

#### 6.1.4 Gold Accent

| Token | Value | Usage |
|-------|-------|-------|
| `--shunya-gold` | `#a4865f` | Primary accent, identity marks |
| `--shunya-gold-light` | `#d4c0a8` | Hover states, light backgrounds |
| `--shunya-gold-dark` | `#8a7050` | Active states (rare) |
| `--shunya-gold-glow` | `rgba(164,134,95,0.08)` | Subtle glow, artwork |

#### 6.1.5 Borders

| Token | Value | Usage |
|-------|-------|-------|
| `--shunya-border` | `rgba(26,28,29,0.07)` | Default borders |
| `--shunya-border-hover` | `rgba(26,28,29,0.14)` | Hover borders |

#### 6.1.6 Semantic Colours

| Token | Value | Usage |
|-------|-------|-------|
| Success / Healthy | `#51cf66` | Positive indicators, health dots |
| Warning / Caution | `#fab005` | Attention items |
| Orange / At Risk | `#fd7e14` | Risk indicators |
| Error / Critical | `#ff6b6b` | Errors, critical items |
| Information | `#74c0fc` | Informational dots |

### 6.2 Colour Usage Rules

1. **Gold is the only accent colour.** Gold is reserved for identity marks, the dot, the hero artwork, and section labels. It is not used for buttons, links, or interactive elements.
2. **Interactive elements use `--shunya-text` (black) as the primary interactive colour.** Buttons, active states, and focus indicators use the dark text colour, not gold.
3. **Semantic colours are used only for indicators** — health dots, status badges, and timeline markers. They are never used for buttons, backgrounds, or decorative elements.
4. **Surface colours are the lightest possible.** White surfaces (`#ffffff`, `#fefefe`) are used for cards and nav. The page background (`#fbfaf8`) is the warmest permitted white.
5. **No dark mode in v1.0.** All designs are light-mode only. Dark mode considerations are deferred.

### 6.3 Contrast Minimums

| Context | Minimum Ratio | Standard |
|---------|---------------|----------|
| Body text on background | 10:1 | WCAG AAA |
| Large text (≥24px) on background | 4.5:1 | WCAG AA |
| UI elements (buttons, inputs) | 3:1 | WCAG AA |
| Placeholder text | 3:1 (minimum) | WCAG AA |

---

## 7. Light & Depth

### 7.1 Shadow System

Depth is created through light, not heavy borders. SHUNYA uses a layered shadow system based on a shared ambient light source.

| Token | Value | Elevation | Usage |
|-------|-------|-----------|-------|
| `--shunya-shadow-sm` | `0 1px 4px rgba(26,28,29,0.03)` | +1 | Subtle separation |
| `--shunya-shadow-md` | `0 2px 12px rgba(26,28,29,0.05)` | +2 | Cards, panels |
| `--shunya-shadow-lg` | `0 4px 24px rgba(26,28,29,0.06)` | +3 | Modals, dropdowns |
| `--shunya-shadow-xl` | `0 8px 40px rgba(26,28,29,0.08)` | +4 | Overlays, dialogs |
| `--shunya-shadow-gold` | `0 4px 40px rgba(164,134,95,0.08)` | Special | Gold accent glow |
| `--shunya-shadow-button` | `0 2px 8px rgba(26,28,29,0.06)` | +1 | Default button |
| `--shunya-shadow-button-hover` | `0 4px 16px rgba(26,28,29,0.1)` | +2 | Button hover |

### 7.2 Glass Surface

```css
.shunya-glass {
  background: var(--shunya-glass);
  backdrop-filter: blur(12px) saturate(1.1);
  -webkit-backdrop-filter: blur(12px) saturate(1.1);
  border: 1px solid var(--shunya-glass-border);
}
```

Glass is used sparingly for:
- Search overlays (full-screen, 97% opacity white with blur)
- Floating panels (when they need to overlay content)
- Navigation bars that scroll behind content

### 7.3 Depth Rules

1. **Never use heavy borders to create depth.** The maximum border opacity is 7% (`rgba(26,28,29,0.07)`).
2. **Elevation is expressed through shadow + background colour, not border.** Higher elevation surfaces may have slightly lighter backgrounds.
3. **Shadows are always warm-neutral** — the shadow colour is `rgba(26,28,29, …)` with very low opacity.
4. **The gold glow shadow** (`--shunya-shadow-gold`) is reserved for the hero artwork and identity elements only.
5. **No inset shadows** on containers (no "inner depth" effect).
6. **No box-shadow on hover** unless the element is interactive (buttons, cards, links).

---

## 8. Iconography

### 8.1 Icon Language

SHUNYA uses a single icon language. Every icon belongs to the same family.

### 8.2 Specifications

| Property | Value |
|----------|-------|
| Stroke width | 1.5px (18px and 24px icons) |
| Corner treatment | Rounded (stroke-linejoin: round, stroke-linecap: round) |
| Standard size | 18px × 18px (navigation), 22px × 22px (industry strip) |
| Fill | None (stroke-only) |
| Colour | `--shunya-text` (default), `--shunya-text-secondary` (inactive) |
| Optical padding | 1px internal padding to prevent edge clipping |

### 8.3 Icon Usage Rules

1. **Icons are always stroke-based.** No filled icons.
2. **Icons accompany text** — they are rarely standalone (exceptions: the gold dot, the identity mark).
3. **Navigation icons are 18px** with 8px gap to the label.
4. **Industry strip icons are 22px** on a 24px viewBox.
5. **No custom icon is introduced without matching the stroke width, corner treatment, and optical weight.**
6. **Icons use the same colour as their adjacent text** — never a different colour.

### 8.4 Prohibited Iconography

- Emoji as icons (🚀, 📊, ⚙️ are not permitted)
- Filled glyph icons
- Multi-colour icons
- Gradient icons
- Icons from different families mixed on the same screen

---

## 9. Illustration System

### 9.1 The Hero Artwork

The SHUNYA hero artwork is the single most important illustration in the system. It is located at `static/img/artwork-hero.svg` and included via `templates/artwork_hero.html`.

### 9.2 Visual Anatomy

The artwork consists of four layers:

```
┌─────────────────────────────────────┐
│  1. Light System                    │
│  ┌───────────────────────────────┐  │
│  │  Ambient glow (radial)        │  │
│  │  Warmth gradient (gold)       │  │
│  │  Top light (white)            │  │
│  │  Vignette (subtle dark edges) │  │
│  └───────────────────────────────┘  │
│                                     │
│  2. Ribbon System                   │
│  ┌───────────────────────────────┐  │
│  │  Silk ribbon 1 (7px, blur)   │  │
│  │  Silk ribbon 2 (3.5px)       │  │
│  │  Silk ribbon 3 (2px, muted)  │  │
│  └───────────────────────────────┘  │
│                                     │
│  3. Halo System                     │
│  ┌───────────────────────────────┐  │
│  │  Primary halo (190px radius)  │  │
│  │  Secondary halo (150px, dash) │  │
│  │  Tertiary halo (100px, dash)  │  │
│  └───────────────────────────────┘  │
│                                     │
│  4. Identity Layer                  │
│  ┌───────────────────────────────┐  │
│  │  शून्य (Devanagari, 36px)    │  │
│  │  INFINITE INTELLIGENCE.       │  │
│  │  ZERO NOISE.                  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 9.3 Ribbon Behaviour

| Property | Ribbon 1 | Ribbon 2 | Ribbon 3 |
|----------|----------|----------|----------|
| Stroke width | 7px | 3.5px | 2px |
| Opacity | 0.2 | 0.25 | 0.15 |
| Blur | 2.5px | None | None |
| Animation duration | 20s | 18s | 22s |
| Gradient | `silk` | `silk` | `silk2` |

Ribbons animate continuously with a gentle undulating path using SVG `<animate>` with `calcMode="spline"` and `keySplines="0.4 0 0.6 1"`.

### 9.4 Halo Behaviour

| Property | Halo 1 | Halo 2 | Halo 3 |
|----------|--------|--------|---------|
| Radius | 190px | 150px | 100px |
| Stroke width | 0.5px | 0.35px | 0.25px |
| Opacity | 0.12 | 0.06 | 0.04 |
| Dash array | None | 5 15 | 3 12 |
| Rotation | 80s CW | 60s CCW | 45s CW |

Halos rotate continuously. The two outer halos rotate in opposite directions.

### 9.5 Gradients

| Gradient | Type | Colours | Purpose |
|----------|------|---------|---------|
| `ambient` | Radial | #faf8f5 → #f5f2ed → transparent | Base ambient light |
| `warmth` | Radial | #d4c0a8 → #a4865f → transparent | Gold warmth |
| `toplight` | Radial | #ffffff → transparent | Top-down illumination |
| `vignette` | Radial | transparent → #000000 4% | Edge darkness |
| `silk` | Linear | #d4bc94 → #c4a87a → #a4865f | Primary ribbon |
| `silk2` | Linear | #d4b888 → #c4a470 → #a4865f | Secondary ribbon |
| `halo` | Linear | #a4865f → #c4a87a → #a4865f | Halo arcs |

### 9.6 Negative Space

The hero artwork is intentionally sparse. The central area around the Devanagari text is kept clear — ribbons and halos orbit the perimeter, not the centre. The bloom effect sits behind the identity text as a soft glow.

### 9.7 Permitted Motion

- Ribbons undulate (20s, 18s, 22s cycles)
- Halos rotate (80s, 60s, 45s cycles)
- शून्य text gently pulses opacity (8s cycle, 0.76–0.82)
- No particle effects
- No floating elements
- No parallax
- Animation is suspended on `prefers-reduced-motion: reduce`

### 9.8 Future Illustration Rules

1. All future illustrations must use the same warm-neutral palette (gold tones, warm whites, muted beiges).
2. No illustration may introduce a new colour not in the palette.
3. No illustration may use solid gold fills — gold is used at low opacity (1–12%) for atmospheric effect.
4. SVG is the only permitted format for illustrations.
5. No raster images, no photographs, no complex gradients outside the defined system.
6. The central composition rule (subject at centre, activity at edges) is canonical.

---

## 10. Motion

### 10.1 Philosophy

Motion exists to communicate state. Never for decoration.

### 10.2 Easing Curves

| Token | Curve | Character |
|-------|-------|-----------|
| `--shunya-ease` | `cubic-bezier(0.22, 1, 0.36, 1)` | Default — smooth, natural |
| `--shunya-ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Exiting — decisive |
| `--shunya-ease-in` | `cubic-bezier(0.4, 0, 0.68, 0.06)` | Entering — gradual |

### 10.3 Duration Scale

| Token | Duration | Usage |
|-------|----------|-------|
| `--shunya-duration-fast` | 200ms | Hover states, colour transitions |
| `--shunya-duration-normal` | 400ms | Most transitions, panel slide |
| `--shunya-duration-slow` | 600ms | Page transitions, overlays |
| `--shunya-duration-slower` | 800ms | Complex transitions |
| `--shunya-duration-slowest` | 1200ms | Page enter animations |

### 10.4 Behaviour Specifications

#### 10.4.1 Hover Behaviour

| Element | Effect | Duration | Easing |
|---------|--------|----------|--------|
| Button | Opacity → 0.85 | 200ms | `--shunya-ease` |
| Card | Border colour → gold-light | 300ms | `--shunya-ease` |
| Navigation item | Background → 5% black | 200ms | `--shunya-ease` |
| Link | Colour → text | 300ms | `--shunya-ease` |
| Icon button | Opacity → 0.7 | 200ms | `--shunya-ease` |
| Chip | Border colour → hover | 200ms | `--shunya-ease` |

#### 10.4.2 Loading Behaviour

- **Page load:** Elements fade up (`translateY(14px) → 0, opacity 0 → 1`) with staggered delays (150ms, 300ms, 450ms, 600ms, 750ms)
- **Skeleton loading:** Shimmer animation (1.5s, 200% → -200% background position, `--shunya-ease`)
- **Content reveal:** Fade in (1.2s, `--shunya-ease`)
- **No spinner animations** — use skeleton shapes or content fade-in instead

#### 10.4.3 Page Transitions

- **Page enter:** Elements fade up in sequence (staggered 150ms delays)
- **Page exit:** No animation (instant removal)
- **Panel open:** Slide from edge (400ms, `--shunya-ease`)
- **Panel close:** Slide to edge (300ms, `--shunya-ease-out`)

#### 10.4.4 Object Transitions

- **Object open:** Panel slides right (400ms)
- **Object close:** Panel slides left (300ms)
- **Tab switch:** Content cross-fade (300ms)
- **List item add:** Fade in from bottom (400ms)
- **List item remove:** Fade out (200ms)

### 10.5 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

All motion must be suspendable. The reduced-motion media query collapses all animation and transition durations to effectively zero. This is not optional — it is a requirement for every component.

### 10.6 Prohibited Motion

- No parallax scrolling
- No confetti or celebration effects
- No spinning loaders
- No bouncing or spring animations
- No decorative hover effects (scale, rotate, wobble)
- No auto-scrolling carousels

---

## 11. Components

### 11.1 Button

**Purpose:** Primary call-to-action, secondary action, or tertiary/link-style action.

**Anatomy:**
```
┌──────────────────────┐
│  Label          →    │
└──────────────────────┘
```

**Spacing:**
- Height: 36px (9px vertical padding on 14px text)
- Horizontal padding: 22px (primary), 22px (outline)
- Border-radius: 10px (`--shunya-radius-sm`)
- Gap between icon and text: 6px

**Variants:**

| Variant | Background | Text | Border | Hover |
|---------|------------|------|--------|-------|
| Primary (`btn-p`) | `--shunya-text` | `--shunya-surface` | None | Opacity 0.85 |
| Outline (`btn-o`) | Transparent | `--shunya-text` | `--shunya-border` | Border → `--shunya-border-hover` |
| Ghost | Transparent | `--shunya-text-secondary` | None | Opacity 0.7 |

**Interaction states:**
- Default: As specified
- Hover: Opacity 0.85 (primary), border darkens (outline)
- Active: Opacity 0.75 (primary)
- Focus-visible: `outline: 2px solid var(--shunya-gold); outline-offset: 2px`
- Disabled: Opacity 0.4, cursor not-allowed

**Typography:**
- Font: Inter, 12px, weight 500 (--shunya-text-base for the button spec says 12px)
- Tracking: 0.02em
- Arrow icon: 14px, inline, transitions translateX(2px) on hover

**Usage rules:**
- One primary button per section
- Primary is always the dark text colour (`--shunya-text`)
- Gold is never used for buttons
- Button text is never uppercase

### 11.2 Card

**Purpose:** Grouped content container.

**Anatomy:**
```
┌──────────────────────────────┐
│  Title / Header    (optional) │
│  ─────────────────────────── │
│  Body content                │
│                              │
│  Footer / Meta    (optional) │
└──────────────────────────────┘
```

**Spacing:**
- Padding: 20px (standard), 16px (compact)
- Border-radius: 16px (`--shunya-radius-md`)
- Border: 1px solid `--shunya-border`
- Background: `--shunya-surface`

**Variants:**

| Variant | Usage |
|---------|-------|
| Default | Standard content grouping |
| Event | Real-time activity cards (landing page) |
| Intel | Intelligence pane cards (workspace right zone) |
| mz-item | Morning Zero attention items |

**Interaction states:**
- Default: `border: 1px solid var(--shunya-border)`
- Hover: `border-color: var(--shunya-border-hover)` or `var(--shunya-gold-light)` for event cards
- Active: N/A (cards are not buttons)

### 11.3 Input

**Purpose:** Text input for forms, search, and data entry.

**Anatomy:**
```
┌──────────────────────────────┐
│  Label (above)               │
│  ┌──────────────────────────┐│
│  │ Placeholder text...      ││
│  └──────────────────────────┘│
└──────────────────────────────┘
```

**Spacing:**
- Height: 38px (10px vertical padding on 14px text)
- Horizontal padding: 14px
- Border-radius: 10px (`--shunya-radius-sm`)
- Background: `--shunya-surface`
- Border: 1px solid `--shunya-border`

**States:**
- Default: `border: 1px solid var(--shunya-border)`
- Focus: `border-color: rgba(25,27,28,0.2)` (no outline, no blue ring)
- Placeholder: `color: var(--shunya-text-faint)`
- Disabled: `opacity: 0.4`
- Error: `border-color: #ff6b6b`

**Typography:**
- Font: Inter, 14px, weight 400
- Colour: `--shunya-text`
- Label: 12px, weight 500, `--shunya-text-secondary`, margin-bottom: 6px

### 11.4 Dropdown / Select

**Purpose:** Choosing from a list of options.

**Anatomy:**
```
┌──────────────────────┐
│  Selected option  ▼  │
└──────────────────────┘
┌──────────────────────┐
│  Option 1            │
│  Option 2            │
│  Option 3            │
└──────────────────────┘
```

**Spacing:**
- Trigger height: 38px
- Padding: 10px 14px
- Border-radius: 10px
- Menu padding: 6px 0
- Item padding: 8px 14px

**States:**
- Same as input
- Menu: `--shunya-surface` with `--shunya-shadow-lg`, no border
- Selected item: subtle background tint

### 11.5 Navigation

**Purpose:** Primary navigation within the workspace (left zone).

**Anatomy:**
```
┌──────────────────────────────┐
│  SECTION LABEL (uppercase)   │
│  ┌──────────────────────────┐│
│  │  Icon  Label          → ││
│  │  Icon  Label         23 ││
│  │  Icon  Label          → ││
│  └──────────────────────────┘│
└──────────────────────────────┘
```

**Spacing:**
- Section label: 10px, weight 600, uppercase, 0.06em tracking, `--shunya-text-faint`
- Nav item: 13px, weight 400, `--shunya-text-secondary`, padding 7px 16px
- Icon: 18px, margin-right 8px
- Badge: 10px, weight 500, `--shunya-text-tertiary`, float right

**States:**
- Default: `--shunya-text-secondary` background transparent
- Hover: `background: rgba(25,27,28,0.05)`, `color: var(--shunya-text)`
- Active: `background: rgba(25,27,28,0.07)`, `color: var(--shunya-text)`, `font-weight: 500`

### 11.6 Modal

**Purpose:** Focused task requiring user attention.

**Anatomy:**
```
┌──────────────────────────────────┐
│  Title              Close (×)    │
│  ─────────────────────────────── │
│  Body content                    │
│                                  │
│  [Cancel]  [Confirm]             │
└──────────────────────────────────┘
```

**Spacing:**
- Max width: 480px
- Border-radius: 16px (`--shunya-radius-md`)
- Padding: 24px
- Overlay: full-screen, `rgba(250,249,247,0.97)` with backdrop-filter blur

**Animation:**
- Enter: Scale up + fade in (400ms, `--shunya-ease`)
- Exit: Fade out (200ms, `--shunya-ease-out`)

### 11.7 Drawer / Side Panel

**Purpose:** Secondary content that doesn't require full navigation.

**Anatomy:**
```
┌──────────────┬─────────────────────┐
│  Main Content│  Drawer (340px)     │
│              │  ┌───────────────┐  │
│              │  │  Title        │  │
│              │  │  ──────────── │  │
│              │  │  Content...   │  │
│              │  └───────────────┘  │
└──────────────┴─────────────────────┘
```

**Spacing:**
- Width: 340px (matches right zone width)
- Padding: 16px
- Header: 16px, 11px uppercase

**Animation:**
- Slide in from right (400ms, `--shunya-ease`)
- Slide out to right (300ms, `--shunya-ease-out`)

### 11.8 Sidebar (Left Zone)

**Purpose:** Navigation and object graph.

**Specifications:**
- Width: 280px (desktop), 220px (tablet)
- Background: `--zone-left-bg` (`#f3f2f2`)
- Border-right: 1px solid `--shunya-border`
- Internal scroll on nav items

### 11.9 Table

**Purpose:** Structured data display (minimal usage).

**Spacing:**
- Cell padding: 10px 8px
- Font: 14px (body), 11px (header)
- Header: 10px or 11px, weight 600, uppercase, 0.06em tracking
- Border: bottom only, 1px solid `--shunya-border`
- Row hover: subtle background tint

**Rules:**
- No alternating row colours
- No horizontal borders between rows (bottom border only)
- No vertical borders
- No sticky header shadow — use a bottom border
- Tables are a last resort for structured data; prefer cards or lists

### 11.10 Timeline

**Purpose:** Chronological history of events, decisions, and changes.

**Anatomy:**
```
  ●  Title
  │  Meta information
  │
  ●  Title
  │  Meta information
```

**Spacing:**
- Item padding: 10px 0
- Gap between dot and content: 12px
- Dot size: 8px
- Connecting line: 2px, `--shunya-border`

**Dots:**
- Default: `--shunya-text-faint`
- Decision: `#74c0fc` (blue)
- Change: `#fab005` (yellow)
- Risk: `#fd7e14` (orange)
- Evidence: `#51cf66` (green)

### 11.11 Activity Card (Event Card)

**Purpose:** Real-time activity display on landing page.

**Anatomy:**
```
┌──────────────────────────────────┐
│  ●  Contract signed              │
│     New partnership agreement... │
│     Just now · Legal             │
└──────────────────────────────────┘
```

**Spacing:**
- Padding: 20px
- Gap between icon and content: 14px
- Icon container: 36px × 36px, border-radius 10px
- Title: 13px, weight 500
- Description: 11px, `--shunya-text-label`
- Timestamp: 10px, `--shunya-text-faint`

**Icon colours:**
- Gold: `rgba(164,134,95,0.1)` background
- Blue: `rgba(59,130,246,0.1)` background
- Emerald: `rgba(16,185,129,0.1)` background
- Amber: `rgba(245,158,11,0.1)` background

### 11.12 Notification

**Purpose:** Inform the user of system events.

**Types:**
- Flash messages (top of page, auto-dismiss at 5s)
- Status dot (bottom-right, green/yellow/off)
- Strip attention dot (top-right identity strip, colour-coded)

**Flash message:**
- Padding: 12px 16px
- Border-radius: 10px
- Font: 14px, weight 500
- Auto-dismiss: 5s, fade + slide-right

### 11.13 Empty State

**Purpose:** Guide the user when no content exists.

**Anatomy (center zone):**
```
┌──────────────────────────────────┐
│                                  │
│         [Icon 40px]              │
│                                  │
│      Heading (18px, 300w)       │
│                                  │
│   Description (13px, tertiary)   │
│   max-width: 320px               │
│                                  │
└──────────────────────────────────┘
```

### 11.14 Chart / Data Visualization

**Purpose:** Display quantitative information.

**Rules:**
- Minimal grid lines (no more than 3 horizontal lines)
- No 3D effects
- No gradient fills
- Single colour for data series (use `--shunya-gold` or `--shunya-text`)
- Use sparklines for inline data trends
- Full charts reserved for Intelligence pane

### 11.15 AI Response

**Purpose:** Display AI-generated content in conversation.

**Anatomy:**
```
┌──────────────────────────────────┐
│  Assistant message               │
│  (surface bg, border, right margin)│
│                                  │
│  ─── ─── ─── ─── ─── ─── ─── ───│
│  Human message                   │
│  (dark bg, white text, left margin)│
└──────────────────────────────────┘
```

**Spacing:**
- Human message: `background: var(--shunya-text)`, `color: white`, `margin-left: 32px`
- Assistant message: `background: var(--shunya-surface)`, `border: 1px solid var(--shunya-border)`, `margin-right: 32px`, `color: var(--shunya-text-secondary)`
- Padding: 10px 14px
- Font: 13px, line-height 1.5
- Border-radius: 10px

---

## 12. SHUNYA Identity Elements

### 12.1 The Sacred Elements

These elements define the brand. They are not to be modified, recoloured, resized, or repositioned without Founder approval.

### 12.2 SHUNYA Wordmark

| Property | Value |
|----------|-------|
| Typeface | Not specified (use Inter, weight 500, 13px) |
| Case | Uppercase: SHUNYA |
| Letter-spacing | 0.03em |
| Colour | `--shunya-text` |
| Companion | Gold dot (5px, `--shunya-gold`, 5px gap) |

**Usage:** Navigation bar, identity strip, footer. Always accompanied by the gold dot.

**Clear space:** Minimum 8px on all sides of the wordmark. No other elements may touch the wordmark.

### 12.3 शून्य Mark (Devanagari Identity)

| Property | Value |
|----------|-------|
| Script | Devanagari |
| Text | शून्य |
| Font | Noto Sans Devanagari, weight 500 |
| Size | 36px (hero artwork), 42px (hero spec) |
| Colour | `#1a1c1d`, opacity 0.78 |
| Letter-spacing | 0.06em |
| Animation | Gentle opacity pulse (0.76–0.82, 8s cycle) |

**Usage:** Exclusively in the hero artwork. Never used outside the artwork context.

**Clear space:** Minimum 40px on all sides. The शून्य mark must have clear space around it — no ribbons, halos, or other elements may pass through its bounding box.

### 12.4 Infinite Intelligence. Zero Noise.

| Property | Value |
|----------|-------|
| Typeface | Inter, weight 400 |
| Size | 9px |
| Colour | `#1a1c1d`, opacity 0.32 (line 1), 0.25 (line 2) |
| Letter-spacing | 0.25em (ultra) |
| Case | Uppercase |
| Line 1 | INFINITE INTELLIGENCE. |
| Line 2 | ZERO NOISE. |

**Usage:** Exclusively below the शून्य mark in the hero artwork. Never used outside the artwork context.

### 12.5 Gold Ring (Dot)

| Property | Value |
|----------|-------|
| Shape | Circle |
| Size | 5px (navigation, footer), 5px (identity strip), 6px (status) |
| Colour | `--shunya-gold` (`#a4865f`) |
| Usage | Brand identifier, navigation marker, section label |

**Usage rules:**
- Always accompanies the SHUNYA wordmark in navigation
- Used as a section label marker in the landing page
- Never used as a bullet point for lists
- Never recoloured

### 12.6 Hero Artwork

**Canonical file:** `static/img/artwork-hero.svg`
**Dimensions:** 736 × 425 (aspect ratio)
**Background:** `#f8f6f2` (or `--shunya-artwork-bg`)
**Border-radius:** 20px

**Placement rules:**
- Always positioned to the right of hero text on desktop
- Full-width on mobile, below hero text
- Never used as a standalone image without the hero text block
- Never cropped or resized to a different aspect ratio
- Minimum width: 320px (mobile)

### 12.7 Visual Ratios

| Context | Ratio |
|---------|-------|
| Landing page hero text to artwork | 42% text, 58% artwork (desktop) |
| Navigation height to page | 52px (fixed) |
| Left zone to total width | 280px / (1200px + gutters) |
| Right zone to total width | 340px / (1200px + gutters) |
| Content max width | 1200px |

### 12.8 Minimum Sizes

| Element | Minimum |
|---------|---------|
| SHUNYA wordmark | 11px font |
| Gold dot | 4px |
| शून्य mark | 24px font |
| Hero artwork | 320px width |
| Button | 80px width (minimum tap target) |

### 12.9 Clear Space

| Element | Clear Space |
|---------|-------------|
| SHUNYA wordmark | 8px all sides |
| Gold dot | 4px all sides |
| शून्य mark | 40px all sides |
| Hero artwork | 24px from other content |
| Logo in navigation | 10px from other nav items |

### 12.10 Misuse Examples (Prohibited)

- SHUNYA wordmark in any colour other than `--shunya-text`
- Gold dot recoloured, resized below 4px, or removed from navigation
- शून्य mark in any font other than Noto Sans Devanagari
- शून्य mark in bold or italic
- Hero artwork cropped, stretched, or used without the warm background
- "Infinite Intelligence. Zero Noise." in any size other than 9px in artwork
- Tagline used as a standalone marketing slogan outside the artwork
- Any identity element used as a watermark or background pattern

---

## 13. Screen Templates

### 13.1 Homepage (Landing Page)

**Canonical file:** `templates/landing.html`
**Structure:**
1. Navigation bar (52px, `--nav-bg`, gold dot + SHUNYA wordmark + nav links + Sign In)
2. Hero section (flex: text left 42%, artwork right 58%)
   - Headline: "Think clearly. Operate intelligently."
   - Subtitle: "An operating system for human organizations..."
   - CTA: "Get started →" (primary button) + "Learn more" (outline button)
   - Artwork: SVG with ribbons, halos, शून्य, tagline
3. Real-time section (section label + heading + 2×2 event card grid)
4. Industry strip (10-column grid of industry icons)
5. Footer (gold dot + SHUNYA + copyright + links)

**Responsive:**
- Tablet (≤960px): Stack hero vertically, 1-column events, 5-column industry
- Mobile (≤600px): 28px headline, stacked buttons, 5-column industry

### 13.2 Login

**Canonical file:** `templates/login.html`
**Structure:**
1. Identity strip (52px, gold dot + SHUNYA + "Home" link)
2. Centered card (max-width: 380px)
   - Heading: "Welcome back"
   - Subtitle: "Sign in to continue to your workspace."
   - Email field + Password field + Sign in button
3. Error state (inline, red)

### 13.3 Onboarding (Future)

**Not yet implemented.** Future onboarding screens must:
- Use the identity strip at top
- Use a centered card layout
- Follow the step-by-step flow with progress indicator
- Use calm, reassuring language
- No "wizard" patterns — use a linear step flow

### 13.4 Workspace

**Canonical file:** `static/css/workspace.css` defines the layout.
**Structure:**
1. Identity strip (44px, top bar with breadcrumbs, attention indicators, time)
2. Three-zone layout:
   - Left (280px): Navigation sections, search, object graph
   - Center (flex: 1): Object workspace, Morning Zero, or conversation
   - Right (340px): Intelligence pane

### 13.5 Object Page

Derived from the workspace template. The center zone shows:
- Object header (type label, name, meta)
- Object tabs (content, timeline, conversation, evidence, links, reasoning)
- Tab panels with appropriate content

### 13.6 AI Conversation

Derived from the workspace template. The center zone shows:
- Conversation messages (human right-aligned, assistant left-aligned)
- Input row (text input + send button)
- Conversation start button (when no conversation exists)

### 13.7 Search

Full-screen overlay:
- Centered search input (26px, weight 300, no border, transparent background)
- Search results appear below
- Overlay background: `rgba(250,249,247,0.97)` with backdrop blur
- Dismiss: Escape key

### 13.8 Calendar (Future)

**Not yet implemented.** Must follow:
- Workspace three-zone layout
- Calendar grid in center zone
- Intelligence pane in right zone (context about selected event)
- Events use the same card style as event cards

### 13.9 CRM (Future)

**Not yet implemented.** Must follow:
- Workspace three-zone layout
- Object list in left zone (or center)
- Object detail in center zone
- Related intelligence in right zone

### 13.10 Knowledge (Future)

**Not yet implemented.** Must follow workspace layout.

### 13.11 Settings (Future)

**Not yet implemented.** Must follow:
- Workspace three-zone layout
- Settings navigation in left zone
- Settings forms in center zone
- Context help in right zone

### 13.12 Mobile

- Single column layout
- No left or right zones
- Object content fills the full width
- Navigation via hamburger menu or bottom navigation
- Same typography and spacing scale, reduced to fit viewport

### 13.13 Tablet

- Two-column layout (left zone visible, right zone hidden)
- Left zone collapsed to 220px
- Same spacing scale, compacted padding

---

## 14. Design Review Checklist

### 14.1 The Seven Questions

Every new screen must answer these questions. If any answer is "no", the design is not ready.

| # | Question | Pass/Fail |
|---|----------|-----------|
| 1 | **Does it reduce cognitive load?** | ☐ |
| 2 | **Does it increase clarity?** | ☐ |
| 3 | **Does it feel recognisably SHUNYA?** | ☐ |
| 4 | **Does it reuse existing patterns?** | ☐ |
| 5 | **Is every element necessary?** | ☐ |
| 6 | **Is whitespace intentional?** | ☐ |
| 7 | **Would removing something improve it?** | ☐ |

### 14.2 The Emotional Hierarchy Check

Does the screen communicate in this order?

```
1. Calm           ☐
2. Understanding  ☐
3. Intelligence   ☐
4. Capability     ☐
```

If the order is reversed, the design is not ready.

### 14.3 Palette Compliance

- [ ] All colours are from the defined palette
- [ ] No new colours introduced without extending the palette
- [ ] Gold is used only for identity marks, section labels, and artwork
- [ ] Interactive elements use `--shunya-text`, not gold
- [ ] Semantic colours are used only for indicators

### 14.4 Typography Compliance

- [ ] Font sizes are from the type scale
- [ ] Playfair Display is used only for display headings
- [ ] Inter is used for all body text
- [ ] No bold Playfair Display
- [ ] Tracking values are from the tracking scale
- [ ] All-caps is used only for labels ≤ 10px

### 14.5 Spacing Compliance

- [ ] Spacing uses the 4px base unit
- [ ] Margins and padding follow the 8px rhythm
- [ ] No arbitrary spacing values
- [ ] Gutter is consistent across the screen

### 14.6 Motion Compliance

- [ ] All motion has a purpose (communicates state)
- [ ] Durations are from the duration scale
- [ ] Easing curves are from the easing scale
- [ ] Reduced-motion behaviour is implemented
- [ ] No decorative animations

### 14.7 Identity Compliance

- [ ] SHUNYA wordmark is accompanied by the gold dot
- [ ] शून्य mark is used only in the hero artwork
- [ ] Tagline is used only below the शून्य mark
- [ ] Identity elements have required clear space
- [ ] No misuse of identity elements

---

*This document is a living document. It will be updated as SHUNYA's visual language evolves. All changes require Founder approval.*

*End of SHUNYA Visual Design Bible v1.0*