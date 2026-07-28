# SHUNYA Design System Foundation

> **Canonical Reference — Phase X2A**
> This document formalizes the complete token hierarchy, interaction tokens, motion tokens, component contracts, composition rules, accessibility rules, attention rules, and confidence rules. Every visual decision must originate from a token. Hardcoded visual values are prohibited.

---

## Part 1: Design Token Hierarchy

### 1.1 Token Classification

Tokens are classified into four tiers. Each tier has different stability guarantees.

| Tier | Type | Change Policy | Examples |
|------|------|---------------|---------|
| **Global** | Immutable across the entire system | Never changed, only deprecated | `--color-brand-primary`, `--font-body`, `--space-4` |
| **Semantic** | Mapped from global tokens to functional roles | Changeable per theme | `--color-surface-primary`, `--text-base` |
| **Component** | Scoped to a single component | Changeable per component variant | `--button-padding`, `--card-radius` |
| **Contextual** | Scoped to a specific state or use case | Changeable per instance | `--button-primary-hover-bg`, `--card-selected-border` |

### 1.2 Color Token System

#### Brand Colors

| Token | Dark Value | Light Value | Usage |
|-------|-----------|-------------|-------|
| `--color-brand-primary` | `#D4A843` | `#B8923A` | Primary accent, active indicators, focus rings, links |
| `--color-brand-primary-subtle` | `rgba(212, 168, 67, 0.12)` | `rgba(184, 146, 58, 0.10)` | Subtle brand backgrounds, suggestion panel, hover areas |
| `--color-brand-secondary` | `#E8C66A` | `#C9A845` | Hover state for brand elements |

#### Surface Tokens

| Token | Dark | Light |
|-------|------|-------|
| `--surface-primary` | `#111111` | `#F5F3EE` |
| `--surface-secondary` | `#1A1A1A` | `#F0EDE6` |
| `--surface-tertiary` | `#242424` | `#E8E4DC` |
| `--surface-raised` | `#2A2A2A` | `#FFFFFF` |
| `--surface-hover` | `#2E2E2E` | `#E0DCD4` |

#### Text Tokens

| Token | Dark | Light |
|-------|------|-------|
| `--text-primary` | `#EDEDED` | `#1A1A1A` |
| `--text-secondary` | `#A0A0A0` | `#666666` |
| `--text-tertiary` | `#666666` | `#999999` |
| `--text-link` | `#D4A843` | `#B8923A` |
| `--text-on-brand` | `#1A1A1A` | `#FFFFFF` |
| `--text-inverse` | `#1A1A1A` | `#FFFFFF` |

#### Semantic Color Tokens

| Token | Dark | Light |
|-------|------|-------|
| `--color-success` | `#22C55E` | `#16A34A` |
| `--color-warning` | `#F59E0B` | `#D97706` |
| `--color-error` | `#EF4444` | `#DC2626` |
| `--color-info` | `#3B82F6` | `#2563EB` |
| `--color-success-bg` | `rgba(34,197,94,0.10)` | `rgba(22,163,74,0.08)` |
| `--color-warning-bg` | `rgba(245,158,11,0.10)` | `rgba(217,119,6,0.08)` |
| `--color-error-bg` | `rgba(239,68,68,0.10)` | `rgba(220,38,38,0.08)` |
| `--color-info-bg` | `rgba(59,130,246,0.10)` | `rgba(37,99,235,0.08)` |

#### Border Tokens

| Token | Dark | Light |
|-------|------|-------|
| `--border-primary` | `#333333` | `#E0E0E0` |
| `--border-secondary` | `#2A2A2A` | `#EBEBEB` |
| `--border-focus` | `#D4A843` | `#B8923A` |
| `--border-selected` | `#D4A843` | `#B8923A` |

#### Shadow Tokens

| Token | Dark | Light |
|-------|------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.30)` | `0 1px 2px rgba(0,0,0,0.05)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.35)` | `0 4px 6px rgba(0,0,0,0.07)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.40)` | `0 10px 15px rgba(0,0,0,0.10)` |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.50)` | `0 20px 25px rgba(0,0,0,0.15)` |

#### Confidence Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--confidence-very-high` | `#22C55E` | 0.90–1.00 |
| `--confidence-high` | `#D4A843` | 0.70–0.89 |
| `--confidence-moderate` | `#F59E0B` | 0.50–0.69 |
| `--confidence-low` | `#EF4444` | 0.30–0.49 |
| `--confidence-very-low` | `#DC2626` | 0.00–0.29 |

