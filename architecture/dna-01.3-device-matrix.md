# Experience Matrix (DNA-01.3)

**Status:** Design — Not Yet Ratified  
**Version:** 2.1  
**Dependency:** DNA-01 Device-Native Architecture

---

## 1. Purpose

This document describes the behavioural characteristics of each canonical experience class. It defines **how each class behaves** — not which pixels define it. Exact dimensions, type scales, and spacing values belong in a design system, not the constitution.

The implementation maps hardware (viewport dimensions, input capabilities, form factor) to these six abstract classes. The mapping is an implementation decision. The resulting user-visible behaviour must match these constitutional guarantees.

## 2. Compact Experience

### Layout Behaviour
- Single column, full-width content
- Content scrolls vertically in one pane
- No persistent side panels — all secondary content is overlaid or pushed to a subsequent view
- Navigation is anchored to the bottom of the viewport

### Navigation Behaviour
- Navigation controls are persistent at the bottom of the screen
- Maximum of five navigation destinations
- Gesture-driven navigation (swipe, tap) is the primary interaction
- No persistent side rail. No hamburger menu.

### Workspace Composition
- Primary object occupies the full viewport
- Secondary objects are presented as sheets that slide up from the bottom
- Supporting context is accessed through bottom sheet, push navigation, or as a tab
- Single panel visible at a time

### Interaction Characteristics
- All touch targets are generously sized for finger precision
- Swipe gestures for navigation and dismissal
- Tap for selection and activation
- Safe areas at top (status bar, notch) and bottom (home indicator) are respected

### Density
- High information density — minimal whitespace, compact cards
- Content prioritisation: most important information is always visible
- Decorative elements are minimised to preserve screen real estate

---

## 3. Personal Experience

### Layout Behaviour
- Two-column layout or single-column with drawer
- Navigation is collapsible — not persistent like Studio, not tabbed like Compact
- Content area dominates the viewport

### Navigation Behaviour
- Navigation is either a collapsible top bar or a slide-out drawer
- Navigation is NOT a bottom tab bar (Compact Experience behaviour does not scale to this width)
- When expanded, navigation includes icon labels

### Workspace Composition
- Primary content occupies the majority of the viewport
- Context panel is a slide-out drawer from the right edge
- Secondary panels may be split-view rather than full overlays
- Context toggles between visible and hidden

### Interaction Characteristics
- Touch-first with optional keyboard attachment
- Hover states are subtle — touch activation is the primary model
- Split-view resize is supported where applicable
- Safe areas are respected but less constrained than Compact Experience

### Density
- Medium density — more whitespace than Compact Experience
- Cards and panels have comfortable padding
- Content is not compressed to fit a small width

---

## 4. Shared Experience

### Layout Behaviour
- Three-column in landscape; two-column or three-column in portrait
- Navigation is persistent or easily revealed
- Layout resembles Workstation Experience but with touch-friendly sizing

### Navigation Behaviour
- Persistent side rail (compact, icon-only when collapsed)
- Rail expands to show labels when activated
- Top bar with breadcrumb for depth navigation
- Keyboard shortcuts when keyboard is attached

### Workspace Composition
- Three panels visible simultaneously in landscape
- Primary content occupies the flexible centre column
- Secondary column (left) for object lists, search results
- Context panel (right) for details, metadata, timeline
- Left and right panels are collapsible to icon-only

### Interaction Characteristics
- Touch + keyboard hybrid
- Drag handles for panel resize
- Pen support may be available
- Hover states are present but not required for any operation

### Density
- Medium density
- Generous padding and spacing
- Comfortable reading distance

---

## 5. Workstation Experience

### Layout Behaviour
- Three-column with persistent labelled rails
- Layout is designed for keyboard-driven interaction
- No gesture navigation

### Navigation Behaviour
- Persistent left rail with icon + label for every destination
- Top bar for breadcrumb, actions, and search
- Keyboard shortcuts are the primary navigation accelerator
- Command palette (keyboard-triggered) for power users

### Workspace Composition
- Three visible columns
- Left rail is always visible
- Context panel (right) is collapsible
- Primary content fills the remaining space

### Interaction Characteristics
- Mouse + keyboard
- Full hover state fidelity (colour, border, shadow)
- Right-click context menus
- Drag-and-drop for reordering, organising

### Density
- Standard density
- Comfortable whitespace without being sprawling
- Content fills available width without exceeding readable line lengths

---

## 6. Studio Experience

### Layout Behaviour
- Three-column with generous spacing and full interaction capabilities
- Layout assumes a large, high-resolution display
- Primary content has a maximum comfortable width

### Navigation Behaviour
- Persistent left rail with section headers, icons, and counts
- Breadcrumb in top bar for depth
- Full keyboard shortcut support
- Command palette (keyboard-triggered)

### Workspace Composition
- Three visible columns with generous padding
- Left rail shows sections with headers and badge counts
- Context panel includes metadata, timeline, AI insights
- Context panel may show multiple content types

### Interaction Characteristics
- Mouse + keyboard
- Drag-and-drop across panels
- Hover previews of content
- Keyboard-driven navigation is primary alongside mouse

### Density
- Standard density
- Ample whitespace
- Content is not compressed — the viewport is large enough to show everything

---

## 7. Orchestration Experience

### Layout Behaviour
- Three-column with expanded context and additional workspace features
- Layout assumes very large or multi-monitor setup
- Primary content width is capped for readability

### Navigation Behaviour
- Same as Studio Experience
- Workspace tabs in a horizontal top bar below main navigation
- Multi-window workspace support

### Workspace Composition
- Three columns with expanded context
- Context panel may split into two sub-panels (e.g., timeline + intelligence)
- Additional space enables: side-by-side object comparison, expanded timeline, multi-panel intelligence

### Interaction Characteristics
- Same as Studio Experience
- Multi-window workspaces
- Simultaneous panel interaction

### Density
- Low density — generous whitespace
- Slightly larger body text for comfortable reading at distance
- Content is not artificially stretched

## 8. Cross-Class Guarantees

| Guarantee | Description |
|-----------|-------------|
| Intentional navigation | Every class has a navigation model designed for its form factor. No class inherits another's navigation. |
|| Object continuity | The user's current object survives all experience class transitions. See DNA-01 §12. |
|| Capability parity | No class receives fewer features than another. See DNA-01 §13. |
| No occlusion | Content is never hidden behind device hardware, safe areas, or OS chrome. |
| No inference | The user on any class should never be able to identify which layout was designed first. |