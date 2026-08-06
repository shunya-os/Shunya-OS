# SHUNYA Product Experience Constitution

**Directive:** Z-12 — Unified Product Experience
**Status:** Ratified
**Authority:** This document governs all visual and interaction decisions for SHUNYA. No surface may deviate.

---

## Preamble

SHUNYA shall no longer be experienced as separate surfaces: Marketing Website, Authentication Portal, Workspace, AI Chat, Dashboard. These cease to exist as separate experiences. The founder experiences only one product — SHUNYA — from landing until closing the browser.

This constitution defines every visual and interaction principle that guarantees that unified experience.

---

## 1. Visual Principles

### 1.1 One Visual Language

Every surface — homepage, authentication, onboarding, workspace, AI, settings, mobile, tablet, documentation, public pages — shares one design language. There is no perceptible transition between website and application.

### 1.2 Calm Computing

| Principle | Meaning |
|-----------|---------|
| 70% calm whitespace | Content breathes. Empty space is a design element, not wasted area. |
| 20% contextual intelligence | AI surfaces as understanding, not UI chrome. Recommendations appear in context, never as popups. |
| 10% controls | Actions are deliberate, sparse, and purposeful. Every control justifies its existence. |

### 1.3 Original Design

SHUNYA is not derived from any commercial product. No layout, navigation, interaction, or composition is recognisably copied. External references may inform principles (calmness, spacing, focus, readability, continuity) but the result is visually original.

### 1.4 Focus Over Features

Every screen answers immediately: What needs attention? Who is waiting? What changed? What should I do next? If a screen cannot answer these, it is incomplete.

---

## 2. Colour System

### 2.1 Primary Identity — Light Mode

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-bg` | `#FDFCF9` | Page background — warm off-white |
| `--sh-surface` | `#FFFFFF` | Card/sheet background |
| `--sh-surface-subtle` | `#F8F7F4` | Secondary surface (nav, sidebar) |
| `--sh-surface-raised` | `#FFFFFF` | Modals, dropdowns, elevated panels |
| `--sh-border` | `rgba(26, 28, 29, 0.08)` | All borders, dividers |
| `--sh-border-hover` | `rgba(26, 28, 29, 0.14)` | Border on hover/focus |
| `--sh-text` | `#1A1C1D` | Primary body text |
| `--sh-text-secondary` | `rgba(26, 28, 29, 0.55)` | Supporting text |
| `--sh-text-tertiary` | `rgba(26, 28, 29, 0.35)` | Placeholder, disabled, metadata |
| `--sh-text-faint` | `rgba(26, 28, 29, 0.15)` | Very faint borders |

### 2.2 Primary Identity — Dark Mode

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-bg` | `#141416` | Page background |
| `--sh-surface` | `#1C1C20` | Card/sheet background |
| `--sh-surface-subtle` | `#222226` | Secondary surface |
| `--sh-surface-raised` | `#28282E` | Modals, elevated panels |
| `--sh-border` | `rgba(255, 255, 255, 0.08)` | Borders |
| `--sh-border-hover` | `rgba(255, 255, 255, 0.14)` | Border on hover |
| `--sh-text` | `#EBEBEB` | Primary body text |
| `--sh-text-secondary` | `rgba(235, 235, 235, 0.55)` | Supporting text |
| `--sh-text-tertiary` | `rgba(235, 235, 235, 0.35)` | Placeholder, metadata |
| `--sh-text-faint` | `rgba(235, 235, 235, 0.12)` | Faint borders |

### 2.3 Brand Colours

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-purple` | `#6C4AE2` | SHUNYA purple — primary interaction colour |
| `--sh-purple-subtle` | `rgba(108, 74, 226, 0.08)` | Hover backgrounds, ghost states |
| `--sh-purple-glow` | `rgba(108, 74, 226, 0.15)` | Focus rings, selection |
| `--sh-gold` | `#A4865F` | SHUNYA gold — secondary identity colour |
| `--sh-gold-light` | `#D4C0A8` | Gold in light contexts |
| `--sh-gold-glow` | `rgba(164, 134, 95, 0.08)` | Subtle gold glow |

