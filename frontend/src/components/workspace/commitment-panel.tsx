/**
 * FDA19 — Commitment Fulfillment Panel
 *
 * Shows commitments, allows creation and state transitions.
 * Closes the loop between intent → commitment → plan → task → action → evidence → outcome.
 */
import { useState, type FC } from 'react';
import { createCommitment, transitionCommitment } from '../../api/workspace-api';

interface Props {
  commitments: any[];
  relationshipId?: number;
}

function statusColor(s: string): string {
  switch (s) {
    case 'pending': return '#f5a623';
    case 'in_progress': return '#60a5fa';
    case 'completed': return '#34d399';
    case 'failed': return '#f88';
    case 'blocked': return '#a78bfa';
    case 'cancelled': return '#888';
    default: return '#888';
  }
}

function nextTransitions(status: string): string[] {
  switch (status) {
    case 'pending': return ['in_progress', 'cancelled'];
    case 'in_progress': return ['completed', 'failed', 'blocked'];
    case 'blocked': return ['in_progress', 'cancelled'];
    default: return [];
  }
}

export const CommitmentPanel: FC<Props> = ({ commitments, relationshipId }) => {
  const [showNew, setShowNew] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newOwner, setNewOwner] = useState('');
  const [newDue, setNewDue] = useState('');
  const [creating, setCreating] = useState(false);
  const [localCommitments, setLocalCommitments] = useState(commitments);
  const [transitioning, setTransitioning] = useState<number | null>(null);

  const handleCreate = async () => {
    if (!newTitle.trim() || creating) return;
    setCreating(true);
    try {
      const resp = await createCommitment({
        title: newTitle.trim(),
        owner: newOwner.trim() || undefined,
        due_at: newDue || undefined,
        relationship_id: relationshipId,
      });
      if (resp.success && resp.data) {
        setLocalCommitments((prev) => [{ ...resp.data, due_at: newDue || null, owner: newOwner || null }, ...prev]);
        setNewTitle('');
        setNewOwner('');
        setNewDue('');
        setShowNew(false);
      }
    } catch {
      // ignore
    } finally {
      setCreating(false);
    }
  };

  const handleTransition = async (id: number, status: string) => {
    setTransitioning(id);
    try {
      const resp = await transitionCommitment(id, status);
      if (resp.success && resp.data) {
        setLocalCommitments((prev) =>
          prev.map((c) => (c.id === id ? { ...c, status, old_status: resp.data.old_status } : c))
        );
      }
    } catch {
      // ignore
    } finally {
      setTransitioning(null);
    }
  };

  // Sort commitments by status: pending first, then in_progress, then completed
  const sorted = [...localCommitments].sort((a, b) => {
    const order = ['pending', 'in_progress', 'blocked', 'failed', 'completed', 'cancelled'];
    return order.indexOf(a.status) - order.indexOf(b.status);
  });

  return (
    <div className="wksp-card wksp-commitments">
      <div className="wksp-card-title">
        Commitments ({localCommitments.length})
        {relationshipId && (
          <button className="wksp-commitment-add-btn" onClick={() => setShowNew(!showNew)}>
            {showNew ? 'Cancel' : '+ New'}
          </button>
        )}
      </div>

      {showNew && (
        <div className="wksp-commitment-new">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="What needs to be done?"
            className="wksp-commitment-input"
          />
          <div className="wksp-commitment-new-row">
            <input
              type="text"
              value={newOwner}
              onChange={(e) => setNewOwner(e.target.value)}
              placeholder="Owner (optional)"
              className="wksp-commitment-input wksp-commitment-input-sm"
            />
            <input
              type="date"
              value={newDue}
              onChange={(e) => setNewDue(e.target.value)}
              className="wksp-commitment-input wksp-commitment-input-sm"
            />
            <button className="wksp-commitment-create-btn" onClick={handleCreate} disabled={creating}>
              {creating ? 'Creating…' : 'Create'}
            </button>
          </div>
        </div>
      )}

      <div className="wksp-card-body wksp-commitment-list">
        {sorted.length === 0 && (
          <div className="wksp-commitment-empty">No commitments yet.</div>
        )}
        {sorted.map((c) => (
          <div key={c.id} className="wksp-commitment-item">
            <div className="wksp-commitment-item-header">
              <span className="wksp-commitment-title">{c.title}</span>
              <span className="wksp-commitment-badge" style={{ background: statusColor(c.status) + '22', color: statusColor(c.status) }}>
                {c.status}
              </span>
            </div>
            <div className="wksp-commitment-item-meta">
              {c.owner && <span>Owner: {c.owner}</span>}
              {c.due_at && <span>Due: {new Date(c.due_at).toLocaleDateString()}</span>}
            </div>
            {nextTransitions(c.status).length > 0 && (
              <div className="wksp-commitment-actions">
                {nextTransitions(c.status).map((s) => (
                  <button
                    key={s}
                    className="wksp-commitment-transition-btn"
                    onClick={() => handleTransition(c.id, s)}
                    disabled={transitioning === c.id}
                  >
                    {transitioning === c.id ? '…' : s === 'in_progress' ? '▶ Start' : s === 'completed' ? '✓ Complete' : s === 'failed' ? '✗ Fail' : s === 'blocked' ? '⊘ Block' : s === 'cancelled' ? '✕ Cancel' : s}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <style>{`
.wksp-commitments { max-height: 500px; overflow: hidden; display: flex; flex-direction: column; }
.wksp-card-title { display: flex; align-items: center; gap: 8px; }
.wksp-commitment-add-btn { margin-left: auto; font-size: 11px; padding: 2px 10px; background: var(--shunya-color-primary, #555); border: none; border-radius: 4px; color: #fff; cursor: pointer; }
.wksp-commitment-new { padding: 10px; border-bottom: 1px solid var(--shunya-surface-1, #222); display: flex; flex-direction: column; gap: 8px; }
.wksp-commitment-input { padding: 8px; background: var(--shunya-surface-3, #2a2a3a); border: 1px solid var(--shunya-surface-1, #222); border-radius: 4px; color: var(--shunya-text, #e0e0e0); font-size: 13px; }
.wksp-commitment-input-sm { flex: 1; }
.wksp-commitment-new-row { display: flex; gap: 6px; }
.wksp-commitment-create-btn { padding: 8px 14px; background: var(--shunya-color-primary, #555); border: none; border-radius: 4px; color: #fff; cursor: pointer; font-size: 13px; }
.wksp-commitment-create-btn:disabled { opacity: 0.5; }
.wksp-commitment-list { flex: 1; overflow-y: auto; }
.wksp-commitment-empty { font-size: 13px; color: var(--shunya-text-secondary, #888); text-align: center; padding: 20px; }
.wksp-commitment-item { padding: 10px; border-bottom: 1px solid var(--shunya-surface-1, #222); }
.wksp-commitment-item:last-child { border-bottom: none; }
.wksp-commitment-item-header { display: flex; align-items: center; gap: 6px; }
.wksp-commitment-title { font-size: 13px; font-weight: 500; color: var(--shunya-text, #e0e0e0); flex: 1; }
.wksp-commitment-badge { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 4px; text-transform: capitalize; }
.wksp-commitment-item-meta { display: flex; gap: 12px; font-size: 11px; color: var(--shunya-text-secondary, #888); margin-top: 4px; }
.wksp-commitment-actions { display: flex; gap: 4px; margin-top: 6px; }
.wksp-commitment-transition-btn { font-size: 11px; padding: 3px 8px; background: var(--shunya-surface-3, #2a2a3a); border: 1px solid var(--shunya-surface-1, #333); border-radius: 4px; color: var(--shunya-text-secondary, #aaa); cursor: pointer; }
.wksp-commitment-transition-btn:hover { background: var(--shunya-surface-4, #333350); color: var(--shunya-text, #e0e0e0); }
.wksp-commitment-transition-btn:disabled { opacity: 0.4; }
      `}</style>
    </div>
  );
};