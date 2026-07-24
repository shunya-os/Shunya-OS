# SHUNYA — Living Design Language Notebook
> Phase Z1 · Captured during implementation, not before.
> Only patterns that survive actual implementation.

---

## 1. The Three-Zone Layout

**Discovered:** The workspace naturally divides into three distinct zones with different background tones. This creates a visual hierarchy without borders.

```
Left (280px, #f3f2f2)  → Tools & navigation
Center (flex: 1, #fafaf8) → Work surface
Right (340px, #ebebea)  → Intelligence & context
```

**Why it works:** The three tones create a west-to-east "light gradient" — left is slightly darker (tool-like), center is brightest (focus), right is slightly darker again (supporting). This is a discovered pattern, not a designed one.

## 2. The Identity Strip

**Discovered:** A 44px strip at the top provides all navigational context without a heavy toolbar. The hierarchy is:
- Left: brand mark → breadcrumb
- Right: status indicators → time

**Pattern:** Breadcrumbs use `#text-faint` separators (›) and `#text-tertiary` labels. This keeps navigation present but invisible.

## 3. Dark Text as the Only Interactive Colour

**Discovered:** Using `--shunya-text` (#1a1c1d) as the primary button and interactive colour instead of blue or gold produces a calmer, more authoritative interface. The user doesn't feel "pushed" toward actions.

**Pattern:** Primary buttons use dark bg + white text. Hover is opacity 0.85. No colour change.

## 4. Gold as Identity, Not Interaction

**Discovered:** Gold works beautifully as an identity marker (dot, section labels, artwork) but fails as an interactive colour. Users don't naturally associate gold with "clickable".

**Patterns:**
- Gold dot + SHUNYA wordmark = brand presence
- Gold section labels = you are here
- Gold artwork glow = atmosphere, not action

## 5. The 16px Card Radius

**Discovered:** 16px (`--shunya-radius-md`) is the "sweet spot" for card and panel corners. It's round enough to feel soft but not so round that it looks playful. 10px (`--shunya-radius-sm`) is better for buttons and inputs.

## 6. The 44px Identity Strip Height

**Discovered:** 52px (standard nav) felt too tall for an always-visible strip. 44px is the minimum height that still feels comfortable for touch targets and text.

## 7. Empty States Should Be Quiet

**Discovered:** Empty states work best when they're calm and informative, not upbeat. The pattern:
- Faint icon (40px, 0.3 opacity)
- 18px heading, weight 300
- 13px description, tertiary colour
- Max-width 320px

No "Let's get started!" or "You're all set!" — just factual information.

## 8. The Intelligence Pane as a Right Zone

**Discovered:** The right zone naturally becomes the "intelligence" layer. When no object is selected, it shows contextual hints. When an object is active, it shows relevant insights, related objects, and next actions.

**Pattern:** The right zone is read-only. All interaction happens in the center zone. The right zone provides context.

## 9. Skeleton Loading as a Sequential Narrative

**Discovered:** Instead of a spinner, showing sequential steps (Verifying → Loading → Building → Connecting → Preparing → Ready) creates a sense of progress and reassurance. Each step advances with a dot animation.

**Pattern:** 6 steps, 800ms each, subtle fade-up animation. The gold dot pulses at the center.

## 10. Tab Panels in Object Workspace

**Discovered:** Object pages need multiple perspectives (content, timeline, conversation, evidence, links, reasoning). Tabs work well because they're predictable and don't reload the page.

**Pattern:** Active tab gets a 2px bottom border in `--shunya-text`. Inactive tabs are `--shunya-text-tertiary`. No icons in tabs.

## 11. The Health System

**Discovered:** A three-level health system (good/caution/critical) with a small dot indicator is sufficient. Adding a 48px health bar provides more granularity for the executive view.

**Patterns:**
- Dot only: small contexts (timeline, object header)
- Dot + bar: executive dashboard, intelligence pane
- Colors: green (#51cf66), yellow (#fab005), orange (#fd7e14), red (#ff6b6b)

## 12. Morning Zero as the Default State

**Discovered:** Instead of a blank dashboard, the workspace should show a "Morning Zero" — a calm, curated view of what needs attention. This sets the tone for the session.

**Pattern:**
- Time-based greeting ("Good morning/afternoon/evening")
- Attention items (yellow dot)
- Info items (blue dot)
- Opportunities (green dot)
- "Quiet" footer when everything is fine

## 13. Navigation Faintness

**Discovered:** Navigation items use `--shunya-text-secondary` (55% opacity) by default, which makes them present but not demanding. Active items use `--shunya-text` (100%) with a subtle background tint. This reduces visual noise significantly.

## 14. The 10px Label Pattern

**Discovered:** 10px, uppercase, 0.06em tracking, `--shunya-text-faint` works for:
- Section labels in navigation
- Object type labels
- Timeline meta labels
- Tab headers (when not active)

It's readable but doesn't compete with content.

---

## Promoted into the Design Language

These patterns are now part of the design language and should be used in all future screens:

1. Three-zone layout with staggered background tones
2. 44px identity strip with breadcrumb navigation
3. Dark text as the only interactive colour
4. Gold reserved for identity, never interaction
5. 16px card radius (default), 10px button radius
6. The intelligence pane pattern (right zone, read-only)
7. Sequential loading narrative (6 steps, 800ms)
8. Tab-based object workspace (6 standard tabs)
9. Health indicator system (dot + bar, 4 levels)
10. Morning Zero as default workspace state
11. Navigation faintness (55% opacity default)
12. 10px uppercase label pattern

*Next phase: Build the first real AI reasoning experience, extract the final Design Bible from the product.*