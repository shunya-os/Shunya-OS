/**
 * CommitmentWorkspace — Real commitment tracking from /api/v1/commitments/.
 *
 * B2 enhanced:
 * - Drill-down detail modal with full commitment info
 * - Inline status cycling (click dot to cycle through statuses)
 * - Overdue countdown with days-overdue display
 * - Detail view with timeline, editing, and evidence
 * - Mobile-responsive
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

interface CommitmentDetail extends Commitment {
  relationship_id?: number | null;
  campaign_id?: number | null;
  timeline?: Array<{
    id: number;
    event_type: string;
    title: string;
    event_time: string | null;
  }>;
}

async function api<T>(path: string, opts?: RequestInit): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    if (!r.ok) {
      const body = await r.text();
      console.warn(`API ${r.status} on ${path}:`, body);
      return null;
    }
    return await r.json() as T;
  } catch (e) {
    console.warn(`API fetch failed for ${path}:`, e);
    return null;
  }
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

/** Days relative to now. Negative = overdue. */
function daysRelative(dateStr: string | null): number | null {
  if (!dateStr) return null;
  try {
    const d = new Date(dateStr);
    const now = new Date();
    return Math.floor((d.getTime() - now.getTime()) / 86400000);
  } catch { return null; }
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'rgba(26,28,29,0.35)',
  active: '#a4865f',
  in_progress: '#a4865f',
  completed: '#2e7d32',
  failed: '#d1453b',
  cancelled: 'rgba(26,28,29,0.2)',
  blocked: '#e65100',
};

const STATUS_OPTIONS = ['active', 'pending', 'in_progress', 'completed', 'failed', 'cancelled'];

