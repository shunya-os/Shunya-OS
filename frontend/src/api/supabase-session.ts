/**
 * Supabase Session Bridge
 *
 * Bridges the Supabase session with the existing SessionManager pattern.
 * On signin/signup, saves access_token and user data to sessionStorage.
 * Provides a getSession() that returns the current Supabase session.
 */
import { supabase } from './supabase';

const SESSION_KEY = 'shunya_supabase_session';

export interface SupabaseBridgeSession {
  access_token: string;
  refresh_token?: string;
  user: {
    id: string;
    email?: string;
    name?: string;
  };
}

/**
 * Save a Supabase session to sessionStorage (bridged to the existing
 * SessionManager pattern used elsewhere in the codebase).
 */
export function saveSupabaseSession(data: {
  access_token: string;
  refresh_token?: string;
  user: { id: string; email?: string; user_metadata?: { full_name?: string; name?: string } };
}) {
  const bridge: SupabaseBridgeSession = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    user: {
      id: data.user.id,
      email: data.user.email,
      name: data.user.user_metadata?.full_name || data.user.user_metadata?.name || '',
    },
  };
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(bridge));
  } catch {
    // sessionStorage unavailable
  }
}

/**
 * Clear the Supabase session from sessionStorage.
 */
export function clearSupabaseSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    // sessionStorage unavailable
  }
}

/**
 * Get the current Supabase bridge session from sessionStorage.
 */
export function getStoredSession(): SupabaseBridgeSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // sessionStorage unavailable
  }
  return null;
}

/**
 * Get the current Supabase session (from the live supabase client,
 * falling back to sessionStorage).
 */
export async function getCurrentSession() {
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session) {
    // Fallback to stored session
    const stored = getStoredSession();
    if (stored) {
      return { session: stored, source: 'storage' as const };
    }
    return { session: null, source: 'none' as const };
  }
  return {
    session: {
      access_token: data.session.access_token,
      refresh_token: data.session.refresh_token,
      user: {
        id: data.session.user.id,
        email: data.session.user.email,
        name: data.session.user.user_metadata?.full_name || data.session.user.user_metadata?.name || '',
      },
    },
    source: 'live' as const,
  };
}
