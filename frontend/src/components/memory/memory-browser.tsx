/**
 * MemoryBrowser — SHUNYA memory and knowledge browser.
 *
 * Reads from /api/v1/memory/entries and /api/v1/memory/knowledge.
 * Shows what SHUNYA remembers and knows.
 * Mobile-responsive.
 */

import { useState, useEffect, type FC } from 'react';

interface MemoryEntry {
  key: string;
  content: string;
  memory_type: string;
  source: string;
  confidence: number;
  timestamp: string;
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

export const MemoryBrowser: FC = () => {
  const [tab, setTab] = useState<'memory' | 'knowledge'>('memory');
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      const path = tab === 'memory' ? '/api/v1/memory/entries' : '/api/v1/memory/knowledge';
      const result = await api<{ success: boolean; data: { entries: MemoryEntry[] } }>(path);
      if (result?.success && result.data) {
        setEntries(result.data.entries || []);
      } else {
        setError('Could not load data');
      }
      setLoading(false);
    })();
  }, [tab]);

  return (
    <div className="pw-panel-container" style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">◈</span>
        <h2 className="pw-domain-title">Memory & Knowledge</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '0 0 20px' }}>
        What SHUNYA remembers and knows about your organization
      </p>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
        {(['memory', 'knowledge'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '6px 16px', borderRadius: 6, fontSize: 13, fontWeight: 500, cursor: 'pointer',
              border: `1px solid ${tab === t ? '#a4865f' : 'rgba(26,28,29,0.06)'}`,
              background: tab === t ? 'rgba(164,134,95,0.1)' : 'transparent',
              color: tab === t ? '#a4865f' : 'rgba(26,28,29,0.55)',
            }}>
            {t === 'memory' ? 'Memory' : 'Knowledge'}
          </button>
        ))}
      </div>

      {/* Summary */}
      {!loading && !error && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          <div className="mem-summary-card">
            <div className="mem-summary-value">{entries.length}</div>
            <div className="mem-summary-label">{tab === 'memory' ? 'Memory Entries' : 'Knowledge Items'}</div>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)' }}>Loading…</div>}
      {error && <div style={{ padding: 40, textAlign: 'center', color: '#d1453b' }}>{error}</div>}

      {/* Empty state */}
      {!loading && !error && entries.length === 0 && (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <p style={{ color: 'rgba(26,28,29,0.55)' }}>
            {tab === 'memory' ? 'No memory entries yet.' : 'No knowledge items yet.'}
          </p>
          <p style={{ fontSize: 13, color: 'rgba(26,28,29,0.45)', marginTop: 4 }}>
            {tab === 'memory'
              ? 'SHUNYA builds memory as it observes and interacts with the organization.'
              : 'Knowledge items appear as SHUNYA learns from interactions and data.'}
          </p>
        </div>
      )}

      {/* Entries */}
      {!loading && !error && entries.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {entries.map((e, i) => (
            <div key={i} className="mem-entry" style={{
              background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
              borderRadius: 10, padding: '14px 16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: e.confidence > 0.7 ? '#2e7d32' : e.confidence > 0.4 ? '#a4865f' : 'rgba(26,28,29,0.2)',
                  display: 'inline-block', flexShrink: 0,
                }} />
                <span style={{ flex: 1, fontSize: 14, fontWeight: 500, color: '#1A1C1D' }}>
                  {e.key}
                </span>
                <span style={{
                  fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                  padding: '2px 8px', borderRadius: 4,
                  background: 'rgba(26,28,29,0.04)', color: 'rgba(26,28,29,0.45)',
                }}>
                  {e.memory_type || 'general'}
                </span>
                <span style={{ fontSize: 11, color: 'rgba(26,28,29,0.35)' }}>
                  {Math.round(e.confidence * 100)}%
                </span>
              </div>
              {e.content && (
                <div style={{ fontSize: 12, color: 'rgba(26,28,29,0.55)', marginTop: 6, lineHeight: 1.4 }}>
                  {e.content}
                </div>
              )}
              <div style={{ display: 'flex', gap: 10, marginTop: 6, fontSize: 11, color: 'rgba(26,28,29,0.35)' }}>
                {e.source && <span>Source: {e.source}</span>}
                {e.timestamp && <span>{_timeAgo(e.timestamp)}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
.mem-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 80px;
}
.mem-summary-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.mem-summary-label { font-size: 11px; color: rgba(26,28,29,0.55); margin-top: 2px; }
      `}</style>
    </div>
  );
};

export default MemoryBrowser;