# SHUNYA Component Inventory v1.0

> **Complete inventory of all SHUNYA components with states, variants, and usage rules.**
> This is the authoritative reference for what exists, what states it can be in, and how to use it correctly.

---

## Quick Reference

| # | Component | Variants | States | Page |
|---|-----------|----------|--------|------|
| 1 | Button | Primary, Outline, Ghost | Default, Hover, Active, Focus, Disabled | 3 |
| 2 | Card | Default, Event, Intel, mz-item, Compact | Default, Hover, Focus | 4 |
| 3 | Input | Text, Email, Password, Search, Textarea | Default, Focus, Placeholder, Disabled, Error, Read-only | 5 |
| 4 | Dropdown | Native, Custom | Closed, Open, Selected, Hover | 6 |
| 5 | Navigation Item | — | Default, Hover, Active | 7 |
| 6 | Tab | — | Default, Hover, Active | 8 |
| 7 | Modal | Alert, Confirm, Form | Open, Closed, Animating | 9 |
| 8 | Drawer | Right, Left | Open, Closed, Animating | 10 |
| 9 | Identity Strip | — | Default | 11 |
| 10 | Search Overlay | — | Open, Closed, Results | 12 |
| 11 | Timeline Item | Default, Decision, Change, Risk, Evidence | Default, Hover | 13 |
| 12 | Event Card | Gold, Blue, Emerald, Amber | Default, Hover | 14 |
| 13 | Conversation Message | Human, Assistant | Default | 15 |
| 14 | Flash Message | Success, Error, Warning | Visible, Dismissing, Hidden | 16 |
| 15 | Empty State | — | Default | 17 |
| 16 | Link Chip | — | Default, Hover | 18 |
| 17 | Health Indicator | Good, Warning, At-Risk, Critical, Silent | Default, Thinking | 19 |
| 18 | Skeleton Loader | Line, Short, Medium, Block | Animating, Static | 20 |
| 19 | Badge | Default, Success, Warning, Error, Info | Default | 21 |
| 20 | Section Label | Gold, Subtle | Default | 22 |
| 21 | Morning Zero | — | Default | 23 |
| 22 | Intel Card | — | Default | 24 |
| 23 | Object Header | — | Default | 25 |
| 24 | Reasoning Trace | — | Default | 26 |
| 25 | Health Bar | Good, Caution, At-Risk, Critical | Default | 27 |

---

## 1. Button

### Variants

| ID | Name | CSS Class | Usage |
|----|------|-----------|-------|
| BTN-01 | Primary | `btn-p` | Primary CTA, one per section |
| BTN-02 | Outline | `btn-o` | Secondary action |
| BTN-03 | Ghost | `btn-ghost` | Low-emphasis action |

### State Matrix

| State | BTN-01 | BTN-02 | BTN-03 |
|-------|--------|--------|--------|
| Default | `bg: #1a1c1d, color: white, radius: 10px, pad: 9px 22px` | `bg: transparent, color: #1a1c1d, border: 1px solid rgba(26,28,29,0.07)` | `bg: transparent, color: rgba(26,28,29,0.55)` |
| Hover | `opacity: 0.85` | `border: 1px solid rgba(26,28,29,0.14)` | `color: #1a1c1d` |
| Active | `opacity: 0.75` | Same as hover | Same as hover |
| Focus | `outline: 2px solid #a4865f, offset: 2px` | Same | Same |
| Disabled | `opacity: 0.4, cursor: not-allowed` | `color: rgba(26,28,29,0.35)` | `color: rgba(26,28,29,0.15)` |

### Content Rules

- Text: Inter 12px, weight 500, letter-spacing 0.02em
- No uppercase
- Max 30 characters
- Optional arrow icon (→) on right side for "next step" CTAs

### Usage Rules

- ✅ One primary button per section
- ✅ Use outline for secondary actions
- ✅ Use ghost for low-emphasis actions
- ❌ Gold never used for buttons
- ❌ No uppercase button text
- ❌ No icon-only buttons (except close ×)

---

## 2. Card

### Variants

