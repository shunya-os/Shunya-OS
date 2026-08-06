/**
 * Session Manager — In-memory session storage with sessionStorage fallback.
 *
 * Handles browsers where sessionStorage is blocked (SecurityError).
 * Falls back to in-memory Map when sessionStorage is unavailable.
 */

const KEY = 'shunya_session';

export interface Session {
  identityId: string;
  email: string;
  name?: string;
  orgId?: string;
  orgName?: string;
}

let inMemorySession: Session | null = null;
let _storageAvailable: boolean | null = null;

function storageAvailable(): boolean {
  if (_storageAvailable !== null) return _storageAvailable;
  try {
    const k = '__shunya_test__';
    sessionStorage.setItem(k, '1');
    sessionStorage.removeItem(k);
    _storageAvailable = true;
  } catch {
    _storageAvailable = false;
  }
  return _storageAvailable;
}

export const SessionManager = {
  save(session: Session): void {
    inMemorySession = session;
    if (storageAvailable()) {
      try {
        sessionStorage.setItem(KEY, JSON.stringify(session));
      } catch {
        /* noop */
      }
    }
  },

  load(): Session | null {
    if (inMemorySession) return inMemorySession;
    if (storageAvailable()) {
      try {
        const raw = sessionStorage.getItem(KEY);
        if (raw) {
          inMemorySession = JSON.parse(raw) as Session;
          return inMemorySession;
        }
      } catch {
        /* noop */
      }
    }
    return null;
  },

  clear(): void {
    inMemorySession = null;
    if (storageAvailable()) {
      try {
        sessionStorage.removeItem(KEY);
      } catch {
        /* noop */
      }
    }
  },
};
