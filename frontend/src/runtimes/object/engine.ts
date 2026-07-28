/**
 * Object Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Fetch, cache, normalise, and subscribe to business objects
 * - Load objects in phases: identity frame → summary → data → intelligence
 * - Maintain a local cache with TTL-based invalidation
 * - Stream real-time updates via WebSocket deltas
 * - Expose a relationship graph of connected objects
 *
 * ── Events Published ──────────────────────────────────────────
 * ObjectRequested, ObjectLoaded, ObjectUpdated, ObjectCached, ObjectError
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * WorkspaceOpened → triggers ObjectRequested for the workspace's primary object
 *
 * ── Owned State ───────────────────────────────────────────────
 * Object cache (Map<type+id, ObjectEntry>), loading flags, error states
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * WorkspaceRuntime.activeId (to know which object to prioritise)
 */

import { bus } from '../event-bus';

export interface ObjectEntry {
  id: string;
  type: string;
  identity: Record<string, unknown>;
  summary?: string;
  data?: Record<string, unknown>;
  ai?: Record<string, unknown>;
  loadedAt: number;
  ttl: number;
}

type CacheMap = Map<string, ObjectEntry>;

const cache: CacheMap = new Map();

function key(type: string, id: string): string {
  return `${type}:${id}`;
}

function isExpired(entry: ObjectEntry): boolean {
  return Date.now() - entry.loadedAt > entry.ttl;
}

export const ObjectRuntime = {
  /** Get an object from cache or trigger a fetch. Returns cached version immediately. */
  get(type: string, id: string): ObjectEntry | null {
    const k = key(type, id);
    const entry = cache.get(k);
    if (entry && !isExpired(entry)) return entry;
    if (entry) cache.delete(k); // expired
    return null;
  },

  /** Request an object — returns cached if fresh, otherwise triggers load. */
  request(type: string, id: string, workspaceId?: string): ObjectEntry | null {
    const cached = this.get(type, id);
    if (cached) return cached;

    bus.emit({ type: 'ObjectRequested', objectType: type, objectId: id, workspaceId: workspaceId ?? '' });

    // Simulate async load (replace with actual API call)
    setTimeout(async () => {
      try {
        const resp = await fetch(`/api/v1/${type}s/${id}`);
        const data = await resp.json();
        const entry: ObjectEntry = {
          id, type,
          identity: { name: data.name ?? data.title ?? id, status: data.status ?? 'active' },
          data,
          loadedAt: Date.now(),
          ttl: 5 * 60 * 1000, // 5 minutes
        };
        cache.set(key(type, id), entry);
        bus.emit({ type: 'ObjectLoaded', objectType: type, objectId: id, data: entry });
      } catch (err) {
        bus.emit({ type: 'ObjectError', objectType: type, objectId: id, error: String(err) });
      }
    }, 0);

    return null;
  },

  /** Update cached data with a delta (from WebSocket). */
  applyDelta(type: string, id: string, delta: Record<string, unknown>): void {
    const k = key(type, id);
    const entry = cache.get(k);
    if (!entry) return;
    entry.data = { ...entry.data, ...delta };
    bus.emit({ type: 'ObjectUpdated', objectType: type, objectId: id, delta });
  },

  /** Invalidate cache for an object. */
  invalidate(type: string, id: string): void {
    cache.delete(key(type, id));
  },

  /** Clear entire cache. */
  clear(): void { cache.clear(); },

  /** Get all cached keys (for debugging). */
  keys(): string[] { return Array.from(cache.keys()); },
};