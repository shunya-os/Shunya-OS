/**
 * Centralised Event Bus — Runtime communication via typed events.
 *
 * No runtime accesses another runtime's internal state directly.
 * Cross-runtime communication occurs only through explicit events.
 */

export type RuntimeEvent =
  // ── Workspace Lifecycle ──────────────────────────────────
  | { type: 'WorkspaceOpened'; workspaceId: string; objectType?: string; objectId?: string }
  | { type: 'WorkspaceHydrated'; workspaceId: string }
  | { type: 'WorkspaceSuspended'; workspaceId: string }
  | { type: 'WorkspaceResumed'; workspaceId: string }
  | { type: 'WorkspaceClosing'; workspaceId: string }
  | { type: 'WorkspaceDestroyed'; workspaceId: string }
  | { type: 'WorkspaceChanged'; workspaceId: string; from: string; to: string }
  | { type: 'WorkspaceError'; workspaceId: string; error: string }
  // ── Object Lifecycle ─────────────────────────────────────
  | { type: 'ObjectRequested'; objectType: string; objectId: string; workspaceId: string }
  | { type: 'ObjectLoaded'; objectType: string; objectId: string; data: unknown }
  | { type: 'ObjectUpdated'; objectType: string; objectId: string; delta: Record<string, unknown> }
  | { type: 'ObjectCached'; objectType: string; objectId: string }
  | { type: 'ObjectError'; objectType: string; objectId: string; error: string }
  | { type: 'ObjectSaveRequested'; objectType: string; objectId: string; workspaceId: string }
  | { type: 'ObjectSaved'; objectType: string; objectId: string; workspaceId: string }
  | { type: 'ObjectSaveFailed'; objectType: string; objectId: string; workspaceId: string; error: string }
  | { type: 'ObjectDirtyChanged'; objectType: string; objectId: string; dirty: boolean }
  | { type: 'ObjectClosed'; objectType: string; objectId: string; workspaceId: string }
  // ── Timeline Lifecycle ───────────────────────────────────
  | { type: 'TimelineRequested'; objectType: string; objectId: string; workspaceId: string }
  | { type: 'TimelineLoaded'; objectType: string; objectId: string; events: unknown[] }
  | { type: 'TimelineUpdated'; objectType: string; objectId: string; event: unknown }
  // ── Intelligence Lifecycle ───────────────────────────────
  | { type: 'IntelligenceRequested'; objectType: string; objectId: string; workspaceId: string }
  | { type: 'IntelligenceLoaded'; objectType: string; objectId: string; insights: unknown[] }
  | { type: 'IntelligenceError'; objectType: string; objectId: string; error: string }
  // ── Commitment Lifecycle ─────────────────────────────────
  | { type: 'CommitmentCreated'; commitmentId: string }
  | { type: 'CommitmentStateChanged'; commitmentId: string; from: string; to: string }
  | { type: 'CommitmentCompleted'; commitmentId: string }
  // ── Navigation ───────────────────────────────────────────
  | { type: 'NavigationChanged'; workspaceId: string; url: string }
  // ── System ───────────────────────────────────────────────
  | { type: 'SystemError'; source: string; error: string }
  // ── API Layer Events (migrated from api/event-bus.ts) ──
  | { type: 'ai:insight'; payload: { title: string; description: string; type: string; confidence: number; evidence: string; source: string; action_label: string | null; action_payload: unknown } }
  | { type: 'data:refresh'; url: string }
  | { type: 'realtime:created'; items: Array<Record<string, unknown>> }
  | { type: 'realtime:updated'; items: Array<Record<string, unknown>> }
  | { type: 'notification'; kind: 'success' | 'error' | 'info'; message: string }
  // ── SSE Runtime Events (Continuous Reality transport) ──
  | { type: 'reality:snapshot'; data: Record<string, unknown> }
  // ── Individual canonical events from the SSE stream ──
  | { type: 'reality:event'; data: Record<string, unknown> }
  | { type: 'reality:error'; message: string }
  | { type: 'reality:disconnected' }
  | { type: 'reality:reconnected' };

type EventHandler = (event: RuntimeEvent) => void;

class EventBus {
  private handlers = new Map<string, Set<EventHandler>>();
  private wildcards = new Set<EventHandler>();

  /** Subscribe to a specific event type. */
  on(type: RuntimeEvent['type'], handler: EventHandler): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set());
    this.handlers.get(type)!.add(handler);
    return () => this.handlers.get(type)?.delete(handler);
  }

  /** Subscribe to all events (for logging, debugging). */
  onAny(handler: EventHandler): () => void {
    this.wildcards.add(handler);
    return () => this.wildcards.delete(handler);
  }

  /** Publish an event. Synchronous — no microtask deferral. */
  emit(event: RuntimeEvent): void {
    const specific = this.handlers.get(event.type);
    if (specific) specific.forEach((h) => h(event));
    this.wildcards.forEach((h) => h(event));
  }

  /** Clear all subscriptions (testing). */
  clear(): void {
    this.handlers.clear();
    this.wildcards.clear();
  }
}

export const bus = new EventBus();
