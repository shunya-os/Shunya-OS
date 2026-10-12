// @vitest-environment jsdom
/**
 * ZG-03 B1 — LeadManagement lifecycle behaviors.
 *
 * Pins the UI → API trace for the three review-critical flows:
 * 1. the list renders real API data and "Add Lead" posts through the
 *    tenant-bound create endpoint, then refreshes;
 * 2. search is server-side (debounced `q` param) — not a client-only filter;
 * 3. opening a lead loads detail + history, and a 404 (cross-tenant id or
 *    missing lead) surfaces as "not available in your organization" rather
 *    than a blank panel or a crash.
 */
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LeadManagement } from '../lead-management';

const LEAD_A = {
  id: 718, code: 'L-A-1', source: 'manual', customer_name: 'Acme Travel',
  phone: '', email: '', destination: 'Paris', budget: 100, status: 'new',
  stage: 'new', assigned_to: '', outcome: '', notes: '',
  created_at: '2026-10-12T10:00:00',
};
const LEAD_FOREIGN = { ...LEAD_A, id: 999, code: 'L-X-9', customer_name: 'Foreign Co' };

function jsonRes(status: number, body: unknown) {
  return Promise.resolve({ status, json: () => Promise.resolve(body) } as Response);
}

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  fetchMock = vi.fn((input: RequestInfo | URL, opts?: RequestInit) => {
    const url = String(input);
    const method = opts?.method || 'GET';
    if (method === 'GET' && /^\/api\/v1\/leads\/718$/.test(url)) {
      return jsonRes(200, { lead: LEAD_A });
    }
    if (method === 'GET' && /^\/api\/v1\/leads\/999$/.test(url)) {
      return jsonRes(404, { error: 'Lead not found' });
    }
    if (method === 'GET' && /^\/api\/v1\/leads\/(\?.*)?$/.test(url)) {
      return jsonRes(200, { leads: [LEAD_A, LEAD_FOREIGN], total: 2 });
    }
    if (method === 'POST' && url === '/api/v1/leads/') {
      return jsonRes(200, { id: 720, code: 'L-A-3', success: true });
    }
    if (method === 'GET' && url === '/leads/718/activities') {
      return jsonRes(200, [{ id: 1, lead_id: 718, action: 'created', detail: '', user: 'x', created_at: '2026-10-12T10:00:00' }]);
    }
    if (method === 'GET' && url === '/leads/999/activities') {
      return jsonRes(404, { error: 'Lead not found' });
    }
    return jsonRes(404, { error: 'not mocked' });
  });
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe('LeadManagement (ZG-03 B1)', () => {
  it('renders API leads and creates a new lead through the tenant-bound endpoint', async () => {
    render(<LeadManagement />);
    expect(await screen.findByText('Acme Travel')).toBeTruthy();

    fireEvent.click(screen.getByText('+ Add Lead'));
    fireEvent.change(screen.getByLabelText('Name *'), { target: { value: 'New Prospect' } });
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([u, o]) => String(u) === '/api/v1/leads/' && (o as RequestInit)?.method === 'POST',
      );
      expect(call).toBeTruthy();
      const body = JSON.parse(String((call![1] as RequestInit).body));
      expect(body.customer_name).toBe('New Prospect');
      // tenant is never sent by the client — server resolves it
      expect(body.tenant_id).toBeUndefined();
    });
  });

  it('searches server-side via the q parameter (debounced)', async () => {
    render(<LeadManagement />);
    await screen.findByText('Acme Travel');

    fireEvent.change(screen.getByLabelText('Search leads'), { target: { value: 'acme' } });
    await waitFor(() => {
      const searched = fetchMock.mock.calls.find(([u]) => String(u).includes('q=acme'));
      expect(searched).toBeTruthy();
    }, { timeout: 1500 });
  });

  it('opens detail + history, and a 404 surfaces as not-available (no leak, no crash)', async () => {
    render(<LeadManagement />);
    await screen.findByText('Acme Travel');

    fireEvent.click(screen.getByText('Acme Travel'));
    expect(await screen.findByText('Lead detail')).toBeTruthy();
    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([u]) => String(u) === '/api/v1/leads/718')).toBe(true);
      expect(fetchMock.mock.calls.some(([u]) => String(u) === '/leads/718/activities')).toBe(true);
    });
    expect(await screen.findByText('History')).toBeTruthy();

    // Close, then open the foreign lead → 404 path
    fireEvent.click(screen.getByText('Close'));
    fireEvent.click(screen.getByText('Foreign Co'));
    expect(await screen.findByText('This lead is not available in your organization.')).toBeTruthy();
  });
});
