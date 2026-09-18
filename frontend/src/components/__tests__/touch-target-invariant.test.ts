// @vitest-environment jsdom
/**
 * Touch-target invariant — WCAG 2.5.5 and the mobile canon require an
 * interactive target of at least 44x44px.
 *
 * Measured in production before this guard existed: the auth buttons were
 * ~38px tall (padding 10px + 12px text) and the public "Get Started" CTA
 * measured 116x38px — under the minimum on the very first surfaces a human
 * touches.
 *
 * This asserts the invariant against the EXPORTED stylesheet (no filesystem
 * access, so no node types are required). The public CTA is covered by the
 * same rule in `components/public/homepage.tsx` and is verified by live
 * measurement, recorded in the browser audit.
 */
import { describe, expect, it } from 'vitest';

import { authStyles } from '../auth/auth-styles';

const REQUIRED_MIN_HEIGHT = 44;

function styleBlock(source: string, selector: string): string {
  const start = source.indexOf(selector);
  if (start === -1) throw new Error(`selector ${selector} not found in stylesheet`);
  const open = source.indexOf('{', start);
  const close = source.indexOf('}', open);
  return source.slice(open + 1, close);
}

function declaredMinHeightPx(source: string, selector: string): number | null {
  const match = styleBlock(source, selector).match(/min-height:\s*(\d+)px/);
  return match ? Number(match[1]) : null;
}

describe('interactive targets meet the 44px minimum', () => {
  const selectors = ['.sh-auth-btn', '.sh-auth-btn-secondary', '.sh-auth-btn-oauth'];

  for (const selector of selectors) {
    it(`${selector} declares min-height >= ${REQUIRED_MIN_HEIGHT}px`, () => {
      const minHeight = declaredMinHeightPx(authStyles, selector);
      expect(minHeight, `${selector} has no min-height`).not.toBeNull();
      expect(minHeight!).toBeGreaterThanOrEqual(REQUIRED_MIN_HEIGHT);
    });

    it(`${selector} centres its label`, () => {
      // min-height plus flex: the label must not end up top-aligned
      expect(styleBlock(authStyles, selector)).toMatch(/align-items:\s*center/);
      expect(styleBlock(authStyles, selector)).toMatch(/justify-content:\s*center/);
    });
  }
});
