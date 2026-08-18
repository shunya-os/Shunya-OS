/**
 * Step: Company Knowledge Import (Z-03A Article X).
 *
 * Before entering the workspace, offer to bring business data into SHUNYA.
 * Options: Upload files (PDFs, Word, Excel, CSV, images, audio),
 * Connect Gmail (OAuth), Import later.
 *
 * File upload uses the real /api/v1/upload endpoint with SHA256 dedup.
 * Drag-drop, file picker, and clipboard paste supported.
 * Never blocks entry — "Import later" always available.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, FileText, Mail, CheckCircle2, AlertCircle } from 'lucide-react';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: () => void;
  onBack: () => void;
}

interface UploadItem {
  id: string;
  name: string;
  size: number;
  status: 'pending' | 'uploading' | 'done' | 'error';
  error?: string;
}

// ── Gmail OAuth (Google Identity Services — Free) ──
// Uses Google's one-tap OAuth flow via the browser.
// No backend proxy needed — Gmail API read scope is free.
function GmailConnect({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle');

  const handleConnect = useCallback(() => {
    setPhase('connecting');
    const W = window as any;
    if (!W.google?.accounts?.oauth2) {
      // Load Google Identity Services
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.onload = () => startGmailOAuth(setPhase, onComplete);
      document.head.appendChild(script);
    } else {
      startGmailOAuth(setPhase, onComplete);
    }
  }, [onComplete]);

  return (
    <div className="oi-gmail">
      {phase === 'idle' && (
        <button className="oi-btn oi-btn-google" onClick={handleConnect}>
          <Mail size={16} />
          <span>Connect Gmail</span>
        </button>
      )}
      {phase === 'connecting' && (
        <div className="oi-phase">
          <span className="oi-spinner" />
          <span>Connecting to Gmail…</span>
        </div>
      )}
      {phase === 'connected' && (
        <div className="oi-phase oi-phase-done">
          <CheckCircle2 size={16} />
          <span>Gmail connected! Recent emails will appear in your workspace.</span>
        </div>
      )}
      {phase === 'error' && (
        <div className="oi-phase oi-phase-error">
          <AlertCircle size={16} />
          <span>Could not connect Gmail. You can try again later from your workspace.</span>
        </div>
      )}
    </div>
  );
}

function startGmailOAuth(setPhase: (p: 'connecting' | 'connected' | 'error') => void, onComplete: () => void) {
  const W = window as any;
  if (!W.google?.accounts?.oauth2) {
    setPhase('error');
    return;
  }

  const client = W.google.accounts.oauth2.initTokenClient({
    client_id: 'YOUR_GOOGLE_CLIENT_ID', // Replace with actual OAuth client ID
    scope: 'https://www.googleapis.com/auth/gmail.readonly',
    callback: (response: any) => {
      if (response.access_token) {
        // Store token and trigger import
        sessionStorage.setItem('shunya_gmail_token', response.access_token);
        setPhase('connected');
        // Trigger async import in background
        fetch('/api/v1/intelligence/mixed', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            question: 'Import my recent Gmail emails',
            gmail_token: response.access_token,
          }),
        }).catch(() => {});
        setTimeout(onComplete, 1500);
      } else {
        setPhase('error');
      }
    },
    error_callback: () => setPhase('error'),
  });
  client.requestAccessToken();
}

// ── Upload Zone ──

function UploadZone({ onUploadsChange }: { onUploadsChange: (count: number) => void }) {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      const newItems: UploadItem[] = [];
      for (const f of Array.from(files)) {
        newItems.push({
          id: `upload_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
          name: f.name,
          size: f.size,
          status: 'pending',
        });
      }
      setUploads((prev) => {
        const combined = [...prev, ...newItems];
        onUploadsChange(combined.filter((u) => u.status !== 'error' && u.status !== 'done').length);
        return combined;
      });

      // Start uploading each file
      for (const item of newItems) {
        const file = Array.from(files).find((f) => f.name === item.name);
        if (!file) continue;

        setUploads((prev) => prev.map((u) => (u.id === item.id ? { ...u, status: 'uploading' } : u)));

        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/v1/upload', {
          method: 'POST',
          body: formData,
          credentials: 'include',
        })
          .then((r) => r.json())
          .then((d) => {
            setUploads((prev) => {
              const next = prev.map((u) =>
                u.id === item.id
                  ? { ...u, status: d.success ? ('done' as const) : ('error' as const), error: d.error }
                  : u,
              );
              onUploadsChange(next.filter((u) => u.status !== 'error' && u.status !== 'done').length);
              return next;
            });
          })
          .catch(() => {
            setUploads((prev) => {
              const next = prev.map((u) =>
                u.id === item.id ? { ...u, status: 'error' as const, error: 'Upload failed' } : u,
              );
              onUploadsChange(next.filter((u) => u.status !== 'error' && u.status !== 'done').length);
              return next;
            });
          });
      }
    },
    [onUploadsChange],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files.length > 0) addFiles(e.dataTransfer.files);
    },
    [addFiles],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragOver(false), []);

  const doneCount = uploads.filter((u) => u.status === 'done').length;
  const errorCount = uploads.filter((u) => u.status === 'error').length;

  return (
    <div className="oi-upload-zone">
      {/* Drop zone */}
      <div
        className={`oi-dropzone ${dragOver ? 'oi-dropzone-active' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileRef.current?.click()}
      >
        <input
          ref={fileRef}
          type="file"
          multiple
          className="oi-hidden-input"
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = '';
          }}
          accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.md,.jpg,.jpeg,.png,.gif,.mp3,.wav,.mp4"
        />
        <Upload size={24} className="oi-drop-icon" />
        <div className="oi-drop-text">
          <span className="oi-drop-main">Drop files here or click to browse</span>
          <span className="oi-drop-hint">PDFs, Word, Excel, CSV, images, audio — anything your business uses</span>
        </div>
      </div>

      {/* Upload progress */}
      {uploads.length > 0 && (
        <div className="oi-uploads">
          {uploads.map((u) => (
            <div key={u.id} className={`oi-upload-item oi-upload-${u.status}`}>
              <FileText size={14} />
              <span className="oi-upload-name">{u.name}</span>
              <span className="oi-upload-status">
                {u.status === 'pending' && 'Waiting…'}
                {u.status === 'uploading' && <span className="oi-spinner" />}
                {u.status === 'done' && <CheckCircle2 size={14} />}
                {u.status === 'error' && <span title={u.error}>⚠</span>}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {doneCount > 0 && (
        <div className="oi-summary oi-summary-done">
          <CheckCircle2 size={14} />
          <span>
            {doneCount} file{doneCount !== 1 ? 's' : ''} uploaded to your workspace
          </span>
        </div>
      )}
      {errorCount > 0 && (
        <div className="oi-summary oi-summary-error">
          <AlertCircle size={14} />
          <span>
            {errorCount} upload{errorCount !== 1 ? 's' : ''} failed — you can retry from your workspace
          </span>
        </div>
      )}
    </div>
  );
}

// ── Main Component ──

export function StepImport({ onNext, onBack }: Props) {
  const [activeTab, setActiveTab] = useState<'upload' | 'gmail'>('upload');
  const [pendingUploads, setPendingUploads] = useState(0);
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    btnRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onBack();
    }
  };

  return (
    <div className="sh-onboarding" onKeyDown={handleKeyDown}>
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in" style={{ maxWidth: 560 }}>
          <div className="sh-onboarding-title">Bring Your Business Into SHUNYA</div>
          <div className="sh-onboarding-subtitle">
            Upload your existing files or connect Gmail. Everything stays private and encrypted. You can always import
            more later from your workspace.
          </div>

          {/* Tab switcher */}
          <div className="oi-tabs">
            <button
              className={`oi-tab ${activeTab === 'upload' ? 'oi-tab-active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              <Upload size={14} />
              <span>Upload Files</span>
            </button>
            <button
              className={`oi-tab ${activeTab === 'gmail' ? 'oi-tab-active' : ''}`}
              onClick={() => setActiveTab('gmail')}
            >
              <Mail size={14} />
              <span>Connect Gmail</span>
            </button>
          </div>

          {/* Content */}
          {activeTab === 'upload' ? (
            <UploadZone onUploadsChange={setPendingUploads} />
          ) : (
            <div className="oi-gmail-section">
              <p className="oi-gmail-desc">
                Connect your Gmail to import recent emails, contacts, and attachments. SHUNYA reads only email metadata
                and content — it never sends emails on your behalf.
              </p>
              <GmailConnect onComplete={() => {}} />
            </div>
          )}

          {/* Actions */}
          <div className="sh-onboarding-btn-row" style={{ marginTop: 20 }}>
            <button className="sh-onboarding-btn" onClick={onNext} ref={btnRef}>
              {pendingUploads > 0 ? `Continue (${pendingUploads} uploading…)` : 'Import later ›'}
            </button>
          </div>

          <button className="sh-onboarding-btn-secondary" onClick={onBack}>
            Back
          </button>
        </div>
      </div>

      <style>{`
        ${onboardingStyles}

        .oi-tabs { display: flex; gap: 4px; background: var(--sh-surface-subtle, #F8F7F4); border-radius: 10px; padding: 3px; margin: 16px 0; width: 100%; }
        .oi-tab { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 8px 12px; border: none; border-radius: 8px; background: transparent; color: var(--sh-text-secondary, rgba(26,28,29,0.55)); font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; transition: all 0.15s; }
        .oi-tab-active { background: #fff; color: var(--sh-gold, #6C4AE2); box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
        .oi-tab:hover { color: var(--sh-text, #1A1C1D); }
        .oi-tab svg { flex-shrink: 0; }

        .oi-dropzone { display: flex; align-items: center; gap: 14px; padding: 24px; border: 2px dashed var(--sh-border, rgba(26,28,29,0.12)); border-radius: 12px; cursor: pointer; transition: all 0.15s; text-align: left; }
        .oi-dropzone:hover, .oi-dropzone-active { border-color: var(--sh-gold, #6C4AE2); background: rgba(108,74,226,0.03); }
        .oi-drop-icon { color: var(--sh-gold, #6C4AE2); flex-shrink: 0; }
        .oi-drop-text { display: flex; flex-direction: column; gap: 2px; }
        .oi-drop-main { font-size: 13px; font-weight: 500; color: var(--sh-text, #1A1C1D); }
        .oi-drop-hint { font-size: 11px; color: var(--sh-text-tertiary, rgba(26,28,29,0.35)); }
        .oi-hidden-input { display: none; }

        .oi-uploads { display: flex; flex-direction: column; gap: 4px; margin-top: 12px; }
        .oi-upload-item { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: var(--sh-surface-subtle, #F8F7F4); border-radius: 8px; font-size: 12px; }
        .oi-upload-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--sh-text, #1A1C1D); }
        .oi-upload-status { width: 16px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .oi-upload-pending .oi-upload-status { color: var(--sh-text-tertiary, rgba(26,28,29,0.35)); }
        .oi-upload-done .oi-upload-status { color: var(--sh-success, #2D6A4F); }
        .oi-upload-error .oi-upload-status { color: var(--sh-danger, #B91C1C); }

        .oi-spinner { width: 14px; height: 14px; border: 2px solid var(--sh-border, rgba(26,28,29,0.08)); border-top-color: var(--sh-gold, #6C4AE2); border-radius: 50%; animation: oi-spin 0.6s linear infinite; display: inline-block; }
        @keyframes oi-spin { to { transform: rotate(360deg); } }

        .oi-summary { display: flex; align-items: center; gap: 6px; padding: 8px 12px; border-radius: 8px; font-size: 12px; margin-top: 8px; }
        .oi-summary-done { background: rgba(45,106,79,0.06); color: var(--sh-success, #2D6A4F); }
        .oi-summary-error { background: rgba(185,28,28,0.06); color: var(--sh-danger, #B91C1C); }

        .oi-gmail-section { padding: 4px 0; }
        .oi-gmail-desc { font-size: 13px; line-height: 1.6; color: var(--sh-text-secondary, rgba(26,28,29,0.55)); margin: 0 0 12px; }
        .oi-gmail { }
        .oi-btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border: 1px solid var(--sh-border, rgba(26,28,29,0.12)); border-radius: 10px; background: #fff; font-size: 13px; font-weight: 500; cursor: pointer; font-family: inherit; transition: all 0.15s; color: var(--sh-text, #1A1C1D); }
        .oi-btn:hover { border-color: var(--sh-gold, #6C4AE2); color: var(--sh-gold, #6C4AE2); }
        .oi-btn-google svg { color: #EA4335; }
        .oi-phase { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--sh-text-secondary, rgba(26,28,29,0.55)); }
        .oi-phase-done { color: var(--sh-success, #2D6A4F); }
        .oi-phase-error { color: var(--sh-danger, #B91C1C); }
      `}</style>
    </div>
  );
}
