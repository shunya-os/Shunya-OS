// SHUNYA Frontend — Event Bus
// Lightweight pub/sub for cross-module communication.

type EventHandler = (payload?: unknown) => void;

class EventBus {
  private handlers = new Map<string, Set<EventHandler>>();
  private wildcardHandlers = new Set<EventHandler>();

  on(event: string, handler: EventHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler);
  }

  onAny(handler: EventHandler): () => void {
    this.wildcardHandlers.add(handler);
    return () => this.wildcardHandlers.delete(handler);
  }

  emit(event: string, payload?: unknown): void {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.forEach((h) => h(payload));
    }
    this.wildcardHandlers.forEach((h) => h({ event, payload }));
  }

  off(event: string, handler: EventHandler): void {
    this.handlers.get(event)?.delete(handler);
  }

  clear(): void {
    this.handlers.clear();
    this.wildcardHandlers.clear();
  }

  listenerCount(event: string): number {
    return this.handlers.get(event)?.size ?? 0;
  }
}

export const eventBus = new EventBus();
export type { EventHandler };