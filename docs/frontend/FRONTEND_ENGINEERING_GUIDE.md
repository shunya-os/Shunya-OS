# SHUNYA Frontend Engineering Guide

> **Implementation-specific engineering guidance for the SHUNYA frontend.**
> Mantine v7 · React 18 · TypeScript · Vite · framer-motion
> If SHUNYA changes frameworks, this is the only document requiring substantial revision.

---

## 1. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | React | 18.x |
| Build tool | Vite | 5.x |
| UI library | Mantine | 7.x |
| Styling | Mantine CSS-in-JS + CSS modules | — |
| Animation | framer-motion | 11.x |
| Icons | lucide-react | — |
| Language | TypeScript | 5.x |
| State | React hooks + event bus | — |
| Routing | No router — single-page SPA | — |
| Auth | Flask session cookie + sessionStorage | — |

---

## 2. Project Structure

```
frontend/src/
├── api/                    # API clients, hooks, event bus
│   ├── client.ts           # Base fetch configuration
│   ├── fetch-with-auth.ts  # Authenticated fetch wrapper
│   ├── session.ts          # SessionManager
│   ├── event-bus.ts        # Pub/sub event bus
│   ├── use-query.ts        # Data fetching hook
│   └── profile.ts          # Profile session management
├── components/
│   ├── public/             # Homepage, auth, mode tabs, space grid
│   │   ├── homepage.tsx    # UnifiedOS — main entry component
│   │   ├── living-os.css   # Living design system CSS
│   │   └── unified-os.css  # Legacy CSS overrides
│   ├── ai/                 # AI command bar, command palette
│   ├── auth/               # Auth modal, unified auth
│   ├── automation/         # Automation rules panel
│   ├── business/           # Business space panels
│   ├── files/              # File manager, upload dropzone
│   ├── integrations/       # Integration hub panels
│   ├── jobs/               # Background jobs panel
│   ├── knowledge/          # Knowledge browser, AI analysis
│   ├── media/              # Pollinations image generator
│   ├── notifications/      # Notification bell
│   ├── pdf/                # PDF preview component
│   ├── proposals/          # Proposals panel
│   ├── settings/           # Settings panel (profile, appearance, AI, payments)
│   ├── space/              # Space shared components (header, skeleton)
│   ├── ui/                 # Generic reusable UI components
│   └── workspace/          # Workspace switcher, create modal
├── context/                # React contexts
├── app.tsx                 # Root app component
├── main.tsx                # Entry point
└── vite-env.d.ts           # Vite type declarations
```

---

## 3. Mantine Usage Patterns

### 3.1 Imports

Import only the components you need — tree-shaking handles the rest:

```tsx
import { Group, Stack, Text, Paper, Badge, Button } from '@mantine/core';
```

### 3.2 Dark Mode

```tsx
import { useMantineColorScheme } from '@mantine/core';

function MyComponent() {
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';
}
```

Use `data-mantine-color-scheme` attribute for CSS overrides:

```css
[data-mantine-color-scheme="dark"] .my-class {
  /* dark mode overrides */
}
```

### 3.3 Responsive Props

Use Mantine's responsive prop syntax:

```tsx
<SimpleGrid cols={{ base: 2, sm: 3, md: 4, lg: 6 }} spacing="md" />
<Box px={{ base: 'xs', sm: 'md', lg: 'xl' }} />
<Group wrap={{ base: 'wrap', sm: 'nowrap' }} />
```

### 3.4 Theming

The Mantine theme is configured in `app.tsx`:

```tsx
<MantineProvider
  defaultColorScheme="light"
  theme={{
    fontFamily: 'Inter, sans-serif',
    primaryColor: 'violet',
    colors: {
      violet: ['#F3EEFF', '#DDD0FF', '#C4B0FF', '#A88EFF', '#8B6FFF', '#6C4AE2', '#5A3CC4', '#4A2FA6', '#3A2488', '#2C1A6A'],
    },
    defaultRadius: 'md',
    components: {
      Card: { defaultProps: { padding: 'md', radius: 'md' } },
      Button: { defaultProps: { radius: 'md' } },
    },
  }}
>
```

### 3.5 Color Tokens

Use Mantine theme colors where possible:

```tsx
<Text c="dimmed" />
<Badge color="violet" />
<ThemeIcon color="violet" variant="light" />
```

Custom brand colors are defined in `living-os.css`:

```css
--sh-purple: #6C4AE2;
--sh-gold: #A4865F;
--sh-success: #2D6A4F;
--sh-danger: #B91C1C;
```

---

## 4. Component Composition

### 4.1 Space Panel Pattern

Every space panel follows this exact structure:

