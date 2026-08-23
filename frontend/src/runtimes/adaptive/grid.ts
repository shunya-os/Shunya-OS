/**
 * SHUNYA Adaptive Surface System — Container-Aware Responsive Primitives
 *
 * Reusable primitives that adapt to container width, viewport, and content growth.
 * Uses CSS container queries where supported, JS fallback where not.
 */

// ── Breakpoint Constants ──────────────────────────────────────

export const BREAKPOINTS = {
  mobile: 0,
  tablet: 480,
  narrow: 768,
  desktop: 1024,
  wide: 1440,
} as const;

export type Breakpoint = keyof typeof BREAKPOINTS;

export function getBreakpoint(width: number): Breakpoint {
  if (width >= BREAKPOINTS.wide) return 'wide';
  if (width >= BREAKPOINTS.desktop) return 'desktop';
  if (width >= BREAKPOINTS.narrow) return 'narrow';
  if (width >= BREAKPOINTS.tablet) return 'tablet';
  return 'mobile';
}

// ── Density Calculation ───────────────────────────────────────

export type Density = 'sparse' | 'comfortable' | 'compact' | 'dense';

export function getDensity(width: number, contentSize: number): Density {
  const ratio = contentSize / Math.max(width, 1);
  if (ratio < 0.3) return 'sparse';
  if (ratio < 0.5) return 'comfortable';
  if (ratio < 0.75) return 'compact';
  return 'dense';
}

// ── Adaptive Grid ──────────────────────────────────────────────

export interface AdaptiveGridConfig {
  minColumnWidth?: number;
  gap?: number;
  maxColumns?: number;
}

export function getGridColumns(containerWidth: number, config: AdaptiveGridConfig = {}): number {
  const minCol = config.minColumnWidth ?? 280;
  const maxCols = config.maxColumns ?? 6;
  const gap = config.gap ?? 16;
  const available = containerWidth - gap;
  const theoretical = Math.floor(available / (minCol + gap));
  return Math.max(1, Math.min(theoretical, maxCols));
}

// ── Adaptive Layout Style Generator ────────────────────────────

export interface AdaptiveStyle {
  display: string;
  gridTemplateColumns: string;
  gap: string;
  '--shunya-density': Density;
}

export function getAdaptiveGridStyle(width: number, config: AdaptiveGridConfig = {}): Partial<AdaptiveStyle> {
  const cols = getGridColumns(width, config);
  const density = getDensity(width, 0);
  return {
    display: 'grid',
    gridTemplateColumns: `repeat(${cols}, 1fr)`,
    gap: `${config.gap ?? 16}px`,
    '--shunya-density': density,
  };
}

// ── Container Query Aware Styles (injected via <style> tag) ────

export const ADAPTIVE_STYLES = `
/* Adaptive Grid Container */
.sh-adaptive-grid {
  container-type: inline-size;
  container-name: adaptive;
}

@container adaptive (max-width: 480px) {
  .sh-adaptive-grid > * { grid-column: 1 / -1; }
}
@container adaptive (min-width: 481px) and (max-width: 768px) {
  .sh-adaptive-grid > * { grid-column: span 2; }
}
@container adaptive (min-width: 769px) and (max-width: 1024px) {
  .sh-adaptive-grid > * { grid-column: span 3; }
}
@container adaptive (min-width: 1025px) {
  .sh-adaptive-grid > * { grid-column: span 4; }
}

/* Adaptive Card */
.sh-adaptive-card {
  container-type: inline-size;
  container-name: card;
  overflow: hidden;
  height: auto;
  min-height: 0;
}
.sh-adaptive-card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
}
@container card (max-width: 300px) {
  .sh-adaptive-card-content {
    padding: 12px;
    gap: 6px;
    font-size: 0.875em;
  }
}

/* Adaptive Stack */
.sh-adaptive-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  container-type: inline-size;
  container-name: stack;
}
@container stack (max-width: 600px) {
  .sh-adaptive-stack {
    flex-direction: column;
  }
  .sh-adaptive-stack > * { width: 100%; }
}

/* Auto-Growing Text */
.sh-auto-grow {
  resize: none;
  overflow: hidden;
  min-height: 40px;
  field-sizing: content;
}

/* Safe Overflow */
.sh-safe-overflow {
  overflow: auto;
  max-height: 60vh;
  overscroll-behavior: contain;
}

/* Touch Targets (mobile safe) */
.sh-touch-target {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Responsive Data Display */
.sh-responsive-table {
  container-type: inline-size;
  container-name: table;
  overflow: auto;
}
@container table (max-width: 500px) {
  .sh-responsive-table table,
  .sh-responsive-table thead,
  .sh-responsive-table tbody,
  .sh-responsive-table th,
  .sh-responsive-table td,
  .sh-responsive-table tr {
    display: block;
  }
  .sh-responsive-table thead {
    display: none;
  }
  .sh-responsive-table td {
    padding: 8px;
    border: none;
    position: relative;
  }
  .sh-responsive-table td::before {
    content: attr(data-label);
    font-weight: 600;
    display: block;
    font-size: 0.75em;
    color: var(--shunya-text-secondary, #888);
  }
}

/* Fluid Field Groups */
.sh-fluid-fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  container-type: inline-size;
  container-name: fields;
}
@container fields (max-width: 350px) {
  .sh-fluid-fields {
    grid-template-columns: 1fr;
  }
}

/* Mobile-first Fallback Wrapper */
.sh-mobile-safe {
  max-width: 100vw;
  overflow-x: hidden;
  padding: 0 max(16px, env(safe-area-inset-left, 16px)) 0 max(16px, env(safe-area-inset-right, 16px));
}

/* Media Aspect Preservation */
.sh-media-frame {
  position: relative;
  width: 100%;
  height: auto;
  aspect-ratio: attr(data-ratio 16/9);
  overflow: hidden;
}
.sh-media-frame img,
.sh-media-frame video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Print */
@media print {
  .sh-no-print { display: none !important; }
  .sh-print-only { display: block !important; }
}
`;

/**
 * Inject adaptive styles into document head.
 * Call once at app bootstrap.
 */
export function injectAdaptiveStyles(): void {
  if (typeof document === 'undefined') return;
  const id = 'sh-adaptive-styles';
  if (document.getElementById(id)) return;
  const el = document.createElement('style');
  el.id = id;
  el.textContent = ADAPTIVE_STYLES;
  document.head.appendChild(el);
}