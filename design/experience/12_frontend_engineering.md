# SHUNYA Frontend Engineering Canon

> **Canonical Reference — Phase X1**
> Defines implementation guidance for building SHUNYA's frontend. Every frontend implementation must conform to these engineering principles.

---

## 1. Engineering Philosophy

### Principles

| Principle | Meaning |
|-----------|---------|
| **Business-agnostic UI** | No UI component contains business logic. Components render data; they do not know what they are rendering. |
| **Type-safe at boundaries** | All component props, API responses, and state are fully typed (TypeScript). No `any`, no implicit types. |
| **Component-first architecture** | Every screen is composed of reusable components. No page-level components. |
| **Separation of concerns** | UI (components), State (stores/hooks), Data (services/queries), Logic (utils/hooks) are separate layers. |
| **Performance as a feature** | Every component is optimized by default. Memoization, virtualization, code splitting are standard practice. |
| **Tested by default** | Every component has tests. Every hook has tests. Every utility has tests. |

### Stack

| Layer | Technology |
|-------|------------|
| Framework | React 19+ (or compatible framework) |
| Language | TypeScript 5+ (strict mode) |
| Styling | CSS Modules or CSS-in-JS with zero runtime (Panda CSS, Vanilla Extract) |
| State | Zustand or Jotai (lightweight, TypeScript-native) |
| Routing | TanStack Router or React Router (client-side, type-safe) |
| Data fetching | TanStack Query (React Query) |
| Virtualization | TanStack Virtual |
| Animations | CSS transitions + Framer Motion (for complex animations) |
| Testing | Vitest + Testing Library + Playwright |
| Build | Vite |

---

## 2. Folder Architecture

```
src/
├── components/          # Reusable UI components
│   ├── ui/              # Primitive components (Button, Card, Input)
│   ├── layout/          # Layout components (WorkspaceLayout, Panel)
│   ├── data/            # Data display (List, Table, Timeline)
│   ├── feedback/        # Feedback components (Toast, Notification)
│   ├── navigation/      # Navigation components (TabBar, Breadcrumb)
│   └── interaction/     # Interactive components (ActionChip, SearchInput)
│
├── composables/         # Reusable hooks and logic
│   ├── useObject.ts     # Current object state
│   ├── useNavigation.ts # Navigation state
│   ├── useSearch.ts     # Search state
│   └── useAI.ts         # AI Resident state
│
├── stores/              # Global state (Zustand/Jotai)
│   ├── workspace.ts     # Workspace store
│   ├── navigation.ts    # Navigation store
│   ├── preferences.ts   # User preferences store
│   └── ai.ts            # AI state store
│
├── services/            # API/data services
│   ├── api.ts           # API client
│   ├── object.ts        # Object CRUD operations
│   ├── search.ts        # Search service
│   └── ai.ts            # AI service
│
├── types/               # TypeScript types
│   ├── object.ts        # Object types
│   ├── navigation.ts    # Navigation types
│   ├── ai.ts            # AI types
│   └── component.ts     # Shared component types
│
├── tokens/              # Design tokens
│   ├── colors.css       # Color tokens
│   ├── typography.css   # Typography tokens
│   ├── spacing.css      # Spacing tokens
│   └── motion.css       # Motion tokens
│
├── utils/               # Pure utility functions
│   ├── format.ts        # Date, number formatting
│   ├── search.ts        # Search utilities
│   └── object.ts        # Object utility functions
│
├── mocks/               # Test mocks and fixtures
│   ├── objects.ts       # Object mocks
│   └── handlers.ts      # MSW handlers
│
├── App.tsx              # Root component
├── main.tsx             # Entry point
└── index.html           # HTML shell
```

### File Naming Convention

