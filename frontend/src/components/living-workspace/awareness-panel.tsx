/**
 * AwarenessPanel — What matters now.
 *
 * A calm, contextual awareness surface inside the living workspace.
 * Shows what changed, why it matters, evidence, and suggested action.
 *
 * Calm when nothing important is happening.
 * Subtle real transition when a new signal arrives.
 * No card explosion. No dashboard feel.
 */
import { useState, useCallback, type FC } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLivingStore } from './living-store';
import type { AwarenessSignal as AW } from './types';

// ── Priority helpers ──────────────────────────────────────────

const priorityClass = (p: string) => {
  switch (p) {
    case 'critical': return 'awareness-critical';
    case 'high': return 'awareness-high';
    case 'normal': return 'awareness-normal';
    default: return 'awareness-low';
  }
};

const priorityLabel = (p: string) => {
  switch (p) {
    case 'critical': return 'Critical';
    case 'high': return 'Important';
    case 'normal': return 'Information';
    default: return 'Low';
  }
};

// ── Signal type helpers ───────────────────────────────────────

const signalIcon = (t: string) => {
  switch (t) {
    case 'risk': return '⚠';
    case 'change': return '◈';
    case 'commitment': return '◉';
    case 'opportunity': return '◆';
    case 'attention': return '◎';
    case 'conflict': return '△';
    case 'blocked': return '⊘';
    case 'overdue': return '◈';
    case 'external': return '◇';
    default: return '○';
  }
};

// ── Single Signal Item ────────────────────────────────────────

interface SignalItemProps {
  signal: AW;
  onAcknowledge: (id: string) => void;
  onDismiss: (id: string) => void;
  onSnooze: (id: string) => void;
  expanded: boolean;
  onToggleExpand: (id: string) => void;
}

const SignalItem: FC<SignalItemProps> = ({ signal, onAcknowledge, onDismiss, onSnooze, expanded, onToggleExpand }) => {
  if (!signal) return null;
  return (
    <motion.div
      className={`awareness-item ${priorityClass(signal.priority)}`}
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
      layout
    >
      <div className="awareness-item-header" onClick={() => onToggleExpand(signal.signal_id)}>
        <span className="awareness-icon">{signalIcon(signal.signal_type)}</span>
        <div className="awareness-item-content">
          <div className="awareness-item-title">{signal.title}</div>
          <div className="awareness-item-reason">{signal.reason}</div>
        </div>
        <span className={`awareness-priority ${priorityClass(signal.priority)}`}>
          {priorityLabel(signal.priority)}
        </span>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            className="awareness-item-detail"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            {signal.description && (
              <div className="awareness-description">{signal.description}</div>
            )}

            {signal.evidence && signal.evidence.length > 0 && (
              <div className="awareness-evidence">
                <div className="awareness-evidence-label">Evidence</div>
                {signal.evidence.map((ev, i) => (
                  <div key={i} className="awareness-evidence-item">
                    <span className="awareness-evidence-source">{ev.source}</span>
                    <span className="awareness-evidence-detail">{ev.detail}</span>
                  </div>
                ))}
              </div>
            )}

            {signal.suggested_action && (
              <div className="awareness-action">
                <span className="awareness-action-label">Suggested: </span>
                {signal.suggested_action}
              </div>
            )}

            <div className="awareness-item-actions">
              <button className="awareness-btn" onClick={() => onAcknowledge(signal.signal_id)}>
                Acknowledge
              </button>
              <button className="awareness-btn awareness-btn-secondary" onClick={() => onSnooze(signal.signal_id)}>
                Snooze
              </button>
              <button className="awareness-btn awareness-btn-ghost" onClick={() => onDismiss(signal.signal_id)}>
                Dismiss
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// ── Awareness Panel ───────────────────────────────────────────

export const AwarenessPanel: FC = () => {
  const signals = useLivingStore((s) => s.awarenessSignals);
  const count = useLivingStore((s) => s.awarenessCount);
  const calm = useLivingStore((s) => s.awarenessCalm);
  const acknowledgeSignal = useLivingStore((s) => s.acknowledgeSignal);
  const dismissSignal = useLivingStore((s) => s.dismissSignal);
  const snoozeSignal = useLivingStore((s) => s.snoozeSignal);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleToggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => prev === id ? null : id);
  }, []);

  const handleAcknowledge = useCallback((id: string) => {
    acknowledgeSignal(id);
    setExpandedId(null);
  }, [acknowledgeSignal]);

  const handleDismiss = useCallback((id: string) => {
    dismissSignal(id);
    setExpandedId(null);
  }, [dismissSignal]);

  const handleSnooze = useCallback((id: string) => {
    snoozeSignal(id);
    setExpandedId(null);
  }, [snoozeSignal]);

  // Calm → completely hidden
  if (calm) return null;

  // Nothing active → calm
  if (!signals || signals.length === 0) return null;

  return (
    <div className="awareness-panel">
      <div className="awareness-header">
        <span className="awareness-header-title">
          {count > 0
            ? `What matters now${count > 1 ? ` (${count})` : ''}`
            : 'Nothing needs attention'}
        </span>
      </div>
      <div className="awareness-list">
        <AnimatePresence>
          {signals.slice(0, 5).map((s) => (
            <SignalItem
              key={s.signal_id}
              signal={s}
              onAcknowledge={handleAcknowledge}
              onDismiss={handleDismiss}
              onSnooze={handleSnooze}
              expanded={expandedId === s.signal_id}
              onToggleExpand={handleToggleExpand}
            />
          ))}
        </AnimatePresence>
      </div>
      {signals.length > 5 && (
        <div className="awareness-more">
          +{signals.length - 5} more
        </div>
      )}
    </div>
  );
};