/**
 * Supabase Client & Auth Helpers
 *
 * Initializes the Supabase client from VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.
 * Exports the client and convenience helpers for email/password and OAuth flows.
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '[supabase] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is not set. ' +
      'Supabase auth will not function until these are configured in .env.',
  );
}

export const supabase = createClient(supabaseUrl || 'http://localhost:54321', supabaseAnonKey || 'placeholder-key', {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});

/** Sign in with email and password. */
export async function signInWithEmail(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email: email.trim().toLowerCase(),
    password,
  });
  if (error) return { success: false as const, error: error.message };
  return { success: true as const, data };
}

/** Sign up with email, password, and optional name. */
export async function signUpWithEmail(email: string, password: string, name?: string) {
  const { data, error } = await supabase.auth.signUp({
    email: email.trim().toLowerCase(),
    password,
    options: name ? { data: { full_name: name } } : undefined,
  });
  if (error) return { success: false as const, error: error.message };
  return { success: true as const, data };
}

/** Sign in with Google OAuth. */
export async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: window.location.origin },
  });
  if (error) return { success: false as const, error: error.message };
  return { success: true as const, data };
}

/** Sign in with GitHub OAuth. */
export async function signInWithGithub() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'github',
    options: { redirectTo: window.location.origin },
  });
  if (error) return { success: false as const, error: error.message };
  return { success: true as const, data };
}

/** Sign out the current user. */
export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) return { success: false as const, error: error.message };
  return { success: true as const };
}

/** Get the current Supabase session. */
export async function getSession() {
  const { data, error } = await supabase.auth.getSession();
  if (error) return { success: false as const, error: error.message, session: null };
  return { success: true as const, session: data.session };
}
