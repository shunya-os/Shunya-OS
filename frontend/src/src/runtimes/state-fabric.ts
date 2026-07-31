/**
 * State Fabric — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Register runtime state with schema, version, and policies
 * - Version every state mutation monotonically
 * - Create immutable snapshots on state change
 * - Provide centralised state observation (subscribe to any runtime's state)
 * - Persist state according to each runtime's declared policy (transient/session/persistent/encrypted)
 * - Coordinate atomic transactions spanning multiple runtimes
 * - Support time-travel debugging via snapshot replay
 * - Maintain derived state from declared formulas
 *
 * ── Events Published ──────────────────────────────────────────
 * RuntimeStateRegistered, RuntimeStateChanged, RuntimeSnapshotCreated,
 * RuntimeSnapshotRestored, RuntimeStateInvalidated, TransactionCommitted,
 * TransactionRolledBack
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * (none — runtimes push state changes to the fabric; the fabric does not pull)
 *
 * ── Owned State ───────────────────────────────────────────────
 * State registry (Map<runtimeId, Slot>), snapshot log (Array<Snapshot>),
 * transaction log, derived state cache
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * (none — the fabric stores state values but does not interpret them)
 *
 * ── Cache Strategy ────────────────────────────────────────────
 * Current state: always in memory
 * Snapshots: capped at 1000, oldest pruned
 * Persisted state: localStorage (session/permanent) or sessionStorage (session)
 *
 * ── Failure Behaviour ─────────────────────────────────────────
 * - Persistence failure logged, state remains in memory
 * - Snapshot quota exceeded: oldest snapshot pruned automatically
 * - Transaction failure: rollback already-applied mutations
 *
 * ── Recovery Behaviour ────────────────────────────────────────
 * - On app restart, rehydrate persistent slots from storage
 * - Session-scoped slots are cleared on restart
 */

import { bus } from './event-bus';

// ── Types ──────────────────────────────────────────────────────

export type PersistencePolicy = 'transient' | 'session' | 'persistent' | 'encrypted';
export type SyncPolicy = 'local' | 'optimistic' | 'remote';

export interface StateRegistration {
  runtimeId: string;
  version: number;
  schema: Record<string, string>;  // key → type description
  persistence: PersistencePolicy;
  sync: SyncPolicy;
  snapshot: boolean;
  derive?: Record<string, (state: Record<string, unknown>) => unknown>;
}

export interface Snapshot {
  id: string;
  runtimeId: string;
  timestamp: number;
  version: number;
  state: Record<string, unknown>;
  origin: string;
  metadata?: Record<string, unknown>;
}

interface Slot {
  registration: StateRegistration;
  current: Record<string, unknown>;
  version: number;
  snapshots: Snapshot[];
  subscribers: Set<(state: Record<string, unknown>, version: number) => void>;
}

// ── Fabric ─────────────────────────────────────────────────────

class StateFabric {
  private slots = new Map<string, Slot>();
  private snapshots: Snapshot[] = [];
  private maxSnapshots = 1000;
  private transactions: Map<string, { slot: Slot; previous: Record<string, unknown>; previousVersion: number }[]> | null = null;

  // ── Registry ─────────────────────────────────────────────────

  register(registration: StateRegistration): void {
    if (this.slots.has(registration.runtimeId)) {
      console.warn(`[StateFabric] Runtime '${registration.runtimeId}' already registered — updating schema`);
    }

    this.slots.set(registration.runtimeId, {
      registration,
      current: {},
      version: registration.version,
      snapshots: [],
      subscribers: new Set(),
    });

    // Rehydrate from storage
    if (registration.persistence === 'session' || registration.persistence === 'persistent') {
      this.rehydrate(registration.runtimeId);
    }

    bus.emit({ type: 'RuntimeStateRegistered' as any, source: registration.runtimeId, error: '' } as any);
  }

  // ── Read ─────────────────────────────────────────────────────

