/**
 * CommitmentWorkspace — Real commitment tracking from /api/v1/commitments/.
 *
 * Shows: all commitments, status, owner, due date, overdue status.
 * Allows: creating new commitments, updating status.
 * Mobile-responsive.
 */

import { useState, useEffect, useCallback, type FC } from 'react';

interface Commitment {
  id: number;
  title: string;
  owner: string;
  status: string;
  due_at: string | null;
  issue_type: string;
  meta: Record<string, unknown>;
  overdue: boolean;
  created_at: string | null;
  updated_at: string | null;
}

async function api<T>(path: string, opts?: RequestInit): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
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

function formatDate(val: string | null): string {
  if (!val) return '—';
  try {
    return new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return val; }
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'rgba(26,28,29,0.35)',
  in_progress: '#a4865f',
  completed: '#2e7d32',
  failed: '#d1453b',
  cancelled: 'rgba(26,28,29,0.2)',
};

const STATUS_OPTIONS = ['pending', 'in_progress', 'completed', 'failed', 'cancelled'];

const ISSUE_TYPE_OPTIONS = ['', 'service', 'escalation', 'approval', 'onboarding', 'followup', 'general'];

export const CommitmentWorkspace: FC = () => {
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newOwner, setNewOwner] = useState('');
  const [newDue, setNewDue] = useState('');
  const [newType, setNewType] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    const result = await api<{ commitments: Commitment[] }>('/api/v1/commitments/');
    if (result && result.commitments) {
      setCommitments(result.commitments);
    } else {
      setError('Could not load commitments');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    setSaving(true);
    const body: Record<string, unknown> = { title: newTitle.trim() };
    if (newOwner.trim()) body.owner = newOwner.trim();
    if (newDue) body.due_at = newDue;
    if (newType) body.issue_type = newType;
    await api('/api/v1/commitments/', { method: 'POST', body: JSON.stringify(body) });
    setSaving(false);
    setShowCreate(false);
    setNewTitle('');
    setNewOwner('');
    setNewDue('');
    setNewType('');
    load();
  };

  const handleStatusChange = async (id: number, status: string) => {
    await api(`/api/v1/commitments/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
    load();
  };

  const filtered = filter === 'all'
    ? commitments
    : filter === 'active'
      ? commitments.filter(c => c.status !== 'completed' && c.status !== 'cancelled' && c.status !== 'failed')
      : filter === 'overdue'
        ? commitments.filter(c => c.overdue)
        : commitments.filter(c => c.status === filter);

  const activeCount = commitments.filter(c => c.status !== 'completed' && c.status !== 'cancelled' && c.status !== 'failed').length;
  const overdueCount = commitments.filter(c => c.overdue).length;

  return (
    <div className="pw-panel-container" style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <div className="pw-domain-header" style={{ marginBottom: 0 }}>
            <span className="pw-domain-icon">◉</span>
            <h2 className="pw-domain-title">Commitments</h2>
          </div>
          <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '4px 0 0' }}>
            Promises, tasks, and obligations
          </p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)}
          style={{
            padding: '8px 18px', background: showCreate ? 'transparent' : '#1A1C1D',
            color: showCreate ? 'rgba(26,28,29,0.55)' : '#fff',
            border: showCreate ? '1px solid rgba(26,28,29,0.07)' : 'none',
            borderRadius: 6, fontSize: 13, fontWeight: 500, cursor: 'pointer',
          }}>
          {showCreate ? 'Cancel' : '+ New Commitment'}
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div style={{
          background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
          borderRadius: 10, padding: 20, marginBottom: 16,
        }}>
          <h3 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 600 }}>New Commitment</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <input placeholder="Title *" value={newTitle} onChange={e => setNewTitle(e.target.value)}
              style={{ padding: '8px 12px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13, outline: 'none', fontFamily: 'inherit' }} />
            <div style={{ display: 'flex', gap: 10 }}>
              <input placeholder="Owner" value={newOwner} onChange={e => setNewOwner(e.target.value)}
                style={{ flex: 1, padding: '8px 12px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13, outline: 'none', fontFamily: 'inherit' }} />
              <input placeholder="Due date" value={newDue} onChange={e => setNewDue(e.target.value)} type="date"
                style={{ flex: 1, padding: '8px 12px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13, outline: 'none', fontFamily: 'inherit' }} />
              <select value={newType} onChange={e => setNewType(e.target.value)}
                style={{ padding: '8px 12px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13, outline: 'none', fontFamily: 'inherit' }}>
                <option value="">Type</option>
                {ISSUE_TYPE_OPTIONS.filter(t => t).map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
            <button onClick={handleCreate} disabled={saving || !newTitle.trim()}
              style={{ padding: '8px 20px', background: '#1A1C1D', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, cursor: 'pointer', opacity: saving || !newTitle.trim() ? 0.5 : 1 }}>
              {saving ? 'Creating…' : 'Create'}
            </button>
            <button onClick={() => setShowCreate(false)}
              style={{ padding: '8px 20px', background: 'transparent', border: '1px solid rgba(26,28,29,0.07)', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Summary */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="cmt-summary-card">
          <div className="cmt-summary-value">{commitments.length}</div>
          <div className="cmt-summary-label">Total</div>
        </div>
        <div className="cmt-summary-card">
          <div className="cmt-summary-value">{activeCount}</div>
          <div className="cmt-summary-label">Active</div>
        </div>
        {overdueCount > 0 && (
          <div className="cmt-summary-card" style={{ borderColor: 'rgba(209,69,59,0.2)' }}>
            <div className="cmt-summary-value" style={{ color: '#d1453b' }}>{overdueCount}</div>
            <div className="cmt-summary-label">Overdue</div>
          </div>
        )}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {['all', 'active', 'overdue', 'pending', 'in_progress', 'completed'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`cmt-filter-btn ${filter === f ? 'cmt-filter-active' : ''}`}>
            {f === 'all' ? 'All' : f === 'in_progress' ? 'In Progress' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading && <div className="cmt-loading">Loading commitments…</div>}
      {error && <div className="cmt-error-msg">{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="cmt-empty">
          <p>{filter === 'all' ? 'No commitments yet. Click "+ New Commitment" to create one.' : `No ${filter} commitments.`}</p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(c => (
            <div key={c.id} className="cmt-item" style={{
              background: '#fff', border: `1px solid ${c.overdue ? 'rgba(209,69,59,0.15)' : 'rgba(26,28,29,0.07)'}`,
              borderLeft: c.overdue ? '3px solid #d1453b' : '1px solid rgba(26,28,29,0.07)',
              borderRadius: 10, padding: '14px 16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  backgroundColor: STATUS_COLORS[c.status] || 'rgba(26,28,29,0.35)',
                  display: 'inline-block', flexShrink: 0,
                }} />
                <div className="cmt-item-title" style={{ flex: 1, fontSize: 14, fontWeight: 500, color: '#1A1C1D', minWidth: 120 }}>
                  {c.title}
                </div>
                <select value={c.status} onChange={e => handleStatusChange(c.id, e.target.value)}
                  style={{
                    padding: '3px 8px', borderRadius: 6, border: '1px solid rgba(26,28,29,0.07)',
                    fontSize: 11, fontWeight: 500, color: STATUS_COLORS[c.status] || 'rgba(26,28,29,0.55)',
                    background: '#fff', cursor: 'pointer', fontFamily: 'inherit',
                  }}>
                  {STATUS_OPTIONS.map(s => (
                    <option key={s} value={s}>{s === 'in_progress' ? 'In Progress' : s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6, fontSize: 11, color: 'rgba(26,28,29,0.45)' }}>
                {c.owner && <span>Owner: {c.owner}</span>}
                {c.issue_type && <span>Type: {c.issue_type}</span>}
                {c.due_at && <span>Due: {formatDate(c.due_at)}</span>}
                {c.overdue && <span style={{ color: '#d1453b', fontWeight: 500 }}>⚠ Overdue</span>}
                <span>Created: {_timeAgo(c.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
.cmt-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 80px;
}
.cmt-summary-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.cmt-summary-label { font-size: 11px; color: rgba(26,28,29,0.55); margin-top: 2px; }
.cmt-loading { padding: 40px; text-align: center; color: rgba(26,28,29,0.55); }
.cmt-error-msg { padding: 40px; text-align: center; color: #d1453b; }
.cmt-empty { padding: 40px; text-align: center; }
.cmt-filter-btn {
  padding: 4px 12px; border-radius: 6px;
  border: 1px solid rgba(26,28,29,0.06);
  background: transparent; color: rgba(26,28,29,0.55);
  font-size: 12px; font-weight: 500; cursor: pointer;
}
.cmt-filter-active {
  border-color: #a4865f; background: rgba(164,134,95,0.1); color: #a4865f;
}
      `}</style>
    </div>
  );
};

export default CommitmentWorkspace;