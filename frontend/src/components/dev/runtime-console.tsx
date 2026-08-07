/**
 * Runtime Dev Console — Development-only health and topology viewer.
 *
 * Shows: registered runtimes, dependency graph, runtime health,
 * startup order, event throughput, cache statistics.
 *
 * Only rendered when SHUNYA_DEV=true.
 */

import { useEffect, useState } from 'react';
import { orchestrator, type RuntimeStatus } from '../../runtimes/orchestrator';

interface ConsoleData {
  topology: { id: string; status: RuntimeStatus; deps: string[] }[];
  health: { total: number; ready: number; failed: number; initialising: number; stopped: number };
  chain: string;
}

export function RuntimeDevConsole() {
  const [data, setData] = useState<ConsoleData | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const refresh = () => {
      setData({
        topology: orchestrator.getTopology().map((t) => ({ id: t.id, status: t.status, deps: t.deps })),
        health: orchestrator.getAggregatedHealth(),
        chain: orchestrator.describeDependencyChain(),
      });
    };
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  if (typeof window !== 'undefined' && !(window as any).__SHUNYA_DEV) return null;

  return (
    <div style={{ position: 'fixed', bottom: 8, right: 8, zIndex: 9999, fontFamily: 'monospace', fontSize: 11 }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          background: data?.health.failed ? '#9B2226' : '#2D6A4F',
          color: '#fff',
          border: 'none',
          borderRadius: 4,
          padding: '2px 8px',
          cursor: 'pointer',
        }}
      >
        Runtimes: {data?.health.ready ?? 0}/{data?.health.total ?? 0}
        {data?.health.failed ? ` ⚠${data.health.failed}` : ''}
      </button>

      {open && data && (
        <div
          style={{
            position: 'absolute',
            bottom: 28,
            right: 0,
            width: 360,
            maxHeight: 400,
            overflow: 'auto',
            background: '#1A1A1E',
            color: '#E8E3DA',
            borderRadius: 8,
            padding: 12,
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 13 }}>Runtime Orchestrator</div>
          <div style={{ marginBottom: 6 }}>
            Status: {data.health.ready}/{data.health.total} ready
            {data.health.failed ? ` · ${data.health.failed} failed` : ''}
          </div>
          <div style={{ marginBottom: 8, whiteSpace: 'pre-wrap', fontSize: 10, opacity: 0.7 }}>
            Startup order:
            {data.chain}
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #38383E' }}>
                <th style={{ textAlign: 'left', padding: '2px 4px' }}>Runtime</th>
                <th style={{ textAlign: 'left', padding: '2px 4px' }}>Status</th>
                <th style={{ textAlign: 'left', padding: '2px 4px' }}>Dependencies</th>
              </tr>
            </thead>
            <tbody>
              {data.topology.map((t) => (
                <tr key={t.id} style={{ borderBottom: '1px solid #2D2D32' }}>
                  <td style={{ padding: '2px 4px' }}>{t.id}</td>
                  <td style={{ padding: '2px 4px' }}>
                    <span
                      style={{
                        color: t.status === 'ready' ? '#2D6A4F' : t.status === 'failed' ? '#9B2226' : '#E09F3E',
                      }}
                    >
                      {t.status}
                    </span>
                  </td>
                  <td style={{ padding: '2px 4px', opacity: 0.6 }}>{t.deps.join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
