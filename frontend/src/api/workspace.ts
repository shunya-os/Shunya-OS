/**
 * Workspace API — CRUD operations for workspaces via SHUNYA Object API.
 *
 * All requests include X-Identity-Id (from the active session) and
 * X-Workspace-Id (from the active workspace) headers.
 */

import { SessionManager } from './session';
import { WorkspaceType } from '../types';

const BASE = '/api/v1/objects';

// ── Helpers ──

let _activeWorkspaceId: string | null = null;

/** Set the active workspace ID (called by WorkspaceContext on switch). */
export function setActiveWorkspaceId(id: string | null): void {
  _activeWorkspaceId = id;
  if (id) {
    try {
      sessionStorage.setItem('shunya_active_workspace', id);
    } catch {
      /* noop */
    }
  } else {
    try {
      sessionStorage.removeItem('shunya_active_workspace');
    } catch {
      /* noop */
    }
  }
}

/** Get the active workspace ID from memory or sessionStorage. */
export function getActiveWorkspaceId(): string | null {
  if (_activeWorkspaceId) return _activeWorkspaceId;
  try {
    const stored = sessionStorage.getItem('shunya_active_workspace');
    if (stored) {
      _activeWorkspaceId = stored;
      return stored;
    }
  } catch {
    /* noop */
  }
  return null;
}

async function authHeaders(): Promise<Record<string, string>> {
  const session = SessionManager.load();
  const wsId = getActiveWorkspaceId();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (session?.identityId) {
    headers['X-Identity-Id'] = session.identityId;
  }
  if (wsId) {
    headers['X-Workspace-Id'] = wsId;
  }
  return headers;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<{ data: T | null; error: string | null; status: number }> {
  try {
    const headers = await authHeaders();
    const res = await fetch(`${BASE}${path}`, {
      ...options,
      headers: { ...headers, ...((options.headers as Record<string, string>) || {}) },
      credentials: 'include',
    });
    const body = await res.json();
    if (!res.ok) {
      return {
        data: null,
        error: body.detail || body.error || `Server error (${res.status})`,
        status: res.status,
      };
    }
    return { data: body.data ?? body, error: null, status: res.status };
  } catch (err) {
    return { data: null, error: err instanceof Error ? err.message : 'Network error', status: 0 };
  }
}

// ── Workspace CRUD ──

/** Fetch all workspaces for the current identity. */
export async function fetchWorkspaces(): Promise<{ workspaces: WorkspaceType[]; error: string | null }> {
  const result = await apiFetch<{ objects?: WorkspaceType[]; workspaces?: WorkspaceType[] }>('/workspaces');
  if (result.error) return { workspaces: [], error: result.error };
  const items = result.data?.objects ?? result.data?.workspaces ?? [];
  return { workspaces: items as WorkspaceType[], error: null };
}

/** Create a new workspace. */
export async function createWorkspace(data: {
  name: string;
  workspace_type: 'business' | 'personal' | 'custom';
  icon?: string;
  color?: string;
  description?: string;
}): Promise<{ workspace: WorkspaceType | null; error: string | null }> {
  const result = await apiFetch<{ object?: WorkspaceType; workspace?: WorkspaceType }>('/workspaces', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (result.error) return { workspace: null, error: result.error };
  const ws = result.data?.object ?? result.data?.workspace ?? null;
  return { workspace: ws as WorkspaceType | null, error: null };
}

/** Update an existing workspace. */
export async function updateWorkspace(
  id: string,
  data: Partial<{
    name: string;
    workspace_type: 'business' | 'personal' | 'custom';
    icon: string;
    color: string;
    description: string;
  }>,
): Promise<{ workspace: WorkspaceType | null; error: string | null }> {
  const result = await apiFetch<{ object?: WorkspaceType; workspace?: WorkspaceType }>(
    `/workspaces/${encodeURIComponent(id)}`,
    {
      method: 'PUT',
      body: JSON.stringify(data),
    },
  );
  if (result.error) return { workspace: null, error: result.error };
  const ws = result.data?.object ?? result.data?.workspace ?? null;
  return { workspace: ws as WorkspaceType | null, error: null };
}

/** Delete a workspace. */
export async function deleteWorkspace(id: string): Promise<{ success: boolean; error: string | null }> {
  const result = await apiFetch<{ success?: boolean }>(`/workspaces/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
  if (result.error) return { success: false, error: result.error };
  return { success: true, error: null };
}

/** Switch to a different workspace (just sets the active workspace ID). */
export async function switchWorkspace(id: string): Promise<void> {
  setActiveWorkspaceId(id);
}

// ── Generic Object CRUD ──

/** List all objects of a given type within the active workspace. */
export async function listObjects(type: string): Promise<{ objects: any[]; total: number; error: string | null }> {
  const result = await apiFetch<{ objects?: any[]; total?: number }>(`/${encodeURIComponent(type)}`);
  if (result.error) return { objects: [], total: 0, error: result.error };
  return {
    objects: result.data?.objects ?? [],
    total: result.data?.total ?? 0,
    error: null,
  };
}

/** Create a new object of a given type. */
export async function createObject(type: string, data: any): Promise<{ object: any | null; error: string | null }> {
  const result = await apiFetch<{ object?: any }>(`/${encodeURIComponent(type)}`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (result.error) return { object: null, error: result.error };
  return { object: result.data?.object ?? result.data ?? null, error: null };
}

/** Update an existing object. */
export async function updateObject(
  type: string,
  id: number,
  data: any,
): Promise<{ object: any | null; error: string | null }> {
  const result = await apiFetch<{ object?: any }>(`/${encodeURIComponent(type)}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (result.error) return { object: null, error: result.error };
  return { object: result.data?.object ?? result.data ?? null, error: null };
}

/** Delete an object. */
export async function deleteObject(type: string, id: number): Promise<{ success: boolean; error: string | null }> {
  const result = await apiFetch<{ success?: boolean }>(`/${encodeURIComponent(type)}/${id}`, {
    method: 'DELETE',
  });
  if (result.error) return { success: false, error: result.error };
  return { success: true, error: null };
}

/** Fetch the object type registry. */
export async function fetchObjectTypes(): Promise<{
  types: Record<string, any>;
  error: string | null;
}> {
  const result = await apiFetch<{ types?: Record<string, any> }>('/types');
  if (result.error) return { types: {}, error: result.error };
  return { types: result.data?.types ?? result.data ?? {}, error: null };
}
