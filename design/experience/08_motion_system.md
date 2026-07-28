# SHUNYA Motion System

> **Canonical Reference — Phase X1**
> Defines the complete motion language. Motion in SHUNYA is always narrative, never decorative.

---

## 1. Motion Philosophy

### Principles

| Principle | Meaning |
|-----------|---------|
| **Narrative, not decorative** | Every animation communicates where something came from, where it is going, or what changed. |
| **Calm, not flashy** | Animations are slow enough to follow, fast enough to not feel sluggish. No bouncing, no elastic, no dramatic effects. |
| **Spatial continuity** | Elements that move across the screen maintain spatial continuity. The user always knows where things are. |
| **Progressive, not simultaneous** | When multiple elements animate, they stagger. No simultaneous crowd movements. |
| **Respectful of attention** | Motion is gentle. No flashing, no pulsing, no attention-grabbing effects. |
| **Accessible by default** | All motion respects prefers-reduced-motion. Always. |

---

## 2. Motion Vocabulary

### Timing

| Duration | Context | Example |
|----------|---------|---------|
| 100ms | Micro-interactions | Button press, checkbox toggle, hover state |
| 200ms | Small transitions | Tooltip show/hide, inline element reveal |
| 300ms | Standard transitions | Panel open/close, section expand/collapse |
| 400ms | Navigation transitions | Workspace switch, object navigation |
| 500ms | Large transitions | Full-screen overlay open, dialog appear |
| 600ms+ | Emphasis transitions | Introduction animations, state celebrations |

### Easing

| Curve | When | Example |
|-------|------|---------|
| `ease-out` | Elements entering | Panels opening, content appearing |
| `ease-in` | Elements leaving | Panels closing, content disappearing |
| `ease-in-out` | Elements changing position | Sorting animations, drag reorder |
| `linear` | Continuous motion | Loading indicators, progress bars |
| `spring(0.3, 0.8, 0.1, 1.0)` | Natural feel | Drag physics, scroll momentum |

### Default CSS Easing

```css
:root {
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.4, 0, 0.68, 0.06);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --duration-micro: 100ms;
  --duration-small: 200ms;
  --duration-standard: 300ms;
  --duration-navigation: 400ms;
  --duration-large: 500ms;
}
```

---

## 3. Opening Animations

### Workspace Switch

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| New content | Slide in from right | 400ms | ease-out |
| Old content | Slide out to left | 300ms | ease-in |
| Context Panel | Fade content, keep structure | 300ms | ease-out |
| Header | Fade workspace name | 200ms | ease-out |

**Combined:** Old content slides left (300ms), new content slides in from right (400ms, 100ms delay). Content never overlaps. Background is a solid color (not transparent) to prevent double-vision.

### Object Open

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Content area | Zoom in 1.0→1.02 then settle | 300ms | ease-out |
| Header | Slide down from top | 200ms | ease-out |
| Summary | Fade in | 300ms (100ms delay) | ease-out |
| Section content | Stagger appear (top to bottom) | 50ms per item | ease-out |

### Panel/Drawer Open

| Type | Animation | Duration | Easing |
|------|-----------|----------|--------|
| Context Panel expand | Slide right, content fades in | 300ms | ease-out |
| Side panel | Slide in from right, backdrop fade | 300ms | ease-out |
| Drawer from bottom | Slide up | 400ms | ease-out |
| Full-screen overlay | Fade in + slight zoom | 300ms | ease-out |

### Dialog/Modal Open

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Backdrop | Fade in (0→0.5) | 200ms | ease-out |
| Dialog | Scale up (0.95→1.0) + fade | 300ms (50ms delay) | ease-out |

---

## 4. Closing Animations

Closing animations are the reverse of opening, with slightly shorter durations:

| Element | Duration | Easing |
|---------|----------|--------|
| Panel close, slide right | 250ms | ease-in |
| Dialog close, scale down + fade | 200ms | ease-in |
| Drawer close, slide down | 250ms | ease-in |
| Workspace leave, slide left | 300ms | ease-in |

### Rule

Closing animations are always faster than opening (approximately 2/3 duration). This creates a sense of returning to a neutral state quickly.

---

## 5. Transition Animations

### Section Tab Switch

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Old content | Fade out, slight vertical move | 150ms | ease-in |
| New content | Fade in, slight vertical move | 200ms | ease-out |

Overlapping fade (cross-fade). 50ms gap between old out and new in.

### Section Expand/Collapse

| Type | Animation | Duration | Easing |
|------|-----------|----------|--------|
| Expand | Height increase + content fade in | 300ms | ease-out |
| Collapse | Height decrease + content fade out | 200ms | ease-in |

