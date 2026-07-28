# Component Adaptation Specification (DNA-01.4)

**Status:** Design — Not Yet Ratified  
**Version:** 2.0  
**Dependency:** DNA-01 Device-Native Architecture, DNA-01.3 Device Matrix

---

## 1. Principle

Every component in SHUNYA defines its presentation for each experience class. No component inherits another class's layout. No component uses a single layout and attempts to scale it.

The constitution defines **what behaviour changes** between classes, not the exact pixel values. Exact dimensions, spacing, and sizing belong in the design system.

## 2. Specification Format

Every component defines three behavioural groupings per experience tier. The tier groupings represent shared behavioural patterns — the Experience Bible and Design System resolve per-class fidelity.

```
Component: [Name]

Compact:   [behavioural description — what changes]
Personal:  [behavioural description — what changes]
Studio:    [behavioural description — what changes]
```

---

## 3. Component Behaviours

### 3.1 Homepage

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Layout | Full-viewport scenes, compact padding | Full-viewport scenes, moderate padding | Full-viewport scenes, generous padding |
| Scene spacing | Tight — minimum breathing room | Moderate — comfortable separation | Generous — narrative pacing |
| शून्य reveal | Dominates viewport proportionally | Dominant but scaled to device | Full cinematic scale |
| Phase cards (Scene 5) | Stacked, centred, compact | Side-by-side with reduced padding | Side-by-side with descriptive text |
| Summary grid | Single column | Two-column grid | Three-column grid (capped width) |
| Footer | Stacked, centred | Inline, centred | Inline, centred |

### 3.2 Workspace Shell

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Column layout | Single column | Two-column or three-column landscape | Three-column |
| Panel navigation | Bottom tab bar, no side rail | Collapsible drawer or compact icon rail | Persistent labelled side rail |
| Context panel | Full-screen sheet overlay | Slide-out drawer or split-view | Persistent right column |
| Panel resize | Not supported | Drag handles on rails | Drag handles on rails |

### 3.3 Navigation (Top Bar)

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Height | Compact — minimal chrome | Moderate | Standard |
| Branding | Icon only | Icon + abbreviated name | Full branding |
| Breadcrumb | Back button only | Truncated to current level | Full breadcrumb visible |
| Search trigger | Icon → full-screen overlay | Icon → expandable panel | Inline input field |

### 3.4 Side Rail / Navigation

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Type | Bottom tab bar | Compact icon rail (landscape) or slide-out drawer (portrait) | Persistent labelled rail |
| Labels | Hidden (icon only) | Hidden with tooltip on hover | Always visible |
| Section headers | None | None when collapsed; visible when expanded | Visible |
| Capacity | Maximum 5 destinations | 5–8 destinations | 8–12 destinations |

### 3.5 Context Panel

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Position | Full-screen sheet (slide up) | Right column (landscape) or drawer (portrait) | Persistent right column |
| Content | Single focus at a time | Timeline + Intelligence stacked | Timeline + Intelligence side-by-side or stacked |
| Dismiss | Gesture (drag down) | Collapse button + gesture | Collapse button |
| Backdrop | Full overlay | Semi-transparent on drawer mode | None (persistent) |

### 3.6 Primary Content Area

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Width | Full viewport | Remaining space after panels | Remaining space (capped) |
| Padding | Compact | Moderate | Generous |
| Header | Back + title only | Title + back + actions | Full header with breadcrumb |

### 3.7 Object Cards

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Grid | Single column | Two columns | Three columns |
| Card density | Compact — essential info only | Moderate — key metadata visible | Full — previews and metadata |
| Interactions | Tap to select, highlight on tap | Tap + subtle hover | Full hover states |

### 3.8 Search

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Trigger | Bottom tab or top bar icon | Top bar icon | Inline input in top bar |
| Overlay type | Full-screen | Full overlay with backdrop | Dropdown panel |
| Filters | Chips or inline | Tabs in overlay | Sidebar in overlay |
| Results | Compact list | List with previews | List with previews |

### 3.9 Dialogs / Modals

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Position | Bottom sheet (slide up) | Centred overlay | Centred overlay |
| Width | Full-width minus margins | Proportionally sized | Sized to content |
| Dismiss | Swipe down + back gesture | Click outside + Esc | Click outside + Esc |

### 3.10 Tables

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Format | Key-value list (single column) | Priority columns only | Full column set |
| Row density | Touch-friendly spacing | Standard | Compact |
| Sorting | Sort dropdown | Column header click | Column header click |
| Selection | Long-press row | Checkbox column | Checkbox column |

### 3.11 Forms

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Layout | Single column | Single column | Multi-column where appropriate |
| Labels | Top-aligned | Top-aligned | Left-aligned |
| Submit | Full-width, sticky bottom | Full-width | Right-aligned |

### 3.12 Authentication

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Card width | Full-width minus margins | Centred card | Centred card |
| Brand strip | Compact (brand only) | Full (brand + navigation) | Full (brand + navigation) |
| Spacing | Generous for touch targets | Comfortable | Standard |

### 3.13 AI Interaction (Copilot)

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Position | Full-screen overlay | Context panel | Context panel |
| Input | Fixed at bottom of screen | Fixed at bottom of panel | Fixed at bottom of panel |
| Responses | Summary with expand option | Compact detail | Full detail |

### 3.14 Footer

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Layout | Stacked | Inline | Inline |
| Content | Minimal branding | Abbreviated branding | Full branding |

### 3.15 Empty States

| Behaviour | Compact | Personal | Studio |
|-----------|---------|----------|---------|
| Illustration | Icon or minimal | Reduced illustration | Full illustration |
| Description | Single line | Short paragraph | Full description |
| CTA | Single, full-width | Primary button | Primary + secondary buttons |

## 4. Cross-Component Guarantees

- Every component defined above must have an explicit behaviour for Compact, Personal, and Studio Experience groupings
- No component may use "same as Studio" as its Compact Experience behaviour — every class is intentionally designed
- Components not listed here must still conform to the Device-Native Architecture; their behaviour is defined by the Layout Matrix (DNA-01.6) and the core principles (DNA-01)
- Capability parity applies: if a feature is present in a component on Studio Experience, it must have an equivalent on Compact Experience — presented differently but functionally equivalent