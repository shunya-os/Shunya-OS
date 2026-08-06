# SHUNYA Living Experience Playbook

> **Canonical execution reference for the Living Experience Architecture (SX-14).**
> Every frontend implementation references this playbook. No UI shall drift from it.

---

## 1. Reality Model

Every visible interface shall originate from and represent this cycle:

```
┌─────────────┐
│   Reality   │  What exists — facts, data, current state
├─────────────┤
│    ─────────│── Understanding ── What it means for the user
├─────────────┤
│    ─────────│── Recommendation ─ What to do about it
├─────────────┤
│    ─────────│── Decision ─────── What the user chooses
├─────────────┤
│    ─────────│── Execution ────── What SHUNYA does
├─────────────┤
│    ─────────│── Observation ──── What changed as a result
├─────────────┤
│   Learning  │  What SHUNYA now knows for next time
└─────────────┘
```

### Every Screen Must Complete the Cycle

| Question | Maps To |
|----------|---------|
| What is happening? | Reality + Observation |
| Why does it matter? | Understanding |
| What should happen next? | Recommendation |
| How can SHUNYA help? | Decision + Execution |

A screen that does not complete this cycle is incomplete.

### No Isolated Components

Every visible element must trace back to one of the seven stages. Elements that cannot be traced shall not exist.

---

## 2. Experience Grammar

Every visible interface element shall represent one or more of these semantic building blocks:

| Block | Definition | Example |
|-------|------------|---------|
| **Reality** | A fact about the world or the user's data | "INV-003 is overdue" |
| **Understanding** | What a reality means for the user | "This affects your cash flow" |
| **Recommendation** | A suggested course of action | "Send a reminder to Acme Corp" |
| **Action** | An executable operation | "Create invoice" button |
| **Evidence** | Data supporting a claim | "Payment is 5 days late" |
| **Relationship** | A connection between realities | "This client has 3 active proposals" |
| **Timeline** | Chronological sequence of events | "Created 2d ago, modified 4h ago" |
| **Confidence** | Certainty level of a claim | "High confidence — 80% match" |
| **Learning** | New knowledge SHUNYA acquired | "Client prefers email over phone" |

No interface element shall introduce a visual category not defined in this grammar.

---

## 3. Human Language

Users interact with natural language, never technical terminology:

```
Customers · Trips · Companies · Documents · Conversations
Payments · Friends · Projects · Proposals · Tasks
```

Never: Entities · Objects · Workspace IDs · Internal models · Database terminology

Every label, message, and notification shall use natural human language. Error messages shall not display technical details.

---

## 4. Explainability

Every AI recommendation shall support explanation. Every explanation shall expose:

| Element | Required | Example |
|---------|----------|---------|
| Why this recommendation | Always | "Because INV-003 is 5 days overdue" |
| Evidence supporting it | Always | "Customer has not responded to 2 reminders" |
| Confidence level | Always | "High (80%) based on payment history" |
| Relevant assumptions | When applicable | "Assuming email address is valid" |
| Suggested alternatives | When applicable | "Alternative: Call instead of email" |

Trust shall emerge through transparency rather than marketing.

---

## 5. Living Interface Rules

The interface changes because **reality changes**. It shall never change merely because time passes.

Adaptive behavior shall respond to:
- Changing commitments
- Communications
- Relationships
- Opportunities
- Risks
- Execution state
- User habits
- Business context

The interface shall evolve quietly throughout the day without becoming visually unstable. Layout shifts shall be intentional and meaningful. Cosmetic rotation (carousels, rotating hero text) is prohibited.

---

## 6. Capability Evolution

Capabilities shall not exist in static menus. They shall reorder, emphasize, or recommend themselves according to the user's current context while preserving discoverability.

Capabilities shall reveal themselves as the user's sophistication grows:
- **First-time user** → Essential 5 capabilities visible
- **Regular user** → Full surface with shortcuts
- **Power user** → Advanced capabilities, keyboard-driven

No capability shall be hidden behind a menu that cannot be contextually revealed.

---

## 7. Experience Personality

SHUNYA shall communicate: **Calm · Confident · Precise · Respectful · Transparent**

| Quality | How |
|---------|-----|
| Calm | No urgency where none exists. Measured tone. |
| Confident | Definite recommendations. No hedging without cause. |
| Precise | Specific numbers, names, dates. No vague language. |
| Respectful | Assume user competence. No condescension. |
| Transparent | Show evidence. Admit uncertainty. |

