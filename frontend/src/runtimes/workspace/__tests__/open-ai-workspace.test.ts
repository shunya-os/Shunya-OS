// @vitest-environment jsdom
/**
 * Opening the resident AI workspace — regression guard for a production defect
 * I introduced.
 *
 * "Ask SHUNYA anything" called `open('Ask SHUNYA', 'ai')`. The router gained an
 * `'ai'` branch, but the workspace store keeps a hardcoded DOMAIN_TYPES allow-list
 * of types that render IMMEDIATELY (self-contained panels that fetch their own
 * data). `'ai'` was not in it, so the workspace was created with status
 * 'loading' and waited for ObjectLoaded/TimelineLoaded events that never arrive
 * for this surface. It timed out and became 'error', so the human saw
 * "Could not open / Unknown error" instead of the AI surface — the primary
 * affordance on the authenticated home.
 *
 * A type that renders immediately MUST be in DOMAIN_TYPES. This test pins the
 * observable consequence (status 'active', never 'loading'/'error') rather than
 * the implementation detail, so refactors cannot silently reintroduce it.
 */
import { describe, expect, it } from 'vitest';

import { useWorkspaceStore } from '../store';

const SELF_CONTAINED_TYPES = ['ai', 'home', 'conversation', 'search'] as const;

describe('opening the resident AI workspace', () => {
  it('opens the AI surface immediately instead of waiting for load events', () => {
    const id = useWorkspaceStore.getState().open('Ask SHUNYA', 'ai');
    const ws = useWorkspaceStore.getState().workspaces.find((w) => w.identity.id === id);

    expect(ws).toBeTruthy();
    expect(ws!.identity.type).toBe('ai');
    expect(ws!.status).toBe('active');
  });

  it('never leaves a self-contained surface in a state that renders "Could not open"', () => {
    for (const type of SELF_CONTAINED_TYPES) {
      const id = useWorkspaceStore.getState().open(`surface-${type}`, type);
      const ws = useWorkspaceStore.getState().workspaces.find((w) => w.identity.id === id);
      expect(ws, `workspace for type ${type}`).toBeTruthy();
      expect(ws!.status, `type ${type} must not be stuck loading`).not.toBe('loading');
      expect(ws!.status, `type ${type} must not be in the error state`).not.toBe('error');
    }
  });
});