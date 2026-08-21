/**
 * ProposalDetail — Full detail view for a single proposal.
 *
 * Shows all proposal fields from the G4 CommercialProposal model:
 * scope, assumptions, exclusions, pricing, terms, timeline, status,
 * and lifecycle actions (accept/decline/transition).
 *
 * Data sourced from /api/v1/commercial/proposals/:id
 */
import { useState, useEffect, useCallback } from 'react';
import type { FC } from 'react';
import type { ProposalData } from './ProposalList';

interface ProposalDetailProps {
  proposalId: number;
  onBack: () => void;
  onUpdated?: (proposal: ProposalData) => void;
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft', ai_generating: 'AI Generating', review: 'In Review',
  sent: 'Sent', viewed: 'Viewed', negotiating: 'Negotiating',
  accepted: 'Accepted', declined: 'Declined', withdrawn: 'Withdrawn', expired: 'Expired',
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'rgba(26,28,29,0.55)', ai_generating: '#4a9e9e', review: '#e67e22',
  sent: '#2980b9', viewed: '#8e44ad', negotiating: '#e67e22',
  accepted: '#6a9f6a', declined: '#c0392b', withdrawn: 'rgba(26,28,29,0.35)', expired: 'rgba(26,28,29,0.35)',
};

async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    if (!r.ok) return null;
    return await r.json() as T;
  } catch { return null; }
}

async function apiPost<T>(path: string, body: unknown): Promise<T | null> {
  try {
    const r = await fetch(path, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return await r.json() as T;
  } catch { return null; }
}

function Section({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`proposal-section ${className || ''}`}>
      <h4 className="proposal-section-title">{title}</h4>
      <div className="proposal-section-body">{children}</div>
      <style>{`
.proposal-section { margin-bottom: 16px; }
.proposal-section-title {
  font-size: 10px; text-transform: uppercase;
  color: rgba(26,28,29,0.35);
  letter-spacing: 0.08em;
  margin: 0 0 6px 0;
  font-weight: 600;
}
.proposal-section-body { font-size: 13px; color: var(--shunya-text, #1A1C1D); line-height: 1.5; }
      `}</style>
    </div>
  );
}