| ID | Name | CSS Class | Padding | Hover | Usage |
|----|------|-----------|---------|-------|-------|
| CRD-01 | Default | `card` | 20px | Border hover | General content |
| CRD-02 | Event | `event` | 20px | Gold border hover | Landing page activity |
| CRD-03 | Intel | `intel-card` | 10px 12px | None | Intelligence pane |
| CRD-04 | mz-item | `mz-item` | 12px 16px | Border hover | Morning Zero items |
| CRD-05 | Compact | `card-compact` | 16px | Border hover | Dense content |

### State Matrix

| State | CRD-01 | CRD-02 | CRD-03 | CRD-04 | CRD-05 |
|-------|--------|--------|--------|--------|--------|
| Default | `bg: white, border: rgba(26,28,29,0.07), radius: 16px` | Same | Same | Same | Same |
| Hover | `border: rgba(26,28,29,0.14)` | `border: #d4c0a8` | None | `border: rgba(26,28,29,0.14)` | Same |
| Focus | Gold outline | Same | Same | Same | Same |

### Content Rules

- Title: 13px, weight 500 (event/intel)
- Description: 11px, `--shunya-text-label` (35% opacity)
- Timestamp: 10px, `--shunya-text-faint` (15% opacity)

---

## 3. Input

### Variants

| ID | Name | Type Attribute | Usage |
|----|------|----------------|-------|
| INP-01 | Text | `type="text"` | General text input |
| INP-02 | Email | `type="email"` | Email addresses |
| INP-03 | Password | `type="password"` | Password entry |
| INP-04 | Search | `type="search"` | Search fields |
| INP-05 | Textarea | `textarea` | Multi-line input |

### State Matrix

| State | Properties |
|-------|------------|
| Default | `bg: white, border: 1px solid rgba(26,28,29,0.07), radius: 10px, pad: 10px 14px, font: 14px` |
| Focus | `border: 1px solid rgba(26,28,29,0.2)` (no outline, no blue ring) |
| Placeholder | `color: rgba(26,28,29,0.15)` |
| Disabled | `opacity: 0.4, cursor: not-allowed` |
| Error | `border: 1px solid #ff6b6b` |
| Read-only | `bg: transparent, border: 1px solid rgba(26,28,29,0.07)` |

### Label

- Font: Inter 12px, weight 500, `color: rgba(26,28,29,0.55)`
- Position: Above input, margin-bottom: 6px

---

## 4. Dropdown / Select

### Variants

| ID | Name | Usage |
|----|------|--------|
| DDL-01 | Native `<select>` | Simple options, 3+ items |
| DDL-02 | Custom dropdown | Styled, 5+ items |

### State Matrix

| State | DDL-01 | DDL-02 |
|-------|--------|--------|
| Closed | Same as input | Same as input |
| Open | Browser native | `bg: white, shadow: 0 4px 24px rgba(26,28,29,0.06), radius: 10px, pad: 6px 0` |
| Selected | Browser default | Subtle bg tint on item |
| Hover (item) | Browser default | `bg: rgba(26,28,29,0.05)` |

---

## 5. Navigation Item

### Variants

| ID | Name | Usage |
|----|------|--------|
| NAV-01 | Section label | Uppercase group header |
| NAV-02 | Standard item | Navigable link |
| NAV-03 | Item with badge | Link with count indicator |

### State Matrix

| State | NAV-01 | NAV-02 | NAV-03 |
|-------|--------|--------|--------|
| Default | `font: 10px, weight 600, uppercase, color: rgba(26,28,29,0.15), pad: 8px 16px 4px` | `font: 13px, color: rgba(26,28,29,0.55), pad: 7px 16px` | Same + badge |
| Hover | None | `bg: rgba(25,27,28,0.05), color: #1a1c1d` | Same |
| Active | None | `bg: rgba(25,27,28,0.07), color: #1a1c1d, weight 500` | Same |

---

## 6. Tab

### Variants

Single variant only.

### State Matrix

| State | Properties |
|-------|------------|
| Default | `font: 12px, color: rgba(26,28,29,0.35), pad: 10px 16px, border-bottom: 2px solid transparent` |
| Hover | `color: rgba(26,28,29,0.55)` |
| Active | `color: #1a1c1d, border-bottom: 2px solid #1a1c1d` |
| Focus | Gold outline |

---

## 7. Modal

### Variants

| ID | Name | Usage |
|----|------|--------|
| MDL-01 | Alert | Single action, informational |
| MDL-02 | Confirm | Two actions (Cancel + Confirm) |
| MDL-03 | Form | Input form with actions |

