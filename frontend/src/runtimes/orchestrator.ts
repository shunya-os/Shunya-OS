/**
 * Runtime Orchestrator — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Register all runtimes with their dependencies, health probes, and lifecycle handlers
 * - Resolve startup order automatically from dependency declarations
 * - Orchestrate init → ready lifecycle across all runtimes
 * - Isolate failures — a failed runtime does not crash unrelated runtimes
 * - Provide centralised recovery policies (retry, restart, dependency refresh, degraded)
 * - Serve as the single discovery point for all runtimes
 * - Aggregate health metrics and emit observability events
 *
 * ── Events Published ──────────────────────────────────────────
 * RuntimeRegistered, RuntimeReady, RuntimeFailed, RuntimeRecovered,
 * RuntimeStopped, RuntimeHealthChanged
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * (none — the orchestrator drives lifecycle; runtimes do not drive it)
 *
 * ── Owned State ───────────────────────────────────────────────
 * Runtime registry (Map<runtimeId, RuntimeRegistration>)
 * Runtime status map (Map<runtimeId, RuntimeStatus>)
 * Dependency graph (DAG adjacency list)
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * (none — runtimes report their own health; orchestrator does not probe internals)
 *
 * ── Cache Strategy ────────────────────────────────────────────
 * Runtime registry: permanent (once registered)
 * Runtime status: updated on every lifecycle transition
 *
 * ── Failure Behaviour ─────────────────────────────────────────
 * - Failed runtime is marked 'failed' and isolated
 * - All other runtimes continue operating
 * - Dependent runtimes receive a 'dependency_degraded' warning
 * - UI components that consume the failed runtime show degraded fallbacks
 *
 * ── Recovery Behaviour ────────────────────────────────────────
 * - Automatic: retry up to 3 times with 1s/4s/15s backoff
 * - On final failure: emit RuntimeFailed, leave stopped
 * - Manual: restart() can be called to retry recovery
 * - Dependency refresh: if a dependency restarts, dependent runtimes are notified
 */

import { bus } from './event-bus';

// ── Types ──────────────────────────────────────────────────────

export type RuntimeStatus = 'registered' | 'initialising' | 'ready' | 'suspended' | 'recovering' | 'failed' | 'stopped';

export interface RuntimeHealth {
  status: RuntimeStatus;
  startedAt: number | null;
  lastActivity: number | null;
  lastFailure: { time: number; error: string } | null;
  startupMs: number | null;
  retryCount: number;
}

export interface RuntimeRegistration {
  id: string;
  version: string;
  description: string;
  dependencies: string[];
  eventsPublished: string[];
  eventsSubscribed: string[];
  startup: () => Promise<void>;
  shutdown: () => Promise<void>;
  health: () => RuntimeHealth;
  recover?: () => Promise<void>;
}

export interface RuntimeInstance {
  registration: RuntimeRegistration;
  status: RuntimeStatus;
  health: RuntimeHealth;
}

// ── Orchestrator ───────────────────────────────────────────────

class Orchestrator {
  private registry = new Map<string, RuntimeInstance>();
  private dependencyGraph = new Map<string, string[]>();
  private startOrder: string[] = [];

  // ── Registration ─────────────────────────────────────────────

  register(registration: RuntimeRegistration): void {
    if (this.registry.has(registration.id)) {
      console.warn(`[Orchestrator] Runtime '${registration.id}' already registered — skipping`);
      return;
    }

    const instance: RuntimeInstance = {
      registration,
      status: 'registered',
      health: {
        status: 'registered',
        startedAt: null,
        lastActivity: null,
        lastFailure: null,
        startupMs: null,
        retryCount: 0,
      },
    };

    this.registry.set(registration.id, instance);
    this.dependencyGraph.set(registration.id, registration.dependencies);

    bus.emit({ type: 'RuntimeRegistered' as any, source: registration.id, error: '' } as any);
  }

  // ── Dependency Resolution ────────────────────────────────────

  /** Resolve startup order using topological sort (DFS-based). Returns ordered runtime IDs. */
  resolveStartOrder(): string[] {
    const visited = new Set<string>();
    const visiting = new Set<string>();
    const order: string[] = [];
    const graph = this.dependencyGraph;

    function visit(id: string): void {
      if (visited.has(id)) return;
      if (visiting.has(id)) {
        console.warn(`[Orchestrator] Circular dependency detected: ${id}`);
        return;
      }
      visiting.add(id);
      const deps = graph.get(id) ?? [];
      for (const dep of deps) {
        if (graph.has(dep)) visit(dep);
      }
      visiting.delete(id);
      visited.add(id);
      order.push(id);
    }

    for (const id of graph.keys()) visit(id);
    this.startOrder = order;
    return order;
  }

  /** Get registration order as a dependency chain description. */
  describeDependencyChain(): string {
    return this.startOrder.map((id, i) => `  ${i + 1}. ${id}`).join('\n');
  }

  // ── Lifecycle ────────────────────────────────────────────────

