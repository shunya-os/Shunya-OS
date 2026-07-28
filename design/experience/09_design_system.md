# SHUNYA Design Tokens & Design System

> **Canonical Reference — Phase X1**
> The authoritative design system. Every pixel in SHUNYA derives from these tokens.

---

## 1. Design Token Philosophy

| Principle | Meaning |
|-----------|---------|
| **Token-first** | Every visual property is a named token. No hardcoded values anywhere. |
| **Semantic, not literal** | Tokens are named by purpose (--color-surface-primary), not by visual value (--color-gray-900). |
| **Themeable** | Tokens support dark and light mode without component changes. |
| **Scalable** | Adding a new component never requires adding a new token. Tokens are comprehensive from the start. |
| **Consistent** | Spacing, typography, and color use a constrained set of values. No "one-off" values. |

---

## 2. Color Tokens

### Brand Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--color-brand-primary` | `#D4A843` | `#B8923A` | Primary accent, active indicators, focus rings |
| `--color-brand-primary-subtle` | `rgba(212, 168, 67, 0.12)` | `rgba(184, 146, 58, 0.10)` | Subtle brand backgrounds, hover states |
| `--color-brand-secondary` | `#E8C66A` | `#C9A845` | Secondary accent, highlights |

### Surface Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--color-surface-primary` | `#111111` | `#FFFFFF` | Main background (Zone 3) |
| `--color-surface-secondary` | `#1A1A1A` | `#F8F8F8` | Context panel, secondary areas |
| `--color-surface-tertiary` | `#242424` | `#F0F0F0` | Cards, elevated surfaces |
| `--color-surface-raised` | `#2A2A2A` | `#FFFFFF` | Modals, dialogs, dropdowns |
| `--color-surface-hover` | `#2E2E2E` | `#EBEBEB` | Hover state for interactive surfaces |

### Text Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--color-text-primary` | `#EDEDED` | `#1A1A1A` | Primary body text |
| `--color-text-secondary` | `#A0A0A0` | `#666666` | Secondary text, metadata |
| `--color-text-tertiary` | `#666666` | `#999999` | Placeholder, disabled text |
| `--color-text-inverse` | `#1A1A1A` | `#FFFFFF` | Text on dark backgrounds |
| `--color-text-link` | `#D4A843` | `#B8923A` | Links and clickable text |
| `--color-text-on-brand` | `#1A1A1A` | `#FFFFFF` | Text on brand-colored backgrounds |

### Border Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--color-border-primary` | `#333333` | `#E0E0E0` | Default borders |
| `--color-border-secondary` | `#2A2A2A` | `#EBEBEB` | Subtle borders, dividers |
| `--color-border-focus` | `#D4A843` | `#B8923A` | Focus ring |
| `--color-border-selected` | `#D4A843` | `#B8923A` | Selected state |

### Semantic Colors

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `--color-success` | `#22C55E` | `#16A34A` | Success, completed, active |
| `--color-warning` | `#F59E0B` | `#D97706` | Warning, pending, caution |
| `--color-error` | `#EF4444` | `#DC2626` | Error, failed, critical |
| `--color-info` | `#3B82F6` | `#2563EB` | Information, neutral updates |
| `--color-success-bg` | `rgba(34,197,94,0.10)` | `rgba(22,163,74,0.08)` | Success background |
| `--color-warning-bg` | `rgba(245,158,11,0.10)` | `rgba(217,119,6,0.08)` | Warning background |
| `--color-error-bg` | `rgba(239,68,68,0.10)` | `rgba(220,38,38,0.08)` | Error background |
| `--color-info-bg` | `rgba(59,130,246,0.10)` | `rgba(37,99,235,0.08)` | Info background |

### Shadow Tokens

| Token | Dark Mode | Light Mode |
|-------|-----------|------------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` | `0 1px 2px rgba(0,0,0,0.05)` |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.35)` | `0 4px 6px rgba(0,0,0,0.07)` |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.4)` | `0 10px 15px rgba(0,0,0,0.1)` |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.5)` | `0 20px 25px rgba(0,0,0,0.15)` |