| File type | Convention | Example |
|-----------|------------|---------|
| Component (default export) | `PascalCase.tsx` | `Button.tsx` |
| Component (named export) | `kebab-case.tsx` | `metric-card.tsx` |
| Hook | `useCamelCase.ts` | `useObject.ts` |
| Store | `camelCase.ts` | `workspace.ts` |
| Service | `camelCase.ts` | `objectService.ts` |
| Type | `camelCase.ts` | `objectTypes.ts` |
| CSS Module | `Component.module.css` | `Button.module.css` |
| Test | `Component.test.tsx` | `Button.test.tsx` |
| Story | `Component.stories.tsx` | `Button.stories.tsx` |

---

## 3. Component Organization

### Component Structure

Every component follows this structure:

```
Button/
├── Button.tsx           # Component implementation
├── Button.module.css    # Component styles
├── Button.test.tsx      # Component tests
├── Button.stories.tsx   # Storybook stories
└── index.ts             # Re-export
```

### Component Pattern

```typescript
// Button.tsx
import { forwardRef } from 'react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './Button.module.css';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Loading state */
  loading?: boolean;
  /** Icon slot */
  icon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, icon, children, className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={[
          styles.button,
          styles[variant],
          styles[size],
          loading && styles.loading,
          className,
        ].filter(Boolean).join(' ')}
        disabled={loading || props.disabled}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <span className={styles.spinner} aria-hidden="true" />
        ) : icon ? (
          <span className={styles.icon} aria-hidden="true">{icon}</span>
        ) : null}
        {children && <span className={styles.label}>{children}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

### Component Design Rules

| Rule | Description |
|------|-------------|
| **One component per file** | No exceptions. |
| **Props are typed** | Every component exports its Props type. |
| **Forward refs** | All interactive components forward refs. |
| **Default exports** | Components use default exports. |
| **No business logic** | Components receive data and callbacks. They do not fetch data. |
| **No layout assumptions** | Components do not set their own margins or positioning (parent controls layout). |
| **CSS Modules** | Component-scoped styles. No global CSS modifications. |
| **Semantic HTML** | Use native HTML elements with ARIA. No `<div>` where `<button>` works. |

---

## 4. State Management Philosophy

### State Layers

| Layer | Store | When to Use |
|-------|-------|-------------|
| **Server state** | TanStack Query | Data from API (objects, relationships, timeline) |
| **URL state** | Router | Current workspace, object, section |
| **UI state** | Zustand/Jotai | Panel open/close, theme, preferences |
| **Local state** | `useState` | Form inputs, toggles, ephemeral UI state |

### Rules

| Rule | Description |
|------|-------------|
| **Server state never lives in UI state** | API data is managed by TanStack Query. Never duplicate API data in Zustand. |
| **URL is the source of truth for navigation** | Current workspace, object, and section are derived from the URL. |
| **UI state is scoped** | Panel state is stored where it is used (component-level or workspace-level). Not global. |
| **Preferences are persisted** | User preferences (theme, panel width, section order) persist to localStorage. |
| **No prop drilling beyond 2 levels** | Use context or store for deeply shared state. |
| **Stores are typed** | Every store has a full TypeScript interface. |

### Query Pattern

```typescript
// useObject.ts
import { useQuery } from '@tanstack/react-query';
import { objectService } from '@/services/object';

interface UseObjectOptions {
  id: string;
  workspace?: string;
}

