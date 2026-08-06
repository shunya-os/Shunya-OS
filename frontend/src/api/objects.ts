/**
 * SHUNYA — Object API Client.
 *
 * Typed client for the Phase 0 backend object endpoints:
 *   - Workspace API:      POST/GET/PUT/DELETE /api/v1/objects/workspaces
 *   - Object CRUD API:    POST/GET/PUT/DELETE /api/v1/objects/<type>
 *   - Object Registry:    GET /api/v1/objects/types, GET /api/v1/objects/types/<type>
 *   - File Upload API:    POST /api/v1/upload
 *
 * Every request:
 *   - Reads identity_id from sessionStorage (shunya_session)
 *   - Reads workspace_id from the parameter or sessionStorage (shunya_active_workspace)
 *   - Sets X-Identity-Id and X-Workspace-Id headers
 *   - Returns the JSON response
 */

const BASE = '/api/v1/objects';
const UPLOAD_BASE = '/api/v1';

// ── Types ─────────────────────────────────────────────────────

export interface Workspace {
  id: string;
  name: string;
  workspace_type: 'business' | 'personal' | 'custom';
  icon: string;
  color: string;
  description: string;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceInput {
  name: string;
  workspace_type?: 'business' | 'personal' | 'custom';
  icon?: string;
  color?: string;
  description?: string;
}

export interface ObjectFieldSpec {
  /** Field key, e.g. "company_name" */
  key: string;
  /** Human-readable label, e.g. "Company Name" */
  label?: string;
  /** Input type hint: text | textarea | number | date | email | select | boolean */
  type?: string;
  /** Options for select fields */
  options?: string[];
  /** Whether the field is required */
  required?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Optional help text */
  help?: string;
}

export interface ObjectTypeSchema {
  type: string;
  name: string;
  /** Plain field keys from the backend registry */
  fields: string[];
  /** Field keys that must be present */
  required: string[];
  /** Backend-resolved display-name field */
  name_field?: string;
  /** Derived field specs (labels/input types inferred from field key) */
  field_specs?: ObjectFieldSpec[];
}

export interface ObjectRecord {
  id: number;
  object_id: string;
  workspace_id: string;
  object_type: string;
  name: string;
  status: string;
  data: Record<string, any>;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// ── Session helpers ───────────────────────────────────────────

/** Read identity_id from the shunya_session sessionStorage payload. */
export function getIdentityId(): string | null {
  try {
    // Check shunya_session JSON first (legacy format)
    const raw = sessionStorage.getItem('shunya_session');
    if (raw) {
      try {
        const session = JSON.parse(raw);
        const id = session?.identityId || session?.identity_id || null;
        if (id) return id;
      } catch {
        /* not JSON */
      }
    }
    // Fall back to plain shunya_identity_id (current format)
    const plain = sessionStorage.getItem('shunya_identity_id');
    if (plain) return plain;
    // Final fallback: localStorage
    return localStorage.getItem('shunya_identity_id');
  } catch {
    return null;
  }
}

/** Read the active workspace id from sessionStorage. */
export function getStoredWorkspaceId(): string | null {
  try {
    // Check multiple storage locations for workspace ID
    let wsId = sessionStorage.getItem('shunya_active_workspace');
    if (wsId) return wsId;
    wsId = sessionStorage.getItem('shunya_workspace_id');
    if (wsId) return wsId;
    wsId = localStorage.getItem('shunya_workspace_id');
    return wsId;
  } catch {
    return null;
  }
}

/**
 * Build auth headers for an object API request.
 * workspaceId takes precedence; falls back to sessionStorage.
 * NOTE: Authentication is handled via the shunya_session HTTP-only cookie
 * (set on sign-in by the backend). The legacy X-Identity-Id header is
 * no longer sent by this client — the cookie is more secure.
 */
function authHeaders(workspaceId?: string): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const wsId = workspaceId || getStoredWorkspaceId() || 'spc_business';
  if (wsId) headers['X-Workspace-Id'] = wsId;
  // Also send X-Identity-Id for backward compatibility (cookie is primary)
  const identityId = getIdentityId();
  if (identityId) headers['X-Identity-Id'] = identityId;
  return headers;
}

// ── Request helper ────────────────────────────────────────────

async function request<T = any>(
  path: string,
  options: RequestInit = {},
  workspaceId?: string,
): Promise<ApiResponse<T>> {
  const headers = authHeaders(workspaceId);
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { ...headers, ...((options.headers as Record<string, string>) || {}) },
    credentials: 'include',
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    return {
      success: false,
      data: undefined,
      error: body.error || body.detail || body.message || `Request failed (${res.status})`,
    };
  }
  return body as ApiResponse<T>;
}

function jsonBody(data: unknown): RequestInit {
  return { method: 'POST', body: JSON.stringify(data) };
}

// ── Workspace CRUD ────────────────────────────────────────────

/** List all workspaces for the current identity. */
export async function fetchWorkspaces(): Promise<ApiResponse<Workspace[]>> {
  return request<Workspace[]>('/workspaces');
}

/** Create a new workspace. */
export async function createWorkspace(data: WorkspaceInput): Promise<ApiResponse<Workspace>> {
  return request<Workspace>('/workspaces', jsonBody(data));
}

