// @vitest-environment jsdom
/**
 * First-object CTA contract.
 *
 * Defects this pins:
 *
 * 1. G1.13 — the CTA was driven by TASK counts, so a workspace with real
 *    business records but no tasks still advertised "Create your first business
 *    object", and a failed/loading object fetch could masquerade as empty.
 *    Correct behaviour: the CTA depends only on a successful emptiness answer.
 *
 * 2. G1.18 / KB-02 — the emptiness answer came from `/api/v1/uop/objects`, a
 *    migration-compatibility store that new writes never touch. Importing
 *    customers therefore left the CTA claiming an empty workspace for ever.
 *    The answer now comes from the authoritative predicate
 *    `GET /api/v1/objects/first-object-state`, which reads every canonical
 *    business store (objects, relationships, leads, suppliers) server-side.
 *
 * Unknown is never empty: pending, failed, unauthorized (403), malformed, and
 * no-organization (400) responses all keep the CTA hidden.
 */
import { render, screen, cleanup, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const openSpy = vi.fn();

vi.mock('../../../runtimes/workspace/store', () => ({
  useWorkspaceStore: Object.assign(
    (selector?: (state: { open: typeof openSpy }) => unknown) =>
      selector ? selector({ open: openSpy }) : { open: openSpy },
    { getState: () => ({ open: openSpy }) },
  ),
}));

const homeState = {
  activeTasks: [],
  completedTasks: [],
  attentionTasks: [],
  reviewItems: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  startPolling: () => () => {},
  refreshActive: vi.fn(),
  clearError: vi.fn(),
  loadAll: vi.fn(),
  refreshLists: vi.fn(),
};

vi.mock('../../../runtimes/home-store', () => ({
  useHomeStore: Object.assign(() => homeState, { getState: () => homeState }),
}));

vi.mock('../../../api/session', () => ({
  SessionManager: { load: () => null },
}));

import { HomePage } from '../home-page';

const CTA_TEXT = 'Create your first business object';
const STATE_URL = '/api/v1/objects/first-object-state';
const LEGACY_URL = '/api/v1/uop/objects';
const fetchMock = vi.fn();

function jsonResponse(payload: unknown, ok = true, status = ok ? 200 : 500) {
  return Promise.resolve({ ok, status, json: async () => payload });
}

function emptyState() {
  return {
    success: true,
    organization_id: 1,
    has_business_data: false,
    total: 0,
    counts: { objects: 0, relationships: 0, leads: 0, suppliers: 0 },
  };
}

function populatedState() {
  return {
    success: true,
    organization_id: 1,
    has_business_data: true,
    total: 1,
    // An import-only organization: no universal objects, one relationship.
    counts: { objects: 0, relationships: 1, leads: 0, suppliers: 0 },
  };
}

function renderHome() {
  return render(
    <MantineProvider>
      <HomePage />
    </MantineProvider>,
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe('HomePage first-object CTA', () => {
  it('asks the authoritative emptiness predicate, not the legacy UOP store', async () => {
    fetchMock.mockReturnValue(jsonResponse(emptyState()));
    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const urls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(urls).toContain(STATE_URL);
    expect(urls).not.toContain(LEGACY_URL);
  });

  it('shows the CTA when the predicate reports no business data', async () => {
    fetchMock.mockReturnValue(jsonResponse(emptyState()));
    renderHome();
    expect(await screen.findByText(CTA_TEXT)).toBeTruthy();
  });

  it('does not show the CTA when only domain records exist, even with zero tasks', async () => {
    fetchMock.mockReturnValue(jsonResponse(populatedState()));
    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByText(CTA_TEXT)).toBeNull());
  });

  it('does not treat a failed predicate request as an empty workspace', async () => {
    fetchMock.mockReturnValue(jsonResponse({ success: false }, false, 500));
    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.queryByText(CTA_TEXT)).toBeNull();
  });

  it('does not treat a rejected request as an empty workspace', async () => {
    fetchMock.mockReturnValue(Promise.reject(new Error('network down')));
    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.queryByText(CTA_TEXT)).toBeNull();
  });

  it('hides the CTA when the caller is not entitled (403)', async () => {
    fetchMock.mockReturnValue(jsonResponse({ success: false, error: 'Forbidden' }, false, 403));
    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.queryByText(CTA_TEXT)).toBeNull();
  });

  it('hides the CTA when the payload carries no authoritative answer', async () => {
    fetchMock.mockReturnValue(jsonResponse({ success: true }));
    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.queryByText(CTA_TEXT)).toBeNull();
  });

  it('does not show the CTA while the predicate is still pending', async () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(screen.queryByText(CTA_TEXT)).toBeNull();
  });

  it('hides the CTA after an import is persisted and the page is reloaded', async () => {
    fetchMock.mockReturnValueOnce(jsonResponse(emptyState()));
    const first = renderHome();
    expect(await screen.findByText(CTA_TEXT)).toBeTruthy();
    first.unmount();

    // Same organization after a successful customer import (relationship row).
    fetchMock.mockReturnValueOnce(jsonResponse(populatedState()));
    renderHome();
    await waitFor(() => expect(screen.queryByText(CTA_TEXT)).toBeNull());
  });

  it('refetches the predicate on remount (organization switch refreshes it)', async () => {
    fetchMock.mockReturnValue(jsonResponse(emptyState()));
    const first = renderHome();
    await screen.findByText(CTA_TEXT);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    first.unmount();

    renderHome();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