SHUNYA shall never communicate dramatically, apologetically, robotically, excessively verbosely, or through marketing language inside the operating system.

---

## 8. Trust Signals

Every important recommendation shall communicate appropriate trust signals:

| Signal | Example |
|--------|---------|
| Evidence | "Because INV-003 is 5 days overdue" |
| Confidence | Badge: "High (80%)" |
| Execution status | "Creating proposal… Done ✅" |
| Source | "From your invoices" / "From the web" |
| Reasoning | Brief explanation of logic |
| Reversibility | Undo button or "This can be undone" |

---

## 9. Living Product Validation

Frontend milestones shall be validated through:

| Metric | What It Measures |
|--------|-----------------|
| Founder Journey completion | New user completes first workflow |
| Executive Briefing quality | Briefing answers all four questions |
| Experience Density | Info per square inch without overload |
| Time-to-Understanding | How fast user grasps current state |
| Time-to-Trust | How fast user trusts recommendations |
| Time-to-Confidence | How fast user feels certain about actions |
| Time-to-Action | How fast user acts on a recommendation |
| Capability Discovery | Capabilities discovered organically |

Screenshots alone shall not validate experience milestones. Every milestone requires a live demonstration with real data.

---

## 10. Experience Principles

Every screen SHUNYA presents shall answer four questions:

| Question | Meaning |
|----------|---------|
| **What is happening?** | Current state, recent changes, active work |
| **Why does it matter?** | Relevance to the user's goals and commitments |
| **What should happen next?** | Suggested actions, decisions needed, opportunities |
| **How can SHUNYA help?** | AI assistance available, automations, commands |

If a screen cannot answer these four questions, it is incomplete.

---

## 11. The Five Experience Layers

```
┌──────────────────────────────────────────────────────────┐
│  LAYER 1 — EXECUTIVE BRIEFING                            │
│  What changed · What matters · Opportunities · Risks     │
│  Recommendations · Commitments · Confidence · Actions    │
├──────────────────────────────────────────────────────────┤
│  LAYER 2 — ACTIVE REALITY                                 │
│  The object, conversation, or workflow deserving focus   │
├──────────────────────────────────────────────────────────┤
│  LAYER 3 — CAPABILITY DISCOVERY                           │
│  Contextual hints · "Did you know?" · Progressive reveal │
├──────────────────────────────────────────────────────────┤
│  LAYER 4 — UNIVERSAL WORKSPACE                            │
│  Every object → consistent layout → semantic adaptation  │
├──────────────────────────────────────────────────────────┤
│  LAYER 5 — COMMAND SURFACE (Always Available)            │
│  Text · Voice · Images · PDFs · Drag-and-drop · URLs     │
└──────────────────────────────────────────────────────────┘
```

### Layer 1: Executive Briefing

The first thing the user sees. Not a dashboard — a briefing.

Contains:
- **What changed** since last visit (new invoices, updated proposals, completed tasks)
- **What matters** (overdue items, pending approvals, expiring quotes)
- **Opportunities** (leads requiring follow-up, upsell recommendations)
- **Risks** (stale pipelines, late payments, resource conflicts)
- **Recommendations** (AI-generated next-best actions)
- **Commitments** (upcoming deadlines, scheduled calls, delivery dates)
- **Confidence** (pipeline health score, task completion velocity)
- **Suggested actions** (one-click: send reminder, create invoice, schedule meeting)

**Rules:**
- Must load in under 1 second (cache-first strategy)
- Every data point must be clickable → navigates to relevant workspace
- Empty states must educate, not apologize
- No hardcoded metrics — every number from real data

### Layer 2: Active Reality

The primary working canvas. What the user is doing right now.

- When a space is opened → that space becomes the Active Reality
- When AI executes a command → result becomes Active Reality
- When a notification is clicked → the referenced object becomes Active Reality
- Active Reality is always one click away from returning to Executive Briefing

**Rules:**
- Back/Close must always return to Executive Briefing
- State must be preserved when returning (scroll position, filters, search)
- Active Reality must show the object's relationships (linked invoices, contacts, tasks)

### Layer 3: Capability Discovery

SHUNYA reveals capabilities contextually — never through menus.

