/** FDA25 — Import / Export Panel (Canonical Location)  [M6 semantic ingestion]
 *
 * Enhanced for M6 (SH-M6→M15 Stage A):
 *   INSPECT → UNDERSTAND → MAP (explained) → RESOLVE AMBIGUITY → CONFIRM
 *   → PERSIST → PROVENANCE → CORRECT → RECOVER → OBSERVABLE OUTCOME
 *
 * - The preview shows SHUNYA's interpretation of every source column, with
 *   method and reasoning, and lets the human decide ambiguous mappings.
 * - After commit, each created record carries provenance the user can open:
 *   source file, row, import session, mapping decision, author, timestamp —
 *   and corrections can be applied (auditable, never silent).
 *
 * Wired into workspace via workspace-container.tsx and executive-home.tsx.
 */

import { useState, useRef, type FC } from 'react';
import { IconDownload, IconUpload, IconFileText, IconCheck, IconX, IconPlus, IconRefresh, IconAlertTriangle, IconBolt, IconHistory, IconArrowRight } from '@tabler/icons-react';
import { useWorkspaceStore } from '../../runtimes/workspace/store';

async function api<T>(path: string, opts?: RequestInit) {
  try {
    const r = await fetch(path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts });
    return r.json() as Promise<{ success: boolean; data?: T; error?: string }>;
  } catch { return { success: false, error: 'Network error' }; }
}

type View = 'import' | 'export';
type InputMethod = 'paste' | 'upload';
type Step = 'input' | 'preview' | 'result';

interface ColumnMapEntry {
  source_column: string;
  target_field: string;
  method: string;
  confidence: number;
  reason: string;
  hint_code?: string;
  conflict?: boolean;
  conflict_note?: string;
}

interface Ambiguity {
  code: string;
  field?: string;
  column?: string;
  columns?: string[];
  chosen?: string;
  row?: number;
  candidate?: { id: number; name: string; similarity: number };
  message: string;
}

interface PreviewRecord {
  row: number;
  data: Record<string, string>;
  valid: boolean;
  errors: string[];
  warnings: string[];
  weak_identity?: boolean;
  identity_action?: string;
  matched_identity?: { id: number; name?: string; code?: string } | null;
  match_basis?: string;
  similar_candidates?: { id: number; name: string; similarity: number; basis: string }[];
  commit_action?: string;
}

interface PreviewData {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  new_identities: number;
  matched_identities: number;
  possible_duplicates: number;
  conflicts: number;
  records_to_create: number;
  records_rejected: number;
  weak_identity_rows: number[];
  column_mapping: ColumnMapEntry[];
  ambiguities: Ambiguity[];
  requires_review: boolean;
  records: PreviewRecord[];
}

interface CreatedRecord { row: number; id: number; name: string }
interface CommitResult {
  status: string;
  created: number;
  updated: number;
  rejected: number;
  duplicates_skipped: number;
  errors: { row?: number; error?: string }[];
  warning?: string;
  warning_row?: string;
  skipped_details?: { row: number; matched: { id: number; name?: string } | null; basis: string }[];
  records_created?: CreatedRecord[];
  provenance?: { row: number; target_type: string; record_id: number; evidence_id: number }[];
  import_session?: string;
  source_name?: string;
}

interface ProvenanceEntry {
  kind: string;
  evidence_id: number;
  source_type?: string;
  source_name?: string;
  row?: number;
  import_session?: string;
  field_mapping?: Record<string, string>;
  imported_by?: string;
  imported_at?: string;
  transformations?: string[];
  field?: string;
  old_value?: string;
  new_value?: string;
  reason?: string;
  corrected_by?: string;
  corrected_at?: string;
  legacy?: boolean;
}

interface ProvenanceData {
  target_type: string;
  record_id: number;
  record: Record<string, unknown>;
  origin: ProvenanceEntry | null;
  corrections: ProvenanceEntry[];
  entries: ProvenanceEntry[];
  has_provenance: boolean;
}

