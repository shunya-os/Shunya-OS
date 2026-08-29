/**
 * DocumentBrowser — Browse, search, and open documents in the current context.
 *
 * Fetches from /api/v1/workspace/documents with the authenticated context.
 * Opens files inline via detail panel or direct navigation for PDFs.
 */
import { useState, useCallback, useEffect, type FC } from 'react';
import { AddToShunya } from '../ingestion/add-to-shunya';

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

const FILE_ICONS: Record<string, string> = {
  pdf: '📕', xlsx: '📊', csv: '📋', text: '📄', png: '🖼️', jpg: '🖼️',
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
        <span style={{ fontSize: 32 }}>{FILE_ICONS[doc.file_type] || '📄'}</span>
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
          <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
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
              <span style={{ fontSize: 24 }}>{FILE_ICONS[doc.file_type] || '📄'}</span>
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