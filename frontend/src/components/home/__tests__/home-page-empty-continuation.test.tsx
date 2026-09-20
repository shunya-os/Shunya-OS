// @vitest-environment jsdom
/**
 * Home empty states must not be dead ends.
 *
 * The defect this pins: all three empty states rendered a bare paragraph with no
 * way forward — a fresh human with an empty workspace was told "nothing here"
 * and given nothing to do. Each now offers a continuation, and the continuation
 * must reach a surface that ACTUALLY EXISTS. A decorative button would be worse
 * than no button, so these assertions check the destination, not just the label.
 */
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

const openSpy = vi.fn();

vi.mock('../../../runtimes/workspace/store', () => ({
  useWorkspaceStore: { getState: () => ({ open: openSpy }) },
}));

const homeState = {
  activeTasks: [],
  completedTasks: [],
  attentionTasks: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  startPolling: () => () => {},
  refreshActive: vi.fn(),
  clearError: vi.fn(),
  loadAll: vi.fn(),
};

vi.mock('../../../runtimes/home-store', () => ({
  useHomeStore: Object.assign(() => homeState, { getState: () => homeState }),
}));

vi.mock('../../../api/session', () => ({
  SessionManager: { load: () => null },
}));

import { HomePage } from '../home-page';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('HomePage empty-state continuations', () => {
  it('offers a way forward in every empty section', () => {
    render(<HomePage />);
    expect(screen.getByText('Bring your business into SHUNYA')).toBeTruthy();
    expect(screen.getByText('Review your organization')).toBeTruthy();
    expect(screen.getByText('Ask SHUNYA to do something')).toBeTruthy();
  });

  it('keeps the truthful message as well as the continuation', () => {
    render(<HomePage />);
    expect(screen.getByText(/Nothing in motion right now/)).toBeTruthy();
  });

  it('opens the ingestion surface from the SHUNYA NOW empty state', () => {
    render(<HomePage />);
    fireEvent.click(screen.getByText('Bring your business into SHUNYA'));
    expect(openSpy).toHaveBeenCalledWith('Bring data into SHUNYA', 'import-export');
  });

  it('opens the organization workspace from the attention empty state', () => {
    render(<HomePage />);
    fireEvent.click(screen.getByText('Review your organization'));
    expect(openSpy).toHaveBeenCalledWith(
      'Organization', 'object', { objectType: 'people', objectId: 'people' },
    );
  });

  it('opens Ask SHUNYA from the completed empty state', () => {
    render(<HomePage />);
    fireEvent.click(screen.getByText('Ask SHUNYA to do something'));
    expect(openSpy).toHaveBeenCalledWith('Ask SHUNYA', 'ai');
  });
});
