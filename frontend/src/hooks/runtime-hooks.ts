/**
 * Runtime Hooks — React bridge for the orchestrator's runtime discovery.
 *
 * Components request runtimes through these hooks instead of importing them directly.
 * This enables testing, replacement, and future modularisation.
 */

import { useSyncExternalStore } from 'react';
import { orchestrator, type RuntimeInstance } from '../runtimes/orchestrator';

function subscribeToOrchestrator(cb: () => void): () => void {
  // Runtimes rarely change after first render; poll is acceptable here.
  const interval = setInterval(cb, 5000);
  return () => clearInterval(interval);
}

function getSnapshot(): number {
  return orchestrator.getAll().length;
}

/** Get a runtime by ID. Returns undefined if not yet registered/started. */
export function useRuntime(id: string): RuntimeInstance | undefined {
  useSyncExternalStore(subscribeToOrchestrator, getSnapshot);
  return orchestrator.get(id);
}

/** Get all registered runtimes with their current status. */
export function useRuntimes(): RuntimeInstance[] {
  useSyncExternalStore(subscribeToOrchestrator, getSnapshot);
  return orchestrator.getAll();
}

/** Check if all runtimes are ready. */
export function useRuntimesReady(): boolean {
  const all = useRuntimes();
  return all.length > 0 && all.every((r) => r.status === 'ready');
}

/** Aggregate health summary. */
export function useRuntimeHealth(): { total: number; ready: number; failed: number } {
  useSyncExternalStore(subscribeToOrchestrator, getSnapshot);
  try {
    const h = orchestrator.getAggregatedHealth();
    if (!h) return { total: 0, ready: 0, failed: 0 };
    return { total: h.total ?? 0, ready: h.ready ?? 0, failed: h.failed ?? 0 };
  } catch {
    return { total: 0, ready: 0, failed: 0 };
  }
}
