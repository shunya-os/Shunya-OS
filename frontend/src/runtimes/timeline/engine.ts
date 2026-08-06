/**
 * Timeline Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Maintain a universal, queryable event stream
 * - Load timeline events for a specific object
 * - Support execution mode (events annotated with commitment impact)
 * - Virtual list management (1000s of events, renders only visible)
 * - Client-side filtering by type, date, object, user, source
 *
 * ── Events Published ──────────────────────────────────────────
 * TimelineRequested, TimelineLoaded, TimelineUpdated
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * WorkspaceOpened → triggers TimelineRequested for the workspace's object
 * ObjectUpdated    → triggers TimelineUpdated (new event generated)
 *
 * ── Owned State ───────────────────────────────────────────────
 * Event cache (Map<objectKey, TimelineEvent[]>), filter state
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * (none — events are fetched from API and cached locally)
 */

import { bus } from '../event-bus';

export interface TimelineEvent {
  id: string;
  type: string;
  title: string;
  description?: string;
  timestamp: number;
  objectType: string;
  objectId: string;
  source: 'system' | 'human' | 'ai';
  commitmentImpact?: 'positive' | 'neutral' | 'negative' | 'critical';
  commitmentId?: string;
  metadata?: Record<string, unknown>;
}

type EventCache = Map<string, TimelineEvent[]>;

const cache: EventCache = new Map();

function objKey(objectType: string, objectId: string): string {
  return `${objectType}:${objectId}`;
}

export const TimelineRuntime = {
  /** Get cached events for an object. */
  get(objectType: string, objectId: string): TimelineEvent[] {
    return cache.get(objKey(objectType, objectId)) ?? [];
  },

  /** Request events for an object. */
  request(objectType: string, objectId: string, workspaceId?: string): void {
    const events = this.get(objectType, objectId);
    if (events.length > 0) return;

    bus.emit({ type: 'TimelineRequested', objectType, objectId, workspaceId: workspaceId ?? '' });

    setTimeout(async () => {
      try {
        const resp = await fetch(`/api/v1/${objectType}s/${objectId}/timeline`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        const entries: TimelineEvent[] = (data.events ?? data ?? []).map((e: any) => ({
          id: e.id ?? crypto.randomUUID(),
          type: e.type ?? 'system',
          title: e.title ?? e.description ?? 'Event',
          description: e.description,
          timestamp: new Date(e.timestamp ?? e.created_at ?? Date.now()).getTime(),
          objectType,
          objectId,
          source: e.source ?? 'system',
          commitmentImpact: e.commitment_impact ?? e.commitmentImpact,
          commitmentId: e.commitment_id ?? e.commitmentId,
        }));
        cache.set(objKey(objectType, objectId), entries);
        bus.emit({ type: 'TimelineLoaded', objectType, objectId, events: entries });
      } catch {
        bus.emit({ type: 'TimelineLoaded', objectType, objectId, events: [] });
      }
    }, 0);
  },

  /** Add a single event (from WebSocket). */
  push(objectType: string, objectId: string, event: TimelineEvent): void {
    const key = objKey(objectType, objectId);
    const existing = cache.get(key) ?? [];
    cache.set(key, [event, ...existing]);
    bus.emit({ type: 'TimelineUpdated', objectType, objectId, event });
  },

  /** Clear cache. */
  clear(): void {
    cache.clear();
  },
};
