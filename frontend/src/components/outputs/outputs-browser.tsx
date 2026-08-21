/**
 * OutputsBrowser — Artifact and output discovery.
 *
 * Surfaces real canonical outputs: documents, proposals, execution results.
 * Each item shows type, status, source, and has a drill-down path.
 * Mobile-responsive via container queries.
 */

import { useState, useEffect, type FC } from 'react';

interface OutputItem {
  id: string;
  type: 'document' | 'proposal' | 'execution_result';
  title: string;
  description: string;
  status: string;
  source: string;
  mime_type?: string;
  file_size?: number;
  value?: number;
  currency?: string;
  has_artifact?: boolean;
  artifact_path?: string;
  created_at?: string | null;
  drilldown?: string;
}

async function api<T>(path: string): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include' });
    return await r.json() as T;
  } catch { return null; }
}

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

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const TYPE_ICONS: Record<string, string> = {
  document: '📄',
  proposal: '📋',
  execution_result: '✓',
};

const STATUS_COLORS: Record<string, string> = {
  received: 'rgba(26,28,29,0.35)',
  parsed: '#a4865f',
  ready: '#2e7d32',
  draft: 'rgba(26,28,29,0.35)',
  sent: '#1a73e8',
  accepted: '#2e7d32',
  completed: '#2e7d32',
  failed: '#d1453b',
};

export const OutputsBrowser: FC = () => {
  const [items, setItems] = useState<OutputItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const result = await api<{ success: boolean; data: { items: OutputItem[] } }>('/api/v1/execution/outputs');
        if (result?.success) {
          setItems(result.data.items || []);
        } else {
          setError('Could not load outputs');
        }
      } catch { setError('Failed to load'); }
      setLoading(false);
    })();
  }, []);

  const filtered = filter === 'all'
    ? items
    : items.filter(i => i.type === filter);

  const proposals = items.filter(i => i.type === 'proposal');
  const docs = items.filter(i => i.type === 'document');
  const results = items.filter(i => i.type === 'execution_result');

  return (
    <div className="pw-panel-container" style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">✓</span>
        <h2 className="pw-domain-title">Outputs</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '0 0 20px' }}>
        Artifacts, documents, and results produced by SHUNYA
      </p>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="out-summary-card">
          <div className="out-summary-value">{items.length}</div>
          <div className="out-summary-label">Total Outputs</div>
        </div>
        {docs.length > 0 && (
          <div className="out-summary-card">
            <div className="out-summary-value">{docs.length}</div>
            <div className="out-summary-label">Documents</div>
          </div>
        )}
        {proposals.length > 0 && (
          <div className="out-summary-card">
            <div className="out-summary-value">{proposals.length}</div>
            <div className="out-summary-label">Proposals</div>
          </div>
        )}
        {results.length > 0 && (
          <div className="out-summary-card">
            <div className="out-summary-value">{results.length}</div>
            <div className="out-summary-label">Results</div>
          </div>
        )}
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, flexWrap: 'wrap' }}>
        {['all', 'document', 'proposal', 'execution_result'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`out-filter-btn ${filter === f ? 'out-filter-active' : ''}`}
          >
            {f === 'all' ? 'All' : f === 'execution_result' ? 'Results' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <div className="out-loading">Loading outputs…</div>}
      {error && <div className="out-error">{error}</div>}

      {/* Empty state */}
      {!loading && !error && filtered.length === 0 && (
        <div className="out-empty">
          <p>No outputs yet.</p>
          <p className="out-empty-sub">Documents, proposals, and execution results appear here when SHUNYA produces them.</p>
        </div>
      )}

      {/* Output items */}
      {!loading && !error && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map((item) => (
            <div key={item.id} className="out-item">
              <div className="out-item-row">
                <span className="out-item-icon">{TYPE_ICONS[item.type] || '📎'}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="out-item-title">{item.title}</div>
                  {item.description && (
                    <div className="out-item-desc">{item.description.length > 200 ? item.description.slice(0, 200) + '…' : item.description}</div>
                  )}
                </div>
                <span className="out-item-status" style={{
                  color: STATUS_COLORS[item.status] || 'rgba(26,28,29,0.55)',
                }}>
                  {item.status}
                </span>
              </div>
              <div className="out-item-meta">
                <span>Type: {item.type === 'execution_result' ? 'Execution Result' : item.type.charAt(0).toUpperCase() + item.type.slice(1)}</span>
                <span>Source: {item.source}</span>
                {item.mime_type && <span>Format: {item.mime_type}</span>}
                {item.file_size && item.file_size > 0 && <span>Size: {formatSize(item.file_size)}</span>}
                {item.value && item.value > 0 && <span>Value: {item.currency || 'USD'} {item.value.toLocaleString()}</span>}
                {item.has_artifact && <span className="out-item-badge">Has artifact</span>}
                {item.created_at && <span>{_timeAgo(item.created_at)}</span>}
                {item.type === 'proposal' && (
                  <a href={`/api/v1/pdf/proposal/${item.id.replace('prop_', '')}`}
                    className="out-item-action" target="_blank" rel="noopener noreferrer"
                    title="Download as PDF">
                    PDF
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
.out-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 80px;
}
.out-summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #1A1C1D;
}
.out-summary-label {
  font-size: 11px;
  color: rgba(26,28,29,0.55);
  margin-top: 2px;
}
.out-loading { padding: 40px; text-align: center; color: rgba(26,28,29,0.55); }
.out-error { padding: 40px; text-align: center; color: #d1453b; }
.out-empty { padding: 40px; text-align: center; }
.out-empty-sub { font-size: 13px; color: rgba(26,28,29,0.45); }
.out-item-action {
  font-size: 11px; font-weight: 600; color: #a4865f; text-decoration: none;
  padding: 2px 8px; border: 1px solid rgba(164,134,95,0.2); border-radius: 4px;
}
.out-item-action:hover { background: rgba(164,134,95,0.06); }
.out-filter-btn {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid rgba(26,28,29,0.06);
  background: transparent;
  color: rgba(26,28,29,0.55);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}
.out-filter-active {
  border-color: #a4865f;
  background: rgba(164,134,95,0.1);
  color: #a4865f;
}
.out-item {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 16px;
  transition: box-shadow 0.15s;
}
.out-item:hover { box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.out-item-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.out-item-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}
.out-item-title {
  font-size: 14px;
  font-weight: 500;
  color: #1A1C1D;
  line-height: 1.3;
}
.out-item-desc {
  font-size: 12px;
  color: rgba(26,28,29,0.55);
  margin-top: 4px;
  line-height: 1.4;
}
.out-item-status {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.out-item-meta {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 8px;
  font-size: 11px;
  color: rgba(26,28,29,0.45);
}
.out-item-badge {
  background: rgba(46,125,50,0.08);
  color: #2e7d32;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}
      `}</style>
    </div>
  );
};

export default OutputsBrowser;