Patterns:
- **"Did you know?"** cards in empty states
- **Suggested next actions** after every AI execution
- **Progressive disclosure** of advanced features based on usage
- **Contextual shortcuts** (e.g., showing "Create invoice for this client" on a contact page)

**Rules:**
- No feature should require documentation to discover
- Every empty state should teach one new capability
- Power-user features should reveal themselves after repeated use

### Layer 4: Universal Workspace

Every object type uses the same workspace layout, adapted semantically:

```
┌─ Identity Panel ─────────────────────────────────────┐
│  Icon | Name | Type Badge | Status | Quick Actions   │
├─ Content Area ───────────────────────────────────────┤
│  Type-specific fields displayed in consistent layout │
├─ AI Analysis ────────────────────────────────────────┤
│  AI-generated insights, recommendations, next steps  │
├─ Relationships ──────────────────────────────────────┤
│  Linked objects (invoices for client, tasks for proj)│
├─ Timeline ───────────────────────────────────────────┤
│  Chronological activity for this object              │
└──────────────────────────────────────────────────────┘
```

**Rules:**
- Same shell for all object types (People, Companies, Trips, Invoices, Documents, Proposals, Projects, Conversations, Finances, Calendars, Tasks)
- Content area adapts to object semantics
- AI Analysis present for every object (may show "Analyzing…" then populate)
- Relationships panel shows linked objects with count badges
- Timeline shows last 10 activities with infinite scroll

### Layer 5: Universal Command Surface

Always available. Always at the center.

Supports:
- **Text** — Type commands in natural language
- **Voice** — Speak commands (Web Speech API)
- **Images** — Drag-and-drop images for analysis/generation
- **PDFs** — Drop PDF to extract or summarize
- **Clipboard** — Paste URLs, text, data
- **Drag-and-drop** — Files, objects, links
- **URLs** — Share links, deep links

**Rules:**
- Must be accessible from any layer without navigation
- Must show execution progress (parsing → thinking → acting → done)
- Must show result inline with suggested next actions
- Must support undo for all destructive actions

---

## 12. Layout System

### Breakpoints

| Class | Width | Columns | Layout Behavior |
|-------|-------|---------|-----------------|
| **Compact** | < 480px | 1 | Single column, stacked navigation, bottom tabs |
| **Personal** | 480–768px | 2 | Two columns, sidebar collapsed, top tabs |
| **Shared** | 768–1024px | 3 | Sidebar visible, 3-column grid |
| **Workstation** | 1024–1920px | 4–6 | Full layout, multi-column grids, side panels |
| **Studio** | > 1920px | 6–12 | Ultra-wide, side-by-side workspaces, pinable panels |

### Grid System

- Use Mantine `SimpleGrid` with responsive `cols` prop
- Never use fixed-width containers — use `maxWidth` with `margin: 0 auto`
- Content max-width: 1400px in Workstation, full-width in Studio
- Padding: `{ base: 'xs', sm: 'md', lg: 'xl' }`

### Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `--sh-space-xs` | 4px | Icons, badges, inline elements |
| `--sh-space-sm` | 8px | Related items, card padding |
| `--sh-space-md` | 16px | Section spacing, card gaps |
| `--sh-space-lg` | 24px | Major sections, page sections |
| `--sh-space-xl` | 40px | Page padding, hero areas |

---

## 13. Typography

### Font Family

```
Inter (body), Noto Sans Devanagari (Devanagari script)
```

### Size Scale

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `--sh-text-xs` | 11px | 500 | Labels, metadata, timestamps |
| `--sh-text-sm` | 13px | 400 | Body text, descriptions |
| `--sh-text-base` | 15px | 400 | Default body |
| `--sh-text-lg` | 18px | 600 | Card titles, section headers |
| `--sh-text-xl` | 24px | 700 | Page titles, hero metrics |
| `--sh-text-2xl` | 32px | 700 | Executive briefing numbers |
| `--sh-text-3xl` | 48px | 800 | Welcome hero, branded displays |

### Color

- Body: `#1A1C1D` (light) / `#E8E8E8` (dark)
- Dimmed: `rgba(26,28,29,0.55)` (light) / `rgba(232,232,232,0.55)` (dark)
- Links: `#6C4AE2`
- Brand gradient: `linear-gradient(135deg, #6C4AE2, #A4865F)`

---

## 14. Color System

### Brand Palette

