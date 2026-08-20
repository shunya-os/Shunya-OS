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
  current_stage: string;
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
  current_stage: string;
  total_value?: number;
  created_at: string;
  opportunity_id?: number;
}

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json() as T;
  } catch { return null; }
}

export const CommercialWorkspace: FC = () => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'opportunities' | 'proposals'>('opportunities');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [oppData, propData] = await Promise.all([
          api<any>('/api/v1/commercial/opportunities'),
          api<any>('/api/v1/commercial/proposals'),
        ]);
        if (oppData) setOpportunities(oppData.opportunities || []);
        if (propData) setProposals(propData.proposals || []);
      } catch {
        setError('Could not load commercial data');
      }
      setLoading(false);
    })();
  }, []);

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
                {opp.current_stage && <span className="pw-commercial-tag">Stage: {opp.current_stage}</span>}
                <span className="pw-commercial-date">Created: {new Date(opp.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && tab === 'proposals' && (
        <div className="pw-commercial-list">
          {proposals.length === 0 && <div className="pw-domain-empty"><p>No proposals yet.</p></div>}
          {proposals.map((prop) => (
            <div key={prop.id} className="pw-commercial-item">
              <div className="pw-commercial-item-title">{prop.title}</div>
              <div className="pw-commercial-item-meta">
                <span className={`pw-commercial-tag pw-status-${prop.status}`}>{prop.status}</span>
                {prop.current_stage && <span className="pw-commercial-tag">Stage: {prop.current_stage}</span>}
                <span className="pw-commercial-date">{new Date(prop.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};