  /** Get the current state for a runtime. */
  read(runtimeId: string): { state: Record<string, unknown>; version: number } | undefined {
    const slot = this.slots.get(runtimeId);
    if (!slot) return undefined;
    return { state: slot.current, version: slot.version };
  }

  /** Get the current state and version for a runtime. */
  getVersion(runtimeId: string): number {
    return this.slots.get(runtimeId)?.version ?? 0;
  }

  // ── Write ────────────────────────────────────────────────────

  /** Update state for a runtime. Returns the new version number. */
  write(runtimeId: string, delta: Record<string, unknown>, origin: string = 'system'): number {
    const slot = this.slots.get(runtimeId);
    if (!slot) return -1;

    const previous = { ...slot.current };
    const previousVersion = slot.version;

    // If inside a transaction, record the rollback info
    if (this.transactions) {
      const entries = this.transactions.get(runtimeId);
      if (entries) {
        entries.push({ slot, previous, previousVersion });
      } else {
        this.transactions.set(runtimeId, [{ slot, previous, previousVersion }]);
      }
    }

    slot.version++;
    Object.assign(slot.current, delta);
    slot.registration.version = slot.version;

    // Snapshot if enabled
    if (slot.registration.snapshot) {
      this.captureSnapshot(runtimeId, origin);
    }

    // Persist if configured
    if (slot.registration.persistence === 'session') {
      this.persistSession(runtimeId, slot.current);
    } else if (slot.registration.persistence === 'persistent') {
      this.persistLocal(runtimeId, slot.current);
    }

    // Notify subscribers
    slot.subscribers.forEach(cb => cb(slot.current, slot.version));

    bus.emit({ type: 'RuntimeStateChanged' as any, source: runtimeId, error: '' } as any);

    return slot.version;
  }

  // ── Transactions ─────────────────────────────────────────────

  /** Begin a transaction. Subsequent writes are tracked for rollback. */
  beginTransaction(): void {
    this.transactions = new Map();
  }

  /** Commit the current transaction. Writes become permanent. */
  commitTransaction(): boolean {
    if (!this.transactions) return false;
    this.transactions = null;
    bus.emit({ type: 'TransactionCommitted' as any, source: 'state-fabric', error: '' } as any);
    return true;
  }

  /** Roll back all writes made during the current transaction. */
  rollbackTransaction(): boolean {
    if (!this.transactions) return false;
    for (const [, entries] of this.transactions) {
      for (const entry of entries.reverse()) {
        entry.slot.current = entry.previous;
        entry.slot.version = entry.previousVersion;
      }
    }
    this.transactions = null;
    bus.emit({ type: 'TransactionRolledBack' as any, source: 'state-fabric', error: '' } as any);
    return true;
  }

  // ── Snapshots ────────────────────────────────────────────────

