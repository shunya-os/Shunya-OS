/**
 * SSE Runtime — Continuous Reality transport.
 *
 * Connects to the backend SSE stream and publishes typed events
 * to the canonical event bus. Handles reconnection with backoff.
 *
 * This is the constitutional transport for Continuous Reality workloads,
 * replacing 15s polling with push delivery.
 *
 * Constitutional basis: Article V §5.5 (typed events, chronological ordering),
 * Article II §2.4 (timeline primacy), Founder Experience (continuous awareness).
 */
import { bus } from './event-bus';

type SSEType = 'reality' | 'events';

interface SSESubscription {
  close: () => void;
}

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30_000;

/**
 * Connect to a backend SSE stream and forward events to the canonical bus.
 * Automatically reconnects with exponential backoff.
 */
export function subscribeSSE(type: SSEType): SSESubscription {
  const url = type === 'reality'
    ? '/api/v1/reality/stream'
    : '/api/v1/events/stream';

  let eventSource: EventSource | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempt = 0;
  let closed = false;

  function connect() {
    if (closed) return;

    eventSource = new EventSource(url, { withCredentials: true });

    eventSource.onmessage = (event) => {
      attempt = 0; // Reset backoff on successful message
      try {
        const data = JSON.parse(event.data);

        if (type === 'reality') {
          bus.emit({ type: 'reality:snapshot', data });
        } else {
          // events stream: { created: [...], updated: [...] }
          if (data.created?.length) {
            bus.emit({ type: 'realtime:created', items: data.created });
          }
          if (data.updated?.length) {
            bus.emit({ type: 'realtime:updated', items: data.updated });
          }
        }
      } catch {
        // Malformed JSON — skip
      }
    };

    eventSource.onerror = () => {
      eventSource?.close();
      eventSource = null;

      if (!closed) {
        const delay = Math.min(
          RECONNECT_BASE_MS * Math.pow(2, attempt),
          RECONNECT_MAX_MS,
        );
        attempt++;
        reconnectTimer = setTimeout(connect, delay);
      }
    };
  }

  connect();

  return {
    close: () => {
      closed = true;
      eventSource?.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    },
  };
}