| Role | Light | Dark | Usage |
|------|-------|------|-------|
| Primary | `#6C4AE2` | `#8B6FFF` | Buttons, links, active states |
| Gold/Accent | `#A4865F` | `#C4A67F` | Secondary accent, highlights |
| Success | `#2D6A4F` | `#3D8A6F` | Completed, active, positive |
| Danger | `#B91C1C` | `#DC2626` | Errors, overdue, delete |
| Warning | `#D97706` | `#F59E0B` | Pending, attention needed |
| Info | `#2563EB` | `#3B82F6` | Information, system messages |

### Background

| Surface | Light | Dark |
|---------|-------|------|
| Page | `#FAF8F5` | `#1A1B1E` |
| Card | `rgba(255,255,255,0.5)` | `rgba(30,30,40,0.5)` |
| Glass | `rgba(255,255,255,0.6)` | `rgba(30,30,40,0.7)` |
| Modal overlay | `rgba(0,0,0,0.1)` | `rgba(0,0,0,0.3)` |

### Border

| Weight | Style | Usage |
|--------|-------|-------|
| Default | `1px solid var(--mantine-color-default-border)` | Cards, panels |
| Glass | `1px solid rgba(108,74,226,0.12)` | Glass-morphism elements |
| Accent | `3px solid {role color}` | Left borders for emphasis |

---

## 15. Motion System

### Principles

1. **Motion communicates understanding** — every animation has meaning
2. **No decorative animation** — if it doesn't explain something, don't animate it
3. **Respect reduced motion** — all animations collapse to instant transitions
4. **Stagger for lists** — items appear one by one with 0.05s delays
5. **Spring physics** — use `type: 'spring', damping: 25, stiffness: 300` for natural feel

### Animation Registry

| Context | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Space panel open | `slideUp` (y: 40 → 0) | 0.4s | spring |
| Space panel close | `slideDown` (y: 0 → 40) | 0.3s | easeOut |
| KPI value change | `countUp` (opacity 0→1, y: 8→0) | 0.6s | easeOut |
| List item appear | `fadeSlide` (x: -20 → 0) | 0.4s | easeOut |
| Modal open | `scaleIn` (scale: 0.95→1) | 0.3s | spring |
| Hover lift | `translateY(-2px)` | 0.15s | easeOut |
| Pulse ring | `scale(1→1.08→1)` | 3s | easeInOut |
| Heartbeat dot | `scale(1→1.2→1)` | 2s | easeInOut |
| Oracle glow | `box-shadow pulse` | 3s | easeInOut |
| Orb drift | `translate(30px, -20px)` | 25s | easeInOut |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 16. Component Behavior Standards

### Every Component Must Handle

| State | Behavior | Visual |
|-------|----------|--------|
| **Loading** | Show skeleton within 100ms | Mantine `Skeleton` or `Loader` |
| **Empty** | Educate user, suggest action | Icon + message + CTA button |
| **Content** | Display data with proper formatting | As designed |
| **Error** | Show message + retry button | Red alert with error text |
| **Updating** | Show subtle indicator | Non-blocking toast or dim |

### Space Panel Pattern

Every space panel follows this structure:

```tsx
<Stack gap="md">
  <SpaceHeader icon title onNew onSearch onClose />
  {loading && <ListSkeleton />}
  {error && <ErrorFallback message onRetry />}
  {!loading && !error && items.length === 0 && <EmptyState />}
  {!loading && !error && items.length > 0 && <ItemList />}
</Stack>
```

---

## 17. Empty State Standards

Every empty state must:

1. Show a relevant icon (floating animation optional)
2. Explain what belongs here in plain language
3. Suggest the first action to take
4. Provide a button/CTA for that action
5. (Optional) Include a "Did you know?" tip about a related capability

**Examples:**

```
No proposals yet
Create your first proposal to get started. AI can help you
build a professional proposal in seconds.
[+ New Proposal]  [Ask AI to create one]
```

---

## 18. Error State Standards

Every error state must:

1. Acknowledge the error without blaming the user
2. Show a clear, non-technical message
3. Provide a Retry button
4. (Optional) Provide a fallback action

**Examples:**

```
Could not load proposals
Something went wrong while fetching your proposals.
[Retry]  [Go to Dashboard]
```

---

## 19. AI Execution Flow

Every AI command follows this visible flow:

