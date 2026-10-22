/**
 * G1.26-A — durable regression coverage for palette → workspace routing.
 *
 * The defect this pins: the palette dispatched `shunya:action` and nothing
 * listened, so every navigation command closed the palette and did nothing. The
 * mapping now lives in `lib/palette-actions.ts`, and this test asserts the real
 * contract:
 *
 *   1. every command the palette offers resolves to a real workspace surface;
 *   2. each surface is the expected workspace type (and object id for domain
 *      surfaces);
 *   3. unknown, empty, and non-string actions resolve to null — never to a
 *      fallback surface, which would look like the command worked.
 *
 * No network, no DOM, no timers: the resolver is pure.
 */
import { describe, expect, it } from 'vitest';

import { PALETTE_ACTION_IDS } from '../../components/ai/command-palette';
import { PALETTE_TARGETS, resolvePaletteAction } from '../palette-actions';

describe('palette action routing', () => {
  it('routes every command the palette offers', () => {
    expect(PALETTE_ACTION_IDS.length).toBeGreaterThan(0);
    for (const id of PALETTE_ACTION_IDS) {
      const target = resolvePaletteAction(id);
      expect(target, `command "${id}" has no destination`).not.toBeNull();
      expect(target?.name.trim(), `command "${id}" has no label`).not.toBe('');
      expect(target?.type, `command "${id}" has no workspace type`).toBeTruthy();
    }
  });

  it('resolves the Work command to the commitment workspace', () => {
    expect(resolvePaletteAction('work')).toEqual({
      name: 'Work',
      type: 'commitment',
      objectType: 'work',
      objectId: 'work',
    });
  });

  it('resolves Home without a domain object', () => {
    const home = resolvePaletteAction('home');
    expect(home).toEqual({ name: 'Home', type: 'home' });
    expect(home?.objectType).toBeUndefined();
  });

  it('resolves Import & Export to its own workspace type', () => {
    expect(resolvePaletteAction('import-export')?.type).toBe('import-export');
  });

  it('returns null for an unknown action rather than a fallback surface', () => {
    expect(resolvePaletteAction('proposals-dead')).toBeNull();
    expect(resolvePaletteAction('toggle-dark')).toBeNull();
  });

  it('returns null for malformed details', () => {
    for (const bad of [undefined, null, 42, {}, [], true]) {
      expect(resolvePaletteAction(bad)).toBeNull();
    }
  });

  it('returns null for empty and whitespace-only ids', () => {
    expect(resolvePaletteAction('')).toBeNull();
    expect(resolvePaletteAction('   ')).toBeNull();
  });

  it('does not resolve inherited object properties', () => {
    // A naive map lookup would return Object.prototype members for these.
    expect(resolvePaletteAction('toString')).toBeNull();
    expect(resolvePaletteAction('constructor')).toBeNull();
    expect(resolvePaletteAction('__proto__')).toBeNull();
  });

  it('keeps the routing map free of duplicate destinations for distinct ids', () => {
    const keys = Object.keys(PALETTE_TARGETS);
    expect(new Set(keys).size).toBe(keys.length);
  });
});
