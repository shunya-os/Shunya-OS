# Panchi Club — Frontend Design System

**Version:** 1.0  
**Stack:** Tailwind CSS v3 + shadcn/ui-inspired component tokens  
**Status:** Design specification — ready for implementation  
**Pages affected:** All 9 Jinja2 templates + static assets  
**Goal:** Modern, clean, responsive internal dashboard that feels like Linear/Stripe

---

## 1. Design Tokens

### Colors

Derived from shadcn/ui neutral palette with Panchi Club brand accent.

```
--background:       #ffffff
--foreground:       #0f172a  (slate-900)
--muted:            #f1f5f9  (slate-100)
--muted-foreground: #64748b  (slate-500)
--border:           #e2e8f0  (slate-200)
--ring:             #94a3b8  (slate-400)

--primary:          #2563eb  (blue-600)
--primary-foreground: #ffffff
--primary-hover:    #1d4ed8  (blue-700)

--success:          #16a34a  (green-600)
--success-bg:       #f0fdf4  (green-50)
--warning:          #d97706  (amber-600)
--warning-bg:       #fffbeb  (amber-50)
--danger:           #dc2626  (red-600)
--danger-bg:        #fef2f2  (red-50)

--card:             #ffffff
--card-foreground:  #1e293b  (slate-800)
--card-shadow:      0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)
--card-shadow-hover: 0 4px 12px rgba(0,0,0,0.08)
```

### Typography

```
--font-sans:        'Inter', -apple-system, BlinkMacSystemFont, sans-serif
--font-mono:        'JetBrains Mono', 'SF Mono', Monaco, monospace

--text-xs:          0.75rem   (12px)
--text-sm:          0.875rem  (14px)
--text-base:        1rem      (16px)
--text-lg:          1.125rem  (18px)
--text-xl:          1.25rem   (20px)
--text-2xl:         1.5rem    (24px)
--text-3xl:         1.875rem  (30px)
```

### Spacing

```
--radius-sm:        6px
--radius-md:        8px
--radius-lg:        12px
--radius-xl:        16px
--radius-full:      9999px
```

---

## 2. Component Specs

### 2.1 Navigation (Topbar)

```
┌──────────────────────────────────────────────────────────┐
│  🏝️ Panchi Club  [AI@panchi.club]            [☰ Menu]   │
└──────────────────────────────────────────────────────────┘
```

- Sticky top bar, 64px height, white bg, subtle bottom border
- Left: logo + brand name + AI identity badge (blue pill)
- Right: hamburger dropdown → Dashboard, Leads, Payments, Invoices, Reports, Settings
- Active route highlighted with light blue bg + blue text
- Mobile: full-width, hamburger stays dropdown

**States:**
- Default: `bg-white border-b border-slate-200`
- Scrolled: add `shadow-sm` (via JS class toggle)
- Active nav item: `bg-blue-50 text-blue-600 font-medium`

### 2.2 Stat Cards (Dashboard)

```
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ Today's    │ │ Guest      │ │ Supplier   │ │ Profit     │
│ Leads      │ │ Revenue    │ │ Outflow    │ │            │
│     14     │ │  ₹2,50,000 │ │   ₹80,000  │ │  ₹1,70,000 │
└────────────┘ └────────────┘ └────────────┘ └────────────┘
```

- White card with rounded corners, border, subtle shadow
- Label: uppercase, 11px, tracking-wide, slate-400
- Value: 28px bold, colored (blue/green/red/neutral)
- Responsive grid: 4 cols → 2 cols → 1 col on mobile

### 2.3 Data Tables

```
┌─────────────────────────────────────────────────────────┐
│  Code           Customer   Destination   Status  Action  │
│ ═══════════════════════════════════════════════════════ │
│  PC10072601     Rajat      Bali         🟡 new    View  │
│  PC10072602     Arshlin    Sri Lanka    🟢 conv.  View  │
└─────────────────────────────────────────────────────────┘
```

- Full width, `border-collapse: collapse`
- Header: uppercase, 11px, tracking-wide, slate-500, bg-slate-50
- Rows: alternating subtle hover (`hover:bg-slate-50`)
- Status badges: pill-shaped, colored based on value
  - `new` → amber bg/text
  - `in_progress` → blue bg/text
  - `converted` → green bg/text
  - `cancelled` → red bg/text
