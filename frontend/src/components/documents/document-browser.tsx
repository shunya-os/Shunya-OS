/**
 * DocumentBrowser — Browse, search, and open documents in the current context.
 *
 * Fetches from /api/v1/documents with the authenticated context.
 * Opens files via /api/v1/documents/serve/<id>.
 */
import { useState, useEffect, useCallback, type FC } from 'react';

interface Document {
  id: number;
  filename: string;
  file_type: string;
  classification: string;
  created_at: string | null;
  size: number;
}

const FILE_ICONS: Record<string, string> = {
  pdf: '📕',
  xlsx: '📊',
  csv: '📋',
  text: '📄',
  docx: '📝',
  png: '🖼️',
  jpg: '🖼️',
  jpeg: '🖼️',
};

function formatSize(bytes: number): string {
  if (bytes === 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return dateStr; }
}

export const DocumentBrowser: FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [contextInfo, setContextInfo] = useState<string>('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const r = await fetch('/api/v1/workspace/documents?limit=50', { credentials: 'include' });
      const data = await r.json();
      if (data.success) {
        setDocuments(data.documents || []);
        if (data.context?.context_type === 'organization') {
          setContextInfo('Panchi Club');
        } else {
          setContextInfo('Personal Workspace');
        }
      } else {
        setError(data.error || 'Failed to load documents');
      }
    } catch {
      setError('Could not connect');
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleOpen = (doc: Document) => {
    window.open(`/api/v1/workspace/documents/serve/${doc.id}`, '_blank');
  };

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
              onClick={() => handleOpen(doc)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 16px',
                background: '#fff', border: '1px solid rgba(26,28,29,0.07)',
                borderRadius: 10, cursor: 'pointer',
                transition: 'box-shadow 0.15s ease',
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