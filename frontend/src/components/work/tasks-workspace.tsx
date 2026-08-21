/**
 * TasksWorkspace — Task management UI.
 *
 * Reads task data from the execution work API.
 * Shows: title, status, priority, assigned_to, due_date.
 * Mobile-responsive.
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
  completed_at?: string | null;
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

const PRIORITY_COLORS: Record<string, string> = {
  urgent: '#d1453b',
  high: '#c97b2d',
  medium: '#a4865f',
  low: 'rgba(26,28,29,0.35)',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'rgba(26,28,29,0.35)',
  in_progress: '#a4865f',
  completed: '#2e7d32',
  cancelled: 'rgba(26,28,29,0.2)',
};

export const TasksWorkspace: FC = () => {
  const [tasks, setTasks] = useState<WorkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    (async () => {
      setLoading(true);
      const result = await api<{ success: boolean; data: { items: WorkItem[] } }>('/api/v1/execution/work');
      if (result?.success && result.data?.items) {
        setTasks(result.data.items.filter(i => i.type === 'task'));
      } else {
        setError('Could not load tasks');
      }
      setLoading(false);
    })();
  }, []);

  const filtered = filter === 'all'
    ? tasks
    : filter === 'active'
      ? tasks.filter(t => t.status !== 'completed' && t.status !== 'cancelled')
      : tasks.filter(t => t.status === filter || t.priority === filter);

  const activeCount = tasks.filter(t => t.status !== 'completed' && t.status !== 'cancelled').length;
  const overdueCount = tasks.filter(t => t.due_date && t.status !== 'completed').filter(t => {
    const d = new Date(t.due_date!);
    return !isNaN(d.getTime()) && d < new Date();
  }).length;

  return (
    <div className="pw-panel-container" style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">◉</span>
        <h2 className="pw-domain-title">Tasks</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '0 0 20px' }}>
        Individual task items across the organization
      </p>

      {/* Summary */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="task-summary-card">
          <div className="task-summary-value">{tasks.length}</div>
          <div className="task-summary-label">Total</div>
        </div>
        <div className="task-summary-card">
          <div className="task-summary-value">{activeCount}</div>
          <div className="task-summary-label">Active</div>
        </div>
        {overdueCount > 0 && (
          <div className="task-summary-card" style={{ borderColor: 'rgba(209,69,59,0.2)' }}>
            <div className="task-summary-value" style={{ color: '#d1453b' }}>{overdueCount}</div>
            <div className="task-summary-label">Overdue</div>
          </div>
        )}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {['all', 'active', 'pending', 'in_progress', 'completed', 'urgent', 'high'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className="task-filter-btn" style={{
              padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer',
              border: `1px solid ${filter === f ? '#a4865f' : 'rgba(26,28,29,0.06)'}`,
              background: filter === f ? 'rgba(164,134,95,0.1)' : 'transparent',
              color: filter === f ? '#a4865f' : 'rgba(26,28,29,0.55)',
            }}>
            {f === 'all' ? 'All' : f === 'in_progress' ? 'In Progress' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading && <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)' }}>Loading tasks…</div>}
      {error && <div style={{ padding: 40, textAlign: 'center', color: '#d1453b' }}>{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <p>{filter === 'all' ? 'No tasks found.' : `No ${filter} tasks.`}</p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(t => (
            <div key={t.id} className="task-item" style={{
              background: '#fff',
              border: '1px solid rgba(26,28,29,0.07)',
              borderRadius: 10, padding: '14px 16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  backgroundColor: STATUS_COLORS[t.status] || 'rgba(26,28,29,0.35)',
                  display: 'inline-block', flexShrink: 0,
                }} />
                <span style={{ flex: 1, fontSize: 14, fontWeight: 500, color: '#1A1C1D', minWidth: 120 }}>
                  {t.title}
                </span>
                {t.priority && (
                  <span style={{
                    fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                    padding: '2px 8px', borderRadius: 4,
                    color: PRIORITY_COLORS[t.priority] || 'rgba(26,28,29,0.45)',
                    background: 'rgba(26,28,29,0.04)',
                  }}>
                    {t.priority}
                  </span>
                )}
                <span style={{
                  fontSize: 11, fontWeight: 500, textTransform: 'capitalize',
                  color: STATUS_COLORS[t.status] || 'rgba(26,28,29,0.55)',
                }}>
                  {t.status === 'in_progress' ? 'In Progress' : t.status}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6, fontSize: 11, color: 'rgba(26,28,29,0.45)' }}>
                {t.owner && <span>Owner: {t.owner}</span>}
                {t.due_date && <span>Due: {_timeAgo(t.due_date)}</span>}
                {t.context && <span>{t.context}</span>}
                <span>Created: {_timeAgo(t.created_at)}</span>
                {t.completed_at && <span>✓ {_timeAgo(t.completed_at)}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
.task-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 80px;
}
.task-summary-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.task-summary-label { font-size: 11px; color: rgba(26,28,29,0.55); margin-top: 2px; }
      `}</style>
    </div>
  );
};

export default TasksWorkspace;