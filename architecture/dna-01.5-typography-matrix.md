# Typography Specification (DNA-01.5)

**Status:** Design — Not Yet Ratified  
**Version:** 2.0  
**Dependency:** DNA-01 Device-Native Architecture

---

## 1. Principle

SHUNYA's typographic hierarchy must remain visually identical across all device classes while being physically appropriate to each form factor. The reader should not consciously notice the difference — but the text should feel natural on every screen.

The constitution defines **hierarchical relationships**, not pixel values. Exact type scales, line heights, and tracking belong in a design system that implements this constitutional spec.

The hierarchy is always:

```
Hero (one occurrence)
  → Section Headings
    → Body
      → Metadata
        → Labels
```

Navigation and buttons sit at their own level within the hierarchy.

## 2. Hierarchical Guarantees

### Hero
- There is exactly one hero element per page
- Hero typography shall **dominate the viewport** while preserving comfortable reading distance
- The hero is the first visual anchor the user encounters
- Hero text uses a lighter weight than other text, creating a refined, unhurried impression
- On smaller form factors, the hero reduces to remain proportionate to the viewport — it dominates without overwhelming

### Section Headings
- Section headings are visually distinct from body text through a combination of size and weight
- The heading hierarchy (H1 → H2 → H3) descends in visual prominence
- The difference between each heading level is perceptible at a glance
- Section headings establish clear visual boundaries between content sections

### Body Text
- Body text shall be **readable without zoom** on every supported device
- Body text line length shall not exceed comfortable reading distance (approximately 66–75 characters per line)
- Body text line height ensures no two lines appear to touch or merge
- Body text is the baseline against which all other levels are measured

### Metadata
- Metadata is **distinguishable from body text without being illegible**
- Metadata uses a smaller size and wider letter spacing to signal "supplementary information"
- Metadata is never used for primary content
- Metadata may use a reduced colour contrast relative to body text

### Labels
- Labels are the smallest typographic level
- Labels use a semibold weight to maintain legibility at small sizes
- Labels use the widest letter spacing to distinguish from metadata
- Labels are reserved for UI elements (tags, badges, field labels), never for content

### Navigation
- Navigation text is visually distinct from body text
- Navigation text uses medium weight and slight letter spacing
- Navigation is sized to be reliable as a touch target on touch devices

### Buttons
- Button text is slightly larger than body text for prominence
- Button text uses medium weight
- Button text is never smaller than the minimum readable size on any device

## 3. Relational Rules

These rules define the relationships between typographic levels:

| Relationship | Rule |
|-------------|------|
| Hero : Body | Hero is large enough that the viewer's eye is drawn to it first, without forcing the user to scan |
| H1 : Body | H1 is clearly the heading of a section; cannot be confused with body text |
| H2 : H1 | H2 is visibly subordinate to H1 |
| Body : Metadata | Body and metadata are distinguishable at a glance — the user never has to check which is which |
| Metadata : Label | Labels are visibly smaller and tighter than metadata |
| Navigation : Body | Navigation text is shorter and slightly denser than body text |
| Button : Body | Buttons are more prominent than body text to signal interactivity |

## 4. Font Family Guarantees

- Typefaces are **consistent across all device classes** — the same family is used everywhere
- Latin text uses a geometric sans-serif family (system-optimised)
- Devanagari text uses a family that harmonises with the Latin choice in weight and proportion
- Display text (decorative, pull quotes) may use a contrasting serif family
- Code/monospace uses a dedicated mono family

## 5. Constitutional Rules

- Font size must never be set per-element without reference to the canonical type hierarchy
- Type scales may vary between device classes but the **hierarchy ratios** must remain perceptually identical
- Viewport-relative units (vw) may be used for fluid scaling but must be bounded so that hero never becomes illegibly small or grotesquely large
- No component may invent its own typographic scale
- Font weight must be consistent per role across all device classes

## 6. Prohibited Patterns

- Setting a font size on a single element without referencing the canonical hierarchy
- Using viewport units directly on text without bounds
- Different type scales on different pages (inconsistent hierarchy)
- Per-component font size overrides that deviate from the canonical scale
- Using metadata sizing for primary content
- Using label sizing for any interactive element