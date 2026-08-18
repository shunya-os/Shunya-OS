/**
 * useRealityPresence — Connects real SSE events to the SHUNYA Presence system.
 *
 * The causal chain:
 *   REAL EVENT (backend event bus)
 *     → SSE stream (/api/v1/reality/stream)
 *     → Event Bus (reality:snapshot, realtime:created, realtime:updated)
 *     → Presence mode transitions
 *     → AI Resident Panel contextual update
 *     → Calm return to idle
 *
 * No fake timers, no fake heartbeat, no decorative activity.
 * Every state transition is driven by a real event from the backend.
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { bus, type RuntimeEvent } from '../runtimes/event-bus';
import { subscribeSSE } from '../runtimes/sse-runtime';

export type PresenceMode = 'ambient' | 'attentive' | 'suggestive' | 'conversational';

export interface RealityContext {
  objectType?: string;
  objectName?: string;
  objectId?: string;
  eventType?: string;
  timestamp?: string;
  summary?: string;
}

const ATTENTIVE_TIMEOUT_MS = 30_000;  // 30s after last event, return to ambient
const SUGGESTIVE_TIMEOUT_MS = 60_000; // 60s after last suggestion, return to ambient

interface RealityPresenceState {
  mode: PresenceMode;
  context: RealityContext | null;
  lastEvent: RuntimeEvent | null;
  lastEventTime: number | null;
  eventCount: number;
  connected: boolean;
}

/**
 * Subscribe to the reality SSE stream and map real events to
 * Presence mode transitions. Automatically returns to ambient
 * after a configurable timeout of inactivity.
 */
export function useRealityPresence(): RealityPresenceState & {
  acknowledge: () => void;
  setConversational: () => void;
} {
  const [state, setState] = useState<RealityPresenceState>({
    mode: 'ambient',
    context: null,
    lastEvent: null,
    lastEventTime: null,
    eventCount: 0,
    connected: false,
  });

  const returnTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sseRef = useRef<{ close: () => void } | null>(null);

  // Schedule a return to ambient after inactivity
  const scheduleReturnToAmbient = useCallback((timeoutMs: number) => {
    if (returnTimerRef.current) {
      clearTimeout(returnTimerRef.current);
    }
    returnTimerRef.current = setTimeout(() => {
      setState(prev => {
        // Only downgrade if we haven't received a new event
        if (prev.mode === 'ambient') return prev;
        return { ...prev, mode: 'ambient', context: null };
      });
    }, timeoutMs);
  }, []);

  // Connect to SSE and subscribe to events
  useEffect(() => {
    // Subscribe to reality stream
    const realitySSE = subscribeSSE('reality');
    sseRef.current = realitySSE;

    // Mark as connected
    setState(prev => ({ ...prev, connected: true }));

    // Subscribe to real-time events from the events stream
    const unsubCreated = bus.on('realtime:created', (event) => {
      if (event.type !== 'realtime:created') return;
      if (!event.items.length) return;

      const item = event.items[0] as Record<string, unknown>;
      const context: RealityContext = {
        objectType: String(item.object_type || ''),
        objectName: String(item.name || ''),
        objectId: String(item.object_id || ''),
        eventType: 'created',
        timestamp: new Date().toISOString(),
        summary: `New ${item.object_type || 'object'}: ${item.name || 'Untitled'}`,
      };

      setState(prev => ({
        ...prev,
        mode: 'attentive',
        context,
        lastEvent: event,
        lastEventTime: Date.now(),
        eventCount: prev.eventCount + 1,
      }));

      scheduleReturnToAmbient(ATTENTIVE_TIMEOUT_MS);
    });

    const unsubUpdated = bus.on('realtime:updated', (event) => {
      if (event.type !== 'realtime:updated') return;
      if (!event.items.length) return;

      const item = event.items[0] as Record<string, unknown>;
      const context: RealityContext = {
        objectType: String(item.object_type || ''),
        objectName: String(item.name || ''),
        objectId: String(item.object_id || ''),
        eventType: 'updated',
        timestamp: new Date().toISOString(),
        summary: `Updated ${item.object_type || 'object'}: ${item.name || 'Untitled'}`,
      };

      setState(prev => {
        // Don't downgrade from suggestive/conversational on a simple update
        if (prev.mode === 'suggestive' || prev.mode === 'conversational') {
          return { ...prev, context, lastEvent: event, lastEventTime: Date.now() };
        }
        return {
          ...prev,
          mode: 'attentive',
          context,
          lastEvent: event,
          lastEventTime: Date.now(),
          eventCount: prev.eventCount + 1,
        };
      });

      scheduleReturnToAmbient(ATTENTIVE_TIMEOUT_MS);
    });

    // Listen for AI insights (these drive suggestive mode)
    const unsubInsight = bus.on('ai:insight', (event) => {
      if (event.type !== 'ai:insight') return;
      const payload = event.payload;
      const context: RealityContext = {
        eventType: 'insight',
        timestamp: new Date().toISOString(),
        summary: payload.title || 'New insight available',
      };

      setState(prev => ({
        ...prev,
        mode: 'suggestive',
        context,
        lastEvent: event,
        lastEventTime: Date.now(),
        eventCount: prev.eventCount + 1,
      }));

      scheduleReturnToAmbient(SUGGESTIVE_TIMEOUT_MS);
    });

    // Listen for system/reality snapshot events
    const unsubSnapshot = bus.on('reality:snapshot', () => {
      // Reality snapshot received — keep connection alive
      setState(prev => ({ ...prev, connected: true }));
    });

    return () => {
      unsubCreated();
      unsubUpdated();
      unsubInsight();
      unsubSnapshot();
      realitySSE.close();
      if (returnTimerRef.current) clearTimeout(returnTimerRef.current);
    };
  }, [scheduleReturnToAmbient]);

  // Log connection status changes
  useEffect(() => {
    if (state.connected) {
      console.log('[RealityPresence] SSE connected');
    }
  }, [state.connected]);

  const acknowledge = useCallback(() => {
    setState(prev => ({ ...prev, mode: 'ambient', context: null }));
    if (returnTimerRef.current) clearTimeout(returnTimerRef.current);
  }, []);

  const setConversational = useCallback(() => {
    setState(prev => ({ ...prev, mode: 'conversational' }));
    if (returnTimerRef.current) clearTimeout(returnTimerRef.current);
  }, []);

  return { ...state, acknowledge, setConversational };
}