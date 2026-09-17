/**
 * SHUNYA Living Presence — Block C (R6B-2.7 Window 6)
 *
 * A single, honest indicator of the fact that SHUNYA is alive and aware.
 *
 * Every state it renders is derived from REAL signals — never decoration:
 *   connection    ← the SSE transport lifecycle (reality:* bus events)
 *   processing    ← activeExecutions (work actually in flight)
 *   completion    ← executionHistory (work that just finished)
 *   attention     ← awareness signals (something needs the human)
 *   activity      ← lastActivityAt (last real frame received)
 *
 * Motion communicates meaning:
 *   • a steady slow pulse = alive and observing
 *   • a fast pulse       = actively processing
 *   • an amber pulse     = attention required
 *   • a broken/stilled   = reconnecting or unavailable
 *
 * If the transport is degraded the label tells the truth. It never shows a
 * calm green dot while disconnected.
 */
import { useState, useEffect, useRef, FC } from 'react';
import { useLivingStore } from './living-store';

type PresenceMode = 'processing' | 'attention' | 'reconnecting' | 'unavailable' | 'observing';

const MODE_META: Record<PresenceMode, { label: string; color: string; hint: string }> = {
  processing: {
    label: 'Working',
    color: 'var(--shunya-info, #4a9e9e)',
    hint: 'SHUNYA is actively working on something.',
  },
  attention: {
    label: 'Needs your attention',
    color: 'var(--shunya-gold, #a4865f)',
    hint: 'SHUNYA noticed something that may need you.',
  },
  reconnecting: {
    label: 'Reconnecting…',
    color: '#c98a2b',
    hint: 'The live connection dropped — reconnecting with backoff.',
  },
  unavailable: {
    label: 'Temporarily unavailable',
    color: '#c0392b',
    hint: 'SHUNYA cannot reach the live stream right now.',
  },
  observing: {
    label: 'Observing',
    color: 'var(--shunya-success, #6a9f6a)',
    hint: 'SHUNYA is connected and watching.',
  },
};

