/** Workspace API — Unified API client for FDA16-FDA19 endpoints. */

const BASE = '/api/v1/workspace';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/** Get unified workspace context for any object. */
export async function getObjectWorkspace(objectId: string, objectType?: string): Promise<ApiResponse<any>> {
  const params = new URLSearchParams();
  if (objectType) params.set('type', objectType);
  const url = `${BASE}/objects/${objectId}${params.toString() ? '?' + params.toString() : ''}`;
  const r = await fetch(url, { credentials: 'include' });
  return r.json();
}

/** Get unified timeline for a context. */
export async function getTimeline(
  objectType: string, objectId: string, relationshipId?: number
): Promise<ApiResponse<any[]>> {
  const params = new URLSearchParams({ object_type: objectType, object_id: objectId });
  if (relationshipId) params.set('relationship_id', String(relationshipId));
  const r = await fetch(`${BASE}/timeline?${params}`, { credentials: 'include' });
  return r.json();
}

/** Get memory timeline with truth classifications. */
export async function getMemoryTimeline(relationshipId: number): Promise<ApiResponse<any[]>> {
  const r = await fetch(`${BASE}/timeline/memory?relationship_id=${relationshipId}`, { credentials: 'include' });
  return r.json();
}

/** Ask SHUNYA a contextual question. */
export async function copilotAsk(
  query: string,
  objectType: string,
  objectId: string,
  relationshipId?: number
): Promise<ApiResponse<any>> {
  const r = await fetch(`${BASE}/copilot/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ query, object_type: objectType, object_id: objectId, relationship_id: relationshipId }),
  });
  return r.json();
}

/** Get commitment detail. */
export async function getCommitment(commitmentId: number): Promise<ApiResponse<any>> {
  const r = await fetch(`${BASE}/commitments/${commitmentId}`, { credentials: 'include' });
  return r.json();
}

/** Transition a commitment to a new state. */
export async function transitionCommitment(
  commitmentId: number, status: string, evidence?: string
): Promise<ApiResponse<any>> {
  const r = await fetch(`${BASE}/commitments/${commitmentId}/transition`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ status, evidence }),
  });
  return r.json();
}

/** Create a new commitment. */
export async function createCommitment(data: {
  title: string; owner?: string; due_at?: string;
  relationship_id?: number; issue_type?: string; evidence?: string;
}): Promise<ApiResponse<any>> {
  const r = await fetch(`${BASE}/commitments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return r.json();
}