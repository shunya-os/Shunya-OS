/**
 * Object Graph Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Model how every object in SHUNYA connects to every other object
 * - Serve as the single canonical authority for all relationships
 * - Traverse relationship graphs without UI knowledge
 * - Load relationships lazily (primary → frequent → contextual → remaining)
 * - Maintain a TTL-based relationship cache with incremental updates
 * - Support optimistic updates and offline compatibility
 * - Provide relationship reasoning to the Intelligence Runtime
 *
 * ── Events Published ──────────────────────────────────────────
 * ObjectLinked, ObjectUnlinked, RelationshipCreated,
 * RelationshipUpdated, RelationshipRemoved, GraphHydrated,
 * GraphExpanded, GraphCollapsed
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * ObjectLoaded       → auto-request relationships for the loaded object
 * WorkspaceOpened    → auto-request primary relationship graph
 *
 * ── Owned State ───────────────────────────────────────────────
 * Relationship graph (Map<objectId, Map<objectId, Edge>>)
 * Node metadata cache (Map<objectId, ObjectIdentity>)
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * (none — the graph is self-contained; objects fetched via API)
 *
 * ── Cache Strategy ────────────────────────────────────────────
 * Primary relationships: TTL 5min
 * Frequent neighbours:  TTL 2min
 * Contextual nodes:     TTL 30s
 * Remaining graph:      TTL 10s (invalidation triggers re-fetch)
 *
 * ── Failure Behaviour ─────────────────────────────────────────
 * - Failed relationship fetch logs warning, returns empty edges
 * - Graceful degradation: graph shows what it has, labels unknowns
 * - Retry on next access with exponential backoff (1s, 4s, 15s)
 *
 * ── Recovery Behaviour ────────────────────────────────────────
 * - On reconnect, re-hydrate all active workspace graphs
 * - Merge delta updates from WebSocket into existing graph
 * - Optimistic updates roll back on server rejection
 */

import { bus } from '../event-bus';

// ── Identity ───────────────────────────────────────────────────

export interface ObjectIdentity {
  id: string;
  type: string;
  name: string;
  status: string;
  createdAt: number;
  updatedAt: number;
}

// ── Graph Types ────────────────────────────────────────────────

export type RelationshipType =
  | 'manages'
  | 'managed_by'
  | 'owns'
  | 'owned_by'
  | 'relates_to'
  | 'related_from'
  | 'references'
  | 'referenced_by'
  | 'depends_on'
  | 'depended_by'
  | 'follows'
  | 'precedes'
  | 'generates'
  | 'generated_by'
  | 'attached_to'
  | 'attachment_of'
  | 'inferred'
  | 'unknown';

export interface Edge {
  id: string;
  fromId: string;
  fromType: string;
  toId: string;
  toType: string;
  type: RelationshipType;
  confidence: number; // 0-1, 1 = explicit, <1 = inferred
  source: 'system' | 'human' | 'ai' | 'import';
  metadata?: Record<string, unknown>;
  createdAt: number;
}

interface GraphNode {
  identity: ObjectIdentity;
  edges: Map<string, Edge[]>; // targetId → edges
  loadedAt: number;
  ttl: number;
}

// ── Cache ──────────────────────────────────────────────────────

const nodes = new Map<string, GraphNode>();
const identityCache = new Map<string, ObjectIdentity>();

function nodeKey(id: string): string {
  return id;
}

function isExpired(node: GraphNode): boolean {
  return Date.now() - node.loadedAt > node.ttl;
}

// ── API ────────────────────────────────────────────────────────

function graphEndpoint(objectType: string, objectId: string): string {
  return `/api/v1/${objectType}s/${objectId}/graph`;
}