```
1. User types/speaks command
2. AI shows interpretation ("I will create a proposal for Amit")
   → Parsing indicator
3. AI shows action plan (steps to execute)
   → "2-step workflow: create object → update object"
4. User confirms with "Execute"
5. Progress shown for each step
   → Step 1 ✅ → Step 2 ✅
6. Result displayed with summary
   → ✅ Execution Complete: "Bali proposal created"
7. Suggested next actions
   → [View Proposal] [Send to Client] [Create Invoice]
8. Undo available
   → [Undo] button for up to 5 actions
```

---

## 20. Responsive Rules

| Rule | Implementation |
|------|---------------|
| Header wraps on mobile | `wrap="wrap"` with `gap: 4px` |
| Tabs scroll horizontally on mobile | `overflowX: 'auto', flexWrap: 'nowrap'` |
| Orbs hidden on mobile | `display: none` at `< 768px` |
| Space grid: 2 cols mobile → 6 cols desktop | `cols={{ base: 2, sm: 3, md: 4, lg: 6 }}` |
| KPI grid: 2 cols mobile → 4 cols desktop | `cols={{ base: 2, sm: 4 }}` |
| Flow stream: 1 col always | Single column for readability |
| Padding: tighter on mobile | `px={{ base: 'xs', sm: 'md' }}` |
| Content max-width: 1400px | `maxWidth: 1400, margin: '0 auto'` |
| Touch targets: minimum 44px | All interactive elements |

---

## 21. Performance Budgets

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| Time to Interactive | < 3.5s |
| Lighthouse Performance | > 90 |
| Main JS bundle | < 500KB (code-split) |
| API response (p95) | < 500ms |

---

## 22. Accessibility Standards

| Requirement | Standard |
|-------------|----------|
| Color contrast | WCAG AA minimum (4.5:1) |
| Focus indicators | Visible 2px outline on all interactive |
| Keyboard navigation | All features accessible via keyboard |
| Screen reader | Semantic HTML, ARIA labels, roles |
| Reduced motion | `prefers-reduced-motion` respected |
| Touch targets | Minimum 44×44px |
| Font scaling | Supports 200% browser zoom |

---

## 23. Implementation Checklist

For every new feature, verify:

- [ ] Answers all four questions (What/Why/Next/Help)
- [ ] Handles all 5 states (loading/empty/content/error/updating)
- [ ] Follows responsive breakpoints (Compact→Studio)
- [ ] Has proper motion (entry/exit/hover/state change)
- [ ] Meets accessibility standards (contrast/keyboard/aria)
- [ ] Uses real data (no mock data, no hardcoded values)
- [ ] Shows AI analysis where relevant
- [ ] Links to related objects (relationships)
- [ ] Provides suggested next actions after execution
- [ ] Supports undo for destructive operations
- [ ] Loads within performance budget
- [ ] Works offline (service worker cache)
- [ ] Has empty state with education + CTA
- [ ] Has error state with retry + fallback

---

## 24. Prohibited Patterns

| Pattern | Why | Replace With |
|---------|-----|-------------|
| Hardcoded metrics | Misleads user | Real API data |
| Mock data in UI | Breaks trust | Empty state or loading |
| iframe-based features | Blocked by X-Frame-Options | Native component or external link |
| Decorative animations | Wastes resources, distracts | Motion with meaning |
| Dashboard overload | Cognitive overload | Executive briefing with layers |
| Excessive gradients | Looks dated | Subtle brand gradient only |
| Decorative AI (sparkles everywhere) | Feels gimmicky | AI where genuinely helpful |
| Unnecessary glass effects | Performance cost | Glass only for overlay elements |
| Visual noise (too many colors) | Reduces clarity | Brand palette with restraint |

---

## 25. Color System Reference

```
Brand Gradient:      #6C4AE2 → #A4865F  (purple to gold)
Page Background:     #FAF8F5             (warm off-white)
Card Background:     rgba(255,255,255,0.5)
Glass Background:    rgba(255,255,255,0.6)
Body Text:           #1A1C1D
Dimmed Text:         rgba(26,28,29,0.55)
Divider:             rgba(108,74,226,0.12)
Success:             #2D6A4F
Danger:              #B91C1C
Warning:             #D97706
Info:                #2563EB
```

---

*This playbook is the canonical reference for all SHUNYA frontend implementation.
Any deviation requires constitutional amendment (XA pattern).*