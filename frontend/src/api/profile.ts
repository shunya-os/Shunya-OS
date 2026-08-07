/**
 * Profile Manager — Multi-account/profile switching API.
 *
 * Supports Business / Personal / Custom profiles, each with its own
 * authentication session stored under a profile-scoped sessionStorage key.
 *
 * Key layout:
 *   shunya_profile          — current profile name
 *   shunya_session_{name}   — auth session for that profile
 */

const PROFILE_KEY = 'shunya_profile';
const PROFILES_INDEX_KEY = 'shunya_profiles';
const DEFAULT_PROFILES = ['Business', 'Personal', 'Custom'];

export interface ProfileSession {
  identityId: string;
  email: string;
  name?: string;
  orgId?: string;
  orgName?: string;
}

let _storageAvailable: boolean | null = null;

function storageAvailable(): boolean {
  if (_storageAvailable !== null) return _storageAvailable;
  try {
    const k = '__shunya_profile_test__';
    sessionStorage.setItem(k, '1');
    sessionStorage.removeItem(k);
    _storageAvailable = true;
  } catch {
    _storageAvailable = false;
  }
  return _storageAvailable;
}

function setSessionItem(key: string, value: string): void {
  if (storageAvailable()) {
    try {
      sessionStorage.setItem(key, value);
    } catch {
      /* noop */
    }
  }
}

function getSessionItem(key: string): string | null {
  if (storageAvailable()) {
    try {
      return sessionStorage.getItem(key);
    } catch {
      /* noop */
    }
  }
  return null;
}

function removeSessionItem(key: string): void {
  if (storageAvailable()) {
    try {
      sessionStorage.removeItem(key);
    } catch {
      /* noop */
    }
  }
}

function setLocalItem(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* noop */
  }
}

function getLocalItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

/**
 * Returns the currently active profile name.
 * Reads from sessionStorage 'shunya_profile'. Defaults to 'Business'.
 */
export function getCurrentProfile(): string {
  return getSessionItem(PROFILE_KEY) || 'Business';
}

/**
 * Returns the active profile session for the current profile.
 * Reads profile-scoped sessionStorage key: shunya_session_{profileName}
 */
export function getCurrentProfileSession(): ProfileSession | null {
  const profile = getCurrentProfile();
  const raw = getSessionItem(`shunya_session_${profile}`);
  if (raw) {
    try {
      return JSON.parse(raw) as ProfileSession;
    } catch {
      /* noop */
    }
  }
  return null;
}

/**
 * Switch to a named profile.
 * Saves the profile name, clears the active session, and triggers a page reload
 * so the new profile's session is loaded fresh.
 */
export function switchProfile(name: string): void {
  setSessionItem(PROFILE_KEY, name);
  // Clear the generic session key so page reload picks up profile-scoped session
  removeSessionItem('shunya_session');
  window.location.reload();
}

/**
 * List all known profiles.
 * Returns defaults plus any custom profiles saved in localStorage.
 */
export function listProfiles(): string[] {
  const defaults = [...DEFAULT_PROFILES];
  const custom = getLocalItem(PROFILES_INDEX_KEY);
  if (custom) {
    try {
      const parsed = JSON.parse(custom) as string[];
      for (const p of parsed) {
        if (!defaults.includes(p)) defaults.push(p);
      }
    } catch {
      /* noop */
    }
  }
  return defaults;
}

/**
 * Save a new custom profile name to localStorage.
 * Does not switch to it — call switchProfile(name) after.
 */
export function saveProfile(name: string): void {
  if (!name.trim()) return;
  if (DEFAULT_PROFILES.includes(name.trim())) return;
  const existing = listProfiles();
  if (existing.includes(name.trim())) return;
  existing.push(name.trim());
  setLocalItem(PROFILES_INDEX_KEY, JSON.stringify(existing));
}

/**
 * Save the current auth session scoped to the active profile.
 * This is called after successful authentication to persist the session
 * under the profile-specific key: shunya_session_{profileName}
 */
export function saveProfileSession(session: ProfileSession): void {
  const profile = getCurrentProfile();
  setSessionItem(`shunya_session_${profile}`, JSON.stringify(session));
  // Also save to generic key for backward compatibility
  setSessionItem('shunya_session', JSON.stringify(session));
}

/**
 * Clear the current profile's session (but keep the profile selection).
 */
export function clearProfileSession(): void {
  const profile = getCurrentProfile();
  removeSessionItem(`shunya_session_${profile}`);
  removeSessionItem('shunya_session');
}
