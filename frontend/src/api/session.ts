/**
 * Session — persists authentication across page refreshes.
 */

const KEY = 'shunya_session';

export interface Session {
  identityId: string;
  email: string;
  orgId?: string;
  orgName?: string;
}

export const SessionManager = {
  save(session: Session): void {
    try { sessionStorage.setItem(KEY, JSON.stringify(session)); } catch { /* noop */ }
  },

  load(): Session | null {
    try {
      const raw = sessionStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  },

  clear(): void {
    try { sessionStorage.removeItem(KEY); } catch { /* noop */ }
  },

  get isAuthenticated(): boolean {
    return this.load() !== null;
  },
};