#### Opacity Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--opacity-invisible` | `0` | Hidden elements |
| `--opacity-subtle` | `0.08` | Subtle backgrounds, dividers |
| `--opacity-medium` | `0.12` | Brand subtle, hover backgrounds |
| `--opacity-strong` | `0.50` | Backdrop overlays |
| `--opacity-disabled` | `0.40` | Disabled interactive elements |
| `--opacity-visible` | `1` | Fully visible |

#### Blur Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--blur-subtle` | `4px` | Backdrop blur for Command Palette overlay |
| `--blur-medium` | `8px` | Backdrop blur for dialogs |

### 1.3 Typography Token System

#### Font Families

| Token | Value | Usage |
|-------|-------|-------|
| `--font-display` | `'Playfair Display', Georgia, serif` | Headings, object names, display text |
| `--font-body` | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` | Body text, UI elements, labels |
| `--font-mono` | `'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace` | Code, identifiers, system IDs |

#### Font Sizes

| Token | Value | Line Height | Usage Context |
|-------|-------|-------------|---------------|
| `--text-tiny` | `11px` | `16px` | Metadata, timestamps, labels |
| `--text-small` | `13px` | `20px` | Secondary text, confidence labels, summary body |
| `--text-base` | `15px` | `24px` | Body text, card content, section content |
| `--text-medium` | `17px` | `28px` | Large body, card titles, section headings |
| `--text-large` | `20px` | `28px` | Section titles, metric values |
| `--text-xl` | `24px` | `32px` | Object names, workspace titles |
| `--text-xxl` | `30px` | `40px` | Page titles, hero values |

#### Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `--weight-normal` | `400` | Body text |
| `--weight-medium` | `500` | Button labels, emphasized text |
| `--weight-semibold` | `600` | Subheadings, section titles |
| `--weight-bold` | `700` | Headings, object names |

#### Letter Spacing Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--tracking-tight` | `-0.01em` | Object names, display text |
| `--tracking-normal` | `0` | Body text |
| `--tracking-wide` | `0.02em` | Labels, minor text |
| `--tracking-uppercase` | `0.08em` | All-caps labels (section titles) |

### 1.4 Spacing Token System

#### Base Scale (4px increments)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-0` | `0` | Zero spacing |
| `--space-1` | `4px` | Micro spacing, icon gaps |
| `--space-2` | `8px` | Tight spacing, inline element gaps |
| `--space-3` | `12px` | Button padding, small element spacing |
| `--space-4` | `16px` | Card padding, default spacing |
| `--space-5` | `20px` | Panel section padding |
| `--space-6` | `24px` | Section gaps, large padding |
| `--space-8` | `32px` | Workspace margins, large gaps |
| `--space-10` | `40px` | Section margins |
| `--space-12` | `48px` | Page margins |
| `--space-16` | `64px` | Maximum spacing |

#### Semantic Spacing

| Token | Ref | Usage |
|-------|-----|-------|
| `--inset-sm` | `--space-3` | Button, chip padding |
| `--inset-md` | `--space-4` | Card, panel padding |
| `--inset-lg` | `--space-6` | Section padding |
| `--stack-sm` | `--space-2` | Tight vertical stack |
| `--stack-md` | `--space-4` | Default vertical stack |
| `--stack-lg` | `--space-6` | Section vertical spacing |
| `--inline-sm` | `--space-2` | Tight horizontal row |
| `--inline-md` | `--space-4` | Default horizontal row |
| `--inline-lg` | `--space-6` | Wide horizontal spacing |

### 1.5 Sizing Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--size-icon-sm` | `16px` | Small icons (in badges, inline) |
| `--size-icon-md` | `24px` | Standard icons (in buttons, labels) |
| `--size-icon-lg` | `32px` | Workspace switcher icons |
| `--size-icon-xl` | `48px` | Object header icons |
| `--size-touch-min` | `44px` | Minimum touch target (mobile) |
| `--size-header` | `56px` | Global nav bar height |
| `--size-header-mobile` | `48px` | Global nav bar height (mobile) |
| `--size-cp-default` | `300px` | Context panel default width |
| `--size-cp-min` | `240px` | Context panel minimum width |
| `--size-cp-max` | `400px` | Context panel maximum width |
| `--size-cp-collapsed` | `40px` | Context panel collapsed width |
| `--size-content-max` | `960px` | Content area maximum width |