### 2.4 Semantic Colours

| Token | Value (Light) | Value (Dark) | Usage |
|-------|-------------|-------------|-------|
| `--sh-success` | `#2D6A4F` | `#4ADE80` | Success states |
| `--sh-warning` | `#B8860B` | `#FBBF24` | Warning states |
| `--sh-danger` | `#B91C1C` | `#F87171` | Error/danger states |
| `--sh-info` | `#3B82F6` | `#60A5FA` | Information |

### 2.5 Dark Mode as Equal First-Class

Dark mode is not an afterthought or a "developer mode." Both themes are designed simultaneously. The default theme is light (warm white). Dark mode toggles via a persistent user preference. Both themes pass WCAG AA contrast on all text elements.

### 2.6 Black as Accent, Not Canvas

Pure black (`#000000`) is never used as a background colour. In dark mode, backgrounds use warm dark greys (`#141416`, `#1C1C20`). Black is reserved for accent — very small elements, icons, or text highlights — and used sparingly.

---

## 3. Typography

### 3.1 Font Families

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-font-display` | `'Playfair Display', 'Georgia', serif` | Headings, hero text, signature moments |
| `--sh-font-body` | `'Inter', -apple-system, sans-serif` | Body text, UI labels, buttons |
| `--sh-font-mono` | `'SF Mono', 'Fira Code', monospace` | Code, data, metrics |
| `--sh-font-devanagari` | `'Noto Sans Devanagari', 'Nirmala UI', serif` | शून्य in Devanagari |

### 3.2 Type Scale

| Token | Size | Line-Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `--sh-text-xs` | 10px | 1.4 | 400 | Captions, labels |
| `--sh-text-sm` | 12px | 1.5 | 400 | Metadata, secondary text |
| `--sh-text-base` | 14px | 1.6 | 400 | Body text |
| `--sh-text-md` | 16px | 1.6 | 400 | Large body, input text |
| `--sh-text-lg` | 18px | 1.5 | 500 | Section headings |
| `--sh-text-xl` | 24px | 1.4 | 500 | Card titles, workspace headings |
| `--sh-text-2xl` | 32px | 1.3 | 400 | Page titles |
| `--sh-text-3xl` | 42px | 1.2 | 400 | Hero/landing headings |
| `--sh-text-4xl` | 56px | 1.1 | 350 | Large hero |
| `--sh-text-5xl` | 72px | 1.05 | 300 | Signature शून्य mark |

Playfair Display is used only for the शून्य mark and hero headings. Body, UI, and workspace text use Inter exclusively.

### 3.3 Line Heights

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-leading-tight` | 1.08 | Headings, hero |
| `--sh-leading-snug` | 1.25 | Card titles |
| `--sh-leading-normal` | 1.5 | Body text |
| `--sh-leading-relaxed` | 1.75 | Long-form reading |
| `--sh-leading-loose` | 2 | Call-to-action blocks |

### 3.4 Letter Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-tracking-tight` | -0.025em | Large headings (2xl+) |
| `--sh-tracking-normal` | 0 | Body text |
| `--sh-tracking-wide` | 0.02em | UI labels |
| `--sh-tracking-wider` | 0.06em | Small caps, secondary labels |
| `--sh-tracking-widest` | 0.12em | SHUNYA wordmark |
| `--sh-tracking-ultra` | 0.2em | All-caps metadata |

---

## 4. Spacing System

### 4.1 Grid Unit

The base unit is 4px (`--sh-unit: 4px`). All spacing is calculated from this unit.

### 4.2 Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-space-1` | 4px | Micro spacing (icon gaps) |
| `--sh-space-2` | 8px | Tight spacing (label to input) |
| `--sh-space-3` | 12px | Comfortable spacing (button padding) |
| `--sh-space-4` | 16px | Standard spacing (card padding) |
| `--sh-space-5` | 20px | Section spacing |
| `--sh-space-6` | 24px | Panel padding |
| `--sh-space-8` | 32px | Section margins |
| `--sh-space-10` | 40px | Large section gaps |
| `--sh-space-12` | 48px | Page section gaps |
| `--sh-space-16` | 64px | Hero spacing |
| `--sh-space-20` | 80px | Major page break |
| `--sh-space-24` | 96px | Landing section gaps |

