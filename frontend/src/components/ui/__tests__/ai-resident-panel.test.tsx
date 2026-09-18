// @vitest-environment jsdom
/**
 * AI Resident Panel — the surface "Ask SHUNYA" opens.
 *
 * Two defects were found in this component during the campaign and are pinned
 * here so they cannot come back:
 *   1. it rendered COLLAPSED regardless of initialMode, so routing "Ask SHUNYA"
 *      to it landed the human on a panel with no input — the affordance still
 *      did not present an ask surface;
 *   2. on failure it FABRICATED an assistant reply ("I understand. Let me think
 *      about that."), which is the pretend behaviour the directive prohibits.
 */
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AIResidentPanel } from '../ai-resident-panel';

afterEach(() => {
  // vitest does not auto-cleanup unless globals are enabled, so unmount
  // explicitly or renders accumulate and queries match multiple elements.
  cleanup();
  vi.restoreAllMocks();
});

describe('AIResidentPanel', () => {
  it('opens the ask input when mounted in conversational mode', () => {
    render(<AIResidentPanel initialMode="conversational" />);
    expect(screen.getByPlaceholderText('Ask anything…')).toBeTruthy();
  });

  it('tells the human what the surface does before anything is asked', () => {
    render(<AIResidentPanel initialMode="conversational" />);
    expect(screen.getByText(/company\s+data first/i)).toBeTruthy();
  });

  it('calls the canonical company-first ask endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      json: async () => ({ success: true, answer: 'From your company data: 1 customer.' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<AIResidentPanel initialMode="conversational" />);
    fireEvent.change(screen.getByPlaceholderText('Ask anything…'), {
      target: { value: 'What customers do we have?' },
    });
    fireEvent.click(screen.getByText('→'));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/intelligence/ask');
    expect(await screen.findByText('From your company data: 1 customer.')).toBeTruthy();
  });

  it('never fabricates an answer when the service fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')));

    render(<AIResidentPanel initialMode="conversational" />);
    fireEvent.change(screen.getByPlaceholderText('Ask anything…'), {
      target: { value: 'What needs attention?' },
    });
    fireEvent.click(screen.getByText('→'));

    // a truthful, recoverable error state — not an invented reply
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText('Try again')).toBeTruthy();
    expect(screen.queryByText(/I understand\. Let me think about that\./)).toBeNull();
  });

  it('does not invent an answer when the service responds with failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      json: async () => ({ success: false, error: 'intelligence service unavailable' }),
    }));

    render(<AIResidentPanel initialMode="conversational" />);
    fireEvent.change(screen.getByPlaceholderText('Ask anything…'), {
      target: { value: 'What changed?' },
    });
    fireEvent.click(screen.getByText('→'));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryAllByText(/^\s*$/)).toBeTruthy(); // no phantom assistant bubble
  });
});