- Responsive: horizontal scroll on mobile (`overflow-x-auto`)

### 2.4 Forms

```
┌────────────────────────────────┐
│  Customer Name                 │
│  ┌──────────────────────────┐  │
│  │ Rajat                     │  │
│  └──────────────────────────┘  │
│                                │
│  Destination  [▼ Select...]    │
│  ┌──────────────────────────┐  │
│  │ Bali                     │  │
│  └──────────────────────────┘  │
│                                │
│  [Cancel]        [Create Lead] │
└────────────────────────────────┘
```

- Labels: 13px, font-semibold, slate-700, `mb-1.5`
- Inputs: 12px padding, `border-slate-300`, `rounded-lg`, focus ring `ring-2 ring-blue-500/20 border-blue-500`
- Select dropdowns: same styling as inputs
- Textareas: same, with `resize-vertical`
- Buttons: solid primary (blue) + secondary (slate) + ghost (transparent)
- Form sections grouped in cards with subtle dividers

### 2.5 Buttons

| Variant | Class Pattern | Use Case |
|---------|---------------|----------|
| Primary | `bg-blue-600 text-white hover:bg-blue-700` | Create, Save, Submit |
| Secondary | `bg-slate-100 text-slate-700 hover:bg-slate-200` | Cancel, Back |
| Danger | `bg-red-600 text-white hover:bg-red-700` | Delete actions |
| Ghost | `text-slate-600 hover:bg-slate-100` | Inline actions, links |
| Outline | `border border-slate-300 text-slate-700 hover:bg-slate-50` | Alternative actions |

All buttons: `rounded-lg font-medium text-sm px-4 py-2.5 transition-colors duration-150`

### 2.6 Cards

```
┌─────────────────────────────────────┐
│  Section Title                       │
│  ─────────────────────────────────   │
│  Content here...                     │
└─────────────────────────────────────┘
```

- White bg, `border border-slate-200`, `rounded-xl`, shadow
- Title section: uppercase 11px tracking-wide slate-400, with bottom border
- Optional icon prefix in title
- Padding: `p-6`

### 2.7 Status Badges

```
 New        In Progress     Converted    Cancelled
[🟡 new]   [🔵 in_prog]   [🟢 conv]    [🔴 canc]
```

- Pill shape: `rounded-full px-2.5 py-0.5 text-xs font-medium`
- Color variants:
  - `new`: amber-100 bg, amber-800 text
  - `in_progress`: blue-100 bg, blue-800 text
  - `converted`: green-100 bg, green-800 text
  - `cancelled`: red-100 bg, red-800 text
  - `on_hold`: purple-100 bg, purple-800 text

### 2.8 Flash Messages (Toast)

```
┌──────────────────────────────────────────┐
│  ✅ Lead created successfully         [×] │
└──────────────────────────────────────────┘
```

- Fixed top-right position (or inline in content area)
- Auto-dismiss after 5 seconds
- Color-coded: green for success, red for error, amber for warning
- Close button on hover
- Slide-in from top animation

### 2.9 Activity Timeline

```
┌──────────────────────────────────────────┐
│  10-07-2026 14:30 │ created             │
│                    │ Lead via Telegram   │
│  ─────────────────────────────────────   │
│  10-07-2026 14:35 │ status_changed      │
│                    │ new → in_progress   │
│  ─────────────────────────────────────   │
│  10-07-2026 14:40 │ payment_received    │
│                    │ Guest: ₹50,000      │
└──────────────────────────────────────────┘
```

- Scrollable container (`max-h-80 overflow-y-auto`)
- Each entry: timestamp (mono, slate-500), action badge, detail text
- Separator lines between entries
- Action badges same color scheme as status badges

### 2.10 Detail Page Layout

