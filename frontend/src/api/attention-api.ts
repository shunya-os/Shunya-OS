/**
 * attention-api — the ONE canonical frontend consumption path for persisted
 * event-driven AttentionItems (server truth from /api/v1/attention).
 *
 * Consumers:
 *   - home-store → HomePage "NEEDS YOUR ATTENTION" (the landing surface)
 *   - executive-home → WhatMattersNow (focus surface)
 *
 * Tenancy/authorization is enforced server-side; this client only carries the
 * session (fetchWithAuth adds X-Identity-Id / X-Workspace-Id + credentials).
 * It never filters for security — server truth decides what is visible.
 */

import { fetchWithAuth } from './fetch-with-auth';

export interface PersistedAttentionItem {
  id: number;
  organization_id: number;
  identity_id: string | null;
  workspace_id: string | null;
  source: string;
  state: string;
  priority: number;
  reason: string;
  related_object_id: string | null;
  related_object_type: string | null;
  created_at: string;
  resolved_at: string | null;
  provenance: Record<string, unknown> | null;
}

export interface AttentionApiResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

async function jsonCall<T>(path: string, options: RequestInit = {}): Promise<AttentionApiResult<T>> {
  try {
    const r = await fetchWithAuth(path, options);
    let body: any = null;
    try { body = await r.json(); } catch { body = null; }
    if (!r.ok) {
      const detail = body && (body.detail || body.error);
      if (r.status === 403) return { success: false, error: detail || 'You are not authorized to act on this item.' };
      if (r.status === 409) return { success: false, error: detail || 'This item has already been handled.' };
      if (r.status === 404) return { success: false, error: detail || 'This item no longer exists.' };
      return { success: false, error: detail || `Request failed (${r.status})` };
    }
    return { success: true, data: (body && body.data !== undefined ? body.data : body) as T };
  } catch {
    return { success: false, error: 'SHUNYA could not be reached.' };
  }
}

/** Active AttentionItems for the current authorized context (server-scoped). */
export async function fetchAttentionItems(): Promise<AttentionApiResult<PersistedAttentionItem[]>> {
  return jsonCall<PersistedAttentionItem[]>('/api/v1/attention/');
}

/** Record the human review decision (canonical state transition) + resolve. */
export async function confirmAttentionReview(itemId: number, note = ''):
  Promise<AttentionApiResult<PersistedAttentionItem>> {
  return jsonCall<PersistedAttentionItem>(`/api/v1/attention/${itemId}/confirm-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note }),
  });
}

/** Dismiss ("not now") — canonical dismiss, not a local hide. */
export async function dismissAttentionItem(itemId: number):
  Promise<AttentionApiResult<PersistedAttentionItem>> {
  return jsonCall<PersistedAttentionItem>(`/api/v1/attention/${itemId}/dismiss`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
}
