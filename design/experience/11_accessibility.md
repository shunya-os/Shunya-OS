# SHUNYA Accessibility Canon

> **Canonical Reference — Phase X1**
> Defines accessibility requirements for all SHUNYA interfaces. Every component, interaction, and screen must conform.

---

## 1. Accessibility Philosophy

| Principle | Meaning |
|-----------|---------|
| **Built-in, not bolted on** | Accessibility is not a layer added after design. It is a design constraint from the first pixel. |
| **Every interaction is keyboard-accessible** | All functionality is available without a mouse or touch. |
| **Every element is screen-reader-accessible** | No content is exclusively visual. ARIA is comprehensive and correct. |
| **Every user chooses their experience** | Zoom, text size, motion, contrast — all user-controllable without breaking layout. |
| **No retrofitting** | Accessibility is verified during component development, not during QA. |

### Compliance Target

WCAG 2.2 Level AA minimum, AAA where feasible (contrast, keyboard, focus).

---

## 2. Keyboard-Only Operation

### Global Keyboard Navigation

All SHUNYA functionality is available via keyboard alone:

| Feature | Keyboard Path |
|---------|---------------|
| Navigate between zones | Tab (forward), Shift+Tab (backward) |
| Open command palette | Ctrl+K |
| Navigate workspace | Ctrl+Tab, Ctrl+Shift+Tab, Ctrl+[1-9] |
| Navigate sections | Alt+[1-9] |
| Navigate object history | Ctrl+[, Ctrl+] |
| Open context panel | Ctrl+\ |
| Execute action | Enter on focused action |
| Close overlay | Escape |
| Search | Ctrl+F or Ctrl+Shift+F |
| Open user menu | Ctrl+Shift+U |

### Tab Order

Tab order follows the visual layout:

1. Zone 1 (Global Navigation Bar) — left to right
2. Zone 2 (Context Panel) — top to bottom
3. Zone 3 (Content Area) — section nav → header → sections top to bottom

Interactive elements only appear in tab order. Non-interactive content is skipped.

### Focus Trapping

| Component | Focus Trap |
|-----------|------------|
| Command palette | Yes — Tab cycles within palette |
| Dialog/Modal | Yes — Tab cycles within dialog |
| Dropdown menu | Yes — Tab cycles within menu |
| Bottom sheet (mobile) | Yes — Tab cycles within sheet |
| Toast | No — focus remains on underlying content |

### Focus Indicator

| Property | Value |
|----------|-------|
| Style | 2px solid gold outline |
| Offset | 2px from element edge |
| Border radius | Matches element radius |
| Visible | Always (never hidden via `outline: none`) |
| Fallback | If gold blends with background, invert color |
| Animation | 100ms transition when focus moves |

```css
*:focus-visible {
  outline: 2px solid var(--color-border-focus);
  outline-offset: 2px;
}

*:focus:not(:focus-visible) {
  outline: none; /* Mouse click — no focus ring */
}
```

---

## 3. ARIA Implementation

### Landmarks

| Region | ARIA Role | Label |
|--------|-----------|-------|
| Global Navigation | `banner` | "Global navigation" |
| Context Panel | `complementary` | "Context panel" |
| Content Area | `main` | "Content" |
| Workspace Switcher | `navigation` | "Workspace switcher" |
| Section Navigation | `navigation` | "Section navigation" |
| Search | `search` | "Search" |
| Command Palette | `dialog` | "Command palette" |
| AI Resident | `region` | "AI assistant" |

### Component ARIA

| Component | Role | Attributes |
|-----------|------|------------|
| Button | `button` | `aria-label`, `aria-disabled`, `aria-expanded` |
| Card | `article` | `aria-label`, `aria-selected` |
| List | `list` | `aria-label` |
| ListItem | `listitem` | `aria-selected`, `aria-current` |
| TabBar | `tablist` | `aria-label` |
| Tab | `tab` | `aria-selected`, `aria-controls`, `aria-label` |
| TabPanel | `tabpanel` | `aria-labelledby` |
| Dialog | `dialog` | `aria-labelledby`, `aria-modal="true"`, `aria-describedby` |
| Tooltip | `tooltip` | `aria-describedby` (on trigger) |
| Alert | `alert` | `aria-live="assertive"` |
| Status | `status` | `aria-live="polite"` |
| ProgressBar | `progressbar` | `aria-valuenow`, `aria-valuemin`, `aria-valuemax` |
| Switch | `switch` | `aria-checked`, `aria-label` |
| Menu | `menu` | `aria-label`, `aria-orientation` |
| MenuItem | `menuitem` | `aria-disabled` |
| Tree (relationships) | `tree` | `aria-label`, `aria-multiselectable` |
| TreeItem | `treeitem` | `aria-expanded`, `aria-selected`, `aria-level` |