### 4.3 Whitespace Principle

70% of every surface is whitespace. Controls cluster in the remaining 30%. Never fill space with decorative elements to avoid emptiness — emptiness IS the design.

---

## 5. Elevation & Surfaces

### 5.1 Elevation Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-shadow-sm` | `0 1px 4px rgba(26,28,29,0.03)` | Subtle surface separation |
| `--sh-shadow-md` | `0 2px 12px rgba(26,28,29,0.05)` | Cards, panels |
| `--sh-shadow-lg` | `0 4px 24px rgba(26,28,29,0.06)` | Modals, dropdowns |
| `--sh-shadow-xl` | `0 8px 40px rgba(26,28,29,0.08)` | Command palette, dialogs |
| `--sh-shadow-gold` | `0 4px 40px rgba(164,134,95,0.08)` | SHUNYA gold glow accent |

Dark mode shadows use `rgba(0,0,0,0.4)` equivalents at double opacity.

### 5.2 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-radius-sm` | 4px | Small UI elements |
| `--sh-radius-md` | 8px | Cards, inputs, buttons |
| `--sh-radius-lg` | 12px | Modals, panels |
| `--sh-radius-xl` | 16px | Large containers |
| `--sh-radius-full` | 50% | Avatars, icons |

### 5.3 Surface Rules

- Surfaces use subtle elevation (shadows), never heavy borders
- No more than 3 elevation layers visible simultaneously
- Elevated surfaces (modals, command palette) cast soft shadows with blur
- Glass effect (`--sh-glass: rgba(255,255,255,0.6)`) reserved for navigation bars only

---

## 6. Homepage — Product Preview (Article V)

### 6.1 Purpose

The homepage is not a marketing site. It is a preview of the operating system. The founder instantly understands: "This is how my work will look."

### 6.2 Layout

- Hero: शून्य wordmark + tagline + CTA "Begin"
- Live work demonstration: 3-4 cards showing real OS behaviour (relationships, follow-ups, payments, proposals)
- No pricing section, no documentation, no marketing filler
- No testimonials, no feature lists, no comparison tables
- Footer: minimal — brand mark + sign in link + copyright

### 6.3 Visual Design

- Warm white background (`--sh-bg: #FDFCF9`)
- SHUNYA Devanagari शून्य in Playfair Display, large, as hero
- Body in Inter
- Gold accent for the CTA button
- Core concept cards as subtle raised surfaces with purple icons
- Fade-in entrance animation (once, on page load)
- Max-width container: 860px content, centered

---

## 7. Authentication — Seamless Continuity (Article VI)

### 7.1 Principle

Authentication feels like entering an existing workspace, not switching applications. Same visual language, same typography, same spacing, same navigation philosophy. No visual discontinuity.

### 7.2 Layout

- Full-viewport centered card on warm white background
- शून्य wordmark in Devanagari at top (same as homepage)
- Tab toggle: Sign In / Create Account
- Forgot password as inline toggle (not separate page)
- Success state replaces form inline (no page transition)
- Subtle fade-in animation matching homepage entrance
- Max-width: 400px card

### 7.3 Visual Design

- Card: white surface with soft shadow (`--sh-shadow-md`)
- Background: `--sh-bg` (warm white) — identical to homepage
- Inputs: subtle border (`--sh-border`), purple focus ring (`--sh-purple-glow`)
- Primary button: purple (`--sh-purple`), white text
- Secondary actions: gold text, no background
- Error states: subtle red background, red text (never blocks or modals)
- Same Inter font throughout — no font family change between homepage and auth

---

## 8. Onboarding — Five Steps to First Execution

### 8.1 Principle

Onboarding is not a tour. It is the founder's first execution. Every step creates real data.

### 8.2 Steps

1. Identity (name + email) — already created during auth
2. Organization — business name, category, industry, country, currency, timezone
3. Auto-Objects — 26 foundational objects created automatically
4. First Action — AI-guided first outcome execution
5. Complete — transition to Executive Home

