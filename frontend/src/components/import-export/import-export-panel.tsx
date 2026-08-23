/** FDA25 — Import / Export Panel (Canonical Location)
 *
 * Enhanced with file upload support (CSV/XLSX/JSON).
 * Wired into workspace via workspace-container.tsx and executive-home.tsx.
 */

import { useState, useRef, type FC } from 'react';

async function api<T>(path: string, opts?: RequestInit) {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.json() as Promise<{ success: boolean; data?: T; error?: string }>;
  } catch { return { success: false, error: 'Network error' }; }
}

type View = 'import' | 'export';
type InputMethod = 'paste' | 'upload';
type Step = 'input' | 'preview' | 'result';

export const ImportExportPanel: FC = () => {
  const [view, setView] = useState<View>('import');
  const [inputMethod, setInputMethod] = useState<InputMethod>('upload');
  const [csvText, setCsvText] = useState('customer_name,phone,email\nSample,+911****7890,sample@test.com');
  const [targetType, setTargetType] = useState('lead');
  const [preview, setPreview] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<Step>('input');
  const [fileName, setFileName] = useState('');
  const [exportType, setExportType] = useState('lead');
  const [exportResult, setExportResult] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (file.name.endsWith('.csv') || file.name.endsWith('.txt') || file.name.endsWith('.json')) {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
      } else if (file.name.endsWith('.xlsx')) {
        // XLSX files are binary — store as base64
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = (reader.result as string).split(',')[1];
          resolve(base64);
        };
        reader.onerror = () => reject(new Error('Failed to read XLSX'));
        reader.readAsDataURL(file);
      } else {
        reject(new Error('Unsupported file type. Use CSV, XLSX, or JSON.'));
      }
    });
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setError('');
    setPreview(null);
    setResult(null);
    setStep('input');
    setLoading(true);
    try {
      const content = await readFileContent(file);
      setCsvText(content);
      const contentType = file.name.endsWith('.xlsx') ? 'xlsx' : file.name.endsWith('.json') ? 'json' : 'csv';
      const r = await api<any>('/api/v1/data/import/preview', {
        method: 'POST', body: JSON.stringify({ content, content_type: contentType, target_type: targetType }),
      });
      if (r.success) {
        setPreview(r.data);
        setStep('preview');
      } else {
        setError(r.error || 'Preview failed');
      }
    } catch (err: any) {
      setError(err.message || 'File read failed');
    }
    setLoading(false);
  };

  const handlePreview = async () => {
    if (!csvText.trim()) { setError('No data to preview'); return; }
    setLoading(true); setError(''); setPreview(null); setResult(null);
    const r = await api<any>('/api/v1/data/import/preview', {
      method: 'POST', body: JSON.stringify({ content: csvText, content_type: 'csv', target_type: targetType }),
    });
    if (r.success) { setPreview(r.data); setStep('preview'); }
    else setError(r.error || 'Preview failed');
    setLoading(false);
  };

  const handleCommit = async () => {
    setLoading(true); setError(''); setResult(null);
    const r = await api<any>('/api/v1/data/import/commit', {
      method: 'POST', body: JSON.stringify({ content: csvText, content_type: 'csv', target_type: targetType }),
    });
    if (r.success) { setResult(r.data); setStep('result'); }
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

  const resetFlow = () => { setStep('input'); setPreview(null); setResult(null); setError(''); setFileName(''); };

  return (
    <div className="wksp-import">
      <div className="wksp-admin-tabs">
        <button className={`wksp-admin-tab ${view === 'import' ? 'active' : ''}`} onClick={() => setView('import')}>📥 Import</button>
        <button className={`wksp-admin-tab ${view === 'export' ? 'active' : ''}`} onClick={() => setView('export')}>📤 Export</button>
      </div>

      {error && <div className="wksp-import-error">{error}</div>}

      {view === 'import' && (
        <div className="wksp-import-section">
          <h3>Bring Data Into SHUNYA</h3>
          {step === 'input' && (
            <>
              <div className="wksp-import-method-tabs">
                <button className={`wksp-import-method ${inputMethod === 'upload' ? 'active' : ''}`} onClick={() => setInputMethod('upload')}>Upload File</button>
                <button className={`wksp-import-method ${inputMethod === 'paste' ? 'active' : ''}`} onClick={() => setInputMethod('paste')}>Paste CSV</button>
              </div>

              {inputMethod === 'upload' ? (
                <div className="wksp-import-upload">
                  <div className="wksp-import-dropzone" onClick={() => fileRef.current?.click()}>
                    {fileName ? (
                      <div className="wksp-import-file-selected">📄 {fileName}</div>
                    ) : (
                      <div className="wksp-import-dropzone-text">Click to select a CSV, XLSX, or JSON file</div>
                    )}
                  </div>
                  <input ref={fileRef} type="file" accept=".csv,.xlsx,.json,.txt" onChange={handleFileSelect} style={{ display: 'none' }} />
                  <div className="wksp-import-target-row">
                    <label>Import as: 
                      <select value={targetType} onChange={e => setTargetType(e.target.value)} className="wksp-input wksp-input-sm">
                        <option value="lead">Leads</option>
                        <option value="customer">Customers</option>
                        <option value="campaign">Campaigns</option>
                      </select>
                    </label>
                  </div>
                </div>
              ) : (
                <div className="wksp-import-form">
                  <label>Target: 
                    <select value={targetType} onChange={e => setTargetType(e.target.value)} className="wksp-input wksp-input-sm">
                      <option value="lead">Leads</option>
                      <option value="customer">Customers</option>
                      <option value="campaign">Campaigns</option>
                    </select>
                  </label>
                  <textarea value={csvText} onChange={e => setCsvText(e.target.value)} rows={6} className="wksp-textarea" placeholder="CSV content…" />
                  <button onClick={handlePreview} disabled={loading} className="wksp-btn wksp-btn-primary">Preview & Validate</button>
                </div>
              )}
            </>
          )}

          {step === 'preview' && preview && (
            <div className="wksp-import-result">
              <h4>Preview — {preview.total_records} records found</h4>
              <div className="wksp-import-stats">
                <span className="wksp-stat wksp-stat-ok">✓ {preview.valid_records} valid</span>
                {preview.invalid_records > 0 && <span className="wksp-stat wksp-stat-err">✗ {preview.invalid_records} invalid</span>}
                <span className="wksp-stat">🆕 {preview.new_identities} new</span>
                <span className="wksp-stat">🔄 {preview.matched_identities} matched</span>
                {preview.possible_duplicates > 0 && <span className="wksp-stat wksp-stat-warn">⚠ {preview.possible_duplicates} duplicates</span>}
                {preview.conflicts > 0 && <span className="wksp-stat wksp-stat-err">⚡ {preview.conflicts} conflicts</span>}
              </div>
              <div className="wksp-import-records">
                {preview.records?.slice(0, 10).map((r: any, i: number) => (
                  <div key={i} className={`wksp-import-row ${r.valid ? '' : 'wksp-import-invalid'}`}>
                    #{i + 1} {r.identity_action === 'match' ? '🔄' : '🆕'} {r.commit_action === 'reject' ? '✗' : r.commit_action === 'update' ? '📝' : '✓'}
                    {' '}{r.display_name || r.customer_name || r.email || `Row ${r.row}`}
                    {r.errors?.length ? <span className="wksp-import-err-detail"> — {r.errors.join('; ')}</span> : ''}
                  </div>
                ))}
                {preview.records?.length > 10 && <div className="wksp-import-more">… and {preview.records.length - 10} more</div>}
              </div>
              <div className="wksp-import-btns">
                <button onClick={handleCommit} disabled={loading} className="wksp-btn wksp-btn-primary">
                  {loading ? 'Importing…' : `Import ${preview.records_to_create || preview.valid_records} records`}
                </button>
                <button onClick={resetFlow} className="wksp-btn">Cancel</button>
              </div>
            </div>
          )}

          {loading && step === 'input' && <div className="wksp-loading-text">Processing file…</div>}

          {step === 'result' && result && (
            <div className="wksp-import-result">
              <h4>{result.status === 'completed' ? '✅ Import Complete' : result.status === 'partial' ? '⚠ Partial Import' : '❌ Import Failed'}</h4>
              <div className="wksp-import-stats">
                <span className="wksp-stat">Created: {result.created || 0}</span>
                <span className="wksp-stat">Updated: {result.updated || 0}</span>
                {result.skipped > 0 && <span className="wksp-stat">Skipped: {result.skipped}</span>}
                {result.errors?.length > 0 && <span className="wksp-stat wksp-stat-err">Errors: {result.errors.length}</span>}
              </div>
              {result.errors?.length > 0 && (
                <div className="wksp-import-result-errors">
                  {result.errors.slice(0, 5).map((e: any, i: number) => (
                    <div key={i} className="wksp-import-err">⚠ {e.message || e}</div>
                  ))}
                  {result.errors.length > 5 && <div>… and {result.errors.length - 5} more</div>}
                </div>
              )}
              {result.warning && <p className="wksp-warning">{result.warning}</p>}
              <button onClick={resetFlow} className="wksp-btn" style={{ marginTop: 12 }}>Import More Data</button>
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
              <h4>📤 Export: {exportResult.record_count} records</h4>
              <pre className="wksp-export-json">{JSON.stringify(exportResult.records?.slice(0, 3), null, 2)}</pre>
              <p className="wksp-muted">Showing first 3 of {exportResult.record_count} records.</p>
            </div>
          )}
        </div>
      )}

      <style>{`
.wksp-import { padding: var(--shunya-spacing-md); }
.wksp-import-section h3 { font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--shunya-text); }
.wksp-import-method-tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.wksp-import-method { padding: 6px 14px; font-size: 12px; background: var(--shunya-surface-2); border: 1px solid var(--shunya-surface-1); border-radius: 4px; cursor: pointer; }
.wksp-import-method.active { background: var(--shunya-color-accent, #7c3aed); color: #fff; border-color: var(--shunya-color-accent, #7c3aed); }
.wksp-import-dropzone { border: 2px dashed var(--shunya-surface-1); border-radius: 8px; padding: 24px; text-align: center; cursor: pointer; margin-bottom: 8px; transition: border-color .2s; }
.wksp-import-dropzone:hover { border-color: var(--shunya-color-accent, #7c3aed); }
.wksp-import-dropzone-text { color: var(--shunya-text-secondary); font-size: 13px; }
.wksp-import-file-selected { font-size: 14px; font-weight: 500; color: var(--shunya-color-accent, #7c3aed); }
.wksp-import-target-row { display: flex; gap: 8px; align-items: center; margin-top: 4px; }
.wksp-import-stats { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }
.wksp-stat { font-size: 12px; padding: 4px 8px; background: var(--shunya-surface-3); border-radius: 4px; }
.wksp-stat-ok { border-left: 3px solid #22c55e; }
.wksp-stat-err { border-left: 3px solid #f88; }
.wksp-stat-warn { border-left: 3px solid #f5a623; }
.wksp-import-records { max-height: 300px; overflow-y: auto; margin: 8px 0; border: 1px solid var(--shunya-surface-1); border-radius: 4px; }
.wksp-import-row { padding: 4px 8px; font-size: 12px; border-bottom: 1px solid var(--shunya-surface-1); }
.wksp-import-invalid { color: #f88; }
.wksp-import-err-detail { color: #f88; font-size: 11px; }
.wksp-import-more { text-align: center; padding: 4px; font-size: 11px; color: var(--shunya-text-secondary); }
.wksp-import-btns { display: flex; gap: 8px; margin-top: 8px; }
.wksp-btn-primary { background: var(--shunya-color-accent, #7c3aed); color: #fff; }
.wksp-import-result { background: var(--shunya-surface-2); padding: 12px; border-radius: 6px; margin-top: 8px; }
.wksp-import-result h4 { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.wksp-import-result-errors { margin-top: 6px; }
.wksp-import-err { color: #f88; font-size: 12px; padding: 2px 0; }
.wksp-import-error { color: #f88; padding: 8px; background: rgba(239,68,68,0.1); border-radius: 4px; margin-bottom: 8px; }
.wksp-warning { color: #f5a623; font-size: 12px; margin-top: 4px; }
.wksp-export-json { background: var(--shunya-surface-1); padding: 8px; border-radius: 4px; font-size: 11px; overflow-x: auto; max-height: 200px; }
.wksp-loading-text { text-align: center; padding: 20px; color: var(--shunya-text-secondary); }
.wksp-muted { color: var(--shunya-text-secondary); font-size: 11px; margin-top: 4px; }
      `}</style>
    </div>
  );
};