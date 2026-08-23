/**
 * RESPONSIVE MATRIX — Adaptive Grid Primitives Verification
 *
 * Validates the complete adaptive surface system:
 * 1. Breakpoint detection across all 5 breakpoints
 * 2. Grid column calculation with configurable min-width, max, gap
 * 3. Density calculation across sparsity spectrum
 * 4. Container-query CSS injection idempotency
 * 5. SHUNYA 70/20/10 visual rules proportion calculation
 *
 * @vitest-environment jsdom
 */
import { describe, it, expect, beforeEach } from 'vitest';

import {
  BREAKPOINTS,
  getBreakpoint,
  getGridColumns,
  getDensity,
  getAdaptiveGridStyle,
  injectAdaptiveStyles,
  getVisualProportions,
} from '../grid';

// ── 1. Breakpoint Detection ─────────────────────────────────────

describe('Breakpoint detection', () => {
  it('returns mobile for width < 480', () => {
    expect(getBreakpoint(0)).toBe('mobile');
    expect(getBreakpoint(200)).toBe('mobile');
    expect(getBreakpoint(479)).toBe('mobile');
  });

  it('returns tablet for width 480-767', () => {
    expect(getBreakpoint(480)).toBe('tablet');
    expect(getBreakpoint(600)).toBe('tablet');
    expect(getBreakpoint(767)).toBe('tablet');
  });

  it('returns narrow for width 768-1023', () => {
    expect(getBreakpoint(768)).toBe('narrow');
    expect(getBreakpoint(900)).toBe('narrow');
    expect(getBreakpoint(1023)).toBe('narrow');
  });

  it('returns desktop for width 1024-1439', () => {
    expect(getBreakpoint(1024)).toBe('desktop');
    expect(getBreakpoint(1280)).toBe('desktop');
    expect(getBreakpoint(1439)).toBe('desktop');
  });

  it('returns wide for width >= 1440', () => {
    expect(getBreakpoint(1440)).toBe('wide');
    expect(getBreakpoint(1920)).toBe('wide');
    expect(getBreakpoint(3840)).toBe('wide');
  });

  it('has correct BREAKPOINTS constant values', () => {
    expect(BREAKPOINTS.mobile).toBe(0);
    expect(BREAKPOINTS.tablet).toBe(480);
    expect(BREAKPOINTS.narrow).toBe(768);
    expect(BREAKPOINTS.desktop).toBe(1024);
    expect(BREAKPOINTS.wide).toBe(1440);
  });
});

// ── 2. Grid Column Calculation ──────────────────────────────────

describe('Grid column calculation', () => {
  it('returns at least 1 column for any width', () => {
    expect(getGridColumns(0)).toBe(1);
    expect(getGridColumns(50)).toBe(1);
    expect(getGridColumns(100)).toBe(1);
  });

  it('calculates columns based on minColumnWidth default (280)', () => {
    // 300px container: (300 - 16) / (280 + 16) = 284 / 296 ≈ 0.96 → 1
    expect(getGridColumns(300)).toBe(1);
    // 600px container: (600 - 16) / 296 ≈ 1.97 → 1 (because theoretical needs to be >=2)
    // Actually: Math.floor(584 / 296) = 1, max(1, 1) = 1
    expect(getGridColumns(600)).toBe(1);
    // 900px container: (900 - 16) / 296 = 884 / 296 = 2.98 → 2
    expect(getGridColumns(900)).toBe(2);
  });

  it('respects maxColumns config', () => {
    // At 3000px wide: (3000 - 16) / 296 ≈ 10.08 → would be 6 (max default)
    expect(getGridColumns(3000)).toBe(6);
    // With max=3
    expect(getGridColumns(3000, { maxColumns: 3 })).toBe(3);
  });

  it('respects custom minColumnWidth', () => {
    // 800px, minColumnWidth=150: (800-16)/(150+16) = 784/166 ≈ 4.72 → 4
    expect(getGridColumns(800, { minColumnWidth: 150 })).toBe(4);
    // 800px, minColumnWidth=400: (800-16)/(400+16) = 784/416 ≈ 1.88 → 1
    expect(getGridColumns(800, { minColumnWidth: 400 })).toBe(1);
  });

  it('respects custom gap', () => {
    // 1000px, gap=32, min=280: (1000-32)/(280+32) = 968/312 ≈ 3.10 → 3
    expect(getGridColumns(1000, { gap: 32 })).toBe(3);
  });
});

// ── 3. Density Calculation ─────────────────────────────────────

describe('Density calculation', () => {
  it('returns sparse when content ratio < 0.3', () => {
    expect(getDensity(1000, 100)).toBe('sparse');  // ratio = 0.1
    expect(getDensity(1000, 250)).toBe('sparse');  // ratio = 0.25
  });

  it('returns comfortable when ratio 0.3-0.5', () => {
    expect(getDensity(1000, 400)).toBe('comfortable'); // ratio = 0.4
    expect(getDensity(1000, 499)).toBe('comfortable'); // ratio = 0.499
  });

  it('returns compact when ratio 0.5-0.75', () => {
    expect(getDensity(1000, 600)).toBe('compact');  // ratio = 0.6
    expect(getDensity(1000, 749)).toBe('compact');  // ratio = 0.749
  });

  it('returns dense when ratio >= 0.75', () => {
    expect(getDensity(1000, 800)).toBe('dense');   // ratio = 0.8
    expect(getDensity(1000, 1000)).toBe('dense');  // ratio = 1.0
    expect(getDensity(1000, 9999)).toBe('dense');  // ratio >> 1.0
  });

  it('handles edge case of zero width gracefully', () => {
    expect(getDensity(0, 100)).toBe('dense'); // denominator clamped to 1
  });
});

