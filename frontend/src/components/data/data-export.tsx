/**
 * Data Export — scope selector, format selector, export button, progress, download.
 *
 * POST /api/v1/export          → create job
 * GET  /api/v1/export/status/:id → poll progress
 * GET  /api/v1/export/download/:id → download file
 */
import { useState, useCallback, useRef } from 'react';
import { IconFileExport, IconDownload, IconLoader2 } from '@tabler/icons-react';

interface ExportJob {
  id: string;
  status: string;
  progress: number;
  scope: string;
  format: string;
  error?: string | null;
  created_at?: string;
  completed_at?: string;
}

const SCOPES = [
  { value: 'all', label: 'All Data' },
  { value: 'contacts', label: 'Contacts & Members' },
  { value: 'documents', label: 'Documents' },
  { value: 'finance', label: 'Finance' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'sales', label: 'Sales' },
  { value: 'notifications', label: 'Notifications' },
];

const FORMATS = [
  { value: 'json', label: 'JSON' },
  { value: 'csv', label: 'CSV' },
];

export function DataExport() {
  const [scope, setScope] = useState('all');
  const [fmt, setFmt] = useState('json');
  const [job, setJob] = useState<ExportJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const pollStatus = useCallback(async (jobId: string) => {
    try {
      const r = await fetch(`/api/v1/export/status/${jobId}`, { credentials: 'include' });
      const d = await r.json();
      if (d.success) {
        setJob(d.job);
        if (d.job.status === 'completed' || d.job.status === 'failed') {
          if (pollRef.current) clearInterval(pollRef.current);
        }
      }
    } catch {
      if (pollRef.current) clearInterval(pollRef.current);
    }
  }, []);

  const handleExport = useCallback(async () => {
    setLoading(true);
    setError('');
    setJob(null);
    try {
      const r = await fetch('/api/v1/export', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope, format: fmt }),
      });
      const d = await r.json();
      if (d.success) {
        setJob(d.job);
        pollRef.current = setInterval(() => pollStatus(d.job.id), 1500);
      } else {
        setError(d.error || 'Export failed to start');
      }
    } catch {
      setError('Network error starting export');
    }
    setLoading(false);
  }, [scope, fmt, pollStatus]);

  const handleDownload = useCallback(async () => {
    if (!job?.id) return;
    try {
      const r = await fetch(`/api/v1/export/download/${job.id}`, { credentials: 'include' });
      if (!r.ok) {
        const d = await r.json();
        setError(d.error || 'Download failed');
        return;
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `shunya_export_${job.id.slice(0, 8)}.${fmt}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError('Download failed');
    }
  }, [job, fmt]);

  const isProcessing = job?.status === 'processing';
  const isCompleted = job?.status === 'completed';
  const isFailed = job?.status === 'failed';

  return (
    <div className="data-export">
      <div className="data-export-header">
        <h2><IconFileExport size={18} /> Data Export</h2>
      </div>
      <p className="data-export-subtitle">
        Export your SHUNYA data for backup or migration.
      </p>

      <div className="data-export-form">
        <div className="data-export-field">
          <label className="data-export-label">Scope</label>
          <select
            className="data-export-select"
            value={scope}
            onChange={e => setScope(e.target.value)}
            disabled={loading || isProcessing}
          >
            {SCOPES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        <div className="data-export-field">
          <label className="data-export-label">Format</label>
          <div className="data-export-format-group">
            {FORMATS.map(f => (
              <button
                key={f.value}
                className={`data-export-format-btn ${fmt === f.value ? 'data-export-format-active' : ''}`}
                onClick={() => setFmt(f.value)}
                disabled={loading || isProcessing}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <button
          className="data-export-btn"
          onClick={handleExport}
          disabled={loading || isProcessing}
        >
          {loading || isProcessing ? (
            <><IconLoader2 size={16} className="data-export-spin" /> Exporting…</>
          ) : (
            <><IconFileExport size={16} /> Export Data</>
          )}
        </button>
      </div>

      {error && <p className="data-export-error" role="alert">{error}</p>}

      {job && (
        <div className={`data-export-job ${isCompleted ? 'data-export-job-done' : ''} ${isFailed ? 'data-export-job-failed' : ''}`}>
          <div className="data-export-job-header">
            <span className="data-export-job-label">
              {isProcessing && 'Processing export…'}
              {isCompleted && 'Export complete'}
              {isFailed && 'Export failed'}
            </span>
            <span className="data-export-job-scope">{job.scope} · {job.format}</span>
          </div>
          {isProcessing && (
            <div className="data-export-progress-track">
              <div className="data-export-progress-fill" style={{ width: `${job.progress}%` }} />
            </div>
          )}
          {isCompleted && (
            <button className="data-export-download-btn" onClick={handleDownload}>
              <IconDownload size={16} /> Download
            </button>
          )}
          {isFailed && job.error && (
            <p className="data-export-job-error">{job.error}</p>
          )}
        </div>
      )}
    </div>
  );
}