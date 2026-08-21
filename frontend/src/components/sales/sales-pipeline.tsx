/**
 * Sales Pipeline Workspace — Real pipeline data from /api/v1/sales/ endpoints.
 *
 * Shows: pipeline stage distribution, forecast, conversion analysis,
 * stalled leads, and lead scoring. Renders real data — no placeholders.
 */

import { useState, useEffect, type FC } from 'react';

interface PipelineHealth {
  total_leads: number;
  stage_distribution: Record<string, number>;
  stalled_count: number;
  stalled_leads: Array<{
    id: number; code: string; name: string;
    stage: string; days_since_creation: number; assigned_to: string | null;
  }>;
  unassigned: number;
}

interface Forecast {
  forecast_months: number;
  pipeline_value: string;
  qualified_count: number;
  expected_value: string;
  historical_conversion_rate: number;
  won_value: string;
  assumptions: string[];
}

interface ConversionAnalysis {
  total_leads: number;
  converted: number;
  lost: number;
  conversion_rate: number;
  loss_reasons: Record<string, number>;
  top_loss_reason: string | null;
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

function StageBar({ name, count, total }: { name: string; count: number; total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
        <span style={{ fontWeight: 500, textTransform: 'capitalize' }}>{name}</span>
        <span style={{ color: 'rgba(26,28,29,0.55)' }}>{count} ({Math.round(pct)}%)</span>
      </div>
      <div style={{
        height: 6, borderRadius: 3, background: 'rgba(26,28,29,0.06)',
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: pct > 50 ? '#2e7d32' : pct > 20 ? '#a4865f' : 'rgba(26,28,29,0.2)',
          borderRadius: 3, transition: 'width 0.3s ease',
        }} />
      </div>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{
      background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
      borderRadius: 10, padding: '16px 20px', flex: 1, minWidth: 120,
    }}>
      <div style={{ fontSize: 24, fontWeight: 700, color: color || 'var(--sh-text, #1A1C1D)' }}>{value}</div>
      <div style={{ fontSize: 12, color: 'rgba(26,28,29,0.55)', marginTop: 4 }}>{label}</div>
    </div>
  );
}

