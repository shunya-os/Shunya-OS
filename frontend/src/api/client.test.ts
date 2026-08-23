/**
 * API Client tests — verify real request-building and error-handling logic.
 *
 * These tests mock fetch and assert the client:
 *   1. Builds correct URLs (/api/v1 + path)
 *   2. Sends JSON content-type and credentials
 *   3. Throws on 5xx (server errors)
 *   4. Returns parsed JSON on success and 4xx business errors
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from './client';

const originalFetch = globalThis.fetch;

function mockFetch(status: number, body: unknown) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    status,
    json: () => Promise.resolve(body),
  } as Response);
}

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe('api client request building', () => {
  beforeEach(() => mockFetch(200, { success: true }));

  it('prepends /api/v1 to request paths', async () => {
    await api.query('/health');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/v1/health',
      expect.objectContaining({ headers: expect.anything() }),
    );
  });

  it('sends JSON content-type header', async () => {
    await api.query('/test');
    const [, opts] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect((opts.headers as Record<string, string>)['Content-Type']).toBe('application/json');
  });

  it('sends credentials include for session auth', async () => {
    await api.query('/test');
    const [, opts] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect(opts.credentials).toBe('include');
  });
});

describe('api client error handling', () => {
  it('throws on 5xx server errors', async () => {
    mockFetch(500, { error: 'boom' });
    await expect(api.query('/test')).rejects.toThrow('Server error');
  });

  it('returns parsed JSON for 4xx business errors (no throw)', async () => {
    mockFetch(401, { success: false, error: 'Account not found' });
    const result = await api.query('/test');
    expect(result).toEqual({ success: false, error: 'Account not found' });
  });

  it('returns parsed JSON on 200 success', async () => {
    mockFetch(200, { success: true, data: { id: 42 } });
    const result = await api.query('/test');
    expect(result).toEqual({ success: true, data: { id: 42 } });
  });
});

describe('api signin payload', () => {
  it('sends email + password JSON body to /founder/signin', async () => {
    mockFetch(200, { success: true, redirect: '/workspace/' });
    await api.signin('founder@shunyaos.com', 'secret');
    const [url, opts] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/v1/founder/signin');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body as string)).toEqual({
      email: 'founder@shunyaos.com',
      password: 'secret',
    });
  });
});