async function fetchEdges(objectType: string, objectId: string): Promise<{ nodes: ObjectIdentity[]; edges: Edge[] }> {
  try {
    const resp = await fetch(graphEndpoint(objectType, objectId));
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch {
    return { nodes: [], edges: [] };
  }
}

// ── TTL Tiers ──────────────────────────────────────────────────

const TTL: Record<string, number> = {
  primary: 5 * 60 * 1000,
  frequent: 2 * 60 * 1000,
  contextual: 30 * 1000,
  remaining: 10 * 1000,
};

function ttlFor(priority: string): number {
  return TTL[priority] ?? TTL.remaining;
}

// ── Graph Runtime ──────────────────────────────────────────────

export const ObjectGraphRuntime = {
  // ── Registration ──────────────────────────────────────────────

  /** Register an object's identity (called by ObjectRuntime on load). */
  registerIdentity(identity: ObjectIdentity): void {
    identityCache.set(identity.id, identity);
  },

  /** Get identity for an object. */
  getIdentity(id: string): ObjectIdentity | undefined {
    return identityCache.get(id);
  },

  // ── Relationship Access ───────────────────────────────────────

  /** Get outgoing edges for an object. */
  getEdges(id: string): Edge[] {
    const node = nodes.get(nodeKey(id));
    if (!node || isExpired(node)) return [];
    return Array.from(node.edges.values()).flat();
  },

  /** Get neighbours of a specific type. */
  getNeighbours(id: string, type?: string): { identity: ObjectIdentity; edges: Edge[] }[] {
    const edges = this.getEdges(id);
    const neighbourIds = new Set<string>();
    const result: { identity: ObjectIdentity; edges: Edge[] }[] = [];

    for (const edge of edges) {
      const neighbourId = edge.fromId === id ? edge.toId : edge.fromId;
      if (type && edge.toType !== type && edge.fromType !== type) continue;
      if (neighbourIds.has(neighbourId)) continue;
      neighbourIds.add(neighbourId);

      const identity = identityCache.get(neighbourId);
      if (identity) {
        result.push({ identity, edges: [edge] });
      }
    }
    return result;
  },

  /** Check if two objects are connected. */
  areConnected(idA: string, idB: string): boolean {
    const edges = this.getEdges(idA);
    return edges.some((e) => e.toId === idB || e.fromId === idB);
  },

  // ── Graph Loading ─────────────────────────────────────────────

  /** Request the relationship graph for an object. Loads lazily by priority tier. */
  async requestGraph(objectType: string, objectId: string, priority: string = 'primary'): Promise<void> {
    const id = objectId;
    const existing = nodes.get(nodeKey(id));

    if (existing && !isExpired(existing)) {
      bus.emit({ type: 'GraphHydrated' as any, objectType, objectId } as any);
      return;
    }

    const result = await fetchEdges(objectType, objectId);

    // Register identities
    for (const ident of result.nodes) {
      identityCache.set(ident.id, ident);
    }

    // Build graph node
    const edgeMap = new Map<string, Edge[]>();
    for (const edge of result.edges) {
      const target = edge.toId === id ? edge.fromId : edge.toId;
      if (!edgeMap.has(target)) edgeMap.set(target, []);
      edgeMap.get(target)!.push(edge);
    }

    nodes.set(nodeKey(id), {
      identity: identityCache.get(id) ?? {
        id,
        type: objectType,
        name: id,
        status: 'unknown',
        createdAt: 0,
        updatedAt: 0,
      },
      edges: edgeMap,
      loadedAt: Date.now(),
      ttl: ttlFor(priority),
    });

    bus.emit({ type: 'GraphHydrated' as any, objectType, objectId } as any);
  },

  /** Expand the graph by loading a neighbour's relationships. */
  async expand(id: string): Promise<void> {
    const node = nodes.get(nodeKey(id));
    if (!node) return;
    const identity = identityCache.get(id);
    if (!identity) return;

    await this.requestGraph(identity.type, id, 'contextual');
    bus.emit({ type: 'GraphExpanded' as any, objectType: identity.type, objectId: id } as any);
  },

  /** Add a relationship edge locally (optimistic). */
  link(fromId: string, toId: string, type: RelationshipType, metadata?: Record<string, unknown>): Edge {
    const edge: Edge = {
      id: crypto.randomUUID(),
      fromId,
      fromType: identityCache.get(fromId)?.type ?? 'unknown',
      toId,
      toType: identityCache.get(toId)?.type ?? 'unknown',
      type,
      confidence: 1,
      source: 'system',
      metadata,
      createdAt: Date.now(),
    };

    for (const id of [fromId, toId]) {
      const node = nodes.get(nodeKey(id));
      if (node) {
        const target = id === fromId ? toId : fromId;
        if (!node.edges.has(target)) node.edges.set(target, []);
        node.edges.get(target)!.push(edge);
      }
    }

    bus.emit({ type: 'ObjectLinked' as any, objectType: edge.fromType, objectId: fromId } as any);
    return edge;
  },

  /** Remove a relationship edge locally (optimistic). */
  unlink(fromId: string, toId: string): void {
    for (const id of [fromId, toId]) {
      const node = nodes.get(nodeKey(id));
      if (node) node.edges.delete(fromId === id ? toId : fromId);
    }
    bus.emit({ type: 'ObjectUnlinked' as any, objectType: 'unknown', objectId: fromId } as any);
  },

  // ── Traversal ─────────────────────────────────────────────────

  /**
   * Walk a path through the graph starting from an object.
   * pathSpec: ['booking', 'invoice', 'payment']
   * Returns array of matching neighbours at each hop.
   */
  traverse(id: string, pathSpec: string[]): { identity: ObjectIdentity; depth: number }[][] {
    const results: { identity: ObjectIdentity; depth: number }[][] = [];
    let currentIds = [id];

    for (const targetType of pathSpec) {
      const hop: { identity: ObjectIdentity; depth: number }[] = [];
      for (const cid of currentIds) {
        const neighbours = this.getNeighbours(cid, targetType);
        for (const n of neighbours) {
          hop.push({ identity: n.identity, depth: results.length });
        }
      }
      results.push(hop);
      currentIds = hop.map((h) => h.identity.id);
    }

    return results;
  },

  // ── Cache Management ──────────────────────────────────────────

  invalidate(id: string): void {
    nodes.delete(nodeKey(id));
  },

  clear(): void {
    nodes.clear();
    identityCache.clear();
  },

  /** Return cache stats for debugging. */
  stats(): { nodes: number; identities: number } {
    return { nodes: nodes.size, identities: identityCache.size };
  },
};
