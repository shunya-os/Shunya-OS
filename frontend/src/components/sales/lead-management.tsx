/**
 * LeadManagement — Lead browser and management UI.
 *
 * Reads real lead data from /api/v1/leads/.
 * Shows: code, customer name, source, status, stage, budget, assigned_to.
 * Mobile-responsive.
 */

import { useState, useEffect, type FC } from 'react';

interface Lead {
  id: number;
  code: string;
  source: string;
  customer_name: string;
  phone: string;
  email: string;
  destination: string;
  budget: number;
  status: string;
  stage: string;
  assigned_to: string;
  outcome: string;
  notes: string;
  created_at: string | null;
}

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json() as T;
  } catch { return null; }
}

const STATUS_COLORS: Record<string, string> = {
  new: 'rgba(26,28,29,0.35)',
  contacted: '#a4865f',
  qualified: '#2e7d32',
  proposal: '#1a73e8',
  negotiation: '#c97b2d',
  won: '#2e7d32',
  lost: '#d1453b',
};

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

export const LeadManagement: FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    (async () => {
      setLoading(true);
      const result = await api<{ leads: Lead[] }>('/api/v1/leads/');
      if (result && result.leads) {
        setLeads(result.leads);
      } else {
        setError('Could not load leads');
      }
      setLoading(false);
    })();
  }, []);

  const filtered = filter === 'all'
    ? leads
    : filter === 'active'
      ? leads.filter(l => l.status !== 'converted' && l.status !== 'lost')
      : leads.filter(l => l.status === filter);

  const activeCount = leads.filter(l => l.status !== 'converted' && l.status !== 'lost').length;
  const qualifiedCount = leads.filter(l => l.status === 'qualified').length;

  return (
    <div style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 4 }}>
        <span style={{ fontSize: 20 }}>⬡</span>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>Leads</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '4px 0 20px' }}>
        Customer inquiries, prospects, and pipeline
      </p>

      {/* Summary */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="lead-summary-card">
          <div className="lead-summary-value">{leads.length}</div>
          <div className="lead-summary-label">Total</div>
        </div>
        <div className="lead-summary-card">
          <div className="lead-summary-value">{activeCount}</div>
          <div className="lead-summary-label">Active</div>
        </div>
        {qualifiedCount > 0 && (
          <div className="lead-summary-card">
            <div className="lead-summary-value" style={{ color: '#2e7d32' }}>{qualifiedCount}</div>
            <div className="lead-summary-label">Qualified</div>
          </div>
        )}
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {['all', 'active', 'new', 'contacted', 'qualified', 'converted', 'lost'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            style={{
              padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer',
              border: `1px solid ${filter === f ? '#a4865f' : 'rgba(26,28,29,0.06)'}`,
              background: filter === f ? 'rgba(164,134,95,0.1)' : 'transparent',
              color: filter === f ? '#a4865f' : 'rgba(26,28,29,0.55)',
            }}>
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading && <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)' }}>Loading leads…</div>}
      {error && <div style={{ padding: 40, textAlign: 'center', color: '#d1453b' }}>{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <p>{filter === 'all' ? 'No leads yet.' : `No ${filter} leads.`}</p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(l => (
            <div key={l.id} className="lead-item" style={{
              background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
              borderRadius: 10, padding: '14px 16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  backgroundColor: STATUS_COLORS[l.status] || 'rgba(26,28,29,0.35)',
                  display: 'inline-block', flexShrink: 0,
                }} />
                <span style={{ fontSize: 11, fontWeight: 600, color: 'rgba(26,28,29,0.35)', fontFamily: 'monospace' }}>{l.code}</span>
                <span style={{ flex: 1, fontSize: 14, fontWeight: 500, minWidth: 120 }}>{l.customer_name || 'Unknown'}</span>
                <span style={{
                  fontSize: 11, fontWeight: 500, textTransform: 'capitalize',
                  padding: '2px 8px', borderRadius: 6, background: 'rgba(26,28,29,0.04)', color: 'rgba(26,28,29,0.55)',
                }}>{l.stage || l.status}</span>
                <span style={{
                  fontSize: 11, fontWeight: 500, textTransform: 'uppercase',
                  color: STATUS_COLORS[l.status] || 'rgba(26,28,29,0.55)',
                }}>{l.status}</span>
              </div>
              <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6, fontSize: 11, color: 'rgba(26,28,29,0.45)' }}>
                <span>Source: {l.source}</span>
                {l.email && <span>{l.email}</span>}
                {l.destination && <span>Destination: {l.destination}</span>}
                {l.budget > 0 && <span>Budget: ${l.budget.toLocaleString()}</span>}
                {l.assigned_to && <span>Owner: {l.assigned_to}</span>}
                <span>Created: {_timeAgo(l.created_at)}</span>
              </div>
              {l.notes && <div style={{ fontSize: 11, color: 'rgba(26,28,29,0.55)', marginTop: 4, fontStyle: 'italic' }}>{l.notes}</div>}
            </div>
          ))}
        </div>
      )}

      <style>{`
.lead-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 80px;
}
.lead-summary-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.lead-summary-label { font-size: 11px; color: rgba(26,28,29,0.55); margin-top: 2px; }
      `}</style>
    </div>
  );
};

export default LeadManagement;