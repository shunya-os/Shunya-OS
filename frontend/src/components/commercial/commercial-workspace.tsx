/**
 * Commercial Workspace — Real G4 Commercial drill-down.
 *
 * Shows opportunities, proposals, and commercial context
 * from the existing /api/v1/commercial/ API.
 *
 * Now uses dedicated ProposalList / ProposalDetail / ProposalEdit
 * components from the proposals/ directory for full proposal lifecycle.
 *
 * This is NOT a placeholder. It renders real data.
 */

import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { ProposalList, ProposalEdit } from '../proposals/index';
import { ProposalDetail } from '../proposals/ProposalDetail';
import type { ProposalData } from '../proposals/ProposalList';

interface Opportunity {
  id: number;
  title: string;
  lifecycle_state?: string;
  current_stage?: string;
  confidence: number;
  value?: number;
  currency?: string;
  description?: string;
  created_at: string;
  campaign_id?: number;
  estimated_value?: number;
  owner_identity_id?: string;
  next_action?: string;
  next_action_due_at?: string;
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

const OPPORTUNITY_STATE_LABELS: Record<string, string> = {
  discovered: 'Discovered', being_understood: 'Learning',
  active: 'Active', waiting: 'Waiting',
  proposal_pending: 'Proposal Sent', accepted: 'Accepted',
  declined: 'Declined', committed: 'Committed',
  executing: 'Executing', completed: 'Completed', lost: 'Lost',
};

const OPPORTUNITY_STATE_COLORS: Record<string, string> = {
  discovered: 'rgba(26,28,29,0.55)', being_understood: '#4a9e9e',
  active: '#6a9f6a', waiting: '#e67e22',
  proposal_pending: '#2980b9', accepted: '#6a9f6a',
  declined: '#c0392b', committed: '#6a9f6a',
  executing: '#6a9f6a', completed: 'rgba(26,28,29,0.45)', lost: '#c0392b',
};

type ViewState =
  | { mode: 'list' }
  | { mode: 'detail'; proposalId: number }
  | { mode: 'create' };

export const CommercialWorkspace: FC = () => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'opportunities' | 'proposals'>('proposals');
  const [view, setView] = useState<ViewState>({ mode: 'list' });

