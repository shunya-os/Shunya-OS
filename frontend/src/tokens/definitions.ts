/**
 * Token Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Define every visual token once (the single source of truth)
 * - Generate CSS custom properties (for the browser)
 * - Export TypeScript constants (for components, Storybook, tests)
 * - Export a JSON schema (for Figma plugins, documentation generators)
 *
 * ── Canonical Source ──────────────────────────────────────────
 * Visual Design Bible v1.0 (design/visual-design-bible/1-visual-design-bible.md)
 * Design System Foundation (design/experience/16_design_system_foundation.md)
 * SHUNYA Design Tokens (design/experience/09_design_system.md)
 *
 * ── Key Differences from Prior Implementation ────────────────
 * - Purple removed as brand colour. Gold is the only accent.
 * - Corrected radius to canonical: sm=10, md=16, lg=24, xl=32
 * - Corrected timing: normal=400ms (was 300ms)
 * - Added motion easing per Visual Design Bible §10
 * - Light mode only (v1.0). No dark mode.
 * - shunya- prefix for all CSS variables (unified from mixed sh-/shunya-)
 */

// ── Source of Truth ───────────────────────────────────────────

export const tokens = {
  colour: {
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
    zone: {
      left: '#F3F2F2',
      center: '#FAFAF8',
      right: '#EBEBEA',
      bar: '#FAF9F8',
    },
  },
  semantic: {
    success: { base: '#51CF66', light: '#EBFBEE' },
    warning: { base: '#FAB005', light: '#FFF9DB' },
    danger: { base: '#FF6B6B', light: '#FFF0F0' },
    info: { base: '#74C0FC', light: '#E7F5FF' },
    ai: { base: '#A4865F', light: '#F9EED9' },
    neutral: { base: '#868E96', light: '#F1F3F5' },
  },
  spacing: {
    xs: 4, sm: 8, md: 16, lg: 24, xl: 32,
    '2xl': 48, '3xl': 64, '4xl': 80, '5xl': 96, '6xl': 128,
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontFamilyDisplay: "'Playfair Display', 'Georgia', 'Times New Roman', serif",
    fontFamilyMono: "'SF Mono', 'Fira Code', 'Cascadia Code', monospace",
    fontFamilyDevanagari: "'Noto Sans Devanagari', 'Nirmala UI', 'Sanskrit Text', 'Mukta', serif",
    scale: {
      '5xl': { size: 72, lineHeight: 1.08 },
      '4xl': { size: 56, lineHeight: 1.08 },
      '3xl': { size: 42, lineHeight: 1.08 },
      '2xl': { size: 32, lineHeight: 1.1 },
      xl: { size: 24, lineHeight: 1.2 },
      lg: { size: 18, lineHeight: 1.3 },
      md: { size: 16, lineHeight: 1.5 },
      base: { size: 14, lineHeight: 1.5 },
      sm: { size: 12, lineHeight: 1.5 },
      xs: { size: 10, lineHeight: 1.2 },
    },
  },
  elevation: {
    sm: '0 1px 4px rgba(26,28,29,0.03)',
    md: '0 2px 12px rgba(26,28,29,0.05)',
    lg: '0 4px 24px rgba(26,28,29,0.06)',
    xl: '0 8px 40px rgba(26,28,29,0.08)',
    gold: '0 4px 40px rgba(164,134,95,0.08)',
    button: '0 2px 8px rgba(26,28,29,0.06)',
    buttonHover: '0 4px 16px rgba(26,28,29,0.1)',
  },
  radius: { sm: 10, md: 16, lg: 24, xl: 32, full: '9999px' },
  timing: {
    micro: 100,
    fast: 200,
    normal: 400,
    slow: 600,
    slower: 800,
    slowest: 1200,
    easing: {
      default: 'cubic-bezier(0.22, 1, 0.36, 1)',
      out: 'cubic-bezier(0.16, 1, 0.3, 1)',
      in: 'cubic-bezier(0.4, 0, 0.68, 0.06)',
    },
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
  const g = t.colour.gold;
  const s = t.colour.surface;
  const z = t.colour.zone;

  return `
:root {
  /* ── Background & Surface (Warm Light) ── */
  --shunya-bg: #FBF8F5;
  --shunya-surface: #FFFFFF;
  --shunya-surface-subtle: ${s[100]};
  --shunya-surface-raised: #FFFFFF;
  --shunya-glass: rgba(255,255,255,0.6);
  --shunya-glass-border: rgba(255,255,255,0.2);

  /* ── Zone Surfaces ── */
  --shunya-zone-left: ${z.left};
  --shunya-zone-center: ${z.center};
  --shunya-zone-right: ${z.right};
  --shunya-bar-bg: ${z.bar};

  /* ── Text ── */
  --shunya-text: #1A1C1D;
  --shunya-text-secondary: rgba(26,28,29,0.55);
  --shunya-text-tertiary: rgba(26,28,29,0.35);
  --shunya-text-faint: rgba(26,28,29,0.15);

  /* ── Borders ── */
  --shunya-border: rgba(26,28,29,0.07);
  --shunya-border-hover: rgba(26,28,29,0.14);
  --shunya-border-focus: ${g[500]};

  /* ── Brand (Gold Only) ── */
  --shunya-gold: ${g[500]};
  --shunya-gold-light: ${g[200]};
  --shunya-gold-dark: ${g[600]};
  --shunya-gold-glow: rgba(164,134,95,0.08);

  /* ── Spacing (4px base) ── */
  --shunya-unit: 4px;
  --shunya-space-1: 4px;   --shunya-space-2: 8px;
  --shunya-space-3: 12px;  --shunya-space-4: 16px;
  --shunya-space-5: 20px;  --shunya-space-6: 24px;
  --shunya-space-8: 32px;  --shunya-space-10: 40px;
  --shunya-space-12: 48px; --shunya-space-16: 64px;
  --shunya-space-20: 80px; --shunya-space-24: 96px;
  --shunya-space-32: 128px;

  /* ── Typography ── */
  --shunya-font-display: ${t.typography.fontFamilyDisplay};
  --shunya-font-body: ${t.typography.fontFamily};
  --shunya-font-mono: ${t.typography.fontFamilyMono};
  --shunya-font-devanagari: ${t.typography.fontFamilyDevanagari};
  --shunya-text-5xl: ${t.typography.scale['5xl'].size}px;
  --shunya-text-4xl: ${t.typography.scale['4xl'].size}px;
  --shunya-text-3xl: ${t.typography.scale['3xl'].size}px;
  --shunya-text-2xl: ${t.typography.scale['2xl'].size}px;
  --shunya-text-xl: ${t.typography.scale.xl.size}px;
  --shunya-text-lg: ${t.typography.scale.lg.size}px;
  --shunya-text-md: ${t.typography.scale.md.size}px;
  --shunya-text-base: ${t.typography.scale.base.size}px;
  --shunya-text-sm: ${t.typography.scale.sm.size}px;
  --shunya-text-xs: ${t.typography.scale.xs.size}px;
  --shunya-leading-tight: ${t.leading.tight};
  --shunya-leading-snug: ${t.leading.snug};
  --shunya-leading-normal: ${t.leading.normal};
  --shunya-leading-relaxed: ${t.leading.relaxed};
  --shunya-leading-loose: ${t.leading.loose};
  --shunya-tracking-tight: ${t.tracking.tight};
  --shunya-tracking-normal: ${t.tracking.normal};
  --shunya-tracking-wide: ${t.tracking.wide};
  --shunya-tracking-wider: ${t.tracking.wider};
  --shunya-tracking-widest: ${t.tracking.widest};
  --shunya-tracking-ultra: ${t.tracking.ultra};

  /* ── Elevation ── */
  --shunya-shadow-sm: ${t.elevation.sm};
  --shunya-shadow-md: ${t.elevation.md};
  --shunya-shadow-lg: ${t.elevation.lg};
  --shunya-shadow-xl: ${t.elevation.xl};
  --shunya-shadow-gold: ${t.elevation.gold};
  --shunya-shadow-button: ${t.elevation.button};
  --shunya-shadow-button-hover: ${t.elevation.buttonHover};

  /* ── Radius ── */
  --shunya-radius-sm: ${t.radius.sm}px;
  --shunya-radius-md: ${t.radius.md}px;
  --shunya-radius-lg: ${t.radius.lg}px;
  --shunya-radius-xl: ${t.radius.xl}px;
  --shunya-radius-full: ${t.radius.full};

  /* ── Motion ── */
  --shunya-ease: ${t.timing.easing.default};
  --shunya-ease-out: ${t.timing.easing.out};
  --shunya-ease-in: ${t.timing.easing.in};
  --shunya-duration-micro: ${t.timing.micro}ms;
  --shunya-duration-fast: ${t.timing.fast}ms;
  --shunya-duration-normal: ${t.timing.normal}ms;
  --shunya-duration-slow: ${t.timing.slow}ms;
  --shunya-duration-slower: ${t.timing.slower}ms;
  --shunya-duration-slowest: ${t.timing.slowest}ms;

  /* ── Semantic ── */
  --shunya-success: ${t.semantic.success.base};
  --shunya-warning: ${t.semantic.warning.base};
  --shunya-danger: ${t.semantic.danger.base};
  --shunya-info: ${t.semantic.info.base};
  --shunya-success-bg: ${t.semantic.success.light};
  --shunya-warning-bg: ${t.semantic.warning.light};
  --shunya-danger-bg: ${t.semantic.danger.light};
  --shunya-info-bg: ${t.semantic.info.light};

  /* ── Backward-compatible aliases (deprecated — use --shunya-* instead) ── */
  --sh-bg: #FBF8F5;
  --sh-surface: #FFFFFF;
  --sh-surface-subtle: ${s[100]};
  --sh-glass: rgba(255,255,255,0.6);
  --sh-text: #1A1C1D;
  --sh-text-secondary: rgba(26,28,29,0.55);
  --sh-text-tertiary: rgba(26,28,29,0.35);
  --sh-text-faint: rgba(26,28,29,0.15);
  --sh-border: rgba(26,28,29,0.07);
  --sh-border-hover: rgba(26,28,29,0.14);
  --sh-gold: ${g[500]};
  --sh-gold-light: ${g[200]};
  --sh-gold-glow: rgba(164,134,95,0.08);
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