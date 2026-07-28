# SHUNYA Component System

> **Canonical Reference — Phase X1**
> Defines the complete reusable component library. Every component is business-agnostic and works for any object type.

---

## 1. Component Philosophy

### Principles

| Principle | Meaning |
|-----------|---------|
| **Everything is reusable** | No component is designed for a single use case. Every component can render any data type. |
| **Composable, not monolithic** | Components are small and composable. A workspace is built from dozens of small components, not one large one. |
| **Data-driven** | Components receive data and render it. They do not know what object type they are displaying. |
| **Consistent across contexts** | A card looks the same in a list, a grid, a search result, and a relationship graph. |
| **Zero business logic** | Components do not contain business rules. They render what they are given. Business logic lives in the object model. |

---

## 2. Component Hierarchy

```
┌─ Surface Components (page-level containers)
│   ├── WorkspaceLayout
│   ├── ContentArea
│   ├── ContextPanel
│   └── GlobalNavbar
│
├─ Section Components (workspace sections)
│   ├── SectionContainer
│   ├── TabBar
│   ├── ObjectHeader
│   └── ExecutiveSummary
│
├─ Data Components (render data)
│   ├── Card
│   ├── List
│   ├── Table
│   ├── Timeline
│   ├── KnowledgeCard
│   ├── RelationshipGraph
│   ├── MetricCard
│   └── InsightCard
│
├─ Interaction Components (user input)
│   ├── Button
│   ├── ActionChip
│   ├── StatusBadge
│   ├── ContextRibbon
│   ├── CommandPalette
│   ├── SearchInput
│   ├── Dropdown
│   └── Dialog
│
├─ Navigation Components
│   ├── Breadcrumb
│   ├── WorkspaceSwitcher
│   ├── TabBar
│   └── IconNav
│
├─ Feedback Components
│   ├── Toast
│   ├── InlineNotification
│   ├── ProgressIndicator
│   └── Skeleton
│
└─ Layout Components
    ├── Grid
    ├── Stack
    ├── Divider
    ├── Panel
    └── Drawer
```

---

## 3. Surface Components

### WorkspaceLayout

The top-level layout container. Manages the three-zone layout.

```
<WorkspaceLayout>
  <GlobalNavbar />
  <ContentArea>
    <ContextPanel />
    <MainContent />
  </ContentArea>
</WorkspaceLayout>
```

**Props:**
- `contextPanelOpen` — boolean, default true
- `contextPanelWidth` — number (240–400px range)
- `onToggleContextPanel` — callback

**States:** Default (3-zone), ContextPanelCollapsed (2-zone), FullScreen (1-zone, overlay mode)

### GlobalNavbar

The persistent top bar (Zone 1).

**Props:**
- `workspaces` — array of workspace objects (id, name, icon, active)
- `currentWorkspace` — workspace ID
- `user` — user object (name, avatar, role)
- `notificationCount` — number
- `searchQuery` — string
- `breadcrumbs` — array of breadcrumb segments

**States:** Normal, NotificationAlert (when count > 0)

### ContextPanel

The persistent left panel (Zone 2).

**Props:**
- `object` — current object data (or null for workspace-level context)
- `sections` — array of context panel sections
- `expandedSections` — set of expanded section IDs
- `aiResidentState` — 'collapsed' | 'expanded' | 'conversation'

**States:** NoObject (workspace-level view), WithObject (object context), Collapsed (thin strip)

### ContentArea

The main content rendering area (Zone 3).

**Props:**
- `children` — rendered content
- `hasContextPanel` — boolean (affects width calculation)

**States:** Default (with CP), Expanded (without CP)

---

## 4. Section Components

### SectionContainer

Generic container for object workspace sections.

**Props:**
- `id` — section identifier
- `title` — section title
- `icon` — section icon
- `empty` — boolean (show empty state)
- `emptyMessage` — string
- `emptyAction` — { label, onClick }
- `children` — section content

**States:** Normal, Empty, Loading

### TabBar

Section tab navigation.

```
<TabBar
  tabs={tabs}
  activeTab="timeline"
  onTabChange={(id) => ...}
/>
```