export function useObject({ id, workspace }: UseObjectOptions) {
  return useQuery({
    queryKey: ['object', id, workspace],
    queryFn: () => objectService.getObject(id, workspace),
    staleTime: 30_000, // 30 seconds
    gcTime: 5 * 60_000, // 5 minutes
  });
}
```

---

## 5. Performance Rules

### Rendering Strategy

| Pattern | When to Use | Implementation |
|---------|-------------|----------------|
| Static rendering | Content that never changes | Plain React component |
| Memoized rendering | Content that changes infrequently | `React.memo` with shallow comparison |
| Virtualized rendering | Lists > 100 items | TanStack Virtual |
| Deferred rendering | Content below the fold | `useDeferredValue` or Intersection Observer |
| Progressive rendering | Large sections | Skeleton → content transition |

### Memoization Rules

| Element | Memoize? | Strategy |
|---------|----------|----------|
| Pure components | Yes | `React.memo` |
| Expensive computations | Yes | `useMemo` |
| Callback props | Yes | `useCallback` |
| Simple components | No | Overhead > benefit |
| Components with many children | Yes | Prevents unnecessary re-renders |

### Virtualization

| When to Virtualize | Threshold |
|--------------------|-----------|
| Lists | > 100 items |
| Tables | > 100 rows |
| Timeline | > 200 events |
| Knowledge items | > 50 items |
| Search results | > 50 results |

### Code Splitting

| Boundary | Strategy |
|----------|----------|
| Per workspace | Lazy loaded (`React.lazy` + suspense) |
| Per dialog/modal | Lazy loaded (import on trigger) |
| Per heavy component | Lazy loaded (chart, graph editor) |
| AI conversation | Lazy loaded (not in critical path) |

### Performance Budgets

| Metric | Target |
|--------|--------|
| Time to interactive | < 2s |
| First input delay | < 50ms |
| Largest contentful paint | < 2.5s |
| Cumulative layout shift | < 0.1 |
| Rendering frame rate | 60fps (smooth scrolling) |
| JavaScript bundle (critical) | < 200KB gzipped |

---

## 6. Rendering Strategy

### Component Rendering

| Component Type | Rendering Pattern |
|----------------|-------------------|
| Layout (WorkspaceLayout, GlobalNavbar) | Static — render once, never re-render |
| Content (Card, List, Table) | Server-data-driven — query determines render |
| Interactive (Button, Input, Dialog) | Client-state-driven — UI state determines render |
| AI (AI Resident, suggestions) | Streaming — progressive content display |

### Conditional Rendering

```typescript
// Pattern: Loading → Empty → Error → Data
function ObjectWorkspace({ id }: { id: string }) {
  const { data, isLoading, isError, error } = useObject({ id });

  if (isLoading) return <ObjectSkeleton />;
  if (isError) return <ErrorState message={error.message} />;
  if (!data) return <EmptyState />;
  return <ObjectContent object={data} />;
}
```

### Data-Driven Rendering

Components render whatever data they receive. They do not switch on object type:

```typescript
// Correct: Generic component renders any object
function ObjectHeader({ object }: { object: ObjectData }) {
  return (
    <header className={styles.header}>
      <ObjectIcon type={object.type} />
      <div className={styles.info}>
        <h1>{object.name}</h1>
        <StatusBadge status={object.status} />
        <ConfidenceBar value={object.confidence} />
      </div>
    </header>
  );
}

// Wrong: Type-switching in component
function ObjectHeader({ object }: { object: ObjectData }) {
  if (object.type === 'person') return <PersonHeader ... />;
  if (object.type === 'project') return <ProjectHeader ... />;
}
```

---

## 7. Animation Architecture

### CSS Animations (Preferred)

```css
/* Button hover — CSS transition (preferred) */
.button {
  background-color: var(--color-surface-tertiary);
  transition: background-color var(--duration-micro) var(--ease-out);
}

.button:hover {
  background-color: var(--color-surface-hover);
}
```

### When to Use Framer Motion

| Use Case | Reason |
|----------|--------|
| Page/workspace transitions | Complex orchestration (enter + exit + layout) |
| Panel slides | Shared layout animations |
| List reorder | Layout animations with `AnimatePresence` |
| Drag and drop | Gesture support |

### When NOT to Use Framer Motion

| Case | Alternative |
|------|-------------|
| Simple hover effects | CSS transition |
| Color transitions | CSS transition |
| Opacity changes | CSS transition |
| Transform animations | CSS transition |
| Loading indicators | CSS animation |

### Animation Lazy Loading

- Framer Motion is lazy-loaded and code-split.
- CSS animations are always available (bundled with component styles).
- Heavy animation libraries are loaded only for views that use them (e.g., relationship graph).

---

## 8. Testing Strategy

### Test Pyramid

```
     ╱╲
    ╱  ╲           E2E (Playwright)
   ╱    ╲          5-10 critical user flows
  ╱──────╲
 ╱        ╲        Integration (Testing Library)