export const ProposalDetail: FC<ProposalDetailProps> = ({ proposalId, onBack, onUpdated }) => {
  const [proposal, setProposal] = useState<ProposalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [transitioning, setTransitioning] = useState(false);
  const [transitionError, setTransitionError] = useState('');
  const [showTransitionForm, setShowTransitionForm] = useState(false);
  const [toState, setToState] = useState('');
  const [reason, setReason] = useState('');

  const loadProposal = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiGet<any>(`/api/v1/commercial/proposals/${proposalId}`);
      if (data && data.proposal) {
        setProposal(data.proposal);
      } else {
        setError('Proposal not found');
      }
    } catch { setError('Failed to load proposal'); }
    setLoading(false);
  }, [proposalId]);

  useEffect(() => { loadProposal(); }, [loadProposal]);

  const handleTransition = async () => {
    if (!proposal || !toState) return;
    setTransitioning(true);
    setTransitionError('');
    const result = await apiPost<any>(`/api/v1/commercial/proposals/${proposal.id}/transition`, {
      to_state: toState,
      reason: reason.trim(),
      triggered_by: 'Founder',
    });
    if (result && result.proposal) {
      setProposal(result.proposal);
      setShowTransitionForm(false);
      setToState('');
      setReason('');
      if (onUpdated) onUpdated(result.proposal);
    } else {
      setTransitionError(result?.error || 'Transition failed');
    }
    setTransitioning(false);
  };

  const availableTransitions: Record<string, string[]> = {
    draft: ['review', 'sent', 'withdrawn'],
    ai_generating: ['draft', 'review'],
    review: ['draft', 'sent', 'withdrawn'],
    sent: ['negotiating', 'accepted', 'declined', 'withdrawn', 'expired'],
    viewed: ['negotiating', 'accepted', 'declined', 'withdrawn'],
    negotiating: ['accepted', 'declined', 'sent', 'withdrawn'],
    accepted: ['withdrawn', 'expired'],
    declined: ['withdrawn'],
    withdrawn: ['draft'],
    expired: ['draft'],
  };

  if (loading) {
    return (
      <div className="proposal-detail">
        <div className="proposal-detail-top">
          <button className="pw-tab-btn" onClick={onBack}>← Back</button>
        </div>
        <div className="pw-domain-loading" style={{ padding: '20px 0' }}>Loading proposal…</div>
      </div>
    );
  }

  if (error || !proposal) {
    return (
      <div className="proposal-detail">
        <div className="proposal-detail-top">
          <button className="pw-tab-btn" onClick={onBack}>← Back</button>
        </div>
        <div className="pw-error-msg">{error || 'Proposal not found'}</div>
      </div>
    );
  }

  const statusColor = STATUS_COLORS[proposal.status] || 'rgba(26,28,29,0.55)';
  const transitions = availableTransitions[proposal.status] || [];

  return (
    <div className="proposal-detail">
      {/* Back + Actions */}
      <div className="proposal-detail-top">
        <button className="pw-tab-btn" onClick={onBack}>← Proposals</button>
        <div className="proposal-detail-top-actions">
          {!showTransitionForm && transitions.length > 0 && (
            <button className="pw-tab-btn" onClick={() => setShowTransitionForm(true)}>
              Change Status
            </button>
          )}
        </div>
      </div>

      {/* Title + Status */}
      <div className="proposal-detail-header">
        <h2 className="proposal-detail-title">{proposal.title}</h2>
        <div className="proposal-detail-badges">
          <span className="pw-commercial-tag proposal-detail-status" style={{
            background: `${statusColor}18`, color: statusColor,
            border: `1px solid ${statusColor}30`, fontWeight: 500,
          }}>
            {STATUS_LABELS[proposal.status] || proposal.status}
          </span>
          {proposal.proposal_type && (
            <span className="pw-commercial-tag">{proposal.proposal_type}</span>
          )}
          {proposal.version_number > 1 && (
            <span className="pw-commercial-tag">v{proposal.version_number}</span>
          )}
          {proposal.ai_generated && (
            <span className="pw-commercial-tag" style={{ color: '#4a9e9e' }}>🤖 AI-generated</span>
          )}
        </div>
      </div>

      {/* Value Summary */}
      <div className="proposal-value-summary">
        <div className="proposal-value-main">
          <span className="proposal-value-amount">
            {proposal.currency || 'INR'} {proposal.total_value?.toLocaleString('en-IN') || '0'}
          </span>
          <span className="proposal-value-label">Total Value</span>
        </div>
        {proposal.subtotal > 0 && (
          <div className="proposal-value-detail">
            <span>Subtotal: {proposal.currency || 'INR'} {proposal.subtotal?.toLocaleString('en-IN')}</span>
            {proposal.tax_amount > 0 && <span>Tax: {proposal.currency || 'INR'} {proposal.tax_amount?.toLocaleString('en-IN')}</span>}
            {proposal.discount_amount > 0 && <span>Discount: {proposal.currency || 'INR'} {proposal.discount_amount?.toLocaleString('en-IN')}</span>}
          </div>
        )}
      </div>

      {/* Transition form */}
      {showTransitionForm && (
        <div className="proposal-transition-form" style={{
          padding: 12, margin: '12px 0',
          border: '1px solid var(--shunya-gold, #a4865f)',
          borderRadius: 8, background: 'rgba(164,134,95,0.04)',
        }}>
          <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 500 }}>Change Status</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              {transitions.map(t => (
                <button
                  key={t}
                  className={`pw-tab-btn ${toState === t ? 'pw-tab-active' : ''}`}
                  onClick={() => setToState(t)}
                >
                  {STATUS_LABELS[t] || t}
                </button>
              ))}
            </div>
            <input
              type="text"
              placeholder="Reason for transition (optional)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              style={{
                padding: '6px 10px',
                border: '1px solid var(--shunya-border, rgba(26,28,29,0.12))',
                borderRadius: 6,
                fontFamily: 'inherit', fontSize: 13,
                background: 'var(--shunya-surface, #ffffff)',
                color: 'var(--shunya-text, #1A1C1D)',
              }}
            />
            {transitionError && <div style={{ color: '#c0392b', fontSize: 12 }}>{transitionError}</div>}
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="pw-tab-btn"
                style={{ background: 'var(--shunya-gold, #a4865f)', color: '#fff', borderColor: 'transparent' }}
                onClick={handleTransition}
                disabled={!toState || transitioning}
              >
                {transitioning ? 'Updating…' : `Set ${STATUS_LABELS[toState] || toState}`}
              </button>
              <button className="pw-tab-btn" onClick={() => {
                setShowTransitionForm(false);
                setTransitionError('');
                setToState('');
              }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fields */}
      <div className="proposal-detail-grid">
        {/* Left column */}
        <div className="proposal-detail-col">
          {proposal.scope_description && (
            <Section title="Scope">{proposal.scope_description}</Section>
          )}
          {proposal.assumptions && (
            <Section title="Assumptions">{proposal.assumptions}</Section>
          )}
          {proposal.exclusions && (
            <Section title="Exclusions">{proposal.exclusions}</Section>
          )}
          {proposal.delivery_timeline && (
            <Section title="Delivery Timeline">{proposal.delivery_timeline}</Section>
          )}
        </div>

        {/* Right column */}
        <div className="proposal-detail-col">
          {proposal.terms && (
            <Section title="Terms">{proposal.terms}</Section>
          )}
          {proposal.conditions && (
            <Section title="Conditions">{proposal.conditions}</Section>
          )}
          {proposal.decisions_required && proposal.decisions_required.length > 0 && (
            <Section title="Decisions Required">
              <ul className="proposal-decisions-list">
                {proposal.decisions_required.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </Section>
          )}
          {proposal.source_context && (
            <Section title="Source Context">{proposal.source_context}</Section>
          )}
        </div>
      </div>

      {/* Meta row */}
      <div className="proposal-detail-meta">
        <div>
          {proposal.valid_from && (
            <span>Valid from {new Date(proposal.valid_from).toLocaleDateString('en-IN')}</span>
          )}
          {proposal.valid_until && (
            <span> · Valid until {new Date(proposal.valid_until).toLocaleDateString('en-IN')}</span>
          )}
        </div>
        {proposal.created_by && (
          <div>Created by {proposal.created_by} on {new Date(proposal.created_at).toLocaleDateString('en-IN')}</div>
        )}
        {proposal.updated_by && (
          <div>Last updated by {proposal.updated_by}</div>
        )}
        {proposal.opportunity_id && (
          <div>Opportunity #{proposal.opportunity_id}</div>
        )}
        {proposal.decision_id && (
          <div>Decision: {proposal.decision_id}</div>
        )}
        {proposal.commitment_id && (
          <div>Commitment: {proposal.commitment_id}</div>
        )}
        {proposal.rejection_reason && (
          <div style={{ color: '#c0392b' }}>Rejection: {proposal.rejection_reason}</div>
        )}
      </div>

      <style>{`
.proposal-detail {
  display: flex;
  flex-direction: column;
}
.proposal-detail-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.proposal-detail-top-actions {
  display: flex;
  gap: 6px;
}
.proposal-detail-header {
  margin-bottom: 12px;
}
.proposal-detail-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  margin: 0 0 8px;
}
.proposal-detail-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.proposal-value-summary {
  background: var(--shunya-surface, #ffffff);
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 16px;
}
.proposal-value-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.proposal-value-amount {
  font-size: 22px;
  font-weight: 600;
  color: var(--shunya-text, #1A1C1D);
}
.proposal-value-label {
  font-size: 11px;
  color: rgba(26,28,29,0.45);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.proposal-value-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
  color: rgba(26,28,29,0.55);
}
.proposal-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 600px) {
  .proposal-detail-grid { grid-template-columns: 1fr; }
}
.proposal-detail-col {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.proposal-decisions-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.6;
}
.proposal-detail-meta {
  padding: 12px;
  border-top: 1px solid var(--shunya-border, rgba(26,28,29,0.07));
  font-size: 11px;
  color: rgba(26,28,29,0.45);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
      `}</style>
    </div>
  );
};