  /** Start all runtimes in dependency order. */
  async startAll(): Promise<{ succeeded: string[]; failed: string[] }> {
    const order = this.resolveStartOrder();
    const succeeded: string[] = [];
    const failed: string[] = [];
    const startTime = Date.now();

    for (const id of order) {
      const instance = this.registry.get(id);
      if (!instance) continue;

      instance.status = 'initialising';
      instance.health.status = 'initialising';
      instance.health.startedAt = Date.now();
      instance.health.retryCount = 0;

      try {
        const t0 = performance.now();
        await instance.registration.startup();
        const elapsed = Math.round(performance.now() - t0);
        instance.status = 'ready';
        instance.health.status = 'ready';
        instance.health.startupMs = elapsed;
        instance.health.lastActivity = Date.now();
        succeeded.push(id);

        bus.emit({ type: 'RuntimeReady' as any, source: id, error: '' } as any);
      } catch (err) {
        instance.status = 'failed';
        instance.health.status = 'failed';
        instance.health.lastFailure = { time: Date.now(), error: String(err) };
        failed.push(id);

        bus.emit({ type: 'RuntimeFailed' as any, source: id, error: String(err) } as any);
        console.error(`[Orchestrator] Runtime '${id}' failed to start:`, err);
      }
    }

    const totalMs = Date.now() - startTime;
    console.log(`[Orchestrator] Startup complete: ${succeeded.length} ready, ${failed.length} failed in ${totalMs}ms`);

    return { succeeded, failed };
  }

  /** Shut down all runtimes in reverse dependency order. */
  async shutdownAll(): Promise<void> {
    const order = [...this.startOrder].reverse();
    for (const id of order) {
      const instance = this.registry.get(id);
      if (!instance || instance.status === 'stopped') continue;
      try {
        await instance.registration.shutdown();
        instance.status = 'stopped';
        instance.health.status = 'stopped';
        bus.emit({ type: 'RuntimeStopped' as any, source: id, error: '' } as any);
      } catch (err) {
        console.error(`[Orchestrator] Runtime '${id}' shutdown error:`, err);
      }
    }
  }

  // ── Recovery ─────────────────────────────────────────────────

  /** Attempt to recover a single runtime. Returns true if recovery succeeded. */
  async recover(id: string): Promise<boolean> {
    const instance = this.registry.get(id);
    if (!instance || instance.status !== 'failed') return false;

    instance.status = 'recovering';
    instance.health.status = 'recovering';
    instance.health.retryCount++;

    const delays = [1000, 4000, 15000];
    const maxRetries = delays.length;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        if (attempt > 0) await new Promise((r) => setTimeout(r, delays[attempt - 1]));
        if (instance.registration.recover) {
          await instance.registration.recover();
        }
        await instance.registration.startup();
        instance.status = 'ready';
        instance.health.status = 'ready';
        instance.health.lastActivity = Date.now();
        instance.health.lastFailure = null;
        instance.health.retryCount = 0;
        bus.emit({ type: 'RuntimeRecovered' as any, source: id, error: '' } as any);
        return true;
      } catch (err) {
        console.warn(`[Orchestrator] Recovery attempt ${attempt + 1}/${maxRetries} failed for '${id}':`, err);
      }
    }

    instance.status = 'failed';
    instance.health.status = 'failed';
    bus.emit({ type: 'RuntimeFailed' as any, source: id, error: 'All recovery attempts exhausted' } as any);
    return false;
  }

  // ── Discovery ────────────────────────────────────────────────

  /** Get a runtime by ID. Returns instance or undefined. */
  get(id: string): RuntimeInstance | undefined {
    return this.registry.get(id);
  }

  /** Get all registered runtimes. */
  getAll(): RuntimeInstance[] {
    return Array.from(this.registry.values());
  }

  /** Update a runtime's health (called by the runtime itself or observers). */
  reportHealth(id: string, health: Partial<RuntimeHealth>): void {
    const instance = this.registry.get(id);
    if (!instance) return;
    Object.assign(instance.health, health);
    bus.emit({ type: 'RuntimeHealthChanged' as any, source: id, error: '' } as any);
  }

  /** Return runtime topology for dev console. */
  getTopology(): { id: string; status: RuntimeStatus; deps: string[]; eventsPublished: string[] }[] {
    return Array.from(this.registry.values()).map((inst) => ({
      id: inst.registration.id,
      status: inst.status,
      deps: inst.registration.dependencies,
      eventsPublished: inst.registration.eventsPublished,
    }));
  }

  /// Return aggregated health summary. */
  getAggregatedHealth(): { total: number; ready: number; failed: number; initialising: number; stopped: number } {
    const all = this.getAll();
    return {
      total: all.length,
      ready: all.filter((r) => r.status === 'ready').length,
      failed: all.filter((r) => r.status === 'failed').length,
      initialising: all.filter((r) => r.status === 'initialising').length,
      stopped: all.filter((r) => r.status === 'stopped').length,
    };
  }

  /// Clear all registrations (testing). */
  clear(): void {
    this.registry.clear();
    this.dependencyGraph.clear();
    this.startOrder = [];
  }
}

export const orchestrator = new Orchestrator();
