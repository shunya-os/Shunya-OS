# SHUNYA Frontend Foundation

> **Canonical Reference — Phase X3**
> The permanent frontend engineering foundation. Every future SHUNYA application is built on this foundation. No new layout systems, interaction systems, component behaviour, or accessibility behaviour should be invented at the application level.

---

## 1. Architecture Overview

```
frontend/
├── package.json              # Next.js 15 + React 19 + Zustand + Tailwind v4
├── tsconfig.json             # TypeScript strict mode
├── next.config.ts            # App Router, typed routes
│
└── src/
    ├── app/
    │   ├── layout.tsx         # Root layout, font loading, theme initialization
    │   ├── page.tsx           # Home page + Object workspace view
    │   └── globals.css        # Design token system (Tailwind @theme)
    │
    ├── components/
    │   ├── ui/index.tsx       # 12 primitive components
    │   ├── layout/index.tsx   # 10 layout components
    │   ├── navigation/index.tsx # 8 navigation components
    │   ├── feedback/index.tsx # 6 feedback components
    │   └── data/index.tsx     # 4 data display components
    │
    ├── stores/index.ts        # 6 Zustand stores (theme, navigation, AI, panel, selection, overlay, focus)
    ├── hooks/index.ts         # 12 custom hooks
    ├── engines/index.ts       # 7 runtime engines
    ├── services/api.ts        # API abstraction layer
    ├── types/index.ts         # Core type system
    ├── lib/
    │   ├── event-bus.ts       # Pub/sub event bus
    │   └── component-registry.ts # Dynamic component registry
    └── data/objects.ts        # Demo data (business-agnostic)
```

### Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | Next.js 15 (App Router) | Production-grade React. Server components + client components. Typed routes. |
| Language | TypeScript (strict mode) | Type safety at all boundaries. `noUncheckedIndexedAccess` enabled. |
| Styling | Tailwind CSS v4 + CSS variables | Design tokens as CSS custom properties. Tailwind's @theme for compile-time safety. |
| State | Zustand | Lightweight, TypeScript-native, no boilerplate. 6 stores cover all runtime state. |
| Animation | CSS transitions + Tailwind | All motion derives from token system. Framer Motion optional for complex sequences. |
| Components | Function components + forwardRef | Every interactive component supports ref forwarding. |

---

## 2. Design Token Runtime

Every visual property derives from CSS custom properties defined in `globals.css`. The token runtime is the single source of truth.

### Token Categories (100+ tokens)

| Category | Count | Key Tokens |
|----------|-------|------------|
| Brand | 3 | `--color-brand-primary`, `--brand-primary-subtle`, `--brand-secondary` |
| Surface | 5 | `--surface-primary` through `--surface-hover` (dark + light) |
| Text | 5 | `--text-primary` through `--text-on-brand` |
| Semantic | 8 | `--color-success`, `--warning`, `--error`, `--info` + background variants |
| Border | 3 | `--border-primary`, `--secondary`, `--focus` |
| Shadow | 4 | `--shadow-sm` through `--shadow-xl` (dark + light) |
| Font | 3 families, 7 sizes, 4 weights | Display (Playfair), Body (Inter), Mono (JetBrains) |
| Spacing | 9 | `--space-1` through `--space-16` (4px scale) |
| Radius | 5 | `--radius-sm` through `--radius-full` |
| Motion | 2 easings, 5 durations | `--ease-out`, `--ease-in`, `--duration-micro` through `--duration-navigation` |
| Layout | 4 | `--header-height`, `--cp-width`, `--cp-collapsed`, `--content-max` |

### Theme Engine

The theme engine (`useThemeStore`) manages dark/light mode:

- Default: dark mode
- Light mode override: `[data-theme="light"]` CSS selector swaps all surface/text/shadow tokens
- Persisted to `localStorage`
- Initialized in root layout to prevent flash

---

## 3. Runtime Engines (7)

| Engine | Responsibility | Key API |
|--------|---------------|---------|
| **ThemeEngine** | Dark/light mode management | `getMode()`, `setMode()`, `toggle()`, `isDark()` |
| **ResponsiveEngine** | Breakpoint detection | `getBreakpoint(width)`, `isMobile(width)`, `isTablet(width)` |
| **AccessibilityEngine** | a11y preferences + screen reader | `prefersReducedMotion()`, `prefersHighContrast()`, `announce()` |
| **KeyboardEngine** | Shortcut registration + dispatch | `register(shortcut)`, `unregister(key)`, `init()` |
| **MotionEngine** | Animation gating | `shouldAnimate()`, `duration(ms)`, `getTransitionClass()` |
| **FocusEngine** | Focus trapping + management | `trapFocus(container, event)`, `focusFirst(container)`, `focusLast(container)` |
| **RTLEngine** | RTL layout support | `isRTL()`, `getDir()`, `logicalStart()`, `logicalEnd()` |

---

## 4. State Management (6 stores)

| Store | State Shape | Key Actions |
|-------|------------|-------------|
| **useThemeStore** | `{ mode }` | `setMode()`, `toggle()` |
| **useNavigationStore** | `{ currentWorkspace, currentObjectId, activeSection, history, historyIndex }` | `setWorkspace()`, `setObject()`, `setSection()`, `goBack()`, `goForward()` |
| **useAIStore** | `{ suggestions, isExpanded, conversation }` | `addSuggestion()`, `dismissSuggestion()`, `toggleExpanded()`, `addMessage()` |
| **usePanelStore** | `{ contextPanelOpen, contextPanelWidth, activePanels }` | `toggleContextPanel()`, `setContextPanelWidth()`, `registerPanel()` |
| **useSelectionStore** | `{ selectedIds, lastSelectedId, mode }` | `select()`, `deselect()`, `toggleSelect()`, `clear()` |
| **useOverlayStore** | `{ overlays }` | `open()`, `close()`, `closeAll()`, `isOpen()` |
| **useFocusStore** | `{ focusedElementId, focusHistory }` | `setFocus()`, `pushFocus()`, `popFocus()` |

