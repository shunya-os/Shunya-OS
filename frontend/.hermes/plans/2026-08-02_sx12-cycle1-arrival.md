# SX-12 Cycle 1: The Arrival — Homepage IS the OS

> **For Hermes:** Execute directly. This plan describes the implementation.

## Goal

Transform the homepage from a marketing landing page into SHUNYA itself. A first-time visitor immediately understands this is an AI OS, can interact with it, discover capabilities naturally, and transition seamlessly into the authenticated experience — with zero "website to app" feeling.

## Architecture Decision

The homepage no longer has "sections" (hero, capabilities grid, workspace previews, footer). It is ONE coherent surface — the OS. The command surface is the primary element. Capabilities appear as contextual chips, not a grid. The visual language is identical to the authenticated OS.

## Open Experience Review (Constitutional Mandate)

Before implementing, evaluating technologies:

| Technology | Decision | Justification |
|-----------|----------|--------------|
| CSS View Transitions API | **Adopt** | Browser-native smooth transitions between public/auth states. No JS library needed. |
| CSS Container Queries | **Adopt** | Fluid responsive layout without media query explosion. |
| View Transitions (same-document) | **Adapt** | Use for auth modal appearance. Falls back gracefully in unsupported browsers. |
| Current stack (React 19, Motion, Lucide, Radix, Zustand, cmdk) | **Adopt** | Already mature, free, open-source. No replacement needed. |
| Typography (Inter + Noto Sans Devanagari) | **Adopt** | Already free, high-quality, self-hostable. |
| Dark mode toggle | **Reject** | Constitution mandates light mode only. |

## Files to Change

- `shunya_os/frontend/src/components/public/homepage.tsx` — Complete reconstruction
- `shunya_os/frontend/src/app.tsx` — Auth rendered as overlay on homepage, not separate phase
- `shunya_os/frontend/src/components/auth/unified-auth.tsx` — Visual language update (same as OS)
- `shunya_os/frontend/src/components/auth/auth-styles.ts` — Update to match OS visual language

## The Five-Second Experience

**Understand:** This is an AI operating system, not a website.  
**Feel:** Calm, curious, invited to interact.  
**Be able to:** Type a command, see capabilities, sign in without leaving the surface.

## Implementation Plan

### Step 1: Rebuild homepage.tsx

The homepage becomes a single-surface OS:

```
┌──────────────────────────────────────────┐
│  शून्य  ·  v1.0            Sign in  →   │ ← OS bar (matches authenticated)
│                                          │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  शून्य  Ask SHUNYA anything...  🎤📎 │  │ ← Command surface (hero)
│  └────────────────────────────────────┘  │
│  → "SHUNYA understands your business..."  │ ← Typewriter AI text
│                                          │
│  Capabilities:                            │
│  [Customers] [Trips] [Invoices] [Docs]   │ ← Inline chips
│  [Search]   [AI]    [Voice]   [Create]   │
│                                          │
│  Try saying:                              │
│  "Create an invoice for Acme Corp"       │ ← Example command chips
│  "Show me my customers"                  │
│  "Plan a trip to Tokyo"                  │
│                                          │
│  Open source · GitHub · v1.0             │ ← Minimal
└──────────────────────────────────────────┘
```

Key differences from current:
- No hero section with big headline — the command surface IS the hero
- Capabilities are inline chips, not a grid section
- No workspace previews section
- Footer is minimal text, not a section
- Same visual language as authenticated OS (same colors, same bar style)
- Auth opens as an overlay on the same surface

### Step 2: Update app.tsx auth flow

Instead of `phase === 'public'` rendering HomePage and `phase === 'login'` rendering AuthRouter as separate pages, render auth as a modal overlay ON the homepage.

New flow:
- phase='public': Show homepage, auth state=false
- User clicks "Sign in": Set showAuth=true (overlay on homepage)
- User signs in: Show brief boot animation, transition to workspace
- The homepage background stays visible behind the auth overlay

### Step 3: Update auth visual language

The auth form should use the same visual tokens as the OS:
- Same background color (--sh-bg, #FDFCF9)
- Same surface color for the auth card
- Same typography
- No separate "auth page" feel

### Step 4: Verify

- `tsc --noEmit` passes
- Vite build succeeds
- Browser screenshots on desktop, tablet, mobile
- Screen recording of complete journey (public → capabilities exploration → auth → workspace)
- No regressions in authenticated experience

## Verification

1. `cd shunya_os/frontend && npx tsc --noEmit`
2. `npx vite build`
3. Browser: open homepage, verify 5-second experience
4. Browser: click "Sign in", verify auth overlay (no page transition)
5. Browser: sign in, verify workspace loads with same visual language
6. Playwright screenshots at each step