### 1.6 Radius Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-none` | `0` | Separators, dividers |
| `--radius-sm` | `4px` | Buttons, inputs, focus rings |
| `--radius-md` | `6px` | Cards, panels, notifications |
| `--radius-lg` | `8px` | Modals, large containers, command palette |
| `--radius-xl` | `12px` | Executive summary background |
| `--radius-full` | `9999px` | Badges, pills, avatars, indicator dots |

### 1.7 Border Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--border-thin` | `1px` | Default borders, section dividers |
| `--border-medium` | `2px` | Focus rings, active indicators |
| `--border-thick` | `3px` | Selected tab indicator, active section indicator |

### 1.8 Elevation Tokens

| Token | z-index | Usage |
|-------|---------|-------|
| `--elevation-base` | `0` | Page content, cards on surface |
| `--elevation-sticky` | `10` | Sticky headers, section navs |
| `--elevation-dropdown` | `100` | Dropdowns, tooltips, popovers |
| `--elevation-overlay` | `200` | Modal backdrops, drawer overlays |
| `--elevation-modal` | `300` | Dialogs, drawers, command palette |
| `--elevation-toast` | `500` | Toast notifications |

### 1.9 Density Tokens

| Token | Value | Context |
|-------|-------|---------|
| `--density-comfortable` | `1` | Executive summary, reading content |
| `--density-standard` | `0.85` | Cards, panels, default |
| `--density-compact` | `0.7` | Tables, data lists, metadata |

Density tokens act as multipliers on spacing tokens. A `--density-compact` card uses `calc(var(--inset-md) * var(--density-compact))` internal padding.

### 1.10 Presence Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--presence-dot-size` | `8px` | AI Resident indicator dot |
| `--presence-dot-glow` | `0 0 6px var(--color-brand-primary)` | AI suggesting state glow |
| `--presence-dot-opacity-idle` | `0.3` | AI waiting state |
| `--presence-dot-opacity-active` | `1.0` | AI suggesting state |
| `--presence-transition` | `500ms` | AI state transitions (slow, calm) |

---

## Part 2: Motion Token System

### 2.1 Duration Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-instant` | `0ms` | Instant state changes (status badges, confidence bars) |
| `--duration-micro` | `100ms` | Hover effects, focus transitions |
| `--duration-small` | `200ms` | Close animations, disappear, micro-interactions |
| `--duration-standard` | `300ms` | Open animations, panel transitions, content reveals |
| `--duration-navigation` | `400ms` | Workspace switches, object navigation |
| `--duration-loading` | `1500ms` | Skeleton pulse cycle |

### 2.2 Easing Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | All entry and open animations |
| `--ease-in` | `cubic-bezier(0.4, 0, 0.68, 0.06)` | All exit and close animations |
| `--ease-pulse` | `ease-in-out` | Loading skeleton pulse |
| `--ease-linear` | `linear` | Progress bars, continuous indicators |

### 2.3 Motion Primitive Tokens

| Token | Duration | Easing | Animation |
|-------|----------|--------|-----------|
| `--motion-appear` | `var(--duration-small)` | `var(--ease-out)` | fade-in |
| `--motion-disappear` | `var(--duration-small)` | `var(--ease-in)` | fade-out |
| `--motion-slide-in` | `var(--duration-standard)` | `var(--ease-out)` | translateX/Y |
| `--motion-slide-out` | `var(--duration-small)` | `var(--ease-in)` | translateX/Y |
| `--motion-expand` | `var(--duration-standard)` | `var(--ease-out)` | scaleY or grid-rows |
| `--motion-collapse` | `var(--duration-small)` | `var(--ease-in)` | scaleY or grid-rows |
| `--motion-crossfade` | `var(--duration-small)` | `var(--ease-out)` | opacity |
| `--motion-glow` | `var(--duration-loading)` | `var(--ease-pulse)` | opacity oscillation |

