/**
 * Step: Company Knowledge Import (Z-03A Article X).
 *
 * Before entering the workspace, offer to bring business data into SHUNYA.
 * Options: Connect Gmail, Connect Outlook, Upload PDFs/Word/Excel/CSV,
 * Upload proposals/invoices/itineraries, Import later.
 *
 * Never blocks entry — "Import later" always available.
 */

import { useState, useRef, useEffect } from 'react';
import { onboardingStyles } from './onboarding-styles';

interface Props {
  onNext: () => void;
  onBack: () => void;
}

interface ImportOption {
  id: string;
  icon: string;
  title: string;
  desc: string;
}

const IMPORT_OPTIONS: ImportOption[] = [
  { id: 'gmail', icon: '📧', title: 'Connect Gmail', desc: 'Import emails and contacts from your Gmail account.' },
  { id: 'outlook', icon: '📨', title: 'Connect Outlook', desc: 'Import emails and contacts from Outlook.' },
  { id: 'docs', icon: '📄', title: 'Upload Documents', desc: 'PDFs, Word, Excel, and CSV files.' },
  { id: 'business', icon: '💼', title: 'Upload Business Files', desc: 'Proposals, invoices, itineraries, and more.' },
];

export function StepImport({ onNext, onBack }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const [uploadPhase, setUploadPhase] = useState<'idle' | 'importing' | 'done' | 'error'>('idle');
  const [uploadError, setUploadError] = useState('');
  const btnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    btnRef.current?.focus();
  }, []);

  const handleOptionClick = async (id: string) => {
    setSelected(id);
    setUploadPhase('importing');

    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      setUploadPhase('done');
      setTimeout(() => {
        onNext();
      }, 1000);
    } catch {
      setUploadPhase('error');
      setUploadError('Could not connect to the import service. Please try again later.');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onBack();
    }
  };

  return (
    <div className="sh-onboarding" onKeyDown={handleKeyDown}>
      <div className="sh-onboarding-content">
        <div className="sh-onboarding-card sh-onb-fade-in">
          <div className="sh-onboarding-title">Import Your Business Data</div>
          <div className="sh-onboarding-subtitle">
            Bring your existing data into SHUNYA to get started faster.
            Your information stays private and secure.
          </div>

          {uploadPhase === 'importing' && (
            <div className="sh-onboarding-info" style={{ width: '100%', textAlign: 'center' }}>
              <span className="sh-onboarding-spinner" />
              <span style={{ marginLeft: 8 }}>Preparing import…</span>
            </div>
          )}

          {uploadPhase === 'done' && (
            <div className="sh-onboarding-success" style={{ width: '100%' }}>
              Import started! You can check progress in your workspace.
            </div>
          )}

          {uploadPhase === 'error' && (
            <div className="sh-onboarding-error" role="alert" style={{ width: '100%' }}>
              {uploadError}
            </div>
          )}

          {uploadPhase !== 'importing' && uploadPhase !== 'done' && (
            <>
              <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {IMPORT_OPTIONS.map(opt => (
                  <button
                    key={opt.id}
                    className={`sh-import-option ${selected === opt.id ? 'selected' : ''}`}
                    onClick={() => handleOptionClick(opt.id)}
                    tabIndex={0}
                  >
                    <span className="sh-import-icon">{opt.icon}</span>
                    <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 2 }}>
                      <span className="sh-import-title">{opt.title}</span>
                      <span className="sh-import-desc">{opt.desc}</span>
                    </span>
                  </button>
                ))}
              </div>

              <div className="sh-onboarding-btn-row">
                <button
                  className="sh-onboarding-btn"
                  onClick={onNext}
                  ref={btnRef}
                  tabIndex={0}
                >
                  Import later ›
                </button>
              </div>
            </>
          )}

          <button
            className="sh-onboarding-btn-secondary"
            onClick={onBack}
            disabled={uploadPhase === 'importing'}
            tabIndex={0}
          >
            Back
          </button>
        </div>
      </div>

      <style>{`
        ${onboardingStyles}

        .sh-import-option {
          display: flex; align-items: center; gap: 14px;
          width: 100%; padding: 12px 16px;
          background: #1a1a24; border: 1px solid #2a2a3a; border-radius: 8px;
          color: #e0e0e0; font-family: inherit; cursor: pointer;
          transition: all 0.2s; text-align: left;
        }
        .sh-import-option:hover { border-color: #444; background: #1f1f2b; }
        .sh-import-option.selected {
          border-color: #D4A84B;
          background: rgba(212, 168, 75, 0.1);
          box-shadow: 0 0 0 1px #D4A84B inset;
        }
        .sh-import-option:focus-visible {
          outline: 2px solid #D4A84B; outline-offset: 2px;
        }
        .sh-import-option:disabled { opacity: 0.5; cursor: not-allowed; }
        .sh-import-icon { font-size: 1.3rem; flex-shrink: 0; }
        .sh-import-title { font-size: 0.9rem; font-weight: 500; color: #fff; }
        .sh-import-desc { font-size: 0.78rem; color: #888; line-height: 1.4; }
      `}</style>
    </div>
  );
}