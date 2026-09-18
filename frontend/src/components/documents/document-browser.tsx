/**
 * DocumentBrowser — Browse, search, and open documents in the current context.
 *
 * Fetches from /api/v1/workspace/documents with the authenticated context.
 * Opens files inline via detail panel or direct navigation for PDFs.
 */
import { useState, useCallback, useEffect, type FC } from 'react';
import { AddToShunya } from '../ingestion/add-to-shunya';
import { IconBook, IconChartBar, IconClipboard, IconFileText, IconPhoto, IconFolder } from '@tabler/icons-react';

// ── Types ──────────────────────────────────────────────────────────

interface Document {
  id: number;
  filename: string;
  file_type: string;
  classification: string;
  created_at: string | null;
  size: number;
}

// ── Helpers ──────────────────────────────────────────────────────

const FILE_ICONS: Record<string, React.ReactNode> = {
  pdf: <IconBook size={24} />, xlsx: <IconChartBar size={24} />, csv: <IconClipboard size={24} />,
  text: <IconFileText size={24} />, png: <IconPhoto size={24} />, jpg: <IconPhoto size={24} />,
};

function formatSize(bytes: number): string {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(d: string | null): string {
  if (!d) return '';
  const date = new Date(d);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  if (diff < 86400000) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (diff < 604800000) return date.toLocaleDateString([], { weekday: 'short' });
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

// ── Document Intelligence (Block D) ──────────────────────────────

interface DocIntelligence {
  classification: string;
  confidence: number;
  reason: string;
  signals: string[];
  entities: Record<string, Array<{ value: string; confidence?: number }>>;
  entity_count: number;
  analysed_at: string;
  engine: string;
}

const ENTITY_LABELS: Record<string, string> = {
  persons: 'People', amounts: 'Amounts', dates: 'Dates', emails: 'Emails',
  phones: 'Phones', references: 'References', organizations: 'Organisations',
};

function IntelligencePanel({ doc }: { doc: Document }) {
  const [intel, setIntel] = useState<DocIntelligence | null>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'none' | 'error'>('loading');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setState('loading');
    setError('');
    try {
      const r = await fetch(`/api/v1/workspace/documents/${doc.id}/intelligence`, { credentials: 'include' });
      const data = await r.json();
      if (!r.ok || !data.success) {
        setError(data.error || `Could not load intelligence (${r.status}).`);
        setState('error');
        return;
      }
      if (data.analysed && data.intelligence) {
        setIntel(data.intelligence);
        setState('ready');
      } else {
        setState('none');
      }
    } catch {
      setError('Could not reach the intelligence service.');
      setState('error');
    }
  }, [doc.id]);

  useEffect(() => { load(); }, [load]);

  const analyse = useCallback(async () => {
    setBusy(true);
    setError('');
    try {
      const r = await fetch(`/api/v1/workspace/documents/${doc.id}/classify`, {
        method: 'POST',
        credentials: 'include',
      });
      const data = await r.json();
      if (!r.ok || !data.success) {
        setError(data.error || `Identification failed (${r.status}).`);
        setState('error');
        return;
      }
      setIntel(data.intelligence);
      setState('ready');
    } catch {
      setError('Could not reach the intelligence service.');
      setState('error');
    } finally {
      setBusy(false);
    }
  }, [doc.id]);

  return (
    <div style={{
      border: '1px solid rgba(26,28,29,0.07)', borderRadius: 10,
      padding: 16, marginBottom: 16, background: 'rgba(26,28,29,0.015)',
    }} data-testid="doc-intelligence">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'rgba(26,28,29,0.45)' }}>
          Document Intelligence
        </span>
        {state === 'ready' && intel && (
          <span style={{ fontSize: 11, color: 'rgba(26,28,29,0.4)' }}>
            {Math.round(intel.confidence * 100)}% confidence
          </span>
        )}
      </div>

      {state === 'loading' && (
        <p style={{ margin: 0, fontSize: 13, color: 'rgba(26,28,29,0.5)' }}>Reading this document…</p>
      )}

      {state === 'error' && (
        <div style={{ fontSize: 13, color: '#d1453b' }}>
          {error}
          <button onClick={load} style={{ marginLeft: 10, fontSize: 12, cursor: 'pointer', background: 'none', border: '1px solid rgba(209,69,59,0.4)', borderRadius: 6, padding: '2px 10px', color: '#d1453b', fontFamily: 'inherit' }}>
            Retry
          </button>
        </div>
      )}

      {state === 'none' && (
        <div>
          <p style={{ margin: '0 0 10px', fontSize: 13, color: 'rgba(26,28,29,0.55)' }}>
            This document has not been identified yet.
          </p>
          <button
            onClick={analyse}
            disabled={busy}
            style={{
              padding: '7px 16px', borderRadius: 6, fontSize: 13, fontWeight: 500,
              background: '#1a1c1d', color: '#fff', border: 'none',
              cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1,
              fontFamily: 'inherit',
            }}
          >
            {busy ? 'Identifying…' : 'Identify document'}
          </button>
        </div>
      )}

      {state === 'ready' && intel && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span style={{
              fontSize: 12, fontWeight: 600, textTransform: 'capitalize',
              padding: '3px 10px', borderRadius: 999,
              background: 'rgba(26,28,29,0.06)', color: '#1a1c1d',
            }} data-testid="doc-classification">
              {intel.classification}
            </span>
            <span style={{ fontSize: 12, color: 'rgba(26,28,29,0.5)' }}>{intel.reason}</span>
          </div>

          {intel.signals.length > 0 && (
            <div style={{ fontSize: 11, color: 'rgba(26,28,29,0.4)', marginBottom: 10 }}>
              Signals: {intel.signals.join(' · ')}
            </div>
          )}

          {intel.entity_count === 0 ? (
            <p style={{ margin: '6px 0 0', fontSize: 13, color: 'rgba(26,28,29,0.45)' }}>
              No structured entities were found in this document.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {Object.entries(intel.entities).map(([key, items]) => (
                <div key={key} style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                  <span style={{ fontSize: 11, color: 'rgba(26,28,29,0.45)', minWidth: 92, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {ENTITY_LABELS[key] || key}
                  </span>
                  <span style={{ fontSize: 13, color: '#1a1c1d', wordBreak: 'break-word' }}>
                    {items.slice(0, 6).map((e) => e.value).join(', ')}
                    {items.length > 6 ? ` +${items.length - 6}` : ''}
                  </span>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={analyse}
            disabled={busy}
            style={{
              marginTop: 12, fontSize: 12, cursor: busy ? 'default' : 'pointer',
              background: 'none', border: '1px solid rgba(26,28,29,0.12)',
              borderRadius: 6, padding: '4px 12px', color: 'rgba(26,28,29,0.6)',
              fontFamily: 'inherit',
            }}
          >
            {busy ? 'Re-identifying…' : 'Re-identify'}
          </button>
        </div>
      )}
    </div>
  );
}

// ── Document Detail Panel ──────────────────────────────────────────

function DocumentDetail({ doc, onBack }: { doc: Document; onBack: () => void }) {
  const isViewable = doc.file_type === 'pdf' || doc.file_type === 'png' || doc.file_type === 'jpg';
  const url = `/api/v1/workspace/documents/serve/${doc.id}`;

  return (
    <div style={{ padding: '24px 32px', maxWidth: 800 }}>
      <button
        onClick={onBack}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          padding: '6px 12px', borderRadius: 6, fontSize: 13,
          color: 'rgba(26,28,29,0.55)', fontFamily: 'inherit',
        }}
      >
        ← Back to Documents
      </button>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        margin: '12px 0 16px',
      }}>
        <span style={{ fontSize: 32 }}>{FILE_ICONS[doc.file_type] || <IconFileText size={32} />}</span>
        <div>
          <h2 style={{ margin: '0 0 2px', fontSize: 18, fontWeight: 600, color: '#1a1c1d' }}>
            {doc.filename}
          </h2>
          <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'rgba(26,28,29,0.45)' }}>
            <span>{doc.file_type.toUpperCase()}</span>
            {doc.size > 0 && <span>{formatSize(doc.size)}</span>}
            <span>{doc.classification}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: '8px 18px', borderRadius: 6, fontSize: 13, fontWeight: 500,
            background: '#1a1c1d', color: '#fff', textDecoration: 'none',
            fontFamily: 'inherit',
          }}
        >
          Open in New Tab
        </a>
      </div>

      <IntelligencePanel doc={doc} />

      {isViewable && (
        <div style={{
          border: '1px solid rgba(26,28,29,0.07)', borderRadius: 10,
          overflow: 'hidden', background: 'rgba(26,28,29,0.02)',
        }}>
          {doc.file_type === 'pdf' ? (
            <iframe
              src={url}
              title={doc.filename}
              style={{ width: '100%', height: '70vh', border: 'none' }}
            />
          ) : (
            <img src={url} alt={doc.filename} style={{ maxWidth: '100%', height: 'auto' }} />
          )}
        </div>
      )}

      {!isViewable && (
        <div style={{
          padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.35)',
          border: '1px dashed rgba(26,28,29,0.1)', borderRadius: 10,
          fontSize: 13,
        }}>
          Preview not available for {doc.file_type.toUpperCase()} files.
          <br />
          <a href={url} target="_blank" rel="noopener noreferrer"
            style={{ color: '#1a72e8', marginTop: 8, display: 'inline-block' }}>
            Download file
          </a>
        </div>
      )}
    </div>
  );
}

