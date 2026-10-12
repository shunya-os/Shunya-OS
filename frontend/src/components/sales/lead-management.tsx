/**
 * LeadManagement — full Sales lead lifecycle (ZG-03 B1).
 *
 * Capabilities: list, search, status filters, add, detail + history,
 * edit, status transitions (general + canonical won/lost), CSV/XLSX import
 * with preview and a trustworthy commit summary.
 *
 * Every action traces UI → API → authorization → persistence → refreshed UI.
 * The backend is tenant-scoped (ZG-03 P0); cross-tenant ids 404 and surface
 * as "not available in your organization" — never as a data leak.
 * Mobile-responsive; SHUNYA visual language (calm surfaces, inline styles).
 */

import { useCallback, useEffect, useRef, useState, type FC, type ChangeEvent, type FormEvent } from 'react';

interface Lead {
  id: number;
  code: string;
  source: string;
  customer_name: string;
  phone: string;
  email: string;
  destination: string;
  budget: number;
  status: string;
  stage: string;
  assigned_to: string;
  outcome: string;
  notes: string;
  created_at: string | null;
  updated_at?: string | null;
}

interface LeadDetail extends Lead {
  pax?: string;
  dates?: string;
  person_id?: number | null;
}

interface Activity {
  id: number;
  lead_id: number;
  action: string;
  detail: string;
  user: string;
  created_at: string | null;
}

interface ApiError { error?: string; code?: string }

async function apiFetch<T = unknown>(path: string, opts?: RequestInit): Promise<{ status: number; data: T | null }> {
  try {
    const r = await fetch(path, {
      credentials: 'include',
      ...(opts?.body ? { headers: { 'Content-Type': 'application/json' } } : {}),
      ...opts,
    });
    let data: T | null = null;
    try { data = (await r.json()) as T; } catch { data = null; }
    return { status: r.status, data };
  } catch {
    return { status: -1, data: null };
  }
}

const STATUS_COLORS: Record<string, string> = {
  new: 'rgba(26,28,29,0.35)',
  contacted: '#a4865f',
  qualified: '#2e7d32',
  proposal: '#1a73e8',
  negotiation: '#c97b2d',
  on_hold: '#795548',
  won: '#2e7d32',
  converted: '#2e7d32',
  lost: '#d1453b',
  cancelled: '#d1453b',
};

const GENERAL_STATUSES = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'on_hold'];
const SOURCES = ['manual', 'api', 'email', 'telegram', 'whatsapp', 'instagram', 'import', 'direct'];

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

interface FormState {
  customer_name: string;
  phone: string;
  email: string;
  source: string;
  destination: string;
  pax: string;
  dates: string;
  budget: string;
  assigned_to: string;
  notes: string;
}

const EMPTY_FORM: FormState = {
  customer_name: '', phone: '', email: '', source: 'manual', destination: '',
  pax: '', dates: '', budget: '', assigned_to: '', notes: '',
};

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px 10px', borderRadius: 8, fontSize: 13,
  border: '1px solid rgba(26,28,29,0.14)', background: '#fff', boxSizing: 'border-box',
};

const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(26,28,29,0.55)',
  marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.4,
};

const btnStyle = (primary?: boolean): React.CSSProperties => ({
  padding: '7px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer',
  border: `1px solid ${primary ? '#a4865f' : 'rgba(26,28,29,0.14)'}`,
  background: primary ? '#a4865f' : '#fff',
  color: primary ? '#fff' : 'rgba(26,28,29,0.75)',
});

// ── Lead form (add / edit) ──────────────────────────────────────────────