### 2.4 Reduced Motion Override

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    --duration-instant: 0ms;
    --duration-micro: 0.01ms;
    --duration-small: 0.01ms;
    --duration-standard: 0.01ms;
    --duration-navigation: 0.01ms;
    --motion-appear: 0.01ms;
    --motion-slide-in: 0.01ms;
    --motion-expand: 0.01ms;
    --motion-crossfade: 0.01ms;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 2.5 Motion Contract (per animated element)

Every animated element must specify:

```
/* Motion Contract for [Element Name]
   Purpose: [why this motion exists]
   Duration: [token]
   Easing: [token]
   Entry: [what happens when the element appears]
   Exit: [what happens when the element disappears]
   Interruption: [what happens if the animation is interrupted mid-flight]
   Reduced-motion: [what happens when prefers-reduced-motion is active]
*/
```

---

## Part 3: Interaction Token System

### 3.1 Focus Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--focus-ring-color` | `var(--color-brand-primary)` | Focus outline color |
| `--focus-ring-width` | `2px` | Focus outline width |
| `--focus-ring-offset` | `2px` | Distance from element edge |
| `--focus-ring-style` | `solid` | Focus outline style |

### 3.2 Selection Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--selection-bg` | `var(--color-brand-primary-subtle)` | Selection highlight background |
| `--selection-text` | `var(--text-primary)` | Selection highlight text color |
| `--selected-bg` | `var(--surface-hover)` | Selected item background |
| `--selected-border` | `var(--border-selected)` | Selected item border |

### 3.3 Hover Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--hover-bg` | `var(--surface-hover)` | Hover background |
| `--hover-lift` | `0` | No lift on hover (buttons, cards do not float) |
| `--hover-transition` | `var(--duration-micro)` | Hover state transition speed |

### 3.4 Silence Tokens

Silence is an explicit interaction state in SHUNYA. These tokens govern when and how silence is expressed.

| Token | Value | Usage |
|-------|-------|-------|
| `--silence-threshold-idle` | `5000` | Milliseconds of user idle before system may transition from Silent to Attentive |
| `--silence-threshold-dismiss` | `2` | Number of suggestion dismissals before permanent silence on that object |
| `--silence-threshold-confidence` | `0.50` | Minimum confidence for system to exit Silent state |
| `--silence-duration-scanning` | `30000` | Milliseconds of scanning mode before AI may surface suggestions (30s) |
| `--silence-max-suggestions` | `3` | Maximum suggestions shown before returning to silence |
| `--silence-reset-interval` | `1800000` | Milliseconds before dismissed suggestion type may resurface (30 min) |
| `--silence-state-label` | `"Nothing requires your attention."` | Default message when silence is the active state |

### 3.5 Disabled Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--disabled-opacity` | `0.4` | Disabled interactive elements |
| `--disabled-cursor` | `not-allowed` | Disabled element cursor |

---

## Part 4: Component Contracts

Every component in SHUNYA has a formal contract that defines its behaviour, constraints, and relationships.

### 4.1 Contract Template

```typescript
interface ComponentContract {
  /** Human-readable purpose statement */
  purpose: string;
  
  /** What this component is responsible for */
  responsibilities: string[];
  
  /** Primitives this component may contain */
  allowedChildren: string[];
  
  /** Primitives this component may never contain */
  forbiddenChildren: string[];
  
  /** How this component behaves on interaction */
  interactionRules: {
    click?: string;
    hover?: string;
    focus?: string;
    keyboard?: string[];
    touch?: string;
  };
  
  /** Position in the visual hierarchy (1 = highest) */
  visualHierarchy: number;
  
  /** ARIA roles and attributes */
  accessibility: {
    role: string;
    attributes: Record<string, string>;
    keyboard: string[];
  };
  
  /** States this component can be in */
  states: string[];
  
  /** How this component renders in each density mode */
  density: {
    comfortable?: Record<string, string>;
    standard: Record<string, string>;
    compact?: Record<string, string>;
  };
}
```

### 4.2 Button Contract (Reference Implementation)

