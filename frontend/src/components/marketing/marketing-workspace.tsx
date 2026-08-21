/**
 * MarketingWorkspace — Campaign browser and marketing domain surface.
 *
 * Fetches real campaign data from the marketing API and displays it
 * as an organized, actionable workspace.
 */

import { useState, useEffect, useCallback, type FC } from 'react';

interface Campaign {
  id: number;
  name: string;
  description: string;
  status: string;
  objective: string;
  budget: string;
  budget_type: string;
  start_date: string | null;
  end_date: string | null;
  owner: string | null;
  created_by: string;
  created_at: string;
  utm_campaign: string;
  utm_medium: string;
  utm_source: string;
}

const STATUS_COLORS: Record<string, string> = {
  active: '#2e7d32',
  draft: 'rgba(26,28,29,0.35)',
  completed: '#1a73e8',
  paused: '#c97b2d',
  archived: '#d1453b',
};

const OBJECTIVE_LABELS: Record<string, string> = {
  conversions: 'Conversions',
  engagement: 'Engagement',
  awareness: 'Awareness',
  sales: 'Sales',
  leads: 'Leads',
  retention: 'Retention',
};

function formatCurrency(val: string): string {
  const n = parseFloat(val);
  if (isNaN(n)) return val;
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
}

function formatDate(val: string | null): string {
  if (!val) return '—';
  try {
    return new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return val; }
}

// ── Campaign Card ────────────────────────────────────────────────

const CampaignCard: FC<{ campaign: Campaign }> = ({ campaign }) => (
  <div className="pw-campaign-card" style={{
    background: 'var(--color-surface-elevated, #fff)',
    border: '1px solid var(--color-border, rgba(0,0,0,0.06))',
    borderRadius: 8,
    padding: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    cursor: 'pointer',
    transition: 'box-shadow 0.15s ease',
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: 'var(--color-text-primary, #1a1c1d)' }}>
        {campaign.name}
      </h3>
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        fontSize: 11,
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: STATUS_COLORS[campaign.status] || 'rgba(26,28,29,0.55)',
      }}>
        <span style={{
          width: 6, height: 6, borderRadius: '50%',
          backgroundColor: STATUS_COLORS[campaign.status] || 'rgba(26,28,29,0.35)',
          display: 'inline-block',
        }} />
        {campaign.status}
      </span>
    </div>
    {campaign.description && (
      <p style={{ margin: 0, fontSize: 13, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))', lineHeight: 1.4 }}>
        {campaign.description}
      </p>
    )}
    <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>
      <span>Objective: {OBJECTIVE_LABELS[campaign.objective] || campaign.objective}</span>
      {campaign.budget && <span>Budget: {formatCurrency(campaign.budget)}</span>}
    </div>
    <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--color-text-tertiary, rgba(26,28,29,0.35))' }}>
      {campaign.start_date && <span>Start: {formatDate(campaign.start_date)}</span>}
      {campaign.end_date && <span>End: {formatDate(campaign.end_date)}</span>}
    </div>
  </div>
);

// ── Marketing Workspace ──────────────────────────────────────────

export const MarketingWorkspace: FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const r = await fetch('/api/v1/marketing/campaigns', { credentials: 'include' });
      const data = await r.json();
      if (data.campaigns) {
        setCampaigns(data.campaigns);
      } else {
        setError('Unexpected response format');
      }
    } catch (e) {
      setError('Failed to load campaigns');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = filter === 'all'
    ? campaigns
    : campaigns.filter(c => c.status === filter);

  const statusCounts = campaigns.reduce((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="pw-marketing-workspace" style={{ padding: '24px 32px', maxWidth: 960 }}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: '0 0 4px 0', fontSize: 22, fontWeight: 600, color: 'var(--color-text-primary, #1a1c1d)' }}>
          Marketing
        </h2>
        <p style={{ margin: 0, fontSize: 14, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>
          Campaigns, content, and growth intelligence
        </p>
      </div>

      {/* Summary */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{
          background: 'var(--color-surface-elevated, #fff)',
          border: '1px solid var(--color-border, rgba(0,0,0,0.06))',
          borderRadius: 8, padding: '12px 20px', flex: 1, minWidth: 120,
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-text-primary, #1a1c1d)' }}>{campaigns.length}</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>Total Campaigns</div>
        </div>
        <div style={{
          background: 'var(--color-surface-elevated, #fff)',
          border: '1px solid var(--color-border, rgba(0,0,0,0.06))',
          borderRadius: 8, padding: '12px 20px', flex: 1, minWidth: 120,
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#2e7d32' }}>{statusCounts['active'] || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>Active</div>
        </div>
        <div style={{
          background: 'var(--color-surface-elevated, #fff)',
          border: '1px solid var(--color-border, rgba(0,0,0,0.06))',
          borderRadius: 8, padding: '12px 20px', flex: 1, minWidth: 120,
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: 'rgba(26,28,29,0.35)' }}>{statusCounts['draft'] || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>Drafts</div>
        </div>
        <div style={{
          background: 'var(--color-surface-elevated, #fff)',
          border: '1px solid var(--color-border, rgba(0,0,0,0.06))',
          borderRadius: 8, padding: '12px 20px', flex: 1, minWidth: 120,
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#1a73e8' }}>{statusCounts['completed'] || 0}</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>Completed</div>
        </div>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['all', 'active', 'draft', 'completed', 'paused'].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              padding: '4px 12px',
              borderRadius: 6,
              border: `1px solid ${filter === s ? 'var(--color-accent, #a4865f)' : 'var(--color-border, rgba(0,0,0,0.06))'}`,
              background: filter === s ? 'var(--color-accent-subtle, rgba(164,134,95,0.1))' : 'transparent',
              color: filter === s ? 'var(--color-accent, #a4865f)' : 'var(--color-text-secondary, rgba(26,28,29,0.55))',
              fontSize: 12, fontWeight: 500, cursor: 'pointer',
            }}
          >
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading && (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>
          Loading campaigns…
        </div>
      )}

      {error && (
        <div style={{ padding: 40, textAlign: 'center', color: '#d1453b' }}>
          {error}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="pw-domain-empty" style={{ padding: 40, textAlign: 'center' }}>
          <p style={{ color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>
            {filter === 'all' ? 'No campaigns found. Create a campaign to get started.' : `No ${filter} campaigns.`}
          </p>
          <p style={{ fontSize: 13, color: 'var(--color-text-tertiary, rgba(26,28,29,0.35))' }}>
            Marketing capability (G5) is ready. Campaigns can be created through SHUNYA.
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map(campaign => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))}
        </div>
      )}
    </div>
  );
};

export default MarketingWorkspace;