// ── Main DocumentBrowser Component ────────────────────────────────

export const DocumentBrowser: FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [contextInfo, setContextInfo] = useState<string>('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const r = await fetch('/api/v1/workspace/documents?limit=50', { credentials: 'include' });
      const data = await r.json();
      if (data.success) {
        setDocuments(data.documents || []);
        setContextInfo(data.context?.context_type === 'organization' ? 'Panchi Club' : 'Personal Workspace');
      } else {
        setError(data.error || 'Failed to load documents');
      }
    } catch {
      setError('Could not connect to server');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (selectedDoc) {
    return <DocumentDetail doc={selectedDoc} onBack={() => setSelectedDoc(null)} />;
  }

  return (
    <div style={{ padding: '24px 32px', maxWidth: 800 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: '0 0 4px', fontSize: 20, fontWeight: 600, color: '#1a1c1d' }}>
            Documents
          </h2>
          <p style={{ margin: 0, fontSize: 13, color: 'rgba(26,28,29,0.55)' }}>
            {contextInfo ? `Showing documents in ${contextInfo}` : 'Your documents and files'}
          </p>
        </div>
      </div>

      <AddToShunya contextType={contextInfo === 'Panchi Club' ? 'organization' : 'personal'} />

      {loading && (
        <div style={{ padding: 40, textAlign: 'center', color: 'rgba(26,28,29,0.55)', fontSize: 14 }}>
          Loading documents…
        </div>
      )}

      {error && (
        <div style={{ padding: 20, textAlign: 'center', color: '#d1453b', fontSize: 13 }}>
          {error}
        </div>
      )}

      {!loading && !error && documents.length === 0 && (
        <div style={{
          padding: 40, textAlign: 'center',
          background: 'rgba(26,28,29,0.02)', borderRadius: 10,
          border: '1px dashed rgba(26,28,29,0.1)',
        }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}><IconFolder size={32} /></div>
          <p style={{ fontSize: 14, color: 'rgba(26,28,29,0.55)', margin: 0 }}>
            No documents yet. Use "Add to My SHUNYA" to upload files.
          </p>
        </div>
      )}

      {!loading && !error && documents.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {documents.map(doc => (
            <div
              key={doc.id}
              onClick={() => setSelectedDoc(doc)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 16px',
                background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
                borderRadius: 10, cursor: 'pointer',
              }}
              title={`Open ${doc.filename}`}
            >
              <span style={{ fontSize: 24 }}>{FILE_ICONS[doc.file_type] || <IconFileText size={24} />}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#1a1c1d', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {doc.filename}
                </div>
                <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'rgba(26,28,29,0.45)', marginTop: 2 }}>
                  <span>{doc.file_type.toUpperCase()}</span>
                  {doc.size > 0 && <span>{formatSize(doc.size)}</span>}
                  <span>{formatDate(doc.created_at)}</span>
                </div>
              </div>
              <span style={{ fontSize: 11, color: 'rgba(26,28,29,0.35)', textTransform: 'uppercase' }}>
                {doc.classification}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentBrowser;