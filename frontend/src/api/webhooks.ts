/**
 * Webhooks API Client — FDA26 Developer/Integration Platform.
 *
 * Server-side webhook subscriptions with HMAC signatures, delivery log,
 * idempotency and retry (handled by the platform backend).
 */

const BASE = '/api/v1/platform/webhooks';

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const extraHeaders: Record<string, string> = {};
  try {
    const raw = sessionStorage.getItem('shunya_session');
    if (raw) {
      const session = JSON.parse(raw);
      if (session.identityId) {
        extraHeaders['X-Identity-Id'] = session.identityId;
      }
    }
  } catch {
    /* noop */
  }
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...extraHeaders, ...opts?.headers },
    credentials: 'include',
    ...opts,
  });
  const body = await r.json().catch(() => ({ success: false, error: `HTTP ${r.status}` }));
  if (!r.ok && !body.success) {
    throw new Error(body.error || `Request failed (${r.status})`);
  }
  return body as T;
}

// ── Types ──

export interface WebhookEntry {
  id: number;
  identity_id: string;
  workspace_id: string | null;
  label: string;
  url: string;
  events: string[];
  secret?: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
  last_delivery_at: string | null;
  last_delivery_status: string;
  delivery_count: number;
}

export interface WebhookDelivery {
  id: number;
  subscription_id: number;
  event_id: string;
  event_name: string;
  attempt: number;
  max_attempts: number;
  status: string;
  http_status: number | null;
  error: string;
  next_retry_at: string | null;
  created_at: string | null;
  delivered_at: string | null;
}

export const AVAILABLE_EVENTS = [
  { id: 'new_invoice', label: 'New Invoice Created' },
  { id: 'invoice_paid', label: 'Invoice Paid' },
  { id: 'new_proposal', label: 'New Proposal Created' },
  { id: 'proposal_accepted', label: 'Proposal Accepted' },
  { id: 'task_completed', label: 'Task Completed' },
  { id: 'contact_added', label: 'Contact Added' },
  { id: 'email_sent', label: 'Email Sent' },
  { id: 'new_note', label: 'New Note Created' },
  { id: 'test', label: 'Test Event' },
] as const;

// ── CRUD ──

export async function fetchWebhooks(): Promise<WebhookEntry[]> {
  const resp = await req<{ success: boolean; data: { webhooks: WebhookEntry[] } }>('');
  return resp.data.webhooks;
}

export async function createWebhook(data: {
  url: string;
  label?: string;
  events: string[];
  is_active?: boolean;
}): Promise<WebhookEntry> {
  const resp = await req<{ success: boolean; data: WebhookEntry }>('', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return resp.data;
}

export async function updateWebhook(
  id: number,
  data: Partial<{ url: string; label: string; events: string[]; is_active: boolean }>,
): Promise<WebhookEntry> {
  const resp = await req<{ success: boolean; data: WebhookEntry }>(`/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  return resp.data;
}

export async function deleteWebhook(id: number): Promise<void> {
  await req<{ success: boolean }>(`/${id}`, { method: 'DELETE' });
}

export async function rotateWebhookSecret(id: number): Promise<WebhookEntry> {
  const resp = await req<{ success: boolean; data: WebhookEntry }>(`/${id}/rotate-secret`, {
    method: 'POST',
  });
  return resp.data;
}

export async function testWebhook(id: number): Promise<WebhookDelivery> {
  const resp = await req<{ success: boolean; data: { delivery: WebhookDelivery } }>(`/${id}/test`, {
    method: 'POST',
  });
  return resp.data.delivery;
}

export async function fetchDeliveries(id: number, limit = 50): Promise<WebhookDelivery[]> {
  const resp = await req<{ success: boolean; data: { deliveries: WebhookDelivery[] } }>(
    `/${id}/deliveries?limit=${limit}`,
  );
  return resp.data.deliveries;
}