```tsx
import { useState, useEffect, useCallback } from 'react';
import { Stack, Paper, Group, Text, Button, Loader, ThemeIcon } from '@mantine/core';
import { SpaceHeader } from '../space/space-header';
import { ListSkeleton } from '../space/space-skeleton';
import { fetchWithAuth } from '../../api/fetch-with-auth';

interface Item { id: number; name: string; /* ... */ }

export function MyPanel() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchWithAuth('/api/v1/objects/mytype');
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const body = await res.json();
      setItems(body.data ?? body.items ?? []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchItems(); }, [fetchItems]);

  if (loading && items.length === 0) return <ListSkeleton rows={3} />;

  if (error && items.length === 0) {
    return (
      <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
        <Text c="red" size="sm">{error}</Text>
        <Button size="xs" mt="sm" variant="light" onClick={fetchItems}>Retry</Button>
      </Paper>
    );
  }

  return (
    <Stack gap="md">
      <SpaceHeader icon={<span>📋</span>} title="My Panel" onNew={() => {}} />
      {items.length === 0 ? (
        <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
          <Text size="sm" c="dimmed">No items yet</Text>
          <Button size="sm" mt="md" variant="light">Create First</Button>
        </Paper>
      ) : (
        items.map(item => (
          <Paper key={item.id} withBorder p="sm" radius="md">
            <Text size="sm">{item.name}</Text>
          </Paper>
        ))
      )}
    </Stack>
  );
}
```

### 4.2 AI Analysis Panel Pattern

When adding AI analysis to any panel:

```tsx
<Paper withBorder p="md" radius="md">
  <Group gap="sm" mb="sm">
    <ThemeIcon size={28} radius="md" variant="light" color="violet">
      <Sparkles size={14} />
    </ThemeIcon>
    <Text size="sm" fw={500}>AI Analysis</Text>
  </Group>
  {aiLoading ? (
    <Group gap="sm"><Loader size="xs" /><Text size="xs" c="dimmed">Analyzing…</Text></Group>
  ) : aiResult ? (
    <Text size="sm">{aiResult}</Text>
  ) : (
    <Button size="compact-sm" variant="light" onClick={triggerAnalysis}>
      Analyze with AI
    </Button>
  )}
</Paper>
```

### 4.3 Lazy Loading Pattern

```tsx
import { lazy, Suspense } from 'react';
import { Loader } from '@mantine/core';

const LazyMyPanel = lazy(() => import('./panels/my-panel').then(m => ({ default: m.MyPanel })));

// Usage:
<Suspense fallback={<Loader size="sm" />}>
  <LazyMyPanel />
</Suspense>
```

---

## 5. CSS Architecture

### 5.1 Layers

| Layer | File | Purpose |
|-------|------|---------|
| Mantine defaults | `@mantine/core` | Base component styles |
| Living design system | `living-os.css` | Animations, glass, pulse, responsive |
| Unified OS overrides | `unified-os.css` | Legacy component overrides |
| Space-specific | Inline styles or CSS modules | Per-space customizations |

### 5.2 Naming Convention

Use BEM-like prefixed classes:

```css
.shunya-[component]-[element]
```

Examples:
- `.shunya-glass` — glass morphism
- `.shunya-oracle` — AI command bar
- `.shunya-metric-card` — KPI cards
- `.shunya-space-card` — space navigation cards
- `.shunya-flow-item` — activity feed items
- `.shunya-pulse-ring` — pulse animation wrapper

### 5.3 Animation Classes

Define animations in `living-os.css`, apply via className:

```tsx
<div className="shunya-flow-item">...</div>
```

Available animation classes:

| Class | Effect |
|-------|--------|
| `.shunya-living-bg` | Animated gradient background |
| `.shunya-oracle` | Glass AI bar with glow pulse |
| `.shunya-pulse-ring` | Expanding ring animation |
| `.shunya-metric-card` | KPI card with hover lift |
| `.shunya-count-up` | Fade-in number animation |
| `.shunya-flow-item` | Slide-in from left |
| `.shunya-flow-dot` | Pulsing connection dot |
| `.shunya-space-card` | Space card with hover glow |
| `.shunya-glass` | Glass morphism effect |
| `.shunya-heartbeat-dot` | System heartbeat pulse |
| `.shunya-suggestion` | Staggered suggestion pill |
| `.shunya-empty-icon` | Floating empty state icon |

### 5.4 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 6. Motion Implementation

### 6.1 framer-motion

```tsx
import { motion, AnimatePresence } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
>
  {children}
</motion.div>
```

### 6.2 Stagger Children

```tsx
const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
};

<motion.div variants={container} initial="hidden" animate="show">
  {items.map(i => <motion.div key={i.id} variants={item}>{i.name}</motion.div>)}
</motion.div>
```

