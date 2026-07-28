/**
 * API Client — Generic. No domain knowledge.
 * Only knows: sign in, and query generic endpoints.
 * Domains register themselves as modules.
 */

const BASE = '/api/v1';

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts?.headers },
    credentials: 'include',
    ...opts,
  });
  if (!r.ok) throw new Error(`API ${r.status}: ${r.statusText}`);
  return r.json();
}

export const api = {
  signin: (email: string, password: string) =>
    req<{ success: boolean; name?: string; redirect?: string; error?: string }>('/founder/signin', {
      method: 'POST', body: JSON.stringify({ email, password }),
    }),

  /** Generic query — discover available capabilities. */
  query: <T = any>(path: string, opts?: RequestInit) => req<T>(path, opts),
};