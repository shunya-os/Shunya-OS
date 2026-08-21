/**
 * CommandToActionBridge — Connects intentions to executable actions.
 *
 * Shows the current SHUNYA recommendation from /api/v1/intention.
 * Allows the user to accept, dismiss, or execute the recommended action.
 * Shows action history.
 * Mobile-responsive.
 */

import { useState, useEffect, useCallback, type FC } from 'react';

interface IntentionSignal {
  type: string;
  label: string;
  object_name: string;
  object_type: string;
  detail: string;
  priority: number;
  count: number;
}

interface IntentionData {
  explanation: string;
  recommendation: {
    label: string;
    object_name: string;
    object_type: string;
    detail: string;
    priority: number;
  };
  signals: IntentionSignal[];
}

async function api<T>(path: string, opts?: RequestInit): Promise<T | null> {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return await r.json() as T;
  } catch { return null; }
}

interface ActionRecord {
  id: string;
  label: string;
  status: 'accepted' | 'executed' | 'dismissed';
  timestamp: string;
}

export const CommandToActionBridge: FC = () => {
  const [intention, setIntention] = useState<IntentionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionHistory, setActionHistory] = useState<ActionRecord[]>([]);
  const [executing, setExecuting] = useState(false);
  const [customInput, setCustomInput] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const result = await api<{ success: boolean; explanation: string; recommendation: any; signals: IntentionSignal[] }>('/api/v1/intention');
    if (result && result.success) {
      setIntention({
        explanation: result.explanation,
        recommendation: result.recommendation,
        signals: result.signals || [],
      });
    } else {
      setError('Could not load intention data');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAccept = async (label: string) => {
    setExecuting(true);
    const record: ActionRecord = {
      id: `act_${Date.now()}`,
      label,
      status: 'accepted',
      timestamp: new Date().toISOString(),
    };
    setActionHistory(prev => [record, ...prev]);
    try {
      const result = await api('/api/v1/outcomes', {
        method: 'POST',
        body: JSON.stringify({ intention: label }),
      });
      if (result) {
        setActionHistory(prev => prev.map(a =>
          a.id === record.id ? { ...a, status: 'executed' as const } : a
        ));
      }
    } catch { /* ignore */ }
    setExecuting(false);
    load();
  };

  const handleDismiss = (label: string) => {
    setActionHistory(prev => [{
      id: `act_${Date.now()}`,
      label,
      status: 'dismissed',
      timestamp: new Date().toISOString(),
    }, ...prev]);
  };

  const handleCustomSubmit = async () => {
    if (!customInput.trim()) return;
    setExecuting(true);
    const record: ActionRecord = {
      id: `act_${Date.now()}`,
      label: customInput.trim(),
      status: 'accepted',
      timestamp: new Date().toISOString(),
    };
    setActionHistory(prev => [record, ...prev]);
    setCustomInput('');
    try {
      const result = await api('/api/v1/outcomes', {
        method: 'POST',
        body: JSON.stringify({ intention: record.label }),
      });
      if (result) {
        setActionHistory(prev => prev.map(a =>
          a.id === record.id ? { ...a, status: 'executed' as const } : a
        ));
      }
    } catch { /* ignore */ }
    setExecuting(false);
    load();
  };

  return (
    <div className="pw-panel-container" style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 960 }}>
      <div className="pw-domain-header">
        <span className="pw-domain-icon">→</span>
        <h2 className="pw-domain-title">Actions</h2>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '0 0 20px' }}>
        SHUNYA's recommendations and your command execution
      </p>

      {/* Custom command input */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            placeholder="Type a command or ask SHUNYA to do something…"
            value={customInput}
            onChange={e => setCustomInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && customInput.trim() && !executing) handleCustomSubmit(); }}
            disabled={executing}
            style={{
              flex: 1, padding: '10px 14px', border: '1px solid rgba(26,28,29,0.12)',
              borderRadius: 8, fontSize: 14, outline: 'none', fontFamily: 'inherit',
              color: '#1A1C1D', background: '#fff',
            }}
          />
          <button onClick={handleCustomSubmit} disabled={!customInput.trim() || executing}
            style={{
              padding: '10px 20px', background: '#1A1C1D', color: '#fff',
              border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer',
              opacity: !customInput.trim() || executing ? 0.5 : 1,
            }}>
            {executing ? '…' : 'Execute'}
          </button>
        </div>
      </div>

      {/* Loading */}
      {loading && <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)' }}>Loading intentions…</div>}
      {error && <div style={{ padding: 40, textAlign: 'center', color: '#d1453b' }}>{error}</div>}

      {/* Current recommendation */}
      {!loading && !error && intention && intention.recommendation && intention.recommendation.label && (
        <div className="cab-recommendation" style={{
          background: 'linear-gradient(135deg, rgba(164,134,95,0.06), rgba(164,134,95,0.02))',
          border: '1px solid rgba(164,134,95,0.2)',
          borderRadius: 12, padding: 20, marginBottom: 20,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'rgba(164,134,95,0.1)', color: '#a4865f',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 16, flexShrink: 0,
            }}>✦</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#a4865f', marginBottom: 6 }}>
                SHUNYA Recommends
              </div>
              <div style={{ fontSize: 15, fontWeight: 500, color: '#1A1C1D', marginBottom: 4 }}>
                {intention.recommendation.label}
              </div>
              {intention.recommendation.detail && (
                <div style={{ fontSize: 13, color: 'rgba(26,28,29,0.55)', marginBottom: 8 }}>
                  {intention.recommendation.detail}
                </div>
              )}
              {intention.recommendation.object_name && (
                <div style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)', marginBottom: 12 }}>
                  Related to: {intention.recommendation.object_name} ({intention.recommendation.object_type})
                </div>
              )}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button onClick={() => handleAccept(intention.recommendation.label)} disabled={executing}
                  style={{ padding: '8px 20px', background: '#a4865f', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: executing ? 0.5 : 1 }}>
                  {executing ? 'Executing…' : 'Accept & Execute'}
                </button>
                <button onClick={() => handleDismiss(intention.recommendation.label)}
                  style={{ padding: '8px 20px', background: 'transparent', border: '1px solid rgba(26,28,29,0.07)', borderRadius: 6, fontSize: 13, cursor: 'pointer' }}>
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Signals */}
      {!loading && !error && intention && intention.signals && intention.signals.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, margin: '0 0 10px', color: 'rgba(26,28,29,0.55)' }}>Signals</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {intention.signals.map((s, i) => (
              <div key={i} className="cab-signal" style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 14px', background: '#fff',
                border: '1px solid rgba(26,28,29,0.06)', borderRadius: 8,
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: s.priority === 1 ? '#a4865f' : 'rgba(26,28,29,0.2)',
                  flexShrink: 0,
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 500, color: '#1A1C1D' }}>{s.label}</div>
                  {s.detail && <div style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)' }}>{s.detail}</div>}
                </div>
                <span style={{ fontSize: 10, color: 'rgba(26,28,29,0.35)', textTransform: 'uppercase' }}>{s.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action history */}
      {actionHistory.length > 0 && (
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, margin: '0 0 10px', color: 'rgba(26,28,29,0.55)' }}>Action History</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {actionHistory.map(a => (
              <div key={a.id} className="cab-history-item" style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 14px', background: '#fff',
                border: '1px solid rgba(26,28,29,0.06)', borderRadius: 8,
              }}>
                <span style={{
                  fontSize: 14,
                  color: a.status === 'executed' ? '#2e7d32' : a.status === 'dismissed' ? 'rgba(26,28,29,0.35)' : '#a4865f',
                }}>
                  {a.status === 'executed' ? '✓' : a.status === 'dismissed' ? '—' : '⟳'}
                </span>
                <span style={{ flex: 1, fontSize: 13, color: '#1A1C1D' }}>{a.label}</span>
                <span style={{
                  fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                  padding: '2px 8px', borderRadius: 4,
                  background: a.status === 'executed' ? 'rgba(46,125,50,0.08)' : a.status === 'dismissed' ? 'rgba(26,28,29,0.04)' : 'rgba(164,134,95,0.08)',
                  color: a.status === 'executed' ? '#2e7d32' : a.status === 'dismissed' ? 'rgba(26,28,29,0.35)' : '#a4865f',
                }}>
                  {a.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && (!intention || !intention.recommendation || !intention.recommendation.label) && actionHistory.length === 0 && (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <p style={{ color: 'rgba(26,28,29,0.55)' }}>No active recommendations.</p>
          <p style={{ fontSize: 13, color: 'rgba(26,28,29,0.45)', marginTop: 4 }}>
            Type a command above or wait for SHUNYA to generate recommendations.
          </p>
        </div>
      )}
    </div>
  );
};

export default CommandToActionBridge;