// Canonical targets the human may choose for each import type.
const MAPPABLE_TARGETS: Record<string, { value: string; label: string }[]> = {
  lead: [
    { value: 'customer_name', label: 'Customer name' },
    { value: 'phone', label: 'Phone' },
    { value: 'email', label: 'Email' },
    { value: 'notes', label: 'Notes' },
  ],
  customer: [
    { value: 'display_name', label: 'Customer name' },
    { value: 'email', label: 'Email' },
    { value: 'phone', label: 'Phone' },
    { value: 'company_name', label: 'Company' },
    { value: 'address_line1', label: 'Address' },
    { value: 'city', label: 'City' },
    { value: 'state', label: 'State' },
    { value: 'postal_code', label: 'Postal code' },
    { value: 'country', label: 'Country' },
    { value: 'gstin', label: 'GST / tax ID' },
    { value: 'source', label: 'Source' },
    { value: 'notes', label: 'Notes' },
  ],
  supplier: [
    { value: 'name', label: 'Supplier name' },
    { value: 'category', label: 'Category' },
    { value: 'contact', label: 'Contact person' },
    { value: 'email', label: 'Email' },
    { value: 'phone', label: 'Phone' },
    { value: 'city', label: 'City' },
    { value: 'gstin', label: 'GST / tax ID' },
    { value: 'payment_terms', label: 'Payment terms' },
    { value: 'rating', label: 'Rating' },
    { value: 'notes', label: 'Notes' },
  ],
  campaign: [{ value: 'name', label: 'Campaign name' }],
};

const CORRECTABLE_FIELDS: Record<string, string[]> = {
  customer: ['display_name', 'email', 'phone', 'company_name', 'city', 'state', 'notes'],
  supplier: ['name', 'category', 'contact', 'email', 'phone', 'city', 'gstin', 'payment_terms', 'notes'],
  lead: ['customer_name', 'phone', 'email', 'notes'],
};

function targetLabel(targetType: string, field: string): string {
  const opts = MAPPABLE_TARGETS[targetType] || [];
  const hit = opts.find(o => o.value === field);
  return hit ? hit.label : field;
}

function methodChip(method: string): string {
  switch (method) {
    case 'alias': return 'known column name';
    case 'alias_fallback': return 'fallback — explained';
    case 'manual': return 'your decision';
    default: return method;
  }
}