export const SalesPipeline: FC = () => {
  const [pipeline, setPipeline] = useState<PipelineHealth | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [conversion, setConversion] = useState<ConversionAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'pipeline' | 'forecast' | 'conversion'>('pipeline');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [p, f, c] = await Promise.all([
          api<{ data?: PipelineHealth }>('/api/v1/sales/pipeline'),
          api<{ data?: Forecast }>('/api/v1/sales/forecast'),
          api<{ data?: ConversionAnalysis }>('/api/v1/sales/conversion'),
        ]);
        if (p?.data) setPipeline(p.data);
        if (f?.data) setForecast(f.data);
        if (c?.data) setConversion(c.data);
      } catch { setError('Could not load sales data'); }
      setLoading(false);
    })();
  }, []);

  const totalLeads = pipeline?.total_leads ?? 0;

  return (
    <div className="pw-panel-container" style={{ padding: '24px 32px', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">⬡</span>
        <h2 className="pw-domain-title">Sales Pipeline</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '0 0 20px' }}>
        Deals, pipeline health, and revenue intelligence
      </p>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
        {(['pipeline', 'forecast', 'conversion'] as const).map(t => (
          <button
            key={t}
            className={`pw-tab-btn ${tab === t ? 'pw-tab-active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'pipeline' ? 'Pipeline' : t === 'forecast' ? 'Forecast' : 'Conversion'}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <div className="pw-domain-loading">Loading sales data…</div>}
      {error && <div className="pw-error-msg">{error}</div>}

      {/* ── PIPELINE TAB ── */}
      {!loading && tab === 'pipeline' && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            <MetricCard label="Total Leads" value={String(totalLeads)} />
            <MetricCard label="Unassigned" value={String(pipeline?.unassigned ?? 0)} color="#c97b2d" />
            <MetricCard label="Stalled" value={String(pipeline?.stalled_count ?? 0)} color="#d1453b" />
          </div>

          <h3 style={{ fontSize: 14, fontWeight: 600, margin: '0 0 12px' }}>Stage Distribution</h3>
          {pipeline && Object.entries(pipeline.stage_distribution).length > 0 ? (
            Object.entries(pipeline.stage_distribution).map(([stage, count]) => (
              <StageBar key={stage} name={stage} count={count} total={totalLeads} />
            ))
          ) : (
            <div className="pw-domain-empty"><p>No leads in pipeline yet.</p></div>
          )}

          {pipeline && pipeline.stalled_leads.length > 0 && (
            <>
              <h3 style={{ fontSize: 14, fontWeight: 600, margin: '16px 0 8px' }}>Stalled Leads (7+ days)</h3>
              {pipeline.stalled_leads.map(l => (
                <div key={l.id} className="pw-commercial-item" style={{ padding: '10px 12px', marginBottom: 6 }}>
                  <div style={{ fontWeight: 500, fontSize: 13 }}>{l.name}</div>
                  <div className="pw-commercial-item-meta" style={{ fontSize: 11 }}>
                    <span>Stage: {l.stage}</span>
                    <span>{l.days_since_creation} days stalled</span>
                    <span>{l.assigned_to || 'Unassigned'}</span>
                  </div>
                </div>
              ))}
            </>
          )}
        </>
      )}

      {/* ── FORECAST TAB ── */}
      {!loading && tab === 'forecast' && forecast && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            <MetricCard label="Pipeline Value" value={formatCurrency(forecast.pipeline_value)} />
            <MetricCard label="Expected Revenue" value={formatCurrency(forecast.expected_value)} />
            <MetricCard label="Conversion Rate" value={`${forecast.historical_conversion_rate}%`} />
            <MetricCard label="Won" value={formatCurrency(forecast.won_value)} color="#2e7d32" />
            <MetricCard label="Qualified Leads" value={String(forecast.qualified_count)} />
          </div>
          <div style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)', marginTop: 8 }}>
            <p style={{ margin: '0 0 4px' }}>Forecast assumptions:</p>
            {forecast.assumptions.map((a, i) => (
              <p key={i} style={{ margin: '0 0 2px 12px' }}>• {a}</p>
            ))}
          </div>
        </>
      )}

      {/* ── CONVERSION TAB ── */}
      {!loading && tab === 'conversion' && conversion && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            <MetricCard label="Total" value={String(conversion.total_leads)} />
            <MetricCard label="Converted" value={String(conversion.converted)} color="#2e7d32" />
            <MetricCard label="Lost" value={String(conversion.lost)} color="#d1453b" />
            <MetricCard label="Conversion Rate" value={`${conversion.conversion_rate}%`} />
          </div>
          {conversion.loss_reasons && Object.keys(conversion.loss_reasons).length > 0 && (
            <>
              <h3 style={{ fontSize: 14, fontWeight: 600, margin: '16px 0 8px' }}>Loss Reasons</h3>
              {Object.entries(conversion.loss_reasons).map(([reason, count]) => (
                <div key={reason} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '6px 0', borderBottom: '1px solid rgba(26,28,29,0.04)' }}>
                  <span style={{ textTransform: 'capitalize' }}>{reason}</span>
                  <span style={{ color: 'rgba(26,28,29,0.55)' }}>{count}</span>
                </div>
              ))}
            </>
          )}
          {conversion.top_loss_reason && (
            <p style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)', marginTop: 8 }}>
              Top reason for lost deals: <strong>{conversion.top_loss_reason}</strong>
            </p>
          )}
        </>
      )}

      {/* Combined empty state */}
      {!loading && !error && !pipeline && !forecast && !conversion && (
        <div className="pw-domain-empty"><p>No sales data available yet.</p></div>
      )}
    </div>
  );
};

export default SalesPipeline;