### State Matrix

| State | Properties |
|-------|------------|
| Closed | `display: none` |
| Open | `display: block, bg: white, radius: 16px, max-width: 480px, pad: 24px, shadow: xl` |
| Animating | Scale(0.95→1) + opacity(0→1), 400ms |

### Overlay

- `bg: rgba(250,249,247,0.97), backdrop-filter: blur(12px)`

---

## 8. Drawer

### Variants

| ID | Name | Position | Usage |
|----|------|----------|-------|
| DRW-01 | Right | Slides from right | Supplementary content |
| DRW-02 | Left | Slides from left | (reserved) |

### State Matrix

| State | Properties |
|-------|------------|
| Closed | `transform: translateX(100%)` |
| Open | `transform: translateX(0), width: 340px` |
| Animating | 400ms ease, 300ms ease-out |

---

## 9. Identity Strip

### Variants

Single variant.

### State Matrix

| State | Properties |
|-------|------------|
| Default | `height: 44px, bg: #faf9f8, border-bottom: 1px solid rgba(26,28,29,0.07), pad: 0 20px` |

---

## 10. Search Overlay

### Variants

Single variant.

### State Matrix

| State | Properties |
|-------|------------|
| Closed | `opacity: 0, pointer-events: none` |
| Open | `opacity: 1, pointer-events: auto, bg: rgba(250,249,247,0.97), backdrop-filter: blur(12px)` |
| Results | Search results visible below input |

---

## 11. Timeline Item

### Variants

| ID | Name | Dot Colour | Usage |
|----|------|------------|-------|
| TML-01 | Default | `rgba(26,28,29,0.15)` | Generic |
| TML-02 | Decision | `#74c0fc` | Decision made |
| TML-03 | Change | `#fab005` | State change |
| TML-04 | Risk | `#fd7e14` | Risk identified |
| TML-05 | Evidence | `#51cf66` | Evidence collected |

### State Matrix

| State | Properties |
|-------|------------|
| Default | `dot: 8px, pad: 10px 0, title: 13px, meta: 11px` |
| Hover (title) | `opacity: 0.8` |

---

## 12. Event Card

### Variants

| ID | Name | Icon Background | Usage |
|----|------|----------------|-------|
| EVT-01 | Gold | `rgba(164,134,95,0.1)` | Legal, contracts |
| EVT-02 | Blue | `rgba(59,130,246,0.1)` | Finance, approvals |
| EVT-03 | Emerald | `rgba(16,185,129,0.1)` | Engineering, ops |
| EVT-04 | Amber | `rgba(245,158,11,0.1)` | Product, milestones |

### State Matrix

| State | Properties |
|-------|------------|
| Default | Same as card, no shadow |
| Hover | `border: 1px solid #d4c0a8` |

---

## 13. Conversation Message

### Variants

| ID | Name | Alignment | Usage |
|----|------|-----------|-------|
| MSG-01 | Human | Right (margin-left: 32px) | User messages |
| MSG-02 | Assistant | Left (margin-right: 32px) | AI messages |

### State Matrix

| State | MSG-01 | MSG-02 |
|-------|--------|--------|
| Default | `bg: #1a1c1d, color: white, radius: 10px, pad: 10px 14px, font: 13px` | `bg: white, border: 1px solid rgba(26,28,29,0.07), color: rgba(26,28,29,0.55), radius: 10px, pad: 10px 14px, font: 13px` |

---

## 14. Flash Message

### Variants

| ID | Name | Background | Text | Border |
|----|------|------------|------|--------|
| FLH-01 | Success | `#dcfce7` | `#166534` | `#bbf7d0` |
| FLH-02 | Error | `#fee2e2` | `#991b1b` | `#fecaca` |
| FLH-03 | Warning | `#fef3c7` | `#92400e` | `#fde68a` |

### State Matrix

| State | Properties |
|-------|------------|
| Visible | `opacity: 1, transform: translateX(0)` |
| Dismissing | `opacity: 0, transform: translateX(20px), transition: 300ms` |
| Hidden | `display: none` |

---

## 15. Empty State

### Variants

Single variant.

### State Matrix

| State | Properties |
|-------|------------|
| Default | `icon: 40px, 0.3 opacity, heading: 18px 300w, desc: 13px, centered, max-width: 320px` |

---

## 16. Link Chip

### Variants

