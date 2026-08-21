/**
 * ExecutionWorkspace — Work visibility and execution traceability.
 *
 * Surfaces real canonical data: outcomes, tasks, commitments.
 * Shows: what SHUNYA is doing, what's been requested, what's completed.
 * Each item is clickable and leads to the relevant drill-down.
 *
 * Mobile-responsive via container queries.
 */

import { useState, useEffect, type FC } from 'react';

interface WorkItem {
  id: string;
  type: 'outcome' | 'task' | 'commitment';
  title: string;
  status: string;
  progress?: number;
  context?: string;
  owner: string;
  source: string;
  priority?: string;
  due_date?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  completed_at?: string | null;
  result?: string;
  error?: string;
  drilldown?: string;
}

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json() as T;
  } catch { return null; }
}

function _timeAgo(ts: string | null | undefined): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const diff = Date.now() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch { return ''; }
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === 'completed' ? '#2e7d32'
    : status === 'in_progress' || status === 'accepted' || status === 'active' ? '#a4865f'
    : status === 'pending' || status === 'new' ? 'rgba(26,28,29,0.2)'
    : status === 'error' || status === 'failed' || status === 'cancelled' ? '#d1453b'
    : 'rgba(26,28,29,0.35)';
  return <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: color, display: 'inline-block', flexShrink: 0 }} />;
}

function ProgressBar({ value }: { value: number }) {
  const pct = Math.min(Math.max(Math.round(value * 100), 0), 100);
  return (
    <div style={{ width: 60, height: 4, borderRadius: 2, background: 'rgba(26,28,29,0.06)', overflow: 'hidden' }}>
      <div style={{ width: `${pct}%`, height: '100%', background: pct >= 100 ? '#2e7d32' : '#a4865f', borderRadius: 2, transition: 'width 0.3s' }} />
    </div>
  );
}

const TYPE_LABELS: Record<string, string> = {
  outcome: 'Request',
  task: 'Task',
  commitment: 'Commitment',
};

export const ExecutionWorkspace: FC = () => {
  const [items, setItems] = useState<WorkItem[]>([]);
  const [summary, setSummary] = useState<{ total_outcomes: number; total_tasks: number; total_commitments: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const result = await api<{ success: boolean; data: { items: WorkItem[]; summary: any } }>('/api/v1/execution/work');
        if (result?.success) {
          setItems(result.data.items || []);
          setSummary(result.data.summary);
        } else {
          setError('Could not load execution data');
        }
      } catch { setError('Failed to load'); }
      setLoading(false);
    })();
  }, []);

  const filtered = filter === 'all'
    ? items
    : filter === 'active'
      ? items.filter(i => i.status !== 'completed' && i.status !== 'cancelled' && i.status !== 'failed')
      : filter === 'completed'
        ? items.filter(i => i.status === 'completed')
        : items.filter(i => i.type === filter);

  const activeCount = items.filter(i => i.status !== 'completed' && i.status !== 'cancelled' && i.status !== 'failed').length;

  return (
    <div className="pw-panel-container" style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">◉</span>
        <h2 className="pw-domain-title">Work</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '0 0 20px' }}>
        Execution visibility — what SHUNYA is doing and what has been done
      </p>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="exe-summary-card">
          <div className="exe-summary-value">{activeCount}</div>
          <div className="exe-summary-label">Active</div>
        </div>
        <div className="exe-summary-card">
          <div className="exe-summary-value">{items.length}</div>
          <div className="exe-summary-label">Total</div>
        </div>
        {summary && (
          <>
            <div className="exe-summary-card">
              <div className="exe-summary-value">{summary.total_outcomes}</div>
              <div className="exe-summary-label">Outcomes</div>
            </div>
            <div className="exe-summary-card">
              <div className="exe-summary-value">{summary.total_tasks}</div>
              <div className="exe-summary-label">Tasks</div>
            </div>
            {summary.total_commitments > 0 && (
              <div className="exe-summary-card">
                <div className="exe-summary-value">{summary.total_commitments}</div>
                <div className="exe-summary-label">Commitments</div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {['all', 'active', 'completed', 'outcome', 'task', 'commitment'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`exe-filter-btn ${filter === f ? 'exe-filter-active' : ''}`}
          >
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <div className="exe-loading">Loading execution data…</div>}
      {error && <div className="exe-error">{error}</div>}

      {/* Empty state */}
      {!loading && !error && filtered.length === 0 && (
        <div className="exe-empty">
          <p>No work items yet.</p>
          <p className="exe-empty-sub">Work items appear here when SHUNYA executes requests or tasks are created.</p>
        </div>
      )}

      {/* Work items */}
      {!loading && !error && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map((item) => (
            <div key={item.id} className="exe-item">
              <div className="exe-item-row">
                <StatusDot status={item.error ? 'error' : item.status} />
                <div className="exe-item-type">{TYPE_LABELS[item.type] || item.type}</div>
                <div className="exe-item-title">{item.title}</div>
                <ProgressBar value={item.progress ?? 0} />
              </div>
              <div className="exe-item-meta">
                <span>Owner: {item.owner}</span>
                {item.priority && <span>Priority: {item.priority}</span>}
                {item.due_date && <span>Due: {_timeAgo(item.due_date)}</span>}
                {item.created_at && <span>Created: {_timeAgo(item.created_at)}</span>}
                {item.completed_at && <span>✓ {_timeAgo(item.completed_at)}</span>}
                {item.source && <span>Source: {item.source}</span>}
              </div>
              {item.error && <div className="exe-item-error">{item.error}</div>}
              {item.result && <div className="exe-item-result">{item.result}</div>}
            </div>
          ))}
        </div>
      )}

      <style>{`
.exe-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 80px;
}
.exe-summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #1A1C1D;
}
.exe-summary-label {
  font-size: 11px;
  color: rgba(26,28,29,0.55);
  margin-top: 2px;
}
.exe-loading { padding: 40px; text-align: center; color: rgba(26,28,29,0.55); }
.exe-error { padding: 40px; text-align: center; color: #d1453b; }
.exe-empty { padding: 40px; text-align: center; }
.exe-empty-sub { font-size: 13px; color: rgba(26,28,29,0.45); }
.exe-filter-btn {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid rgba(26,28,29,0.06);
  background: transparent;
  color: rgba(26,28,29,0.55);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}
.exe-filter-active {
  border-color: #a4865f;
  background: rgba(164,134,95,0.1);
  color: #a4865f;
}
.exe-item {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 16px;
  transition: box-shadow 0.15s;
}
.exe-item:hover { box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.exe-item-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.exe-item-type {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(26,28,29,0.35);
  padding: 2px 6px;
  background: rgba(26,28,29,0.04);
  border-radius: 4px;
}
.exe-item-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #1A1C1D;
  min-width: 120px;
  line-height: 1.3;
}
.exe-item-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 6px;
  font-size: 11px;
  color: rgba(26,28,29,0.45);
}
.exe-item-error {
  margin-top: 6px;
  font-size: 12px;
  color: #d1453b;
  background: rgba(209,69,59,0.06);
  padding: 6px 10px;
  border-radius: 6px;
}
.exe-item-result {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(26,28,29,0.65);
  background: rgba(26,28,29,0.03);
  padding: 6px 10px;
  border-radius: 6px;
  line-height: 1.4;
}
      `}</style>
    </div>
  );
};

export default ExecutionWorkspace;