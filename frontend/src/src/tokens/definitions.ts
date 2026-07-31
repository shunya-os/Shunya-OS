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
 * Colour palettes (primary/secondary/surface/semantic/dark)
 * Spacing scale, typography scale, elevation, radius, timing
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * (none)
 */

// ── Source of Truth ───────────────────────────────────────────

export const tokens = {
  colour: {
    primary: { 50: '#F5F2ED', 100: '#E8E3DA', 200: '#D1CAB8', 300: '#BAB096', 400: '#A39774', 500: '#8B7D52', 600: '#6F643E', 700: '#544B2E', 800: '#38321E', 900: '#1D190F', 950: '#0E0C07' },
    secondary: { 50: '#FEF6E7', 100: '#FDEBCB', 200: '#FBD79A', 300: '#F9C368', 400: '#F7AF36', 500: '#D4A84B', 600: '#A9863C', 700: '#7F652D', 800: '#55431E', 900: '#2B220F', 950: '#151107' },
    surface: { 50: '#FFFBFA', 100: '#F9F4F0', 200: '#F0E9E3', 300: '#E5DCD4', 400: '#D8CDC2', 500: '#C9BBB0', 600: '#B8A99E', 700: '#A5958B', 800: '#8F8077', 900: '#756A62', 950: '#5A514B' },
  },
  dark: {
    primary: { 50: '#1A1A1E', 100: '#222226', 200: '#2D2D32', 300: '#38383E', 400: '#44444A', 500: '#505058', 600: '#5E5E66', 700: '#6E6E76', 800: '#808088', 900: '#94949C', 950: '#AAAA12' },
    surface: { 50: '#141416', 100: '#1C1C20', 200: '#242428', 300: '#2C2C30', 400: '#343438', 500: '#3C3C40', 600: '#46464A', 700: '#505054', 800: '#5C5C60', 900: '#68686C', 950: '#76767A' },
  },
  semantic: {
    success: { base: '#2D6A4F', light: '#D8EDE3', dark: '#1E4836' },
    warning: { base: '#E09F3E', light: '#FDF0D6', dark: '#8B5E1A' },
    danger: { base: '#9B2226', light: '#F5D6D7', dark: '#6B1518' },
    info: { base: '#3B82F6', light: '#DBE8FD', dark: '#1D4ED8' },
    finance: { base: '#0F766E', light: '#D1FAE5', dark: '#0D5E57' },
    relationship: { base: '#7C3AED', light: '#EDE9FE', dark: '#5B21B6' },
    executive: { base: '#1E293B', light: '#F1F5F9', dark: '#0F172A' },
    ai: { base: '#D4A84B', light: '#FEF3C7', dark: '#A9863C' },
    learning: { base: '#0891B2', light: '#CFFAFE', dark: '#065B78' },
    neutral: { base: '#64748B', light: '#F1F5F9', dark: '#475569' },
  },
  spacing: { xs: 4, sm: 8, md: 16, lg: 24, xl: 32, '2xl': 48, '3xl': 64 },
  typography: {
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    fontFamilyMono: "'JetBrains Mono', monospace",
    scale: {
      xs: { size: 12, lineHeight: 1.4 }, sm: { size: 14, lineHeight: 1.5 },
      md: { size: 16, lineHeight: 1.6 }, lg: { size: 18, lineHeight: 1.5 },
      xl: { size: 24, lineHeight: 1.4 }, '2xl': { size: 32, lineHeight: 1.3 },
      '3xl': { size: 48, lineHeight: 1.2 }, '4xl': { size: 64, lineHeight: 1.1 },
    },
  },
  elevation: ['none', '0 1px 3px rgba(0,0,0,0.08)', '0 4px 12px rgba(0,0,0,0.10)', '0 8px 24px rgba(0,0,0,0.12)', '0 16px 48px rgba(0,0,0,0.16)'],
  radius: { sm: 4, md: 8, lg: 16, full: '50%' },
  timing: { micro: 100, fast: 200, normal: 300, slow: 500 },
} as const;