```
┌─────────────────────────────────────────────┐
│  Lead PC10072601           [Edit] [Delete]   │
├─────────────────────────────────────────────┤
│  ┌─────────┐ ┌──────────────┐               │
│  │ Source  │ │ Status       │               │
│  │ Telegram│ │ [in_progress▼]│               │
│  ├─────────┤ ├──────────────┤               │
│  │ Cust    │ │ Destination  │               │
│  │ Rajat   │ │ Bali         │               │
│  └─────────┘ └──────────────┘               │
├─────────────────────────────────────────────┤
│  Revenue Card      │  Quick Actions         │
│  Guest: ₹50,000    │  [+ Invoice] [+ Paym]  │
│  Margin: ₹30,000   │                        │
├─────────────────────────────────────────────┤
│  Payments Table                              │
├─────────────────────────────────────────────┤
│  Invoices Table                              │
├─────────────────────────────────────────────┤
│  Activity Log (scollable)                    │
└─────────────────────────────────────────────┘
```

- 2-column grid for metadata (key-value pairs)
- 2-column grid for revenue + actions
- Full-width tables below
- Activity log at bottom with scroll

---

## 3. Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|------------|-------|----------------|
| `sm` | 640px | Single column, stacked cards |
| `md` | 768px | 2-column grids activate |
| `lg` | 1024px | Full dashboard layout |
| `xl` | 1280px | Max width container 1280px |

---

## 4. Implementation Plan

### Phase A (Current — Template Overhaul)
1. Install Tailwind CSS via CDN (quickest for Flask/Jinja2)
2. Rewrite `base.html` with Tailwind utility classes
3. Rewrite `dashboard.html` with stat cards grid
4. Update `leads.html`, `lead_detail.html`, `lead_form.html`
5. Update `payments.html`, `invoices.html`, `reports.html`, `settings.html`

### Phase B (Static Assets)
6. Extract common patterns as `@apply` directives in `app.css`
7. Add Inter font from Google Fonts
8. Add JetBrains Mono font for code/monospace elements
9. Add subtle animations (fade-in, slide-down for toasts)

### Phase C (Advanced)
10. Dark mode toggle (optional — store preference in localStorage)
11. Skeleton loading states
12. Date range picker component for reports

---

## 5. Tailwind Config

```javascript
// tailwind.config.js (for reference — not needed when using CDN)
module.exports = {
  content: ['./templates/**/*.html'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        xl: '12px',
        '2xl': '16px',
      },
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
}
```

---

## 6. shadcn/ui Component Mapping

Since shadcn/ui is a React library and this is a Jinja2 project, we map its visual tokens to Jinja2 template partials:

| shadcn Component | Jinja2 Equivalent | Status |
|-----------------|-------------------|--------|
| `Button` | Inline `<button>` with Tailwind classes | ✅ Current |
| `Card` | `.card` div with Tailwind | ✅ Current |
| `Badge` | `.badge` span with variant classes | ✅ Current |
| `Table` | `<table>` with Tailwind styles | ✅ Current |
| `Input` | `<input>` with focus ring styling | ✅ Current |
| `Select` | `<select>` with same styling | ✅ Current |
| `DropdownMenu` | `<details>` nav menu | ✅ Current |
| `Toast` | Flash message banners | ✅ Current |
| `Separator` | `<hr class="border-slate-200">` | ✅ Current |
| `DashboardShell` | `base.html` layout | 🔄 Plan |
| `PageHeader` | `<h2>` + action buttons row | 🔄 Plan |
| `Skeleton` | CSS pulse animation | 📋 Future |
| `Tabs` | Tab navigation for lead detail | 📋 Future |

---

## 7. Implementation Checklist

- [ ] Add Tailwind CDN to `base.html`
- [ ] Add Google Fonts (Inter + JetBrains Mono)
- [ ] Remove old `app.css` inline styles, use Tailwind utilities
- [ ] Convert `base.html` to Tailwind layout
- [ ] Convert `dashboard.html` — stat grid + recent table
- [ ] Convert `leads.html` — search + table with status badges
- [ ] Convert `lead_detail.html` — 2-col metadata, revenue card, tables, timeline
- [ ] Convert `lead_form.html` — clean form layout
- [ ] Convert `payments.html` — form + table
- [ ] Convert `invoices.html` — form + table + PDF link
- [ ] Convert `reports.html` — destination stats
- [ ] Convert `settings.html` — Telegram + supplier form
- [ ] Add active nav highlighting via JS
- [ ] Add flash message auto-dismiss animation
- [ ] Test responsive on mobile widths
- [ ] Update `PROJECT.md` with UI status