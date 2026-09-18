/**
 * Post-authentication phase decision.
 *
 * The server is the authority on whether a person has completed onboarding; the
 * browser flag is only a cache. The sign-in path used to consult ONLY the cache,
 * so a returning user (valid account, real data) was sent through first-time
 * onboarding on every new tab — while the adjacent session-restore path in
 * app.tsx already read the truth from `GET /api/v1/auth/session`. Verified in a
 * real browser: sign-in for an existing account rendered "Welcome to Your
 * Personal SHUNYA" onboarding.
 */

export type PostAuthPhase = 'workspace' | 'onboarding';

/**
 * Pure decision, so the precedence is testable without rendering the app.
 *
 *   server says complete  -> workspace  (even if the local cache says otherwise)
 *   server says incomplete -> onboarding (even if the local cache says complete)
 *   server unknown         -> fall back to the local cache
 *
 * Server truth must win in BOTH directions: a stale local flag must not grant a
 * finished state, and a missing local flag must not force a finished account
 * back through onboarding.
 */
export function decidePostAuthPhase(
  serverComplete: boolean | null,
  cachedComplete: boolean,
): PostAuthPhase {
  if (serverComplete === true) return 'workspace';
  if (serverComplete === false) return 'onboarding';
  return cachedComplete ? 'workspace' : 'onboarding';
}

/**
 * Read the server's onboarding truth.
 *
 * Returns `null` when the server cannot be reached or is not authenticated, so
 * callers can distinguish "the server says no" from "we could not ask" — the
 * distinction the previous implementation collapsed.
 */
export async function resolveOnboardingComplete(
  doFetch: typeof fetch = fetch,
): Promise<boolean | null> {
  try {
    const response = await doFetch('/api/v1/auth/session', { credentials: 'include' });
    if (!response.ok) return null;
    const data = await response.json();
    if (!data || !data.authenticated) return null;
    return Boolean(data.onboarding_complete);
  } catch {
    return null;
  }
}