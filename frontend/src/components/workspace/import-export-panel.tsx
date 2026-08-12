/** FDA25 — Import/Export Panel */

import { useState, type FC } from 'react';

async function api<T>(path: string, opts?: RequestInit) {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.json() as Promise<{ success: boolean; data?: T; error?: string }>;
  } catch { return { success: false, error: 'Network error' }; }
}

type View = 'import' | 'export';

export const ImportExportPanel: FC = () => {
  const [view, setView] = useState<View>('import');
  const [csvText, setCsvText] = useState('customer_name,phone,email\nSample,+911234567890,sample@test.com');
  const [targetType, setTargetType] = useState('lead');
  const [preview, setPreview] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [exportType, setExportType] = useState('lead');
  const [exportResult, setExportResult] = useState<any>(null);

  const handlePreview = async () => {
    setLoading(true); setError(''); setPreview(null);
    const r = await api<any>('/api/v1/data/import/preview', {
      method: 'POST', body: JSON.stringify({ content: csvText, content_type: 'csv', target_type: targetType }),
    });
    if (r.success) setPreview(r.data);
    else setError(r.error || 'Preview failed');
    setLoading(false);
  };

  const handleCommit = async () => {
    setLoading(true); setError(''); setResult(null);
    const r = await api<any>('/api/v1/data/import/commit', {
      method: 'POST', body: JSON.stringify({ content: csvText, content_type: 'csv', target_type: targetType }),
    });
    if (r.success) setResult(r.data);
    else setError(r.error || 'Import failed');
    setLoading(false);
  };

  const handleExport = async () => {
    setLoading(true); setError(''); setExportResult(null);
    const r = await api<any>('/api/v1/data/export', {
      method: 'POST', body: JSON.stringify({ target_type: exportType, format: 'json' }),
    });
    if (r.success) setExportResult(r.data);
    else setError(r.error || 'Export failed');
    setLoading(false);
  };

  return (
    <div className="wksp-import">
      <div className="wksp-admin-tabs">
        <button className={`wksp-admin-tab ${view === 'import' ? 'active' : ''}`} onClick={() => setView('import')}>Import</button>
        <button className={`wksp-admin-tab ${view === 'export' ? 'active' : ''}`} onClick={() => setView('export')}>Export</button>
      </div>

      {error && <div className="wksp-import-error">{error}</div>}

      {view === 'import' && (
        <div className="wksp-import-section">
          <h3>Import Data</h3>
          <div className="wksp-import-form">
            <label>Target: 
              <select value={targetType} onChange={e => setTargetType(e.target.value)} className="wksp-input wksp-input-sm">
                <option value="lead">Leads</option>
                <option value="customer">Customers</option>
              </select>
            </label>
            <textarea value={csvText} onChange={e => setCsvText(e.target.value)} rows={6} className="wksp-textarea" placeholder="CSV content…" />
            <div className="wksp-import-btns">
              <button onClick={handlePreview} disabled={loading} className="wksp-btn">Preview</button>
              <button onClick={handleCommit} disabled={loading} className="wksp-btn wksp-btn-primary">Commit Import</button>
            </div>
          </div>

          {loading && <div className="wksp-loading-text">Processing…</div>}

          {preview && !loading && (
            <div className="wksp-import-result">
              <h4>Preview Result</h4>
              <p>Total: {preview.total_records} | Valid: {preview.valid_records} | Invalid: {preview.invalid_records}</p>
              <p>New: {preview.new_identities} | Matched: {preview.matched_identities} | Duplicates: {preview.possible_duplicates}</p>
              {preview.records?.slice(0, 5).map((r: any, i: number) => (
                <div key={i} className={`wksp-import-row ${r.valid ? '' : 'wksp-import-invalid'}`}>
                  Row {r.row}: {r.valid ? '✓' : '✗'} {r.errors?.join(', ')}
                </div>
              ))}
            </div>
          )}

          {result && !loading && (
            <div className="wksp-import-result">
              <h4>Import Result: {result.status}</h4>
              <p>Created: {result.created} | Errors: {result.errors?.length || 0}</p>
              {result.warning && <p className="wksp-warning">{result.warning}</p>}
            </div>
          )}
        </div>
      )}

      {view === 'export' && (
        <div className="wksp-import-section">
          <h3>Export Data</h3>
          <div className="wksp-import-form">
            <label>Type: 
              <select value={exportType} onChange={e => setExportType(e.target.value)} className="wksp-input wksp-input-sm">
                <option value="lead">Leads</option>
                <option value="customer">Customers</option>
              </select>
            </label>
            <button onClick={handleExport} disabled={loading} className="wksp-btn">Export</button>
          </div>
          {exportResult && !loading && (
            <div className="wksp-import-result">
              <h4>Export: {exportResult.record_count} records</h4>
              <pre className="wksp-export-json">{JSON.stringify(exportResult.records?.slice(0, 3), null, 2)}</pre>
              <p className="wksp-muted">Showing first 3 of {exportResult.record_count} records. Full export shown in JSON.</p>
            </div>
          )}
        </div>
      )}

      <style>{`
.wksp-import { padding: var(--shunya-spacing-md); }
.wksp-import-section h3 { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--shunya-text); }
.wksp-import-form { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.wksp-textarea { padding: 8px; background: var(--shunya-surface-3); border: 1px solid var(--shunya-surface-1); border-radius: 4px; color: var(--shunya-text); font-size: 12px; font-family: monospace; resize: vertical; }
.wksp-input-sm { width: auto; min-width: 100px; }
.wksp-import-btns { display: flex; gap: 8px; }
.wksp-btn-primary { background: var(--shunya-color-accent, #7c3aed); }
.wksp-import-result { background: var(--shunya-surface-2); padding: 12px; border-radius: 6px; margin-top: 8px; }
.wksp-import-result h4 { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.wksp-import-row { padding: 4px 0; font-size: 12px; }
.wksp-import-invalid { color: #f88; }
.wksp-import-error { color: #f88; padding: 8px; background: rgba(239,68,68,0.1); border-radius: 4px; margin-bottom: 8px; }
.wksp-warning { color: #f5a623; font-size: 12px; margin-top: 4px; }
.wksp-export-json { background: var(--shunya-surface-1); padding: 8px; border-radius: 4px; font-size: 11px; overflow-x: auto; max-height: 200px; }
.wksp-loading-text { text-align: center; padding: 20px; color: var(--shunya-text-secondary); }
      `}</style>
    </div>
  );
};