/** Update an existing workspace. */
export async function updateWorkspace(id: string, data: Partial<WorkspaceInput>): Promise<ApiResponse<Workspace>> {
  return request<Workspace>(`/workspaces/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(data) });
}

/** Archive (soft-delete) a workspace. */
export async function deleteWorkspace(id: string): Promise<ApiResponse<{ id: string; status: string }>> {
  return request<{ id: string; status: string }>(`/workspaces/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

// ── Object CRUD ───────────────────────────────────────────────

/** List objects of a type within a workspace. */
export async function fetchObjects(
  type: string,
  workspaceId?: string,
): Promise<ApiResponse<{ objects: ObjectRecord[]; total: number; page: number; per_page: number }>> {
  return request<{ objects: ObjectRecord[]; total: number; page: number; per_page: number }>(
    `/${encodeURIComponent(type)}`,
    { method: 'GET' },
    workspaceId,
  );
}

/** Create a new object of a type within a workspace. */
export async function createObject(
  type: string,
  data: Record<string, any>,
  workspaceId?: string,
): Promise<ApiResponse<ObjectRecord>> {
  return request<ObjectRecord>(`/${encodeURIComponent(type)}`, jsonBody(data), workspaceId);
}

/** Fetch a single object by its numeric id. */
export async function getObject(
  type: string,
  id: number | string,
  workspaceId?: string,
): Promise<ApiResponse<ObjectRecord>> {
  return request<ObjectRecord>(
    `/${encodeURIComponent(type)}/${encodeURIComponent(String(id))}`,
    { method: 'GET' },
    workspaceId,
  );
}

/** Update an object — supports both a full data map and a nested { data } merge. */
export async function updateObject(
  type: string,
  id: number | string,
  data: Record<string, any>,
  workspaceId?: string,
): Promise<ApiResponse<ObjectRecord>> {
  return request<ObjectRecord>(
    `/${encodeURIComponent(type)}/${encodeURIComponent(String(id))}`,
    { method: 'PUT', body: JSON.stringify(data) },
    workspaceId,
  );
}

/** Archive (soft-delete) an object. */
export async function deleteObject(
  type: string,
  id: number | string,
  workspaceId?: string,
): Promise<ApiResponse<{ id: number; object_id: string; status: string }>> {
  return request<{ id: number; object_id: string; status: string }>(
    `/${encodeURIComponent(type)}/${encodeURIComponent(String(id))}`,
    { method: 'DELETE' },
    workspaceId,
  );
}

// ── Object Registry ───────────────────────────────────────────

/** Fetch the full object-type registry. */
export async function getObjectTypes(): Promise<ApiResponse<Record<string, Omit<ObjectTypeSchema, 'type'>>>> {
  return request<Record<string, Omit<ObjectTypeSchema, 'type'>>>('/types');
}

/** Fetch the schema for a single object type. */
export async function getObjectTypeSchema(type: string): Promise<ApiResponse<ObjectTypeSchema>> {
  return request<ObjectTypeSchema>(`/types/${encodeURIComponent(type)}`);
}

// ── File Upload ───────────────────────────────────────────────

/** Upload a file. Returns the stored file path + metadata. */
export async function uploadFile(
  file: File,
  workspaceId?: string,
): Promise<ApiResponse<{ path: string; file_name: string; file_type: string; file_size: number }>> {
  const headers: Record<string, string> = {};
  // Auth via shunya_session cookie (credentials: 'include')
  const wsId = workspaceId || getStoredWorkspaceId();
  if (wsId) headers['X-Workspace-Id'] = wsId;

  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${UPLOAD_BASE}/upload`, {
    method: 'POST',
    headers,
    credentials: 'include',
    body: formData,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    return { success: false, data: undefined, error: body.error || body.detail || `Upload failed (${res.status})` };
  }
  return body as ApiResponse<{ path: string; file_name: string; file_type: string; file_size: number }>;
}

// ── Field metadata helpers ────────────────────────────────────

/**
 * Infer a display label from a snake_case field key.
 * e.g. "company_name" → "Company Name", "due_date" → "Due Date".
 */
export function humanizeField(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Infer an input type from a field key. */
export function inferFieldType(key: string): string {
  if (key === 'email') return 'email';
  if (key === 'phone' || key === 'file_path' || key === 'file_type' || key === 'file_size') return 'text';
  if (key === 'amount' || key === 'budget' || key === 'file_size' || key === 'progress') return 'number';
  if (
    key.includes('date') ||
    key === 'deadline' ||
    key === 'issue_date' ||
    key === 'due_date' ||
    key === 'valid_until' ||
    key === 'joined'
  )
    return 'date';
  if (key === 'status' || key === 'priority' || key === 'workspace_type') return 'select';
  if (
    key === 'notes' ||
    key === 'description' ||
    key === 'content' ||
    key === 'terms' ||
    key === 'address' ||
    key === 'summary'
  )
    return 'textarea';
  if (key === 'tags') return 'text';
  return 'text';
}

/** Infer select options for known enum-like fields. */
export function inferFieldOptions(key: string): string[] | undefined {
  if (key === 'status') return ['active', 'pending', 'completed', 'archived', 'draft', 'sent', 'paid', 'overdue'];
  if (key === 'priority') return ['low', 'medium', 'high', 'urgent'];
  if (key === 'workspace_type') return ['business', 'personal', 'custom'];
  return undefined;
}

/** Convert a backend registry entry (string keys) into rich field specs. */
export function buildFieldSpecs(fields: string[], required: string[] = []): ObjectFieldSpec[] {
  return fields.map((key) => ({
    key,
    label: humanizeField(key),
    type: inferFieldType(key),
    options: inferFieldOptions(key),
    required: required.includes(key),
  }));
}
