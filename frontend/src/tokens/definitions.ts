/**
 * Token Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Define every visual token once (the single source of truth)
 * - Generate CSS custom properties (for the browser)
 * - Export TypeScript constants (for components, Storybook, tests)
 * - Export a JSON schema (for Figma plugins, documentation generators)
 *
 * ── Events Published ──────────────────────────────────────────
 * (none — passive, queried by components and build tooling)
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * (none)
 *
 * ── Owned State ───────────────────────────────────────────────
 * Colour palettes (purple/gold/surface/semantic)
 * Spacing scale, typography scale, elevation, radius, timing
 * Motion tokens
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * (none)
 *
 * ── Product Experience Constitution §2-5 ────────────────────
 * Light identity. Purple primary, gold secondary.
 * Light mode only.
 */

// ── Source of Truth ───────────────────────────────────────────

export const tokens = {
  colour: {
    purple: {
      50: '#F5F0FF',
      100: '#EDE5FF',
      200: '#D4C4FF',
      300: '#B8A0FF',
      400: '#9C7CF5',
      500: '#6C4AE2',
      600: '#5A3CC4',
      700: '#4A2EA6',
      800: '#3A2288',
      900: '#2A186A',
      950: '#1A0E4C',
    },
    gold: {
      50: '#FDF8F0',
      100: '#F9EED9',
      200: '#F0D9AD',
      300: '#E4C07E',
      400: '#C9A76B',
      500: '#A4865F',
      600: '#8A6F4E',
      700: '#70583D',
      800: '#56422C',
      900: '#3C2C1B',
      950: '#22160A',
    },
    surface: {
      50: '#FAF8F5',
      100: '#F8F7F4',
      200: '#F0EFEA',
      300: '#E5E4DE',
      400: '#D8D7D0',
      500: '#C9C8C0',
      600: '#B8B7AE',
      700: '#A5A49B',
      800: '#8F8E86',
      900: '#75746C',
      950: '#5A5952',
    },
  },
  semantic: {
    success: { base: '#2D6A4F', light: '#D8EDE3' },
    warning: { base: '#B8860B', light: '#FDF0D6' },
    danger: { base: '#B91C1C', light: '#F5D6D7' },
    info: { base: '#3B82F6', light: '#DBE8FD' },
    finance: { base: '#0F766E', light: '#D1FAE5' },
    relationship: { base: '#6C4AE2', light: '#EDE5FF' },
    executive: { base: '#1E293B', light: '#F1F5F9' },
    ai: { base: '#A4865F', light: '#F9EED9' },
    learning: { base: '#0891B2', light: '#CFFAFE' },
    neutral: { base: '#64748B', light: '#F1F5F9' },
  },
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, '2xl': 48, '3xl': 64, '4xl': 80, '5xl': 96 },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontFamilyDisplay: "'Playfair Display', 'Georgia', 'Times New Roman', serif",
    fontFamilyMono: "'SF Mono', 'Fira Code', 'Cascadia Code', monospace",
    fontFamilyDevanagari: "'Noto Sans Devanagari', 'Nirmala UI', 'Sanskrit Text', 'Mukta', serif",
    scale: {
      xs: { size: 10, lineHeight: 1.4 },
      sm: { size: 12, lineHeight: 1.5 },
      base: { size: 14, lineHeight: 1.6 },
      md: { size: 16, lineHeight: 1.6 },
      lg: { size: 18, lineHeight: 1.5 },
      xl: { size: 24, lineHeight: 1.4 },
      '2xl': { size: 32, lineHeight: 1.3 },
      '3xl': { size: 42, lineHeight: 1.2 },
      '4xl': { size: 56, lineHeight: 1.1 },
      '5xl': { size: 72, lineHeight: 1.05 },
    },
  },
  elevation: {
    sm: '0 1px 4px rgba(26,28,29,0.03)',
    md: '0 2px 12px rgba(26,28,29,0.05)',
    lg: '0 4px 24px rgba(26,28,29,0.06)',
    xl: '0 8px 40px rgba(26,28,29,0.08)',
    gold: '0 4px 40px rgba(164,134,95,0.08)',
  },
  radius: { sm: 4, md: 8, lg: 12, xl: 16, full: '50%' },
  timing: {
    micro: 100,
    fast: 200,
    normal: 300,
    slow: 400,
    easing: { enter: 'ease-out', exit: 'ease-in', crossFade: 'ease-in-out' },
  },
  leading: {
    tight: 1.08,
    snug: 1.25,
    normal: 1.5,
    relaxed: 1.75,
    loose: 2,
  },
  tracking: {
    tight: '-0.025em',
    normal: '0',
    wide: '0.02em',
    wider: '0.06em',
    widest: '0.12em',
    ultra: '0.2em',
  },
} as const;

// ── Output: CSS Custom Properties ─────────────────────────────