### Live Regions

| Event | Region | `aria-live` | Behavior |
|-------|--------|-------------|----------|
| Toast notification | `status` | `polite` | Announce after current speech |
| Error message | `alert` | `assertive` | Interrupt current speech |
| Content update (section) | `region` | `polite` | Announce when idle |
| AI suggestion | `status` | `polite` | "AI has 3 new suggestions" |
| Status change | `status` | `polite` | Announce new status |
| Progress update | `progressbar` | — | Announce on completion |

---

## 4. Focus Management

### Focus Rules

| Rule | Implementation |
|------|----------------|
| Focus starts at the topmost interactive element | On page load, focus goes to the search input (or first interactive element). |
| Focus moves to new content | When a dialog opens, focus moves to the first focusable element inside. |
| Focus returns on close | When a dialog closes, focus returns to the element that triggered it. |
| Focus never leaves viewport | Tab never moves focus outside the visible area. |
| Focusable elements are predictable | Tab order follows visual order. No unexpected jumps. |
| Focus is visible | Focus ring is always visible (2px gold outline). |

### Focus Restoration

When navigating through SHUNYA:

| Navigation | Focus Target |
|------------|-------------|
| Switch workspace | Search input in new workspace |
| Open object | Object header "Edit" button |
| Switch section | First focusable element in new section |
| Close dialog | Element that opened the dialog |
| Close panel | Content area |
| Command palette close | Search input |
| Back navigation | Previously focused element |

---

## 5. Color and Contrast

### Contrast Ratios (WCAG AA)

| Token | Dark Mode Ratio | Light Mode Ratio |
|-------|----------------|------------------|
| Text primary (EDEDED / 1A1A1A) | 16.5:1 (AAA ✓) | 18.0:1 (AAA ✓) |
| Text secondary (A0A0A0 / 666666) | 7.0:1 (AA ✓) | 5.8:1 (AA ✓) |
| Text tertiary (666666 / 999999) | 3.5:1 (AA ✗ for small text) | 3.0:1 (AA ✗ for small text) |
| Brand primary (D4A843 / B8923A) On surface | 4.7:1 (AA ✓) | 4.5:1 (AA ✓) |
| Success (22C55E / 16A34A) On surface | 6.5:1 (AA ✓) | 5.2:1 (AA ✓) |
| Error (EF4444 / DC2626) On surface | 5.5:1 (AA ✓) | 4.8:1 (AA ✓) |

### Notes

- Text tertiary is used only for placeholder text and non-essential metadata — WCAG AA exceptions apply.
- All status indicators use both color AND icon/shape for identification.
- Links are underlined on hover AND marked with a link icon for color-independent identification.
- Focus ring uses gold with sufficient contrast on all surfaces.

---

## 6. Screen Reader Support

### Semantic HTML

- Use native HTML elements (`<button>`, `<nav>`, `<main>`, `<article>`, `<section>`) with correct hierarchy.
- Headings use proper `<h1>` through `<h6>` nesting (h1: workspace name, h2: object name, h3: section titles).
- Lists use `<ul>` / `<ol>` with `<li>`.
- Tables use `<table>` with `<thead>`, `<th>`, `<tbody>`.

### Descriptive Labels

| Element | Label Strategy |
|---------|---------------|
| Icon-only buttons | `aria-label` with action description |
| Icon | `aria-hidden="true"` with invisible text label |
| Status badge | `aria-label="Status: Active"` |
| Confidence bar | `aria-label="Confidence: 72 percent"` |
| Metric card | `aria-label="Revenue: 2.4 million, up 12 percent"` |
| Card | `aria-label="Project Alpha: Active, 3 tasks remaining"` |
| AI suggestion | `aria-label="Suggestion: Approve budget. Confidence 72 percent"` |
| Chart/Graph | `aria-label` with data summary, `aria-describedby` for detailed table |

### Dynamic Content

- Use `aria-live` regions for dynamically updated content (see Live Regions table).
- Announce state changes: "Item moved to In Progress", "Decision approved".
- Do NOT announce every keystroke — only meaningful state changes.
- Announce loading state: "Loading content", then "Content loaded" on completion.

---

## 7. Reduced Motion