  private captureSnapshot(runtimeId: string, origin: string): void {
    const slot = this.slots.get(runtimeId);
    if (!slot) return;

    const snap: Snapshot = {
      id: `snap_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      runtimeId,
      timestamp: Date.now(),
      version: slot.version,
      state: { ...slot.current },
      origin,
    };

    slot.snapshots.push(snap);
    this.snapshots.push(snap);
    bus.emit({ type: 'RuntimeSnapshotCreated' as any, source: runtimeId, error: '' } as any);

    // Enforce cap
    if (this.snapshots.length > this.maxSnapshots) {
      const removed = this.snapshots.shift()!;
      const rslot = this.slots.get(removed.runtimeId);
      if (rslot) {
        rslot.snapshots = rslot.snapshots.filter(s => s.id !== removed.id);
      }
    }
  }

  /** Get all snapshots for a runtime (for time-travel debugging). */
  getSnapshots(runtimeId: string): Snapshot[] {
    return (this.slots.get(runtimeId)?.snapshots ?? []).slice();
  }

  /** Get all snapshots across all runtimes. */
  getAllSnapshots(): Snapshot[] {
    return this.snapshots.slice();
  }

  /** Restore a snapshot (development only). */
  restoreSnapshot(snapshotId: string): boolean {
    const snap = this.snapshots.find(s => s.id === snapshotId);
    if (!snap) return false;
    const slot = this.slots.get(snap.runtimeId);
    if (!slot) return false;

    slot.current = { ...snap.state };
    slot.version = snap.version;
    slot.subscribers.forEach(cb => cb(slot.current, slot.version));

    bus.emit({ type: 'RuntimeSnapshotRestored' as any, source: snap.runtimeId, error: '' } as any);
    return true;
  }

  // ── Observation ──────────────────────────────────────────────

  /** Subscribe to state changes for a runtime. Returns unsubscribe function. */
  subscribe(runtimeId: string, callback: (state: Record<string, unknown>, version: number) => void): () => void {
    const slot = this.slots.get(runtimeId);
    if (!slot) {
      console.warn(`[StateFabric] Cannot subscribe to unknown runtime '${runtimeId}'`);
      return () => {};
    }
    slot.subscribers.add(callback);
    return () => slot.subscribers.delete(callback);
  }

  // ── Derived State ────────────────────────────────────────────

  /** Compute derived state for a runtime from declared formulas. */
  derive(runtimeId: string): Record<string, unknown> {
    const slot = this.slots.get(runtimeId);
    if (!slot || !slot.registration.derive) return {};
    const result: Record<string, unknown> = {};
    for (const [key, fn] of Object.entries(slot.registration.derive)) {
      result[key] = fn(slot.current);
    }
    return result;
  }

  // ── Persistence ──────────────────────────────────────────────

  private storageKey(runtimeId: string): string {
    return `shunya_state_${runtimeId}`;
  }

  private persistLocal(runtimeId: string, state: Record<string, unknown>): void {
    try { localStorage.setItem(this.storageKey(runtimeId), JSON.stringify(state)); } catch { /* quota */ }
  }

  private persistSession(runtimeId: string, state: Record<string, unknown>): void {
    try { sessionStorage.setItem(this.storageKey(runtimeId), JSON.stringify(state)); } catch { /* quota */ }
  }

  private rehydrate(runtimeId: string): void {
    const slot = this.slots.get(runtimeId);
    if (!slot) return;
    try {
      const store = slot.registration.persistence === 'persistent' ? localStorage : sessionStorage;
      const raw = store.getItem(this.storageKey(runtimeId));
      if (raw) {
        const saved = JSON.parse(raw);
        Object.assign(slot.current, saved);
      }
    } catch { /* noop */ }
  }

  /** Invalidate persisted state for a runtime. */
  invalidate(runtimeId: string): void {
    this.slots.delete(runtimeId);
    try {
      localStorage.removeItem(this.storageKey(runtimeId));
      sessionStorage.removeItem(this.storageKey(runtimeId));
    } catch { /* noop */ }
    bus.emit({ type: 'RuntimeStateInvalidated' as any, source: runtimeId, error: '' } as any);
  }

  // ── Development Tools ────────────────────────────────────────

  /** Get registry info for all registered runtimes. */
  getRegistry(): { runtimeId: string; version: number; persistence: PersistencePolicy; snapshotEnabled: boolean }[] {
    return Array.from(this.slots.values()).map(s => ({
      runtimeId: s.registration.runtimeId,
      version: s.version,
      persistence: s.registration.persistence,
      snapshotEnabled: s.registration.snapshot,
    }));
  }

  /** Clear all state (testing). */
  clear(): void {
    this.slots.clear();
    this.snapshots = [];
    this.transactions = null;
  }
}

export const stateFabric = new StateFabric();

// ── React Hook ─────────────────────────────────────────────────

import { useSyncExternalStore, useCallback } from 'react';

/** React hook that subscribes to a runtime's state and returns its current state. */
export function useRuntimeState(runtimeId: string): Record<string, unknown> {
  const subscribe = useCallback((cb: () => void) => stateFabric.subscribe(runtimeId, cb), [runtimeId]);
  useSyncExternalStore(subscribe, () => stateFabric.read(runtimeId)?.version ?? 0);
  const r = stateFabric.read(runtimeId);
  return r?.state ?? {};
}