  // Create opportunity form
  const [showCreateOpp, setShowCreateOpp] = useState(false);
  const [newOppTitle, setNewOppTitle] = useState('');
  const [newOppValue, setNewOppValue] = useState<number | ''>('');
  const [newOppDesc, setNewOppDesc] = useState('');
  const [creatingOpp, setCreatingOpp] = useState(false);
  const [createOppError, setCreateOppError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [oppData] = await Promise.all([
        api<any>('/api/v1/commercial/opportunities'),
      ]);
      if (oppData) {
        setOpportunities(
          (oppData.opportunities || []).map((o: any) => ({
            ...o,
            current_stage: o.current_stage || o.lifecycle_state,
          }))
        );
      }
    } catch {
      setError('Could not load commercial data');
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const handleCreateOpportunity = async () => {
    const title = newOppTitle.trim();
    if (!title) {
      setCreateOppError('Title is required');
      return;
    }
    setCreatingOpp(true);
    setCreateOppError('');

    const result = await postApi<any>('/api/v1/commercial/opportunities', {
      title,
      description: newOppDesc.trim(),
      estimated_value: newOppValue || undefined,
    });

    if (result?.success) {
      setShowCreateOpp(false);
      setNewOppTitle('');
      setNewOppValue('');
      setNewOppDesc('');
      await loadData();
    } else {
      setCreateOppError(result?.error || 'Failed to create opportunity');
    }
    setCreatingOpp(false);
  };

  const handleSelectProposal = (proposal: ProposalData) => {
    setView({ mode: 'detail', proposalId: proposal.id });
  };

  const handleCreateProposal = () => {
    setView({ mode: 'create' });
  };

  const handleSaveProposal = (proposal: ProposalData) => {
    setView({ mode: 'detail', proposalId: proposal.id });
  };

  const handleBackToList = () => {
    setView({ mode: 'list' });
  };

  const handleProposalUpdated = () => {
    // Refresh proposals list when returning to list view
    // Detail view does its own reload
  };

  // Render proposal views
  if (view.mode === 'detail') {
    return (
      <div className="pw-panel-container">
        <div className="pw-domain-header">
          <span className="pw-domain-icon">◆</span>
          <h2 className="pw-domain-title">Proposal Details</h2>
        </div>
        <ProposalDetail
          proposalId={view.proposalId}
          onBack={handleBackToList}
          onUpdated={handleProposalUpdated}
        />
      </div>
    );
  }

  if (view.mode === 'create') {
    return (
      <div className="pw-panel-container">
        <div className="pw-domain-header">
          <span className="pw-domain-icon">◆</span>
          <h2 className="pw-domain-title">New Proposal</h2>
        </div>
        <ProposalEdit
          editing={null}
          onSave={handleSaveProposal}
          onCancel={handleBackToList}
        />
      </div>
    );
  }

  return (
    <div className="pw-panel-container">
      <div className="pw-domain-header">
        <span className="pw-domain-icon">◆</span>
        <h2 className="pw-domain-title">Commercial</h2>
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
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
          Proposals
        </button>
      </div>

      {loading && <div className="pw-domain-loading">Loading commercial data…</div>}
      {error && <div className="pw-error-msg">{error}</div>}

      {!loading && tab === 'opportunities' && (
        <div>
          <div className="pw-commercial-list">
            {opportunities.length === 0 && (
              <div className="pw-domain-empty"><p>No opportunities yet.</p></div>
            )}
            {opportunities.map((opp) => {
              const stateColor = OPPORTUNITY_STATE_COLORS[opp.lifecycle_state || opp.current_stage || ''] || 'rgba(26,28,29,0.55)';
              return (
                <div key={opp.id} className="pw-commercial-item">
                  <div className="pw-commercial-item-title">{opp.title}</div>
                  <div className="pw-commercial-item-meta">
                    <span className="pw-commercial-tag">Confidence: {opp.confidence}%</span>
                    {(opp.current_stage || opp.lifecycle_state) && (
                      <span className="pw-commercial-tag" style={{
                        background: `${stateColor}18`, color: stateColor,
                        border: `1px solid ${stateColor}30`, fontWeight: 500,
                      }}>
                        {OPPORTUNITY_STATE_LABELS[opp.lifecycle_state || opp.current_stage || ''] || opp.lifecycle_state || opp.current_stage}
                      </span>
                    )}
                    {((opp.estimated_value ?? opp.value) ?? 0) > 0 && (
                      <span className="pw-commercial-tag" style={{ fontWeight: 500 }}>
                        {opp.currency || 'INR'} {((opp.estimated_value ?? opp.value) ?? 0).toLocaleString('en-IN')}
                      </span>
                    )}
                    <span className="pw-commercial-date">Created: {new Date(opp.created_at).toLocaleDateString()}</span>
                  </div>
                  {opp.next_action && (
                    <div style={{ fontSize: 12, color: '#e67e22', marginTop: 4 }}>
                      Next: {opp.next_action}
                      {opp.next_action_due_at && ` (due ${new Date(opp.next_action_due_at).toLocaleDateString()})`}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {!showCreateOpp && (
            <button
              className="pw-tab-btn"
              style={{ marginTop: 8 }}
              onClick={() => setShowCreateOpp(true)}
            >
              + Create Opportunity
            </button>
          )}

          {showCreateOpp && (
            <div className="pw-commercial-item" style={{ marginTop: 8 }}>
              <div className="pw-commercial-item-title" style={{ marginBottom: 8 }}>
                New Opportunity
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <input
                  type="text"
                  placeholder="Opportunity title *"
                  value={newOppTitle}
                  onChange={(e) => setNewOppTitle(e.target.value)}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                    borderRadius: 6,
                    fontFamily: 'inherit', fontSize: 13,
                    background: 'var(--shunya-surface, #ffffff)',
                    color: 'var(--shunya-text, #1A1C1D)',
                  }}
                />
                <input
                  type="number"
                  placeholder="Estimated value"
                  value={newOppValue}
                  onChange={(e) => setNewOppValue(e.target.value ? Number(e.target.value) : '')}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                    borderRadius: 6,
                    fontFamily: 'inherit', fontSize: 13,
                    background: 'var(--shunya-surface, #ffffff)',
                    color: 'var(--shunya-text, #1A1C1D)',
                  }}
                />
                <textarea
                  placeholder="Description (optional)"
                  value={newOppDesc}
                  onChange={(e) => setNewOppDesc(e.target.value)}
                  rows={2}
                  style={{
                    padding: '6px 10px',
                    border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                    borderRadius: 6,
                    fontFamily: 'inherit', fontSize: 13,
                    background: 'var(--shunya-surface, #ffffff)',
                    color: 'var(--shunya-text, #1A1C1D)',
                    resize: 'vertical',
                  }}
                />
                {createOppError && <div style={{ color: '#c0392b', fontSize: 12 }}>{createOppError}</div>}
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    className="pw-tab-btn"
                    style={{ background: 'var(--shunya-gold, #a4865f)', color: '#fff', borderColor: 'transparent' }}
                    onClick={handleCreateOpportunity}
                    disabled={creatingOpp}
                  >
                    {creatingOpp ? 'Creating…' : 'Create'}
                  </button>
                  <button
                    className="pw-tab-btn"
                    onClick={() => { setShowCreateOpp(false); setCreateOppError(''); }}
                    disabled={creatingOpp}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {!loading && tab === 'proposals' && (
        <ProposalList
          onSelect={handleSelectProposal}
          onCreate={handleCreateProposal}
        />
      )}
    </div>
  );
};