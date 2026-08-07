/**
 * fetchWithAuth — Wraps fetch() with the X-Identity-Id header from sessionStorage.
 * Use this in all panel components instead of raw fetch().
 */
export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const headers: Record<string, string> = { ...((options.headers as Record<string, string>) || {}) };
  try {
    // Check multiple storage locations for identity ID
    let identityId = null;
    const raw = sessionStorage.getItem('shunya_session');
    if (raw) {
      try {
        const session = JSON.parse(raw);
        identityId = session.identityId || session.userId;
      } catch {
        identityId = raw;
      }
    }
    if (!identityId) identityId = sessionStorage.getItem('shunya_identity_id');
    if (!identityId) identityId = localStorage.getItem('shunya_identity_id');
    if (identityId) headers['X-Identity-Id'] = identityId;
  } catch {
    /* storage unavailable */
  }
  // Send workspace ID if available
  try {
    const wsId = sessionStorage.getItem('shunya_active_workspace');
    if (wsId) headers['X-Workspace-Id'] = wsId;
  } catch { /* ignore */ }
  return fetch(url, { ...options, headers, credentials: 'include' });
}
