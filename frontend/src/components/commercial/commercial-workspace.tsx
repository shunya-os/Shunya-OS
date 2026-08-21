/**
 * Commercial Workspace — Real G4 Commercial drill-down.
 *
 * Shows opportunities, proposals, and commercial context
 * from the existing /api/v1/commercial/ API.
 *
 * This is NOT a placeholder. It renders real data.
 */

import { useState, useEffect } from 'react';
import type { FC } from 'react';

interface Opportunity {
  id: number;
  title: string;
  lifecycle_state?: string;
  current_stage?: string; // deprecated alias
  confidence: number;
  value?: number;
  currency?: string;
  description?: string;
  created_at: string;
  campaign_id?: number;
}

interface Proposal {
  id: number;
  title: string;
  status: string;
  total_value?: number;
  currency?: string;
  created_at: string;
  opportunity_id?: number;
}

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json() as T;
  } catch { return null; }
}

async function postApi<T>(path: string, body: unknown): Promise<T | null> {
  try {
    const r = await fetch(path, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return await r.json() as T;
  } catch { return null; }
}

export const CommercialWorkspace: FC = () => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'opportunities' | 'proposals'>('opportunities');

  // Create proposal form state
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newOppId, setNewOppId] = useState<number | ''>('');
  const [newValue, setNewValue] = useState<number | ''>('');
  const [newScope, setNewScope] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [oppData, propData] = await Promise.all([
        api<any>('/api/v1/commercial/opportunities'),
        api<any>('/api/v1/commercial/proposals'),
      ]);
      if (oppData) {
        setOpportunities(
          (oppData.opportunities || []).map((o: any) => ({
            ...o,
            current_stage: o.current_stage || o.lifecycle_state,
          }))
        );
      }
      if (propData) {
        setProposals(propData.proposals || []);
      }
    } catch {
      setError('Could not load commercial data');
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const handleCreateProposal = async () => {
    const title = newTitle.trim();
    if (!title) {
      setCreateError('Title is required');
      return;
    }
    setCreating(true);
    setCreateError('');

    const result = await postApi<any>('/api/v1/commercial/proposals', {
      title,
      opportunity_id: newOppId || undefined,
      total_value: newValue || undefined,
      scope_description: newScope.trim(),
    });

    if (result?.success) {
      setShowCreate(false);
      setNewTitle('');
      setNewOppId('');
      setNewValue('');
      setNewScope('');
      await loadData();
    } else {
      setCreateError(result?.error || 'Failed to create proposal');
    }
    setCreating(false);
  };

  return (
    <div className="pw-panel-container">
      <div className="pw-domain-header">
        <span className="pw-domain-icon">◆</span>
        <h2 className="pw-domain-title">Commercial</h2>
      </div>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px' }}>
        <button
          className={`pw-tab-btn ${tab === 'opportunities' ? 'pw-tab-active' : ''}`}
          onClick={() => setTab('opportunities')}
        >
          Opportunities ({opportunities.length})
        </button>
        <button
          className={`pw-tab-btn ${tab === 'proposals' ? 'pw-tab-active' : ''}`}
          onClick={() => setTab('proposals')}
        >
          Proposals ({proposals.length})
        </button>
      </div>

      {loading && <div className="pw-domain-loading">Loading commercial data…</div>}
      {error && <div className="pw-error-msg">{error}</div>}

      {!loading && tab === 'opportunities' && (
        <div className="pw-commercial-list">
          {opportunities.length === 0 && <div className="pw-domain-empty"><p>No opportunities yet.</p></div>}
          {opportunities.map((opp) => (
            <div key={opp.id} className="pw-commercial-item">
              <div className="pw-commercial-item-title">{opp.title}</div>
              <div className="pw-commercial-item-meta">
                <span className="pw-commercial-tag">Confidence: {opp.confidence}%</span>
                {(opp.current_stage || opp.lifecycle_state) && (
                  <span className="pw-commercial-tag">Stage: {opp.current_stage || opp.lifecycle_state}</span>
                )}
                <span className="pw-commercial-date">Created: {new Date(opp.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && tab === 'proposals' && (
        <div>
          <div className="pw-commercial-list" style={{ marginBottom: 12 }}>
            {proposals.length === 0 && <div className="pw-domain-empty"><p>No proposals yet.</p></div>}
            {proposals.map((prop) => (
              <div key={prop.id} className="pw-commercial-item">
                <div className="pw-commercial-item-title">{prop.title}</div>
                <div className="pw-commercial-item-meta">
                  <span className={`pw-commercial-tag pw-status-${prop.status}`}>{prop.status}</span>
                  {prop.total_value != null && prop.total_value > 0 && (
                    <span className="pw-commercial-tag">{prop.currency || 'INR'} {prop.total_value.toLocaleString()}</span>
                  )}
                  <span className="pw-commercial-date">{new Date(prop.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>

          {!showCreate && (
            <button
              className="pw-tab-btn"
              style={{ marginTop: 4 }}
              onClick={() => setShowCreate(true)}
            >
              + Create Proposal
            </button>
          )}

          {showCreate && (
            <div className="pw-commercial-item" style={{ marginTop: 8 }}>
              <div className="pw-commercial-item-title" style={{ marginBottom: 8 }}>New Proposal</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <input
                  type="text"
                  placeholder="Proposal title *"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                    borderRadius: 6,
                    fontFamily: 'inherit',
                    fontSize: 13,
                    background: 'var(--shunya-surface, #ffffff)',
                    color: 'var(--shunya-text, #1A1C1D)',
                  }}
                />
                <select
                  value={newOppId}
                  onChange={(e) => setNewOppId(e.target.value ? Number(e.target.value) : '')}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                    borderRadius: 6,
                    fontFamily: 'inherit',
                    fontSize: 13,
                    background: 'var(--shunya-surface, #ffffff)',
                    color: 'var(--shunya-text, #1A1C1D)',
                  }}
                >
                  <option value="">— No opportunity —</option>
                  {opportunities.map((opp) => (
                    <option key={opp.id} value={opp.id}>{opp.title}</option>
                  ))}
                </select>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="number"
                    placeholder="Total value"
                    value={newValue}
                    onChange={(e) => setNewValue(e.target.value ? Number(e.target.value) : '')}
                    style={{
                      flex: 1,
                      padding: '6px 10px',
                      border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                      borderRadius: 6,
                      fontFamily: 'inherit',
                      fontSize: 13,
                      background: 'var(--shunya-surface, #ffffff)',
                      color: 'var(--shunya-text, #1A1C1D)',
                    }}
                  />
                </div>
                <textarea
                  placeholder="Scope description (optional)"
                  value={newScope}
                  onChange={(e) => setNewScope(e.target.value)}
                  rows={2}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                    borderRadius: 6,
                    fontFamily: 'inherit',
                    fontSize: 13,
                    background: 'var(--shunya-surface, #ffffff)',
                    color: 'var(--shunya-text, #1A1C1D)',
                    resize: 'vertical',
                  }}
                />
                {createError && <div style={{ color: '#c0392b', fontSize: 12 }}>{createError}</div>}
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    className="pw-tab-btn"
                    style={{ background: 'var(--shunya-gold, #a4865f)', color: '#fff', borderColor: 'transparent' }}
                    onClick={handleCreateProposal}
                    disabled={creating}
                  >
                    {creating ? 'Creating…' : 'Create'}
                  </button>
                  <button
                    className="pw-tab-btn"
                    onClick={() => { setShowCreate(false); setCreateError(''); }}
                    disabled={creating}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};