function _timeAgo(ms: number | null): string {
  if (!ms) return '';
  const diff = Date.now() - ms;
  if (diff < 5000) return 'just now';
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export const LivingPresence: FC<{ compact?: boolean }> = ({ compact = false }) => {
  const presenceConnection = useLivingStore((s) => s.presenceConnection);
  const lastActivityAt = useLivingStore((s) => s.lastActivityAt);
  const activeExecutions = useLivingStore((s) => s.activeExecutions);
  const executionHistory = useLivingStore((s) => s.executionHistory);
  const awarenessSignals = useLivingStore((s) => s.awarenessSignals);
  const observations = useLivingStore((s) => s.observations);

  // Re-render every 5s so the "last activity" label stays truthful.
  const [, forceTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => forceTick((n) => n + 1), 5000);
    return () => clearInterval(t);
  }, []);

  // Detect a recent completion so the presence can briefly show it.
  const [recentCompletion, setRecentCompletion] = useState<string | null>(null);
  const lastHistoryLen = useRef(executionHistory.length);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    if (executionHistory.length > lastHistoryLen.current) {
      const done = executionHistory[0];
      if (done) {
        setRecentCompletion(done.label || 'Task completed');
        timer = setTimeout(() => setRecentCompletion(null), 6000);
      }
    }
    lastHistoryLen.current = executionHistory.length;
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [executionHistory]);

  // ─ Derive the single truthful mode ──
  const hasAttention = awarenessSignals.some((s) => s.status === 'active') || observations.length > 0;
  let mode: PresenceMode;
  if (presenceConnection === 'unavailable') mode = 'unavailable';
  else if (presenceConnection === 'reconnecting') mode = 'reconnecting';
  else if (activeExecutions.length > 0) mode = 'processing';
  else if (hasAttention) mode = 'attention';
  else mode = 'observing';

  const meta = MODE_META[mode];
  const processing = mode === 'processing';
  const degraded = presenceConnection === 'reconnecting' || presenceConnection === 'unavailable';

  // Pulse durations communicate meaning — fast when working, slow when calm.
  const pulseDuration = processing ? 1.1 : mode === 'attention' ? 1.6 : degraded ? 2.8 : 3.2;

  const activityText = recentCompletion
    ? `Completed: ${recentCompletion}`
    : lastActivityAt
      ? `Last update ${_timeAgo(lastActivityAt)}`
      : 'Waiting for first update…';

  const count =
    activeExecutions.length > 0
      ? `${activeExecutions.length} in progress`
      : hasAttention
        ? `${awarenessSignals.filter((s) => s.status === 'active').length || observations.length} to review`
        : '';

  if (compact) {
    return (
      <div className="lp-presence lp-presence-compact" title={`${meta.label} — ${meta.hint}`}>
        <span
          className="lp-dot"
          style={{ backgroundColor: meta.color, boxShadow: `0 0 6px ${meta.color}` }}
          data-mode={mode}
          data-testid="living-presence-dot"
        />
        <span className="lp-label">{meta.label}</span>
      </div>
    );
  }

  return (
    <div className="lp-presence" data-mode={mode} data-testid="living-presence">
      <span
        className="lp-dot"
        style={{ backgroundColor: meta.color, boxShadow: `0 0 8px ${meta.color}` }}
        data-mode={mode}
        data-testid="living-presence-dot"
      />
      <div className="lp-body">
        <span className="lp-label" data-testid="living-presence-label">
          {meta.label}
          {count && <span className="lp-count"> · {count}</span>}
        </span>
        <span className="lp-activity" data-testid="living-presence-activity">
          {activityText}
        </span>
      </div>
      <style>{`
.lp-presence {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 12px; border-radius: 999px;
  background: rgba(26,28,29,0.02);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.06));
  font-family: var(--shunya-font-body, 'Inter', sans-serif);
  transition: background 0.3s, border-color 0.3s;
}
.lp-presence[data-mode="reconnecting"],
.lp-presence[data-mode="unavailable"] {
  background: rgba(201,138,43,0.06);
  border-color: rgba(201,138,43,0.25);
}
.lp-presence-compact { padding: 4px 8px; gap: 7px; background: transparent; border-color: transparent; }
.lp-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.lp-dot[data-mode="processing"] { animation: lp-pulse-fast ${pulseDuration}s ease-in-out infinite; }
.lp-dot[data-mode="attention"] { animation: lp-pulse-mid ${pulseDuration}s ease-in-out infinite; }
.lp-dot[data-mode="reconnecting"] { animation: lp-pulse-slow ${pulseDuration}s ease-in-out infinite; }
.lp-dot[data-mode="unavailable"] { animation: lp-pulse-slow ${pulseDuration}s ease-in-out infinite; opacity: 0.6; }
.lp-dot[data-mode="observing"] { animation: lp-pulse-slow ${pulseDuration}s ease-in-out infinite; }
@keyframes lp-pulse-fast { 0%,100% { opacity: 0.5; transform: scale(1); } 50% { opacity: 1; transform: scale(1.35); } }
@keyframes lp-pulse-mid { 0%,100% { opacity: 0.6; transform: scale(1); } 50% { opacity: 1; transform: scale(1.2); } }
@keyframes lp-pulse-slow { 0%,100% { opacity: 0.45; } 50% { opacity: 1; } }
.lp-body { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.lp-label { font-size: 12px; font-weight: 500; color: var(--shunya-text, #1A1C1D); white-space: nowrap; }
.lp-count { font-weight: 400; color: rgba(26,28,29,0.5); }
.lp-activity { font-size: 10px; color: rgba(26,28,29,0.4); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
@media (max-width: 640px) {
  .lp-activity { display: none; }
  .lp-presence { padding: 5px 9px; }
}
@media (prefers-reduced-motion: reduce) {
  .lp-dot { animation: none !important; opacity: 0.9 !important; }
}
      `}</style>
    </div>
  );
};