**Props:**
- `tabs` — array of { id, label, icon, count, hasNew }
- `activeTab` — active tab ID
- `onTabChange` — callback
- `variant` — 'top' (default) | 'side'

**States:** Normal, WithNewContent (blue dot on tab), Overflow (scrollable)

### ObjectHeader

The fixed header for every object workspace.

**Props:**
- `icon` — object type icon
- `name` — object name
- `type` — object type label
- `status` — { label, color }
- `confidence` — number (0-1)
- `id` — object ID string
- `timestamps` — { created, updated }
- `actions` — array of action objects
- `onEdit` — callback
- `onShare` — callback

**States:** Viewing (default), Editing (name inline edit active)

### ExecutiveSummary

AI-generated 3-line summary.

**Props:**
- `summary` — text (3 lines max)
- `confidence` — number (0-1)
- `sourceCount` — number
- `generatedAt` — timestamp
- `actions` — array of { label, onClick, confidence }
- `collapsible` — boolean (default true)
- `collapsed` — boolean

**States:** Normal, Loading (skeleton), Unavailable (fallback template), Collapsed

---

## 5. Data Components

### Card

```
┌──────────────────────┐
│ Icon  Title          │
│       Subtitle       │
│                       │
│  Metric: ████░░ 65%  │
│  Status: ● Active    │
│                       │
│  [Action] [Action]    │
└──────────────────────┘
```

**Props:**
- `icon` — icon element
- `title` — primary text
- `subtitle` — secondary text
- `metrics` — array of { label, value, trend, confidence? }
- `status` — { label, color }
- `actions` — array of action objects
- `onClick` — callback
- `selected` — boolean
- `variant` — 'default' | 'compact' | 'detail'

**States:** Default, Selected, Hover, Loading, Empty

### List

```
<List>
  <ListItem icon title subtitle status onClick />
  <ListItem icon title subtitle status onClick />
  <ListItem icon title subtitle status onClick />
</List>
```

**Props:**
- `items` — array of list item data
- `variant` — 'simple' | 'detailed' | 'dense'
- `selectable` — boolean
- `selectedId` — string
- `onSelect` — callback
- `virtualized` — boolean (for large lists)

**States:** Normal, Loading, Empty, Filtered (results count shown)

### Table

```
<Table
  columns={[ { key, label, sortable, width }, ... ]}
  rows={[ { id, cells: { key: value } }, ... ]}
  sortable={true}
  onSort={(key, direction) => ...}
  onRowClick={(id) => ...}
/>
```

**Props:**
- `columns` — column definitions
- `rows` — row data
- `sortable` — boolean
- `onSort` — callback
- `onRowClick` — callback
- `selectedRow` — row ID
- `pageSize` — number (default: 25)
- `virtualized` — boolean (default: true for >100 rows)

**States:** Normal, Loading, Empty, Sorted, Filtered

### Timeline

```
<Timeline
  events={events}
  groupBy="day"
  onEventClick={(event) => ...}
  filterable={true}
/>
```

**Props:**
- `events` — array of { id, timestamp, type, actor, description, comment, metadata }
- `groupBy` — 'day' | 'week' | 'month' | 'all'
- `onEventClick` — callback
- `filterable` — boolean
- `searchable` — boolean
- `maxVisible` — number (lazy load beyond this)

**States:** Normal, Filtered, Loading, Empty, LoadOlder (pagination)

### KnowledgeCard

```
┌───────────────────────────────┐
│ 🧠 Knowledge Title            │
│ ─────────────────────────────  │
│ Knowledge content text...     │
│                               │
│ Confidence: ████░░ 0.78      │
│ Source: AI Analysis           │
│ 2d ago                        │
└───────────────────────────────┘
```

**Props:**
- `title` — knowledge title
- `content` — text content
- `confidence` — number (0-1)
- `source` — source label
- `sourceType` — 'ai' | 'curated' | 'observation'
- `timestamp` — date string
- `actions` — array of action objects

**States:** Normal, Loading, Expanded (show full content), Collapsed (show preview)

### RelationshipGraph

Interactive relationship graph visualization.

**Props:**
- `nodes` — array of { id, label, type, icon }
- `edges` — array of { sourceId, targetId, type, label }
- `selectedNode` — node ID
- `onNodeClick` — callback
- `onNodeDoubleClick` — callback
- `pinnedNodes` — set of pinned node IDs