Height is animated via CSS `grid-template-rows` transition (not `height`) for performance. Content uses `opacity` fade (not `display`).

### Object Switch (Forward/Back)

| Direction | Animation | Duration | Easing |
|-----------|-----------|----------|--------|
| Forward | Old slides left, new slides in from right | 400ms | ease-out |
| Backward | Old slides right, new slides in from left | 400ms | ease-out |

---

## 6. Loading States

### Skeleton to Content Transition

When content loads:

1. Skeleton placeholder is shown (no animation — it is already there).
2. Content fades in (300ms, ease-out).
3. Skeleton fades out simultaneously.
4. No opacity overlap period — content transitions instantly, then skeleton disappears.

### Progressive Loading

When sections load progressively:

1. Top section content appears (immediate, no animation — user is waiting).
2. Subsequent sections appear with 50ms stagger.
3. No global loading spinner for progressive loading.

### Full Loading (initial workspace load)

1. Global skeleton layout (header + content outline).
2. Content appears fragment by fragment as each section loads.
3. No spinner, no progress bar, no percentage.

---

## 7. Microinteractions

### Hover State

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Button | Background color change | 100ms | ease-out |
| Card | Subtle lift (translateY -2px) | 150ms | ease-out |
| Clickable item | Background tint | 100ms | ease-out |
| Link | Underline reveal | 200ms | ease-out |

### Focus State

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Focus ring | Appear (gold outline, 2px) | 100ms | ease-out |
| Focus movement | Ring transitions between elements | 150ms | ease-out |

### Selection State

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| List item select | Background highlight + left border | 200ms | ease-out |
| Toggle on | Background slide, color change | 150ms | ease-out |
| Checkbox | Check mark appear (scale) | 100ms | ease-out |

### Data Updates

| Event | Animation | Duration | Easing |
|-------|-----------|----------|--------|
| Cell value change | Brief yellow highlight (2s, then fade) | 300ms fade out | ease-out |
| Status change | Badge color transition | 300ms | ease-out |
| New item appears | Slide in + slight scale | 300ms | ease-out |
| Item removed | Shrink + fade | 200ms | ease-in |

---

## 8. Scrolling Behavior

### Smooth Scrolling

- All scroll behavior uses `scroll-behavior: smooth` for anchor jumps and tab-to-section navigation.
- Scroll animation duration: proportional to distance. 100px: 100ms. 1000px: 400ms.
- Scroll easing: ease-out (decelerating).

### Virtual Scroll

- Lists and tables use virtual scrolling for performance.
- No visible scroll animation for virtual content — items appear in place as they enter the viewport (no fade-in on viewport entry).
- Scrollbar is always visible (thin, 6px, with hover-expand to 10px).

### Scroll-triggered Animations

- Content does NOT animate on scroll entry. No parallax, no reveal-on-scroll.
- The only scroll-triggered behavior is the sticky header and the active section indicator update.

---

## 9. Reduced-Motion Accessibility

### Detection

All motion respects the user's `prefers-reduced-motion` media query:

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

### Behavior When Reduced Motion Is Active

| Normal | Reduced Motion |
|--------|---------------|
| Slide transitions | Instant (no animation) |
| Fade transitions | Instant (opacity 0→1 immediately) |
| Scale transitions | Instant (no transform) |
| Hover effects | Instant (no transition) |
| Loading skeletons | Fade in instantly |
| Microinteractions | Instant |
| Scroll-triggered position | No animation |

### Never-Animated Elements

These elements never animate, regardless of motion preference:

- Status badges (color changes are instant)
- Confidence bars (width changes are instant)
- Text content (never animated)
- Icons (no rotation, bounce, or pulse)

---

## 10. Motion Invariants

1. **No animation lasts longer than 600ms.** Attention is captured briefly or not at all.
2. **No element animates without a narrative purpose.** "Where did that come from?" must always have an answer.
3. **No flashing, pulsing, or strobing effects.** Ever. For any reason.
4. **No overlapping opacity transitions.** Content never appears through fading transparency.
5. **No parallax, parallax-like effects, or scroll-triggered reveals.**
6. **No element moves faster than 500px/s on screen.** Speed is moderated for comfort.
7. **Every animation can be disabled via prefers-reduced-motion.** No exceptions.
8. **Microinteractions are faster than navigation transitions.** 100-200ms vs 300-500ms.
9. **Opening is slower than closing.** Open: 300ms. Close: 200ms.
10. **Content appears in reading order** (top to bottom, left to right) with stagger.