```typescript
const ButtonContract: ComponentContract = {
  purpose: "Trigger a single action on click or keyboard activation.",
  responsibilities: [
    "Communicate what happens on activation via label and optional icon",
    "Provide visual feedback on hover, focus, active, and disabled states",
    "Handle click, Enter, and Space activation"
  ],
  allowedChildren: ["TextBlock", "Icon", "Indicator"],
  forbiddenChildren: ["Button", "Input", "TabBar", "Dialog"],
  interactionRules: {
    click: "Execute the associated action immediately.",
    hover: "Background transitions to --hover-bg (100ms ease-out).",
    focus: "Focus ring appears (--focus-ring-width solid --focus-ring-color).",
    keyboard: ["Enter activates", "Space activates", "Tab moves focus"]
  },
  visualHierarchy: 2,
  accessibility: {
    role: "button",
    attributes: {
      "aria-disabled": "true when disabled",
      "aria-expanded": "true when button controls an expandable region",
      "aria-label": "when icon-only"
    },
    keyboard: ["Enter", "Space"]
  },
  states: ["default", "hover", "focus", "active", "disabled", "loading"],
  density: {
    standard: {
      padding: "var(--space-1) var(--space-3)",
      fontSize: "var(--text-small)",
      lineHeight: "28px"
    },
    compact: {
      padding: "var(--space-1) var(--space-2)",
      fontSize: "var(--text-tiny)",
      lineHeight: "24px"
    }
  }
};
```

### 4.3 Component State Contracts

Every component must implement the following states:

| State | When | Visual |
|-------|------|--------|
| `default` | Component is rendered and interactive | Normal token values |
| `hover` | Pointer is over the component | Background shift to `--hover-bg` |
| `focus` | Component has keyboard focus | `--focus-ring` visible |
| `active` | Component is being activated (mousedown, keydown) | Typically darker background |
| `disabled` | Component is not interactive | `--disabled-opacity` |
| `loading` | Component is in a pending state | Show skeleton or spinner variant |
| `error` | Component failed to load or save | Red border or `--color-error-bg` background |
| `empty` | Component has no data to display | Empty state message with CTA |

---

## Part 5: Accessibility Contract

### 5.1 Inherited ARIA Rules

Every component automatically inherits ARIA from its primitive type. No per-component ARIA work is needed for standard configurations.

| Primitive | Inherited Role | Inherited Attributes |
|-----------|---------------|---------------------|
| TextBlock | (none — implicit) | — |
| Icon | `img` (via CSS) | `aria-hidden="true"` |
| Button | `button` | `aria-disabled`, `aria-expanded` (conditional) |
| Input | `textbox` | `aria-label` from label, `aria-describedby` from hint |
| TabBar | `tablist` | `aria-orientation="horizontal"` |
| Tab | `tab` | `aria-selected`, `aria-controls` |
| TabPanel | `tabpanel` | `aria-labelledby` (references Tab id) |
| Dialog | `dialog` | `aria-modal="true"`, `aria-labelledby` |
| Panel | `complementary` | `aria-label` |
| Toast | `status` | `aria-live="polite"` |
| Alert | `alert` | `aria-live="assertive"` |

### 5.2 Focus Order Contract

| Rule | Implementation |
|------|----------------|
| **Global order** | Skip-link → Global Nav → Context Panel → Content Area → (overlays if active) |
| **Within zone** | Visual order (top to bottom, left to right) |
| **Skip link** | First focusable element. Skips Z1 and Z2, jumps to Z3 main content. |
| **Tab trap** | Dialogs, drawers, and command palette trap focus. Tab cycles within. |
| **Return focus** | On overlay close, focus returns to the element that triggered it. |
| **No invisible focus** | `display: none` and `visibility: hidden` elements are not in tab order. |
| **Focus visible always** | `:focus-visible` always shows the focus ring. Never `outline: none` without `:focus-visible` polyfill. |

### 5.3 Screen Reader Contract

| Situation | Announcement |
|-----------|-------------|
| New content loaded | `aria-live="polite"` region announces "Content loaded." |
| State change | `aria-live="polite"` announces the new state. |
| Error | `aria-live="assertive"` announces the error message. |
| Toast appears | `role="status"` announces the toast message. |
| Navigation | Page title updates. Focus moves to the new content heading. |

### 5.4 Touch Contract

| Rule | Implementation |
|------|----------------|
| **Minimum target** | 44x44px for all tappable elements on touch devices |
| **No hover dependency** | All hover interactions have a tap equivalent. No functionality depends on hover alone. |
| **Swipe gestures** | Supplement standard controls. Never replace them. Every swipe action has a visible button alternative. |
| **Touch feedback** | 100ms visual feedback on touch down. |

### 5.5 High Contrast Contract

