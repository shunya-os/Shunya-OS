/**
 * FDA17 — Timeline View
 *
 * Unified temporal view across all canonical sources.
 * Shows events from TimelineEntry, ActivityLog, commitments, and memory.
 */
import { useState, type FC } from 'react';
import { getMemoryTimeline } from '../../api/workspace-api';

interface Props {
  events: any[];
  _objectType?: string;
  _objectId?: string;
  relationshipId?: number;
}

function formatTime(ts: string): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

function truthLabel(t: string): string {
  switch (t) {
    case 'fact': return 'F';
    case 'memory': return 'M';
    case 'observation': return 'O';
    case 'inference': return 'I';
    case 'unknown': return '?';
    default: return t ? t[0].toUpperCase() : '?';
  }
}

function truthColor(t: string): string {
  switch (t) {
    case 'fact': return '#34d399';
    case 'memory': return '#f5a623';
    case 'observation': return '#60a5fa';
    case 'inference': return '#a78bfa';
    default: return '#888';
  }
}

export const TimelineView: FC<Props> = ({ events, relationshipId }) => {
  const [showMemory, setShowMemory] = useState(false);
  const [memoryEvents, setMemoryEvents] = useState<any[]>([]);
  const [loadingMemory, setLoadingMemory] = useState(false);

  const loadMemory = async () => {
    if (!relationshipId) return;
    setLoadingMemory(true);
    try {
      const resp = await getMemoryTimeline(relationshipId);
      if (resp.success && resp.data) {
        setMemoryEvents(resp.data);
        setShowMemory(true);
      }
    } catch {
      // ignore
    } finally {
      setLoadingMemory(false);
    }
  };

  const allEvents = showMemory ? [...events, ...memoryEvents.map((m) => ({
    id: m.id,
    time: m.created_at,
    type: 'memory',
    event_type: m.memory_type,
    title: m.memory_key,
    description: m.value,
    truth: m.truth_classification,
    source: 'ai_memory',
  }))] : events;

  // Sort by time descending
  allEvents.sort((a, b) => {
    const ta = a.time || '';
    const tb = b.time || '';
    return tb.localeCompare(ta);
  });

  return (
    <div className="wksp-card wksp-timeline">
      <div className="wksp-card-title">
        Timeline ({allEvents.length})
        {relationshipId && !showMemory && (
          <button className="wksp-timeline-memory-btn" onClick={loadMemory} disabled={loadingMemory}>
            {loadingMemory ? 'Loading…' : 'Show AI Memory'}
          </button>
        )}
        {showMemory && (
          <button className="wksp-timeline-memory-btn active" onClick={() => setShowMemory(false)}>
            Hide AI Memory
          </button>
        )}
      </div>
      <div className="wksp-card-body wksp-timeline-list">
        {allEvents.length === 0 && (
          <div className="wksp-timeline-empty">No timeline events yet.</div>
        )}
        {allEvents.map((e, i) => (
          <div key={e.id || i} className="wksp-timeline-item">
            <div className="wksp-timeline-dot" style={{ borderColor: truthColor(e.truth || e.source || 'fact') }} />
            <div className="wksp-timeline-content">
              <div className="wksp-timeline-header">
                <span className="wksp-timeline-title">{e.title || e.event_type}</span>
                <span className="wksp-timeline-truth" style={{ background: truthColor(e.truth || e.source || 'fact') + '22', color: truthColor(e.truth || e.source || 'fact') }}>
                  {truthLabel(e.truth || e.source || 'fact')}
                </span>
                <span className="wksp-timeline-time">{formatTime(e.time)}</span>
              </div>
              {e.description && <div className="wksp-timeline-desc">{(e.description || '').slice(0, 200)}</div>}
            </div>
          </div>
        ))}
      </div>

      <style>{`
.wksp-timeline { max-height: 500px; overflow: hidden; display: flex; flex-direction: column; }
.wksp-card-title { display: flex; align-items: center; gap: 8px; }
.wksp-timeline-memory-btn { margin-left: auto; font-size: 11px; padding: 2px 8px; background: var(--shunya-surface-3, #2a2a3a); border: 1px solid var(--shunya-surface-1, #222); border-radius: 4px; color: var(--shunya-text-secondary, #888); cursor: pointer; }
.wksp-timeline-memory-btn.active { background: rgba(245,166,35,0.15); color: #f5a623; }
.wksp-timeline-list { flex: 1; overflow-y: auto; padding-right: 4px; }
.wksp-timeline-empty { font-size: 13px; color: var(--shunya-text-secondary, #888); text-align: center; padding: 20px; }
.wksp-timeline-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--shunya-surface-1, #222); }
.wksp-timeline-item:last-child { border-bottom: none; }
.wksp-timeline-dot { width: 10px; height: 10px; border-radius: 50%; border: 2px solid; margin-top: 4px; flex-shrink: 0; }
.wksp-timeline-content { flex: 1; min-width: 0; }
.wksp-timeline-header { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.wksp-timeline-title { font-size: 13px; font-weight: 500; color: var(--shunya-text, #e0e0e0); }
.wksp-timeline-truth { font-size: 10px; font-weight: 700; padding: 1px 5px; border-radius: 3px; }
.wksp-timeline-time { font-size: 11px; color: var(--shunya-text-secondary, #666); margin-left: auto; white-space: nowrap; }
.wksp-timeline-desc { font-size: 12px; color: var(--shunya-text-secondary, #888); margin-top: 2px; line-height: 1.4; }
      `}</style>
    </div>
  );
};