---

## 3. Spacing Tokens

### Base Scale (4px increments)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Micro spacing |
| `--space-2` | 8px | Tight spacing, icon padding |
| `--space-3` | 12px | Standard button padding |
| `--space-4` | 16px | Card padding, section spacing |
| `--space-5` | 20px | Panel padding |
| `--space-6` | 24px | Section gaps |
| `--space-8` | 32px | Large gaps, workspace margins |
| `--space-10` | 40px | Section padding |
| `--space-12` | 48px | Page margins |
| `--space-16` | 64px | Workspace padding |
| `--space-20` | 80px | Maximum spacing |

### Semantic Spacing

| Token | References | Context |
|-------|------------|---------|
| `--space-inset-sm` | `--space-3` | Button padding |
| `--space-inset-md` | `--space-4` | Card padding |
| `--space-inset-lg` | `--space-6` | Panel padding |
| `--space-stack-sm` | `--space-2` | Tight vertical stack |
| `--space-stack-md` | `--space-4` | Default vertical stack |
| `--space-stack-lg` | `--space-6` | Section spacing |
| `--space-inline-sm` | `--space-2` | Tight horizontal |
| `--space-inline-md` | `--space-4` | Default horizontal |
| `--space-inline-lg` | `--space-6` | Wide horizontal |

---

## 4. Typography

### Font Families

| Token | Value | Usage |
|-------|-------|-------|
| `--font-display` | `'Playfair Display', Georgia, serif` | Headings, display text (warm, elegant) |
| `--font-body` | `'Inter', -apple-system, sans-serif` | Body text, UI elements (clean, readable) |
| `--font-mono` | `'JetBrains Mono', 'Fira Code', monospace` | Code, IDs, data display |

### Font Sizes

| Token | Value | Line Height | Usage |
|-------|-------|-------------|-------|
| `--text-xs` | 11px | 16px | Metadata, labels |
| `--text-sm` | 13px | 20px | Secondary text, summaries |
| `--text-base` | 15px | 24px | Body text (default) |
| `--text-lg` | 17px | 28px | Large body, card titles |
| `--text-xl` | 20px | 28px | Section headings |
| `--text-2xl` | 24px | 32px | Object names |
| `--text-3xl` | 30px | 40px | Page titles |

### Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `--weight-normal` | 400 | Body text |
| `--weight-medium` | 500 | Emphasis, button labels |
| `--weight-semibold` | 600 | Subheadings |
| `--weight-bold` | 700 | Headings |

### Typography Scale

```
Object Name     — Playfair Display, 24px/32px, Bold
Section Title   — Inter, 17px/28px, Semibold
Card Title      — Inter, 15px/24px, Medium
Body Text       — Inter, 15px/24px, Normal
Summary         — Inter, 13px/20px, Normal
Metadata        — Inter, 11px/16px, Normal
Monospace       — JetBrains Mono, 13px/20px, Normal
```

---

## 5. Grid System

### Layout Grid

| Property | Value |
|----------|-------|
| Columns | 12 (desktop), 8 (tablet), 4 (mobile) |
| Gutter | 24px (desktop), 16px (tablet), 16px (mobile) |
| Margin | 32px (desktop), 24px (tablet), 16px (mobile) |
| Max width | 1440px (content area) |

### Content Grid

| Property | Value |
|----------|-------|
| Card columns | Auto-fill, min 280px, max 1fr |
| Section width | 100% with max-width 960px |
| Side panel width | 300px (default), resizable 240-400px |
| Full-width content | 100% (when context panel is collapsed) |

---

## 6. Elevation

| Token | Shadow | z-index Context |
|-------|--------|-----------------|
| `--elevation-flat` | None | Cards on surface |
| `--elevation-raised` | `--shadow-sm` | Hovered cards, dropdown |
| `--elevation-overlay` | `--shadow-md` | Tooltips, popovers |
| `--elevation-modal` | `--shadow-lg` | Modals, dialogs |
| `--elevation-top` | `--shadow-xl` | Command palette, full-screen |

