/**
 * AuditViewer — D-09 Audit Trail Visibility UI.
 *
 * Lists recent audit log entries from /api/v1/audit/list and supports
 * pagination. Each entry shows who did what to which resource, when.
 * Clicking an entry navigates to the object workspace for full reconstruction.
 */
import { useState, useEffect, useCallback } from 'react';
import { useWorkspaceStore } from '../../runtimes/workspace/store';

/* ── Types ─────────────────────────────────────────────────── */

interface AuditEntry {
  id: number;
  timestamp: string | null;
  identity_id: string;
  workspace_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  ip_address: string;
  user_agent: string;
  details: Record<string, unknown>;
}

interface AuditListResponse {
  success: boolean;
  data?: {
    logs: AuditEntry[];
    total: number;
    limit: number;
    offset: number;
  };
  error?: string;
}

/* ── Helpers ───────────────────────────────────────────────── */

function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function actionColor(action: string): string {
  switch (action.toLowerCase()) {
    case 'create': return '#2D6A4F';
    case 'update': return '#6C4AE2';
    case 'delete': return '#B91C1C';
    case 'approve': return '#16A34A';
    case 'reject': return '#DC2626';
    case 'authorize': return '#0891B2';
    default: return '#A4865F';
  }
}

/* ── Component ─────────────────────────────────────────────── */

