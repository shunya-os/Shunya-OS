// @vitest-environment jsdom
/**
 * Post-auth phase decision — regression guard for B-1.
 *
 * An existing account was sent through first-time onboarding on every new tab
 * because the sign-in path trusted a browser flag instead of the server. These
 * tests pin the precedence, including the two directions a stale cache can lie.
 */
import { describe, expect, it, vi } from 'vitest';

import { decidePostAuthPhase, resolveOnboardingComplete } from '../post-auth';

describe('decidePostAuthPhase', () => {
  it('sends a server-confirmed account to the workspace', () => {
    expect(decidePostAuthPhase(true, false)).toBe('workspace');
  });

  it('sends a server-incomplete account to onboarding even if the cache claims complete', () => {
    // a stale local flag must not grant a finished state
    expect(decidePostAuthPhase(false, true)).toBe('onboarding');
  });

  it('does not force a finished account back through onboarding when the cache is empty', () => {
    // the exact defect: returning user, fresh tab, no local flag
    expect(decidePostAuthPhase(true, false)).toBe('workspace');
  });

  it('falls back to the cache only when the server cannot be asked', () => {
    expect(decidePostAuthPhase(null, true)).toBe('workspace');
    expect(decidePostAuthPhase(null, false)).toBe('onboarding');
  });
});

describe('resolveOnboardingComplete', () => {
  const jsonResponse = (body: unknown, ok = true) =>
    ({ ok, json: async () => body }) as unknown as Response;

  it('returns the server value when authenticated', async () => {
    const doFetch = vi.fn().mockResolvedValue(
      jsonResponse({ authenticated: true, onboarding_complete: true }),
    );
    expect(await resolveOnboardingComplete(doFetch as unknown as typeof fetch)).toBe(true);
  });

  it('reports false distinctly from unknown', async () => {
    const doFetch = vi.fn().mockResolvedValue(
      jsonResponse({ authenticated: true, onboarding_complete: false }),
    );
    expect(await resolveOnboardingComplete(doFetch as unknown as typeof fetch)).toBe(false);
  });

  it('returns null when unauthenticated, on error, or on network failure', async () => {
    const unauth = vi.fn().mockResolvedValue(jsonResponse({ authenticated: false }));
    expect(await resolveOnboardingComplete(unauth as unknown as typeof fetch)).toBeNull();

    const bad = vi.fn().mockResolvedValue(jsonResponse({}, false));
    expect(await resolveOnboardingComplete(bad as unknown as typeof fetch)).toBeNull();

    const boom = vi.fn().mockRejectedValue(new Error('network down'));
    expect(await resolveOnboardingComplete(boom as unknown as typeof fetch)).toBeNull();
  });
});