### z-index Layers

| Layer | z-index | Elements |
|-------|---------|----------|
| Base | 0 | Page content |
| Sticky | 10 | Header, section nav |
| Dropdown | 100 | Dropdowns, tooltips |
| Overlay | 200 | Backdrop |
| Modal | 300 | Dialogs, panels |
| Command | 400 | Command palette, search overlay |
| Toast | 500 | Toasts, notifications |

---

## 7. Radius Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Input fields, small elements |
| `--radius-md` | 6px | Buttons, cards, panels |
| `--radius-lg` | 8px | Modals, dialogs |
| `--radius-xl` | 12px | Large containers |
| `--radius-full` | 9999px | Badges, pills, avatars |

### Border Width

| Token | Value | Usage |
|-------|-------|-------|
| `--border-thin` | 1px | Default borders |
| `--border-medium` | 2px | Focus rings, active borders |
| `--border-thick` | 3px | Emphasis borders (selected tab, status) |

---

## 8. Interaction Colors

### Button States

| State | Primary Button | Secondary Button | Ghost Button |
|-------|---------------|-----------------|--------------|
| Default | Brand bg, text-on-brand | Surface-tertiary bg, text-primary | Transparent, text-primary |
| Hover | Brand hover (lighter) | Surface-hover bg | Surface-hover bg |
| Active | Brand darker | Surface-hover darker | Surface-hover darker |
| Disabled | Opacity 0.4 | Opacity 0.4 | Opacity 0.4 |

### Link States

| State | Color | Underline |
|-------|-------|-----------|
| Default | `--color-text-link` | None |
| Hover | `--color-text-link` | Yes |
| Active | Lighter shade | Yes |
| Visited | `--color-text-link` (same) | None |

---

## 9. Dark Mode Strategy

### Philosophy

Dark mode is the **default** and **primary** mode. SHUNYA is designed for extended use in varied lighting conditions — dark mode reduces eye strain and visual fatigue.

### Strategy

| Aspect | Approach |
|--------|----------|
| Default | Dark mode is the default. Light mode is the alternative. |
| Switching | User can toggle in settings. System preference is respected on first visit. |
| Consistency | Components never distinguish between modes — they consume CSS variables. |
| Images | All images and icons support both modes. No white-background images. |
| Shadows | Dark mode shadows are larger and darker (black rather than gray). |
| Saturation | Slightly reduced saturation in dark mode for comfort. |

### CSS Implementation

```css
:root[data-theme="dark"] {
  /* Dark mode tokens from section 2 */
}

:root[data-theme="light"] {
  /* Light mode tokens from section 2 */
}
```

---

## 10. Light Mode Strategy

### Philosophy

Light mode is for well-lit environments where readability benefits from higher contrast.

### Differences from Dark Mode

| Aspect | Dark Mode | Light Mode |
|--------|-----------|------------|
| Surfaces | Dark (111) to dark gray (2A) | White (FFF) to light gray (F0) |
| Text | Near-white (ED) on dark bg | Near-black (1A) on white bg |
| Shadows | Dark, high opacity | Light, low opacity |
| Brand accent | D4A843 (gold) | B8923A (deeper gold) |
| Contrast | Slightly lower for comfort | Higher for readability |

---

## 11. Design Invariants

1. **Every visual property is a CSS custom property.** No hardcoded values in components.
2. **The spacing scale uses 4px increments.** No arbitrary spacing values.
3. **Typography uses exactly three font families.** No additional fonts.
4. **The brand color (gold) is the only accent color.** No secondary accent other than status colors.
5. **Dark mode is the default.** Light mode is derived from the same token system.
6. **Colors are semantic, not literal.** Tokens reference purpose (#surface-primary), not value (#111111).
7. **Radius values are from a fixed scale.** No arbitrary border-radius values.
8. **Elevation uses exactly 5 levels.** No in-between shadow values.
9. **All transitions use the standard timing curve.** No custom per-component curves.
10. **Every token has both a dark and light mode value.** No token exists for only one mode.