Single variant.

### State Matrix

| State | Properties |
|-------|------------|
| Default | `bg: white, border: 1px solid rgba(26,28,29,0.07), radius: 20px, pad: 6px 14px, font: 12px` |
| Hover | `border: 1px solid rgba(26,28,29,0.14), color: #1a1c1d` |

---

## 17. Health Indicator

### Variants

| ID | Name | Colour | Usage |
|----|------|--------|-------|
| HTH-01 | Good | `#51cf66` | Everything nominal |
| HTH-02 | Warning | `#fab005` | Needs attention |
| HTH-03 | At-Risk | `#fd7e14` | Escalating |
| HTH-04 | Critical | `#ff6b6b` | Immediate action |
| HTH-05 | Silent | `rgba(26,28,29,0.15)` | Offline/inactive |

### State Matrix

| State | Properties |
|-------|------------|
| Default | `size: 6px, radius: 50%, display: inline-block` |
| Thinking | `animation: pulse 1.5s ease-in-out infinite` |

---

## 18. Skeleton Loader

### Variants

| ID | Name | Width | Usage |
|----|------|-------|-------|
| SKL-01 | Full line | 100% | Standard content |
| SKL-02 | Medium | 80% | Secondary content |
| SKL-03 | Short | 60% | Metadata, labels |
| SKL-04 | Block | Custom | Card/panel shapes |

### State Matrix

| State | Properties |
|-------|------------|
| Animating | `bg: shimmer gradient, animation: 1.5s` |
| Static | `bg: rgba(26,28,29,0.07)` |

---

## 19. Badge

### Variants

| ID | Name | Background | Text | Usage |
|----|------|------------|------|-------|
| BDG-01 | Default | `rgba(26,28,29,0.07)` | `rgba(26,28,29,0.35)` | Neutral |
| BDG-02 | Success | `#dcfce7` | `#166534` | Positive |
| BDG-03 | Warning | `#fef3c7` | `#92400e` | Attention |
| BDG-04 | Error | `#fee2e2` | `#991b1b` | Negative |
| BDG-05 | Info | `#dbeafe` | `#1d4ed8` | Informational |

---

## 20. Section Label

### Variants

| ID | Name | Colour | Usage |
|----|------|--------|-------|
| SCL-01 | Gold | `#a4865f` | Landing page sections |
| SCL-02 | Subtle | `rgba(26,28,29,0.15)` | Workspace panel headers |

---

## 21. Morning Zero

### Variants

Single variant — the default center zone state.

### Anatomy

- Greeting: "Good morning/afternoon" (22px, 300w, `--shunya-text`)
- Subtitle: contextual message (13px, `--shunya-text-tertiary`)
- Sections: Attention items, Recent activity, Opportunities
- Items: Same as mz-item card

---

## 22. Intel Card

### Variants

Single variant — the right zone intelligence card.

### Anatomy

- Label: 12px, weight 500, `--shunya-text`
- Meta: 11px, `--shunya-text-tertiary`
- Confidence: 10px, `--shunya-text-faint`

---

## 23. Object Header

### Variants

Single variant — the workspace object header.

### Anatomy

- Type label: 10px, uppercase, 0.06em tracking, `--shunya-text-tertiary`
- Name: 24px, 300w, -0.02em tracking, `--shunya-text`
- Meta: 12px, `--shunya-text-tertiary`
- Health dot: 6px, colour-coded

---

## 24. Reasoning Trace

### Variants

Single variant — the reasoning panel.

### Anatomy

- Step label: 10px, uppercase, 0.05em tracking, `--shunya-text-tertiary`
- Step content: 12px, `--shunya-text-secondary`, line-height 1.5
- Connecting line: 2px, `--shunya-border`

---

## 25. Health Bar

### Variants

| ID | Name | Fill Colour | Usage |
|----|------|-------------|-------|
| HBR-01 | Good | `#51cf66` | 75–100% |
| HBR-02 | Caution | `#fab005` | 50–74% |
| HBR-03 | At-Risk | `#fd7e14` | 25–49% |
| HBR-04 | Critical | `#ff6b6b` | 0–24% |

### Dimensions

- Bar width: 48px
- Height: 3px
- Radius: 2px
- Background: `rgba(26,28,29,0.07)`
- Fill transition: 400ms

---

*End of Component Inventory v1.0*