// ── Output: CSS Custom Properties ─────────────────────────────

export function cssVariables(theme: 'light' | 'dark' = 'light'): string {
  const t = tokens;
  const p = theme === 'dark' ? t.dark.primary : t.colour.primary;
  const s = theme === 'dark' ? t.dark.surface : t.colour.surface;
  return `
:root {
  --shunya-bg: ${theme === 'dark' ? s[950] : s[50]};
  --shunya-text: ${theme === 'dark' ? s[50] : p[900]};
  --shunya-text-secondary: ${theme === 'dark' ? s[400] : p[600]};
  --shunya-surface-0: ${theme === 'dark' ? s[950] : s[50]};
  --shunya-surface-1: ${theme === 'dark' ? s[100] : s[100]};
  --shunya-surface-2: ${theme === 'dark' ? '#1C1C20' : '#FFFFFF'};
  --shunya-spacing-xs: ${t.spacing.xs}px; --shunya-spacing-sm: ${t.spacing.sm}px;
  --shunya-spacing-md: ${t.spacing.md}px; --shunya-spacing-lg: ${t.spacing.lg}px;
  --shunya-spacing-xl: ${t.spacing.xl}px; --shunya-spacing-2xl: ${t.spacing['2xl']}px;
  --shunya-spacing-3xl: ${t.spacing['3xl']}px;
  --shunya-font-family: ${t.typography.fontFamily};
  --shunya-font-size-xs: ${t.typography.scale.xs.size}px;
  --shunya-font-size-sm: ${t.typography.scale.sm.size}px;
  --shunya-font-size-md: ${t.typography.scale.md.size}px;
  --shunya-font-size-lg: ${t.typography.scale.lg.size}px;
  --shunya-font-size-xl: ${t.typography.scale.xl.size}px;
  --shunya-font-size-2xl: ${t.typography.scale['2xl'].size}px;
  --shunya-font-size-3xl: ${t.typography.scale['3xl'].size}px;
  --shunya-font-size-4xl: ${t.typography.scale['4xl'].size}px;
  --shunya-radius-sm: ${t.radius.sm}px; --shunya-radius-md: ${t.radius.md}px;
  --shunya-radius-lg: ${t.radius.lg}px;
  --shunya-elevation-0: ${t.elevation[0]}; --shunya-elevation-1: ${t.elevation[1]};
  --shunya-elevation-2: ${t.elevation[2]}; --shunya-elevation-3: ${t.elevation[3]};
  --shunya-elevation-4: ${t.elevation[4]};
  --shunya-timing-micro: ${t.timing.micro}ms; --shunya-timing-fast: ${t.timing.fast}ms;
  --shunya-timing-normal: ${t.timing.normal}ms; --shunya-timing-slow: ${t.timing.slow}ms;
  --shunya-color-primary: ${p[500]}; --shunya-color-secondary: ${t.colour.secondary[500]};
  --shunya-color-success: ${t.semantic.success.base};
  --shunya-color-warning: ${t.semantic.warning.base};
  --shunya-color-danger: ${t.semantic.danger.base};
  --shunya-color-finance: ${t.semantic.finance.base};
  --shunya-color-relationship: ${t.semantic.relationship.base};
  --shunya-color-ai: ${t.semantic.ai.base};
}`;
}

// ── Output: JSON Schema (for Figma, documentation generators) ─

export function tokenSchema(): Record<string, unknown> {
  return JSON.parse(JSON.stringify(tokens));
}

// ── Output: Flat key-value map (for Storybook theming, tests) ──

export function flatTokens(theme: 'light' | 'dark' = 'light'): Record<string, string> {
  const kv: Record<string, string> = {};
  const lines = cssVariables(theme).replace(':root {', '').replace('}', '').split(';');
  for (const line of lines) {
    const m = line.trim().match(/^(--[\w-]+):\s*(.+)$/);
    if (m) kv[m[1]] = m[2];
  }
  return kv;
}