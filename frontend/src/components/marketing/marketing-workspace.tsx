/**
 * MarketingWorkspace — Campaign browser and marketing domain surface.
 *
 * Fetches real campaign data from the marketing API and displays it
 * as an organized, actionable workspace. Supports campaign creation.
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

interface NewCampaign {
  name: string;
  description: string;
  objective: string;
  budget: string;
  status: string;
  start_date: string;
  end_date: string;
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

async function apiPost<T>(path: string, body: Record<string, unknown>): Promise<{ data?: T; error?: string }> {
  try {
    const r = await fetch(path, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return await r.json() as { data?: T; error?: string };
  } catch { return { error: 'Network error' }; }
}

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

// ── Campaign Create Form ─────────────────────────────────────────

function CampaignCreateForm({ onCreated, onCancel }: { onCreated: () => void; onCancel: () => void }) {
  const [form, setForm] = useState<NewCampaign>({
    name: '', description: '', objective: 'leads',
    budget: '0', status: 'draft', start_date: '', end_date: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: keyof NewCampaign, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) { setError('Campaign name is required'); return; }
    setSaving(true); setError('');
    const body: Record<string, unknown> = {
      name: form.name.trim(),
      description: form.description.trim(),
      objective: form.objective,
      budget: parseFloat(form.budget) || 0,
      status: form.status,
    };
    if (form.start_date) body.start_date = form.start_date;
    if (form.end_date) body.end_date = form.end_date;
    const result = await apiPost('/api/v1/marketing/campaigns', body);
    if (result.error) {
      setError(result.error);
      setSaving(false);
    } else {
      setSaving(false);
      onCreated();
    }
  };

  return (
    <div style={{
      background: 'var(--color-surface-elevated, #fff)',
      border: '1px solid var(--color-border, rgba(0,0,0,0.06))',
      borderRadius: 8, padding: 20, marginBottom: 16,
    }}>
      <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>New Campaign</h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <input placeholder="Campaign name *" value={form.name}
          onChange={e => handleChange('name', e.target.value)}
          style={inputStyle} />

        <textarea placeholder="Description" value={form.description} rows={2}
          onChange={e => handleChange('description', e.target.value)}
          style={{ ...inputStyle, resize: 'vertical' }} />

        <div style={{ display: 'flex', gap: 10 }}>
          <select value={form.objective} onChange={e => handleChange('objective', e.target.value)} style={{ ...inputStyle, flex: 1 }}>
            {Object.entries(OBJECTIVE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <select value={form.status} onChange={e => handleChange('status', e.target.value)} style={{ ...inputStyle, flex: 1 }}>
            {['draft', 'active', 'paused'].map(s => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <input placeholder="Budget (USD)" value={form.budget}
            onChange={e => handleChange('budget', e.target.value)}
            style={inputStyle} type="number" min="0" step="100" />
          <input placeholder="Start date" value={form.start_date}
            onChange={e => handleChange('start_date', e.target.value)}
            style={inputStyle} type="date" />
          <input placeholder="End date" value={form.end_date}
            onChange={e => handleChange('end_date', e.target.value)}
            style={inputStyle} type="date" />
        </div>
      </div>

      {error && <p style={{ color: '#d1453b', fontSize: 12, margin: '8px 0 0' }}>{error}</p>}

      <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
        <button onClick={handleSubmit} disabled={saving || !form.name.trim()}
          style={{ padding: '8px 20px', background: '#1A1C1D', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, cursor: 'pointer', opacity: saving || !form.name.trim() ? 0.5 : 1 }}>
          {saving ? 'Creating…' : 'Create Campaign'}
        </button>
        <button onClick={onCancel}
          style={{ padding: '8px 20px', background: 'transparent', border: '1px solid rgba(26,28,29,0.07)', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>
          Cancel
        </button>
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  padding: '8px 12px',
  border: '1px solid rgba(26,28,29,0.12)',
  borderRadius: 6,
  fontSize: 13,
  outline: 'none',
  fontFamily: 'inherit',
  color: '#1A1C1D',
  background: '#fff',
  width: '100%',
  boxSizing: 'border-box',
};

// ── Marketing Workspace ──────────────────────────────────────────

export const MarketingWorkspace: FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');
  const [showCreateForm, setShowCreateForm] = useState(false);

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

  const handleCreated = () => {
    setShowCreateForm(false);
    load();
  };

  const filtered = filter === 'all'
    ? campaigns
    : campaigns.filter(c => c.status === filter);

  const statusCounts = campaigns.reduce((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="pw-marketing-workspace" style={{ padding: '24px 32px', maxWidth: 960 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: 22, fontWeight: 600, color: 'var(--color-text-primary, #1a1c1d)' }}>
            Marketing
          </h2>
          <p style={{ margin: 0, fontSize: 14, color: 'var(--color-text-secondary, rgba(26,28,29,0.55))' }}>
            Campaigns, content, and growth intelligence
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          style={{
            padding: '8px 18px',
            background: showCreateForm ? 'transparent' : '#1A1C1D',
            color: showCreateForm ? 'rgba(26,28,29,0.55)' : '#fff',
            border: showCreateForm ? '1px solid rgba(26,28,29,0.07)' : 'none',
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          {showCreateForm ? 'Cancel' : '+ New Campaign'}
        </button>
      </div>

      {/* Create form */}
      {showCreateForm && (
        <CampaignCreateForm onCreated={handleCreated} onCancel={() => setShowCreateForm(false)} />
      )}

      {/* Summary cards */}
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
            {filter === 'all' ? 'No campaigns found. Click "+ New Campaign" to create one.' : `No ${filter} campaigns.`}
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