All motion honors `prefers-reduced-motion: reduce`.

### When Reduced Motion Is Active

| Feature | Behavior |
|---------|----------|
| Page transitions | Instant (no animation) |
| Panel opens/closes | Instant (no slide) |
| Section transitions | Instant (no fade) |
| Loading states | Content appears instantly (no skeleton fade) |
| Hover effects | Color changes instantly (no transition) |
| Microinteractions | Instant |
| Scroll-to-section | Instant jump (no smooth scroll) |

### Animation Override

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### No Animation Guarantee

Certain elements never animate even when reduced motion is not set:

- Status badges (instant color change)
- Text content
- Icons (no rotation, bounce, pulse)
- Focus indicators
- Progress bars (width changes without animation)

---

## 8. Zoom Support

### Browser Zoom

| Zoom Level | Expected Behavior |
|------------|-------------------|
| 100% | Default layout, all content visible |
| 150% | Layout adjusts. No horizontal scroll. Text remains readable. |
| 200% | Layout stacks. Cards become single column. Panels collapse. |
| 300%+ | All content accessible via scrolling. No overlap. All interactive elements functional. |

### Implementation

- All sizes use `rem` units (not `px`) for typography.
- Spacing uses relative units that scale with zoom.
- Fixed-position elements (Zone 1, Context Panel) have a `max-height: 100vh` with overflow scroll.
- No `position: fixed` elements that block content at high zoom.
- No `overflow: hidden` on body or main containers (prevents content clipping).

### Text Resize

- User can increase text size up to 200% without breaking layout.
- Text never truncates in a way that loses meaning.
- All containers grow with text content (no fixed-height containers for text).
- Buttons and interactive elements grow proportionally with text.

---

## 9. Large Text Support

| Element | Large Text Behavior |
|---------|---------------------|
| Headers | Line height adjusts. No truncation. |
| Section titles | Wrap to multiple lines if needed. |
| Breadcrumbs | Wrap or abbreviate (first + last segments). |
| Tab labels | Abbreviate to icon only, full label in tooltip. |
| Metric values | Scale down font size at large text settings. |
| Card content | Wraps naturally. Cards grow in height. |
| Table cells | Wrap or truncate with full text on hover/focus. |

---

## 10. Internationalization Readiness

### i18n Architecture

```typescript
// Example usage
t('workspace.decision.title')
// → "Decision Workspace" (en)
// → "Espace de décision" (fr)
```

### Requirements

| Requirement | Implementation |
|-------------|----------------|
| All strings are externalized | No hardcoded user-facing text in components. |
| RTL support | Layout uses logical properties (`margin-inline-start`, `padding-block-end`). |
| Date formatting | Use `Intl.DateTimeFormat`. Never hardcode date formats. |
| Number formatting | Use `Intl.NumberFormat`. Never hardcode number formats. |
| Pluralization | Use ICU message format or equivalent. |
| String concatenation | Never concatenate translated strings. Use template substitution. |

### Right-to-Left (RTL) Strategy

- All layout uses CSS logical properties (not physical `left`/`right`).
- Navigation reverses direction (swipe right for next in RTL).
- Text alignment defaults to `start` (not `left`).
- Icons that imply direction (arrows, chevrons) are mirrored in RTL.
- Grid and flex layouts use `gap` (not margin on individual items).

---

## 11. Accessibility Testing

### Automated Testing

| Tool | Scope | Frequency |
|------|-------|-----------|
| axe-core | All components | CI (every commit) |
| Lighthouse a11y audit | All pages | CI (per deployment) |
| Color contrast checker | Design tokens | Per token change |
| Keyboard navigation test | All flows | CI (every commit) |

### Manual Testing

| Test | Frequency | Criteria |
|------|-----------|----------|
| Full keyboard navigation | Per feature | All functionality accessible via keyboard |
| Screen reader (VoiceOver/NVDA) | Per feature | All content announced correctly |
| 200% zoom test | Per feature | No content loss or overlap |
| High contrast mode | Per feature | All content visible |
| Reduced motion | Per feature | No jarring transitions |

### Acceptance Criteria

Every component or feature is not considered complete until:

1. All keyboard interactions work (tab, enter, escape, arrows).
2. All interactive elements have accessible labels.
3. Focus management is correct (focus order, return on close).
4. Contrast meets WCAG AA minimum.
5. Screen reader correctly announces all content and state changes.
6. Works at 200% zoom without horizontal scroll.
7. Works with reduced motion enabled.