/** Cycle order for click-to-cycle: pending → in_progress → completed → (loop back to pending for re-open) */
const STATUS_CYCLE: Record<string, string> = {
  active: 'completed',
  pending: 'in_progress',
  in_progress: 'completed',
  completed: 'pending',
  failed: 'pending',
  cancelled: 'pending',
  blocked: 'in_progress',
};

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

  // Drill-down detail state
  const [detailCommitment, setDetailCommitment] = useState<CommitmentDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  // Inline editing in detail modal
  const [editTitle, setEditTitle] = useState('');
  const [editOwner, setEditOwner] = useState('');
  const [editType, setEditType] = useState('');
  const [editDue, setEditDue] = useState('');
  const [editMeta, setEditMeta] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [editEvidence, setEditEvidence] = useState('');

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
    // If detail is open and matches, update it too
    if (detailCommitment && detailCommitment.id === id) {
      setDetailCommitment(prev => prev ? { ...prev, status } : null);
    }
    load();
  };

  /** Click-to-cycle status on the status dot */
  const handleCycleStatus = async (c: Commitment) => {
    const nextStatus = STATUS_CYCLE[c.status] || 'in_progress';
    await handleStatusChange(c.id, nextStatus);
  };

  /** Open detail modal for a commitment */
  const handleOpenDetail = async (id: number) => {
    setDetailLoading(true);
    setDetailError('');
    setDetailCommitment(null);
    const result = await api<CommitmentDetail>(`/api/v1/commitments/${id}`);
    if (result) {
      setDetailCommitment(result);
      setEditTitle(result.title || '');
      setEditOwner(result.owner || '');
      setEditType(result.issue_type || '');
      setEditDue(result.due_at ? result.due_at.split('T')[0] : '');
      setEditMeta(result.meta ? JSON.stringify(result.meta, null, 2) : '');
      setEditEvidence('');
    } else {
      setDetailError('Could not load commitment detail');
    }
    setDetailLoading(false);
  };

  /** Save edits from detail modal */
  const handleSaveDetail = async () => {
    if (!detailCommitment) return;
    setEditSaving(true);
    const body: Record<string, unknown> = {};
    if (editTitle !== detailCommitment.title) body.title = editTitle;
    if (editOwner !== (detailCommitment.owner || '')) body.owner = editOwner;
    if (editType !== (detailCommitment.issue_type || '')) body.issue_type = editType;
    if (editDue !== (detailCommitment.due_at ? detailCommitment.due_at.split('T')[0] : '')) {
      body.due_at = editDue ? `${editDue}T00:00:00` : null;
    }
    if (editMeta) {
      try { body.meta = JSON.parse(editMeta); } catch { /* keep original */ }
    }

    if (Object.keys(body).length > 0) {
      const result = await api<CommitmentDetail>(`/api/v1/commitments/${detailCommitment.id}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      });
      if (result) {
        setDetailCommitment(result);
      }
    }

    // If evidence was provided, log via transition endpoint
    if (editEvidence.trim()) {
      await api(`/api/v1/commitments/${detailCommitment.id}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ resolution_note: editEvidence.trim() }),
      }).catch(() => { /* transition endpoint may not exist on all backends */ });
    }

    setEditSaving(false);
    setEditEvidence('');
    load();
  };

  /** Handle status transition in detail modal */
  const handleDetailStatusChange = async (newStatus: string) => {
    if (!detailCommitment) return;
    const evidence = editEvidence.trim() ? `: ${editEvidence.trim()}` : '';
    console.log(`Transition: ${detailCommitment.status} → ${newStatus}${evidence}`);
    await handleStatusChange(detailCommitment.id, newStatus);
    // Re-fetch detail to get updated timeline
    handleOpenDetail(detailCommitment.id);
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
          <div className="cmt-summary-card cmt-overdue-card">
            <div className="cmt-summary-value">{overdueCount}</div>
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
          {filtered.map(c => {
            const daysLeft = daysRelative(c.due_at);
            const isCriticallyOverdue = c.overdue && daysLeft !== null && daysLeft < -7;
            const daysOverdue = daysLeft !== null && daysLeft < 0 ? Math.abs(daysLeft) : 0;

            return (
              <div key={c.id} className={`cmt-item ${c.overdue ? 'cmt-item-overdue' : ''} ${isCriticallyOverdue ? 'cmt-item-critical' : ''}`}
                style={{
                  background: '#fff',
                  border: `1px solid ${c.overdue ? (isCriticallyOverdue ? 'rgba(209,69,59,0.3)' : 'rgba(209,69,59,0.15)') : 'rgba(26,28,29,0.07)'}`,
                  borderLeft: c.overdue
                    ? (isCriticallyOverdue ? '4px solid #b71c1c' : '3px solid #d1453b')
                    : '1px solid rgba(26,28,29,0.07)',
                  borderRadius: 10, padding: '14px 16px',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.15s',
                }}
                onClick={() => handleOpenDetail(c.id)}
                onMouseEnter={e => { if (!isCriticallyOverdue) e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.08)'; }}
                onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  {/* Clickable status dot for quick cycle */}
                  <span
                    title={`Click to cycle status (${c.status})`}
                    onClick={e => { e.stopPropagation(); handleCycleStatus(c); }}
                    style={{
                      width: 10, height: 10, borderRadius: '50%',
                      backgroundColor: STATUS_COLORS[c.status] || 'rgba(26,28,29,0.35)',
                      display: 'inline-block', flexShrink: 0,
                      cursor: 'pointer',
                      border: c.status === 'pending' ? '2px dashed rgba(26,28,29,0.2)' : 'none',
                      transition: 'transform 0.1s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.4)'; }}
                    onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }} />
                  <div className="cmt-item-title" style={{
                    flex: 1, fontSize: 14, fontWeight: 500, color: '#1A1C1D', minWidth: 120,
                    textDecoration: c.status === 'completed' ? 'line-through' : 'none',
                    opacity: c.status === 'completed' || c.status === 'cancelled' ? 0.6 : 1,
                  }}>
                    {c.title}
                  </div>
                  <select value={c.status} onChange={e => { e.stopPropagation(); handleStatusChange(c.id, e.target.value); }}
                    onClick={e => e.stopPropagation()}
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
                  {c.overdue && daysOverdue > 0 && (
                    <span style={{ color: isCriticallyOverdue ? '#b71c1c' : '#d1453b', fontWeight: 600 }}>
                      ⚠ {daysOverdue}d overdue
                    </span>
                  )}
                  {c.overdue && daysOverdue === 0 && (
                    <span style={{ color: '#d1453b', fontWeight: 500 }}>⚠ Due today</span>
                  )}
                  {!c.overdue && daysLeft !== null && daysLeft <= 3 && daysLeft > 0 && (
                    <span style={{ color: '#e65100', fontWeight: 500 }}>⏰ {daysLeft}d left</span>
                  )}
                  <span>Created: {_timeAgo(c.created_at)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Detail Modal ── */}
      {(detailCommitment || detailLoading) && (
        <div className="cmt-modal-overlay" onClick={() => { setDetailCommitment(null); setDetailLoading(false); }}>
          <div className="cmt-modal" onClick={e => e.stopPropagation()} style={{
            background: '#fff', borderRadius: 14, maxWidth: 620, width: '90vw',
            maxHeight: '80vh', overflowY: 'auto', padding: '28px 32px',
            boxShadow: '0 8px 40px rgba(0,0,0,0.15)',
          }}>
            {detailLoading && (
              <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)' }}>
                Loading detail…
              </div>
            )}

            {detailError && (
              <div style={{ padding: 20, textAlign: 'center', color: '#d1453b' }}>
                {detailError}
                <br />
                <button onClick={() => setDetailCommitment(null)}
                  style={{ marginTop: 12, padding: '6px 16px', background: '#1A1C1D', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
                  Close
                </button>
              </div>
            )}

            {detailCommitment && !detailLoading && !detailError && (
              <>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                      <span style={{
                        width: 12, height: 12, borderRadius: '50%',
                        backgroundColor: STATUS_COLORS[detailCommitment.status] || 'rgba(26,28,29,0.35)',
                        display: 'inline-block', flexShrink: 0,
                      }} />
                      <h3 style={{ margin: 0, fontSize: 17, fontWeight: 600, color: '#1A1C1D' }}>
                        {detailCommitment.title}
                      </h3>
                    </div>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 4, fontSize: 12, color: 'rgba(26,28,29,0.45)' }}>
                      <span>ID: #{detailCommitment.id}</span>
                      <span>Status: <strong style={{ color: STATUS_COLORS[detailCommitment.status] }}>{detailCommitment.status}</strong></span>
                      {detailCommitment.created_at && <span>Created: {formatDate(detailCommitment.created_at)}</span>}
                      {detailCommitment.updated_at && <span>Updated: {_timeAgo(detailCommitment.updated_at)}</span>}
                    </div>
                  </div>
                  <button onClick={() => { setDetailCommitment(null); setDetailLoading(false); }}
                    style={{
                      background: 'none', border: 'none', fontSize: 20, cursor: 'pointer',
                      color: 'rgba(26,28,29,0.35)', padding: 4, lineHeight: 1,
                    }}>
                    ✕
                  </button>
                </div>

                {/* Status transition buttons */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 20 }}>
                  {STATUS_OPTIONS.filter(s => s !== detailCommitment.status).map(s => (
                    <button key={s} onClick={() => handleDetailStatusChange(s)}
                      style={{
                        padding: '5px 12px', borderRadius: 6, border: '1px solid rgba(26,28,29,0.07)',
                        fontSize: 11, fontWeight: 500, cursor: 'pointer', background: '#fff',
                        color: STATUS_COLORS[s] || 'rgba(26,28,29,0.55)',
                      }}>
                      → {s === 'in_progress' ? 'In Progress' : s.charAt(0).toUpperCase() + s.slice(1)}
                    </button>
                  ))}
                </div>

                {/* Overdue warning */}
                {detailCommitment.overdue && (
                  <div style={{
                    background: 'rgba(209,69,59,0.08)', border: '1px solid rgba(209,69,59,0.2)',
                    borderRadius: 8, padding: '10px 14px', marginBottom: 20,
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}>
                    <span style={{ fontSize: 18 }}>⚠️</span>
                    <div>
                      <strong style={{ color: '#d1453b', fontSize: 13 }}>Overdue</strong>
                      <span style={{ color: '#d1453b', fontSize: 12, marginLeft: 8 }}>
                        {daysRelative(detailCommitment.due_at) !== null
                          ? `${Math.abs(daysRelative(detailCommitment.due_at)!)} day${Math.abs(daysRelative(detailCommitment.due_at)!) === 1 ? '' : 's'} past due`
                          : ''}
                      </span>
                    </div>
                  </div>
                )}

                {/* Info grid */}
                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 20,
                }}>
                  <div>
                    <label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', display: 'block', marginBottom: 2 }}>Owner</label>
                    <input value={editOwner} onChange={e => setEditOwner(e.target.value)}
                      style={{ width: '100%', padding: '6px 10px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13, outline: 'none', fontFamily: 'inherit' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', display: 'block', marginBottom: 2 }}>Due Date</label>
                    <input type="date" value={editDue} onChange={e => setEditDue(e.target.value)}
                      style={{ width: '100%', padding: '6px 10px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13, outline: 'none', fontFamily: 'inherit' }} />
                  </div>
                  <div>
                    <label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', display: 'block', marginBottom: 2 }}>Issue Type</label>
                    <select value={editType} onChange={e => setEditType(e.target.value)}
                      style={{ width: '100%', padding: '6px 10px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 13, outline: 'none', fontFamily: 'inherit' }}>
                      {ISSUE_TYPE_OPTIONS.map(t => (
                        <option key={t} value={t}>{t || '—'}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', display: 'block', marginBottom: 2 }}>Relationship</label>
                    <div style={{ padding: '6px 10px', fontSize: 13, color: 'rgba(26,28,29,0.55)' }}>
                      {detailCommitment.relationship_id ? `#${detailCommitment.relationship_id}` : '—'}
                    </div>
                  </div>
                </div>

                {/* Meta / Notes */}
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', display: 'block', marginBottom: 2 }}>
                    Notes (JSON meta)
                  </label>
                  <textarea value={editMeta} onChange={e => setEditMeta(e.target.value)}
                    rows={3}
                    style={{ width: '100%', padding: '6px 10px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 12, outline: 'none', fontFamily: 'monospace', resize: 'vertical' }} />
                </div>

                {/* Evidence / Note */}
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', display: 'block', marginBottom: 2 }}>
                    Evidence / Update Note
                  </label>
                  <textarea value={editEvidence} onChange={e => setEditEvidence(e.target.value)}
                    rows={2}
                    placeholder="What changed? Why was the status updated?"
                    style={{ width: '100%', padding: '6px 10px', border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6, fontSize: 12, outline: 'none', fontFamily: 'inherit', resize: 'vertical' }} />
                </div>

                {/* Save button */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
                  <button onClick={handleSaveDetail} disabled={editSaving}
                    style={{
                      padding: '8px 20px', background: '#1A1C1D', color: '#fff', border: 'none',
                      borderRadius: 6, fontSize: 13, cursor: 'pointer', opacity: editSaving ? 0.5 : 1,
                    }}>
                    {editSaving ? 'Saving…' : 'Save Changes'}
                  </button>
                </div>

                {/* Timeline */}
                {detailCommitment.timeline && detailCommitment.timeline.length > 0 && (
                  <div style={{ borderTop: '1px solid rgba(26,28,29,0.07)', paddingTop: 16 }}>
                    <h4 style={{ margin: '0 0 12px', fontSize: 13, fontWeight: 600, color: 'rgba(26,28,29,0.7)' }}>
                      Timeline
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {detailCommitment.timeline.map(t => (
                        <div key={t.id} style={{
                          display: 'flex', gap: 8, fontSize: 12, color: 'rgba(26,28,29,0.6)',
                        }}>
                          <span style={{ color: 'rgba(26,28,29,0.25)', flexShrink: 0 }}>
                            {t.event_time ? formatDate(t.event_time) : '—'}
                          </span>
                          <span>{t.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
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
.cmt-overdue-card {
  border-color: rgba(209,69,59,0.2);
}
.cmt-summary-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.cmt-overdue-card .cmt-summary-value { color: #d1453b; }
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
.cmt-item-critical {
  animation: cmt-pulse-overdue 2s ease-in-out infinite;
}
@keyframes cmt-pulse-overdue {
  0%, 100% { border-color: rgba(209,69,59,0.3); }
  50% { border-color: rgba(209,69,59,0.6); }
}
.cmt-modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
}
      `}</style>
    </div>
  );
};

export default CommitmentWorkspace;