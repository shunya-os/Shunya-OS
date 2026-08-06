/**
 * useRealtimeSync — Continuous Intelligence Runtime hook
 *
 * Subscribes to the SSE delta events stream (`/api/v1/events/stream`) for
 * real-time object updates. No polling — push delivery via the canonical
 * event bus.
 *
 * The SSE Runtime (runtimes/sse-runtime.ts) forwards `realtime:created` and
 * `realtime:updated` events to the bus. This hook subscribes to those events
 * and maintains local state for the component.
 */
import { useEffect, useState } from 'react';
import { bus } from '../runtimes/event-bus';
import { subscribeSSE } from '../runtimes/sse-runtime';

interface RealtimeEvent {
  object_id: string;
  object_type: string;
  workspace_id: string;
  name: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  [key: string]: unknown;
}

interface RealtimeSyncState {
  events: {
    created: RealtimeEvent[];
    updated: RealtimeEvent[];
  };
  lastSync: string | null;
  isSyncing: boolean;
}

/**
 * Subscribes to the SSE stream for real-time object updates.
 * Returns current delta batch, last-sync timestamp, and sync status.
 * Automatically cleans up the SSE connection on unmount.
 */
export function useRealtimeSync(): RealtimeSyncState & { lastSync: string | null } {
  const [state, setState] = useState<RealtimeSyncState>({
    events: { created: [], updated: [] },
    lastSync: null,
    isSyncing: false,
  });

  useEffect(() => {
    const created: RealtimeEvent[] = [];
    const updated: RealtimeEvent[] = [];

    const unsubCreated = bus.on('realtime:created', (e) => {
      if (e.type !== 'realtime:created') return;
      e.items.forEach((item) => created.push(item as RealtimeEvent));
      setState((prev) => ({
        ...prev,
        events: { created: [...created], updated: [...updated] },
        isSyncing: true,
      }));
    });

    const unsubUpdated = bus.on('realtime:updated', (e) => {
      if (e.type !== 'realtime:updated') return;
      e.items.forEach((item) => updated.push(item as RealtimeEvent));
      setState((prev) => ({
        ...prev,
        events: { created: [...created], updated: [...updated] },
        isSyncing: true,
      }));
    });

    // Open the SSE connection
    const sse = subscribeSSE('events');

    return () => {
      unsubCreated();
      unsubUpdated();
      sse.close();
    };
  }, []);

  return { ...state, lastSync: state.lastSync };
}