### 8.3 Visual Design

- Same warm white background as auth and workspace
- Step indicator: simple numbered dots (no progress bar)
- Each step is a centered card, max 480px
- Previous/Next navigation at bottom
- Back and Skip available on every step
- Same colour system as auth — purple for primary actions

---

## 9. Workspace — Executive Home (Article II, IV)

### 9.1 Principle

The workspace never opens to a generic dashboard. It always opens around the founder's current focus. "Current focus" is: the last object the founder was working on, or the Executive Home showing what needs attention.

### 9.2 Three-Zone Layout

```
┌────────────────────────────────────────────────────────┐
│ Zone 1: Navigation Bar (48px)                           │
│  शून्य    [Workspace Tabs]    Search    Theme  Avatar   │
├──────────┬─────────────────────────────────────────────┤
│ Zone 2:  │ Zone 3: Content Area                         │
│ Context  │ (object workspace / executive home /          │
│ Panel    │  conversation / settings)                     │
│ (280px)  │                                               │
└──────────┴─────────────────────────────────────────────┘
```

### 9.3 Zone 1 — Navigation Bar

- Height: 48px
- Background: `--sh-glass` with `backdrop-filter: blur(12px)`
- Left: शून्य wordmark (small, 14px, Devanagari)
- Center: Workspace tabs (Home, Objects, Conversations, Settings)
- Right: Search (Cmd+K trigger), Theme toggle, User avatar
- Border-bottom: `1px solid var(--sh-border)`

### 9.4 Zone 2 — Context Panel

- Width: 280px (collapsible to 0)
- Left border: `1px solid var(--sh-border)`
- Sections (top to bottom):
  1. Current Object (when in object workspace)
  2. Quick Actions (create new, import, etc.)
  3. Recent Items (last 5 visited objects)
  4. AI Resident (ambient, compact)
- Background: `--sh-surface-subtle` (slightly different from main content)
- Scrolling: independent scroll

### 9.5 Zone 3 — Content Area

- Background: `--sh-bg` (warm white)
- Padding: `--sh-space-6`
- Flexible: adapts to available width
- Container queries for internal component layout

### 9.6 Executive Home (No Active Object)

- Header: "Executive Home" + last-refreshed timestamp
- Priorities section: cards with urgency colour, recommended action
- Recent Activity: timeline list with type icons
- Active Commitments: compact cards with progress bar
- Object Summary: type counts
- System Status: pipeline health, runtime count
- Empty state: "Welcome to SHUNYA" with outcome-driven action buttons

### 9.7 Object Workspace (Active Object)

The workspace transforms around the active object:

```
┌─────────────────────────────────────────┐
│ Object Header: [Icon] Name · Type · Status │
├─────────────────────────────────────────┤
│ Tab Bar: Identity | Relationships |     │
│          Timeline | Knowledge | AI      │
├─────────────────────────────────────────┤
│ Active Tab Content                      │
│                                         │
│ (Panels composed per object type)       │
└─────────────────────────────────────────┘
```

### 9.8 70/20/10 in the Workspace

- 70% whitespace: generous padding, margins, breathing room around content blocks
- 20% intelligence: AI suggestions in context panel, insight cards, next-action hints
- 10% controls: action buttons, object creation, settings — visible but unobtrusive

---

## 10. AI Presence — Ambient Intelligence (Article VII)

### 10.1 Principle

The AI is ambient rather than dominant. It occupies the interface through understanding, recommendations, and execution — never as a chatbot that visually overpowers the workspace.

### 10.2 Presence Modes

| Mode | Appearance | When |
|------|------------|------|
| Ambient | No visible element. AI is listening. | Default state |
| Attentive | Compact suggestion count badge in Context Panel | Object loaded, context known |
| Suggestive | 2-3 contextual suggestions as inline text | After idle, on object open |
| Conversational | Expandable text input at bottom of Context Panel | Founder types |

### 10.3 AI Resident — Context Panel Section

- Compact text area: "Ask about your business…"
- Suggestion pills above input (2-3, context-aware)
- Response displayed inline within Context Panel (not a modal)
- The AI never takes over the main content area
- Responses include confidence indicator and source count
- No "thinking" animation — responses appear fully formed