╱          ╲        Component + hook tests
╱────────────╲
╱              ╲   Unit (Vitest)
╱                ╲ Pure functions, utilities, types
━━━━━━━━━━━━━━━━━━
```

### Unit Tests (Vitest)

| Scope | Coverage Target | What to Test |
|-------|-----------------|--------------|
| Utils | 100% | Pure functions, formatters, validators |
| Hooks | 90% | State logic, query configurations |
| Stores | 90% | State transitions, persistence |
| Types | Compile-time | TypeScript strict mode |

### Component Tests (Testing Library)

| Scope | Coverage Target | What to Test |
|-------|-----------------|--------------|
| UI components | 80% | Rendering, props, states |
| Interactive components | 90% | Click, keyboard, focus |
| Layout components | 70% | Responsive behavior |

### Component Test Pattern

```typescript
// Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with label', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Save</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
  });

  it('is keyboard accessible', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Submit</Button>);
    screen.getByRole('button').focus();
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onClick).toHaveBeenCalled();
  });
});
```

### Integration Tests

| Scope | Tool | What to Test |
|-------|------|--------------|
| Object workspace | Testing Library | Navigation, section rendering, data display |
| Search flow | Testing Library | Input → results → selection → navigation |
| AI Resident | Testing Library | Suggestions display, conversation |
| Navigation | Testing Library | Workspace switch, back/forward, history |

### E2E Tests (Playwright)

| Flow | Critical? |
|------|-----------|
| Login → Home workspace | Yes |
| Search → Open object → Navigate sections | Yes |
| Workspace switch → Back to home | Yes |
| Open object → Navigate relationship → Back | Yes |
| Command palette → Workspace switch | Yes |
| AI suggestion → Execute action | No (important but not critical) |

---

## 9. Naming Conventions

### TypeScript/React

| Element | Convention | Example |
|---------|------------|---------|
| Component | PascalCase | `ObjectWorkspace` |
| Hook | camelCase, `use` prefix | `useObject` |
| Store | camelCase | `useWorkspaceStore` |
| Utility function | camelCase | `formatCurrency` |
| Type | PascalCase | `ObjectData` |
| Interface | PascalCase, no `I` prefix | `ButtonProps` |
| Enum | PascalCase | `WorkspaceType` |
| CSS class | camelCase (with CSS Modules) | `styles.headerContent` |
| CSS variable | kebab-case, `--` prefix | `--color-surface-primary` |
| File (component) | PascalCase | `Button.tsx` |
| File (other) | camelCase | `useObject.ts` |

### CSS

| Element | Convention | Example |
|---------|------------|---------|
| Class name | camelCase | `.headerContent` |
| Custom property | kebab-case | `--color-surface-primary` |
| Modifier class | camelCase | `.loading`, `.active` |
| Animation name | kebab-case | `@keyframes slide-in` |

---

## 10. Engineering Invariants

1. **No business logic in UI components.** Components render data; they do not transform, validate, or decide.
2. **Every component is typed.** No `any` in component props or state.
3. **Every interactive component has a disabled state.** No exceptions.
4. **Every data component has loading, empty, error, and success states.**
5. **Every component supports keyboard navigation.** Tab, Enter, Escape, arrows as appropriate.
6. **Every component has ARIA attributes.** Labels, roles, states, live regions.
7. **CSS Modules are the default styling approach.** No global CSS that affects other components.
8. **Server state is managed by TanStack Query.** Never duplicate API data in UI state stores.
9. **URL is the canonical source of truth for navigation.** Workspace, object, section are always in the URL.
10. **Performance budgets are enforced in CI.** Bundle size, render time, and accessibility are tested on every commit.
11. **Tests are written alongside components.** No "add tests later."
12. **All strings are externalized for i18n.** No user-facing hardcoded strings.