export function cssVariables(): string {
  const t = tokens;
  const p = t.colour.purple;
  const g = t.colour.gold;
  const s = t.colour.surface;

  return `
:root {
  /* ── Background & Surface ── */
  --sh-bg: #FAF8F5;
  --sh-surface: #FFFFFF;
  --sh-surface-subtle: ${s[100]};
  --sh-surface-raised: #FFFFFF;
  --sh-glass: rgba(255,255,255,0.6);

  /* ── Text ── */
  --sh-text: #1A1C1D;
  --sh-text-secondary: rgba(26,28,29,0.55);
  --sh-text-tertiary: rgba(26,28,29,0.35);
  --sh-text-faint: rgba(26,28,29,0.15);

  /* ── Borders ── */
  --sh-border: rgba(26,28,29,0.08);
  --sh-border-hover: rgba(26,28,29,0.14);

  /* ── Brand ── */
  --sh-purple: ${p[500]};
  --sh-purple-hover: ${p[600]};
  --sh-purple-subtle: rgba(108, 74, 226, 0.08);
  --sh-purple-glow: rgba(108, 74, 226, 0.15);
  --sh-gold: ${g[500]};
  --sh-gold-light: ${g[200]};
  --sh-gold-glow: rgba(164, 134, 95, 0.08);

  /* ── Spacing (4px base) ── */
  --sh-unit: 4px;
  --sh-space-1: 4px;  --sh-space-2: 8px;  --sh-space-3: 12px;
  --sh-space-4: 16px; --sh-space-5: 20px; --sh-space-6: 24px;
  --sh-space-8: 32px; --sh-space-10: 40px; --sh-space-12: 48px;
  --sh-space-16: 64px; --sh-space-20: 80px; --sh-space-24: 96px;

  /* ── Typography ── */
  --sh-font-display: ${t.typography.fontFamilyDisplay};
  --sh-font-body: ${t.typography.fontFamily};
  --sh-font-mono: ${t.typography.fontFamilyMono};
  --sh-font-devanagari: ${t.typography.fontFamilyDevanagari};
  --sh-text-xs: ${t.typography.scale.xs.size}px;
  --sh-text-sm: ${t.typography.scale.sm.size}px;
  --sh-text-base: ${t.typography.scale.base.size}px;
  --sh-text-md: ${t.typography.scale.md.size}px;
  --sh-text-lg: ${t.typography.scale.lg.size}px;
  --sh-text-xl: ${t.typography.scale.xl.size}px;
  --sh-text-2xl: ${t.typography.scale['2xl'].size}px;
  --sh-text-3xl: ${t.typography.scale['3xl'].size}px;
  --sh-text-4xl: ${t.typography.scale['4xl'].size}px;
  --sh-text-5xl: ${t.typography.scale['5xl'].size}px;
  --sh-leading-tight: ${t.leading.tight};
  --sh-leading-snug: ${t.leading.snug};
  --sh-leading-normal: ${t.leading.normal};
  --sh-leading-relaxed: ${t.leading.relaxed};
  --sh-leading-loose: ${t.leading.loose};
  --sh-tracking-tight: ${t.tracking.tight};
  --sh-tracking-normal: ${t.tracking.normal};
  --sh-tracking-wide: ${t.tracking.wide};
  --sh-tracking-wider: ${t.tracking.wider};
  --sh-tracking-widest: ${t.tracking.widest};
  --sh-tracking-ultra: ${t.tracking.ultra};

  /* ── Elevation ── */
  --sh-shadow-sm: ${t.elevation.sm}; --sh-shadow-md: ${t.elevation.md};
  --sh-shadow-lg: ${t.elevation.lg}; --sh-shadow-xl: ${t.elevation.xl};
  --sh-shadow-gold: ${t.elevation.gold};

  /* ── Radius ── */
  --sh-radius-sm: ${t.radius.sm}px; --sh-radius-md: ${t.radius.md}px;
  --sh-radius-lg: ${t.radius.lg}px; --sh-radius-xl: ${t.radius.xl}px;
  --sh-radius-full: ${t.radius.full};

  /* ── Timing ── */
  --sh-timing-micro: ${t.timing.micro}ms; --sh-timing-fast: ${t.timing.fast}ms;
  --sh-timing-normal: ${t.timing.normal}ms; --sh-timing-slow: ${t.timing.slow}ms;
  --sh-easing-enter: ${t.timing.easing.enter};
  --sh-easing-exit: ${t.timing.easing.exit};
  --sh-easing-cross: ${t.timing.easing.crossFade};

  /* ── Semantic ── */
  --sh-success: ${t.semantic.success.base};
  --sh-warning: ${t.semantic.warning.base};
  --sh-danger: ${t.semantic.danger.base};
  --sh-info: ${t.semantic.info.base};
}`;
}

// ── Output: JSON Schema (for Figma, documentation generators) ─

export function tokenSchema(): Record<string, unknown> {
  return JSON.parse(JSON.stringify(tokens));
}

// ── Output: Flat key-value map (for Storybook theming, tests) ──

export function flatTokens(): Record<string, string> {
  const kv: Record<string, string> = {};
  const lines = cssVariables().replace(':root {', '').replace('}', '').split(';');
  for (const line of lines) {
    const m = line.trim().match(/^(--[\w-]+):\s*(.+)$/);
    if (m) kv[m[1]] = m[2];
  }
  return kv;
}