// ── 4. Adaptive Grid Style Generator ────────────────────────────

describe('getAdaptiveGridStyle', () => {
  it('returns grid display with correct template', () => {
    const style = getAdaptiveGridStyle(900);
    expect(style.display).toBe('grid');
    expect(style.gridTemplateColumns).toContain('repeat(');
    expect(style.gridTemplateColumns).toContain('1fr)');
    expect(style.gap).toBe('16px');
  });

  it('includes density custom property', () => {
    const style = getAdaptiveGridStyle(900);
    expect(style['--shunya-density']).toBeDefined();
  });

  it('respects custom gap in output', () => {
    const style = getAdaptiveGridStyle(900, { gap: 24 });
    expect(style.gap).toBe('24px');
  });
});

// ── 5. CSS Injection ───────────────────────────────────────────

describe('injectAdaptiveStyles', () => {
  beforeEach(() => {
    // Clean up any previous style element
    const existing = document.getElementById('sh-adaptive-styles');
    if (existing) existing.remove();
  });

  it('injects a style element into document head', () => {
    injectAdaptiveStyles();
    const el = document.getElementById('sh-adaptive-styles');
    expect(el).not.toBeNull();
    expect(el?.tagName).toBe('STYLE');
  });

  it('is idempotent — second call does not duplicate', () => {
    injectAdaptiveStyles();
    injectAdaptiveStyles();
    const els = document.querySelectorAll('#sh-adaptive-styles');
    expect(els.length).toBe(1);
  });

  it('contains adaptive grid CSS rules', () => {
    injectAdaptiveStyles();
    const el = document.getElementById('sh-adaptive-styles');
    expect(el?.textContent).toContain('.sh-adaptive-grid');
    expect(el?.textContent).toContain('container-type: inline-size');
  });

  it('contains 70/20/10 visual rules', () => {
    injectAdaptiveStyles();
    const el = document.getElementById('sh-adaptive-styles');
    expect(el?.textContent).toContain('--shunya-prop-whitespace');
    expect(el?.textContent).toContain('.sh-visual-rule-area');
    expect(el?.textContent).toContain('.sh-density-aware');
  });
});

// ── 6. 70/20/10 Visual Proportions ─────────────────────────────

describe('getVisualProportions (70/20/10 rule)', () => {
  it('returns correct proportions for a standard width', () => {
    const p = getVisualProportions(1000);
    expect(p.whitespacePx).toBe(700);  // 70%
    expect(p.infoPx).toBe(200);        // 20%
    expect(p.controlsPx).toBe(100);    // 10%
  });

  it('uses floor-based rounding preserving total sum', () => {
    const p = getVisualProportions(333);
    expect(p.whitespacePx).toBe(233);  // Math.floor(333 * 0.70) = 233
    expect(p.infoPx).toBe(66);         // Math.floor(333 * 0.20) = 66
    expect(p.controlsPx).toBe(34);     // 333 - 233 - 66 = 34
    expect(p.whitespacePx + p.infoPx + p.controlsPx).toBe(333);  // sum preserved
  });

  it('sum of proportions always equals container width', () => {
    const widths = [1, 100, 333, 480, 768, 1024, 1440, 1920, 2560];
    for (const w of widths) {
      const p = getVisualProportions(w);
      const sum = p.whitespacePx + p.infoPx + p.controlsPx;
      expect(sum).toBe(w);
    }
  });

  it('handles zero width gracefully', () => {
    const p = getVisualProportions(0);
    expect(p.whitespacePx).toBe(0);
    expect(p.infoPx).toBe(0);
    expect(p.controlsPx).toBe(0);
  });
});

// ── 7. Full Responsive Matrix: combined grid + density + proportions ──

describe('Full responsive matrix — combined validation', () => {
  const widths = [
    { label: 'mobile', w: 375 },
    { label: 'tablet', w: 600 },
    { label: 'narrow', w: 834 },
    { label: 'desktop', w: 1280 },
    { label: 'wide', w: 1920 },
  ];

  for (const { label, w } of widths) {
    it(`computes consistent layout for ${label} (${w}px)`, () => {
      const bp = getBreakpoint(w);
      const cols = getGridColumns(w);
      const density = getDensity(w, 0); // getAdaptiveGridStyle uses contentSize=0
      const style = getAdaptiveGridStyle(w);
      const prop = getVisualProportions(w);

      // Breakpoint matches
      expect(bp).toBe(label as any);

      // Columns sensible
      expect(cols).toBeGreaterThanOrEqual(1);
      expect(cols).toBeLessThanOrEqual(6);

      // Density defined
      expect(['sparse', 'comfortable', 'compact', 'dense']).toContain(density);

      // Grid style valid
      expect(style.display).toBe('grid');
      expect(style['--shunya-density']).toBe(density);

      // Visual proportions sum
      expect(prop.whitespacePx + prop.infoPx + prop.controlsPx).toBe(w);
    });
  }
});