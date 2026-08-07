/**
 * Intelligence Runtime — Runtime contract.
 *
 * ── Responsibilities ──────────────────────────────────────────
 * - Provide AI insights and recommendations contextually
 * - Resolve current context (which object, workspace, user)
 * - Route AI requests to appropriate provider endpoints
 * - Score confidence (high/medium/low) on every response
 * - Cache pre-generated insights per object (refresh every 5 min)
 * - Generate proactive notifications (risk detection, missed opportunities)
 * - Support execution-aware reasoning (how does this affect commitments?)
 *
 * ── Events Published ──────────────────────────────────────────
 * IntelligenceRequested, IntelligenceLoaded, IntelligenceError
 *
 * ── Events Subscribed To ──────────────────────────────────────
 * WorkspaceOpened → triggers IntelligenceRequested for context
 * ObjectLoaded    → triggers IntelligenceRequested for the loaded object
 * ObjectUpdated   → triggers re-evaluation of cached insights
 *
 * ── Owned State ───────────────────────────────────────────────
 * Insight cache (Map<contextKey, CachedInsight>), pending requests
 *
 * ── State Referenced (not owned) ──────────────────────────────
 * ObjectRuntime cache (for reading object data to generate insights)
 * TimelineRuntime events (for detecting patterns, risks)
 */

import { bus } from '../event-bus';

export interface Insight {
  id: string;
  type: 'observation' | 'recommendation' | 'risk' | 'opportunity' | 'summary';
  title: string;
  body: string;
  confidence: 'high' | 'medium' | 'low';
  source: string;
  timestamp: number;
  objectType?: string;
  objectId?: string;
  commitmentId?: string;
  metadata?: Record<string, unknown>;
}

interface CachedInsight {
  insights: Insight[];
  generatedAt: number;
}

const cache = new Map<string, CachedInsight>();
const TTL = 5 * 60 * 1000; // 5 minutes

function contextKey(objectType?: string, objectId?: string): string {
  return `${objectType ?? '*'}:${objectId ?? '*'}`;
}

function isExpired(entry: CachedInsight): boolean {
  return Date.now() - entry.generatedAt > TTL;
}

async function fetchInsights(objectType: string, objectId: string): Promise<Insight[]> {
  try {
    const resp = await fetch(`/api/v1/${objectType}s/${objectId}/insights`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    return (data.insights ?? data ?? []).map((i: any): Insight => ({
      id: i.id ?? crypto.randomUUID(),
      type: i.type ?? 'observation',
      title: i.title ?? '',
      body: i.body ?? i.description ?? '',
      confidence: i.confidence ?? 'medium',
      source: i.source ?? 'ai',
      timestamp: new Date(i.timestamp ?? Date.now()).getTime(),
      objectType,
      objectId,
      commitmentId: i.commitment_id ?? i.commitmentId,
    }));
  } catch {
    return [];
  }
}

export const IntelligenceRuntime = {
  /** Get cached insights for a context. */
  get(objectType?: string, objectId?: string): Insight[] {
    const entry = cache.get(contextKey(objectType, objectId));
    if (entry && !isExpired(entry)) return entry.insights;
    return [];
  },

  /** Request insights for a context. */
  async request(objectType: string, objectId: string, workspaceId?: string): Promise<void> {
    const key = contextKey(objectType, objectId);
    const cached = cache.get(key);
    if (cached && !isExpired(cached)) return;

    bus.emit({ type: 'IntelligenceRequested', objectType, objectId, workspaceId: workspaceId ?? '' });

    const insights = await fetchInsights(objectType, objectId);
    cache.set(key, { insights, generatedAt: Date.now() });
    bus.emit({ type: 'IntelligenceLoaded', objectType, objectId, insights });
  },

  /** Generate an insight locally (for rule-based observations). */
  observe(
    type: Insight['type'],
    title: string,
    body: string,
    confidence: Insight['confidence'],
    objectType?: string,
    objectId?: string,
  ): Insight {
    const insight: Insight = {
      id: crypto.randomUUID(),
      type,
      title,
      body,
      confidence,
      source: 'system',
      timestamp: Date.now(),
      objectType,
      objectId,
    };
    const key = contextKey(objectType, objectId);
    const existing = cache.get(key);
    if (existing) existing.insights.push(insight);
    else cache.set(key, { insights: [insight], generatedAt: Date.now() });
    return insight;
  },

  /** Invalidate cache for a context. */
  invalidate(objectType?: string, objectId?: string): void {
    cache.delete(contextKey(objectType, objectId));
  },

  /** Clear all cached insights. */
  clear(): void {
    cache.clear();
  },
};
