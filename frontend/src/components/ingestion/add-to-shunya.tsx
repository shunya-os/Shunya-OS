/**
 * AddToShunya — Ingest a file into the current context (personal or organization).
 *
 * Shows target context clearly. After upload, shows a summary of what SHUNYA understood.
 */
import { useState, useRef, type FC } from 'react';

interface IngestResult {
  success: boolean;
  document_id?: number;
  filename?: string;
  file_type?: string;
  size?: number;
  summary?: string;
  context?: { context_type: string };
  error?: string;
}

export const AddToShunya: FC<{ contextType?: 'personal' | 'organization' }> = ({ contextType }) => {
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<'select' | 'uploading' | 'result' | 'error'>('select');
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);
  const isOrg = contextType === 'organization';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setPhase('uploading');
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      const r = await fetch('/api/v1/founder/ingest', {
        method: 'POST', credentials: 'include', body: formData,
      });
      const data: IngestResult = await r.json();
      if (data.success) {
        setResult(data);
        setPhase('result');
      } else {
        setError(data.error || 'Upload failed');
        setPhase('error');
      }
    } catch {
      setError('Could not connect to server');
      setPhase('error');
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setPhase('select');
    setError('');
    if (fileRef.current) fileRef.current.value = '';
  };

  const contextLabel = isOrg ? 'Adding to: Panchi Club' : 'Adding to: Nishesh\'s Personal Workspace';

  return (
    <div style={{
      padding: '16px 20px',
      background: 'rgba(164,134,95,0.06)',
      border: '1px solid rgba(164,134,95,0.15)',
      borderRadius: 10,
      marginBottom: 16,
    }}>
      {/* Context indicator */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        fontSize: 11, fontWeight: 500, color: '#a4865f',
        textTransform: 'uppercase', letterSpacing: '0.05em',
        marginBottom: 10,
      }}>
        <span style={{
          width: 6, height: 6, borderRadius: '50%',
          background: '#a4865f', display: 'inline-block',
        }} />
        {contextLabel}
      </div>

      {/* File selection */}
      {phase === 'select' && (
        <div>
          <p style={{ fontSize: 13, color: 'rgba(26,28,29,0.65)', margin: '0 0 10px' }}>
            Share a file with SHUNYA. Your files stay private to your current context.
          </p>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              ref={fileRef}
              type="file"
              onChange={handleFileChange}
              accept=".pdf,.xlsx,.csv,.txt,.docx,.md,.json,.png,.jpg,.jpeg"
              style={{
                flex: 1, padding: '8px 12px',
                border: '1px solid rgba(26,28,29,0.12)', borderRadius: 6,
                fontSize: 13, fontFamily: 'inherit',
              }}
            />
            <button
              onClick={handleUpload}
              disabled={!file}
              style={{
                padding: '8px 18px', borderRadius: 6, border: 'none',
                background: !file ? 'rgba(26,28,29,0.1)' : '#1a1c1d',
                color: !file ? 'rgba(26,28,29,0.35)' : '#fff',
                fontSize: 13, fontWeight: 500, cursor: !file ? 'default' : 'pointer',
                fontFamily: 'inherit', whiteSpace: 'nowrap',
              }}
            >
              Add to {isOrg ? 'Panchi Club' : 'My SHUNYA'}
            </button>
          </div>
          {file && (
            <div style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)', marginTop: 6 }}>
              Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>
      )}

      {/* Uploading */}
      {phase === 'uploading' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0' }}>
          <div style={{
            width: 16, height: 16, borderRadius: '50%',
            border: '2px solid rgba(164,134,95,0.3)',
            borderTopColor: '#a4865f',
            animation: 'as-spin 0.8s linear infinite',
          }} />
          <span style={{ fontSize: 13, color: 'rgba(26,28,29,0.55)' }}>
            SHUNYA is reading your file…
          </span>
        </div>
      )}

      {/* Result */}
      {phase === 'result' && result && (
        <div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            fontSize: 13, color: '#2e7d32', marginBottom: 8,
          }}>
            <span>✅</span>
            <span>File added to <strong>{isOrg ? 'Panchi Club' : 'your personal workspace'}</strong></span>
          </div>
          <div style={{
            padding: '10px 14px',
            background: 'rgba(46,125,50,0.04)',
            borderRadius: 8, fontSize: 13, color: 'rgba(26,28,29,0.65)',
            lineHeight: 1.5, marginBottom: 10,
          }}>
            {result.summary || `File "${result.filename}" stored successfully.`}
          </div>
          <div style={{ fontSize: 12, color: 'rgba(26,28,29,0.45)', marginBottom: 10 }}>
            File type: {result.file_type?.toUpperCase()} | Size: {result.size ? `${(result.size / 1024).toFixed(1)} KB` : 'unknown'}
          </div>
          <button
            onClick={handleReset}
            style={{
              padding: '6px 16px', borderRadius: 6,
              border: '1px solid rgba(26,28,29,0.12)',
              background: 'transparent', fontSize: 12,
              cursor: 'pointer', fontFamily: 'inherit', color: 'rgba(26,28,29,0.55)',
            }}
          >
            Add Another File
          </button>
        </div>
      )}

      {/* Error */}
      {phase === 'error' && (
        <div>
          <div style={{ fontSize: 13, color: '#d1453b', marginBottom: 8 }}>
            ❌ {error}
          </div>
          <button
            onClick={handleReset}
            style={{
              padding: '6px 16px', borderRadius: 6,
              border: '1px solid rgba(26,28,29,0.12)',
              background: 'transparent', fontSize: 12,
              cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            Try Again
          </button>
        </div>
      )}

      <style>{`@keyframes as-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};

export default AddToShunya;