**States:** Normal, Loading, Empty, NodeSelected, Dragging

### MetricCard

```
┌──────────────┐
│ Metric Label │
│    22%       │
│   ▲ 3%      │
└──────────────┘
```

**Props:**
- `label` — metric name
- `value` — formatted value string
- `trend` — 'up' | 'down' | 'flat'
- `trendValue` — percentage change
- `confidence` — number (optional)
- `onClick` — callback
- `size` — 'sm' | 'md' | 'lg'

**States:** Normal, Loading, Error (can't load), Threshold (exceeded)

### InsightCard

AI-generated insight card.

```
┌────────────────────────────────┐
│ 💡 Key Insight                 │
│ ────────────────────────────── │
│ Object X is connected to 5     │
│ pending decisions. Review      │
│ their dependencies before      │
│ proceeding.                    │
│                                │
│ Confidence: 0.72 · 3 sources   │
└────────────────────────────────┘
```

**Props:**
- `icon` — insight type icon
- `content` — text
- `confidence` — number
- `sourceCount` — number
- `actions` — array of { label, onClick }

**States:** Normal, Dismissed

---

## 6. Interaction Components

### Button

Primary interactive element for triggering actions.

```
[Save] [Cancel] [Delete]
```

**Props:**
- `label` — string
- `variant` — 'primary' | 'secondary' | 'ghost' | 'danger'
- `size` — 'sm' | 'md' | 'lg'
- `icon` — optional icon element
- `loading` — boolean (shows spinner, disables)
- `onClick` — callback
- `disabled` — boolean
- `type` — 'button' | 'submit' | 'reset'

**States:** Default, Hover, Active, Disabled, Loading

### ActionChip

Compact clickable action element.

```
[Approve] [Review] [Share]
```

**Props:**
- `label` — string
- `icon` — optional icon
- `variant` — 'primary' | 'secondary' | 'ghost' | 'danger'
- `onClick` — callback
- `disabled` — boolean
- `size` — 'sm' | 'md'

**States:** Default, Hover, Active, Disabled, Loading (spinner)

### StatusBadge

```
[● Active] [● Pending] [● Completed] [● Archived]
```

**Props:**
- `label` — status name
- `color` — status color (green, amber, blue, gray, red)
- `size` — 'sm' | 'md'

**States:** Only visual — no interactive states.

### ContextRibbon

Horizontal strip showing contextual metadata and quick actions.

```
Object Type · Status · Owner · Priority · [Action] [Action]
```

**Props:**
- `items` — array of { label, value, icon }
- `actions` — array of action objects
- `overflow` — max visible items before "..." truncation

### CommandPalette

Full-screen overlay for search and commands.

**Props:**
- `open` — boolean
- `onClose` — callback
- `onSelect` — (result) => void callback
- `initialQuery` — string

**States:** Open (default), Closed, Loading (searching), NoResults, Results

### SearchInput

Text input with search behavior.

**Props:**
- `value` — string
- `onChange` — callback
- `placeholder` — string
- `variant` — 'global' | 'inline' | 'overlay'
- `autofocus` — boolean
- `onClear` — callback

**States:** Empty, Typing, Results (dropdown shown), NoResults

### Dropdown

Standard dropdown menu.

**Props:**
- `items` — array of { label, onClick, icon, disabled, divider }
- `align` — 'left' | 'right'
- `size` — 'sm' | 'md'

**States:** Closed, Open, ItemHover

### Dialog

Modal dialog for confirmations, forms, and alerts.

**Props:**
- `open` — boolean
- `title` — string
- `content` — ReactNode
- `actions` — array of { label, variant, onClick }
- `size` — 'sm' | 'md' | 'lg' | 'fullscreen'
- `closable` — boolean (default true)
- `onClose` — callback

**States:** Closed, Open, Submitting (actions disabled)

---

## 7. Navigation Components

### Breadcrumb

```
Workspace  >  Object Name  >  Section
```

**Props:**
- `segments` — array of { label, icon?, onClick }
- `maxSegments` — number (default: 3)

**States:** Normal, Truncated (overflow with "...")

### WorkspaceSwitcher

```
[🏠] [🔗] [🏢] [📋] [📄] [⚖️] [...]  (icons)
```

**Props:**
- `workspaces` — array of { id, icon, name, active }
- `activeId` — workspace ID
- `onSwitch` — callback
- `overflow` — array of hidden workspace IDs

**States:** Normal, Overflow (hidden workspaces behind "..." menu)

### IconNav

Vertical icon navigation bar (used for section navigation in object workspace).

**Props:**
- `items` — array of { id, icon, label, active, hasNew }
- `activeId` — current active section
- `onSelect` — callback
- `expanded` — boolean (show labels)

**States:** Normal, Expanded (shows labels), ItemActive, ItemHasNew

---

## 8. Feedback Components

### Toast

Non-blocking notification.

**Props:**
- `message` — string
- `variant` — 'success' | 'error' | 'warning' | 'info'
- `duration` — milliseconds (default: 4000)
- `action` — { label, onClick }
- `onDismiss` — callback

**States:** Entering, Visible, Exiting

### InlineNotification

Contextual notification embedded in content.

```
┌───────────────────────────────────────────────┐
│ ⚠ 3 tasks are overdue. Review them now. [Dismiss] │
└───────────────────────────────────────────────┘
```

**Props:**
- `message` — string
- `variant` — 'info' | 'warning' | 'error' | 'success'
- `action` — { label, onClick }
- `dismissable` — boolean
- `onDismiss` — callback

**States:** Visible, Dismissed

### ProgressIndicator

```
████████░░░░░░░░ 45%
```

**Props:**
- `value` — number (0-100)
- `variant` — 'linear' | 'circular'
- `size` — 'sm' | 'md'
- `indeterminate` — boolean

**States:** Determinate (value shown), Indeterminate (animated), Complete (100%)

### Skeleton

Loading placeholder that matches component shape.

```
<Skeleton variant="card" count={3} />
<Skeleton variant="text" lines={4} />
<Skeleton variant="table" rows={5} columns={3} />
```

**Props:**
- `variant` — 'card' | 'text' | 'table' | 'metric' | 'custom'
- `count` — number of skeleton items (default: 1)
- `width` — custom width (for 'custom' variant)

---

## 9. Layout Components

### Grid

Flexible grid for card layouts.

```
<Grid columns={2} gap="lg">
  <Card ... />
  <Card ... />
</Grid>
```

**Props:**
- `columns` — number (responsive: auto-adjusts)
- `gap` — 'sm' | 'md' | 'lg'
- `minChildWidth` — number (for responsive grid)

### Stack

Vertical layout with consistent spacing.

```
<Stack gap="md">
  <Section ... />
  <Section ... />
</Stack>
```

**Props:**
- `gap` — 'none' | 'xs' | 'sm' | 'md' | 'lg'
- `direction` — 'vertical' | 'horizontal'

### Panel

Sliding side panel for detail views.

**Props:**
- `open` — boolean
- `side` — 'left' | 'right'
- `width` — number (default: 400)
- `title` — string
- `children` — panel content
- `onClose` — callback
- `closable` — boolean

**States:** Closed, Open, Closing

### Drawer

Overlay drawer from any edge.

**Props:**
- `open` — boolean
- `side` — 'left' | 'right' | 'bottom'
- `size` — number or 'full'
- `children` — drawer content
- `onClose` — callback

**States:** Closed, Open, Closing

---

## 10. Component Invariants

1. **Every component is business-agnostic.** No component references specific object types, industries, or use cases.
2. **Every component has defined states.** Default, Loading, Empty, Error, Hover, Active, Disabled.
3. **Every component supports keyboard navigation.** Tab stops, arrow keys, Enter, Escape.
4. **Every component supports theming via CSS variables.** No hardcoded colors or spacing.
5. **Every component has ARIA attributes.** Labels, roles, states, descriptions.
6. **Every component is responsive.** Works at all viewport widths.
7. **Every component supports reduced motion.** Animations respect prefers-reduced-motion.
8. **Every interactive component has a disabled state.**
9. **Every data component has loading and empty states.**
10. **Components compose without layout leaks.** A Card inside a Grid inside a Stack renders correctly.