### 10.4 AI Rules

- Every AI response produces work when possible (execution, not explanation)
- AI disappears when not needed — the Context Panel collapses naturally
- AI never uses celebratory language, congratulations, or gamification
- AI admits uncertainty directly: "I'm not certain. Here's what I know…"
- AI never interrupts the founder's current task

---

## 11. Navigation Philosophy

### 11.1 Grammar

- Tab-based workspace switching (Home → Objects → Conversations → Settings)
- Object navigation within workspace through clickable relationships
- Back navigation preserves workspace context (history stack per workspace)
- Breadcrumb: Workspace > Object > Section (always visible in content area header)
- Command palette: Cmd+K for universal search and actions
- Keyboard shortcuts: consistent across all workspaces

### 11.2 No Separate Pages

- Sign In / Create Account / Forgot Password: toggles within same card
- Settings: workspace tab, not separate page
- Object creation: inline modal within current workspace
- PDF reports: served via `/reports/` route, opened in same tab

### 11.3 Browser History

- SPA manages pushState for meaningful URLs
- Back button restores previous workspace state
- Bookmarkable object URLs: `/workspace/<type>/<id>`
- Page refresh restores last workspace via session

---

## 12. Responsive Behaviour (Article VIII)

### 12.1 Breakpoints

| Category | Width | Target Devices |
|----------|-------|----------------|
| Desktop | ≥ 1024px | 1920, 1600, 1440, 1366 |
| Tablet Landscape | 768-1023px | iPad Pro, iPad Air |
| Tablet Portrait | 480-767px | iPad mini, small tablets |
| Mobile | < 480px | iPhone, Pixel, Samsung Galaxy, foldables |

### 12.2 Desktop (≥ 1024px)

- Three-zone layout as described in §9
- Context Panel: 280px, always visible
- Content Area: remaining width
- Navigation bar: full width

### 12.3 Tablet Landscape (768-1023px)

- Three-zone layout preserved
- Context Panel: collapsible, default collapsed (toggle via hamburger/chevron)
- Navigation bar: same as desktop, text labels hidden on smaller screens
- Content Area: fills remaining width

### 12.4 Tablet Portrait (480-767px)

- Context Panel: hidden by default, slides in as overlay on tap
- Zone 1: compact nav (icon-only workspace tabs, search icon)
- Content Area: full width
- Object workspace tabs become scrollable pill row

### 12.5 Mobile (< 480px)

- Single-zone layout (no persistent context panel)
- Bottom navigation bar: 4 icons (Home, Objects, AI, Settings)
- Content Area: full width
- AI Resident: bottom sheet, triggered by AI icon in bottom nav
- Context Panel: bottom sheet overlay
- Object workspace: single-column, all sections stacked
- Touch targets: minimum 44×44px
- Prevent iOS zoom: body font-size minimum 16px on inputs

### 12.6 Responsive Principles

- Desktop, tablet, and mobile are intentionally designed — not scaled versions of each other
- Content is never hidden due to responsive constraints; it is reorganized
- Touch targets increase on smaller screens
- Navigation adapts but the information hierarchy remains constant
- The operating system feel is preserved at every viewport

---

## 13. Motion & Interaction (Article IX)

### 13.1 Philosophy

Interactions are deliberate and calm. Every animation reinforces continuity and confidence. No unnecessary motion, no distracting transitions, no excessive animation.

### 13.2 Timing

| Token | Duration | Usage |
|-------|----------|-------|
| `--sh-timing-micro` | 100ms | Hover states, micro-interactions |
| `--sh-timing-fast` | 200ms | Button presses, tab switches |
| `--sh-timing-normal` | 300ms | Panel opens, page transitions |
| `--sh-timing-slow` | 400ms | Modal open, large transitions |

### 13.3 Easing

All transitions use `ease-out` for entering, `ease-in` for exiting. No bounce, elastic, or playful easings.

### 13.4 Motion Rules

