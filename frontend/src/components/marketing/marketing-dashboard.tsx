/**
 * MarketingDashboard — Aggregated marketing overview.
 *
 * Reads from /api/v1/growth/intelligence/overview and /api/v1/marketing/campaigns.
 * Shows: campaign summary, budget, active campaigns, interactions.
 * Mobile-responsive.
 */

import { useState, useEffect, type FC } from 'react';

interface Overview {
  active_campaigns: number;
  total_campaigns: number;
  total_budget: string;
  total_interactions: number;
  roi: string;
  total_attributed_revenue: string;
  total_learnings: number;
  actionable_learnings: number;
  campaigns_with_data: number;
}

interface Campaign {
  id: number;
  name: string;
  status: string;
  objective: string;
  budget: string;
  start_date: string | null;
  end_date: string | null;
}

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json() as T;
  } catch { return null; }
}

function formatCurrency(val: string | number): string {
  const n = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(n)) return String(val);
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
}

export const MarketingDashboard: FC = () => {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [ov, cmp] = await Promise.all([
          api<{ success: boolean; overview: Overview }>('/api/v1/growth/intelligence/overview'),
          api<{ campaigns: Campaign[] }>('/api/v1/marketing/campaigns'),
        ]);
        if (ov?.success) setOverview(ov.overview);
        if (cmp?.campaigns) setCampaigns(cmp.campaigns);
      } catch { setError('Could not load marketing data'); }
      setLoading(false);
    })();
  }, []);

  const activeCampaigns = campaigns.filter(c => c.status === 'active');

  return (
    <div style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 4 }}>
        <span style={{ fontSize: 20 }}>○</span>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>Marketing</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '4px 0 20px' }}>
        Campaigns, growth intelligence, and performance overview
      </p>

      {loading && <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)' }}>Loading marketing data…</div>}
      {error && <div style={{ padding: 40, textAlign: 'center', color: '#d1453b' }}>{error}</div>}

      {!loading && !error && overview && (
        <>
          {/* Summary cards */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            <div className="mkt-card">
              <div className="mkt-card-value">{overview.total_campaigns}</div>
              <div className="mkt-card-label">Total Campaigns</div>
            </div>
            <div className="mkt-card">
              <div className="mkt-card-value" style={{ color: '#2e7d32' }}>{overview.active_campaigns}</div>
              <div className="mkt-card-label">Active</div>
            </div>
            <div className="mkt-card">
              <div className="mkt-card-value">{formatCurrency(overview.total_budget)}</div>
              <div className="mkt-card-label">Total Budget</div>
            </div>
            <div className="mkt-card">
              <div className="mkt-card-value">{overview.total_interactions}</div>
              <div className="mkt-card-label">Interactions</div>
            </div>
            <div className="mkt-card">
              <div className="mkt-card-value">{overview.roi === '0.0' ? '—' : `${overview.roi}x`}</div>
              <div className="mkt-card-label">ROI</div>
            </div>
            <div className="mkt-card">
              <div className="mkt-card-value" style={{ color: overview.total_attributed_revenue !== '0.0' ? '#2e7d32' : 'rgba(26,28,29,0.35)' }}>
                {overview.total_attributed_revenue === '0.0' ? '—' : formatCurrency(overview.total_attributed_revenue)}
              </div>
              <div className="mkt-card-label">Attributed Revenue</div>
            </div>
          </div>

          {/* Active campaigns */}
          {activeCampaigns.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, margin: '0 0 10px' }}>Active Campaigns</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {activeCampaigns.map(c => (
                  <div key={c.id} className="mkt-campaign-row" style={{
                    background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
                    borderRadius: 10, padding: '12px 16px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ flex: 1, fontSize: 14, fontWeight: 500, minWidth: 120 }}>{c.name}</span>
                      <span style={{ fontSize: 11, textTransform: 'capitalize', color: 'rgba(26,28,29,0.55)' }}>{c.objective}</span>
                      {c.budget && <span style={{ fontSize: 12, fontWeight: 500, color: 'rgba(26,28,29,0.45)' }}>{formatCurrency(c.budget)}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Campaigns by status */}
          {campaigns.length > 0 && (
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 600, margin: '0 0 10px' }}>All Campaigns by Status</h3>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {['active', 'draft', 'completed', 'paused'].map(s => {
                  const count = campaigns.filter(c => c.status === s).length;
                  if (count === 0) return null;
                  return (
                    <div key={s} className="mkt-status-chip" style={{
                      padding: '8px 16px', borderRadius: 8,
                      background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
                    }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: s === 'active' ? '#2e7d32' : 'rgba(26,28,29,0.55)' }}>{count}</div>
                      <div style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', textTransform: 'capitalize' }}>{s}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Empty state for data */}
          {overview.total_interactions === 0 && overview.total_learnings === 0 && (
            <div style={{ marginTop: 20, padding: 24, background: 'rgba(26,28,29,0.02)', borderRadius: 10, textAlign: 'center' }}>
              <p style={{ fontSize: 13, color: 'rgba(26,28,29,0.45)' }}>
                Campaigns are set up. Interaction and attribution data will appear as campaigns receive engagement.
              </p>
            </div>
          )}
        </>
      )}

      <style>{`
.mkt-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 100px;
}
.mkt-card-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.mkt-card-label { font-size: 11px; color: rgba(26,28,29,0.55); margin-top: 2px; }
      `}</style>
    </div>
  );
};

export default MarketingDashboard;