const LeadForm: FC<{
  initial: FormState; title: string; submitting: boolean; error: string;
  onSubmit: (f: FormState) => void; onClose: () => void;
}> = ({ initial, title, submitting, error, onSubmit, onClose }) => {
  const [form, setForm] = useState<FormState>(initial);
  const set = (k: keyof FormState) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }));

  return (
    <div role="dialog" aria-label={title} style={{
      position: 'fixed', inset: 0, background: 'rgba(26,28,29,0.35)', zIndex: 60,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }} onClick={onClose}>
      <form onClick={e => e.stopPropagation()} onSubmit={(e: FormEvent) => { e.preventDefault(); onSubmit(form); }}
        style={{ background: '#fff', borderRadius: 14, padding: 22, width: '100%', maxWidth: 480, maxHeight: '90vh', overflowY: 'auto' }}>
        <h3 style={{ margin: '0 0 14px', fontSize: 17, fontWeight: 600 }}>{title}</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={labelStyle} htmlFor="lf-name">Name *</label>
            <input id="lf-name" required style={inputStyle} value={form.customer_name} onChange={set('customer_name')} autoFocus />
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-phone">Phone</label>
            <input id="lf-phone" style={inputStyle} value={form.phone} onChange={set('phone')} />
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-email">Email</label>
            <input id="lf-email" type="email" style={inputStyle} value={form.email} onChange={set('email')} />
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-source">Source</label>
            <select id="lf-source" style={inputStyle} value={form.source} onChange={set('source')}>
              {SOURCES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-dest">Destination</label>
            <input id="lf-dest" style={inputStyle} value={form.destination} onChange={set('destination')} />
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-pax">Pax</label>
            <input id="lf-pax" style={inputStyle} value={form.pax} onChange={set('pax')} />
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-dates">Dates</label>
            <input id="lf-dates" style={inputStyle} value={form.dates} onChange={set('dates')} placeholder="e.g. 10-14 Jan 2027" />
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-budget">Budget</label>
            <input id="lf-budget" style={inputStyle} value={form.budget} onChange={set('budget')} inputMode="decimal" />
          </div>
          <div>
            <label style={labelStyle} htmlFor="lf-owner">Owner</label>
            <input id="lf-owner" style={inputStyle} value={form.assigned_to} onChange={set('assigned_to')} />
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={labelStyle} htmlFor="lf-notes">Notes</label>
            <textarea id="lf-notes" style={{ ...inputStyle, minHeight: 64, resize: 'vertical' }} value={form.notes} onChange={set('notes')} />
          </div>
        </div>
        {error && <p role="alert" style={{ color: '#d1453b', fontSize: 12, margin: '10px 0 0' }}>{error}</p>}
        <div style={{ display: 'flex', gap: 8, marginTop: 16, justifyContent: 'flex-end' }}>
          <button type="button" style={btnStyle()} onClick={onClose}>Cancel</button>
          <button type="submit" style={btnStyle(true)} disabled={submitting}>
            {submitting ? 'Saving…' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
};

// ── Import panel ────────────────────────────────────────────────────────

interface ImportPreview {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  new_identities: number;
  matched_identities: number;
  possible_duplicates: number;
  conflicts: number;
  records_to_create: number;
  records_to_update: number;
  records_rejected: number;
  weak_identity_rows: number[];
  column_mapping: Array<{ source_column: string; target_field: string; method: string; confidence?: number }>;
  ambiguities: Array<{ code?: string; message?: string; detail?: string }>;
  requires_review: boolean;
  records: Array<{ row?: number; valid?: boolean; errors?: string[]; commit_action?: string; reasons?: string[] }>;
}

interface CommitResult {
  status?: string;
  created?: number;
  updated?: number;
  rejected?: number;
  duplicates_skipped?: number;
  warning?: string;
  errors?: Array<string | { error?: string }>;
}

const ImportPanel: FC<{ onClose: () => void; onCommitted: () => void }> = ({ onClose, onCommitted }) => {
  const [fileName, setFileName] = useState('');
  const [content, setContent] = useState('');
  const [contentType, setContentType] = useState<'csv' | 'xlsx'>('csv');
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [commitResult, setCommitResult] = useState<CommitResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const onFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setError('');
    setPreview(null);
    setCommitResult(null);
    const isXlsx = /\.xlsx?$/i.test(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      if (isXlsx) {
        setContentType('xlsx');
        setContent(result.split(',')[1] || ''); // base64 payload after data: prefix
      } else {
        setContentType('csv');
        setContent(result);
      }
    };
    if (isXlsx) reader.readAsDataURL(file); else reader.readAsText(file);
  };

  const doPreview = async () => {
    if (!content) { setError('Choose a CSV or XLSX file first.'); return; }
    setBusy(true); setError('');
    const { status, data } = await apiFetch<{ success?: boolean; data?: ImportPreview } & ApiError>('/api/v1/data/import/preview', {
      method: 'POST',
      body: JSON.stringify({ content, content_type: contentType, target_type: 'lead', source_name: fileName }),
    });
    setBusy(false);
    if (status === 200 && data?.success && data.data) setPreview(data.data);
    else if (status === 403) setError("You don't have permission to import data.");
    else setError(data?.error || `Preview failed (status ${status}).`);
  };

  const doCommit = async () => {
    setBusy(true); setError('');
    const { status, data } = await apiFetch<{ success?: boolean; data?: CommitResult } & ApiError>('/api/v1/data/import/commit', {
      method: 'POST',
      body: JSON.stringify({ content, content_type: contentType, target_type: 'lead', source_name: fileName }),
    });
    setBusy(false);
    if (status === 200 || status === 201) {
      setCommitResult(data?.data || {});
      onCommitted();
    } else if (status === 400) {
      setCommitResult(data?.data || { status: 'rejected', errors: [{ error: data?.error || 'All rows rejected' }] });
    } else if (status === 403) {
      setError("You don't have permission to import data.");
    } else {
      setError(data?.error || `Import failed (status ${status}).`);
    }
  };

  return (
    <div role="dialog" aria-label="Import leads" style={{
      position: 'fixed', inset: 0, background: 'rgba(26,28,29,0.35)', zIndex: 60,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: '#fff', borderRadius: 14, padding: 22, width: '100%', maxWidth: 640,
        maxHeight: '90vh', overflowY: 'auto',
      }}>
        <h3 style={{ margin: '0 0 6px', fontSize: 17, fontWeight: 600 }}>Import leads</h3>
        <p style={{ fontSize: 12, color: 'rgba(26,28,29,0.55)', margin: '0 0 14px' }}>
          CSV or XLSX. Nothing is written until you commit after reviewing the preview.
        </p>
        <input aria-label="Import file" type="file" accept=".csv,.xlsx,.xls" onChange={onFile} style={{ fontSize: 12 }} />
        {fileName && <p style={{ fontSize: 12, margin: '8px 0 0', color: 'rgba(26,28,29,0.6)' }}>File: {fileName}</p>}

        {!preview && !commitResult && (
          <div style={{ marginTop: 14 }}>
            <button style={btnStyle(true)} onClick={doPreview} disabled={busy}>
              {busy ? 'Inspecting…' : 'Preview import'}
            </button>
          </div>
        )}

        {preview && !commitResult && (
          <div style={{ marginTop: 14 }}>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', fontSize: 12 }}>
              <span><b>{preview.total_records}</b> rows</span>
              <span style={{ color: '#2e7d32' }}><b>{preview.valid_records}</b> valid</span>
              <span style={{ color: preview.invalid_records ? '#d1453b' : 'inherit' }}><b>{preview.invalid_records}</b> invalid</span>
              <span><b>{preview.records_to_create}</b> to create</span>
              <span><b>{preview.records_to_update}</b> to update</span>
              <span><b>{preview.records_rejected}</b> to reject</span>
              {preview.possible_duplicates > 0 && <span><b>{preview.possible_duplicates}</b> possible dupes</span>}
              {preview.conflicts > 0 && <span><b>{preview.conflicts}</b> conflicts</span>}
            </div>
            {preview.column_mapping?.length > 0 && (
              <details style={{ marginTop: 10 }}>
                <summary style={{ fontSize: 12, cursor: 'pointer' }}>Column mapping</summary>
                <ul style={{ fontSize: 12, margin: '6px 0 0', paddingLeft: 18 }}>
                  {preview.column_mapping.map((m, i) => (
                    <li key={i}>{m.source_column} → <b>{m.target_field || '(not imported)'}</b> <span style={{ color: 'rgba(26,28,29,0.45)' }}>({m.method})</span></li>
                  ))}
                </ul>
              </details>
            )}
            {preview.ambiguities?.length > 0 && (
              <p style={{ fontSize: 12, color: '#c97b2d', margin: '10px 0 0' }}>
                {preview.ambiguities.length} ambiguit{preview.ambiguities.length === 1 ? 'y' : 'ies'} need review.
              </p>
            )}
            {preview.records?.length > 0 && (
              <details style={{ marginTop: 8 }}>
                <summary style={{ fontSize: 12, cursor: 'pointer' }}>Rows (first {preview.records.length})</summary>
                <ul style={{ fontSize: 12, margin: '6px 0 0', paddingLeft: 18 }}>
                  {preview.records.slice(0, 10).map((r, i) => (
                    <li key={i}>
                      row {r.row ?? i + 1}: {r.commit_action || (r.valid === false ? 'reject' : 'create')}
                      {r.errors?.length ? ` — ${r.errors.join('; ')}` : ''}
                    </li>
                  ))}
                </ul>
              </details>
            )}
            <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
              <button style={btnStyle(true)} onClick={doCommit} disabled={busy || preview.total_records === 0}>
                {busy ? 'Importing…' : `Commit import (${preview.records_to_create} create / ${preview.records_to_update} update)`}
              </button>
              <button style={btnStyle()} onClick={() => setPreview(null)} disabled={busy}>Choose another file</button>
            </div>
          </div>
        )}

        {commitResult && (
          <div style={{ marginTop: 14 }}>
            <p style={{ fontSize: 13, fontWeight: 600, color: commitResult.status === 'completed' ? '#2e7d32' : commitResult.status === 'rejected' ? '#d1453b' : '#c97b2d' }}>
              Import {commitResult.status}: {commitResult.created ?? 0} created · {commitResult.updated ?? 0} updated · {commitResult.rejected ?? 0} rejected · {commitResult.duplicates_skipped ?? 0} duplicates skipped
            </p>
            {commitResult.warning && <p style={{ fontSize: 12 }}>{commitResult.warning}</p>}
            {commitResult.errors && commitResult.errors.length > 0 && (
              <ul style={{ fontSize: 12, color: '#d1453b', paddingLeft: 18 }}>
                {commitResult.errors.slice(0, 10).map((e, i) => (
                  <li key={i}>{typeof e === 'string' ? e : (e.error || JSON.stringify(e))}</li>
                ))}
              </ul>
            )}
            <button style={btnStyle(true)} onClick={onClose}>Done</button>
          </div>
        )}

        {error && <p role="alert" style={{ color: '#d1453b', fontSize: 12, marginTop: 10 }}>{error}</p>}
        <div style={{ marginTop: 14, textAlign: 'right' }}>
          <button style={btnStyle()} onClick={onClose} disabled={busy}>Close</button>
        </div>
      </div>
    </div>
  );
};

// ── Main component ──────────────────────────────────────────────────────

export const LeadManagement: FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<LeadDetail | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  const [showAdd, setShowAdd] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [editing, setEditing] = useState(false);
  const [formBusy, setFormBusy] = useState(false);
  const [formError, setFormError] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  const [lostReason, setLostReason] = useState('');
  const [showLost, setShowLost] = useState(false);

  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced search → server-side q param (tenant-scoped)
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setQuery(search.trim()), 300);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [search]);

  const loadLeads = useCallback(async () => {
    setLoading(true);
    setError('');
    const params = new URLSearchParams();
    if (filter !== 'all' && filter !== 'active') params.set('status', filter);
    if (query) params.set('q', query);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const { status, data } = await apiFetch<{ leads?: Lead[] }>(`/api/v1/leads/${suffix}`);
    if (status === 200 && data?.leads) {
      setLeads(data.leads);
    } else if (status === 403) {
      setError("You don't have permission to view leads.");
    } else {
      setError('Could not load leads. Retry.');
    }
    setLoading(false);
  }, [filter, query]);

  useEffect(() => { loadLeads(); }, [loadLeads]);

  const openDetail = useCallback(async (id: number) => {
    setSelectedId(id);
    setDetail(null);
    setDetailError('');
    setDetailLoading(true);
    setShowLost(false);
    setLostReason('');
    const [d, a] = await Promise.all([
      apiFetch<{ lead?: LeadDetail }>(`/api/v1/leads/${id}`),
      apiFetch<Activity[]>(`/leads/${id}/activities`),
    ]);
    if (d.status === 200 && d.data?.lead) {
      setDetail(d.data.lead);
      setActivities(Array.isArray(a.data) ? a.data : []);
    } else if (d.status === 404) {
      setDetailError('This lead is not available in your organization.');
    } else if (d.status === 403) {
      setDetailError("You don't have permission to view this lead.");
    } else {
      setDetailError('Could not load the lead.');
    }
    setDetailLoading(false);
  }, []);

  const refreshAll = useCallback(async (id: number | null) => {
    await loadLeads();
    if (id != null) await openDetail(id);
  }, [loadLeads, openDetail]);

  const addLead = async (f: FormState) => {
    setFormBusy(true); setFormError('');
    const { status, data } = await apiFetch<{ id?: number; code?: string; success?: boolean } & ApiError>('/api/v1/leads/', {
      method: 'POST',
      body: JSON.stringify({
        customer_name: f.customer_name, phone: f.phone, email: f.email,
        source: f.source || 'manual', destination: f.destination,
        pax: f.pax, budget: f.budget ? Number(f.budget) : 0,
        notes: f.notes, assigned_to: f.assigned_to,
      }),
    });
    setFormBusy(false);
    if (status === 200 && data?.id) {
      setShowAdd(false);
      setActionMsg(`Lead ${data.code || ''} created.`);
      await loadLeads();
      await openDetail(data.id);
    } else if (status === 403) {
      setFormError("You don't have permission to create leads.");
    } else {
      setFormError(data?.error || `Could not create the lead (status ${status}).`);
    }
  };

  const saveEdit = async (f: FormState) => {
    if (selectedId == null) return;
    setFormBusy(true); setFormError('');
    const { status, data } = await apiFetch<ApiError>(`/api/v1/leads/${selectedId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        customer_name: f.customer_name, phone: f.phone, email: f.email,
        source: f.source, destination: f.destination, pax: f.pax,
        dates: f.dates, budget: f.budget ? Number(f.budget) : 0,
        assigned_to: f.assigned_to, notes: f.notes,
      }),
    });
    setFormBusy(false);
    if (status === 200) {
      setEditing(false);
      setActionMsg('Lead updated.');
      await refreshAll(selectedId);
    } else if (status === 403) {
      setFormError("You don't have permission to edit leads.");
    } else {
      setFormError(data?.error || `Could not save (status ${status}).`);
    }
  };

  const changeStatus = async (newStatus: string) => {
    if (selectedId == null) return;
    setActionMsg('');
    const { status, data } = await apiFetch<ApiError>(`/api/v1/leads/${selectedId}/status`, {
      method: 'POST',
      body: JSON.stringify({ status: newStatus }),
    });
    if (status === 200) {
      setActionMsg(`Status → ${newStatus}.`);
      await refreshAll(selectedId);
    } else {
      setActionMsg(data?.error || `Could not change status (status ${status}).`);
    }
  };

  const markWon = async () => {
    if (selectedId == null) return;
    const { status, data } = await apiFetch<ApiError>(`/api/v1/crm/leads/${selectedId}/won`, {
      method: 'POST', body: JSON.stringify({}),
    });
    if (status === 200) {
      setActionMsg('Lead won and converted to customer.');
      await refreshAll(selectedId);
    } else {
      setActionMsg(data?.error || `Could not mark won (status ${status}).`);
    }
  };

  const markLost = async () => {
    if (selectedId == null) return;
    const { status, data } = await apiFetch<ApiError>(`/api/v1/crm/leads/${selectedId}/lost`, {
      method: 'POST', body: JSON.stringify({ reason: lostReason || 'No reason provided' }),
    });
    if (status === 200) {
      setShowLost(false);
      setActionMsg('Lead marked lost.');
      await refreshAll(selectedId);
    } else {
      setActionMsg(data?.error || `Could not mark lost (status ${status}).`);
    }
  };

  const filtered = filter === 'active'
    ? leads.filter(l => l.status !== 'converted' && l.status !== 'lost' && l.status !== 'cancelled')
    : leads;

  const activeCount = leads.filter(l => l.status !== 'converted' && l.status !== 'lost' && l.status !== 'cancelled').length;
  const qualifiedCount = leads.filter(l => l.status === 'qualified').length;

  const editInitial: FormState = detail ? {
    customer_name: detail.customer_name, phone: detail.phone, email: detail.email,
    source: detail.source || 'manual', destination: detail.destination,
    pax: detail.pax || '', dates: detail.dates || '',
    budget: detail.budget ? String(detail.budget) : '',
    assigned_to: detail.assigned_to, notes: detail.notes,
  } : EMPTY_FORM;

  return (
    <div style={{ padding: 'clamp(16px, 3vw, 32px)', maxWidth: 1020 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 20 }}>⬡</span>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 600, flex: 1 }}>Leads</h2>
        <button style={btnStyle()} onClick={() => setShowImport(true)}>Import</button>
        <button style={btnStyle(true)} onClick={() => { setFormError(''); setShowAdd(true); }}>+ Add Lead</button>
      </div>
      <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: '4px 0 20px' }}>
        Customer inquiries, prospects, and pipeline
      </p>

      {/* Summary */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <div className="lead-summary-card">
          <div className="lead-summary-value">{leads.length}</div>
          <div className="lead-summary-label">Total</div>
        </div>
        <div className="lead-summary-card">
          <div className="lead-summary-value">{activeCount}</div>
          <div className="lead-summary-label">Active</div>
        </div>
        {qualifiedCount > 0 && (
          <div className="lead-summary-card">
            <div className="lead-summary-value" style={{ color: '#2e7d32' }}>{qualifiedCount}</div>
            <div className="lead-summary-label">Qualified</div>
          </div>
        )}
      </div>

      {/* Search + filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <input aria-label="Search leads" placeholder="Search name, code, phone, email…"
          value={search} onChange={e => setSearch(e.target.value)}
          style={{ ...inputStyle, maxWidth: 280 }} />
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {['all', 'active', 'new', 'contacted', 'qualified', 'won', 'lost'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              style={{
                padding: '4px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer',
                border: `1px solid ${filter === f ? '#a4865f' : 'rgba(26,28,29,0.06)'}`,
                background: filter === f ? 'rgba(164,134,95,0.1)' : 'transparent',
                color: filter === f ? '#a4865f' : 'rgba(26,28,29,0.55)',
              }}>
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {actionMsg && <p style={{ fontSize: 12, color: '#2e7d32', margin: '0 0 10px' }}>{actionMsg}</p>}

      {/* Content */}
      {loading && <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)' }}>Loading leads…</div>}
      {error && (
        <div style={{ padding: 40, textAlign: 'center', color: '#d1453b' }}>
          <p>{error}</p>
          <button style={btnStyle()} onClick={loadLeads}>Retry</button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div style={{ padding: 40, textAlign: 'center' }}>
          <p>{query ? `No leads match “${query}”.` : filter === 'all' ? 'No leads yet.' : `No ${filter} leads.`}</p>
          {!query && filter === 'all' && (
            <button style={btnStyle(true)} onClick={() => setShowAdd(true)}>Add your first lead</button>
          )}
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(l => (
            <div key={l.id} className="lead-item"
              role="button" tabIndex={0}
              onClick={() => openDetail(l.id)}
              onKeyDown={e => { if (e.key === 'Enter') openDetail(l.id); }}
              style={{
                background: '#fff', border: `1px solid ${selectedId === l.id ? '#a4865f' : 'rgba(26,28,29,0.07)'}`,
                borderRadius: 10, padding: '14px 16px', cursor: 'pointer',
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  backgroundColor: STATUS_COLORS[l.status] || 'rgba(26,28,29,0.35)',
                  display: 'inline-block', flexShrink: 0,
                }} />
                <span style={{ fontSize: 11, fontWeight: 600, color: 'rgba(26,28,29,0.35)', fontFamily: 'monospace' }}>{l.code}</span>
                <span style={{ flex: 1, fontSize: 14, fontWeight: 500, minWidth: 120 }}>{l.customer_name || 'Unknown'}</span>
                <span style={{
                  fontSize: 11, fontWeight: 500, textTransform: 'capitalize',
                  padding: '2px 8px', borderRadius: 6, background: 'rgba(26,28,29,0.04)', color: 'rgba(26,28,29,0.55)',
                }}>{l.stage || l.status}</span>
                <span style={{
                  fontSize: 11, fontWeight: 500, textTransform: 'uppercase',
                  color: STATUS_COLORS[l.status] || 'rgba(26,28,29,0.55)',
                }}>{l.status}</span>
              </div>
              <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6, fontSize: 11, color: 'rgba(26,28,29,0.45)' }}>
                <span>Source: {l.source}</span>
                {l.email && <span>{l.email}</span>}
                {l.destination && <span>Destination: {l.destination}</span>}
                {l.budget > 0 && <span>Budget: ${l.budget.toLocaleString()}</span>}
                {l.assigned_to && <span>Owner: {l.assigned_to}</span>}
                <span>Created: {_timeAgo(l.created_at)}</span>
              </div>
              {l.notes && <div style={{ fontSize: 11, color: 'rgba(26,28,29,0.55)', marginTop: 4, fontStyle: 'italic' }}>{l.notes}</div>}
            </div>
          ))}
        </div>
      )}

      {/* Detail panel */}
      {selectedId != null && (
        <div role="dialog" aria-label="Lead detail" style={{
          position: 'fixed', top: 0, right: 0, bottom: 0, width: 'min(440px, 100vw)',
          background: '#fff', boxShadow: '-8px 0 24px rgba(26,28,29,0.12)', zIndex: 50,
          padding: 20, overflowY: 'auto',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, flex: 1 }}>Lead detail</h3>
            <button style={btnStyle()} onClick={() => setSelectedId(null)}>Close</button>
          </div>

          {detailLoading && <p style={{ fontSize: 13, color: 'rgba(26,28,29,0.55)' }}>Loading…</p>}
          {detailError && <p style={{ fontSize: 13, color: '#d1453b' }}>{detailError}</p>}

          {detail && !detailLoading && (
            <>
              <p style={{ fontSize: 12, fontFamily: 'monospace', color: 'rgba(26,28,29,0.45)', margin: '0 0 8px' }}>{detail.code}</p>
              <p style={{ fontSize: 16, fontWeight: 600, margin: '0 0 4px' }}>{detail.customer_name || 'Unknown'}</p>
              <p style={{ fontSize: 12, color: 'rgba(26,28,29,0.55)', margin: '0 0 12px' }}>
                <span style={{ color: STATUS_COLORS[detail.status] || 'inherit', fontWeight: 600, textTransform: 'uppercase' }}>{detail.status}</span>
                {' · '}{detail.source}{detail.assigned_to ? ` · Owner: ${detail.assigned_to}` : ''}
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 12, marginBottom: 12 }}>
                {detail.phone && <span>📞 {detail.phone}</span>}
                {detail.email && <span>✉️ {detail.email}</span>}
                {detail.destination && <span>📍 {detail.destination}</span>}
                {detail.pax && <span>👥 {detail.pax}</span>}
                {detail.dates && <span>🗓 {detail.dates}</span>}
                {detail.budget > 0 && <span>💰 ${detail.budget.toLocaleString()}</span>}
              </div>
              {detail.notes && <p style={{ fontSize: 12, fontStyle: 'italic', color: 'rgba(26,28,29,0.6)', margin: '0 0 12px' }}>{detail.notes}</p>}

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                <button style={btnStyle()} onClick={() => { setFormError(''); setEditing(true); }}>Edit</button>
                <button style={btnStyle(true)} onClick={markWon}>Mark won</button>
                <button style={btnStyle()} onClick={() => setShowLost(v => !v)}>Mark lost</button>
              </div>

              {showLost && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                  <input aria-label="Lost reason" placeholder="Reason" value={lostReason}
                    onChange={e => setLostReason(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
                  <button style={btnStyle(true)} onClick={markLost}>Confirm</button>
                </div>
              )}

              <div style={{ marginBottom: 12 }}>
                <span style={labelStyle}>Change status</span>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {GENERAL_STATUSES.map(s => (
                    <button key={s} onClick={() => changeStatus(s)} disabled={detail.status === s}
                      style={{
                        padding: '4px 10px', borderRadius: 6, fontSize: 11, cursor: detail.status === s ? 'default' : 'pointer',
                        border: `1px solid ${detail.status === s ? '#a4865f' : 'rgba(26,28,29,0.12)'}`,
                        background: detail.status === s ? 'rgba(164,134,95,0.12)' : '#fff',
                        color: detail.status === s ? '#a4865f' : 'rgba(26,28,29,0.65)',
                      }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <h4 style={{ fontSize: 12, fontWeight: 600, color: 'rgba(26,28,29,0.55)', textTransform: 'uppercase', margin: '16px 0 8px' }}>
                History
              </h4>
              {activities.length === 0 && <p style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)' }}>No recorded activity yet.</p>}
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {activities.map(a => (
                  <li key={a.id} style={{ padding: '6px 0', borderBottom: '1px solid rgba(26,28,29,0.05)', fontSize: 12 }}>
                    <b>{a.action}</b>{a.detail ? ` — ${a.detail}` : ''}
                    <span style={{ color: 'rgba(26,28,29,0.4)' }}> · {_timeAgo(a.created_at)}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {editing && detail && (
            <LeadForm initial={editInitial} title={`Edit ${detail.code}`} submitting={formBusy}
              error={formError} onSubmit={saveEdit} onClose={() => setEditing(false)} />
          )}
        </div>
      )}

      {showAdd && (
        <LeadForm initial={EMPTY_FORM} title="Add Lead" submitting={formBusy}
          error={formError} onSubmit={addLead} onClose={() => setShowAdd(false)} />
      )}

      {showImport && (
        <ImportPanel onClose={() => setShowImport(false)} onCommitted={loadLeads} />
      )}

      <style>{`
.lead-summary-card {
  background: #fff;
  border: 1px solid rgba(26,28,29,0.07);
  border-radius: 10px;
  padding: 14px 18px;
  flex: 1;
  min-width: 80px;
}
.lead-summary-value { font-size: 22px; font-weight: 700; color: #1A1C1D; }
.lead-summary-label { font-size: 11px; color: rgba(26,28,29,0.55); margin-top: 2px; }
      `}</style>
    </div>
  );
};

export default LeadManagement;
