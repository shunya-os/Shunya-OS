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
  // 4xx responses are valid business errors (e.g. "Account not found")
  // Only throw on 5xx or network errors
  if (r.status >= 500) {
    throw new Error(`Server error (${r.status}). Please try again.`);
  }
  return r.json();
}

export const api = {
  signin: (email: string, password: string) =>
    req<{ success: boolean; name?: string; identity_id?: string; redirect?: string; error?: string }>('/founder/signin', {
      method: 'POST', body: JSON.stringify({ email, password }),
    }),

  /** Generic query — discover available capabilities. */
  query: <T = any>(path: string, opts?: RequestInit) => req<T>(path, opts),

  /** Auto-create foundational objects during onboarding. */
  autoCreateFoundationalObjects: (category: string) =>
    req<{ success: boolean; data?: { objects: any[]; count: number }; error?: string }>('/founder/auto-create-objects', {
      method: 'POST', body: JSON.stringify({ category }),
    }),

  // ── Auth Pages ──

  /** Request a password reset email. */
  forgotPassword: (email: string) =>
    req<{ success: boolean; error?: string }>('/auth/forgot-password', {
      method: 'POST', body: JSON.stringify({ email }),
    }),

  /** Reset password using a reset token. */
  resetPassword: (token: string, password: string) =>
    req<{ success: boolean; error?: string }>('/auth/reset-password', {
      method: 'POST', body: JSON.stringify({ token, password }),
    }),

  /** Request a verification email. */
  requestVerification: (email: string) =>
    req<{ success: boolean; error?: string }>('/auth/request-verification', {
      method: 'POST', body: JSON.stringify({ email }),
    }),

  /** Verify email with a token. */
  verifyEmail: (token: string) =>
    req<{ success: boolean; error?: string }>('/auth/verify-email', {
      method: 'POST', body: JSON.stringify({ token }),
    }),

  /** Get invitation details (name, email, org). */
  getInvitation: (token: string) =>
    req<{ success: boolean; name?: string; email?: string; orgName?: string; error?: string }>(
      `/auth/invitation/${token}`,
    ),

  /** Accept an invitation — set name and password. */
  acceptInvitation: (token: string, name: string, password: string) =>
    req<{ success: boolean; identity_id?: string; error?: string }>('/auth/accept-invitation', {
      method: 'POST', body: JSON.stringify({ token, name, password }),
    }),

  /** Sign up with email, password, and name. */
  signup: (email: string, password: string, name: string) =>
    req<{ success: boolean; identity_id?: string; error?: string }>('/auth/signup', {
      method: 'POST', body: JSON.stringify({ email, password, name }),
    }),

  // ── Onboarding / Org ──

  /** Create an organization. */
  createOrg: (name: string, businessType: string) =>
    req<{ success: boolean; org_id?: string; org_name?: string; error?: string }>('/orgs', {
      method: 'POST', body: JSON.stringify({ company_name: name, business_type: businessType }),
    }),

  /** Ask the intelligence engine a question. */
  ask: (question: string) =>
    req<{ success: boolean; answer?: string; error?: string }>('/intelligence/ask', {
      method: 'POST', body: JSON.stringify({ question }),
    }),

  // ── Workspace API ──

  /** List workspaces for the current identity. */
  listWorkspaces: () =>
    req<{ success: boolean; data: { workspaces: any[] } }>('/workspace'),

  /** Create a new workspace. */
  createWorkspace: (name: string, workspaceType: string, description?: string) =>
    req<{ success: boolean; data: any }>('/workspace', {
      method: 'POST', body: JSON.stringify({ name, workspace_type: workspaceType, description }),
    }),

  /** Switch to a different workspace. */
  switchWorkspace: (workspaceId: string) =>
    req<{ success: boolean; data: { workspace: any } }>('/workspace/switch', {
      method: 'POST', body: JSON.stringify({ workspace_id: workspaceId }),
    }),

  /** Get current workspace context. */
  getWorkspaceContext: () =>
    req<{ success: boolean; data: { workspace_id: string; workspace_name: string; workspace_type: string; capabilities: string[] } }>('/workspace/context'),

  /** Get workspace types. */
  getWorkspaceTypes: () =>
    req<{ success: boolean; data: { types: { type: string; name: string; description: string }[] } }>('/workspace/types'),

  /** Create a business object. */
  createObject: (name: string, objectType: string) =>
    req<{ success: boolean; object_id?: string; object_type?: string; error?: string }>('/objects', {
      method: 'POST', body: JSON.stringify({ name, object_type: objectType }),
    }),
};