export function AuditViewer() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const limit = 50;

  const fetchLogs = useCallback(async (newOffset: number) => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/v1/audit/list?limit=${limit}&offset=${newOffset}`, {
        credentials: 'include',
      });
      const body: AuditListResponse = await r.json();
      if (body.success && body.data) {
        let items = body.data.logs;
        if (filter !== 'all') {
          items = items.filter(l => l.action === filter);
        }
        setLogs(items);
        setTotal(body.data.total);
        setOffset(newOffset);
      } else {
        setError(body.error || 'Failed to load audit logs');
      }
    } catch (err: any) {
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchLogs(0);
  }, [fetchLogs]);

  const navigateToObject = (entry: AuditEntry) => {
    const ws = useWorkspaceStore.getState();
    ws.open(`${entry.resource_type} #${entry.resource_id}`, 'object', {
      objectType: entry.resource_type,
      objectId: entry.resource_id,
    });
  };

  const totalPages = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="av-container">
      {/* Header */}
      <div className="av-header">
        <div className="av-header-left">
          <div className="av-header-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6C4AE2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
          </div>
          <div>
            <div className="av-header-title">Audit Trail</div>
            <div className="av-header-sub">Governed event log with full provenance ({total} entries)</div>
          </div>
        </div>
        <div className="av-header-right">
          <span className="av-filter-label">Action:</span>
          <select className="av-filter-select" value={filter} onChange={e => { setFilter(e.target.value); setOffset(0); }}>
            <option value="all">All</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="approve">Approve</option>
            <option value="reject">Reject</option>
            <option value="authorize">Authorize</option>
          </select>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="av-loading">
          <div className="av-spinner" />
          <span>Loading audit trail…</span>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="av-error">
          <div className="av-error-icon">⚠</div>
          <div className="av-error-msg">{error}</div>
          <button className="av-retry-btn" onClick={() => fetchLogs(offset)}>Retry</button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && logs.length === 0 && (
        <div className="av-empty">
          <div className="av-empty-icon">📋</div>
          <div className="av-empty-text">No audit entries recorded yet.</div>
          <div className="av-empty-hint">Audit entries are created automatically when objects are created, updated, or deleted.</div>
        </div>
      )}

      {/* Table */}
      {!loading && !error && logs.length > 0 && (
        <>
          <div className="av-table-wrapper">
            <table className="av-table">
              <thead>
                <tr>
                  <th style={{ width: '36px' }}>#</th>
                  <th>Timestamp</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Resource</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(entry => (
                  <tr key={entry.id} className="av-row" onClick={() => navigateToObject(entry)} title="Click to view object workspace">
                    <td className="av-cell-id">{entry.id}</td>
                    <td className="av-cell-time">{formatTime(entry.timestamp)}</td>
                    <td className="av-cell-actor">{entry.identity_id}</td>
                    <td>
                      <span className="av-action-badge" style={{ background: `${actionColor(entry.action)}18`, color: actionColor(entry.action), borderColor: `${actionColor(entry.action)}30` }}>
                        {entry.action}
                      </span>
                    </td>
                    <td className="av-cell-resource">
                      <span className="av-resource-type">{entry.resource_type}</span>
                      <span className="av-resource-id">#{entry.resource_id || '—'}</span>
                    </td>
                    <td className="av-cell-details">
                      {entry.details && Object.keys(entry.details).length > 0
                        ? Object.entries(entry.details).slice(0, 2).map(([k, v]) => (
                            <span key={k} className="av-detail-chip">{k}: {String(v).slice(0, 40)}</span>
                          ))
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="av-pagination">
            <span className="av-page-info">Page {currentPage} of {totalPages}</span>
            <div className="av-page-buttons">
              <button className="av-page-btn" disabled={offset === 0} onClick={() => fetchLogs(Math.max(0, offset - limit))}>
                ← Previous
              </button>
              <button className="av-page-btn" disabled={offset + limit >= total} onClick={() => fetchLogs(offset + limit)}>
                Next →
              </button>
            </div>
          </div>
        </>
      )}

      <style>{avCss}</style>
    </div>
  );
}

/* ── Styles ─────────────────────────────────────────────────── */

const avCss = `
.av-container { display: flex; flex-direction: column; gap: 14px; padding: 18px; width: 100%; }

/* Header */
.av-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.av-header-left { display: flex; align-items: center; gap: 10px; }
.av-header-icon { width: 36px; height: 36px; border-radius: 10px; background: rgba(108,74,226,0.10); display: flex; align-items: center; justify-content: center; }
.av-header-title { font-size: 15px; font-weight: 600; color: #1A1C1D; }
.av-header-sub { font-size: 11px; color: rgba(26,28,29,0.45); margin-top: 1px; }
.av-header-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.av-filter-label { font-size: 10px; color: rgba(26,28,29,0.45); }
.av-filter-select { padding: 4px 10px; border: 1px solid rgba(26,28,29,0.08); border-radius: 6px; background: rgba(255,255,255,0.5); font-size: 11px; font-family: inherit; color: #1A1C1D; cursor: pointer; }

/* Loading */
.av-loading { display: flex; align-items: center; gap: 10px; padding: 40px; justify-content: center; color: rgba(26,28,29,0.45); font-size: 13px; }
.av-spinner { width: 18px; height: 18px; border: 2px solid rgba(108,74,226,0.15); border-top-color: #6C4AE2; border-radius: 50%; animation: av-spin 0.6s linear infinite; }
@keyframes av-spin { to { transform: rotate(360deg); } }

/* Error */
.av-error { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px; text-align: center; }
.av-error-icon { font-size: 24px; }
.av-error-msg { font-size: 13px; color: rgba(26,28,29,0.6); }
.av-retry-btn { padding: 6px 16px; border: none; border-radius: 6px; background: #6C4AE2; color: #fff; font-size: 12px; cursor: pointer; }

/* Empty */
.av-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 60px 20px; text-align: center; }
.av-empty-icon { font-size: 32px; opacity: 0.4; }
.av-empty-text { font-size: 14px; font-weight: 500; color: rgba(26,28,29,0.5); }
.av-empty-hint { font-size: 12px; color: rgba(26,28,29,0.3); max-width: 360px; }

/* Table */
.av-table-wrapper { background: rgba(255,255,255,0.5); border: 1px solid rgba(26,28,29,0.04); border-radius: 12px; overflow: hidden; }
.av-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.av-table th { text-align: left; padding: 8px 14px; font-weight: 600; color: rgba(26,28,29,0.45); background: rgba(250,248,245,0.3); border-bottom: 1px solid rgba(26,28,29,0.04); text-transform: uppercase; font-size: 9px; letter-spacing: 0.06em; white-space: nowrap; }
.av-table td { padding: 8px 14px; color: rgba(26,28,29,0.7); border-bottom: 1px solid rgba(26,28,29,0.03); }
.av-table tr:last-child td { border-bottom: none; }
.av-row { cursor: pointer; transition: background 0.1s; }
.av-row:hover td { background: rgba(108,74,226,0.04); }
.av-cell-id { font-weight: 600; color: rgba(26,28,29,0.3); font-variant-numeric: tabular-nums; }
.av-cell-time { white-space: nowrap; font-variant-numeric: tabular-nums; }
.av-cell-actor { font-weight: 500; color: #1A1C1D; }
.av-action-badge { display: inline-flex; padding: 2px 10px; border-radius: 20px; font-size: 10px; font-weight: 600; border: 1px solid; text-transform: capitalize; }
.av-cell-resource { display: flex; gap: 6px; align-items: center; }
.av-resource-type { background: rgba(26,28,29,0.04); padding: 1px 6px; border-radius: 4px; font-size: 10px; color: rgba(26,28,29,0.6); text-transform: uppercase; }
.av-resource-id { font-weight: 500; color: rgba(26,28,29,0.5); font-family: monospace; font-size: 10px; }
.av-cell-details { display: flex; gap: 4px; flex-wrap: wrap; }
.av-detail-chip { padding: 1px 6px; background: rgba(26,28,29,0.03); border-radius: 4px; font-size: 10px; color: rgba(26,28,29,0.5); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Pagination */
.av-pagination { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.av-page-info { font-size: 11px; color: rgba(26,28,29,0.45); }
.av-page-buttons { display: flex; gap: 4px; }
.av-page-btn { padding: 5px 12px; border: 1px solid rgba(108,74,226,0.12); border-radius: 6px; background: rgba(108,74,226,0.03); font-size: 10px; font-weight: 500; color: #6C4AE2; cursor: pointer; font-family: inherit; }
.av-page-btn:disabled { opacity: 0.3; cursor: default; }
.av-page-btn:hover:not(:disabled) { background: rgba(108,74,226,0.08); }
`;