### 6.3 When to Animate

| Context | Animate? | How |
|---------|----------|-----|
| Panel opens | Yes | slideUp, spring |
| Panel closes | Yes | slideDown, easeOut |
| List appears | Yes | staggerChildren |
| KPI changes | Yes | countUp animation |
| Error appears | Yes | fadeIn |
| AI executes | Yes | step progress |
| Background orbs | Yes | CSS keyframes |
| Empty state icon | Yes | CSS float animation |
| Routine page scroll | No | — |

---

## 7. Responsive Utilities

### 7.1 Breakpoint Reference

```tsx
// Mantine breakpoints
const breakpoints = {
  xs: 480,
  sm: 768,
  md: 1024,
  lg: 1440,
  xl: 1920,
};

// Responsive props
<SimpleGrid cols={{ base: 1, xs: 2, sm: 3, md: 4, lg: 6 }} />
<Text visibleFrom="sm" hiddenFrom="md" />
```

### 7.2 Layout Max Width

```tsx
<Box style={{ maxWidth: 1400, margin: '0 auto' }}>
```

### 7.3 Touch Targets

All interactive elements must have minimum 44×44px touch targets:

```tsx
<ActionIcon size="md" /> {/* 36px — use size="lg" (42px) for mobile */}
```

---

## 8. State Management

### 8.1 Local State

Use React hooks for component-local state:

```tsx
const [items, setItems] = useState<Item[]>([]);
const [loading, setLoading] = useState(true);
```

### 8.2 Event Bus

For cross-component communication:

```tsx
import { eventBus } from '../../api/event-bus';

// Emit
eventBus.emit('object:created', { type: 'invoice', id: 123 });

// Subscribe
useEffect(() => {
  const unsub = eventBus.on('object:created', (data) => { /* handle */ });
  return unsub;
}, []);
```

### 8.3 Session State

```tsx
import { SessionManager } from '../../api/session';
import { saveProfileSession, getCurrentProfileSession, clearProfileSession } from '../../api/profile';
```

---

## 9. API Patterns

### 9.1 Authenticated Fetch

Always use `fetchWithAuth` for API calls:

```tsx
import { fetchWithAuth } from '../../api/fetch-with-auth';

const res = await fetchWithAuth('/api/v1/objects/proposal', { credentials: 'include' });
if (!res.ok) throw new Error(`Server error (${res.status})`);
const body = await res.json();
const items = body.data ?? body.items ?? [];
```

### 9.2 Response Shape

The backend returns:

```typescript
// Success
{ success: true, data: [...] }
// Error
{ success: false, error: "message" }
```

### 9.3 Authentication

- Session cookie set by backend on sign-in
- `X-Identity-Id` header set by `fetchWithAuth` from sessionStorage
- `X-Workspace-Id` header set by `fetchWithAuth` from sessionStorage

---

## 10. Testing

### 10.1 TypeScript

```bash
npx tsc --noEmit
```

### 10.2 ESLint

```bash
npx eslint "src/**/*.{ts,tsx}" --quiet
```

### 10.3 Build

```bash
npm run build
```

### 10.4 pytest (Backend)

```bash
cd .. && source .venv/bin/activate && pytest -x -q
```

---

## 11. Build & Deploy

### 11.1 Build

```bash
cd frontend
npm run build
```

Output goes to `frontend/dist/`. The Flask backend serves this directory as static files.

### 11.2 Backend Restart

```bash
kill -HUP <gunicorn-master-pid>
```

### 11.3 Health Check

```bash
curl http://127.0.0.1:5001/health
```

---

## 12. Code-Splitting

### 12.1 Space Registry

All non-critical panels are lazy-loaded via `space-registry.ts`:

```typescript
import { lazy } from 'react';
export const LazyMyPanel = lazy(() =>
  import('./components/panels/my-panel').then((m) => ({ default: m.MyPanel }))
);
```

### 12.2 Chunk Size Warning Threshold

```bash
# Vite warns when chunks exceed 500KB
# Adjust in vite.config.ts:
build: { chunkSizeWarningLimit: 500 }
```

---

## 13. Performance

### 13.1 Bundle Analysis

```bash
npx vite-bundle-analyzer
```

### 13.2 Key Metrics

| Metric | Target |
|--------|--------|
| Main JS bundle | < 500KB |
| Space panel chunks | < 50KB each |
| API response (p95) | < 500ms |
| Time to Interactive | < 3.5s |

---

*This Engineering Guide is framework-specific. If SHUNYA migrates frameworks, rewrite this document.
The Constitution and Playbook above it shall remain unchanged.*