| Rule | Implementation |
|------|----------------|
| **Contrast minimum** | WCAG AA (4.5:1) for text, WCAG AA (3:1) for non-text |
| **Focus ring** | 2px solid gold outline, regardless of theme |
| **Status colors** | Always accompanied by icon or text label. Never conveyed by color alone. |
| **Custom properties** | High-contrast mode can override all color tokens via `@media (prefers-contrast: high)`. |

---

## Part 6: Validation Matrix

### 6.1 Primitive-to-Domain Validation

Each primitive has been validated against 12 domains to confirm no domain assumptions:

| Primitive | CRM | ERP | Healthcare | Education | Legal | Finance | Manufacturing | Travel | Govt | Hospitality | Knowledge | Tech |
|-----------|-----|-----|-----------|-----------|-------|---------|-------------|-------|------|-------------|-----------|------|
| PrimaryObject | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ObjectHeader | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ExecutiveSummary | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| IdentityPanel | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| EvidenceBlock | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| RelationshipGraph | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Timeline | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| KnowledgeSurface | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| SuggestionPanel | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ConfidenceIndicator | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ActionSurface | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ContextPanel | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### 6.2 Prototype Reconstruction

Every screen in the Phase X2 prototype reconstructs entirely from documented primitives:

| Prototype Screen | Composition |
|-----------------|-------------|
| Global Nav | Logo + WorkspaceSwitcher + Breadcrumb + SearchInput + ThemeToggle + NotificationSurface(Icon) + UserMenu |
| Home Workspace | WorkspaceHeader + NotificationSurface(ChangeSummary) + Card × 4 (Icon + TextBlock + Indicator) |
| Object Workspace | ObjectHeader + ExecutiveSummary + SectionTabBar + IdentityPanel + RelationshipGraph + Timeline + KnowledgeSurface + SuggestionPanel + ReasoningSurface + ActionSurface + HistorySurface |
| Context Panel (no object) | PanelHeader(WorkspaceInfo) + PanelSection(RecentItems) + PanelSection(QuickActions) + AIResident |
| Context Panel (with object) | PanelHeader(ObjectInfo) + PanelSection(QuickActions) + PanelSection(Relationships) + PanelSection(RecentItems) + AIResident |
| Command Palette | CommandPalette(overlay): Input + TextBlock × N |
| Toast | NotificationSurface (Z5): TextBlock + Button(Dismiss) |

### 6.3 No Application-Specific Components

**Every prototype element** is built from the 30 documented composite primitives. Zero application-specific components exist.

---

## Part 7: Token Maintenance

### 7.1 Token Lifecycle

```
Proposed → Approved → Published → Deprecated → Removed
```

| Stage | Criteria | Duration |
|-------|----------|----------|
| **Proposed** | Token has a named value and a documented use case | — |
| **Approved** | Reviewed by design system team. Value is finalized. | — |
| **Published** | Available in token CSS file. Documentation updated. | Indefinite |
| **Deprecated** | Marked --deprecated-. New usage prohibited. | 2 release cycles |
| **Removed** | Token deleted from token file. Migration guide published. | After deprecation period |

### 7.2 Token Creation Rules

| Rule | Rationale |
|------|-----------|
| No new token without an existing component that needs it | Prevents speculative tokens |
| No token that duplicates an existing semantic value | Prevents token bloat |
| Global tokens cannot reference other global tokens | Prevent circular dependencies |
| Component tokens must reference global tokens | Ensure theme consistency |
| New tokens are appended, never inserted | Preserve token ordering |
| Token names are kebab-case, prefixed by category | Consistent naming convention |

### 7.3 Token Audit Cadence

| Audit | Frequency | Scope |
|-------|-----------|-------|
| Token usage scan | Monthly | Find unused tokens |
| Token value review | Quarterly | Verify values against brand guidelines |
| Token deprecation review | Per release | Remove expired deprecated tokens |
| Token documentation sync | Per release | Ensure token documentation matches token file |

---

## Canonical Status

This Design System Foundation, together with the Interaction Language (15_interaction_language.md), forms the complete reusable grammar for every future SHUNYA interface.

Every visual decision originates from a token.
Every component follows a contract.
Every interaction decomposes into primitives.
Every primitive inherits accessibility.
No application-specific components are required.
No domain assumptions are embedded.

---

*Canonical reference — Phase X2A. July 2026.*