| Context | Motion | Duration |
|---------|--------|----------|
| Page/phase transition | Fade in + translateY(8px) | 400ms ease-out |
| Panel open | Slide right (from context panel) | 300ms ease-out |
| Modal open | Fade in + scale(0.98→1) | 300ms ease-out |
| Tab switch | Fade cross-fade | 200ms ease-out |
| Button hover | Background colour transition | 100ms ease-out |
| Command palette | Fade in + translateY(-4px) | 200ms ease-out |
| Toast notification | Slide in from top | 300ms ease-out |
| Theme toggle | Cross-fade (no colour transition) | 400ms ease-in-out |

### 13.5 Reduce Motion

When `prefers-reduced-motion: reduce` is active, all animations are disabled. Transitions become instant (0ms). No opacity transitions, no transforms.

---

## 14. Accessibility Standards

### 14.1 WCAG Compliance

All surfaces target WCAG AA minimum:
- Body text ≥ 4.5:1 contrast ratio
- Large text (≥ 18px bold / ≥ 24px) ≥ 3:1 contrast ratio
- Focus indicators ≥ 2px, visible on all interactive elements
- Touch targets ≥ 44×44px on touch devices

### 14.2 Keyboard Navigation

- All interactive elements reachable via Tab
- Tab order follows visual order (left to right, top to bottom)
- Escape closes modals, menus, overlays
- Cmd+K opens command palette
- Enter activates focused element
- Arrow keys navigate lists and tab bars
- Focus-visible ring on all keyboard-focused elements (purple, 2px)

### 14.3 ARIA

- Landmark roles on all major sections (banner, navigation, main, complementary, contentinfo)
- Live regions for dynamic content updates (AI responses, notifications)
- Role and aria-label on interactive elements without visible labels
- aria-expanded on collapsible sections
- aria-selected on tabs
- aria-current on active navigation items

### 14.4 Screen Reader

- All icons have accessible labels (aria-label or hidden text)
- AI responses announce via polite live region
- Loading states use aria-busy
- Error messages use role="alert"
- Skip-to-content link at top of every page

---

## 15. Component Principles

### 15.1 Skeleton, Empty, Content, Error

Every component implements four states:
1. **Skeleton** — loading placeholder matching final layout
2. **Empty** — honest state explaining what should exist, with action if applicable
3. **Content** — actual data display
4. **Error** — error description with retry action

### 15.2 No Placeholder Content

- No "lorem ipsum" anywhere
- No "Coming soon" badges
- No fake metrics or hardcoded counts
- Empty states are honest: "No customers yet. Add your first customer to get started."

---

## 16. Product Identity Invariants

These rules may never be violated:

1. **One OS.** Homepage, auth, onboarding, workspace, and settings share one visual language. No surface feels like a separate application.
2. **Calm first.** 70% whitespace is the default. Never fill space to avoid emptiness.
3. **Light-first.** The default theme is warm white. Dark mode is equal but not primary.
4. **Purple primary.** SHUNYA purple (`#6C4AE2`) is the single interaction colour. Gold (`#A4865F`) is secondary identity.
5. **Black accent.** Pure black is never a background. Only for accent text/icons.
6. **Object-centric.** The workspace opens around the founder's current focus, never a generic dashboard.
7. **Ambient AI.** AI is never a dominant chatbot. It lives in the Context Panel, embedded, not overpowering.
8. **No copied design.** Every layout, navigation, and interaction is originally SHUNYA's.
9. **No marketing homepage.** The homepage is a product preview. No pricing, documentation, testimonials, or feature lists.
10. **Seamless auth.** Authentication is a mode within the OS, not a separate page. Same visual identity.
11. **Intentional responsive.** Desktop, tablet, and mobile are designed independently. No scaled versions.
12. **Deliberate motion.** Every animation serves continuity. No decorative motion, no delays, no excess.

---

*This constitution is the permanent UX foundation for SHUNYA. It governs all surfaces, all interactions, and all future development. No feature, screen, or interaction may deviate from these principles without a constitutional amendment.*

**Ratified:** August 1, 2026
**Directive:** Z-12 — Unified Product Experience
**Authority:** SHUNYA Product Constitution