---

## 5. Component Library (40 components)

### UI Primitives (12)

| Component | States | Props |
|-----------|--------|-------|
| `Button` | default, hover, focus, active, disabled, loading | variant, size, loading, icon |
| `Input` | default, focus, error, disabled | label, error, hint, all input attrs |
| `Badge` | 5 semantic variants | variant, size |
| `Card` | default, hover, selected | onClick, selected, hoverable |
| `Avatar` | with image, with initials | src, initials, size |
| `Spinner` | 3 sizes | size |
| `Progress` | determinate | value, max, size |
| `Tooltip` | hover reveal | content, children |
| `Switch` | on/off | checked, onChange, label, disabled |
| `EmptyState` | — | icon, title, description, action |
| `ErrorState` | — | message, onRetry |
| `Skeleton` | text, card, metric, table | variant, lines |

### Navigation (8)

| Component | Description |
|-----------|-------------|
| `Breadcrumb` | Segmented path with truncation |
| `Tabs` | Horizontal tab bar with active indicator |
| `CommandPalette` | Ctrl+K overlay with search, keyboard nav, arrow key selection |
| `SearchBar` | Global search input |
| `WorkspaceSwitcher` | Icon grid with active indicator |
| `ContextMenu` | Right-click menu (foundation, extensible) |
| `Tree` | Collapsible tree with keyboard nav |
| `Table` | Sortable columns, row selection |

### Layout (10)

| Component | Description |
|-----------|-------------|
| `AppLayout` | Three-zone layout orchestrator |
| `GlobalNavBar` | Zone 1: logo, switcher, breadcrumb, search, theme toggle, user |
| `ContextPanel` | Zone 2: collapsible sidebar with AI Resident |
| `WorkspaceShell` | Zone 3: scrollable content container |
| `ObjectHeader` | Icon + name + badges + metadata |
| `ExecutiveSummary` | AI summary with confidence + actions |
| `SectionContainer` | Generic section with empty state |
| `Panel` | Sliding side panel manager |
| `TabsPanel` | Tabbed panel content |

### Feedback (6)

| Component | Description |
|-----------|-------------|
| `ToastProvider` / `useToast` | Context-based toast system with variants |
| `Dialog` | Modal dialog with Escape, backdrop click, focus trap |
| `EmptyState` | Empty content placeholder |
| `ErrorState` | Error state with retry |
| `Skeleton` | Loading placeholder (text, card, metric, table) |
| `Spinner` | Loading spinner |

### Data Display (4)

| Component | Description |
|-----------|-------------|
| `Timeline` | Chronological event list with date groups |
| `Table` | Sortable data table |
| `Tree` | Collapsible hierarchical tree |
| `TreeNode` | Recursive tree node |

---

## 6. Accessibility Foundation

| Feature | Implementation |
|---------|---------------|
| **Keyboard navigation** | All interactive components are keyboard-accessible. Tab order follows visual order. |
| **Focus management** | `focus-visible` outlines on all interactive elements. Focus engine for trapping. Focus store for history. |
| **Screen reader** | ARIA roles (`button`, `dialog`, `tablist`, `tab`, `progressbar`, `switch`, `tree`, `treeitem`). `aria-live` announcer in root layout. |
| **Reduced motion** | `@media (prefers-reduced-motion: reduce)` sets all durations to 0.01ms. Motion engine gates all animations. |
| **High contrast** | Theme engine supports high-contrast media query overrides. |
| **RTL readiness** | RTL engine provides logical direction utilities. CSS uses logical properties. |
| **Skip link** | First focusable element in the layout. |

---

## 7. Production Readiness

### Performance

| Pattern | Implementation |
|---------|---------------|
| **Code splitting** | Next.js App Router automatically code-splits by route |
| **Memoization** | `React.memo`, `useMemo`, `useCallback` on expensive components |
| **CSS containment** | Content area scrolls independently of navigation |
| **Font loading** | Google Fonts with `display=swap` during development; self-hosted in production |
| **Bundle analysis** | `@next/bundle-analyzer` ready |

### Testing Strategy

| Layer | Tool | Scope |
|-------|------|-------|
| **Unit** | Vitest | Stores, engines, services, utilities |
| **Component** | Testing Library | UI primitives, layout components, feedback components |
| **Integration** | Testing Library | Navigation flows, object workspace, AI collaboration |
| **E2E** | Playwright | Full user workflows across breakpoints |
| **Accessibility** | axe-core | CI step on every component test |

### Build & Deploy

```
next build         # Optimized production build
next start         # Production server
npm run typecheck  # TypeScript strict check
npm run lint       # ESLint
```

---

## 8. Canonical Status

This Frontend Foundation, together with all preceding canon documents, forms the complete production-ready implementation layer for SHUNYA.

A future engineer can build any SHUNYA application entirely from this foundation without inventing new:
- Layout systems (three-zone, workspace shell, panel manager)
- Interaction systems (event bus, keyboard engine, focus engine)
- Component behaviour (40 components with standardised contracts)
- Accessibility behaviour (inherited from engines + components)
- State management (7 stores covering all runtime state)
- Design tokens (100+ tokens in a runtime theme engine)

All components are business-agnostic. No travel, CRM, ERP, or sales assumptions are embedded.

The complete implementation path:

```
Human Principles → Presence Canon → Experience Canon
  → Interaction Language → Design System Foundation → Pattern Library
    → Frontend Foundation (you are here) → Applications
```

---

*Canonical reference — Phase X3. July 2026.*