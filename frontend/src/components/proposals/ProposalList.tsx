/**
 * ProposalList — Full-featured proposals list view.
 *
 * Shows all proposals from /api/v1/commercial/proposals with
 * status filtering, sorting by date/value, and drill-down to detail view.
 *
 * Manufactured for SHUNYA by G4 — real data, real routes.
 */
import { useState, useEffect, useCallback } from 'react';
import type { FC } from 'react';

export interface ProposalData {
  id: number;
  title: string;
  status: string;
  proposal_type: string;
  total_value: number;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  currency: string;
  scope_description: string;
  assumptions: string;
  exclusions: string;
  terms: string;
  conditions: string;
  opportunity_id: number | null;
  relationship_id: number | null;
  version_number: number;
  valid_from: string | null;
  valid_until: string | null;
  delivery_timeline: string;
  pricing_structure: any[];
  decisions_required: string[];
  source_context: string;
  ai_generated: boolean;
  evidence_refs: string[];
  rendered_pdf_path: string;
  sent_at: string | null;
  sent_via: string;
  viewed_at: string | null;
  accepted_at: string | null;
  decision_id: string | null;
  commitment_id: string | null;
  rejection_reason: string;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
  can_accept?: boolean;
  can_decline?: boolean;
}

interface ProposalListProps {
  onSelect: (proposal: ProposalData) => void;
  onCreate: () => void;
  compact?: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'rgba(26,28,29,0.55)',
  ai_generating: '#4a9e9e',
  review: '#e67e22',
  sent: '#2980b9',
  viewed: '#8e44ad',
  negotiating: '#e67e22',
  accepted: '#6a9f6a',
  declined: '#c0392b',
  withdrawn: 'rgba(26,28,29,0.35)',
  expired: 'rgba(26,28,29,0.35)',
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  ai_generating: 'AI Generating',
  review: 'In Review',
  sent: 'Sent',
  viewed: 'Viewed',
  negotiating: 'Negotiating',
  accepted: 'Accepted',
  declined: 'Declined',
  withdrawn: 'Withdrawn',
  expired: 'Expired',
};

const PROPOSAL_TYPE_ICONS: Record<string, string> = {
  proposal: '📋',
  offer: '🤝',
  quote: '💰',
  estimate: '📊',
};

async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    if (!r.ok) return null;
    return await r.json() as T;
  } catch { return null; }
}