export const ImportExportPanel: FC = () => {
  const [view, setView] = useState<View>('import');
  const [inputMethod, setInputMethod] = useState<InputMethod>('upload');
  const [csvText, setCsvText] = useState('customer_name,phone,email\nSample,+911****7890,sample@test.com');
  const [targetType, setTargetType] = useState('lead');
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [result, setResult] = useState<CommitResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<Step>('input');
  const [fileName, setFileName] = useState('');
  const [exportType, setExportType] = useState('lead');
  const [exportResult, setExportResult] = useState<Record<string, unknown> | null>(null);
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [contentType, setContentType] = useState('csv');
  const fileRef = useRef<HTMLInputElement>(null);
  const sessionRef = useRef<string>('');

  // Provenance drawer state
  const [provFor, setProvFor] = useState<{ type: string; id: number } | null>(null);
  const [prov, setProv] = useState<ProvenanceData | null>(null);
  const [provLoading, setProvLoading] = useState(false);
  const [provError, setProvError] = useState('');
  // Correction state (per open record)
  const [corrField, setCorrField] = useState('');
  const [corrValue, setCorrValue] = useState('');
  const [corrReason, setCorrReason] = useState('');
  const [corrBusy, setCorrBusy] = useState(false);
  const [corrError, setCorrError] = useState('');
  const [corrNotice, setCorrNotice] = useState('');

  const readFileContent = (file: File): Promise<{ content: string; kind: string }> => {
    return new Promise((resolve, reject) => {
      if (file.name.endsWith('.csv') || file.name.endsWith('.txt') || file.name.endsWith('.json')) {
        const reader = new FileReader();
        reader.onload = () => {
          const kind = file.name.endsWith('.json') ? 'json' : 'csv';
          resolve({ content: reader.result as string, kind });
        };
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
      } else if (file.name.endsWith('.xlsx')) {
        // XLSX files are binary — store as base64
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = (reader.result as string).split(',')[1];
          resolve({ content: base64, kind: 'xlsx' });
        };
        reader.onerror = () => reject(new Error('Failed to read XLSX'));
        reader.readAsDataURL(file);
      } else {
        reject(new Error('Unsupported file type. Use CSV, XLSX, or JSON.'));
      }
    });
  };

  const newSession = () => {
    try {
      sessionRef.current = (globalThis.crypto && 'randomUUID' in globalThis.crypto)
        ? globalThis.crypto.randomUUID()
        : `imp_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
    } catch {
      sessionRef.current = `imp_${Date.now()}`;
    }
  };

  const runPreview = async (content: string, kind: string, ovr: Record<string, string>) => {
    setLoading(true); setError(''); setPreview(null); setResult(null); setProvFor(null); setCorrNotice('');
    newSession();
    const r = await api<PreviewData>('/api/v1/data/import/preview', {
      method: 'POST',
      body: JSON.stringify({ content, content_type: kind, target_type: targetType, column_overrides: ovr }),
    });
    if (r.success && r.data) { setPreview(r.data); setStep('preview'); }
    else setError(r.error || 'Preview failed');
    setLoading(false);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setError(''); setPreview(null); setResult(null); setOverrides({});
    setLoading(true);
    try {
      const { content, kind } = await readFileContent(file);
      setCsvText(content);
      setContentType(kind);
      setLoading(false);
      await runPreview(content, kind, {});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'File read failed');
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    if (!csvText.trim()) { setError('No data to preview'); return; }
    await runPreview(csvText, contentType, overrides);
  };

  const handleOverrideChange = (column: string, target: string) => {
    setOverrides(prev => ({ ...prev, [column]: target }));
  };

  const handleCommit = async () => {
    setLoading(true); setError(''); setResult(null);
    const r = await api<CommitResult>('/api/v1/data/import/commit', {
      method: 'POST',
      body: JSON.stringify({
        content: csvText, content_type: contentType, target_type: targetType,
        column_overrides: overrides,
        source_name: fileName || 'pasted content',
        session_token: sessionRef.current,
      }),
    });
    if (r.success && r.data) { setResult(r.data); setStep('result'); }
    else if (r.data) { setResult(r.data); setStep('result'); setError(r.error || r.data.warning || 'Import failed'); }
    else setError(r.error || 'Import failed');
    setLoading(false);
  };

  const handleExport = async () => {
    setLoading(true); setError(''); setExportResult(null);
    const r = await api<Record<string, unknown>>('/api/v1/data/export', {
      method: 'POST', body: JSON.stringify({ target_type: exportType, format: 'json' }),
    });
    if (r.success && r.data) setExportResult(r.data);
    else setError(r.error || 'Export failed');
    setLoading(false);
  };

  const openProvenance = async (type: string, id: number) => {
    setProvFor({ type, id }); setProv(null); setProvError('');
    setCorrField(''); setCorrValue(''); setCorrReason(''); setCorrError(''); setCorrNotice('');
    setProvLoading(true);
    const r = await api<ProvenanceData>(`/api/v1/data/provenance/${type}/${id}`);
    if (r.success && r.data) setProv(r.data);
    else setProvError(r.error || 'Could not load provenance');
    setProvLoading(false);
  };

  const submitCorrection = async () => {
    if (!provFor || !corrField) { setCorrError('Choose a field to correct'); return; }
    setCorrBusy(true); setCorrError(''); setCorrNotice('');
    const r = await api<{ ok: boolean; correction: { field: string; old_value: string; new_value: string } }>(
      '/api/v1/data/import/correct',
      {
        method: 'POST',
        body: JSON.stringify({
          target_type: provFor.type, record_id: provFor.id,
          field: corrField, new_value: corrValue, reason: corrReason,
        }),
      },
    );
    setCorrBusy(false);
    if (r.success && r.data) {
      setCorrNotice(`Corrected ${corrField} — the change is recorded with your identity and reason.`);
      setCorrValue(''); setCorrReason('');
      await openProvenanceRetainNotice(provFor.type, provFor.id);
    } else {
      setCorrError(r.error || 'Correction failed');
    }
  };

  // Reload provenance keeping the success notice visible.
  const openProvenanceRetainNotice = async (type: string, id: number) => {
    setProvLoading(true);
    const r = await api<ProvenanceData>(`/api/v1/data/provenance/${type}/${id}`);
    if (r.success && r.data) setProv(r.data);
    setProvLoading(false);
  };

  const goToRelationships = () => {
    useWorkspaceStore.getState().open('Relationships', 'object', {
      objectType: 'relationships', objectId: 'relationships',
    });
  };

  const resetFlow = () => { setStep('input'); setPreview(null); setResult(null); setError(''); setFileName(''); setOverrides({}); setProvFor(null); setCorrNotice(''); };

  const unresolvedAmbiguities = (preview?.ambiguities || []).filter(a =>
    a.code === 'multiple_candidates' || a.code.startsWith('unmapped_') || a.code === 'conflicting_duplicate');
  const reviewNotes = (preview?.ambiguities || []).filter(a => a.code === 'similar_existing_entity');

  return (
    <div className="wksp-import">
      <div className="wksp-admin-tabs">
        <button className={`wksp-admin-tab ${view === 'import' ? 'active' : ''}`} onClick={() => setView('import')}><IconDownload size={14} /> Import</button>
        <button className={`wksp-admin-tab ${view === 'export' ? 'active' : ''}`} onClick={() => setView('export')}><IconUpload size={14} /> Export</button>
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
                      <div className="wksp-import-file-selected"><IconFileText size={14} /> {fileName}</div>
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
                        <option value="supplier">Suppliers</option>
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
                      <option value="supplier">Suppliers</option>
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
                <span className="wksp-stat wksp-stat-ok"><IconCheck size={12} /> {preview.valid_records} valid</span>
                {preview.invalid_records > 0 && <span className="wksp-stat wksp-stat-err"><IconX size={12} /> {preview.invalid_records} invalid</span>}
                <span className="wksp-stat"><IconPlus size={12} /> {preview.new_identities} new</span>
                <span className="wksp-stat"><IconRefresh size={12} /> {preview.matched_identities} matched</span>
                {preview.possible_duplicates > 0 && <span className="wksp-stat wksp-stat-warn"><IconAlertTriangle size={12} /> {preview.possible_duplicates} duplicates</span>}
                {preview.conflicts > 0 && <span className="wksp-stat wksp-stat-err"><IconBolt size={12} /> {preview.conflicts} conflicts</span>}
              </div>

              {/* SHUNYA's interpretation of every column — explained. */}
              <div className="wksp-import-mapping">
                <div className="wksp-import-mapping-title">How SHUNYA reads your columns</div>
                <table className="wksp-mapping-table">
                  <thead>
                    <tr><th>Your column</th><th>SHUNYA understands</th><th>Why</th></tr>
                  </thead>
                  <tbody>
                    {(preview.column_mapping || []).map(m => (
                      <tr key={m.source_column} className={m.conflict ? 'wksp-mapping-conflict' : ''}>
                        <td>{m.source_column}</td>
                        <td>
                          <select
                            className="wksp-input wksp-input-xs"
                            value={overrides[m.source_column] !== undefined ? overrides[m.source_column] : m.target_field}
                            onChange={e => handleOverrideChange(m.source_column, e.target.value)}
                          >
                            <option value="">Not imported</option>
                            {(MAPPABLE_TARGETS[targetType] || []).map(o => (
                              <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                          </select>
                        </td>
                        <td className="wksp-mapping-why">
                          {m.reason}
                          {m.conflict_note && <span className="wksp-mapping-conflict-note"> {m.conflict_note}</span>}
                          {!m.conflict && <span className="wksp-mapping-method"> ({methodChip(m.method)})</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {Object.keys(overrides).length > 0 && (
                  <div className="wksp-import-btns">
                    <button onClick={handlePreview} disabled={loading} className="wksp-btn">
                      {loading ? 'Re-reading…' : 'Re-read with my mapping'}
                    </button>
                  </div>
                )}
              </div>

              {/* Needs your decision */}
              {unresolvedAmbiguities.length > 0 && (
                <div className="wksp-import-ambiguities">
                  <div className="wksp-ambiguity-title"><IconAlertTriangle size={13} /> Needs your decision</div>
                  {unresolvedAmbiguities.map((a, i) => (
                    <div key={i} className="wksp-ambiguity-row">{a.message}</div>
                  ))}
                </div>
              )}

              {/* Similar entities — surfaced, never merged */}
              {reviewNotes.length > 0 && (
                <div className="wksp-import-similar">
                  <div className="wksp-ambiguity-title"><IconHistory size={13} /> Similar existing records</div>
                  {reviewNotes.map((a, i) => (
                    <div key={i} className="wksp-ambiguity-row">{a.message}</div>
                  ))}
                </div>
              )}

              <div className="wksp-import-records">
                {preview.records?.slice(0, 10).map((r, i) => (
                  <div key={i} className={`wksp-import-row ${r.valid ? '' : 'wksp-import-invalid'}`}>
                    #{r.row} {r.identity_action === 'match' ? <IconRefresh size={12} /> : <IconPlus size={12} />} {r.commit_action === 'reject' ? <IconX size={12} /> : <IconCheck size={12} />}
                    {' '}{r.data?.display_name || r.data?.name || r.data?.customer_name || `Row ${r.row}`}
                    {r.match_basis && <span className="wksp-import-basis"> — {r.match_basis}</span>}
                    {r.errors?.length ? <span className="wksp-import-err-detail"> — {r.errors.join('; ')}</span> : ''}
                    {r.warnings?.length ? <span className="wksp-import-warn-detail"> — {r.warnings.join('; ')}</span> : ''}
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
              <h4>{result.status === 'completed' ? <><IconCheck size={14} /> Import Complete</> : result.status === 'partial' ? <><IconAlertTriangle size={14} /> Partial Import</> : result.status === 'noop' ? <><IconRefresh size={14} /> Nothing New</> : <><IconX size={14} /> Import Failed</>}</h4>
              <div className="wksp-import-stats">
                <span className="wksp-stat">Created: {result.created || 0}</span>
                {result.duplicates_skipped > 0 && <span className="wksp-stat">Already existed: {result.duplicates_skipped}</span>}
                {result.rejected > 0 && <span className="wksp-stat wksp-stat-warn">Rejected: {result.rejected}</span>}
                {result.errors?.length > 0 && <span className="wksp-stat wksp-stat-err">Errors: {result.errors.length}</span>}
              </div>
              {result.warning && <p className="wksp-warning">{result.warning}</p>}
              {result.import_session && (
                <p className="wksp-muted">Import session {result.import_session.slice(0, 8)} · source: {result.source_name}</p>
              )}

              {(result.records_created?.length || 0) > 0 && (
                <div className="wksp-import-created">
                  <div className="wksp-import-mapping-title">Imported records</div>
                  {result.records_created?.map(rc => (
                    <div key={rc.id} className="wksp-created-row">
                      <span>{rc.name || `#${rc.id}`}</span>
                      <button className="wksp-btn wksp-btn-sm" onClick={() => openProvenance(targetType, rc.id)}>
                        <IconHistory size={12} /> Where did this come from?
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {(result.skipped_details?.length || 0) > 0 && (
                <div className="wksp-import-skipped">
                  <div className="wksp-import-mapping-title">Skipped — already exists</div>
                  {result.skipped_details?.slice(0, 5).map((s, i) => (
                    <div key={i} className="wksp-ambiguity-row">Row {s.row}: {s.basis}</div>
                  ))}
                </div>
              )}

              {result.errors?.length > 0 && (
                <div className="wksp-import-result-errors">
                  {result.errors.slice(0, 5).map((e, i) => (
                    <div key={i} className="wksp-import-err"><IconAlertTriangle size={12} /> {e.row ? `Row ${e.row}: ` : ''}{e.error || String(e)}</div>
                  ))}
                  {result.errors.length > 5 && <div>… and {result.errors.length - 5} more</div>}
                </div>
              )}

              {/* Failure recovery: fix the file and retry — retry is idempotent. */}
              {result.status !== 'completed' && (
                <p className="wksp-muted">Retrying the same file is safe: rows that already exist are skipped, not duplicated.</p>
              )}
              {targetType === 'customer' && (result.created || 0) > 0 && (
                <button className="wksp-btn wksp-btn-sm" onClick={goToRelationships} style={{ marginTop: 8 }}>
                  Open Relationships <IconArrowRight size={12} />
                </button>
              )}
              <button onClick={resetFlow} className="wksp-btn" style={{ marginTop: 12 }}>Import More Data</button>
            </div>
          )}

          {/* ── Provenance drawer — where did this come from? ── */}
          {provFor && (
            <div className="wksp-prov">
              <div className="wksp-prov-head">
                <span className="wksp-prov-title">Where did this come from?</span>
                <button className="wksp-prov-close" onClick={() => setProvFor(null)} aria-label="Close"><IconX size={13} /></button>
              </div>
              {provLoading && <div className="wksp-loading-text">Loading provenance…</div>}
              {provError && <div className="wksp-import-error">{provError}</div>}
              {prov && !provLoading && (
                <div className="wksp-prov-body">
                  {prov.has_provenance && prov.origin ? (
                    <>
                      <div className="wksp-prov-line">
                        <strong>{String(prov.record?.display_name || prov.record?.name || `#${prov.record_id}`)}</strong>
                        {' '}was created by an import from <strong>{prov.origin.source_name || 'unknown source'}</strong>
                        {prov.origin.row ? `, row ${prov.origin.row}` : ''}
                        {prov.origin.imported_at ? ` on ${new Date(prov.origin.imported_at).toLocaleString()}` : ''}.
                      </div>
                      <div className="wksp-prov-line wksp-muted">
                        Mapping used: {Object.entries(prov.origin.field_mapping || {}).map(([k, v]) => `${v} → ${targetLabel(prov.target_type, k)}`).join(', ') || '—'}
                      </div>
                      <div className="wksp-prov-line wksp-muted">
                        Import session {String(prov.origin.import_session || '').slice(0, 8)} · read by {prov.origin.imported_by || 'unknown'}
                      </div>
                    </>
                  ) : (
                    <div className="wksp-prov-line">No import provenance recorded for this record — it was created directly, not imported.</div>
                  )}

                  {prov.corrections.length > 0 && (
                    <div className="wksp-prov-corrections">
                      <div className="wksp-import-mapping-title">Corrections</div>
                      {prov.corrections.map((c, i) => (
                        <div key={i} className="wksp-ambiguity-row">
                          {c.field}: “{c.old_value}” → “{c.new_value}”{c.reason ? ` — ${c.reason}` : ''} (by {c.corrected_by})
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Correction form — auditable, never silent */}
                  <div className="wksp-prov-correct">
                    <div className="wksp-import-mapping-title">Correct something</div>
                    <div className="wksp-prov-correct-row">
                      <select className="wksp-input wksp-input-sm" value={corrField} onChange={e => setCorrField(e.target.value)}>
                        <option value="">Field…</option>
                        {(CORRECTABLE_FIELDS[prov.target_type] || []).map(f => (
                          <option key={f} value={f}>{targetLabel(prov.target_type, f)}</option>
                        ))}
                      </select>
                      <input className="wksp-input wksp-input-sm" placeholder="New value" value={corrValue} onChange={e => setCorrValue(e.target.value)} />
                    </div>
                    <input className="wksp-input wksp-input-sm wksp-prov-reason" placeholder="Why? (recorded with your identity)" value={corrReason} onChange={e => setCorrReason(e.target.value)} />
                    {corrError && <div className="wksp-import-err">{corrError}</div>}
                    {corrNotice && <div className="wksp-prov-notice" role="status">{corrNotice}</div>}
                    <button className="wksp-btn wksp-btn-sm" onClick={submitCorrection} disabled={corrBusy || !corrField}>
                      {corrBusy ? 'Recording…' : 'Record correction'}
                    </button>
                  </div>
                </div>
              )}
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
                <option value="supplier">Suppliers</option>
              </select>
            </label>
            <button onClick={handleExport} disabled={loading} className="wksp-btn">Export</button>
          </div>
          {exportResult && !loading && (
            <div className="wksp-import-result">
              <h4><IconUpload size={14} /> Export: {String(exportResult.record_count ?? 0)} records</h4>
              <pre className="wksp-export-json">{JSON.stringify((exportResult.records as unknown[] | undefined)?.slice(0, 3), null, 2)}</pre>
              <p className="wksp-muted">Showing first 3 of {String(exportResult.record_count ?? 0)} records.</p>
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
.wksp-import-mapping { margin: 10px 0; }
.wksp-import-mapping-title { font-size: 12px; font-weight: 600; margin-bottom: 6px; color: var(--shunya-text); }
.wksp-mapping-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.wksp-mapping-table th { text-align: left; font-weight: 500; color: var(--shunya-text-secondary); padding: 4px 6px; border-bottom: 1px solid var(--shunya-surface-1); }
.wksp-mapping-table td { padding: 4px 6px; border-bottom: 1px solid var(--shunya-surface-1); vertical-align: top; }
.wksp-mapping-why { color: var(--shunya-text-secondary); }
.wksp-mapping-method { color: var(--shunya-text-secondary); font-style: italic; }
.wksp-mapping-conflict { background: rgba(245,166,35,0.06); }
.wksp-mapping-conflict-note { color: #b07a1e; }
.wksp-input-xs { font-size: 12px; padding: 2px 6px; }
.wksp-import-ambiguities, .wksp-import-similar { background: rgba(245,166,35,0.05); border: 1px solid rgba(245,166,35,0.25); border-radius: 6px; padding: 8px 10px; margin: 8px 0; }
.wksp-import-similar { background: rgba(74,158,158,0.05); border-color: rgba(74,158,158,0.25); }
.wksp-ambiguity-title { font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 5px; margin-bottom: 4px; }
.wksp-ambiguity-row { font-size: 12px; color: var(--shunya-text-secondary); padding: 2px 0; line-height: 1.45; }
.wksp-import-records { max-height: 300px; overflow-y: auto; margin: 8px 0; border: 1px solid var(--shunya-surface-1); border-radius: 4px; }
.wksp-import-row { padding: 4px 8px; font-size: 12px; border-bottom: 1px solid var(--shunya-surface-1); }
.wksp-import-invalid { color: #f88; }
.wksp-import-err-detail { color: #f88; font-size: 11px; }
.wksp-import-warn-detail { color: #b07a1e; font-size: 11px; }
.wksp-import-basis { color: var(--shunya-text-secondary); font-size: 11px; }
.wksp-import-more { text-align: center; padding: 4px; font-size: 11px; color: var(--shunya-text-secondary); }
.wksp-import-btns { display: flex; gap: 8px; margin-top: 8px; }
.wksp-btn-primary { background: var(--shunya-color-accent, #7c3aed); color: #fff; }
.wksp-btn-sm { font-size: 12px; padding: 4px 10px; display: inline-flex; align-items: center; gap: 4px; }
.wksp-import-result { background: var(--shunya-surface-2); padding: 12px; border-radius: 6px; margin-top: 8px; }
.wksp-import-result h4 { font-size: 13px; font-weight: 600; margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
.wksp-import-result-errors { margin-top: 6px; }
.wksp-import-err { color: #f88; font-size: 12px; padding: 2px 0; }
.wksp-import-error { color: #f88; padding: 8px; background: rgba(239,68,68,0.1); border-radius: 4px; margin-bottom: 8px; }
.wksp-warning { color: #f5a623; font-size: 12px; margin-top: 4px; }
.wksp-export-json { background: var(--shunya-surface-1); padding: 8px; border-radius: 4px; font-size: 11px; overflow-x: auto; max-height: 200px; }
.wksp-loading-text { text-align: center; padding: 20px; color: var(--shunya-text-secondary); }
.wksp-muted { color: var(--shunya-text-secondary); font-size: 11px; margin-top: 4px; }
.wksp-import-created, .wksp-import-skipped { margin: 8px 0; }
.wksp-created-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 12px; padding: 4px 0; border-bottom: 1px solid var(--shunya-surface-1); }
.wksp-prov { margin-top: 10px; border: 1px solid var(--shunya-surface-1); border-radius: 6px; background: var(--shunya-surface-2); }
.wksp-prov-head { display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-bottom: 1px solid var(--shunya-surface-1); }
.wksp-prov-title { font-size: 12px; font-weight: 600; }
.wksp-prov-close { background: none; border: none; cursor: pointer; color: var(--shunya-text-secondary); display: flex; }
.wksp-prov-body { padding: 8px 10px; display: flex; flex-direction: column; gap: 6px; }
.wksp-prov-line { font-size: 12px; line-height: 1.5; }
.wksp-prov-corrections { margin-top: 4px; }
.wksp-prov-correct { margin-top: 6px; display: flex; flex-direction: column; gap: 6px; }
.wksp-prov-correct-row { display: flex; gap: 6px; }
.wksp-prov-reason { width: 100%; }
.wksp-prov-notice { color: #2e7d32; font-size: 12px; }
@keyframes wksp-prov-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
.wksp-prov { animation: wksp-prov-in .18s ease-out; }
@media (max-width: 640px) {
  .wksp-mapping-table th:nth-child(3), .wksp-mapping-table td:nth-child(3) { display: none; }
  .wksp-prov-correct-row { flex-direction: column; }
}
      `}</style>
    </div>
  );
};
