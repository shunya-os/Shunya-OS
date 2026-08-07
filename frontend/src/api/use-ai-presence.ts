/**
 * SHUNYA OS — useAIPresence Hook
 * Proactive ambient intelligence that surfaces insights without being prompted.
 *
 * Polls the AI insights endpoint every 45s, filters by confidence >= 0.7,
 * deduplicates by title using sessionStorage, and emits 'ai:insight' events
 * on the event bus at most once per 60 seconds.
 */

import { useEffect, useRef } from 'react';
import { bus } from '../runtimes/event-bus';

export interface AIInsight {
  title: string;
  description: string;
  type: 'reminder' | 'opportunity' | 'alert' | 'suggestion';
  confidence: number;
  evidence: string;
  source: string;
  action_label: string | null;
  action_payload: any;
}

const POLL_INTERVAL_MS = 45_000;
const MIN_SPACING_MS = 60_000;
const CONFIDENCE_THRESHOLD = 0.7;
const STORAGE_KEY = 'shunya_shown_insights';

/** Read the set of shown insight titles from sessionStorage. */
function getShownInsights(): Set<string> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw));
  } catch {
    return new Set();
  }
}

/** Save an insight title to the shown set in sessionStorage. */
function markInsightShown(title: string): void {
  try {
    const set = getShownInsights();
    set.add(title);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...set]));
  } catch {
    // sessionStorage may be full — silently ignore
  }
}

/**
 * Polls the proactive insights endpoint and emits new, high-confidence
 * insights on the event bus for the rest of the app to consume.
 */
export function useAIPresence(): void {
  const lastShownRef = useRef<number>(0);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const resp = await fetch('/api/v1/ai/insights', {
          credentials: 'include',
        });
        if (!resp.ok) return;
        const body = await resp.json();
        if (!body.success || !Array.isArray(body.data)) return;

        const insights: AIInsight[] = body.data;

        // Filter by confidence threshold
        const highConfidence = insights.filter(
          (i) => i.confidence >= CONFIDENCE_THRESHOLD,
        );

        // Deduplicate against previously shown insights
        const shown = getShownInsights();
        const unseen = highConfidence.filter((i) => !shown.has(i.title));

        if (unseen.length === 0) return;

        // Rate-limit: at most 1 insight per MIN_SPACING_MS
        const now = Date.now();
        if (now - lastShownRef.current < MIN_SPACING_MS) return;

        // Pick the highest-confidence unseen insight
        const best = unseen.reduce((a, b) =>
          a.confidence >= b.confidence ? a : b,
        );

        // Mark as shown and emit
        markInsightShown(best.title);
        lastShownRef.current = Date.now();

        if (!cancelled) {
          bus.emit({ type: 'ai:insight', payload: best });
        }
      } catch {
        // Network errors — silent
      }
    };

    // Initial poll after a short delay
    const initialTimeout = setTimeout(poll, 5_000);

    // Recurring poll every 45s
    const interval = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, []);
}