export const ProposalList: FC<ProposalListProps> = ({ onSelect, onCreate, compact = false }) => {
  const [proposals, setProposals] = useState<ProposalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'value' | 'title'>('date');

  const loadProposals = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      params.set('limit', '100');
      const data = await apiGet<any>(`/api/v1/commercial/proposals?${params.toString()}`);
      if (data && data.proposals) {
        setProposals(data.proposals);
      } else {
        setProposals([]);
        if (!data) setError('Could not load proposals');
      }
    } catch {
      setError('Failed to load proposals');
    }
    setLoading(false);
  }, [statusFilter]);

  useEffect(() => { loadProposals(); }, [loadProposals]);

  const sorted = [...proposals].sort((a, b) => {
    if (sortBy === 'value') return (b.total_value || 0) - (a.total_value || 0);
    if (sortBy === 'title') return a.title.localeCompare(b.title);
    return new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime();
  });

  const statuses = Array.from(new Set(proposals.map(p => p.status))).sort();

  return (
    <div className="proposal-list">
      {/* Header */}
      <div className="proposal-list-header">
        <div className="proposal-list-header-left">
          <h3 className="proposal-list-title">Proposals ({proposals.length})</h3>
        </div>
        <div className="proposal-list-header-right">
          <button className="pw-tab-btn" onClick={onCreate}>
            + New Proposal
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="proposal-list-controls">
        <div className="proposal-list-filters">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="proposal-filter-select"
            aria-label="Filter by status"
          >
            <option value="">All Statuses</option>
            {statuses.map(s => (
              <option key={s} value={s}>{STATUS_LABELS[s] || s}</option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="proposal-filter-select"
            aria-label="Sort by"
          >
            <option value="date">Sort by Date</option>
            <option value="value">Sort by Value</option>
            <option value="title">Sort by Title</option>
          </select>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="pw-domain-loading" style={{ padding: '20px 0' }}>
          Loading proposals…
        </div>
      )}

      {/* Error */}
      {error && <div className="pw-error-msg">{error}</div>}

      {/* Empty */}
      {!loading && !error && sorted.length === 0 && (
        <div className="pw-domain-empty" style={{ padding: '20px 0' }}>
          <p>No proposals found.</p>
          {statusFilter && (
            <p style={{ marginTop: 4, fontSize: 12, color: 'rgba(26,28,29,0.45)' }}>
              Try clearing the status filter.
            </p>
          )}
        </div>
      )}

      {/* Proposal Cards */}
      {!loading && sorted.length > 0 && (
        <div className="proposal-list-items">
          {sorted.map((proposal) => {
            const statusColor = STATUS_COLORS[proposal.status] || 'rgba(26,28,29,0.55)';
            const typeIcon = PROPOSAL_TYPE_ICONS[proposal.proposal_type] || '📋';
            return (
              <div
                key={proposal.id}
                className="pw-commercial-item proposal-card"
                onClick={() => onSelect(proposal)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter') onSelect(proposal); }}
              >
                <div className="proposal-card-head">
                  <span className="proposal-type-icon" style={{ fontSize: 16, marginRight: 6 }}>
                    {typeIcon}
                  </span>
                  <span className="pw-commercial-item-title" style={{ flex: 1 }}>
                    {proposal.title}
                  </span>
                  {proposal.version_number > 1 && (
                    <span className="proposal-version-badge">v{proposal.version_number}</span>
                  )}
                </div>
                <div className="pw-commercial-item-meta" style={{ marginTop: 6 }}>
                  <span
                    className="pw-commercial-tag"
                    style={{
                      background: `${statusColor}18`,
                      color: statusColor,
                      fontWeight: 500,
                      border: `1px solid ${statusColor}30`,
                    }}
                  >
                    {STATUS_LABELS[proposal.status] || proposal.status}
                  </span>
                  {proposal.total_value != null && proposal.total_value > 0 && (
                    <span className="pw-commercial-tag" style={{ fontWeight: 500 }}>
                      {proposal.currency || 'INR'} {proposal.total_value.toLocaleString('en-IN')}
                    </span>
                  )}
                  <span className="pw-commercial-date">
                    {new Date(proposal.updated_at || proposal.created_at).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric',
                    })}
                  </span>
                </div>
                {proposal.scope_description && !compact && (
                  <div className="proposal-card-desc">
                    {proposal.scope_description.substring(0, 120)}
                    {proposal.scope_description.length > 120 ? '…' : ''}
                  </div>
                )}
                <div className="proposal-card-meta-row" style={{ marginTop: 6, display: 'flex', gap: 8, fontSize: 11, color: 'rgba(26,28,29,0.45)' }}>
                  {proposal.opportunity_id && <span>Opp #{proposal.opportunity_id}</span>}
                  {proposal.created_by && <span>by {proposal.created_by}</span>}
                  {proposal.ai_generated && <span style={{ color: '#4a9e9e' }}>🤖 AI-generated</span>}
                  {proposal.can_accept && <span style={{ color: '#6a9f6a' }}>✓ Ready to accept</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <style>{`
.proposal-card {
  cursor: pointer;
}
.proposal-card:focus-visible {
  outline: 2px solid var(--shunya-gold, #a4865f);
  outline-offset: 2px;
}
.proposal-card-head {
  display: flex;
  align-items: center;
  gap: 4px;
}
.proposal-version-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  background: rgba(26,28,29,0.04);
  color: rgba(26,28,29,0.45);
}
.proposal-card-desc {
  font-size: 12px;
  color: rgba(26,28,29,0.55);
  margin-top: 4px;
  line-height: 1.4;
}
.proposal-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.proposal-list-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.proposal-list-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--shunya-text, #1A1C1D);
  margin: 0;
}
.proposal-list-controls {
  margin-bottom: 12px;
}
.proposal-list-filters {
  display: flex;
  gap: 8px;
}
.proposal-filter-select {
  padding: 5px 10px;
  border: 1px solid var(--shunya-border, rgba(26,28,29,0.12));
  border-radius: 6px;
  font-family: inherit;
  font-size: 12px;
  background: var(--shunya-surface, #ffffff);
  color: var(--shunya-text, #1A1C1D);
  cursor: pointer;
}
      `}</style>
    </div>
  );
};